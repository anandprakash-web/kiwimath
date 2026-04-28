"""
v3b Content Adapter — converts Kiwimath v3b JSON files to backend Pydantic model format.

The v3b content files use a different schema than the backend expects:
  - Different ID format (G1-CH01-CO-001 vs G1-COUNT-001)
  - Free-text topic field vs Topic enum
  - Nested content structure vs flat top-level fields
  - Varying param formats (pool/range/type/formula/default/etc.)
  - Distractors with {formula, label, diag} or {value, rationale} format
  - Misconceptions with extra fields (trigger_pattern, socratic_nudge)
  - Missing required fields (subskills, tier, version int, etc.)

This module bridges the gap so v3b files can be loaded through the existing models.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Union


# ---------------------------------------------------------------------------
# Topic mapping: free-text v3b topic -> backend Topic enum value
# ---------------------------------------------------------------------------

# Exhaustive mapping from v3b free-text topics to backend enum values.
# Topics that don't fit existing enums get new enum values (added to Topic).
_TOPIC_MAP: Dict[str, str] = {
    # counting_observation
    "counting objects": "counting_observation",
    "attribute counting": "counting_observation",
    "subitizing": "counting_observation",
    "lateral counting": "counting_observation",
    "counting down": "counting_observation",
    "counting up": "counting_observation",
    "counting arrangements": "counting_observation",
    "organized counting": "counting_observation",
    "one for one": "counting_observation",
    "sorting": "counting_observation",
    "counting by 10s": "counting_observation",

    # arithmetic_missing_numbers
    "missing numbers": "arithmetic_missing_numbers",
    "mystery numbers": "arithmetic_missing_numbers",
    "number bonds": "arithmetic_missing_numbers",
    "cryptarithms": "arithmetic_missing_numbers",

    # patterns_sequences
    "pattern discovery": "patterns_sequences",
    "shape patterns": "patterns_sequences",
    "growing patterns": "patterns_sequences",
    "number patterns": "patterns_sequences",
    "hundred chart patterns": "patterns_sequences",
    "special patterns": "patterns_sequences",
    "units digit patterns": "patterns_sequences",
    "arithmetic sequences": "patterns_sequences",
    "geometric sequences": "patterns_sequences",
    "finding the nth term": "patterns_sequences",
    "number sequence": "patterns_sequences",
    "skip counting": "patterns_sequences",
    "skip-count by 2s, 5s, 10s": "patterns_sequences",
    "skip-count by 3s, 4s, 6s": "patterns_sequences",
    "skip-count from any number": "patterns_sequences",
    "patterns in squares": "patterns_sequences",
    "hundred chart": "patterns_sequences",

    # logic_ordering
    "logic puzzles": "logic_ordering",
    "if-then statements": "logic_ordering",
    "venn diagrams": "logic_ordering",
    "yes/no questions": "logic_ordering",
    "organized lists": "logic_ordering",
    "puzzles": "logic_ordering",
    "math meet puzzles": "logic_ordering",
    "pathfinding": "logic_ordering",
    "spatial pathfinding": "logic_ordering",
    "spatial paths": "logic_ordering",

    # spatial_reasoning_3d
    "identifying solids": "spatial_reasoning_3d",
    "nets": "spatial_reasoning_3d",
    "volume of prisms": "spatial_reasoning_3d",
    "surface area": "spatial_reasoning_3d",

    # shapes_folding_symmetry
    "shape names": "shapes_folding_symmetry",
    "shape definitions": "shapes_folding_symmetry",
    "line symmetry": "shapes_folding_symmetry",
    "symmetry": "shapes_folding_symmetry",
    "spins & flips": "shapes_folding_symmetry",
    "turns": "shapes_folding_symmetry",
    "polygon properties": "shapes_folding_symmetry",
    "quadrilaterals": "shapes_folding_symmetry",
    "triangles": "shapes_folding_symmetry",
    "polyominoes": "shapes_folding_symmetry",
    "building squares": "shapes_folding_symmetry",

    # word_problems
    "word problems": "word_problems",
    "story problems": "word_problems",
    "multi-step problems": "word_problems",
    "fraction story problems": "word_problems",
    "fraction word problems": "word_problems",
    "fraction \"of\" problems": "word_problems",
    "drawing a picture": "word_problems",
    "act it out": "word_problems",
    "guess and check": "word_problems",
    "working backwards": "word_problems",
    "making a list": "word_problems",

    # number_puzzles_grids
    "dots and boxes": "number_puzzles_grids",
    "comparison puzzle": "number_puzzles_grids",
    "binary numbers": "number_puzzles_grids",
    "fair games": "number_puzzles_grids",
    "triangular numbers": "number_puzzles_grids",
    "square numbers": "number_puzzles_grids",

    # place_value
    "place value": "place_value",
    "digits & places": "place_value",
    "reading numbers": "place_value",
    "expanded form": "place_value",
    "place value add": "place_value",
    "place value ordering": "place_value",
    "place value patterns": "place_value",
    "place value strategies": "place_value",
    "thousands & beyond": "place_value",
    "rounding": "place_value",
    "rounding & estimating": "place_value",
    "decimal place value": "place_value",

    # time_measurement
    "time": "time_measurement",
    "days & time": "time_measurement",
    "ruler": "time_measurement",
    "using a ruler": "time_measurement",
    "lengths": "time_measurement",
    "comparing lengths": "time_measurement",
    "units of length": "time_measurement",
    "weight and capacity": "time_measurement",
    "using units": "time_measurement",
    "unit conversions": "time_measurement",
    "converting units": "time_measurement",
    "unit conversion chains": "time_measurement",
    "square units": "time_measurement",

    # money_currency
    "coins & sharing": "money_currency",

    # comparison_ordering
    "more or less": "comparison_ordering",
    "ordering": "comparison_ordering",
    "comparing big numbers": "comparison_ordering",
    "comparing differences": "comparison_ordering",
    "comparing expressions": "comparison_ordering",
    "comparing decimals": "comparison_ordering",
    "comparing fractions": "comparison_ordering",
    "comparing integers": "comparison_ordering",
    "comparison tricks": "comparison_ordering",
    "using < > =": "comparison_ordering",
    "closest to": "comparison_ordering",
    "location": "comparison_ordering",
    "directions": "comparison_ordering",
    "number line": "comparison_ordering",
    "distance between numbers": "comparison_ordering",

    # --- New enum values for topics that don't fit existing categories ---

    # addition_subtraction
    "addition basics": "addition_subtraction",
    "adding multiple": "addition_subtraction",
    "adding tens": "addition_subtraction",
    "stacking addition": "addition_subtraction",
    "stacking subtraction": "addition_subtraction",
    "stacking three numbers": "addition_subtraction",
    "checking with addition": "addition_subtraction",
    "taking away": "addition_subtraction",
    "subtracting in parts": "addition_subtraction",
    "subtraction order": "addition_subtraction",
    "subtract 10": "addition_subtraction",
    "finding difference": "addition_subtraction",
    "doubles & near-doubles": "addition_subtraction",
    "making 10s and 100s": "addition_subtraction",
    "breaking apart": "addition_subtraction",
    "breaking & regrouping": "addition_subtraction",
    "regrouping": "addition_subtraction",
    "compensation": "addition_subtraction",
    "add-sub connection": "addition_subtraction",
    "add/sub patterns": "addition_subtraction",
    "adding/subtracting 1, 10, 100": "addition_subtraction",
    "adding three numbers": "addition_subtraction",
    "multi-borrow subtraction": "addition_subtraction",
    "commutative property": "addition_subtraction",
    "commutativity": "addition_subtraction",
    "apart & together": "addition_subtraction",

    # multiplication_division
    "meaning of multiplication": "multiplication_division",
    "meaning of division": "multiplication_division",
    "times tables 1-10": "multiplication_division",
    "division facts": "multiplication_division",
    "division with remainders": "multiplication_division",
    "long division": "multiplication_division",
    "multi-digit × 1-digit": "multiplication_division",
    "multi-digit × multi-digit": "multiplication_division",
    "two-digit × one-digit": "multiplication_division",
    "multiplying by multiples of 10": "multiplication_division",
    "multiplying with zeros": "multiplication_division",
    "special quotients": "multiplication_division",
    "teamwork division": "multiplication_division",
    "multiplication principle": "multiplication_division",
    "breaking apart rectangles": "multiplication_division",
    "all four operations": "multiplication_division",
    "basic facts review": "multiplication_division",

    # fractions_decimals
    "what is a fraction?": "fractions_decimals",
    "fractions on number line": "fractions_decimals",
    "equivalent fractions": "fractions_decimals",
    "mixed numbers": "fractions_decimals",
    "adding same denominator": "fractions_decimals",
    "adding different denominator": "fractions_decimals",
    "basic fraction addition": "fractions_decimals",
    "multiplying fractions": "fractions_decimals",
    "dividing by fractions": "fractions_decimals",
    "simplifying before multiplying": "fractions_decimals",
    "canceling": "fractions_decimals",
    "fraction of a whole number": "fractions_decimals",
    "fraction-decimal conversion": "fractions_decimals",
    "decimal-fraction conversions": "fractions_decimals",
    "decimal operations": "fractions_decimals",
    "decimal × decimal": "fractions_decimals",
    "decimal ÷ decimal": "fractions_decimals",

    # estimation_mental_math
    "estimation": "estimation_mental_math",
    "estimation games": "estimation_mental_math",
    "estimating sums and differences": "estimation_mental_math",
    "estimating products": "estimation_mental_math",
    "estimating square roots": "estimation_mental_math",
    "strategies": "estimation_mental_math",
    "strategies review": "estimation_mental_math",

    # area_perimeter
    "perimeter": "area_perimeter",
    "perimeter intro": "area_perimeter",
    "area by counting": "area_perimeter",
    "area of rectangles": "area_perimeter",
    "area of complex shapes": "area_perimeter",
    "area and perimeter together": "area_perimeter",
    "same perimeter, different area": "area_perimeter",
    "missing side lengths": "area_perimeter",
    "right triangle area": "area_perimeter",

    # data_probability
    "reading graphs": "data_probability",
    "organizing data": "data_probability",
    "misleading graphs": "data_probability",
    "mean, median, mode": "data_probability",
    "range and outliers": "data_probability",
    "likelihood": "data_probability",
    "computing probability": "data_probability",
    "compound events": "data_probability",

    # number_theory
    "even numbers": "number_theory",
    "odd numbers": "number_theory",
    "factor pairs": "number_theory",
    "factor trees": "number_theory",
    "finding all factors": "number_theory",
    "prime numbers": "number_theory",
    "prime factorization": "number_theory",
    "divisibility rules": "number_theory",
    "divisibility challenges": "number_theory",
    "gcf": "number_theory",
    "lcm": "number_theory",
    "number categories": "number_theory",

    # exponents_roots
    "understanding exponents": "exponents_roots",
    "exponent basics review": "exponents_roots",
    "exponent rules intro": "exponents_roots",
    "exponent rules": "exponents_roots",
    "powers of 2 and 10": "exponents_roots",
    "powers of negatives": "exponents_roots",
    "zero and negative exponents": "exponents_roots",
    "perfect square roots": "exponents_roots",
    "simplifying square roots": "exponents_roots",
    "scientific notation intro": "exponents_roots",
    "pythagorean theorem intro": "exponents_roots",

    # integers_negatives
    "negative numbers": "integers_negatives",
    "absolute value": "integers_negatives",
    "adding integers": "integers_negatives",
    "subtracting integers": "integers_negatives",
    "integer arithmetic": "integers_negatives",
    "order of operations with integers": "integers_negatives",

    # algebra_expressions
    "what is a variable?": "algebra_expressions",
    "writing expressions": "algebra_expressions",
    "reading expressions": "algebra_expressions",
    "evaluating": "algebra_expressions",
    "evaluating expressions": "algebra_expressions",
    "simplifying expressions": "algebra_expressions",
    "parentheses": "algebra_expressions",
    "order of operations": "algebra_expressions",
    "writing equations": "algebra_expressions",
    "solving for unknowns": "algebra_expressions",
    "solving one-step equations": "algebra_expressions",
    "two-step equations": "algebra_expressions",
    "checking solutions": "algebra_expressions",
    "rearranging": "algebra_expressions",
    "infinity": "algebra_expressions",
    "computing with big numbers": "algebra_expressions",

    # ratios_percents
    "understanding ratios": "ratios_percents",
    "equivalent ratios": "ratios_percents",
    "unit rates": "ratios_percents",
    "understanding percents": "ratios_percents",
    "percent calculations": "ratios_percents",
    "percent increase/decrease": "ratios_percents",
    "percent proportions": "ratios_percents",

    # angles_geometry
    "angles": "angles_geometry",
    "angles (degrees)": "angles_geometry",
    "angle relationships": "angles_geometry",
}


def map_topic(free_text: str) -> str:
    """Map a v3b free-text topic to a Topic enum value.

    Returns the enum value string. Falls back to a slugified version
    of the free text if no mapping exists.
    """
    key = free_text.strip().lower()
    if key in _TOPIC_MAP:
        return _TOPIC_MAP[key]
    # Fallback: slugify the topic
    slug = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    return slug


# ---------------------------------------------------------------------------
# ID normalization
# ---------------------------------------------------------------------------

# v3b parent: G1-CH01-CO-001   step-down: G1-CH01-CO-001-S1
_V3B_PARENT_RE = re.compile(r"^G(\d)-CH(\d{2})-([A-Za-z0-9]+)-(\d{3})$")
_V3B_STEP_RE = re.compile(r"^G(\d)-CH(\d{2})-([A-Za-z0-9]+)-(\d{3})-S(\d)$")


def _chapter_slug_to_topic_slug(chapter_slug: str, topic_enum: str) -> str:
    """Convert a topic enum value to an uppercase slug suitable for IDs.

    E.g. 'counting_observation' -> 'COUNT', 'addition_subtraction' -> 'ADDSUB'
    """
    _ENUM_TO_ID_SLUG = {
        "counting_observation": "COUNT",
        "arithmetic_missing_numbers": "AMISS",
        "patterns_sequences": "PATT",
        "logic_ordering": "LOGIC",
        "spatial_reasoning_3d": "SPAT3D",
        "shapes_folding_symmetry": "SHAPE",
        "word_problems": "WPROB",
        "number_puzzles_grids": "NPUZZ",
        "place_value": "PLVAL",
        "time_measurement": "TIMEM",
        "money_currency": "MONEY",
        "comparison_ordering": "CMPORD",
        "addition_subtraction": "ADDSUB",
        "multiplication_division": "MULDIV",
        "fractions_decimals": "FRDEC",
        "estimation_mental_math": "ESTIM",
        "area_perimeter": "AREAP",
        "data_probability": "DPROB",
        "number_theory": "NUMTH",
        "exponents_roots": "EXPRT",
        "integers_negatives": "INTNEG",
        "algebra_expressions": "ALGEX",
        "ratios_percents": "RATPC",
        "angles_geometry": "ANGLE",
    }
    return _ENUM_TO_ID_SLUG.get(topic_enum, chapter_slug.upper())


def normalize_id(v3b_id: str, topic_enum: str) -> str:
    """Convert a v3b ID to backend format.

    v3b:     G1-CH01-CO-001     -> backend: G1-CH01-CO-001  (kept as-is with new regex)
    We keep the v3b ID format since we're updating the regex to accept it.
    """
    return v3b_id


# ---------------------------------------------------------------------------
# Answer type mapping
# ---------------------------------------------------------------------------

_ANSWER_TYPE_MAP = {
    "multiple_choice": "multiple_choice",
    "numerical_input": "numeric_input",
    "tap_to_count": "tap_to_select",
    "sequence_input": "numeric_input",
    "equation_input": "numeric_input",
    "fraction_input": "numeric_input",
    "quotient_remainder": "numeric_input",
    "decimal_input": "numeric_input",
    "mixed_number_input": "numeric_input",
}


def _map_answer_type(v3b_type: str) -> str:
    """Map v3b answer_type to backend AnswerType enum value."""
    return _ANSWER_TYPE_MAP.get(v3b_type, "multiple_choice")


# ---------------------------------------------------------------------------
# Status mapping
# ---------------------------------------------------------------------------

_STATUS_MAP = {
    "production": "approved",
    "production_enriched": "approved",
    "draft": "draft",
    "review": "review",
}


def _map_status(v3b_status: Optional[str]) -> str:
    """Map v3b status to backend Status enum value."""
    if not v3b_status:
        return "draft"
    return _STATUS_MAP.get(v3b_status, "draft")


# ---------------------------------------------------------------------------
# Param conversion
# ---------------------------------------------------------------------------

def _normalize_constraint(raw: str, all_param_names: List[str] = None) -> Optional[str]:
    """Convert English-like constraints to Python expressions for safe_eval.

    Returns None if the constraint can't be meaningfully converted (skip it).
    """
    if not raw or not isinstance(raw, str):
        return None

    c = raw.strip()

    # Convert "if X then Y" patterns first (before character filtering).
    import re as _re
    if_then = _re.match(r"if\s+(.+?)\s+then\s+(.+)", c, _re.IGNORECASE)
    if if_then:
        condition, consequence = if_then.group(1), if_then.group(2)
        return f"(not ({condition})) or ({consequence})"

    # Already looks like a valid Python expression
    # Quick test: if it only contains identifiers, operators, numbers, parens, quotes
    if all(ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_<>=!+*/-() .,&|'\"" for ch in c):
        pass  # Fall through to further checks

    # "all distinct" -> n1 != n2 and n1 != n3 and n2 != n3
    if "all distinct" in c.lower():
        # Can't generate without knowing the param names; skip
        return None

    # "X is even" -> "X % 2 == 0"
    import re as _re
    even_match = _re.match(r"(\w+)\s+is\s+even", c)
    if even_match:
        return f"{even_match.group(1)} % 2 == 0"

    # "X is 2-digit" -> "X >= 10 and X <= 99"
    digit_match = _re.match(r"(\w+)\s+is\s+(\d+)-digit", c)
    if digit_match:
        var, digits = digit_match.group(1), int(digit_match.group(2))
        lo = 10 ** (digits - 1)
        hi = 10 ** digits - 1
        return f"{var} >= {lo} and {var} <= {hi}"

    # "multiple of N" -> skip (too ambiguous without context)
    if "multiple of" in c.lower():
        return None

    # English phrases we can't parse -> skip
    for skip_phrase in [
        "no borrowing", "all digits nonzero", "same parity",
        "different_from", "divisible_by", "valid triangle",
        "start is a", "sum and diff",
    ]:
        if skip_phrase in c.lower():
            return None

    # If it looks like it could be a Python expression, return as-is
    # (the renderer will catch eval errors gracefully)
    return c


def _convert_param(key: str, spec: Any) -> Dict[str, Any]:
    """Convert a v3b param spec to ParamPool or ParamRange format.

    v3b param variants:
      - {"pool": [...]}  -> ParamPool
      - {"range": [lo, hi]}  -> ParamRange
      - {"type": "pool", "pool": [...]}  -> ParamPool
      - {"type": "integer", "range": [lo, hi]}  -> ParamRange
      - {"min": lo, "max": hi}  -> ParamRange
      - {"formula": "..."}  -> ParamPool with single value
      - {"default": val}  -> ParamPool with single value
      - {"value": val}  -> ParamPool with single value
      - {"values": [...]}  -> ParamPool
      - {"inherit_from_parent": true}  -> ParamInherit
      - bool True  -> ParamInherit (for step-down shorthand)
    """
    if isinstance(spec, bool) and spec:
        return {"inherit_from_parent": True}

    if not isinstance(spec, dict):
        # Scalar default
        return {"pool": [spec]}

    # Inherit
    if spec.get("inherit_from_parent"):
        return {"inherit_from_parent": True}

    # Pool-style
    if "pool" in spec:
        pool = spec["pool"]
        # Flatten nested lists: [["A","B","C"]] -> ["A","B","C"]
        # and convert non-scalar items to strings
        flat_pool = []
        for item in pool:
            if isinstance(item, list):
                flat_pool.extend(str(x) for x in item)
            else:
                flat_pool.append(item)
        result: Dict[str, Any] = {"pool": flat_pool}
        if "constraint" in spec:
            nc = _normalize_constraint(spec["constraint"])
            if nc:
                result["constraint"] = nc
        return result

    if "values" in spec:
        result = {"pool": spec["values"]}
        if "constraint" in spec:
            nc = _normalize_constraint(spec["constraint"])
            if nc:
                result["constraint"] = nc
        return result

    # Range-style -- only if both endpoints are actual integers
    if "range" in spec:
        r = spec["range"]
        if (
            isinstance(r, list) and len(r) == 2
            and isinstance(r[0], int) and isinstance(r[1], int)
        ):
            result = {"range": r}
            if "constraint" in spec:
                nc = _normalize_constraint(spec["constraint"])
                if nc:
                    result["constraint"] = nc
            return result
        else:
            # Range has non-integer bounds (e.g. "denom - 1"); treat as pool
            return {"pool": [str(v) for v in r]}

    if "min" in spec and "max" in spec:
        lo, hi = spec["min"], spec["max"]
        if isinstance(lo, int) and isinstance(hi, int):
            result = {"range": [lo, hi]}
            if "constraint" in spec:
                nc = _normalize_constraint(spec["constraint"])
                if nc:
                    result["constraint"] = nc
            return result
        else:
            return {"pool": [str(lo), str(hi)]}

    # Formula or default -> treat as pool with a single computed value
    if "formula" in spec:
        return {"pool": [spec["formula"]]}

    if "default" in spec:
        return {"pool": [spec["default"]]}

    if "value" in spec:
        return {"pool": [spec["value"]]}

    # Options list (another pool variant)
    if "options" in spec:
        return {"pool": spec["options"]}

    # Fallback: wrap the whole thing as a pool with placeholder
    return {"pool": ["__unknown__"]}


def _map_to_ternary(map_dict: Dict[str, Any], lookup_keys: List[str]) -> str:
    """Convert a map dict to a chained ternary expression for safe_eval.

    Example:
        map_dict = {"rectangle": 2, "hexagon": 6, "big square": 4, "trapezoid": 3}
        lookup_keys = ["big_shape"]
        -> "2 if big_shape == 'rectangle' else 6 if big_shape == 'hexagon' else ..."

    For compound keys (e.g. "triangle_rectangle"):
        lookup_keys = ["small_shape", "big_shape"]
        The key is split by '_' and matched against the concatenation of lookup params.
        We build the ternary using string equality on the individual parts.
    """
    items = list(map_dict.items())
    if not items:
        return "0"

    if len(lookup_keys) == 1:
        # Simple single-key lookup
        var = lookup_keys[0]
        # Build chained ternary: val0 if var == 'key0' else val1 if var == 'key1' else ...
        parts = []
        for k, v in items[:-1]:
            parts.append(f"{v} if {var} == '{k}' else ")
        # Last item is the default
        parts.append(str(items[-1][1]))
        return "".join(parts)
    else:
        # Compound key: build condition checking all parts
        # For "triangle_rectangle" with lookup_keys ["small_shape", "big_shape"],
        # we need: val if (small_shape == 'triangle' and big_shape == 'rectangle') else ...
        parts = []
        for k, v in items[:-1]:
            key_parts = k.split("_", len(lookup_keys) - 1)
            if len(key_parts) != len(lookup_keys):
                # Key doesn't split cleanly; try the whole key against first var
                cond = f"{lookup_keys[0]} == '{k}'"
            else:
                conditions = [f"{var} == '{kp}'" for var, kp in zip(lookup_keys, key_parts)]
                cond = " and ".join(conditions)
            parts.append(f"{v} if ({cond}) else ")
        parts.append(str(items[-1][1]))
        return "".join(parts)


def _infer_map_lookup_keys(
    param_name: str,
    map_keys: List[str],
    all_param_names: List[str],
    all_params: Dict[str, Any],
) -> List[str]:
    """Infer which other params a map's keys reference.

    Strategy:
      1. Collect pool values from all candidate params.
      2. If map keys directly match a single param's pool values, use that param.
      3. If map keys contain '_', try splitting and matching parts to param pools.
      4. Fall back to using the first other param that has a pool.
    """
    # Collect candidate params (all params except this map param itself)
    candidates = [p for p in all_param_names if p != param_name]

    # Build pool-value sets for each candidate param
    param_pools: Dict[str, set] = {}
    for c in candidates:
        spec = all_params.get(c, {})
        if isinstance(spec, dict):
            pool = spec.get("pool", [])
            if pool:
                param_pools[c] = set(str(v) for v in pool)

    # Single-key match: check if all map keys match a single param's pool
    map_key_set = set(map_keys)
    for c in candidates:
        if c in param_pools and map_key_set <= param_pools[c]:
            return [c]

    # Compound key: try splitting map keys and matching parts to params
    has_underscores = any("_" in k for k in map_keys)
    if has_underscores and len(candidates) >= 2:
        first_key = map_keys[0]
        # Try splitting with 2, 3, ... parts
        for n_parts in range(2, len(candidates) + 1):
            parts = first_key.split("_", n_parts - 1)
            if len(parts) != n_parts:
                continue
            # Try to find a param whose pool contains each part
            matched_params: List[str] = []
            used: set = set()
            for part in parts:
                found = False
                for c in candidates:
                    if c in used:
                        continue
                    if c in param_pools and part in param_pools[c]:
                        matched_params.append(c)
                        used.add(c)
                        found = True
                        break
                if not found:
                    break
            if len(matched_params) == n_parts:
                return matched_params

    # Default: first candidate with a pool
    for c in candidates:
        if c in param_pools:
            return [c]
    if candidates:
        return [candidates[0]]
    return [param_name]


def _convert_params(v3b_params: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Convert all params from v3b format to backend format.

    Returns (params_dict, map_derived_dict) where map_derived_dict contains
    derived formulas for any map-type params.

    Special case: step-down files may have {"inherit_from_parent": true}
    as the entire params dict (not per-key).
    """
    if not v3b_params:
        return {}, {}

    # Step-down shorthand: entire params is {"inherit_from_parent": true}
    # We return an empty dict here; the main adapt_v3b function will
    # fill in individual inherit entries from the stem_template placeholders.
    if v3b_params.get("inherit_from_parent") is True and len(v3b_params) == 1:
        return {}, {}

    all_param_names = [k for k in v3b_params.keys() if k != "inherit_from_parent"]
    result = {}
    map_derived: Dict[str, str] = {}

    for key, spec in v3b_params.items():
        if key in ("inherit_from_parent",):
            continue
        # Handle map-type params: convert to derived ternary expressions
        if isinstance(spec, dict) and "map" in spec and isinstance(spec["map"], dict):
            map_dict = spec["map"]
            map_keys = list(map_dict.keys())
            lookup_keys = _infer_map_lookup_keys(key, map_keys, all_param_names, v3b_params)
            map_derived[key] = _map_to_ternary(map_dict, lookup_keys)
            continue
        result[key] = _convert_param(key, spec)

    return result, map_derived


