"""
Unified Skill Mapper — maps ALL questions (Olympiad + NCERT + ICSE + Singapore + USCC)
to the prerequisite skill graph for cross-curriculum adaptive sessions.

This is the bridge between:
  - Content (21,330 questions across 5 curricula)
  - The skill graph (37 nodes in path_engine.py)
  - The adaptive engine (per-skill theta tracking)

Every question gets a `skill_id` assignment based on its tags, topic, difficulty,
and curriculum metadata. The session planner then picks from the unified pool.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from app.services.content_store_v2 import QuestionV2, store_v2


# ---------------------------------------------------------------------------
# Skill mapping rules — tag patterns → skill_id
# Priority: first match wins. More specific rules go first.
# ---------------------------------------------------------------------------

# (tag_pattern, difficulty_range, skill_id)
# tag_pattern: set of tags that must ALL be present (AND logic)
# difficulty_range: (min, max) or None for any difficulty
TAG_RULES: List[Tuple[Set[str], Optional[Tuple[int, int]], str]] = [
    # Fractions & Decimals
    ({"decimal", "operations"}, None, "decimal_operations"),
    ({"decimal"}, None, "decimals"),
    ({"fraction", "multiply"}, None, "fraction_multiply"),
    ({"fraction", "add"}, None, "fraction_add"),
    ({"fraction", "subtract"}, None, "fraction_add"),
    ({"fraction", "compare"}, None, "fraction_compare"),
    ({"fractions", "multiplication"}, None, "fraction_multiply"),
    ({"fractions", "addition"}, None, "fraction_add"),
    ({"fractions", "compare"}, None, "fraction_compare"),
    ({"fractions"}, (1, 120), "fraction_concept"),
    ({"fractions"}, (121, 300), "fraction_add"),

    # Geometry
    ({"coordinate"}, None, "coordinates"),
    ({"area"}, None, "area"),
    ({"perimeter"}, None, "perimeter"),
    ({"angle"}, None, "angles"),
    ({"symmetry"}, None, "symmetry"),
    ({"3d", "shape"}, None, "shapes_3d"),
    ({"shapes", "3d"}, None, "shapes_3d"),
    ({"shape"}, None, "shapes_2d"),
    ({"shapes"}, None, "shapes_2d"),

    # Measurement
    ({"conversion"}, None, "unit_conversion"),
    ({"unit"}, None, "unit_conversion"),
    ({"data_handling"}, None, "data_handling"),
    ({"statistics"}, None, "data_handling"),
    ({"graph"}, None, "data_handling"),
    ({"money"}, None, "money"),
    ({"time"}, None, "time"),
    ({"capacity"}, None, "capacity"),
    ({"volume"}, None, "capacity"),
    ({"weight"}, None, "weight"),
    ({"mass"}, None, "weight"),
    ({"length"}, None, "length"),
    ({"measurement"}, (1, 100), "length"),
    ({"measurement"}, (101, 200), "unit_conversion"),
    ({"measurement"}, (201, 300), "unit_conversion"),

    # Arithmetic — ordered from complex to simple
    ({"order_of_operations"}, None, "order_of_ops"),
    ({"bodmas"}, None, "order_of_ops"),
    ({"multi_step"}, None, "multi_step"),
    ({"division"}, None, "division_basic"),
    ({"multiplication"}, (1, 120), "multiplication_facts"),
    ({"multiplication"}, (121, 300), "multi_step"),
    ({"subtraction"}, (101, 300), "subtraction_2digit"),
    ({"subtraction"}, (1, 100), "subtraction_basic"),
    ({"addition"}, (101, 300), "addition_2digit"),
    ({"addition"}, (1, 100), "addition_basic"),
    ({"arithmetic"}, (1, 80), "addition_basic"),
    ({"arithmetic"}, (81, 150), "addition_2digit"),
    ({"arithmetic"}, (151, 250), "multi_step"),
    ({"arithmetic"}, (251, 300), "order_of_ops"),

    # Numbers & Place Value
    ({"rounding"}, None, "rounding"),
    ({"number_patterns"}, None, "number_patterns"),
    ({"patterns"}, (1, 100), "number_patterns"),
    ({"patterns"}, (101, 300), "number_patterns"),
    ({"place_value"}, (1, 80), "place_value_2"),
    ({"place_value"}, (81, 150), "place_value_3"),
    ({"place_value"}, (151, 300), "place_value_4"),
    ({"comparison"}, None, "comparison"),
    ({"counting"}, (1, 50), "counting_10"),
    ({"counting"}, (51, 300), "counting_100"),
    ({"numbers"}, (1, 50), "counting_10"),
    ({"numbers"}, (51, 120), "counting_100"),
    ({"numbers"}, (121, 200), "place_value_3"),
    ({"numbers"}, (201, 300), "place_value_4"),
]

# Fallback: map topic_id prefixes to skills when tags don't match
TOPIC_FALLBACKS: Dict[str, str] = {
    "counting_observation": "counting_100",
    "arithmetic_missing_numbers": "addition_basic",
    "patterns_sequences": "number_patterns",
    "logic_ordering": "comparison",
    "spatial_reasoning_3d": "shapes_3d",
    "spatial_reasoning": "shapes_2d",
    "shapes_folding_symmetry": "symmetry",
    "shapes_geometry": "shapes_2d",
    "word_problems_stories": "multi_step",
    "word_problems": "multi_step",
    "number_puzzles_games": "number_patterns",
    "puzzles_games": "number_patterns",
    "logic_deduction": "comparison",
    "data_handling": "data_handling",
}

# NCERT/ICSE/Singapore topic → skill mapping
CURRICULUM_TOPIC_MAP: Dict[str, str] = {
    "ncert_g1_numbers": "counting_100",
    "ncert_g1_addition": "addition_basic",
    "ncert_g1_subtraction": "subtraction_basic",
    "ncert_g1_shapes": "shapes_2d",
    "ncert_g1_measurement": "length",
    "ncert_g2_numbers": "place_value_2",
    "ncert_g2_addition": "addition_2digit",
    "ncert_g2_subtraction": "subtraction_2digit",
    "ncert_g2_multiplication": "multiplication_facts",
    "ncert_g2_shapes": "shapes_2d",
    "ncert_g2_measurement": "length",
    "ncert_g3_numbers": "place_value_3",
    "ncert_g3_arithmetic": "addition_2digit",
    "ncert_g3_fractions": "fraction_concept",
    "ncert_g3_geometry": "perimeter",
    "ncert_g3_measurement": "unit_conversion",
    "ncert_g4_numbers": "place_value_4",
    "ncert_g4_arithmetic": "multi_step",
    "ncert_g4_fractions": "fraction_compare",
    "ncert_g4_geometry": "area",
    "ncert_g4_measurement": "unit_conversion",
    "ncert_g5_numbers": "place_value_4",
    "ncert_g5_arithmetic": "order_of_ops",
    "ncert_g5_fractions": "fraction_add",
    "ncert_g5_geometry": "angles",
    "ncert_g5_measurement": "unit_conversion",
    "ncert_g6_numbers": "place_value_4",
    "ncert_g6_integers": "subtraction_2digit",
    "ncert_g6_fractions": "fraction_multiply",
    "ncert_g6_geometry": "coordinates",
    "ncert_g6_algebra": "order_of_ops",
    "ncert_g6_ratio": "fraction_multiply",
    "ncert_g6_data": "data_handling",
}


def _match_tags(
    question_tags: Set[str],
    difficulty: int,
) -> Optional[str]:
    """Try to match question tags against TAG_RULES."""
    for required_tags, diff_range, skill_id in TAG_RULES:
        if not required_tags.issubset(question_tags):
            continue
        if diff_range is not None:
            lo, hi = diff_range
            if not (lo <= difficulty <= hi):
                continue
        return skill_id
    return None


def map_question_to_skill(q: QuestionV2) -> str:
    """Map a single question to its skill_id in the prerequisite graph.

    Resolution order:
      1. Tag-based matching (most precise)
      2. Curriculum topic mapping
      3. Topic ID fallback
      4. Difficulty-based fallback
    """
    tags = set(t.lower().replace(" ", "_") for t in (q.tags or []))
    difficulty = q.difficulty_score or 50

    # 1. Tag-based matching
    skill = _match_tags(tags, difficulty)
    if skill:
        return skill

    # 2. Curriculum topic mapping (for NCERT/ICSE/Singapore questions)
    topic = (q.topic or "").lower()
    if topic in CURRICULUM_TOPIC_MAP:
        return CURRICULUM_TOPIC_MAP[topic]

    # 3. Topic ID fallback (Olympiad topics)
    for prefix, skill_id in TOPIC_FALLBACKS.items():
        if topic.startswith(prefix):
            return skill_id

    # 4. Difficulty-based fallback
    if difficulty <= 50:
        return "counting_10"
    elif difficulty <= 100:
        return "addition_basic"
    elif difficulty <= 150:
        return "addition_2digit"
    elif difficulty <= 200:
        return "multiplication_facts"
    else:
        return "multi_step"


# ---------------------------------------------------------------------------
# Unified skill index — built once at startup, provides fast lookups
# ---------------------------------------------------------------------------

class SkillIndex:
    """Pre-built index mapping skills → questions from ALL curricula."""

    def __init__(self):
        self._skill_questions: Dict[str, List[str]] = {}  # skill_id -> [qid, ...]
        self._question_skill: Dict[str, str] = {}  # qid -> skill_id
        self._built = False

    def build(self) -> None:
        """Build the index from all loaded content. Call after store_v2 is loaded."""
        self._skill_questions.clear()
        self._question_skill.clear()

        for q in store_v2.all_questions():
            skill = map_question_to_skill(q)
            self._question_skill[q.id] = skill
            self._skill_questions.setdefault(skill, []).append(q.id)

        self._built = True

    @property
    def is_built(self) -> bool:
        return self._built

    def get_skill(self, qid: str) -> str:
        """Get the skill_id for a question."""
        if not self._built:
            self.build()
        return self._question_skill.get(qid, "counting_10")

    def get_questions_for_skill(
        self,
        skill_id: str,
        min_difficulty: int = 1,
        max_difficulty: int = 300,
        exclude_ids: Optional[Set[str]] = None,
    ) -> List[QuestionV2]:
        """Get all questions mapped to a skill within a difficulty range."""
        if not self._built:
            self.build()

        exclude = exclude_ids or set()
        results = []
        for qid in self._skill_questions.get(skill_id, []):
            if qid in exclude:
                continue
            q = store_v2.get(qid)
            if q and min_difficulty <= q.difficulty_score <= max_difficulty:
                results.append(q)

        return results

    def get_skill_distribution(self) -> Dict[str, int]:
        """Summary: how many questions per skill."""
        if not self._built:
            self.build()
        return {k: len(v) for k, v in self._skill_questions.items()}

    def get_skills_for_domain(self, domain: str) -> List[str]:
        """Get all skills belonging to a domain (numbers, arithmetic, etc.)."""
        from app.assessment.path_engine import PREREQUISITE_GRAPH
        return [
            node.skill_id for node in PREREQUISITE_GRAPH.values()
            if node.domain == domain
        ]


# Singleton
skill_index = SkillIndex()
