"""Mastery recompute Cloud Function for Kiwimath.

Firestore trigger that fires when a new attempt is written to
``users/{userId}/attempts/{attemptId}``.  It reads the attempt, fetches (or
initialises) the corresponding mastery document, applies a simplified Elo
update, enforces the monotonic shown-score invariant, and writes the result
back inside a Firestore transaction so concurrent attempts cannot race.

Business rules
--------------
* K-factor is 0.15 -- tuned for Grade 1 where we want faster progression.
* difficulty_weight normalises question_difficulty (1-5) into [0.2, 1.0].
* Wrong answers are penalised at half the rate of correct-answer gains.
* ``shown_score`` NEVER decreases (monotonic guarantee).
* Mastery labels: new (0-24), familiar (25-49), proficient (50-79),
  mastered (80-100).
* Spaced-repetition interval doubles each time the child is mastered,
  capped at 180 days.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone

import firebase_admin
from firebase_admin import firestore as admin_firestore
from firebase_functions import firestore_fn
from google.cloud import firestore  # type: ignore[attr-defined]

logger = logging.getLogger("kiwimath.mastery_recompute")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

K_FACTOR: float = 0.15
WRONG_PENALTY_FACTOR: float = 0.5
MAX_DIFFICULTY: int = 5
DEFAULT_REVIEW_INTERVAL_DAYS: int = 7
MAX_REVIEW_INTERVAL_DAYS: int = 180

MASTERY_LABELS: list[tuple[int, str]] = [
    (80, "mastered"),
    (50, "proficient"),
    (25, "familiar"),
    (0, "new"),
]

# ---------------------------------------------------------------------------
# Firebase app initialisation (idempotent)
# ---------------------------------------------------------------------------

if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = admin_firestore.client()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mastery_label(shown_score: int) -> str:
    """Derive a human-readable mastery label from the shown_score (0-100)."""
    for threshold, label in MASTERY_LABELS:
        if shown_score >= threshold:
            return label
    return "new"


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp *value* between *lo* and *hi*."""
    return max(lo, min(hi, value))