# ---------------------------------------------------------------------------
# Distractor conversion
# ---------------------------------------------------------------------------

def _convert_distractors(v3b_distractors: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Convert v3b distractors to backend {formula, label} format.

    v3b variants:
      - {"formula": "N-1", "label": "off_by_one", "diag": "..."}
      - {"value": "A*B", "rationale": "Product without simplification"}
      - {"value_expr": "...", "reason": "..."}
    """
    result = []
    seen_formulas = set()
    seen_labels = set()

    for i, d in enumerate(v3b_distractors):
        formula = d.get("formula") or d.get("value") or d.get("value_expr") or f"distractor_{i}"

        # Convert IF/THEN/ELSE pseudo-code in distractor formulas
        if isinstance(formula, str):
            formula = _convert_if_then_else(formula)

        # Generate label: use existing label or slugify the rationale/diag
        label = d.get("label")
        if not label:
            text = d.get("rationale") or d.get("diag") or d.get("reason") or f"distractor_{i}"
            label = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]

        # Ensure uniqueness
        base_formula = formula
        counter = 2
        while formula in seen_formulas:
            formula = f"{base_formula}_{counter}"
            counter += 1
        seen_formulas.add(formula)

        base_label = label
        counter = 2
        while label in seen_labels:
            label = f"{base_label}_{counter}"
            counter += 1
        seen_labels.add(label)

        result.append({"formula": str(formula), "label": label})

    return result


# ---------------------------------------------------------------------------
# Misconception conversion
# ---------------------------------------------------------------------------

def _slugify_diagnosis(text: str) -> str:
    """Convert free-text diagnosis to snake_case for backend regex validation."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    # Ensure it starts with a letter
    if slug and not slug[0].isalpha():
        slug = "d_" + slug
    return slug[:60] or "unknown_diagnosis"


def _truncate_feedback(text: str, max_len: int = 120, max_words: int = 18) -> str:
    """Truncate feedback_child to max_len characters and max_words while keeping it readable.

    Backend hard cap: 120 chars, 20 words. We target 18 words to leave margin.
    """
    # First truncate by word count
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words])
        if not text.endswith((".", "!", "?")):
            text += "."
    # Then truncate by character length
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rsplit(" ", 1)[0] + "..."


