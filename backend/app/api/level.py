"""
v3 Level/Grade API — the remapped Olympiad (L1-L8) + School (grade) banks,
with one server-side economy so coins / gems / XP / streak / awards and
performance are identical on every tab (no disjoint).

Olympiad (level-based):
    GET  /v3/olympiad/levels                                  → L1-L8 + topics
    GET  /v3/olympiad/levels/{level}/topics                   → topics for a level
    GET  /v3/olympiad/levels/{level}/topics/{tk}/next         → adaptive question
    GET  /v3/olympiad/levels/{level}/topics/{tk}/questions    → question list
    GET  /v3/olympiad/question/{qid}                          → one question
    GET  /v3/olympiad/question/{qid}/visual                   → inline SVG

School (grade-based):
    GET  /v3/curriculum/boards
    GET  /v3/curriculum/{board}/grades
    GET  /v3/curriculum/{board}/grade/{grade}/chapters        → sequenced chapters
    GET  /v3/curriculum/{board}/grade/{grade}/chapter/{ch}/questions

Unified economy / performance (single source of truth):
    POST /v3/answer/check     → grade server-side, award economy, return wallet
    GET  /v3/me/wallet        → coins/gems/xp/streak/awards (every tab reads this)
    GET  /v3/me/progress      → academic height + strand mastery (same state)
    GET  /v3/stats
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.auth import assert_user_match, verify_token
from app.services.content_store_level import (
    OLYMPIAD_STRANDS, PILLAR_NAMES, level_store,
)
from app.services.gamification import gamification
from app.services.state_store import get_idempotent_response, record_idempotent_response

router = APIRouter(prefix="/v3", tags=["v3-level"])

# Topic keys that make up the cross-cutting "Logic & Puzzles" extra strand.
LOGIC_TOPIC_KEYS = {
    "counting_logic", "logic_puzzles", "games_invariants", "pigeonhole",
    "sorting", "systematic_listing", "counting_principles",
}


def _q_public(q) -> Dict[str, Any]:
    """Shape a question WITHOUT leaking the answer (fetch-time)."""
    return {
        "id": q.id,
        "stem": q.stem,
        "choices": q.choices,
        "interaction_mode": getattr(q, "interaction_mode", "mcq"),
        "visual_svg": q.visual_svg,
        "visual_png": getattr(q, "visual_png", None),     # base64 PNG figure (RMO/INMO)
        "visual_requirement": getattr(q, "visual_requirement", None),
        "difficulty_tier": q.difficulty_tier,
        "irt_b": q.irt_b,
        "hint": q.hint,                      # Socratic hints never reveal the answer
        # Olympiad study cards reveal the worked solution on demand (not a graded quiz).
        "solution_steps": getattr(q, "solution_steps", None),
        "solution": getattr(q, "solution", None),
        "video_url": getattr(q, "video_url", None),   # per-problem video solution (reveal)
        "source": getattr(q, "source", None),         # provenance, e.g. "Vedantu OMM L6 · GCD & LCM"
        "verified": getattr(q, "verified", False),    # human-authored + key-validated → "Verified" badge
        # SECURITY: correct_answer / correct_value intentionally omitted here.
    }


# --------------------------------------------------------------- olympiad
@router.get("/olympiad/levels")
def olympiad_levels():
    return {"levels": level_store.levels()}


@router.get("/olympiad/strands")
def olympiad_strands():
    """The seven canonical olympiad strands (subtopics). Converted content is
    tagged with one of these; the app can show them as filter chips."""
    return {"strands": OLYMPIAD_STRANDS}


@router.get("/olympiad/levels/{level}/topics")
def olympiad_topics(level: str):
    topics = level_store.topics(level)
    if not topics:
        # empty (e.g. L4-L8) is valid — return [] so the UI shows "coming soon"
        return {"level": level, "topics": []}
    return {
        "level": level,
        "topics": [
            {
                "topic_key": t.topic_key,
                "display_name": t.display_name,
                "pillar": t.pillar,                 # internal; app hides it
                "pillar_name": PILLAR_NAMES.get(t.pillar, t.pillar),
                "question_count": len(t.questions),  # app hides it
                "available": bool(t.questions),
            }
            for t in topics
            if t.questions  # hide empty scaffold topics (0 questions)
        ],
    }


@router.get("/olympiad/levels/{level}/topics/{topic_key}/next")
def olympiad_next(
    level: str, topic_key: str,
    user_id: Optional[str] = Query(None, description="If set, selection follows this student's saved skill-ladder position"),
    theta: float = Query(0.0, description="Fallback ability used when no user_id is given"),
    exclude: Optional[str] = Query(None, description="Comma-separated ids to skip (IRT fallback only)"),
    mode: str = Query("skill", description="'skill' = concept-cluster ladder (default); 'irt' = ability-based"),
    decoded: Dict[str, Any] = Depends(verify_token),
):
    """Adaptive selection.

    Default ('skill' mode, when user_id is supplied): the concept-cluster ladder.
    The student is shown the **skill question** for their current rung; getting it
    right advances to the next skill, getting it wrong drips that skill's **cluster
    questions** until one is right or they run out (see app.services.adaptive_skill).
    The position is persisted, so this resumes exactly where the student left off.

    Fallback ('irt' mode, or no user_id, or a topic without skill tags): the older
    IRT ZPD selection — a question a touch below the student's ability so success
    stays ~65-80%."""
    # Bind the token identity to the requested user_id so a signed-in student
    # can't read/resume another student's ladder via ?user_id=.
    if user_id:
        assert_user_match(decoded, user_id)
    if user_id and mode != "irt":
        try:
            from app.services.adaptive_skill import engine_skill
            st = engine_skill.status(user_id, level, topic_key)
            if st["skills_total"] > 0:
                if st["completed"]:
                    raise HTTPException(404, "Topic complete — every skill cleared")
                qid = engine_skill.next_qid(user_id, level, topic_key)
                q = level_store.get(qid) if qid else None
                if q:
                    resp = _q_public(q)
                    resp["adaptive"] = st          # rung the student is on (for resume UI)
                    return resp
        except HTTPException:
            raise
        except Exception:
            pass  # fall through to IRT if the ladder is unavailable

    exclude_ids = [x.strip() for x in exclude.split(",")] if exclude else []
    sel_theta = theta
    if user_id:
        try:
            from app.services.adaptive_engine_v2 import engine_v2
            ability = engine_v2.get_ability(user_id, topic_key)
            sel_theta = ability.theta - 0.3  # ZPD: a touch below ability
        except Exception:
            pass
    q = level_store.next_adaptive(level, topic_key, theta=sel_theta, exclude_ids=exclude_ids)
    if not q:
        raise HTTPException(404, "No more questions for this level/topic")
    return _q_public(q)


@router.get("/olympiad/levels/{level}/topics/{topic_key}/adaptive-status")
def olympiad_adaptive_status(
    level: str, topic_key: str,
    user_id: str = Query(...),
    decoded: Dict[str, Any] = Depends(verify_token),
):
    """Where the student is on this topic's skill ladder — used to resume on
    login (skills_total, skill_index, on_cluster_question, completed)."""
    assert_user_match(decoded, user_id)
    from app.services.adaptive_skill import engine_skill
    try:
        return engine_skill.status(user_id, level, topic_key)
    except Exception:
        # Never 500 a resume call — report an empty/fresh ladder instead.
        return {"level": level, "topic": topic_key, "skills_total": 0,
                "skill_index": 0, "on_cluster_question": 0,
                "current_skill_id": None, "completed": False}


@router.get("/olympiad/levels/{level}/topics/{topic_key}/questions")
def olympiad_question_list(level: str, topic_key: str, limit: int = Query(20, ge=1, le=100)):
    qs = level_store.topic_questions(level, topic_key)
    if not qs:
        raise HTTPException(404, "Topic not found or empty")
    return {"level": level, "topic_key": topic_key, "total": len(qs),
            "questions": [_q_public(q) for q in qs[:limit]]}


@router.get("/olympiad/question/{qid}")
def olympiad_question(qid: str):
    q = level_store.get(qid)
    if not q:
        raise HTTPException(404, f"Question '{qid}' not found")
    return _q_public(q)


@router.get("/olympiad/question/{qid}/visual")
def olympiad_visual(qid: str):
    q = level_store.get(qid)
    if not q or not q.visual_svg:
        raise HTTPException(404, "No visual for this question")
    return Response(content=q.visual_svg, media_type="image/svg+xml")


# --------------------------------------------------------------- curriculum
@router.get("/curriculum/boards")
def curriculum_boards():
    return {"boards": level_store.boards()}


@router.get("/curriculum/{board}/grades")
def curriculum_grades(board: str):
    grades = level_store.grades(board)
    if not grades:
        raise HTTPException(404, f"No grades for board '{board}'")
    return {"board": board, "grades": grades}


@router.get("/curriculum/{board}/grade/{grade}/chapters")
def curriculum_chapters(board: str, grade: int):
    chapters = level_store.chapters(board, grade)
    if not chapters:
        raise HTTPException(404, f"No chapters for {board} grade {grade}")
    return {"board": board, "grade": grade,
            "total_questions": level_store.curriculum_total(board, grade),
            "chapters": chapters}


@router.get("/curriculum/{board}/grade/{grade}/chapter/{chapter}/questions")
def curriculum_chapter_questions(board: str, grade: int, chapter: str, limit: int = Query(50, ge=1, le=200)):
    qs = level_store.chapter_questions(board, grade, chapter)
    if not qs:
        raise HTTPException(404, f"Chapter '{chapter}' not found / empty")
    return {"board": board, "grade": grade, "chapter": chapter,
            "total": len(qs), "questions": [_q_public(q) for q in qs[:limit]]}


# --------------------------------------------------- unified economy / answer
class AnswerCheck(BaseModel):
    user_id: str
    question_id: str
    selected_index: Optional[int] = None     # MCQ: chosen choice index
    selected_value: Optional[Any] = None     # integer/fill-up: typed value
    hints_used: int = 0
    time_taken_ms: int = 0


def _is_correct(q, body: AnswerCheck) -> bool:
    if body.selected_index is not None and q.choices:
        try:
            if int(body.selected_index) == int(q.correct_answer):
                return True
        except (TypeError, ValueError):
            if str(body.selected_index).strip() == str(q.correct_answer).strip():
                return True
    if body.selected_value is not None and getattr(q, "correct_value", None) is not None:
        from app.services.content_store_level import numeric_correct
        if numeric_correct(q, body.selected_value):   # range-aware (fraction/decimal) or exact
            return True
    # also accept a typed value matching the keyed choice text
    if body.selected_value is not None and q.choices:
        try:
            if str(body.selected_value).strip() == str(q.choices[int(q.correct_answer)]).strip():
                return True
        except (IndexError, ValueError, TypeError):
            pass
    return False


@router.post("/answer/check")
def answer_check(
    body: AnswerCheck,
    decoded: Dict[str, Any] = Depends(verify_token),
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
):
    assert_user_match(decoded, body.user_id)

    if idempotency_key:
        cached = get_idempotent_response(idempotency_key)
        if cached is not None:
            return cached

    q = level_store.get(body.question_id)
    if not q:
        raise HTTPException(404, f"Question '{body.question_id}' not found")

    correct = _is_correct(q, body)
    meta = level_store.meta(q.id)               # (level, topic_key, pillar)
    topic_key = meta[1] if meta else (q.skill_id or "olympiad")

    # Drive the ONE economy. Coins/gems/xp/streak all flow from here and are
    # read back identically by /v3/me/wallet on every tab.
    events = gamification.record_answer(
        user_id=body.user_id,
        topic_id=topic_key,
        is_correct=correct,
        difficulty=int(getattr(q, "difficulty_score", 0) or 0),
        hints_used=body.hints_used,
        time_taken_seconds=(body.time_taken_ms or 0) / 1000.0,
        question_id=q.id,
    )

    # Also update IRT ability + proficiency so Growth/Parent (which read
    # /v2/proficiency) reflect /v3 practice — ONE source of truth, not a
    # parallel economy. Best-effort: never fail the answer check.
    try:
        from app.services.adaptive_engine_v2 import engine_v2
        from app.services.proficiency_levels import proficiency_store
        res = engine_v2.process_answer(
            user_id=body.user_id, topic_id=topic_key, question_id=q.id,
            question_difficulty=int(getattr(q, "difficulty_score", 0) or 0),
            is_correct=correct, time_taken_ms=body.time_taken_ms or 0,
        )
        approx_theta = res.new_difficulty / 33.33 - 1.5
        proficiency_store.update_proficiency(
            user_id=body.user_id, theta=approx_theta, grade=0,
            competency="K", correct=correct, topic_id=topic_key,
        )
    except Exception:
        pass

    # Advance the adaptive skill ladder (concept-cluster rule) and persist the
    # student's new position, so a re-login resumes exactly here — correct →
    # next skill; wrong → next cluster question (or next skill if exhausted).
    adaptive_status = None
    try:
        from app.services.adaptive_skill import engine_skill
        if meta:
            engine_skill.record(body.user_id, meta[0], meta[1], q.id, correct)
            adaptive_status = engine_skill.status(body.user_id, meta[0], meta[1])
    except Exception:
        pass

    # Small League Points for correct practice. The Daily Contest is the apex
    # source; this just lets everyday practice nudge the weekly league.
    try:
        if meta and correct:
            from app.services.league_service import league
            league.add_lp(body.user_id, meta[0], 5)
    except Exception:
        pass

    # Wrong-answer diagnostic for the chosen distractor.
    diagnostic = None
    if not correct and body.selected_index is not None and isinstance(q.diagnostics, dict):
        diagnostic = q.diagnostics.get(str(body.selected_index))

    resp = {
        "correct": correct,
        "correct_answer": q.correct_answer,
        "correct_value": getattr(q, "correct_value", None),
        "solution_steps": getattr(q, "solution_steps", None),
        "diagnostic": diagnostic,
        "adaptive": adaptive_status,     # skill-ladder rung after this answer
        "reward": {
            "xp": events.get("xp_earned", 0),
            "coins": events.get("coins_earned", 0),
            "gems": events.get("gems_earned", 0),
        },
        "badge_unlocks": events.get("badge_unlocks", []),
        "level_up": events.get("level_up"),
        "wallet": gamification.get_profile_summary(body.user_id),
    }
    if idempotency_key:
        record_idempotent_response(idempotency_key, resp)
    return resp


@router.get("/me/wallet")
def me_wallet(user_id: str = Query(...), decoded: Dict[str, Any] = Depends(verify_token)):
    """Single source of truth for coins / gems / XP / streak / topics — every
    tab (Olympiad header, Progress, Profile) reads this so nothing diverges."""
    assert_user_match(decoded, user_id)
    return gamification.get_profile_summary(user_id)


class SettingsUpdate(BaseModel):
    user_id: str
    selected_level: Optional[str] = None
    grade: Optional[int] = None
    curriculum: Optional[str] = None


@router.get("/me/settings")
def me_settings(user_id: str = Query(...), decoded: Dict[str, Any] = Depends(verify_token)):
    """The user's app-scoping settings: the chosen level (L1-L8), grade, and
    curriculum. ``onboarded`` is True once a level has been picked — the app
    shows onboarding until then, and scopes every tab to ``selected_level``
    after."""
    assert_user_match(decoded, user_id)
    from app.services.firestore_service import get_user_profile
    p = get_user_profile(user_id)
    return {
        "selected_level": p.get("selected_level"),
        "grade": p.get("grade"),
        "curriculum": p.get("curriculum"),
        "onboarded": bool(p.get("selected_level")),
    }


@router.post("/me/settings")
def set_me_settings(body: SettingsUpdate, decoded: Dict[str, Any] = Depends(verify_token)):
    """Set the chosen level / grade — onboarding and the in-app level switcher."""
    assert_user_match(decoded, body.user_id)
    from app.services.firestore_service import update_user_profile
    updates: Dict[str, Any] = {}
    if body.selected_level:
        updates["selected_level"] = body.selected_level
    if body.grade is not None:
        updates["grade"] = body.grade
    if body.curriculum:
        updates["curriculum"] = body.curriculum
    if updates:
        update_user_profile(body.user_id, updates)
    return {"ok": True, **updates}


@router.get("/me/progress")
def me_progress(
    user_id: str = Query(...),
    level: Optional[str] = Query(None, description="Scope to one level (e.g. L3); omit for overall"),
    decoded: Dict[str, Any] = Depends(verify_token),
):
    """Academic height + strand mastery, derived from the SAME gamification
    state as the wallet, so performance never disagrees with the economy.

    When ``level`` is given the score reflects mastery of THAT level's content
    only (so it genuinely changes as you switch level/grade); omit it for the
    student's overall academic height."""
    assert_user_match(decoded, user_id)
    state = gamification.get_state(user_id)

    # Strand mastery per pillar (NT/ALG/GEO/COM) + the Logic & Puzzles extra,
    # scoped to `level` when supplied.
    p_att: Dict[str, int] = defaultdict(int)
    p_cor: Dict[str, int] = defaultdict(int)
    logic_att = logic_cor = 0
    scope_att = scope_cor = scope_mastered = 0
    for tk in state.topics_practised:
        if level and not level_store.topic_in_level(tk, level):
            continue
        att = state.topic_attempts.get(tk, 0)
        cor = state.topic_correct.get(tk, 0)
        pil = level_store.pillar_for_topic(tk)
        if pil:
            p_att[pil] += att
            p_cor[pil] += cor
        if tk in LOGIC_TOPIC_KEYS:
            logic_att += att
            logic_cor += cor
        scope_att += att
        scope_cor += cor
        if att >= 3 and cor / att >= 0.70:
            scope_mastered += 1

    def pct(c: int, a: int) -> int:
        return round(100 * c / a) if a else 0

    strands = [
        {"pillar": p, "name": PILLAR_NAMES[p], "pct": pct(p_cor.get(p, 0), p_att.get(p, 0)),
         "attempts": p_att.get(p, 0)}
        for p in ("NT", "ALG", "GEO", "COM")
    ]
    logic = {"pillar": "LOGIC", "name": "Logic & Puzzles",
             "pct": pct(logic_cor, logic_att), "attempts": logic_att}

    # Scale score (200-800, 500 ~ average). Scoped to the level when given (so it
    # moves with grade/level), else the student's overall accuracy + breadth.
    if level:
        acc = (100.0 * scope_cor / scope_att) if scope_att else 0.0
        mastered = scope_mastered
    else:
        acc = state.accuracy_percent
        mastered = state.topics_mastered_count
    scale = max(200, min(800, round(440 + (acc - 50) * 3 + min(mastered, 40) * 2)))
    if scale < 460:
        verdict, band = "Building foundations", "building"
    elif scale <= 560:
        verdict, band = "On track", "on_track"
    else:
        verdict, band = "Ahead of grade", "ahead"

    return {
        "scale_score": scale,
        "scale_max": 800,
        "grade_average": 500,
        "verdict": verdict,
        "band": band,
        "accuracy": round(acc, 1),
        "topics_mastered": mastered,
        "streak": state.live_streak(),
        "strands": strands,
        "logic_puzzles": logic,
        "scope": level or "all",                      # which level this score reflects
        "scope_attempts": (scope_att if level else None),  # 0 => no practice yet at this level
    }


@router.get("/stats")
def v3_stats():
    return level_store.stats()
