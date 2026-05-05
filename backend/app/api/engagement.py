"""
Kiwimath Engagement API — v4 endpoints for Leagues, Clan Wars, and Rewards.

Endpoints (10):
    GET    /v4/leagues/status              → Player league status
    GET    /v4/leagues/leaderboard         → League tier leaderboard

    GET    /v4/clan-wars/current           → Current war for a clan
    POST   /v4/clan-wars/{war_id}/submit   → Submit puzzle answer in war
    GET    /v4/clan-wars/history           → Past war results

    GET    /v4/rewards/{uid}               → Full reward state
    POST   /v4/rewards/{uid}/open-mystery-box → Open effort-gated mystery box
    POST   /v4/rewards/{uid}/claim-daily   → Claim daily calendar reward

    POST   /v4/pledges/{uid}               → Create commitment pledge
    GET    /v4/pledges/clan/{clan_id}      → Active clan pledges

Game theory mechanics:
    - Nash equilibrium in clan wars (best-N scoring)
    - Loss aversion (streak, daily calendar skip penalty)
    - Variable ratio reinforcement (mystery box)
    - Social commitment (pledge visibility)
    - Endowed progress (sticker album starts 10% filled)
    - Goal gradient (contribution bar acceleration)
    - Fresh start (weekly leaderboard resets)
    - Comeback mechanic (underdog 1.5x boost)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.engagement_service import (
    DAILY_CALENDAR_REWARDS,
    ELO_DEFAULT,
    ELO_K_FACTOR,
    LEAGUE_TIERS,
    MYSTERY_BOX_EFFORT_THRESHOLD,
    PUZZLES_PER_WAR,
    STICKER_CATALOG,
    STICKERS_PER_GRADE,
    WAR_DURATION_HOURS,
    apply_season_reset,
    compute_comeback_boost,
    compute_contribution_display,
    compute_expected_score,
    compute_puzzle_points,
    compute_war_score,
    create_pledge,
    create_starter_album,
    find_war_opponent,
    generate_mystery_box_reward,
    get_age_tier,
    get_daily_calendar_grid,
    get_daily_calendar_reward,
    get_league_tier,
    get_season_info,
    pick_random_sticker,
    rank_players_in_league,
    update_elo,
)

router = APIRouter(prefix="/v4", tags=["engagement"])

# ---------------------------------------------------------------------------
# In-memory stores (replace with Firestore in production)
# ---------------------------------------------------------------------------
_league_players: Dict[str, Dict[str, Any]] = {}  # uid -> league data
_wars: Dict[str, Dict[str, Any]] = {}  # war_id -> war data
_war_submissions: Dict[str, Dict[str, Dict[str, Any]]] = {}  # war_id -> uid -> submissions
_war_history: Dict[str, List[str]] = {}  # clan_id -> [war_ids]
_rewards: Dict[str, Dict[str, Any]] = {}  # uid -> reward state
_pledges: Dict[str, Dict[str, Any]] = {}  # uid -> pledge data
_clan_elos: Dict[str, int] = {}  # clan_id -> ELO rating


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class LeagueStatusResponse(BaseModel):
    league: str
    league_points: int
    rank_in_league: int
    promotion_threshold: Optional[int] = None
    demotion_threshold: Optional[int] = None
    season_number: int
    season_ends_at: str
    trophies_earned: int


class LeaderboardPlayerEntry(BaseModel):
    rank: int
    uid: str
    league_points: int
    trophies_earned: int


class WarMemberScore(BaseModel):
    uid: str
    score: int
    submitted: bool


class ClanWarResponse(BaseModel):
    war_id: str
    status: str  # upcoming / active / completed
    opponent_clan: Dict[str, Any]
    our_score: int
    their_score: int
    puzzle_set: List[str]
    start_time: str
    end_time: str
    member_scores: List[WarMemberScore]
    comeback_boost: float


class WarSubmitRequest(BaseModel):
    uid: str
    clan_id: str
    puzzle_id: str
    answer: str = Field(..., max_length=120)
    time_taken: int = Field(..., ge=0, le=600)  # seconds, max 10 min


class WarSubmitResponse(BaseModel):
    correct: bool
    points: int
    clan_total: int
    opponent_total: int
    war_status: str


class WarHistoryEntry(BaseModel):
    war_id: str
    opponent_name: str
    our_score: int
    their_score: int
    result: str  # W / L / D
    ended_at: str


class RewardState(BaseModel):
    stickers_collected: List[Dict[str, Any]]
    sticker_album_progress: str
    mystery_boxes_available: int
    badges: List[Dict[str, Any]]
    daily_calendar: List[Dict[str, Any]]
    pledge: Optional[Dict[str, Any]] = None
    total_gems: int


class MysteryBoxRewardResponse(BaseModel):
    reward_type: str
    reward_data: Dict[str, Any]
    rarity: str


class DailyClaimResponse(BaseModel):
    day_number: int
    reward: Dict[str, Any]
    next_reward_preview: Optional[Dict[str, Any]] = None


class CreatePledgeRequest(BaseModel):
    target_puzzles: int = Field(..., ge=1, le=5)
    duration_days: int = Field(7, ge=1, le=30)


class PledgeResponse(BaseModel):
    uid: str
    target_puzzles_per_day: int
    duration_days: int
    start_date: str
    end_date: str
    days_completed: int
    current_streak: int
    active: bool


# ---------------------------------------------------------------------------
# Leagues
# ---------------------------------------------------------------------------

@router.get("/leagues/status", response_model=LeagueStatusResponse)
async def get_league_status(uid: str = Query(...)):
    """Get a player's current league status, tier, rank, and season info."""
    player = _league_players.get(uid)
    if not player:
        raise HTTPException(404, "Player not found in any league")

    points = player.get("league_points", 0)
    tier_info = get_league_tier(points)
    season = get_season_info()

    # Compute rank within league
    all_players = list(_league_players.values())
    league_ranked = rank_players_in_league(all_players, tier_info["league"])
    rank = 0
    for p in league_ranked:
        if p.get("uid") == uid:
            rank = p.get("rank_in_league", 0)
            break

    return LeagueStatusResponse(
        league=tier_info["league"],
        league_points=points,
        rank_in_league=rank,
        promotion_threshold=tier_info.get("promotion_threshold"),
        demotion_threshold=tier_info.get("demotion_threshold"),
        season_number=season["season_number"],
        season_ends_at=season["season_ends_at"],
        trophies_earned=player.get("trophies_earned", 0),
    )