def _convert_misconceptions(
    v3b_misconceptions: List[Dict[str, Any]],
    distractor_formulas: List[str],
    question_id: str,
) -> List[Dict[str, Any]]:
    """Convert v3b misconceptions to backend format.

    Backend requires:
      - trigger_answer: must match a distractor formula
      - diagnosis: snake_case
      - feedback_child: max 120 chars
      - step_down_path: list of step-down IDs

    v3b may have trigger_answer=None and trigger_pattern instead.
    """
    result = []

    for i, m in enumerate(v3b_misconceptions):
        # trigger_answer: use existing or map from distractor formulas
        trigger_answer = m.get("trigger_answer")
        if trigger_answer is None or str(trigger_answer) == "None":
            # Try to match by index to distractor formulas
            if i < len(distractor_formulas):
                trigger_answer = distractor_formulas[i]
            elif distractor_formulas:
                trigger_answer = distractor_formulas[i % len(distractor_formulas)]
            else:
                trigger_answer = f"unknown_{i}"

        trigger_answer = str(trigger_answer)

        # diagnosis: slugify
        raw_diagnosis = m.get("diagnosis", m.get("trigger_pattern", f"misconception_{i}"))
        diagnosis = _slugify_diagnosis(raw_diagnosis)

        # feedback_child: truncate
        feedback = m.get("feedback_child", raw_diagnosis)
        feedback_child = _truncate_feedback(feedback)

        # step_down_path
        step_down_path = m.get("step_down_path", [])
        if not step_down_path:
            # Generate default step-down path
            step_down_path = [f"{question_id}-S1"]

        result.append({
            "trigger_answer": trigger_answer,
            "diagnosis": diagnosis,
            "feedback_child": feedback_child,
            "step_down_path": step_down_path,
        })

    return result


