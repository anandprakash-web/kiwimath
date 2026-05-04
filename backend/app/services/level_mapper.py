"""
Level Mapper — Maps grades + difficulty to Kiwimath Levels (1-6)
and provides the Universal Skill ID taxonomy.

Levels replace grades in the core product. Grade is only relevant
in the Curriculum tab. This mapper bridges the existing grade-based
content to the new level-based system.

Level System:
  Level 1: Explorer  (rough age 5-6, KiwiScore 140-170)
  Level 2: Builder   (rough age 6-7, KiwiScore 170-200)
  Level 3: Thinker   (rough age 7-8, KiwiScore 200-225)
  Level 4: Solver    (rough age 8-9, KiwiScore 225-250)
  Level 5: Strategist(rough age 9-10, KiwiScore 250-270)
  Level 6: Master    (rough age 10-12, KiwiScore 270-300)
"""

from __future__ import annotations
from typing import Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Grade → Level mapping
# ---------------------------------------------------------------------------

# Direct grade mapping (for curriculum-tagged questions)
GRADE_TO_LEVEL: Dict[int, int] = {
    1: 1,  # Grade 1 → Level 1: Explorer
    2: 2,  # Grade 2 → Level 2: Builder
    3: 3,  # Grade 3 → Level 3: Thinker
    4: 4,  # Grade 4 → Level 4: Solver
    5: 5,  # Grade 5 → Level 5: Strategist
    6: 6,  # Grade 6 → Level 6: Master
}

LEVEL_NAMES: Dict[int, str] = {
    1: "Explorer",
    2: "Builder",
    3: "Thinker",
    4: "Solver",
    5: "Strategist",
    6: "Master",
}

# For Olympiad questions (no explicit grade), use difficulty_score ranges
# These were calibrated against the topic files:
#   topic-N/questions.json       → difficulty 1-100   → G1-2 → Level 1-2
#   topic-N/grade34_questions.json → difficulty 101-200 → G3-4 → Level 3-4
#   topic-N/g56_questions.json   → difficulty 201-300  → G5-6 → Level 5-6
DIFFICULTY_TO_LEVEL: list[Tuple[int, int, int]] = [
    (1, 50, 1),      # Easy G1 → Level 1
    (51, 100, 2),     # Medium G1-2 → Level 2
    (101, 150, 3),    # G3 range → Level 3
    (151, 200, 4),    # G4 range → Level 4
    (201, 250, 5),    # G5 range → Level 5
    (251, 500, 6),    # G6+ range → Level 6
]


def grade_to_level(grade: Optional[int]) -> int:
    """Map a school grade (1-6) to Kiwimath Level (1-6)."""
    if grade is None:
        return 3  # default to middle
    return GRADE_TO_LEVEL.get(grade, min(max(grade, 1), 6))


def difficulty_to_level(difficulty_score: int) -> int:
    """Map a difficulty score to Kiwimath Level (for gradeless questions)."""
    for lo, hi, level in DIFFICULTY_TO_LEVEL:
        if lo <= difficulty_score <= hi:
            return level
    return 3  # fallback


def infer_level(grade: Optional[int], difficulty_score: int) -> int:
    """Infer level from grade (if available) or difficulty score."""
    if grade and 1 <= grade <= 6:
        return grade_to_level(grade)
    return difficulty_to_level(difficulty_score)


# ---------------------------------------------------------------------------
# Universal Skill ID taxonomy
# Maps existing 37 skill_ids → structured Universal_Skill_IDs
# Format: DOMAIN_SKILL_LEVEL.VARIANT
# ---------------------------------------------------------------------------

