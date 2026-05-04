"""
Firestore persistence layer for the Kiwimath clan system.

Collections
===========
clans/{clan_id}                                 → clan document
clans/{clan_id}/daily_scores/{date}             → daily aggregated scores
clans/{clan_id}/challenges/{cid}                → per-challenge clan progress
clans/{clan_id}/challenges/{cid}/guesses/{uid}  → member guesses
challenges/{challenge_id}                       → global challenge definitions

Design
------
- Mirrors the pattern in firestore_service.py: lazy Firestore init, graceful
  degradation to safe defaults when Firestore is unavailable.
- Every public method returns a sensible default (None, empty list, etc.) on
  failure so callers never need to handle Firestore outages.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Firestore client — reuse the lazy-init helper from firestore_service
# ---------------------------------------------------------------------------

def _get_db():
    """Import and delegate to the shared Firestore client initialiser."""
    try:
        from app.services.firestore_service import _get_db as _shared_get_db
        return _shared_get_db()
    except Exception as e:
        logger.warning("Could not obtain Firestore client: %s", e)
        return None


# ---------------------------------------------------------------------------
# ClanFirestoreService
# ---------------------------------------------------------------------------

class ClanFirestoreService:
    """Wraps all clan-related Firestore operations.

    Every method acquires the Firestore client via ``_get_db()``.  If the
    client is ``None`` (Firestore not configured / unavailable), the method
    logs a warning and returns an appropriate default so the caller can
    fall back to in-memory storage.
    """

    # ------------------------------------------------------------------ #
    # Clan CRUD
    # ------------------------------------------------------------------ #

    def get_clan(self, clan_id: str) -> Optional[Dict[str, Any]]:
        """Return the clan document as a dict, or None if not found."""
        db = _get_db()
        if not db:
            logger.warning("Firestore unavailable — cannot read clan %s", clan_id)
            return None
        try:
            doc = db.collection("clans").document(clan_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error("Failed to get clan %s: %s", clan_id, e)
            return None

    def create_clan(self, clan_id: str, data: Dict[str, Any]) -> None:
        """Create a new clan document."""
        db = _get_db()
        if not db:
            logger.warning("Firestore unavailable — cannot create clan %s", clan_id)
            return
        try:
            db.collection("clans").document(clan_id).set(data)
        except Exception as e:
            logger.error("Failed to create clan %s: %s", clan_id, e)

    def update_clan(self, clan_id: str, updates: Dict[str, Any]) -> None:
        """Merge-update fields on an existing clan document."""
        db = _get_db()
        if not db:
            logger.warning("Firestore unavailable — cannot update clan %s", clan_id)
            return
        try:
            db.collection("clans").document(clan_id).set(updates, merge=True)
        except Exception as e:
            logger.error("Failed to update clan %s: %s", clan_id, e)

    def delete_clan(self, clan_id: str) -> None:
        """Delete a clan document.

        Note: Firestore does not cascade-delete subcollections.  Subcollection
        cleanup (daily_scores, challenges, guesses) should be handled
        separately if needed.
        """
        db = _get_db()
        if not db:
            logger.warning("Firestore unavailable — cannot delete clan %s", clan_id)
            return
        try:
            db.collection("clans").document(clan_id).delete()
        except Exception as e:
            logger.error("Failed to delete clan %s: %s", clan_id, e)

    # ------------------------------------------------------------------ #
    # Clan queries
    # ------------------------------------------------------------------ #

    def find_clan_by_member(
        self, user_uid: str
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find the active clan that contains *user_uid*.

        Uses a Firestore ``array_contains`` query on the ``member_uids``
        field.  Returns ``(clan_id, clan_dict)`` or ``None``.
        """
        db = _get_db()
        if not db:
            logger.warning(
                "Firestore unavailable — cannot find clan for member %s", user_uid
            )
            return None
        try:
            docs = (
                db.collection("clans")
                .where("member_uids", "array_contains", user_uid)
                .where("status", "==", "active")
                .limit(1)
                .stream()
            )
            for doc in docs:
                return (doc.id, doc.to_dict())
            return None
        except Exception as e:
            logger.error("Failed to find clan for member %s: %s", user_uid, e)
            return None

    def find_clans_by_grade(
        self, grade: int, limit: int = 50
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Return active clans for a given grade, up to *limit* results."""
        db = _get_db()
        if not db:
            logger.warning(
                "Firestore unavailable — cannot find clans for grade %s", grade
            )
            return []
        try:
            docs = (
                db.collection("clans")
                .where("grade", "==", grade)
                .where("status", "==", "active")
                .limit(limit)
                .stream()
            )
            return [(doc.id, doc.to_dict()) for doc in docs]
        except Exception as e:
            logger.error("Failed to find clans for grade %s: %s", grade, e)
            return []

    # ------------------------------------------------------------------ #
    # Global challenges
    # ------------------------------------------------------------------ #

    def get_challenge(self, challenge_id: str) -> Optional[Dict[str, Any]]:
        """Return a global challenge definition, or None."""
        db = _get_db()
        if not db:
            logger.warning(
                "Firestore unavailable — cannot read challenge %s", challenge_id
            )
            return None
        try:
            doc = db.collection("challenges").document(challenge_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error("Failed to get challenge %s: %s", challenge_id, e)
            return None

    def create_challenge(self, challenge_id: str, data: Dict[str, Any]) -> None:
        """Create a global challenge document."""
        db = _get_db()
        if not db:
            logger.warning(
                "Firestore unavailable — cannot create challenge %s", challenge_id
            )
            return
        try:
            db.collection("challenges").document(challenge_id).set(data)
        except Exception as e:
            logger.error("Failed to create challenge %s: %s", challenge_id, e)

    # ------------------------------------------------------------------ #
    # Per-clan challenge progress (subcollection)
    # ------------------------------------------------------------------ #

    def get_challenge_progress(
        self, clan_id: str, challenge_id: str
    ) -> Optional[Dict[str, Any]]:
        """Return a clan's progress for a specific challenge, or None."""
        db = _get_db()
        if not db:
            logger.warning(
                "Firestore unavailable — cannot read challenge progress "
                "for clan %s / challenge %s",
                clan_id,
                challenge_id,
            )
            return None
        try:
            doc = (
                db.collection("clans")
                .document(clan_id)
                .collection("challenges")
                .document(challenge_id)
                .get()
            )
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(
                "Failed to get challenge progress for clan %s / challenge %s: %s",
                clan_id,
                challenge_id,
                e,
            )
            return None

    def update_challenge_progress(
        self, clan_id: str, challenge_id: str, updates: Dict[str, Any]
    ) -> None:
        """Merge-update a clan's challenge progress document."""
        db = _get_db()
        if not db:
            logger.warning(
                "Firestore unavailable — cannot update challenge progress "
                "for clan %s / challenge %s",
                clan_id,
                challenge_id,
            )
            return
        try:
            (
                db.collection("clans")
                .document(clan_id)
                .collection("challenges")
                .document(challenge_id)
                .set(updates, merge=True)
            )
        except Exception as e:
            logger.error(
                "Failed to update challenge progress for clan %s / challenge %s: %s",
                clan_id,
                challenge_id,
                e,
            )

    # ------------------------------------------------------------------ #
    # Guesses (nested subcollection under challenges)
    # ------------------------------------------------------------------ #

    def get_guesses(
        self, clan_id: str, challenge_id: str
    ) -> List[Dict[str, Any]]:
        """Return all guesses for a clan+challenge, sorted by submitted_at."""
        db = _get_db()
        if not db:
            logger.warning(
                "Firestore unavailable — cannot read guesses "
                "for clan %s / challenge %s",
                clan_id,
                challenge_id,
            )
            return []
        try:
            docs = (
                db.collection("clans")
                .document(clan_id)
                .collection("challenges")
                .document(challenge_id)
                .collection("guesses")
                .order_by("submitted_at")
                .stream()
            )
            return [{"uid": doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            logger.error(
                "Failed to get guesses for clan %s / challenge %s: %s",
                clan_id,
                challenge_id,
                e,
            )
            return []

    def add_guess(
        self,
        clan_id: str,
        challenge_id: str,
        user_uid: str,
        guess_data: Dict[str, Any],
    ) -> None:
        """Write (or overwrite) a member's guess for a challenge.

        The document id is the user's UID, so each member has at most one
        guess document per challenge (latest guess wins).
        """
        db = _get_db()
        if not db:
            logger.warning(
                "Firestore unavailable — cannot add guess "
                "for user %s in clan %s / challenge %s",
                user_uid,
                clan_id,
                challenge_id,
            )
            return
        try:
            (
                db.collection("clans")
                .document(clan_id)
                .collection("challenges")
                .document(challenge_id)
                .collection("guesses")
                .document(user_uid)
                .set(guess_data)
            )
        except Exception as e:
            logger.error(
                "Failed to add guess for user %s in clan %s / challenge %s: %s",
                user_uid,
                clan_id,
                challenge_id,
                e,
            )

    # ------------------------------------------------------------------ #
    # Daily scores (subcollection)
    # ------------------------------------------------------------------ #

    def get_daily_scores(
        self, clan_id: str, date_str: str
    ) -> Optional[Dict[str, Any]]:
        """Return the daily score document for *clan_id* on *date_str*."""
        db = _get_db()
        if not db:
            logger.warning(
                "Firestore unavailable — cannot read daily scores "
                "for clan %s on %s",
                clan_id,
                date_str,
            )
            return None
        try:
            doc = (
                db.collection("clans")
                .document(clan_id)
                .collection("daily_scores")
                .document(date_str)
                .get()
            )
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(
                "Failed to get daily scores for clan %s on %s: %s",
                clan_id,
                date_str,
                e,
            )
            return None

    def set_daily_scores(
        self, clan_id: str, date_str: str, data: Dict[str, Any]
    ) -> None:
        """Write (overwrite) the daily score document for a clan."""
        db = _get_db()
        if not db:
            logger.warning(
                "Firestore unavailable — cannot set daily scores "
                "for clan %s on %s",
                clan_id,
                date_str,
            )
            return
        try:
            (
                db.collection("clans")
                .document(clan_id)
                .collection("daily_scores")
                .document(date_str)
                .set(data)
            )
        except Exception as e:
            logger.error(
                "Failed to set daily scores for clan %s on %s: %s",
                clan_id,
                date_str,
                e,
            )
