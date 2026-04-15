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
    max_tries: int = 50,
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
        if isinstance(spec, ParamRange) and spec.constraint:
            try:
                if not safe_eval(spec.constraint, values):
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
        # Only built-in rule right now. Extend as needed.
        if rule.startswith("pronoun_from_name("):
            src_match = re.match(r"pronoun_from_name\((\w+)\)", rule)
            if not src_match:
                raise RenderError(f"malformed derived rule: {rule}")
            src_param = src_match.group(1)
            name = values.get(src_param, "")
            pronouns = _PRONOUN_TABLE.get(
                name, {"subject": "They", "object": "them", "possessive": "their"}
            )
            if "subject" in derived_name:
                values[derived_name] = pronouns["subject"]
            elif "object" in derived_name:
                values[derived_name] = pronouns["object"]
            elif "possessive" in derived_name:
                values[derived_name] = pronouns["possessive"]
            else:
                values[derived_name] = pronouns["subject"]
        else:
            raise RenderError(f"unknown derived rule: {rule}")


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

    # Compute answer and distractor values.
    try:
        correct_value = safe_eval(q.answer_formula, values)
    except Exception as e:
        raise RenderError(f"failed to evaluate answer_formula '{q.answer_formula}': {e}")

    distractor_entries: List[tuple[int, str, Distractor]] = []  # (value, label, spec)
    seen_values = {correct_value}
    for d in q.distractors:
        try:
            v = safe_eval(d.formula, values)
        except Exception:
            # Skip distractors that fail to evaluate (e.g. negatives, div by zero).
            continue
        if v in seen_values:
            continue
        seen_values.add(v)
        distractor_entries.append((v, d.label, d))

    # Need at least 2 distractors for a meaningful MCQ.
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

    for idx, (value, is_correct, distractor) in enumerate(all_options):
        rendered_options.append(RenderedOption(text=str(value), is_correct=is_correct))
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
        # Resolve any param references in the visual's own params
        if "params" in visual_dict and isinstance(visual_dict["params"], dict):
            visual_dict["params"] = {
                k: (values[v] if isinstance(v, str) and v in values else v)
                for k, v in visual_dict["params"].items()
            }

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
