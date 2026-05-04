"""
Proficiency Level System — Map IRT theta to named student levels (L1-L6).

Based on the Vedantu Learning Outcomes framework, adapted for Kiwimath:
  L1: Explorer     (theta < -2.0)  — Just starting, building foundations
  L2: Builder      (theta -2.0 to -1.0) — Grasping basics, needs practice
  L3: Achiever     (theta -1.0 to 0.0)  — Solid on grade-level concepts
  L4: Star         (theta 0.0 to 1.0)   — Strong understanding, applies well
  L5: Champion     (theta 1.0 to 2.0)   — Advanced, reasons across topics
  L6: Legend       (theta > 2.0)    — Exceptional, olympiad-ready

Also provides:
  - Scale score transformation (logit → 500-based scale)
  - Growth tracking over time
  - Competency-wise (K/A/R) proficiency breakdown
  - Grade-appropriate descriptions for parent reports
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("kiwimath.proficiency")


# ---------------------------------------------------------------------------
# Scale Score Configuration (Vedantu standard: mean=500, SD=50)
# ---------------------------------------------------------------------------

SCALE_MEAN = 500
SCALE_SD = 50

# Theta reference points (from population)
THETA_MEAN = 0.0
THETA_SD = 1.0


def theta_to_scale_score(theta: float) -> int:
    """Transform IRT theta (logit) to a parent-friendly scale score.

    Linear transformation: scale = SCALE_MEAN + (theta - THETA_MEAN) / THETA_SD * SCALE_SD
    Clamped to [200, 800] range.
    """
    scale = SCALE_MEAN + (theta - THETA_MEAN) / THETA_SD * SCALE_SD
    return max(200, min(800, round(scale)))


def scale_score_to_theta(scale: int) -> float:
    """Inverse: convert scale score back to theta."""
    return THETA_MEAN + (scale - SCALE_MEAN) / SCALE_SD * THETA_SD


# ---------------------------------------------------------------------------
# Proficiency Levels
# ---------------------------------------------------------------------------

@dataclass
class ProficiencyLevel:
    """A named proficiency level with descriptions."""
    level: int           # 1-6
    name: str            # Kid-friendly name
    emoji: str           # Visual indicator
    theta_min: float     # Lower bound (inclusive)
    theta_max: float     # Upper bound (exclusive)
    scale_min: int       # Corresponding scale score min
    scale_max: int       # Corresponding scale score max
    color: str           # Hex color for UI

    # Grade-band descriptions
    description_g12: str   # Grades 1-2
    description_g34: str   # Grades 3-4
    description_g56: str   # Grades 5-6

    # What the student can do at this level
    can_do: List[str] = field(default_factory=list)

    # Recommended next steps
    next_steps: List[str] = field(default_factory=list)


PROFICIENCY_LEVELS: List[ProficiencyLevel] = [
    ProficiencyLevel(
        level=1, name="Explorer", emoji="🌱",
        theta_min=-4.0, theta_max=-2.0,
        scale_min=200, scale_max=400,
        color="#EF4444",
        description_g12="Your child is beginning their math journey. They're learning to recognize numbers and do simple counting.",
        description_g34="Your child is building foundational skills. They can handle some basic operations but need more practice with grade-level concepts.",
        description_g56="Your child is working on strengthening core skills. Some grade-level concepts need more attention.",
        can_do=[
            "Recognize numbers and basic shapes",
            "Count objects with guidance",
            "Attempt simple calculations",
        ],
        next_steps=[
            "Practice counting and number recognition daily",
            "Use hands-on objects (blocks, fingers) for calculations",
            "Focus on building confidence with easy problems first",
        ],
    ),
    ProficiencyLevel(
        level=2, name="Builder", emoji="🧱",
        theta_min=-2.0, theta_max=-1.0,
        scale_min=400, scale_max=450,
        color="#F59E0B",
        description_g12="Your child understands basic number concepts and can do simple addition and subtraction with support.",
        description_g34="Your child grasps most basic operations and is starting to apply them to simple word problems.",
        description_g56="Your child handles standard procedures but needs practice with multi-step problems and new contexts.",
        can_do=[
            "Perform basic calculations correctly",
            "Understand place value for small numbers",
            "Solve simple one-step problems",
        ],
        next_steps=[
            "Practice mental math with small numbers",
            "Try simple word problems with familiar contexts",
            "Work on number facts fluency (addition, subtraction)",
        ],
    ),
    ProficiencyLevel(
        level=3, name="Achiever", emoji="⭐",
        theta_min=-1.0, theta_max=0.0,
        scale_min=450, scale_max=500,
        color="#3B82F6",
        description_g12="Your child is solid with grade-level math! They can add, subtract, and solve simple word problems independently.",
        description_g34="Your child demonstrates good understanding of grade-level concepts and can apply them to familiar problems.",
        description_g56="Your child handles most grade-level content well and is starting to tackle multi-step challenges.",
        can_do=[
            "Solve grade-level problems independently",
            "Apply math to familiar real-world situations",
            "Explain basic problem-solving steps",
        ],
        next_steps=[
            "Challenge with slightly harder problems",
            "Introduce problems from unfamiliar contexts",
            "Encourage explaining solutions out loud",
        ],
    ),
    ProficiencyLevel(
        level=4, name="Star", emoji="🌟",
        theta_min=0.0, theta_max=1.0,
        scale_min=500, scale_max=550,
        color="#10B981",
        description_g12="Your child is excelling! They handle all grade-level math with confidence and can tackle above-level challenges.",
        description_g34="Your child demonstrates strong understanding across all topics and applies math to complex, multi-step problems.",
        description_g56="Your child is proficient across all areas and beginning to show reasoning skills with non-routine problems.",
        can_do=[
            "Solve complex multi-step problems",
            "Apply concepts to new, unfamiliar situations",
            "Show clear mathematical reasoning",
        ],
        next_steps=[
            "Try challenge-level and olympiad problems",
            "Work on explaining WHY solutions work",
            "Explore connections between different math topics",
        ],
    ),
    ProficiencyLevel(
        level=5, name="Champion", emoji="🏆",
        theta_min=1.0, theta_max=2.0,
        scale_min=550, scale_max=600,
        color="#8B5CF6",
        description_g12="Outstanding! Your child reasons mathematically beyond their grade level and loves solving challenging puzzles.",
        description_g34="Your child demonstrates advanced problem-solving skills and can analyze mathematical patterns and relationships.",
        description_g56="Your child excels at reasoning, generalization, and can handle olympiad-level challenges.",
        can_do=[
            "Analyze and solve non-routine problems",
            "Generalize patterns and create rules",
            "Justify solutions with mathematical reasoning",
        ],
        next_steps=[
            "Participate in math olympiad competitions",
            "Explore higher-grade concepts for enrichment",
            "Try open-ended investigation problems",
        ],
    ),
    ProficiencyLevel(
        level=6, name="Legend", emoji="👑",
        theta_min=2.0, theta_max=4.0,
        scale_min=600, scale_max=800,
        color="#EC4899",
        description_g12="Exceptional! Your child demonstrates mathematical thinking well beyond their grade — a true math prodigy!",
        description_g34="Exceptional! Your child masters advanced concepts and demonstrates deep mathematical reasoning at a remarkable level.",
        description_g56="Exceptional! Your child operates at a competitive math level with sophisticated reasoning and creative problem-solving.",
        can_do=[
            "Solve competition-level math problems",
            "Create and test mathematical conjectures",
            "Apply advanced reasoning across multiple domains",
        ],
        next_steps=[
            "Compete in national/international math olympiads",
            "Explore advanced topics (number theory, combinatorics)",
            "Consider math enrichment programs and mentorship",
        ],
    ),
]

# Quick lookup by level number
_LEVEL_MAP = {pl.level: pl for pl in PROFICIENCY_LEVELS}


def get_proficiency_level(theta: float) -> ProficiencyLevel:
    """Get the proficiency level for a given theta value."""
    for pl in PROFICIENCY_LEVELS:
        if theta < pl.theta_max:
            return pl
    return PROFICIENCY_LEVELS[-1]  # Legend


def get_proficiency_for_display(theta: float, grade: int = 0) -> Dict[str, Any]:
    """Get a parent-friendly proficiency summary.

    Returns a dict ready for API response with level details,
    scale score, and grade-appropriate description.
    """
    pl = get_proficiency_level(theta)
    scale = theta_to_scale_score(theta)

    # Pick grade-appropriate description
    if grade <= 2:
        description = pl.description_g12
    elif grade <= 4:
        description = pl.description_g34
    else:
        description = pl.description_g56

    # Calculate progress within current level (0-100%)
    level_range = pl.theta_max - pl.theta_min
    progress_in_level = (theta - pl.theta_min) / level_range if level_range > 0 else 0.5
    progress_pct = max(0, min(100, round(progress_in_level * 100)))

    return {
        "level": pl.level,
        "name": pl.name,
        "emoji": pl.emoji,
        "color": pl.color,
        "scale_score": scale,
        "theta": round(theta, 3),
        "description": description,
        "can_do": pl.can_do,
        "next_steps": pl.next_steps,
        "progress_in_level": progress_pct,
        "next_level_name": _LEVEL_MAP[pl.level + 1].name if pl.level < 6 else None,
        "theta_to_next_level": round(pl.theta_max - theta, 2) if pl.level < 6 else 0,
    }


# ---------------------------------------------------------------------------
# Competency-wise Proficiency
# ---------------------------------------------------------------------------

@dataclass
class CompetencyProfile:
    """Tracks performance per competency level (K/A/R)."""
    knowing_correct: int = 0
    knowing_total: int = 0
    applying_correct: int = 0
    applying_total: int = 0
    reasoning_correct: int = 0
    reasoning_total: int = 0

    @property
    def knowing_accuracy(self) -> float:
        return self.knowing_correct / max(1, self.knowing_total)

    @property
    def applying_accuracy(self) -> float:
        return self.applying_correct / max(1, self.applying_total)

    @property
    def reasoning_accuracy(self) -> float:
        return self.reasoning_correct / max(1, self.reasoning_total)

    def record(self, competency: str, correct: bool) -> None:
        """Record a response for a competency level."""
        if competency == 'K':
            self.knowing_total += 1
            if correct:
                self.knowing_correct += 1
        elif competency == 'A':
            self.applying_total += 1
            if correct:
                self.applying_correct += 1
        elif competency == 'R':
            self.reasoning_total += 1
            if correct:
                self.reasoning_correct += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API response."""
        return {
            "knowing": {
                "name": "Knowing",
                "short": "Recall & Compute",
                "correct": self.knowing_correct,
                "total": self.knowing_total,
                "accuracy": round(self.knowing_accuracy * 100, 1),
                "mastery": _competency_mastery(self.knowing_accuracy, self.knowing_total),
            },
            "applying": {
                "name": "Applying",
                "short": "Use & Solve",
                "correct": self.applying_correct,
                "total": self.applying_total,
                "accuracy": round(self.applying_accuracy * 100, 1),
                "mastery": _competency_mastery(self.applying_accuracy, self.applying_total),
            },
            "reasoning": {
                "name": "Reasoning",
                "short": "Analyze & Justify",
                "correct": self.reasoning_correct,
                "total": self.reasoning_total,
                "accuracy": round(self.reasoning_accuracy * 100, 1),
                "mastery": _competency_mastery(self.reasoning_accuracy, self.reasoning_total),
            },
        }

    def weakest_competency(self) -> Optional[str]:
        """Return the weakest competency that has enough data."""
        candidates = []
        if self.knowing_total >= 3:
            candidates.append(('K', self.knowing_accuracy))
        if self.applying_total >= 3:
            candidates.append(('A', self.applying_accuracy))
        if self.reasoning_total >= 3:
            candidates.append(('R', self.reasoning_accuracy))
        if not candidates:
            return None
        return min(candidates, key=lambda x: x[1])[0]

    def strongest_competency(self) -> Optional[str]:
        """Return the strongest competency that has enough data."""
        candidates = []
        if self.knowing_total >= 3:
            candidates.append(('K', self.knowing_accuracy))
        if self.applying_total >= 3:
            candidates.append(('A', self.applying_accuracy))
        if self.reasoning_total >= 3:
            candidates.append(('R', self.reasoning_accuracy))
        if not candidates:
            return None
        return max(candidates, key=lambda x: x[1])[0]


