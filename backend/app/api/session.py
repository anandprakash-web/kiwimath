"""
Session API — adaptive learning session endpoints.

These endpoints power the core learning loop:
    POST /session/start    → begin a session for a concept
    POST /session/answer   → submit an answer, get next question + feedback
    GET  /session/state    → peek at current session state (debug)
    GET  /session/concepts      → list available concepts
    GET  /session/review-queue  → spaced-repetition review queue

Persistence:
    - Active sessions live in server memory (_sessions dict).
    - On session start: mastery loaded from Firestore (or in-memory fallback).
    - On session complete: mastery + gamification flushed to Firestore.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.question import ConceptGraph
from app.services import content_store
from app.services.adaptive_engine import (
    AdaptiveEngine,
    AttemptResult,
    MasterySnapshot,
    SessionState,
)
from app.services.firestore_service import (
    compute_session_rewards,
    get_mastery_states,
    get_user_profile,
    save_mastery_states,
    save_session_log,
    update_gamification_on_session_end,
)
from app.services.svg_generators import UnknownGeneratorError, render_svg
from app.services.visual_validator import generate_alt_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/session", tags=["session"])


# ---------------------------------------------------------------------------
# In-memory session store (active sessions only — Firestore handles persistence)
# ---------------------------------------------------------------------------

_sessions: Dict[str, SessionState] = {}
_session_meta: Dict[str, Dict[str, Any]] = {}  # session_id -> metadata (started_at, etc.)
_engine: Optional[AdaptiveEngine] = None
_concept_graph: Optional[ConceptGraph] = None


def _get_engine() -> AdaptiveEngine:
    """Lazy-initialise the adaptive engine with the loaded content store."""
    global _engine, _concept_graph
    if _engine is None:
        if _concept_graph is None:
            import os
            from pathlib import Path

            graph_path = os.environ.get("KIWIMATH_DAG_PATH")
            if not graph_path:
                content_dir = os.environ.get("KIWIMATH_CONTENT_DIR", "")
                if content_dir:
                    # Prefer the all-grades concept graph, fall back to grade1-only.
                    base = Path(content_dir).parent
                    for candidate_name in [
                        "concept_graph_all_grades.json",
                        "concept_graph_grade1.json",
                    ]:
                        candidate = base / candidate_name
                        if candidate.exists():
                            graph_path = str(candidate)
                            break

            if graph_path and Path(graph_path).exists():
                data = json.loads(Path(graph_path).read_text())
                _concept_graph = ConceptGraph(**data)
            else:
                _concept_graph = ConceptGraph(nodes=[], version=1)

        _engine = AdaptiveEngine(content_store.store, _concept_graph)
    return _engine


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class StartSessionRequest(BaseModel):
    user_id: str = Field(default="demo-user", description="User identifier (Firebase UID)")
    concept_id: str = Field(..., description="Concept to practise (e.g. 'addition.within_10')")
    mastery_states: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Optional client-provided mastery overrides. If omitted, loaded from Firestore.",
    )


class AnswerRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier from start response")
    question_id: str = Field(..., description="The question being answered")
    selected_option_index: int = Field(..., ge=0, description="Zero-based index of chosen option")
    time_taken_ms: int = Field(default=0, ge=0, description="Milliseconds spent before answering")


class OptionOut(BaseModel):
    text: str
    is_correct: bool = False


class VisualOut(BaseModel):
    kind: str
    svg: Optional[str] = None
    alt_text: Optional[str] = None


class QuestionOut(BaseModel):
    question_id: str
    stem: str
    options: List[OptionOut]
    correct_index: int
    visual: Optional[VisualOut] = None
    params_used: Dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    session_id: str
    question: Optional[QuestionOut] = None
    feedback_message: Optional[str] = None
    misconception_diagnosis: Optional[str] = None
    mascot_emotion: str = "neutral"
    is_step_down: bool = False
    session_complete: bool = False
    concept_mastered: bool = False
    suggest_next_concept: Optional[str] = None
    mastery_snapshot: Optional[Dict[str, Any]] = None
    session_stats: Optional[Dict[str, Any]] = None
    retry_same_question: bool = False
    scaffold_level: int = 0
    # Gamification fields — included when session completes.
    rewards: Optional[Dict[str, Any]] = None
    user_profile: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_visual(visual_dict: Optional[Dict], stem: str = "") -> Optional[VisualOut]:
    if not visual_dict:
        return None
    vtype = visual_dict.get("type")
    if vtype == "svg_generator":
        generator_name = visual_dict.get("generator", "")
        params = visual_dict.get("params", {})
        try:
            svg = render_svg(generator_name, params)
            # Generate accessibility alt-text for the visual.
            alt = generate_alt_text(generator_name, params, stem)
            return VisualOut(kind="svg_inline", svg=svg, alt_text=alt)
        except (UnknownGeneratorError, Exception) as e:
            logger.warning(f"SVG render failed for '{generator_name}': {e}")
            return VisualOut(kind="svg_inline", svg=f"<!-- {e} -->")
    return None


def _rendered_to_question_out(rendered) -> QuestionOut:
    visual = _render_visual(rendered.visual, stem=rendered.stem)
    return QuestionOut(
        question_id=rendered.question_id,
        stem=rendered.stem,
        options=[
            OptionOut(text=o.text, is_correct=o.is_correct)
            for o in rendered.options
        ],
        correct_index=rendered.correct_index,
        visual=visual,
        params_used=rendered.params_used,
    )


def _attempt_to_response(session_id: str, result: AttemptResult, **extra) -> SessionResponse:
    question_out = None
    if result.rendered_question is not None:
        question_out = _rendered_to_question_out(result.rendered_question)

    return SessionResponse(
        session_id=session_id,
        question=question_out,
        feedback_message=result.feedback_message,
        misconception_diagnosis=result.misconception_diagnosis,
        mascot_emotion=result.mascot_emotion,
        is_step_down=result.is_step_down,
        session_complete=result.session_complete,
        concept_mastered=result.concept_mastered,
        suggest_next_concept=result.suggest_next_concept,
        mastery_snapshot=result.mastery_snapshot,
        retry_same_question=result.retry_same_question,
        scaffold_level=result.scaffold_level,
        session_stats=result.session_stats,
        **extra,
    )


def compute_review_queue(mastery_states: Dict[str, Dict[str, Any]], concept_graph: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Compute concepts due for spaced-repetition review.

    Uses a simple interval schedule based on mastery level:
        learning: 1 day, familiar: 3 days, proficient: 7 days, mastered: 14 days.
    Concepts with mastery_label 'new' or without a last_practised timestamp are skipped.

    Returns a list of due concepts sorted by urgency (most overdue first).
    """
    INTERVALS = {
        "learning": 1,
        "familiar": 3,
        "proficient": 7,
        "mastered": 14,
    }

    now = datetime.now(timezone.utc)
    due_items: List[Dict[str, Any]] = []

    # Build a lookup for display names from the concept graph.
    display_names: Dict[str, str] = {}
    if concept_graph and hasattr(concept_graph, "nodes"):
        for node in concept_graph.nodes:
            display_names[node.concept_id] = node.display_name

    for concept_id, data in mastery_states.items():
        mastery_label = data.get("mastery_label", "new")
        if mastery_label == "new" or mastery_label not in INTERVALS:
            continue

        last_practised_raw = data.get("last_practised")
        if not last_practised_raw:
            continue

        # Parse ISO timestamp.
        try:
            if isinstance(last_practised_raw, str):
                # Handle both with and without timezone info.
                lp = datetime.fromisoformat(last_practised_raw.replace("Z", "+00:00"))
            else:
                # Already a datetime (e.g. from Firestore).
                lp = last_practised_raw
                if lp.tzinfo is None:
                    lp = lp.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

        days_since = (now - lp).total_seconds() / 86400.0
        interval = INTERVALS[mastery_label]

        if days_since >= interval:
            overdue_ratio = days_since / interval
            if overdue_ratio >= 2.0:
                urgency = "overdue"
            else:
                urgency = "due"

            display_name = display_names.get(concept_id, concept_id.replace(".", " ").replace("_", " ").title())

            due_items.append({
                "concept_id": concept_id,
                "display_name": display_name,
                "mastery_label": mastery_label,
                "days_since_practice": round(days_since, 1),
                "urgency": urgency,
            })

    # Sort by most overdue first (highest days_since / interval ratio).
    due_items.sort(
        key=lambda x: x["days_since_practice"] / INTERVALS.get(x["mastery_label"], 1),
        reverse=True,
    )

    return due_items


