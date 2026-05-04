"""
Adaptive Learning Path API (Task #197).

Endpoint:
    GET /v2/learning-path?user_id=...&grade=...

Builds a personalized, ordered sequence of topics + difficulty ranges for a
student based on their per-topic ability and recent activity:

  • Topics with the lowest ability go first (build foundations)
  • Mastered topics are scheduled for spaced-repetition review
  • Difficulty range targets the student's flow zone (P(correct) ≈ 0.72)
  • Grade filter (1-6) clamps the recommended difficulty band
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.adaptive_engine_v2 import (
    engine_v2,
    theta_to_difficulty,
)
from app.services.content_store_v2 import store_v2

router = APIRouter(prefix="/v2", tags=["v2-learning-path"])


# Same grade bands as onboarding / questions_v2
_GRADE_BANDS = {
    1: (1, 50),
    2: (51, 100),
    3: (101, 150),
    4: (151, 200),
    5: (201, 250),
    6: (251, 300),
}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class LearningPathStop(BaseModel):
    sequence: int
    topic_id: str
    topic_name: str
    reason: str               # why this topic next
    target_difficulty: int    # difficulty 1-200
    difficulty_range: List[int]  # [min, max]
    questions_to_attempt: int
    mastery_label: str        # learning / practising / mastered / review
    review: bool              # spaced-repetition review session?


class LearningPathResponse(BaseModel):
    user_id: str
    grade: Optional[int] = None
    generated_at: str
    summary: str
    path: List[LearningPathStop]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mastery_label(accuracy: float, attempts: int) -> str:
    if attempts < 3:
        return "learning"
    if accuracy >= 0.8 and attempts >= 10:
        return "mastered"
    if accuracy >= 0.6:
        return "practising"
    return "learning"


def _spaced_repetition_due(updated_at: str, mastery: str) -> bool:
    """A mastered topic is "due" for review after a few days idle.

    We use a simple ladder:
      • mastered → 5 days
      • practising → 3 days
      • learning → 1 day
    If we can't parse updated_at, we don't mark it as due (avoid noise).
    """
    if not updated_at:
        return False
    try:
        ts = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    age = datetime.now(timezone.utc) - ts
    if mastery == "mastered":
        return age >= timedelta(days=5)
    if mastery == "practising":
        return age >= timedelta(days=3)
    return age >= timedelta(days=1)


def _clamp(val: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, val))


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("/learning-path", response_model=LearningPathResponse)
def get_learning_path(
    user_id: str = Query(..., min_length=1),
    grade: Optional[int] = Query(None, ge=1, le=6, description="Grade band 1-6"),
):
    """Generate a personalised topic ordering + difficulty plan."""
    # Only include the 8 Kangaroo/Olympiad topics.
    # Curriculum-specific topics (NCERT, ICSE, IGCSE, Singapore, US Common Core)
    # are served via the /v2/chapters endpoint instead.
    _CURRICULUM_PREFIXES = ("ncert_", "icse_", "igcse_")
    all_topics = store_v2.topics()
    topics = [
        t for t in all_topics
        if not t.topic_id.startswith(_CURRICULUM_PREFIXES)
        and ":" not in t.topic_id
        and "&" not in t.topic_id
    ]
    if not topics:
        raise HTTPException(status_code=404, detail="No v2 content loaded.")

    # Grade band, if provided.
    band_min, band_max = (1, 200)
    if grade and grade in _GRADE_BANDS:
        band_min, band_max = _GRADE_BANDS[grade]

    # Build a record per topic with everything we need to score it.
    records: List[Dict[str, Any]] = []
    for topic in topics:
        ability = engine_v2.get_ability(user_id, topic.topic_id)
        accuracy = ability.correct / max(1, ability.attempts) if ability.attempts else 0.0
        mastery = _mastery_label(accuracy, ability.attempts)
        records.append({
            "topic_id": topic.topic_id,
            "topic_name": topic.topic_name,
            "attempts": ability.attempts,
            "accuracy": accuracy,
            "ability": ability.difficulty_score,
            "mastery": mastery,
            "updated_at": ability.updated_at,
            "review_due": _spaced_repetition_due(ability.updated_at, mastery),
        })

    # ── Ordering rules ────────────────────────────────────────────────
    # 1. New / under-explored topics first (attempts < 3) — gentle introduction.
    # 2. Then "learning" / "practising" topics, weakest accuracy first.
    # 3. Then mastered topics that are *due* for spaced-repetition review.
    # 4. Mastered, not-yet-due topics at the bottom (recency check skipped).

    new_topics    = [r for r in records if r["attempts"] < 3]
    weak_topics   = [r for r in records if r["attempts"] >= 3 and r["mastery"] != "mastered"]
    review_topics = [r for r in records if r["mastery"] == "mastered" and r["review_due"]]
    fresh_master  = [r for r in records if r["mastery"] == "mastered" and not r["review_due"]]

    # Sort sub-lists.
    new_topics.sort(key=lambda r: r["topic_id"])
    weak_topics.sort(key=lambda r: (r["accuracy"], r["ability"]))
    review_topics.sort(key=lambda r: r["updated_at"])
    fresh_master.sort(key=lambda r: r["topic_id"])

    ordered = new_topics + weak_topics + review_topics + fresh_master

    # ── Build path stops ──────────────────────────────────────────────
    path: List[LearningPathStop] = []
    for i, r in enumerate(ordered, start=1):
        # Target difficulty: a bit below ability for weak topics, at ability
        # for practising topics, and slightly harder for mastered review.
        if r["mastery"] == "mastered":
            target = _clamp(r["ability"] + 3, band_min, band_max)
            d_range = [_clamp(target - 5, band_min, band_max),
                       _clamp(target + 8, band_min, band_max)]
            qcount = 5  # quick review pass
        elif r["mastery"] == "practising":
            target = _clamp(r["ability"], band_min, band_max)
            d_range = [_clamp(target - 5, band_min, band_max),
                       _clamp(target + 5, band_min, band_max)]
            qcount = 10
        elif r["attempts"] < 3:
            # Brand-new — start at the bottom of the grade band.
            target = _clamp(band_min + 2, band_min, band_max)
            d_range = [band_min, _clamp(band_min + 8, band_min, band_max)]
            qcount = 8
        else:
            # weak / learning
            target = _clamp(max(1, r["ability"] - 5), band_min, band_max)
            d_range = [_clamp(target - 5, band_min, band_max),
                       _clamp(target + 5, band_min, band_max)]
            qcount = 12

        # Reason text
        if r["attempts"] < 3:
            reason = f"New topic — let's introduce {r['topic_name']}."
        elif r["mastery"] == "learning":
            reason = (
                f"Practice {r['topic_name']} — current accuracy "
                f"{round(r['accuracy'] * 100)}%."
            )
        elif r["mastery"] == "practising":
            reason = (
                f"Build fluency in {r['topic_name']} — almost there at "
                f"{round(r['accuracy'] * 100)}%."
            )
        elif r["mastery"] == "mastered" and r["review_due"]:
            reason = f"Spaced-repetition review of {r['topic_name']} to keep it sharp."
        else:
            reason = f"Light maintenance pass on {r['topic_name']}."

        path.append(LearningPathStop(
            sequence=i,
            topic_id=r["topic_id"],
            topic_name=r["topic_name"],
            reason=reason,
            target_difficulty=target,
            difficulty_range=d_range,
            questions_to_attempt=qcount,
            mastery_label=r["mastery"],
            review=(r["mastery"] == "mastered" and r["review_due"]),
        ))

    # ── Summary line ──────────────────────────────────────────────────
    if any(r["attempts"] >= 3 for r in records):
        weakest = min((r for r in records if r["attempts"] >= 3),
                      key=lambda r: r["accuracy"], default=None)
        if weakest:
            summary = (
                f"Your plan starts with {weakest['topic_name']} "
                f"(your trickiest topic right now) and ramps up from there."
            )
        else:
            summary = "Your plan covers all 8 topics, weakest first."
    else:
        summary = "Welcome! We'll start gently and figure out your strengths together."

    return LearningPathResponse(
        user_id=user_id,
        grade=grade,
        generated_at=datetime.now(timezone.utc).isoformat(),
        summary=summary,
        path=path,
    )
