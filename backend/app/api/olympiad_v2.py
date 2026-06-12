"""
Olympiad v2 API — 4-Pillar × 5-Level system.

Endpoints:
    GET  /olympiad/v2/pillars?grade=N                          → list pillars
    GET  /olympiad/v2/levels?pillar=X&grade=N                  → levels for a pillar
    GET  /olympiad/v2/topics?pillar=X&level=N                  → topics for a level
    GET  /olympiad/v2/worksheet?pillar=X&level=N&topic=T       → questions
    POST /olympiad/v2/submit                                   → submit answer
    POST /olympiad/v2/submit-proof                             → submit proof (AI graded)
    GET  /olympiad/v2/progress?user_id=X                       → pillar progress
    GET  /olympiad/v2/daily-challenge?grade=N                  → daily challenge
    GET  /olympiad/v2/stats                                    → content statistics
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from ..services.pillar_content_store import pillar_store
from ..services import pillar_progress_store
from ..services.proof_grader import grade_proof

router = APIRouter(prefix="/olympiad/v2", tags=["olympiad-v2"])


# ── Read endpoints ─────────────────────────────────────────────────────────

@router.get("/pillars")
async def get_pillars(grade: int = Query(1, ge=1, le=10)):
    """List all 4 pillars with metadata, topic lists, and question counts."""
    pillars = pillar_store.get_pillars(grade)
    return {"pillars": pillars, "grade": grade}


@router.get("/levels")
async def get_levels(
    pillar: str = Query(..., description="Pillar ID: algebra, number_theory, combinatorics, geometry"),
    grade: int = Query(1, ge=1, le=10),
):
    """List all 5 levels for a pillar with topics and lock status."""
    levels = pillar_store.get_levels(pillar, grade)
    if not levels:
        raise HTTPException(status_code=404, detail=f"Unknown pillar: {pillar}")
    return {"pillar": pillar, "grade": grade, "levels": levels}


@router.get("/topics")
async def get_topics(
    pillar: str = Query(...),
    level: int = Query(..., ge=1, le=5),
):
    """List topics for a pillar + level with per-topic question counts."""
    topics = pillar_store.get_topics(pillar, level)
    return {"pillar": pillar, "level": level, "topics": topics}


@router.get("/worksheet")
async def get_worksheet(
    pillar: str = Query(...),
    level: int = Query(..., ge=1, le=5),
    topic: str = Query(...),
):
    """Get a worksheet (list of questions) for pillar/level/topic."""
    ws = pillar_store.get_worksheet(pillar, level, topic)
    if not ws["questions"]:
        raise HTTPException(
            status_code=404,
            detail=f"No questions for {pillar}/level{level}/{topic}",
        )
    return ws


# ── Write endpoints ────────────────────────────────────────────────────────

class SubmitRequest(BaseModel):
    user_id: str
    question_id: str
    answer: Any  # int for MCQ index, str for fill_up, etc.
    time_taken_seconds: int = 0


@router.post("/submit")
async def submit_answer(req: SubmitRequest):
    """Submit an answer for a question. Returns correctness + updated progress."""
    question = pillar_store.get_question(req.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check correctness based on interaction mode
    mode = question.get("interaction_mode", "mcq")
    correct = False

    if mode == "mcq":
        correct = req.answer == question.get("correct_answer")
    elif mode == "integer":
        try:
            correct = int(req.answer) == question.get("correct_value")
        except (TypeError, ValueError):
            correct = False
    elif mode == "fill_up":
        user_ans = str(req.answer).strip().lower()
        expected = str(question.get("fill_blank_answer", "")).strip().lower()
        correct = user_ans == expected
    elif mode == "drag_drop":
        # Correct order is [0, 1, 2, ...]
        if isinstance(req.answer, list):
            correct = req.answer == list(range(len(req.answer)))
    elif mode == "match_column":
        expected = question.get("correct_matches", {})
        correct = req.answer == expected
    elif mode == "subjective_ai":
        # Subjective answers graded via /submit-proof
        return {"error": "Use /submit-proof for subjective questions"}

    # Record progress
    pillar = question.get("pillar", "")
    level = question.get("level", 1)
    topic = question.get("topic", "")

    progress = pillar_progress_store.record_answer(
        user_id=req.user_id,
        pillar=pillar,
        level=level,
        topic=topic,
        question_id=req.question_id,
        correct=correct,
        time_taken_seconds=req.time_taken_seconds,
    )

    return {
        "correct": correct,
        "correct_answer": question.get("correct_answer"),
        "model_solution": question.get("model_solution"),
        "approach": question.get("approach", ""),
        "progress": progress,
    }


class ProofSubmitRequest(BaseModel):
    user_id: str
    question_id: str
    proof_text: str
    image_urls: Optional[List[str]] = None


@router.post("/submit-proof")
async def submit_proof(req: ProofSubmitRequest):
    """Submit a subjective proof for AI grading (L4-L5 questions)."""
    question = pillar_store.get_question(req.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if question.get("interaction_mode") != "subjective_ai":
        raise HTTPException(
            status_code=400,
            detail="This question is not subjective — use /submit instead",
        )

    result = await grade_proof(
        question_stem=question.get("stem", ""),
        student_proof=req.proof_text,
        rubric=question.get("subjective_rubric"),
        model_solution=question.get("model_solution"),
    )

    # Record as correct if passed (score >= 60)
    pillar = question.get("pillar", "")
    level = question.get("level", 1)
    topic = question.get("topic", "")

    progress = pillar_progress_store.record_answer(
        user_id=req.user_id,
        pillar=pillar,
        level=level,
        topic=topic,
        question_id=req.question_id,
        correct=result.get("passed", False),
        time_taken_seconds=0,
    )

    return {
        "grading": result,
        "progress": progress,
    }


# ── Progress & daily challenge ─────────────────────────────────────────────

@router.get("/progress")
async def get_progress(user_id: str = Query(...)):
    """Get full pillar progress summary for a user."""
    return pillar_progress_store.get_progress(user_id)


@router.get("/daily-challenge")
async def get_daily_challenge(grade: int = Query(1, ge=1, le=10)):
    """Get today's daily challenge question."""
    question = pillar_store.get_daily_challenge(grade)
    if not question:
        raise HTTPException(status_code=404, detail="No challenge available")
    return {"question": question, "grade": grade}


@router.get("/stats")
async def get_stats():
    """Content statistics for all pillars."""
    return pillar_store.stats
