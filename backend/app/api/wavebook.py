"""
Wavebook API — serves live-class olympiad worksheet MCQs (Level 3 = G3-4, Level 4 = G5-6).

Endpoints:
    GET  /wavebook/topics?grade=N            → list topics for grade's level
    GET  /wavebook/questions?grade=N&topic=T → questions for a topic
    GET  /wavebook/download?grade=N&topic=T  → downloadable PDF-style JSON
    GET  /wavebook/stats                     → content statistics
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

router = APIRouter(prefix="/wavebook", tags=["wavebook"])

# ─── Content loading ─────────────────────────────────────

def _content_dir() -> Path:
    env = os.environ.get("KIWIMATH_V2_CONTENT_DIR", "")
    if env:
        return Path(env) / "wavebook"
    return Path(__file__).resolve().parent.parent.parent / "content-v2" / "wavebook"


_cache: Dict[int, List[dict]] = {}  # level -> list of questions


def _grade_to_level(grade: int) -> int:
    if grade in (3, 4):
        return 3
    if grade in (5, 6):
        return 4
    raise HTTPException(status_code=400, detail=f"Wavebook only available for grades 3-6, got {grade}")


def _load_level(level: int):
    if level in _cache:
        return
    questions: List[dict] = []
    cdir = _content_dir()
    for batch in range(1, 5):
        path = cdir / f"wavebook_L{level}_batch{batch}.json"
        if not path.exists():
            continue
        with open(path) as f:
            data = json.load(f)
        questions.extend(data.get("questions", []))
    _cache[level] = questions


def _ensure_loaded(grade: int) -> int:
    level = _grade_to_level(grade)
    _load_level(level)
    return level


# ─── Endpoints ───────────────────────────────────────────

@router.get("/topics")
def list_topics(grade: int = Query(..., ge=3, le=6)):
    """List all topics for a grade's wavebook level, with difficulty breakdown."""
    level = _ensure_loaded(grade)
    questions = _cache[level]

    topics: Dict[str, Dict[str, Any]] = {}
    for q in questions:
        t = q["topic"]
        if t not in topics:
            topics[t] = {"topic": t, "total": 0, "warmup": 0, "practice": 0, "challenge": 0}
        topics[t]["total"] += 1
        tier = q.get("difficulty_tier", "practice")
        if tier in topics[t]:
            topics[t][tier] += 1

    topic_list = sorted(topics.values(), key=lambda x: -x["total"])

    return {
        "grade": grade,
        "level": level,
        "grade_band": "3-4" if level == 3 else "5-6",
        "total_topics": len(topic_list),
        "total_questions": len(questions),
        "topics": topic_list,
    }


@router.get("/questions")
def get_questions(
    grade: int = Query(..., ge=3, le=6),
    topic: str = Query(..., min_length=1),
):
    """Get all questions for a specific topic, ordered by difficulty tier."""
    level = _ensure_loaded(grade)
    questions = _cache[level]

    tier_order = {"warmup": 0, "practice": 1, "challenge": 2}
    filtered = [q for q in questions if q["topic"].lower() == topic.lower()]

    if not filtered:
        # Try partial match
        filtered = [q for q in questions if topic.lower() in q["topic"].lower()]

    if not filtered:
        raise HTTPException(status_code=404, detail=f"No questions found for topic '{topic}' at grade {grade}")

    filtered.sort(key=lambda q: (tier_order.get(q.get("difficulty_tier", "practice"), 1), q.get("question_number", 0)))

    return {
        "grade": grade,
        "level": level,
        "topic": filtered[0]["topic"],
        "total": len(filtered),
        "questions": filtered,
    }


@router.get("/download")
def download_topic(
    grade: int = Query(..., ge=3, le=6),
    topic: str = Query(..., min_length=1),
):
    """Download questions for a topic as a JSON file (for offline/PDF generation)."""
    result = get_questions(grade=grade, topic=topic)
    content = json.dumps(result, indent=2, ensure_ascii=False)
    filename = f"wavebook_g{grade}_{result['topic'].lower().replace(' ', '_')}.json"
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/stats")
def get_stats():
    """Overall wavebook content statistics."""
    stats = {}
    for level in (3, 4):
        _load_level(level)
        questions = _cache.get(level, [])
        topics = set(q["topic"] for q in questions)
        stats[f"level_{level}"] = {
            "grade_band": "3-4" if level == 3 else "5-6",
            "total_questions": len(questions),
            "total_topics": len(topics),
            "topics": sorted(topics),
        }
    total = sum(s["total_questions"] for s in stats.values())
    return {"total_questions": total, "levels": stats}
