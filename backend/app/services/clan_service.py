"""
Kiwimath Clan Service — Core CRUD, invite codes, membership management.

Firestore collections:
    clans/{clan_id}                         → clan document
    clans/{clan_id}/daily_scores/{date}     → daily aggregated scores
    clans/{clan_id}/challenges/{cid}        → per-challenge clan progress
    clans/{clan_id}/challenges/{cid}/guesses/{uid} → member guesses
    challenges/{challenge_id}               → global challenge definitions

Safety:
    - Parent must approve create + join
    - Name filtered (profanity + PII regex)
    - Max 15 members per clan
    - Grade-locked membership
    - No PII in clan data (UID references only)
"""

from __future__ import annotations

import hashlib
import logging
import random
import re
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kiwimath.clans")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CLAN_SIZE = 15
MIN_ACTIVE_MEMBERS = 2
INVITE_CODE_LENGTH = 6
INVITE_EXPIRY_HOURS = 48
HIBERNATION_DAYS = 14
MAX_CLANS_PER_PARENT_MONTH = 3

CLAN_LEVELS = [
    {"level": 1, "name": "Seedling",      "emoji": "\U0001f331", "xp_min": 0,     "xp_max": 4999},
    {"level": 2, "name": "Sapling",       "emoji": "\U0001f33f", "xp_min": 5000,  "xp_max": 14999},
    {"level": 3, "name": "Tree",          "emoji": "\U0001f333", "xp_min": 15000, "xp_max": 39999},
    {"level": 4, "name": "Forest",        "emoji": "\U0001f332", "xp_min": 40000, "xp_max": 99999},
    {"level": 5, "name": "Ancient Grove", "emoji": "\U0001f3d4️", "xp_min": 100000, "xp_max": 999999999},
]

CREST_SHAPES = ["bolt", "lion", "wave", "rocket", "blossom", "dolphin"]
CREST_COLORS = ["#FF6D00", "#7C4DFF", "#448AFF", "#FF4081", "#00E5FF", "#76FF03", "#FFD600", "#FF8A65"]

