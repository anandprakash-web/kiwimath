"""
v2 Question API — serves the new flat JSON/SVG content.

Endpoints:
    GET  /v2/topics                    → list all topics
    GET  /v2/questions/next            → adaptive next question
    GET  /v2/questions/{question_id}   → specific question by ID
    POST /v2/answer/check              → check an answer, get diagnostics
    GET  /v2/questions/{qid}/visual    → SVG visual for a question
    GET  /v2/student/summary           → student ability summary
    POST /v2/questions/{qid}/feedback  → submit user feedback on a question
    GET  /v2/admin/feedback            → list all submitted feedback (admin)
"""

from __future__ import annotations

import re
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.services.content_store_v2 import store_v2, QuestionV2, _QUESTION_ID_RE
from app.services.adaptive_engine_v2 import engine_v2, theta_to_difficulty, difficulty_to_theta, p_correct
from app.services.gamification import gamification
from app.services.cluster_mastery_store import record_cluster_attempt, get_cluster_mastery, get_mastered_clusters
from app.services.session_planner import plan_session, SessionPlan
from app.services.mistake_tracker import mistake_tracker

router = APIRouter(prefix="/v2", tags=["v2"])


# ---------------------------------------------------------------------------
# Session-level cluster tracker (in-memory, per-user)
# Tracks which concept clusters a user has seen/mastered in recent questions
# to prevent repetitive pattern selection.
# ---------------------------------------------------------------------------

_cluster_tracker_lock = Lock()
_cluster_tracker: Dict[str, Dict[str, int]] = {}       # user_id -> {cluster: seen_count}
_mastered_clusters: Dict[str, set] = {}                 # user_id -> {clusters answered correctly}


def _record_cluster(user_id: str, cluster: Optional[str], correct: bool) -> None:
    """Track a cluster as seen; if answered correctly, mark as mastered."""
    if not cluster or not user_id:
        return
    with _cluster_tracker_lock:
        if user_id not in _cluster_tracker:
            _cluster_tracker[user_id] = {}
        _cluster_tracker[user_id][cluster] = _cluster_tracker[user_id].get(cluster, 0) + 1
        if correct:
            if user_id not in _mastered_clusters:
                _mastered_clusters[user_id] = set()
            _mastered_clusters[user_id].add(cluster)


def _get_cluster_state(user_id: str):
    """Return (seen_clusters_dict, mastered_clusters_set) for a user."""
    with _cluster_tracker_lock:
        seen = dict(_cluster_tracker.get(user_id, {}))
        mastered = set(_mastered_clusters.get(user_id, set()))
    return seen, mastered


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class TopicOut(BaseModel):
    topic_id: str
    topic_name: str
    total_questions: int
    difficulty_distribution: Dict[str, int]


class ChapterOut(BaseModel):
    id: str
    name: str
    question_count: int
    topics: List[str] = Field(default_factory=list)


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
    choices: List[str] = Field(default_factory=list)
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
    solution_steps: List[str] = Field(default_factory=list)
    # Multi-mode interaction
    interaction_mode: str = "mcq"  # "mcq" | "integer" | "drag_drop"
    correct_value: Optional[int] = None  # Integer mode answer
    drag_items: Optional[List[str]] = None  # Drag-drop items (shuffled)


