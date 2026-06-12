"""
Bookmark storage — in-memory dict + Firestore persistence.

Firestore path: users/{uid}/bookmarks/{question_id}

Same lazy-init pattern as other stores: works in-memory when
Firestore is unavailable (local dev), persists when connected.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.firestore_service import _get_db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory fallback: uid -> {question_id -> bookmark_doc}
# ---------------------------------------------------------------------------
_mem_bookmarks: Dict[str, Dict[str, Dict[str, Any]]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def toggle_bookmark(uid: str, question_id: str) -> bool:
    """Toggle bookmark on/off. Returns True if now bookmarked, False if removed."""
    db = _get_db()

    if db:
        try:
            doc_ref = (
                db.collection("users")
                .document(uid)
                .collection("bookmarks")
                .document(question_id)
            )
            doc = doc_ref.get()
            if doc.exists:
                doc_ref.delete()
                # Also remove from memory cache
                if uid in _mem_bookmarks:
                    _mem_bookmarks[uid].pop(question_id, None)
                return False
            else:
                data = {"question_id": question_id, "bookmarked_at": _now_iso()}
                doc_ref.set(data)
                # Update memory cache
                _mem_bookmarks.setdefault(uid, {})[question_id] = data
                return True
        except Exception as e:
            logger.warning(f"Firestore bookmark toggle failed for {uid}, falling back to memory: {e}")

    # In-memory fallback
    user_bookmarks = _mem_bookmarks.setdefault(uid, {})
    if question_id in user_bookmarks:
        del user_bookmarks[question_id]
        return False
    else:
        user_bookmarks[question_id] = {
            "question_id": question_id,
            "bookmarked_at": _now_iso(),
        }
        return True


def is_bookmarked(uid: str, question_id: str) -> bool:
    """Check if a specific question is bookmarked by a user."""
    db = _get_db()

    if db:
        try:
            doc = (
                db.collection("users")
                .document(uid)
                .collection("bookmarks")
                .document(question_id)
                .get()
            )
            return doc.exists
        except Exception as e:
            logger.warning(f"Firestore bookmark check failed for {uid}: {e}")

    return question_id in _mem_bookmarks.get(uid, {})


def get_all(uid: str) -> List[Dict[str, Any]]:
    """Get all bookmarked question IDs for a user, sorted by most recent first."""
    db = _get_db()

    if db:
        try:
            docs = (
                db.collection("users")
                .document(uid)
                .collection("bookmarks")
                .order_by("bookmarked_at", direction="DESCENDING")
                .stream()
            )
            results = []
            for doc in docs:
                data = doc.to_dict()
                data["question_id"] = doc.id
                results.append(data)
            # Sync to memory cache
            _mem_bookmarks[uid] = {d["question_id"]: d for d in results}
            return results
        except Exception as e:
            logger.warning(f"Firestore bookmark list failed for {uid}: {e}")

    user_bookmarks = _mem_bookmarks.get(uid, {})
    items = list(user_bookmarks.values())
    items.sort(key=lambda x: x.get("bookmarked_at", ""), reverse=True)
    return items


def count(uid: str) -> int:
    """Count total bookmarks for a user."""
    db = _get_db()

    if db:
        try:
            docs = (
                db.collection("users")
                .document(uid)
                .collection("bookmarks")
                .stream()
            )
            return sum(1 for _ in docs)
        except Exception as e:
            logger.warning(f"Firestore bookmark count failed for {uid}: {e}")

    return len(_mem_bookmarks.get(uid, {}))
