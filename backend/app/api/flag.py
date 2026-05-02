"""
Kiwimath Question Flagging API — closed-loop quality system.

Students and parents can flag problematic questions. Flags are stored
in-memory and exposed via summary/analysis endpoints for quality review.

Endpoints:
    POST /flag/submit                — submit a flag on a question
    GET  /flag/summary               — aggregated flag summary
    GET  /flag/question/{question_id} — flags for a specific question
    GET  /flag/analysis              — AI-ready analysis for quality review
    GET  /flag/review-queue          — flagged questions with full content for immediate fix
    POST /flag/resolve/{flag_id}     — mark a flag as resolved
    POST /flag/diagnostic-review     — submit diagnostic test review (batch of flags with reasons)
"""

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.content_store_v2 import store_v2
from app.services.flag_store import FlagType, flag_store

router = APIRouter(prefix="/flag", tags=["Question Flagging"])


# ── Request / Response models ─────────────────────────────────────


class FlagSubmitRequest(BaseModel):
    question_id: str
    student_id: str
    flag_type: FlagType
    comment: Optional[str] = None
    session_id: Optional[str] = None


class FlagSubmitResponse(BaseModel):
    flag_id: str
    status: str = "received"


# ── Endpoints ─────────────────────────────────────────────────────


@router.post("/submit", response_model=FlagSubmitResponse)
def submit_flag(req: FlagSubmitRequest):
    """Submit a flag on a question.

    Flag types: answer_error, hint_not_good, visual_missing,
    visual_mismatch, question_error, other.
    """
    flag = flag_store.add_flag(
        question_id=req.question_id,
        student_id=req.student_id,
        flag_type=req.flag_type,
        comment=req.comment,
        session_id=req.session_id,
    )
    return FlagSubmitResponse(flag_id=flag["flag_id"])


@router.get("/summary")
def flag_summary():
    """Get summary of all flags for analysis.

    Returns count by flag_type, list of flagged question_ids
    with details, sorted by frequency.
    """
    return flag_store.summary()


@router.get("/question/{question_id}")
def flags_for_question(question_id: str):
    """Get all flags for a specific question."""
    flags = flag_store.get_by_question(question_id)
    return {"question_id": question_id, "total": len(flags), "flags": flags}


@router.get("/analysis")
def flag_analysis():
    """AI-ready analysis endpoint.

    Groups flags by question, identifies most-flagged questions,
    and returns structured data ready for quality review.
    """
    return flag_store.analysis()


# ── Diagnostic Review Endpoints ──────────────────────────────────


class DiagnosticReviewItem(BaseModel):
    question_id: str
    flag_type: FlagType = FlagType.diagnostic_review
    reason: str = Field(..., description="Why this question is flagged (specific issue)")
    grade: Optional[int] = None
    severity: str = Field(default="medium", description="low | medium | high | critical")


class DiagnosticReviewBatch(BaseModel):
    reviewer_id: str = Field(default="admin", description="Who is reviewing (e.g. 'anand')")
    items: List[DiagnosticReviewItem]
    session_notes: Optional[str] = None


class DiagnosticReviewResponse(BaseModel):
    flags_created: int
    review_queue_size: int
    status: str = "logged"


@router.post("/diagnostic-review", response_model=DiagnosticReviewResponse)
def submit_diagnostic_review(req: DiagnosticReviewBatch):
    """Submit a batch of diagnostic test flags with reasons.

    Used by admin (Anand) to flag questions during diagnostic test review.
    Each flag includes a specific reason explaining what's wrong.
    """
    created = 0
    for item in req.items:
        comment = f"[{item.severity.upper()}] {item.reason}"
        if item.grade:
            comment = f"[G{item.grade}] {comment}"
        flag_store.add_flag(
            question_id=item.question_id,
            student_id=req.reviewer_id,
            flag_type=item.flag_type,
            comment=comment,
            session_id=f"diagnostic_review_{req.reviewer_id}",
        )
        created += 1

    return DiagnosticReviewResponse(
        flags_created=created,
        review_queue_size=len(flag_store.get_all()),
    )


@router.get("/review-queue")
def review_queue(grade: Optional[int] = None, severity: Optional[str] = None):
    """Get flagged questions with full question content for immediate fix.

    Returns enriched queue: flag details + full question data from content store.
    Filter by grade or severity.
    """
    analysis = flag_store.analysis()
    queue = []

    for item in analysis.get("questions", []):
        qid = item["question_id"]

        # Get full question content
        question_data = None
        try:
            q = store_v2.get(qid)
            if q:
                question_data = {
                    "id": q.id,
                    "stem": q.stem,
                    "choices": q.choices,
                    "correct_answer": q.correct_answer,
                    "difficulty_score": q.difficulty_score,
                    "chapter": q.chapter,
                    "hint": q.hint if hasattr(q, "hint") else None,
                    "diagnostics": q.diagnostics if hasattr(q, "diagnostics") else None,
                    "tags": q.tags,
                    "interaction_mode": getattr(q, "interaction_mode", "mcq"),
                }
        except Exception:
            pass

        entry = {
            "question_id": qid,
            "total_flags": item["total_flags"],
            "priority": item["priority"],
            "dominant_issue": item["dominant_issue"],
            "comments": item["comments"],
            "question_data": question_data,
        }

        # Filter by grade if requested
        if grade and question_data:
            q_grade = None
            if "-G" in qid:
                try:
                    q_grade = int(qid.split("-G")[1].split("-")[0])
                except (IndexError, ValueError):
                    pass
            if q_grade and q_grade != grade:
                continue

        # Filter by severity if requested
        if severity:
            has_severity = any(f"[{severity.upper()}]" in c for c in item["comments"])
            if not has_severity:
                continue

        queue.append(entry)

    return {
        "total_in_queue": len(queue),
        "items": queue,
    }


@router.post("/resolve/{flag_id}")
def resolve_flag(flag_id: str, resolution: str = "fixed"):
    """Mark a flag as resolved.

    Removes it from the active queue. Logs the resolution.
    """
    with flag_store._lock:
        for i, f in enumerate(flag_store._flags):
            if f["flag_id"] == flag_id:
                f["resolved"] = True
                f["resolution"] = resolution
                return {"status": "resolved", "flag_id": flag_id}
    return {"status": "not_found", "flag_id": flag_id}
