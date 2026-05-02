"""
Kiwimath Adaptive Engine — decides what question to serve next.

This is the core adaptive loop for the Grade 1 math app.  The engine is
stateless between requests: ``SessionState`` is passed in and out, stored in
Flutter app state or Firestore.  This keeps the server thin and lets the client
drive the session loop with minimal latency.

THE THREE LOOPS
===============
1. **Within-question** — wrong answer on parent -> diagnose misconception ->
   step-down scaffold -> re-attempt parent with hint.
2. **Within-session** — concept-level question selection based on mastery
   state, difficulty banding, and streak signals.
3. **Across-sessions** — spaced repetition + revisit scheduling
   (Cloud Functions, not in this module).

This module handles loops 1 and 2.

DESIGN PRINCIPLES (from design cofounder)
==========================================
- Step-downs are the moat: every wrong answer diagnoses a specific
  misconception and routes to scaffolded sub-questions.
- No BKT in v1: simple Elo + strategy signals.
- Session length: 8-12 *parent* questions for K-2 attention span.
  Step-downs don't count (they're remediation, not new content).
- Never dead-end: every wrong answer leads somewhere helpful.
- Monotonic shown_score: internal Elo moves both ways, shown score never drops.
- Warm, not clinical: feedback is encouraging, never punitive.

FIRESTORE INTEGRATION
=====================
The engine reads mastery snapshots on session start and emits
``AttemptResult`` objects.  The caller is responsible for persisting mastery
changes and firing ``AttemptRecorded`` / ``MasteryUpdated`` events.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.models.question import (
    ConceptGraph,
    ConceptNode,
    EdgeType,
    MasteryLevel,
    Question,
    StepDownQuestion,
    mastery_label,
)
from app.services.content_store import ContentStore
from app.services.renderer import RenderedQuestion, render_question

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_PARENT_QUESTIONS: int = 6
"""Hard ceiling on parent questions per session (step-downs excluded).
Shorter sessions (5-7 questions) have better completion rates for young children."""

MIN_PARENT_QUESTIONS: int = 4
"""Minimum parents before a streak-exit is allowed."""

MASTERY_STREAK_EXIT: int = 3
"""Correct streak that, combined with proficient+ mastery, ends the session."""

ADVANCE_STREAK_THRESHOLD: int = 3
"""Correct streak that triggers a 'consider advancing' suggestion."""

MAX_STEP_DOWNS_PER_CHAIN: int = 3
"""Hard cap on step-down depth to prevent infinite scaffold chains."""

MAX_ATTEMPTS_PER_QUESTION: int = 3
"""Parent attempts before moving on gently (supports 3-level scaffolding:
hint -> visual/misconception hint -> step-down)."""

CONCEPT_SWITCH_AFTER_WRONG: int = 3
"""Consecutive wrong answers that trigger a concept switch."""

_MASTERY_RANK: Dict[str, int] = {
    "new": 0,
    "familiar": 1,
    "proficient": 2,
    "mastered": 3,
}
"""Mastery label ordering for comparisons."""


# ---------------------------------------------------------------------------
# Data classes — engine state
# ---------------------------------------------------------------------------


@dataclass
class MasterySnapshot:
    """Lightweight view of a user's mastery for one concept.

    Populated from Firestore on session start and updated locally as the
    session progresses.  The caller is responsible for persisting changes
    back to Firestore.
    """

    internal_score: float = 0.0   # 0.0 – 1.0, bidirectional Elo
    shown_score: int = 0          # 0 – 100, kid-facing, monotonic (never drops)
    mastery_label: str = "new"    # new / familiar / proficient / mastered
    total_attempts: int = 0
    streak_current: int = 0

    # -- helpers -----------------------------------------------------------

    @property
    def rank(self) -> int:
        """Numeric rank of the current mastery label (0–3)."""
        return _MASTERY_RANK.get(self.mastery_label, 0)

    def at_least(self, label: str) -> bool:
        """Return True if mastery is at or above *label*."""
        return self.rank >= _MASTERY_RANK.get(label, 0)

    def record_attempt(self, is_correct: bool, question_weight: float = 1.0) -> None:
        """Update mastery after an attempt.

        Elo-inspired: correct answers increase ``internal_score``, wrong
        answers decrease it.  ``shown_score`` only goes up (monotonic).

        Parameters
        ----------
        is_correct:
            Whether the student answered correctly.
        question_weight:
            Weight from the question's ``mastery_config`` (default 1.0).
        """
        self.total_attempts += 1

        if is_correct:
            self.streak_current += 1
            headroom = 1.0 - self.internal_score
            gain = 0.15 * question_weight * headroom
            # Streak bonus: consecutive correct answers compound slightly
            if self.streak_current >= 3:
                gain *= 1.2
            self.internal_score = min(1.0, self.internal_score + gain)
        else:
            self.streak_current = 0
            drop = 0.10 * question_weight * self.internal_score
            self.internal_score = max(0.0, self.internal_score - drop)

        # Monotonic shown_score: NEVER drops
        new_shown = int(self.internal_score * 100)
        self.shown_score = max(self.shown_score, new_shown)

        # Recompute label from shown_score
        if self.shown_score >= 80:
            self.mastery_label = "mastered"
        elif self.shown_score >= 50:
            self.mastery_label = "proficient"
        elif self.shown_score >= 25:
            self.mastery_label = "familiar"
        else:
            self.mastery_label = "new"


class SessionPhase(str, Enum):
    """Where we are in the within-question adaptive loop."""
    parent = "parent"
    step_down = "step_down"
    retry_parent = "retry_parent"


@dataclass
class SessionState:
    """In-memory state for a single learning session.

    This object is serialisable (all fields are plain types or dataclasses)
    so the Flutter client can stash it in local state or Firestore between
    network round-trips.
    """

    user_id: str
    concept_id: str               # concept the session is practising

    mastery_states: Dict[str, MasterySnapshot] = field(default_factory=dict)
    """concept_id -> MasterySnapshot, seeded from Firestore on start."""

    current_question_id: Optional[str] = None
    current_question_is_step_down: bool = False
    current_phase: SessionPhase = SessionPhase.parent
    current_attempt_number: int = 0
    """How many times the student has attempted the current parent question."""

    current_correct_index: int = -1
    """The correct option index for the currently served question.
    Stored at render time so submit_answer doesn't need to re-render
    (re-rendering shuffles options, changing the correct index)."""

    current_rendered: Optional[RenderedQuestion] = None
    """The rendered question currently on screen. Kept so submit_answer can
    look up wrong-option diagnosis without re-rendering."""

    step_down_queue: List[str] = field(default_factory=list)
    """Ordered step-down IDs still to serve (front = next)."""

    step_down_index: int = 0
    """How deep we are in the current step-down chain."""

    parent_question_for_step_downs: Optional[str] = None
    """The parent question that triggered the current step-down sequence."""

    current_diagnosis: Optional[str] = None
    """Misconception diagnosed on the current parent question."""

    questions_served: List[str] = field(default_factory=list)
    """All question IDs served this session (parents + step-downs)."""

    parent_questions_served: int = 0
    """Count of *parent* questions served (excludes step-downs).
    Used to enforce the per-session cap."""

    correct_streak: int = 0
    total_attempts: int = 0
    wrong_streak: int = 0
    """Consecutive wrong answers (across all question types)."""

    params_context: Dict[str, Any] = field(default_factory=dict)
    """Inherited rendering params (character name, number, etc.) for
    step-down consistency — step-downs inherit the same narrative context
    as the parent question they scaffold."""

    concepts_touched: List[str] = field(default_factory=list)
    """Concepts the student interacted with this session."""

    # -- helpers -----------------------------------------------------------

    def get_mastery(self, concept_id: str) -> MasterySnapshot:
        """Get or create a mastery snapshot for a concept."""
        if concept_id not in self.mastery_states:
            self.mastery_states[concept_id] = MasterySnapshot()
        return self.mastery_states[concept_id]


@dataclass
class AttemptResult:
    """What the engine decided after processing an attempt.

    Returned to the caller so the client can render the next screen, update
    analytics, and (optionally) persist mastery changes.
    """

    next_question_id: Optional[str] = None
    """Question to serve next, or None if the session is done."""

    is_step_down: bool = False
    """Whether the next question is a step-down (scaffolding mode —
    UI shows Kiwi mascot helping)."""

    rendered_question: Optional[RenderedQuestion] = None
    """Pre-rendered next question, ready for the client to display."""

    feedback_message: Optional[str] = None
    """Kid-facing message (shown alongside Kiwi mascot)."""

    misconception_diagnosis: Optional[str] = None
    """Identifier of the diagnosed misconception, for analytics / parent reports."""

    mascot_emotion: str = "neutral"
    """Kiwi's emotional state for the UI animation."""

    session_complete: bool = False
    """True when the session should end."""

    concept_mastered: bool = False
    """True if this attempt pushed mastery to 'mastered'."""

    suggest_next_concept: Optional[str] = None
    """If the concept is sufficiently practised, the next concept to try."""

    mastery_snapshot: Optional[Dict[str, Any]] = None
    """Current mastery state for the concept, for the client to display."""

    session_stats: Optional[Dict[str, Any]] = None
    """Summary stats when the session ends."""

    retry_same_question: bool = False
    """True when the student should re-attempt the same question (multi-level
    scaffolding: hint or visual hint shown, but no step-down yet)."""

    scaffold_level: int = 0
    """Current scaffolding level for this wrong-answer sequence:
    0 = no scaffolding, 1 = text hint, 2 = visual/misconception hint,
    3 = step-down questions."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _difficulty_band(mastery: MasterySnapshot) -> Tuple[int, int]:
    """Map a mastery snapshot to a preferred difficulty range (inclusive).

    Returns ``(low, high)`` where difficulty values are 1–5.

    The bands are intentionally wide so there's always something to serve,
    but the engine prefers the centre of the band when multiple questions
    are available.

    +---------------+------------+
    | Mastery       | Band       |
    +===============+============+
    | new           | 1–2        |
    | familiar      | 2–3        |
    | proficient+   | 3–5        |
    +---------------+------------+

    >>> _difficulty_band(MasterySnapshot(mastery_label="new"))
    (1, 2)
    >>> _difficulty_band(MasterySnapshot(mastery_label="familiar"))
    (2, 3)
    >>> _difficulty_band(MasterySnapshot(mastery_label="proficient"))
    (3, 5)
    >>> _difficulty_band(MasterySnapshot(mastery_label="mastered"))
    (3, 5)
    """
    if mastery.at_least("proficient"):
        return (3, 5)
    if mastery.at_least("familiar"):
        return (2, 3)
    return (1, 2)


def _pick_from_band(
    questions: List[Question],
    low: int,
    high: int,
    exclude_ids: Optional[set] = None,
) -> Optional[Question]:
    """Choose a random question whose difficulty falls in [low, high].

    If no questions match the preferred band, fall back to the full list so
    the session can continue rather than ending prematurely.

    Parameters
    ----------
    questions:
        Pool of candidate questions (already filtered for session-seen).
    low, high:
        Inclusive difficulty range.
    exclude_ids:
        Additional question IDs to exclude (e.g. from prior diagnostics).

    Returns the chosen ``Question`` or ``None`` if the list is empty.
    """
    if not questions:
        return None

    # Apply external exclusion set if provided.
    if exclude_ids:
        questions = [q for q in questions if q.id not in exclude_ids]
        if not questions:
            return None

    in_band = [q for q in questions if low <= getattr(q, "difficulty", 1) <= high]
    pool = in_band if in_band else questions

    chosen = random.choice(pool)
    if not in_band:
        logger.debug(
            "No questions in difficulty band [%d, %d]; fell back to full pool "
            "(chose difficulty %d)",
            low,
            high,
            getattr(chosen, "difficulty", -1),
        )
    return chosen


# ---------------------------------------------------------------------------
# The Engine
# ---------------------------------------------------------------------------


class AdaptiveEngine:
    """Core adaptive engine for Kiwimath.

    Decides *what* question to serve next based on student state.  Holds no
    mutable state itself — all session state lives in :class:`SessionState`,
    which is threaded through every call.  This makes the engine safe for
    concurrent use and trivially testable.

    Typical call sequence::

        engine = AdaptiveEngine(content_store, concept_graph)
        session = engine.start_session(uid, concept_id, mastery_states)

        result = engine.next_question(session)
        # client displays result.rendered_question

        # ... user taps an option ...
        result = engine.submit_answer(session, question_id, option_idx, time_ms)
        # result tells the caller what to do next

    Parameters
    ----------
    content_store:
        Content store with ``get(qid)``, ``parents()``, ``by_topic(topic)``.
    concept_graph:
        Concept graph with typed edges (hard_prereq, soft_prereq, strand_order).
    """

    def __init__(self, content_store: ContentStore, concept_graph: ConceptGraph) -> None:
        self._store = content_store
        self._graph = concept_graph
        self._node_map: Dict[str, ConceptNode] = {
            n.concept_id: n for n in concept_graph.nodes
        }
        self._rng = random.Random()

    # -------------------------------------------------------------------
    # Session lifecycle
    # -------------------------------------------------------------------

    def start_session(
        self,
        user_id: str,
        concept_id: str,
        mastery_states: Optional[Dict[str, MasterySnapshot]] = None,
        session_id: Optional[str] = None,
    ) -> SessionState:
        """Initialise a session for a specific concept.

        Parameters
        ----------
        user_id:
            Authenticated user identifier.
        concept_id:
            The concept the student will practise in this session.
        mastery_states:
            Pre-loaded mastery snapshots for all concepts the student has
            interacted with (or at least the current concept and its
            neighbours in the concept graph).  Keyed by concept_id.
        session_id:
            Optional explicit session ID (for testing / replay).

        Returns
        -------
        SessionState
            A fresh session state ready for :meth:`next_question`.
        """
        states = dict(mastery_states) if mastery_states else {}

        # Ensure the target concept has a snapshot even if never attempted.
        if concept_id not in states:
            states[concept_id] = MasterySnapshot()

        session = SessionState(
            user_id=user_id,
            concept_id=concept_id,
            mastery_states=states,
        )

        logger.info(
            "Session started: user=%s concept=%s mastery=%s",
            user_id,
            concept_id,
            states[concept_id].mastery_label,
        )
        return session

    # -------------------------------------------------------------------
    # Question selection (within-session loop)
    # -------------------------------------------------------------------

    def next_question(
        self,
        session: SessionState,
        preferred_concept: Optional[str] = None,
        seed: Optional[int] = None,
        exclude_ids: Optional[set] = None,
    ) -> AttemptResult:
        """Pick and render the next question for the student.

        Selection logic
        ~~~~~~~~~~~~~~~
        1. If ``step_down_queue`` is non-empty, serve the next step-down.
        2. Check session-complete conditions (question cap, streak exit,
           pool exhausted).
        3. Pick a parent question for the concept:
           a. Filter to questions not yet served this session.
           b. Determine the difficulty band from current mastery.
           c. Pick randomly within the band (fall back to full pool).
        4. If no questions remain, return session-complete.

        Parameters
        ----------
        session:
            Current session state (mutated in place).
        preferred_concept:
            Override concept selection (e.g. after a concept switch).
        seed:
            RNG seed for deterministic rendering (testing).

        Returns
        -------
        AttemptResult
            Contains the rendered question and display metadata.
        """
        concept_id = preferred_concept or session.concept_id
        mastery = session.get_mastery(concept_id)

        # 1. Step-down queue takes priority.
        if session.step_down_queue:
            return self._serve_next_step_down(session, mastery, seed)

        # 2. Check session-complete conditions (parent questions only).
        if self._should_end_session(session):
            logger.info(
                "Session complete: parents_served=%d streak=%d mastery=%s",
                session.parent_questions_served,
                session.correct_streak,
                mastery.mastery_label,
            )
            return AttemptResult(
                session_complete=True,
                mascot_emotion="celebrating",
                suggest_next_concept=self.suggest_next_concept(session),
                mastery_snapshot=self._mastery_dict(mastery),
                session_stats=self._session_stats(session),
            )

        # 3. Parent question selection.
        question = self._pick_question(session, concept_id, exclude_ids=exclude_ids)
        if question is None:
            # No questions for this concept — try another concept.
            alt_concept = self._pick_concept(session, exclude=[concept_id])
            if alt_concept:
                question = self._pick_question(session, alt_concept, exclude_ids=exclude_ids)
                concept_id = alt_concept
            if question is None:
                logger.info(
                    "No unseen questions left for any concept; ending session"
                )
                return AttemptResult(
                    session_complete=True,
                    mascot_emotion="celebrating",
                    suggest_next_concept=self.suggest_next_concept(session),
                    mastery_snapshot=self._mastery_dict(mastery),
                    session_stats=self._session_stats(session),
                )

        # Render the question.
        rng_seed = seed or int(time.time() * 1000) % (2**31)
        rendered = render_question(question, seed=rng_seed)

        # Update session state.
        session.current_question_id = question.id
        session.current_question_is_step_down = False
        session.current_phase = SessionPhase.parent
        session.current_attempt_number = 0
        session.current_diagnosis = None
        session.current_correct_index = rendered.correct_index
        session.current_rendered = rendered
        session.step_down_queue.clear()
        session.step_down_index = 0
        session.parent_question_for_step_downs = None
        session.params_context = getattr(rendered, "params_used", {})
        session.questions_served.append(question.id)
        session.parent_questions_served += 1

        if concept_id not in session.concepts_touched:
            session.concepts_touched.append(concept_id)

        logger.debug(
            "Serving parent: %s difficulty=%d (band=[%d,%d], parents_served=%d)",
            question.id,
            getattr(question, "difficulty", -1),
            *_difficulty_band(mastery),
            session.parent_questions_served,
        )

        return AttemptResult(
            next_question_id=question.id,
            is_step_down=False,
            rendered_question=rendered,
            mascot_emotion="neutral",
            mastery_snapshot=self._mastery_dict(mastery),
        )

    # -------------------------------------------------------------------
    # Answer submission (within-question loop)
    # -------------------------------------------------------------------

    def submit_answer(
        self,
        session: SessionState,
        question_id: str,
        selected_option_index: int,
        time_taken_ms: int = 0,
        strategy_signals: Optional[Dict[str, Any]] = None,
    ) -> AttemptResult:
        """Process a student's answer and decide what happens next.

        Parameters
        ----------
        session:
            Current session state (mutated in place).
        question_id:
            The question the student answered.
        selected_option_index:
            Zero-based index of the option the student tapped.
        time_taken_ms:
            Milliseconds the student spent before answering.
        strategy_signals:
            Optional dict of strategy signals from the Flutter client
            (e.g. manipulable_taps, undo_count, hint_used).

        Returns
        -------
        AttemptResult
            Instructions for the caller (next question, feedback, etc.).
        """
        if session.current_question_id is None:
            raise ValueError("No active question — call next_question first")

        session.total_attempts += 1
        session.current_attempt_number += 1

        # Look up the question to determine correctness and weight.
        question = self._store.get(question_id)
        if question is None:
            logger.error("Question %s not found in content store", question_id)
            raise ValueError(f"Question {question_id} not found in content store")

        # Use the stored correct_index and rendered question from when the
        # question was originally served. Re-rendering would reshuffle options,
        # giving a different correct_index — causing correct answers to appear
        # wrong and triggering spurious step-downs.
        is_correct = selected_option_index == session.current_correct_index
        rendered = session.current_rendered

        if rendered is None:
            # Fallback: shouldn't happen, but re-render if state is missing.
            logger.warning(
                "No stored rendered question for %s; re-rendering (may be inaccurate)",
                question_id,
            )
            rendered = render_question(
                question,
                inherited_params=session.params_context if session.current_question_is_step_down else None,
            )
            is_correct = selected_option_index == rendered.correct_index

        # Mastery weight from question config.
        weight = 1.0
        if hasattr(question, "mastery_config") and question.mastery_config:
            weight = question.mastery_config.weight

        mastery = session.get_mastery(session.concept_id)

        # Step-down questions don't update mastery (they're remediation).
        if not session.current_question_is_step_down:
            mastery.record_attempt(is_correct, weight)

        if is_correct:
            return self._handle_correct(session, question_id, mastery, rendered)
        else:
            return self._handle_wrong(
                session, question_id, selected_option_index, mastery, rendered
            )

    # -------------------------------------------------------------------
    # Correct answer handling
    # -------------------------------------------------------------------

    def _handle_correct(
        self,
        session: SessionState,
        question_id: str,
        mastery: MasterySnapshot,
        rendered: RenderedQuestion,
    ) -> AttemptResult:
        """Handle a correct answer (parent or step-down).

        If correct on a parent:
          - Clear step-down queue.
          - Increment correct streak.
          - If streak >= ADVANCE_STREAK_THRESHOLD and mastery >= proficient,
            suggest advancing to next concept.

        If correct on a step-down:
          - Encouraging praise (the kid is recovering from a mistake).
          - Move to next step-down or retry the parent.
        """
        is_step_down = session.current_question_is_step_down

        session.correct_streak += 1
        session.wrong_streak = 0

        feedback = self._positive_feedback(session.correct_streak, is_step_down)

        # -- correct on step-down: continue scaffold or retry parent --------
        if is_step_down:
            if session.step_down_queue:
                # More step-downs to go.
                return self._serve_next_step_down(session, mastery)
            else:
                # Step-down chain complete — retry the parent with a hint.
                return self._retry_parent_question(session, mastery)

        # -- correct on parent: standard flow ------------------------------
        session.step_down_queue.clear()
        session.parent_question_for_step_downs = None
        session.params_context.clear()

        # Check for mastery milestone.
        concept_mastered = mastery.mastery_label == "mastered"
        if concept_mastered and mastery.total_attempts > 1:
            logger.info(
                "Concept mastered: %s (shown_score=%d)",
                session.concept_id,
                mastery.shown_score,
            )

        # Suggest next concept if streak is strong enough.
        suggest_next: Optional[str] = None
        if (
            session.correct_streak >= ADVANCE_STREAK_THRESHOLD
            and mastery.at_least("proficient")
        ):
            suggest_next = self.suggest_next_concept(session)

        # Check session end.
        if self._should_end_session(session):
            return AttemptResult(
                feedback_message=feedback,
                mascot_emotion="celebrating",
                session_complete=True,
                concept_mastered=concept_mastered,
                suggest_next_concept=suggest_next,
                mastery_snapshot=self._mastery_dict(mastery),
                session_stats=self._session_stats(session),
            )

        # Serve next parent question.
        next_result = self.next_question(session)
        next_result.feedback_message = feedback
        next_result.concept_mastered = concept_mastered
        next_result.suggest_next_concept = suggest_next
        if concept_mastered:
            next_result.mascot_emotion = "celebrating"
        else:
            next_result.mascot_emotion = "happy"
        return next_result

    # -------------------------------------------------------------------
    # Wrong answer handling — THE MOAT
    # -------------------------------------------------------------------

    def _handle_wrong(
        self,
        session: SessionState,
        question_id: str,
        selected_option_index: int,
        mastery: MasterySnapshot,
        rendered: RenderedQuestion,
    ) -> AttemptResult:
        """Handle a wrong answer.  Diagnose, scaffold, never dead-end.

        If wrong on a **parent question**:
          - Look up misconception from the selected option index.
          - Load step-down path into ``step_down_queue``.
          - Store rendering params so step-downs inherit the same
            name/number context.
          - Reset correct streak.

        If wrong on a **step-down question**:
          - Provide encouraging feedback.
          - Move to next step-down in queue.
          - If step-down queue exhausted, re-serve the parent with a hint.
        """
        session.correct_streak = 0
        session.wrong_streak += 1
        is_step_down = session.current_question_is_step_down

        if is_step_down:
            return self._handle_wrong_step_down(session, question_id, mastery)
        else:
            return self._handle_wrong_parent(
                session, question_id, selected_option_index, mastery, rendered
            )

    def _handle_wrong_parent(
        self,
        session: SessionState,
        question_id: str,
        selected_option_index: int,
        mastery: MasterySnapshot,
        rendered: RenderedQuestion,
    ) -> AttemptResult:
        """Wrong answer on a parent question — multi-level scaffolding.

        Three levels of support before moving on:
          Level 1 (attempt 1): Show a text hint from socratic_feedback or
              generic encouragement, let the child retry the same question.
          Level 2 (attempt 2): Show misconception diagnosis + enhanced
              feedback, let the child retry once more.
          Level 3 (attempt 3+): Route to step-down scaffold questions as
              before.

        If no hint text is available at levels 1-2, we skip straight to
        the next applicable level so the child always gets useful help.
        """
        attempt = session.current_attempt_number  # already incremented by submit_answer

        # Extract misconception diagnosis, step-down path, and per-option
        # feedback from the rendered question.
        diagnosis: Optional[str] = None
        step_down_path: List[str] = []
        option_feedback: Optional[str] = None

        if hasattr(rendered, "wrong_option_diagnosis"):
            diagnosis = rendered.wrong_option_diagnosis.get(selected_option_index)
        if hasattr(rendered, "wrong_option_step_down_path"):
            step_down_path = list(
                rendered.wrong_option_step_down_path.get(selected_option_index, [])
            )
        if hasattr(rendered, "wrong_option_feedback"):
            option_feedback = rendered.wrong_option_feedback.get(selected_option_index)

        # Fallback: check the question model's misconceptions list.
        question = self._store.get(question_id)
        if not step_down_path and question and hasattr(question, "misconceptions"):
            for misconception in question.misconceptions:
                if self._misconception_matches_option(
                    misconception, selected_option_index, question
                ):
                    diagnosis = getattr(misconception, "id", str(misconception))
                    step_down_path = list(
                        getattr(misconception, "step_down_path", [])
                    )
                    if not option_feedback:
                        option_feedback = getattr(misconception, "feedback_child", None)
                    break

        # Gather hint text from the question's socratic_feedback field.
        # Substitute {param} placeholders with actual rendered values.
        hint_text: Optional[str] = None
        if question and hasattr(question, "socratic_feedback") and question.socratic_feedback:
            sf = question.socratic_feedback
            raw_hint = getattr(sf, "generic_incorrect", None)
            if raw_hint and rendered and hasattr(rendered, "params_used"):
                import re as _re
                def _hint_repl(m):
                    key = m.group(1)
                    return str(rendered.params_used.get(key, m.group(0)))
                hint_text = _re.sub(r"\{(\w+)\}", _hint_repl, raw_hint)
            else:
                hint_text = raw_hint

        # Store diagnosis for later levels even if we don't use it yet.
        session.current_diagnosis = diagnosis

        # ---- Level 1: Text hint (first wrong answer) --------------------
        if attempt == 1:
            # Use the socratic_feedback hint, or the option-specific feedback,
            # or a generic encouraging message.
            level1_feedback = hint_text or option_feedback
            if level1_feedback:
                logger.debug(
                    "Wrong on parent %s (attempt %d): showing Level 1 text hint",
                    question_id,
                    attempt,
                )
                return AttemptResult(
                    next_question_id=question_id,
                    rendered_question=rendered,
                    feedback_message=level1_feedback,
                    mascot_emotion="encouraging",
                    mastery_snapshot=self._mastery_dict(mastery),
                    retry_same_question=True,
                    scaffold_level=1,
                )
            # No hint text available — fall through to Level 2.
            logger.debug(
                "Wrong on parent %s (attempt %d): no Level 1 hint available, "
                "escalating to Level 2",
                question_id,
                attempt,
            )

        # ---- Level 2: Visual/misconception hint (second wrong answer) ---
        if attempt <= 2:
            # Show the misconception-specific feedback if available, otherwise
            # use the generic hint.  We no longer append the raw diagnosis label
            # ("counted_crossed_out" → awkward text); the kid-friendly
            # option_feedback already explains the misconception clearly.
            level2_feedback = option_feedback or hint_text
            if level2_feedback or diagnosis:
                display_feedback = (
                    level2_feedback or self._encouraging_feedback_wrong(is_step_down=False)
                )
                logger.debug(
                    "Wrong on parent %s (attempt %d): showing Level 2 "
                    "misconception hint (diagnosis=%s)",
                    question_id,
                    attempt,
                    diagnosis,
                )
                return AttemptResult(
                    next_question_id=question_id,
                    rendered_question=rendered,
                    feedback_message=display_feedback,
                    misconception_diagnosis=diagnosis,
                    mascot_emotion="thinking",
                    mastery_snapshot=self._mastery_dict(mastery),
                    retry_same_question=True,
                    scaffold_level=2,
                )
            # No misconception info at all — fall through to Level 3.
            logger.debug(
                "Wrong on parent %s (attempt %d): no Level 2 hint available, "
                "escalating to Level 3 step-down",
                question_id,
                attempt,
            )

        # ---- Level 3: Step-down scaffold (third wrong answer or fallthrough)
        if step_down_path:
            session.step_down_queue = list(step_down_path)
            session.step_down_index = 0
            session.parent_question_for_step_downs = question_id
            session.params_context = getattr(rendered, "params_used", {})

            logger.debug(
                "Wrong on parent %s (attempt %d): Level 3 step-down "
                "(misconception=%s step_downs=%s)",
                question_id,
                attempt,
                diagnosis,
                step_down_path,
            )

            return AttemptResult(
                feedback_message=option_feedback or self._encouraging_feedback_wrong(
                    is_step_down=False
                ),
                misconception_diagnosis=diagnosis,
                mascot_emotion="encouraging",
                is_step_down=True,
                mastery_snapshot=self._mastery_dict(mastery),
                next_question_id=self._peek_next_step_down(session),
                scaffold_level=3,
            )
        else:
            logger.warning(
                "Wrong on parent %s option=%d (attempt %d) but no step-down "
                "path found; moving on",
                question_id,
                selected_option_index,
                attempt,
            )
            # No step-down authored — move on gently if attempts exhausted.
            if session.current_attempt_number >= MAX_ATTEMPTS_PER_QUESTION:
                return self._move_on_gently(session, mastery)

            # Let the student try again with encouraging feedback.
            return AttemptResult(
                next_question_id=question_id,
                feedback_message=option_feedback or self._encouraging_feedback_wrong(
                    is_step_down=False
                ),
                misconception_diagnosis=diagnosis,
                mascot_emotion="encouraging",
                mastery_snapshot=self._mastery_dict(mastery),
                retry_same_question=True,
            )

    def _handle_wrong_step_down(
        self,
        session: SessionState,
        question_id: str,
        mastery: MasterySnapshot,
    ) -> AttemptResult:
        """Wrong answer on a step-down — encourage and continue scaffolding.

        Step-downs don't recurse: if the kid gets a step-down wrong we show
        encouragement and move to the next one.  If the queue is exhausted,
        re-serve the parent with a hint.
        """
        feedback = self._encouraging_feedback_wrong(is_step_down=True)

        if session.step_down_queue:
            # More step-downs remain — serve the next one.
            logger.debug(
                "Wrong on step-down %s; moving to next (remaining=%d)",
                question_id,
                len(session.step_down_queue),
            )
            result = self._serve_next_step_down(session, mastery)
            result.feedback_message = feedback
            return result
        else:
            # Step-down queue exhausted — re-serve parent with a hint.
            logger.debug(
                "Step-down queue exhausted after wrong on %s; retrying parent",
                question_id,
            )
            return self._retry_parent_question(session, mastery)

    # -------------------------------------------------------------------
    # Step-down scaffold chain
    # -------------------------------------------------------------------

    def _serve_next_step_down(
        self,
        session: SessionState,
        mastery: MasterySnapshot,
        seed: Optional[int] = None,
    ) -> AttemptResult:
        """Serve the next step-down question in the scaffold chain.

        Pops the front of ``step_down_queue``, renders the question with
        inherited params, and updates session state.
        """
        if not session.step_down_queue:
            # Queue empty — retry the parent.
            return self._retry_parent_question(session, mastery)

        if session.step_down_index >= MAX_STEP_DOWNS_PER_CHAIN:
            # Too many step-downs — reveal answer gently and move on.
            logger.debug(
                "Step-down chain exceeded max depth (%d); moving on",
                MAX_STEP_DOWNS_PER_CHAIN,
            )
            return self._move_on_gently(session, mastery)

        step_down_id = session.step_down_queue.pop(0)
        session.step_down_index += 1

        # Load and render the step-down question.
        sd_question = self._store.get(step_down_id)
        if sd_question is None:
            logger.warning("Step-down %s not found; skipping", step_down_id)
            # Recurse to try the next one (or retry parent if empty).
            return self._serve_next_step_down(session, mastery, seed)

        rng_seed = seed or int(time.time() * 1000) % (2**31)
        rendered = render_question(
            sd_question,
            seed=rng_seed,
            inherited_params=session.params_context,
        )

        session.current_question_id = step_down_id
        session.current_question_is_step_down = True
        session.current_phase = SessionPhase.step_down
        session.current_correct_index = rendered.correct_index
        session.current_rendered = rendered
        session.questions_served.append(step_down_id)
        # Note: parent_questions_served is NOT incremented for step-downs.

        logger.debug(
            "Serving step-down: %s (index=%d, remaining=%d)",
            step_down_id,
            session.step_down_index,
            len(session.step_down_queue),
        )

        return AttemptResult(
            next_question_id=step_down_id,
            is_step_down=True,
            rendered_question=rendered,
            feedback_message="Let's break this down...",
            mascot_emotion="thinking",
            mastery_snapshot=self._mastery_dict(mastery),
        )

    def _retry_parent_question(
        self,
        session: SessionState,
        mastery: MasterySnapshot,
    ) -> AttemptResult:
        """After completing step-downs, retry the original parent question.

        If the student has already exceeded ``MAX_ATTEMPTS_PER_QUESTION``,
        we move on gently instead.
        """
        parent_qid = session.parent_question_for_step_downs
        if parent_qid is None or session.current_attempt_number >= MAX_ATTEMPTS_PER_QUESTION:
            return self._move_on_gently(session, mastery)

        parent_q = self._store.get(parent_qid)
        if parent_q is None:
            logger.warning("Parent %s not found for retry; moving on", parent_qid)
            return self.next_question(session)

        rendered = render_question(
            parent_q,
            inherited_params=session.params_context,
        )

        session.current_question_id = parent_qid
        session.current_question_is_step_down = False
        session.current_phase = SessionPhase.retry_parent
        session.current_correct_index = rendered.correct_index
        session.current_rendered = rendered
        session.step_down_queue.clear()
        session.step_down_index = 0
        # Don't re-add to questions_served — already counted.

        logger.debug("Retrying parent %s with hint", parent_qid)

        return AttemptResult(
            next_question_id=parent_qid,
            is_step_down=False,
            rendered_question=rendered,
            feedback_message=(
                "Great job on the practice! Let's try the original question again."
            ),
            mascot_emotion="encouraging",
            mastery_snapshot=self._mastery_dict(mastery),
        )

    def _move_on_gently(
        self,
        session: SessionState,
        mastery: MasterySnapshot,
    ) -> AttemptResult:
        """Student struggled through step-downs and retry.  Don't dead-end.

        Show the answer warmly and move to the next question.  If the student
        has hit ``CONCEPT_SWITCH_AFTER_WRONG`` consecutive wrong answers,
        try switching to a different concept to avoid frustration.
        """
        # Check if we should switch concepts to avoid frustration.
        if session.wrong_streak >= CONCEPT_SWITCH_AFTER_WRONG:
            alt_concept = self._pick_concept(
                session, exclude=[session.concept_id]
            )
            if alt_concept:
                logger.info(
                    "Switching concept after %d consecutive wrong: %s -> %s",
                    session.wrong_streak,
                    session.concept_id,
                    alt_concept,
                )
                session.concept_id = alt_concept
                result = self.next_question(session, preferred_concept=alt_concept)
                result.feedback_message = (
                    "Let's try something different for a bit!"
                )
                result.mascot_emotion = "waving"
                return result

        # Clear scaffold state and serve the next parent question.
        session.step_down_queue.clear()
        session.step_down_index = 0
        session.parent_question_for_step_downs = None
        session.current_diagnosis = None
        session.current_question_id = None

        return self.next_question(session)

    # -------------------------------------------------------------------
    # Concept selection (across-session intelligence)
    # -------------------------------------------------------------------

    def suggest_next_concept(
        self,
        session: SessionState,
        concept_graph: Optional[ConceptGraph] = None,
    ) -> Optional[str]:
        """After a concept is sufficiently practised, suggest the next one.

        Uses the concept graph topology and mastery state to find the best
        next concept. Delegates to ``suggest_next_concept_for_user`` with
        the session's mastery states.

        Parameters
        ----------
        session:
            Current session state.
        concept_graph:
            Override concept graph (defaults to ``self._graph``).

        Returns
        -------
        str or None
            concept_id to suggest, or None if no good candidate.
        """
        graph = concept_graph or self._graph
        if graph is None:
            return None

        return self.suggest_next_concept_for_user(
            mastery_states=session.mastery_states,
            current_concept=session.concept_id,
            recent_failure_concept=self._detect_recent_failure(session),
            graph=graph,
        )

    def suggest_next_concept_for_user(
        self,
        mastery_states: Dict[str, MasterySnapshot],
        current_concept: Optional[str] = None,
        recent_failure_concept: Optional[str] = None,
        graph: Optional[ConceptGraph] = None,
    ) -> Optional[str]:
        """Graph-aware next-concept suggestion.

        Selection logic
        ~~~~~~~~~~~~~~~
        1. If a concept was recently failed, suggest a prerequisite for review.
        2. Find concepts whose hard prerequisites are all at ``familiar``
           or above in the student's mastery state.
        3. Among those, prefer concepts the child hasn't practised yet.
        4. Among already-attempted concepts, prefer the weakest for review.
        5. Respect ``strand_order`` edges for natural curriculum flow.
        6. Respect world-region clustering for Explorer tier.

        Parameters
        ----------
        mastery_states:
            concept_id -> MasterySnapshot for the user.
        current_concept:
            The concept to exclude from suggestions (currently being practised).
        recent_failure_concept:
            If the user recently failed a concept, suggest a prerequisite instead.
        graph:
            Override concept graph (defaults to ``self._graph``).

        Returns
        -------
        str or None
            concept_id to suggest, or None if no good candidate.
        """
        graph = graph or self._graph
        if graph is None or not graph.nodes:
            return None

        # 1. If a concept was recently failed, suggest a weak prerequisite
        #    for review instead of pushing forward.
        if recent_failure_concept:
            review = self._find_weak_prerequisite(
                recent_failure_concept, mastery_states, graph
            )
            if review:
                logger.debug(
                    "Suggesting prerequisite review %s after failure on %s",
                    review,
                    recent_failure_concept,
                )
                return review

        # 2. Gather all concepts and determine which are unlocked.
        all_concepts: List[str] = [n.concept_id for n in graph.nodes]
        unlocked: List[str] = []
        for cid in all_concepts:
            if cid == current_concept:
                continue
            if self._hard_prereqs_met(cid, mastery_states, graph):
                unlocked.append(cid)

        if not unlocked:
            logger.debug(
                "No unlocked concepts found beyond current=%s", current_concept
            )
            return None

        # 3. Partition into never-attempted vs already-attempted (not mastered).
        new_concepts: List[str] = []
        attempted_concepts: List[str] = []
        for cid in unlocked:
            snap = mastery_states.get(cid, MasterySnapshot())
            if snap.mastery_label == "new" and snap.total_attempts == 0:
                new_concepts.append(cid)
            elif not snap.at_least("mastered"):
                attempted_concepts.append(cid)

        # Prefer region-local concepts if region metadata exists.
        current_region = self._concept_region(current_concept, graph) if current_concept else None
        if current_region:
            region_new = [
                c for c in new_concepts
                if self._concept_region(c, graph) == current_region
            ]
            if region_new:
                new_concepts = region_new
            region_attempted = [
                c for c in attempted_concepts
                if self._concept_region(c, graph) == current_region
            ]
            if region_attempted:
                attempted_concepts = region_attempted

        # 4. Prefer a new concept, especially one that follows via strand_order.
        if new_concepts:
            strand_next = self._strand_order_successors(current_concept, graph) if current_concept else set()
            strand_new = [c for c in new_concepts if c in strand_next]
            choice = (
                self._rng.choice(strand_new)
                if strand_new
                else self._rng.choice(new_concepts)
            )
            logger.debug("Suggesting new concept: %s", choice)
            return choice

        # 5. All unlocked concepts have been attempted — revisit the weakest.
        if attempted_concepts:
            weakest = min(
                attempted_concepts,
                key=lambda cid: mastery_states.get(
                    cid, MasterySnapshot()
                ).internal_score,
            )
            logger.debug(
                "All unlocked concepts attempted; suggesting weakest: %s",
                weakest,
            )
            return weakest

        return None

    def _detect_recent_failure(self, session: SessionState) -> Optional[str]:
        """Check if the session ended with a failure pattern (high wrong streak).

        Returns the concept_id that was being practised during failure, or None.
        """
        if session.wrong_streak >= CONCEPT_SWITCH_AFTER_WRONG:
            return session.concept_id
        return None

    def _find_weak_prerequisite(
        self,
        concept_id: str,
        mastery_states: Dict[str, MasterySnapshot],
        graph: ConceptGraph,
    ) -> Optional[str]:
        """Find the weakest prerequisite of a concept for review.

        Returns the prerequisite concept_id with the lowest mastery that
        isn't already mastered, or None if all prerequisites are strong.
        """
        node = self._node_map.get(concept_id)
        if node is None:
            return None

        prereq_ids = node.prerequisite_ids
        if not prereq_ids:
            return None

        # Find the weakest prerequisite that isn't mastered.
        weakest_id: Optional[str] = None
        weakest_score: float = 2.0  # higher than any real score
        for pid in prereq_ids:
            snap = mastery_states.get(pid, MasterySnapshot())
            if not snap.at_least("mastered") and snap.internal_score < weakest_score:
                weakest_score = snap.internal_score
                weakest_id = pid
        return weakest_id

    # -------------------------------------------------------------------
    # Learning path (topological ordering + mastery status)
    # -------------------------------------------------------------------

    def get_learning_path(
        self,
        mastery_states: Dict[str, MasterySnapshot],
        graph: Optional[ConceptGraph] = None,
    ) -> List[Dict[str, Any]]:
        """Return the full learning path as a topologically sorted list.

        Each entry includes the concept metadata and its status for the
        given user:
          - "locked": hard prerequisites not met
          - "ready": prerequisites met, not yet started
          - "in_progress": started but not mastered
          - "mastered": mastery label is "mastered"

        Parameters
        ----------
        mastery_states:
            concept_id -> MasterySnapshot for the user.
        graph:
            Override concept graph (defaults to ``self._graph``).

        Returns
        -------
        List of dicts with concept info and status.
        """
        graph = graph or self._graph
        if graph is None or not graph.nodes:
            return []

        sorted_nodes = self._topological_sort(graph)

        path: List[Dict[str, Any]] = []
        for node in sorted_nodes:
            cid = node.concept_id
            snap = mastery_states.get(cid, MasterySnapshot())
            prereqs_met = self._hard_prereqs_met(cid, mastery_states, graph)

            # Determine status.
            if snap.at_least("mastered"):
                status = "mastered"
            elif snap.total_attempts > 0:
                status = "in_progress"
            elif prereqs_met:
                status = "ready"
            else:
                status = "locked"

            path.append({
                "concept_id": cid,
                "display_name": node.display_name,
                "description": node.description,
                "world_region": getattr(node, "world_region", None),
                "topic_branch": getattr(node, "topic_branch", None),
                "status": status,
                "mastery_label": snap.mastery_label,
                "shown_score": snap.shown_score,
                "total_attempts": snap.total_attempts,
                "prerequisites": node.prerequisite_ids,
            })

        return path

    @staticmethod
    def _topological_sort(graph: ConceptGraph) -> List[ConceptNode]:
        """Kahn's algorithm topological sort over the concept graph.

        Uses all prerequisite edges (hard + soft) to determine ordering.
        Nodes with no prerequisites come first. Ties are broken by the
        original order in the graph file to preserve authorial intent.
        """
        node_map: Dict[str, ConceptNode] = {
            n.concept_id: n for n in graph.nodes
        }
        # Build in-degree map and adjacency list.
        in_degree: Dict[str, int] = {n.concept_id: 0 for n in graph.nodes}
        dependents: Dict[str, List[str]] = {n.concept_id: [] for n in graph.nodes}

        for node in graph.nodes:
            for prereq_id in node.prerequisite_ids:
                if prereq_id in in_degree:
                    in_degree[node.concept_id] += 1
                    dependents[prereq_id].append(node.concept_id)

        # Seed with zero in-degree nodes, preserving original order.
        queue: List[str] = [
            n.concept_id for n in graph.nodes
            if in_degree[n.concept_id] == 0
        ]
        result: List[ConceptNode] = []

        while queue:
            cid = queue.pop(0)
            result.append(node_map[cid])
            for dep in dependents[cid]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        # If there are cycles, append remaining nodes at the end.
        if len(result) < len(graph.nodes):
            seen = {n.concept_id for n in result}
            for node in graph.nodes:
                if node.concept_id not in seen:
                    result.append(node)

        return result

    def _pick_concept(
        self,
        session: SessionState,
        exclude: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Pick the best concept to practice next, respecting the DAG.

        Used internally when the current concept's question pool is exhausted
        or when switching concepts after repeated wrong answers.

        Priority:
        1. Concepts in the zone of proximal development (familiar, 25-50%).
        2. New concepts (never attempted, but unlocked).
        3. Proficient concepts that could use reinforcement.
        4. Mastered concepts (lowest priority).
        """
        exclude_set = set(exclude or [])
        unlocked = self._get_unlocked_concepts(session)

        available: List[str] = []
        for cid in unlocked:
            if cid in exclude_set:
                continue
            questions = self._get_questions_for_concept(cid)
            if questions:
                available.append(cid)

        if not available:
            return None

        # Score each concept and pick from the top candidates with some
        # randomisation to keep sessions feeling fresh.
        scored: List[Tuple[float, str]] = []
        for cid in available:
            mastery = session.get_mastery(cid)
            score = self._concept_priority_score(mastery)
            scored.append((score, cid))

        scored.sort(key=lambda x: -x[0])

        # Weighted random from top 3 to avoid being too predictable.
        top = scored[:3]
        weights = [s[0] + 0.1 for s in top]
        chosen = self._rng.choices(
            [s[1] for s in top], weights=weights, k=1
        )[0]
        return chosen

    # -------------------------------------------------------------------
    # Question selection within a concept
    # -------------------------------------------------------------------

    def _pick_question(
        self,
        session: SessionState,
        concept_id: str,
        exclude_ids: Optional[set] = None,
    ) -> Optional[Question]:
        """Pick a question for the given concept.

        Filters to questions not yet served this session, then selects from
        the appropriate difficulty band based on mastery.

        Parameters
        ----------
        session:
            Current session state.
        concept_id:
            Concept to select questions from.
        exclude_ids:
            Additional question IDs to exclude (e.g. from prior diagnostics
            to prevent repetition on retests).
        """
        all_questions = self._get_questions_for_concept(concept_id)
        if not all_questions:
            return None

        served_set = set(session.questions_served)
        candidates = [q for q in all_questions if q.id not in served_set]

        if not candidates:
            logger.debug(
                "All questions served for concept=%s (%d total)",
                concept_id,
                len(all_questions),
            )
            return None

        mastery = session.get_mastery(concept_id)
        low, high = _difficulty_band(mastery)
        return _pick_from_band(candidates, low, high, exclude_ids=exclude_ids)

    def _get_questions_for_concept(self, concept_id: str) -> List[Question]:
        """Find all parent questions mapped to a concept.

        Checks ``mastery_config.concept_id`` first, then falls back to
        grade-based ID matching and topic-based lookup for v3b questions.
        """
        result: List[Question] = []

        # Strategy 1: Explicit mastery_config.concept_id
        for q in self._store.parents():
            if hasattr(q, "mastery_config") and q.mastery_config:
                if q.mastery_config.concept_id == concept_id:
                    result.append(q)

        if result:
            return result

        # Strategy 2: v3b ID-based matching.
        # concept_id format: g{grade}.{topic_slug}
        # question ID format: G{grade}-CH{NN}-{TOPIC_CODE}-{NNN}
        # Map concept graph nodes to questions by grade + chapter.
        parts = concept_id.split(".")
        if len(parts) >= 2:
            grade_prefix = parts[0].upper()  # "g1" -> "G1"
            # Look up which chapter(s) this concept maps to from the graph node
            node = self._node_map.get(concept_id)
            if node:
                desc = getattr(node, "description", "") or ""
                # Extract chapter number from description: "Grade 1, Chapter 3: ..."
                import re as _re
                ch_match = _re.search(r"Chapter\s+(\d+)", desc)
                if ch_match:
                    ch_num = int(ch_match.group(1))
                    ch_prefix = f"{grade_prefix}-CH{ch_num:02d}-"
                    result = [
                        q for q in self._store.parents()
                        if q.id.startswith(ch_prefix)
                    ]
                    if result:
                        logger.debug(
                            "v3b chapter mapping: %s -> %s (%d questions)",
                            concept_id, ch_prefix, len(result),
                        )
                        return result

            # Strategy 3: Grade-level fallback — all questions for this grade
            grade_questions = [
                q for q in self._store.parents()
                if q.id.startswith(f"{grade_prefix}-")
            ]
            if grade_questions:
                # Try topic-based filtering within the grade
                topic_slug = "_".join(parts[1:])  # e.g. "attribute_counting"
                topic_filtered = [
                    q for q in grade_questions
                    if hasattr(q, "topic") and topic_slug.replace("_", " ").lower()
                    in q.topic.value.replace("_", " ").lower()
                ]
                if len(topic_filtered) >= 2:
                    result = topic_filtered
                    logger.debug(
                        "v3b topic filter: %s -> %d questions",
                        concept_id, len(result),
                    )
                    return result

        # Strategy 4: Legacy topic-based lookup
        _CONCEPT_TO_TOPIC = {
            "counting": "counting_observation",
            "addition": "arithmetic_missing_numbers",
            "subtraction": "arithmetic_missing_numbers",
            "shapes": "shapes_folding_symmetry",
            "spatial": "spatial_reasoning_3d",
            "patterns": "patterns_sequences",
            "measurement": "logic_ordering",
        }
        _CONCEPT_SUBSKILL_FILTER = {
            "addition": ["addition", "missing_addend", "add_", "sum", "plus",
                         "doubles", "near_doubles", "number_bond", "fact_famil"],
            "subtraction": ["subtraction", "missing_subtrahend", "subtract_",
                            "minus", "difference", "take_away"],
        }
        prefix = concept_id.split(".")[0] if "." in concept_id else concept_id
        topic = _CONCEPT_TO_TOPIC.get(prefix)
        if topic:
            pool = self._store.by_topic(topic)
            subskill_keys = _CONCEPT_SUBSKILL_FILTER.get(prefix)
            if subskill_keys and pool:
                filtered = [
                    q for q in pool
                    if hasattr(q, "subskills") and q.subskills and any(
                        any(key in sk.lower() for key in subskill_keys)
                        for sk in q.subskills
                    )
                ]
                if len(filtered) >= 3:
                    result = filtered
                else:
                    result = pool
            else:
                result = pool
            logger.debug(
                "Legacy topic mapping: %s -> %s (%d questions)",
                concept_id, topic, len(result),
            )

        return result

    # -------------------------------------------------------------------
    # Session-end logic
    # -------------------------------------------------------------------

    def _should_end_session(self, session: SessionState) -> bool:
        """Determine whether the session should end.

        Conditions (any one triggers exit):
        1. Parent question cap (``MAX_PARENT_QUESTIONS``) reached.
        2. Correct streak >= ``MASTERY_STREAK_EXIT`` *and* mastery is
           ``proficient+`` *and* at least ``MIN_PARENT_QUESTIONS`` served.
        3. No more questions available (checked by caller).
        """
        if session.parent_questions_served >= MAX_PARENT_QUESTIONS:
            return True

        mastery = session.get_mastery(session.concept_id)
        if (
            session.correct_streak >= MASTERY_STREAK_EXIT
            and mastery.at_least("proficient")
            and session.parent_questions_served >= MIN_PARENT_QUESTIONS
        ):
            return True

        return False

    # -------------------------------------------------------------------
    # Concept graph helpers
    # -------------------------------------------------------------------

    def _hard_prereqs_met(
        self,
        concept_id: str,
        mastery_states: Dict[str, MasterySnapshot],
        graph: ConceptGraph,
    ) -> bool:
        """Return True if all hard prerequisites for *concept_id* are met.

        A hard prerequisite is met when the student's mastery for that
        prerequisite concept is at ``familiar`` or above.
        """
        node = self._node_map.get(concept_id)
        if node is None:
            return True

        hard_prereqs = getattr(node, "hard_prerequisites", [])
        if not hard_prereqs:
            return True

        for prereq_id in hard_prereqs:
            snap = mastery_states.get(prereq_id, MasterySnapshot())
            if not snap.at_least("familiar"):
                logger.debug(
                    "Concept %s locked: hard prereq %s is %s",
                    concept_id,
                    prereq_id,
                    snap.mastery_label,
                )
                return False
        return True

    def _get_unlocked_concepts(self, session: SessionState) -> List[str]:
        """Determine which concepts are unlocked based on DAG prerequisites.

        A concept is unlocked if all its hard prerequisites are at
        ``familiar`` or above.
        """
        unlocked: List[str] = []
        for node in self._graph.nodes:
            if self._hard_prereqs_met(
                node.concept_id, session.mastery_states, self._graph
            ):
                unlocked.append(node.concept_id)
        return unlocked

    @staticmethod
    def _strand_order_successors(
        concept_id: str, graph: ConceptGraph
    ) -> set:
        """Return concepts that follow *concept_id* via strand_order edges."""
        try:
            successors: set = set()
            for edge in graph.edges:
                if (
                    edge.source == concept_id
                    and edge.edge_type == EdgeType.strand_order
                ):
                    successors.add(edge.target)
            return successors
        except (AttributeError, TypeError):
            return set()

    @staticmethod
    def _concept_region(
        concept_id: str, graph: ConceptGraph
    ) -> Optional[str]:
        """Extract world-region metadata for a concept, if available.

        Used for Explorer-tier cohesion — keeps the student in the same
        world region when suggesting the next concept.
        """
        try:
            for node in graph.nodes:
                if node.concept_id == concept_id:
                    return getattr(node, "world_region", None)
        except (AttributeError, TypeError):
            pass
        return None

    # -------------------------------------------------------------------
    # Misconception matching
    # -------------------------------------------------------------------

    @staticmethod
    def _misconception_matches_option(
        misconception: Any,
        selected_option_index: int,
        question: Question,
    ) -> bool:
        """Determine whether a misconception corresponds to the chosen option.

        Supports two content-store layouts:

        1. The misconception has an ``option_index`` attribute.
        2. The question has a ``wrong_option_misconception_map`` dict
           mapping option indices to misconception IDs.
        3. Fallback: if there's only one misconception, assume it matches.
        """
        # Layout 1: direct attribute.
        if hasattr(misconception, "option_index"):
            return misconception.option_index == selected_option_index

        # Layout 2: question-level map.
        if hasattr(question, "wrong_option_misconception_map"):
            mapped = question.wrong_option_misconception_map.get(
                selected_option_index
            )
            mid = getattr(misconception, "id", None)
            return mapped is not None and mapped == mid

        # Fallback: single misconception.
        if hasattr(question, "misconceptions") and len(question.misconceptions) == 1:
            return True

        return False

    # -------------------------------------------------------------------
    # Priority scoring
    # -------------------------------------------------------------------

    @staticmethod
    def _concept_priority_score(mastery: MasterySnapshot) -> float:
        """Score a concept for selection priority.  Higher = more likely.

        +--------------------+-------+----------------------------------+
        | Mastery band       | Score | Rationale                        |
        +====================+=======+==================================+
        | new (0 attempts)   | 3.0   | High priority, needs exposure    |
        | new (< 25%)        | 2.5   | Struggling, needs practice       |
        | familiar (25-50%)  | 4.0   | Zone of proximal development     |
        | proficient (50-80%)| 2.0   | Getting there, moderate priority |
        | mastered (80+%)    | 0.5   | Reinforcement only               |
        +--------------------+-------+----------------------------------+
        """
        if mastery.total_attempts == 0:
            return 3.0
        if mastery.shown_score < 25:
            return 2.5
        if mastery.shown_score < 50:
            return 4.0
        if mastery.shown_score < 80:
            return 2.0
        return 0.5

    # -------------------------------------------------------------------
    # Step-down peek (for pre-loading)
    # -------------------------------------------------------------------

    def _peek_next_step_down(self, session: SessionState) -> Optional[str]:
        """Return the next step-down ID without popping it from the queue.

        Used to pre-populate ``next_question_id`` in feedback responses so
        the client can begin loading the next question while showing feedback.
        """
        if session.step_down_queue:
            return session.step_down_queue[0]
        return None

    # -------------------------------------------------------------------
    # Serialisation helpers
    # -------------------------------------------------------------------

    @staticmethod
    def _mastery_dict(mastery: MasterySnapshot) -> Dict[str, Any]:
        """Serialise a mastery snapshot for the client."""
        return {
            "internal_score": round(mastery.internal_score, 3),
            "shown_score": mastery.shown_score,
            "mastery_label": mastery.mastery_label,
            "total_attempts": mastery.total_attempts,
            "streak_current": mastery.streak_current,
        }

    @staticmethod
    def _session_stats(session: SessionState) -> Dict[str, Any]:
        """Summarise session stats for the end-of-session screen."""
        return {
            "user_id": session.user_id,
            "concept_id": session.concept_id,
            "parent_questions_served": session.parent_questions_served,
            "total_questions_served": len(session.questions_served),
            "total_attempts": session.total_attempts,
            "correct_streak_best": session.correct_streak,
            "concepts_touched": list(session.concepts_touched),
            "masteries": {
                cid: {
                    "internal_score": round(snap.internal_score, 3),
                    "shown_score": snap.shown_score,
                    "mastery_label": snap.mastery_label,
                }
                for cid, snap in session.mastery_states.items()
            },
        }

    # -------------------------------------------------------------------
    # Kid-facing feedback strings
    # -------------------------------------------------------------------

    @staticmethod
    def _positive_feedback(streak: int, is_step_down: bool) -> str:
        """Return a kid-friendly success message.

        Messages escalate with the streak to give a sense of momentum.
        Step-down correct answers get gentler praise (the kid is recovering
        from a mistake).
        """
        if is_step_down:
            return random.choice([
                "You got it!",
                "Nice work! You're figuring it out.",
                "That's right! Keep going.",
            ])

        if streak >= 5:
            return random.choice([
                "You're on fire! Amazing job!",
                "Wow, 5 in a row! You're a math superstar!",
                "Incredible streak! Kiwi is so proud!",
            ])
        if streak >= 3:
            return random.choice([
                "Awesome, you're on a roll!",
                "3 in a row! You're really getting this!",
                "Great streak! Keep it up!",
            ])
        return random.choice([
            "Great job!",
            "That's correct!",
            "Well done!",
            "You nailed it!",
        ])

    @staticmethod
    def _encouraging_feedback_wrong(is_step_down: bool) -> str:
        """Return a kind, encouraging message after a wrong answer.

        Grade 1 students need to feel safe making mistakes.  Messages never
        use the word "wrong" — they frame the error as a learning moment.
        """
        if is_step_down:
            return random.choice([
                "Not quite -- let's keep working on this together!",
                "Almost! Kiwi believes in you. Let's try the next one.",
                "That's okay! Learning takes practice.",
            ])
        return random.choice([
            "Hmm, let's think about this a different way!",
            "Not quite, but that's okay! Let's figure it out together.",
            "Tricky one! Kiwi has some steps to help you.",
        ])
