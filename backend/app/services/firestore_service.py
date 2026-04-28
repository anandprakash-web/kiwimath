"""
Firestore persistence layer for Kiwimath.

Collections
===========
users/{uid}
    display_name, avatar, created_at, last_active,
    streak_current, streak_longest, streak_last_date,
    xp_total, gems, daily_goal, daily_progress, daily_date

users/{uid}/mastery/{concept_id}
    internal_score, shown_score, mastery_label, total_attempts,
    streak_current, last_practised

users/{uid}/sessions/{session_id}
    concept_id, started_at, ended_at, parent_questions, total_correct,
    total_wrong, mastery_before, mastery_after, questions_served[]

Design
------
- Reads happen on session start (load mastery snapshots for a concept + neighbours).
- Writes happen on session end (batch: update mastery, write session log, update gamification).
- During a session, state lives in server memory (in _sessions dict). Only flushed to Firestore
  when the session completes or the user disconnects.
- If Firestore is unavailable, the engine still works with in-memory defaults (graceful degradation).
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Firestore client (lazy init)
# ---------------------------------------------------------------------------

_db = None
_firestore_available = False


def _get_db():
    """Lazy-init Firestore client. Returns None if unavailable."""
    global _db, _firestore_available
    if _db is not None:
        return _db
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        # Check if already initialized.
        try:
            firebase_admin.get_app()
        except ValueError:
            # Initialize. In Cloud Run, default credentials work automatically.
            # Locally, set GOOGLE_APPLICATION_CREDENTIALS env var.
            cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()

        _db = firestore.client()
        _firestore_available = True
        logger.info("Firestore connected successfully")
        return _db
    except Exception as e:
        logger.warning(f"Firestore unavailable, using in-memory fallback: {e}")
        _firestore_available = False
        return None


def is_firestore_available() -> bool:
    """Check if Firestore is connected."""
    _get_db()
    return _firestore_available


# ---------------------------------------------------------------------------
# In-memory fallback store (for local dev without Firestore)
# ---------------------------------------------------------------------------

_mem_users: Dict[str, Dict[str, Any]] = {}
_mem_mastery: Dict[str, Dict[str, Dict[str, Any]]] = {}  # uid -> concept_id -> data
_mem_sessions: Dict[str, Dict[str, Dict[str, Any]]] = {}  # uid -> session_id -> data


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

DEFAULT_USER = {
    "display_name": "Kiwi Learner",
    "avatar": "kiwi_default",
    "created_at": None,
    "last_active": None,
    "streak_current": 0,
    "streak_longest": 0,
    "streak_last_date": None,
    "xp_total": 0,
    "gems": 10,  # starter gems
    "daily_goal": 5,
    "daily_progress": 0,
    "daily_date": None,
}


def get_user_profile(uid: str) -> Dict[str, Any]:
    """Load user profile. Creates default if doesn't exist."""
    db = _get_db()
    if db:
        try:
            doc = db.collection("users").document(uid).get()
            if doc.exists:
                data = doc.to_dict()
                # Ensure all fields present (in case of schema evolution).
                for key, default in DEFAULT_USER.items():
                    if key not in data:
                        data[key] = default
                return data
            else:
                # First time — create user doc.
                profile = {**DEFAULT_USER, "created_at": _now_iso(), "last_active": _now_iso()}
                db.collection("users").document(uid).set(profile)
                return profile
        except Exception as e:
            logger.warning(f"Firestore read failed for user {uid}, using in-memory fallback: {e}")
    # In-memory fallback.
    if uid not in _mem_users:
        _mem_users[uid] = {**DEFAULT_USER, "created_at": _now_iso(), "last_active": _now_iso()}
    return _mem_users[uid]


