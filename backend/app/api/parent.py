"""
Parent Dashboard API (Task #199).

Endpoints:
    GET /v2/parent/dashboard?user_id=...   → child progress summary

Returns a parent-friendly view of the child's learning state, combining:
  • Adaptive engine ability per topic (from adaptive_engine_v2)
  • Gamification stats (level, XP, coins, streaks)
  • Strengths / weaknesses with plain-language recommendations
  • Recent activity (last 10 answers)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.adaptive_engine_v2 import engine_v2
from app.services.content_store_v2 import store_v2
from app.services.gamification import gamification

router = APIRouter(prefix="/v2/parent", tags=["v2-parent"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class TopicProgress(BaseModel):
    topic_id: str
    topic_name: str
    ability_score: int        # 1-200
    accuracy: float           # 0-100 (percent)
    attempts: int
    correct: int
    streak: int
    confidence: str           # low / medium / high
    mastery: str              # learning / practising / mastered
    last_practised: Optional[str] = None  # ISO timestamp


class RecentActivity(BaseModel):
    question_id: str
    topic_id: str
    topic_name: str = ""
    correct: bool
    difficulty: int
    difficulty_label: str = "Medium"  # Easy / Medium / Hard / Challenge
    timestamp: str


class ParentDashboardResponse(BaseModel):
    user_id: str
    generated_at: str
    # Headline numbers
    overall_accuracy: float            # 0-100
    total_questions: int
    correct_questions: int
    current_streak: int                # current daily streak from gamification
    longest_streak: int                # historical longest streak
    level: int
    level_name: Optional[str] = None
    xp: int
    kiwi_coins: int
    mastery_gems: int
    # Per-topic
    topics: List[TopicProgress]
    strengths: List[str]               # topic ids where child is strongest
    needs_practice: List[str]          # topic ids where child is weakest
    # Plain-language recommendations
    recommendations: List[str]
    # Activity
    recent_activity: List[RecentActivity]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _difficulty_label(difficulty: int) -> str:
    """Human-friendly difficulty band for parent-facing display."""
    if difficulty <= 50:
        return "Easy"
    if difficulty <= 150:
        return "Medium"
    if difficulty <= 250:
        return "Hard"
    return "Challenge"


def _mastery_label(accuracy: float, attempts: int) -> str:
    """Coarse mastery bucket for a topic."""
    if attempts < 3:
        return "learning"
    if accuracy >= 0.8 and attempts >= 10:
        return "mastered"
    if accuracy >= 0.6:
        return "practising"
    return "learning"


def _build_recommendations(
    topics: List[TopicProgress],
    daily_streak: int = 0,
) -> List[str]:
    """Generate up to 3 plain-language recommendations for the parent.

    Args:
        topics: per-topic progress data
        daily_streak: gamification daily streak (consecutive days active)
    """
    recs: List[str] = []
    if not topics:
        return ["Welcome! Have your child do their first session to unlock personalized guidance."]

    # Topics they have actually attempted
    practised = [t for t in topics if t.attempts >= 3]
    if not practised:
        recs.append("Your child is just getting started. A few short sessions will give us a clearer picture.")
        return recs

    # Strength callout
    practised_sorted = sorted(practised, key=lambda t: t.accuracy, reverse=True)
    if practised_sorted and practised_sorted[0].accuracy >= 75:
        top = practised_sorted[0]
        recs.append(
            f"Your child is strong in {top.topic_name} ({round(top.accuracy)}% accuracy). "
            f"Great time to try a harder challenge here."
        )

    # Weakness callout
    weakest = sorted(practised, key=lambda t: t.accuracy)[0]
    if weakest.accuracy < 60:
        recs.append(
            f"{weakest.topic_name} could use some extra practice "
            f"({round(weakest.accuracy)}% accuracy). Short, frequent sessions help most."
        )

    # Streak / consistency nudge — only praise streaks when the daily streak
    # is genuinely above 2 (so the parent doesn't see "Nice momentum" when
    # the dashboard shows 0 days streak).
    total_attempts = sum(t.attempts for t in topics)
    if daily_streak >= 3:
        recs.append(
            f"{daily_streak}-day streak! Consistency like this builds long-term retention."
        )
    elif total_attempts < 20:
        recs.append("Aim for ~10 questions a day. Consistency beats long sessions.")
    elif daily_streak == 0 and total_attempts >= 20:
        recs.append("Your child has been making progress — a short session today would keep the momentum going.")

    return recs[:3]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=ParentDashboardResponse)
def get_parent_dashboard(
    user_id: str = Query(..., min_length=1, description="Child's user ID"),
    curriculum: Optional[str] = Query(None, description="Child's curriculum: ncert, icse, igcse, olympiad"),
):
    """Parent-facing summary of the child's learning state.

    Combines adaptive engine ability data with gamification stats and produces
    plain-language recommendations.

    Only shows topics relevant to the child's selected curriculum:
    - Olympiad users: 8 Kangaroo topics (topic-1 through topic-8)
    - Curriculum users (NCERT/ICSE/IGCSE): Kangaroo topics + their curriculum topics
    """
    # ── Filter topics based on child's curriculum ─────────────────────
    all_topics = store_v2.topics()
    if curriculum and curriculum != 'olympiad':
        # Show only the 8 Kangaroo topics — curriculum progress is shown via chapters
        relevant_topics = [t for t in all_topics if t.topic_id.startswith("topic-")]
    else:
        # Olympiad users: show only the 8 Kangaroo topics
        relevant_topics = [t for t in all_topics if t.topic_id.startswith("topic-")]

    # ── Per-topic progress (only topics the child has actually attempted) ──
    topic_progress: List[TopicProgress] = []
    for topic in relevant_topics:
        ability = engine_v2.get_ability(user_id, topic.topic_id)
        # Only include topics where the child has actually practiced
        if ability.attempts == 0:
            continue
        accuracy_pct = (ability.correct / max(1, ability.attempts)) * 100.0

        last_ts: Optional[str] = None
        if ability.history:
            # history entries store an ISO ts under "ts"
            last_ts = ability.history[-1].get("ts") or ability.updated_at or None

        topic_progress.append(TopicProgress(
            topic_id=topic.topic_id,
            topic_name=topic.topic_name,
            ability_score=ability.difficulty_score,
            accuracy=round(accuracy_pct, 1),
            attempts=ability.attempts,
            correct=ability.correct,
            streak=ability.streak,
            confidence=ability.confidence,
            mastery=_mastery_label(ability.correct / max(1, ability.attempts), ability.attempts),
            last_practised=last_ts,
        ))

    # ── Headline aggregates ───────────────────────────────────────────
    total_attempts = sum(t.attempts for t in topic_progress)
    total_correct = sum(t.correct for t in topic_progress)
    overall_acc = (total_correct / max(1, total_attempts)) * 100.0 if total_attempts else 0.0

    # ── Pull gamification profile (level, coins, streaks) ─────────────
    try:
        profile = gamification.get_profile_summary(user_id) or {}
    except Exception:
        profile = {}

    # `level` is a dict in this codebase ({level: int, name: str, ...}).
    level_blob = profile.get("level") or {}
    if isinstance(level_blob, dict):
        level = int(level_blob.get("level", 1) or 1)
        level_name = level_blob.get("name") or None
    else:
        level = int(level_blob or 1)
        level_name = profile.get("level_name") or profile.get("title")

    xp = int(profile.get("xp_total", profile.get("xp", 0)) or 0)
    coins = int(profile.get("kiwi_coins", profile.get("coins", 0)) or 0)
    gems = int(profile.get("gems", profile.get("mastery_gems", 0)) or 0)
    current_streak = int(
        profile.get("streak_current", profile.get("current_streak", 0)) or 0
    )
    longest_streak = int(
        profile.get("streak_longest", profile.get("longest_streak", current_streak)) or 0
    )

    # ── Strengths / weaknesses ────────────────────────────────────────
    practised = [t for t in topic_progress if t.attempts >= 3]
    practised_sorted = sorted(practised, key=lambda t: t.accuracy, reverse=True)
    strengths = [t.topic_id for t in practised_sorted if t.accuracy >= 75][:3]
    needs_practice = [t.topic_id for t in sorted(practised, key=lambda t: t.accuracy) if t.accuracy < 60][:3]

    # ── Recent activity (across topics, latest 10, sorted by recency) ─
    recent: List[RecentActivity] = []
    for topic in relevant_topics:
        ability = engine_v2.get_ability(user_id, topic.topic_id)
        for h in ability.history:
            diff = int(h.get("difficulty", 0) or 0)
            recent.append(RecentActivity(
                question_id=h.get("qid", ""),
                topic_id=topic.topic_id,
                topic_name=topic.topic_name,
                correct=bool(h.get("correct", False)),
                difficulty=diff,
                difficulty_label=_difficulty_label(diff),
                timestamp=h.get("ts", ""),
            ))
    # Sort by timestamp descending — parents want "what did my kid do today"
    recent.sort(key=lambda r: r.timestamp, reverse=True)
    recent = recent[:10]

    return ParentDashboardResponse(
        user_id=user_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        overall_accuracy=round(overall_acc, 1),
        total_questions=total_attempts,
        correct_questions=total_correct,
        current_streak=current_streak,
        longest_streak=max(longest_streak, current_streak),
        level=level,
        level_name=level_name,
        xp=xp,
        kiwi_coins=coins,
        mastery_gems=gems,
        topics=topic_progress,
        strengths=strengths,
        needs_practice=needs_practice,
        recommendations=_build_recommendations(topic_progress, daily_streak=current_streak),
        recent_activity=recent,
    )
