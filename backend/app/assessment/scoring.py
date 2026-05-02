"""
Scoring & Reporting — converts raw θ to KiwiScore and generates reports.

KiwiScore scale:
    KiwiScore = 200 + (θ × 30)
    Mean centered at Grade 3.5 (KiwiScore = 200)
    Each standard deviation = 30 points
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Percentile lookup (approximated from normal distribution)
# Maps KiwiScore ranges to approximate percentiles per grade
GRADE_NORMS = {
    1: {"p25": 110, "p50": 120, "p75": 130, "mean": 120, "sd": 15},
    2: {"p25": 140, "p50": 150, "p75": 160, "mean": 150, "sd": 15},
    3: {"p25": 170, "p50": 180, "p75": 190, "mean": 180, "sd": 15},
    4: {"p25": 200, "p50": 210, "p75": 220, "mean": 210, "sd": 15},
    5: {"p25": 230, "p50": 240, "p75": 250, "mean": 240, "sd": 15},
    6: {"p25": 260, "p50": 270, "p75": 280, "mean": 270, "sd": 15},
}


def theta_to_kiwiscore(theta: float) -> int:
    return int(round(200 + theta * 30))


def kiwiscore_to_theta(kiwiscore: int) -> float:
    return (kiwiscore - 200) / 30.0


def theta_to_grade_equivalent(theta: float) -> float:
    """Approximate grade equivalent from θ."""
    return round(3.5 + theta * 1.5, 1)


def kiwiscore_to_percentile(kiwiscore: int, grade: int) -> int:
    """Approximate percentile rank within grade cohort."""
    norms = GRADE_NORMS.get(grade, GRADE_NORMS[3])
    mean = norms["mean"]
    sd = norms["sd"]

    # Z-score relative to grade norms
    z = (kiwiscore - mean) / sd

    # Approximate percentile from z-score (using logistic approximation)
    import math
    percentile = int(round(100 / (1 + math.exp(-1.7 * z))))
    return max(1, min(99, percentile))


@dataclass
class DomainReport:
    """Report for a single domain."""
    domain: str
    theta: float
    se: float
    kiwiscore: int
    grade_equivalent: float
    percentile: Optional[int] = None
    status: str = "at_level"  # below_level | at_level | above_level

    @classmethod
    def from_assessment(
        cls, domain: str, theta: float, se: float, grade: int
    ) -> "DomainReport":
        ks = theta_to_kiwiscore(theta)
        ge = theta_to_grade_equivalent(theta)
        pct = kiwiscore_to_percentile(ks, grade)

        norms = GRADE_NORMS.get(grade, GRADE_NORMS[3])
        if ks < norms["p25"]:
            status = "below_level"
        elif ks > norms["p75"]:
            status = "above_level"
        else:
            status = "at_level"

        return cls(
            domain=domain,
            theta=round(theta, 3),
            se=round(se, 3),
            kiwiscore=ks,
            grade_equivalent=ge,
            percentile=pct,
            status=status,
        )


@dataclass
class FullAssessmentReport:
    """Complete assessment report for a student."""
    student_id: str
    grade: int
    curriculum: str
    overall_kiwiscore: int
    overall_grade_equivalent: float
    overall_percentile: int
    domains: list[DomainReport]
    strengths: list[str]
    growth_areas: list[str]
    recommended_track: str
    parent_summary: str

    @classmethod
    def from_domain_scores(
        cls,
        student_id: str,
        grade: int,
        curriculum: str,
        domain_results: dict[str, tuple[float, float]],  # domain -> (theta, se)
    ) -> "FullAssessmentReport":
        domains = []
        thetas = []

        for domain, (theta, se) in domain_results.items():
            report = DomainReport.from_assessment(domain, theta, se, grade)
            domains.append(report)
            thetas.append(theta)

        # Overall = average of domain thetas
        overall_theta = sum(thetas) / max(len(thetas), 1)
        overall_ks = theta_to_kiwiscore(overall_theta)
        overall_ge = theta_to_grade_equivalent(overall_theta)
        overall_pct = kiwiscore_to_percentile(overall_ks, grade)

        # Identify strengths and growth areas
        sorted_domains = sorted(domains, key=lambda d: d.theta, reverse=True)
        strengths = [d.domain for d in sorted_domains if d.status == "above_level"]
        growth_areas = [d.domain for d in sorted_domains if d.status == "below_level"]

        if not strengths and sorted_domains:
            strengths = [sorted_domains[0].domain]
        if not growth_areas and sorted_domains:
            growth_areas = [sorted_domains[-1].domain]

        # Determine track
        n_below = sum(1 for d in domains if d.status == "below_level")
        n_above = sum(1 for d in domains if d.status == "above_level")
        if n_below >= 3:
            track = "foundation"
        elif n_above >= 3:
            track = "accelerate"
        else:
            track = "school"

        # Parent-friendly summary
        summary = _build_parent_summary(
            overall_ks, overall_ge, grade, strengths, growth_areas, track
        )

        return cls(
            student_id=student_id,
            grade=grade,
            curriculum=curriculum,
            overall_kiwiscore=overall_ks,
            overall_grade_equivalent=overall_ge,
            overall_percentile=overall_pct,
            domains=domains,
            strengths=strengths,
            growth_areas=growth_areas,
            recommended_track=track,
            parent_summary=summary,
        )

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "grade": self.grade,
            "curriculum": self.curriculum,
            "overall": {
                "kiwiscore": self.overall_kiwiscore,
                "grade_equivalent": self.overall_grade_equivalent,
                "percentile": self.overall_percentile,
            },
            "domains": [
                {
                    "domain": d.domain,
                    "kiwiscore": d.kiwiscore,
                    "grade_equivalent": d.grade_equivalent,
                    "percentile": d.percentile,
                    "status": d.status,
                    "se": d.se,
                }
                for d in self.domains
            ],
            "strengths": self.strengths,
            "growth_areas": self.growth_areas,
            "recommended_track": self.recommended_track,
            "parent_summary": self.parent_summary,
        }


def _build_parent_summary(
    kiwiscore: int,
    grade_equiv: float,
    grade: int,
    strengths: list[str],
    growth_areas: list[str],
    track: str,
) -> str:
    """Generate a parent-friendly summary paragraph."""
    # Grade comparison
    if grade_equiv >= grade + 0.5:
        level_msg = f"performing above Grade {grade} level (at Grade {grade_equiv} equivalent)"
    elif grade_equiv <= grade - 0.5:
        level_msg = f"currently working at Grade {grade_equiv} level"
    else:
        level_msg = f"right on track for Grade {grade}"

    # Strengths
    strength_str = " and ".join(s.replace("_", " ").title() for s in strengths[:2])

    # Growth areas
    growth_str = " and ".join(g.replace("_", " ").title() for g in growth_areas[:2])

    # Track recommendation
    track_msgs = {
        "foundation": "We recommend focusing on building strong foundations before moving ahead.",
        "school": "The focus should be on keeping pace with grade-level material.",
        "accelerate": "Your child is ready for more challenging material!",
    }

    return (
        f"Your child is {level_msg} with a KiwiScore of {kiwiscore}. "
        f"Strongest in: {strength_str}. "
        f"Area to focus on: {growth_str}. "
        f"{track_msgs.get(track, '')}"
    )