@router.get("/leagues/leaderboard")
async def get_league_leaderboard(
    league: str = Query(...),
    limit: int = Query(20, le=50),
):
    """Get top players in a specific league tier."""
    valid_leagues = {t["name"] for t in LEAGUE_TIERS}
    if league not in valid_leagues:
        raise HTTPException(400, f"Invalid league. Choose from: {sorted(valid_leagues)}")

    all_players = list(_league_players.values())
    ranked = rank_players_in_league(all_players, league)[:limit]

    return [
        LeaderboardPlayerEntry(
            rank=p.get("rank_in_league", 0),
            uid=p.get("uid", ""),
            league_points=p.get("league_points", 0),
            trophies_earned=p.get("trophies_earned", 0),
        )
        for p in ranked
    ]


# ---------------------------------------------------------------------------
# Clan Wars
# ---------------------------------------------------------------------------

@router.get("/clan-wars/current", response_model=ClanWarResponse)
async def get_current_war(clan_id: str = Query(...)):
    """Get the current or most recent war for a clan."""
    # Find active or most recent war for this clan
    clan_wars = _war_history.get(clan_id, [])
    if not clan_wars:
        raise HTTPException(404, "No wars found for this clan")

    # Return the latest war
    war_id = clan_wars[-1]
    war = _wars.get(war_id)
    if not war:
        raise HTTPException(404, "War data not found")

    # Determine which side this clan is on
    is_clan_a = war["clan_a_id"] == clan_id
    our_score = war["clan_a_score"] if is_clan_a else war["clan_b_score"]
    their_score = war["clan_b_score"] if is_clan_a else war["clan_a_score"]
    opponent_id = war["clan_b_id"] if is_clan_a else war["clan_a_id"]

    # Build member scores
    submissions = _war_submissions.get(war_id, {})
    our_members = war["clan_a_members"] if is_clan_a else war["clan_b_members"]
    member_scores = []
    for uid in our_members:
        sub = submissions.get(uid, {})
        member_scores.append(WarMemberScore(
            uid=uid,
            score=sub.get("total_score", 0),
            submitted=bool(sub.get("puzzles_answered", [])),
        ))

    comeback = compute_comeback_boost(our_score, their_score)

    return ClanWarResponse(
        war_id=war_id,
        status=war["status"],
        opponent_clan={
            "clan_id": opponent_id,
            "name": war.get("clan_b_name" if is_clan_a else "clan_a_name", "Unknown"),
            "crest": war.get("clan_b_crest" if is_clan_a else "clan_a_crest", {}),
            "members": len(war["clan_b_members"] if is_clan_a else war["clan_a_members"]),
        },
        our_score=our_score,
        their_score=their_score,
        puzzle_set=war.get("puzzle_set", []),
        start_time=war.get("start_time", ""),
        end_time=war.get("end_time", ""),
        member_scores=member_scores,
        comeback_boost=comeback,
    )


