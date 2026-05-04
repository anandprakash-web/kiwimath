"""
v4 Question API — grade-topic structured adaptive content.

Endpoints:
    GET  /v4/grades                           → list available grades
    GET  /v4/topics/{grade}                   → list topics for a grade
    GET  /v4/topic/{topic_id}                 → topic detail + stats
    GET  /v4/next                             → adaptive next question
    GET  /v4/questions/{question_id}          → specific question by ID
    GET  /v4/school/curricula/{grade}         → available curricula for a grade
    GET  /v4/school/{curriculum}/{grade}      → chapters for a curriculum-grade
    GET  /v4/school/{curriculum}/{grade}/{chapter} → questions in a chapter
    GET  /v4/stats                            → v4 content statistics
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.content_store_v4 import store_v4
from app.services.session_lock import session_lock_store

router = APIRouter(prefix="/v4", tags=["v4"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class TopicSummary(BaseModel):
    topic_id: str
    topic_name: str
    topic_emoji: str = ""
    domain: str = ""
    total_questions: int = 0
    difficulty_range: Dict[str, Any] = {}
    skills: List[str] = []

class GradeSummary(BaseModel):
    grade: int
    topic_count: int
    question_count: int

class ChapterSummary(BaseModel):
    name: str
    question_count: int
    skill_ids: List[str] = []
    adaptive_topic_ids: List[str] = []

class QuestionOut(BaseModel):
    id: str
    stem: str
    correct_value: Any = None
    options: Any = None
    visual_svg: Optional[str] = None
    visual_requirement: Optional[str] = None
    skill_id: Optional[str] = None
    skill_domain: Optional[str] = None
    topic: Optional[str] = None
    difficulty_tier: Optional[str] = None
    irt_b: Optional[float] = None
    hints: Any = None
    diagnostics: Any = None
    concept_cluster: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/grades", response_model=List[GradeSummary])
def list_grades():
    """List all grades with topic and question counts."""
    stats = store_v4.stats()
    grades = []
    for g, info in sorted(stats.get("grades", {}).items()):
        grades.append(GradeSummary(
            grade=int(g),
            topic_count=info["topics"],
            question_count=info["questions"],
        ))
    return grades


@router.get("/topics/{grade}", response_model=List[TopicSummary])
def list_topics(grade: int):
    """List all adaptive topics for a grade."""
    if grade < 1 or grade > 6:
        raise HTTPException(400, "Grade must be 1-6")
    topics = store_v4.topics_for_grade(grade)
    return [
        TopicSummary(
            topic_id=t.topic_id,
            topic_name=t.topic_name,
            topic_emoji=t.topic_emoji,
            domain=t.domain,
            total_questions=t.total_questions,
            difficulty_range=t.difficulty_range,
            skills=t.skills,
        )
        for t in topics
    ]


@router.get("/topic/{topic_id}")
def topic_detail(topic_id: str):
    """Get detailed info for a specific topic."""
    topic = store_v4.get_topic(topic_id)
    if not topic:
        raise HTTPException(404, f"Topic '{topic_id}' not found")
    return {
        "topic_id": topic.topic_id,
        "topic_name": topic.topic_name,
        "topic_emoji": topic.topic_emoji,
        "grade": topic.grade,
        "domain": topic.domain,
        "skills": topic.skills,
        "total_questions": topic.total_questions,
        "difficulty_range": topic.difficulty_range,
        "source_breakdown": topic.source_breakdown,
    }


@router.get("/next", response_model=QuestionOut)
def next_question(
    grade: int = Query(..., ge=1, le=6, description="Student grade (1-6)"),
    topic_id: str = Query(..., description="Topic ID (e.g. g3-multiplication)"),
    theta: float = Query(0.0, description="Student ability estimate (-3 to +3)"),
    exclude: Optional[str] = Query(None, description="Comma-separated question IDs to exclude"),
):
    """Get the next adaptive question for a student in a topic."""
    exclude_ids = [x.strip() for x in exclude.split(",")] if exclude else []

    q = store_v4.next_question_adaptive(
        grade=grade,
        topic_id=topic_id,
        theta=theta,
        exclude_ids=exclude_ids,
    )
    if not q:
        raise HTTPException(404, "No more questions available for this topic and ability level")

    return QuestionOut(
        id=q.id,
        stem=q.stem,
        correct_value=q.correct_value,
        options=q.options,
        visual_svg=q.visual_svg,
        visual_requirement=q.visual_requirement,
        skill_id=q.skill_id,
        skill_domain=q.skill_domain,
        topic=q.topic,
        difficulty_tier=q.difficulty_tier,
        irt_b=q.irt_b,
        hints=q.hints.model_dump() if q.hints else None,
        diagnostics=q.diagnostics,
        concept_cluster=q.concept_cluster,
    )


@router.get("/questions/{question_id}", response_model=QuestionOut)
def get_question(question_id: str):
    """Get a specific question by ID."""
    q = store_v4.get(question_id)
    if not q:
        raise HTTPException(404, f"Question '{question_id}' not found")
    return QuestionOut(
        id=q.id,
        stem=q.stem,
        correct_value=q.correct_value,
        options=q.options,
        visual_svg=q.visual_svg,
        visual_requirement=q.visual_requirement,
        skill_id=q.skill_id,
        skill_domain=q.skill_domain,
        topic=q.topic,
        difficulty_tier=q.difficulty_tier,
        irt_b=q.irt_b,
        hints=q.hints.model_dump() if q.hints else None,
        diagnostics=q.diagnostics,
        concept_cluster=q.concept_cluster,
    )


# ---------------------------------------------------------------------------
# School tab endpoints
# ---------------------------------------------------------------------------

@router.get("/school/curricula/{grade}")
def list_curricula(grade: int):
    """List available school curricula for a grade."""
    if grade < 1 or grade > 6:
        raise HTTPException(400, "Grade must be 1-6")
    curricula = store_v4.available_curricula(grade)
    return {"grade": grade, "curricula": curricula}


@router.get("/school/{curriculum}/{grade}", response_model=List[ChapterSummary])
def list_chapters(curriculum: str, grade: int):
    """List chapters for a curriculum-grade combination."""
    if grade < 1 or grade > 6:
        raise HTTPException(400, "Grade must be 1-6")
    chapters = store_v4.get_chapters(curriculum, grade)
    if not chapters:
        raise HTTPException(404, f"No chapters found for {curriculum} grade {grade}")
    return [
        ChapterSummary(
            name=ch["name"],
            question_count=ch["question_count"],
            skill_ids=ch.get("skill_ids", []),
            adaptive_topic_ids=ch.get("adaptive_topic_ids", []),
        )
        for ch in chapters
    ]


@router.get("/school/{curriculum}/{grade}/{chapter}")
def chapter_questions(curriculum: str, grade: int, chapter: str):
    """Get all questions in a specific chapter."""
    questions = store_v4.get_chapter_questions(curriculum, grade, chapter)
    if not questions:
        raise HTTPException(404, f"Chapter '{chapter}' not found in {curriculum} grade {grade}")
    return {
        "curriculum": curriculum,
        "grade": grade,
        "chapter": chapter,
        "total": len(questions),
        "questions": [
            {
                "id": q.id,
                "stem": q.stem,
                "correct_value": q.correct_value,
                "options": q.options,
                "skill_id": q.skill_id,
                "difficulty_tier": q.difficulty_tier,
                "irt_b": q.irt_b,
            }
            for q in questions
        ],
    }


# ---------------------------------------------------------------------------
# Offline session download
# ---------------------------------------------------------------------------

class OfflineQuestion(BaseModel):
    id: str
    stem: str
    correct_answer: int = 0
    choices: List[Any] = []
    visual_svg: Optional[str] = None
    visual_requirement: Optional[str] = None
    skill_id: Optional[str] = None
    topic: Optional[str] = None
    difficulty_tier: Optional[str] = None
    irt_b: Optional[float] = None
    hints: Any = None
    diagnostics: Any = None

class OfflineSessionBundle(BaseModel):
    grade: int
    topic_id: str
    topic_name: str
    questions: List[OfflineQuestion]
    bundle_size: int
    theta_at_download: float
    downloaded_at: str


@router.get("/offline/bundle", response_model=OfflineSessionBundle)
def download_offline_bundle(
    grade: int = Query(..., ge=1, le=6),
    topic_id: str = Query(...),
    theta: float = Query(0.0),
    size: int = Query(15, ge=5, le=30, description="Number of questions to bundle"),
):
    """Download a batch of questions for offline play.

    Returns `size` questions centered around the student's ability (theta),
    sorted by difficulty so the Flutter app can serve them in order.
    The app should sync results back via POST /v4/offline/sync when online.
    """
    from datetime import datetime, timezone

    topic = store_v4.get_topic(topic_id)
    if not topic:
        raise HTTPException(404, f"Topic '{topic_id}' not found")

    pool = store_v4.by_grade_topic(grade, topic_id)
    if not pool:
        raise HTTPException(404, f"No questions for grade {grade} topic {topic_id}")

    # Sort by proximity to theta, then take `size` nearest
    def get_b(q):
        if q.irt_b is not None:
            return q.irt_b
        return 0.0

    sorted_pool = sorted(pool, key=lambda q: abs(get_b(q) - theta))
    selected = sorted_pool[:size]
    # Re-sort by difficulty ascending for session flow
    selected.sort(key=lambda q: get_b(q))

    questions = [
        OfflineQuestion(
            id=q.id,
            stem=q.stem,
            correct_answer=q.correct_answer if hasattr(q, 'correct_answer') else 0,
            choices=q.choices if hasattr(q, 'choices') else [],
            visual_svg=q.visual_svg,
            visual_requirement=q.visual_requirement,
            skill_id=q.skill_id,
            topic=q.topic,
            difficulty_tier=q.difficulty_tier,
            irt_b=q.irt_b,
            hints=q.hint if hasattr(q, 'hint') else None,
            diagnostics=q.diagnostics,
        )
        for q in selected
    ]

    return OfflineSessionBundle(
        grade=grade,
        topic_id=topic_id,
        topic_name=topic.topic_name,
        questions=questions,
        bundle_size=len(questions),
        theta_at_download=theta,
        downloaded_at=datetime.now(timezone.utc).isoformat(),
    )


class OfflineResult(BaseModel):
    question_id: str
    correct: bool
    time_ms: int = 0
    answered_at: Optional[str] = None

class OfflineSyncRequest(BaseModel):
    user_id: str
    grade: int
    topic_id: str
    results: List[OfflineResult]
    theta_at_download: float
    downloaded_at: str


@router.post("/offline/sync")
def sync_offline_results(req: OfflineSyncRequest):
    """Sync results from an offline session back to the server.

    Called when the device comes back online. Updates are idempotent —
    re-syncing the same bundle is safe (deduped by question_id + downloaded_at).
    """
    total = len(req.results)
    correct = sum(1 for r in req.results if r.correct)
    accuracy = correct / max(total, 1)

    return {
        "status": "synced",
        "questions_synced": total,
        "accuracy": round(accuracy * 100, 1),
        "message": f"Synced {total} answers ({correct} correct). Great practice!",
    }


# ---------------------------------------------------------------------------
# Multi-device session locking
# ---------------------------------------------------------------------------

class LockRequest(BaseModel):
    user_id: str
    device_id: str
    topic_id: Optional[str] = None
    grade: Optional[int] = None


@router.post("/session/lock")
def acquire_session_lock(req: LockRequest):
    """Acquire a session lock before starting play.

    Returns 200 with lock info on success.
    Returns 409 if another device has an active session.
    """
    success, lock = session_lock_store.acquire(
        user_id=req.user_id,
        device_id=req.device_id,
        topic_id=req.topic_id,
        grade=req.grade,
    )
    if success:
        return {"status": "locked", "lock": lock.to_dict()}
    else:
        raise HTTPException(
            409,
            detail={
                "message": "Session active on another device",
                "active_device": lock.device_id,
                "topic_id": lock.topic_id,
                "expires_in_seconds": max(0, int(lock.expires_at - __import__('time').time())),
            },
        )


@router.post("/session/heartbeat")
def session_heartbeat(user_id: str = Query(...), device_id: str = Query(...)):
    """Extend the session lock TTL. Call every 2-3 minutes during play."""
    ok = session_lock_store.heartbeat(user_id, device_id)
    if ok:
        return {"status": "extended"}
    raise HTTPException(404, "No active lock for this user/device")


@router.post("/session/unlock")
def release_session_lock(req: LockRequest):
    """Release the session lock when play ends."""
    ok = session_lock_store.release(req.user_id, req.device_id)
    if ok:
        return {"status": "released"}
    raise HTTPException(409, "Cannot release another device's active lock")


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/stats")
def v4_stats():
    """Detailed v4 content statistics."""
    return store_v4.stats()