SKILL_TO_UNIVERSAL: Dict[str, Dict] = {
    # Counting & Numbers
    "counting_10":       {"uid": "COUNT_10",       "domain": "numbers",     "level_range": (1, 1)},
    "counting_100":      {"uid": "COUNT_100",      "domain": "numbers",     "level_range": (1, 2)},
    "place_value_2":     {"uid": "PV_2DIG",        "domain": "numbers",     "level_range": (2, 2)},
    "place_value_3":     {"uid": "PV_3DIG",        "domain": "numbers",     "level_range": (3, 3)},
    "place_value_4":     {"uid": "PV_4DIG",        "domain": "numbers",     "level_range": (4, 6)},
    "comparison":        {"uid": "NUM_COMPARE",    "domain": "numbers",     "level_range": (1, 3)},
    "rounding":          {"uid": "NUM_ROUND",      "domain": "numbers",     "level_range": (3, 4)},
    "number_patterns":   {"uid": "NUM_PATTERN",    "domain": "numbers",     "level_range": (2, 5)},

    # Arithmetic
    "addition_basic":    {"uid": "ADD_BASIC",      "domain": "arithmetic",  "level_range": (1, 2)},
    "addition_2digit":   {"uid": "ADD_2DIG",       "domain": "arithmetic",  "level_range": (2, 3)},
    "subtraction_basic": {"uid": "SUB_BASIC",      "domain": "arithmetic",  "level_range": (1, 2)},
    "subtraction_2digit":{"uid": "SUB_2DIG",       "domain": "arithmetic",  "level_range": (2, 3)},
    "multiplication_facts":{"uid": "MULT_FACTS",   "domain": "arithmetic",  "level_range": (3, 3)},
    "division_basic":    {"uid": "DIV_BASIC",      "domain": "arithmetic",  "level_range": (3, 4)},
    "multi_step":        {"uid": "ARITH_MULTI",    "domain": "arithmetic",  "level_range": (4, 5)},
    "order_of_ops":      {"uid": "ORDER_OPS",      "domain": "arithmetic",  "level_range": (5, 6)},

    # Fractions & Decimals
    "fraction_concept":  {"uid": "FRAC_CONCEPT",   "domain": "fractions",   "level_range": (3, 3)},
    "fraction_compare":  {"uid": "FRAC_COMPARE",   "domain": "fractions",   "level_range": (3, 4)},
    "fraction_add":      {"uid": "FRAC_ADD",       "domain": "fractions",   "level_range": (4, 5)},
    "fraction_multiply": {"uid": "FRAC_MULT",      "domain": "fractions",   "level_range": (5, 6)},
    "decimals":          {"uid": "DEC_CONCEPT",    "domain": "fractions",   "level_range": (4, 5)},
    "decimal_operations":{"uid": "DEC_OPS",        "domain": "fractions",   "level_range": (5, 6)},

    # Geometry
    "shapes_2d":         {"uid": "SHAPE_2D",       "domain": "geometry",    "level_range": (1, 3)},
    "shapes_3d":         {"uid": "SHAPE_3D",       "domain": "geometry",    "level_range": (3, 5)},
    "symmetry":          {"uid": "GEO_SYMMETRY",   "domain": "geometry",    "level_range": (3, 4)},
    "angles":            {"uid": "GEO_ANGLES",     "domain": "geometry",    "level_range": (4, 5)},
    "perimeter":         {"uid": "GEO_PERIMETER",  "domain": "geometry",    "level_range": (3, 4)},
    "area":              {"uid": "GEO_AREA",       "domain": "geometry",    "level_range": (4, 5)},
    "coordinates":       {"uid": "GEO_COORD",      "domain": "geometry",    "level_range": (5, 6)},

    # Measurement
    "length":            {"uid": "MEAS_LENGTH",    "domain": "measurement", "level_range": (1, 3)},
    "weight":            {"uid": "MEAS_WEIGHT",    "domain": "measurement", "level_range": (2, 3)},
    "capacity":          {"uid": "MEAS_CAPACITY",  "domain": "measurement", "level_range": (2, 4)},
    "time":              {"uid": "MEAS_TIME",      "domain": "measurement", "level_range": (2, 4)},
    "money":             {"uid": "MEAS_MONEY",     "domain": "measurement", "level_range": (2, 4)},
    "unit_conversion":   {"uid": "MEAS_CONVERT",   "domain": "measurement", "level_range": (4, 6)},

    # Data
    "data_handling":     {"uid": "DATA_HANDLE",    "domain": "data",        "level_range": (3, 6)},
}