def _competency_mastery(accuracy: float, total: int) -> str:
    """Mastery label for a competency."""
    if total < 3:
        return "not_enough_data"
    if accuracy >= 0.85:
        return "mastered"
    if accuracy >= 0.65:
        return "developing"
    return "needs_practice"


# ---------------------------------------------------------------------------
# Growth Tracking
# ---------------------------------------------------------------------------

@dataclass
class GrowthSnapshot:
    """A point-in-time record of student ability for growth tracking."""
    timestamp: str       # ISO format
    theta: float
    scale_score: int
    level: int
    level_name: str
    total_questions: int
    accuracy: float      # 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "theta": self.theta,
            "scale_score": self.scale_score,
            "level": self.level,
            "level_name": self.level_name,
            "total_questions": self.total_questions,
            "accuracy": round(self.accuracy, 3),
        }


def create_growth_snapshot(
    theta: float,
    total_questions: int,
    accuracy: float,
) -> GrowthSnapshot:
    """Create a growth snapshot at the current moment."""
    pl = get_proficiency_level(theta)
    return GrowthSnapshot(
        timestamp=datetime.now(timezone.utc).isoformat(),
        theta=round(theta, 4),
        scale_score=theta_to_scale_score(theta),
        level=pl.level,
        level_name=pl.name,
        total_questions=total_questions,
        accuracy=accuracy,
    )


