"""
Response Logger — Persistent item-level response data for IRT calibration.

Logs every student response to Firestore for later analysis:
  - Which question was answered
  - Whether correct
  - Response time
  - Student's theta at time of response
  - Question's current IRT params

This data enables:
  1. Empirical IRT parameter calibration (replacing algorithmic estimates)
  2. Item fit analysis (which questions don't behave as expected)
  3. DIF analysis (do questions work differently across subgroups)
  4. Content quality metrics (which questions are too easy/hard/guessable)

Firestore path: response_logs/{auto_id}
Batch collection: response_log_batches/{user_id}_{date}

The calibration script reads this data and recalculates IRT params.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kiwimath.response_logger")


class ResponseLogger:
    """Logs item-level response data to Firestore."""

    def __init__(self):
        self._db = None
        self._firestore_available = False
        self._buffer: List[Dict[str, Any]] = []  # In-memory buffer
        self._buffer_limit = 50  # Flush every N responses
        self._init_firestore()

    def _init_firestore(self):
        try:
            import firebase_admin
            from firebase_admin import firestore as fs

            if not firebase_admin._apps:
                firebase_admin.initialize_app()
            self._db = fs.client()
            self._firestore_available = True
            logger.info("Response logger connected to Firestore")
        except Exception as e:
            logger.warning(f"Response logger: Firestore unavailable, buffering in memory: {e}")
            self._firestore_available = False

    def log_response(
        self,
        user_id: str,
        question_id: str,
        correct: bool,
        response_time_ms: int,
        user_theta: float,
        skill_id: str = "",
        question_difficulty: int = 0,
        question_irt_a: float = 1.0,
        question_irt_b: float = 0.0,
        question_irt_c: float = 0.25,
        session_id: str = "",
        grade: int = 0,
    ) -> None:
        """Log a single response for IRT calibration.

        This is called after every question answer. The data is buffered
        and flushed in batches to Firestore for efficiency.
        """
        record = {
            "user_id": user_id,
            "question_id": question_id,
            "correct": correct,
            "response_time_ms": response_time_ms,
            "user_theta": round(user_theta, 4),
            "skill_id": skill_id,
            "difficulty_score": question_difficulty,
            "irt_a": round(question_irt_a, 3),
            "irt_b": round(question_irt_b, 3),
            "irt_c": round(question_irt_c, 3),
            "session_id": session_id,
            "grade": grade,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "epoch_ms": int(time.time() * 1000),
        }

        self._buffer.append(record)

        if len(self._buffer) >= self._buffer_limit:
            self._flush()

    def _flush(self) -> None:
        """Write buffered responses to Firestore."""
        if not self._buffer:
            return

        if self._firestore_available and self._db:
            try:
                batch = self._db.batch()
                collection = self._db.collection("response_logs")

                for record in self._buffer:
                    doc_ref = collection.document()
                    batch.set(doc_ref, record)

                batch.commit()
                logger.info(f"Flushed {len(self._buffer)} responses to Firestore")
                self._buffer.clear()
            except Exception as e:
                logger.warning(f"Firestore flush failed, keeping buffer: {e}")
        else:
            # Keep in memory — will be lost on restart but prevents crashes
            if len(self._buffer) > 10000:
                # Prevent unbounded growth
                self._buffer = self._buffer[-5000:]

    def flush(self) -> None:
        """Public flush — call at session completion."""
        self._flush()

    def get_item_responses(self, question_id: str, limit: int = 1000) -> List[Dict]:
        """Get all responses for a specific question (for calibration)."""
        if not self._firestore_available or not self._db:
            return [r for r in self._buffer if r["question_id"] == question_id]

        try:
            docs = (
                self._db.collection("response_logs")
                .where("question_id", "==", question_id)
                .order_by("epoch_ms")
                .limit(limit)
                .get()
            )
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.warning(f"Failed to query responses: {e}")
            return []

    def get_response_count(self) -> int:
        """Get total responses logged (for monitoring)."""
        if not self._firestore_available or not self._db:
            return len(self._buffer)

        try:
            # Firestore doesn't have a cheap count operation, use aggregation
            from google.cloud.firestore_v1.aggregation import AggregationQuery
            query = self._db.collection("response_logs")
            agg = AggregationQuery(query)
            agg.count(alias="total")
            results = agg.get()
            for r in results:
                return r[0].value
        except Exception:
            return len(self._buffer)

    def get_daily_stats(self, date_str: str = "") -> Dict:
        """Get aggregated stats for a specific date."""
        if not date_str:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        responses = []
        if self._firestore_available and self._db:
            try:
                docs = (
                    self._db.collection("response_logs")
                    .where("timestamp", ">=", f"{date_str}T00:00:00")
                    .where("timestamp", "<", f"{date_str}T23:59:59")
                    .get()
                )
                responses = [doc.to_dict() for doc in docs]
            except Exception:
                responses = [r for r in self._buffer if r.get("timestamp", "").startswith(date_str)]
        else:
            responses = [r for r in self._buffer if r.get("timestamp", "").startswith(date_str)]

        if not responses:
            return {"date": date_str, "total": 0, "accuracy": 0, "unique_users": 0}

        correct = sum(1 for r in responses if r["correct"])
        users = set(r["user_id"] for r in responses)

        return {
            "date": date_str,
            "total": len(responses),
            "accuracy": round(correct / len(responses), 3),
            "unique_users": len(users),
            "avg_response_time_ms": round(sum(r["response_time_ms"] for r in responses) / len(responses)),
        }


# Singleton
response_logger = ResponseLogger()