class AnswerCheckRequest(BaseModel):
    question_id: str
    selected_answer: int = Field(default=0, ge=0, le=3, description="MCQ: selected option index")
    integer_answer: Optional[int] = Field(default=None, description="Integer mode: typed numeric answer")
    drag_order: Optional[List[int]] = Field(default=None, description="Drag-drop mode: submitted ordering of items")
    user_id: str = Field(default="anonymous", description="Student ID for adaptive tracking")
    time_taken_ms: int = Field(default=0, ge=0, description="Time taken to answer in ms")
    hints_used: int = Field(default=0, ge=0, le=5, description="Highest hint level viewed (0-2 for 3-level, legacy 0-5 still accepted)")

    @field_validator("question_id")
    @classmethod
    def validate_question_id(cls, v: str) -> str:
        if not _QUESTION_ID_RE.match(v):
            raise ValueError(
                f"Invalid question_id '{v}'. Must match format T[1-8]-NNN (e.g. T1-001)"
            )
        return v


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

    # For drag_drop, shuffle items and DON'T send correct_order to client
    drag_items = None
    if q.interaction_mode == "drag_drop" and q.drag_items:
        import random
        drag_items = q.drag_items[:]  # Send items (frontend shuffles on display)

    return QuestionOutV2(
        question_id=q.id,
        stem=q.stem,
        choices=q.choices if q.choices else [],
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
        solution_steps=q.solution_steps if hasattr(q, 'solution_steps') else [],
        interaction_mode=q.interaction_mode or "mcq",
        correct_value=q.correct_value if q.interaction_mode == "integer" else None,
        drag_items=drag_items,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

_GRADE_DIFFICULTY = {
    1: (1, 50),
    2: (51, 100),
    3: (101, 150),
    4: (151, 200),
    5: (201, 250),
    6: (251, 300),
}


@router.get("/topics", response_model=List[TopicOut])
def list_topics(
    grade: Optional[int] = Query(None, ge=1, le=6, description="Grade filter (1-6)"),
):
    """List Olympiad/Kangaroo topics (topic-1 through topic-8) with question counts.

    Only returns the 8 core Kangaroo topics. Curriculum-specific content
    (NCERT/ICSE/IGCSE) is served via /v2/chapters instead.

    When `grade` is provided, total_questions and difficulty_distribution
    are scoped to the grade's difficulty range (G1: 1-50, G2: 51-100).
    """
    all_topics = store_v2.topics()
    # Filter to only Olympiad topics (exclude curriculum-specific topics)
    _CURRICULUM_PREFIXES = ("ncert_", "icse_", "igcse_")
    topics = [
        t for t in all_topics
        if not t.topic_id.startswith(_CURRICULUM_PREFIXES)
        and ":" not in t.topic_id
        and "&" not in t.topic_id
    ]
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


@router.get("/chapters", response_model=List[ChapterOut])
def list_chapters(
    grade: int = Query(..., ge=1, le=6, description="Grade (1-6)"),
    curriculum: str = Query(..., description="Curriculum: ncert, icse, igcse"),
):
    """List ordered chapters for a curriculum + grade combination.

    Returns chapters with question counts, extracted from loaded content.
    Use for NCERT/ICSE/IGCSE — Olympiad uses /v2/topics instead.
    """
    chapters = store_v2.get_chapters(curriculum, grade)
    if not chapters:
        return []
    return [
        ChapterOut(
            id=ch["id"],
            name=ch["name"],
            question_count=ch["question_count"],
            topics=ch["topics"],
        )
        for ch in chapters
    ]


@router.get("/questions/next", response_model=QuestionOutV2)
def next_question(
    topic: Optional[str] = Query(None, description="Topic ID filter"),
    difficulty: Optional[int] = Query(None, ge=1, le=200, description="Target difficulty (1-200)"),
    window: int = Query(10, ge=1, le=50, description="Difficulty search window (±)"),
    exclude: Optional[str] = Query(None, description="Comma-separated question IDs to exclude"),
    user_id: Optional[str] = Query(None, description="Student ID for adaptive selection"),
    grade: Optional[int] = Query(None, ge=1, le=6, description="Grade filter (1-6)"),
    chapter: Optional[str] = Query(None, description="Curriculum chapter filter (e.g. 'Ch1: Numbers 1 to 9')"),
    curriculum: Optional[str] = Query(None, description="Curriculum filter: ncert, icse, igcse"),
    use_learning_path: bool = Query(
        False,
        description="If true and no topic is given, follows the user's adaptive learning path "
        "(Task #197) — picks the first not-yet-mastered topic.",
    ),
):
    """Get the next question, optionally filtered by topic, difficulty, and grade.

    When `grade` is provided, questions are restricted to that grade's
    difficulty range (G1: 1-50, G2: 51-100, G3: 101-150, G4: 151-200).

    If user_id is provided, uses ELO/IRT-based selection to pick the
    optimal question for the student's current ability level.
    Otherwise falls back to difficulty-window matching.

    If `use_learning_path=true` (and no `topic` given), the endpoint
    queries the per-user learning path and uses the first stop's topic
    + difficulty range for selection.
    """
    exclude_ids = exclude.split(",") if exclude else []

    # Add recently seen questions from history to prevent cross-session repetition
    if user_id:
        recently_seen = skill_ability_store.get_recent_question_ids(user_id)
        exclude_ids = list(set(exclude_ids) | recently_seen)

    exclude_ids = exclude_ids if exclude_ids else None

    # Apply grade-based difficulty filter
    grade_min, grade_max = None, None
    if grade and grade in _GRADE_DIFFICULTY:
        grade_min, grade_max = _GRADE_DIFFICULTY[grade]

    # Optionally consult the learning path to fill in topic + difficulty
    eff_topic = topic
    eff_difficulty = difficulty
    if use_learning_path and user_id and not eff_topic:
        try:
            from app.api.learning_path import get_learning_path
            plan = get_learning_path(user_id=user_id, grade=grade)
            if plan.path:
                first = plan.path[0]
                eff_topic = first.topic_id
                eff_difficulty = first.target_difficulty
        except Exception:
            # Learning-path lookup is best-effort; fall through.
            pass

    # Get cluster state for diversity-aware selection
    seen_clusters, mastered_clusters = {}, set()
    if user_id:
        seen_clusters, mastered_clusters = _get_cluster_state(user_id)

    # ─── IRT for curriculum chapters ───────────────────────────────────
    # When chapter + curriculum are provided, build the candidate pool from
    # curriculum questions and run IRT selection over that pool.
    if user_id and chapter and curriculum and grade:
        pool = store_v2.get_curriculum_questions(curriculum, grade, chapter)
        if pool:
            # Use a stable topic_id for ability tracking: curriculum_g{grade}_{chapter}
            chapter_topic_id = f"{curriculum.lower()}_g{grade}_{chapter}"
            q = engine_v2.select_question(
                user_id=user_id,
                topic_id=chapter_topic_id,
                available_questions=pool,
                exclude_ids=exclude_ids,
                exclude_clusters=list(mastered_clusters),
                seen_clusters=seen_clusters,
            )
            if q:
                return _to_response(q)
            # If IRT couldn't pick (e.g. all excluded), fall through to basic selector

    # If we have a user_id and topic, use the smart adaptive selector
    if user_id and eff_topic:
        pool = store_v2.by_topic(eff_topic)
        # Filter pool by grade difficulty range
        if pool and grade_min is not None:
            pool = [q for q in pool if grade_min <= q.difficulty_score <= grade_max]
        if pool:
            q = engine_v2.select_question(
                user_id=user_id,
                topic_id=eff_topic,
                available_questions=pool,
                exclude_ids=exclude_ids,
                exclude_clusters=list(mastered_clusters),
                seen_clusters=seen_clusters,
            )
            if q:
                return _to_response(q)

    # Fallback: use the basic difficulty-window selector
    # Clamp difficulty target within grade range if applicable
    if eff_difficulty and grade_min is not None:
        eff_difficulty = max(grade_min, min(grade_max, eff_difficulty))
    elif grade_min is not None and eff_difficulty is None:
        # Default to midpoint of grade range
        eff_difficulty = (grade_min + grade_max) // 2

    q = store_v2.next_question(
        topic_id=eff_topic,
        difficulty=eff_difficulty,
        window=window,
        exclude_ids=exclude_ids,
        min_difficulty=grade_min,
        max_difficulty=grade_max,
        exclude_clusters=list(mastered_clusters),
        seen_clusters=seen_clusters,
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
    if not _QUESTION_ID_RE.match(question_id):
        raise HTTPException(status_code=422, detail=f"Invalid question ID format: {question_id}")
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

    # Determine correctness based on interaction mode
    mode = q.interaction_mode or "mcq"
    if mode == "integer" and req.integer_answer is not None:
        is_correct = req.integer_answer == q.correct_value
        feedback = "Try again! Check your calculation." if not is_correct else ""
    elif mode == "drag_drop" and req.drag_order is not None:
        is_correct = req.drag_order == q.correct_order
        feedback = "Not quite — try a different arrangement." if not is_correct else ""
    else:
        # MCQ mode (default)
        is_correct = req.selected_answer == q.correct_answer
        feedback = q.diagnostics.get(str(req.selected_answer), "Try again!")

    if is_correct:
        feedback = "Correct! Well done!"

    # Record cluster for diversity tracking (in-memory session-level)
    _record_cluster(req.user_id, q.concept_cluster, is_correct)

    # Persist cluster mastery to Firestore (cross-session)
    if req.user_id and req.user_id != "anonymous" and q.concept_cluster:
        try:
            record_cluster_attempt(req.user_id, q.concept_cluster, is_correct)
        except Exception:
            pass  # Best-effort; never fail the answer check

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

        # Track mistakes for spaced revision
        if not is_correct:
            try:
                mistake_tracker.record_mistake(
                    student_id=req.user_id,
                    question_id=q.id,
                    topic_id=q.topic,
                    concept_cluster=q.concept_cluster or f"{q.topic}/_default",
                    tags=q.tags,
                )
            except Exception:
                pass  # Best-effort; never fail the answer check

        # Record revision result for spaced-interval tracking
        if is_correct and q.concept_cluster:
            try:
                mistake_tracker.record_revision_result(
                    student_id=req.user_id,
                    concept_cluster=q.concept_cluster,
                    correct=True,
                )
            except Exception:
                pass
        elif not is_correct and q.concept_cluster:
            try:
                mistake_tracker.record_revision_result(
                    student_id=req.user_id,
                    concept_cluster=q.concept_cluster,
                    correct=False,
                )
            except Exception:
                pass

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
            question_id=q.id,
        )

        # Log response for IRT calibration
        approx_theta = result.new_difficulty / 33.33 - 1.5
        response_logger.log_response(
            user_id=req.user_id,
            question_id=q.id,
            correct=is_correct,
            response_time_ms=req.time_taken_ms,
            user_theta=approx_theta,
            skill_id="",
            question_difficulty=q.difficulty_score,
            question_irt_a=q.irt_a,
            question_irt_b=q.irt_b,
            question_irt_c=q.irt_c,
            grade=0,
        )

        # Update proficiency tracking (competency + scale scores)
        competency = getattr(q, 'competency_level', None) or 'K'
        try:
            proficiency_store.update_proficiency(
                user_id=req.user_id,
                theta=approx_theta,
                grade=0,
                competency=competency,
                correct=is_correct,
                topic_id=q.topic,
            )
        except Exception:
            pass  # Best-effort

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


@router.get("/irt/stats")
def irt_data_stats():
    """Check how much response data has been collected for IRT calibration."""
    return {
        "total_responses_buffered": response_logger.get_response_count(),
        "daily_stats": response_logger.get_daily_stats(),
        "message": "Once you have 30+ responses per question, run: python scripts/irt_calibrator.py",
    }


# ---------------------------------------------------------------------------
# Proficiency & Growth Endpoints
# ---------------------------------------------------------------------------

@router.get("/proficiency")
def get_proficiency(
    user_id: str = Query(..., description="Student ID"),
    grade: int = Query(0, description="Student grade (1-6)"),
):
    """Get student's proficiency level, scale score, and competency breakdown."""
    # Get overall theta from adaptive engine
    from app.services.adaptive_engine_v2 import engine_v2
    topics = store_v2.topics()
    total_attempts = 0
    total_correct = 0
    weighted_theta = 0.0
    topic_count = 0

    for topic in topics:
        ability = engine_v2.get_ability(user_id, topic.topic_id)
        if ability.attempts > 0:
            # Approximate theta from difficulty score
            theta = ability.difficulty_score / 33.33 - 1.5
            weighted_theta += theta * ability.attempts
            total_attempts += ability.attempts
            total_correct += ability.correct
            topic_count += 1

    avg_theta = weighted_theta / max(1, total_attempts)
    overall_accuracy = total_correct / max(1, total_attempts)

    proficiency = get_proficiency_for_display(avg_theta, grade)

    # Get competency profile from Firestore
    prof_data = proficiency_store.get_proficiency(user_id, grade)
    competency = prof_data.get("competency_profile", CompetencyProfile().to_dict())

    # Get growth data
    growth = proficiency_store.get_growth_data(user_id)

    return {
        "user_id": user_id,
        "proficiency": proficiency,
        "competency_profile": competency,
        "growth": growth,
        "stats": {
            "total_questions": total_attempts,
            "total_correct": total_correct,
            "overall_accuracy": round(overall_accuracy * 100, 1),
            "topics_practiced": topic_count,
        },
    }


@router.get("/proficiency/levels")
def list_proficiency_levels():
    """List all proficiency levels with descriptions."""
    from app.services.proficiency_levels import PROFICIENCY_LEVELS
    return {
        "levels": [
            {
                "level": pl.level,
                "name": pl.name,
                "emoji": pl.emoji,
                "color": pl.color,
                "theta_range": [pl.theta_min, pl.theta_max],
                "scale_range": [pl.scale_min, pl.scale_max],
                "can_do": pl.can_do,
                "next_steps": pl.next_steps,
            }
            for pl in PROFICIENCY_LEVELS
        ]
    }


# ---------------------------------------------------------------------------
# Benchmark Test Endpoints
# ---------------------------------------------------------------------------

@router.post("/benchmark/create")
def create_benchmark_test(
    user_id: str = Query(...),
    grade: int = Query(1),
    benchmark_type: str = Query("diagnostic", regex="^(baseline|midline|endline|diagnostic)$"),
):
    """Create a structured benchmark test for the student."""
    all_questions = [q.__dict__ if hasattr(q, '__dict__') else q
                     for q in store_v2.all_questions()]

    # Get previously seen question IDs to exclude
    from app.services.skill_ability_store import skill_ability_store
    seen_ids = set(skill_ability_store.get_recent_question_ids(user_id))

    test = benchmark_service.create_benchmark_test(
        user_id=user_id,
        grade=grade,
        benchmark_type=benchmark_type,
        all_questions=all_questions,
        exclude_ids=seen_ids,
    )

    if not test:
        raise HTTPException(status_code=400, detail="Not enough questions to create benchmark test")

    # Return the questions for the test
    questions = []
    for qid in test.question_ids:
        q = store_v2.get(qid)
        if q:
            questions.append(_to_response(q))

    return {
        "benchmark_id": test.benchmark_id,
        "benchmark_type": test.benchmark_type,
        "total_questions": len(questions),
        "time_limit_seconds": len(questions) * 90,
        "questions": questions,
    }


@router.post("/benchmark/submit")
def submit_benchmark(
    benchmark_id: str = Query(...),
    user_id: str = Query(...),
    grade: int = Query(1),
    responses: List[Dict] = [],
):
    """Submit completed benchmark test responses for scoring."""
    from pydantic import BaseModel

    all_questions = [q.__dict__ if hasattr(q, '__dict__') else q
                     for q in store_v2.all_questions()]

    result = benchmark_service.score_benchmark(
        user_id=user_id,
        benchmark_id=benchmark_id,
        responses=responses,
        all_questions=all_questions,
        grade=grade,
    )

    if not result:
        raise HTTPException(status_code=400, detail="Could not score benchmark test")

    # Record growth snapshot
    proficiency_store.record_growth_snapshot(
        user_id=user_id,
        theta=result.theta,
        total_questions=result.total_questions,
        accuracy=result.accuracy,
    )

    return result.to_dict()


@router.get("/benchmark/history")
def benchmark_history(user_id: str = Query(...)):
    """Get all benchmark test results for a student."""
    history = benchmark_service.get_benchmark_history(user_id)
    growth = benchmark_service.get_growth_comparison(user_id)
    return {
        "user_id": user_id,
        "benchmarks": history,
        "growth_comparison": growth,
    }


# ---------------------------------------------------------------------------
# Remedial Endpoints
# ---------------------------------------------------------------------------

@router.get("/remedial/stats")
def remedial_stats(user_id: str = Query(...)):
    """Get remedial effectiveness stats for a student."""
    return remedial_engine.get_remedial_stats(user_id)


@router.get("/questions/{question_id}/visual")
def get_visual(question_id: str):
    """Get the SVG visual for a question."""
    if not _QUESTION_ID_RE.match(question_id):
        raise HTTPException(status_code=422, detail=f"Invalid question ID format: {question_id}")
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
    min_difficulty: int = Query(1, ge=1, le=500),
    max_difficulty: int = Query(200, ge=1, le=500),
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


# ---------------------------------------------------------------------------
# Question Feedback (Task #194)
# ---------------------------------------------------------------------------

# Allowed feedback categories.
_FEEDBACK_TYPES = {
    "wrong_answer",
    "unclear_stem",
    "bad_visual",
    "too_easy",
    "too_hard",
    "other",
}


class QuestionFeedbackRequest(BaseModel):
    """Payload sent when a student flags a question."""
    user_id: str = Field(default="anonymous", description="Student ID submitting the feedback")
    feedback_type: str = Field(..., description="One of: wrong_answer, unclear_stem, bad_visual, too_easy, too_hard, other")
    comment: Optional[str] = Field(default=None, max_length=500, description="Optional free-text comment")

    @field_validator("feedback_type")
    @classmethod
    def validate_feedback_type(cls, v: str) -> str:
        if v not in _FEEDBACK_TYPES:
            raise ValueError(f"Invalid feedback_type '{v}'. Must be one of {sorted(_FEEDBACK_TYPES)}")
        return v

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None


class QuestionFeedbackOut(BaseModel):
    """Stored feedback record."""
    feedback_id: str
    question_id: str
    user_id: str
    feedback_type: str
    comment: Optional[str] = None
    created_at: str
    topic: Optional[str] = None
    difficulty_score: Optional[int] = None


# In-memory feedback store. Falls back to Firestore when available.
# Structure: {feedback_id: feedback_dict}
_FEEDBACK_STORE: Dict[str, Dict[str, Any]] = {}
_FEEDBACK_LOCK = Lock()


def _save_feedback_firestore(record: Dict[str, Any]) -> None:
    """Best-effort save to Firestore. Silent no-op if unavailable."""
    try:
        from app.services.firestore_service import _get_db, is_firestore_available
        if not is_firestore_available():
            return
        db = _get_db()
        if not db:
            return
        db.collection("question_feedback").document(record["feedback_id"]).set(record)
    except Exception:
        # Never fail user-facing endpoint just because Firestore is down.
        pass


@router.post("/questions/{question_id}/feedback", response_model=QuestionFeedbackOut)
def submit_question_feedback(question_id: str, req: QuestionFeedbackRequest):
    """Accept user-side feedback on a specific question.

    Students can flag questions as wrong/unclear/bad-visual/too-easy/too-hard/other.
    Feedback is stored in-memory (and Firestore when available) for admin review.
    """
    if not _QUESTION_ID_RE.match(question_id):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid question_id '{question_id}'. Must match T[1-8]-NNN format.",
        )

    q = store_v2.get(question_id)
    if q is None:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")

    feedback_id = uuid.uuid4().hex
    record: Dict[str, Any] = {
        "feedback_id": feedback_id,
        "question_id": question_id,
        "user_id": req.user_id,
        "feedback_type": req.feedback_type,
        "comment": req.comment,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "topic": q.topic,
        "difficulty_score": q.difficulty_score,
    }

    with _FEEDBACK_LOCK:
        _FEEDBACK_STORE[feedback_id] = record

    _save_feedback_firestore(record)

    return QuestionFeedbackOut(**record)


