"""
Kiwimath Daily Puzzle API — v4 endpoints for daily puzzles, streaks, and leaderboard.

Endpoints (5):
    GET    /v4/daily-puzzle                        → Get today's puzzle for a grade
    POST   /v4/daily-puzzle/submit                 → Submit answer, get IPS score
    GET    /v4/streaks/{uid}                       → Get streak info + 30-day calendar
    POST   /v4/streaks/{uid}/freeze                → Use a streak freeze
    GET    /v4/daily-puzzle/leaderboard             → Top 20 by IPS for a period

Time window (daily):
    drops_at  → 4:00 PM IST = 10:30 UTC
    closes_at → 10:00 PM IST = 16:30 UTC

IPS scoring (max 1000):
    accuracy  50%  → 500 pts if correct
    speed     30%  → 300 pts max (under 30s = max, linear to 0 at 300s)
    streak    15%  → 150 pts max
    bonus      5%  →  50 pts (first attempt, early bird)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.daily_puzzle_service import (
    GRADE_BAND_STYLES,
    PUZZLE_TYPE_LABELS,
    compute_ips,
    compute_streak_after_submission,
    get_daily_puzzle,
    get_freeze_window_start,
    get_puzzle_time_window,
    get_streak_bonus_points,
    get_streak_tier,
    is_streak_alive,
)

router = APIRouter(prefix="/v4", tags=["daily-puzzle"])

# ---------------------------------------------------------------------------
# In-memory stores (replace with Firestore in production)
# ---------------------------------------------------------------------------
_submissions: Dict[str, Dict[str, Any]] = {}          # "{uid}:{puzzle_id}" -> submission
_streaks: Dict[str, Dict[str, Any]] = {}              # uid -> streak data
_leaderboard_scores: Dict[str, List[Dict[str, Any]]] = {}  # "{grade}:{date}" -> [scores]
_freeze_usage: Dict[str, Dict[str, Any]] = {}         # uid -> {"week_start": str, "used": bool}


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class SubmitAnswerRequest(BaseModel):
    uid: str
    puzzle_id: str
    answer: str = Field(..., max_length=200)
    time_taken_seconds: float = Field(..., ge=0, le=3600)


class PuzzleOption(BaseModel):
    label: str
    value: str


class DailyPuzzleResponse(BaseModel):
    puzzle_id: str
    title: str
    story_narrative: str
    puzzle_type: str
    puzzle_type_label: str
    difficulty: int
    grade: int
    question_text: str
    options: List[str]
    hint_1: str
    hint_2: str
    drops_at: str
    closes_at: str
    svg_template: str
    grade_band_style: str
    date: str


class SubmitAnswerResponse(BaseModel):
    correct: bool
    points_earned: int
    accuracy_pts: int
    speed_pts: int
    streak_pts: int
    bonus_pts: int
    streak_count: int
    streak_bonus: int
    total_score: int
    streak_tier: str
    message: str


class DayEntry(BaseModel):
    date: str
    completed: bool
    points: int


class StreakResponse(BaseModel):
    uid: str
    current_streak: int
    longest_streak: int
    streak_freeze_available: bool
    last_puzzle_date: Optional[str]
    daily_calendar: List[DayEntry]
    streak_tier: str
    total_points: int


class FreezeResponse(BaseModel):
    freeze_used: bool
    streak_preserved: bool
    next_freeze_available: str
    current_streak: int
    message: str


class LeaderboardEntry(BaseModel):
    rank: int
    uid: str
    display_name: str
    total_score: int
    puzzles_solved: int
    streak_count: int
    streak_tier: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today_str() -> str:
    """Get today's date string in YYYY-MM-DD (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _ensure_streak(uid: str) -> Dict[str, Any]:
    """Get or create streak record for a user."""
    if uid not in _streaks:
        _streaks[uid] = {
            "current_streak": 0,
            "longest_streak": 0,
            "last_puzzle_date": None,
            "total_points": 0,
            "daily_log": {},  # date -> {"completed": bool, "points": int}
            "display_name": f"Student_{uid[:6]}",
        }
    return _streaks[uid]