def _now_utc() -> datetime:
    """Return the current UTC time (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# Transaction body
# ---------------------------------------------------------------------------


def _update_mastery_in_transaction(
    transaction: firestore.Transaction,
    mastery_ref: firestore.DocumentReference,
    attempt_data: dict,
    user_id: str,
    concept_id: str,
) -> None:
    """Read-then-write mastery inside a Firestore transaction.

    This prevents race conditions when two attempts for the same concept land
    at roughly the same time.
    """

    snapshot = mastery_ref.get(transaction=transaction)

    now = _now_utc()

    if snapshot.exists:
        mastery = snapshot.to_dict()
    else:
        mastery = {
            "user_id": user_id,
            "concept_id": concept_id,
            "internal_score": 0.0,
            "shown_score": 0,
            "mastery_label": "new",
            "total_attempts": 0,
            "correct_attempts": 0,
            "streak_current": 0,
            "streak_best": 0,
            "review_interval_days": DEFAULT_REVIEW_INTERVAL_DAYS,
            "next_review_at": None,
            "mastered_at": None,
            "created_at": now,
            "updated_at": now,
        }

    # ----- extract attempt fields -----
    is_correct: bool = attempt_data.get("is_correct", False)
    question_difficulty: int = int(attempt_data.get("question_difficulty", 3))
    difficulty_weight: float = question_difficulty / MAX_DIFFICULTY  # 0.2-1.0

    # ----- Elo-style internal score update -----
    prev_internal: float = float(mastery.get("internal_score", 0.0))

    if is_correct:
        new_internal = prev_internal + K_FACTOR * (1.0 - prev_internal) * difficulty_weight
    else:
        new_internal = prev_internal - K_FACTOR * prev_internal * difficulty_weight * WRONG_PENALTY_FACTOR

    new_internal = _clamp(new_internal)

    # ----- CRITICAL INVARIANT: shown_score never drops -----
    prev_shown: int = int(mastery.get("shown_score", 0))
    candidate_shown: int = math.floor(new_internal * 100)
    new_shown: int = max(prev_shown, candidate_shown)

    # ----- mastery label -----
    new_label: str = _mastery_label(new_shown)

    # ----- streak tracking -----
    streak_current: int = int(mastery.get("streak_current", 0))
    streak_best: int = int(mastery.get("streak_best", 0))

    if is_correct:
        streak_current += 1
        streak_best = max(streak_best, streak_current)
    else:
        streak_current = 0

    # ----- attempt counters -----
    total_attempts: int = int(mastery.get("total_attempts", 0)) + 1
    correct_attempts: int = int(mastery.get("correct_attempts", 0)) + (1 if is_correct else 0)

    # ----- mastered_at -----
    mastered_at = mastery.get("mastered_at")
    if new_shown >= 80 and mastered_at is None:
        mastered_at = now

    # ----- spaced repetition scheduling -----
    review_interval_days: int = int(mastery.get("review_interval_days", DEFAULT_REVIEW_INTERVAL_DAYS))

    if new_shown >= 80:
        # Double interval on each mastered write, cap at MAX
        review_interval_days = min(review_interval_days * 2, MAX_REVIEW_INTERVAL_DAYS)

    next_review_at = now + timedelta(days=review_interval_days)

    # ----- write back -----
    updated_mastery = {
        "user_id": user_id,
        "concept_id": concept_id,
        "internal_score": new_internal,
        "shown_score": new_shown,
        "mastery_label": new_label,
        "total_attempts": total_attempts,
        "correct_attempts": correct_attempts,
        "streak_current": streak_current,
        "streak_best": streak_best,
        "review_interval_days": review_interval_days,
        "next_review_at": next_review_at,
        "mastered_at": mastered_at,
        "created_at": mastery.get("created_at", now),
        "updated_at": now,
    }

    transaction.set(mastery_ref, updated_mastery)

    logger.info(
        "Mastery updated for user=%s concept=%s: internal=%.4f shown=%d label=%s streak=%d",
        user_id,
        concept_id,
        new_internal,
        new_shown,
        new_label,
        streak_current,
    )


# ---------------------------------------------------------------------------
# Cloud Function entry point (Firebase Functions v2)
# ---------------------------------------------------------------------------


@firestore_fn.on_document_created(document="users/{userId}/attempts/{attemptId}")
def mastery_recompute(
    event: firestore_fn.Event[firestore_fn.DocumentSnapshot],
) -> None:
    """Recompute mastery for a concept after a new attempt is recorded.

    Triggered by Firestore ``onCreate`` on
    ``users/{userId}/attempts/{attemptId}``.

    The entire mastery update runs inside a Firestore transaction so that
    concurrent attempts for the same concept are serialised correctly.
    """

    try:
        # --- extract path params and attempt data ---
        user_id: str = event.params["userId"]
        attempt_data: dict = event.data.to_dict() or {}

        concept_id: str | None = attempt_data.get("concept_id")
        if not concept_id:
            logger.error(
                "Attempt %s for user %s is missing concept_id -- skipping.",
                event.params.get("attemptId"),
                user_id,
            )
            return

        logger.info(
            "Processing attempt %s for user=%s concept=%s",
            event.params.get("attemptId"),
            user_id,
            concept_id,
        )

        mastery_ref = db.document(f"users/{user_id}/mastery/{concept_id}")

        # --- run transactional update ---
        transaction = db.transaction()

        @firestore.transactional
        def _run(txn: firestore.Transaction) -> None:
            _update_mastery_in_transaction(txn, mastery_ref, attempt_data, user_id, concept_id)

        _run(transaction)

    except Exception:
        logger.exception("mastery_recompute failed")
        raise