def calculate_growth(snapshots: List[Dict]) -> Dict[str, Any]:
    """Calculate growth metrics from a list of snapshots.

    Returns growth summary including:
    - scale score change
    - level change
    - growth rate (expected: 0.5 logits per academic year)
    - trajectory: improving / steady / declining
    """
    if len(snapshots) < 2:
        return {
            "has_growth_data": False,
            "message": "Need at least 2 data points to track growth.",
        }

    first = snapshots[0]
    latest = snapshots[-1]

    scale_change = latest.get('scale_score', 500) - first.get('scale_score', 500)
    theta_change = latest.get('theta', 0) - first.get('theta', 0)
    level_change = latest.get('level', 1) - first.get('level', 1)

    # Determine trajectory
    if len(snapshots) >= 3:
        recent_3 = snapshots[-3:]
        recent_thetas = [s.get('theta', 0) for s in recent_3]
        trend = recent_thetas[-1] - recent_thetas[0]
        if trend > 0.1:
            trajectory = "improving"
        elif trend < -0.1:
            trajectory = "declining"
        else:
            trajectory = "steady"
    else:
        trajectory = "improving" if theta_change > 0 else "steady" if theta_change == 0 else "declining"

    return {
        "has_growth_data": True,
        "scale_score_change": scale_change,
        "theta_change": round(theta_change, 3),
        "level_change": level_change,
        "trajectory": trajectory,
        "first_snapshot": first,
        "latest_snapshot": latest,
        "total_snapshots": len(snapshots),
        "message": _growth_message(scale_change, level_change, trajectory),
    }