def _flush_session(session_id: str, session: SessionState) -> Dict[str, Any]:
    """Persist session results to Firestore when a session completes.

    Returns rewards dict and updated user profile.
    """
    uid = session.user_id

    # 1. Save mastery states.
    mastery_to_save = {}
    for cid, snap in session.mastery_states.items():
        mastery_to_save[cid] = {
            "internal_score": round(snap.internal_score, 4),
            "shown_score": snap.shown_score,
            "mastery_label": snap.mastery_label,
            "total_attempts": snap.total_attempts,
            "streak_current": snap.streak_current,
        }
    save_mastery_states(uid, mastery_to_save)

    # 2. Compute rewards.
    total_correct = session.correct_streak  # approximate — use session stats if available
    total_questions = session.total_attempts
    # Better: count from questions_served vs correct
    parent_correct = 0
    for qid in session.questions_served:
        # We don't have per-question results stored, so use the streak as proxy.
        pass
    # Use the total_attempts and correct_streak from session.
    total_correct = session.total_attempts - session.wrong_streak  # rough
    rewards = compute_session_rewards(
        total_correct=max(0, session.parent_questions_served),  # safe fallback
        total_questions=max(1, session.parent_questions_served),
        streak=session.correct_streak,
    )

    # 3. Update gamification.
    updated_profile = update_gamification_on_session_end(
        uid=uid,
        xp_earned=rewards["xp_earned"],
        gems_earned=rewards["gems_earned"],
        questions_completed=session.parent_questions_served,
    )

    # 4. Save session log.
    meta = _session_meta.get(session_id, {})
    save_session_log(uid, session_id, {
        "concept_id": session.concept_id,
        "started_at": meta.get("started_at"),
        "parent_questions": session.parent_questions_served,
        "total_questions": len(session.questions_served),
        "questions_served": session.questions_served,
        "concepts_touched": session.concepts_touched,
        "mastery_after": mastery_to_save,
        "rewards": rewards,
    })

    # 5. Cleanup.
    _sessions.pop(session_id, None)
    _session_meta.pop(session_id, None)

    return {"rewards": rewards, "user_profile": updated_profile}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/start", response_model=SessionResponse)
