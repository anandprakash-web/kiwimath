"""
Kiwimath Adaptive Engine v2.1 — Behavioral Prediction Engine.

Based on the "Proof of Progress" (PoP) model. Extends ELO/IRT with
a Latency × Accuracy behavioral matrix that classifies each answer
into one of four cognitive states and applies state-specific interventions.

HOW IT WORKS
============

1. **Student ability (θ)**: Latent ability per topic on a logit scale.
   Maps to difficulty 1-100 for the content system. Starts at -3.0
   (difficulty 1) for new students.

2. **Rasch/1PL IRT probability model**:
      P(correct | θ, b) = 1 / (1 + exp(-(θ - b)))

3. **Latency × Accuracy Behavioral Matrix**:
   Each answer is classified into one of four cognitive states:

   ┌─────────────────────────────────────────────────────────────┐
   │                    FAST (<median)         SLOW (>median)    │
   │ CORRECT    "mastery" — confident      "struggle_win" —     │
   │            knows it cold               goldilocks zone,    │
   │            Action: step up, normal     Action: BIG reward   │
   │            reward                      multiplier (3×)      │
   │                                                             │
   │ WRONG      "guessing" — impulsive     "frustrated" —       │
   │            rushing through             cognitive overload   │
   │            Action: cooldown,           Action: drop diff,   │
   │            conceptual shift            trigger visual aid,  │
   │                                        airdrop reward       │
   └─────────────────────────────────────────────────────────────┘

4. **P(abandon) — Probability of Exit**:
   Computed from: wrong streak length, declining accuracy trend,
   rising latency trend, and session duration. When P(abandon) > 0.7,
   the engine triggers "airdrop" interventions: easier problems +
   bonus rewards to prevent churn.

5. **Flow State Equilibrium**:
      Engagement = (Variable_Reward × Perceived_Progress) / (Friction + Predictability)
   The engine continuously adjusts difficulty and reward timing to
   maintain the student in the Flow State zone (P(correct) ≈ 0.70-0.75).

6. **Variable Reward Schedule**:
   Replaces fixed XP with a variable ratio schedule. Reward multiplier
   depends on behavioral state:
   - mastery: 1.0× base XP
   - struggle_win: 3.0× base XP (reinforces productive struggle)
   - guessing: 0.5× base XP (discourages rushing)
   - frustrated: 1.5× base XP + visual scaffolding trigger

PERSISTENCE
===========
Student ability state is stored in Firestore under:
    users/{uid}/ability_v2/{topic_id}

Fields:
    theta: float        — current ability estimate (logit scale)
    attempts: int       — total questions answered
    correct: int        — total correct answers
    streak: int         — current streak (+correct, -wrong)
    behavioral_state: str — last classified state
    median_latency_ms: float — running median response time
    history: list       — last 50 entries with behavioral metadata
    updated_at: str     — ISO timestamp

The engine is stateless — all state is loaded/saved via Firestore.
In-memory fallback works for local dev.
"""

from __future__ import annotations

import logging
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("kiwimath.adaptive_v2")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Logit scale range: difficulty_score 1-100 maps to approximately -3.0 to +3.0
LOGIT_MIN = -3.0
LOGIT_MAX = 3.0

# Default starting ability (logit) — start at the very bottom for young children.
DEFAULT_THETA = -3.0

# K-factor schedule
K_INITIAL = 1.0       # First 5 questions: fast adaptation
K_SETTLING = 0.6      # Questions 6-20: settling in
K_STABLE = 0.4        # 20+ questions: stable updates
K_VETERAN = 0.25      # 50+ questions: very stable

# Target probability of correct answer (zone of proximal development).
TARGET_P_CORRECT = 0.72

# How many candidate questions to consider when selecting next question
CANDIDATE_POOL_SIZE = 8

# Maximum history entries to store per topic
MAX_HISTORY = 50

# Streak bonuses / penalties for adaptive adjustments
STREAK_CORRECT_BOOST = 0.15
STREAK_WRONG_CUSHION = 0.10

# Minimum questions before we trust the estimate
MIN_QUESTIONS_FOR_CONFIDENCE = 5

# ---------------------------------------------------------------------------
# Behavioral Matrix Constants (PoP Model)
# ---------------------------------------------------------------------------

# Latency thresholds (ms) — "fast" vs "slow" relative to running median.
# If no median yet, use these absolute defaults for Grade 1-2 (ages 6-8).
DEFAULT_FAST_THRESHOLD_MS = 8000   # <8s = "fast" for young children
DEFAULT_SLOW_THRESHOLD_MS = 8000   # >8s = "slow"

