"""
v3 adaptive Challenge ("The Climb") API — a sequential mini-CAT.

    POST /v3/challenge/start    {user_id, level}                 → first/resumed item (no leak)
    POST /v3/challenge/answer   {user_id, session_id, qid, ...}  → next item OR final result
    GET  /v3/challenge/me?user_id=&level=                        → best rating + history

Separate from the skill-ladder Practice (the moat): touches no content, no
skill/cluster tags, no ladder engine. Identity is bound with assert_user_match;
in-flight questions never carry the answer.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.auth import assert_user_match, verify_token
from app.services.challenge_service import challenge

router = APIRouter(prefix="/v3", tags=["v3-challenge"])


class ClimbStart(BaseModel):
    user_id: str
    level: str


@router.post("/challenge/start")
def climb_start(body: ClimbStart, decoded: Dict[str, Any] = Depends(verify_token)):
    assert_user_match(decoded, body.user_id)
    return challenge.start(body.user_id, body.level)


class ClimbAnswer(BaseModel):
    user_id: str
    qid: str
    session_id: Optional[str] = None
    selected_index: Optional[int] = None
    selected_value: Optional[Any] = None
    time_ms: Optional[int] = 0


@router.post("/challenge/answer")
def climb_answer(body: ClimbAnswer, decoded: Dict[str, Any] = Depends(verify_token)):
    assert_user_match(decoded, body.user_id)
    return challenge.answer(
        body.user_id, body.session_id, body.qid,
        body.selected_index, body.selected_value, body.time_ms or 0,
    )


@router.get("/challenge/me")
def climb_me(
    user_id: str = Query(...),
    level: str = Query(...),
    decoded: Dict[str, Any] = Depends(verify_token),
):
    assert_user_match(decoded, user_id)
    return challenge.me(user_id, level)
