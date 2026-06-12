"""
Generic Firestore-backed key/value state store + idempotency helpers.

Why this exists
---------------
The backend runs on Cloud Run with multiple instances. Module-level in-memory
dicts lose data on every deploy and diverge across instances. This module
gives API routers a tiny persistence layer:

    store = FirestoreBackedStore("daily_puzzle_streaks")
    data = store.get(uid)            # dict | None
    store.set(uid, data)             # synchronous write-through
    store.update(uid, {"x": 1})      # merge-update
    store.delete(uid)
    store.all(limit=500)             # [(key, value), ...] — use sparingly

Design
------
- Firestore client comes from app.services.firestore_service._get_db()
  (lazy init, returns None when Firestore is unavailable).
- When Firestore is unavailable (local dev / test suite without
  firebase-admin), every operation transparently falls back to an in-memory
  dict so behaviour is unchanged for tests.
- All WRITES go to Firestore synchronously. Reads may be served from a
  short-TTL per-instance cache ONLY if the store was created with
  cache_ttl_seconds > 0 (use for leaderboards where staleness is fine;
  never for streaks/rewards/submissions).
- Values must be JSON-serializable dicts. Convert dataclasses / pydantic
  models to plain dicts at the boundary.

Known races (accepted)
----------------------
- get() → mutate → set() is not transactional. Two instances writing the
  same key concurrently last-write-wins. Callers that need stronger
  guarantees (points, streaks) should keep mutations small and idempotent;
  remaining races are documented at each call site.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _get_db():
    """Shared lazy Firestore client. None when unavailable."""
    try:
        from app.services.firestore_service import _get_db as _shared
        return _shared()
    except Exception as e:  # pragma: no cover - import error path
        logger.warning("Could not obtain Firestore client: %s", e)
        return None


def _doc_id(key: str) -> str:
    """Firestore document ids cannot contain '/'. Keys like 'uid:puzzle' are fine."""
    return key.replace("/", "__")


class FirestoreBackedStore:
    """Key/value store backed by a Firestore collection with in-memory fallback.

    One instance per logical store, created at module import time. Cheap to
    construct (no Firestore call until first use).
    """

    def __init__(self, collection_name: str, cache_ttl_seconds: float = 0.0):
        self.collection_name = collection_name
        self.cache_ttl = cache_ttl_seconds
        self._lock = threading.Lock()
        # In-memory map. Doubles as:
        #  - the authoritative store when Firestore is unavailable
        #  - a short-TTL read cache when cache_ttl_seconds > 0
        self._mem: Dict[str, Dict[str, Any]] = {}
        self._mem_ts: Dict[str, float] = {}
        self._all_cache: Optional[List[Tuple[str, Dict[str, Any]]]] = None
        self._all_cache_ts: float = 0.0

    # -- internals ---------------------------------------------------------

    def _coll(self, db):
        return db.collection(self.collection_name)

    def _cache_put(self, key: str, value: Optional[Dict[str, Any]]) -> None:
        with self._lock:
            if value is None:
                self._mem.pop(key, None)
                self._mem_ts.pop(key, None)
            else:
                self._mem[key] = value
                self._mem_ts[key] = time.time()

    # -- public API ---------------------------------------------------------

    def get(self, key: str, allow_cached: bool = True) -> Optional[Dict[str, Any]]:
        """Return the stored dict for *key*, or None.

        allow_cached only matters when the store has a cache TTL configured;
        pass allow_cached=False to force a fresh Firestore read.
        """
        db = _get_db()
        if db is None:
            with self._lock:
                return self._mem.get(key)

        if allow_cached and self.cache_ttl > 0:
            with self._lock:
                ts = self._mem_ts.get(key)
                if ts is not None and (time.time() - ts) < self.cache_ttl:
                    return self._mem.get(key)

        try:
            doc = self._coll(db).document(_doc_id(key)).get()
            value = doc.to_dict() if doc.exists else None
            if self.cache_ttl > 0:
                self._cache_put(key, value)
            return value
        except Exception as e:
            logger.error("Firestore get failed (%s/%s): %s", self.collection_name, key, e)
            with self._lock:
                return self._mem.get(key)

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Write-through set. Value must be a JSON-serializable dict."""
        db = _get_db()
        if db is not None:
            try:
                self._coll(db).document(_doc_id(key)).set(value)
            except Exception as e:
                logger.error("Firestore set failed (%s/%s): %s", self.collection_name, key, e)
        # Always keep the in-memory copy (fallback store / warm cache).
        self._cache_put(key, value)
        self._all_cache = None

    def update(self, key: str, updates: Dict[str, Any]) -> None:
        """Merge-update fields on the stored document (creates it if missing)."""
        db = _get_db()
        if db is not None:
            try:
                self._coll(db).document(_doc_id(key)).set(updates, merge=True)
            except Exception as e:
                logger.error("Firestore update failed (%s/%s): %s", self.collection_name, key, e)
        with self._lock:
            base = self._mem.get(key) or {}
            base.update(updates)
            self._mem[key] = base
            self._mem_ts[key] = time.time()
        self._all_cache = None

    def delete(self, key: str) -> None:
        db = _get_db()
        if db is not None:
            try:
                self._coll(db).document(_doc_id(key)).delete()
            except Exception as e:
                logger.error("Firestore delete failed (%s/%s): %s", self.collection_name, key, e)
        self._cache_put(key, None)
        self._all_cache = None

    def all(self, limit: int = 500) -> List[Tuple[str, Dict[str, Any]]]:
        """Return up to *limit* (key, value) pairs.

        WARNING: full-collection scan. Only use on cold paths (leaderboards,
        cron aggregation). Honour the cache TTL when configured.
        """
        db = _get_db()
        if db is None:
            with self._lock:
                return list(self._mem.items())[:limit]

        if self.cache_ttl > 0 and self._all_cache is not None:
            if (time.time() - self._all_cache_ts) < self.cache_ttl:
                return self._all_cache[:limit]

        try:
            docs = self._coll(db).limit(limit).stream()
            result = [(d.id, d.to_dict()) for d in docs]
            if self.cache_ttl > 0:
                self._all_cache = result
                self._all_cache_ts = time.time()
            return result
        except Exception as e:
            logger.error("Firestore scan failed (%s): %s", self.collection_name, e)
            with self._lock:
                return list(self._mem.items())[:limit]


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------
#
# The Flutter client sends X-Idempotency-Key on POST /v2/answer/check and
# engagement mutations. We dedupe server-side via a Firestore collection
# `idempotency_keys` (doc id = key). Where the previous response is cheap to
# store, it is stored in the doc and replayed verbatim on a duplicate request
# (rewards must never double-grant).
#
# Race note: two concurrent requests with the same key can both pass the
# initial check (check-then-act). The window is milliseconds and retries from
# mobile clients are sequential, so this is accepted. Firestore TTL policy on
# `expires_at` should be enabled in the console to garbage-collect old keys.

