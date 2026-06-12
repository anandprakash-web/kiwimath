"""
Firestore-backed flag store for question flagging system.

Stores student/parent flags on problematic questions for quality review.
Persists to Firestore collection `flags`. Falls back to in-memory storage
if Firestore is unavailable (same graceful degradation pattern as other services).
"""

import logging
import threading
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class FlagType(str, Enum):
    answer_error = "answer_error"
    hint_not_good = "hint_not_good"
    visual_missing = "visual_missing"
    visual_mismatch = "visual_mismatch"
    question_error = "question_error"
    diagnostic_review = "diagnostic_review"  # Admin review of diagnostic test questions
    difficulty_wrong = "difficulty_wrong"
    stem_unclear = "stem_unclear"
    other = "other"


# ---------------------------------------------------------------------------
# Firestore client — reuse the lazy-init helper from firestore_service
# ---------------------------------------------------------------------------

def _get_db():
    """Import and delegate to the shared Firestore client initialiser."""
    try:
        from app.services.firestore_service import _get_db as _shared_get_db
        return _shared_get_db()
    except Exception as e:
        logger.warning("Could not obtain Firestore client for flag_store: %s", e)
        return None


_COLLECTION = "flags"


class FlagStore:
    """Firestore-backed store for question flags with in-memory fallback.

    Firestore document ID = flag_id (deterministic for deduplication).
    Deduplication key: (question_id, student_id, flag_type).
    """

    def __init__(self):
        # In-memory fallback used when Firestore is unavailable.
        self._flags: list[dict] = []
        self._lock = threading.Lock()
        self._firestore_mode: Optional[bool] = None  # lazy detection

    # ── Helpers ────────────────────────────────────────────────────────

    def _use_firestore(self) -> bool:
        """Check if Firestore is available. Re-checks on every call so that
        Firestore becoming available mid-process is picked up."""
        available = _get_db() is not None
        if self._firestore_mode is None and available:
            logger.info("FlagStore: using Firestore persistence")
        elif self._firestore_mode is None and not available:
            logger.warning("FlagStore: Firestore unavailable, using in-memory fallback")
        self._firestore_mode = available
        return self._firestore_mode

    def _dedup_doc_id(self, question_id: str, student_id: str, flag_type: str) -> str:
        """Deterministic document ID for deduplication."""
        # Use a stable hash so the same triple always maps to the same doc.
        import hashlib
        key = f"{question_id}|{student_id}|{flag_type}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    # ── Write ──────────────────────────────────────────────────────────

    def add_flag(
        self,
        question_id: str,
        student_id: str,
        flag_type: FlagType,
        comment: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """Store a new flag and return it.

        If a flag with the same question_id, student_id, and flag_type
        already exists, update its timestamp and comment instead of
        creating a duplicate.
        """
        now = datetime.now(timezone.utc).isoformat()
        flag_type_value = flag_type.value if isinstance(flag_type, FlagType) else flag_type

        if self._use_firestore():
            return self._add_flag_firestore(
                question_id, student_id, flag_type_value, comment, session_id, now
            )
        else:
            return self._add_flag_memory(
                question_id, student_id, flag_type_value, comment, session_id, now
            )

    def _add_flag_firestore(
        self,
        question_id: str,
        student_id: str,
        flag_type_value: str,
        comment: Optional[str],
        session_id: Optional[str],
        now: str,
    ) -> dict:
        db = _get_db()
        if not db:
            # Firestore went away — fall back for this call
            return self._add_flag_memory(
                question_id, student_id, flag_type_value, comment, session_id, now
            )

        dedup_id = self._dedup_doc_id(question_id, student_id, flag_type_value)
        doc_ref = db.collection(_COLLECTION).document(dedup_id)

        try:
            existing_doc = doc_ref.get()
            if existing_doc.exists:
                # Update existing flag (deduplication).
                updates = {"comment": comment, "created_at": now}
                if session_id is not None:
                    updates["session_id"] = session_id
                doc_ref.update(updates)
                data = existing_doc.to_dict()
                data.update(updates)
                return data
            else:
                # New flag.
                flag_id = uuid.uuid4().hex[:12]
                flag = {
                    "flag_id": flag_id,
                    "question_id": question_id,
                    "student_id": student_id,
                    "flag_type": flag_type_value,
                    "comment": comment,
                    "session_id": session_id,
                    "created_at": now,
                }
                doc_ref.set(flag)
                return flag
        except Exception as e:
            logger.error("FlagStore: Firestore write failed, falling back to memory: %s", e)
            return self._add_flag_memory(
                question_id, student_id, flag_type_value, comment, session_id, now
            )

    def _add_flag_memory(
        self,
        question_id: str,
        student_id: str,
        flag_type_value: str,
        comment: Optional[str],
        session_id: Optional[str],
        now: str,
    ) -> dict:
        with self._lock:
            for existing in self._flags:
                if (
                    existing["question_id"] == question_id
                    and existing["student_id"] == student_id
                    and existing["flag_type"] == flag_type_value
                ):
                    existing["comment"] = comment
                    existing["created_at"] = now
                    if session_id is not None:
                        existing["session_id"] = session_id
                    # Attempt write-through to Firestore
                    self._try_write_through(question_id, student_id, flag_type_value, existing)
                    return existing

            flag = {
                "flag_id": uuid.uuid4().hex[:12],
                "question_id": question_id,
                "student_id": student_id,
                "flag_type": flag_type_value,
                "comment": comment,
                "session_id": session_id,
                "created_at": now,
            }
            self._flags.append(flag)
            # Attempt write-through to Firestore
            self._try_write_through(question_id, student_id, flag_type_value, flag)
            return flag

    def _try_write_through(
        self,
        question_id: str,
        student_id: str,
        flag_type_value: str,
        flag_data: dict,
    ) -> None:
        """Attempt to write an in-memory flag to Firestore (write-through).

        Called from the in-memory fallback path.  If Firestore has become
        available since the initial check, this succeeds and the data is
        persisted.
        """
        try:
            db = _get_db()
            if not db:
                return
            dedup_id = self._dedup_doc_id(question_id, student_id, flag_type_value)
            db.collection(_COLLECTION).document(dedup_id).set(flag_data, merge=True)
        except Exception as e:
            logger.warning("FlagStore: write-through to Firestore failed: %s", e)

    # ── Read ───────────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        """Return all flags, newest first."""
        if self._use_firestore():
            return self._get_all_firestore()
        with self._lock:
            return list(reversed(self._flags))

    def _get_all_firestore(self) -> list[dict]:
        db = _get_db()
        if not db:
            with self._lock:
                return list(reversed(self._flags))
        try:
            docs = (
                db.collection(_COLLECTION)
                .order_by("created_at", direction="DESCENDING")
                .stream()
            )
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error("FlagStore: Firestore read (get_all) failed: %s", e)
            with self._lock:
                return list(reversed(self._flags))

    def get_by_question(self, question_id: str) -> list[dict]:
        """Return all flags for a specific question, newest first."""
        if self._use_firestore():
            return self._get_by_question_firestore(question_id)
        with self._lock:
            return [
                f for f in reversed(self._flags) if f["question_id"] == question_id
            ]

    def _get_by_question_firestore(self, question_id: str) -> list[dict]:
        db = _get_db()
        if not db:
            with self._lock:
                return [
                    f for f in reversed(self._flags) if f["question_id"] == question_id
                ]
        try:
            docs = (
                db.collection(_COLLECTION)
                .where("question_id", "==", question_id)
                .order_by("created_at", direction="DESCENDING")
                .stream()
            )
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error("FlagStore: Firestore read (get_by_question) failed: %s", e)
            with self._lock:
                return [
                    f for f in reversed(self._flags) if f["question_id"] == question_id
                ]

    # ── Resolve ────────────────────────────────────────────────────────

    def resolve_flag(self, flag_id: str, resolution: str = "fixed") -> dict:
        """Mark a flag as resolved. Returns status dict."""
        if self._use_firestore():
            return self._resolve_flag_firestore(flag_id, resolution)
        return self._resolve_flag_memory(flag_id, resolution)

    def _resolve_flag_firestore(self, flag_id: str, resolution: str) -> dict:
        db = _get_db()
        if not db:
            return self._resolve_flag_memory(flag_id, resolution)
        try:
            # Query by flag_id field since doc IDs are dedup hashes.
            docs = (
                db.collection(_COLLECTION)
                .where("flag_id", "==", flag_id)
                .limit(1)
                .stream()
            )
            for doc in docs:
                doc.reference.update({"resolved": True, "resolution": resolution})
                return {"status": "resolved", "flag_id": flag_id}
            return {"status": "not_found", "flag_id": flag_id}
        except Exception as e:
            logger.error("FlagStore: Firestore resolve failed: %s", e)
            return self._resolve_flag_memory(flag_id, resolution)

    def _resolve_flag_memory(self, flag_id: str, resolution: str) -> dict:
        with self._lock:
            for f in self._flags:
                if f["flag_id"] == flag_id:
                    f["resolved"] = True
                    f["resolution"] = resolution
                    # Attempt write-through to Firestore
                    self._try_write_through(
                        f["question_id"], f["student_id"], f["flag_type"], f
                    )
                    return {"status": "resolved", "flag_id": flag_id}
        return {"status": "not_found", "flag_id": flag_id}

    # ── Summaries ──────────────────────────────────────────────────────

    def summary(self) -> dict:
        """Aggregate flag counts by type and by question."""
        flags_snapshot = self._get_active_flags()

        by_type: dict[str, int] = defaultdict(int)
        by_question: dict[str, list[dict]] = defaultdict(list)

        for f in flags_snapshot:
            if f.get("resolved"):
                continue
            by_type[f["flag_type"]] += 1
            by_question[f["question_id"]].append(f)

        # Sort questions by flag count descending
        question_summary = sorted(
            [
                {
                    "question_id": qid,
                    "total_flags": len(flags),
                    "flag_types": dict(defaultdict(int, **{
                        ft: sum(1 for f in flags if f["flag_type"] == ft)
                        for ft in set(f["flag_type"] for f in flags)
                    })),
                    "latest_flag": max(f["created_at"] for f in flags),
                }
                for qid, flags in by_question.items()
            ],
            key=lambda x: x["total_flags"],
            reverse=True,
        )

        return {
            "total_flags": sum(1 for f in flags_snapshot if not f.get("resolved")),
            "by_type": dict(by_type),
            "flagged_questions": question_summary,
        }

    def analysis(self) -> dict:
        """AI-ready analysis: groups flags by question with full details.

        Identifies the most-flagged questions and provides structured data
        suitable for automated quality review pipelines.
        """
        flags_snapshot = self._get_active_flags()

        by_question: dict[str, list[dict]] = defaultdict(list)
        for f in flags_snapshot:
            if f.get("resolved"):
                continue
            by_question[f["question_id"]].append(f)

        questions = []
        for qid, flags in by_question.items():
            type_counts: dict[str, int] = defaultdict(int)
            comments = []
            student_ids = set()
            for f in flags:
                type_counts[f["flag_type"]] += 1
                if f.get("comment"):
                    comments.append(f["comment"])
                student_ids.add(f["student_id"])

            # Determine dominant issue
            dominant_type = max(type_counts, key=type_counts.get) if type_counts else None

            questions.append({
                "question_id": qid,
                "total_flags": len(flags),
                "unique_students": len(student_ids),
                "dominant_issue": dominant_type,
                "flag_type_counts": dict(type_counts),
                "comments": comments,
                "first_flagged": min(f["created_at"] for f in flags),
                "last_flagged": max(f["created_at"] for f in flags),
                "priority": "high" if len(flags) >= 5 else "medium" if len(flags) >= 2 else "low",
            })

        # Sort by total flags descending
        questions.sort(key=lambda x: x["total_flags"], reverse=True)

        return {
            "total_flags": sum(1 for f in flags_snapshot if not f.get("resolved")),
            "total_flagged_questions": len(questions),
            "high_priority_count": sum(1 for q in questions if q["priority"] == "high"),
            "questions": questions,
        }

    # ── Internal: fetch all flags (batch read) ─────────────────────────

    def _get_active_flags(self) -> list[dict]:
        """Fetch all flags for summary/analysis. Uses Firestore batch read."""
        if self._use_firestore():
            db = _get_db()
            if db:
                try:
                    docs = db.collection(_COLLECTION).stream()
                    return [doc.to_dict() for doc in docs]
                except Exception as e:
                    logger.error("FlagStore: Firestore batch read failed: %s", e)
        # Fallback
        with self._lock:
            return list(self._flags)


# Singleton instance
flag_store = FlagStore()
