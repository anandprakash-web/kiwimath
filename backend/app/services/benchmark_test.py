"""
Benchmark Test System — Structured diagnostic assessments with IRT equating.

Based on Vedantu's LPT (Learning Progress Test) methodology:
  - Baseline test at start of learning journey
  - Midline test after ~2 months
  - Endline test at end of term/year

Each benchmark test:
  1. Has fixed anchor items (for equating across test forms)
  2. Covers all competency levels (K/A/R) in balanced proportions
  3. Spans all topics at appropriate difficulty
  4. Produces scale scores comparable across time periods
  5. Generates a detailed diagnostic report

Equating method:
  - Fixed anchoring: 5-8 common items across baseline/midline/endline
  - These anchor items are never shown in regular practice sessions
  - Scale scores derived from 2PL IRT with fixed anchor parameters

Firestore paths:
  users/{uid}/benchmarks/{benchmark_id}  → test results
  benchmark_items/{grade}                → anchor item bank
"""

from __future__ import annotations

import logging
import math
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from app.services.proficiency_levels import (
    theta_to_scale_score,
    get_proficiency_level,
    get_proficiency_for_display,
)

logger = logging.getLogger("kiwimath.benchmark")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Number of questions per benchmark test
BENCHMARK_TEST_LENGTH = 20

# Anchor items: used for equating across test forms (never shown in practice)
ANCHOR_ITEMS_PER_TEST = 6

# Non-anchor items: selected to match student's approximate level
NON_ANCHOR_ITEMS = BENCHMARK_TEST_LENGTH - ANCHOR_ITEMS_PER_TEST

# Competency distribution for benchmark tests (balanced assessment)
COMPETENCY_TARGET = {
    'K': 0.40,  # 40% Knowing
    'A': 0.40,  # 40% Applying
    'R': 0.20,  # 20% Reasoning
}

# Time limit per question (seconds)
TIME_PER_QUESTION = 90

# Benchmark types
BENCHMARK_BASELINE = "baseline"
BENCHMARK_MIDLINE = "midline"
BENCHMARK_ENDLINE = "endline"
BENCHMARK_DIAGNOSTIC = "diagnostic"


# ---------------------------------------------------------------------------
# Anchor Item Bank
# ---------------------------------------------------------------------------

# Pre-selected anchor items per grade band.
# These items have stable, well-calibrated IRT parameters and are
# NEVER shown in regular practice sessions.
# In production, these would be loaded from Firestore after real calibration.
# For now, we select them from existing content based on criteria:
#   - Moderate difficulty (IRT_b close to 0)
#   - Good discrimination (IRT_a > 0.8)
#   - Balanced across topics

ANCHOR_SELECTION_CRITERIA = {
    'irt_b_range': (-1.0, 1.0),     # Moderate difficulty
    'irt_a_min': 0.8,                # Good discrimination
    'min_per_competency': 2,         # At least 2 K, 2 A, 2 R
}

# Grade-band mapping for Kangaroo topics (T1-T8).
# questions.json = G1-2 (difficulty 1-100), grade34 = G3-4 (101-200), g56 = G5-6 (201-300)
KANGAROO_GRADE_BANDS = {
    1: (1, 2),    # Grade 1 tests → G1-2 content
    2: (1, 2),    # Grade 2 tests → G1-2 content
    3: (3, 4),    # Grade 3 tests → G3-4 content
    4: (3, 4),    # Grade 4 tests → G3-4 content
    5: (5, 6),    # Grade 5 tests → G5-6 content
    6: (5, 6),    # Grade 6 tests → G5-6 content
}

# Difficulty score ranges that correspond to each grade band in Kangaroo topics
KANGAROO_DIFFICULTY_RANGES = {
    (1, 2): (1, 100),
    (3, 4): (101, 200),
    (5, 6): (201, 300),
}


def _grade_for_question(q: Dict) -> Optional[int]:
    """Infer the target grade of a question from its ID or difficulty.

    Returns the grade (1-6) or None if undetermined.

    Curriculum questions: ID contains -G{grade}- (e.g., NCERT-G3-001)
    Kangaroo topics: difficulty_score 1-100 → G1-2, 101-200 → G3-4, 201-300 → G5-6
    """
    import re
    qid = q.get('id', '')

    # Curriculum questions have grade in ID
    m = re.search(r'-G(\d)-', qid)
    if m:
        return int(m.group(1))

    # Kangaroo topics (T1-T8): use difficulty_score to infer grade band
    if re.match(r'^T\d-', qid):
        diff = q.get('difficulty_score', 0)
        if diff <= 100:
            return 1  # G1-2 band, return lower grade
        elif diff <= 200:
            return 3  # G3-4 band
        else:
            return 5  # G5-6 band

    return None