# Behavioral state names
STATE_MASTERY = "mastery"           # Fast + Correct — confident, knows it
STATE_GUESSING = "guessing"         # Fast + Wrong — impulsive, rushing
STATE_STRUGGLE_WIN = "struggle_win" # Slow + Correct — goldilocks zone!
STATE_FRUSTRATED = "frustrated"     # Slow + Wrong — cognitive overload

# Reward multipliers per behavioral state
REWARD_MULTIPLIER = {
    STATE_MASTERY: 1.0,       # Normal reward
    STATE_GUESSING: 0.5,      # Reduced — discourage rushing
    STATE_STRUGGLE_WIN: 3.0,  # MASSIVE — reinforce productive struggle
    STATE_FRUSTRATED: 1.5,    # Slightly elevated — compassion + keep engaged
}

# Theta adjustment modifiers per behavioral state (applied on top of ELO)
THETA_MODIFIER = {
    STATE_MASTERY: 0.10,      # Small extra bump up
    STATE_GUESSING: -0.15,    # Pull back — they're not actually learning
    STATE_STRUGGLE_WIN: 0.20, # Big bump — this is real growth
    STATE_FRUSTRATED: -0.20,  # Drop down significantly — they need easier
}

# P(abandon) thresholds
P_ABANDON_AIRDROP = 0.70     # Trigger interventions above this
P_ABANDON_CRITICAL = 0.85    # Emergency: maximum difficulty drop

# P(abandon) weights for computing abandonment probability
ABANDON_W_WRONG_STREAK = 0.35     # Weight of wrong-streak signal
ABANDON_W_ACCURACY_TREND = 0.25   # Weight of declining accuracy
ABANDON_W_LATENCY_TREND = 0.20    # Weight of increasing response times
ABANDON_W_SESSION_LENGTH = 0.20   # Weight of session fatigue

# Session fatigue: after this many questions in one session, fatigue kicks in
SESSION_FATIGUE_ONSET = 8
SESSION_FATIGUE_MAX = 20