def get_universal_skill_id(skill_id: str, level: int) -> str:
    """Convert an old skill_id to a Universal Skill ID with level suffix.

    Example: "fraction_add" at level 4 → "FRAC_ADD_4"
    """
    info = SKILL_TO_UNIVERSAL.get(skill_id)
    if not info:
        return f"UNKNOWN_{level}"
    return f"{info['uid']}_{level}"


def get_skill_domain(skill_id: str) -> str:
    """Get the domain for a skill_id."""
    info = SKILL_TO_UNIVERSAL.get(skill_id)
    return info["domain"] if info else "unknown"


# ---------------------------------------------------------------------------
# Visual requirement inference
# ---------------------------------------------------------------------------

# Tags/topics that REQUIRE visuals (essential)
VISUAL_ESSENTIAL_TAGS = {
    "shapes", "shape", "geometry", "symmetry", "3d", "spatial",
    "graph", "data_handling", "statistics", "chart", "picture",
    "visual_counting", "pattern_visual", "number_line",
    "coordinate", "area", "perimeter", "angle", "folding",
}

# Tags where visuals help but aren't required (optional)
VISUAL_OPTIONAL_TAGS = {
    "word_problem", "counting", "measurement", "money", "time",
    "fractions", "fraction", "place_value", "comparison",
}


def infer_visual_requirement(
    tags: list[str],
    level: int,
    has_visual: bool,
    interaction_mode: str = "mcq",
) -> str:
    """Infer visual_requirement: essential | optional | none."""
    tag_set = {t.lower().replace(" ", "_") for t in tags}

    # Drag-drop always needs visuals
    if interaction_mode in ("drag_drop", "tap_to_count", "draw"):
        return "essential"

    # Check essential tags
    if tag_set & VISUAL_ESSENTIAL_TAGS:
        return "essential"

    # Levels 1-2: almost everything benefits from visuals
    if level <= 2:
        return "essential" if has_visual else "optional"

    # Check optional tags
    if tag_set & VISUAL_OPTIONAL_TAGS:
        return "optional"

    # Pure computation at higher levels
    return "none"


# ---------------------------------------------------------------------------
# Maturity bucket inference
# ---------------------------------------------------------------------------

def infer_maturity_bucket(
    has_irt: bool,
    has_hints: bool,
    has_diagnostics: bool,
    times_served: int = 0,
) -> str:
    """Infer the maturity bucket for a question.

    Since all existing questions have IRT params and have been in production,
    we start them at 'calibrating' or 'production' based on completeness.
    New questions (future) would start at 'experimental'.
    """
    if times_served >= 1000:
        return "production"
    if has_irt and has_hints and has_diagnostics:
        return "calibrating"
    if has_irt:
        return "calibrating"
    return "experimental"


# ---------------------------------------------------------------------------
# Country context templates
# ---------------------------------------------------------------------------

COUNTRY_CONTEXTS = {
    "india": {
        "currency": "₹",
        "currency_name": "rupees",
        "names": ["Aarav", "Priya", "Arjun", "Diya", "Rohan", "Ananya", "Vihaan", "Isha"],
        "objects": ["mangoes", "rotis", "sweets", "bangles", "diyas"],
        "units": "km/kg/L",
    },
    "singapore": {
        "currency": "$",
        "currency_name": "dollars",
        "names": ["Wei", "Mei", "Jun", "Li", "Kai", "Xin", "Rui", "Zhi"],
        "objects": ["mooncakes", "oranges", "dumplings", "lanterns"],
        "units": "km/kg/L",
    },
    "us": {
        "currency": "$",
        "currency_name": "dollars",
        "names": ["Alex", "Emma", "Liam", "Sophia", "Noah", "Olivia", "Mason", "Ava"],
        "objects": ["apples", "cookies", "cupcakes", "stickers"],
        "units": "mi/lb/gal",
    },
    "global": {
        "currency": "coins",
        "currency_name": "coins",
        "names": ["Alex", "Sam", "Kai", "Ria", "Leo", "Zoe", "Max", "Mia"],
        "objects": ["fruits", "toys", "stickers", "marbles"],
        "units": "km/kg/L",
    },
}


# ---------------------------------------------------------------------------
# Curriculum cross-reference builder
# ---------------------------------------------------------------------------