def _filter_questions_for_grade(all_questions: List[Dict], grade: int) -> List[Dict]:
    """Filter questions appropriate for a benchmark test at the given grade.

    For a grade N test, include:
    - Curriculum questions for grade N-1 and grade N (test what they should already
      know + what they're currently learning)
    - Kangaroo topic questions from the matching grade band

    This ensures a grade-2 child never sees grade-6 algebra, and the test
    covers both mastery of prior content and current-grade progress.
    """
    # Grades to include: current grade + one below (floor at 1)
    allowed_grades = {grade, max(1, grade - 1)}

    # For Kangaroo topics, also allow the full grade band
    band = KANGAROO_GRADE_BANDS.get(grade, (grade, grade))
    allowed_grades.update(range(band[0], band[1] + 1))

    filtered = []
    for q in all_questions:
        q_grade = _grade_for_question(q)
        if q_grade is None:
            # Unknown grade — skip for benchmarks (these are the ~3600 untagged questions)
            continue
        if q_grade in allowed_grades:
            filtered.append(q)

    return filtered


@dataclass
class AnchorItem:
    """A fixed anchor item used for test equating."""
    question_id: str
    irt_a: float
    irt_b: float
    irt_c: float
    competency: str
    topic: str


# ---------------------------------------------------------------------------
# Benchmark Test Builder
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkTest:
    """A structured diagnostic test."""
    benchmark_id: str
    benchmark_type: str  # baseline/midline/endline/diagnostic
    grade: int
    user_id: str
    question_ids: List[str]
    anchor_ids: List[str]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_type": self.benchmark_type,
            "grade": self.grade,
            "user_id": self.user_id,
            "question_ids": self.question_ids,
            "anchor_ids": self.anchor_ids,
            "total_questions": len(self.question_ids),
            "created_at": self.created_at,
        }


@dataclass
class BenchmarkResult:
    """Results from a completed benchmark test."""
    benchmark_id: str
    benchmark_type: str
    user_id: str
    grade: int
    theta: float
    scale_score: int
    level: int
    level_name: str
    total_questions: int
    correct: int
    accuracy: float
    time_taken_seconds: int
    competency_scores: Dict[str, Any]
    topic_scores: Dict[str, Any]
    completed_at: str
    responses: List[Dict]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_type": self.benchmark_type,
            "user_id": self.user_id,
            "grade": self.grade,
            "theta": self.theta,
            "scale_score": self.scale_score,
            "level": self.level,
            "level_name": self.level_name,
            "total_questions": self.total_questions,
            "correct": self.correct,
            "accuracy": round(self.accuracy, 3),
            "time_taken_seconds": self.time_taken_seconds,
            "competency_scores": self.competency_scores,
            "topic_scores": self.topic_scores,
            "completed_at": self.completed_at,
            "responses": self.responses,
        }


