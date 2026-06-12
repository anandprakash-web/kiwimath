"""
Admin content review API — review, approve, flag, and auto-fix questions.

Endpoints:
    GET  /admin/review/questions  — paginated questions for review
    POST /admin/review/approve    — approve a question
    POST /admin/review/flag       — flag with optional auto-fix
    GET  /admin/review/stats      — dashboard stats
    GET  /admin/review/changelog  — auto-fix history
    GET  /admin/verify            — check if email is admin
"""

import json
import logging
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.admin_store import admin_review_store, is_admin
from app.services.content_store_v2 import QuestionV2, store_v2
from app.services.content_store_v4 import store_v4
from app.services.ncert_content_store import ncert_store
from app.services.singapore_content_store import singapore_store
from app.services.uscc_content_store import uscc_store
from app.services.icse_content_store import icse_store

logger = logging.getLogger("kiwimath.admin_review")

router = APIRouter(tags=["Admin Review"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_admin(email: str):
    if not is_admin(email):
        raise HTTPException(status_code=403, detail="Not an admin")


def _find_question(question_id: str) -> Optional[QuestionV2]:
    """Look up a question across all stores."""
    q = store_v2.get(question_id)
    if q:
        return q
    q = store_v4.get(question_id)
    if q:
        return q
    return None


def _find_question_dict(question_id: str) -> Optional[Dict[str, Any]]:
    """Look up a question as a dict from curriculum stores."""
    for store in (ncert_store, singapore_store, uscc_store, icse_store):
        d = store._questions.get(question_id)
        if d:
            return d
    return None


def _question_to_dict(q: QuestionV2) -> Dict[str, Any]:
    return {
        "id": q.id,
        "stem": q.stem,
        "choices": q.choices,
        "correct_answer": q.correct_answer,
        "difficulty_score": q.difficulty_score,
        "difficulty_tier": q.difficulty_tier,
        "topic": q.topic,
        "topic_name": q.topic_name,
        "chapter": q.chapter,
        "hint": q.hint,
        "solution_steps": q.solution_steps,
        "tags": q.tags,
        "interaction_mode": q.interaction_mode,
        "curriculum_source": q.curriculum_source,
        "school_grade": q.school_grade,
    }


def _extract_grade(question_id: str) -> Optional[int]:
    """Extract grade from question ID like NCERT-G3-001 or T1-001-G2-L1."""
    import re
    m = re.search(r"-G(\d)", question_id)
    return int(m.group(1)) if m else None


def _find_source_json_path(question_id: str) -> Optional[str]:
    """Find the JSON file on disk containing a question ID."""
    root = store_v2._root
    if not root:
        return None
    for json_file in root.rglob("*.json"):
        try:
            text = json_file.read_text()
            if question_id in text:
                return str(json_file)
        except Exception:
            continue
    return None


def _update_question_in_file(filepath: str, question_id: str, field: str, new_value: Any) -> Any:
    """Update a field in a question's source JSON file. Returns old value."""
    data = json.loads(open(filepath).read())
    questions = data.get("questions", data) if isinstance(data, dict) else data
    if not isinstance(questions, list):
        questions = data.get("questions", [])

    for q in questions:
        if q.get("id") == question_id:
            old_value = q.get(field)
            q[field] = new_value
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return old_value
    return None


def _regenerate_hint(q: QuestionV2) -> Dict[str, str]:
    """Regenerate hint ladder from solution steps."""
    steps = q.solution_steps or []
    if not steps:
        return {
            "level_0": "Take a moment to re-read the question carefully.",
            "level_1": f"Look at: {q.stem[:60]}...",
            "level_2": "What operation might help here?",
            "level_3": "Try breaking the problem into smaller steps.",
            "level_4": f"The answer involves one of: {', '.join(q.choices[:2])}...",
            "level_5": f"The correct answer is option {q.correct_answer}.",
        }
    return {
        "level_0": "Pause and re-read the question. What is it asking?",
        "level_1": f"Focus on: {steps[0]}" if steps else "Look at the numbers in the problem.",
        "level_2": f"Think about: {steps[1]}" if len(steps) > 1 else "What operation connects the numbers?",
        "level_3": f"Step-by-step: {steps[len(steps)//2]}" if steps else "Break it down.",
        "level_4": f"Almost there: {steps[-1]}" if steps else "You're close to the answer.",
        "level_5": f"The answer is {q.choices[q.correct_answer] if q.choices else 'option ' + str(q.correct_answer)}. Here's why: {'; '.join(steps)}",
    }


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ApproveRequest(BaseModel):
    question_id: str
    reviewer_email: str


class FlagRequest(BaseModel):
    question_id: str
    reviewer_email: str
    flag_type: Literal[
        "wrong_answer", "bad_hint", "bad_stem", "needs_visual",
        "wrong_difficulty", "duplicate", "other"
    ]
    comment: str = ""
    correct_answer: Optional[int] = None  # for wrong_answer fix


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/admin/review/questions")
def list_questions_for_review(
    grade: Optional[int] = Query(None),
    topic: Optional[str] = Query(None),
    curriculum: Optional[str] = Query(None),
    status: str = Query("pending"),
    page: int = Query(1, ge=0),
    per_page: int = Query(20, ge=1, le=100),
):
    """Return paginated questions for admin review, from all stores."""
    if page < 1:
        page = 1
    all_questions: List[Dict[str, Any]] = []

    # Gather from v2 store
    for q in store_v2.all_questions():
        all_questions.append(_question_to_dict(q))

    # Gather from v4 store
    for q in store_v4.all_questions():
        if q.id not in store_v2._questions:
            all_questions.append(_question_to_dict(q))

    # Gather from curriculum stores
    for store in (ncert_store, singapore_store, uscc_store, icse_store):
        for qid, qd in store._questions.items():
            if qid not in store_v2._questions and qid not in store_v4._questions:
                all_questions.append({
                    "id": qid,
                    "stem": qd.get("stem", ""),
                    "choices": qd.get("choices", []),
                    "correct_answer": qd.get("correct_answer", 0),
                    "difficulty_score": qd.get("difficulty_score", 0),
                    "topic": qd.get("topic", ""),
                    "chapter": qd.get("chapter"),
                    "tags": qd.get("tags", []),
                })

    # Filter by grade
    if grade is not None:
        filtered = []
        for q in all_questions:
            q_grade = q.get("school_grade") or _extract_grade(q["id"])
            if q_grade == grade:
                filtered.append(q)
        all_questions = filtered

    # Filter by topic
    if topic:
        all_questions = [q for q in all_questions if q.get("topic", "").lower() == topic.lower()]

    # Filter by curriculum
    if curriculum:
        prefix_map = {"ncert": "NCERT", "singapore": "SING", "uscc": "USCC", "icse": "ICSE", "igcse": "IGCSE"}
        prefix = prefix_map.get(curriculum.lower(), curriculum.upper())
        all_questions = [q for q in all_questions if q["id"].startswith(prefix)]

    # Filter by review status
    if status in ("approved", "flagged"):
        all_questions = [
            q for q in all_questions
            if admin_review_store.get_status(q["id"]) == status
        ]
    elif status == "pending":
        all_questions = [
            q for q in all_questions
            if admin_review_store.get_status(q["id"]) == "pending"
        ]

    # Attach review info
    for q in all_questions:
        review = admin_review_store.get_review(q["id"])
        q["review_status"] = review["status"] if review else "pending"

    total = len(all_questions)
    start = (page - 1) * per_page
    page_items = all_questions[start:start + per_page]

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "questions": page_items,
    }


@router.post("/admin/review/approve")
def approve_question(req: ApproveRequest):
    _require_admin(req.reviewer_email)
    result = admin_review_store.approve(req.question_id, req.reviewer_email)
    return {"status": "approved", "question_id": req.question_id, "review": result}


@router.post("/admin/review/flag")
def flag_question(req: FlagRequest):
    _require_admin(req.reviewer_email)

    q = _find_question(req.question_id)
    autofix_applied = None

    if req.flag_type == "wrong_answer" and req.correct_answer is not None:
        if q:
            old_answer = q.correct_answer
            # Update in-memory
            q.correct_answer = req.correct_answer
            # Update on disk
            filepath = _find_source_json_path(req.question_id)
            if filepath:
                _update_question_in_file(filepath, req.question_id, "correct_answer", req.correct_answer)
            admin_review_store.log_change(
                req.question_id, req.reviewer_email, "wrong_answer",
                "correct_answer", old_answer, req.correct_answer,
            )
            autofix_applied = {"field": "correct_answer", "old": old_answer, "new": req.correct_answer}

    elif req.flag_type == "bad_hint" and q:
        old_hint = q.hint
        new_hint = _regenerate_hint(q)
        q.hint = new_hint
        filepath = _find_source_json_path(req.question_id)
        if filepath:
            _update_question_in_file(filepath, req.question_id, "hint", new_hint)
        admin_review_store.log_change(
            req.question_id, req.reviewer_email, "bad_hint",
            "hint", str(old_hint)[:200], new_hint,
        )
        autofix_applied = {"field": "hint", "regenerated": True}

    elif req.flag_type == "wrong_difficulty" and q:
        old_score = q.difficulty_score
        # Reposition based on the comment hint or leave for manual fix
        admin_review_store.log_change(
            req.question_id, req.reviewer_email, "wrong_difficulty",
            "difficulty_score", old_score, f"flagged — needs manual reorder ({req.comment})",
        )
        autofix_applied = {"field": "difficulty_score", "flagged_for_reorder": True, "current": old_score}

    # Always record the flag
    result = admin_review_store.flag(req.question_id, req.reviewer_email, req.flag_type, req.comment)

    return {
        "status": "flagged",
        "question_id": req.question_id,
        "flag_type": req.flag_type,
        "autofix_applied": autofix_applied,
        "review": result,
    }


@router.get("/admin/review/stats")
def review_stats():
    store_stats = admin_review_store.stats()

    # Count total questions across all stores
    total_questions = len(store_v2._questions) + len(store_v4._questions)
    for store in (ncert_store, singapore_store, uscc_store, icse_store):
        total_questions += len(store._questions)

    # By grade
    by_grade: Dict[int, int] = {}
    for q in store_v2.all_questions():
        g = q.school_grade or _extract_grade(q.id)
        if g:
            by_grade[g] = by_grade.get(g, 0) + 1
    for q in store_v4.all_questions():
        g = q.school_grade or _extract_grade(q.id)
        if g:
            by_grade[g] = by_grade.get(g, 0) + 1

    return {
        "total_questions": total_questions,
        **store_stats,
        "by_grade": by_grade,
    }


@router.get("/admin/review/changelog")
def review_changelog(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    entries = admin_review_store.get_changelog(limit=limit, offset=offset)
    return {"total": len(admin_review_store._changelog), "entries": entries}


@router.get("/admin/verify")
def verify_admin(email: str = Query(...)):
    return {"email": email, "is_admin": is_admin(email)}
