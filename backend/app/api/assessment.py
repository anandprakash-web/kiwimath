"""
Assessment API — endpoints for diagnostic testing and path generation.

Endpoints:
    POST /assess/start          — Start a diagnostic CAT session for a domain
    GET  /assess/next-item      — Get the next adaptive item
    POST /assess/respond        — Submit a response, get updated estimate
    GET  /assess/result         — Get final assessment result
    POST /assess/full-diagnostic — Start full multi-domain diagnostic
    GET  /assess/report         — Get complete report with path recommendation
    POST /assess/end            — End session early
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.assessment.cat_engine import CATEngine, CATSession, Domain, StopReason
from app.assessment.item_bank import ItemBank
from app.assessment.irt_model import ItemParameters
from app.assessment.path_engine import PathEngine
from app.assessment.scoring import FullAssessmentReport
from app.assessment.spaced_rep import SpacedRepEngine
from app.services.ncert_content_store import ncert_store
from app.services.singapore_content_store import singapore_store
from app.services.uscc_content_store import uscc_store
from app.services.icse_content_store import icse_store
from app.services.question_history import question_history

router = APIRouter(prefix="/assess", tags=["assessment"])

# --- Singletons (initialized on startup) ---
_item_bank: Optional[ItemBank] = None
_cat_engine: Optional[CATEngine] = None
_path_engine: Optional[PathEngine] = None
_spaced_rep: Optional[SpacedRepEngine] = None

# Track multi-domain sessions: student_id -> {domain -> session_id}
_diagnostic_sessions: dict[str, dict[str, str]] = {}

# Track per-session exclusion sets: session_id -> set of item IDs to exclude
_session_exclusions: dict[str, set[str]] = {}


def get_item_bank() -> ItemBank:
    global _item_bank
    if _item_bank is None:
        _item_bank = ItemBank()
        _bootstrap_item_bank(_item_bank)
    return _item_bank


def get_cat_engine() -> CATEngine:
    global _cat_engine
    if _cat_engine is None:
        _cat_engine = CATEngine(get_item_bank())
    return _cat_engine


def get_path_engine() -> PathEngine:
    global _path_engine
    if _path_engine is None:
        _path_engine = PathEngine()
    return _path_engine


def get_spaced_rep() -> SpacedRepEngine:
    global _spaced_rep
    if _spaced_rep is None:
        _spaced_rep = SpacedRepEngine()
    return _spaced_rep


# --- Request/Response Models ---

class StartSessionRequest(BaseModel):
    student_id: str
    domain: str  # numbers, arithmetic, fractions, geometry, measurement
    grade: int = Field(ge=1, le=6)
    curriculum: Optional[str] = None
    prior_theta: Optional[float] = None


class StartSessionResponse(BaseModel):
    session_id: str
    domain: str
    first_item: dict


class RespondRequest(BaseModel):
    session_id: str
    item_id: str
    correct: bool
    response_time_sec: float = Field(ge=0)


class RespondResponse(BaseModel):
    theta: float
    se: float
    kiwiscore: int
    n_items: int
    correct: bool
    is_field_test: bool
    stop_reason: str
    converged: bool
    next_item: Optional[dict] = None


class FullDiagnosticRequest(BaseModel):
    student_id: str
    grade: int = Field(ge=1, le=6)
    curriculum: Optional[str] = None
    domains: Optional[list[str]] = None  # If None, assess all 5


class EndSessionRequest(BaseModel):
    session_id: str


# --- Endpoints ---

@router.post("/start", response_model=StartSessionResponse)
async def start_assessment(req: StartSessionRequest):
    """Start a CAT assessment session for a single domain."""
    try:
        domain = Domain(req.domain)
    except ValueError:
        raise HTTPException(400, f"Invalid domain: {req.domain}. Options: {[d.value for d in Domain]}")

    engine = get_cat_engine()
    session = engine.start_session(
        student_id=req.student_id,
        domain=domain,
        grade=req.grade,
        curriculum=req.curriculum,
        prior_theta=req.prior_theta,
    )

    # Load question history exclusion set for retests.
    exclude_ids: set[str] = set()
    if question_history.is_retest(req.student_id):
        bank = get_item_bank()
        total_available = bank.size
        exclude_ids = question_history.get_exclusion_set(
            req.student_id, total_available=total_available,
        )
        _session_exclusions[session.session_id] = exclude_ids

    # Start tracking this diagnostic session.
    question_history.start_diagnostic_session(req.student_id)

    # Select first item
    item = engine.select_next_item(session, exclude_ids=exclude_ids)
    if not item:
        raise HTTPException(503, "No items available for this domain/grade combination")

    # Record the served item in question history.
    question_history.record_diagnostic_question(
        req.student_id, item.item_id, "assessment",
    )

    return StartSessionResponse(
        session_id=session.session_id,
        domain=req.domain,
        first_item=_item_to_response(item),
    )


@router.get("/next-item")
async def get_next_item(session_id: str = Query(...)):
    """Get the next item in an active CAT session."""
    engine = get_cat_engine()
    session = engine.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.is_active:
        return {"done": True, "stop_reason": session.stop_reason.value}

    exclude_ids = _session_exclusions.get(session_id, set())
    item = engine.select_next_item(session, exclude_ids=exclude_ids)
    if not item:
        return {"done": True, "stop_reason": "no_items"}

    # Record the served item in question history.
    question_history.record_diagnostic_question(
        session.student_id, item.item_id, "assessment",
    )

    return {"done": False, "item": _item_to_response(item)}


@router.post("/respond", response_model=RespondResponse)
async def submit_response(req: RespondRequest):
    """Submit a response and get updated ability estimate."""
    engine = get_cat_engine()
    session = engine.get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.is_active:
        raise HTTPException(400, "Session already completed")

    item = get_item_bank().get_item(req.item_id)
    if not item:
        raise HTTPException(404, f"Item not found: {req.item_id}")

    result = engine.record_response(session, item, req.correct, req.response_time_sec)

    # Get next item if session still active
    next_item = None
    if result["stop_reason"] == "not_stopped":
        exclude_ids = _session_exclusions.get(req.session_id, set())
        next = engine.select_next_item(session, exclude_ids=exclude_ids)
        if next:
            next_item = _item_to_response(next)
            # Record the next item in question history.
            question_history.record_diagnostic_question(
                session.student_id, next.item_id, "assessment",
            )
    else:
        # Session ended — finalise the diagnostic session in question history.
        question_history.end_diagnostic_session(session.student_id)
        # Clean up exclusion set.
        _session_exclusions.pop(req.session_id, None)

    return RespondResponse(
        theta=result["theta"],
        se=result["se"],
        kiwiscore=result["kiwiscore"],
        n_items=result["n_items"],
        correct=result["correct"],
        is_field_test=result["is_field_test"],
        stop_reason=result["stop_reason"],
        converged=result["converged"],
        next_item=next_item,
    )


@router.get("/result")
async def get_result(session_id: str = Query(...)):
    """Get final result for a completed session."""
    engine = get_cat_engine()
    session = engine.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    return engine.get_result(session)


@router.post("/full-diagnostic")
async def start_full_diagnostic(req: FullDiagnosticRequest):
    """Start a full multi-domain diagnostic assessment.

    Creates sessions for all requested domains and returns the first item
    from the first domain.  On retests, previously seen questions are
    excluded to prevent answer memorisation.
    """
    domains = req.domains or [d.value for d in Domain]
    engine = get_cat_engine()

    # Load exclusion set once for this student (shared across all domains).
    exclude_ids: set[str] = set()
    if question_history.is_retest(req.student_id):
        bank = get_item_bank()
        total_available = bank.size
        exclude_ids = question_history.get_exclusion_set(
            req.student_id, total_available=total_available,
        )

    # Start tracking this diagnostic session.
    question_history.start_diagnostic_session(req.student_id)

    sessions = {}
    for domain_str in domains:
        try:
            domain = Domain(domain_str)
        except ValueError:
            continue
        session = engine.start_session(
            student_id=req.student_id,
            domain=domain,
            grade=req.grade,
            curriculum=req.curriculum,
        )
        sessions[domain_str] = session.session_id
        # Store the exclusion set for each session so subsequent
        # next-item / respond calls can use it.
        if exclude_ids:
            _session_exclusions[session.session_id] = exclude_ids

    # Track for this student
    _diagnostic_sessions[req.student_id] = sessions

    # Get first item from first domain
    first_domain = domains[0]
    first_session = engine.get_session(sessions[first_domain])
    first_item = engine.select_next_item(first_session, exclude_ids=exclude_ids)

    # Record the first item in question history.
    if first_item:
        question_history.record_diagnostic_question(
            req.student_id, first_item.item_id, "full_diagnostic",
        )

    return {
        "student_id": req.student_id,
        "sessions": sessions,
        "current_domain": first_domain,
        "total_domains": len(domains),
        "first_item": _item_to_response(first_item) if first_item else None,
    }


@router.get("/report")
async def get_full_report(student_id: str = Query(...)):
    """Get complete assessment report with learning path recommendation.

    Requires all domain sessions to be completed.
    """
    sessions = _diagnostic_sessions.get(student_id)
    if not sessions:
        raise HTTPException(404, "No diagnostic found for this student")

    engine = get_cat_engine()
    domain_results = {}

    for domain, session_id in sessions.items():
        session = engine.get_session(session_id)
        if not session:
            continue
        if session.is_active:
            raise HTTPException(400, f"Domain '{domain}' assessment not yet complete")
        domain_results[domain] = (session.ability.theta, session.ability.se)

    if not domain_results:
        raise HTTPException(404, "No completed assessments found")

    # Get grade/curriculum from first session
    first_session = engine.get_session(list(sessions.values())[0])
    grade = first_session.grade if first_session else 3
    curriculum = first_session.curriculum or "NCERT"

    # Build report
    report = FullAssessmentReport.from_domain_scores(
        student_id=student_id,
        grade=grade,
        curriculum=curriculum,
        domain_results=domain_results,
    )

    # Generate learning path
    path_engine = get_path_engine()
    domain_thetas = {d: t for d, (t, _) in domain_results.items()}
    path = path_engine.generate_path(
        student_id=student_id,
        domain_scores=domain_thetas,
        grade=grade,
        curriculum=curriculum,
    )

    return {
        "report": report.to_dict(),
        "learning_path": path.to_dict(),
    }


@router.post("/end")
async def end_session(req: EndSessionRequest):
    """End a session early and get partial results."""
    engine = get_cat_engine()
    session = engine.get_session(req.session_id)
    result = engine.end_session(req.session_id)
    if not result:
        raise HTTPException(404, "Session not found")
    # Finalise question history for this student.
    if session:
        question_history.end_diagnostic_session(session.student_id)
    _session_exclusions.pop(req.session_id, None)
    return result


@router.get("/spaced-review")
async def get_spaced_review(
    student_id: str = Query(...),
    max_items: int = Query(default=10, ge=1, le=30),
):
    """Get skills that need spaced review."""
    sr = get_spaced_rep()
    queue = sr.get_review_queue(student_id, max_items=max_items)
    return {
        "student_id": student_id,
        "review_items": [
            {
                "skill_id": m.skill_id,
                "recall_probability": round(m.recall_probability(), 3),
                "priority": round(m.review_priority(), 3),
                "hours_until_review": round(m.time_until_review(), 1),
                "strength": round(m.strength, 2),
            }
            for m in queue
        ],
        "health": sr.get_skill_health(student_id),
    }


@router.get("/item-bank/stats")
async def get_item_bank_stats():
    """Get item bank health statistics."""
    bank = get_item_bank()
    return {
        "total_items": bank.size,
        "domain_stats": bank.get_domain_stats(),
        "items_needing_review": len(bank.get_items_needing_review()),
    }


@router.get("/curricula")
async def list_curricula():
    """List available curricula and their question counts."""
    curricula = [
        {
            "id": "NCERT",
            "name": "NCERT (CBSE)",
            "description": "National Council of Educational Research and Training — India's CBSE curriculum",
            "grades": list(range(1, 7)),
            "total_questions": ncert_store.total_questions,
            "questions_by_grade": ncert_store.questions_by_grade(),
            "id_prefix": "NCERT-G",
        },
        {
            "id": "SINGAPORE",
            "name": "Singapore Math",
            "description": "Singapore Ministry of Education mathematics curriculum — CPA approach",
            "grades": list(range(1, 7)),
            "total_questions": singapore_store.total_questions,
            "questions_by_grade": singapore_store.questions_by_grade(),
            "id_prefix": "SING-G",
        },
        {
            "id": "US_COMMON_CORE",
            "name": "US Common Core",
            "description": "Common Core State Standards for Mathematics — United States",
            "grades": list(range(1, 7)),
            "total_questions": uscc_store.total_questions,
            "questions_by_grade": uscc_store.questions_by_grade(),
            "id_prefix": "USCC-G",
        },
        {
            "id": "ICSE",
            "name": "ICSE (CISCE)",
            "description": "Indian Certificate of Secondary Education — CISCE curriculum",
            "grades": list(range(1, 7)),
            "total_questions": icse_store.total_questions,
            "questions_by_grade": icse_store.questions_by_grade(),
            "id_prefix": "ICSE-G",
        },
    ]
    total = sum(c["total_questions"] for c in curricula)
    return {
        "total_questions": total,
        "total_curricula": len(curricula),
        "curricula": curricula,
    }


# --- Helpers ---

def _item_to_response(item: ItemParameters) -> dict:
    """Convert item to API response with full question content for Flutter."""
    response = {
        "item_id": item.item_id,
        "domain": item.domain,
        "subdomain": item.subdomain,
    }

    # Enrich with actual question content from the appropriate curriculum store
    if item.item_id.startswith("ICSE-"):
        content = icse_store.get_question_content_for_response(item.item_id)
    elif item.item_id.startswith("USCC-"):
        content = uscc_store.get_question_content_for_response(item.item_id)
    elif item.item_id.startswith("SING-"):
        content = singapore_store.get_question_content_for_response(item.item_id)
    else:
        content = ncert_store.get_question_content_for_response(item.item_id)
    if content:
        response["stem"] = content["stem"]
        response["choices"] = content["choices"]
        response["correct_answer"] = content["correct_answer"]
        response["visual_svg"] = content["visual_svg"]
        response["visual_url"] = content["visual_url"]
        response["visual_alt"] = content["visual_alt"]
        response["hint"] = content["hint"]
        response["diagnostics"] = content["diagnostics"]
        response["difficulty_tier"] = content["difficulty_tier"]
        response["chapter"] = content["chapter"]
        response["tags"] = content["tags"]

    return response


def _bootstrap_item_bank(bank: ItemBank) -> None:
    """Bootstrap item bank with expert-calibrated parameters.

    In production, this loads from Firestore. For now, creates initial items
    from existing content with estimated parameters based on difficulty level.
    """
    import json
    from pathlib import Path

    # Try to load from calibrated items file (multiple candidate paths)
    candidate_paths = [
        Path(__file__).resolve().parent.parent.parent / "assessment_items.json",  # backend/
        Path("/app/assessment_items.json"),  # Docker
    ]
    for calibrated_path in candidate_paths:
        if calibrated_path.exists():
            with open(calibrated_path) as f:
                items_data = json.load(f)
            bank.add_items([
                ItemParameters(
                    item_id=d["item_id"],
                    a=d["a"], b=d["b"], c=d["c"],
                    domain=d["domain"],
                    subdomain=d.get("subdomain", ""),
                    curriculum_tags=d.get("curriculum_tags", []),
                    grade_range=tuple(d.get("grade_range", [1, 6])),
                    state=d.get("state", "active"),
                )
                for d in items_data
            ])
            return

    # Fallback: generate from existing content with estimated parameters
    # Map difficulty 1-100 to IRT b parameter (-3 to +3)
    # Discrimination estimated from topic/type
    # Guessing = 0.25 for 4-choice MCQ
    _generate_initial_items(bank)


def _generate_initial_items(bank: ItemBank) -> None:
    """Generate initial item parameters from content difficulty levels.

    Uses heuristic mapping:
        difficulty 1-100 → b: linear map to [-3.0, +3.0]
        a: 1.0 for standard, 1.5 for discriminating items
        c: 0.25 for 4-choice MCQ
    """
    # Domain mapping from topic IDs
    topic_to_domain = {
        "T1": "numbers", "T2": "arithmetic", "T3": "geometry",
        "T4": "measurement", "T5": "arithmetic", "T6": "fractions",
        "T7": "geometry", "T8": "numbers",
    }

    # Generate placeholder items for each domain/difficulty combination
    for domain in Domain:
        for diff_level in range(1, 101):
            b = -3.0 + (diff_level - 1) * 6.0 / 99.0  # Map 1-100 to -3..+3
            item = ItemParameters(
                item_id=f"ASSESS_{domain.value.upper()}_{diff_level:03d}",
                a=1.2,  # Moderate discrimination
                b=round(b, 2),
                c=0.25,  # 4-choice MCQ guessing
                domain=domain.value,
                subdomain=f"{domain.value}_level_{diff_level // 20 + 1}",
                curriculum_tags=["NCERT", "OLYMPIAD"],
                grade_range=(max(1, diff_level // 20), min(6, diff_level // 15 + 1)),
                state="active",
            )
            bank.add_item(item)