def _is_early_bird(date_str: str) -> bool:
    """Check if current time is within the first 30 minutes of puzzle window (early bird bonus)."""
    window = get_puzzle_time_window(date_str)
    now = datetime.now(timezone.utc)
    drops = datetime.fromisoformat(window["drops_at"])
    return drops <= now <= drops + timedelta(minutes=30)


# ---------------------------------------------------------------------------
# 1. GET /v4/daily-puzzle
# ---------------------------------------------------------------------------

@router.get("/daily-puzzle", response_model=DailyPuzzleResponse)
async def get_daily_puzzle_endpoint(
    grade: int = Query(..., ge=1, le=6, description="Student grade (1-6)"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (defaults to today)"),
):
    """Return today's puzzle for the requested grade.

    Each grade gets a different puzzle, deterministically selected from the
    30-puzzle pool using a hash of (date + grade). Puzzle drops at 4 PM IST
    (10:30 UTC) and closes at 10 PM IST (16:30 UTC).
    """
    date_str = date or _today_str()

    # Validate date format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")

    puzzle = get_daily_puzzle(grade, date_str)
    if not puzzle:
        raise HTTPException(404, f"No puzzle found for grade {grade}")

    window = get_puzzle_time_window(date_str)
    style = GRADE_BAND_STYLES.get(grade, "real_world")
    type_label = PUZZLE_TYPE_LABELS.get(puzzle["puzzle_type"], puzzle["puzzle_type"])

    return DailyPuzzleResponse(
        puzzle_id=puzzle["puzzle_id"],
        title=puzzle["title"],
        story_narrative=puzzle["story_narrative"],
        puzzle_type=puzzle["puzzle_type"],
        puzzle_type_label=type_label,
        difficulty=puzzle["difficulty"],
        grade=puzzle["grade"],
        question_text=puzzle["question_text"],
        options=puzzle["options"],
        hint_1=puzzle["hint_1"],
        hint_2=puzzle["hint_2"],
        drops_at=window["drops_at"],
        closes_at=window["closes_at"],
        svg_template=puzzle.get("svg_template", ""),
        grade_band_style=style,
        date=date_str,
    )


# ---------------------------------------------------------------------------
# 2. POST /v4/daily-puzzle/submit
# ---------------------------------------------------------------------------

@router.post("/daily-puzzle/submit", response_model=SubmitAnswerResponse)
async def submit_daily_puzzle(req: SubmitAnswerRequest):
    """Submit an answer for today's daily puzzle.

    Computes IPS score (accuracy + speed + streak + bonus = max 1000).
    Updates the student's streak and records the submission.
    """
    # Parse puzzle_id to extract date and grade
    parts = req.puzzle_id.split("_")
    if len(parts) < 4 or parts[0] != "dp":
        raise HTTPException(400, "Invalid puzzle_id format")

    puzzle_date = parts[1]
    try:
        puzzle_grade = int(parts[2])
    except ValueError:
        raise HTTPException(400, "Invalid puzzle_id format")

    # Check for duplicate submission
    submission_key = f"{req.uid}:{req.puzzle_id}"
    if submission_key in _submissions:
        existing = _submissions[submission_key]
        return SubmitAnswerResponse(
            correct=existing["correct"],
            points_earned=existing["points_earned"],
            accuracy_pts=existing["accuracy_pts"],
            speed_pts=existing["speed_pts"],
            streak_pts=existing["streak_pts"],
            bonus_pts=existing["bonus_pts"],
            streak_count=existing["streak_count"],
            streak_bonus=existing["streak_bonus"],
            total_score=existing["total_score"],
            streak_tier=existing["streak_tier"],
            message="You already submitted for this puzzle. Here are your results.",
        )

    # Get the puzzle to check answer
    puzzle = get_daily_puzzle(puzzle_grade, puzzle_date)
    if not puzzle:
        raise HTTPException(404, "Puzzle not found")

    if puzzle["puzzle_id"] != req.puzzle_id:
        raise HTTPException(400, "Puzzle ID mismatch")

    # Check correctness
    correct = req.answer.strip().lower() == puzzle["correct_answer"].strip().lower()

    # Get/update streak
    streak_data = _ensure_streak(req.uid)
    is_first_attempt = submission_key not in _submissions
    early_bird = _is_early_bird(puzzle_date)

    # Update streak if correct
    if correct:
        new_streak, new_longest, new_date = compute_streak_after_submission(
            current_streak=streak_data["current_streak"],
            longest_streak=streak_data["longest_streak"],
            last_puzzle_date=streak_data["last_puzzle_date"],
            submission_date=puzzle_date,
        )
        streak_data["current_streak"] = new_streak
        streak_data["longest_streak"] = new_longest
        streak_data["last_puzzle_date"] = new_date
    else:
        new_streak = streak_data["current_streak"]

    # Compute IPS
    ips = compute_ips(
        correct=correct,
        time_taken_seconds=req.time_taken_seconds,
        streak_count=new_streak,
        is_first_attempt=is_first_attempt,
        is_early_bird=early_bird,
    )

    streak_bonus = get_streak_bonus_points(new_streak) if correct else 0
    tier = get_streak_tier(new_streak)

    # Update total points and daily log
    streak_data["total_points"] = streak_data.get("total_points", 0) + ips["total"]
    streak_data["daily_log"][puzzle_date] = {
        "completed": True,
        "points": ips["total"],
    }

    # Record submission
    _submissions[submission_key] = {
        "uid": req.uid,
        "puzzle_id": req.puzzle_id,
        "answer": req.answer,
        "correct": correct,
        "time_taken_seconds": req.time_taken_seconds,
        "points_earned": ips["total"],
        "accuracy_pts": ips["accuracy_pts"],
        "speed_pts": ips["speed_pts"],
        "streak_pts": ips["streak_pts"],
        "bonus_pts": ips["bonus_pts"],
        "streak_count": new_streak,
        "streak_bonus": streak_bonus,
        "total_score": streak_data["total_points"],
        "streak_tier": tier,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    # Add to leaderboard
    lb_key = f"{puzzle_grade}:{puzzle_date}"
    if lb_key not in _leaderboard_scores:
        _leaderboard_scores[lb_key] = []

    # Update or insert leaderboard entry
    existing_entry = None
    for entry in _leaderboard_scores[lb_key]:
        if entry["uid"] == req.uid:
            existing_entry = entry
            break

    if existing_entry:
        existing_entry["score"] = ips["total"]
        existing_entry["streak_count"] = new_streak
    else:
        _leaderboard_scores[lb_key].append({
            "uid": req.uid,
            "display_name": streak_data.get("display_name", f"Student_{req.uid[:6]}"),
            "score": ips["total"],
            "grade": puzzle_grade,
            "date": puzzle_date,
            "streak_count": new_streak,
        })

    # Build message
    if correct:
        if ips["total"] >= 900:
            message = "Outstanding! Captain Kiwi is amazed by your skills!"
        elif ips["total"] >= 700:
            message = "Great job! Captain Kiwi gives you a high-five!"
        elif ips["total"] >= 500:
            message = "Well done! Keep practising with Captain Kiwi!"
        else:
            message = "Correct! Captain Kiwi is proud of you!"
    else:
        message = "Not quite right. Captain Kiwi says: review the hints and try tomorrow!"

    return SubmitAnswerResponse(
        correct=correct,
        points_earned=ips["total"],
        accuracy_pts=ips["accuracy_pts"],
        speed_pts=ips["speed_pts"],
        streak_pts=ips["streak_pts"],
        bonus_pts=ips["bonus_pts"],
        streak_count=new_streak,
        streak_bonus=streak_bonus,
        total_score=streak_data["total_points"],
        streak_tier=tier,
        message=message,
    )


# ---------------------------------------------------------------------------
# 3. GET /v4/streaks/{uid}
# ---------------------------------------------------------------------------

@router.get("/streaks/{uid}", response_model=StreakResponse)
async def get_streaks(uid: str):
    """Return streak info and 30-day activity calendar for a student.

    Includes current streak, longest streak, streak tier, freeze availability,
    and a calendar of the last 30 days showing completion and points.
    """
    streak_data = _ensure_streak(uid)
    today = _today_str()

    # Check if streak is still alive
    if streak_data["last_puzzle_date"] and not is_streak_alive(streak_data["last_puzzle_date"], today):
        # Check if a freeze was used
        freeze = _freeze_usage.get(uid, {})
        week_start = get_freeze_window_start(today)
        if not (freeze.get("week_start") == week_start and freeze.get("used_for_date")):
            # Streak is broken — reset
            streak_data["current_streak"] = 0

    current = streak_data["current_streak"]
    longest = streak_data["longest_streak"]
    tier = get_streak_tier(current)

    # Build 30-day calendar
    calendar: List[DayEntry] = []
    today_date = datetime.strptime(today, "%Y-%m-%d").date()
    for i in range(29, -1, -1):
        d = today_date - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        log = streak_data.get("daily_log", {}).get(d_str, {})
        calendar.append(DayEntry(
            date=d_str,
            completed=log.get("completed", False),
            points=log.get("points", 0),
        ))

    # Check freeze availability
    week_start = get_freeze_window_start(today)
    freeze_info = _freeze_usage.get(uid, {})
    freeze_available = not (freeze_info.get("week_start") == week_start and freeze_info.get("used"))

    return StreakResponse(
        uid=uid,
        current_streak=current,
        longest_streak=longest,
        streak_freeze_available=freeze_available,
        last_puzzle_date=streak_data["last_puzzle_date"],
        daily_calendar=calendar,
        streak_tier=tier,
        total_points=streak_data.get("total_points", 0),
    )


# ---------------------------------------------------------------------------
# 4. POST /v4/streaks/{uid}/freeze
# ---------------------------------------------------------------------------

@router.post("/streaks/{uid}/freeze", response_model=FreezeResponse)
async def use_streak_freeze(uid: str):
    """Use a streak freeze to preserve the current streak.

    Each student gets 1 free freeze per week (resets Monday 00:00 UTC).
    The freeze prevents streak reset for one missed day.
    """
    streak_data = _ensure_streak(uid)
    today = _today_str()
    week_start = get_freeze_window_start(today)

    # Check if freeze already used this week
    freeze_info = _freeze_usage.get(uid, {})
    if freeze_info.get("week_start") == week_start and freeze_info.get("used"):
        # Calculate next Monday
        today_date = datetime.strptime(today, "%Y-%m-%d").date()
        days_until_monday = (7 - today_date.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today_date + timedelta(days=days_until_monday)
        return FreezeResponse(
            freeze_used=False,
            streak_preserved=False,
            next_freeze_available=next_monday.strftime("%Y-%m-%d"),
            current_streak=streak_data["current_streak"],
            message="You already used your freeze this week. Next freeze available on Monday!",
        )

    # Check if there is a streak to preserve
    if streak_data["current_streak"] == 0:
        return FreezeResponse(
            freeze_used=False,
            streak_preserved=False,
            next_freeze_available=week_start,
            current_streak=0,
            message="No active streak to freeze. Start solving puzzles to build one!",
        )

    # Use the freeze
    _freeze_usage[uid] = {
        "week_start": week_start,
        "used": True,
        "used_for_date": today,
        "used_at": datetime.now(timezone.utc).isoformat(),
    }

    # Calculate next Monday
    today_date = datetime.strptime(today, "%Y-%m-%d").date()
    days_until_monday = (7 - today_date.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today_date + timedelta(days=days_until_monday)

    return FreezeResponse(
        freeze_used=True,
        streak_preserved=True,
        next_freeze_available=next_monday.strftime("%Y-%m-%d"),
        current_streak=streak_data["current_streak"],
        message=f"Streak freeze activated! Your {streak_data['current_streak']}-day streak is safe. Captain Kiwi has your back!",
    )


# ---------------------------------------------------------------------------
# 5. GET /v4/daily-puzzle/leaderboard
# ---------------------------------------------------------------------------

@router.get("/daily-puzzle/leaderboard")
async def get_leaderboard(
    grade: int = Query(..., ge=1, le=6, description="Student grade (1-6)"),
    period: str = Query("daily", description="Period: daily, weekly, or alltime"),
):
    """Get the top 20 students by IPS score for a grade and time period.

    Periods:
        daily   → today's scores only
        weekly  → sum of scores from the last 7 days
        alltime → total accumulated IPS points
    """
    if period not in ("daily", "weekly", "alltime"):
        raise HTTPException(400, "Period must be one of: daily, weekly, alltime")

    today = _today_str()
    today_date = datetime.strptime(today, "%Y-%m-%d").date()

    if period == "daily":
        # Single day leaderboard
        lb_key = f"{grade}:{today}"
        entries = _leaderboard_scores.get(lb_key, [])
        ranked = sorted(entries, key=lambda e: e.get("score", 0), reverse=True)[:20]
        return [
            LeaderboardEntry(
                rank=i + 1,
                uid=e["uid"],
                display_name=e.get("display_name", f"Student_{e['uid'][:6]}"),
                total_score=e["score"],
                puzzles_solved=1,
                streak_count=e.get("streak_count", 0),
                streak_tier=get_streak_tier(e.get("streak_count", 0)),
            )
            for i, e in enumerate(ranked)
        ]

    elif period == "weekly":
        # Aggregate last 7 days
        aggregated: Dict[str, Dict[str, Any]] = {}
        for day_offset in range(7):
            d = today_date - timedelta(days=day_offset)
            d_str = d.strftime("%Y-%m-%d")
            lb_key = f"{grade}:{d_str}"
            for entry in _leaderboard_scores.get(lb_key, []):
                uid = entry["uid"]
                if uid not in aggregated:
                    aggregated[uid] = {
                        "uid": uid,
                        "display_name": entry.get("display_name", f"Student_{uid[:6]}"),
                        "total_score": 0,
                        "puzzles_solved": 0,
                        "streak_count": entry.get("streak_count", 0),
                    }
                aggregated[uid]["total_score"] += entry.get("score", 0)
                aggregated[uid]["puzzles_solved"] += 1
                # Keep the highest streak count seen
                aggregated[uid]["streak_count"] = max(
                    aggregated[uid]["streak_count"],
                    entry.get("streak_count", 0),
                )

        ranked = sorted(aggregated.values(), key=lambda e: e["total_score"], reverse=True)[:20]
        return [
            LeaderboardEntry(
                rank=i + 1,
                uid=e["uid"],
                display_name=e["display_name"],
                total_score=e["total_score"],
                puzzles_solved=e["puzzles_solved"],
                streak_count=e["streak_count"],
                streak_tier=get_streak_tier(e["streak_count"]),
            )
            for i, e in enumerate(ranked)
        ]

    else:  # alltime
        # Use streak data for all-time totals
        all_students: List[Dict[str, Any]] = []
        for uid, sdata in _streaks.items():
            # Check if this student has scores for the requested grade
            has_grade_scores = False
            for key in _leaderboard_scores:
                if key.startswith(f"{grade}:"):
                    for entry in _leaderboard_scores[key]:
                        if entry["uid"] == uid:
                            has_grade_scores = True
                            break
                if has_grade_scores:
                    break

            if has_grade_scores:
                # Sum all scores for this grade
                total = 0
                puzzles = 0
                for key, entries in _leaderboard_scores.items():
                    if key.startswith(f"{grade}:"):
                        for entry in entries:
                            if entry["uid"] == uid:
                                total += entry.get("score", 0)
                                puzzles += 1

                all_students.append({
                    "uid": uid,
                    "display_name": sdata.get("display_name", f"Student_{uid[:6]}"),
                    "total_score": total,
                    "puzzles_solved": puzzles,
                    "streak_count": sdata.get("current_streak", 0),
                })

        ranked = sorted(all_students, key=lambda e: e["total_score"], reverse=True)[:20]
        return [
            LeaderboardEntry(
                rank=i + 1,
                uid=e["uid"],
                display_name=e["display_name"],
                total_score=e["total_score"],
                puzzles_solved=e["puzzles_solved"],
                streak_count=e["streak_count"],
                streak_tier=get_streak_tier(e["streak_count"]),
            )
            for i, e in enumerate(ranked)
        ]