def start_session(req: StartSessionRequest):
    """Start a new adaptive learning session for a concept."""
    engine = _get_engine()

    # Load mastery from Firestore if not provided by client.
    mastery_states: Optional[Dict[str, MasterySnapshot]] = None
    if req.mastery_states:
        mastery_states = {}
        for cid, data in req.mastery_states.items():
            mastery_states[cid] = MasterySnapshot(
                internal_score=data.get("internal_score", 0.0),
                shown_score=data.get("shown_score", 0),
                mastery_label=data.get("mastery_label", "new"),
                total_attempts=data.get("total_attempts", 0),
                streak_current=data.get("streak_current", 0),
            )
    else:
        # Load from Firestore.
        stored = get_mastery_states(req.user_id)
        if stored:
            mastery_states = {}
            for cid, data in stored.items():
                mastery_states[cid] = MasterySnapshot(
                    internal_score=data.get("internal_score", 0.0),
                    shown_score=data.get("shown_score", 0),
                    mastery_label=data.get("mastery_label", "new"),
                    total_attempts=data.get("total_attempts", 0),
                    streak_current=data.get("streak_current", 0),
                )

    session = engine.start_session(
        user_id=req.user_id,
        concept_id=req.concept_id,
        mastery_states=mastery_states,
    )

    session_id = hashlib.md5(
        f"{req.user_id}:{req.concept_id}:{time.time()}".encode()
    ).hexdigest()[:12]

    _sessions[session_id] = session
    _session_meta[session_id] = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user_id": req.user_id,
    }

    result = engine.next_question(session)
    return _attempt_to_response(session_id, result)


