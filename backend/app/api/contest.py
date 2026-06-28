"""
v3 Daily Contest + Weekly League API.

    GET  /v3/contest/today?user_id=&level=     → today's contest (no answer leak) + your status
    POST /v3/contest/submit                    → server-graded; awards economy + LP; one attempt
    GET  /v3/contest/leaderboard?level=&date=  → today's contest board
    GET  /v3/league/me?user_id=&level=         → your weekly cohort standings + zones

Auth: the router is mounted under the shared `verify_token`; endpoints that take a
`user_id` additionally bind identity with `assert_user_match` (a student can only
read/act on their own contest + league).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import assert_user_match, is_admin, verify_token
from app.services.contest_service import contest
from app.services.league_service import league

router = APIRouter(prefix="/v3", tags=["v3-contest"])


@router.get("/contest/today")
def contest_today(
    user_id: str = Query(...),
    level: str = Query(...),
    decoded: Dict[str, Any] = Depends(verify_token),
):
    assert_user_match(decoded, user_id)
    return contest.get_contest(user_id, level)


class ContestAnswer(BaseModel):
    qid: str
    selected_index: Optional[int] = None
    selected_value: Optional[Any] = None
    time_ms: Optional[int] = 0


class ContestSubmit(BaseModel):
    user_id: str
    level: str
    answers: List[ContestAnswer] = []
    name: Optional[str] = None


@router.post("/contest/submit")
def contest_submit(body: ContestSubmit, decoded: Dict[str, Any] = Depends(verify_token)):
    assert_user_match(decoded, body.user_id)
    st = contest.status()
    already = contest.get_contest(body.user_id, body.level)["attempted"]
    if st["status"] != "live" and not already:
        raise HTTPException(409, "The Daily Contest is not live right now.")
    answers = [{"qid": a.qid, "selected_index": a.selected_index,
                "selected_value": a.selected_value, "time_ms": a.time_ms}
               for a in body.answers]
    return contest.submit(body.user_id, body.level, answers, body.name)


@router.get("/contest/leaderboard")
def contest_leaderboard(
    level: str = Query(...),
    date: Optional[str] = Query(None),
    decoded: Dict[str, Any] = Depends(verify_token),
):
    return contest.leaderboard(level, date)


@router.get("/league/me")
def league_me(
    user_id: str = Query(...),
    level: str = Query(...),
    decoded: Dict[str, Any] = Depends(verify_token),
):
    assert_user_match(decoded, user_id)
    return league.standings(user_id, level)


@router.post("/internal/league-rollover")
def league_rollover(
    week: Optional[str] = Query(None, description="Week to roll, e.g. 2026-W25; defaults to the current week"),
    decoded: Dict[str, Any] = Depends(verify_token),
):
    """End-of-week promotion/relegation. Called by Cloud Scheduler (Sunday 23:55
    IST) via the X-Internal-Key header — `verify_token` accepts that as an
    internal identity. Admins may also trigger it. Normal users are rejected."""
    if not (decoded.get("internal") or decoded.get("dev_mode") or is_admin(decoded)):
        raise HTTPException(403, "Forbidden: admin or internal cron only")
    return {"ok": True, **league.rollover(week)}