# ---------------------------------------------------------------------------
# Visual conversion
# ---------------------------------------------------------------------------

def _convert_visual(v3b_visual: Any) -> Optional[Dict[str, Any]]:
    """Convert v3b visual to backend SvgGeneratorVisual or StaticAssetVisual.

    v3b visual can be:
      - {"question": {...}, "hint": {...}, "step_down": {...}}  (multi-part)
      - {"type": "SVG", "description": "...", "generator": "..."}  (single)

    Backend expects: {"type": "svg_generator", "generator": "...", "params": {}}
    """
    if not v3b_visual:
        return None

    # Multi-part: extract the question visual
    if "question" in v3b_visual:
        vis = v3b_visual["question"]
    elif "type" in v3b_visual:
        vis = v3b_visual
    else:
        return None

    generator = vis.get("generator", "default_visual")
    return {
        "type": "svg_generator",
        "generator": generator,
        "params": {},
    }


# ---------------------------------------------------------------------------
# Subskills inference
# ---------------------------------------------------------------------------

def _infer_subskills(data: Dict[str, Any]) -> List[str]:
    """Infer subskills from the v3b data.

    Uses subtopic and topic to generate reasonable snake_case subskills.
    """
    subtopic = data.get("subtopic", "")
    topic = data.get("topic", "")

    # Slugify subtopic as primary subskill
    text = subtopic or topic
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

    # Remove step-down suffixes
    slug = re.sub(r"_step_down_\d+$", "", slug)

    if not slug or not slug[0].isalpha():
        slug = "skill_" + (slug or "general")

    return [slug]


