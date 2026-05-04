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
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

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
# In-memory stores (replace with Firestore in production)
# ---------------------------------------------------------------------------
_clans: Dict[str, Dict[str, Any]] = {}
_daily_scores: Dict[str, Dict[str, Dict[str, Any]]] = {}  # clan_id -> date -> scores
_challenges: Dict[str, Dict[str, Any]] = {}
_clan_challenge_progress: Dict[str, Dict[str, Dict[str, Any]]] = {}  # clan_id -> cid -> progress
_guesses: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {}  # clan_id -> cid -> uid -> guess
_reactions: Dict[str, List[Dict[str, Any]]] = {}  # clan_id -> [reactions]


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
    for cid, clan in _clans.items():
        if req.leader_uid in clan.get("member_uids", []) and clan["status"] == "active":
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
    _clans[clan_id] = doc

    return ClanResponse(
        clan_id=clan_id,
        name=doc["name"],
        grade=doc["grade"],
        crest=doc["crest"],
        leader_uid=doc["leader_uid"],
        member_count=len(doc["member_uids"]),
        status=doc["status"],
        lifetime_brain_points=0,
        lifetime_brawn_points=0,
        lifetime_quiz_points=0,
        clan_level=get_clan_level(0),
        invite_code=doc["invite_code"],
        invite_expires_at=doc["invite_expires_at"],
        member_uids=doc["member_uids"],
        created_at=doc["created_at"],
    )


@router.get("/clans/mine")
async def get_my_clan(user_uid: str = Query(...)):
    """Look up the clan a user belongs to. Returns 404 if not in any clan."""
    for cid, clan in _clans.items():
        if user_uid in clan.get("member_uids", []):
            member_count = len(clan.get("member_uids", []))
            clan_xp = clan.get("clan_xp", 0)
            lvl = get_clan_level(clan_xp)
            return ClanResponse(
                clan_id=cid,
                name=clan["name"],
                grade=clan["grade"],
                crest=clan["crest"],
                leader_uid=clan["leader_uid"],
                member_count=member_count,
                status=clan.get("status", "active"),
                lifetime_brain_points=clan.get("lifetime_brain_points", 0),
                lifetime_brawn_points=clan.get("lifetime_brawn_points", 0),
                lifetime_quiz_points=clan.get("lifetime_quiz_points", 0),
                clan_level=lvl,
                invite_code=clan.get("invite_code"),
                invite_expires_at=clan.get("invite_expires_at"),
                member_uids=clan.get("member_uids", []),
                created_at=clan.get("created_at", ""),
            )
    raise HTTPException(404, "You are not in any clan")


