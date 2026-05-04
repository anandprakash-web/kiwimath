"""
Auto-Remedial Engine — Targeted concept repair when students struggle.

Based on Vedantu's Learning Outcomes remedial methodology:
When a student gets a Knowledge-tagged question wrong, they have a concept gap.
The engine automatically generates a mini-remedial session to address it.

Remedial flow:
  1. Student answers a K-tagged question wrong
  2. Engine identifies the concept gap (from question tags + topic)
  3. Selects 2-3 easier questions on the SAME concept
  4. Inserts them as a "concept boost" before continuing
  5. Tracks remedial success rate

This is more targeted than just lowering difficulty — it specifically
addresses the foundational gap before moving on.

Firestore path: users/{uid}/remedial_history/{auto_id}
"""

from __future__ import annotations

import logging
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("kiwimath.remedial")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# How many remedial questions to insert per concept gap
REMEDIAL_QUESTIONS_PER_GAP = 3

# Maximum remedials per session (avoid frustration)
MAX_REMEDIALS_PER_SESSION = 2

# Cooldown: don't remediate the same concept within N questions
CONCEPT_COOLDOWN = 15

# Only trigger remedial for K-tagged questions (concept gaps)
# A and R wrong answers get normal difficulty adjustment instead
REMEDIAL_COMPETENCY_LEVELS = {'K'}

# Difficulty reduction for remedial questions (pick easier ones)
REMEDIAL_DIFFICULTY_REDUCTION = 0.6  # Select at 60% of failed question's difficulty


# ---------------------------------------------------------------------------
# Concept Mapping
# ---------------------------------------------------------------------------

# Map tags to broader concept groups for remedial targeting
CONCEPT_GROUPS = {
    # Arithmetic
    'addition': 'addition_basics',
    'addition-carry': 'addition_basics',
    'subtraction': 'subtraction_basics',
    'subtraction-borrow': 'subtraction_basics',
    'multiplication': 'multiplication_basics',
    'multiplication-table': 'multiplication_basics',
    'division': 'division_basics',
    'division-remainder': 'division_basics',
    'missing-number': 'number_operations',

    # Number Sense
    'place-value': 'place_value',
    'number-recognition': 'number_sense',
    'counting': 'number_sense',
    'skip-counting': 'number_sense',
    'before-after': 'number_sequence',
    'ordering': 'number_sequence',
    'comparison': 'number_comparison',
    'even-odd': 'number_properties',
    'rounding': 'number_estimation',
    'estimation': 'number_estimation',

    # Fractions & Decimals
    'fractions-basic': 'fractions',
    'fractions-equivalent': 'fractions',
    'fractions-comparison': 'fractions',
    'fractions-operations': 'fractions',
    'decimals': 'decimals',
    'decimals-operations': 'decimals',
    'percentage': 'percentage',

    # Geometry
    'shapes-identify': 'shapes',
    'shapes-properties': 'shapes',
    'area': 'measurement_area',
    'perimeter': 'measurement_perimeter',
    'volume': 'measurement_volume',
    'angles': 'angles',
    'symmetry': 'symmetry',

    # Measurement
    'time-reading': 'time',
    'time-calculation': 'time',
    'money-identification': 'money',
    'money-calculation': 'money',
    'measurement-units': 'measurement_units',
    'conversion': 'unit_conversion',
    'length': 'measurement_length',
    'weight': 'measurement_weight',
    'capacity': 'measurement_capacity',

    # Data
    'data-reading': 'data_handling',
    'graph-reading': 'data_handling',
    'tally': 'data_handling',
    'pictograph': 'data_handling',
    'bar-graph': 'data_handling',

    # Patterns
    'pattern': 'patterns',
    'pattern-number': 'patterns',
    'pattern-shape': 'patterns',
    'pattern-rule': 'patterns',
    'sequence': 'patterns',
}


