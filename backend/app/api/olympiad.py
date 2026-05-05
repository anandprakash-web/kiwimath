"""
Olympiad Worksheet API — serves daily olympiad worksheets with on-demand SVG rendering.

Endpoints:
    GET  /olympiad/worksheets?grade=N&day=D       → single worksheet
    GET  /olympiad/worksheets/list?grade=N         → list all worksheet IDs for a grade
    GET  /olympiad/questions/{qid}/visual          → render SVG visual on demand
    GET  /olympiad/stats?grade=N                   → content statistics
"""

from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

router = APIRouter(prefix="/olympiad", tags=["olympiad"])

# ─── Content loading ─────────────────────────────────────

CONTENT_DIR = Path(__file__).resolve().parent.parent.parent / "content" / "olympiad"

# Add SVG components to path for rendering
_svg_components_dir = CONTENT_DIR / "svg_components"
if _svg_components_dir.exists():
    sys.path.insert(0, str(_svg_components_dir))

_worksheets_cache: Dict[int, Dict[int, dict]] = {}  # grade -> {day -> worksheet}
_questions_cache: Dict[str, dict] = {}               # question_id -> question


def _load_grade(grade: int):
    """Load all worksheets for a grade from batch files."""
    if grade in _worksheets_cache:
        return

    _worksheets_cache[grade] = {}
    for batch in range(1, 6):
        path = CONTENT_DIR / f"g{grade}_olympiad_batch{batch}.json"
        if not path.exists():
            continue
        with open(path) as f:
            data = json.load(f)
        for ws in data:
            day = ws["day"]
            _worksheets_cache[grade][day] = ws
            for q in ws["questions"]:
                _questions_cache[q["id"]] = q


def _ensure_loaded(grade: int):
    if grade not in _worksheets_cache:
        _load_grade(grade)


# ─── SVG Renderer ────────────────────────────────────────

_renderer = None

def _get_renderer():
    global _renderer
    if _renderer is None:
        try:
            from visual_ref_renderer import render_visual_ref
            _renderer = render_visual_ref
        except ImportError:
            _renderer = lambda x: None
    return _renderer


# ─── Endpoints ───────────────────────────────────────────

@router.get("/worksheets")
def get_worksheet(
    grade: int = Query(..., ge=1, le=6, description="Grade (1-6)"),
    day: int = Query(..., ge=1, le=100, description="Day (1-100)"),
):
    """Get a single olympiad worksheet for a grade and day.

    Returns the full worksheet with all questions.
    Questions with visuals include a visual_url field for fetching the SVG.
    """
    _ensure_loaded(grade)
    ws = _worksheets_cache.get(grade, {}).get(day)
    if ws is None:
        raise HTTPException(404, f"No worksheet found for G{grade} Day {day}")

    # Add visual_url to questions that have visual_ref
    result = dict(ws)
    questions_out = []
    for q in result["questions"]:
        q_out = dict(q)
        if q.get("visual_ref"):
            q_out["visual_url"] = f"/olympiad/questions/{q['id']}/visual"
        questions_out.append(q_out)
    result["questions"] = questions_out
    return result


@router.get("/worksheets/list")
def list_worksheets(
    grade: int = Query(..., ge=1, le=6, description="Grade (1-6)"),
):
    """List all available worksheet days with metadata for a grade.

    Returns title, subtitle, dominant topic, and question count for each worksheet
    so the app can display a rich worksheet browser without fetching full content.
    """
    _ensure_loaded(grade)
    ws_map = _worksheets_cache.get(grade, {})
    days = sorted(ws_map.keys())
    worksheets_meta = []
    for d in days:
        ws = ws_map[d]
        worksheets_meta.append({
            "day": d,
            "title": ws.get("title", f"Day {d}"),
            "subtitle": ws.get("subtitle", ""),
            "dominant_topic": ws.get("dominant_topic", "mixed"),
            "question_count": len(ws.get("questions", [])),
            "difficulty_distribution": ws.get("difficulty_distribution", {}),
        })
    return {
        "grade": grade,
        "total_worksheets": len(days),
        "days": days,
        "worksheets": worksheets_meta,
    }


@router.get("/questions/{question_id}/visual")
def get_question_visual(question_id: str):
    """Render and return the SVG visual for an olympiad question.

    The visual is generated on-demand from the visual_ref stored in the question.
    """
    # Find the question
    if question_id not in _questions_cache:
        # Try loading all grades
        for g in range(1, 7):
            _ensure_loaded(g)
    q = _questions_cache.get(question_id)
    if q is None:
        raise HTTPException(404, f"Question {question_id} not found")

    visual_ref = q.get("visual_ref")
    if not visual_ref:
        raise HTTPException(404, f"Question {question_id} has no visual")

    renderer = _get_renderer()
    svg = renderer(visual_ref)
    if svg is None:
        raise HTTPException(500, f"Failed to render visual for {question_id}")

    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


@router.get("/stats")
def get_stats(
    grade: Optional[int] = Query(None, ge=1, le=6, description="Grade (1-6), or all"),
):
    """Get content statistics for olympiad worksheets."""
    grades = [grade] if grade else list(range(1, 7))
    stats = {}

    for g in grades:
        _ensure_loaded(g)
        ws_map = _worksheets_cache.get(g, {})
        total_q = 0
        modes = {}
        topics = {}
        visuals = 0

        for ws in ws_map.values():
            for q in ws["questions"]:
                total_q += 1
                m = q["interaction_mode"]
                modes[m] = modes.get(m, 0) + 1
                t = q["topic"]
                topics[t] = topics.get(t, 0) + 1
                if q.get("visual_ref"):
                    visuals += 1

        stats[f"grade_{g}"] = {
            "worksheets": len(ws_map),
            "total_questions": total_q,
            "questions_with_visuals": visuals,
            "interaction_modes": modes,
            "topics": topics,
        }

    return {"stats": stats}
