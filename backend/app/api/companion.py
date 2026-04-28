"""
Companion API — config delivery, summon resolver, telemetry, and companion management.

Endpoints:
    GET  /companion/config           → full config bundle (session start)
    POST /companion/summon           → resolve companion for a surface
    POST /companion/choose           → set chosen primary companion
    GET  /companion/cast             → list all companions
    GET  /companion/prefetch         → asset prefetch manifest
    POST /companion/telemetry        → ingest telemetry events
    POST /companion/dismiss          → log companion dismissal
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.companion import (
    CAST, CompanionId, Emotion, Surface, AgeTier,
    UserCompanionState, SummonRequest, SummonResponse,
    resolve_companion, get_companion_config, build_prefetch_manifest,
    companion_summoned_event, companion_dismissed_event,
)

router = APIRouter(prefix="/companion", tags=["Companion"])


# ── Request/Response models ───────────────────────────────────────────

class SummonRequestBody(BaseModel):
    surface: str
    chosen_primary: str = "kiwi"
    age_tier: str = "k2"
    lesson_id: Optional[str] = None
    problem_steps_required: int = 1
    pico_appearances_in_lesson: int = 0
    last_kid_action_ms_ago: int = 0
    kid_typing: bool = False
    app_version: int = 1


class ChooseCompanionBody(BaseModel):
    companion_id: str
    user_id: str = "anonymous"


class TelemetryEventBody(BaseModel):
    event: str
    companion_id: str
    surface: str
    extra: dict = Field(default_factory=dict)


class DismissBody(BaseModel):
    companion_id: str
    surface: str
    dismiss_reason: str = "surface_changed"
    time_visible_ms: int = 0
    kid_acted: bool = False


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get("/config")
def companion_config(
    chosen_primary: str = "kiwi",
    age_tier: str = "k2",
    audio_enabled: bool = True,
    app_version: int = 1,
):
    """Return the full companion config bundle for client-side caching."""
    try:
        cid = CompanionId(chosen_primary)
    except ValueError:
        cid = CompanionId.KIWI
    try:
        tier = AgeTier(age_tier)
    except ValueError:
        tier = AgeTier.K2

    state = UserCompanionState(
        chosen_primary=cid,
        age_tier=tier,
        audio_enabled=audio_enabled,
    )
    return get_companion_config(state, app_version)


@router.post("/summon")
def summon_companion(body: SummonRequestBody):
    """Resolve which companion appears on a given surface."""
    try:
        surface = Surface(body.surface)
    except ValueError:
        raise HTTPException(400, f"Unknown surface: {body.surface}")
    try:
        cid = CompanionId(body.chosen_primary)
    except ValueError:
        cid = CompanionId.KIWI
    try:
        tier = AgeTier(body.age_tier)
    except ValueError:
        tier = AgeTier.K2

    state = UserCompanionState(chosen_primary=cid, age_tier=tier)
    req = SummonRequest(
        surface=surface,
        user_state=state,
        lesson_id=body.lesson_id,
        problem_steps_required=body.problem_steps_required,
        pico_appearances_in_lesson=body.pico_appearances_in_lesson,
        last_kid_action_ms_ago=body.last_kid_action_ms_ago,
        kid_typing=body.kid_typing,
        current_app_version=body.app_version,
    )
    response = resolve_companion(req)

    # Build telemetry event (in production, fire-and-forget to Firestore)
    telemetry = companion_summoned_event(response, req)

    return {
        **response.to_dict(),
        "telemetry": telemetry,
    }


@router.post("/choose")
def choose_companion(body: ChooseCompanionBody):
    """Set a kid's chosen primary companion."""
    try:
        cid = CompanionId(body.companion_id)
    except ValueError:
        raise HTTPException(400, f"Unknown companion: {body.companion_id}")

    companion = CAST[cid]
    if not companion.is_default and companion.ship_in_version > 1:
        # v1: only Kiwi can be chosen; others shown as coming soon
        return {
            "status": "unavailable",
            "companion_id": cid.value,
            "message": f"{companion.name} is coming soon!",
            "ship_in_version": companion.ship_in_version,
        }

    import time
    return {
        "status": "ok",
        "companion_id": cid.value,
        "companion_name": companion.name,
        "chosen_at": time.time(),
        "signature_color": companion.signature_color,
    }


@router.get("/cast")
def list_cast(app_version: int = 1):
    """List all 5 companions with their ship status."""
    result = []
    for cid, comp in CAST.items():
        shipped = comp.ship_in_version <= app_version
        result.append({
            "id": comp.id.value,
            "name": comp.name,
            "region": comp.region,
            "role": comp.role,
            "signature_color": comp.signature_color,
            "signature_color_soft": comp.signature_color_soft,
            "signature_color_text": comp.signature_color_text,
            "habitat_region_id": comp.habitat_region_id,
            "is_default": comp.is_default,
            "shipped": shipped,
            "status": "available" if shipped else "coming_soon",
        })
    return {"cast": result, "app_version": app_version}


@router.get("/prefetch")
def prefetch_manifest(
    chosen_primary: str = "kiwi",
    age_tier: str = "k2",
):
    """Return the list of asset URLs to prefetch on session start."""
    try:
        cid = CompanionId(chosen_primary)
    except ValueError:
        cid = CompanionId.KIWI
    try:
        tier = AgeTier(age_tier)
    except ValueError:
        tier = AgeTier.K2
    return {
        "companion_id": cid.value,
        "age_tier": tier.value,
        "assets": build_prefetch_manifest(cid, tier),
    }


@router.post("/telemetry")
def ingest_telemetry(body: TelemetryEventBody):
    """Ingest a companion telemetry event (companion_summoned, _changed, _interaction)."""
    # In production, write to Firestore analytics collection
    return {
        "status": "ok",
        "event": body.event,
        "companion_id": body.companion_id,
        "surface": body.surface,
    }


@router.post("/dismiss")
def dismiss_companion(body: DismissBody):
    """Log a companion dismissal event."""
    event = companion_dismissed_event(
        companion_id=body.companion_id,
        surface=body.surface,
        reason=body.dismiss_reason,
        time_visible_ms=body.time_visible_ms,
        kid_acted=body.kid_acted,
    )
    return {"status": "ok", "event": event}