@router.get("/clans/{clan_id}", response_model=ClanResponse)
async def get_clan(clan_id: str, uid: Optional[str] = None):
    """Get clan details. Only members see invite code and member list."""
    clan = _clans.get(clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")

    is_member = uid in clan.get("member_uids", []) if uid else False

    return ClanResponse(
        clan_id=clan_id,
        name=clan["name"],
        grade=clan["grade"],
        crest=clan["crest"],
        leader_uid=clan["leader_uid"],
        member_count=len(clan["member_uids"]),
        status=clan["status"],
        lifetime_brain_points=clan.get("lifetime_brain_points", 0),
        lifetime_brawn_points=clan.get("lifetime_brawn_points", 0),
        lifetime_quiz_points=clan.get("lifetime_quiz_points", 0),
        clan_level=get_clan_level(clan.get("clan_xp", 0)),
        invite_code=clan.get("invite_code") if is_member else None,
        invite_expires_at=clan.get("invite_expires_at") if is_member else None,
        member_uids=clan["member_uids"] if is_member else [],
        created_at=clan.get("created_at", ""),
    )


@router.post("/clans/join", response_model=ClanResponse)
async def join_clan(req: JoinClanRequest):
    """Join a clan via invite code (parent-authorized)."""
    # Find clan by invite code
    target_clan_id = None
    target_clan = None
    for cid, clan in _clans.items():
        if clan.get("invite_code") == req.invite_code and clan["status"] == "active":
            target_clan_id = cid
            target_clan = clan
            break

    if not target_clan:
        raise HTTPException(404, "Invalid or expired invite code")

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
    for cid, clan in _clans.items():
        if cid != target_clan_id and req.uid in clan.get("member_uids", []) and clan["status"] == "active":
            raise HTTPException(400, "You are already in another clan. Leave it first.")

    # Join
    target_clan["member_uids"].append(req.uid)

    return ClanResponse(
        clan_id=target_clan_id,
        name=target_clan["name"],
        grade=target_clan["grade"],
        crest=target_clan["crest"],
        leader_uid=target_clan["leader_uid"],
        member_count=len(target_clan["member_uids"]),
        status=target_clan["status"],
        lifetime_brain_points=target_clan.get("lifetime_brain_points", 0),
        lifetime_brawn_points=target_clan.get("lifetime_brawn_points", 0),
        lifetime_quiz_points=target_clan.get("lifetime_quiz_points", 0),
        clan_level=get_clan_level(target_clan.get("clan_xp", 0)),
        invite_code=target_clan.get("invite_code"),
        invite_expires_at=target_clan.get("invite_expires_at"),
        member_uids=target_clan["member_uids"],
        created_at=target_clan.get("created_at", ""),
    )


@router.delete("/clans/{clan_id}/members/{uid}")
async def remove_member(clan_id: str, uid: str, requester_uid: str = Query(...)):
    """Remove a member (leader or self-removal). Gentle messaging — no 'kicked' language."""
    clan = _clans.get(clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")

    if uid not in clan["member_uids"]:
        raise HTTPException(400, "This person is not in the clan")

    # Only leader or self can remove
    if requester_uid != clan["leader_uid"] and requester_uid != uid:
        raise HTTPException(403, "Only the clan leader can remove members")

    clan["member_uids"].remove(uid)

    # If leader leaves, promote longest-tenured
    if uid == clan["leader_uid"] and clan["member_uids"]:
        clan["leader_uid"] = clan["member_uids"][0]

    # If empty, dissolve
    if not clan["member_uids"]:
        clan["status"] = "dissolved"

    return {"message": "This clan adventure has ended for this member", "remaining_members": len(clan["member_uids"])}


@router.post("/clans/{clan_id}/invite")
async def regenerate_invite(clan_id: str, uid: str = Query(...)):
    """Regenerate invite code (leader only)."""
    clan = _clans.get(clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")
    if uid != clan["leader_uid"]:
        raise HTTPException(403, "Only the clan leader can regenerate invite codes")

    new_code = generate_invite_code()
    clan["invite_code"] = new_code
    clan["invite_expires_at"] = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()

    return {"invite_code": new_code, "expires_at": clan["invite_expires_at"]}


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
        for cid, clan in _clans.items()
        if clan["grade"] == grade and clan["status"] == "active"
    ]

    sort_key = "lifetime_brain_points"
    if challenge_id:
        # Use challenge-specific points
        for clan in grade_clans:
            cid = clan["clan_id"]
            progress = (_clan_challenge_progress.get(cid, {}).get(challenge_id, {}))
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
    if clan_id not in _clans:
        raise HTTPException(404, "Clan not found")
    if req.emoji not in VALID_EMOJIS:
        raise HTTPException(400, f"Invalid emoji. Choose from: {VALID_EMOJIS}")

    clan = _clans[clan_id]
    if req.uid not in clan["member_uids"]:
        raise HTTPException(403, "You must be a clan member to react")

    if clan_id not in _reactions:
        _reactions[clan_id] = []

    _reactions[clan_id].append({
        "uid": req.uid,
        "emoji": req.emoji,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Keep only last 50 reactions
    _reactions[clan_id] = _reactions[clan_id][-50:]

    return {"status": "ok", "emoji": req.emoji}


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------

@router.get("/challenges/active")
async def get_active_challenge():
    """Get the current active Picture Unravel challenge."""
    now = datetime.now(timezone.utc)
    for cid, ch in _challenges.items():
        if ch["status"] == "active":
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
    ch = _challenges.get(challenge_id)
    if not ch:
        raise HTTPException(404, "Challenge not found")
    clan = _clans.get(clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")

    total_blocks = ch["grid_rows"] * ch["grid_cols"]
    progress = _clan_challenge_progress.get(clan_id, {}).get(challenge_id, {})

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
    ch = _challenges.get(challenge_id)
    if not ch:
        raise HTTPException(404, "Challenge not found")
    clan = _clans.get(req.clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")
    if req.uid != clan["leader_uid"]:
        raise HTTPException(403, "Only the clan leader can submit the official answer")

    total_blocks = ch["grid_rows"] * ch["grid_cols"]
    progress = _clan_challenge_progress.setdefault(req.clan_id, {}).setdefault(challenge_id, {})
    total_points = progress.get("total_clan_points", 0)
    blocks = compute_blocks_revealed(total_points, ch.get("points_per_block", 100), total_blocks)

    if not can_submit_answer(blocks, total_blocks):
        pct = round(blocks / max(1, total_blocks) * 100, 1)
        raise HTTPException(400, f"Submit unlocks at 30% revealed. Currently at {pct}%.")

    start = datetime.fromisoformat(ch["start_date"])
    day_number = max(1, (datetime.now(timezone.utc) - start).days + 1)
    pts = compute_answer_points(day_number, ch["duration_days"])

    progress["answer"] = req.answer.strip()
    progress["answer_day"] = day_number
    progress["answer_points"] = pts

    return {
        "answer": progress["answer"],
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
    clan_guesses = _guesses.get(clan_id, {}).get(challenge_id, {})

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
    ch = _challenges.get(challenge_id)
    if not ch:
        raise HTTPException(404, "Challenge not found")
    clan = _clans.get(req.clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")
    if req.uid not in clan["member_uids"]:
        raise HTTPException(403, "You must be a clan member to submit guesses")

    # Filter
    valid, reason = filter_guess_text(req.guess_text)
    if not valid:
        raise HTTPException(400, reason)

    # Check 1/day limit
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    clan_guesses = _guesses.setdefault(req.clan_id, {}).setdefault(challenge_id, {})

    existing = clan_guesses.get(req.uid)
    if existing and existing.get("date") == today:
        raise HTTPException(400, "You've already submitted a guess today. Try again tomorrow!")

    # Calculate day number
    start = datetime.fromisoformat(ch["start_date"])
    day_number = max(1, (datetime.now(timezone.utc) - start).days + 1)

    clan_guesses[req.uid] = {
        "guess_text": req.guess_text.strip(),
        "day_number": day_number,
        "date": today,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "guess_text": req.guess_text.strip(),
        "day_number": day_number,
        "message": "Your guess is on the board! Check back tomorrow to guess again.",
    }


# ---------------------------------------------------------------------------
# Internal: Daily score aggregation (called by Cloud Scheduler)
# ---------------------------------------------------------------------------


@router.post("/internal/aggregate-daily")
async def aggregate_daily_scores(api_key: str = Query(...)):
    """Aggregate daily clan scores. Called by Cloud Scheduler at midnight IST.

    For each active clan:
    1. Collect member session scores from the last 24h
    2. Compute brain points (top-N), quiz weighted mean, brawn points
    3. Apply Full Squad bonus if all members practiced
    4. Update clan lifetime totals and XP
    5. Store daily score document
    """
    # Simple API key check for internal endpoints
    if api_key != "kiwimath_internal_2026":
        raise HTTPException(403, "Invalid API key")

    results = []
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    for clan_id, clan in _clans.items():
        if clan.get("status") != "active":
            continue

        member_uids = clan.get("member_uids", [])
        if not member_uids:
            continue

        # Simulate member scores for now (in production, query from session data)
        # Each member's daily score would come from their practice sessions
        member_scores = {}
        active_count = 0
        for uid in member_uids:
            # Check if member has sessions today (simulated)
            # In production: query user_sessions collection for today's sessions
            score = _daily_scores.get(f"{clan_id}:{uid}:{today}", {})
            if score:
                member_scores[uid] = score
                active_count += 1

        if not member_scores:
            # No activity today — still record brawn for active members
            # In production, check last 48h activity
            continue

        daily_doc = new_daily_score_doc(member_scores, active_count)

        # Store daily score
        _daily_scores[f"{clan_id}:{today}"] = daily_doc

        # Update clan lifetime totals
        clan["lifetime_brain_points"] = clan.get("lifetime_brain_points", 0) + daily_doc["brain_points"]
        clan["lifetime_brawn_points"] = clan.get("lifetime_brawn_points", 0) + daily_doc["brawn_points"]
        clan["lifetime_quiz_points"] = clan.get("lifetime_quiz_points", 0) + daily_doc["quiz_clan_score"]
        clan["clan_xp"] = clan.get("clan_xp", 0) + daily_doc["clan_xp_earned"]

        # Update challenge progress if active
        for cid, challenge in _challenges.items():
            if challenge.get("status") == "active":
                progress = _clan_challenge_progress.setdefault(clan_id, {}).setdefault(cid, {
                    "total_clan_points": 0,
                    "brain_points": 0,
                    "quiz_points": 0,
                    "brawn_points": 0,
                })
                progress["total_clan_points"] += daily_doc["daily_total"]
                progress["brain_points"] += daily_doc["brain_points"]
                progress["quiz_points"] += daily_doc["quiz_clan_score"]
                progress["brawn_points"] += daily_doc["brawn_points"]

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
    """Create 'The Star Map' demo challenge."""
    now = datetime.now(timezone.utc)
    _challenges["challenge_star_map_01"] = {
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


seed_demo_challenge()
