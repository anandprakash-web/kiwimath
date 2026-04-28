"""
User API — profile and gamification endpoints.

    GET  /user/profile    → load user profile (streak, XP, gems, daily progress)
    POST /user/profile    → update profile fields (display_name, avatar, daily_goal)
    GET  /user/mastery    → all mastery states for a user
    GET  /user/sessions   → recent session history
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.firestore_service import (
    get_mastery_states,
    get_recent_sessions,
    get_user_profile,
    update_user_profile,
)

router = APIRouter(prefix="/user", tags=["user"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class UpdateProfileRequest(BaseModel):
    user_id: str = Field(..., description="Firebase UID")
    display_name: Optional[str] = None
    avatar: Optional[str] = None
    daily_goal: Optional[int] = Field(default=None, ge=1, le=20)


class ProfileResponse(BaseModel):
    user_id: str
    display_name: str
    avatar: str
    streak_current: int
    streak_longest: int
    xp_total: int
    gems: int
    daily_goal: int
    daily_progress: int
    daily_date: Optional[str] = None


class MasteryResponse(BaseModel):
    concept_id: str
    internal_score: float
    shown_score: int
    mastery_label: str
    total_attempts: int
    streak_current: int
    last_practised: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/profile", response_model=ProfileResponse)
def get_profile(user_id: str = Query(..., description="Firebase UID")):
    """Load the user's profile with gamification stats."""
    profile = get_user_profile(user_id)
    return ProfileResponse(
        user_id=user_id,
        display_name=profile.get("display_name", "Kiwi Learner"),
        avatar=profile.get("avatar", "kiwi_default"),
        streak_current=profile.get("streak_current", 0),
        streak_longest=profile.get("streak_longest", 0),
        xp_total=profile.get("xp_total", 0),
        gems=profile.get("gems", 0),
        daily_goal=profile.get("daily_goal", 5),
        daily_progress=profile.get("daily_progress", 0),
        daily_date=profile.get("daily_date"),
    )


@router.post("/profile", response_model=ProfileResponse)
def update_profile(req: UpdateProfileRequest):
    """Update mutable profile fields."""
    updates = {}
    if req.display_name is not None:
        updates["display_name"] = req.display_name
    if req.avatar is not None:
        updates["avatar"] = req.avatar
    if req.daily_goal is not None:
        updates["daily_goal"] = req.daily_goal

    profile = update_user_profile(req.user_id, updates)
    return ProfileResponse(
        user_id=req.user_id,
        display_name=profile.get("display_name", "Kiwi Learner"),
        avatar=profile.get("avatar", "kiwi_default"),
        streak_current=profile.get("streak_current", 0),
        streak_longest=profile.get("streak_longest", 0),
        xp_total=profile.get("xp_total", 0),
        gems=profile.get("gems", 0),
        daily_goal=profile.get("daily_goal", 5),
        daily_progress=profile.get("daily_progress", 0),
        daily_date=profile.get("daily_date"),
    )


@router.get("/mastery", response_model=List[MasteryResponse])
def get_mastery(user_id: str = Query(...)):
    """Get all mastery states for a user."""
    states = get_mastery_states(user_id)
    return [
        MasteryResponse(
            concept_id=cid,
            internal_score=round(data.get("internal_score", 0.0), 4),
            shown_score=data.get("shown_score", 0),
            mastery_label=data.get("mastery_label", "new"),
            total_attempts=data.get("total_attempts", 0),
            streak_current=data.get("streak_current", 0),
            last_practised=data.get("last_practised"),
        )
        for cid, data in states.items()
    ]


@router.get("/sessions", response_model=List[Dict[str, Any]])
def get_sessions(user_id: str = Query(...), limit: int = Query(default=10, ge=1, le=50)):
    """Get recent session history for a user."""
    return get_recent_sessions(user_id, limit=limit)
