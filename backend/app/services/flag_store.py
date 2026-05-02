"""
In-memory flag store for question flagging system.

Stores student/parent flags on problematic questions for quality review.
Will be replaced with a persistent store (Firestore) once validated.
"""

import threading
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


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


class FlagStore:
    """Thread-safe in-memory store for question flags."""

    def __init__(self):
        self._flags: list[dict] = []
        self._lock = threading.Lock()

    # ── Write ──────────────────────────────────────────────────────

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
        with self._lock:
            # Deduplicate: check for existing flag with same key triple
            for existing in self._flags:
                if (
                    existing["question_id"] == question_id
                    and existing["student_id"] == student_id
                    and existing["flag_type"] == flag_type.value
                ):
                    existing["comment"] = comment
                    existing["created_at"] = now
                    if session_id is not None:
                        existing["session_id"] = session_id
                    return existing

            flag = {
                "flag_id": uuid.uuid4().hex[:12],
                "question_id": question_id,
                "student_id": student_id,
                "flag_type": flag_type.value,
                "comment": comment,
                "session_id": session_id,
                "created_at": now,
            }
            self._flags.append(flag)
            return flag

    # ── Read ───────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        """Return all flags, newest first."""
        with self._lock:
            return list(reversed(self._flags))

    def get_by_question(self, question_id: str) -> list[dict]:
        """Return all flags for a specific question, newest first."""
        with self._lock:
            return [
                f for f in reversed(self._flags) if f["question_id"] == question_id
            ]

    # ── Summaries ──────────────────────────────────────────────────

    def summary(self) -> dict:
        """Aggregate flag counts by type and by question."""
        with self._lock:
            flags_snapshot = list(self._flags)

        by_type: dict[str, int] = defaultdict(int)
        by_question: dict[str, list[dict]] = defaultdict(list)

        for f in flags_snapshot:
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
            "total_flags": len(flags_snapshot),
            "by_type": dict(by_type),
            "flagged_questions": question_summary,
        }

    def analysis(self) -> dict:
        """AI-ready analysis: groups flags by question with full details.

        Identifies the most-flagged questions and provides structured data
        suitable for automated quality review pipelines.
        """
        with self._lock:
            flags_snapshot = list(self._flags)

        by_question: dict[str, list[dict]] = defaultdict(list)
        for f in flags_snapshot:
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
            "total_flags": len(flags_snapshot),
            "total_flagged_questions": len(questions),
            "high_priority_count": sum(1 for q in questions if q["priority"] == "high"),
            "questions": questions,
        }


# Singleton instance
flag_store = FlagStore()