_idem_store = FirestoreBackedStore("idempotency_keys")
_IDEM_MEM_PRUNE_SIZE = 20000


def get_idempotent_response(key: str) -> Optional[Dict[str, Any]]:
    """Return the previously recorded payload for *key*, or None if first time.

    A recorded key with no stored response returns {"duplicate": True}.
    """
    if not key:
        return None
    doc = _idem_store.get(key)
    if not doc:
        return None
    expires_at = doc.get("expires_at")
    if expires_at:
        try:
            if datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
                return None  # expired — treat as first time
        except (ValueError, TypeError):
            pass
    return doc.get("response") or {"duplicate": True}


def record_idempotent_response(
    key: str,
    response: Optional[Dict[str, Any]] = None,
    ttl_hours: int = 24,
) -> None:
    """Record that *key* has been processed, optionally storing the response JSON."""
    if not key:
        return
    now = datetime.now(timezone.utc)
    doc: Dict[str, Any] = {
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=ttl_hours)).isoformat(),
    }
    if response is not None:
        doc["response"] = response
    _idem_store.set(key, doc)
    # Keep the in-memory fallback bounded (only matters in local/no-Firestore mode).
    with _idem_store._lock:
        if len(_idem_store._mem) > _IDEM_MEM_PRUNE_SIZE:
            cutoff = now.isoformat()
            stale = [
                k for k, v in _idem_store._mem.items()
                if (v.get("expires_at") or "") < cutoff
            ]
            for k in stale:
                _idem_store._mem.pop(k, None)
                _idem_store._mem_ts.pop(k, None)


def check_and_record_idempotency(key: str, ttl_hours: int = 24) -> bool:
    """Return True if *key* is seen for the first time (and record it).

    Convenience wrapper for endpoints that don't replay a stored response.
    """
    if not key:
        return True
    if get_idempotent_response(key) is not None:
        return False
    record_idempotent_response(key, None, ttl_hours)
    return True
