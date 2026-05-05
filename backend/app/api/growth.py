"""
Growth Journey API — endpoints for the Growth tab in the Flutter app.

Endpoints:
    GET   /growth/journey              → Mountain journey data
    GET   /growth/topics               → Per-topic heatmap
    GET   /growth/timeline             → Sparkline data
    GET   /growth/milestones           → Achievement timeline
    POST  /growth/diagnostic/save-baseline → Save diagnostic baseline
    GET   /growth/has-diagnostic       → Check if diagnostic taken
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.growth_service import growth_service

router = APIRouter(prefix="/growth", tags=["growth"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class SaveBaselineRequest(BaseModel):
    """Payload for saving a diagnostic baseline."""
    user_id: str
    grade: int = Field(..., ge=1, le=6)
    benchmark_id: str
    theta: float
    per_topic_theta: Dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/journey")
def get_journey(
    user_id: str = Query(..., description="Student ID"),
    grade: int = Query(1, ge=1, le=6, description="Student grade"),
):
    """Get mountain journey data: current level, baseline, engagement stats.

    Returns the student's current proficiency level and scale score,
    their diagnostic baseline (if taken), the delta between them,
    aggregated engagement statistics, and whether a diagnostic retake
    is suggested (> 30 days since last one).
    """
    return growth_service.get_journey(user_id, grade)


@router.get("/topics")
def get_topic_heatmap(
    user_id: str = Query(..., description="Student ID"),
    grade: int = Query(1, ge=1, le=6, description="Student grade"),
):
    """Get per-topic growth heatmap.

    For each of the 8 core math topics, returns the current proficiency
    level and theta alongside the diagnostic baseline, with a computed
    delta and trend indicator (up / down / flat).
    """
    return growth_service.get_topic_heatmap(user_id, grade)


@router.get("/timeline")
def get_timeline(
    user_id: str = Query(..., description="Student ID"),
):
    """Get sparkline chart data: theta snapshots over time.

    Returns historical growth snapshots for rendering a sparkline,
    plus overlay engagement milestones (first badge, streak records, etc.).
    """
    return growth_service.get_timeline(user_id)


@router.get("/milestones")
def get_milestones(
    user_id: str = Query(..., description="Student ID"),
    grade: int = Query(1, ge=1, le=6, description="Student grade"),
):
    """Get achievement timeline.

    Combines proficiency level-ups, topic breakthroughs, streak
    milestones, gem milestones, badge unlocks, worksheet milestones,
    and clan war victories into a single sorted timeline.
    """
    return growth_service.get_milestones(user_id, grade)


@router.post("/diagnostic/save-baseline")
def save_diagnostic_baseline(req: SaveBaselineRequest):
    """Save diagnostic test result as the growth baseline.

    Stores the overall theta, per-topic theta, and an engagement
    snapshot at the time of the diagnostic. This baseline is used
    to compute growth deltas in the journey and heatmap views.
    """
    return growth_service.save_diagnostic_baseline(
        user_id=req.user_id,
        grade=req.grade,
        benchmark_id=req.benchmark_id,
        theta=req.theta,
        per_topic_theta=req.per_topic_theta,
    )


@router.get("/has-diagnostic")
def has_diagnostic(
    user_id: str = Query(..., description="Student ID"),
):
    """Check if the student has taken a diagnostic test.

    Returns a boolean indicating whether a baseline exists.
    """
    return {"has_diagnostic": growth_service.has_diagnostic(user_id)}
