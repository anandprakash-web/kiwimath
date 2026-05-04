"""
Skill Ability Store — Per-skill theta tracking for the adaptive engine.

Tracks ability estimates at the SKILL level (37 nodes) rather than
domain level (5 nodes). Each student has an independent theta for every
skill they've interacted with.

Firestore path: users/{uid}/skill_abilities/{skill_id}

This replaces the domain-level approximation in the unified session planner
with precise per-skill ability tracking, enabling accurate ZPD targeting
and mastery gating.

Research basis:
- Multidimensional IRT: tracking multiple latent dimensions improves precision
- BKT per-skill: each skill has independent mastery probability
- Time-weighted updates: response time modulates theta change magnitude
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from app.assessment.path_engine import PREREQUISITE_GRAPH, GRADE_EXPECTATIONS

logger = logging.getLogger("kiwimath.skill_ability")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_THETA = -1.5          # New skill starts moderately below average
LOGIT_MIN = -3.0
LOGIT_MAX = 3.0

# K-factor for per-skill updates (faster adaptation than domain-level)
K_INITIAL = 0.8              # First 3 responses on a skill
K_SETTLING = 0.5             # Responses 4-10
K_STABLE = 0.3               # 10+ responses
K_VETERAN = 0.2              # 25+ responses

# Mastery thresholds (research: sustained mastery across 2+ sessions)
MASTERY_ACCURACY_THRESHOLD = 0.80
MASTERY_MIN_RESPONSES = 5
MASTERY_MIN_SESSIONS = 2     # Must demonstrate across 2+ non-consecutive sessions

# Response time modifiers (research: 8-15% accuracy improvement)
RT_FAST_CORRECT_BOOST = 1.3   # Fast + correct → stronger evidence of mastery
RT_SLOW_CORRECT_DAMPEN = 0.7  # Slow + correct → less confident mastery
RT_FAST_WRONG_REDUCE = 0.5    # Fast + wrong → likely careless, reduce penalty
RT_SLOW_WRONG_FULL = 1.0      # Slow + wrong → genuine difficulty, full penalty

# Default median RT per difficulty tier (ms) — bootstrapped from population
DEFAULT_MEDIAN_RT = {
    "easy": 6000,       # Difficulty 1-100
    "medium": 10000,    # Difficulty 101-200
    "hard": 15000,      # Difficulty 201-300
}

# Transfer coefficients when a prereq is mastered
TRANSFER_DIRECT_PREREQ = 0.6
TRANSFER_TWO_HOP = 0.3
TRANSFER_SAME_DOMAIN = 0.2


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SkillAbility:
    """Tracks a student's ability for a single skill node."""
    skill_id: str
    theta: float = DEFAULT_THETA
    se: float = 1.0               # Standard error of estimate
    n_responses: int = 0
    n_correct: int = 0
    n_sessions: int = 0           # Distinct sessions with responses on this skill
    session_ids: List[str] = field(default_factory=list)  # Last 10 session IDs
    mastery_confirmed: bool = False
    mastery_date: Optional[str] = None
    mastery_sessions_count: int = 0   # Sessions where accuracy >= threshold
    last_response_time: Optional[str] = None
    last_session_accuracy: float = 0.0
    median_rt_ms: float = 0.0
    rt_history: List[int] = field(default_factory=list)  # Last 20 RTs
    history: List[Dict[str, Any]] = field(default_factory=list)  # Last 30 responses
    updated_at: str = ""

    @property
    def accuracy(self) -> float:
        return self.n_correct / max(1, self.n_responses)

    @property
    def difficulty_target(self) -> int:
        """Convert theta to difficulty score (1-300)."""
        # Linear map: theta -3 → difficulty 1, theta +3 → difficulty 300
        normalized = (self.theta - LOGIT_MIN) / (LOGIT_MAX - LOGIT_MIN)
        return max(1, min(300, int(normalized * 299 + 1)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "theta": self.theta,
            "se": self.se,
            "n_responses": self.n_responses,
            "n_correct": self.n_correct,
            "n_sessions": self.n_sessions,
            "session_ids": self.session_ids[-10:],
            "mastery_confirmed": self.mastery_confirmed,
            "mastery_date": self.mastery_date,
            "mastery_sessions_count": self.mastery_sessions_count,
            "last_response_time": self.last_response_time,
            "last_session_accuracy": self.last_session_accuracy,
            "median_rt_ms": self.median_rt_ms,
            "rt_history": self.rt_history[-20:],
            "history": self.history[-30:],
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillAbility":
        return cls(
            skill_id=data.get("skill_id", ""),
            theta=data.get("theta", DEFAULT_THETA),
            se=data.get("se", 1.0),
            n_responses=data.get("n_responses", 0),
            n_correct=data.get("n_correct", 0),
            n_sessions=data.get("n_sessions", 0),
            session_ids=data.get("session_ids", []),
            mastery_confirmed=data.get("mastery_confirmed", False),
            mastery_date=data.get("mastery_date"),
            mastery_sessions_count=data.get("mastery_sessions_count", 0),
            last_response_time=data.get("last_response_time"),
            last_session_accuracy=data.get("last_session_accuracy", 0.0),
            median_rt_ms=data.get("median_rt_ms", 0.0),
            rt_history=data.get("rt_history", []),
            history=data.get("history", []),
            updated_at=data.get("updated_at", ""),
        )


# ---------------------------------------------------------------------------
# Theta update logic
# ---------------------------------------------------------------------------

def _get_k_factor(n_responses: int) -> float:
    """Adaptive K-factor: decreases as more data is collected."""
    if n_responses < 3:
        return K_INITIAL
    elif n_responses < 10:
        return K_SETTLING
    elif n_responses < 25:
        return K_STABLE
    return K_VETERAN


def _compute_rt_modifier(
    correct: bool,
    response_time_ms: int,
    median_rt_ms: float,
    difficulty_score: int,
) -> float:
    """Compute response-time modifier for the theta update.

    Research: time-sensitive IRT improves prediction by 8-15%.
    Fast + correct = deeper mastery, bigger boost.
    Fast + wrong = careless error, reduced penalty.
    """
    if median_rt_ms <= 0:
        # No RT history — use default for difficulty tier
        if difficulty_score <= 100:
            median_rt_ms = DEFAULT_MEDIAN_RT["easy"]
        elif difficulty_score <= 200:
            median_rt_ms = DEFAULT_MEDIAN_RT["medium"]
        else:
            median_rt_ms = DEFAULT_MEDIAN_RT["hard"]

    is_fast = response_time_ms < median_rt_ms * 0.8
    is_slow = response_time_ms > median_rt_ms * 1.5

    if correct:
        if is_fast:
            return RT_FAST_CORRECT_BOOST  # 1.3×
        elif is_slow:
            return RT_SLOW_CORRECT_DAMPEN  # 0.7×
        return 1.0
    else:
        if is_fast:
            return RT_FAST_WRONG_REDUCE  # 0.5× — likely careless
        return RT_SLOW_WRONG_FULL  # 1.0× — genuine difficulty


def _irt_probability(theta: float, difficulty_b: float) -> float:
    """1PL IRT probability: P(correct | theta, b)."""
    return 1.0 / (1.0 + math.exp(-(theta - difficulty_b)))


def _difficulty_to_b(difficulty_score: int) -> float:
    """Convert difficulty_score (1-300) to IRT b parameter (logit scale)."""
    normalized = (difficulty_score - 1) / 299.0
    return LOGIT_MIN + normalized * (LOGIT_MAX - LOGIT_MIN)


def update_skill_theta(
    ability: SkillAbility,
    correct: bool,
    difficulty_score: int,
    response_time_ms: int = 0,
    session_id: str = "",
) -> SkillAbility:
    """Update a skill's theta after a response.

    Uses 1PL IRT with:
    - Adaptive K-factor (decreases with more data)
    - Response time modulation (fast/slow × correct/wrong)
    - Standard error reduction

    Returns updated SkillAbility (mutated in place).
    """
    b = _difficulty_to_b(difficulty_score)
    p_correct = _irt_probability(ability.theta, b)

    # Base update: observed - expected
    residual = (1.0 if correct else 0.0) - p_correct
    k = _get_k_factor(ability.n_responses)

    # Apply response time modifier
    rt_mod = 1.0
    if response_time_ms > 0:
        rt_mod = _compute_rt_modifier(
            correct, response_time_ms, ability.median_rt_ms, difficulty_score
        )

    # Theta update
    delta = k * residual * rt_mod
    ability.theta = max(LOGIT_MIN, min(LOGIT_MAX, ability.theta + delta))

    # Update SE (decreases with more observations)
    ability.se = max(0.1, ability.se * 0.95)

    # Update counts
    ability.n_responses += 1
    if correct:
        ability.n_correct += 1

    # Track session
    if session_id and (not ability.session_ids or ability.session_ids[-1] != session_id):
        ability.session_ids.append(session_id)
        ability.session_ids = ability.session_ids[-10:]
        ability.n_sessions += 1

    # Update RT tracking
    if response_time_ms > 0:
        ability.rt_history.append(response_time_ms)
        ability.rt_history = ability.rt_history[-20:]
        sorted_rt = sorted(ability.rt_history)
        ability.median_rt_ms = sorted_rt[len(sorted_rt) // 2]

    # Add to history
    now = datetime.now(timezone.utc).isoformat()
    ability.history.append({
        "correct": correct,
        "difficulty": difficulty_score,
        "theta_after": round(ability.theta, 3),
        "rt_ms": response_time_ms,
        "rt_mod": round(rt_mod, 2),
        "session_id": session_id,
        "time": now,
    })
    ability.history = ability.history[-30:]

    ability.last_response_time = now
    ability.updated_at = now

    return ability


# ---------------------------------------------------------------------------
# Mastery verification
# ---------------------------------------------------------------------------

def check_mastery(
    ability: SkillAbility,
    session_id: str,
    session_accuracy: float,
) -> bool:
    """Check if a skill has achieved sustained mastery.

    Research: mastery requires demonstration across multiple sessions.
    Single-session spikes don't indicate genuine learning.

    Criteria:
      1. Overall accuracy >= 80%
      2. At least 5 total responses
      3. Session accuracy >= 80% in at least 2 non-consecutive sessions
    """
    if ability.mastery_confirmed:
        return True  # Already mastered

    # Minimum responses
    if ability.n_responses < MASTERY_MIN_RESPONSES:
        return False

    # Overall accuracy check
    if ability.accuracy < MASTERY_ACCURACY_THRESHOLD:
        return False

    # Track this session's performance
    if session_accuracy >= MASTERY_ACCURACY_THRESHOLD:
        # Only count if this is a new session (not the same one)
        if not ability.session_ids or ability.session_ids[-1] != session_id:
            ability.mastery_sessions_count += 1
        elif ability.mastery_sessions_count == 0:
            ability.mastery_sessions_count = 1

    ability.last_session_accuracy = session_accuracy

    # Sustained mastery check
    if ability.mastery_sessions_count >= MASTERY_MIN_SESSIONS:
        ability.mastery_confirmed = True
        ability.mastery_date = datetime.now(timezone.utc).isoformat()
        logger.info(
            f"MASTERY CONFIRMED: skill={ability.skill_id}, "
            f"theta={ability.theta:.2f}, accuracy={ability.accuracy:.1%}, "
            f"sessions={ability.mastery_sessions_count}"
        )
        return True

    return False


# ---------------------------------------------------------------------------
# Transfer model
# ---------------------------------------------------------------------------

def compute_transfer_boost(
    mastered_skill_id: str,
    target_skill_id: str,
    mastered_theta: float,
) -> float:
    """Compute theta boost for a dependent skill when a prereq is mastered.

    Research: prerequisite mastery provides a warm-start prior to dependent skills.
    Direct prereqs get 0.6× transfer, 2-hop gets 0.3×, same-domain peers get 0.2×.
    """
    target_node = PREREQUISITE_GRAPH.get(target_skill_id)
    mastered_node = PREREQUISITE_GRAPH.get(mastered_skill_id)

    if not target_node or not mastered_node:
        return 0.0

    # Direct prerequisite
    if mastered_skill_id in (target_node.prerequisites or []):
        return mastered_theta * TRANSFER_DIRECT_PREREQ

    # 2-hop: mastered skill is a prereq of one of target's prereqs
    for prereq_id in (target_node.prerequisites or []):
        prereq_node = PREREQUISITE_GRAPH.get(prereq_id)
        if prereq_node and mastered_skill_id in (prereq_node.prerequisites or []):
            return mastered_theta * TRANSFER_TWO_HOP

    # Same domain peer
    if mastered_node.domain == target_node.domain:
        return mastered_theta * TRANSFER_SAME_DOMAIN

    return 0.0


def apply_transfer_on_mastery(
    user_abilities: Dict[str, SkillAbility],
    mastered_skill_id: str,
) -> List[str]:
    """When a skill is mastered, boost dependent skills that haven't been started.

    Returns list of skill_ids that received a boost.
    """
    mastered = user_abilities.get(mastered_skill_id)
    if not mastered:
        return []

    boosted = []
    for skill_id, node in PREREQUISITE_GRAPH.items():
        if skill_id == mastered_skill_id:
            continue

        # Only boost skills that haven't been interacted with much
        existing = user_abilities.get(skill_id)
        if existing and existing.n_responses > 3:
            continue  # Already has enough data — don't override

        boost = compute_transfer_boost(mastered_skill_id, skill_id, mastered.theta)
        if boost <= 0:
            continue

        if existing is None:
            existing = SkillAbility(skill_id=skill_id)
            user_abilities[skill_id] = existing

        # Only boost if it would improve the current estimate
        new_theta = max(existing.theta, boost)
        if new_theta > existing.theta:
            existing.theta = new_theta
            boosted.append(skill_id)
            logger.info(
                f"TRANSFER: {mastered_skill_id} → {skill_id}, "
                f"boost to theta={new_theta:.2f}"
            )

    return boosted


# ---------------------------------------------------------------------------
# Store (Firestore persistence + in-memory fallback)
# ---------------------------------------------------------------------------

class SkillAbilityStore:
    """Manages per-skill ability estimates for all students.

    Firestore path: users/{uid}/skill_abilities/{skill_id}
    Falls back to in-memory dict for local development.
    """

    def __init__(self):
        self._memory: Dict[str, Dict[str, SkillAbility]] = {}  # uid -> {skill_id -> ability}
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
                logger.info("SkillAbilityStore: Firestore connected")
        except Exception:
            logger.info("SkillAbilityStore: Using in-memory fallback")

    def get_skill_ability(self, user_id: str, skill_id: str) -> SkillAbility:
        """Get ability for a specific skill. Creates default if not exists."""
        # Check memory cache first
        if user_id in self._memory and skill_id in self._memory[user_id]:
            return self._memory[user_id][skill_id]

        # Try Firestore
        if self._firestore_available and self._db:
            try:
                doc = (
                    self._db.collection("users")
                    .document(user_id)
                    .collection("skill_abilities")
                    .document(skill_id)
                    .get()
                )
                if doc.exists:
                    ability = SkillAbility.from_dict(doc.to_dict())
                    self._memory.setdefault(user_id, {})[skill_id] = ability
                    return ability
            except Exception as e:
                logger.warning(f"Firestore read error: {e}")

        # Create default
        ability = SkillAbility(skill_id=skill_id)
        self._memory.setdefault(user_id, {})[skill_id] = ability
        return ability

    def get_all_abilities(self, user_id: str) -> Dict[str, SkillAbility]:
        """Get all skill abilities for a user."""
        # Try Firestore first for complete picture
        if self._firestore_available and self._db:
            try:
                docs = (
                    self._db.collection("users")
                    .document(user_id)
                    .collection("skill_abilities")
                    .stream()
                )
                abilities = {}
                for doc in docs:
                    ability = SkillAbility.from_dict(doc.to_dict())
                    abilities[ability.skill_id] = ability
                self._memory[user_id] = abilities
                return abilities
            except Exception as e:
                logger.warning(f"Firestore read all error: {e}")

        return self._memory.get(user_id, {})

    def save_skill_ability(self, user_id: str, ability: SkillAbility) -> None:
        """Persist a skill ability to Firestore."""
        self._memory.setdefault(user_id, {})[ability.skill_id] = ability

        if self._firestore_available and self._db:
            try:
                (
                    self._db.collection("users")
                    .document(user_id)
                    .collection("skill_abilities")
                    .document(ability.skill_id)
                    .set(ability.to_dict())
                )
            except Exception as e:
                logger.warning(f"Firestore write error: {e}")

    def record_response(
        self,
        user_id: str,
        skill_id: str,
        correct: bool,
        difficulty_score: int,
        response_time_ms: int = 0,
        session_id: str = "",
    ) -> SkillAbility:
        """Record a response and update the skill's theta.

        This is the main entry point called by the answer-check endpoint.
        Returns the updated ability.
        """
        ability = self.get_skill_ability(user_id, skill_id)

        # Update theta with time-weighted IRT
        update_skill_theta(
            ability,
            correct=correct,
            difficulty_score=difficulty_score,
            response_time_ms=response_time_ms,
            session_id=session_id,
        )

        # Persist
        self.save_skill_ability(user_id, ability)
        return ability

    def check_and_confirm_mastery(
        self,
        user_id: str,
        skill_id: str,
        session_id: str,
        session_accuracy: float,
    ) -> Optional[str]:
        """Check mastery and apply transfer if confirmed.

        Returns the skill_id if mastery was just confirmed, None otherwise.
        """
        ability = self.get_skill_ability(user_id, skill_id)

        was_mastered = ability.mastery_confirmed
        is_now_mastered = check_mastery(ability, session_id, session_accuracy)

        if is_now_mastered and not was_mastered:
            # NEW mastery event! Apply transfer to dependent skills
            all_abilities = self.get_all_abilities(user_id)
            boosted = apply_transfer_on_mastery(all_abilities, skill_id)

            # Save all boosted skills
            for boosted_id in boosted:
                self.save_skill_ability(user_id, all_abilities[boosted_id])

            # Save the mastered skill
            self.save_skill_ability(user_id, ability)
            return skill_id

        self.save_skill_ability(user_id, ability)
        return None

    def get_skill_progress(self, user_id: str, grade: int) -> Dict[str, Any]:
        """Get a summary of all skill progress for the parent dashboard.

        Returns per-skill theta, mastery status, and grade-level comparison.
        """
        abilities = self.get_all_abilities(user_id)
        skills_summary = []

        for skill_id, node in PREREQUISITE_GRAPH.items():
            if node.grade_level > grade + 1.5:
                continue

            ability = abilities.get(skill_id)
            expected = GRADE_EXPECTATIONS.get(node.domain, {}).get(grade, 0.0)

            if ability:
                status = "mastered" if ability.mastery_confirmed else (
                    "progressing" if ability.theta > expected - 0.5 else "needs_work"
                )
                skills_summary.append({
                    "skill_id": skill_id,
                    "skill_name": node.name,
                    "domain": node.domain,
                    "theta": round(ability.theta, 2),
                    "accuracy": round(ability.accuracy, 2),
                    "n_responses": ability.n_responses,
                    "mastery_confirmed": ability.mastery_confirmed,
                    "status": status,
                    "grade_gap": round(expected - ability.theta, 2),
                })
            else:
                skills_summary.append({
                    "skill_id": skill_id,
                    "skill_name": node.name,
                    "domain": node.domain,
                    "theta": DEFAULT_THETA,
                    "accuracy": 0.0,
                    "n_responses": 0,
                    "mastery_confirmed": False,
                    "status": "not_started",
                    "grade_gap": round(expected - DEFAULT_THETA, 2),
                })

        # Sort: needs_work first, then progressing, then mastered
        status_order = {"needs_work": 0, "not_started": 1, "progressing": 2, "mastered": 3}
        skills_summary.sort(key=lambda s: status_order.get(s["status"], 2))

        mastered_count = sum(1 for s in skills_summary if s["mastery_confirmed"])
        total_relevant = len(skills_summary)

        return {
            "user_id": user_id,
            "grade": grade,
            "mastered_skills": mastered_count,
            "total_skills": total_relevant,
            "mastery_percentage": round(mastered_count / max(1, total_relevant) * 100, 1),
            "skills": skills_summary,
        }

    def initialize_from_domain_theta(
        self,
        user_id: str,
        domain_thetas: Dict[str, float],
    ) -> None:
        """Bootstrap skill-level thetas from existing domain-level estimates.

        Called once during migration for existing users.
        """
        for skill_id, node in PREREQUISITE_GRAPH.items():
            existing = self.get_skill_ability(user_id, skill_id)
            if existing.n_responses > 0:
                continue  # Already has real data — don't overwrite

            domain_theta = domain_thetas.get(node.domain, DEFAULT_THETA)
            existing.theta = domain_theta
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            self.save_skill_ability(user_id, existing)


    # ------------------------------------------------------------------
    # Question History — tracks recently served question IDs per student
    # ------------------------------------------------------------------

    def get_recent_question_ids(self, user_id: str, max_ids: int = 100) -> set[str]:
        """Get recently served question IDs for deduplication across sessions.

        Firestore path: users/{uid}/question_history/recent
        Returns up to max_ids most recent question IDs.
        """
        # Check memory cache
        cache_key = f"_qhist_{user_id}"
        if cache_key in self._memory:
            ids = self._memory[cache_key]
            if isinstance(ids, set):
                return ids

        # Try Firestore
        if self._firestore_available and self._db:
            try:
                doc = (
                    self._db.collection("users")
                    .document(user_id)
                    .collection("question_history")
                    .document("recent")
                    .get()
                )
                if doc.exists:
                    data = doc.to_dict()
                    ids = set(data.get("question_ids", [])[-max_ids:])
                    self._memory[cache_key] = ids
                    return ids
            except Exception as e:
                logger.warning(f"Firestore question history read error: {e}")

        return set()

    def record_served_questions(self, user_id: str, question_ids: list[str]) -> None:
        """Record question IDs that were served in a session.

        Keeps a rolling window of the last 200 question IDs.
        Firestore path: users/{uid}/question_history/recent
        """
        cache_key = f"_qhist_{user_id}"
        existing = self.get_recent_question_ids(user_id)
        combined = list(existing) + question_ids
        # Keep last 200
        trimmed = combined[-200:]
        new_set = set(trimmed)
        self._memory[cache_key] = new_set

        if self._firestore_available and self._db:
            try:
                (
                    self._db.collection("users")
                    .document(user_id)
                    .collection("question_history")
                    .document("recent")
                    .set({
                        "question_ids": trimmed,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    })
                )
            except Exception as e:
                logger.warning(f"Firestore question history write error: {e}")


# Singleton
skill_ability_store = SkillAbilityStore()
