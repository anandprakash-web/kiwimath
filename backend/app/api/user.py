"""
User API — profile and gamification endpoints.

    GET  /user/profile    → load user profile (streak, XP, gems, daily progress)
    POST /user/profile    → update profile fields (display_name, avatar, daily_goal)
    GET  /user/mastery    → all mastery states for a user
    GET  /user/sessions   → recent session history
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.auth import assert_user_match, verify_token
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
    child_name: Optional[str] = Field(default=None, description="Child's name (set during onboarding)")
    avatar: Optional[str] = None
    daily_goal: Optional[int] = Field(default=None, ge=1, le=20)
    curriculum: Optional[str] = Field(default=None, description="Curriculum: ncert, icse, igcse, olympiad")


class ProfileResponse(BaseModel):
    user_id: str
    display_name: str
    child_name: Optional[str] = None
    avatar: str
    streak_current: int
    streak_longest: int
    xp_total: int
    kiwi_coins: int = 0
    gems: int
    daily_goal: int
    daily_progress: int
    daily_date: Optional[str] = None
    onboarded_at: Optional[str] = None
    grade: Optional[int] = None
    curriculum: Optional[str] = None
    learner_persona: Optional[str] = None
    persona_info: Optional[Dict[str, Any]] = None
    topics_mastered: int = 0


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
def get_profile(
    user_id: str = Query(..., description="Firebase UID"),
    decoded: dict = Depends(verify_token),
):
    """Load the user's profile with gamification stats."""
    assert_user_match(decoded, user_id)
    profile = get_user_profile(user_id)
    return _build_profile_response(user_id, profile)


@router.post("/profile", response_model=ProfileResponse)
def update_profile(req: UpdateProfileRequest, decoded: dict = Depends(verify_token)):
    """Update mutable profile fields."""
    assert_user_match(decoded, req.user_id)
    updates = {}
    if req.display_name is not None:
        updates["display_name"] = req.display_name
    if req.child_name is not None:
        updates["child_name"] = req.child_name
    if req.avatar is not None:
        updates["avatar"] = req.avatar
    if req.daily_goal is not None:
        updates["daily_goal"] = req.daily_goal
    if req.curriculum is not None:
        updates["curriculum"] = req.curriculum

    profile = update_user_profile(req.user_id, updates)
    return _build_profile_response(req.user_id, profile)


def _build_profile_response(user_id: str, profile: dict) -> ProfileResponse:
    """Build a ProfileResponse from a raw profile dict."""
    persona_info = None
    persona_name = profile.get("persona_name")
    persona_emoji = profile.get("persona_emoji")
    if persona_name or persona_emoji:
        persona_info = {"name": persona_name, "emoji": persona_emoji}

    return ProfileResponse(
        user_id=user_id,
        display_name=profile.get("display_name", "Kiwi Learner"),
        child_name=profile.get("child_name"),
        avatar=profile.get("avatar", "kiwi_default"),
        streak_current=profile.get("streak_current", 0),
        streak_longest=profile.get("streak_longest", 0),
        xp_total=profile.get("xp_total", 0),
        kiwi_coins=profile.get("kiwi_coins", 0),
        gems=profile.get("gems", 0),
        daily_goal=profile.get("daily_goal", 5),
        daily_progress=profile.get("daily_progress", 0),
        daily_date=profile.get("daily_date"),
        onboarded_at=profile.get("onboarded_at"),
        grade=profile.get("grade"),
        curriculum=profile.get("curriculum"),
        learner_persona=profile.get("learner_persona"),
        persona_info=persona_info,
        topics_mastered=profile.get("topics_mastered", 0),
    )


@router.get("/mastery", response_model=List[MasteryResponse])
def get_mastery(user_id: str = Query(...), decoded: dict = Depends(verify_token)):
    """Get all mastery states for a user."""
    assert_user_match(decoded, user_id)
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
def get_sessions(
    user_id: str = Query(...),
    limit: int = Query(default=10, ge=1, le=50),
    decoded: dict = Depends(verify_token),
):
    """Get recent session history for a user."""
    assert_user_match(decoded, user_id)
    return get_recent_sessions(user_id, limit=limit)