@router.post("/answer", response_model=SessionResponse)
def submit_answer(req: AnswerRequest):
    """Submit an answer and get the next question or feedback."""
    session = _sessions.get(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{req.session_id}' not found")

    engine = _get_engine()

    try:
        result = engine.submit_answer(
            session=session,
            question_id=req.question_id,
            selected_option_index=req.selected_option_index,
            time_taken_ms=req.time_taken_ms,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if (
        result.rendered_question is None
        and result.next_question_id is not None
        and not result.session_complete
    ):
        next_result = engine.next_question(session)
        next_result.feedback_message = result.feedback_message or next_result.feedback_message
        next_result.misconception_diagnosis = result.misconception_diagnosis
        next_result.mascot_emotion = result.mascot_emotion
        # Preserve scaffolding flags from the original answer result.
        next_result.is_step_down = result.is_step_down or next_result.is_step_down
        next_result.scaffold_level = result.scaffold_level or next_result.scaffold_level
        next_result.retry_same_question = result.retry_same_question
        result = next_result

    # If session is complete, flush to Firestore and include rewards.
    extra = {}
    if result.session_complete:
        flush_data = _flush_session(req.session_id, session)
        extra["rewards"] = flush_data["rewards"]
        extra["user_profile"] = flush_data["user_profile"]

    return _attempt_to_response(req.session_id, result, **extra)


@router.get("/state", response_model=Dict[str, Any])
def session_state(session_id: str = Query(...)):
    """Debug endpoint: peek at the raw session state."""
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    return {
        "session_id": session_id,
        "user_id": session.user_id,
        "concept_id": session.concept_id,
        "parent_questions_served": session.parent_questions_served,
        "total_questions_served": len(session.questions_served),
        "correct_streak": session.correct_streak,
        "wrong_streak": session.wrong_streak,
        "current_question_id": session.current_question_id,
        "current_phase": session.current_phase.value,
        "step_down_queue": session.step_down_queue,
        "questions_served": session.questions_served,
        "concepts_touched": session.concepts_touched,
        "mastery_states": {
            cid: {
                "internal_score": round(snap.internal_score, 3),
                "shown_score": snap.shown_score,
                "mastery_label": snap.mastery_label,
                "total_attempts": snap.total_attempts,
                "streak_current": snap.streak_current,
            }
            for cid, snap in session.mastery_states.items()
        },
    }


@router.get("/concepts", response_model=List[Dict[str, Any]])
def list_concepts(
    grade: Optional[int] = Query(None, ge=1, le=5, description="Filter to a specific grade (1-5)"),
):
    """List all concepts from the loaded concept graph, optionally filtered by grade."""
    engine = _get_engine()
    if _concept_graph is None or not _concept_graph.nodes:
        return []
    nodes = _concept_graph.nodes
    if grade is not None:
        nodes = [n for n in nodes if getattr(n, "concept_id", "").startswith(f"g{grade}.")]
        # Also try G{grade}. prefix pattern
        if not nodes:
            nodes = [n for n in _concept_graph.nodes
                     if f"grade{grade}" in getattr(n, "concept_id", "").lower()
                     or getattr(n, "concept_id", "").startswith(f"g{grade}.")]
    return [
        {
            "concept_id": n.concept_id,
            "display_name": n.display_name,
            "description": n.description,
            "world_region": getattr(n, "world_region", None),
            "topic_branch": getattr(n, "topic_branch", None),
            "question_count": len(engine._get_questions_for_concept(n.concept_id)),
        }
        for n in nodes
    ]


@router.get("/learning-path", response_model=Dict[str, Any])
def learning_path(
    user_id: str = Query(..., description="User identifier (Firebase UID)"),
    grade: Optional[int] = Query(None, ge=1, le=5, description="Filter to a specific grade (1-5)"),
):
    """Return the recommended learning path for a user.

    Topologically sorts concepts from the concept graph and marks each with
    a status based on the user's mastery state:
      - "locked": hard prerequisites not met
      - "ready": prerequisites met, not yet started
      - "in_progress": started but not mastered
      - "mastered": mastery label is "mastered"

    Also includes the suggested next concept to practise.
    """
    engine = _get_engine()

    # Load mastery from Firestore.
    stored = get_mastery_states(user_id)
    mastery_states: Dict[str, MasterySnapshot] = {}
    if stored:
        for cid, data in stored.items():
            mastery_states[cid] = MasterySnapshot(
                internal_score=data.get("internal_score", 0.0),
                shown_score=data.get("shown_score", 0),
                mastery_label=data.get("mastery_label", "new"),
                total_attempts=data.get("total_attempts", 0),
                streak_current=data.get("streak_current", 0),
            )

    # Build the learning path.
    path = engine.get_learning_path(mastery_states)

    # Suggest the next concept.
    suggest_next = engine.suggest_next_concept_for_user(
        mastery_states=mastery_states,
    )

    # Compute summary stats.
    total = len(path)
    mastered_count = sum(1 for p in path if p["status"] == "mastered")
    in_progress_count = sum(1 for p in path if p["status"] == "in_progress")
    ready_count = sum(1 for p in path if p["status"] == "ready")
    locked_count = sum(1 for p in path if p["status"] == "locked")

    return {
        "user_id": user_id,
        "suggest_next_concept": suggest_next,
        "summary": {
            "total": total,
            "mastered": mastered_count,
            "in_progress": in_progress_count,
            "ready": ready_count,
            "locked": locked_count,
        },
        "path": path,
    }


@router.get("/review-queue", response_model=List[Dict[str, Any]])
def get_review_queue(user_id: str = Query(..., description="Firebase UID")):
    """Return concepts due for spaced-repetition review, sorted by urgency.

    Uses a simple interval schedule based on mastery level:
        learning: 1 day, familiar: 3 days, proficient: 7 days, mastered: 14 days.
    """
    # Ensure concept graph is loaded (needed for display names).
    _get_engine()

    mastery_states = get_mastery_states(user_id)
    if not mastery_states:
        return []

    return compute_review_queue(mastery_states, _concept_graph)
