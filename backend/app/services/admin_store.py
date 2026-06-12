"""
Admin review state store — tracks review status, flags, and auto-fix changelog.

Stores review state in-memory with persistence to admin_review_log.json.
"""

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kiwimath.admin_store")

_LOG_FILE = Path(__file__).resolve().parent.parent.parent / "admin_review_log.json"


def _get_admin_emails() -> List[str]:
    """Get admin emails from Firestore, falling back to env var."""
    try:
        from app.services.firestore_service import _get_db
        db = _get_db()
        if db:
            doc = db.collection("admin_config").document("settings").get()
            if doc.exists:
                emails = doc.to_dict().get("admin_emails", [])
                if emails:
                    return [e.strip().lower() for e in emails]
    except Exception as e:
        logger.debug(f"Firestore admin_config read failed: {e}")

    env_emails = os.environ.get("KIWIMATH_ADMIN_EMAILS", "anand.prakash@vedantu.com")
    return [e.strip().lower() for e in env_emails.split(",") if e.strip()]


def is_admin(email: str) -> bool:
    return email.strip().lower() in _get_admin_emails()


class AdminReviewStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._reviews: Dict[str, Dict[str, Any]] = {}  # question_id -> review state
        self._changelog: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        """Load from Firestore first; fall back to JSON file."""
        loaded_from_firestore = False
        try:
            from app.services.firestore_service import _get_db
            db = _get_db()
            if db:
                # Load reviews
                review_docs = db.collection("admin_reviews").stream()
                for doc in review_docs:
                    self._reviews[doc.id] = doc.to_dict()
                # Load changelog
                changelog_docs = (
                    db.collection("admin_changelog")
                    .order_by("timestamp")
                    .stream()
                )
                for doc in changelog_docs:
                    self._changelog.append(doc.to_dict())
                if self._reviews or self._changelog:
                    loaded_from_firestore = True
                    logger.info(
                        f"Loaded {len(self._reviews)} reviews, "
                        f"{len(self._changelog)} changelog entries from Firestore"
                    )
        except Exception as e:
            logger.warning(f"Failed to load admin data from Firestore: {e}")

        if not loaded_from_firestore and _LOG_FILE.exists():
            try:
                data = json.loads(_LOG_FILE.read_text())
                self._reviews = data.get("reviews", {})
                self._changelog = data.get("changelog", [])
                logger.info(
                    f"Loaded {len(self._reviews)} reviews, "
                    f"{len(self._changelog)} changelog entries from JSON file"
                )
            except Exception as e:
                logger.warning(f"Failed to load admin_review_log.json: {e}")

    def _persist(self):
        """Persist to JSON file as fallback, always attempted."""
        try:
            _LOG_FILE.write_text(json.dumps({
                "reviews": self._reviews,
                "changelog": self._changelog,
            }, indent=2, default=str))
        except Exception as e:
            logger.warning(f"Failed to persist admin_review_log.json: {e}")

    def _persist_review_to_firestore(self, question_id: str, review_data: Dict[str, Any]) -> None:
        """Write a single review to Firestore."""
        try:
            from app.services.firestore_service import _get_db
            db = _get_db()
            if db:
                db.collection("admin_reviews").document(question_id).set(
                    review_data, merge=True
                )
        except Exception as e:
            logger.warning(f"Failed to persist review to Firestore for {question_id}: {e}")

    def _persist_changelog_to_firestore(self, entry: Dict[str, Any]) -> None:
        """Append a single changelog entry to Firestore."""
        try:
            from app.services.firestore_service import _get_db
            db = _get_db()
            if db:
                db.collection("admin_changelog").document().set(entry)
        except Exception as e:
            logger.warning(f"Failed to persist changelog entry to Firestore: {e}")

    def get_review(self, question_id: str) -> Optional[Dict[str, Any]]:
        return self._reviews.get(question_id)

    def get_status(self, question_id: str) -> str:
        r = self._reviews.get(question_id)
        return r["status"] if r else "pending"

    def approve(self, question_id: str, reviewer_email: str) -> Dict[str, Any]:
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            self._reviews[question_id] = {
                "status": "approved",
                "reviewer": reviewer_email,
                "timestamp": now,
                "flags": self._reviews.get(question_id, {}).get("flags", []),
            }
            self._persist()
            self._persist_review_to_firestore(question_id, self._reviews[question_id])
            return self._reviews[question_id]

    def flag(self, question_id: str, reviewer_email: str, flag_type: str, comment: str) -> Dict[str, Any]:
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            existing = self._reviews.get(question_id, {"flags": []})
            flag_entry = {
                "flag_type": flag_type,
                "comment": comment,
                "reviewer": reviewer_email,
                "timestamp": now,
            }
            existing.setdefault("flags", []).append(flag_entry)
            existing["status"] = "flagged"
            existing["reviewer"] = reviewer_email
            existing["timestamp"] = now
            self._reviews[question_id] = existing
            self._persist()
            self._persist_review_to_firestore(question_id, existing)
            return existing

    def log_change(self, question_id: str, reviewer: str, change_type: str,
                   field: str, before: Any, after: Any):
        with self._lock:
            entry = {
                "question_id": question_id,
                "reviewer": reviewer,
                "change_type": change_type,
                "field": field,
                "before": before,
                "after": after,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._changelog.append(entry)
            self._persist()
            self._persist_changelog_to_firestore(entry)

    def get_changelog(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        return list(reversed(self._changelog))[offset:offset + limit]

    def stats(self) -> Dict[str, Any]:
        total = len(self._reviews)
        approved = sum(1 for r in self._reviews.values() if r.get("status") == "approved")
        flagged = sum(1 for r in self._reviews.values() if r.get("status") == "flagged")
        by_flag_type: Dict[str, int] = {}
        for r in self._reviews.values():
            for f in r.get("flags", []):
                ft = f.get("flag_type", "other")
                by_flag_type[ft] = by_flag_type.get(ft, 0) + 1
        return {
            "total_reviewed": total,
            "approved": approved,
            "flagged": flagged,
            "by_flag_type": by_flag_type,
        }

    def all_reviews(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._reviews)


admin_review_store = AdminReviewStore()
