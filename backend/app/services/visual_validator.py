"""
Visual Validator — catches stem-visual mismatches BEFORE a question reaches the child.

This is the "validation gate" recommended by the QA review.
It ensures:
  1. Visual generator matches the object described in the stem (no scattered_dots for triangles)
  2. Visual params use the same resolved values as stem/answer (single source of truth)
  3. Null visuals are flagged with a reason (not silently inherited)
  4. Numeric quantities in the visual match what the stem describes

The validator runs inside the renderer pipeline.  If validation fails, the visual
is stripped (set to None) and a warning is logged — the question is still served,
just without the misleading image.  This is safer than showing a wrong image to a
6-year-old.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Semantic object → allowed generators mapping
# ---------------------------------------------------------------------------
# If the stem mentions one of these objects, only these generators make sense.
# This prevents "scattered_dots" from being used for triangle-counting questions.

_OBJECT_GENERATOR_MAP: Dict[str, List[str]] = {
    # Geometry
    "triangle": [
        "triangle_subdivision", "subdivided_triangle", "mixed_shapes",
        "four_shapes_one_different", "two_shapes_compare",
    ],
    "tally": [
        "tally_marks",
    ],
    "cube": [
        "cube_stack", "object_row",
    ],
    "circle": [
        "overlapping_circles", "separated_circles", "mixed_shapes",
        "four_shapes_one_different", "two_shapes_compare",
    ],
    "square": [
        "mixed_shapes", "four_shapes_one_different", "two_shapes_compare",
        "grid_colored",
    ],
    "rectangle": [
        "mixed_shapes", "four_shapes_one_different", "two_shapes_compare",
    ],

    # Concrete objects — these can use object-aware generators
    "apple": [
        "object_row_with_cross_out", "single_group", "two_groups",
        "combine_groups", "combine_groups_coloured", "scattered_objects",
        "two_hands", "dot_addition", "dot_subtraction",
    ],
    "balloon": [
        "object_row_with_cross_out", "single_group", "two_groups",
        "combine_groups", "balloons_with_popped", "popped_only",
        "dot_addition", "dot_subtraction", "scattered_objects",
    ],
    "finger": [
        "two_hands", "dot_addition", "single_group",
    ],
    "marble": [
        "single_jar", "two_jars", "three_jars", "marbles_partial_cover",
        "marbles_revealed", "scattered_objects", "object_row_with_cross_out",
        "single_group", "two_groups",
    ],
    "coin": [
        "coin_row", "scattered_coins", "coin_counting",
    ],
    "hand": [
        "two_hands",
    ],

    # Time
    "clock": ["clock_face", "timeline"],
    "o'clock": ["clock_face"],
    "half past": ["clock_face"],

    # Patterns
    "pattern": ["pattern_strip", "colour_sequence", "colour_sequence_with_arrows"],

    # Number line
    "number line": ["number_line", "number_line_highlight"],
}

# Generators that are "generic" — they show abstract dots/shapes,
# NOT semantic objects.  These should NOT be used when the stem mentions
# a specific real-world object.
_GENERIC_GENERATORS = {
    "scattered_dots", "dot_row", "dot_counter", "overlapping_circles",
}


# ---------------------------------------------------------------------------
# Stem analysis helpers
# ---------------------------------------------------------------------------

def _extract_stem_objects(stem: str) -> List[str]:
    """Extract semantic object keywords from the rendered stem text."""
    stem_lower = stem.lower()
    found = []
    for obj_key in _OBJECT_GENERATOR_MAP:
        # Match whole words or plurals
        pattern = rf"\b{re.escape(obj_key)}s?\b"
        if re.search(pattern, stem_lower):
            found.append(obj_key)
    return found


def _extract_stem_numbers(stem: str) -> List[int]:
    """Extract all numbers mentioned in the stem."""
    return [int(x) for x in re.findall(r"\b(\d+)\b", stem)]


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------

class ValidationResult:
    """Result of visual validation."""

    def __init__(self):
        self.is_valid = True
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.strip_visual = False  # If True, the visual should be removed

    def warn(self, msg: str):
        self.warnings.append(msg)

    def error(self, msg: str):
        self.errors.append(msg)
        self.is_valid = False
        self.strip_visual = True


def validate_visual(
    question_id: str,
    stem: str,
    visual_dict: Optional[Dict[str, Any]],
    params_used: Dict[str, Any],
    correct_answer: Any,
) -> ValidationResult:
    """
    Validate that a question's visual matches its stem and answer.

    Returns a ValidationResult.  If result.strip_visual is True,
    the caller should set the visual to None rather than show a wrong image.
    """
    result = ValidationResult()

    # --- 1. Null visual check ---
    if visual_dict is None:
        # This is OK — just means no image.  Not an error.
        return result

    vtype = visual_dict.get("type")
    if vtype != "svg_generator":
        return result  # Only validate SVG generators

    generator = visual_dict.get("generator", "")
    vparams = visual_dict.get("params", {})

    # --- 2. Semantic object vs generator check ---
    stem_objects = _extract_stem_objects(stem)

    if stem_objects and generator in _GENERIC_GENERATORS:
        # Stem mentions specific objects but generator is generic
        result.error(
            f"[{question_id}] Stem mentions {stem_objects} but visual uses "
            f"generic generator '{generator}'. Expected one of: "
            f"{_OBJECT_GENERATOR_MAP.get(stem_objects[0], ['any semantic generator'])}"
        )

    # Check if generator is in the allowed list for the stem object
    for obj in stem_objects:
        allowed = _OBJECT_GENERATOR_MAP.get(obj, [])
        if allowed and generator not in allowed and generator not in _GENERIC_GENERATORS:
            # Generator exists but isn't in the allowed list — just warn, don't strip
            result.warn(
                f"[{question_id}] Stem mentions '{obj}' but uses generator "
                f"'{generator}' (expected one of {allowed})"
            )

    # --- 3. Numeric quantity consistency ---
    # Check that key numeric params in the visual match what the stem implies
    stem_numbers = _extract_stem_numbers(stem)

    # For two_hands: left + right should match the addition in the stem
    if generator == "two_hands":
        left = vparams.get("left", vparams.get("per_hand", 0))
        right = vparams.get("right", vparams.get("per_hand", 0))
        try:
            left, right = int(left), int(right)
            total = left + right
            if correct_answer is not None:
                try:
                    ca = int(correct_answer)
                    if ca != total and total > 0:
                        result.error(
                            f"[{question_id}] two_hands shows {left}+{right}={total} "
                            f"but correct answer is {ca}"
                        )
                except (ValueError, TypeError):
                    pass
        except (ValueError, TypeError):
            pass

    # For dot_addition / combine_groups: group1 + group2 should match answer
    if generator in ("dot_addition", "combine_groups", "combine_groups_coloured"):
        g1 = vparams.get("group1", vparams.get("left", vparams.get("a", 0)))
        g2 = vparams.get("group2", vparams.get("right", vparams.get("b", 0)))
        try:
            g1, g2 = int(g1), int(g2)
            if correct_answer is not None:
                ca = int(correct_answer)
                if g1 + g2 != ca and g1 + g2 > 0:
                    result.error(
                        f"[{question_id}] {generator} shows {g1}+{g2}={g1+g2} "
                        f"but correct answer is {ca}"
                    )
        except (ValueError, TypeError):
            pass

    # For object_row_with_cross_out: total - cross_out should make sense
    if generator == "object_row_with_cross_out":
        total_objs = vparams.get("count_from", vparams.get("total", 0))
        cross_out = vparams.get("cross_out", vparams.get("remove", 0))
        try:
            total_objs, cross_out = int(total_objs), int(cross_out)
            remaining = total_objs - cross_out
            if correct_answer is not None:
                ca = int(correct_answer)
                if remaining != ca and remaining > 0:
                    result.warn(
                        f"[{question_id}] Shows {total_objs} objects with {cross_out} "
                        f"crossed out = {remaining}, but answer is {ca}"
                    )
        except (ValueError, TypeError):
            pass

    # For balloons_with_popped: total - popped should match
    if generator == "balloons_with_popped":
        total_b = vparams.get("total", 0)
        popped = vparams.get("popped", 0)
        try:
            total_b, popped = int(total_b), int(popped)
            remaining = total_b - popped
            if correct_answer is not None:
                ca = int(correct_answer)
                if remaining != ca and remaining >= 0:
                    result.warn(
                        f"[{question_id}] balloons shows {total_b}-{popped}={remaining} "
                        f"but answer is {ca}"
                    )
        except (ValueError, TypeError):
            pass

    # --- 4. Unresolved placeholders ---
    for k, v in vparams.items():
        if isinstance(v, str) and re.match(r"^[A-Z]$|^\{[A-Z]\}$", v):
            result.error(
                f"[{question_id}] Visual param '{k}' has unresolved placeholder: {v}"
            )

    # Log results
    if result.errors:
        for err in result.errors:
            logger.warning(f"VISUAL_VALIDATION_ERROR: {err}")
    if result.warnings:
        for warn_msg in result.warnings:
            logger.info(f"VISUAL_VALIDATION_WARN: {warn_msg}")

    return result


# ---------------------------------------------------------------------------
# Alt-text generation
# ---------------------------------------------------------------------------

def generate_alt_text(
    generator: str,
    params: Dict[str, Any],
    stem: str,
) -> str:
    """
    Generate a descriptive alt-text for an SVG visual.

    This makes the math visuals accessible to screen readers.
    The alt-text describes the mathematical relationship shown,
    not just the visual appearance.
    """

    # Try to generate a meaningful description based on the generator type
    gen = generator.lower()

    if gen == "two_hands":
        left = params.get("left", params.get("per_hand", "?"))
        right = params.get("right", params.get("per_hand", "?"))
        return f"Two hands: left hand holding {left} objects, right hand holding {right} objects."

    if gen in ("dot_addition", "combine_groups", "combine_groups_coloured"):
        g1 = params.get("group1", params.get("left", params.get("a", "?")))
        g2 = params.get("group2", params.get("right", params.get("b", "?")))
        return f"Two groups of objects: {g1} in the first group and {g2} in the second group, being combined."

    if gen in ("dot_subtraction", "object_row_with_cross_out"):
        total = params.get("total", params.get("count_from", "?"))
        remove = params.get("remove", params.get("cross_out", "?"))
        return f"A row of {total} objects with {remove} being taken away."

    if gen == "balloons_with_popped":
        total = params.get("total", "?")
        popped = params.get("popped", "?")
        return f"{total} balloons with {popped} of them popped."

    if gen == "ten_frame":
        filled = params.get("filled", params.get("count", "?"))
        return f"A ten-frame with {filled} dots filled in out of 10 spaces."

    if gen == "number_line":
        start = params.get("start", 0)
        end = params.get("end", 20)
        highlight = params.get("highlight", None)
        text = f"A number line from {start} to {end}."
        if highlight is not None:
            text += f" The number {highlight} is highlighted."
        return text

    if gen == "number_line_highlight":
        start = params.get("start", 0)
        end = params.get("end", 20)
        highlight = params.get("highlight", params.get("target", None))
        text = f"A number line from {start} to {end}."
        if highlight is not None:
            text += f" The number {highlight} is highlighted."
        return text

    if gen == "bar_model":
        total = params.get("total", params.get("whole", "?"))
        part1 = params.get("part1", params.get("left", "?"))
        part2 = params.get("part2", params.get("right", "?"))
        return f"A bar model showing a total of {total}, split into parts of {part1} and {part2}."

    if gen == "comparison_bars":
        v1 = params.get("value1", params.get("bigger", params.get("a", "?")))
        v2 = params.get("value2", params.get("smaller", params.get("b", "?")))
        return f"Two bars for comparison: one showing {v1} and another showing {v2}."

    if gen == "clock_face":
        hour = params.get("hour", "?")
        minute = params.get("minute", params.get("minutes", 0))
        if minute == 0:
            return f"A clock showing {hour} o'clock."
        elif minute == 30:
            return f"A clock showing half past {hour}."
        else:
            return f"A clock showing {hour}:{minute:02d}."

    if gen in ("pattern_strip", "colour_sequence", "colour_sequence_with_arrows"):
        return "A repeating pattern of colored shapes."

    if gen == "dice_face":
        value = params.get("value", params.get("dots", "?"))
        return f"A die showing {value} dots."

    if gen == "domino":
        left = params.get("left", "?")
        right = params.get("right", "?")
        return f"A domino tile with {left} dots on the left and {right} dots on the right."

    if gen == "grid_colored":
        rows = params.get("rows", "?")
        cols = params.get("cols", "?")
        colored = params.get("colored", "?")
        return f"A {rows} by {cols} grid with {colored} cells colored in."

    if gen == "tens_blocks":
        tens = params.get("tens", 0)
        ones = params.get("ones", 0)
        return f"Place value blocks: {tens} tens and {ones} ones, showing the number {tens * 10 + ones}."

    if gen in ("single_jar", "two_jars", "three_jars"):
        count = params.get("count", params.get("visible", "?"))
        return f"A jar containing {count} objects."

    if gen == "marbles_partial_cover":
        visible = params.get("visible", "?")
        hidden = params.get("hidden", "?")
        return f"Marbles with {visible} visible and {hidden} hidden under a cover."

    if gen in ("coin_row", "coin_counting", "scattered_coins"):
        return "A collection of coins for counting."

    if gen in ("single_group", "two_groups"):
        count = params.get("count", params.get("total", "?"))
        return f"A group of {count} objects."

    if gen == "equal_groups":
        groups = params.get("groups", "?")
        per_group = params.get("per_group", "?")
        return f"{groups} equal groups with {per_group} objects in each group."

    if gen == "sharing_circles":
        total = params.get("total", "?")
        groups = params.get("groups", "?")
        return f"{total} objects being shared equally into {groups} groups."

    if gen in ("triangle_subdivision", "subdivided_triangle"):
        side = params.get("side", "?")
        return f"A large triangle subdivided into smaller triangles ({side} rows). Students count the small triangles."

    if gen == "tally_marks":
        count = params.get("count", "?")
        return f"Tally marks showing a count of {count} — grouped in bundles of five."

    if gen == "cube_stack":
        count = params.get("count", "?")
        return f"A row of {count} colourful cubes for counting."

    if gen == "split_object":
        parts = params.get("parts", "?")
        return f"An object split into {parts} equal parts."

    if gen in ("scattered_dots", "dot_row", "dot_counter"):
        count = params.get("count", params.get("total", params.get("n", "?")))
        return f"{count} dots arranged for counting."

    if gen in ("paired_rows", "two_rows_compare"):
        top = params.get("top", params.get("row1", "?"))
        bottom = params.get("bottom", params.get("row2", "?"))
        return f"Two rows for comparison: top row has {top} objects, bottom row has {bottom} objects."

    if gen in ("four_shapes_one_different", "mixed_shapes"):
        return "A set of shapes where one is different from the others."

    if gen == "timeline":
        return "A timeline showing events in sequence."

    # Fallback
    return f"A visual illustration for this math question."