def _growth_message(scale_change: int, level_change: int, trajectory: str) -> str:
    """Generate a parent-friendly growth message."""
    if trajectory == "improving":
        if level_change > 0:
            return f"Great progress! Your child moved up {level_change} level{'s' if level_change > 1 else ''} and gained {scale_change} points."
        elif scale_change > 10:
            return f"Growing steadily — up {scale_change} points! Keep it up."
        else:
            return "Making progress with consistent practice. Every session counts!"
    elif trajectory == "steady":
        return "Holding steady. A bit more practice each day will help push to the next level."
    else:
        return "Some concepts are challenging right now. Focused practice on weak areas will help."


# ---------------------------------------------------------------------------
# Firestore Integration
# ---------------------------------------------------------------------------

class ProficiencyStore:
    """Manages proficiency data in Firestore.

    Firestore paths:
      users/{uid}/proficiency/overall  → current level, scale score, competency profile
      users/{uid}/proficiency/growth   → list of growth snapshots
      users/{uid}/proficiency/topics/{topic_id} → per-topic competency profile
    """

    def __init__(self):
        self._db = None
        self._available = False
        self._cache: Dict[str, Dict] = {}
        self._init_firestore()

    def _init_firestore(self):
        try:
            import firebase_admin
            from firebase_admin import firestore as fs
            if not firebase_admin._apps:
                firebase_admin.initialize_app()
            self._db = fs.client()
            self._available = True
        except Exception as e:
            logger.warning(f"Proficiency store: Firestore unavailable: {e}")

    def get_proficiency(self, user_id: str, grade: int = 0) -> Dict[str, Any]:
        """Get current proficiency data for a user."""
        cache_key = f"{user_id}:overall"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = {"competency_profile": CompetencyProfile().to_dict()}

        if self._available and self._db:
            try:
                doc = self._db.document(f"users/{user_id}/proficiency/overall").get()
                if doc.exists:
                    data = doc.to_dict()
            except Exception as e:
                logger.warning(f"Failed to load proficiency for {user_id}: {e}")

        self._cache[cache_key] = data
        return data

    def update_proficiency(
        self,
        user_id: str,
        theta: float,
        grade: int,
        competency: str,
        correct: bool,
        topic_id: str = "",
        total_questions: int = 0,
        accuracy: float = 0.0,
    ) -> None:
        """Update proficiency after a response.

        Called after every answer to keep proficiency data current.
        """
        if not self._available or not self._db:
            return

        try:
            from google.cloud.firestore_v1 import ArrayUnion

            # Update overall proficiency
            prof_ref = self._db.document(f"users/{user_id}/proficiency/overall")
            pl = get_proficiency_level(theta)
            scale = theta_to_scale_score(theta)

            # Build update
            update = {
                "theta": round(theta, 4),
                "scale_score": scale,
                "level": pl.level,
                "level_name": pl.name,
                "grade": grade,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            # Update competency counts
            comp_key = {"K": "knowing", "A": "applying", "R": "reasoning"}.get(competency, "knowing")
            from google.cloud.firestore_v1 import Increment
            update[f"competency.{comp_key}.total"] = Increment(1)
            if correct:
                update[f"competency.{comp_key}.correct"] = Increment(1)

            prof_ref.set(update, merge=True)

            # Update per-topic competency if topic_id provided
            if topic_id:
                topic_ref = self._db.document(f"users/{user_id}/proficiency/topics/{topic_id}")
                topic_update = {
                    f"competency.{comp_key}.total": Increment(1),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                if correct:
                    topic_update[f"competency.{comp_key}.correct"] = Increment(1)
                topic_ref.set(topic_update, merge=True)

            # Clear cache
            self._cache.pop(f"{user_id}:overall", None)

        except Exception as e:
            logger.warning(f"Failed to update proficiency for {user_id}: {e}")

    def record_growth_snapshot(
        self,
        user_id: str,
        theta: float,
        total_questions: int,
        accuracy: float,
    ) -> None:
        """Record a growth snapshot. Call periodically (e.g., weekly or every 50 questions)."""
        if not self._available or not self._db:
            return

        try:
            snapshot = create_growth_snapshot(theta, total_questions, accuracy)
            from google.cloud.firestore_v1 import ArrayUnion

            growth_ref = self._db.document(f"users/{user_id}/proficiency/growth")
            growth_ref.set(
                {"snapshots": ArrayUnion([snapshot.to_dict()])},
                merge=True,
            )
        except Exception as e:
            logger.warning(f"Failed to record growth snapshot for {user_id}: {e}")

    def get_growth_data(self, user_id: str) -> Dict[str, Any]:
        """Get growth history and analysis for a user."""
        if not self._available or not self._db:
            return calculate_growth([])

        try:
            doc = self._db.document(f"users/{user_id}/proficiency/growth").get()
            if doc.exists:
                snapshots = doc.to_dict().get("snapshots", [])
                return calculate_growth(snapshots)
        except Exception as e:
            logger.warning(f"Failed to load growth data for {user_id}: {e}")

        return calculate_growth([])


# Singleton
proficiency_store = ProficiencyStore()