class BenchmarkTestService:
    """Manages benchmark test creation, scoring, and storage."""

    def __init__(self):
        self._db = None
        self._available = False
        self._anchor_cache: Dict[int, List[str]] = {}
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

    def create_benchmark_test(
        self,
        user_id: str,
        grade: int,
        benchmark_type: str,
        all_questions: List[Dict],
        exclude_ids: Set[str] = None,
    ) -> Optional[BenchmarkTest]:
        """Create a structured benchmark test.

        Selects questions to cover:
        - All competency levels (K/A/R) in target proportions
        - Multiple topics for broad coverage
        - Range of difficulties centered on expected grade level
        """
        exclude_ids = exclude_ids or set()
        benchmark_id = f"bm-{user_id[:8]}-{benchmark_type}-{int(time.time())}"

        # CRITICAL: Filter questions to only include grade-appropriate content.
        # Without this, a grade-1 child could receive grade-6 algebra questions.
        grade_questions = _filter_questions_for_grade(all_questions, grade)
        logger.info(
            f"Benchmark grade filter: grade={grade}, "
            f"total={len(all_questions)} → filtered={len(grade_questions)}"
        )

        # Select anchor items (fixed across test forms)
        anchor_ids = self._select_anchor_items(grade, grade_questions, exclude_ids)

        # Select non-anchor items (balanced by competency and topic)
        non_anchor_ids = self._select_balanced_items(
            grade, grade_questions,
            exclude_ids | set(anchor_ids),
            count=NON_ANCHOR_ITEMS,
        )

        all_test_ids = anchor_ids + non_anchor_ids

        # Graceful degradation: if the K/A/R blueprint couldn't fill all 20
        # slots (sparse competency/topic buckets in the grade-filtered pool),
        # top up from the nearest difficulty/competency bucket within the
        # allowed grades so the test is always BENCHMARK_TEST_LENGTH long
        # whenever the pool has enough questions.
        if len(all_test_ids) < BENCHMARK_TEST_LENGTH:
            all_test_ids = self._top_up_items(
                grade_questions, all_test_ids, exclude_ids, BENCHMARK_TEST_LENGTH
            )

        if len(all_test_ids) < BENCHMARK_TEST_LENGTH // 2:
            logger.warning(f"Not enough questions for benchmark test (got {len(all_test_ids)})")
            return None

        # Shuffle so anchors aren't clustered
        random.shuffle(all_test_ids)

        test = BenchmarkTest(
            benchmark_id=benchmark_id,
            benchmark_type=benchmark_type,
            grade=grade,
            user_id=user_id,
            question_ids=all_test_ids,
            anchor_ids=anchor_ids,
        )

        # Save to Firestore
        if self._available and self._db:
            try:
                self._db.document(f"users/{user_id}/benchmarks/{benchmark_id}").set(
                    test.to_dict()
                )
            except Exception as e:
                logger.warning(f"Failed to save benchmark test: {e}")

        return test

    def _select_anchor_items(
        self,
        grade: int,
        all_questions: List[Dict],
        exclude_ids: Set[str],
    ) -> List[str]:
        """Select anchor items for equating.

        Criteria: moderate difficulty, good discrimination, balanced competency.
        """
        b_min, b_max = ANCHOR_SELECTION_CRITERIA['irt_b_range']
        a_min = ANCHOR_SELECTION_CRITERIA['irt_a_min']

        candidates_by_comp = defaultdict(list)
        for q in all_questions:
            qid = q.get('id', '')
            if qid in exclude_ids:
                continue
            # Questions may carry irt_a/irt_b keys explicitly set to None
            # (Optional fields on QuestionV2) — treat None as default.
            irt_a = q.get('irt_a')
            irt_b = q.get('irt_b')
            irt_a = 1.0 if irt_a is None else irt_a
            irt_b = 0.0 if irt_b is None else irt_b
            comp = q.get('competency_level', 'K')

            if irt_a >= a_min and b_min <= irt_b <= b_max:
                candidates_by_comp[comp].append(qid)

        # Pick 2 per competency
        selected = []
        for comp in ['K', 'A', 'R']:
            pool = candidates_by_comp.get(comp, [])
            if pool:
                n = min(2, len(pool))
                selected.extend(random.sample(pool, n))

        return selected[:ANCHOR_ITEMS_PER_TEST]

    def _select_balanced_items(
        self,
        grade: int,
        all_questions: List[Dict],
        exclude_ids: Set[str],
        count: int,
    ) -> List[str]:
        """Select non-anchor items balanced by competency and topic."""
        # Target counts per competency
        k_count = round(count * COMPETENCY_TARGET['K'])
        a_count = round(count * COMPETENCY_TARGET['A'])
        r_count = count - k_count - a_count

        targets = {'K': k_count, 'A': a_count, 'R': r_count}

        # Group candidates by competency
        by_comp = defaultdict(list)
        for q in all_questions:
            qid = q.get('id', '')
            if qid in exclude_ids:
                continue
            comp = q.get('competency_level', 'K')
            by_comp[comp].append(q)

        selected = []
        for comp, target in targets.items():
            pool = by_comp.get(comp, [])
            if not pool:
                continue

            # Spread across topics
            by_topic = defaultdict(list)
            for q in pool:
                topic = q.get('topic', 'unknown')
                by_topic[topic].append(q)

            # Round-robin from each topic
            per_topic = max(1, target // max(1, len(by_topic)))
            for topic, qs in by_topic.items():
                # Sort by difficulty, pick spread
                qs_sorted = sorted(qs, key=lambda q: q.get('difficulty_score', 100))
                step = max(1, len(qs_sorted) // per_topic)
                picks = qs_sorted[::step][:per_topic]
                selected.extend(q.get('id', '') for q in picks)

                if len(selected) >= count:
                    break

        return selected[:count]

    def _top_up_items(
        self,
        pool: List[Dict],
        selected_ids: List[str],
        exclude_ids: Set[str],
        target_len: int,
    ) -> List[str]:
        """Fill remaining test slots from the nearest difficulty/competency bucket.

        Called when the strict K/A/R blueprint can't fill every slot from the
        grade-filtered pool. Prefers questions from under-represented
        competencies, breaking ties by proximity to the pool's median
        difficulty, so the filled test stays as close to the blueprint as
        the pool allows.
        """
        selected = list(selected_ids)
        taken = set(selected) | set(exclude_ids)
        remaining = [q for q in pool if q.get('id') and q.get('id') not in taken]
        if not remaining:
            return selected

        # Median difficulty of the grade pool as the anchor point
        diffs = sorted(q.get('difficulty_score', 100) for q in pool)
        median_diff = diffs[len(diffs) // 2]

        # Competency counts among the current selection
        by_id = {q.get('id'): q for q in pool}
        comp_counts: Dict[str, int] = defaultdict(int)
        for qid in selected:
            q = by_id.get(qid)
            if q:
                comp_counts[q.get('competency_level', 'K')] += 1

        while len(selected) < target_len and remaining:
            remaining.sort(key=lambda q: (
                comp_counts[q.get('competency_level', 'K')],
                abs(q.get('difficulty_score', 100) - median_diff),
            ))
            q = remaining.pop(0)
            selected.append(q['id'])
            comp_counts[q.get('competency_level', 'K')] += 1

        return selected

    def score_benchmark(
        self,
        user_id: str,
        benchmark_id: str,
        responses: List[Dict],
        all_questions: List[Dict],
        grade: int = 0,
    ) -> Optional[BenchmarkResult]:
        """Score a completed benchmark test using IRT.

        Uses Maximum Likelihood Estimation to compute theta from responses.
        """
        if not responses:
            return None

        # Build question lookup
        q_map = {q.get('id', ''): q for q in all_questions}

        # Compute correctness from selected_option if not already set
        for r in responses:
            if 'correct' not in r:
                q = q_map.get(r.get('question_id', ''), {})
                correct_ans = q.get('correct_answer', q.get('a', -1))
                selected = r.get('selected_option', -1)
                r['correct'] = (selected == correct_ans) if selected >= 0 else False

        # Compute theta using MLE
        theta = self._estimate_theta_mle(responses, q_map)
        scale = theta_to_scale_score(theta)
        pl = get_proficiency_level(theta)

        total = len(responses)
        correct = sum(1 for r in responses if r.get('correct', False))
        accuracy = correct / max(1, total)

        # Competency-wise scores
        comp_scores = defaultdict(lambda: {"correct": 0, "total": 0})
        for r in responses:
            q = q_map.get(r.get('question_id', ''), {})
            comp = q.get('competency_level', 'K')
            comp_scores[comp]["total"] += 1
            if r.get('correct'):
                comp_scores[comp]["correct"] += 1

        competency_scores = {}
        for comp in ['K', 'A', 'R']:
            s = comp_scores[comp]
            competency_scores[comp] = {
                "correct": s["correct"],
                "total": s["total"],
                "accuracy": round(s["correct"] / max(1, s["total"]) * 100, 1),
            }

        # Topic-wise scores
        topic_scores_raw = defaultdict(lambda: {"correct": 0, "total": 0})
        for r in responses:
            q = q_map.get(r.get('question_id', ''), {})
            topic = q.get('topic_name', q.get('topic', 'Unknown'))
            topic_scores_raw[topic]["total"] += 1
            if r.get('correct'):
                topic_scores_raw[topic]["correct"] += 1

        topic_scores = {}
        for topic, s in topic_scores_raw.items():
            topic_scores[topic] = {
                "correct": s["correct"],
                "total": s["total"],
                "accuracy": round(s["correct"] / max(1, s["total"]) * 100, 1),
            }

        time_taken = sum(r.get('time_ms', 0) for r in responses) // 1000

        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            benchmark_type=self._get_benchmark_type(user_id, benchmark_id),
            user_id=user_id,
            grade=grade,
            theta=round(theta, 4),
            scale_score=scale,
            level=pl.level,
            level_name=pl.name,
            total_questions=total,
            correct=correct,
            accuracy=accuracy,
            time_taken_seconds=time_taken,
            competency_scores=competency_scores,
            topic_scores=topic_scores,
            completed_at=datetime.now(timezone.utc).isoformat(),
            responses=responses,
        )

        # Save results
        self._save_result(user_id, result)

        return result

    def _estimate_theta_mle(
        self,
        responses: List[Dict],
        q_map: Dict[str, Dict],
    ) -> float:
        """Estimate student ability using Maximum Likelihood Estimation.

        Uses the 3PL model with Newton-Raphson iteration.
        """
        theta = 0.0  # Start at average ability

        for iteration in range(25):
            numerator = 0.0
            denominator = 0.0

            for r in responses:
                q = q_map.get(r.get('question_id', ''), {})
                a = q.get('irt_a')
                b = q.get('irt_b')
                c = q.get('irt_c')
                a = 1.0 if a is None else a
                b = 0.0 if b is None else b
                c = 0.25 if c is None else c
                correct = 1.0 if r.get('correct', False) else 0.0

                # P(correct | theta)
                exp_val = min(20, max(-20, -a * (theta - b)))
                p_star = 1.0 / (1.0 + math.exp(exp_val))
                p = c + (1 - c) * p_star

                # Derivatives for Newton-Raphson
                w = p_star * (1 - p_star)
                p_safe = max(1e-10, min(1 - 1e-10, p))

                info = a * (1 - c) * w
                numerator += a * (1 - c) * p_star * (correct - p) / p_safe
                denominator += info * info / (p_safe * (1 - p_safe))

            if abs(denominator) < 1e-10:
                break

            delta = numerator / denominator
            theta += delta

            if abs(delta) < 0.01:
                break

        return max(-3.5, min(3.5, theta))

    def _get_benchmark_type(self, user_id: str, benchmark_id: str) -> str:
        """Get the benchmark type from stored data."""
        if self._available and self._db:
            try:
                doc = self._db.document(f"users/{user_id}/benchmarks/{benchmark_id}").get()
                if doc.exists:
                    return doc.to_dict().get("benchmark_type", BENCHMARK_DIAGNOSTIC)
            except Exception:
                pass
        return BENCHMARK_DIAGNOSTIC

    def _save_result(self, user_id: str, result: BenchmarkResult) -> None:
        """Save benchmark result to Firestore."""
        if not self._available or not self._db:
            return
        try:
            self._db.document(
                f"users/{user_id}/benchmarks/{result.benchmark_id}"
            ).set(result.to_dict(), merge=True)
        except Exception as e:
            logger.warning(f"Failed to save benchmark result: {e}")

    def get_benchmark_history(self, user_id: str) -> List[Dict]:
        """Get all benchmark results for a user, ordered by time."""
        if not self._available or not self._db:
            return []

        try:
            docs = self._db.collection(f"users/{user_id}/benchmarks") \
                .where("completed_at", "!=", None) \
                .order_by("completed_at") \
                .get()
            return [doc.to_dict() for doc in docs if doc.to_dict().get("scale_score")]
        except Exception as e:
            logger.warning(f"Failed to load benchmark history: {e}")
            return []

    def get_growth_comparison(self, user_id: str) -> Dict[str, Any]:
        """Compare baseline vs latest benchmark for growth analysis."""
        history = self.get_benchmark_history(user_id)
        if len(history) < 2:
            return {
                "has_comparison": False,
                "message": "Complete at least 2 benchmark tests to see growth.",
                "benchmarks_completed": len(history),
            }

        baseline = history[0]
        latest = history[-1]

        scale_growth = latest.get('scale_score', 500) - baseline.get('scale_score', 500)
        level_growth = latest.get('level', 1) - baseline.get('level', 1)

        return {
            "has_comparison": True,
            "baseline": {
                "type": baseline.get('benchmark_type'),
                "scale_score": baseline.get('scale_score'),
                "level": baseline.get('level'),
                "level_name": baseline.get('level_name'),
                "accuracy": baseline.get('accuracy'),
                "date": baseline.get('completed_at'),
            },
            "latest": {
                "type": latest.get('benchmark_type'),
                "scale_score": latest.get('scale_score'),
                "level": latest.get('level'),
                "level_name": latest.get('level_name'),
                "accuracy": latest.get('accuracy'),
                "date": latest.get('completed_at'),
            },
            "growth": {
                "scale_score_change": scale_growth,
                "level_change": level_growth,
                "accuracy_change": round(
                    (latest.get('accuracy', 0) - baseline.get('accuracy', 0)) * 100, 1
                ),
            },
            "benchmarks_completed": len(history),
        }


# Singleton
benchmark_service = BenchmarkTestService()
