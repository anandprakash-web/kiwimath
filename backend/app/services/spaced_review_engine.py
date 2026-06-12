"""
FSRS v5 Spaced Review Engine — Adaptive review scheduling using the Free
Spaced Repetition Scheduler algorithm (now in Anki since v23.10).

Implements the full FSRS v5 formulas from:
  "A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition
   Scheduling" — Ye et al. (2024)

Key improvements over the previous FSRS-Lite implementation:
  - Power-law forgetting curve: R(t,S) = (1 + FACTOR*t/S)^DECAY
  - Per-skill difficulty tracking (1.0–10.0 scale)
  - 4-grade rating support (Again/Hard/Good/Easy)
  - Research-validated parameter set (17 weights)
  - Backward-compatible: boolean success maps to Good/Again

Firestore path: users/{uid}/review_schedule/{skill_id}
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from app.assessment.path_engine import PREREQUISITE_GRAPH

logger = logging.getLogger("kiwimath.spaced_review")

# ---------------------------------------------------------------------------
# FSRS v5 Constants & Parameters
# ---------------------------------------------------------------------------

# Ratings
AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4

# Power-law forgetting curve constants
DECAY = -0.5
FACTOR = 19.0 / 81.0  # (0.9^(1/DECAY) - 1)

# Target recall probability
TARGET_RECALL = 0.90

# Maximum / minimum intervals (days)
MAX_INTERVAL_DAYS = 365
MIN_INTERVAL_DAYS = 1

# FSRS v5 default parameters (from open-source FSRS optimizer)
# w[0..3] : initial stability for ratings Again, Hard, Good, Easy
# w[4]    : initial difficulty mean
# w[5]    : initial difficulty scaling
# w[6]    : difficulty reversion strength
# w[7]    : difficulty mean-reversion weight
# w[8..10]: success stability factors
# w[11..14]: failure (lapse) stability factors
# w[15]   : hard penalty multiplier
# w[16]   : easy bonus multiplier
W = [
    0.40,   # w0  - S0(Again)
    0.60,   # w1  - S0(Hard)
    2.40,   # w2  - S0(Good)
    5.80,   # w3  - S0(Easy)
    4.93,   # w4  - initial difficulty base
    0.94,   # w5  - initial difficulty scaling
    0.86,   # w6  - difficulty grade factor
    0.01,   # w7  - difficulty mean-reversion weight
    1.49,   # w8  - success stability exp factor
    0.14,   # w9  - success stability power factor
    0.94,   # w10 - success retrievability factor
    2.18,   # w11 - lapse stability base
    0.05,   # w12 - lapse difficulty power
    0.34,   # w13 - lapse stability power
    1.26,   # w14 - lapse retrievability factor
    0.29,   # w15 - hard penalty
    2.61,   # w16 - easy bonus
]

# Difficulty bounds
MIN_DIFFICULTY = 1.0
MAX_DIFFICULTY = 10.0

# Skill-type difficulty adjustments (offset added to D0)
# Procedural skills are easier to retain; conceptual skills harder
DOMAIN_TO_CATEGORY = {
    "numbers": "conceptual",
    "arithmetic": "procedural",
    "fractions": "conceptual",
    "geometry": "spatial",
    "measurement": "measurement",
    "data": "data",
}

CATEGORY_DIFFICULTY_OFFSET = {
    "procedural": -0.8,   # Easier to retain (drill-based)
    "conceptual": +0.5,   # Harder (abstract)
    "spatial": 0.0,
    "measurement": -0.3,
    "data": 0.0,
}

SKILL_CATEGORY_OVERRIDES = {
    "addition_basic": "procedural",
    "addition_2digit": "procedural",
    "subtraction_basic": "procedural",
    "subtraction_2digit": "procedural",
    "multiplication_facts": "procedural",
    "division_basic": "procedural",
    "order_of_ops": "procedural",
    "multi_step": "conceptual",
    "number_patterns": "conceptual",
    "rounding": "conceptual",
}


# ---------------------------------------------------------------------------
# Core FSRS v5 formulas
# ---------------------------------------------------------------------------

def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def forgetting_curve(elapsed_days: float, stability: float) -> float:
    """Power-law forgetting curve: R(t, S) = (1 + FACTOR * t / S)^DECAY"""
    if stability <= 0:
        return 0.0
    return (1.0 + FACTOR * elapsed_days / stability) ** DECAY


def next_interval(stability: float, desired_retention: float = TARGET_RECALL) -> float:
    """Compute days until recall drops to desired_retention.

    Solving R = (1 + FACTOR*t/S)^DECAY for t:
        t = S/FACTOR * (R^(1/DECAY) - 1)
    """
    if stability <= 0:
        return MIN_INTERVAL_DAYS
    interval = stability / FACTOR * (desired_retention ** (1.0 / DECAY) - 1.0)
    return _clamp(interval, MIN_INTERVAL_DAYS, MAX_INTERVAL_DAYS)


def initial_stability(rating: int) -> float:
    """S0(G) = w[G-1] for rating G ∈ {1,2,3,4}"""
    idx = _clamp(rating - 1, 0, 3)
    return max(0.01, W[int(idx)])


def initial_difficulty(rating: int) -> float:
    """D0(G) = w4 - exp(w5 * (G - 1)) + 1, clamped to [1, 10]"""
    d = W[4] - math.exp(W[5] * (rating - 1)) + 1.0
    return _clamp(d, MIN_DIFFICULTY, MAX_DIFFICULTY)


def next_difficulty(d: float, rating: int) -> float:
    """Mean-reversion difficulty update:
    D' = w7 * D0(3) + (1 - w7) * (D - w6 * (G - 3))
    """
    d_new = W[7] * initial_difficulty(GOOD) + (1.0 - W[7]) * (d - W[6] * (rating - 3))
    return _clamp(d_new, MIN_DIFFICULTY, MAX_DIFFICULTY)


def next_stability_success(s: float, d: float, r: float, rating: int) -> float:
    """Stability after successful recall:
    S'_s = S * (exp(w8) * (11-D) * S^(-w9) * (exp(w10*(1-R)) - 1) * hard_pen * easy_bon + 1)
    """
    hard_pen = W[15] if rating == HARD else 1.0
    easy_bon = W[16] if rating == EASY else 1.0

    inner = (
        math.exp(W[8])
        * (11.0 - d)
        * (s ** (-W[9]))
        * (math.exp(W[10] * (1.0 - r)) - 1.0)
        * hard_pen
        * easy_bon
    )
    return max(0.01, s * (inner + 1.0))


def next_stability_failure(s: float, d: float, r: float) -> float:
    """Stability after lapse (forgot):
    S'_f = w11 * D^(-w12) * ((S+1)^w13 - 1) * exp(w14*(1-R))
    """
    s_new = (
        W[11]
        * (d ** (-W[12]))
        * ((s + 1.0) ** W[13] - 1.0)
        * math.exp(W[14] * (1.0 - r))
    )
    return _clamp(s_new, 0.01, s)  # Never increase stability on failure


# ---------------------------------------------------------------------------
# Skill category helper
# ---------------------------------------------------------------------------

def _get_skill_category(skill_id: str) -> str:
    if skill_id in SKILL_CATEGORY_OVERRIDES:
        return SKILL_CATEGORY_OVERRIDES[skill_id]
    node = PREREQUISITE_GRAPH.get(skill_id)
    if node:
        return DOMAIN_TO_CATEGORY.get(node.domain, "conceptual")
    return "conceptual"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ReviewSchedule:
    """Tracks the FSRS review schedule for a single mastered skill."""
    skill_id: str
    stability: float = 2.4                  # Current stability (days)
    difficulty: float = 5.0                 # Difficulty (1.0–10.0)
    n_reviews: int = 0
    n_successful: int = 0
    last_review_date: Optional[str] = None
    next_review_date: Optional[str] = None
    mastery_date: Optional[str] = None
    consecutive_successes: int = 0
    review_history: List[Dict[str, Any]] = field(default_factory=list)
    # Legacy field kept for backward compatibility (ignored in FSRS v5)
    decay_rate: float = 0.35

    @property
    def is_due(self) -> bool:
        if not self.next_review_date:
            return False
        try:
            next_dt = datetime.fromisoformat(self.next_review_date.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) >= next_dt
        except (ValueError, AttributeError):
            return False

    @property
    def days_overdue(self) -> float:
        if not self.next_review_date:
            return -999.0
        try:
            next_dt = datetime.fromisoformat(self.next_review_date.replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - next_dt).total_seconds() / 86400
        except (ValueError, AttributeError):
            return -999.0

    @property
    def estimated_recall(self) -> float:
        if not self.last_review_date:
            return 1.0
        try:
            last_dt = datetime.fromisoformat(self.last_review_date.replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds() / 86400
            return forgetting_curve(elapsed, self.stability)
        except (ValueError, AttributeError):
            return 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "stability": round(self.stability, 4),
            "difficulty": round(self.difficulty, 2),
            "n_reviews": self.n_reviews,
            "n_successful": self.n_successful,
            "last_review_date": self.last_review_date,
            "next_review_date": self.next_review_date,
            "mastery_date": self.mastery_date,
            "consecutive_successes": self.consecutive_successes,
            "review_history": self.review_history[-20:],
            "decay_rate": self.decay_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewSchedule":
        return cls(
            skill_id=data.get("skill_id", ""),
            stability=data.get("stability", 2.4),
            difficulty=data.get("difficulty", 5.0),
            n_reviews=data.get("n_reviews", 0),
            n_successful=data.get("n_successful", 0),
            last_review_date=data.get("last_review_date"),
            next_review_date=data.get("next_review_date"),
            mastery_date=data.get("mastery_date"),
            consecutive_successes=data.get("consecutive_successes", 0),
            review_history=data.get("review_history", []),
            decay_rate=data.get("decay_rate", 0.35),
        )


# ---------------------------------------------------------------------------
# Core scheduling API
# ---------------------------------------------------------------------------

def create_review_schedule(skill_id: str) -> ReviewSchedule:
    """Create a new review schedule when a skill is mastered.

    First review is treated as an initial rating of Good (3).
    """
    category = _get_skill_category(skill_id)
    d_offset = CATEGORY_DIFFICULTY_OFFSET.get(category, 0.0)

    s0 = initial_stability(GOOD)
    d0 = _clamp(initial_difficulty(GOOD) + d_offset, MIN_DIFFICULTY, MAX_DIFFICULTY)

    now = datetime.now(timezone.utc)
    interval = next_interval(s0)
    next_review = now + timedelta(days=interval)

    schedule = ReviewSchedule(
        skill_id=skill_id,
        stability=s0,
        difficulty=d0,
        mastery_date=now.isoformat(),
        last_review_date=now.isoformat(),
        next_review_date=next_review.isoformat(),
    )

    logger.info(
        f"FSRS SCHEDULED: skill={skill_id}, category={category}, "
        f"S0={s0:.2f}, D0={d0:.2f}, first_review_in={interval:.1f}d"
    )
    return schedule


def record_review_result(
    schedule: ReviewSchedule,
    success: bool,
    rating: Optional[int] = None,
) -> ReviewSchedule:
    """Update the schedule after a review.

    Args:
        schedule: Current schedule to update.
        success: True if recalled correctly (backward compat).
        rating: Optional FSRS rating 1-4 (Again/Hard/Good/Easy).
                If not provided, maps success→Good(3), fail→Again(1).
    """
    now = datetime.now(timezone.utc)

    # Determine rating
    if rating is not None:
        g = _clamp(rating, AGAIN, EASY)
    else:
        g = GOOD if success else AGAIN

    # Compute elapsed days since last review
    elapsed = 0.0
    if schedule.last_review_date:
        try:
            last_dt = datetime.fromisoformat(schedule.last_review_date.replace("Z", "+00:00"))
            elapsed = max(0, (now - last_dt).total_seconds() / 86400)
        except (ValueError, AttributeError):
            pass

    # Current retrievability at the moment of review
    r = forgetting_curve(elapsed, schedule.stability)

    # Update difficulty
    schedule.difficulty = next_difficulty(schedule.difficulty, int(g))

    # Update stability based on success/failure
    old_stability = schedule.stability
    if g == AGAIN:
        schedule.stability = next_stability_failure(
            schedule.stability, schedule.difficulty, r
        )
        schedule.consecutive_successes = 0
    else:
        schedule.stability = next_stability_success(
            schedule.stability, schedule.difficulty, r, int(g)
        )
        schedule.n_successful += 1
        schedule.consecutive_successes += 1

    schedule.n_reviews += 1
    schedule.last_review_date = now.isoformat()

    # Schedule next review
    interval = next_interval(schedule.stability)
    schedule.next_review_date = (now + timedelta(days=interval)).isoformat()

    # History
    schedule.review_history.append({
        "date": now.isoformat(),
        "rating": int(g),
        "success": g != AGAIN,
        "stability_before": round(old_stability, 2),
        "stability_after": round(schedule.stability, 2),
        "difficulty": round(schedule.difficulty, 2),
        "retrievability": round(r, 3),
        "interval_days": round(interval, 1),
    })
    schedule.review_history = schedule.review_history[-20:]

    logger.info(
        f"FSRS REVIEW: skill={schedule.skill_id}, rating={g}, "
        f"S={old_stability:.1f}→{schedule.stability:.1f}, "
        f"D={schedule.difficulty:.1f}, R={r:.2f}, next_in={interval:.1f}d"
    )
    return schedule


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class SpacedReviewStore:
    """Manages FSRS review schedules for all students.

    Firestore path: users/{uid}/review_schedule/{skill_id}
    """

    def __init__(self):
        self._memory: Dict[str, Dict[str, ReviewSchedule]] = {}

    def get_schedule(self, user_id: str, skill_id: str) -> Optional[ReviewSchedule]:
        if user_id in self._memory and skill_id in self._memory[user_id]:
            return self._memory[user_id][skill_id]

        from app.services.firestore_service import _get_db
        db = _get_db()
        if db:
            try:
                doc = (
                    db.collection("users")
                    .document(user_id)
                    .collection("review_schedule")
                    .document(skill_id)
                    .get()
                )
                if doc.exists:
                    schedule = ReviewSchedule.from_dict(doc.to_dict())
                    self._memory.setdefault(user_id, {})[skill_id] = schedule
                    return schedule
            except Exception as e:
                logger.warning(f"Firestore read error: {e}")
        return None

    def get_due_reviews(self, user_id: str, max_items: int = 5) -> List[ReviewSchedule]:
        all_schedules = self._get_all_schedules(user_id)
        due = [s for s in all_schedules.values() if s.is_due]
        due.sort(key=lambda s: s.days_overdue, reverse=True)
        return due[:max_items]

    def get_upcoming_reviews(self, user_id: str, days_ahead: int = 7) -> List[ReviewSchedule]:
        all_schedules = self._get_all_schedules(user_id)
        cutoff = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        upcoming = []
        for schedule in all_schedules.values():
            if not schedule.next_review_date:
                continue
            try:
                next_dt = datetime.fromisoformat(
                    schedule.next_review_date.replace("Z", "+00:00")
                )
                if next_dt <= cutoff:
                    upcoming.append(schedule)
            except (ValueError, AttributeError):
                continue
        upcoming.sort(key=lambda s: s.next_review_date or "")
        return upcoming

    def schedule_mastered_skill(self, user_id: str, skill_id: str) -> ReviewSchedule:
        schedule = create_review_schedule(skill_id)
        self._save_schedule(user_id, schedule)
        return schedule

    def record_review(
        self, user_id: str, skill_id: str, success: bool, rating: Optional[int] = None,
    ) -> Optional[ReviewSchedule]:
        schedule = self.get_schedule(user_id, skill_id)
        if not schedule:
            return None
        record_review_result(schedule, success, rating=rating)
        self._save_schedule(user_id, schedule)
        return schedule

    def get_review_summary(self, user_id: str) -> Dict[str, Any]:
        all_schedules = self._get_all_schedules(user_id)
        due_now = [s for s in all_schedules.values() if s.is_due]
        total_scheduled = len(all_schedules)
        avg_recall = (
            sum(s.estimated_recall for s in all_schedules.values())
            / max(1, total_scheduled)
        )
        return {
            "total_mastered_skills": total_scheduled,
            "due_for_review": len(due_now),
            "average_recall": round(avg_recall, 2),
            "upcoming_7_days": len(self.get_upcoming_reviews(user_id, 7)),
            "skills_due": [
                {
                    "skill_id": s.skill_id,
                    "days_overdue": round(s.days_overdue, 1),
                    "difficulty": round(s.difficulty, 1),
                }
                for s in due_now[:5]
            ],
        }

    def _get_all_schedules(self, user_id: str) -> Dict[str, ReviewSchedule]:
        if user_id in self._memory:
            return self._memory[user_id]

        from app.services.firestore_service import _get_db
        db = _get_db()
        if db:
            try:
                docs = (
                    db.collection("users")
                    .document(user_id)
                    .collection("review_schedule")
                    .stream()
                )
                schedules = {}
                for doc in docs:
                    s = ReviewSchedule.from_dict(doc.to_dict())
                    schedules[s.skill_id] = s
                self._memory[user_id] = schedules
                return schedules
            except Exception as e:
                logger.warning(f"Firestore read all error: {e}")

        self._memory.setdefault(user_id, {})
        return self._memory[user_id]

    def _save_schedule(self, user_id: str, schedule: ReviewSchedule) -> None:
        self._memory.setdefault(user_id, {})[schedule.skill_id] = schedule

        from app.services.firestore_service import _get_db
        db = _get_db()
        if db:
            try:
                (
                    db.collection("users")
                    .document(user_id)
                    .collection("review_schedule")
                    .document(schedule.skill_id)
                    .set(schedule.to_dict(), merge=True)
                )
            except Exception as e:
                logger.warning(f"Firestore write error: {e}")


# Singleton
spaced_review_store = SpacedReviewStore()
