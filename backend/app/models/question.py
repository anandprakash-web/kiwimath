"""
Kiwimath question schema — Pydantic models.

These models ARE the schema. If the schema changes, change it here and everything
downstream (validator, backend API, ingester) picks it up.

Reference spec: docs/question-schema.md
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums — the tight constraints
# ---------------------------------------------------------------------------


class Topic(str, Enum):
    counting_observation = "counting_observation"
    arithmetic_missing_numbers = "arithmetic_missing_numbers"
    patterns_sequences = "patterns_sequences"
    logic_ordering = "logic_ordering"
    spatial_reasoning_3d = "spatial_reasoning_3d"
    shapes_folding_symmetry = "shapes_folding_symmetry"
    word_problems = "word_problems"
    number_puzzles_grids = "number_puzzles_grids"


class Tier(str, Enum):
    warmup = "warmup"
    practice = "practice"
    challenge = "challenge"


class AnswerType(str, Enum):
    multiple_choice = "multiple_choice"
    numeric_input = "numeric_input"
    tap_to_select = "tap_to_select"
    drag_and_drop = "drag_and_drop"


class Status(str, Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    live = "live"


# ---------------------------------------------------------------------------
# Param spec — either a fixed pool, a numeric range, or inherit-from-parent
# ---------------------------------------------------------------------------


class ParamPool(BaseModel):
    pool: List[Union[str, int, float]]


class ParamRange(BaseModel):
    range: List[int] = Field(..., min_length=2, max_length=2)
    constraint: Optional[str] = None  # e.g. "K < N"

    @field_validator("range")
    @classmethod
    def _ordered(cls, v: List[int]) -> List[int]:
        if v[0] > v[1]:
            raise ValueError(f"range min ({v[0]}) > max ({v[1]})")
        return v


class ParamInherit(BaseModel):
    inherit_from_parent: Literal[True]


ParamSpec = Union[ParamPool, ParamRange, ParamInherit]


# ---------------------------------------------------------------------------
# Visual
# ---------------------------------------------------------------------------


class SvgGeneratorVisual(BaseModel):
    type: Literal["svg_generator"]
    generator: str
    params: Dict[str, Any] = Field(default_factory=dict)


class StaticAssetVisual(BaseModel):
    type: Literal["static_asset"]
    path: str
    alt_text: str


VisualSpec = Union[SvgGeneratorVisual, StaticAssetVisual]


# ---------------------------------------------------------------------------
# Distractors & misconceptions
# ---------------------------------------------------------------------------


class Distractor(BaseModel):
    formula: str
    label: str


class Misconception(BaseModel):
    trigger_answer: str
    diagnosis: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9_]+$",
        description="snake_case label — reused across questions, powers parent reports",
    )
    feedback_child: str = Field(..., max_length=120)
    step_down_path: List[str] = Field(..., min_length=1, max_length=5)

    @field_validator("feedback_child")
    @classmethod
    def _word_count(cls, v: str) -> str:
        wc = len(v.split())
        if wc > 20:
            raise ValueError(
                f"feedback_child is {wc} words; style rule says <15 words, hard cap 20"
            )
        return v


# ---------------------------------------------------------------------------
# Locale
# ---------------------------------------------------------------------------


class LocaleOverride(BaseModel):
    names: Optional[List[str]] = None
    objects: Optional[List[str]] = None
    currency: Optional[str] = None


class LocaleContext(BaseModel):
    IN: Optional[LocaleOverride] = None
    US: Optional[LocaleOverride] = None
    SG: Optional[LocaleOverride] = None
    global_: Optional[LocaleOverride] = Field(None, alias="global")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Main question models
# ---------------------------------------------------------------------------


ID_RE_PARENT = re.compile(r"^G[1-8]-[A-Z]+-\d{3}$")
ID_RE_STEP = re.compile(r"^G[1-8]-[A-Z]+-\d{3}-S[1-5]$")
PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


class _QuestionBase(BaseModel):
    """Fields shared by parent questions and step-downs."""

    id: str
    grade: int = Field(..., ge=1, le=8)
    topic: Topic
    subtopic: Optional[str] = None
    subskills: List[str] = Field(..., min_length=1)
    difficulty: int = Field(..., ge=1, le=5)
    tier: Tier
    source_inspiration: Optional[str] = None

    stem_template: str = Field(..., min_length=3)
    visual: Optional[VisualSpec] = None
    answer_type: AnswerType

    params: Dict[str, ParamSpec] = Field(default_factory=dict)
    derived: Optional[Dict[str, str]] = None

    answer_formula: str
    distractors: List[Distractor] = Field(..., min_length=2, max_length=5)

    tags: List[str] = Field(default_factory=list)
    est_time_seconds: Optional[int] = Field(None, ge=5, le=300)
    version: int = Field(..., ge=1)
    author: str = Field(..., min_length=1, max_length=10)
    status: Status

    @field_validator("subskills")
    @classmethod
    def _snake_case_subskills(cls, v: List[str]) -> List[str]:
        for s in v:
            if not re.match(r"^[a-z][a-z0-9_]+$", s):
                raise ValueError(f"subskill '{s}' must be snake_case")
        return v

    @model_validator(mode="after")
    def _check_distractor_labels_unique(self) -> "_QuestionBase":
        labels = [d.label for d in self.distractors]
        if len(labels) != len(set(labels)):
            raise ValueError(f"duplicate distractor labels: {labels}")
        return self

    @model_validator(mode="after")
    def _check_placeholders_resolve(self) -> "_QuestionBase":
        placeholders = set(PLACEHOLDER_RE.findall(self.stem_template))
        provided = set(self.params.keys())
        if self.derived:
            provided |= set(self.derived.keys())
        missing = placeholders - provided
        if missing:
            raise ValueError(
                f"stem_template uses {{{sorted(missing)}}} but no params/derived "
                f"declared for them (have: {sorted(provided)})"
            )
        return self


class Question(_QuestionBase):
    """A golden parent question. Must have misconceptions."""

    misconceptions: List[Misconception] = Field(..., min_length=2, max_length=5)
    locale_context: Optional[LocaleContext] = None

    @field_validator("id")
    @classmethod
    def _valid_parent_id(cls, v: str) -> str:
        if not ID_RE_PARENT.match(v):
            raise ValueError(
                f"id '{v}' must match G{{grade}}-{{TOPIC}}-{{nnn}}, e.g. G1-COUNT-001"
            )
        return v

    @model_validator(mode="after")
    def _misconceptions_link_to_distractors(self) -> "Question":
        distractor_formulas = {d.formula for d in self.distractors}
        for m in self.misconceptions:
            if m.trigger_answer not in distractor_formulas:
                raise ValueError(
                    f"misconception trigger_answer '{m.trigger_answer}' is not one of "
                    f"the distractor formulas {sorted(distractor_formulas)}"
                )
        return self

    @model_validator(mode="after")
    def _each_distractor_has_misconception(self) -> "Question":
        distractor_formulas = {d.formula for d in self.distractors}
        covered = {m.trigger_answer for m in self.misconceptions}
        uncovered = distractor_formulas - covered
        if uncovered:
            # Warn-level — allowed for v0 but flagged
            # (Authors: every distractor should have a misconception; we allow up to 1 uncovered)
            if len(uncovered) > 1:
                raise ValueError(
                    f"{len(uncovered)} distractors have no misconception "
                    f"(max allowed: 1): {sorted(uncovered)}"
                )
        return self

    @model_validator(mode="after")
    def _step_down_ids_well_formed(self) -> "Question":
        for m in self.misconceptions:
            for sd_id in m.step_down_path:
                if not sd_id.startswith(self.id + "-S"):
                    raise ValueError(
                        f"step_down_path id '{sd_id}' should start with '{self.id}-S' "
                        f"(step-downs must belong to their parent question)"
                    )
        return self


class StepDownQuestion(_QuestionBase):
    """A scaffolding sub-question. No misconceptions — we don't recurse."""

    parent_id: str
    step_index: int = Field(..., ge=1, le=5)
    misconceptions: List[Misconception] = Field(default_factory=list, max_length=0)

    @field_validator("id")
    @classmethod
    def _valid_step_id(cls, v: str) -> str:
        if not ID_RE_STEP.match(v):
            raise ValueError(
                f"id '{v}' must match G{{grade}}-{{TOPIC}}-{{nnn}}-S{{n}}, "
                f"e.g. G1-COUNT-001-S1"
            )
        return v

    @model_validator(mode="after")
    def _parent_id_matches(self) -> "StepDownQuestion":
        expected_prefix = self.parent_id + "-S"
        if not self.id.startswith(expected_prefix):
            raise ValueError(
                f"step-down id '{self.id}' does not belong to parent '{self.parent_id}'"
            )
        return self


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def is_step_down_id(qid: str) -> bool:
    return bool(ID_RE_STEP.match(qid))


def parse_question_file(data: Dict[str, Any]) -> Union[Question, StepDownQuestion]:
    """Dispatch to the right model based on id shape."""
    qid = data.get("id", "")
    if is_step_down_id(qid):
        return StepDownQuestion.model_validate(data)
    return Question.model_validate(data)
