"""
Learning Path Recommendation Engine.

Takes diagnostic assessment results and generates a personalized learning path
based on:
1. Prerequisite skill graph (topological dependencies)
2. Domain-level gaps vs grade expectations
3. Student's current track (foundation / school / accelerate)
4. Curriculum alignment
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Track(str, Enum):
    FOUNDATION = "foundation"   # >1 grade behind — fill basics
    SCHOOL = "school"           # At grade level — curriculum-aligned
    ACCELERATE = "accelerate"   # Above grade — push ahead


@dataclass
class SkillNode:
    """A single skill in the prerequisite graph."""
    skill_id: str
    name: str
    domain: str
    grade_level: float  # Expected grade level (e.g., 2.5)
    prerequisites: list[str] = field(default_factory=list)
    curriculum_tags: list[str] = field(default_factory=list)


@dataclass
class PathRecommendation:
    """A single recommended skill/topic to work on."""
    skill_id: str
    name: str
    domain: str
    priority: int  # 1 = highest
    reason: str  # "prerequisite_gap", "grade_level_gap", "accelerate"
    estimated_sessions: int = 3  # How many practice sessions to master
    track: Track = Track.SCHOOL


@dataclass
class LearningPath:
    """Complete learning path for a student."""
    student_id: str
    overall_track: Track
    grade: int
    curriculum: str
    recommendations: list[PathRecommendation] = field(default_factory=list)
    focus_domains: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def foundation_items(self) -> list[PathRecommendation]:
        return [r for r in self.recommendations if r.track == Track.FOUNDATION]

    @property
    def school_items(self) -> list[PathRecommendation]:
        return [r for r in self.recommendations if r.track == Track.SCHOOL]

    @property
    def accelerate_items(self) -> list[PathRecommendation]:
        return [r for r in self.recommendations if r.track == Track.ACCELERATE]

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "overall_track": self.overall_track.value,
            "grade": self.grade,
            "curriculum": self.curriculum,
            "focus_domains": self.focus_domains,
            "summary": self.summary,
            "foundation": [
                {"skill": r.skill_id, "name": r.name, "domain": r.domain,
                 "priority": r.priority, "sessions": r.estimated_sessions}
                for r in self.foundation_items
            ],
            "school": [
                {"skill": r.skill_id, "name": r.name, "domain": r.domain,
                 "priority": r.priority, "sessions": r.estimated_sessions}
                for r in self.school_items
            ],
            "accelerate": [
                {"skill": r.skill_id, "name": r.name, "domain": r.domain,
                 "priority": r.priority, "sessions": r.estimated_sessions}
                for r in self.accelerate_items
            ],
            "total_sessions_estimated": sum(
                r.estimated_sessions for r in self.recommendations
            ),
        }


# Grade-level expectations: domain -> expected θ per grade
GRADE_EXPECTATIONS = {
    "numbers":     {1: -2.0, 2: -1.3, 3: -0.5, 4: 0.2, 5: 0.8, 6: 1.5},
    "arithmetic":  {1: -2.5, 2: -1.5, 3: -0.7, 4: 0.0, 5: 0.7, 6: 1.3},
    "fractions":   {1: -3.0, 2: -2.5, 3: -1.5, 4: -0.5, 5: 0.3, 6: 1.0},
    "geometry":    {1: -2.0, 2: -1.2, 3: -0.5, 4: 0.2, 5: 0.8, 6: 1.4},
    "measurement": {1: -2.0, 2: -1.3, 3: -0.6, 4: 0.1, 5: 0.7, 6: 1.2},
}


# Prerequisite graph — skill dependencies
PREREQUISITE_GRAPH: dict[str, SkillNode] = {
    # Numbers
    "counting_10": SkillNode("counting_10", "Count to 10", "numbers", 1.0),
    "counting_100": SkillNode("counting_100", "Count to 100", "numbers", 1.5, ["counting_10"]),
    "place_value_2": SkillNode("place_value_2", "2-digit place value", "numbers", 2.0, ["counting_100"]),
    "place_value_3": SkillNode("place_value_3", "3-digit place value", "numbers", 2.5, ["place_value_2"]),
    "place_value_4": SkillNode("place_value_4", "4+ digit place value", "numbers", 3.5, ["place_value_3"]),
    "comparison": SkillNode("comparison", "Compare numbers", "numbers", 2.0, ["place_value_2"]),
    "rounding": SkillNode("rounding", "Rounding numbers", "numbers", 3.0, ["place_value_3"]),
    "number_patterns": SkillNode("number_patterns", "Number patterns", "numbers", 3.5, ["place_value_3"]),

    # Arithmetic
    "addition_basic": SkillNode("addition_basic", "Addition within 20", "arithmetic", 1.0, ["counting_10"]),
    "subtraction_basic": SkillNode("subtraction_basic", "Subtraction within 20", "arithmetic", 1.5, ["addition_basic"]),
    "addition_2digit": SkillNode("addition_2digit", "2-digit addition", "arithmetic", 2.0, ["addition_basic", "place_value_2"]),
    "subtraction_2digit": SkillNode("subtraction_2digit", "2-digit subtraction", "arithmetic", 2.5, ["subtraction_basic", "place_value_2"]),
    "multiplication_facts": SkillNode("multiplication_facts", "Multiplication tables", "arithmetic", 3.0, ["addition_2digit"]),
    "division_basic": SkillNode("division_basic", "Basic division", "arithmetic", 3.5, ["multiplication_facts"]),
    "multi_step": SkillNode("multi_step", "Multi-step problems", "arithmetic", 4.0, ["addition_2digit", "subtraction_2digit", "multiplication_facts"]),
    "order_of_ops": SkillNode("order_of_ops", "Order of operations", "arithmetic", 5.0, ["multi_step"]),

    # Fractions
    "fraction_concept": SkillNode("fraction_concept", "Fraction concepts", "fractions", 3.0, ["division_basic"]),
    "fraction_compare": SkillNode("fraction_compare", "Compare fractions", "fractions", 3.5, ["fraction_concept"]),
    "fraction_add": SkillNode("fraction_add", "Add/subtract fractions", "fractions", 4.0, ["fraction_compare"]),
    "fraction_multiply": SkillNode("fraction_multiply", "Multiply fractions", "fractions", 5.0, ["fraction_add", "multiplication_facts"]),
    "decimals": SkillNode("decimals", "Decimal concepts", "fractions", 4.5, ["fraction_concept", "place_value_4"]),
    "decimal_operations": SkillNode("decimal_operations", "Decimal operations", "fractions", 5.5, ["decimals", "fraction_add"]),

    # Geometry
    "shapes_2d": SkillNode("shapes_2d", "2D shape recognition", "geometry", 1.0),
    "shapes_3d": SkillNode("shapes_3d", "3D shape recognition", "geometry", 2.0, ["shapes_2d"]),
    "symmetry": SkillNode("symmetry", "Lines of symmetry", "geometry", 3.0, ["shapes_2d"]),
    "angles": SkillNode("angles", "Angle concepts", "geometry", 4.0, ["shapes_2d"]),
    "perimeter": SkillNode("perimeter", "Perimeter", "geometry", 3.5, ["addition_2digit", "shapes_2d"]),
    "area": SkillNode("area", "Area of shapes", "geometry", 4.0, ["multiplication_facts", "shapes_2d"]),
    "coordinates": SkillNode("coordinates", "Coordinate geometry", "geometry", 5.0, ["number_patterns"]),

    # Measurement
    "length": SkillNode("length", "Measuring length", "measurement", 1.5),
    "weight": SkillNode("weight", "Measuring weight", "measurement", 2.0, ["comparison"]),
    "capacity": SkillNode("capacity", "Capacity/volume", "measurement", 2.5, ["comparison"]),
    "time": SkillNode("time", "Telling time", "measurement", 2.0),
    "money": SkillNode("money", "Money concepts", "measurement", 2.5, ["addition_2digit"]),
    "unit_conversion": SkillNode("unit_conversion", "Unit conversions", "measurement", 4.0, ["multiplication_facts", "decimals"]),
    "data_handling": SkillNode("data_handling", "Data & graphs", "measurement", 3.5, ["addition_2digit"]),
}


class PathEngine:
    """Generates personalized learning paths from assessment results."""

    def __init__(self, graph: Optional[dict[str, SkillNode]] = None):
        self.graph = graph or PREREQUISITE_GRAPH

    def generate_path(
        self,
        student_id: str,
        domain_scores: dict[str, float],  # domain -> theta
        grade: int,
        curriculum: str = "NCERT",
    ) -> LearningPath:
        """Generate a complete learning path from diagnostic results.

        Args:
            student_id: Student identifier
            domain_scores: theta per domain from CAT assessment
            grade: Student's enrolled grade
            curriculum: Primary curriculum

        Returns:
            LearningPath with prioritized recommendations
        """
        # Determine overall track
        overall_track = self._determine_track(domain_scores, grade)

        # Find focus domains (weakest relative to grade expectation)
        focus_domains = self._find_focus_domains(domain_scores, grade)

        # Find weak skills using prerequisite graph
        recommendations = []
        priority = 1

        for domain in focus_domains:
            theta = domain_scores.get(domain, -3.0)
            expected = GRADE_EXPECTATIONS.get(domain, {}).get(grade, 0.0)
            gap = expected - theta

            # Find skills in this domain that are below student's level
            domain_skills = [
                node for node in self.graph.values()
                if node.domain == domain
            ]

            # Sort by grade level (teach prerequisites first)
            domain_skills.sort(key=lambda n: n.grade_level)

            for skill in domain_skills:
                # Skip skills way above student level
                if skill.grade_level > grade + 0.5:
                    continue

                # Check if prerequisites are likely mastered
                prereq_ready = self._check_prereqs_mastered(
                    skill, domain_scores
                )

                # Estimate if student has mastered this skill
                skill_theta_needed = (skill.grade_level - 3.5) / 1.5
                student_likely_knows = theta >= skill_theta_needed + 0.3

                if not student_likely_knows and prereq_ready:
                    track = Track.FOUNDATION if skill.grade_level < grade - 1 else Track.SCHOOL
                    recommendations.append(PathRecommendation(
                        skill_id=skill.skill_id,
                        name=skill.name,
                        domain=domain,
                        priority=priority,
                        reason="prerequisite_gap" if track == Track.FOUNDATION else "grade_level_gap",
                        estimated_sessions=self._estimate_sessions(gap, skill.grade_level),
                        track=track,
                    ))
                    priority += 1

        # Add acceleration opportunities for strong domains
        for domain, theta in domain_scores.items():
            expected = GRADE_EXPECTATIONS.get(domain, {}).get(grade, 0.0)
            if theta > expected + 0.5:  # Above grade level
                above_skills = [
                    node for node in self.graph.values()
                    if node.domain == domain and node.grade_level > grade
                ]
                above_skills.sort(key=lambda n: n.grade_level)
                for skill in above_skills[:2]:  # Max 2 acceleration items per domain
                    recommendations.append(PathRecommendation(
                        skill_id=skill.skill_id,
                        name=skill.name,
                        domain=domain,
                        priority=priority,
                        reason="accelerate",
                        estimated_sessions=2,
                        track=Track.ACCELERATE,
                    ))
                    priority += 1

        # Build summary
        summary = self._build_summary(overall_track, focus_domains, domain_scores, grade)

        return LearningPath(
            student_id=student_id,
            overall_track=overall_track,
            grade=grade,
            curriculum=curriculum,
            recommendations=recommendations,
            focus_domains=focus_domains,
            summary=summary,
        )

    def _determine_track(self, domain_scores: dict[str, float], grade: int) -> Track:
        """Determine overall track from domain scores."""
        gaps = []
        for domain, theta in domain_scores.items():
            expected = GRADE_EXPECTATIONS.get(domain, {}).get(grade, 0.0)
            gaps.append(expected - theta)

        avg_gap = sum(gaps) / max(len(gaps), 1)

        if avg_gap > 1.0:
            return Track.FOUNDATION
        elif avg_gap < -0.5:
            return Track.ACCELERATE
        return Track.SCHOOL

    def _find_focus_domains(
        self, domain_scores: dict[str, float], grade: int
    ) -> list[str]:
        """Find the 2-3 weakest domains relative to grade expectation."""
        gaps = []
        for domain, theta in domain_scores.items():
            expected = GRADE_EXPECTATIONS.get(domain, {}).get(grade, 0.0)
            gap = expected - theta
            gaps.append((domain, gap))

        gaps.sort(key=lambda x: -x[1])  # Largest gap first
        # Return domains with positive gap (below expectation), max 3
        return [d for d, g in gaps if g > 0.2][:3]

    def _check_prereqs_mastered(
        self, skill: SkillNode, domain_scores: dict[str, float]
    ) -> bool:
        """Check if a skill's prerequisites are likely mastered."""
        if not skill.prerequisites:
            return True

        for prereq_id in skill.prerequisites:
            prereq = self.graph.get(prereq_id)
            if not prereq:
                continue
            # Check if student's domain score is above prereq level
            domain_theta = domain_scores.get(prereq.domain, -3.0)
            prereq_theta_needed = (prereq.grade_level - 3.5) / 1.5
            if domain_theta < prereq_theta_needed - 0.3:
                return False
        return True

    def _estimate_sessions(self, gap: float, skill_grade: float) -> int:
        """Estimate practice sessions needed to master a skill."""
        # Bigger gaps and higher-grade skills need more practice
        base = max(2, int(gap * 2))
        grade_factor = 1 + (skill_grade - 1) * 0.1
        return min(8, int(base * grade_factor))

    def _build_summary(
        self,
        track: Track,
        focus_domains: list[str],
        domain_scores: dict[str, float],
        grade: int,
    ) -> str:
        """Build a parent-friendly summary of the learning path."""
        track_messages = {
            Track.FOUNDATION: "building strong foundations",
            Track.SCHOOL: "keeping pace with grade-level work",
            Track.ACCELERATE: "ready to push beyond grade level",
        }

        focus_str = ", ".join(focus_domains) if focus_domains else "all areas"
        return (
            f"Focus: {track_messages[track]}. "
            f"Priority areas: {focus_str}. "
            f"Estimated 2-3 weeks of daily practice to see measurable growth."
        )
