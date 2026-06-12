"""
Kiwimath Question Bookmarking API — save questions for later review.

Students can bookmark questions during practice and review them later
from the Saved Questions screen.

Endpoints:
    POST /v2/bookmarks/toggle     — toggle bookmark on/off for a question
    GET  /v2/bookmarks/list       — get user's bookmarked questions (paginated)
    GET  /v2/bookmarks/check      — check if a specific question is bookmarked
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.bookmark_store import (
    count as bookmark_count,
    get_all as bookmark_get_all,
    is_bookmarked as bookmark_is_bookmarked,
    toggle_bookmark,
)
from app.services.content_store_v2 import store_v2

router = APIRouter(prefix="/v2/bookmarks", tags=["Bookmarks"])


# ── Request / Response models ─────────────────────────────────────


class BookmarkToggleRequest(BaseModel):
    user_id: str
    question_id: str


class BookmarkToggleResponse(BaseModel):
    bookmarked: bool
    total_bookmarks: int


class BookmarkCheckResponse(BaseModel):
    bookmarked: bool


# ── Endpoints ─────────────────────────────────────────────────────


@router.post("/toggle", response_model=BookmarkToggleResponse)
def toggle(req: BookmarkToggleRequest):
    """Toggle bookmark on/off for a question.

    If the question is currently bookmarked, it will be un-bookmarked,
    and vice versa.
    """
    now_bookmarked = toggle_bookmark(req.user_id, req.question_id)
    total = bookmark_count(req.user_id)
    return BookmarkToggleResponse(bookmarked=now_bookmarked, total_bookmarks=total)


@router.get("/list")
def list_bookmarks(
    user_id: str = Query(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
) -> Dict[str, Any]:
    """Get user's bookmarked questions with full question data.

    Returns paginated list of bookmarked question objects.
    """
    all_bookmarks = bookmark_get_all(user_id)
    total = len(all_bookmarks)

    # Paginate
    start = (page - 1) * per_page
    end = start + per_page
    page_bookmarks = all_bookmarks[start:end]

    # Enrich with full question data from content store
    questions: List[Dict[str, Any]] = []
    for bm in page_bookmarks:
        qid = bm["question_id"]
        question_data = _get_question_data(qid)
        if question_data:
            question_data["bookmarked_at"] = bm.get("bookmarked_at")
            questions.append(question_data)
        else:
            # Question may have been removed from content — still show stub
            questions.append({
                "id": qid,
                "stem": "(Question no longer available)",
                "topic": "unknown",
                "difficulty_score": 0,
                "bookmarked_at": bm.get("bookmarked_at"),
            })

    return {
        "questions": questions,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


@router.get("/check", response_model=BookmarkCheckResponse)
def check_bookmark(
    user_id: str = Query(..., description="User ID"),
    question_id: str = Query(..., description="Question ID"),
):
    """Check if a specific question is bookmarked by the user."""
    return BookmarkCheckResponse(bookmarked=bookmark_is_bookmarked(user_id, question_id))


# ── Helpers ───────────────────────────────────────────────────────


def _get_question_data(question_id: str) -> Optional[Dict[str, Any]]:
    """Load full question data from v2 content store."""
    try:
        q = store_v2.get(question_id)
        if q:
            return {
                "id": q.id,
                "stem": q.stem,
                "choices": q.choices,
                "correct_answer": q.correct_answer,
                "difficulty_score": q.difficulty_score,
                "chapter": q.chapter,
                "topic": getattr(q, "topic", None) or getattr(q, "chapter", ""),
                "tags": q.tags,
                "hint": q.hint if hasattr(q, "hint") else None,
                "interaction_mode": getattr(q, "interaction_mode", "mcq"),
            }
    except Exception:
        pass
    return None
