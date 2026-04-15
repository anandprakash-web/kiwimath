"""
Tests for the question renderer.
"""

from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

import pytest

from app.models.question import Question, parse_question_file
from app.services.renderer import RenderError, render_question


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _golden() -> Question:
    data = json.loads((FIXTURE_DIR / "G1-COUNT-001.json").read_text())
    return parse_question_file(data)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Basic rendering
# ---------------------------------------------------------------------------


def test_render_deterministic_with_seed():
    q = _golden()
    r1 = render_question(q, seed=42)
    r2 = render_question(q, seed=42)
    assert r1.stem == r2.stem
    assert r1.params_used == r2.params_used
    assert r1.correct_index == r2.correct_index


def test_render_produces_valid_mcq():
    q = _golden()
    r = render_question(q, seed=1)
    # Must have at least 3 options (1 correct + 2 distractors)
    assert len(r.options) >= 3
    # Exactly one is marked correct and correct_index matches
    correct_flags = [o.is_correct for o in r.options]
    assert sum(correct_flags) == 1
    assert r.options[r.correct_index].is_correct is True


def test_correct_answer_matches_formula():
    q = _golden()
    r = render_question(q, seed=7)
    N = r.params_used["N"]
    K = r.params_used["K"]
    assert r.options[r.correct_index].text == str(N - K)


def test_constraint_always_satisfied():
    """K < N should hold across many random renders."""
    q = _golden()
    for seed in range(50):
        r = render_question(q, seed=seed)
        assert r.params_used["K"] < r.params_used["N"]


def test_stem_has_no_leftover_placeholders():
    q = _golden()
    for seed in range(20):
        r = render_question(q, seed=seed)
        assert "{" not in r.stem, f"unresolved placeholder in: {r.stem}"
        assert "}" not in r.stem


# ---------------------------------------------------------------------------
# Misconceptions → wrong-option diagnosis
# ---------------------------------------------------------------------------


def test_wrong_options_carry_diagnosis():
    q = _golden()
    r = render_question(q, seed=3)
    # At least one wrong option should have an attached diagnosis
    assert len(r.wrong_option_diagnosis) >= 1
    for idx, diag in r.wrong_option_diagnosis.items():
        assert idx != r.correct_index
        assert isinstance(diag, str) and diag  # non-empty


def test_step_down_path_attached_to_wrong_options():
    q = _golden()
    r = render_question(q, seed=9)
    for idx, path in r.wrong_option_step_down_path.items():
        assert isinstance(path, list) and len(path) >= 1
        assert all(sd.startswith("G1-COUNT-001-S") for sd in path)


# ---------------------------------------------------------------------------
# Locale
# ---------------------------------------------------------------------------


def test_indian_locale_uses_indian_names():
    q = _golden()
    # Try many seeds — locale should override name to one of the IN pool
    seen_names = Counter()
    for seed in range(30):
        r = render_question(q, seed=seed, locale="IN")
        seen_names[r.params_used["name"]] += 1
    allowed = {"Aarav", "Priya", "Diya", "Rohan", "Ananya"}
    assert set(seen_names.keys()).issubset(allowed), (
        f"got names {sorted(seen_names.keys())} that aren't in IN pool {sorted(allowed)}"
    )


# ---------------------------------------------------------------------------
# Visual propagation
# ---------------------------------------------------------------------------


def test_visual_is_none_when_question_has_no_visual():
    q = _golden()
    r = render_question(q, seed=0)
    assert r.visual is None


# ---------------------------------------------------------------------------
# Regression: pronoun must match the FINAL (locale-overridden) name, not the sampled one.
# ---------------------------------------------------------------------------

_FEMALE_NAMES = {"Mei", "Zara", "Priya", "Diya", "Ananya", "Sofia"}
_MALE_NAMES = {"Pablo", "Liam", "Aarav", "Rohan", "Kofi"}


def test_pronoun_matches_final_name_after_locale_swap():
    q = _golden()
    for seed in range(30):
        r = render_question(q, seed=seed, locale="IN")
        name = r.params_used["name"]
        # Must be a name from the IN pool
        assert name in {"Aarav", "Priya", "Diya", "Rohan", "Ananya"}
        # Pronoun must match the final name
        if name in _MALE_NAMES:
            assert " He " in r.stem or r.stem.startswith("He ")
        elif name in _FEMALE_NAMES:
            assert " She " in r.stem or r.stem.startswith("She ")


# ---------------------------------------------------------------------------
# Regression: step-downs must render without crashing.
# ---------------------------------------------------------------------------


def test_warm_feedback_messages_carried_to_wrong_options():
    q = _golden()
    r = render_question(q, seed=5)
    # Every diagnosed wrong option must have a kid-friendly feedback message.
    for idx, diagnosis in r.wrong_option_diagnosis.items():
        assert idx in r.wrong_option_feedback, (
            f"option {idx} has diagnosis {diagnosis} but no feedback_child"
        )
        msg = r.wrong_option_feedback[idx]
        assert isinstance(msg, str) and len(msg) > 0
        # Placeholders should be resolved
        assert "{" not in msg and "}" not in msg


def test_feedback_placeholder_substitution():
    """feedback_child may reference {name} — it must come out with the final name."""
    q = _golden()
    r = render_question(q, seed=11, locale="IN")
    name = r.params_used["name"]
    # At least one misconception references {name}
    has_name_in_any = any(name in fb for fb in r.wrong_option_feedback.values())
    # Not all of them reference name, but at least one should have the substitution work
    # (the "ignored_action_word" misconception uses {name}).
    assert has_name_in_any, (
        f"expected at least one feedback message to contain '{name}'; "
        f"got {r.wrong_option_feedback}"
    )


def test_step_down_renders_with_inherited_params():
    from app.models.question import parse_question_file
    data = json.loads((FIXTURE_DIR / "G1-COUNT-001-S1.json").read_text())
    step = parse_question_file(data)
    r = render_question(
        step,  # type: ignore[arg-type]
        seed=1,
        locale="IN",
        inherited_params={"name": "Aarav", "N": 9, "object": "apples"},
    )
    assert r.question_id == "G1-COUNT-001-S1"
    assert "Aarav" in r.stem
    # Correct answer is N - 1 = 8
    assert r.options[r.correct_index].text == "8"