@router.post("/clan-wars/{war_id}/submit", response_model=WarSubmitResponse)
async def submit_war_puzzle(war_id: str, req: WarSubmitRequest):
    """Submit a puzzle answer in a clan war.

    Scoring: best-N scores count (Nash equilibrium — all must contribute).
    Comeback: trailing by >20% triggers 1.5x multiplier.
    """
    war = _wars.get(war_id)
    if not war:
        raise HTTPException(404, "War not found")
    if war["status"] != "active":
        raise HTTPException(400, "This war is not currently active")

    # Check war hasn't expired
    end_time = datetime.fromisoformat(war["end_time"])
    if datetime.now(timezone.utc) > end_time:
        war["status"] = "completed"
        raise HTTPException(400, "This war has ended")

    # Verify player is in one of the clans
    is_clan_a = req.uid in war.get("clan_a_members", [])
    is_clan_b = req.uid in war.get("clan_b_members", [])
    if not is_clan_a and not is_clan_b:
        raise HTTPException(403, "You are not a participant in this war")

    # Verify puzzle is in the set
    if req.puzzle_id not in war.get("puzzle_set", []):
        raise HTTPException(400, "This puzzle is not part of this war")

    # Check if already answered this puzzle
    submissions = _war_submissions.setdefault(war_id, {})
    player_sub = submissions.setdefault(req.uid, {
        "total_score": 0,
        "puzzles_answered": [],
        "clan_id": req.clan_id,
    })
    if req.puzzle_id in player_sub.get("puzzles_answered", []):
        raise HTTPException(400, "You already answered this puzzle")

    # Determine scores for comeback calculation
    our_score = war["clan_a_score"] if is_clan_a else war["clan_b_score"]
    their_score = war["clan_b_score"] if is_clan_a else war["clan_a_score"]
    comeback = compute_comeback_boost(our_score, their_score)

    # Simple correctness check (in production, validate against puzzle answer DB)
    # For now: answer is "correct" if it matches puzzle_id hash (deterministic demo)
    expected = hashlib.md5(req.puzzle_id.encode()).hexdigest()[:6]
    correct = req.answer.strip().lower() == expected or req.answer.strip() == "correct"

    points = compute_puzzle_points(correct, req.time_taken, comeback)

    # Update player submission
    player_sub["puzzles_answered"].append(req.puzzle_id)
    player_sub["total_score"] += points

    # Recalculate clan total using best-N scoring
    clan_key = "clan_a" if is_clan_a else "clan_b"
    members = war[f"{clan_key}_members"]
    member_totals = []
    for uid in members:
        sub = submissions.get(uid, {})
        member_totals.append(sub.get("total_score", 0))

    clan_total = compute_war_score(member_totals, len(members))

    if is_clan_a:
        war["clan_a_score"] = clan_total
    else:
        war["clan_b_score"] = clan_total

    # Check if war is complete (all puzzles answered by all members or time up)
    new_our = war["clan_a_score"] if is_clan_a else war["clan_b_score"]
    new_their = war["clan_b_score"] if is_clan_a else war["clan_a_score"]

    return WarSubmitResponse(
        correct=correct,
        points=points,
        clan_total=new_our,
        opponent_total=new_their,
        war_status=war["status"],
    )


