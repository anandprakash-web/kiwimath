"""
Tests for the Kiwimath question schema.

Covers:
- The four G1-COUNT-001 example files validate cleanly.
- Each kind of authoring error raises a clear, specific exception.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.question import (
    Question,
    StepDownQuestion,
    parse_question_file,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Example-based sanity checks
# ---------------------------------------------------------------------------


def _golden_parent() -> dict:
    return json.loads((FIXTURE_DIR / "G1-COUNT-001.json").read_text())


def _golden_step_1() -> dict:
    return json.loads((FIXTURE_DIR / "G1-COUNT-001-S1.json").read_text())


def test_parent_example_validates():
    obj = parse_question_file(_golden_parent())
    assert isinstance(obj, Question)
    assert obj.id == "G1-COUNT-001"
    assert len(obj.misconceptions) >= 2
    assert obj.answer_formula == "N - K"


def test_step_down_example_validates():
    obj = parse_question_file(_golden_step_1())
    assert isinstance(obj, StepDownQuestion)
    assert obj.id == "G1-COUNT-001-S1"
    assert obj.parent_id == "G1-COUNT-001"
    assert obj.misconceptions == []


# ---------------------------------------------------------------------------
# Authoring-error cases — the validator's real job
# ---------------------------------------------------------------------------


def test_parent_rejects_bad_id_format():
    data = _golden_parent()
    data["id"] = "counting_q1"
    with pytest.raises(ValidationError, match="must match"):
        Question.model_validate(data)


def test_parent_rejects_single_misconception():
    data = _golden_parent()
    data["misconceptions"] = data["misconceptions"][:1]
    with pytest.raises(ValidationError):
        Question.model_validate(data)


def test_placeholder_without_param_fails():
    data = _golden_parent()
    data["stem_template"] = "{mystery} has {N} things"
    with pytest.raises(ValidationError, match="mystery"):
        Question.model_validate(data)


def test_misconception_must_link_to_real_distractor():
    data = _golden_parent()
    data["misconceptions"][0]["trigger_answer"] = "N * 9000"
    with pytest.raises(ValidationError, match="not one of the distractor"):
        Question.model_validate(data)


def test_feedback_over_20_words_fails():
    data = _golden_parent()
    data["misconceptions"][0]["feedback_child"] = " ".join(["word"] * 21)
    with pytest.raises(ValidationError, match="words"):
        Question.model_validate(data)


def test_step_down_cannot_have_misconceptions():
    data = _golden_step_1()
    data["misconceptions"] = [
        {
            "trigger_answer": "N",
            "diagnosis": "something",
            "feedback_child": "try again",
            "step_down_path": ["G1-COUNT-001-S2"],
        }
    ]
    with pytest.raises(ValidationError):
        StepDownQuestion.model_validate(data)


def test_step_down_id_must_belong_to_parent():
    data = _golden_step_1()
    data["parent_id"] = "G1-COUNT-999"
    with pytest.raises(ValidationError, match="does not belong"):
        StepDownQuestion.model_validate(data)


def test_range_min_greater_than_max_fails():
    data = _golden_parent()
    data["params"]["N"]["range"] = [10, 5]
    with pytest.raises(ValidationError, match="range"):
        Question.model_validate(data)


def test_diagnosis_must_be_snake_case():
    data = _golden_parent()
    data["misconceptions"][0]["diagnosis"] = "AddedInsteadOfSubtracted"
    with pytest.raises(ValidationError):
        Question.model_validate(data)


def test_duplicate_distractor_labels_fail():
    data = _golden_parent()
    data["distractors"][1]["label"] = data["distractors"][0]["label"]
    with pytest.raises(ValidationError, match="duplicate"):
        Question.model_validate(data)
