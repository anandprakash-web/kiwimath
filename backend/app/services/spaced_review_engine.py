"""
FSRS-Lite Spaced Review Engine — Adaptive review scheduling based on forgetting curves.

Replaces the fixed 3-day review window with per-skill exponential decay modeling.
Each mastered skill has an independent "stability" value that grows with successful
reviews and decays differently based on skill type.

Research basis:
- FSRS algorithm (Free Spaced Repetition Scheduler) — now in Anki since v23.10
- PNAS: "Enhancing human learning via spaced repetition optimization" (2019)
- Meta-analyses show spaced practice benefits g > 0.40 for mathematics

Key insight: review should happen just before P(recall) drops to 90%.
The optimal interval = stability × (-ln(0.9) / decay_rate).

Skill types decay at different rates:
- Procedural (addition, multiplication): slow decay — once learned, stays longer
- Conceptual (fractions, place value): faster decay — abstract concepts fade
- Spatial (geometry, symmetry): moderate decay

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
# Constants
# ---------------------------------------------------------------------------

# Target recall probability — schedule review when P(recall) drops to this
TARGET_RECALL = 0.90

# Base stability (days) — how long a skill "lasts" after first mastery
BASE_STABILITY = 1.0

# Success multiplier — each successful review multiplies stability
SUCCESS_MULTIPLIER = 2.2

# Failure divisor — failed review divides stability
FAILURE_DIVISOR = 1.8

# Maximum interval (days) — never wait longer than this
MAX_INTERVAL_DAYS = 90

# Minimum interval (days)
MIN_INTERVAL_DAYS = 1

# Decay rates by skill category (higher = faster forgetting)
DECAY_RATES = {
    "procedural": 0.25,    # Addition, subtraction, multiplication, division
    "conceptual": 0.45,    # Fractions, place value, decimals, comparison
    "spatial": 0.35,       # Geometry, shapes, symmetry, coordinates
    "measurement": 0.30,   # Units, time, money, length, weight
    "data": 0.35,          # Data handling, statistics, graphs
}

# Map skill domains to decay categories
DOMAIN_TO_CATEGORY = {
    "numbers": "conceptual",
    "arithmetic": "procedural",
    "fractions": "conceptual",
    "geometry": "spatial",
    "measurement": "measurement",
    "data": "data",
}

# Map specific skills to override categories
SKILL_CATEGORY_OVERRIDES = {
    # These arithmetic skills are more procedural (drill-based)
    "addition_basic": "procedural",
    "addition_2digit": "procedural",
    "subtraction_basic": "procedural",
    "subtraction_2digit": "procedural",
    "multiplication_facts": "procedural",
    "division_basic": "procedural",
    "order_of_ops": "procedural",
    # These are conceptual despite being in arithmetic domain
    "multi_step": "conceptual",
    "number_patterns": "conceptual",
    "rounding": "conceptual",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ReviewSchedule:
    """Tracks the review schedule for a single mastered skill."""
    skill_id: str
    stability: float = BASE_STABILITY       # Current stability in days
    n_reviews: int = 0                      # Total reviews completed
    n_successful: int = 0                   # Successful reviews (recalled)
    last_review_date: Optional[str] = None  # ISO datetime of last review
    next_review_date: Optional[str] = None  # ISO datetime of next scheduled review
    mastery_date: Optional[str] = None      # When mastery was first confirmed
    decay_rate: float = 0.35                # Skill-specific decay rate
    consecutive_successes: int = 0          # Streak of successful reviews
    review_history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_due(self) -> bool:
        """Check if this skill is due for review right now."""
        if not self.next_review_date:
            return False
        try:
            next_dt = datetime.fromisoformat(self.next_review_date.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) >= next_dt
        except (ValueError, AttributeError):
            return False

    @property
    def days_overdue(self) -> float:
        """How many days past the scheduled review date. Negative = not yet due."""
        if not self.next_review_date:
            return -999.0
        try:
            next_dt = datetime.fromisoformat(self.next_review_date.replace("Z", "+00:00"))
            delta = (datetime.now(timezone.utc) - next_dt).total_seconds() / 86400
            return delta
        except (ValueError, AttributeError):
            return -999.0

    @property
    def estimated_recall(self) -> float:
        """Estimate current recall probability based on time since last review."""
        if not self.last_review_date:
            return 1.0  # Just mastered, assume full recall
        try:
            last_dt = datetime.fromisoformat(self.last_review_date.replace("Z", "+00:00"))
            days_elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds() / 86400
            # Exponential decay: R(t) = exp(-decay_rate * t / stability)
            recall = math.exp(-self.decay_rate * days_elapsed / max(0.1, self.stability))
            return max(0.0, min(1.0, recall))
        except (ValueError, AttributeError):
            return 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "stability": self.stability,
            "n_reviews": self.n_reviews,
            "n_successful": self.n_successful,
            "last_review_date": self.last_review_date,
            "next_review_date": self.next_review_date,
            "mastery_date": self.mastery_date,
            "decay_rate": self.decay_rate,
            "consecutive_successes": self.consecutive_successes,
            "review_history": self.review_history[-20:],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewSchedule":
        return cls(
            skill_id=data.get("skill_id", ""),
            stability=data.get("stability", BASE_STABILITY),
            n_reviews=data.get("n_reviews", 0),
            n_successful=data.get("n_successful", 0),
            last_review_date=data.get("last_review_date"),
            next_review_date=data.get("next_review_date"),
            mastery_date=data.get("mastery_date"),
            decay_rate=data.get("decay_rate", 0.35),
            consecutive_successes=data.get("consecutive_successes", 0),
            review_history=data.get("review_history", []),
        )


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------

def _get_skill_category(skill_id: str) -> str:
    """Determine the decay category for a skill."""
    if skill_id in SKILL_CATEGORY_OVERRIDES:
        return SKILL_CATEGORY_OVERRIDES[skill_id]

    node = PREREQUISITE_GRAPH.get(skill_id)
    if node:
        return DOMAIN_TO_CATEGORY.get(node.domain, "conceptual")
    return "conceptual"


def _compute_next_interval(stability: float, decay_rate: float) -> float:
    """Compute optimal review interval in days.

    The interval is when P(recall) drops to TARGET_RECALL (0.90).
    Solving: 0.90 = exp(-decay_rate * t / stability)
    → t = stability * (-ln(0.90)) / decay_rate
    """
    interval = stability * (-math.log(TARGET_RECALL)) / max(0.01, decay_rate)
    return max(MIN_INTERVAL_DAYS, min(MAX_INTERVAL_DAYS, interval))


def create_review_schedule(skill_id: str) -> ReviewSchedule:
    """Create a new review schedule when a skill is mastered.

    Called immediately after mastery confirmation.
    First review is scheduled at base_stability * factor.
    """
    category = _get_skill_category(skill_id)
    decay_rate = DECAY_RATES.get(category, 0.35)

    now = datetime.now(timezone.utc)
    first_interval = _compute_next_interval(BASE_STABILITY, decay_rate)
    next_review = now + timedelta(days=first_interval)

    schedule = ReviewSchedule(
        skill_id=skill_id,
        stability=BASE_STABILITY,
        decay_rate=decay_rate,
        mastery_date=now.isoformat(),
        last_review_date=now.isoformat(),
        next_review_date=next_review.isoformat(),
    )

    logger.info(
        f"REVIEW SCHEDULED: skill={skill_id}, category={category}, "
        f"decay_rate={decay_rate}, first_review_in={first_interval:.1f} days"
    )
    return schedule


def record_review_result(schedule: ReviewSchedule, success: bool) -> ReviewSchedule:
    """Update the schedule after a review attempt.

    Success (recalled correctly): stability increases, interval grows.
    Failure (forgot): stability decreases, interval shrinks.
    """
    now = datetime.now(timezone.utc)

    schedule.n_reviews += 1
    schedule.last_review_date = now.isoformat()

    if success:
        schedule.n_successful += 1
        schedule.consecutive_successes += 1
        # Stability grows with success — each review strengthens memory
        schedule.stability *= SUCCESS_MULTIPLIER
        # Bonus for consecutive successes (strong retention signal)
        if schedule.consecutive_successes >= 3:
            schedule.stability *= 1.1  # 10% extra stability for 3+ streaks
    else:
        schedule.consecutive_successes = 0
        # Stability drops on failure
        schedule.stability /= FAILURE_DIVISOR
        schedule.stability = max(BASE_STABILITY * 0.5, schedule.stability)

    # Compute next interval
    interval = _compute_next_interval(schedule.stability, schedule.decay_rate)
    schedule.next_review_date = (now + timedelta(days=interval)).isoformat()

    # Record in history
    schedule.review_history.append({
        "date": now.isoformat(),
        "success": success,
        "stability_after": round(schedule.stability, 2),
        "interval_days": round(interval, 1),
    })
    schedule.review_history = schedule.review_history[-20:]

    logger.info(
        f"REVIEW {'SUCCESS' if success else 'FAIL'}: skill={schedule.skill_id}, "
        f"stability={schedule.stability:.1f}, next_in={interval:.1f} days"
    )
    return schedule


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class SpacedReviewStore:
    """Manages review schedules for all students.

    Firestore path: users/{uid}/review_schedule/{skill_id}
    """

    def __init__(self):
        self._memory: Dict[str, Dict[str, ReviewSchedule]] = {}
        self._firestore_available = False
        self._db = None
        self._try_init_firestore()

    def _try_init_firestore(self):
        try:
            import firebase_admin
            from firebase_admin import firestore
            if firebase_admin._apps:
                self._db = firestore.client()
                self._firestore_available = True
                logger.info("SpacedReviewStore: Firestore connected")
        except Exception:
            logger.info("SpacedReviewStore: Using in-memory fallback")

    def get_schedule(self, user_id: str, skill_id: str) -> Optional[ReviewSchedule]:
        """Get review schedule for a skill. Returns None if not scheduled."""
        if user_id in self._memory and skill_id in self._memory[user_id]:
            return self._memory[user_id][skill_id]

        if self._firestore_available and self._db:
            try:
                doc = (
                    self._db.collection("users")
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
        """Get all skills that are due for review, sorted by urgency.

        Most overdue items come first.
        """
        all_schedules = self._get_all_schedules(user_id)
        due = [s for s in all_schedules.values() if s.is_due]
        due.sort(key=lambda s: s.days_overdue, reverse=True)  # Most overdue first
        return due[:max_items]

    def get_upcoming_reviews(self, user_id: str, days_ahead: int = 7) -> List[ReviewSchedule]:
        """Get reviews coming up in the next N days."""
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
        """Create and save a review schedule when a skill is mastered."""
        schedule = create_review_schedule(skill_id)
        self._save_schedule(user_id, schedule)
        return schedule

    def record_review(
        self, user_id: str, skill_id: str, success: bool
    ) -> Optional[ReviewSchedule]:
        """Record a review attempt result and update the schedule."""
        schedule = self.get_schedule(user_id, skill_id)
        if not schedule:
            return None

        record_review_result(schedule, success)
        self._save_schedule(user_id, schedule)
        return schedule

    def get_review_summary(self, user_id: str) -> Dict[str, Any]:
        """Summary for parent dashboard: what's been reviewed, what's due."""
        all_schedules = self._get_all_schedules(user_id)

        due_now = [s for s in all_schedules.values() if s.is_due]
        total_scheduled = len(all_schedules)
        avg_recall = sum(s.estimated_recall for s in all_schedules.values()) / max(1, total_scheduled)

        return {
            "total_mastered_skills": total_scheduled,
            "due_for_review": len(due_now),
            "average_recall": round(avg_recall, 2),
            "upcoming_7_days": len(self.get_upcoming_reviews(user_id, 7)),
            "skills_due": [
                {"skill_id": s.skill_id, "days_overdue": round(s.days_overdue, 1)}
                for s in due_now[:5]
            ],
        }

    def _get_all_schedules(self, user_id: str) -> Dict[str, ReviewSchedule]:
        """Load all review schedules for a user."""
        if user_id in self._memory:
            return self._memory[user_id]

        if self._firestore_available and self._db:
            try:
                docs = (
                    self._db.collection("users")
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
        """Persist a review schedule."""
        self._memory.setdefault(user_id, {})[schedule.skill_id] = schedule

        if self._firestore_available and self._db:
            try:
                (
                    self._db.collection("users")
                    .document(user_id)
                    .collection("review_schedule")
                    .document(schedule.skill_id)
                    .set(schedule.to_dict())
                )
            except Exception as e:
                logger.warning(f"Firestore write error: {e}")


# Singleton
spaced_review_store = SpacedReviewStore()
