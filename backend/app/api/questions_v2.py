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
    3: (101, 150),
    4: (151, 200),
    5: (201, 250),
    6: (251, 300),
}


@router.get("/topics", response_model=List[TopicOut])
def list_topics(
    grade: Optional[int] = Query(None, ge=1, le=6, description="Grade filter (1-6)"),
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
    difficulty: Optional[int] = Query(None, ge=1, le=200, description="Target difficulty (1-200)"),
    window: int = Query(10, ge=1, le=50, description="Difficulty search window (±)"),
    exclude: Optional[str] = Query(None, description="Comma-separated question IDs to exclude"),
    user_id: Optional[str] = Query(None, description="Student ID for adaptive selection"),
    grade: Optional[int] = Query(None, ge=1, le=6, description="Grade filter (1-6)"),
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
    exclude_ids = exclude.split(",") if exclude else None

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
    grade: int = Query(1, ge=1, le=4, description="Grade (1-4)"),
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
            grade_upgrade_available=all_mastered and grade < 4,
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
    """Update student profile (name, grade, avatar)."""
    display_name: Optional[str] = Field(None, max_length=30, description="Kid's display name")
    grade: Optional[int] = Field(None, ge=1, le=4, description="Selected grade")
    avatar: Optional[str] = Field(None, description="Avatar ID")


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
