"""
Mistake Tracker & Spaced Revision Scheduler.

Tracks every wrong answer by student, groups mistakes by topic and question
pattern (concept cluster / tags), and schedules spaced revision using an
expanding interval schedule: 1 day, 3 days, 7 days, 14 days, 30 days.

When a student answers a revision question correctly the interval advances;
when wrong it resets to the beginning of the schedule.

Usage:
    from app.services.mistake_tracker import mistake_tracker

    # Record a mistake (called automatically from check_answer)
    mistake_tracker.record_mistake(
        student_id="u123", question_id="T1-042", topic_id="arithmetic",
        concept_cluster="subtraction_with_borrowing",
        tags=["subtraction", "borrowing", "place_value"],
    )

    # Get revision queue for a student
    queue = mistake_tracker.get_revision_queue("u123", max_items=5)
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("kiwimath.mistake_tracker")

# ---------------------------------------------------------------------------
# Spaced Revision Schedule (in seconds for precise scheduling)
# ---------------------------------------------------------------------------

# Review intervals in days — advances on correct, resets on wrong.
REVISION_INTERVALS_DAYS = [1, 3, 7, 14, 30]

# Mastery status labels
MASTERY_NOT_STARTED = "not_started"
MASTERY_REVIEWING = "reviewing"
MASTERY_ALMOST = "almost_mastered"
MASTERY_MASTERED = "mastered"


def _mastery_status(interval_index: int, times_reviewed: int) -> str:
    """Derive mastery status from the current interval index."""
    if times_reviewed == 0:
        return MASTERY_NOT_STARTED
    if interval_index >= len(REVISION_INTERVALS_DAYS):
        return MASTERY_MASTERED
    if interval_index >= 3:  # past the 14-day interval
        return MASTERY_ALMOST
    return MASTERY_REVIEWING


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class MistakeRecord:
    """A single mistake event."""
    student_id: str
    question_id: str
    topic_id: str
    concept_cluster: str          # e.g. "subtraction_with_borrowing"
    tags: List[str]               # e.g. ["subtraction", "borrowing"]
    timestamp: float              # Unix timestamp of the mistake


@dataclass
class RevisionItem:
    """Tracks revision state for a specific mistake pattern (concept cluster)."""
    student_id: str
    concept_cluster: str
    topic_id: str
    tags: List[str]
    # All question IDs where the student made mistakes in this pattern
    mistake_question_ids: List[str] = field(default_factory=list)
    # Timestamps of each mistake
    mistake_timestamps: List[float] = field(default_factory=list)
    # Revision tracking
    interval_index: int = 0       # Index into REVISION_INTERVALS_DAYS
    times_reviewed: int = 0
    times_correct: int = 0
    times_wrong: int = 0
    last_review_time: float = 0.0  # Unix timestamp of last review
    created_at: float = 0.0        # When first mistake was recorded

    @property
    def mistake_count(self) -> int:
        return len(self.mistake_question_ids)

    @property
    def last_mistake_time(self) -> float:
        return max(self.mistake_timestamps) if self.mistake_timestamps else self.created_at

    @property
    def next_review_time(self) -> float:
        """Unix timestamp when the next review is due."""
        if self.interval_index >= len(REVISION_INTERVALS_DAYS):
            # Mastered — no more reviews needed
            return float("inf")
        base_time = self.last_review_time if self.last_review_time > 0 else self.last_mistake_time
        interval_seconds = REVISION_INTERVALS_DAYS[self.interval_index] * 86400
        return base_time + interval_seconds

    @property
    def is_due(self) -> bool:
        """Whether this item is due for revision now."""
        if self.interval_index >= len(REVISION_INTERVALS_DAYS):
            return False  # Mastered
        return time.time() >= self.next_review_time

    @property
    def mastery_status(self) -> str:
        return _mastery_status(self.interval_index, self.times_reviewed)

    @property
    def priority_score(self) -> float:
        """Higher = more urgent. Considers recency, frequency, and overdue-ness."""
        now = time.time()
        # How overdue (in hours); 0 if not yet due
        overdue_hours = max(0, (now - self.next_review_time) / 3600)
        # More mistakes = higher base priority
        frequency_weight = min(5.0, self.mistake_count)
        # Recency boost: recent mistakes get higher priority
        recency_hours = (now - self.last_mistake_time) / 3600
        recency_weight = max(0.5, 5.0 - (recency_hours / 24))  # decays over days
        return overdue_hours * 2.0 + frequency_weight + recency_weight

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for API responses."""
        now = time.time()
        next_ts = self.next_review_time
        return {
            "concept_cluster": self.concept_cluster,
            "topic_id": self.topic_id,
            "tags": self.tags,
            "mistake_count": self.mistake_count,
            "mistake_question_ids": self.mistake_question_ids,
            "last_mistake_date": datetime.fromtimestamp(
                self.last_mistake_time, tz=timezone.utc
            ).isoformat(),
            "times_reviewed": self.times_reviewed,
            "times_correct": self.times_correct,
            "times_wrong": self.times_wrong,
            "next_review_date": (
                datetime.fromtimestamp(next_ts, tz=timezone.utc).isoformat()
                if next_ts < float("inf")
                else None
            ),
            "is_due": self.is_due,
            "mastery_status": self.mastery_status,
            "current_interval_days": (
                REVISION_INTERVALS_DAYS[self.interval_index]
                if self.interval_index < len(REVISION_INTERVALS_DAYS)
                else None
            ),
        }


