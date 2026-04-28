"""
Kiwimath Admin API — Analytics & Retention routes.

Student Analytics:
    GET /admin/analytics/overview       — dashboard overview metrics
    GET /admin/analytics/mastery        — mastery distribution
    GET /admin/analytics/daily-active   — DAU time series
    GET /admin/analytics/topics         — per-topic performance
    GET /admin/analytics/personas       — learner persona breakdown
    GET /admin/analytics/students       — student list with search/sort
    GET /admin/analytics/students/{uid} — student drill-down

Retention:
    GET /admin/retention/cohorts        — weekly cohort retention table
    GET /admin/retention/curve          — averaged retention curve (D0-D30)
    GET /admin/retention/daily          — daily returning/new/churned
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.analytics_store import (
    get_analytics_overview,
    get_mastery_distribution,
    get_daily_active,
    get_topic_performance,
    get_persona_breakdown,
    get_students,
    get_student_detail,
    get_retention_cohorts,
    get_retention_curve,
    get_daily_retention,
)

router = APIRouter(prefix="/admin", tags=["Admin Analytics"])


# ── Student Analytics ─────────────────────────────────────────────

@router.get("/analytics/overview")
def analytics_overview():
    """Dashboard overview: total students, active counts, session stats."""
    return get_analytics_overview()


@router.get("/analytics/mastery")
def analytics_mastery():
    """Mastery distribution: Emerging / Growing / Mastered breakdown."""
    return get_mastery_distribution()


@router.get("/analytics/daily-active")
def analytics_daily_active(days: int = Query(30, ge=7, le=90)):
    """Daily active users time series."""
    return get_daily_active(days)


@router.get("/analytics/topics")
def analytics_topics():
    """Per-topic performance: accuracy, attempts, mastery rate."""
    return get_topic_performance()


@router.get("/analytics/personas")
def analytics_personas():
    """Learner persona breakdown: Steady, Power, Mastery, Comeback, New."""
    return get_persona_breakdown()


@router.get("/analytics/students")
def analytics_students(
    search: str = Query("", description="Search by name or UID"),
    sort: str = Query("last_active", description="Sort field"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Student list with search, sort, pagination."""
    return get_students(search=search, sort=sort, limit=limit, offset=offset)


@router.get("/analytics/students/{uid}")
def analytics_student_detail(uid: str):
    """Per-student drill-down: mastery map, recent sessions, stats."""
    detail = get_student_detail(uid)
    if not detail:
        raise HTTPException(status_code=404, detail="Student not found")
    return detail


# ── Retention Dashboard ───────────────────────────────────────────

@router.get("/retention/cohorts")
def retention_cohorts():
    """Weekly cohort retention table: D0, D1, D7, D30 per cohort."""
    return get_retention_cohorts()


@router.get("/retention/curve")
def retention_curve():
    """Averaged retention curve across all cohorts (D0-D30)."""
    return get_retention_curve()


@router.get("/retention/daily")
def retention_daily(days: int = Query(30, ge=7, le=90)):
    """Daily returning, new, and churned user counts."""
    return get_daily_retention(days)