@router.get("/clan-wars/history")
async def get_war_history(
    clan_id: str = Query(...),
    limit: int = Query(10, le=50),
):
    """Get past war results with W/L/D record."""
    clan_wars = _war_history.get(clan_id, [])
    if not clan_wars:
        return {"clan_id": clan_id, "wars": [], "record": {"wins": 0, "losses": 0, "draws": 0}}

    history = []
    wins = losses = draws = 0

    for wid in reversed(clan_wars[:limit]):
        war = _wars.get(wid)
        if not war:
            continue

        is_clan_a = war["clan_a_id"] == clan_id
        our_score = war["clan_a_score"] if is_clan_a else war["clan_b_score"]
        their_score = war["clan_b_score"] if is_clan_a else war["clan_a_score"]
        opponent_name = war.get("clan_b_name" if is_clan_a else "clan_a_name", "Unknown")

        if our_score > their_score:
            result = "W"
            wins += 1
        elif our_score < their_score:
            result = "L"
            losses += 1
        else:
            result = "D"
            draws += 1

        history.append(WarHistoryEntry(
            war_id=wid,
            opponent_name=opponent_name,
            our_score=our_score,
            their_score=their_score,
            result=result,
            ended_at=war.get("end_time", ""),
        ))

    return {
        "clan_id": clan_id,
        "wars": [h.model_dump() for h in history],
        "record": {"wins": wins, "losses": losses, "draws": draws},
    }


# ---------------------------------------------------------------------------
# Rewards & Engagement
# ---------------------------------------------------------------------------

@router.get("/rewards/{uid}", response_model=RewardState)
async def get_rewards(uid: str):
    """Get full reward state for a player.

    Age-tiered: G1-2 gets sticker data, G3-4 gets mystery boxes, G5-6 gets badges.
    """
    reward = _rewards.get(uid)
    if not reward:
        raise HTTPException(404, "Reward data not found for this player")

    grade = reward.get("grade", 1)
    age_tier = get_age_tier(grade)

    # Build sticker data
    collected_ids = reward.get("stickers_collected", [])
    total_stickers = STICKERS_PER_GRADE
    stickers_data = []
    if age_tier == "stickers" or True:  # Always return stickers, highlight for G1-2
        grade_catalog = STICKER_CATALOG.get(grade, [])
        for s in grade_catalog:
            stickers_data.append({
                "id": s["id"],
                "name": s["name"],
                "theme": s["theme"],
                "rarity": s["rarity"],
                "collected": s["id"] in collected_ids,
            })

    album_progress = f"{len(collected_ids)}/{total_stickers}"

    # Mystery boxes (effort-gated)
    puzzles_today = reward.get("puzzles_completed_today", 0)
    mystery_boxes_available = reward.get("mystery_boxes_available", 0)
    if puzzles_today >= MYSTERY_BOX_EFFORT_THRESHOLD:
        mystery_boxes_available = max(mystery_boxes_available, 1)

    # Badges
    badges = reward.get("badges", [])

    # Daily calendar
    claimed_days = reward.get("claimed_days", [])
    cycle_start = reward.get("current_cycle_start", 0)
    calendar = get_daily_calendar_grid(claimed_days, cycle_start)

    # Pledge
    pledge = _pledges.get(uid)
    pledge_info = None
    if pledge and pledge.get("active"):
        pledge_info = {
            "target": pledge["target_puzzles_per_day"],
            "current": reward.get("puzzles_completed_today", 0),
            "active": True,
        }

    return RewardState(
        stickers_collected=stickers_data,
        sticker_album_progress=album_progress,
        mystery_boxes_available=mystery_boxes_available,
        badges=badges,
        daily_calendar=calendar,
        pledge=pledge_info,
        total_gems=reward.get("total_gems", 0),
    )


