"""
Question API — the endpoints the Flutter app will hit.

v0 scope:
    GET  /questions/next?topic=...&locale=...  → a rendered question
    POST /answer/submit                        → check answer, return next step

Week 3 will add:
    - /student/me for progress
    - /questions/preview for the admin tool
    - Auth via Firebase ID token
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.question import Question, StepDownQuestion
from app.services import content_store
from app.services.renderer import RenderError, render_question
from app.services.svg_generators import (
    UnknownGeneratorError,
    render_svg,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response shapes
# ---------------------------------------------------------------------------


class OptionOut(BaseModel):
    text: str


class VisualOut(BaseModel):
    kind: str = Field(..., description="'svg_inline' or 'static_asset'")
    svg: Optional[str] = None
    path: Optional[str] = None
    alt_text: Optional[str] = None


class QuestionOut(BaseModel):
    question_id: str
    stem: str
    options: List[OptionOut]
    visual: Optional[VisualOut] = None
    est_time_seconds: Optional[int] = None
    # Secrets the app should NOT show — kept server-side in a real deploy.
    # For v0 we include them so you can see the full render in browser.
    correct_index: int
    wrong_option_diagnosis: Dict[int, str] = Field(default_factory=dict)
    wrong_option_step_down_path: Dict[int, List[str]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_visual(visual_dict: Optional[Dict]) -> Optional[VisualOut]:
    if not visual_dict:
        return None
    vtype = visual_dict.get("type")
    if vtype == "svg_generator":
        try:
            svg = render_svg(
                visual_dict["generator"], visual_dict.get("params", {})
            )
            return VisualOut(kind="svg_inline", svg=svg)
        except UnknownGeneratorError as e:
            # Missing generator shouldn't crash the whole question
            return VisualOut(kind="svg_inline", svg=f"<!-- {e} -->")
    if vtype == "static_asset":
        return VisualOut(
            kind="static_asset",
            path=visual_dict.get("path"),
            alt_text=visual_dict.get("alt_text"),
        )
    return None


def _to_response(
    rendered, est_time_seconds: Optional[int]
) -> QuestionOut:
    return QuestionOut(
        question_id=rendered.question_id,
        stem=rendered.stem,
        options=[OptionOut(text=o.text) for o in rendered.options],
        visual=_render_visual(rendered.visual),
        est_time_seconds=est_time_seconds,
        correct_index=rendered.correct_index,
        wrong_option_diagnosis=rendered.wrong_option_diagnosis,
        wrong_option_step_down_path=rendered.wrong_option_step_down_path,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/questions/next", response_model=QuestionOut)
def questions_next(
    topic: Optional[str] = Query(None, description="Filter to a single topic"),
    locale: Optional[str] = Query(None, description="IN / US / SG / global"),
    seed: Optional[int] = Query(None, description="Fix the RNG for reproducible renders"),
):
    """Pick a parent question at random (v0 adaptive: none) and render it."""
    candidates: List[Question]
    if topic:
        candidates = content_store.store.by_topic(topic)
    else:
        candidates = content_store.store.parents()

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail=(
                "No questions available. Set KIWIMATH_CONTENT_DIR and restart, "
                "or check that topic/locale filters match existing content."
            ),
        )

    q = random.choice(candidates)
    try:
        rendered = render_question(q, seed=seed, locale=locale)
    except RenderError as e:
        raise HTTPException(status_code=500, detail=f"render failed: {e}")
    return _to_response(rendered, q.est_time_seconds)


@router.get("/questions/{question_id}", response_model=QuestionOut)
def question_by_id(
    question_id: str,
    locale: Optional[str] = Query(None),
    seed: Optional[int] = Query(None),
    # For step-downs, the parent's params can be passed in so the step inherits
    # the same name/object/N. Comma-separated k=v pairs, ints parsed when possible.
    inherit: Optional[str] = Query(None, description="e.g. 'name=Aarav,N=9,K=3'"),
):
    obj = content_store.store.get(question_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"unknown question id {question_id}")

    inherited: Dict = {}
    if inherit:
        for kv in inherit.split(","):
            if "=" not in kv:
                continue
            k, v = kv.split("=", 1)
            k, v = k.strip(), v.strip()
            try:
                inherited[k] = int(v)
            except ValueError:
                inherited[k] = v

    # We render both parents and step-downs through the same path.
    # Step-downs are just Questions with no misconceptions (schema-wise).
    try:
        # Cast: renderer accepts any Question; StepDownQuestion shares the base fields.
        rendered = render_question(
            obj,  # type: ignore[arg-type]
            seed=seed,
            locale=locale,
            inherited_params=inherited if inherited else None,
        )
    except RenderError as e:
        raise HTTPException(status_code=500, detail=f"render failed: {e}")
    return _to_response(rendered, obj.est_time_seconds)


@router.get("/health")
def health():
    return {"status": "ok", **content_store.store.stats()}
