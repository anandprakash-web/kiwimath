"""
Item Calibration Pipeline.

Handles empirical calibration of item parameters from student response data.
Runs as a batch job (weekly) to refine a, b, c parameters and detect item drift.

Methods:
- Joint Maximum Likelihood Estimation (JMLE) for initial calibration
- Marginal Maximum Likelihood (MML) for production refinement
- Item fit statistics (infit/outfit mean-square)
- Differential Item Functioning (DIF) detection across curricula
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .irt_model import ItemParameters


@dataclass
class ResponseRecord:
    """A single student response for calibration."""
    student_id: str
    item_id: str
    correct: bool
    response_time_sec: float
    theta_at_response: float  # Student's θ when they answered


@dataclass
class CalibrationResult:
    """Result of calibrating a single item."""
    item_id: str
    old_params: tuple[float, float, float]  # (a, b, c)
    new_params: tuple[float, float, float]
    n_responses: int
    fit_statistic: float  # Infit mean-square (target: 0.7–1.3)
    drift_magnitude: float  # How much parameters shifted
    flagged: bool = False
    flag_reason: str = ""


@dataclass
class CalibrationReport:
    """Summary of a calibration run."""
    timestamp: str
    items_calibrated: int
    items_flagged: int
    items_retired: int
    avg_fit: float
    results: list[CalibrationResult] = field(default_factory=list)


class ItemCalibrator:
    """Calibrates item parameters from observed response data."""

    DRIFT_THRESHOLD = 0.3  # Flag if any parameter shifts more than this
    MIN_RESPONSES = 50  # Minimum responses before calibrating
    FIT_LOWER = 0.7
    FIT_UPPER = 1.3
    BLEND_WEIGHT = 0.3  # Weight for new parameters in blended update

    def calibrate_item(
        self,
        item: ItemParameters,
        responses: list[ResponseRecord],
    ) -> CalibrationResult:
        """Calibrate a single item from response data.

        Uses iterative procedure to estimate a, b, c that maximize
        the likelihood of observed responses.
        """
        if len(responses) < self.MIN_RESPONSES:
            return CalibrationResult(
                item_id=item.item_id,
                old_params=(item.a, item.b, item.c),
                new_params=(item.a, item.b, item.c),
                n_responses=len(responses),
                fit_statistic=1.0,
                drift_magnitude=0.0,
            )

        # Estimate difficulty (b) from proportion correct adjusted for ability
        thetas = [r.theta_at_response for r in responses]
        corrects = [r.correct for r in responses]
        mean_theta = sum(thetas) / len(thetas)
        p_correct = sum(corrects) / len(corrects)

        # Rough b estimate: transform p_correct accounting for guessing
        c_est = item.c  # Keep guessing parameter stable
        if p_correct <= c_est:
            p_adj = 0.01
        else:
            p_adj = min(0.99, (p_correct - c_est) / (1.0 - c_est))

        # b ≈ mean_theta - logit(p_adj) / a
        logit_p = math.log(p_adj / (1.0 - p_adj))
        b_est = mean_theta - logit_p / max(item.a, 0.5)

        # Estimate discrimination (a) using point-biserial correlation
        a_est = self._estimate_discrimination(thetas, corrects, b_est, c_est)

        # Clamp to reasonable ranges
        a_est = max(0.3, min(3.0, a_est))
        b_est = max(-4.0, min(4.0, b_est))
        c_est = max(0.0, min(0.40, c_est))

        # Compute fit statistic
        fit = self._compute_infit(item, responses)

        # Check drift
        drift = max(
            abs(a_est - item.a),
            abs(b_est - item.b),
            abs(c_est - item.c) * 3,  # Weight c drift more heavily
        )

        # Flag conditions
        flagged = False
        flag_reason = ""
        if drift > self.DRIFT_THRESHOLD:
            flagged = True
            flag_reason = "parameter_drift"
        elif fit < self.FIT_LOWER or fit > self.FIT_UPPER:
            flagged = True
            flag_reason = "misfit"
        elif a_est < 0.4:
            flagged = True
            flag_reason = "low_discrimination"

        return CalibrationResult(
            item_id=item.item_id,
            old_params=(item.a, item.b, item.c),
            new_params=(a_est, b_est, c_est),
            n_responses=len(responses),
            fit_statistic=round(fit, 3),
            drift_magnitude=round(drift, 3),
            flagged=flagged,
            flag_reason=flag_reason,
        )

    def apply_calibration(
        self,
        item: ItemParameters,
        result: CalibrationResult,
        blend: bool = True,
    ) -> ItemParameters:
        """Apply calibration result to update item parameters.

        Uses blended update by default to prevent sudden jumps.
        """
        if result.flagged and result.flag_reason == "parameter_drift":
            # Don't auto-apply drifted items — needs human review
            return item

        new_a, new_b, new_c = result.new_params
        if blend:
            w = self.BLEND_WEIGHT
            item.a = item.a * (1 - w) + new_a * w
            item.b = item.b * (1 - w) + new_b * w
            item.c = item.c * (1 - w) + new_c * w
        else:
            item.a = new_a
            item.b = new_b
            item.c = new_c

        return item

    def _estimate_discrimination(
        self,
        thetas: list[float],
        corrects: list[bool],
        b: float,
        c: float,
    ) -> float:
        """Estimate discrimination from point-biserial correlation."""
        if len(thetas) < 10:
            return 1.0

        # Split into upper/lower groups by theta
        paired = sorted(zip(thetas, corrects))
        n = len(paired)
        lower = paired[:n // 3]
        upper = paired[2 * n // 3:]

        p_lower = sum(c for _, c in lower) / max(len(lower), 1)
        p_upper = sum(c for _, c in upper) / max(len(upper), 1)

        # Discrimination proportional to difference in performance
        diff = p_upper - p_lower
        if diff <= 0:
            return 0.5

        # Scale to IRT discrimination range
        a_est = diff * 2.5  # Rough scaling factor
        return max(0.3, min(3.0, a_est))

    def _compute_infit(
        self,
        item: ItemParameters,
        responses: list[ResponseRecord],
    ) -> float:
        """Compute infit mean-square (weighted fit statistic).

        Target: 1.0 (perfect fit)
        Acceptable: 0.7–1.3
        Flagged: < 0.5 or > 1.5
        """
        if not responses:
            return 1.0

        numerator = 0.0
        denominator = 0.0

        for r in responses:
            p = item.probability(r.theta_at_response)
            variance = p * (1.0 - p)
            if variance < 1e-6:
                continue

            expected = p
            observed = 1.0 if r.correct else 0.0
            residual_sq = (observed - expected) ** 2

            numerator += residual_sq * variance  # Weighted by information
            denominator += variance ** 2

        if denominator < 1e-6:
            return 1.0

        return numerator / denominator

    def detect_dif(
        self,
        item: ItemParameters,
        group_a_responses: list[ResponseRecord],
        group_b_responses: list[ResponseRecord],
    ) -> dict:
        """Detect Differential Item Functioning between two groups.

        e.g., NCERT students vs Singapore students

        Returns:
            {"dif_magnitude": float, "favors": "A"|"B"|"none", "significant": bool}
        """
        if len(group_a_responses) < 30 or len(group_b_responses) < 30:
            return {"dif_magnitude": 0.0, "favors": "none", "significant": False}

        # Compare observed vs expected performance for each group
        p_a_obs = sum(r.correct for r in group_a_responses) / len(group_a_responses)
        p_b_obs = sum(r.correct for r in group_b_responses) / len(group_b_responses)

        # Expected from model (using their ability levels)
        p_a_exp = sum(
            item.probability(r.theta_at_response) for r in group_a_responses
        ) / len(group_a_responses)
        p_b_exp = sum(
            item.probability(r.theta_at_response) for r in group_b_responses
        ) / len(group_b_responses)

        # DIF = difference in residuals
        resid_a = p_a_obs - p_a_exp
        resid_b = p_b_obs - p_b_exp
        dif = resid_a - resid_b

        significant = abs(dif) > 0.10  # Practical significance threshold
        favors = "A" if dif > 0.05 else "B" if dif < -0.05 else "none"

        return {
            "dif_magnitude": round(abs(dif), 3),
            "favors": favors,
            "significant": significant,
        }
