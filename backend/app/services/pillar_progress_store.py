"""
Pillar Progress Store — tracks per-user, per-pillar progress in Firestore.

Firestore collection: pillar_progress/{userId}/pillars/{pillarId}

Falls back to in-memory dict when Firestore is unavailable (local dev).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from .firestore_service import is_firestore_available

logger = logging.getLogger("kiwimath.pillar_progress")

# In-memory fallback for local dev (no Firestore)
_mem_store: Dict[str, Dict[str, dict]] = {}  # userId -> pillarId -> progress


def _get_db():
    """Lazy import Firestore client."""
    try:
        from google.cloud import firestore
        return firestore.Client()
    except Exception:
        return None


def get_progress(user_id: str) -> dict:
    """Fetch full pillar progress summary for a user."""
    if is_firestore_available():
        try:
            db = _get_db()
            if db:
                docs = db.collection("pillar_progress").document(user_id)\
                    .collection("pillars").stream()
                pillars = {}
                for doc in docs:
                    data = doc.to_dict()
                    pillars[doc.id] = data
                return {
                    "pillars": pillars,
                    "total_questions": sum(p.get("questions_attempted", 0) for p in pillars.values()),
                    "total_correct": sum(p.get("questions_correct", 0) for p in pillars.values()),
                    "streak": 0,  # TODO: compute from daily activity
                }
        except Exception as e:
            logger.error(f"Firestore read error: {e}")

    # In-memory fallback
    user_data = _mem_store.get(user_id, {})
    return {
        "pillars": user_data,
        "total_questions": sum(p.get("questions_attempted", 0) for p in user_data.values()),
        "total_correct": sum(p.get("questions_correct", 0) for p in user_data.values()),
        "streak": 0,
    }


def record_answer(
    user_id: str,
    pillar: str,
    level: int,
    topic: str,
    question_id: str,
    correct: bool,
    time_taken_seconds: int,
) -> dict:
    """Record a single answer and update progress."""
    if is_firestore_available():
        try:
            db = _get_db()
            if db:
                ref = db.collection("pillar_progress").document(user_id)\
                    .collection("pillars").document(pillar)
                doc = ref.get()
                data = doc.to_dict() if doc.exists else _default_progress(pillar)
                _update_progress(data, level, topic, correct)
                ref.set(data)
                return data
        except Exception as e:
            logger.error(f"Firestore write error: {e}")

    # In-memory fallback
    if user_id not in _mem_store:
        _mem_store[user_id] = {}
    if pillar not in _mem_store[user_id]:
        _mem_store[user_id][pillar] = _default_progress(pillar)

    data = _mem_store[user_id][pillar]
    _update_progress(data, level, topic, correct)
    return data


def _default_progress(pillar: str) -> dict:
    return {
        "pillar": pillar,
        "current_level": 1,
        "questions_attempted": 0,
        "questions_correct": 0,
        "mastery_percent": 0.0,
        "level_progress": {},
    }


def _update_progress(data: dict, level: int, topic: str, correct: bool):
    """Mutate progress dict with new answer."""
    data["questions_attempted"] = data.get("questions_attempted", 0) + 1
    if correct:
        data["questions_correct"] = data.get("questions_correct", 0) + 1

    # Update overall mastery
    attempted = data["questions_attempted"]
    if attempted > 0:
        data["mastery_percent"] = round(data["questions_correct"] / attempted * 100, 1)

    # Update level-specific progress
    level_key = str(level)
    if "level_progress" not in data:
        data["level_progress"] = {}
    if level_key not in data["level_progress"]:
        data["level_progress"][level_key] = {
            "level": level,
            "attempted": 0,
            "correct": 0,
            "mastery": 0.0,
            "completed_topics": [],
        }

    lp = data["level_progress"][level_key]
    lp["attempted"] = lp.get("attempted", 0) + 1
    if correct:
        lp["correct"] = lp.get("correct", 0) + 1
    if lp["attempted"] > 0:
        lp["mastery"] = round(lp["correct"] / lp["attempted"] * 100, 1)
    lp["last_practiced"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Track completed topics (>= 60% mastery with >= 5 questions)
    if topic and topic not in lp.get("completed_topics", []):
        if lp["mastery"] >= 60.0 and lp["attempted"] >= 5:
            lp.setdefault("completed_topics", []).append(topic)

    # Auto-advance level if mastery >= 60% with sufficient attempts
    if lp["mastery"] >= 60.0 and lp["attempted"] >= 10:
        if level >= data.get("current_level", 1):
            data["current_level"] = min(level + 1, 5)
