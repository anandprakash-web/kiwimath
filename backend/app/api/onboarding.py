"""
Onboarding API — diagnostic benchmark test (Task #196).

Endpoints:
    GET  /v2/onboarding/benchmark/questions  → fetch a 10-question diagnostic set
    POST /v2/onboarding/benchmark            → submit answers, get ability profile

The benchmark spans all 8 topics with a difficulty curve (easy → medium → hard
sampling) so we can quickly estimate the student's starting ability without
overwhelming a brand-new user.

After submission, results are pushed through the adaptive engine so subsequent
`/v2/questions/next` calls start at the right difficulty for each topic.
"""

from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.services.adaptive_engine_v2 import (
    DEFAULT_THETA,
    LOGIT_MAX,
    LOGIT_MIN,
    difficulty_to_theta,
    engine_v2,
    p_correct,
    theta_to_difficulty,
)
from app.services.content_store_v2 import _QUESTION_ID_RE, store_v2
from app.services.firestore_service import update_user_profile
from app.services.question_history import question_history

router = APIRouter(prefix="/v2/onboarding", tags=["v2-onboarding"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class BenchmarkAnswer(BaseModel):
    """One graded answer from the benchmark quiz."""
    question_id: str
    selected_answer: int = Field(..., ge=0, le=3)
    time_taken_ms: int = Field(default=0, ge=0)

    @field_validator("question_id")
    @classmethod
    def validate_qid(cls, v: str) -> str:
        if not _QUESTION_ID_RE.match(v):
            raise ValueError(f"Invalid question_id '{v}'")
        return v


class BenchmarkSubmitRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    grade: int = Field(..., ge=1, le=6)
    answers: List[BenchmarkAnswer] = Field(..., min_length=1, max_length=20)


class TopicAbility(BaseModel):
    topic_id: str
    topic_name: str
    ability_score: int            # 1-100
    recommended_difficulty: int   # 1-100
    correct: int
    attempts: int


class BenchmarkResult(BaseModel):
    user_id: str
    grade: int
    total_questions: int
    total_correct: int
    overall_accuracy: float                # 0..100
    estimated_ability: int                 # overall difficulty 1-100
    recommended_starting_difficulty: int   # 1-100 — the safe starting point
    suggested_topics: List[str]            # topic_ids ordered: weakest first
    strengths: List[str]                   # topic_ids where student excelled
    per_topic: List[TopicAbility]


# ---------------------------------------------------------------------------
# Difficulty band per grade — wider than the standard grade filter so we can
# sample easy / medium / hard for diagnostic purposes.
# ---------------------------------------------------------------------------

_BENCHMARK_BAND = {
    1: (1, 50),
    2: (1, 100),
    3: (50, 150),    # extends into Grade 3-4 content (Task #191)
    4: (75, 175),
    5: (100, 200),
    6: (150, 250),
}


def _band_for_grade(grade: int) -> tuple[int, int]:
    return _BENCHMARK_BAND.get(grade, (1, 100))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/benchmark/questions")
def benchmark_questions(
    grade: int = Query(..., ge=1, le=6),
    count: int = Query(10, ge=4, le=20),
    user_id: Optional[str] = Query(None, description="Student ID — required for retest exclusion"),
):
    """Generate a balanced diagnostic question set.

    Strategy:
      - Round-robin across all 8 topics so every topic is represented.
      - Within each topic, sample one easy, one medium, one hard wherever
        possible across the grade-appropriate difficulty band.
      - On retests (when ``user_id`` is provided and the student has prior
        diagnostic history), previously seen questions are excluded so the
        student cannot memorize answers.
      - Return as plain dicts (same shape as QuestionOutV2 minus the visual url).
    """
    topics = store_v2.topics()
    if not topics:
        raise HTTPException(status_code=404, detail="No v2 content loaded.")

    band_min, band_max = _band_for_grade(grade)
    band_size = band_max - band_min + 1
    # Carve the band into 3 buckets (easy / mid / hard relative to the grade).
    third = max(1, band_size // 3)
    buckets = [
        (band_min, band_min + third - 1),
        (band_min + third, band_min + 2 * third - 1),
        (band_min + 2 * third, band_max),
    ]

    # --- Retest exclusion: load question history for this student -----------
    history_exclude: set[str] = set()
    is_retest = False
    if user_id:
        # Count total available questions across all topics for the safety valve.
        total_available = sum(
            len(store_v2.by_topic(t.topic_id)) for t in topics
        )
        history_exclude = question_history.get_exclusion_set(
            user_id, total_available=total_available,
        )
        is_retest = question_history.is_retest(user_id)
        if is_retest:
            import logging
            logging.getLogger("kiwimath.onboarding").info(
                "Retest for student=%s: excluding %d previously seen questions",
                user_id,
                len(history_exclude),
            )
        # Start a new diagnostic session for tracking.
        question_history.start_diagnostic_session(user_id)

    rng = random.Random(f"benchmark-{grade}-{count}")
    # Use a time-based seed on retests so the student gets a different set.
    if is_retest:
        rng = random.Random(f"benchmark-{grade}-{count}-{int(time.time())}")

    picked: List[Any] = []
    seen_ids: set[str] = set()

    # Pass 1: ensure every topic appears with one mid-difficulty question.
    for topic in topics:
        if len(picked) >= count:
            break
        pool = store_v2.by_difficulty_range(topic.topic_id, buckets[1][0], buckets[1][1])
        pool = [q for q in pool if q.id not in seen_ids and q.id not in history_exclude]
        if pool:
            q = rng.choice(pool)
            picked.append(q)
            seen_ids.add(q.id)

    # Pass 2: round-robin add easy + hard until we hit the count.
    bucket_indices = [0, 2, 1]  # easy, hard, mid
    bi = 0
    topic_cycle = list(topics)
    rng.shuffle(topic_cycle)
    while len(picked) < count and topic_cycle:
        topic = topic_cycle[len(picked) % len(topic_cycle)]
        b_min, b_max = buckets[bucket_indices[bi % len(bucket_indices)]]
        pool = store_v2.by_difficulty_range(topic.topic_id, b_min, b_max)
        pool = [q for q in pool if q.id not in seen_ids and q.id not in history_exclude]
        if pool:
            q = rng.choice(pool)
            picked.append(q)
            seen_ids.add(q.id)
        bi += 1
        # Bail out if we keep missing — pull from any remaining unseen pool
        if bi > 50:
            for topic in topics:
                pool = [
                    q for q in store_v2.by_topic(topic.topic_id)
                    if q.id not in seen_ids and q.id not in history_exclude
                ]
                if pool and len(picked) < count:
                    q = rng.choice(pool)
                    picked.append(q)
                    seen_ids.add(q.id)
            break

    # Record all picked questions in the history tracker.
    if user_id:
        for q in picked:
            question_history.record_diagnostic_question(user_id, q.id, "diagnostic")

    # Sort easiest → hardest for a gentle ramp.
    picked.sort(key=lambda q: q.difficulty_score)

    return [
        {
            "question_id": q.id,
            "stem": q.stem,
            "choices": q.choices,
            "difficulty_score": q.difficulty_score,
            "difficulty_tier": q.difficulty_tier,
            "visual_svg": f"/v2/questions/{q.id}/visual" if q.visual_svg else None,
            "visual_alt": q.visual_alt,
            "topic": q.topic,
            "topic_name": q.topic_name,
            "tags": q.tags,
            # Correct answer is intentionally returned so the client can grade
            # locally before submitting — keeps the diagnostic snappy. The
            # server still re-grades on submission.
            "correct_answer": q.correct_answer,
            "hint": None,
            "hint_ladder": None,
        }
        for q in picked
    ]


@router.post("/benchmark", response_model=BenchmarkResult)
def submit_benchmark(req: BenchmarkSubmitRequest):
    """Submit benchmark answers, run them through the adaptive engine,
    and return an initial ability profile.

    Side effects:
      • Updates the user's per-topic ability via `engine_v2.process_answer`.
      • Persists to Firestore when available.
    """
    if not req.answers:
        raise HTTPException(status_code=422, detail="No answers submitted")

    per_topic_acc: Dict[str, Dict[str, Any]] = {}
    total_correct = 0

    for ans in req.answers:
        q = store_v2.get(ans.question_id)
        if q is None:
            # Skip unknown ids rather than failing the whole submission.
            continue
        is_correct = ans.selected_answer == q.correct_answer
        if is_correct:
            total_correct += 1

        # Push through adaptive engine — this updates the per-topic theta.
        engine_v2.process_answer(
            user_id=req.user_id,
            topic_id=q.topic,
            question_id=q.id,
            question_difficulty=q.difficulty_score,
            is_correct=is_correct,
            time_taken_ms=ans.time_taken_ms,
        )

        bucket = per_topic_acc.setdefault(
            q.topic,
            {"topic_id": q.topic, "topic_name": q.topic_name, "correct": 0, "attempts": 0},
        )
        bucket["attempts"] += 1
        if is_correct:
            bucket["correct"] += 1

    total_q = len(req.answers)
    overall_acc = (total_correct / total_q) * 100.0 if total_q else 0.0

    # Build per-topic ability list using the engine's view of the world.
    per_topic_list: List[TopicAbility] = []
    for topic in store_v2.topics():
        ability = engine_v2.get_ability(req.user_id, topic.topic_id)
        bucket = per_topic_acc.get(topic.topic_id, {"correct": 0, "attempts": 0})
        per_topic_list.append(
            TopicAbility(
                topic_id=topic.topic_id,
                topic_name=topic.topic_name,
                ability_score=ability.difficulty_score,
                recommended_difficulty=engine_v2.recommend_difficulty(
                    req.user_id, topic.topic_id
                ),
                correct=bucket["correct"],
                attempts=bucket["attempts"],
            )
        )

    # Estimated overall ability = mean of per-topic ability scores
    if per_topic_list:
        avg_ability = round(
            sum(t.ability_score for t in per_topic_list) / len(per_topic_list)
        )
    else:
        avg_ability = theta_to_difficulty(DEFAULT_THETA)

    # Recommended starting difficulty leans easier so the kid feels capable.
    rec_start = max(1, min(100, avg_ability - 5))

    # Suggested topics: weakest first (lowest ability among those attempted)
    attempted = [t for t in per_topic_list if t.attempts > 0]
    attempted.sort(key=lambda t: (t.correct / max(1, t.attempts), t.ability_score))
    suggested = [t.topic_id for t in attempted]

    # Strengths: topics where the student got 100% (and answered ≥1)
    strengths = [
        t.topic_id
        for t in attempted
        if t.attempts > 0 and t.correct == t.attempts
    ]

    # Finalise the diagnostic session so future retests exclude these questions.
    question_history.end_diagnostic_session(req.user_id)

    # Mark user as onboarded — prevents repeat onboarding on next login.
    try:
        update_user_profile(req.user_id, {
            "onboarded_at": datetime.now(timezone.utc).isoformat(),
            "grade": req.grade,
        })
    except Exception:
        pass  # Non-fatal — profile write can retry later.

    return BenchmarkResult(
        user_id=req.user_id,
        grade=req.grade,
        total_questions=total_q,
        total_correct=total_correct,
        overall_accuracy=round(overall_acc, 1),
        estimated_ability=avg_ability,
        recommended_starting_difficulty=rec_start,
        suggested_topics=suggested,
        strengths=strengths,
        per_topic=per_topic_list,
    )
