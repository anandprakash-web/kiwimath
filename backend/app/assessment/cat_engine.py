"""
Computerized Adaptive Testing (CAT) Engine.

Implements the full CAT loop:
1. Initialize ability estimate
2. Select optimal item (maximum Fisher information with constraints)
3. Administer item
4. Update ability estimate (EAP)
5. Check stopping rules
6. Repeat or terminate

Supports:
- Domain-specific assessment (5 math domains)
- Content balancing across subdomains
- Exposure control (Sympson-Hetter)
- Age-appropriate session limits
- Field test item seeding (unscored)
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .irt_model import (
    AbilityEstimate,
    ItemParameters,
    estimate_ability_eap,
)
from .item_bank import ItemBank


class StopReason(str, Enum):
    CONVERGED = "converged"         # SE < threshold
    MAX_ITEMS = "max_items"         # Hit item limit
    TIME_LIMIT = "time_limit"       # Session too long
    NO_ITEMS = "no_items"           # Item bank exhausted
    USER_EXIT = "user_exit"         # Student quit
    NOT_STOPPED = "not_stopped"     # Assessment still running


class Domain(str, Enum):
    NUMBERS = "numbers"
    ARITHMETIC = "arithmetic"
    FRACTIONS = "fractions"
    GEOMETRY = "geometry"
    MEASUREMENT = "measurement"


# Grade-appropriate session limits
GRADE_LIMITS = {
    1: {"max_items": 12, "max_time_min": 12},
    2: {"max_items": 12, "max_time_min": 12},
    3: {"max_items": 15, "max_time_min": 15},
    4: {"max_items": 15, "max_time_min": 15},
    5: {"max_items": 20, "max_time_min": 18},
    6: {"max_items": 20, "max_time_min": 18},
}

DEFAULT_SE_THRESHOLD = 0.30
MIN_ITEMS = 8
FIELD_TEST_RATIO = 0.10  # Seed ~10% field test items


@dataclass
class CATSession:
    """State of an active CAT session."""
    session_id: str
    student_id: str
    domain: Domain
    grade: int
    curriculum: Optional[str] = None

    # Ability tracking
    ability: AbilityEstimate = field(default_factory=AbilityEstimate)

    # Session state
    items_administered: list[ItemParameters] = field(default_factory=list)
    responses: list[bool] = field(default_factory=list)
    response_times: list[float] = field(default_factory=list)
    field_test_ids: set[str] = field(default_factory=set)

    # Timing
    start_time: float = 0.0
    stop_reason: StopReason = StopReason.NOT_STOPPED

    # Subdomain coverage tracking
    subdomain_counts: dict[str, int] = field(default_factory=dict)

    @property
    def n_scored_items(self) -> int:
        """Number of scored (non-field-test) items administered."""
        return sum(
            1 for item in self.items_administered
            if item.item_id not in self.field_test_ids
        )

    @property
    def elapsed_minutes(self) -> float:
        if self.start_time == 0:
            return 0.0
        return (time.time() - self.start_time) / 60.0

    @property
    def is_active(self) -> bool:
        return self.stop_reason == StopReason.NOT_STOPPED


class CATEngine:
    """Core CAT engine — manages adaptive item selection and scoring."""

    def __init__(self, item_bank: ItemBank):
        self.item_bank = item_bank
        self._sessions: dict[str, CATSession] = {}

    def start_session(
        self,
        student_id: str,
        domain: Domain,
        grade: int,
        curriculum: Optional[str] = None,
        prior_theta: Optional[float] = None,
    ) -> CATSession:
        """Start a new CAT assessment session."""
        session = CATSession(
            session_id=str(uuid.uuid4()),
            student_id=student_id,
            domain=domain,
            grade=grade,
            curriculum=curriculum,
            start_time=time.time(),
        )

        # Set prior if available
        if prior_theta is not None:
            session.ability.theta = prior_theta
            session.ability.se = 1.5  # Still uncertain but not starting blind

        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[CATSession]:
        return self._sessions.get(session_id)

    def select_next_item(
        self,
        session: CATSession,
        exclude_ids: Optional[set[str]] = None,
    ) -> Optional[ItemParameters]:
        """Select the optimal next item using maximum information with constraints.

        Selection strategy:
        1. Get eligible items (domain, curriculum, grade, not seen)
        2. Compute Fisher information at current θ for each
        3. Apply content balancing bonus for underrepresented subdomains
        4. Apply exposure penalty for overexposed items
        5. Occasionally seed a field test item (unscored)
        6. Return highest-scoring item

        Parameters
        ----------
        session:
            Active CAT session.
        exclude_ids:
            Additional item IDs to exclude (e.g. from question history
            to prevent repetition on retests).
        """
        if not session.is_active:
            return None

        # Check if we should seed a field test item
        if (
            session.n_scored_items > 0
            and session.n_scored_items % int(1 / FIELD_TEST_RATIO) == 0
        ):
            ft_items = self.item_bank.get_field_test_items(
                domain=session.domain.value, n=1
            )
            if ft_items:
                item = ft_items[0]
                session.field_test_ids.add(item.item_id)
                return item

        # Get eligible scored items — merge session-seen IDs with
        # any externally-provided exclusion set (e.g. prior diagnostics).
        seen_ids = {item.item_id for item in session.items_administered}
        if exclude_ids:
            seen_ids = seen_ids | exclude_ids
        candidates = self.item_bank.get_eligible_items(
            domain=session.domain.value,
            curriculum=session.curriculum,
            grade=session.grade,
            exclude_ids=seen_ids,
            student_id=session.student_id,
            state="active",
        )

        if not candidates:
            return None

        theta = session.ability.theta
        best_item = None
        best_score = -1.0

        for item in candidates:
            # Base score: Fisher information at current θ
            info = item.information(theta)

            # Content balance bonus: prefer subdomains we haven't covered
            subdomain_count = session.subdomain_counts.get(item.subdomain, 0)
            total_items = max(len(session.items_administered), 1)
            balance_bonus = 1.0 / (1.0 + subdomain_count / total_items)

            # Exposure penalty: reduce score for overexposed items
            exposure_penalty = 1.0
            if item.exposure_count > 100:
                exposure_penalty = max(0.3, 1.0 - item.exposure_count / 5000)

            score = info * balance_bonus * exposure_penalty

            if score > best_score:
                best_score = score
                best_item = item

        return best_item

    def record_response(
        self,
        session: CATSession,
        item: ItemParameters,
        correct: bool,
        response_time_sec: float,
    ) -> dict:
        """Record a response and update ability estimate.

        Returns:
            dict with updated theta, se, kiwiscore, stop_reason, etc.
        """
        # Record in session
        session.items_administered.append(item)
        session.responses.append(correct)
        session.response_times.append(response_time_sec)
        session.ability.responses.append(
            (item.item_id, correct, response_time_sec)
        )

        # Track subdomain coverage
        if item.subdomain:
            session.subdomain_counts[item.subdomain] = (
                session.subdomain_counts.get(item.subdomain, 0) + 1
            )

        # Record in item bank
        self.item_bank.record_exposure(item.item_id, session.student_id)
        self.item_bank.record_response(item.item_id, correct, response_time_sec)

        # Skip ability update for field test items
        is_field_test = item.item_id in session.field_test_ids
        if not is_field_test:
            # Get only scored items/responses
            scored_items = [
                it for it in session.items_administered
                if it.item_id not in session.field_test_ids
            ]
            scored_responses = [
                r for it, r in zip(session.items_administered, session.responses)
                if it.item_id not in session.field_test_ids
            ]

            # Update ability via EAP
            theta, se = estimate_ability_eap(
                items=scored_items,
                responses=scored_responses,
                prior_mean=0.0,
                prior_sd=1.5,
            )
            session.ability.theta = theta
            session.ability.se = se
            session.ability.n_items = len(scored_items)

        # Check stopping rules
        stop_reason = self._check_stop(session)
        if stop_reason != StopReason.NOT_STOPPED:
            session.stop_reason = stop_reason

        return {
            "theta": session.ability.theta,
            "se": session.ability.se,
            "kiwiscore": session.ability.kiwiscore,
            "n_items": session.n_scored_items,
            "is_field_test": is_field_test,
            "correct": correct,
            "stop_reason": stop_reason.value,
            "converged": session.ability.is_converged,
        }

    def _check_stop(self, session: CATSession) -> StopReason:
        """Check all stopping rules."""
        limits = GRADE_LIMITS.get(session.grade, GRADE_LIMITS[6])

        # 1. Convergence (SE below threshold) — only after minimum items
        if (
            session.n_scored_items >= MIN_ITEMS
            and session.ability.se < DEFAULT_SE_THRESHOLD
        ):
            return StopReason.CONVERGED

        # 2. Maximum items reached
        if session.n_scored_items >= limits["max_items"]:
            return StopReason.MAX_ITEMS

        # 3. Time limit
        if session.elapsed_minutes >= limits["max_time_min"]:
            return StopReason.TIME_LIMIT

        # 4. No more eligible items
        seen_ids = {item.item_id for item in session.items_administered}
        remaining = self.item_bank.get_eligible_items(
            domain=session.domain.value,
            curriculum=session.curriculum,
            grade=session.grade,
            exclude_ids=seen_ids,
            student_id=session.student_id,
        )
        if not remaining:
            return StopReason.NO_ITEMS

        return StopReason.NOT_STOPPED

    def get_result(self, session: CATSession) -> dict:
        """Get final assessment result for a completed session."""
        scored_items = [
            it for it in session.items_administered
            if it.item_id not in session.field_test_ids
        ]
        scored_responses = [
            r for it, r in zip(session.items_administered, session.responses)
            if it.item_id not in session.field_test_ids
        ]

        # Compute accuracy
        n_correct = sum(scored_responses)
        accuracy = n_correct / max(len(scored_responses), 1)

        # Compute avg response time
        scored_times = [
            t for it, t in zip(session.items_administered, session.response_times)
            if it.item_id not in session.field_test_ids
        ]
        avg_time = sum(scored_times) / max(len(scored_times), 1)

        return {
            "session_id": session.session_id,
            "student_id": session.student_id,
            "domain": session.domain.value,
            "curriculum": session.curriculum,
            "grade": session.grade,
            "theta": round(session.ability.theta, 3),
            "se": round(session.ability.se, 3),
            "kiwiscore": session.ability.kiwiscore,
            "grade_equivalent": session.ability.grade_equivalent,
            "n_items": len(scored_responses),
            "n_correct": n_correct,
            "accuracy": round(accuracy, 3),
            "avg_response_time_sec": round(avg_time, 1),
            "stop_reason": session.stop_reason.value,
            "converged": session.ability.is_converged,
            "subdomain_breakdown": session.subdomain_counts,
            "elapsed_minutes": round(session.elapsed_minutes, 1),
        }

    def end_session(self, session_id: str, reason: StopReason = StopReason.USER_EXIT) -> Optional[dict]:
        """End a session early and return results."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        if session.is_active:
            session.stop_reason = reason
        return self.get_result(session)