@router.post("/rewards/{uid}/open-mystery-box", response_model=MysteryBoxRewardResponse)
async def open_mystery_box(uid: str):
    """Open a mystery box.

    Requires 5 daily puzzles completed (effort-gated, NOT purchase-gated).
    Variable ratio reinforcement: 60% common, 25% rare, 10% epic, 5% legendary.
    """
    reward = _rewards.get(uid)
    if not reward:
        raise HTTPException(404, "Reward data not found for this player")

    puzzles_today = reward.get("puzzles_completed_today", 0)
    if puzzles_today < MYSTERY_BOX_EFFORT_THRESHOLD:
        raise HTTPException(
            400,
            f"Complete {MYSTERY_BOX_EFFORT_THRESHOLD} daily puzzles to earn a mystery box. "
            f"You've done {puzzles_today} so far today. Keep going!",
        )

    boxes = reward.get("mystery_boxes_available", 0)
    if boxes <= 0:
        # If they've met the threshold, they get one
        if puzzles_today >= MYSTERY_BOX_EFFORT_THRESHOLD:
            boxes = 1
        else:
            raise HTTPException(400, "No mystery boxes available")

    grade = reward.get("grade", 1)
    box_reward = generate_mystery_box_reward(grade)

    # Consume one box
    reward["mystery_boxes_available"] = max(0, boxes - 1)

    # If sticker, add to collection
    if box_reward["reward_type"] == "sticker":
        sticker_id = box_reward["reward_data"].get("sticker_id")
        if sticker_id and sticker_id not in reward.get("stickers_collected", []):
            reward.setdefault("stickers_collected", []).append(sticker_id)

    # If gems/XP, add to totals
    if box_reward["reward_type"] == "bonus_xp":
        reward["total_xp"] = reward.get("total_xp", 0) + box_reward["reward_data"].get("amount", 0)

    return MysteryBoxRewardResponse(
        reward_type=box_reward["reward_type"],
        reward_data=box_reward["reward_data"],
        rarity=box_reward["rarity"],
    )


@router.post("/rewards/{uid}/claim-daily", response_model=DailyClaimResponse)
async def claim_daily_reward(uid: str):
    """Claim today's daily calendar reward.

    7-day cycle: day1=10gems, day2=sticker, day3=25gems, day4=streak_freeze,
                 day5=50gems, day6=mystery_box, day7=100gems+rare_sticker.
    Loss aversion: missing a day skips that slot.
    """
    reward = _rewards.get(uid)
    if not reward:
        raise HTTPException(404, "Reward data not found for this player")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check if already claimed today
    last_claim_date = reward.get("last_claim_date")
    if last_claim_date == today:
        raise HTTPException(400, "You already claimed today's reward. Come back tomorrow!")

    # Calculate current day in cycle
    claim_count = reward.get("daily_claim_count", 0)
    day_number = (claim_count % 7) + 1

    # Check for streak break (loss aversion: missing a day skips that slot)
    if last_claim_date:
        last_dt = datetime.strptime(last_claim_date, "%Y-%m-%d")
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        days_gap = (today_dt - last_dt).days
        if days_gap > 1:
            # Skipped day(s) — advance the counter but don't give those rewards
            skipped = days_gap - 1
            claim_count += skipped
            day_number = (claim_count % 7) + 1

    day_reward = get_daily_calendar_reward(day_number)

    # Apply reward
    if "gems" in day_reward["reward_type"]:
        gems = day_reward["reward_data"].get("amount", 0) or day_reward["reward_data"].get("gems", 0)
        reward["total_gems"] = reward.get("total_gems", 0) + gems

    if "sticker" in day_reward["reward_type"]:
        grade = reward.get("grade", 1)
        rarity = "rare" if "rare" in str(day_reward["reward_data"].get("sticker", "")) else "common"
        sticker = pick_random_sticker(grade, rarity)
        if sticker and sticker["id"] not in reward.get("stickers_collected", []):
            reward.setdefault("stickers_collected", []).append(sticker["id"])

    if day_reward["reward_type"] == "mystery_box":
        reward["mystery_boxes_available"] = reward.get("mystery_boxes_available", 0) + 1

    if day_reward["reward_type"] == "streak_freeze":
        reward["streak_freezes"] = reward.get("streak_freezes", 0) + 1

    # Update claim tracking
    reward["last_claim_date"] = today
    reward["daily_claim_count"] = claim_count + 1
    claimed_days = reward.setdefault("claimed_days", [])
    claimed_days.append(reward["daily_claim_count"])

    # Next reward preview
    next_day = ((claim_count + 1) % 7) + 1
    next_reward = get_daily_calendar_reward(next_day)

    return DailyClaimResponse(
        day_number=day_number,
        reward=day_reward,
        next_reward_preview={"day": next_day, **next_reward},
    )


# ---------------------------------------------------------------------------
# Pledges
# ---------------------------------------------------------------------------