# ---------------------------------------------------------------------------
# IF/THEN/ELSE → Python ternary conversion
# ---------------------------------------------------------------------------

def _convert_if_then_else(formula: str) -> str:
    """Convert IF/THEN/ELIF/ELSE pseudo-code to Python ternary syntax.

    Examples:
        "IF degrees == 90 THEN 'right' ELIF degrees < 90 THEN 'acute' ELSE 'obtuse'"
        -> "'right' if degrees == 90 else 'acute' if degrees < 90 else 'obtuse'"

        "IF a == b == c THEN 'equilateral' ELIF a==b OR b==c OR a==c THEN 'isosceles' ELSE 'scalene'"
        -> "'equilateral' if a == b == c else 'isosceles' if (a==b or b==c or a==c) else 'scalene'"

        "IF N is a perfect square THEN (yes, sqrt(N)) ELSE (no)"
        -> handled as special case: use sqrt-based ternary
    """
    import re as _re
    s = formula.strip()

    # Only process formulas that start with IF (case-insensitive)
    if not _re.match(r'^IF\b', s, _re.IGNORECASE):
        return formula

    # Special case: "IF N is a perfect square THEN (yes, sqrt(N)) ELSE (no)"
    ps_match = _re.match(
        r"IF\s+(\w+)\s+is\s+a\s+perfect\s+square\s+THEN\s+.*sqrt.*ELSE.*no",
        s, _re.IGNORECASE
    )
    if ps_match:
        var = ps_match.group(1)
        return f"sqrt({var}) if int(sqrt({var})) * int(sqrt({var})) == {var} else 'no'"

    # General pattern: split on IF/THEN/ELIF/ELSE tokens
    # Replace OR/AND with Python equivalents
    s = _re.sub(r'\bOR\b', 'or', s)
    s = _re.sub(r'\bAND\b', 'and', s)

    # Parse IF cond THEN result [ELIF cond THEN result]* ELSE result
    # Tokenize by splitting on IF/THEN/ELIF/ELSE keywords
    parts = _re.split(r'\b(IF|THEN|ELIF|ELSE)\b', s, flags=_re.IGNORECASE)
    # parts will be like: ['', 'IF', ' cond ', 'THEN', ' result ', 'ELIF', ' cond ', 'THEN', ' result ', 'ELSE', ' result']

    # Extract condition-result pairs
    branches = []
    i = 0
    while i < len(parts):
        token = parts[i].strip().upper()
        if token in ('IF', 'ELIF'):
            # Next part is condition, then THEN, then result
            cond = parts[i + 1].strip() if i + 1 < len(parts) else ""
            # Skip THEN
            result = parts[i + 3].strip() if i + 3 < len(parts) else ""
            branches.append((cond, result))
            i += 4
        elif token == 'ELSE':
            default = parts[i + 1].strip() if i + 1 < len(parts) else ""
            branches.append((None, default))
            i += 2
        else:
            i += 1

    if not branches:
        return formula

    # Build Python ternary: result1 if cond1 else result2 if cond2 else default
    expr_parts = []
    for cond, result in branches:
        if cond is not None:
            expr_parts.append(f"{result} if {cond}")
        else:
            expr_parts.append(result)

    return " else ".join(expr_parts)


