"""
Multi-device session locking.

Prevents concurrent sessions on different devices from corrupting
the student's adaptive state. When a student starts a session,
we acquire a lock. If another device tries to start a session,
it gets a 409 Conflict with details about the active session.

Lock storage:
  - Firestore (production): uses server timestamps for TTL
  - In-memory fallback (dev/test): dict-based with expiry

Lock TTL: 10 minutes (auto-expires if device disconnects without
properly ending the session). Heartbeats extend the lock.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock as ThreadLock
from typing import Dict, Optional

from app.services.firestore_service import is_firestore_available

LOCK_TTL_SECONDS = 600  # 10 minutes
HEARTBEAT_EXTENSION = 300  # 5 minutes added per heartbeat


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


class SessionLockStore:
    """In-memory session lock store (Firestore extension possible)."""

    def __init__(self):
        self._locks: Dict[str, SessionLock] = {}  # user_id -> lock
        self._mutex = ThreadLock()

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
        with self._mutex:
            existing = self._locks.get(user_id)

            if existing and not existing.is_expired:
                if existing.device_id == device_id:
                    # Same device re-acquiring — extend the lock
                    existing.expires_at = time.time() + LOCK_TTL_SECONDS
                    existing.topic_id = topic_id
                    existing.grade = grade
                    return True, existing
                else:
                    # Different device — blocked
                    return False, existing

            # No active lock or expired — grant new one
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

    def heartbeat(self, user_id: str, device_id: str) -> bool:
        """Extend an active lock's TTL. Returns False if no matching lock."""
        with self._mutex:
            lock = self._locks.get(user_id)
            if not lock or lock.is_expired or lock.device_id != device_id:
                return False
            lock.expires_at = time.time() + HEARTBEAT_EXTENSION
            return True

    def release(self, user_id: str, device_id: str) -> bool:
        """Release the lock (session ended). Returns False if no matching lock."""
        with self._mutex:
            lock = self._locks.get(user_id)
            if not lock:
                return True  # Already released
            if lock.device_id != device_id and not lock.is_expired:
                return False  # Can't release another device's lock
            del self._locks[user_id]
            return True

    def get_active_lock(self, user_id: str) -> Optional[SessionLock]:
        """Get the active lock for a user, if any."""
        with self._mutex:
            lock = self._locks.get(user_id)
            if lock and not lock.is_expired:
                return lock
            if lock and lock.is_expired:
                del self._locks[user_id]
            return None

    def force_release(self, user_id: str) -> bool:
        """Admin: force-release a stuck lock."""
        with self._mutex:
            if user_id in self._locks:
                del self._locks[user_id]
                return True
            return False


# Module-level singleton
session_lock_store = SessionLockStore()
