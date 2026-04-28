"""
v2 Question API — serves the new flat JSON/SVG content.

Endpoints:
    GET  /v2/topics                    → list all topics
    GET  /v2/questions/next            → adaptive next question
    GET  /v2/questions/{question_id}   → specific question by ID
    POST /v2/answer/check              → check an answer, get diagnostics
    GET  /v2/questions/{qid}/visual    → SVG visual for a question
    GET  /v2/student/summary           → student ability summary
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.content_store_v2 import store_v2, QuestionV2
from app.services.adaptive_engine_v2 import engine_v2, theta_to_difficulty, difficulty_to_theta, p_correct
from app.services.gamification import gamification

router = APIRouter(prefix="/v2", tags=["v2"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class TopicOut(BaseModel):
    topic_id: str
    topic_name: str
    total_questions: int
    difficulty_distribution: Dict[str, int]


class HintLadderOut(BaseModel):
    """Socratic 6-level hint ladder."""
    level_0: str
    level_1: str
    level_2: str
    level_3: str
    level_4: str
    level_5: str


class QuestionOutV2(BaseModel):
    question_id: str
    stem: str
    choices: List[str]
    difficulty_score: int
    difficulty_tier: str
    visual_svg: Optional[str] = None
    visual_alt: Optional[str] = None
    topic: str
    topic_name: str
    tags: List[str] = Field(default_factory=list)
    # In production, correct_answer should NOT be sent to client.
    # For v2 preview / dev mode, we include it.
    correct_answer: int
    hint: Optional[str] = None
    hint_ladder: Optional[HintLadderOut] = None


class AnswerCheckRequest(BaseModel):
    question_id: str
    selected_answer: int = Field(..., ge=0, le=3)
    user_id: str = Field(default="anonymous", description="Student ID for adaptive tracking")
    time_taken_ms: int = Field(default=0, ge=0, description="Time taken to answer in ms")
    hints_used: int = Field(default=0, ge=0, le=5, description="Highest hint level viewed (0-5)")


class AnswerCheckResponse(BaseModel):
    correct: bool
    correct_answer: int
    feedback: str
    difficulty_score: int
    next_difficulty: int  # ELO/IRT recommended next difficulty (1-100)
    # New adaptive fields
    p_expected: float = Field(default=0.5, description="Model's predicted P(correct) before answer")
    ability_score: int = Field(default=50, description="Student's current ability (1-100)")
    streak: int = Field(default=0, description="Current streak (+correct, -wrong)")
    confidence: str = Field(default="low", description="Confidence in ability estimate: low/medium/high")
    accuracy: float = Field(default=0.0, description="Overall accuracy percentage")
    # Behavioral matrix fields (PoP model)
    behavioral_state: str = Field(default="", description="Cognitive state: mastery/guessing/struggle_win/frustrated")
    reward_multiplier: float = Field(default=1.0, description="XP multiplier based on behavioral state")
    p_abandon: float = Field(default=0.0, description="Probability the student is about to quit (0-1)")
    intervention: str = Field(default="none", description="Recommended intervention: none/visual_scaffold/cooldown/airdrop/boss_battle")
    latency_class: str = Field(default="normal", description="Response speed: fast/slow/unknown")
    # Gamification events
    xp_earned: int = Field(default=0, description="XP earned from this answer")
    coins_earned: int = Field(default=0, description="Kiwi Coins earned from this answer")
    gems_earned: int = Field(default=0, description="Gems earned from this answer")
    level_up: Optional[Dict[str, Any]] = Field(default=None, description="Level-up info if leveled up")
    micro_celebration: Optional[str] = Field(default=None, description="Celebration message if threshold crossed")
    badge_unlocks: List[Dict[str, Any]] = Field(default_factory=list, description="Newly unlocked badges")
    title_unlocks: List[Dict[str, Any]] = Field(default_factory=list, description="Newly earned titles")
    # Kiwi Brain engine fields
    child_state: str = Field(default="", description="Child's cognitive state: flowing/struggling/guessing/fatigued/confident/bored/new_user")
    next_action: Optional[Dict[str, str]] = Field(default=None, description="Recommended next action from the Kiwi Brain engine")
    reward_breakdown: Optional[Dict[str, Any]] = Field(default=None, description="Per-question coin reward breakdown")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_response(q: QuestionV2) -> QuestionOutV2:
    # Build hint ladder if structured hints are available
    ladder_out = None
    ladder = q.hint_ladder
    if ladder:
        ladder_out = HintLadderOut(
            level_0=ladder.level_0,
            level_1=ladder.level_1,
            level_2=ladder.level_2,
            level_3=ladder.level_3,
            level_4=ladder.level_4,
            level_5=ladder.level_5,
        )

    return QuestionOutV2(
        question_id=q.id,
        stem=q.stem,
        choices=q.choices,
        difficulty_score=q.difficulty_score,
        difficulty_tier=q.difficulty_tier,
        visual_svg=f"/v2/questions/{q.id}/visual" if q.visual_svg else None,
        visual_alt=q.visual_alt,
        topic=q.topic,
        topic_name=q.topic_name,
        tags=q.tags,
        correct_answer=q.correct_answer,
        hint=q.hint_text,
        hint_ladder=ladder_out,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

_GRADE_DIFFICULTY = {
    1: (1, 50),
    2: (51, 100),
}


@router.get("/topics", response_model=List[TopicOut])
def list_topics(
    grade: Optional[int] = Query(None, ge=1, le=2, description="Grade filter (1 or 2)"),
):
    """List all available topics with question counts.

    When `grade` is provided, total_questions and difficulty_distribution
    are scoped to the grade's difficulty range (G1: 1-50, G2: 51-100).
    """
    topics = store_v2.topics()
    if not topics:
        raise HTTPException(status_code=404, detail="No v2 content loaded.")

    if grade is None:
        return [
            TopicOut(
                topic_id=t.topic_id,
                topic_name=t.topic_name,
                total_questions=t.total_questions,
                difficulty_distribution=t.difficulty_distribution,
            )
            for t in topics
        ]

    min_d, max_d = _GRADE_DIFFICULTY[grade]
    result = []
    for t in topics:
        filtered = store_v2.by_difficulty_range(t.topic_id, min_d, max_d)
        dist: Dict[str, int] = {}
        for q in filtered:
            dist[q.difficulty_tier] = dist.get(q.difficulty_tier, 0) + 1
        result.append(TopicOut(
            topic_id=t.topic_id,
            topic_name=t.topic_name,
            total_questions=len(filtered),
            difficulty_distribution=dist,
        ))
    return result


@router.get("/questions/next", response_model=QuestionOutV2)
def next_question(
    topic: Optional[str] = Query(None, description="Topic ID filter"),
    difficulty: Optional[int] = Query(None, ge=1, le=100, description="Target difficulty (1-100)"),
    window: int = Query(10, ge=1, le=50, description="Difficulty search window (±)"),
    exclude: Optional[str] = Query(None, description="Comma-separated question IDs to exclude"),
    user_id: Optional[str] = Query(None, description="Student ID for adaptive selection"),
    grade: Optional[int] = Query(None, ge=1, le=2, description="Grade filter (1 or 2)"),
):
    """Get the next question, optionally filtered by topic, difficulty, and grade.

    When `grade` is provided, questions are restricted to that grade's
    difficulty range (G1: 1-50, G2: 51-100).

    If user_id is provided, uses ELO/IRT-based selection to pick the
    optimal question for the student's current ability level.
    Otherwise falls back to difficulty-window matching.
    """
    exclude_ids = exclude.split(",") if exclude else None

    # Apply grade-based difficulty filter
    grade_min, grade_max = None, None
    if grade and grade in _GRADE_DIFFICULTY:
        grade_min, grade_max = _GRADE_DIFFICULTY[grade]

    # If we have a user_id and topic, use the smart adaptive selector
    if user_id and topic:
        pool = store_v2.by_topic(topic)
        # Filter pool by grade difficulty range
        if pool and grade_min is not None:
            pool = [q for q in pool if grade_min <= q.difficulty_score <= grade_max]
        if pool:
            q = engine_v2.select_question(
                user_id=user_id,
                topic_id=topic,
                available_questions=pool,
                exclude_ids=exclude_ids,
            )
            if q:
                return _to_response(q)

    # Fallback: use the basic difficulty-window selector
    # Clamp difficulty target within grade range if applicable
    eff_difficulty = difficulty
    if eff_difficulty and grade_min is not None:
        eff_difficulty = max(grade_min, min(grade_max, eff_difficulty))
    elif grade_min is not None and eff_difficulty is None:
        # Default to midpoint of grade range
        eff_difficulty = (grade_min + grade_max) // 2

    q = store_v2.next_question(
        topic_id=topic,
        difficulty=eff_difficulty,
        window=window,
        exclude_ids=exclude_ids,
        min_difficulty=grade_min,
        max_difficulty=grade_max,
    )

    if q is None:
        raise HTTPException(
            status_code=404,
            detail="No questions available. Check KIWIMATH_V2_CONTENT_DIR.",
        )

    return _to_response(q)


@router.get("/questions/{question_id}", response_model=QuestionOutV2)
def get_question(question_id: str):
    """Get a specific question by ID."""
    q = store_v2.get(question_id)
    if q is None:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
    return _to_response(q)


@router.post("/answer/check", response_model=AnswerCheckResponse)
def check_answer(req: AnswerCheckRequest):
    """Check an answer and get diagnostic feedback.

    Uses ELO/IRT adaptive engine to:
    1. Update the student's ability estimate
    2. Compute the optimal next difficulty level
    3. Return rich adaptive feedback

    If no user_id is provided, falls back to simple +5/-3 adjustment.
    """
    q = store_v2.get(req.question_id)
    if q is None:
        raise HTTPException(status_code=404, detail=f"Question {req.question_id} not found")

    is_correct = req.selected_answer == q.correct_answer
    feedback = q.diagnostics.get(str(req.selected_answer), "Try again!")

    if is_correct:
        feedback = "Correct! Well done!"

    # Use ELO/IRT engine if user_id is provided
    if req.user_id and req.user_id != "anonymous":
        result = engine_v2.process_answer(
            user_id=req.user_id,
            topic_id=q.topic,
            question_id=q.id,
            question_difficulty=q.difficulty_score,
            is_correct=is_correct,
            time_taken_ms=req.time_taken_ms,
        )

        # Trigger gamification events (with full Kiwi Brain params)
        is_hard = q.difficulty_tier == "hard"
        time_taken_secs = req.time_taken_ms / 1000.0
        gam_events = gamification.record_answer(
            user_id=req.user_id,
            topic_id=q.topic,
            is_correct=is_correct,
            is_hard=is_hard,
            difficulty=q.difficulty_score,
            hints_used=req.hints_used,
            time_taken_seconds=time_taken_secs,
        )

        # Apply reward multiplier to XP
        base_xp = gam_events.get("xp_earned", 0)
        boosted_xp = int(base_xp * result.reward_multiplier)

        return AnswerCheckResponse(
            correct=is_correct,
            correct_answer=q.correct_answer,
            feedback=feedback,
            difficulty_score=q.difficulty_score,
            next_difficulty=result.new_difficulty,
            p_expected=round(result.p_correct, 3),
            ability_score=result.new_difficulty,
            streak=result.streak,
            confidence=result.confidence,
            accuracy=round(result.accuracy * 100, 1),
            behavioral_state=result.behavioral_state,
            reward_multiplier=result.reward_multiplier,
            p_abandon=result.p_abandon,
            intervention=result.intervention,
            latency_class=result.latency_class,
            xp_earned=boosted_xp,
            coins_earned=gam_events.get("coins_earned", 0),
            gems_earned=gam_events.get("gems_earned", 0),
            level_up=gam_events.get("level_up"),
            micro_celebration=gam_events.get("micro_celebration"),
            badge_unlocks=gam_events.get("badge_unlocks", []),
            title_unlocks=gam_events.get("title_unlocks", []),
            child_state=gam_events.get("child_state", ""),
            next_action=gam_events.get("next_action"),
            reward_breakdown=gam_events.get("reward_breakdown"),
        )

    # Fallback: simple adaptive (for anonymous / legacy clients)
    # Correct: step up by 3 levels.  Wrong: fall back halfway toward 1.
    if is_correct:
        next_diff = min(100, q.difficulty_score + 3)
    else:
        next_diff = max(1, (q.difficulty_score + 1) // 2)

    return AnswerCheckResponse(
        correct=is_correct,
        correct_answer=q.correct_answer,
        feedback=feedback,
        difficulty_score=q.difficulty_score,
        next_difficulty=next_diff,
    )


@router.get("/questions/{question_id}/visual")
def get_visual(question_id: str):
    """Get the SVG visual for a question."""
    q = store_v2.get(question_id)
    if q is None:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")

    if not q.visual_svg:
        raise HTTPException(status_code=404, detail=f"Question {question_id} has no visual")

    svg_content = store_v2.get_svg(q.topic, q.visual_svg)
    if svg_content is None:
        raise HTTPException(status_code=404, detail=f"SVG file {q.visual_svg} not found")

    from fastapi.responses import Response
    return Response(content=svg_content, media_type="image/svg+xml")


@router.get("/student/summary")
def student_summary(
    user_id: str = Query(..., description="Student ID"),
    topic: Optional[str] = Query(None, description="Topic ID (or all topics)"),
):
    """Get student's ability summary for one or all topics.

    Returns ELO/IRT ability data: current level, accuracy, streak,
    confidence, and recommended difficulty.
    """
    if topic:
        return engine_v2.get_student_summary(user_id, topic)

    # All topics
    topics = store_v2.topics()
    return [engine_v2.get_student_summary(user_id, t.topic_id) for t in topics]


@router.get("/questions", response_model=List[QuestionOutV2])
def list_questions(
    topic: Optional[str] = Query(None, description="Topic ID filter"),
    min_difficulty: int = Query(1, ge=1, le=100),
    max_difficulty: int = Query(100, ge=1, le=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List questions with optional filters. Useful for admin/preview."""
    if topic:
        pool = store_v2.by_difficulty_range(topic, min_difficulty, max_difficulty)
    else:
        pool = [
            q for q in store_v2.all_questions()
            if min_difficulty <= q.difficulty_score <= max_difficulty
        ]

    total = len(pool)
    page = pool[offset:offset + limit]

    return page and [_to_response(q) for q in page] or []
