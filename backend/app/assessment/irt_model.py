"""
3-Parameter Logistic IRT Model.

Implements the core psychometric model:
    P(correct | θ, a, b, c) = c + (1 - c) / (1 + exp(-a * (θ - b)))

Where:
    θ = student ability (latent trait)
    a = item discrimination (how sharply the item differentiates)
    b = item difficulty (ability level at midpoint)
    c = pseudo-guessing parameter (lower asymptote)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ItemParameters:
    """IRT parameters for a single item."""
    item_id: str
    a: float  # discrimination: typical range 0.5–2.5
    b: float  # difficulty: typical range -3.0–+3.0
    c: float  # guessing: typical range 0.15–0.25 for 4-choice MCQ

    # Metadata for selection constraints
    domain: str = ""
    subdomain: str = ""
    curriculum_tags: list[str] = field(default_factory=list)
    grade_range: tuple[int, int] = (1, 6)
    exposure_count: int = 0
    state: str = "active"  # field_test | active | retired

    def probability(self, theta: float) -> float:
        """P(correct | θ) under the 3PL model."""
        exponent = -self.a * (theta - self.b)
        # Clamp to prevent overflow
        exponent = max(-50.0, min(50.0, exponent))
        return self.c + (1.0 - self.c) / (1.0 + math.exp(exponent))

    def information(self, theta: float) -> float:
        """Fisher information at ability θ.

        I(θ) = a² * (P - c)² / ((1 - c)² * P * Q)
        where Q = 1 - P
        """
        p = self.probability(theta)
        q = 1.0 - p
        if q < 1e-10 or p < 1e-10:
            return 0.0
        numerator = (self.a ** 2) * ((p - self.c) ** 2)
        denominator = ((1.0 - self.c) ** 2) * p * q
        if denominator < 1e-10:
            return 0.0
        return numerator / denominator

    def log_likelihood(self, theta: float, correct: bool) -> float:
        """Log-likelihood of the response given θ."""
        p = self.probability(theta)
        p = max(1e-10, min(1.0 - 1e-10, p))
        if correct:
            return math.log(p)
        return math.log(1.0 - p)


@dataclass
class AbilityEstimate:
    """Current estimate of a student's ability in a domain."""
    theta: float = 0.0
    se: float = 3.0  # Standard error — starts high (uncertain)
    n_items: int = 0
    responses: list[tuple[str, bool, float]] = field(default_factory=list)
    # (item_id, correct, response_time_sec)

    @property
    def kiwiscore(self) -> int:
        """Convert θ to KiwiScore (vertical scale: mean=200, SD=30)."""
        return int(round(200 + self.theta * 30))

    @property
    def grade_equivalent(self) -> float:
        """Approximate grade equivalent from θ."""
        # θ=0 ~ Grade 3.5, each unit ~ 1.5 grades
        return round(3.5 + self.theta * 1.5, 1)

    @property
    def is_converged(self) -> bool:
        """Whether the estimate has converged (SE below threshold)."""
        return self.se < 0.30


def estimate_ability_eap(
    items: list[ItemParameters],
    responses: list[bool],
    prior_mean: float = 0.0,
    prior_sd: float = 1.5,
    n_quadrature: int = 61,
) -> tuple[float, float]:
    """Estimate ability using Expected A Posteriori (EAP).

    Uses Gaussian quadrature over the ability range with a normal prior.

    Returns:
        (theta_estimate, standard_error)
    """
    # Quadrature points from -4 to +4
    lo, hi = -4.0, 4.0
    step = (hi - lo) / (n_quadrature - 1)
    points = [lo + i * step for i in range(n_quadrature)]

    # Compute posterior at each quadrature point
    log_posteriors = []
    for theta in points:
        # Log prior: normal(prior_mean, prior_sd)
        log_prior = -0.5 * ((theta - prior_mean) / prior_sd) ** 2

        # Log likelihood: product over items
        log_lik = 0.0
        for item, correct in zip(items, responses):
            log_lik += item.log_likelihood(theta, correct)

        log_posteriors.append(log_prior + log_lik)

    # Normalize (log-sum-exp trick for numerical stability)
    max_lp = max(log_posteriors)
    posteriors = [math.exp(lp - max_lp) for lp in log_posteriors]
    total = sum(posteriors) * step
    if total < 1e-30:
        return prior_mean, prior_sd

    posteriors = [p / total for p in posteriors]

    # EAP = E[θ | data]
    theta_hat = sum(p * t * step for p, t in zip(posteriors, points))

    # SE = sqrt(Var[θ | data])
    variance = sum(p * (t - theta_hat) ** 2 * step for p, t in zip(posteriors, points))
    se = math.sqrt(max(variance, 1e-6))

    return theta_hat, se


def compute_standard_error(
    theta: float,
    items: list[ItemParameters],
) -> float:
    """Compute SE from test information: SE = 1/sqrt(sum(I(θ)))."""
    total_info = sum(item.information(theta) for item in items)
    if total_info < 1e-10:
        return 3.0
    return 1.0 / math.sqrt(total_info)