# ---------------------------------------------------------------------------
# Mistake Tracker Service
# ---------------------------------------------------------------------------

class MistakeTracker:
    """Tracks student mistakes and schedules spaced revision."""

    def __init__(self):
        # student_id -> {concept_cluster -> RevisionItem}
        self._items: Dict[str, Dict[str, RevisionItem]] = {}
        # student_id -> [MistakeRecord] (raw log of all mistakes)
        self._mistake_log: Dict[str, List[MistakeRecord]] = {}

    # ------------------------------------------------------------------
    # Recording mistakes
    # ------------------------------------------------------------------

    def record_mistake(
        self,
        student_id: str,
        question_id: str,
        topic_id: str,
        concept_cluster: str,
        tags: Optional[List[str]] = None,
        timestamp: Optional[float] = None,
    ) -> RevisionItem:
        """Record a wrong answer and create/update a revision item.

        Args:
            student_id: The student who made the mistake.
            question_id: The question that was answered incorrectly.
            topic_id: The topic the question belongs to.
            concept_cluster: The concept pattern (e.g. "subtraction_with_borrowing").
            tags: Question tags for grouping patterns.
            timestamp: Override timestamp (defaults to now).

        Returns:
            The updated RevisionItem for this concept cluster.
        """
        now = timestamp or time.time()
        tags = tags or []

        # Use topic_id as fallback cluster if none provided
        effective_cluster = concept_cluster or f"{topic_id}/_default"

        # Store raw mistake record
        record = MistakeRecord(
            student_id=student_id,
            question_id=question_id,
            topic_id=topic_id,
            concept_cluster=effective_cluster,
            tags=tags,
            timestamp=now,
        )
        if student_id not in self._mistake_log:
            self._mistake_log[student_id] = []
        self._mistake_log[student_id].append(record)

        # Create or update revision item
        if student_id not in self._items:
            self._items[student_id] = {}

        student_items = self._items[student_id]
        if effective_cluster not in student_items:
            student_items[effective_cluster] = RevisionItem(
                student_id=student_id,
                concept_cluster=effective_cluster,
                topic_id=topic_id,
                tags=list(tags),
                created_at=now,
            )

        item = student_items[effective_cluster]
        # Add this question if not already tracked
        if question_id not in item.mistake_question_ids:
            item.mistake_question_ids.append(question_id)
        item.mistake_timestamps.append(now)
        # Merge in any new tags
        for tag in tags:
            if tag not in item.tags:
                item.tags.append(tag)

        logger.debug(
            "Recorded mistake for %s on cluster %s (q=%s, total=%d)",
            student_id, effective_cluster, question_id, item.mistake_count,
        )
        return item

    # ------------------------------------------------------------------
    # Recording revision results
    # ------------------------------------------------------------------

    def record_revision_result(
        self,
        student_id: str,
        concept_cluster: str,
        correct: bool,
        timestamp: Optional[float] = None,
    ) -> Optional[RevisionItem]:
        """Record the result of a revision question.

        If correct, advance the interval. If wrong, reset to interval 0.

        Returns:
            The updated RevisionItem, or None if not found.
        """
        now = timestamp or time.time()

        if student_id not in self._items:
            return None
        item = self._items[student_id].get(concept_cluster)
        if item is None:
            return None

        item.times_reviewed += 1
        item.last_review_time = now

        if correct:
            item.times_correct += 1
            # Advance to the next interval
            item.interval_index = min(
                item.interval_index + 1,
                len(REVISION_INTERVALS_DAYS),  # can exceed to indicate mastered
            )
        else:
            item.times_wrong += 1
            # Reset interval to beginning (but keep history)
            item.interval_index = 0

        logger.debug(
            "Revision result for %s on %s: %s (interval_idx=%d, status=%s)",
            student_id, concept_cluster, "correct" if correct else "wrong",
            item.interval_index, item.mastery_status,
        )
        return item

    # ------------------------------------------------------------------
    # Querying revision queue
    # ------------------------------------------------------------------

    def get_revision_queue(
        self,
        student_id: str,
        max_items: int = 10,
        include_not_yet_due: bool = False,
    ) -> List[RevisionItem]:
        """Get items due for revision, sorted by priority (most urgent first).

        Args:
            student_id: The student to query.
            max_items: Maximum items to return.
            include_not_yet_due: If True, also include items not yet due
                (useful for previewing upcoming reviews).

        Returns:
            List of RevisionItems sorted by priority.
        """
        if student_id not in self._items:
            return []

        items = list(self._items[student_id].values())

        # Filter out mastered items
        items = [i for i in items if i.mastery_status != MASTERY_MASTERED]

        if not include_not_yet_due:
            items = [i for i in items if i.is_due]

        # Sort by priority (highest first)
        items.sort(key=lambda i: i.priority_score, reverse=True)
        return items[:max_items]

    # ------------------------------------------------------------------
    # Querying mistake patterns
    # ------------------------------------------------------------------

    def get_mistake_patterns(
        self,
        student_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get the most frequent/recent mistake patterns for a student.

        Returns a list of pattern summaries sorted by frequency then recency.
        """
        if student_id not in self._items:
            return []

        items = list(self._items[student_id].values())
        # Sort by mistake count (descending), then recency (descending)
        items.sort(
            key=lambda i: (i.mistake_count, i.last_mistake_time),
            reverse=True,
        )
        return [item.to_dict() for item in items[:limit]]

    def get_all_items(self, student_id: str) -> List[RevisionItem]:
        """Get all revision items for a student (all statuses)."""
        if student_id not in self._items:
            return []
        return list(self._items[student_id].values())

    def get_revision_stats(self, student_id: str) -> Dict[str, Any]:
        """Summary statistics for a student's revision state."""
        items = self.get_all_items(student_id)
        if not items:
            return {
                "total_patterns": 0,
                "due_now": 0,
                "reviewing": 0,
                "almost_mastered": 0,
                "mastered": 0,
                "total_mistakes": 0,
            }

        return {
            "total_patterns": len(items),
            "due_now": sum(1 for i in items if i.is_due),
            "reviewing": sum(1 for i in items if i.mastery_status == MASTERY_REVIEWING),
            "almost_mastered": sum(1 for i in items if i.mastery_status == MASTERY_ALMOST),
            "mastered": sum(1 for i in items if i.mastery_status == MASTERY_MASTERED),
            "total_mistakes": sum(i.mistake_count for i in items),
        }

    def get_revision_question_ids(
        self,
        student_id: str,
        max_items: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get question IDs suitable for revision, drawn from actual mistakes.

        Returns a list of dicts with question_id, topic_id, concept_cluster,
        and priority_reason="revision" for mixing into session plans.
        """
        queue = self.get_revision_queue(student_id, max_items=max_items)
        results: List[Dict[str, Any]] = []

        for item in queue:
            if not item.mistake_question_ids:
                continue
            # Pick the most recent mistake question for review
            qid = item.mistake_question_ids[-1]
            results.append({
                "question_id": qid,
                "topic_id": item.topic_id,
                "concept_cluster": item.concept_cluster,
                "priority_reason": "revision",
                "mastery_status": item.mastery_status,
            })
            if len(results) >= max_items:
                break

        return results


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

mistake_tracker = MistakeTracker()
