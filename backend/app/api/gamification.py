"""
Gamification API v2 — Meritocratic Achievement Economy

Endpoints:
    GET  /rewards/profile              -> full profile (level, coins, gems, persona)
    GET  /rewards/badges               -> all badge definitions + student progress
    GET  /rewards/shop                 -> shop catalog (priced in Kiwi Coins)
    POST /rewards/shop/purchase        -> buy a regular item with Kiwi Coins
    GET  /rewards/legendaries          -> legendary items with achievement gate progress
    POST /rewards/legendaries/unlock   -> attempt to unlock a legendary via achievement gate
    POST /rewards/avatar/equip         -> equip/unequip an avatar item
    POST /rewards/genesis              -> genesis onboarding (pet hatching, initial wealth)
    GET  /rewards/parent-dashboard     -> parent-friendly mastery view
    GET  /rewards/economy-stats        -> (admin) invisible central bank stats
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.gamification import (
    gamification,
    BADGE_DEFINITIONS,
    LEARNER_PERSONAS,
    LEGENDARY_ITEMS,
    LEVELS,
    SHOP_ITEMS,
    TITLES,
    get_level,
    get_active_legendaries,
    get_vaulted_legendaries,
)

router = APIRouter(prefix="/rewards", tags=["rewards"])


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class PurchaseRequest(BaseModel):
    user_id: str
    item_id: str


class LegendaryUnlockRequest(BaseModel):
    user_id: str
    item_id: str


class EquipRequest(BaseModel):
    user_id: str
    slot: str = Field(..., description="Avatar slot: hat, glasses, outfit, base_color, celebration_fx")
    item_id: Optional[str] = Field(None, description="Item ID to equip, or null to unequip")


class GenesisRequest(BaseModel):
    user_id: str
    pet_name: str = Field("Kiwi", description="Name for the child's Kiwi pet")


# ---------------------------------------------------------------------------
# Core Profile
# ---------------------------------------------------------------------------

@router.get("/profile")
def get_profile(user_id: str = Query(..., description="Student ID")):
    """Full gamification profile: level, XP, Kiwi Coins, Mastery Gems, persona."""
    return gamification.get_profile_summary(user_id)


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------

@router.get("/badges")
def get_badges(user_id: str = Query(..., description="Student ID")):
    """All badge definitions with student progress on each."""
    state = gamification.get_state(user_id)
    result = []

    for badge_id, defn in BADGE_DEFINITIONS.items():
        badge_state = state.badges.get(badge_id)
        result.append({
            "badge_id": badge_id,
            "name": defn["name"],
            "emoji": defn["emoji"],
            "category": defn["category"],
            "description": defn["description"],
            "current_tier": badge_state.current_tier if badge_state else None,
            "progress": badge_state.progress if badge_state else 0,
            "tiers": defn["tiers"],
        })

    return result


@router.get("/levels")
def get_levels():
    """All level definitions."""
    return LEVELS


@router.get("/titles")
def get_titles(user_id: str = Query(..., description="Student ID")):
    """All title definitions with earned status."""
    state = gamification.get_state(user_id)
    result = []
    for title in TITLES:
        result.append({
            **title,
            "earned": title["id"] in state.titles,
        })
    return result


# ---------------------------------------------------------------------------
# Shop — Regular Items (Kiwi Coins)
# ---------------------------------------------------------------------------

@router.get("/shop")
def get_shop(user_id: str = Query(..., description="Student ID")):
    """Shop catalog. Regular items priced in Kiwi Coins. Stable prices."""
    state = gamification.get_state(user_id)
    catalog = {}

    for category, items in SHOP_ITEMS.items():
        catalog[category] = []
        for item in items:
            catalog[category].append({
                **item,
                "owned": item["id"] in state.owned_items,
                "can_afford": state.kiwi_coins >= item["coin_price"],
            })

    return {
        "kiwi_coins": state.kiwi_coins,
        "mastery_gems": state.gems,
        "catalog": catalog,
    }


@router.post("/shop/purchase")
def purchase_item(req: PurchaseRequest):
    """Purchase a regular shop item with Kiwi Coins."""
    result = gamification.purchase_item(req.user_id, req.item_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# Legendary Items — Achievement Gates (not purchases)
# ---------------------------------------------------------------------------

@router.get("/legendaries")
def get_legendaries(user_id: str = Query(..., description="Student ID")):
    """Legendary items with achievement gate progress.

    Shows the child a checklist of requirements for each legendary,
    NOT a price tag. The child sees: "You need 3 more topics mastered"
    instead of "You need 200 more coins."
    """
    return {
        "active": gamification.get_legendary_status(user_id),
        "vaulted": get_vaulted_legendaries(),
    }


@router.post("/legendaries/unlock")
def unlock_legendary(req: LegendaryUnlockRequest):
    """Attempt to unlock a legendary item via Achievement Gate.

    All gate requirements must be met simultaneously. This is an
    achievement, not a purchase — the child BECOMES worthy of the item.
    """
    result = gamification.unlock_legendary(req.user_id, req.item_id)
    if not result["success"]:
        if "gate_status" in result:
            return result  # Return gate status so UI shows what's missing
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# Avatar
# ---------------------------------------------------------------------------

@router.post("/avatar/equip")
def equip_avatar(req: EquipRequest):
    """Equip or unequip an avatar customization item."""
    result = gamification.equip_item(req.user_id, req.slot, req.item_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# Learner Personas
# ---------------------------------------------------------------------------

@router.get("/persona")
def get_persona(user_id: str = Query(..., description="Student ID")):
    """Get the child's current learner persona with description."""
    state = gamification.get_state(user_id)
    persona = LEARNER_PERSONAS.get(state.learner_persona, {})
    return {
        "persona_id": state.learner_persona,
        **persona,
        "all_personas": LEARNER_PERSONAS,
    }


# ---------------------------------------------------------------------------
# Genesis Onboarding
# ---------------------------------------------------------------------------

@router.post("/genesis")
def start_genesis(req: GenesisRequest):
    """Start the genesis onboarding flow for a new child.

    Awards initial wealth (100 coins + 1 gem), creates the pet,
    sets genesis badge, and enables the 2× reward multiplier for
    the first session. Idempotent — returns error if already completed.
    """
    result = gamification.start_genesis(req.user_id, req.pet_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# Parent Dashboard
# ---------------------------------------------------------------------------

@router.get("/parent-dashboard")
def parent_dashboard(user_id: str = Query(..., description="Student/child ID")):
    """Parent-friendly dashboard with mastery labels and learner persona.

    Shows: Mastered / Growing / Emerging / Starting per topic,
    strengths, areas needing practice, and the child's learner identity.
    """
    return gamification.get_parent_dashboard(user_id)


# ---------------------------------------------------------------------------
# Admin: Invisible Central Bank
# ---------------------------------------------------------------------------

@router.get("/economy-stats")
def economy_stats():
    """Admin-only: Invisible Central Bank statistics.

    Shows coin/gem circulation, legendary saturation percentages,
    and whether any legendaries should be vaulted.

    NEVER exposed to children. This is for the game designer to
    monitor economy health and decide vault rotations.
    """
    return gamification.get_economy_stats()
