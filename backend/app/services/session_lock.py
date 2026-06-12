"""
Multi-device session locking.

Prevents concurrent sessions on different devices from corrupting
the student's adaptive state. When a student starts a session,
we acquire a lock. If another device tries to start a session,
it gets a 409 Conflict with details about the active session.

Lock storage:
  - Firestore (production): collection `session_locks`, doc id = user_id.
    TTL is enforced via the `expires_at` epoch timestamp stored on the
    document (expired docs are treated as released and overwritten).
    Acquisition uses a Firestore transaction so two devices racing for
    the same user cannot both win across Cloud Run instances.
  - In-memory fallback (dev/test): dict-based with expiry. Also kept as a
    per-instance mirror, but Firestore is authoritative when available.

Lock TTL: 10 minutes (auto-expires if device disconnects without
properly ending the session). Heartbeats extend the lock.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from threading import Lock as ThreadLock
from typing import Dict, Optional

logger = logging.getLogger(__name__)

LOCK_TTL_SECONDS = 600  # 10 minutes
HEARTBEAT_EXTENSION = 300  # 5 minutes added per heartbeat
_COLLECTION = "session_locks"


def _get_db():
    """Lazy shared Firestore client (None when unavailable)."""
    try:
        from app.services.firestore_service import _get_db as _shared
        return _shared()
    except Exception as e:  # pragma: no cover
        logger.warning("Could not obtain Firestore client for session locks: %s", e)
        return None


@dataclass
class SessionLock:
    user_id: str
    device_id: str
    lock_id: str
    acquired_at: float  # time.time()
    expires_at: float
    topic_id: Optional[str] = None
    grade: Optional[int] = None

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "device_id": self.device_id,
            "lock_id": self.lock_id,
            "acquired_at": self.acquired_at,
            "expires_at": self.expires_at,
            "topic_id": self.topic_id,
            "grade": self.grade,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionLock":
        return cls(
            user_id=data.get("user_id", ""),
            device_id=data.get("device_id", ""),
            lock_id=data.get("lock_id", ""),
            acquired_at=float(data.get("acquired_at", 0.0)),
            expires_at=float(data.get("expires_at", 0.0)),
            topic_id=data.get("topic_id"),
            grade=data.get("grade"),
        )


class SessionLockStore:
    """Session lock store: Firestore-authoritative with in-memory fallback."""

    def __init__(self):
        self._locks: Dict[str, SessionLock] = {}  # user_id -> lock (fallback/mirror)
        self._mutex = ThreadLock()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def acquire(
        self,
        user_id: str,
        device_id: str,
        topic_id: Optional[str] = None,
        grade: Optional[int] = None,
    ) -> tuple[bool, SessionLock]:
        """Try to acquire a session lock for a user.

        Returns (success, lock). If success=False, lock contains
        the existing active lock (for the 409 response).
        """
        db = _get_db()
        if db is not None:
            try:
                ok, lock = self._acquire_firestore(db, user_id, device_id, topic_id, grade)
                with self._mutex:
                    self._locks[user_id] = lock  # mirror for debugging/fast reads
                return ok, lock
            except Exception as e:
                logger.error("Firestore lock acquire failed for %s: %s", user_id, e)
        return self._acquire_memory(user_id, device_id, topic_id, grade)

    def heartbeat(self, user_id: str, device_id: str) -> bool:
        """Extend an active lock's TTL. Returns False if no matching lock."""
        db = _get_db()
        if db is not None:
            try:
                ref = db.collection(_COLLECTION).document(user_id)
                snap = ref.get()
                if not snap.exists:
                    return False
                lock = SessionLock.from_dict(snap.to_dict())
                if lock.is_expired or lock.device_id != device_id:
                    return False
                # Small read-modify-write race with a concurrent acquire from
                # another device is acceptable: worst case a heartbeat briefly
                # extends a lock the acquirer is about to overwrite.
                new_expiry = time.time() + HEARTBEAT_EXTENSION
                ref.set({"expires_at": new_expiry}, merge=True)
                with self._mutex:
                    mirrored = self._locks.get(user_id)
                    if mirrored and mirrored.device_id == device_id:
                        mirrored.expires_at = new_expiry
                return True
            except Exception as e:
                logger.error("Firestore lock heartbeat failed for %s: %s", user_id, e)
        return self._heartbeat_memory(user_id, device_id)

    def release(self, user_id: str, device_id: str) -> bool:
        """Release the lock (session ended). Returns False if no matching lock."""
        db = _get_db()
        if db is not None:
            try:
                ref = db.collection(_COLLECTION).document(user_id)
                snap = ref.get()
                if not snap.exists:
                    return True  # already released
                lock = SessionLock.from_dict(snap.to_dict())
                if lock.device_id != device_id and not lock.is_expired:
                    return False  # can't release another device's active lock
                ref.delete()
                with self._mutex:
                    self._locks.pop(user_id, None)
                return True
            except Exception as e:
                logger.error("Firestore lock release failed for %s: %s", user_id, e)
        return self._release_memory(user_id, device_id)

    def get_active_lock(self, user_id: str) -> Optional[SessionLock]:
        """Get the active lock for a user, if any."""
        db = _get_db()
        if db is not None:
            try:
                snap = db.collection(_COLLECTION).document(user_id).get()
                if not snap.exists:
                    return None
                lock = SessionLock.from_dict(snap.to_dict())
                if lock.is_expired:
                    return None  # left for the next acquire to overwrite
                return lock
            except Exception as e:
                logger.error("Firestore lock read failed for %s: %s", user_id, e)
        with self._mutex:
            lock = self._locks.get(user_id)
            if lock and not lock.is_expired:
                return lock
            if lock and lock.is_expired:
                del self._locks[user_id]
            return None

    def force_release(self, user_id: str) -> bool:
        """Admin: force-release a stuck lock."""
        released = False
        db = _get_db()
        if db is not None:
            try:
                db.collection(_COLLECTION).document(user_id).delete()
                released = True
            except Exception as e:
                logger.error("Firestore lock force-release failed for %s: %s", user_id, e)
        with self._mutex:
            if user_id in self._locks:
                del self._locks[user_id]
                released = True
        return released

    # ------------------------------------------------------------------ #
    # Firestore path
    # ------------------------------------------------------------------ #

    def _acquire_firestore(
        self,
        db,
        user_id: str,
        device_id: str,
        topic_id: Optional[str],
        grade: Optional[int],
    ) -> tuple[bool, SessionLock]:
        """Transactional acquire — authoritative across all instances."""
        from google.cloud import firestore as gcf  # lazy: only when Firestore live

        ref = db.collection(_COLLECTION).document(user_id)
        transaction = db.transaction()

        @gcf.transactional
        def _txn(tx) -> tuple[bool, SessionLock]:
            snap = ref.get(transaction=tx)
            now = time.time()
            if snap.exists:
                existing = SessionLock.from_dict(snap.to_dict())
                if not existing.is_expired:
                    if existing.device_id == device_id:
                        # Same device re-acquiring — extend the lock.
                        existing.expires_at = now + LOCK_TTL_SECONDS
                        existing.topic_id = topic_id
                        existing.grade = grade
                        tx.set(ref, existing.to_dict())
                        return True, existing
                    return False, existing  # different device — blocked

            lock = SessionLock(
                user_id=user_id,
                device_id=device_id,
                lock_id=str(uuid.uuid4())[:8],
                acquired_at=now,
                expires_at=now + LOCK_TTL_SECONDS,
                topic_id=topic_id,
                grade=grade,
            )
            tx.set(ref, lock.to_dict())
            return True, lock

        return _txn(transaction)

    # ------------------------------------------------------------------ #
    # In-memory fallback (dev/test, or Firestore outage)
    # ------------------------------------------------------------------ #

    def _acquire_memory(
        self,
        user_id: str,
        device_id: str,
        topic_id: Optional[str],
        grade: Optional[int],
    ) -> tuple[bool, SessionLock]:
        with self._mutex:
            existing = self._locks.get(user_id)

            if existing and not existing.is_expired:
                if existing.device_id == device_id:
                    existing.expires_at = time.time() + LOCK_TTL_SECONDS
                    existing.topic_id = topic_id
                    existing.grade = grade
                    return True, existing
                return False, existing

            lock = SessionLock(
                user_id=user_id,
                device_id=device_id,
                lock_id=str(uuid.uuid4())[:8],
                acquired_at=time.time(),
                expires_at=time.time() + LOCK_TTL_SECONDS,
                topic_id=topic_id,
                grade=grade,
            )
            self._locks[user_id] = lock
            return True, lock

    def _heartbeat_memory(self, user_id: str, device_id: str) -> bool:
        with self._mutex:
            lock = self._locks.get(user_id)
            if not lock or lock.is_expired or lock.device_id != device_id:
                return False
            lock.expires_at = time.time() + HEARTBEAT_EXTENSION
            return True

    def _release_memory(self, user_id: str, device_id: str) -> bool:
        with self._mutex:
            lock = self._locks.get(user_id)
            if not lock:
                return True  # already released
            if lock.device_id != device_id and not lock.is_expired:
                return False
            del self._locks[user_id]
            return True


# Module-level singleton
session_lock_store = SessionLockStore()