def identify_concept(question: Dict) -> str:
    """Identify the core concept being tested by a question.

    Uses tags, topic, and stem analysis to determine the concept group.
    """
    tags = set(t.lower() for t in (question.get('tags') or []))
    topic = (question.get('topic') or '').lower()

    # Check tag-based concept mapping
    for tag in tags:
        if tag in CONCEPT_GROUPS:
            return CONCEPT_GROUPS[tag]

    # Fallback: use topic-based mapping
    topic_concept_map = {
        'arithmetic': 'number_operations',
        'counting': 'number_sense',
        'patterns': 'patterns',
        'logic': 'logical_reasoning',
        'spatial': 'spatial_reasoning',
        'shapes': 'shapes',
        'word_problems': 'word_problem_strategy',
        'puzzles': 'puzzle_solving',
        'measurement': 'measurement_units',
        'geometry': 'shapes',
        'fractions': 'fractions',
        'decimals': 'decimals',
        'data': 'data_handling',
        'time': 'time',
        'money': 'money',
    }

    for key, concept in topic_concept_map.items():
        if key in topic:
            return concept

    return 'general_math'


# ---------------------------------------------------------------------------
# Remedial Session Generator
# ---------------------------------------------------------------------------

@dataclass
class RemedialSession:
    """A mini-session of easier questions targeting a specific concept gap."""
    concept: str
    triggered_by_question_id: str
    question_ids: List[str]
    difficulty_target: int
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept": self.concept,
            "triggered_by": self.triggered_by_question_id,
            "question_ids": self.question_ids,
            "difficulty_target": self.difficulty_target,
            "created_at": self.created_at,
        }


