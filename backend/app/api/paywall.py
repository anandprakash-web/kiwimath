"""
Paywall API v2 — Topic Unlock & Premium Subscription

Endpoints:
    GET  /v2/paywall/status    -> unlock status for all 8 topics
    POST /v2/paywall/unlock    -> unlock a topic using Kiwi Coins
    POST /v2/paywall/restore   -> restore purchases / activate premium
    GET  /v2/paywall/pricing   -> pricing info (coins & subscription)

Topics 1-2 (Counting & Arithmetic) are always free.
Topics 3-8 cost 500 Kiwi Coins each, or are free with a premium subscription.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.services.gamification import gamification

router = APIRouter(prefix="/v2/paywall", tags=["v2-paywall"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UNLOCK_COST = 500  # Kiwi Coins per topic

_TOPIC_CATALOG = [
    {"topic_id": "topic-1-counting",       "topic_name": "Counting",       "is_free": True},
    {"topic_id": "topic-2-arithmetic",     "topic_name": "Arithmetic",     "is_free": True},
    {"topic_id": "topic-3-patterns",       "topic_name": "Patterns",       "is_free": False},
    {"topic_id": "topic-4-logic",          "topic_name": "Logic",          "is_free": False},
    {"topic_id": "topic-5-spatial",        "topic_name": "Spatial",        "is_free": False},
    {"topic_id": "topic-6-shapes",         "topic_name": "Shapes",         "is_free": False},
    {"topic_id": "topic-7-word-problems",  "topic_name": "Word Problems",  "is_free": False},
    {"topic_id": "topic-8-puzzles",        "topic_name": "Puzzles",        "is_free": False},
]

_FREE_TOPICS = {"topic-1-counting", "topic-2-arithmetic"}

_VALID_TOPIC_IDS = {t["topic_id"] for t in _TOPIC_CATALOG}

# ---------------------------------------------------------------------------
# In-memory store (with Firestore fallback)
# ---------------------------------------------------------------------------

_UNLOCK_STORE: Dict[str, Set[str]] = {}  # user_id -> set of unlocked topic_ids
_PREMIUM_USERS: Dict[str, str] = {}       # user_id -> subscription_id
_LOCK = threading.Lock()


def _get_unlocked_topics(user_id: str) -> Set[str]:
    """Return the set of topic IDs the user has unlocked (excluding free topics)."""
    with _LOCK:
        if user_id not in _UNLOCK_STORE:
            _UNLOCK_STORE[user_id] = _load_unlocks_from_firestore(user_id)
        return _UNLOCK_STORE[user_id]


def _is_premium(user_id: str) -> bool:
    """Check if user has an active premium subscription."""
    with _LOCK:
        return user_id in _PREMIUM_USERS


def _save_unlock_to_firestore(user_id: str, topic_id: str) -> None:
    """Persist a single topic unlock to Firestore."""
    try:
        from app.services.firestore_service import _get_db, is_firestore_available
        if not is_firestore_available():
            return
        db = _get_db()
        if not db:
            return
        (db.collection("users").document(user_id)
         .collection("paywall").document("unlocks")
         .set({"topics": list(_UNLOCK_STORE.get(user_id, set()))}, merge=True))
    except Exception:
        pass


def _load_unlocks_from_firestore(user_id: str) -> Set[str]:
    """Load unlock state from Firestore."""
    try:
        from app.services.firestore_service import _get_db, is_firestore_available
        if not is_firestore_available():
            return set()
        db = _get_db()
        if not db:
            return set()
        doc = (db.collection("users").document(user_id)
               .collection("paywall").document("unlocks").get())
        if doc.exists:
            return set(doc.to_dict().get("topics", []))
    except Exception:
        pass
    return set()


def _save_premium_to_firestore(user_id: str, subscription_id: str) -> None:
    """Persist premium status to Firestore."""
    try:
        from app.services.firestore_service import _get_db, is_firestore_available
        if not is_firestore_available():
            return
        db = _get_db()
        if not db:
            return
        (db.collection("users").document(user_id)
         .collection("paywall").document("premium")
         .set({"subscription_id": subscription_id, "is_premium": True}, merge=True))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class UnlockRequest(BaseModel):
    user_id: str
    topic_id: str

    @field_validator("topic_id")
    @classmethod
    def validate_topic_id(cls, v: str) -> str:
        if v not in _VALID_TOPIC_IDS:
            raise ValueError(f"Invalid topic_id: {v}. Must be one of {sorted(_VALID_TOPIC_IDS)}")
        return v


class RestoreRequest(BaseModel):
    user_id: str
    subscription_id: str


# ---------------------------------------------------------------------------
# GET /v2/paywall/status
# ---------------------------------------------------------------------------

@router.get("/status")
def get_status(user_id: str = Query(..., description="Student ID")):
    """Return unlock status for all 8 topics.

    Topics 1-2 are always free. Topics 3-8 are locked by default unless
    the user has unlocked them with Kiwi Coins or has a premium subscription.
    """
    unlocked = _get_unlocked_topics(user_id)
    premium = _is_premium(user_id)

    result = []
    for topic in _TOPIC_CATALOG:
        tid = topic["topic_id"]
        is_free = topic["is_free"]
        is_locked = not is_free and tid not in unlocked and not premium
        result.append({
            "topic_id": tid,
            "topic_name": topic["topic_name"],
            "is_locked": is_locked,
            "unlock_cost": 0 if is_free else UNLOCK_COST,
            "is_premium_free": not is_free,
        })

    return {
        "user_id": user_id,
        "is_premium": premium,
        "topics": result,
    }


# ---------------------------------------------------------------------------
# POST /v2/paywall/unlock
# ---------------------------------------------------------------------------

@router.post("/unlock")
def unlock_topic(req: UnlockRequest):
    """Unlock a topic using Kiwi Coins.

    Deducts 500 coins from the user's balance. Returns 402 if the user
    does not have enough coins.
    """
    topic_id = req.topic_id
    user_id = req.user_id

    # Free topics are always unlocked
    if topic_id in _FREE_TOPICS:
        return {
            "success": True,
            "already_unlocked": True,
            "topic_id": topic_id,
            "message": "This topic is free and always unlocked.",
        }

    # Check if already unlocked or premium
    unlocked = _get_unlocked_topics(user_id)
    if topic_id in unlocked or _is_premium(user_id):
        return {
            "success": True,
            "already_unlocked": True,
            "topic_id": topic_id,
            "message": "Topic is already unlocked.",
        }

    # Check coin balance via gamification service
    state = gamification.get_state(user_id)
    if state.kiwi_coins < UNLOCK_COST:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Insufficient Kiwi Coins",
                "coins_available": state.kiwi_coins,
                "coins_needed": UNLOCK_COST - state.kiwi_coins,
                "unlock_cost": UNLOCK_COST,
            },
        )

    # Deduct coins and unlock
    state.kiwi_coins -= UNLOCK_COST
    gamification._save_to_firestore(user_id, state)

    with _LOCK:
        unlocked.add(topic_id)
    _save_unlock_to_firestore(user_id, topic_id)

    return {
        "success": True,
        "already_unlocked": False,
        "topic_id": topic_id,
        "coins_deducted": UNLOCK_COST,
        "coins_remaining": state.kiwi_coins,
        "message": f"Topic unlocked! You spent {UNLOCK_COST} Kiwi Coins.",
    }


# ---------------------------------------------------------------------------
# POST /v2/paywall/restore
# ---------------------------------------------------------------------------

@router.post("/restore")
def restore_purchases(req: RestoreRequest):
    """Restore purchases / activate premium subscription.

    In production this would verify the subscription with Play Store or
    App Store. For now it simply marks the user as premium, unlocking
    all topics.
    """
    user_id = req.user_id
    subscription_id = req.subscription_id

    with _LOCK:
        _PREMIUM_USERS[user_id] = subscription_id

    _save_premium_to_firestore(user_id, subscription_id)

    return {
        "success": True,
        "user_id": user_id,
        "is_premium": True,
        "subscription_id": subscription_id,
        "topics_unlocked": [t["topic_id"] for t in _TOPIC_CATALOG],
        "message": "Premium activated! All topics are now unlocked.",
    }


# ---------------------------------------------------------------------------
# GET /v2/paywall/pricing
# ---------------------------------------------------------------------------

@router.get("/pricing")
def get_pricing():
    """Return pricing information for topic unlocks and subscriptions."""
    return {
        "per_topic": {
            "cost_coins": UNLOCK_COST,
            "description": f"Unlock any premium topic for {UNLOCK_COST} Kiwi Coins",
        },
        "premium_monthly": {
            "price_usd": 4.99,
            "description": "Unlock all topics + bonus coins monthly",
            "store_product_id": "com.kiwimath.premium.monthly",
        },
        "premium_yearly": {
            "price_usd": 39.99,
            "description": "Unlock all topics + bonus coins yearly (save 33%)",
            "store_product_id": "com.kiwimath.premium.yearly",
        },
        "free_topics": sorted(_FREE_TOPICS),
        "premium_topics": sorted(_VALID_TOPIC_IDS - _FREE_TOPICS),
    }