def update_user_profile(uid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Partial update of user profile fields."""
    db = _get_db()
    updates["last_active"] = _now_iso()
    if db:
        db.collection("users").document(uid).set(updates, merge=True)
        return get_user_profile(uid)
    else:
        if uid not in _mem_users:
            get_user_profile(uid)  # ensure exists
        _mem_users[uid].update(updates)
        return _mem_users[uid]


# ---------------------------------------------------------------------------
# Mastery persistence
# ---------------------------------------------------------------------------


def get_mastery_states(uid: str, concept_ids: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """Load mastery snapshots for a user.

    If concept_ids is None, loads ALL concepts for the user.
    Returns dict of concept_id -> mastery data.
    """
    db = _get_db()
    result = {}

    if db:
        try:
            coll = db.collection("users").document(uid).collection("mastery")
            if concept_ids:
                for cid in concept_ids:
                    doc = coll.document(cid).get()
                    if doc.exists:
                        result[cid] = doc.to_dict()
            else:
                for doc in coll.stream():
                    result[doc.id] = doc.to_dict()
            return result
        except Exception as e:
            logger.warning(f"Firestore mastery read failed for user {uid}, using in-memory fallback: {e}")

    user_mastery = _mem_mastery.get(uid, {})
    if concept_ids:
        result = {cid: user_mastery[cid] for cid in concept_ids if cid in user_mastery}
    else:
        result = dict(user_mastery)

    return result


def save_mastery_states(uid: str, mastery_states: Dict[str, Dict[str, Any]]) -> None:
    """Batch-write mastery snapshots after a session ends."""
    db = _get_db()
    now = _now_iso()

    if db:
        batch = db.batch()
        coll = db.collection("users").document(uid).collection("mastery")
        for cid, data in mastery_states.items():
            data["last_practised"] = now
            batch.set(coll.document(cid), data, merge=True)
        batch.commit()
    else:
        if uid not in _mem_mastery:
            _mem_mastery[uid] = {}
        for cid, data in mastery_states.items():
            data["last_practised"] = now
            _mem_mastery[uid][cid] = data


# ---------------------------------------------------------------------------
# Session logging
# ---------------------------------------------------------------------------


def save_session_log(uid: str, session_id: str, session_data: Dict[str, Any]) -> None:
    """Write a completed session log for analytics / parent reports."""
    db = _get_db()
    session_data["ended_at"] = _now_iso()

    if db:
        db.collection("users").document(uid).collection("sessions").document(session_id).set(session_data)
    else:
        if uid not in _mem_sessions:
            _mem_sessions[uid] = {}
        _mem_sessions[uid][session_id] = session_data


def get_recent_sessions(uid: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent session logs for a user."""
    db = _get_db()
    if db:
        docs = (
            db.collection("users").document(uid).collection("sessions")
            .order_by("ended_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return [{"session_id": d.id, **d.to_dict()} for d in docs]
    else:
        sessions = list((_mem_sessions.get(uid, {})).values())
        sessions.sort(key=lambda s: s.get("ended_at", ""), reverse=True)
        return sessions[:limit]


# ---------------------------------------------------------------------------
# Gamification updates (called on session complete)
# ---------------------------------------------------------------------------


def update_gamification_on_session_end(
    uid: str,
    xp_earned: int,
    gems_earned: int,
    questions_completed: int,
) -> Dict[str, Any]:
    """Update XP, gems, streak, and daily progress after a session.

    Returns the updated user profile.
    """
    profile = get_user_profile(uid)
    today = date.today().isoformat()

    # -- Daily progress --
    if profile.get("daily_date") == today:
        profile["daily_progress"] = profile.get("daily_progress", 0) + questions_completed
    else:
        # New day — reset daily progress.
        profile["daily_date"] = today
        profile["daily_progress"] = questions_completed

    # -- XP & Gems --
    profile["xp_total"] = profile.get("xp_total", 0) + xp_earned
    profile["gems"] = profile.get("gems", 0) + gems_earned

    # -- Streak --
    last_date = profile.get("streak_last_date")
    current_streak = profile.get("streak_current", 0)

    if last_date == today:
        pass  # already counted today
    elif last_date == _yesterday_iso():
        current_streak += 1
    else:
        current_streak = 1  # streak broken or first ever

    profile["streak_current"] = current_streak
    profile["streak_last_date"] = today
    profile["streak_longest"] = max(profile.get("streak_longest", 0), current_streak)

    # -- Persist --
    return update_user_profile(uid, profile)


def compute_session_rewards(total_correct: int, total_questions: int, streak: int) -> Dict[str, int]:
    """Compute XP and gems earned from a session."""
    # Base: 10 XP per correct answer.
    xp = total_correct * 10
    # Streak bonus: +2 XP per correct if streak >= 3.
    if streak >= 3:
        xp += total_correct * 2
    # Perfect session bonus.
    if total_correct == total_questions and total_questions >= 5:
        xp += 25

    # Gems: 1 per 3 correct answers, bonus gem for perfect.
    gems = total_correct // 3
    if total_correct == total_questions and total_questions >= 5:
        gems += 2

    return {"xp_earned": xp, "gems_earned": gems}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _yesterday_iso() -> str:
    from datetime import timedelta
    return (date.today() - timedelta(days=1)).isoformat()