class RemedialEngine:
    """Generates targeted remedial mini-sessions when students struggle.

    Integrates with the session planner to inject remedial questions
    at the right moment.
    """

    def __init__(self):
        self._session_remedial_count: Dict[str, int] = {}
        self._concept_cooldowns: Dict[str, Dict[str, int]] = {}  # user -> concept -> last_q_index
        self._db = None
        self._available = False
        self._init_firestore()

    def _init_firestore(self):
        try:
            import firebase_admin
            from firebase_admin import firestore as fs
            if not firebase_admin._apps:
                firebase_admin.initialize_app()
            self._db = fs.client()
            self._available = True
        except Exception:
            self._available = False

    def should_trigger_remedial(
        self,
        user_id: str,
        question: Dict,
        correct: bool,
        session_question_index: int,
    ) -> bool:
        """Determine if a remedial session should be triggered.

        Returns True if:
        1. The student got a K-tagged question wrong
        2. Haven't exceeded max remedials this session
        3. Haven't remediated this concept recently (cooldown)
        """
        if correct:
            return False

        # Only trigger for Knowledge-level questions
        competency = question.get('competency_level', '')
        if competency not in REMEDIAL_COMPETENCY_LEVELS:
            return False

        # Check session limit
        session_key = f"{user_id}:{int(time.time() // 3600)}"
        current_count = self._session_remedial_count.get(session_key, 0)
        if current_count >= MAX_REMEDIALS_PER_SESSION:
            return False

        # Check concept cooldown
        concept = identify_concept(question)
        user_cooldowns = self._concept_cooldowns.get(user_id, {})
        last_index = user_cooldowns.get(concept, -100)
        if session_question_index - last_index < CONCEPT_COOLDOWN:
            return False

        return True

    def generate_remedial(
        self,
        user_id: str,
        failed_question: Dict,
        all_questions: List[Dict],
        used_ids: Set[str],
        session_question_index: int,
    ) -> Optional[RemedialSession]:
        """Generate a remedial session targeting the concept gap.

        Selects easier questions on the same concept that the student
        hasn't seen recently.
        """
        concept = identify_concept(failed_question)
        failed_difficulty = failed_question.get('difficulty_score', 100)
        target_difficulty = int(failed_difficulty * REMEDIAL_DIFFICULTY_REDUCTION)

        # Find candidate questions: same concept, easier, not used
        candidates = []
        for q in all_questions:
            qid = q.get('id', '')
            if qid in used_ids or qid == failed_question.get('id'):
                continue
            if q.get('competency_level') != 'K':
                continue

            q_concept = identify_concept(q)
            if q_concept != concept:
                continue

            q_diff = q.get('difficulty_score', 100)
            if q_diff > failed_difficulty:
                continue

            # Prefer questions closer to target difficulty
            diff_distance = abs(q_diff - target_difficulty)
            candidates.append((q, diff_distance))

        if not candidates:
            # Fallback: any easier question in the same topic
            topic = failed_question.get('topic', '')
            for q in all_questions:
                qid = q.get('id', '')
                if qid in used_ids or qid == failed_question.get('id'):
                    continue
                if q.get('topic', '') != topic:
                    continue
                q_diff = q.get('difficulty_score', 100)
                if q_diff < failed_difficulty:
                    candidates.append((q, abs(q_diff - target_difficulty)))

        if len(candidates) < 2:
            return None

        # Sort by distance to target difficulty, pick best
        candidates.sort(key=lambda x: x[1])
        selected = [c[0] for c in candidates[:REMEDIAL_QUESTIONS_PER_GAP]]

        # Record cooldown and session count
        session_key = f"{user_id}:{int(time.time() // 3600)}"
        self._session_remedial_count[session_key] = \
            self._session_remedial_count.get(session_key, 0) + 1

        if user_id not in self._concept_cooldowns:
            self._concept_cooldowns[user_id] = {}
        self._concept_cooldowns[user_id][concept] = session_question_index

        remedial = RemedialSession(
            concept=concept,
            triggered_by_question_id=failed_question.get('id', ''),
            question_ids=[q.get('id', '') for q in selected],
            difficulty_target=target_difficulty,
        )

        # Log to Firestore
        self._log_remedial(user_id, remedial)

        logger.info(
            f"Remedial triggered for {user_id}: concept={concept}, "
            f"triggered_by={failed_question.get('id')}, "
            f"remedial_questions={remedial.question_ids}"
        )

        return remedial

    def _log_remedial(self, user_id: str, remedial: RemedialSession) -> None:
        """Log remedial session to Firestore for analytics."""
        if not self._available or not self._db:
            return
        try:
            self._db.collection(f"users/{user_id}/remedial_history").add(
                remedial.to_dict()
            )
        except Exception as e:
            logger.warning(f"Failed to log remedial: {e}")

    def record_remedial_result(
        self,
        user_id: str,
        remedial_question_id: str,
        correct: bool,
        concept: str,
    ) -> None:
        """Record how the student did on a remedial question."""
        if not self._available or not self._db:
            return
        try:
            self._db.collection(f"users/{user_id}/remedial_results").add({
                "question_id": remedial_question_id,
                "correct": correct,
                "concept": concept,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.warning(f"Failed to record remedial result: {e}")

    def get_remedial_stats(self, user_id: str) -> Dict[str, Any]:
        """Get remedial effectiveness stats for a user."""
        if not self._available or not self._db:
            return {"available": False}

        try:
            docs = self._db.collection(f"users/{user_id}/remedial_results") \
                .order_by("timestamp") \
                .limit(200) \
                .get()

            results = [doc.to_dict() for doc in docs]
            if not results:
                return {"available": True, "total_remedials": 0}

            total = len(results)
            correct = sum(1 for r in results if r.get("correct"))

            # Group by concept
            concept_stats = defaultdict(lambda: {"correct": 0, "total": 0})
            for r in results:
                c = r.get("concept", "unknown")
                concept_stats[c]["total"] += 1
                if r.get("correct"):
                    concept_stats[c]["correct"] += 1

            return {
                "available": True,
                "total_remedials": total,
                "remedial_accuracy": round(correct / max(1, total) * 100, 1),
                "concepts_remediated": len(concept_stats),
                "concept_breakdown": {
                    k: {
                        "accuracy": round(v["correct"] / max(1, v["total"]) * 100, 1),
                        "total": v["total"],
                    }
                    for k, v in concept_stats.items()
                },
            }

        except Exception as e:
            logger.warning(f"Failed to get remedial stats: {e}")
            return {"available": False}


# Singleton
remedial_engine = RemedialEngine()