@router.post("/pledges/{uid}", response_model=PledgeResponse)
async def create_user_pledge(uid: str, req: CreatePledgeRequest):
    """Create a commitment pledge visible to clanmates.

    Social commitment device: public pledges increase follow-through by 65%.
    """
    # Check for existing active pledge
    existing = _pledges.get(uid)
    if existing and existing.get("active"):
        end_date = datetime.fromisoformat(existing["end_date"])
        if datetime.now(timezone.utc) < end_date:
            raise HTTPException(
                400,
                "You already have an active pledge. Complete it first or wait for it to expire.",
            )

    pledge = create_pledge(uid, req.target_puzzles, req.duration_days)
    _pledges[uid] = pledge

    return PledgeResponse(
        uid=uid,
        target_puzzles_per_day=pledge["target_puzzles_per_day"],
        duration_days=pledge["duration_days"],
        start_date=pledge["start_date"],
        end_date=pledge["end_date"],
        days_completed=0,
        current_streak=0,
        active=True,
    )


@router.get("/pledges/clan/{clan_id}")
async def get_clan_pledges(clan_id: str):
    """Get all active pledges for clan members.

    Social visibility: seeing clanmates' pledges creates positive peer pressure.
    """
    # We need the clan's member list — import from clans module's in-memory store
    from app.api.clans import _clans

    clan = _clans.get(clan_id)
    if not clan:
        raise HTTPException(404, "Clan not found")

    member_uids = clan.get("member_uids", [])
    now = datetime.now(timezone.utc)

    active_pledges = []
    for uid in member_uids:
        pledge = _pledges.get(uid)
        if not pledge or not pledge.get("active"):
            continue

        end_date = datetime.fromisoformat(pledge["end_date"])
        if now > end_date:
            pledge["active"] = False
            continue

        # Contribution progress with goal gradient
        progress = compute_contribution_display(
            pledge.get("days_completed", 0),
            pledge.get("duration_days", 7),
        )

        active_pledges.append({
            "uid": uid,
            "target_puzzles_per_day": pledge["target_puzzles_per_day"],
            "duration_days": pledge["duration_days"],
            "days_completed": pledge.get("days_completed", 0),
            "current_streak": pledge.get("current_streak", 0),
            "progress": progress,
            "start_date": pledge["start_date"],
            "end_date": pledge["end_date"],
        })

    return {"clan_id": clan_id, "pledges": active_pledges}


# ---------------------------------------------------------------------------
# Seed engagement data (for testing/demo)
# ---------------------------------------------------------------------------

