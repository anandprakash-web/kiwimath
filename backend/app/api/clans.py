"""
Kiwimath Clan API — v4 endpoints for clan operations.

Endpoints (12):
    POST   /v4/clans                              → Create clan (parent-gated)
    GET    /v4/clans/{clan_id}                    → Get clan details
    POST   /v4/clans/join                         → Join via invite code (parent-gated)
    DELETE /v4/clans/{clan_id}/members/{uid}      → Remove member
    POST   /v4/clans/{clan_id}/invite             → Regenerate invite code
    GET    /v4/clans/leaderboard/{grade}          → Top 20 for grade
    POST   /v4/clans/{clan_id}/react              → Send emoji reaction

    GET    /v4/challenges/active                  → Current active challenge
    GET    /v4/challenges/{cid}/progress/{clan_id}→ Clan's challenge progress
    POST   /v4/challenges/{cid}/answer            → Submit answer (leader only)
    GET    /v4/challenges/{cid}/guesses/{clan_id} → Get clan's guess board
    POST   /v4/challenges/{cid}/guess             → Submit a guess (1/day, 60 chars)

Persistence:
    All clan state lives in Firestore via ClanFirestoreService
    (app/services/clan_firestore.py). When Firestore is unavailable
    (local dev / tests without firebase-admin) the module-level dicts
    below act as the fallback store so everything still works.

    Firestore queries used (may require composite indexes):
      - clans: member_uids array_contains + status ==   (find my clan)
      - clans: invite_code == + status ==               (join by code)
      - clans: grade == + status ==                     (leaderboard)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth import internal_key_matches

from app.services.clan_firestore import ClanFirestoreService
from app.services.state_store import FirestoreBackedStore
from app.services.clan_service import (
    CREST_COLORS,
    CREST_SHAPES,
    MAX_CLAN_SIZE,
    can_submit_answer,
    compute_answer_points,
    compute_blocks_revealed,
    filter_clan_name,
    filter_guess_text,
    generate_block_order,
    generate_invite_code,
    get_clan_level,
    new_clan_doc,
    new_daily_score_doc,
    rank_clans,
)

router = APIRouter(prefix="/v4", tags=["clans"])

# ---------------------------------------------------------------------------
# Persistence layer
# ---------------------------------------------------------------------------
# Firestore-backed (authoritative in production). The dicts below are used
# ONLY as the fallback store when Firestore is unavailable — they are not a
# read-through cache, so reads never serve stale cross-instance data.
_clan_fs = ClanFirestoreService()

_clans: Dict[str, Dict[str, Any]] = {}
_daily_scores: Dict[str, Dict[str, Any]] = {}  # "{clan_id}:{date}" or "{clan_id}:{uid}:{date}"
_challenges: Dict[str, Dict[str, Any]] = {}
_clan_challenge_progress: Dict[str, Dict[str, Dict[str, Any]]] = {}  # clan_id -> cid -> progress
_guesses: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {}  # clan_id -> cid -> uid -> guess

# Reactions are ephemeral social fluff — short-TTL read cache is fine.
_reactions_store = FirestoreBackedStore("clan_reactions", cache_ttl_seconds=10)
# Per-member daily practice scores (written by the practice pipeline; read by
# the daily aggregation cron). Key: "{clan_id}:{uid}:{date}".
_member_scores_store = FirestoreBackedStore("clan_member_daily_scores")


def _fs() -> bool:
    """True when Firestore is connected (authoritative mode)."""
    try:
        from app.services.firestore_service import is_firestore_available
        return is_firestore_available()
    except Exception:
        return False


# --- Clan accessors --------------------------------------------------------

def get_clan_doc(clan_id: str) -> Optional[Dict[str, Any]]:
    """Public accessor used by other routers (e.g. engagement pledges)."""
    if _fs():
        return _clan_fs.get_clan(clan_id)
    return _clans.get(clan_id)


def _save_clan(clan_id: str, doc: Dict[str, Any]) -> None:
    if _fs():
        _clan_fs.create_clan(clan_id, doc)
    else:
        _clans[clan_id] = doc


def _update_clan(clan_id: str, updates: Dict[str, Any]) -> None:
    if _fs():
        _clan_fs.update_clan(clan_id, updates)
    else:
        _clans.setdefault(clan_id, {}).update(updates)


def _find_clan_by_member(uid: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    if _fs():
        return _clan_fs.find_clan_by_member(uid)
    for cid, clan in _clans.items():
        if uid in clan.get("member_uids", []) and clan.get("status") == "active":
            return cid, clan
    return None


def _find_clan_by_invite(code: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    if _fs():
        return _clan_fs.find_clan_by_invite_code(code)
    for cid, clan in _clans.items():
        if clan.get("invite_code") == code and clan.get("status") == "active":
            return cid, clan
    return None


def _find_clans_by_grade(grade: int) -> List[Tuple[str, Dict[str, Any]]]:
    if _fs():
        return _clan_fs.find_clans_by_grade(grade)
    return [
        (cid, clan) for cid, clan in _clans.items()
        if clan.get("grade") == grade and clan.get("status") == "active"
    ]


def _all_active_clans() -> List[Tuple[str, Dict[str, Any]]]:
    if _fs():
        return _clan_fs.all_active_clans()
    return [(cid, c) for cid, c in _clans.items() if c.get("status") == "active"]


# --- Challenge accessors -----------------------------------------------------

def _get_challenge(challenge_id: str) -> Optional[Dict[str, Any]]:
    if _fs():
        return _clan_fs.get_challenge(challenge_id)
    return _challenges.get(challenge_id)


def _find_active_challenge() -> Optional[Tuple[str, Dict[str, Any]]]:
    if _fs():
        return _clan_fs.find_active_challenge()
    for cid, ch in _challenges.items():
        if ch.get("status") == "active":
            return cid, ch
    return None


def _get_progress(clan_id: str, challenge_id: str) -> Dict[str, Any]:
    if _fs():
        return _clan_fs.get_challenge_progress(clan_id, challenge_id) or {}
    return _clan_challenge_progress.get(clan_id, {}).get(challenge_id, {})


def _update_progress(clan_id: str, challenge_id: str, updates: Dict[str, Any]) -> None:
    if _fs():
        _clan_fs.update_challenge_progress(clan_id, challenge_id, updates)
    else:
        prog = _clan_challenge_progress.setdefault(clan_id, {}).setdefault(challenge_id, {})
        prog.update(updates)


# --- Guess accessors ----------------------------------------------------------

def _get_guess_map(clan_id: str, challenge_id: str) -> Dict[str, Dict[str, Any]]:
    """Return uid -> guess dict for a clan + challenge."""
    if _fs():
        entries = _clan_fs.get_guesses(clan_id, challenge_id)
        return {e["uid"]: e for e in entries}
    return _guesses.get(clan_id, {}).get(challenge_id, {})


def _save_guess(clan_id: str, challenge_id: str, uid: str, guess: Dict[str, Any]) -> None:
    if _fs():
        _clan_fs.add_guess(clan_id, challenge_id, uid, guess)
    else:
        _guesses.setdefault(clan_id, {}).setdefault(challenge_id, {})[uid] = guess


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class CreateClanRequest(BaseModel):
    name: str = Field(..., max_length=20, min_length=3)
    grade: int = Field(..., ge=1, le=6)
    leader_uid: str
    parent_uid: str  # parent must authorize
    crest_shape: str = "bolt"
    crest_color: str = "#FF6D00"


class JoinClanRequest(BaseModel):
    invite_code: str
    uid: str
    parent_uid: str  # parent must authorize
    grade: int = Field(..., ge=1, le=6)


class SubmitAnswerRequest(BaseModel):
    clan_id: str
    uid: str  # must be leader
    answer: str = Field(..., max_length=60)


class SubmitGuessRequest(BaseModel):
    clan_id: str
    uid: str
    guess_text: str = Field(..., max_length=60)


class ReactRequest(BaseModel):
    uid: str
    emoji: str  # one of: high_five, fire, star, brain, muscle


class ClanResponse(BaseModel):
    clan_id: str
    name: str
    grade: int
    crest: Dict[str, str]
    leader_uid: str
    member_count: int
    status: str
    lifetime_brain_points: int
    lifetime_brawn_points: int
    lifetime_quiz_points: int
    clan_level: Dict[str, Any]
    invite_code: Optional[str] = None
    invite_expires_at: Optional[str] = None
    member_uids: List[str] = []
    created_at: str = ""


class LeaderboardEntry(BaseModel):
    rank: int
    clan_id: str
    name: str
    crest: Dict[str, str]
    member_count: int
    clan_level: Dict[str, Any]
    total_points: int


class ChallengeResponse(BaseModel):
    challenge_id: str
    title: str
    puzzle_type: str
    difficulty_tier: str
    grid_rows: int
    grid_cols: int
    duration_days: int
    start_date: str
    end_date: str
    status: str
    days_remaining: int = 0


class ChallengeProgressResponse(BaseModel):
    clan_id: str
    challenge_id: str
    total_clan_points: int
    brain_points: int
    quiz_points: int
    brawn_points: int
    blocks_revealed: int
    total_blocks: int
    reveal_percentage: float
    can_submit: bool
    current_answer: Optional[str] = None
    answer_day: Optional[int] = None
    answer_points_today: int = 0
    block_order: List[int] = []


class GuessEntry(BaseModel):
    uid: str
    initial: str
    guess_text: str
    day_number: int
    submitted_at: str


def _clan_response(clan_id: str, clan: Dict[str, Any], include_private: bool = True) -> ClanResponse:
    return ClanResponse(
        clan_id=clan_id,
        name=clan["name"],
        grade=clan["grade"],
        crest=clan["crest"],
        leader_uid=clan["leader_uid"],
        member_count=len(clan.get("member_uids", [])),
        status=clan.get("status", "active"),
        lifetime_brain_points=clan.get("lifetime_brain_points", 0),
        lifetime_brawn_points=clan.get("lifetime_brawn_points", 0),
        lifetime_quiz_points=clan.get("lifetime_quiz_points", 0),
        clan_level=get_clan_level(clan.get("clan_xp", 0)),
        invite_code=clan.get("invite_code") if include_private else None,
        invite_expires_at=clan.get("invite_expires_at") if include_private else None,
        member_uids=clan.get("member_uids", []) if include_private else [],
        created_at=clan.get("created_at", ""),
    )


# ---------------------------------------------------------------------------
# Clan CRUD
# ---------------------------------------------------------------------------

@router.post("/clans", response_model=ClanResponse)
async def create_clan(req: CreateClanRequest):
    """Create a new clan (parent-authorized)."""
    # Validate name
    valid, reason = filter_clan_name(req.name)
    if not valid:
        raise HTTPException(400, reason)

    # Validate crest
    if req.crest_shape not in CREST_SHAPES:
        raise HTTPException(400, f"Invalid crest shape. Choose from: {CREST_SHAPES}")
    if req.crest_color not in CREST_COLORS:
        raise HTTPException(400, f"Invalid crest color. Choose from: {CREST_COLORS}")

    # Check if user already in a clan
    if _find_clan_by_member(req.leader_uid):
        raise HTTPException(400, "You are already in a clan. Leave your current clan first.")

    # Create clan
    import uuid
    clan_id = f"clan_{uuid.uuid4().hex[:12]}"
    doc = new_clan_doc(
        name=req.name,
        grade=req.grade,
        leader_uid=req.leader_uid,
        crest_shape=req.crest_shape,
        crest_color=req.crest_color,
    )
    _save_clan(clan_id, doc)

    return _clan_response(clan_id, doc)


@router.get("/clans/mine")
async def get_my_clan(user_uid: str = Query(...)):
    """Look up the clan a user belongs to. Returns 404 if not in any clan."""
    found = _find_clan_by_member(user_uid)
    if not found:
        raise HTTPException(404, "You are not in any clan")
    cid, clan = found
    return _clan_response(cid, clan)


@router.get("/clans/{clan_id}", response_model=ClanResponse)
async def get_clan(clan_id: str, uid: Optional[str] = None):
    """Get clan details. Only members see invite code and member list."""
    clan = get_clan_doc(clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")

    is_member = uid in clan.get("member_uids", []) if uid else False
    return _clan_response(clan_id, clan, include_private=is_member)


@router.post("/clans/join", response_model=ClanResponse)
async def join_clan(req: JoinClanRequest):
    """Join a clan via invite code (parent-authorized)."""
    found = _find_clan_by_invite(req.invite_code)
    if not found:
        raise HTTPException(404, "Invalid or expired invite code")
    target_clan_id, target_clan = found

    # Check expiry
    expires = target_clan.get("invite_expires_at", "")
    if expires:
        exp_dt = datetime.fromisoformat(expires)
        if datetime.now(timezone.utc) > exp_dt:
            raise HTTPException(400, "This invite code has expired. Ask the clan leader for a new one.")

    # Grade check with helpful redirect
    if target_clan["grade"] != req.grade:
        raise HTTPException(
            400,
            f"This clan is for Grade {target_clan['grade']}. "
            f"You're in Grade {req.grade}. "
            f"Want to start your own Grade {req.grade} clan instead?"
        )

    # Size check
    if len(target_clan["member_uids"]) >= MAX_CLAN_SIZE:
        raise HTTPException(400, "This clan is full (max 15 members)")

    # Already a member check
    if req.uid in target_clan["member_uids"]:
        raise HTTPException(400, "You are already in this clan")

    # Check if user is in another clan
    other = _find_clan_by_member(req.uid)
    if other and other[0] != target_clan_id:
        raise HTTPException(400, "You are already in another clan. Leave it first.")

    # Join. NOTE: read-modify-write — two simultaneous joins could briefly
    # exceed MAX_CLAN_SIZE or drop one member (last write wins). Join traffic
    # per clan is tiny; accepted.
    target_clan["member_uids"].append(req.uid)
    _update_clan(target_clan_id, {"member_uids": target_clan["member_uids"]})

    return _clan_response(target_clan_id, target_clan)


@router.delete("/clans/{clan_id}/members/{uid}")
async def remove_member(clan_id: str, uid: str, requester_uid: str = Query(...)):
    """Remove a member (leader or self-removal). Gentle messaging — no 'kicked' language."""
    clan = get_clan_doc(clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")

    if uid not in clan["member_uids"]:
        raise HTTPException(400, "This person is not in the clan")

    # Only leader or self can remove
    if requester_uid != clan["leader_uid"] and requester_uid != uid:
        raise HTTPException(403, "Only the clan leader can remove members")

    clan["member_uids"].remove(uid)
    updates: Dict[str, Any] = {"member_uids": clan["member_uids"]}

    # If leader leaves, promote longest-tenured
    if uid == clan["leader_uid"] and clan["member_uids"]:
        clan["leader_uid"] = clan["member_uids"][0]
        updates["leader_uid"] = clan["leader_uid"]

    # If empty, dissolve
    if not clan["member_uids"]:
        clan["status"] = "dissolved"
        updates["status"] = "dissolved"

    _update_clan(clan_id, updates)

    return {"message": "This clan adventure has ended for this member", "remaining_members": len(clan["member_uids"])}


@router.post("/clans/{clan_id}/invite")
async def regenerate_invite(clan_id: str, uid: str = Query(...)):
    """Regenerate invite code (leader only)."""
    clan = get_clan_doc(clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")
    if uid != clan["leader_uid"]:
        raise HTTPException(403, "Only the clan leader can regenerate invite codes")

    new_code = generate_invite_code()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
    _update_clan(clan_id, {"invite_code": new_code, "invite_expires_at": expires_at})

    return {"invite_code": new_code, "expires_at": expires_at}


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

@router.get("/clans/leaderboard/{grade}")
async def get_leaderboard(
    grade: int,
    challenge_id: Optional[str] = None,
    limit: int = Query(20, le=50),
):
    """Get top clans for a grade. Optionally filter by challenge."""
    grade_clans = [
        {**clan, "clan_id": cid}
        for cid, clan in _find_clans_by_grade(grade)
    ]

    sort_key = "lifetime_brain_points"
    if challenge_id:
        # Use challenge-specific points (one progress read per clan; grade
        # leaderboards are capped at 50 clans so this stays bounded).
        for clan in grade_clans:
            progress = _get_progress(clan["clan_id"], challenge_id)
            clan["challenge_points"] = progress.get("total_clan_points", 0)
        sort_key = "challenge_points"

    ranked = rank_clans(grade_clans, sort_key)[:limit]

    return [
        LeaderboardEntry(
            rank=c["rank"],
            clan_id=c["clan_id"],
            name=c["name"],
            crest=c["crest"],
            member_count=len(c["member_uids"]),
            clan_level=get_clan_level(c.get("clan_xp", 0)),
            total_points=c.get(sort_key, 0),
        )
        for c in ranked
    ]


# ---------------------------------------------------------------------------
# Emoji Reactions (pre-set only, throttled)
# ---------------------------------------------------------------------------

VALID_EMOJIS = {"high_five", "fire", "star", "brain", "muscle"}

@router.post("/clans/{clan_id}/react")
async def send_reaction(clan_id: str, req: ReactRequest):
    """Send a pre-set emoji reaction (throttled: 1 per type per hour)."""
    clan = get_clan_doc(clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")
    if req.emoji not in VALID_EMOJIS:
        raise HTTPException(400, f"Invalid emoji. Choose from: {VALID_EMOJIS}")

    if req.uid not in clan["member_uids"]:
        raise HTTPException(403, "You must be a clan member to react")

    doc = _reactions_store.get(clan_id, allow_cached=False) or {"reactions": []}
    doc["reactions"].append({
        "uid": req.uid,
        "emoji": req.emoji,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # Keep only last 50 reactions
    doc["reactions"] = doc["reactions"][-50:]
    _reactions_store.set(clan_id, doc)

    return {"status": "ok", "emoji": req.emoji}


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------

@router.get("/challenges/active")
async def get_active_challenge():
    """Get the current active Picture Unravel challenge."""
    now = datetime.now(timezone.utc)
    found = _find_active_challenge()
    if found:
        cid, ch = found
        end = datetime.fromisoformat(ch["end_date"])
        days_remaining = max(0, (end - now).days)
        return ChallengeResponse(
            challenge_id=cid,
            title=ch["title"],
            puzzle_type=ch.get("puzzle_type", "pattern_sequence"),
            difficulty_tier=ch.get("difficulty_tier", "explorer"),
            grid_rows=ch["grid_rows"],
            grid_cols=ch["grid_cols"],
            duration_days=ch["duration_days"],
            start_date=ch["start_date"],
            end_date=ch["end_date"],
            status="active",
            days_remaining=days_remaining,
        )
    return {"message": "No active challenge right now", "status": "none"}


@router.get("/challenges/{challenge_id}/progress/{clan_id}")
async def get_challenge_progress(challenge_id: str, clan_id: str):
    """Get clan's progress in a challenge — blocks revealed, scores, answer status."""
    ch = _get_challenge(challenge_id)
    if not ch:
        raise HTTPException(404, "Challenge not found")
    clan = get_clan_doc(clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")

    total_blocks = ch["grid_rows"] * ch["grid_cols"]
    progress = _get_progress(clan_id, challenge_id)

    total_points = progress.get("total_clan_points", 0)
    brain = progress.get("brain_points", 0)
    quiz = progress.get("quiz_points", 0)
    brawn = progress.get("brawn_points", 0)

    blocks = compute_blocks_revealed(total_points, ch.get("points_per_block", 100), total_blocks)
    can_sub = can_submit_answer(blocks, total_blocks)

    # Calculate current day number
    start = datetime.fromisoformat(ch["start_date"])
    now = datetime.now(timezone.utc)
    day_number = max(1, (now - start).days + 1)
    pts_today = compute_answer_points(day_number, ch["duration_days"])

    block_order = generate_block_order(total_blocks, challenge_id)

    return ChallengeProgressResponse(
        clan_id=clan_id,
        challenge_id=challenge_id,
        total_clan_points=total_points,
        brain_points=brain,
        quiz_points=quiz,
        brawn_points=brawn,
        blocks_revealed=blocks,
        total_blocks=total_blocks,
        reveal_percentage=round(blocks / max(1, total_blocks) * 100, 1),
        can_submit=can_sub,
        current_answer=progress.get("answer"),
        answer_day=progress.get("answer_day"),
        answer_points_today=pts_today,
        block_order=block_order,
    )


@router.post("/challenges/{challenge_id}/answer")
async def submit_answer(challenge_id: str, req: SubmitAnswerRequest):
    """Submit or update the official answer (leader only)."""
    ch = _get_challenge(challenge_id)
    if not ch:
        raise HTTPException(404, "Challenge not found")
    clan = get_clan_doc(req.clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")
    if req.uid != clan["leader_uid"]:
        raise HTTPException(403, "Only the clan leader can submit the official answer")

    total_blocks = ch["grid_rows"] * ch["grid_cols"]
    progress = _get_progress(req.clan_id, challenge_id)
    total_points = progress.get("total_clan_points", 0)
    blocks = compute_blocks_revealed(total_points, ch.get("points_per_block", 100), total_blocks)

    if not can_submit_answer(blocks, total_blocks):
        pct = round(blocks / max(1, total_blocks) * 100, 1)
        raise HTTPException(400, f"Submit unlocks at 30% revealed. Currently at {pct}%.")

    start = datetime.fromisoformat(ch["start_date"])
    day_number = max(1, (datetime.now(timezone.utc) - start).days + 1)
    pts = compute_answer_points(day_number, ch["duration_days"])

    answer = req.answer.strip()
    _update_progress(req.clan_id, challenge_id, {
        "answer": answer,
        "answer_day": day_number,
        "answer_points": pts,
    })

    return {
        "answer": answer,
        "day_submitted": day_number,
        "points_if_correct": pts,
        "message": "Answer updated. You can change it again — last answer counts.",
    }


# ---------------------------------------------------------------------------
# Guess Board
# ---------------------------------------------------------------------------

@router.get("/challenges/{challenge_id}/guesses/{clan_id}")
async def get_guess_board(challenge_id: str, clan_id: str):
    """Get all guesses from clan members for this challenge."""
    clan_guesses = _get_guess_map(clan_id, challenge_id)

    entries = []
    for uid, guess in sorted(clan_guesses.items(), key=lambda x: x[1].get("submitted_at", "")):
        entries.append(GuessEntry(
            uid=uid,
            initial=uid[0].upper() if uid else "?",
            guess_text=guess["guess_text"],
            day_number=guess.get("day_number", 1),
            submitted_at=guess.get("submitted_at", ""),
        ))

    return {"challenge_id": challenge_id, "clan_id": clan_id, "guesses": entries}


@router.post("/challenges/{challenge_id}/guess")
async def submit_guess(challenge_id: str, req: SubmitGuessRequest):
    """Submit a guess to the clan's guess board (1/day, 60 chars, filtered)."""
    ch = _get_challenge(challenge_id)
    if not ch:
        raise HTTPException(404, "Challenge not found")
    clan = get_clan_doc(req.clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")
    if req.uid not in clan["member_uids"]:
        raise HTTPException(403, "You must be a clan member to submit guesses")

    # Filter
    valid, reason = filter_guess_text(req.guess_text)
    if not valid:
        raise HTTPException(400, reason)

    # Check 1/day limit (reads Firestore directly — no stale cache)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = _get_guess_map(req.clan_id, challenge_id).get(req.uid)
    if existing and existing.get("date") == today:
        raise HTTPException(400, "You've already submitted a guess today. Try again tomorrow!")

    # Calculate day number
    start = datetime.fromisoformat(ch["start_date"])
    day_number = max(1, (datetime.now(timezone.utc) - start).days + 1)

    _save_guess(req.clan_id, challenge_id, req.uid, {
        "guess_text": req.guess_text.strip(),
        "day_number": day_number,
        "date": today,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "guess_text": req.guess_text.strip(),
        "day_number": day_number,
        "message": "Your guess is on the board! Check back tomorrow to guess again.",
    }


# ---------------------------------------------------------------------------
# Internal: Daily score aggregation (called by Cloud Scheduler)
# ---------------------------------------------------------------------------


@router.post("/internal/aggregate-daily")
async def aggregate_daily_scores(
    x_internal_key: Optional[str] = Header(default=None, alias="X-Internal-Key"),
    api_key: Optional[str] = Query(default=None, deprecated=True,
                                   description="Deprecated — use X-Internal-Key header"),
):
    """Aggregate daily clan scores. Called by Cloud Scheduler at midnight IST.

    For each active clan:
    1. Collect member session scores from the last 24h
    2. Compute brain points (top-N), quiz weighted mean, brawn points
    3. Apply Full Squad bonus if all members practiced
    4. Update clan lifetime totals and XP
    5. Store daily score document
    """
    # Internal key check — compares against KIWIMATH_INTERNAL_API_KEY env var
    # (constant-time). Rejects if the env var is unset/empty. Prefer the
    # X-Internal-Key header; the api_key query param is a deprecated fallback.
    provided = x_internal_key or api_key or ""
    if not internal_key_matches(provided):
        raise HTTPException(403, "Invalid API key")

    results = []
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    active_challenge = _find_active_challenge()

    for clan_id, clan in _all_active_clans():
        member_uids = clan.get("member_uids", [])
        if not member_uids:
            continue

        # Per-member daily scores written by the practice pipeline
        # (clan_member_daily_scores collection; key "{clan_id}:{uid}:{date}").
        member_scores = {}
        active_count = 0
        for uid in member_uids:
            if _fs():
                score = _member_scores_store.get(f"{clan_id}:{uid}:{today}")
            else:
                score = _daily_scores.get(f"{clan_id}:{uid}:{today}")
            if score:
                member_scores[uid] = score
                active_count += 1

        if not member_scores:
            # No activity today — still record brawn for active members
            # In production, check last 48h activity
            continue

        daily_doc = new_daily_score_doc(member_scores, active_count)

        # Store daily score
        if _fs():
            _clan_fs.set_daily_scores(clan_id, today, daily_doc)
        else:
            _daily_scores[f"{clan_id}:{today}"] = daily_doc

        # Update clan lifetime totals. Cron runs once daily from a single
        # Cloud Scheduler job, so this read-modify-write is effectively
        # single-writer.
        clan["lifetime_brain_points"] = clan.get("lifetime_brain_points", 0) + daily_doc["brain_points"]
        clan["lifetime_brawn_points"] = clan.get("lifetime_brawn_points", 0) + daily_doc["brawn_points"]
        clan["lifetime_quiz_points"] = clan.get("lifetime_quiz_points", 0) + daily_doc["quiz_clan_score"]
        clan["clan_xp"] = clan.get("clan_xp", 0) + daily_doc["clan_xp_earned"]
        _update_clan(clan_id, {
            "lifetime_brain_points": clan["lifetime_brain_points"],
            "lifetime_brawn_points": clan["lifetime_brawn_points"],
            "lifetime_quiz_points": clan["lifetime_quiz_points"],
            "clan_xp": clan["clan_xp"],
        })

        # Update challenge progress if active
        if active_challenge:
            cid, _challenge = active_challenge
            progress = _get_progress(clan_id, cid)
            _update_progress(clan_id, cid, {
                "total_clan_points": progress.get("total_clan_points", 0) + daily_doc["daily_total"],
                "brain_points": progress.get("brain_points", 0) + daily_doc["brain_points"],
                "quiz_points": progress.get("quiz_points", 0) + daily_doc["quiz_clan_score"],
                "brawn_points": progress.get("brawn_points", 0) + daily_doc["brawn_points"],
            })

        results.append({
            "clan_id": clan_id,
            "clan_name": clan["name"],
            "daily_total": daily_doc["daily_total"],
            "brain": daily_doc["brain_points"],
            "quiz": daily_doc["quiz_clan_score"],
            "brawn": daily_doc["brawn_points"],
            "full_squad": daily_doc["full_squad"],
            "active_members": active_count,
        })

    return {
        "status": "ok",
        "date": today,
        "clans_processed": len(results),
        "results": results,
    }


# ---------------------------------------------------------------------------
# Seed a demo challenge (for testing)
# ---------------------------------------------------------------------------

def seed_demo_challenge():
    """Create 'The Star Map' demo challenge.

    - Firestore mode: only creates it if no active challenge exists, so
      redeploys never reset challenge dates.
    - Fallback mode (local/tests): seeds the in-memory store on import.
    """
    now = datetime.now(timezone.utc)
    doc = {
        "title": "The Star Map",
        "puzzle_type": "pattern_sequence",
        "difficulty_tier": "explorer",
        "image_url": "/static/puzzles/star_map_01.svg",
        "answer": "23",
        "grid_rows": 20,
        "grid_cols": 15,
        "points_per_block": 100,
        "duration_days": 10,
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=10)).isoformat(),
        "status": "active",
    }
    try:
        if _fs():
            if _clan_fs.find_active_challenge() is None:
                _clan_fs.create_challenge("challenge_star_map_01", doc)
        else:
            _challenges["challenge_star_map_01"] = doc
    except Exception:
        _challenges["challenge_star_map_01"] = doc


seed_demo_challenge()