@router.get("/admin/feedback", response_model=List[QuestionFeedbackOut])
def list_feedback(
    question_id: Optional[str] = Query(None, description="Filter by question ID"),
    feedback_type: Optional[str] = Query(None, description="Filter by feedback type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List all submitted feedback with optional filters.

    Most recent first. Combines in-memory store and Firestore if available.
    """
    if feedback_type and feedback_type not in _FEEDBACK_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid feedback_type. Must be one of {sorted(_FEEDBACK_TYPES)}",
        )

    with _FEEDBACK_LOCK:
        records: List[Dict[str, Any]] = list(_FEEDBACK_STORE.values())

    # Try to merge in any Firestore-only records (best effort).
    try:
        from app.services.firestore_service import _get_db, is_firestore_available
        if is_firestore_available():
            db = _get_db()
            if db:
                seen = {r["feedback_id"] for r in records}
                for doc in db.collection("question_feedback").stream():
                    data = doc.to_dict() or {}
                    if data.get("feedback_id") and data["feedback_id"] not in seen:
                        records.append(data)
                        seen.add(data["feedback_id"])
    except Exception:
        pass

    # Apply filters
    if question_id:
        records = [r for r in records if r.get("question_id") == question_id]
    if feedback_type:
        records = [r for r in records if r.get("feedback_type") == feedback_type]
    if user_id:
        records = [r for r in records if r.get("user_id") == user_id]

    # Most recent first
    records.sort(key=lambda r: r.get("created_at", ""), reverse=True)

    page = records[offset:offset + limit]
    return [QuestionFeedbackOut(**r) for r in page]


@router.get("/admin/feedback/summary")
def feedback_summary():
    """High-level feedback stats for the admin dashboard."""
    with _FEEDBACK_LOCK:
        records = list(_FEEDBACK_STORE.values())

    by_type: Dict[str, int] = defaultdict(int)
    by_question: Dict[str, int] = defaultdict(int)
    for r in records:
        by_type[r.get("feedback_type", "unknown")] += 1
        by_question[r.get("question_id", "")] += 1

    # Top 10 most-flagged questions
    top_flagged = sorted(by_question.items(), key=lambda kv: kv[1], reverse=True)[:10]

    return {
        "total_feedback": len(records),
        "by_type": dict(by_type),
        "top_flagged_questions": [
            {"question_id": qid, "flag_count": n} for qid, n in top_flagged if qid
        ],
    }


# ---------------------------------------------------------------------------
# Level Progression System (Task #284)
# 10 micro-levels per topic per grade, auto-promote via IRT ability score
# ---------------------------------------------------------------------------

_LEVEL_NAMES = [
    "Starter", "Explorer", "Builder", "Thinker", "Climber",
    "Solver", "Strategist", "Champion", "Master", "Legend",
]

_LEVELS_PER_GRADE = 10
_POINTS_PER_LEVEL = 5  # Each grade spans 50 difficulty points, 10 levels × 5


class LevelInfo(BaseModel):
    """A single level within a topic."""
    level: int = Field(..., ge=1, le=10)
    name: str
    status: str = Field(..., description="locked | current | completed")
    difficulty_min: int
    difficulty_max: int
    questions_done: int = 0
    questions_total: int = 0
    stars: int = Field(0, ge=0, le=3, description="0-3 stars based on accuracy")
    accuracy: float = 0.0


class TopicLevelsOut(BaseModel):
    """Level progression for a single topic."""
    topic_id: str
    topic_name: str
    grade: int
    current_level: int = Field(1, ge=1, le=10)
    levels: List[LevelInfo]
    all_mastered: bool = False
    grade_upgrade_available: bool = False


class StudentLevelsOut(BaseModel):
    """All topic progressions for a student."""
    user_id: str
    grade: int
    topics: List[TopicLevelsOut]
    overall_level: float = Field(0.0, description="Average level across topics")


def _compute_level_from_ability(ability_score: int, grade: int) -> int:
    """Map an IRT ability score to a level (1-10) within a grade.

    Grade 1: diff 1-50  → L1=1-5, L2=6-10, ..., L10=46-50
    Grade 2: diff 51-100 → L1=51-55, ..., L10=96-100
    etc.
    """
    grade_min = (grade - 1) * 50 + 1
    # How far into the grade the student is
    offset = max(0, ability_score - grade_min)
    level = (offset // _POINTS_PER_LEVEL) + 1
    return min(level, _LEVELS_PER_GRADE)


def _stars_from_accuracy(accuracy: float) -> int:
    """Convert accuracy percentage to 0-3 stars."""
    if accuracy >= 0.9:
        return 3
    if accuracy >= 0.7:
        return 2
    if accuracy >= 0.5:
        return 1
    return 0


@router.get("/student/levels", response_model=StudentLevelsOut)
def student_levels(
    user_id: str = Query(..., description="Student ID"),
    grade: int = Query(1, ge=1, le=6, description="Grade (1-6)"),
):
    """Get level progression for all topics for a student.

    Returns 10 levels per topic, with current level determined by the
    student's IRT ability score. Levels below current are 'completed',
    the current is 'current', and above are 'locked'.
    """
    grade_min, grade_max = _GRADE_DIFFICULTY.get(grade, (1, 50))
    topics = store_v2.topics()
    topic_levels: List[TopicLevelsOut] = []
    level_sum = 0.0

    for t in topics:
        # Get student's ability for this topic
        summary = engine_v2.get_student_summary(user_id, t.topic_id)
        ability = summary.get("recommended_difficulty", grade_min)
        total_answered = summary.get("total_questions", 0)
        accuracy = summary.get("accuracy", 0.0)
        if isinstance(accuracy, (int, float)) and accuracy > 1:
            accuracy = accuracy / 100.0  # normalize to 0-1

        current_level = _compute_level_from_ability(ability, grade)
        level_sum += current_level

        # Build levels
        levels: List[LevelInfo] = []
        for lv in range(1, _LEVELS_PER_GRADE + 1):
            lv_min = grade_min + (lv - 1) * _POINTS_PER_LEVEL
            lv_max = min(lv_min + _POINTS_PER_LEVEL - 1, grade_max)

            # Count questions in this level's range
            qs_in_range = store_v2.by_difficulty_range(t.topic_id, lv_min, lv_max)
            q_total = len(qs_in_range)

            if lv < current_level:
                status = "completed"
                lv_stars = _stars_from_accuracy(accuracy)
                lv_accuracy = accuracy
            elif lv == current_level:
                status = "current"
                lv_stars = 0
                lv_accuracy = accuracy
            else:
                status = "locked"
                lv_stars = 0
                lv_accuracy = 0.0

            levels.append(LevelInfo(
                level=lv,
                name=_LEVEL_NAMES[lv - 1],
                status=status,
                difficulty_min=lv_min,
                difficulty_max=lv_max,
                questions_done=total_answered if lv <= current_level else 0,
                questions_total=q_total,
                stars=lv_stars,
                accuracy=round(lv_accuracy, 3),
            ))

        all_mastered = current_level >= _LEVELS_PER_GRADE and accuracy >= 0.7
        topic_levels.append(TopicLevelsOut(
            topic_id=t.topic_id,
            topic_name=t.topic_name,
            grade=grade,
            current_level=current_level,
            levels=levels,
            all_mastered=all_mastered,
            grade_upgrade_available=all_mastered and grade < 6,
        ))

    n_topics = len(topic_levels) or 1
    return StudentLevelsOut(
        user_id=user_id,
        grade=grade,
        topics=topic_levels,
        overall_level=round(level_sum / n_topics, 1),
    )


# ---------------------------------------------------------------------------
# Student Profile — name + grade (Task #285)
# ---------------------------------------------------------------------------

class ProfileUpdateRequest(BaseModel):
    """Update student profile (name, grade, avatar, curriculum)."""
    display_name: Optional[str] = Field(None, max_length=30, description="Kid's display name")
    grade: Optional[int] = Field(None, ge=1, le=6, description="Selected grade")
    avatar: Optional[str] = Field(None, description="Avatar ID")
    curriculum: Optional[str] = Field(None, description="Curriculum: ncert, icse, igcse, olympiad")


@router.post("/student/profile")
def update_student_profile(
    user_id: str = Query(..., description="Student ID"),
    req: ProfileUpdateRequest = ...,
):
    """Update student's display name, grade, and avatar.

    Called during onboarding when the parent enters the kid's name.
    Persists to Firestore if available, otherwise in-memory.
    """
    profile_data: Dict[str, Any] = {"user_id": user_id}
    if req.display_name is not None:
        profile_data["display_name"] = req.display_name.strip()
    if req.grade is not None:
        profile_data["grade"] = req.grade
    if req.avatar is not None:
        profile_data["avatar"] = req.avatar
    if req.curriculum is not None:
        profile_data["curriculum"] = req.curriculum

    # Save to Firestore — write to 'users' collection (same as GET /user/profile reads)
    try:
        from app.services.firestore_service import update_user_profile, is_firestore_available
        if is_firestore_available():
            updates = {}
            if req.display_name is not None:
                updates["display_name"] = req.display_name.strip()
            if req.grade is not None:
                updates["grade"] = req.grade
            if req.avatar is not None:
                updates["avatar"] = req.avatar
            if req.curriculum is not None:
                updates["curriculum"] = req.curriculum
            if updates:
                update_user_profile(user_id, updates)
    except Exception:
        pass

    # Also save in-memory for this server instance
    _profile_cache[user_id] = {**_profile_cache.get(user_id, {}), **profile_data}

    return {"status": "ok", **profile_data}


# In-memory profile cache (supplements Firestore)
_profile_cache: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Smart Session Plan (Task #317)
# ---------------------------------------------------------------------------


class PlannedQuestionOut(BaseModel):
    question_id: str
    topic_id: str
    topic_name: str
    concept_cluster: str
    difficulty_score: int
    priority_reason: str


class SessionPlanOut(BaseModel):
    user_id: str
    grade: int
    questions: List[PlannedQuestionOut]
    cluster_breakdown: Dict[str, int]
    topic_breakdown: Dict[str, int]
    total_mastered: int
    total_clusters: int


@router.get("/session/plan", response_model=SessionPlanOut)
def get_session_plan(
    user_id: str = Query(..., description="Student ID"),
    grade: int = Query(1, ge=1, le=6, description="Grade (1-6)"),
    size: int = Query(10, ge=5, le=20, description="Session size"),
):
    """Build a smart 10-question session plan across all topics.

    Uses cluster mastery data to skip mastered skills, target weak spots,
    and spread questions across topics for variety.
    """
    sp = plan_session(user_id=user_id, grade=grade, session_size=size)
    return SessionPlanOut(
        user_id=sp.user_id,
        grade=sp.grade,
        questions=[
            PlannedQuestionOut(
                question_id=pq.question_id,
                topic_id=pq.topic_id,
                topic_name=pq.topic_name,
                concept_cluster=pq.concept_cluster,
                difficulty_score=pq.difficulty_score,
                priority_reason=pq.priority_reason,
            )
            for pq in sp.questions
        ],
        cluster_breakdown=sp.cluster_breakdown,
        topic_breakdown=sp.topic_breakdown,
        total_mastered=sp.total_mastered,
        total_clusters=sp.total_clusters,
    )


# ---------------------------------------------------------------------------
# Mastery Overview (Task #317)
# ---------------------------------------------------------------------------


class ClusterMasteryOut(BaseModel):
    cluster: str
    attempts: int
    correct: int
    accuracy: float
    mastered: bool
    last_seen: str


class MasteryOverviewOut(BaseModel):
    user_id: str
    total_clusters: int
    mastered_count: int
    clusters: List[ClusterMasteryOut]
    topic_mastery: Dict[str, Dict[str, int]]  # topic -> {total, mastered}


@router.get("/mastery/overview", response_model=MasteryOverviewOut)
def mastery_overview(
    user_id: str = Query(..., description="Student ID"),
    grade: Optional[int] = Query(None, ge=1, le=6, description="Grade filter"),
):
    """Get the student's cluster mastery overview for the home screen.

    Shows how many skill clusters are mastered per topic, and the full
    list of clusters with their mastery status.
    """
    user_mastery = get_cluster_mastery(user_id)
    mastered_set = get_mastered_clusters(user_id)

    # Build topic-level mastery counts from content
    grade_min, grade_max = None, None
    if grade and grade in _GRADE_DIFFICULTY:
        grade_min, grade_max = _GRADE_DIFFICULTY[grade]

    all_clusters_by_topic: Dict[str, set] = defaultdict(set)
    for t in store_v2.topics():
        if grade_min is not None:
            questions = store_v2.by_difficulty_range(t.topic_id, grade_min, grade_max)
        else:
            questions = store_v2.by_topic(t.topic_id)
        for q in questions:
            if q.concept_cluster:
                all_clusters_by_topic[t.topic_id].add(q.concept_cluster)

    topic_mastery: Dict[str, Dict[str, int]] = {}
    for tid, clusters in all_clusters_by_topic.items():
        mastered_in_topic = len(clusters & mastered_set)
        topic_mastery[tid] = {"total": len(clusters), "mastered": mastered_in_topic}

    clusters_out = [
        ClusterMasteryOut(
            cluster=name,
            attempts=m.attempts,
            correct=m.correct,
            accuracy=round(m.accuracy, 3),
            mastered=m.mastered,
            last_seen=m.last_seen,
        )
        for name, m in sorted(user_mastery.items(), key=lambda x: x[1].accuracy)
    ]

    return MasteryOverviewOut(
        user_id=user_id,
        total_clusters=sum(len(c) for c in all_clusters_by_topic.values()),
        mastered_count=len(mastered_set),
        clusters=clusters_out,
        topic_mastery=topic_mastery,
    )


# ---------------------------------------------------------------------------
# Spaced Revision Queue (Task: Spaced Revision System)
# ---------------------------------------------------------------------------


class RevisionItemOut(BaseModel):
    """A single revision queue item for the student."""
    concept_cluster: str
    topic_id: str
    tags: List[str]
    question_id: Optional[str] = None
    question_stem: Optional[str] = None
    question_choices: Optional[List[str]] = None
    question_difficulty: Optional[int] = None
    mistake_count: int
    last_mistake_date: str
    times_reviewed: int
    next_review_date: Optional[str] = None
    is_due: bool
    mastery_status: str


class RevisionQueueOut(BaseModel):
    """Full revision queue response."""
    user_id: str
    total_pending: int
    items: List[RevisionItemOut]
    stats: Dict[str, Any]


@router.get("/revision-queue/{user_id}", response_model=RevisionQueueOut)
def get_revision_queue_endpoint(
    user_id: str,
    max_items: int = Query(10, ge=1, le=50, description="Max items to return"),
    include_upcoming: bool = Query(False, description="Include items not yet due"),
):
    """Get the student's pending revision items with question details.

    Returns items due for spaced revision based on past mistakes.
    Each item includes the original question details so the UI can
    render revision questions directly.
    """
    queue = mistake_tracker.get_revision_queue(
        student_id=user_id,
        max_items=max_items,
        include_not_yet_due=include_upcoming,
    )

    items_out: List[RevisionItemOut] = []
    for item in queue:
        item_dict = item.to_dict()
        # Enrich with question details from the content store
        question_id = None
        question_stem = None
        question_choices = None
        question_difficulty = None

        if item.mistake_question_ids:
            # Pick the most recent mistake question
            qid = item.mistake_question_ids[-1]
            q = store_v2.get(qid)
            if q is not None:
                question_id = q.id
                question_stem = q.stem
                question_choices = q.choices
                question_difficulty = q.difficulty_score

        items_out.append(RevisionItemOut(
            concept_cluster=item.concept_cluster,
            topic_id=item.topic_id,
            tags=item.tags,
            question_id=question_id,
            question_stem=question_stem,
            question_choices=question_choices,
            question_difficulty=question_difficulty,
            mistake_count=item_dict["mistake_count"],
            last_mistake_date=item_dict["last_mistake_date"],
            times_reviewed=item_dict["times_reviewed"],
            next_review_date=item_dict["next_review_date"],
            is_due=item_dict["is_due"],
            mastery_status=item_dict["mastery_status"],
        ))

    stats = mistake_tracker.get_revision_stats(user_id)

    return RevisionQueueOut(
        user_id=user_id,
        total_pending=stats.get("due_now", 0),
        items=items_out,
        stats=stats,
    )


# ---------------------------------------------------------------------------
# Unified Cross-Curriculum Session (THE MOAT)
# ---------------------------------------------------------------------------

from app.services.unified_session_planner import (
    plan_unified_session,
    generate_session_summary,
    generate_weekly_report,
    adjust_remaining_session,
    detect_learning_rate,
    UnifiedSessionPlan,
    UnifiedPlannedQuestion,
    ParentSessionSummary,
)
from app.services.skill_ability_store import skill_ability_store
from app.services.response_logger import response_logger
from app.services.spaced_review_engine import spaced_review_store
from app.services.proficiency_levels import (
    proficiency_store, get_proficiency_for_display, theta_to_scale_score,
    CompetencyProfile,
)
from app.services.remedial_engine import remedial_engine
from app.services.benchmark_test import benchmark_service


class UnifiedQuestionOut(BaseModel):
    question_id: str
    skill_id: str
    skill_name: str
    difficulty_score: int
    slot_type: str
    source_curriculum: str


class UnifiedSessionOut(BaseModel):
    user_id: str
    grade: int
    questions: List[UnifiedQuestionOut]
    focus_skills: List[str]
    skill_breakdown: Dict[str, int]
    curriculum_mix: Dict[str, int]
    session_message: str
    mastery_transitions: List[str]


@router.get("/session/unified", response_model=UnifiedSessionOut)
def get_unified_session(
    user_id: str = Query(..., description="Student ID"),
    grade: int = Query(1, ge=1, le=6, description="Grade (1-6)"),
    size: int = Query(10, ge=5, le=20, description="Session size"),
):
    """Build a cross-curriculum adaptive session pulling from ALL curricula.

    This is the primary session endpoint — replaces /session/plan.
    Questions are selected from the unified pool of 21,330 across
    Olympiad + NCERT + ICSE + Singapore + USCC, routed through the
    37-node prerequisite skill graph.

    Session structure: [warmup] → [core skill practice] → [stretch] → [review]
    """
    # Load recently seen question IDs to prevent cross-session repetition
    recently_seen = skill_ability_store.get_recent_question_ids(user_id)

    plan = plan_unified_session(
        user_id=user_id,
        grade=grade,
        session_size=size,
        previously_seen_ids=recently_seen,
    )

    # Cache the plan for session completion
    _unified_plans[f"{user_id}_{grade}"] = plan

    return UnifiedSessionOut(
        user_id=plan.user_id,
        grade=plan.grade,
        questions=[
            UnifiedQuestionOut(
                question_id=q.question_id,
                skill_id=q.skill_id,
                skill_name=q.skill_name,
                difficulty_score=q.difficulty_score,
                slot_type=q.slot_type,
                source_curriculum=q.source_curriculum,
            )
            for q in plan.questions
        ],
        focus_skills=plan.focus_skills,
        skill_breakdown=plan.skill_breakdown,
        curriculum_mix=plan.curriculum_mix,
        session_message=plan.session_message,
        mastery_transitions=plan.mastery_transitions,
    )


# In-memory cache for active unified session plans
_unified_plans: Dict[str, UnifiedSessionPlan] = {}


class SessionResultIn(BaseModel):
    """Submitted when a unified session completes."""
    user_id: str
    grade: int
    results: List[Dict[str, Any]]  # [{question_id, correct, time_ms, skill_id}, ...]


class ParentSummaryOut(BaseModel):
    session_id: str
    accuracy: float
    questions_correct: int
    questions_total: int
    skills_practiced: List[str]
    new_masteries: List[str]
    progress_message: str
    next_focus: str
    weekly_trend: str


@router.post("/session/unified/complete", response_model=ParentSummaryOut)
def complete_unified_session(body: SessionResultIn):
    """Submit results for a completed unified session.

    Updates per-skill thetas, checks mastery, schedules FSRS reviews,
    and returns a parent-facing summary message.
    """
    plan_key = f"{body.user_id}_{body.grade}"
    plan = _unified_plans.get(plan_key)

    if not plan:
        # Reconstruct a minimal plan from results
        plan = plan_unified_session(
            user_id=body.user_id, grade=body.grade, session_size=len(body.results)
        )

    summary = generate_session_summary(
        user_id=body.user_id,
        grade=body.grade,
        session_plan=plan,
        results=body.results,
    )

    # Record served question IDs so they won't repeat in next session
    served_ids = [r.question_id for r in body.results]
    skill_ability_store.record_served_questions(body.user_id, served_ids)

    # Log responses for IRT calibration
    all_abilities = skill_ability_store.get_all_abilities(body.user_id)
    for r in body.results:
        q = store_v2.get(r.question_id)
        skill_id = r.skill_id if hasattr(r, 'skill_id') and r.skill_id else ""
        ability = all_abilities.get(skill_id)
        user_theta = ability.theta if ability else -1.5
        response_logger.log_response(
            user_id=body.user_id,
            question_id=r.question_id,
            correct=r.correct,
            response_time_ms=r.time_ms if hasattr(r, 'time_ms') else 0,
            user_theta=user_theta,
            skill_id=skill_id,
            question_difficulty=q.difficulty_score if q else 0,
            question_irt_a=q.irt_a if q else 1.0,
            question_irt_b=q.irt_b if q else 0.0,
            question_irt_c=q.irt_c if q else 0.25,
            session_id=summary.session_id,
            grade=body.grade,
        )
    response_logger.flush()

    # Clean up cached plan
    _unified_plans.pop(plan_key, None)

    return ParentSummaryOut(
        session_id=summary.session_id,
        accuracy=summary.accuracy,
        questions_correct=summary.questions_correct,
        questions_total=summary.questions_total,
        skills_practiced=summary.skills_practiced,
        new_masteries=summary.new_masteries,
        progress_message=summary.progress_message,
        next_focus=summary.next_focus,
        weekly_trend=summary.weekly_trend,
    )


class SkillProgressOut(BaseModel):
    user_id: str
    grade: int
    mastered_skills: int
    total_skills: int
    mastery_percentage: float
    skills: List[Dict[str, Any]]


@router.get("/skills/progress", response_model=SkillProgressOut)
def get_skill_progress(
    user_id: str = Query(..., description="Student ID"),
    grade: int = Query(1, ge=1, le=6, description="Grade (1-6)"),
):
    """Get comprehensive skill-level progress for a student.

    Returns all 37 skills with: theta, accuracy, mastery status,
    grade-level gap. Used by the parent dashboard and learning path.
    """
    progress = skill_ability_store.get_skill_progress(user_id, grade)
    return SkillProgressOut(**progress)


class ReviewSummaryOut(BaseModel):
    total_mastered_skills: int
    due_for_review: int
    average_recall: float
    upcoming_7_days: int
    skills_due: List[Dict[str, Any]]


@router.get("/skills/review-status", response_model=ReviewSummaryOut)
def get_review_status(
    user_id: str = Query(..., description="Student ID"),
):
    """Get FSRS-based review status for mastered skills.

    Shows which mastered skills are due for refresh and estimated recall.
    """
    summary = spaced_review_store.get_review_summary(user_id)
    return ReviewSummaryOut(**summary)


class WeeklyReportOut(BaseModel):
    report: str
    mastered_skills: int
    total_skills: int


@router.get("/parent/weekly-report", response_model=WeeklyReportOut)
def get_weekly_report(
    user_id: str = Query(..., description="Student ID"),
    grade: int = Query(1, ge=1, le=6, description="Grade"),
    child_name: str = Query("Your child", description="Child's name"),
):
    """Generate a weekly parent report.

    Summarizes: mastered skills, skills in progress, weak areas,
    review status, and actionable recommendations.
    """
    report = generate_weekly_report(user_id=user_id, grade=grade, child_name=child_name)
    progress = skill_ability_store.get_skill_progress(user_id, grade)
    return WeeklyReportOut(
        report=report,
        mastered_skills=progress["mastered_skills"],
        total_skills=progress["total_skills"],
    )


class MidSessionAdjustIn(BaseModel):
    """Request to adjust remaining session based on real-time performance."""
    user_id: str
    grade: int
    results_so_far: List[Dict[str, Any]]
    current_index: int


class LearningRateOut(BaseModel):
    adjustments: Dict[str, Any]  # {skill_id: {trend, difficulty_adjustment}}


@router.post("/session/unified/adjust", response_model=LearningRateOut)
def adjust_session_mid_flight(body: MidSessionAdjustIn):
    """Mid-session difficulty adjustment based on within-session learning rate.

    Called after each answer to detect if the student is accelerating
    or struggling, and adjust remaining question difficulty accordingly.
    """
    plan_key = f"{body.user_id}_{body.grade}"
    plan = _unified_plans.get(plan_key)

    adjustments = {}
    if plan:
        for skill_id in plan.focus_skills:
            rate = detect_learning_rate(body.results_so_far, skill_id)
            if rate["difficulty_adjustment"] != 0:
                adjustments[skill_id] = rate

        # Apply adjustments to cached plan
        adjust_remaining_session(plan, body.results_so_far, body.current_index)

    return LearningRateOut(adjustments=adjustments)