# Maps NCERT chapter patterns to cross-curriculum equivalents
# This enables the "curricula are skins" architecture
CROSS_CURRICULUM_MAP = {
    # Numbers
    "counting": {
        "cbse": "Ch1: Numbers",
        "icse": "Ch1: Numbers",
        "cambridge": "1Nn - Numbers",
        "singapore": "Whole Numbers",
        "common_core": "K.CC / 1.NBT",
    },
    "place_value": {
        "cbse": "Ch1: Numbers",
        "icse": "Ch1: Numerals",
        "cambridge": "Nn - Place Value",
        "singapore": "Whole Numbers",
        "common_core": "NBT - Number & Operations in Base Ten",
    },
    "addition": {
        "cbse": "Ch2: Addition",
        "icse": "Ch2: Addition",
        "cambridge": "Nc - Calculation (Addition)",
        "singapore": "Addition & Subtraction",
        "common_core": "OA - Operations & Algebraic Thinking",
    },
    "subtraction": {
        "cbse": "Ch3: Subtraction",
        "icse": "Ch3: Subtraction",
        "cambridge": "Nc - Calculation (Subtraction)",
        "singapore": "Addition & Subtraction",
        "common_core": "OA - Operations & Algebraic Thinking",
    },
    "multiplication": {
        "cbse": "Ch4: Multiplication",
        "icse": "Ch4: Multiplication",
        "cambridge": "Nc - Calculation (Multiplication)",
        "singapore": "Multiplication & Division",
        "common_core": "OA - Operations & Algebraic Thinking",
    },
    "division": {
        "cbse": "Ch5: Division",
        "icse": "Ch5: Division",
        "cambridge": "Nc - Calculation (Division)",
        "singapore": "Multiplication & Division",
        "common_core": "OA - Operations & Algebraic Thinking",
    },
    "fractions": {
        "cbse": "Ch7: Fractions",
        "icse": "Ch6: Fractions",
        "cambridge": "Nf - Fractions",
        "singapore": "Fractions",
        "common_core": "NF - Number & Operations — Fractions",
    },
    "decimals": {
        "cbse": "Ch8: Decimals",
        "icse": "Ch7: Decimals",
        "cambridge": "Nf - Fractions & Decimals",
        "singapore": "Decimals",
        "common_core": "NBT / NF",
    },
    "geometry": {
        "cbse": "Ch5: Shapes & Spatial Understanding",
        "icse": "Ch8: Geometry",
        "cambridge": "Gg - Geometry",
        "singapore": "Shapes & Space",
        "common_core": "G - Geometry",
    },
    "measurement": {
        "cbse": "Ch6: Measurement",
        "icse": "Ch9: Measurement",
        "cambridge": "Gm - Measure",
        "singapore": "Measurement",
        "common_core": "MD - Measurement & Data",
    },
    "data_handling": {
        "cbse": "Ch9: Data Handling",
        "icse": "Ch10: Data Handling",
        "cambridge": "Gs - Statistics",
        "singapore": "Data Analysis",
        "common_core": "MD - Measurement & Data",
    },
    "patterns": {
        "cbse": "Ch3: Patterns",
        "icse": "Ch3: Patterns",
        "cambridge": "Na - Algebra",
        "singapore": "Patterns",
        "common_core": "OA - Operations & Algebraic Thinking",
    },
    "money": {
        "cbse": "Ch6: Money",
        "icse": "Ch5: Money",
        "cambridge": "Gm - Money",
        "singapore": "Money",
        "common_core": "MD - Measurement & Data",
    },
    "time": {
        "cbse": "Ch6: Time",
        "icse": "Ch5: Time",
        "cambridge": "Gm - Time",
        "singapore": "Time",
        "common_core": "MD - Measurement & Data",
    },
}


def build_curriculum_map(tags: list[str], skill_domain: str) -> dict:
    """Build a cross-curriculum mapping for a question based on its tags/domain."""
    # Find the best matching cross-curriculum entry
    tag_set = {t.lower() for t in tags}

    for key, mapping in CROSS_CURRICULUM_MAP.items():
        if key in tag_set or key == skill_domain:
            return mapping

    # Fallback: use domain
    return CROSS_CURRICULUM_MAP.get(skill_domain, {})
