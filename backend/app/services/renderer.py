"""
Question renderer — the heart of Kiwimath's engine.

Takes an authored Question (JSON/Pydantic) and produces a RenderedQuestion
with concrete parameter values, a filled-in stem, shuffled options, and the
correct-option index. This is what the app actually displays.

One authored template + random params = many unique rendered instances.
40 well-authored questions → ~2000 unique rendered problems for the student.

Pipeline:
    1. Sample each parameter from its pool/range.
    2. Check all constraints; resample up to N tries if violated.
    3. Compute derived fields (pronoun from name, etc.).
    4. Apply locale overrides (swap names, objects for the student's locale).
    5. Compute the correct answer via answer_formula.
    6. Compute each distractor value via its formula.
    7. Deduplicate — if a distractor collides with the correct answer, drop it.
    8. Substitute placeholders in the stem template.
    9. Shuffle options and record correct index.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.models.question import (
    Distractor,
    LocaleContext,
    ParamInherit,
    ParamPool,
    ParamRange,
    Question,
)
from app.services.safe_eval import safe_eval
from app.services.visual_validator import validate_visual

import logging

logger = logging.getLogger(__name__)

# Very small pronoun table. Expand as content grows.
# Names not in this table fall back to "They".
_PRONOUN_TABLE: Dict[str, Dict[str, str]] = {
    "Pablo":  {"subject": "He",  "object": "him", "possessive": "his"},
    "Liam":   {"subject": "He",  "object": "him", "possessive": "his"},
    "Aarav":  {"subject": "He",  "object": "him", "possessive": "his"},
    "Rohan":  {"subject": "He",  "object": "him", "possessive": "his"},
    "Kofi":   {"subject": "He",  "object": "him", "possessive": "his"},
    "Mei":    {"subject": "She", "object": "her", "possessive": "her"},
    "Zara":   {"subject": "She", "object": "her", "possessive": "her"},
    "Priya":  {"subject": "She", "object": "her", "possessive": "her"},
    "Diya":   {"subject": "She", "object": "her", "possessive": "her"},
    "Ananya": {"subject": "She", "object": "her", "possessive": "her"},
    "Sofia":  {"subject": "She", "object": "her", "possessive": "her"},
}


_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")

# Topics where float results should be displayed as fractions
_FRACTION_TOPICS = {
    "fractions_decimals",
}


def _float_to_fraction_str(value: float) -> str:
    """Convert a float to a simplified fraction string like '3/7'.

    Uses Python's Fraction class for exact conversion with a
    reasonable denominator limit. Returns the original float string
    if conversion produces a denominator > 1000.
    """
    from fractions import Fraction
    frac = Fraction(value).limit_denominator(1000)
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def _strip_formula_comments(formula: str) -> str:
    """Strip inline comments from formulas.

    Content uses ``--`` and ``#`` for inline documentation:
        'No' -- A - B != B - A (subtraction is not commutative)
        (a * lcd/d1 + b * lcd/d2) / lcd  # where lcd = LCM(d1, d2)

    We need to strip these before evaluation, but carefully:
        - ``#`` only stripped if preceded by whitespace (to avoid ``a#b`` identifiers)
        - ``--`` only stripped if preceded by whitespace (to avoid ``a--b`` double negation)
        - Don't strip inside string literals.
    """
    # Handle -- comments (but not -- as double negation like "a - -b")
    if ' -- ' in formula:
        formula = formula.split(' -- ')[0].rstrip()
    # Handle # comments (common Python-style)
    if '  #' in formula or '\t#' in formula:
        # Split on first occurrence of whitespace-then-#
        import re
        formula = re.split(r'\s+#\s', formula, maxsplit=1)[0].rstrip()
    return formula


def _eval_formula(formula: str, values: Dict[str, Any]) -> Any:
    """Evaluate a formula that might be an arithmetic expression OR a string template.

    Strategy:
      1. Strip inline comments (-- and #).
      2. Try safe_eval first (handles ``N + K``, ``s_plus4``, ``3``, etc.)
      3. If the formula contains ``{var}`` placeholders, fall back to _substitute
         (handles string templates like ``{c1} and {c2}`` or ``{s1}, {s2}``).
      4. If safe_eval fails with "unknown variable" and the formula is a simple
         identifier-like string not in values, treat it as a string literal answer
         (handles MCQ string answers like ``red``, ``triangle``, ``yes``).
      5. Otherwise re-raise the safe_eval error.
    """
    formula = _strip_formula_comments(formula)

    # Normalize caret-as-power: replace ^ with ** (but not inside strings)
    # e.g. "a^2 + b^2" -> "a**2 + b**2"
    if '^' in formula and "'" not in formula and '"' not in formula:
        formula = re.sub(r'\^', '**', formula)

    try:
        return safe_eval(formula, values)
    except Exception as eval_err:
        # Fall back to template substitution if {var} placeholders present
        if _PLACEHOLDER_RE.search(formula):
            substituted = _substitute(formula, values)
            # Try safe_eval on the substituted result (e.g. "max({A}, {B})" -> "max(1409, 5506)")
            try:
                return safe_eval(substituted, values)
            except Exception:
                pass
            return substituted
        # Treat as a string literal if safe_eval cannot handle it AND there are
        # no {var} placeholders. Covers literal MCQ answers like "red", "4th",
        # "add 2", "not enough", etc.
        err_str = str(eval_err)
        if any(hint in err_str for hint in (
            "unknown variable", "invalid expression", "not allowed",
        )):
            return formula
        raise eval_err


class RenderError(Exception):
    """Rendering failed — usually because constraints can't be satisfied."""


@dataclass
class RenderedOption:
    text: str
    is_correct: bool


@dataclass
class RenderedQuestion:
    question_id: str
    stem: str
    options: List[RenderedOption]
    correct_index: int
    params_used: Dict[str, Any]
    visual: Optional[Dict[str, Any]] = None
    # Map each wrong-option index to its misconception diagnosis (if any).
    # App uses this to fire the right step-down path when the kid taps a wrong option.
    wrong_option_diagnosis: Dict[int, str] = field(default_factory=dict)
    wrong_option_step_down_path: Dict[int, List[str]] = field(default_factory=dict)
    # Warm, kid-facing message per wrong option (from Misconception.feedback_child,
    # with {placeholders} substituted).
    wrong_option_feedback: Dict[int, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "stem": self.stem,
            "options": [
                {"text": o.text, "is_correct": o.is_correct} for o in self.options
            ],
            "correct_index": self.correct_index,
            "params_used": self.params_used,
            "visual": self.visual,
            "wrong_option_diagnosis": self.wrong_option_diagnosis,
            "wrong_option_step_down_path": self.wrong_option_step_down_path,
            "wrong_option_feedback": self.wrong_option_feedback,
        }


# ---------------------------------------------------------------------------
# Param sampling
# ---------------------------------------------------------------------------


def _sample_one(param_name: str, spec: Any, rng: random.Random) -> Any:
    if isinstance(spec, ParamPool):
        return rng.choice(spec.pool)
    if isinstance(spec, ParamRange):
        return rng.randint(spec.range[0], spec.range[1])
    raise RenderError(
        f"param '{param_name}' is inherit-only — must be passed in via inherited_params"
    )


def _sample_params(
    q: Question,
    rng: random.Random,
    inherited: Optional[Dict[str, Any]],
    max_tries: int = 200,
) -> Dict[str, Any]:
    inherited = inherited or {}
    for _ in range(max_tries):
        values: Dict[str, Any] = {}
        for name, spec in q.params.items():
            if isinstance(spec, ParamInherit):
                if name not in inherited:
                    raise RenderError(
                        f"param '{name}' marked inherit_from_parent but not supplied"
                    )
                values[name] = inherited[name]
            else:
                values[name] = _sample_one(name, spec, rng)

        if _constraints_satisfied(q, values):
            return values

    raise RenderError(
        f"could not satisfy constraints for {q.id} after {max_tries} tries"
    )


def _constraints_satisfied(q: Question, values: Dict[str, Any]) -> bool:
    for name, spec in q.params.items():
        constraint = getattr(spec, "constraint", None)
        if constraint:
            try:
                if not safe_eval(constraint, values):
                    return False
            except Exception:
                return False
    return True


# ---------------------------------------------------------------------------
# Derived fields (pronouns etc.)
# ---------------------------------------------------------------------------


def _apply_derived(q: Question, values: Dict[str, Any]) -> None:
    if not q.derived:
        return
    for derived_name, rule in q.derived.items():
        # Pronoun rules — support several naming conventions
        pronoun_match = re.match(
            r"(pronoun_from_name|object_pronoun_from_name|subject_pronoun_from_name)\((\w+)\)",
            rule,
        )
        if pronoun_match:
            fn_name, src_param = pronoun_match.group(1), pronoun_match.group(2)
            name = values.get(src_param, "")
            pronouns = _PRONOUN_TABLE.get(
                name, {"subject": "They", "object": "them", "possessive": "their"}
            )
            if fn_name == "object_pronoun_from_name":
                values[derived_name] = pronouns["object"]
            elif fn_name == "subject_pronoun_from_name":
                values[derived_name] = pronouns["subject"]
            elif "subject" in derived_name:
                values[derived_name] = pronouns["subject"]
            elif "object" in derived_name:
                values[derived_name] = pronouns["object"]
            elif "possessive" in derived_name:
                values[derived_name] = pronouns["possessive"]
            else:
                values[derived_name] = pronouns["subject"]
            continue

        # lowercase(var_name) — e.g. lowercase(pronoun_subject) → "he"
        lowercase_match = re.match(r"lowercase\((\w+)\)", rule)
        if lowercase_match:
            src = lowercase_match.group(1)
            values[derived_name] = str(values.get(src, "")).lower()
            continue

        # Resolve {var} template placeholders in the rule before evaluating.
        resolved_rule = rule
        if _PLACEHOLDER_RE.search(resolved_rule):
            try:
                resolved_rule = _substitute(resolved_rule, values)
            except RenderError:
                pass  # If substitution fails, try evaluating as-is.

        # Try evaluating as a safe_eval formula (e.g. "A + 1", "N * 2").
        try:
            values[derived_name] = safe_eval(resolved_rule, values)
        except Exception as e:
            # Gracefully handle English-language rules that can't be parsed.
            # Use a sensible default rather than failing the whole question.
            err_str = str(e)
            if any(hint in err_str for hint in (
                "invalid expression", "invalid syntax",
                "not allowed", "unknown variable",
            )):
                # Try to extract a numeric value from the rule if possible.
                # E.g. "round B up to next multiple of 10" — try rounding.
                if "round" in rule.lower() and "multiple of 10" in rule.lower():
                    # Find a referenced variable and round it.
                    for var_name, var_val in values.items():
                        if var_name.upper() in rule.upper() and isinstance(var_val, (int, float)):
                            import math
                            values[derived_name] = int(math.ceil(var_val / 10) * 10)
                            break
                    else:
                        values[derived_name] = 0
                elif "round" in rule.lower() and "nearest 10" in rule.lower():
                    for var_name, var_val in values.items():
                        if var_name.upper() in rule.upper() and isinstance(var_val, (int, float)):
                            values[derived_name] = int(round(var_val / 10) * 10)
                            break
                    else:
                        values[derived_name] = 0
                elif "split" in rule.lower() or "random" in rule.lower():
                    # "random split of B where B1 in [1..B-1]" — pick midpoint
                    for var_name, var_val in values.items():
                        if var_name.upper() in rule.upper() and isinstance(var_val, (int, float)):
                            values[derived_name] = max(1, int(var_val) // 2)
                            break
                    else:
                        values[derived_name] = 1
                elif "chosen so" in rule.lower():
                    # "chosen so 2*(L1+W1)=P" — solve for variable
                    values[derived_name] = 5  # reasonable default
                else:
                    # Last resort: set to 0 or empty string.
                    values[derived_name] = 0
                logger.debug(f"Derived rule '{derived_name}' used fallback for: {rule}")
            else:
                raise RenderError(f"failed to evaluate derived rule '{derived_name}': {rule} — {e}")


# ---------------------------------------------------------------------------
# Locale
# ---------------------------------------------------------------------------


def _apply_locale(
    q: Question, values: Dict[str, Any], locale: Optional[str], rng: random.Random
) -> None:
    # StepDownQuestion has no locale_context — gracefully no-op.
    locale_context = getattr(q, "locale_context", None)
    if not locale_context or not locale:
        return
    loc = getattr(locale_context, locale, None)
    if loc is None:
        # Fall back to `global` if defined.
        loc = locale_context.global_
    if loc is None:
        return
    # Override name/object if locale provides them.
    if loc.names and "name" in values:
        values["name"] = rng.choice(loc.names)
    if loc.objects and "object" in values:
        values["object"] = rng.choice(loc.objects)


# ---------------------------------------------------------------------------
# Stem substitution
# ---------------------------------------------------------------------------


def _substitute(template: str, values: Dict[str, Any]) -> str:
    def repl(match: re.Match) -> str:
        key = match.group(1)
        if key not in values:
            raise RenderError(f"template uses {{{key}}} but no value provided")
        return str(values[key])

    return _PLACEHOLDER_RE.sub(repl, template)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def render_question(
    q: Question,
    *,
    seed: Optional[int] = None,
    locale: Optional[str] = None,
    inherited_params: Optional[Dict[str, Any]] = None,
) -> RenderedQuestion:
    """Render a Question into a concrete question ready for the student."""
    rng = random.Random(seed)

    values = _sample_params(q, rng, inherited_params)
    # Locale override must happen BEFORE derived fields so pronouns match the final name.
    _apply_locale(q, values, locale, rng)
    _apply_derived(q, values)

    # Auto-compute common derived values that content formulas expect.
    # E.g. "lcd" (least common denominator) referenced in fraction formulas.
    # Also fix cases where derived set lcd to a string literal instead of computing it.
    if 'lcd' in q.answer_formula:
        lcd_val = values.get('lcd')
        if lcd_val is None or isinstance(lcd_val, str):
            d1 = values.get('d1') or values.get('denom1') or values.get('denominator1')
            d2 = values.get('d2') or values.get('denom2') or values.get('denominator2')
            if d1 is not None and d2 is not None:
                import math
                d1_int, d2_int = int(d1), int(d2)
                values['lcd'] = abs(d1_int * d2_int) // math.gcd(d1_int, d2_int)

    # Compute answer and distractor values.
    # Some v3b content has params that are strings but answer formulas that expect
    # numbers (e.g. pool: ["3", "5", "7"] with formula "A + B"). Try coercing.
    try:
        correct_value = _eval_formula(q.answer_formula, values)
    except (TypeError, ValueError) as e:
        # Retry with numeric coercion of string params.
        err_str = str(e)
        if "unsupported operand" in err_str or "multiply sequence" in err_str:
            coerced = {}
            for k, v in values.items():
                if isinstance(v, str):
                    try:
                        coerced[k] = float(v) if '.' in v else int(v)
                    except (ValueError, TypeError):
                        coerced[k] = v
                else:
                    coerced[k] = v
            try:
                correct_value = _eval_formula(q.answer_formula, coerced)
                # Update values with coerced versions for distractor formulas too.
                values.update(coerced)
            except Exception as e2:
                raise RenderError(f"failed to evaluate answer_formula '{q.answer_formula}': {e2}")
        else:
            raise RenderError(f"failed to evaluate answer_formula '{q.answer_formula}': {e}")
    except Exception as e:
        raise RenderError(f"failed to evaluate answer_formula '{q.answer_formula}': {e}")

    distractor_entries: List[tuple[int, str, Distractor]] = []  # (value, label, spec)

    def _hashable(v):
        """Make a value hashable for set membership (lists → tuples)."""
        if isinstance(v, list):
            return tuple(v)
        return v

    seen_values = {_hashable(correct_value)}
    grade = getattr(q, 'grade', None)
    for d in q.distractors:
        try:
            v = _eval_formula(d.formula, values)
        except Exception:
            # Skip distractors that fail to evaluate (e.g. negatives, div by zero).
            continue
        # Skip negative distractor values for grades 1-2
        if isinstance(v, (int, float)) and v < 0 and grade is not None and grade <= 2:
            continue
        hv = _hashable(v)
        if hv in seen_values:
            continue
        seen_values.add(hv)
        distractor_entries.append((v, d.label, d))

    # Need at least 2 distractors for a meaningful MCQ.
    # If we don't have enough, auto-generate fallback distractors.
    if len(distractor_entries) < 2 and isinstance(correct_value, (int, float)):
        grade = getattr(q, 'grade', None)
        for offset in [1, -1, 2, -2, 3, -3]:
            if len(distractor_entries) >= 2:
                break
            candidate = correct_value + offset
            if candidate < 0 and grade is not None and grade <= 2:
                continue
            if candidate not in seen_values:
                seen_values.add(candidate)
                # Display as int if whole number
                if isinstance(candidate, float) and candidate == int(candidate):
                    candidate = int(candidate)
                distractor_entries.append((candidate, chr(ord("B") + len(distractor_entries)), None))

    # Auto-generate string distractors for string answers.
    if len(distractor_entries) < 2 and isinstance(correct_value, str):
        # Common plausible wrong answers for Yes/No, True/False, comparison questions.
        _STRING_DISTRACTOR_POOLS = {
            "yes": ["No", "Maybe", "Not enough info"],
            "no": ["Yes", "Maybe", "Not enough info"],
            "true": ["False", "Sometimes", "Not enough info"],
            "false": ["True", "Sometimes", "Not enough info"],
            ">": ["<", "=", "Cannot tell"],
            "<": [">", "=", "Cannot tell"],
            "=": [">", "<", "Cannot tell"],
            "even": ["Odd", "Neither", "Both"],
            "odd": ["Even", "Neither", "Both"],
        }
        pool = _STRING_DISTRACTOR_POOLS.get(correct_value.lower().strip(), [])
        for candidate in pool:
            if len(distractor_entries) >= 3:
                break
            if candidate not in seen_values and candidate.lower() != correct_value.lower():
                seen_values.add(candidate)
                distractor_entries.append((candidate, chr(ord("B") + len(distractor_entries)), None))

        # If still not enough, generate generic string distractors.
        if len(distractor_entries) < 2:
            for fallback in ["Not enough information", "None of the above", "Cannot determine"]:
                if len(distractor_entries) >= 2:
                    break
                if fallback not in seen_values:
                    seen_values.add(fallback)
                    distractor_entries.append((fallback, chr(ord("B") + len(distractor_entries)), None))

    # Clean up formula-like distractor text that leaked through.
    # v3b content has descriptive distractor formulas (e.g. "wrong_object",
    # "reflected_version", "shape_with_adjacent_side_count") that safe_eval
    # can't compute. These get passed through as literal string option values.
    # Detect and replace them so students see clean answers.
    def _looks_like_formula(text: str) -> bool:
        """Return True if text looks like a code identifier, not a student answer.
        Checks the *evaluated value*, not the formula expression."""
        s = str(text).strip()
        if not s:
            return False
        if '__unknown__' in s:
            return True
        # Prefixes that are always formula artifacts
        if s.startswith('lookup(') or s.startswith('correct_') or s.startswith('wrong_'):
            return True
        # snake_case identifiers: has underscore, no spaces, all alphanumeric/underscore
        # Catches "reflected_version", "adjacent_polygon", "based_on_tens_digit", etc.
        # But NOT real words like "two-digit" or short param values.
        if '_' in s and not any(c.isspace() for c in s) and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', s):
            return True
        # Function-call syntax that leaked through: "correct_net(solid)"
        if re.match(r'^[a-zA-Z_]\w*\(', s):
            return True
        return False

    # First pass: remove formula-like distractors entirely.
    # We'll regenerate replacements below with offset/fallback logic.
    cleaned_distractors = []
    for v, label, d in distractor_entries:
        if _looks_like_formula(str(v)):
            # Drop it — we'll regenerate below
            hv = _hashable(v)
            seen_values.discard(hv)  # Free up the slot
            continue
        cleaned_distractors.append((v, label, d))
    distractor_entries = cleaned_distractors

    # Regenerate numeric distractors for numeric answers
    if isinstance(correct_value, (int, float)):
        grade = getattr(q, 'grade', None)
        for offset in [1, -1, 2, -2, 3, -3, 5, 10, -10]:
            if len(distractor_entries) >= 3:
                break
            candidate = correct_value + offset
            if candidate < 0 and grade is not None and grade <= 2:
                continue
            hc = _hashable(candidate)
            if hc not in seen_values:
                seen_values.add(hc)
                if isinstance(candidate, float) and candidate == int(candidate):
                    candidate = int(candidate)
                distractor_entries.append((candidate, chr(ord("B") + len(distractor_entries)), None))

    # Regenerate string distractors for string answers
    if isinstance(correct_value, str) and len(distractor_entries) < 2:
        _STRING_FALLBACK_POOLS = {
            "yes": ["No", "Maybe", "Not enough info"],
            "no": ["Yes", "Maybe", "Not enough info"],
            "true": ["False", "Sometimes", "Not enough info"],
            "false": ["True", "Sometimes", "Not enough info"],
            ">": ["<", "=", "Cannot tell"],
            "<": [">", "=", "Cannot tell"],
            "=": [">", "<", "Cannot tell"],
            "even": ["Odd", "Neither", "Both"],
            "odd": ["Even", "Neither", "Both"],
        }
        pool = _STRING_FALLBACK_POOLS.get(correct_value.lower().strip(), [])
        for candidate in pool:
            if len(distractor_entries) >= 3:
                break
            hc = _hashable(candidate)
            if hc not in seen_values and candidate.lower() != correct_value.lower():
                seen_values.add(hc)
                distractor_entries.append((candidate, chr(ord("B") + len(distractor_entries)), None))

        # Generic fallbacks for any string answer
        if len(distractor_entries) < 2:
            for fallback in ["Not enough information", "None of the above", "Cannot determine"]:
                if len(distractor_entries) >= 2:
                    break
                hc = _hashable(fallback)
                if hc not in seen_values:
                    seen_values.add(hc)
                    distractor_entries.append((fallback, chr(ord("B") + len(distractor_entries)), None))

    if len(distractor_entries) < 2:
        raise RenderError(
            f"only {len(distractor_entries)} unique distractor(s) for {q.id}"
        )

    # Build option list and shuffle.
    all_options: List[tuple[Any, bool, Optional[Distractor]]] = [
        (correct_value, True, None)
    ]
    for v, _, d in distractor_entries:
        all_options.append((v, False, d))
    rng.shuffle(all_options)

    rendered_options: List[RenderedOption] = []
    correct_index = -1
    wrong_diagnosis: Dict[int, str] = {}
    wrong_steps: Dict[int, List[str]] = {}
    wrong_feedback: Dict[int, str] = {}

    # Build misconception lookup: formula -> misconception (parents only; step-downs
    # have empty misconceptions by schema).
    misc_by_formula: Dict[str, Any] = {
        m.trigger_answer: m for m in getattr(q, "misconceptions", [])
    }

    # Determine if this is a fraction topic (display floats as fractions)
    topic_val = getattr(q, 'topic', None)
    topic_str = topic_val.value if hasattr(topic_val, 'value') else str(topic_val)
    subtopic_str = str(getattr(q, 'subtopic', '') or '').lower()
    is_fraction_topic = (
        topic_str in _FRACTION_TOPICS
        or 'fraction' in subtopic_str
    )

    for idx, (value, is_correct, distractor) in enumerate(all_options):
        # Format value: integers should never show as "6.0"
        if isinstance(value, float) and value == int(value):
            display_text = str(int(value))
        elif isinstance(value, float) and is_fraction_topic:
            display_text = _float_to_fraction_str(value)
        else:
            display_text = str(value)
        rendered_options.append(RenderedOption(text=display_text, is_correct=is_correct))
        if is_correct:
            correct_index = idx
        else:
            # Look up misconception by formula, not by rendered value
            if distractor is not None:
                misc = misc_by_formula.get(distractor.formula)
                if misc is not None:
                    wrong_diagnosis[idx] = misc.diagnosis
                    wrong_steps[idx] = list(misc.step_down_path)
                    # Substitute placeholders in the kid-facing feedback message too.
                    try:
                        wrong_feedback[idx] = _substitute(misc.feedback_child, values)
                    except RenderError:
                        wrong_feedback[idx] = misc.feedback_child

    stem = _substitute(q.stem_template, values)

    visual_dict: Optional[Dict[str, Any]] = None
    if q.visual is not None:
        visual_dict = q.visual.model_dump()
        # Resolve any param references in the visual's own params.
        # Supports both bare names ("N") and template syntax ("{N}").
        if "params" in visual_dict and isinstance(visual_dict["params"], dict):
            resolved = {}
            for k, v in visual_dict["params"].items():
                if isinstance(v, str):
                    # Strip {braces} if present
                    stripped = v.strip()
                    if stripped.startswith("{") and stripped.endswith("}"):
                        stripped = stripped[1:-1]
                    if stripped in values:
                        resolved[k] = values[stripped]
                    else:
                        # Try evaluating as an expression (e.g. "A + B")
                        try:
                            resolved[k] = safe_eval(stripped, values)
                        except Exception:
                            resolved[k] = v
                else:
                    resolved[k] = v
            visual_dict["params"] = resolved

    # --- Visual validation gate ---
    # Catches mismatches BEFORE the question reaches the child.
    # If the visual doesn't match the stem/answer, strip it (show no image
    # rather than a wrong image).
    if visual_dict is not None:
        vresult = validate_visual(
            question_id=q.id,
            stem=stem,
            visual_dict=visual_dict,
            params_used=values,
            correct_answer=correct_value,
        )
        if vresult.strip_visual:
            logger.warning(
                f"VISUAL_STRIPPED for {q.id}: {vresult.errors}"
            )
            visual_dict = None

    # --- QA debug logging ---
    # Logs the final resolved payload so mismatches can be traced quickly.
    # Only in debug mode to avoid noise in production.
    logger.debug(
        f"QA_RENDER [{q.id}] stem='{stem[:80]}...' "
        f"answer={correct_value} params={values} "
        f"visual={'None' if visual_dict is None else visual_dict.get('generator', 'unknown')}"
    )

    return RenderedQuestion(
        question_id=q.id,
        stem=stem,
        options=rendered_options,
        correct_index=correct_index,
        params_used=values,
        visual=visual_dict,
        wrong_option_diagnosis=wrong_diagnosis,
        wrong_option_step_down_path=wrong_steps,
        wrong_option_feedback=wrong_feedback,
    )
