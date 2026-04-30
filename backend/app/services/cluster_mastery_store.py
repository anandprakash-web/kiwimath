"""
Firestore persistence layer for per-user, per-cluster mastery tracking.

Collection
==========
users/{uid}/cluster_mastery/{cluster_doc_id}
    cluster_doc_id = cluster.replace("/", "__")  (e.g. "arithmetic__division-hard")

    attempts, correct, accuracy, streak, mastered,
    last_seen, mastered_at

Mastery rules
-------------
- Mastered when: streak >= 3 OR (accuracy >= 0.8 AND attempts >= 5)
- Mastery decays: if last_seen is older than 7 days, mastered resets to False on read.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from app.services.firestore_service import _get_db

logger = logging.getLogger(__name__)

MASTERY_DECAY_DAYS = 7

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ClusterMastery:
    attempts: int = 0
    correct: int = 0
    accuracy: float = 0.0
    streak: int = 0
    mastered: bool = False
    last_seen: str = ""
    mastered_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempts": self.attempts,
            "correct": self.correct,
            "accuracy": self.accuracy,
            "streak": self.streak,
            "mastered": self.mastered,
            "last_seen": self.last_seen,
            "mastered_at": self.mastered_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ClusterMastery:
        return cls(
            attempts=d.get("attempts", 0),
            correct=d.get("correct", 0),
            accuracy=d.get("accuracy", 0.0),
            streak=d.get("streak", 0),
            mastered=d.get("mastered", False),
            last_seen=d.get("last_seen", ""),
            mastered_at=d.get("mastered_at"),
        )


# ---------------------------------------------------------------------------
# In-memory fallback store
# ---------------------------------------------------------------------------

_mem_cluster_mastery: Dict[str, Dict[str, Dict[str, Any]]] = {}  # uid -> doc_id -> data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _doc_id(cluster: str) -> str:
    """Convert cluster name to a safe Firestore document ID."""
    return cluster.replace("/", "__")


def _cluster_name(doc_id: str) -> str:
    """Reverse of _doc_id."""
    return doc_id.replace("__", "/")


def _is_stale(last_seen: str) -> bool:
    """Return True if last_seen is older than MASTERY_DECAY_DAYS."""
    if not last_seen:
        return False
    try:
        seen_dt = datetime.fromisoformat(last_seen)
        return (datetime.now(timezone.utc) - seen_dt) > timedelta(days=MASTERY_DECAY_DAYS)
    except (ValueError, TypeError):
        return False


def _evaluate_mastery(m: ClusterMastery) -> None:
    """Re-evaluate and update mastery status in place."""
    now = _now_iso()
    was_mastered = m.mastered
    m.mastered = m.streak >= 3 or (m.accuracy >= 0.8 and m.attempts >= 5)
    if m.mastered and not was_mastered:
        m.mastered_at = now
    elif not m.mastered:
        m.mastered_at = None


def _apply_decay(m: ClusterMastery) -> None:
    """If last_seen is stale, reset mastered flag (but keep stats)."""
    if m.mastered and _is_stale(m.last_seen):
        m.mastered = False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def record_cluster_attempt(uid: str, cluster: str, is_correct: bool) -> ClusterMastery:
    """Record one attempt on a cluster and return updated mastery state."""
    did = _doc_id(cluster)
    db = _get_db()

    # -- Load current state --
    m = _load_one(db, uid, did)

    # -- Update --
    m.attempts += 1
    if is_correct:
        m.correct += 1
        m.streak += 1
    else:
        m.streak = 0
    m.accuracy = m.correct / m.attempts if m.attempts > 0 else 0.0
    m.last_seen = _now_iso()
    _evaluate_mastery(m)

    # -- Save --
    _save_one(db, uid, did, m)
    return m


def get_cluster_mastery(uid: str) -> Dict[str, ClusterMastery]:
    """Return all cluster mastery records for a user, with decay applied."""
    db = _get_db()
    raw = _load_all(db, uid)
    result: Dict[str, ClusterMastery] = {}
    for did, data in raw.items():
        m = ClusterMastery.from_dict(data)
        _apply_decay(m)
        result[_cluster_name(did)] = m
    return result


def get_mastered_clusters(uid: str) -> Set[str]:
    """Return the set of cluster names currently mastered."""
    all_mastery = get_cluster_mastery(uid)
    return {name for name, m in all_mastery.items() if m.mastered}


def get_weak_clusters(
    uid: str, min_attempts: int = 2
) -> List[Tuple[str, ClusterMastery]]:
    """Return non-mastered clusters sorted by accuracy ascending (weakest first).

    Only includes clusters with at least *min_attempts* attempts.
    """
    all_mastery = get_cluster_mastery(uid)
    weak = [
        (name, m)
        for name, m in all_mastery.items()
        if m.attempts >= min_attempts and not m.mastered
    ]
    weak.sort(key=lambda pair: pair[1].accuracy)
    return weak


# ---------------------------------------------------------------------------
# Internal Firestore / in-memory CRUD
# ---------------------------------------------------------------------------


def _load_one(db, uid: str, did: str) -> ClusterMastery:
    if db:
        try:
            doc = (
                db.collection("users")
                .document(uid)
                .collection("cluster_mastery")
                .document(did)
                .get()
            )
            if doc.exists:
                return ClusterMastery.from_dict(doc.to_dict())
            return ClusterMastery()
        except Exception as e:
            logger.warning(
                f"Firestore read failed for cluster_mastery {uid}/{did}: {e}"
            )
    # In-memory fallback.
    data = _mem_cluster_mastery.get(uid, {}).get(did, {})
    return ClusterMastery.from_dict(data) if data else ClusterMastery()


def _save_one(db, uid: str, did: str, m: ClusterMastery) -> None:
    payload = m.to_dict()
    if db:
        try:
            (
                db.collection("users")
                .document(uid)
                .collection("cluster_mastery")
                .document(did)
                .set(payload, merge=True)
            )
            return
        except Exception as e:
            logger.warning(
                f"Firestore write failed for cluster_mastery {uid}/{did}: {e}"
            )
    # In-memory fallback.
    _mem_cluster_mastery.setdefault(uid, {})[did] = payload


def _load_all(db, uid: str) -> Dict[str, Dict[str, Any]]:
    if db:
        try:
            coll = (
                db.collection("users")
                .document(uid)
                .collection("cluster_mastery")
            )
            return {doc.id: doc.to_dict() for doc in coll.stream()}
        except Exception as e:
            logger.warning(
                f"Firestore stream failed for cluster_mastery {uid}: {e}"
            )
    return dict(_mem_cluster_mastery.get(uid, {}))