# ---------------------------------------------------------------------------
# Main adapter
# ---------------------------------------------------------------------------

def adapt_v3b(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a v3b JSON dict to backend-compatible format.

    Returns a new dict suitable for passing to parse_question_file()
    (which dispatches to Question or StepDownQuestion model).
    """
    content = data.get("content", {})
    is_step_down = "-S" in data.get("id", "").split("-")[-1] if data.get("id") else False
    # More precise: check if last segment matches S\d
    qid = data.get("id", "")
    is_step_down = bool(re.search(r"-S\d$", qid))

    # Map topic
    topic_text = data.get("topic", "")
    topic_enum = map_topic(topic_text)

    # The ID stays as-is (we update the regex to accept v3b format)
    qid = data.get("id", "")

    # Grade
    grade = data.get("grade", 1)

    # Flatten content fields to top level
    stem_template = content.get("stem_template", data.get("stem_template", ""))
    if not stem_template:
        stem_template = f"Question about {topic_text}"

    answer_type = _map_answer_type(
        content.get("answer_type", data.get("answer_type", "multiple_choice"))
    )
    answer_formula = content.get("answer_formula", data.get("answer_formula", "0"))

    # Convert IF/THEN/ELSE pseudo-code to Python ternary syntax
    answer_formula = _convert_if_then_else(answer_formula)

    # Params — extract formula-type params as derived fields
    raw_params = content.get("params", data.get("params", {}))

    # Derived
    derived = content.get("derived", data.get("derived", None))

    # Move formula-type params to derived (they depend on other params)
    if isinstance(raw_params, dict):
        formula_params = {}
        for k, v in list(raw_params.items()):
            if isinstance(v, dict) and "formula" in v and "pool" not in v and "range" not in v:
                formula_params[k] = v["formula"]
        if formula_params:
            if derived is None:
                derived = {}
            for k, f in formula_params.items():
                derived[k] = f
                raw_params.pop(k, None)

    params, map_derived = _convert_params(raw_params)

    # Merge map-derived entries into derived dict
    if map_derived:
        if derived is None:
            derived = {}
        for k, formula in map_derived.items():
            derived[k] = formula

    # Ensure all stem_template placeholders have a corresponding param or derived entry.
    # Also check answer_formula for variable references.
    import re as _re
    placeholders = set(_re.findall(r"\{(\w+)\}", stem_template))
    # Also add variables from answer_formula (e.g. "K", "total - K")
    formula_vars = set(_re.findall(r"\b([a-zA-Z_]\w*)\b", answer_formula))
    # Filter out known non-variable tokens
    formula_vars -= {"and", "or", "not", "if", "else", "True", "False", "None",
                     "abs", "min", "max", "round", "int", "float", "len", "str"}
    all_needed = placeholders | formula_vars
    provided = set(params.keys())
    if derived:
        provided |= set(derived.keys())
    missing_placeholders = all_needed - provided

    # For step-downs, missing placeholders should be inherited from parent.
    # For parents, they become derived string literals as fallback.
    raw_inherit = content.get("params", data.get("params", {}))
    is_inherit_all = (isinstance(raw_inherit, dict)
                      and raw_inherit.get("inherit_from_parent") is True
                      and len(raw_inherit) == 1)

    if missing_placeholders:
        if is_step_down or is_inherit_all:
            # Step-down: create ParamInherit entries for each missing placeholder
            for ph in missing_placeholders:
                params[ph] = {"inherit_from_parent": True}
        else:
            if derived is None:
                derived = {}
            for ph in missing_placeholders:
                # Add as a derived variable with a passthrough formula
                derived[ph] = f'"{ph}"'

    # Distractors: check content.distractors, content.distractor_formulas, then top-level
    raw_distractors = content.get("distractors", data.get("distractors", []))
    if not raw_distractors:
        # Some v3b files use distractor_formulas as plain string list
        df_list = content.get("distractor_formulas", [])
        if df_list and isinstance(df_list, list):
            raw_distractors = []
            for i, formula_str in enumerate(df_list):
                if isinstance(formula_str, str):
                    raw_distractors.append({"formula": formula_str, "label": f"distractor_{i}"})
                elif isinstance(formula_str, dict):
                    raw_distractors.append(formula_str)
    distractors = _convert_distractors(raw_distractors)

    # Ensure at least 2 distractors (backend minimum)
    while len(distractors) < 2:
        idx = len(distractors)
        distractors.append({
            "formula": f"wrong_{idx}",
            "label": f"placeholder_{idx}",
        })

    # Limit to 5 (backend maximum)
    distractors = distractors[:5]

    # Distractor formulas for misconception mapping
    distractor_formulas = [d["formula"] for d in distractors]

    # Visual
    visual = _convert_visual(data.get("visual"))

    # Difficulty
    diff_data = data.get("difficulty", {})
    if isinstance(diff_data, dict):
        difficulty = diff_data.get("numeric", 1)
        tier = diff_data.get("tier", "warmup")
    elif isinstance(diff_data, int):
        difficulty = diff_data
        tier = "warmup" if difficulty <= 2 else ("practice" if difficulty <= 4 else "challenge")
    else:
        difficulty = 1
        tier = "warmup"

    # Clamp difficulty to [1, 5]
    difficulty = max(1, min(5, difficulty))

    # Status
    status = _map_status(data.get("status"))

    # Version: v3b uses version=3 as a schema version; backend expects a content revision int
    version = 1

    # Author: backend max_length=10
    author = (data.get("author", "v3b") or "v3b")[:10]

    # Subskills
    subskills = _infer_subskills(data)

    # Tags
    tags = data.get("tags", [])

    # est_time_seconds
    metadata = data.get("metadata", {})
    est_time = metadata.get("est_time_seconds")
    if est_time is not None:
        est_time = max(5, min(300, est_time))

    # Build the result
    result: Dict[str, Any] = {
        "id": qid,
        "grade": grade,
        "topic": topic_enum,
        "subtopic": data.get("subtopic"),
        "subskills": subskills,
        "difficulty": difficulty,
        "tier": tier,
        "stem_template": stem_template,
        "answer_type": answer_type,
        "answer_formula": answer_formula,
        "params": params,
        "distractors": distractors,
        "tags": tags,
        "version": version,
        "author": author,
        "status": status,
    }

    if visual:
        result["visual"] = visual
    if derived:
        result["derived"] = derived
    if est_time is not None:
        result["est_time_seconds"] = est_time

    # Misconceptions (parent questions only)
    if not is_step_down:
        raw_misconceptions = data.get("misconceptions", [])
        misconceptions = _convert_misconceptions(raw_misconceptions, distractor_formulas, qid)

        # Ensure at least 2 misconceptions (backend minimum for parent)
        while len(misconceptions) < 2:
            idx = len(misconceptions)
            formula = distractor_formulas[idx] if idx < len(distractor_formulas) else f"wrong_{idx}"
            misconceptions.append({
                "trigger_answer": formula,
                "diagnosis": f"placeholder_misconception_{idx}",
                "feedback_child": "Let's try again!",
                "step_down_path": [f"{qid}-S1"],
            })

        # Limit to 5
        misconceptions = misconceptions[:5]

        # Ensure all misconception trigger_answers appear in distractor formulas
        existing_formulas = set(distractor_formulas)
        for mc in misconceptions:
            if mc["trigger_answer"] not in existing_formulas:
                # Add a matching distractor if there's room
                if len(distractors) < 5:
                    distractors.append({
                        "formula": mc["trigger_answer"],
                        "label": mc["diagnosis"][:40],
                    })
                    existing_formulas.add(mc["trigger_answer"])
                else:
                    # Remap to an existing distractor
                    mc["trigger_answer"] = distractor_formulas[0]

        # Backend validator: at most 1 distractor can lack a misconception.
        # Ensure sufficient coverage by mapping uncovered distractors to misconceptions.
        distractor_formulas_updated = [d["formula"] for d in distractors]
        covered = {m["trigger_answer"] for m in misconceptions}
        uncovered = [f for f in distractor_formulas_updated if f not in covered]

        # If more than 1 uncovered, we need to add misconceptions or trim distractors
        while len(uncovered) > 1:
            if len(misconceptions) < 5:
                # Add a misconception for an uncovered distractor
                uf = uncovered.pop(0)
                misconceptions.append({
                    "trigger_answer": uf,
                    "diagnosis": f"auto_misconception_{len(misconceptions)}",
                    "feedback_child": "Let's think about this differently!",
                    "step_down_path": [f"{qid}-S1"],
                })
            else:
                # Cannot add more misconceptions; remove excess uncovered distractors
                # but keep at least 2 distractors
                if len(distractors) > 2:
                    remove_formula = uncovered.pop(0)
                    distractors = [d for d in distractors if d["formula"] != remove_formula]
                else:
                    break

        result["distractors"] = distractors
        result["misconceptions"] = misconceptions
    else:
        # Step-down fields
        result["parent_id"] = data.get("parent_id", "")
        result["step_index"] = data.get("step_index", 1)
        result["misconceptions"] = []

    # Ensure answer_formula is not in distractors (backend validator)
    distractor_formula_set = {d["formula"] for d in result["distractors"]}
    if result["answer_formula"] in distractor_formula_set:
        # Remove the conflicting distractor
        result["distractors"] = [
            d for d in result["distractors"] if d["formula"] != result["answer_formula"]
        ]
        # Ensure still at least 2
        while len(result["distractors"]) < 2:
            idx = len(result["distractors"])
            result["distractors"].append({
                "formula": f"alt_wrong_{idx}",
                "label": f"alt_placeholder_{idx}",
            })

    return result


def try_adapt_v3b(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Try to adapt a v3b JSON dict. Returns None on failure."""
    try:
        return adapt_v3b(data)
    except Exception:
        return None
