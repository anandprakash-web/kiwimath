"""Revisit scheduler Cloud Function for Kiwimath.

Firestore trigger that fires when a mastery document is created or updated at
``users/{userId}/mastery/{conceptId}``.  It inspects the mastery state and
decides whether to create (or bump) a revisit document so the child is nudged
to practise the concept again.

Revisit reasons
---------------
* **spaced_repetition** -- ``next_review_at`` is in the past.
* **decay_threshold** -- ``internal_score`` has silently dropped below 0.5
  while ``shown_score`` still shows >= 50 (invisible decay).
* **mastery_check** -- the child just reached "mastered" for the first time;
  schedule a verification revisit in 3 days.

Anti-spam
---------
* If an active revisit already exists for the same reason, ``nudge_count`` is
  incremented (capped at 3).  Once the cap is reached no further revisits are
  created for that reason -- we stop pushing.
* Revisits expire 30 days after creation.

Priority (lower = higher)
--------------------------
1. prerequisite_review (blocks downstream -- assigned externally, not here)
2. decay_threshold
3. spaced_repetition
4. mastery_check
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import firebase_admin
from firebase_admin import firestore as admin_firestore
from firebase_functions import firestore_fn
from google.cloud import firestore  # type: ignore[attr-defined]

logger = logging.getLogger("kiwimath.revisit_scheduler")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NUDGE_CAP: int = 3
REVISIT_EXPIRY_DAYS: int = 30
MASTERY_CHECK_DELAY_DAYS: int = 3

REASON_PRIORITY: dict[str, int] = {
    "prerequisite_review": 1,
    "decay_threshold": 2,
    "spaced_repetition": 3,
    "mastery_check": 4,
}

# ---------------------------------------------------------------------------
# Firebase app initialisation (idempotent)
# ---------------------------------------------------------------------------

if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = admin_firestore.client()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _build_revisit(
    user_id: str,
    concept_id: str,
    reason: str,
    shown_score: int,
    mastery_label: str,
) -> dict[str, Any]:
    """Build a fresh RevisitDue document."""
    now = _now_utc()
    return {
        "user_id": user_id,
        "concept_id": concept_id,
        "reason": reason,
        "priority": REASON_PRIORITY.get(reason, 5),
        "is_active": True,
        "nudge_count": 0,
        "current_shown_score": shown_score,
        "current_mastery_label": mastery_label,
        "created_at": now,
        "expires_at": now + timedelta(days=REVISIT_EXPIRY_DAYS),
    }


def _upsert_revisit(
    user_id: str,
    concept_id: str,
    reason: str,
    shown_score: int,
    mastery_label: str,
) -> None:
    """Create a revisit or bump nudge_count on an existing one.

    Uses a Firestore transaction to avoid races between concurrent mastery
    updates for the same concept.
    """

    revisit_ref = db.document(f"users/{user_id}/revisits/{concept_id}_{reason}")

    transaction = db.transaction()

    @firestore.transactional
    def _run(txn: firestore.Transaction) -> None:
        snapshot = revisit_ref.get(transaction=txn)

        if snapshot.exists:
            existing = snapshot.to_dict()

            # Only bump active revisits for the *same* reason.
            if existing.get("is_active") and existing.get("reason") == reason:
                current_nudge: int = int(existing.get("nudge_count", 0))
                if current_nudge >= NUDGE_CAP:
                    logger.info(
                        "Nudge cap reached for user=%s concept=%s reason=%s -- skipping.",
                        user_id,
                        concept_id,
                        reason,
                    )
                    return

                txn.update(revisit_ref, {
                    "nudge_count": current_nudge + 1,
                    "current_shown_score": shown_score,
                    "current_mastery_label": mastery_label,
                })
                logger.info(
                    "Bumped nudge_count to %d for user=%s concept=%s reason=%s",
                    current_nudge + 1,
                    user_id,
                    concept_id,
                    reason,
                )
                return

        # No active revisit for this reason -- create one.
        revisit_doc = _build_revisit(user_id, concept_id, reason, shown_score, mastery_label)
        txn.set(revisit_ref, revisit_doc)
        logger.info(
            "Created revisit for user=%s concept=%s reason=%s priority=%d",
            user_id,
            concept_id,
            reason,
            revisit_doc["priority"],
        )

    _run(transaction)


# ---------------------------------------------------------------------------
# Condition checkers
# ---------------------------------------------------------------------------


def _check_spaced_repetition(mastery: dict) -> bool:
    """Return True if next_review_at exists and is in the past."""
    next_review = mastery.get("next_review_at")
    if next_review is None:
        return False
    if isinstance(next_review, datetime):
        return next_review <= _now_utc()
    return False


def _check_decay_threshold(mastery: dict) -> bool:
    """Return True if internal score has silently decayed below 0.5
    while shown_score still presents >= 50."""
    internal: float = float(mastery.get("internal_score", 0.0))
    shown: int = int(mastery.get("shown_score", 0))
    return internal < 0.5 and shown >= 50


def _check_mastery_achieved(mastery: dict) -> bool:
    """Return True if the child just reached mastered for the first time.

    We detect this by checking ``mastery_label == "mastered"`` AND
    ``mastered_at`` is very recent (within the last 60 seconds), which
    effectively means this is the write that set it.
    """
    if mastery.get("mastery_label") != "mastered":
        return False

    mastered_at = mastery.get("mastered_at")
    if mastered_at is None:
        return False

    if isinstance(mastered_at, datetime):
        elapsed = _now_utc() - mastered_at
        return elapsed.total_seconds() < 60

    return False


# ---------------------------------------------------------------------------
# Cloud Function entry point (Firebase Functions v2)
# ---------------------------------------------------------------------------


@firestore_fn.on_document_written(document="users/{userId}/mastery/{conceptId}")
def revisit_scheduler(
    event: firestore_fn.Event[firestore_fn.Change[firestore_fn.DocumentSnapshot]],
) -> None:
    """Evaluate revisit conditions after a mastery document is written.

    Triggered by Firestore ``onWrite`` on
    ``users/{userId}/mastery/{conceptId}``.

    The function is idempotent: re-running it for the same mastery state will
    either no-op (nudge cap reached / revisit already exists) or safely bump
    the nudge counter.
    """

    try:
        after_snapshot = event.data.after
        if after_snapshot is None or not after_snapshot.exists:
            logger.info("Mastery document deleted -- nothing to schedule.")
            return

        mastery: dict = after_snapshot.to_dict() or {}
        user_id: str = event.params["userId"]
        concept_id: str = event.params["conceptId"]
        shown_score: int = int(mastery.get("shown_score", 0))
        mastery_label: str = str(mastery.get("mastery_label", "new"))

        logger.info(
            "Evaluating revisit conditions for user=%s concept=%s shown=%d label=%s",
            user_id,
            concept_id,
            shown_score,
            mastery_label,
        )

        # --- spaced_repetition ---
        if _check_spaced_repetition(mastery):
            logger.info("Condition met: spaced_repetition for user=%s concept=%s", user_id, concept_id)
            _upsert_revisit(user_id, concept_id, "spaced_repetition", shown_score, mastery_label)

        # --- decay_threshold ---
        if _check_decay_threshold(mastery):
            logger.info("Condition met: decay_threshold for user=%s concept=%s", user_id, concept_id)
            _upsert_revisit(user_id, concept_id, "decay_threshold", shown_score, mastery_label)

        # --- mastery_check ---
        if _check_mastery_achieved(mastery):
            logger.info("Condition met: mastery_check for user=%s concept=%s", user_id, concept_id)
            _upsert_revisit(user_id, concept_id, "mastery_check", shown_score, mastery_label)

    except Exception:
        logger.exception("revisit_scheduler failed")
        raise
