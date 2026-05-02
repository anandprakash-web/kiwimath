"""
Question History Tracker — prevents question repetition on diagnostic retests.

When a student retakes the diagnostic/onboarding test, they should not see
the same questions they saw last time (otherwise they can memorize answers,
defeating the purpose of assessment).

This service tracks which questions each student has seen in diagnostic
contexts and provides an exclusion set for subsequent retests.

Storage
-------
In-memory ``Dict[str, List[Set[str]]]`` mapping
    student_id -> list of per-session seen-question sets (ordered oldest first).

The list-of-sets design supports the safety-valve rule: if >80% of the
available pool is exhausted, we allow questions from 2+ retests ago
(oldest sessions first) while always blocking questions from the most
recent diagnostic.
"""

from __future__ import annotations

import logging
from threading import Lock
from typing import Dict, List, Optional, Set

logger = logging.getLogger("kiwimath.question_history")


class QuestionHistoryTracker:
    """Tracks which diagnostic questions each student has seen.

    Thread-safe via a lock around all mutations.
    """

    def __init__(self) -> None:
        # student_id -> list of sets, each set is one diagnostic session.
        # Ordered oldest-first: index 0 = oldest session.
        self._history: Dict[str, List[Set[str]]] = {}
        # student_id -> current (in-progress) session set
        self._current_session: Dict[str, Set[str]] = {}
        self._lock = Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_diagnostic_session(self, student_id: str) -> None:
        """Call when a student begins a new diagnostic/benchmark session.

        Finalises any in-progress session and opens a fresh one.
        """
        with self._lock:
            self._finalise_current(student_id)
            self._current_session[student_id] = set()
            logger.debug(
                "Started new diagnostic session for student=%s "
                "(prior sessions=%d)",
                student_id,
                len(self._history.get(student_id, [])),
            )

    def record_diagnostic_question(
        self,
        student_id: str,
        question_id: str,
        session_type: str = "diagnostic",
    ) -> None:
        """Record that a student saw a question in a diagnostic context."""
        with self._lock:
            if student_id not in self._current_session:
                # Auto-start a session if none was explicitly started.
                self._current_session[student_id] = set()
            self._current_session[student_id].add(question_id)
            logger.debug(
                "Recorded question %s for student=%s (type=%s)",
                question_id,
                student_id,
                session_type,
            )

    def end_diagnostic_session(self, student_id: str) -> None:
        """Call when a diagnostic session ends. Finalises the current set."""
        with self._lock:
            self._finalise_current(student_id)

    def get_seen_questions(
        self,
        student_id: str,
        session_type: str = "diagnostic",
    ) -> Set[str]:
        """Get all question IDs this student has ever seen in diagnostics."""
        with self._lock:
            result: Set[str] = set()
            for session_set in self._history.get(student_id, []):
                result |= session_set
            # Include current in-progress session.
            current = self._current_session.get(student_id)
            if current:
                result |= current
            return result

    def get_exclusion_set(
        self,
        student_id: str,
        total_available: int = 0,
    ) -> Set[str]:
        """Get the set of question IDs to exclude from the next diagnostic.

        Safety valve: if the exclusion set would exceed 80% of
        ``total_available``, allow questions from the oldest sessions
        (2+ retests ago) while always blocking the most recent session.

        Parameters
        ----------
        student_id:
            The student to look up.
        total_available:
            Total number of questions in the pool. If 0, no safety-valve
            logic is applied (all seen questions are excluded).

        Returns
        -------
        Set of question IDs to exclude.
        """
        with self._lock:
            sessions = list(self._history.get(student_id, []))
            current = self._current_session.get(student_id)

        if not sessions and not current:
            return set()

        # Always exclude the most recent completed session.
        most_recent: Set[str] = set()
        if sessions:
            most_recent = set(sessions[-1])

        # Also exclude the current in-progress session.
        if current:
            most_recent = most_recent | current

        # Full exclusion set = all sessions.
        full_exclusion: Set[str] = set()
        for s in sessions:
            full_exclusion |= s
        if current:
            full_exclusion |= current

        # Safety valve: if we'd exclude >80% of the pool, relax older
        # sessions while keeping the most recent blocked.
        if total_available > 0 and len(full_exclusion) > 0:
            ratio = len(full_exclusion) / total_available
            if ratio > 0.80:
                logger.warning(
                    "Question exhaustion for student=%s: %d/%d (%.0f%%) "
                    "excluded. Relaxing oldest sessions.",
                    student_id,
                    len(full_exclusion),
                    total_available,
                    ratio * 100,
                )
                # Relax from oldest sessions first, keep most recent blocked.
                relaxed = set(most_recent)  # always keep most recent
                # Add sessions from newest to oldest (excluding the most recent
                # which is already included), stopping when we hit 80%.
                older_sessions = sessions[:-1] if len(sessions) > 1 else []
                for s in reversed(older_sessions):
                    candidate = relaxed | s
                    if total_available > 0 and len(candidate) / total_available > 0.80:
                        # Adding this session would exceed 80%, skip it
                        # (i.e. allow its questions to be reused).
                        logger.info(
                            "Allowing reuse of %d questions from an older "
                            "diagnostic session for student=%s",
                            len(s),
                            student_id,
                        )
                        continue
                    relaxed = candidate

                return relaxed

        return full_exclusion

    def get_retest_count(self, student_id: str) -> int:
        """Return how many completed diagnostic sessions this student has."""
        with self._lock:
            return len(self._history.get(student_id, []))

    def is_retest(self, student_id: str) -> bool:
        """Return True if the student has completed at least one diagnostic."""
        return self.get_retest_count(student_id) > 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _finalise_current(self, student_id: str) -> None:
        """Move current session to history (caller holds the lock)."""
        current = self._current_session.pop(student_id, None)
        if current:
            if student_id not in self._history:
                self._history[student_id] = []
            self._history[student_id].append(current)
            logger.debug(
                "Finalised diagnostic session for student=%s "
                "(%d questions in session, %d total sessions)",
                student_id,
                len(current),
                len(self._history[student_id]),
            )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

question_history = QuestionHistoryTracker()