# Simple profanity filter — expand as needed
_PROFANITY_WORDS = {
    "damn", "hell", "crap", "stupid", "idiot", "dumb", "hate", "kill",
    "die", "ugly", "fat", "loser", "suck", "butt", "poop", "fart",
}
_PII_PATTERN = re.compile(
    r"(\b\d{10,}\b"         # phone numbers
    r"|\b\S+@\S+\.\S+\b"   # emails
    r"|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"  # US phone
    r")",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Name filtering
# ---------------------------------------------------------------------------

def filter_clan_name(name: str) -> tuple[bool, str]:
    """Validate and filter a clan name. Returns (is_valid, reason)."""
    name = name.strip()
    if not name:
        return False, "Clan name cannot be empty"
    if len(name) > 20:
        return False, "Clan name must be 20 characters or less"
    if len(name) < 3:
        return False, "Clan name must be at least 3 characters"
    if not re.match(r"^[a-zA-Z0-9 ]+$", name):
        return False, "Clan name can only contain letters, numbers, and spaces"
    lower = name.lower()
    for word in _PROFANITY_WORDS:
        if word in lower:
            return False, "Clan name contains inappropriate language"
    if _PII_PATTERN.search(name):
        return False, "Clan name cannot contain personal information"
    return True, "OK"


def filter_guess_text(text: str) -> tuple[bool, str]:
    """Validate and filter a guess board submission."""
    text = text.strip()
    if not text:
        return False, "Guess cannot be empty"
    if len(text) > 60:
        return False, "Guess must be 60 characters or less"
    lower = text.lower()
    for word in _PROFANITY_WORDS:
        if word in lower:
            return False, "Guess contains inappropriate language"
    if _PII_PATTERN.search(text):
        return False, "Guess cannot contain personal information"
    return True, "OK"


# ---------------------------------------------------------------------------
# Invite code generation
# ---------------------------------------------------------------------------

def generate_invite_code() -> str:
    """Generate a 6-character alphanumeric invite code like 'KIWI-7X3F'."""
    chars = string.ascii_uppercase + string.digits
    # Remove confusable characters
    chars = chars.replace("O", "").replace("0", "").replace("I", "").replace("1", "").replace("L", "")
    suffix = "".join(random.choices(chars, k=4))
    return f"KIWI-{suffix}"


# ---------------------------------------------------------------------------
# Clan level calculation
# ---------------------------------------------------------------------------

def get_clan_level(clan_xp: int) -> Dict[str, Any]:
    """Get current clan level info from total XP."""
    for lvl in reversed(CLAN_LEVELS):
        if clan_xp >= lvl["xp_min"]:
            progress = (clan_xp - lvl["xp_min"]) / max(1, lvl["xp_max"] - lvl["xp_min"] + 1)
            return {
                **lvl,
                "current_xp": clan_xp,
                "progress": min(1.0, progress),
                "xp_to_next": max(0, lvl["xp_max"] + 1 - clan_xp) if lvl["level"] < 5 else 0,
            }
    return {**CLAN_LEVELS[0], "current_xp": clan_xp, "progress": 0.0, "xp_to_next": 5000}


# ---------------------------------------------------------------------------
# Clan data structures
# ---------------------------------------------------------------------------

def new_clan_doc(
    name: str,
    grade: int,
    leader_uid: str,
    crest_shape: str = "bolt",
    crest_color: str = "#FF6D00",
) -> Dict[str, Any]:
    """Create a new clan Firestore document."""
    now = datetime.now(timezone.utc)
    invite_code = generate_invite_code()
    return {
        "name": name,
        "grade": grade,
        "crest": {"shape": crest_shape, "color": crest_color},
        "leader_uid": leader_uid,
        "member_uids": [leader_uid],
        "created_at": now.isoformat(),
        "status": "active",
        "lifetime_brain_points": 0,
        "lifetime_brawn_points": 0,
        "lifetime_quiz_points": 0,
        "clan_xp": 0,
        "invite_code": invite_code,
        "invite_expires_at": (now + timedelta(hours=INVITE_EXPIRY_HOURS)).isoformat(),
    }


def new_daily_score_doc(
    member_scores: Dict[str, Dict[str, Any]],
    active_member_count: int,
) -> Dict[str, Any]:
    """Create a daily score document after aggregation."""
    # Brain points: top-N scores
    scores = sorted(
        [s.get("score", 0) for s in member_scores.values()],
        reverse=True,
    )
    n = min(len(scores), 10)
    brain_points = sum(scores[:n])

    # Quiz weighted mean
    quiz_entries = [
        (s.get("quiz_score", 0), s.get("quiz_weight", 1.0))
        for s in member_scores.values()
        if s.get("quiz_score") is not None
    ]
    if quiz_entries:
        total_weight = sum(w for _, w in quiz_entries)
        quiz_weighted_mean = (
            sum(s * w for s, w in quiz_entries) / max(total_weight, 0.001)
        )
    else:
        quiz_weighted_mean = 0.0

    quiz_clan_score = int(quiz_weighted_mean * active_member_count * 10)
    full_squad = active_member_count >= len(member_scores) and active_member_count >= MIN_ACTIVE_MEMBERS
    if full_squad:
        brain_points *= 2  # Full Squad 2× bonus

    # Brawn points (active members only)
    brawn_points = 50 * active_member_count

    daily_total = brain_points + quiz_clan_score
    clan_xp_earned = sum(s.get("score", 0) for s in member_scores.values())  # ALL members

    return {
        "member_scores": member_scores,
        "brain_points": brain_points,
        "quiz_weighted_mean": round(quiz_weighted_mean, 2),
        "quiz_clan_score": quiz_clan_score,
        "brawn_points": brawn_points,
        "clan_xp_earned": clan_xp_earned,
        "full_squad": full_squad,
        "active_member_count": active_member_count,
        "daily_total": daily_total,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Challenge progress
# ---------------------------------------------------------------------------

def compute_blocks_revealed(
    total_clan_points: int,
    points_per_block: int,
    total_blocks: int,
) -> int:
    """How many blocks of the puzzle are revealed."""
    return min(total_blocks, total_clan_points // max(1, points_per_block))


def compute_answer_points(day_number: int, duration_days: int = 7) -> int:
    """Points available for correct answer on a given day. Decreases over time."""
    if day_number < 1:
        return 0
    base = 5000
    decrement = int(3000 / max(1, duration_days - 1))  # spread 3000 over the duration
    return max(500, base - (day_number - 1) * decrement)


def can_submit_answer(blocks_revealed: int, total_blocks: int) -> bool:
    """Submit is locked until ≥30% revealed."""
    return (blocks_revealed / max(1, total_blocks)) >= 0.30


# ---------------------------------------------------------------------------
# Pixel reveal order (deterministic, same for all clans)
# ---------------------------------------------------------------------------

def generate_block_order(total_blocks: int, challenge_seed: str) -> List[int]:
    """Generate a deterministic shuffled reveal order from a challenge seed.

    Same seed → same order for all clans (fair).
    """
    seed_int = int(hashlib.sha256(challenge_seed.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed_int)
    order = list(range(total_blocks))
    rng.shuffle(order)
    return order


# ---------------------------------------------------------------------------
# Leaderboard helpers
# ---------------------------------------------------------------------------

def rank_clans(clans: List[Dict[str, Any]], sort_key: str = "lifetime_brain_points") -> List[Dict[str, Any]]:
    """Rank clans by a score field, add rank number."""
    sorted_clans = sorted(clans, key=lambda c: c.get(sort_key, 0), reverse=True)
    for i, clan in enumerate(sorted_clans):
        clan["rank"] = i + 1
    return sorted_clans


logger.info("Clan service loaded — max %d members, %d-char invite codes", MAX_CLAN_SIZE, INVITE_CODE_LENGTH)
