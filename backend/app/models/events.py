"""
Kiwimath event schemas — Firestore document models.

v1: Three events drive the adaptive loop:
  1. attempt_recorded — client writes after each question attempt
  2. mastery_updated — Cloud Function writes in a transaction (server-only)
  3. revisit_due     — Cloud Function writes when spaced repetition triggers

DESIGN PRINCIPLES (from design cofounder event schema):
  - Monotonic shownScore is SERVER-ENFORCED, not client-trusted
  - Client writes attempts only; mastery is Cloud Function in a transaction
  - Document IDs are deterministic (no auto-IDs where it matters)
  - No PII in any kid-writable field; userId is opaque
  - COPPA / GDPR-K / India DPDPA clean by construction

FIRESTORE STRUCTURE:
  users/{userId}/attempts/{attemptId}       — AttemptRecorded
  users/{userId}/mastery/{conceptId}         — MasteryUpdated
  users/{userId}/revisits/{conceptId}        — RevisitDue

Reference: _Schema/event_schemas_v1.json (JSON Schema draft-2020-12)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------


class MascotEmotion(str, Enum):
    """Defined emotion set for universal mascot assets.
    Asset path: /assets/universal/mascot/{companion_id}-{emotion}.svg"""
    neutral = "neutral"
    thinking = "thinking"
    happy = "happy"
    encouraging = "encouraging"
    celebrating = "celebrating"
    waving = "waving"
    reading = "reading"


class SolutionPath(str, Enum):
    """How the kid solved it — inferred from tap signature.
    Enables DreamBox-style adaptivity without BKT in v1.
    Acad cofounder may extend this enum."""
    direct = "direct"                     # knew it immediately (subitizing)
    counted_up = "counted_up"             # tapped sequentially from 1
    counted_down = "counted_down"         # tapped down from total
    trial_and_error = "trial_and_error"   # multiple undos, no clear strategy
    used_hint = "used_hint"               # triggered hint before answering
    unknown = "unknown"                   # couldn't classify


class RevisitReason(str, Enum):
    """Four distinct reasons for a revisit nudge, each meaningful for adaptivity."""
    spaced_repetition = "spaced_repetition"       # time-based decay
    decay_threshold = "decay_threshold"           # internal Elo dropped below threshold
    prerequisite_review = "prerequisite_review"   # upstream concept is rusty
    mastery_check = "mastery_check"               # one-time verification after first mastery


# ---------------------------------------------------------------------------
# Event 1: attempt_recorded
# Firestore path: users/{userId}/attempts/{attemptId}
# Written by: CLIENT (Flutter app, flushed from offline buffer)
# attemptId: client UUID — idempotent on retry (no duplicates)
# ---------------------------------------------------------------------------


class StrategySignals(BaseModel):
    """Rich interaction signals for adaptivity — what the tap signature tells us.
    These let us infer HOW a kid solved it, not just IF they got it right."""
    manipulable_taps: Optional[int] = None        # total taps on manipulable objects
    undo_count: int = 0                           # times kid un-tapped a marble
    overshoot_count: int = 0                      # times kid tried to tap past the cap
    first_tap_latency_ms: Optional[int] = None    # ms from question render to first tap
    pauses_over_3s_count: int = 0                 # number of pauses >3 seconds
    solution_path: SolutionPath = SolutionPath.unknown
    hint_used: bool = False
    hint_tap_count: int = 0                       # how many times hint was requested
    audio_replay_count: int = 0                   # how many times narration was replayed


class StructuredAnswer(BaseModel):
    """Structured answer representation — no free-text fields (privacy).
    answerGiven is typed by interaction mode."""
    answer_type: Literal["count", "option_index", "option_letter", "ordered_list", "structured"]
    value: Any                                    # int for count, str for option, list for ordered
    raw_json: Optional[Dict[str, Any]] = None     # full structured representation if needed


class AttemptRecorded(BaseModel):
    """A single question attempt by a student.
    Client writes this after each answer check.
    attemptId is a client-generated UUID for idempotent offline flush."""

    # ── Identity ──
    attempt_id: str = Field(..., description="Client UUID — idempotent on retry")
    user_id: str = Field(..., description="Opaque user ID — no PII")
    question_id: str = Field(..., pattern=r"^G\d+-[A-Z]+-\d{3}(-S\d)?$")
    concept_id: str = Field(..., pattern=r"^[a-z][a-z0-9_.]+$")

    # ── Context ──
    session_id: str                               # groups attempts within a single lesson
    tier: Literal["explorer", "adventurer", "architect"]
    region: Optional[str] = None                  # "IN", "US", etc.
    locale: Optional[str] = None                  # "en-IN", "es-MX"

    # ── Result ──
    is_correct: bool
    answer_given: StructuredAnswer
    correct_answer: StructuredAnswer
    retry_number: int = Field(0, ge=0, le=10)     # 0 = first attempt, 1+ = retries
    time_taken_ms: int = Field(..., ge=0)         # wall-clock time from render to submit

    # ── Strategy signals (the adaptivity gold) ──
    strategy: Optional[StrategySignals] = None

    # ── Timestamps ──
    client_timestamp: datetime                    # device clock (may drift)
    server_timestamp: Optional[datetime] = None   # Firestore server timestamp (set by trigger)

    # ── Offline ──
    is_offline_flush: bool = False                # true if written from offline buffer
    offline_queue_position: Optional[int] = None  # position in offline queue


# ---------------------------------------------------------------------------
# Event 2: mastery_updated
# Firestore path: users/{userId}/mastery/{conceptId}
# Written by: CLOUD FUNCTION ONLY (transaction: read prev → compute → write)
# Document ID: conceptId (one row per concept per user, overwrite-on-update)
#
# INVARIANT: shown_score = max(shown_score_prev, floor(internal_score * 100))
# This is the monotonic guarantee — shownScore never drops.
# ---------------------------------------------------------------------------


class MasteryUpdated(BaseModel):
    """Per-concept mastery state for a student.
    Server-only writes in a transaction. Client reads for display.

    The internal_score moves both ways (bidirectional Elo for adaptivity).
    The shown_score only moves up (monotonic for kid confidence).
    This is the core contract of the mastery model."""

    # ── Identity ──
    user_id: str
    concept_id: str = Field(..., pattern=r"^[a-z][a-z0-9_.]+$")

    # ── Scores ──
    internal_score: float = Field(..., ge=0.0, le=1.0,
        description="Bidirectional Elo — moves both ways for adaptivity")
    shown_score: int = Field(..., ge=0, le=100,
        description="Monotonic: max(prev_shown, floor(internal*100))")
    mastery_label: Literal["new", "familiar", "proficient", "mastered"]

    # ── Attempt stats ──
    total_attempts: int = Field(0, ge=0)
    correct_attempts: int = Field(0, ge=0)
    streak_current: int = Field(0, ge=0)          # consecutive correct
    streak_best: int = Field(0, ge=0)

    # ── Triggering attempt ──
    last_attempt_id: str
    last_attempt_correct: bool

    # ── Timestamps ──
    first_attempted_at: datetime
    last_attempted_at: datetime
    mastered_at: Optional[datetime] = None        # first time shown_score >= 80

    # ── Spaced repetition ──
    review_interval_days: Optional[int] = None    # current interval
    next_review_at: Optional[datetime] = None     # when revisit should trigger


# ---------------------------------------------------------------------------
# Event 3: revisit_due
# Firestore path: users/{userId}/revisits/{conceptId}
# Written by: CLOUD FUNCTION (after mastery_updated, checks decay/prereqs)
# Document ID: conceptId (one active revisit per concept)
# ---------------------------------------------------------------------------


class RevisitDue(BaseModel):
    """A spaced repetition or prerequisite-review nudge.
    Home screen batches to at most one nudge per session.
    nudge_count caps at 3 before we stop pushing.

    Four reasons, each meaningful:
    - spaced_repetition: time-based decay interval elapsed
    - decay_threshold: internal Elo dropped below proficiency threshold
    - prerequisite_review: kid attempts downstream concept when upstream is rusty
    - mastery_check: one-time verification right after first mastery
    """

    # ── Identity ──
    user_id: str
    concept_id: str = Field(..., pattern=r"^[a-z][a-z0-9_.]+$")

    # ── Revisit details ──
    reason: RevisitReason
    priority: int = Field(..., ge=1, le=5,
        description="1 = highest priority. Home screen sorts by this.")
    trigger_attempt_id: Optional[str] = None      # for prerequisite_review: what triggered it

    # ── Status ──
    is_active: bool = True
    nudge_count: int = Field(0, ge=0, le=3,
        description="How many times we've nudged. Cap at 3, then stop.")
    last_nudged_at: Optional[datetime] = None

    # ── Context ──
    current_shown_score: int = Field(..., ge=0, le=100)
    current_mastery_label: Literal["new", "familiar", "proficient", "mastered"]
    decay_from_score: Optional[int] = None        # what shown_score was before decay

    # ── Timestamps ──
    created_at: datetime
    resolved_at: Optional[datetime] = None        # set when kid completes the revisit
    expires_at: Optional[datetime] = None         # auto-resolve if not acted on


# ---------------------------------------------------------------------------
# Firestore index requirements (for query patterns)
# ---------------------------------------------------------------------------
# These would be defined in firestore.indexes.json:
#
# 1. users/{userId}/attempts — compound index on:
#    (concept_id ASC, client_timestamp DESC) — "recent attempts for concept"
#    (session_id ASC, client_timestamp ASC) — "all attempts in session order"
#    (is_correct ASC, concept_id ASC) — "wrong attempts by concept"
#
# 2. users/{userId}/mastery — compound index on:
#    (mastery_label ASC, last_attempted_at DESC) — "concepts by mastery level"
#    (next_review_at ASC) — "upcoming reviews"
#
# 3. users/{userId}/revisits — compound index on:
#    (is_active ASC, priority ASC) — "active revisits sorted by priority"
#    (reason ASC, is_active ASC) — "active revisits by type"
