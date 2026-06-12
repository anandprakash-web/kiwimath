"""
Pillar Content Store — loads and serves 4-pillar × 5-level olympiad content.

Content lives in: content/olympiad_v2/{pillar}/level{N}/
Each level folder contains JSON batch files with questions.

Directory layout:
    content/olympiad_v2/
    ├── algebra/
    │   ├── level1/  (G1-2)
    │   ├── level2/  (G3-4)
    │   ├── level3/  (G5-6)
    │   ├── level4/  (G7-8)
    │   └── level5/  (G9-10)
    ├── number_theory/
    ├── combinatorics/
    └── geometry/
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kiwimath.pillar_content")

PILLARS = ["algebra", "number_theory", "combinatorics", "geometry"]
LEVELS = [1, 2, 3, 4, 5]

# Level → grade ranges (for filtering)
LEVEL_GRADE_MAP = {
    1: [1, 2],
    2: [3, 4],
    3: [5, 6],
    4: [7, 8],
    5: [9, 10],
}

# Reverse: grade → appropriate level
GRADE_LEVEL_MAP = {g: lvl for lvl, grades in LEVEL_GRADE_MAP.items() for g in grades}

# ── Pillar metadata ────────────────────────────────────────────────────────

PILLAR_META = {
    "algebra": {
        "name": "Algebra",
        "emoji": "\U0001f9ee",  # 🧮
        "tagline": "Patterns, equations & elegant proofs",
        "color": "#FF6D00",
    },
    "number_theory": {
        "name": "Number Theory",
        "emoji": "\U0001f522",  # 🔢
        "tagline": "Primes, divisibility & hidden structure",
        "color": "#2E7D32",
    },
    "combinatorics": {
        "name": "Combinatorics",
        "emoji": "\U0001f3b2",  # 🎲
        "tagline": "Counting, probability & clever arguments",
        "color": "#1565C0",
    },
    "geometry": {
        "name": "Geometry",
        "emoji": "\U0001f4d0",  # 📐
        "tagline": "Shapes, symmetry & spatial reasoning",
        "color": "#7B1FA2",
    },
}

# ── Level topic curriculum (corrected from v2 storyboard comparison) ──────

LEVEL_TOPICS: Dict[str, Dict[int, List[Dict[str, str]]]] = {
    "algebra": {
        1: [
            {"id": "odd_even_magic", "name": "Odd & Even Magic", "tagline": "Parity patterns in sums"},
            {"id": "balance_equations", "name": "Balance Equations", "tagline": "Scales that balance"},
            {"id": "number_patterns", "name": "Number Patterns", "tagline": "What comes next?"},
        ],
        2: [
            {"id": "algebraic_expressions", "name": "Algebraic Expressions", "tagline": "Letters meet numbers"},
            {"id": "linear_equations", "name": "Linear Equations", "tagline": "Solve for x"},
            {"id": "sequences_series", "name": "Sequences & Series", "tagline": "Arithmetic & geometric"},
        ],
        3: [
            {"id": "quadratics", "name": "Quadratic Equations", "tagline": "Parabolas & roots"},
            {"id": "inequalities", "name": "Inequalities", "tagline": "AM-GM & Cauchy-Schwarz"},
            {"id": "polynomials", "name": "Polynomials", "tagline": "Factor & remainder theorems"},
        ],
        4: [
            {"id": "functional_equations", "name": "Functional Equations", "tagline": "f(x+y) = f(x)f(y)"},
            {"id": "complex_numbers", "name": "Complex Numbers", "tagline": "Beyond the real line"},
            {"id": "adv_inequalities", "name": "Advanced Inequalities", "tagline": "Schur, Muirhead, SOS"},
        ],
        5: [
            {"id": "abstract_algebra", "name": "Abstract Algebra", "tagline": "Groups, rings, fields"},
            {"id": "olympiad_algebra", "name": "Olympiad Algebra", "tagline": "IMO-level problems"},
        ],
    },
    "number_theory": {
        1: [
            {"id": "factors_multiples", "name": "Factors & Multiples", "tagline": "Breaking numbers apart"},
            {"id": "divisibility_rules", "name": "Divisibility Rules", "tagline": "Quick checks"},
            {"id": "prime_composite", "name": "Primes & Composites", "tagline": "Building blocks"},
        ],
        2: [
            {"id": "gcd_lcm", "name": "GCD & LCM", "tagline": "Greatest & least"},
            {"id": "place_value", "name": "Place Value & Digits", "tagline": "Digit sums & products"},
            {"id": "remainders", "name": "Remainders & Division", "tagline": "What's left over?"},
        ],
        3: [
            {"id": "modular_intro", "name": "Modular Arithmetic", "tagline": "Clock arithmetic"},
            {"id": "diophantine_basic", "name": "Diophantine Equations", "tagline": "Integer solutions only"},
            {"id": "perfect_numbers", "name": "Perfect & Special Numbers", "tagline": "Triangular, square, Fibonacci"},
        ],
        4: [
            {"id": "fermat_euler", "name": "Fermat & Euler", "tagline": "Little theorem, totient"},
            {"id": "quadratic_residues", "name": "Quadratic Residues", "tagline": "Squares mod p"},
            {"id": "adv_diophantine", "name": "Advanced Diophantine", "tagline": "Pell, Vieta jumping"},
        ],
        5: [
            {"id": "analytic_nt", "name": "Analytic Number Theory", "tagline": "Generating functions & bounds"},
            {"id": "olympiad_nt", "name": "Olympiad Number Theory", "tagline": "IMO-level problems"},
        ],
    },
    "combinatorics": {
        1: [
            {"id": "counting_basics", "name": "Counting & Listing", "tagline": "Systematic counting"},
            {"id": "patterns_observation", "name": "Patterns & Observation", "tagline": "See what others miss"},
            {"id": "simple_logic", "name": "Simple Logic", "tagline": "If-then reasoning"},
        ],
        2: [
            {"id": "permutations", "name": "Permutations", "tagline": "Order matters"},
            {"id": "combinations", "name": "Combinations", "tagline": "Order doesn't matter"},
            {"id": "multiplication_principle", "name": "Multiplication Principle", "tagline": "Counting paths"},
        ],
        3: [
            {"id": "pascals_triangle", "name": "Pascal's Triangle", "tagline": "Binomial coefficients"},
            {"id": "pigeonhole", "name": "Pigeonhole Principle", "tagline": "Forced collisions"},
            {"id": "inclusion_exclusion", "name": "Inclusion-Exclusion", "tagline": "Count by overcounting"},
        ],
        4: [
            {"id": "generating_functions", "name": "Generating Functions", "tagline": "Polynomials encode sequences"},
            {"id": "graph_theory", "name": "Graph Theory", "tagline": "Vertices & edges"},
            {"id": "adv_counting", "name": "Advanced Counting", "tagline": "Burnside, Catalan, Stirling"},
        ],
        5: [
            {"id": "extremal_combinatorics", "name": "Extremal Combinatorics", "tagline": "How far can we push?"},
            {"id": "olympiad_combo", "name": "Olympiad Combinatorics", "tagline": "IMO-level problems"},
        ],
    },
    "geometry": {
        1: [
            {"id": "shapes_2d", "name": "Shapes & Properties", "tagline": "Triangles, squares, circles"},
            {"id": "symmetry_reflection", "name": "Symmetry & Reflection", "tagline": "Mirror images"},
            {"id": "spatial_reasoning", "name": "Spatial Reasoning", "tagline": "See in 3D"},
        ],
        2: [
            {"id": "angles_triangles", "name": "Angles & Triangles", "tagline": "Angle sums & types"},
            {"id": "area_perimeter", "name": "Area & Perimeter", "tagline": "Measure shapes"},
            {"id": "coordinate_intro", "name": "Coordinate Geometry", "tagline": "Points on a grid"},
        ],
        3: [
            {"id": "overlapping_pie", "name": "Overlapping & PIE", "tagline": "Overlapping regions"},
            {"id": "congruence_similarity", "name": "Congruence & Similarity", "tagline": "Same shape, same size"},
            {"id": "circle_properties", "name": "Circle Properties", "tagline": "Arcs, chords, tangents"},
        ],
        4: [
            {"id": "pythagoras_trig", "name": "Pythagoras & Trig", "tagline": "Right triangle power"},
            {"id": "circle_theorems", "name": "Circle Theorems", "tagline": "Cyclic quads & power of a point"},
            {"id": "transformations", "name": "Transformations", "tagline": "Rotate, reflect, translate"},
        ],
        5: [
            {"id": "projective_geometry", "name": "Projective Geometry", "tagline": "Cross-ratios & duality"},
            {"id": "olympiad_geometry", "name": "Olympiad Geometry", "tagline": "IMO-level problems"},
        ],
    },
}


class PillarContentStore:
    """In-memory content store for pillar-based olympiad questions."""

    def __init__(self):
        self._questions: Dict[str, Dict[int, List[dict]]] = {}  # pillar -> level -> [questions]
        self._by_id: Dict[str, dict] = {}  # question_id -> question
        self._loaded = False

    def load(self, content_dir: str | Path):
        """Load all pillar content from disk."""
        content_dir = Path(content_dir)
        if not content_dir.exists():
            logger.warning(f"Pillar content dir not found: {content_dir}")
            self._loaded = True
            return

        total = 0
        for pillar in PILLARS:
            self._questions[pillar] = {}
            for level in LEVELS:
                level_dir = content_dir / pillar / f"level{level}"
                questions = []
                if level_dir.exists():
                    for f in sorted(level_dir.glob("*.json")):
                        try:
                            data = json.loads(f.read_text())
                            if isinstance(data, list):
                                questions.extend(data)
                            elif isinstance(data, dict) and "questions" in data:
                                questions.extend(data["questions"])
                        except Exception as e:
                            logger.error(f"Error loading {f}: {e}")
                self._questions[pillar][level] = questions
                for q in questions:
                    self._by_id[q.get("id", "")] = q
                total += len(questions)

        self._loaded = True
        logger.info(f"Pillar content loaded: {total} questions across {len(PILLARS)} pillars")

    def get_pillars(self, grade: int) -> List[dict]:
        """Return pillar summaries with question counts for a grade."""
        level = GRADE_LEVEL_MAP.get(grade, 1)
        result = []
        for pid in PILLARS:
            meta = PILLAR_META[pid]
            qs = self._questions.get(pid, {}).get(level, [])
            result.append({
                **meta,
                "id": pid,
                "level": level,
                "question_count": len(qs),
                "topics": LEVEL_TOPICS.get(pid, {}).get(level, []),
            })
        return result

    def get_levels(self, pillar: str, grade: int) -> List[dict]:
        """Return all levels for a pillar with topic lists and counts."""
        if pillar not in PILLARS:
            return []
        result = []
        for level in LEVELS:
            qs = self._questions.get(pillar, {}).get(level, [])
            topics = LEVEL_TOPICS.get(pillar, {}).get(level, [])
            grade_range = LEVEL_GRADE_MAP.get(level, [])
            result.append({
                "level": level,
                "grade_range": grade_range,
                "question_count": len(qs),
                "topics": topics,
                "locked": level > GRADE_LEVEL_MAP.get(grade, 1) + 1,
            })
        return result

    def get_topics(self, pillar: str, level: int) -> List[dict]:
        """Return topics for a pillar+level with per-topic question counts."""
        topics = LEVEL_TOPICS.get(pillar, {}).get(level, [])
        qs = self._questions.get(pillar, {}).get(level, [])
        result = []
        for topic in topics:
            tid = topic["id"]
            count = sum(1 for q in qs if q.get("topic") == tid)
            result.append({**topic, "question_count": count})
        return result

    def get_worksheet(self, pillar: str, level: int, topic: str) -> dict:
        """Build a worksheet from questions matching pillar/level/topic."""
        qs = self._questions.get(pillar, {}).get(level, [])
        filtered = [q for q in qs if q.get("topic") == topic]

        # Sort by difficulty: warmup → practice → challenge
        tier_order = {"warmup": 0, "practice": 1, "challenge": 2}
        filtered.sort(key=lambda q: tier_order.get(q.get("difficulty_tier", "practice"), 1))

        meta = PILLAR_META.get(pillar, {})
        topic_info = next(
            (t for t in LEVEL_TOPICS.get(pillar, {}).get(level, []) if t["id"] == topic),
            {"name": topic, "tagline": ""},
        )
        return {
            "grade": LEVEL_GRADE_MAP.get(level, [0])[0] if LEVEL_GRADE_MAP.get(level) else 0,
            "day": 1,
            "title": topic_info["name"],
            "subtitle": topic_info.get("tagline", ""),
            "dominant_topic": topic,
            "pillar": pillar,
            "level": level,
            "questions": filtered,
        }

    def get_question(self, question_id: str) -> Optional[dict]:
        """Fetch a single question by ID."""
        return self._by_id.get(question_id)

    def get_daily_challenge(self, grade: int) -> Optional[dict]:
        """Pick a daily challenge question. Currently random from appropriate level."""
        import random
        from datetime import date

        level = GRADE_LEVEL_MAP.get(grade, 1)
        # Use date as seed for deterministic daily selection
        seed = date.today().isoformat() + str(grade)
        rng = random.Random(seed)

        # Collect all challenge-tier questions for this level across pillars
        candidates = []
        for pillar in PILLARS:
            qs = self._questions.get(pillar, {}).get(level, [])
            candidates.extend(q for q in qs if q.get("difficulty_tier") == "challenge")

        if not candidates:
            # Fallback to any question
            for pillar in PILLARS:
                candidates.extend(self._questions.get(pillar, {}).get(level, []))

        if not candidates:
            return None

        return rng.choice(candidates)

    @property
    def stats(self) -> dict:
        """Return content statistics."""
        result = {"total": 0, "by_pillar": {}}
        for pillar in PILLARS:
            pillar_total = 0
            by_level = {}
            for level in LEVELS:
                count = len(self._questions.get(pillar, {}).get(level, []))
                by_level[f"level{level}"] = count
                pillar_total += count
            result["by_pillar"][pillar] = {"total": pillar_total, **by_level}
            result["total"] += pillar_total
        return result


# ── Singleton ──────────────────────────────────────────────────────────────

pillar_store = PillarContentStore()


def init_pillar_store():
    """Initialize from env or default path."""
    content_dir = os.environ.get(
        "KIWIMATH_OLYMPIAD_V2_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "content" / "olympiad_v2"),
    )
    pillar_store.load(content_dir)