def seed_engagement_data():
    """Initialize leagues, sticker catalog, demo wars, and reward states.

    Called on module load to populate in-memory stores with demo data.
    """
    now = datetime.now(timezone.utc)
    season = get_season_info()

    # --- Seed league players ---
    demo_players = [
        {"uid": "player_aarav",    "league_points": 16200, "trophies_earned": 24, "grade": 4},
        {"uid": "player_priya",    "league_points": 12500, "trophies_earned": 18, "grade": 4},
        {"uid": "player_rohan",    "league_points": 8700,  "trophies_earned": 14, "grade": 5},
        {"uid": "player_ananya",   "league_points": 5200,  "trophies_earned": 10, "grade": 3},
        {"uid": "player_arjun",    "league_points": 3800,  "trophies_earned": 8,  "grade": 5},
        {"uid": "player_diya",     "league_points": 2100,  "trophies_earned": 6,  "grade": 2},
        {"uid": "player_vivaan",   "league_points": 1200,  "trophies_earned": 4,  "grade": 1},
        {"uid": "player_ishaan",   "league_points": 750,   "trophies_earned": 3,  "grade": 3},
        {"uid": "player_saanvi",   "league_points": 320,   "trophies_earned": 1,  "grade": 2},
        {"uid": "player_kavya",    "league_points": 80,    "trophies_earned": 0,  "grade": 1},
    ]
    for p in demo_players:
        _league_players[p["uid"]] = p

    # --- Seed clan ELOs ---
    _clan_elos["clan_tigers"] = 1280
    _clan_elos["clan_rockets"] = 1240
    _clan_elos["clan_dolphins"] = 1150
    _clan_elos["clan_pandas"] = 1320

    # --- Seed a demo war ---
    war_id = "war_demo_001"
    _wars[war_id] = {
        "war_id": war_id,
        "status": "active",
        "clan_a_id": "clan_tigers",
        "clan_a_name": "Tiger Squad",
        "clan_a_crest": {"shape": "bolt", "color": "#FF6D00"},
        "clan_a_members": ["player_aarav", "player_priya", "player_ananya"],
        "clan_a_score": 0,
        "clan_b_id": "clan_rockets",
        "clan_b_name": "Rocket Racers",
        "clan_b_crest": {"shape": "rocket", "color": "#7C4DFF"},
        "clan_b_members": ["player_rohan", "player_arjun", "player_ishaan"],
        "clan_b_score": 0,
        "puzzle_set": [
            "puzzle_war_001",
            "puzzle_war_002",
            "puzzle_war_003",
            "puzzle_war_004",
            "puzzle_war_005",
        ],
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(hours=WAR_DURATION_HOURS)).isoformat(),
    }
    _war_history.setdefault("clan_tigers", []).append(war_id)
    _war_history.setdefault("clan_rockets", []).append(war_id)

    # Seed a completed war for history
    old_war_id = "war_demo_000"
    old_end = now - timedelta(days=3)
    _wars[old_war_id] = {
        "war_id": old_war_id,
        "status": "completed",
        "clan_a_id": "clan_tigers",
        "clan_a_name": "Tiger Squad",
        "clan_a_crest": {"shape": "bolt", "color": "#FF6D00"},
        "clan_a_members": ["player_aarav", "player_priya"],
        "clan_a_score": 450,
        "clan_b_id": "clan_dolphins",
        "clan_b_name": "Dolphin Divers",
        "clan_b_crest": {"shape": "dolphin", "color": "#00E5FF"},
        "clan_b_members": ["player_diya", "player_saanvi"],
        "clan_b_score": 380,
        "puzzle_set": [
            "puzzle_old_001",
            "puzzle_old_002",
            "puzzle_old_003",
            "puzzle_old_004",
            "puzzle_old_005",
        ],
        "start_time": (old_end - timedelta(hours=WAR_DURATION_HOURS)).isoformat(),
        "end_time": old_end.isoformat(),
    }
    _war_history.setdefault("clan_tigers", []).append(old_war_id)
    _war_history["clan_tigers"] = [old_war_id, war_id]  # Keep order
    _war_history.setdefault("clan_dolphins", []).append(old_war_id)

    # --- Seed reward states ---
    for p in demo_players:
        uid = p["uid"]
        grade = p["grade"]
        starter_stickers = create_starter_album(grade)

        _rewards[uid] = {
            "uid": uid,
            "grade": grade,
            "stickers_collected": starter_stickers,
            "mystery_boxes_available": 1 if p["league_points"] > 1000 else 0,
            "puzzles_completed_today": 3,
            "badges": [],
            "total_gems": p["league_points"] // 10,
            "total_xp": p["league_points"] * 2,
            "streak_freezes": 1,
            "claimed_days": [],
            "current_cycle_start": 0,
            "daily_claim_count": 0,
            "last_claim_date": None,
        }

    # Give top players some badges
    _rewards["player_aarav"]["badges"] = [
        {"id": "badge_legend", "name": "Legendary League", "earned_at": now.isoformat()},
        {"id": "badge_war_hero", "name": "War Hero (10 wins)", "earned_at": now.isoformat()},
        {"id": "badge_collector", "name": "Sticker Collector (50%)", "earned_at": now.isoformat()},
    ]
    _rewards["player_priya"]["badges"] = [
        {"id": "badge_diamond", "name": "Diamond League", "earned_at": now.isoformat()},
        {"id": "badge_streak_7", "name": "7-Day Streak", "earned_at": now.isoformat()},
    ]
    _rewards["player_rohan"]["badges"] = [
        {"id": "badge_diamond", "name": "Diamond League", "earned_at": now.isoformat()},
    ]

    # Give one player enough puzzles for mystery box
    _rewards["player_aarav"]["puzzles_completed_today"] = 6

    # Seed a pledge
    _pledges["player_aarav"] = create_pledge("player_aarav", 3, 7)
    _pledges["player_priya"] = create_pledge("player_priya", 2, 7)


# Import hashlib for war submission correctness check
import hashlib

seed_engagement_data()