# Content intervention flags
INTERVENTION_NONE = "none"
INTERVENTION_VISUAL_SCAFFOLD = "visual_scaffold"  # Switch to visual-heavy content
INTERVENTION_COOLDOWN = "cooldown"                 # Shift to different concept
INTERVENTION_AIRDROP = "airdrop"                   # Easy problem + bonus reward
INTERVENTION_BOSS_BATTLE = "boss_battle"           # Challenge for engaged students


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class StudentAbility:
    """Tracks a student's ability and behavioral state for a single topic."""
    topic_id: str
    theta: float = DEFAULT_THETA          # ability on logit scale
    attempts: int = 0                      # total questions answered
    correct: int = 0                       # total correct
    streak: int = 0                        # current consecutive correct (neg = wrong streak)
    behavioral_state: str = ""             # last classified behavioral state
    median_latency_ms: float = 0.0         # running median response time
    latency_history: List[int] = field(default_factory=list)  # recent latencies for median
    session_count: int = 0                 # questions answered in current session
    p_abandon: float = 0.0                 # last computed P(abandon)
    history: List[Dict[str, Any]] = field(default_factory=list)
    updated_at: str = ""

    @property
    def accuracy(self) -> float:
        """Overall accuracy ratio."""
        return self.correct / max(1, self.attempts)

    @property
    def recent_accuracy(self) -> float:
        """Accuracy over last 5 answers (for trend detection)."""
        recent = self.history[-5:]
        if not recent:
            return 0.5
        return sum(1 for h in recent if h.get("correct", False)) / len(recent)

    @property
    def accuracy_trend(self) -> float:
        """Slope of accuracy: positive = improving, negative = declining.
        Compares last-5 accuracy vs previous-5 accuracy."""
        if len(self.history) < 6:
            return 0.0
        recent_5 = self.history[-5:]
        prev_5 = self.history[-10:-5] if len(self.history) >= 10 else self.history[:5]
        recent_acc = sum(1 for h in recent_5 if h.get("correct")) / len(recent_5)
        prev_acc = sum(1 for h in prev_5 if h.get("correct")) / max(1, len(prev_5))
        return recent_acc - prev_acc

    @property
    def latency_trend(self) -> float:
        """Slope of latency: positive = slowing down, negative = speeding up."""
        if len(self.latency_history) < 4:
            return 0.0
        recent = self.latency_history[-3:]
        prev = self.latency_history[-6:-3] if len(self.latency_history) >= 6 else self.latency_history[:3]
        recent_avg = sum(recent) / len(recent)
        prev_avg = sum(prev) / max(1, len(prev))
        if prev_avg == 0:
            return 0.0
        return (recent_avg - prev_avg) / prev_avg  # relative change

    @property
    def k_factor(self) -> float:
        """Dynamic K-factor based on number of attempts."""
        if self.attempts < 5:
            return K_INITIAL
        elif self.attempts < 20:
            return K_SETTLING
        elif self.attempts < 50:
            return K_STABLE
        else:
            return K_VETERAN

    @property
    def confidence(self) -> str:
        """How confident we are in the ability estimate."""
        if self.attempts < MIN_QUESTIONS_FOR_CONFIDENCE:
            return "low"
        elif self.attempts < 20:
            return "medium"
        else:
            return "high"

    @property
    def difficulty_score(self) -> int:
        """Convert theta to difficulty_score (1-100) for the content system."""
        return theta_to_difficulty(self.theta)

    def update_median_latency(self, new_latency_ms: int) -> None:
        """Update the running median response time."""
        self.latency_history.append(new_latency_ms)
        # Keep last 20 latencies for the running median
        if len(self.latency_history) > 20:
            self.latency_history = self.latency_history[-20:]
        sorted_lat = sorted(self.latency_history)
        mid = len(sorted_lat) // 2
        if len(sorted_lat) % 2 == 0:
            self.median_latency_ms = (sorted_lat[mid - 1] + sorted_lat[mid]) / 2
        else:
            self.median_latency_ms = sorted_lat[mid]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for Firestore."""
        return {
            "topic_id": self.topic_id,
            "theta": round(self.theta, 4),
            "attempts": self.attempts,
            "correct": self.correct,
            "streak": self.streak,
            "behavioral_state": self.behavioral_state,
            "median_latency_ms": round(self.median_latency_ms, 0),
            "latency_history": self.latency_history[-20:],
            "p_abandon": round(self.p_abandon, 3),
            "history": self.history[-MAX_HISTORY:],
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StudentAbility":
        """Deserialize from Firestore."""
        return cls(
            topic_id=data.get("topic_id", ""),
            theta=data.get("theta", DEFAULT_THETA),
            attempts=data.get("attempts", 0),
            correct=data.get("correct", 0),
            streak=data.get("streak", 0),
            behavioral_state=data.get("behavioral_state", ""),
            median_latency_ms=data.get("median_latency_ms", 0.0),
            latency_history=data.get("latency_history", []),
            p_abandon=data.get("p_abandon", 0.0),
            history=data.get("history", []),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class AdaptiveResult:
    """Result of processing an answer through the adaptive engine."""
    correct: bool
    old_theta: float
    new_theta: float
    old_difficulty: int   # difficulty_score 1-100
    new_difficulty: int   # recommended next difficulty_score
    p_correct: float      # predicted probability before answer
    k_factor: float       # K used for this update
    streak: int           # current streak after this answer
    confidence: str       # low/medium/high
    accuracy: float       # overall accuracy
    # Behavioral matrix fields (PoP model)
    behavioral_state: str = ""             # mastery/guessing/struggle_win/frustrated
    reward_multiplier: float = 1.0         # XP multiplier for this answer
    p_abandon: float = 0.0                # probability of user quitting
    intervention: str = INTERVENTION_NONE  # recommended intervention
    latency_class: str = "normal"          # fast/slow classification

    @property
    def theta_change(self) -> float:
        return self.new_theta - self.old_theta


# ---------------------------------------------------------------------------
# Scale conversions
# ---------------------------------------------------------------------------

def difficulty_to_theta(difficulty_score: int) -> float:
    """Convert difficulty_score (1-100) to logit scale (-3.0 to +3.0)."""
    # Linear mapping: 1 → -3.0, 100 → +3.0
    return LOGIT_MIN + (difficulty_score - 1) / 99.0 * (LOGIT_MAX - LOGIT_MIN)


def theta_to_difficulty(theta: float) -> int:
    """Convert logit scale (-3.0 to +3.0) to difficulty_score (1-100)."""
    # Inverse of difficulty_to_theta
    score = 1 + (theta - LOGIT_MIN) / (LOGIT_MAX - LOGIT_MIN) * 99.0
    return max(1, min(100, round(score)))


# ---------------------------------------------------------------------------
# IRT probability model
# ---------------------------------------------------------------------------

def p_correct(theta: float, b: float) -> float:
    """Rasch model: probability of correct answer.

    Args:
        theta: student ability (logit scale)
        b: question difficulty (logit scale)

    Returns:
        Probability between 0 and 1.
    """
    exponent = theta - b
    # Clamp to prevent overflow
    exponent = max(-10, min(10, exponent))
    return 1.0 / (1.0 + math.exp(-exponent))


def information(theta: float, b: float) -> float:
    """Fisher information at this theta/b combination.

    Higher information = more useful question for estimating ability.
    Maximum information occurs when theta = b (P = 0.5).
    """
    p = p_correct(theta, b)
    return p * (1 - p)


# ---------------------------------------------------------------------------
# Core adaptive engine
# ---------------------------------------------------------------------------

class AdaptiveEngineV2:
    """ELO/IRT adaptive engine for v2 content."""

    def __init__(self):
        # In-memory ability cache (uid:topic_id -> StudentAbility)
        self._abilities: Dict[str, StudentAbility] = {}

    def _cache_key(self, user_id: str, topic_id: str) -> str:
        return f"{user_id}:{topic_id}"

    def get_ability(self, user_id: str, topic_id: str) -> StudentAbility:
        """Get or create a student's ability for a topic.

        In production, this loads from Firestore on first access.
        """
        key = self._cache_key(user_id, topic_id)
        if key in self._abilities:
            return self._abilities[key]

        # Try loading from Firestore
        ability = self._load_from_firestore(user_id, topic_id)
        if ability is None:
            ability = StudentAbility(topic_id=topic_id)

        self._abilities[key] = ability
        return ability

    def process_answer(
        self,
        user_id: str,
        topic_id: str,
        question_id: str,
        question_difficulty: int,  # 1-100
        is_correct: bool,
        time_taken_ms: int = 0,
    ) -> AdaptiveResult:
        """Process an answer using the PoP behavioral prediction model.

        Steps:
        1. Classify behavioral state (Latency × Accuracy matrix)
        2. Compute expected probability P(correct)
        3. Apply ELO update with behavioral modifier
        4. Compute P(abandon) — probability of user quitting
        5. Determine intervention (airdrop, scaffold, cooldown, etc.)
        6. Compute recommended next difficulty

        Args:
            user_id: Student identifier
            topic_id: Topic the question belongs to
            question_id: The question that was answered
            question_difficulty: Difficulty score 1-100
            is_correct: Whether the answer was correct
            time_taken_ms: Time taken to answer in milliseconds

        Returns:
            AdaptiveResult with behavioral metadata.
        """
        ability = self.get_ability(user_id, topic_id)
        old_theta = ability.theta
        ability.session_count += 1

        # ── Step 1: Classify behavioral state ──────────────────────
        beh_state, latency_class = self._classify_behavior(
            ability, is_correct, time_taken_ms
        )
        ability.behavioral_state = beh_state

        # Update latency tracking
        if time_taken_ms > 0:
            ability.update_median_latency(time_taken_ms)

        # ── Step 2: Compute expected probability ───────────────────
        b = difficulty_to_theta(question_difficulty)
        p_exp = p_correct(ability.theta, b)
        outcome = 1.0 if is_correct else 0.0

        # ── Step 3: ELO update with behavioral modifier ────────────
        K = ability.k_factor
        delta = K * (outcome - p_exp)

        # Streak adjustments
        if is_correct:
            ability.streak = max(0, ability.streak) + 1
            if ability.streak >= 3:
                delta += STREAK_CORRECT_BOOST * (1.0 - p_exp)
        else:
            ability.streak = min(0, ability.streak) - 1
            if ability.streak <= -2:
                delta -= STREAK_WRONG_CUSHION * p_exp

        # Apply behavioral state modifier (the key PoP innovation)
        state_mod = THETA_MODIFIER.get(beh_state, 0.0)
        delta += state_mod

        # Apply update
        new_theta = ability.theta + delta
        new_theta = max(LOGIT_MIN - 0.5, min(LOGIT_MAX + 0.5, new_theta))

        # Update ability state
        ability.theta = new_theta
        ability.attempts += 1
        if is_correct:
            ability.correct += 1

        # ── Step 4: Compute P(abandon) ─────────────────────────────
        p_abn = self._compute_p_abandon(ability)
        ability.p_abandon = p_abn

        # ── Step 5: Determine intervention ─────────────────────────
        intervention = self._determine_intervention(
            beh_state, p_abn, ability
        )

        # ── Step 6: Compute recommended next difficulty ────────────
        # If P(abandon) is high, override target difficulty downward
        if p_abn >= P_ABANDON_CRITICAL:
            # Emergency: drop to well below current ability
            next_theta_target = new_theta - 1.5
        elif p_abn >= P_ABANDON_AIRDROP:
            # Airdrop: drop moderately below current ability
            next_theta_target = new_theta - 0.8
        elif beh_state == STATE_GUESSING:
            # Guessing: shift to slightly different difficulty range
            next_theta_target = self._target_difficulty_theta(new_theta) - 0.3
        elif beh_state == STATE_MASTERY and ability.streak >= 5:
            # Hot streak mastery: push up more aggressively ("boss battle")
            next_theta_target = self._target_difficulty_theta(new_theta) + 0.3
        else:
            # Normal flow-state targeting
            next_theta_target = self._target_difficulty_theta(new_theta)

        next_difficulty = theta_to_difficulty(next_theta_target)

        # Get reward multiplier
        reward_mult = REWARD_MULTIPLIER.get(beh_state, 1.0)
        # Bonus multiplier for struggle_win during P(abandon) > threshold
        # (the "airdrop" reward boost from the PoP model)
        if p_abn >= P_ABANDON_AIRDROP and is_correct:
            reward_mult *= 1.5  # Extra boost when they succeed despite frustration

        # Record in history (with behavioral metadata)
        from datetime import datetime, timezone
        ability.history.append({
            "qid": question_id,
            "correct": is_correct,
            "difficulty": question_difficulty,
            "p_expected": round(p_exp, 3),
            "theta_before": round(old_theta, 4),
            "theta_after": round(new_theta, 4),
            "time_ms": time_taken_ms,
            "behavioral_state": beh_state,
            "latency_class": latency_class,
            "p_abandon": round(p_abn, 3),
            "reward_mult": round(reward_mult, 2),
            "intervention": intervention,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

        # Trim history
        if len(ability.history) > MAX_HISTORY:
            ability.history = ability.history[-MAX_HISTORY:]

        ability.updated_at = datetime.now(timezone.utc).isoformat()

        # Persist
        self._save_to_firestore(user_id, topic_id, ability)

        return AdaptiveResult(
            correct=is_correct,
            old_theta=old_theta,
            new_theta=new_theta,
            old_difficulty=theta_to_difficulty(old_theta),
            new_difficulty=next_difficulty,
            p_correct=p_exp,
            k_factor=K,
            streak=ability.streak,
            confidence=ability.confidence,
            accuracy=ability.accuracy,
            behavioral_state=beh_state,
            reward_multiplier=reward_mult,
            p_abandon=p_abn,
            intervention=intervention,
            latency_class=latency_class,
        )

    def recommend_difficulty(self, user_id: str, topic_id: str) -> int:
        """Get the recommended starting difficulty for a new session.

        Returns difficulty_score (1-100).
        """
        ability = self.get_ability(user_id, topic_id)

        if ability.attempts == 0:
            # Brand new student: always start at easiest (difficulty 1).
            # The high K-factor will ramp them up quickly if they get it right.
            return 1

        if ability.attempts < MIN_QUESTIONS_FOR_CONFIDENCE:
            # Still calibrating: use current estimate but lean easier
            target_theta = ability.theta - 0.5
        else:
            target_theta = self._target_difficulty_theta(ability.theta)

        return max(1, theta_to_difficulty(target_theta))

    def select_question(
        self,
        user_id: str,
        topic_id: str,
        available_questions: list,
        exclude_ids: Optional[List[str]] = None,
        exclude_clusters: Optional[List[str]] = None,
        seen_clusters: Optional[Dict[str, int]] = None,
        max_per_cluster: int = 2,
    ) -> Optional[Any]:
        """Select the optimal next question with cluster-aware deduplication.

        Uses information-theoretic selection + concept cluster diversity:
        - Picks questions closest to P(correct) ≈ TARGET_P_CORRECT
        - Penalizes questions from clusters already seen in the session
        - Fully excludes clusters the kid has mastered (answered correctly)

        Args:
            user_id: Student identifier
            topic_id: Topic to select from
            available_questions: List of QuestionV2 objects
            exclude_ids: Question IDs to skip
            exclude_clusters: Clusters to fully skip (mastered patterns)
            seen_clusters: Dict of cluster -> times_seen for soft limiting
            max_per_cluster: Max questions from same cluster per session

        Returns:
            Best question, or None if no candidates.
        """
        ability = self.get_ability(user_id, topic_id)
        exclude = set(exclude_ids or [])
        excluded_clusters = set(exclude_clusters or [])
        cluster_counts = dict(seen_clusters or {})

        # Also exclude recently-answered questions from history
        recent_qids = {h["qid"] for h in ability.history[-20:]}
        exclude = exclude | recent_qids

        pool = [q for q in available_questions if q.id not in exclude]
        if not pool:
            pool = [q for q in available_questions if q.id not in set(exclude_ids or [])]
        if not pool:
            return None

        # Partition into preferred (fresh clusters) and over-limit
        preferred = []
        over_limit = []
        for q in pool:
            cluster = getattr(q, 'concept_cluster', None)
            if cluster and cluster in excluded_clusters:
                over_limit.append(q)
            elif cluster and cluster_counts.get(cluster, 0) >= max_per_cluster:
                over_limit.append(q)
            else:
                preferred.append(q)

        # Use preferred pool if available, otherwise fall back
        active_pool = preferred if preferred else over_limit if over_limit else pool

        # Target difficulty on logit scale
        target_b = self._target_difficulty_theta(ability.theta)

        # Score each question: IRT fitness + cluster diversity bonus
        scored = []
        for q in active_pool:
            q_theta = difficulty_to_theta(q.difficulty_score)
            q_p = p_correct(ability.theta, q_theta)
            p_distance = abs(q_p - TARGET_P_CORRECT)
            q_info = information(ability.theta, q_theta)
            # Base score: lower is better
            score = p_distance - 0.1 * q_info

            # Cluster diversity bonus: penalize questions from already-seen clusters
            cluster = getattr(q, 'concept_cluster', None)
            if cluster:
                times_seen = cluster_counts.get(cluster, 0)
                # Each repeat adds 0.15 penalty (significant but not overwhelming)
                score += times_seen * 0.15

            scored.append((score, q))

        # Sort by score (best first) and pick from top candidates
        scored.sort(key=lambda x: x[0])
        top_n = min(CANDIDATE_POOL_SIZE, len(scored))
        candidates = [q for _, q in scored[:top_n]]

        # Weighted random selection: favor better-scored candidates
        weights = []
        for i in range(len(candidates)):
            weights.append(math.exp(-0.5 * i))

        total = sum(weights)
        weights = [w / total for w in weights]

        r = random.random()
        cumsum = 0.0
        for i, w in enumerate(weights):
            cumsum += w
            if r <= cumsum:
                return candidates[i]
        return candidates[-1]

    def get_student_summary(self, user_id: str, topic_id: str) -> Dict[str, Any]:
        """Get a summary of student's ability for a topic.

        Useful for dashboards and parent reports.
        """
        ability = self.get_ability(user_id, topic_id)
        return {
            "topic_id": topic_id,
            "ability_score": ability.difficulty_score,
            "theta": round(ability.theta, 3),
            "attempts": ability.attempts,
            "correct": ability.correct,
            "accuracy": round(ability.accuracy * 100, 1),
            "streak": ability.streak,
            "confidence": ability.confidence,
            "recommended_difficulty": self.recommend_difficulty(user_id, topic_id),
            "recent_history": ability.history[-10:],
        }

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _classify_behavior(
        self,
        ability: StudentAbility,
        is_correct: bool,
        time_taken_ms: int,
    ) -> Tuple[str, str]:
        """Classify the answer into one of four behavioral states.

        Uses the Latency × Accuracy matrix:
            Fast + Correct  → mastery    (confident, knows it)
            Fast + Wrong    → guessing   (impulsive, rushing)
            Slow + Correct  → struggle_win (productive struggle — goldilocks!)
            Slow + Wrong    → frustrated  (cognitive overload)

        "Fast" vs "slow" is determined relative to the student's own running
        median response time. For new students (fewer than 3 data points),
        we fall back to the absolute DEFAULT_FAST_THRESHOLD_MS.

        Args:
            ability: Current student ability state.
            is_correct: Whether this answer was correct.
            time_taken_ms: Response time in milliseconds.

        Returns:
            Tuple of (behavioral_state, latency_class).
            latency_class is "fast", "slow", or "unknown" (if no timing data).
        """
        # If no timing data, we can't classify latency — fall back to a
        # simplified correctness-only classification.
        if time_taken_ms <= 0:
            state = STATE_MASTERY if is_correct else STATE_FRUSTRATED
            return state, "unknown"

        # Determine the fast/slow threshold.
        # Use the student's own median if we have enough data points;
        # otherwise use the age-appropriate absolute default.
        if ability.median_latency_ms > 0 and len(ability.latency_history) >= 3:
            threshold = ability.median_latency_ms
        else:
            threshold = DEFAULT_FAST_THRESHOLD_MS

        # Classify latency. A 10% dead-zone around the median avoids noisy
        # flipping when response time is right at the boundary.
        if time_taken_ms < threshold * 0.9:
            latency_class = "fast"
        elif time_taken_ms > threshold * 1.1:
            latency_class = "slow"
        else:
            # In the dead-zone — lean toward the less dramatic state
            latency_class = "fast" if is_correct else "slow"

        # 2×2 matrix lookup
        if is_correct and latency_class == "fast":
            return STATE_MASTERY, latency_class
        elif not is_correct and latency_class == "fast":
            return STATE_GUESSING, latency_class
        elif is_correct and latency_class == "slow":
            return STATE_STRUGGLE_WIN, latency_class
        else:
            return STATE_FRUSTRATED, latency_class

    def _compute_p_abandon(self, ability: StudentAbility) -> float:
        """Compute the probability that the student is about to quit.

        Uses four weighted signals:
          1. Wrong-streak length  (weight 0.35)
          2. Accuracy trend       (weight 0.25)
          3. Latency trend        (weight 0.20)
          4. Session fatigue      (weight 0.20)

        Each signal is normalised to [0, 1] where 1 = maximum abandonment
        risk, then combined with the configured weights.

        Returns:
            Float in [0, 1]. Values above P_ABANDON_AIRDROP (0.70) trigger
            interventions; above P_ABANDON_CRITICAL (0.85) triggers emergency
            difficulty drops.
        """
        # ── Signal 1: Wrong streak ────────────────────────────────────
        # streak is negative when the student is on a wrong streak.
        # 1 wrong → 0.2, 2 wrong → 0.5, 3 wrong → 0.75, 4+ → ~0.95
        wrong_streak = max(0, -ability.streak)
        if wrong_streak == 0:
            s_streak = 0.0
        elif wrong_streak == 1:
            s_streak = 0.2
        elif wrong_streak == 2:
            s_streak = 0.5
        elif wrong_streak == 3:
            s_streak = 0.75
        else:
            # Asymptotic approach to 1.0
            s_streak = min(1.0, 0.75 + 0.05 * (wrong_streak - 3))

        # ── Signal 2: Accuracy trend ──────────────────────────────────
        # accuracy_trend is (recent_5_acc - prev_5_acc), range roughly -1 to +1.
        # A negative trend means the student is getting worse → higher risk.
        trend = ability.accuracy_trend
        if trend >= 0:
            s_accuracy = 0.0  # Improving or stable — no risk signal
        else:
            # Normalise: -0.4 decline → risk 0.5, -0.8 → risk 1.0
            s_accuracy = min(1.0, abs(trend) / 0.8)

        # ── Signal 3: Latency trend ───────────────────────────────────
        # latency_trend is (recent_avg - prev_avg) / prev_avg, a relative change.
        # Positive = slowing down → higher risk.
        lat_trend = ability.latency_trend
        if lat_trend <= 0:
            s_latency = 0.0  # Getting faster — no risk
        else:
            # 50% slower → risk 0.5, 100% slower → risk 1.0
            s_latency = min(1.0, lat_trend / 1.0)

        # ── Signal 4: Session fatigue ─────────────────────────────────
        # After SESSION_FATIGUE_ONSET questions, fatigue builds linearly
        # to max at SESSION_FATIGUE_MAX questions.
        if ability.session_count <= SESSION_FATIGUE_ONSET:
            s_fatigue = 0.0
        else:
            fatigue_range = SESSION_FATIGUE_MAX - SESSION_FATIGUE_ONSET
            excess = ability.session_count - SESSION_FATIGUE_ONSET
            s_fatigue = min(1.0, excess / max(1, fatigue_range))

        # ── Weighted combination ──────────────────────────────────────
        p_abn = (
            ABANDON_W_WRONG_STREAK * s_streak
            + ABANDON_W_ACCURACY_TREND * s_accuracy
            + ABANDON_W_LATENCY_TREND * s_latency
            + ABANDON_W_SESSION_LENGTH * s_fatigue
        )

        return round(min(1.0, max(0.0, p_abn)), 3)

    def _determine_intervention(
        self,
        beh_state: str,
        p_abandon: float,
        ability: StudentAbility,
    ) -> str:
        """Decide which intervention (if any) to apply.

        Decision tree:
          1. P(abandon) ≥ CRITICAL  → airdrop (emergency easy question + reward)
          2. P(abandon) ≥ AIRDROP   → airdrop or visual_scaffold (based on state)
          3. frustrated state        → visual_scaffold (show a worked example)
          4. guessing state          → cooldown (switch concept, slow them down)
          5. mastery streak ≥ 5      → boss_battle (challenge them!)
          6. Otherwise               → none

        Args:
            beh_state: The classified behavioral state.
            p_abandon: The computed P(abandon) value.
            ability: The current student ability state.

        Returns:
            One of the INTERVENTION_* constants.
        """
        # Critical abandonment risk — always airdrop
        if p_abandon >= P_ABANDON_CRITICAL:
            return INTERVENTION_AIRDROP

        # High abandonment risk — state-specific intervention
        if p_abandon >= P_ABANDON_AIRDROP:
            if beh_state == STATE_FRUSTRATED:
                return INTERVENTION_VISUAL_SCAFFOLD
            return INTERVENTION_AIRDROP

        # State-specific interventions (when P(abandon) is below threshold)
        if beh_state == STATE_FRUSTRATED:
            # Two frustrated answers in a row → visual scaffold
            if len(ability.history) >= 2:
                prev_state = ability.history[-1].get("behavioral_state", "")
                if prev_state == STATE_FRUSTRATED:
                    return INTERVENTION_VISUAL_SCAFFOLD
            return INTERVENTION_NONE

        if beh_state == STATE_GUESSING:
            # Three guesses in a row → cooldown (switch to different concept area)
            guess_run = 0
            for h in reversed(ability.history[-5:]):
                if h.get("behavioral_state") == STATE_GUESSING:
                    guess_run += 1
                else:
                    break
            if guess_run >= 2:  # current + 2 prev = 3 in a row
                return INTERVENTION_COOLDOWN
            return INTERVENTION_NONE

        if beh_state == STATE_MASTERY and ability.streak >= 5:
            return INTERVENTION_BOSS_BATTLE

        return INTERVENTION_NONE

    def _target_difficulty_theta(self, theta: float) -> float:
        """Find the question difficulty (logit) where P(correct) = TARGET_P_CORRECT.

        From the Rasch model:
            P = 1 / (1 + exp(-(θ - b)))
            => b = θ - ln(P / (1-P))
            => b = θ + ln((1-P) / P)

        With TARGET_P_CORRECT = 0.72:
            b = θ + ln(0.28 / 0.72)
            b = θ + ln(0.389)
            b ≈ θ - 0.944
        """
        # This gives us a question slightly easier than the student's ability
        # so they succeed ~72% of the time.
        target_b = theta + math.log((1 - TARGET_P_CORRECT) / TARGET_P_CORRECT)
        return target_b

    def _load_from_firestore(self, user_id: str, topic_id: str) -> Optional[StudentAbility]:
        """Load ability from Firestore."""
        try:
            from app.services.firestore_service import _get_db, is_firestore_available
            if not is_firestore_available():
                return None

            db = _get_db()
            if not db:
                return None

            doc = (db.collection("users").document(user_id)
                   .collection("ability_v2").document(topic_id).get())
            if doc.exists:
                return StudentAbility.from_dict(doc.to_dict())
            return None
        except Exception as e:
            logger.warning(f"Failed to load ability for {user_id}/{topic_id}: {e}")
            return None

    def _save_to_firestore(self, user_id: str, topic_id: str, ability: StudentAbility) -> None:
        """Save ability to Firestore."""
        try:
            from app.services.firestore_service import _get_db, is_firestore_available
            if not is_firestore_available():
                return

            db = _get_db()
            if not db:
                return

            (db.collection("users").document(user_id)
             .collection("ability_v2").document(topic_id)
             .set(ability.to_dict(), merge=True))
        except Exception as e:
            logger.warning(f"Failed to save ability for {user_id}/{topic_id}: {e}")


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

engine_v2 = AdaptiveEngineV2()
