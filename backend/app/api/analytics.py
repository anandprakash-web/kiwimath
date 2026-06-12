"""
Kiwimath Admin Analytics API — Comprehensive analytics dashboard.

Endpoints (all admin-only):
    GET /admin/analytics/content      — Content quality dashboard
    GET /admin/analytics/engagement   — User engagement metrics
    GET /admin/analytics/learning     — Learning outcomes & mastery
    GET /admin/analytics/revenue      — Revenue, growth & economy
    GET /admin/analytics/overview     — Quick KPI summary
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.admin_store import admin_review_store, is_admin
from app.services.content_store_v2 import store_v2
from app.services.content_store_v4 import store_v4
from app.services.flag_store import flag_store
from app.services.gamification import gamification
from app.services.mistake_tracker import mistake_tracker
from app.services.ncert_content_store import ncert_store
from app.services.response_logger import response_logger
from app.services.singapore_content_store import singapore_store
from app.services.skill_ability_store import skill_ability_store
from app.services.spaced_review_engine import spaced_review_store
from app.services.uscc_content_store import uscc_store
from app.services.icse_content_store import icse_store
from app.api.paywall import _PREMIUM_USERS, _UNLOCK_STORE

logger = logging.getLogger("kiwimath.analytics")

router = APIRouter(tags=["Admin Analytics"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_admin(email: str) -> None:
    if not email or not is_admin(email):
        raise HTTPException(status_code=403, detail="Admin access required")


def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if denominator else default


def _all_questions() -> List[Any]:
    """Collect questions from all content stores."""
    qs: List[Any] = []
    try:
        qs.extend(store_v2.all_questions())
    except Exception:
        pass
    try:
        qs.extend(store_v4.all_questions())
    except Exception:
        pass
    return qs


def _all_questions_dicts() -> Dict[str, Dict[str, Any]]:
    """All question dicts from all stores keyed by ID."""
    merged: Dict[str, Dict[str, Any]] = {}
    for store_name, store_obj in [
        ("adaptive-v2", store_v2),
        ("adaptive-v4", store_v4),
        ("ncert", ncert_store),
        ("singapore", singapore_store),
        ("uscc", uscc_store),
        ("icse", icse_store),
    ]:
        try:
            if hasattr(store_obj, "_questions") and store_obj._questions:
                for qid, q in store_obj._questions.items():
                    merged[qid] = {"store": store_name, "question": q}
        except Exception:
            pass
    return merged


# ---------------------------------------------------------------------------
# 1. GET /admin/analytics/content
# ---------------------------------------------------------------------------

@router.get("/admin/analytics/content")
def analytics_content(email: str = Query(..., description="Admin email")):
    """Content quality dashboard."""
    _require_admin(email)

    all_qs = _all_questions()
    all_dicts = _all_questions_dicts()

    # Total questions
    total_questions = len(all_dicts)

    # By curriculum
    by_curriculum: Dict[str, int] = defaultdict(int)
    for info in all_dicts.values():
        by_curriculum[info["store"]] += 1

    # By grade
    by_grade: Dict[int, int] = defaultdict(int)
    for q in all_qs:
        grade = getattr(q, "school_grade", None)
        if grade is not None:
            by_grade[grade] += 1

    # By difficulty tier
    by_difficulty_tier: Dict[str, int] = defaultdict(int)
    for q in all_qs:
        tier = getattr(q, "difficulty_tier", "unknown")
        by_difficulty_tier[tier] += 1

    # Review stats
    try:
        review_stats_raw = admin_review_store.stats()
    except Exception:
        review_stats_raw = {}
    review_stats = {
        "approved": review_stats_raw.get("approved", 0),
        "flagged": review_stats_raw.get("flagged", 0),
        "pending": review_stats_raw.get("pending", 0),
    }

    # Flagged questions
    flagged_questions = len(flag_store._flags) if hasattr(flag_store, "_flags") else 0

    # Per-question accuracy from response_logger
    q_stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"attempts": 0, "correct": 0, "total_time": 0, "topic": ""}
    )
    for resp in response_logger._buffer:
        qid = resp.get("question_id", "")
        if not qid:
            continue
        q_stats[qid]["attempts"] += 1
        if resp.get("correct"):
            q_stats[qid]["correct"] += 1
        q_stats[qid]["total_time"] += resp.get("response_time_ms", 0)
        if not q_stats[qid]["topic"]:
            q_stats[qid]["topic"] = resp.get("skill_id", "")

    question_accuracy = []
    for qid, stats in q_stats.items():
        if stats["attempts"] > 0:
            question_accuracy.append({
                "question_id": qid,
                "attempts": stats["attempts"],
                "accuracy": round(_safe_div(stats["correct"], stats["attempts"]), 4),
                "avg_time_ms": round(_safe_div(stats["total_time"], stats["attempts"])),
                "topic": stats["topic"],
            })

    # Sort: top 20 hardest (lowest accuracy) + top 20 easiest (highest accuracy)
    sorted_by_acc = sorted(question_accuracy, key=lambda x: x["accuracy"])
    hardest_20 = sorted_by_acc[:20]
    easiest_20 = sorted_by_acc[-20:][::-1] if len(sorted_by_acc) > 20 else []
    combined_accuracy = hardest_20 + easiest_20

    # Interaction modes
    interaction_modes: Dict[str, int] = defaultdict(int)
    for q in all_qs:
        mode = getattr(q, "interaction_mode", "mcq")
        interaction_modes[mode] += 1

    # Missing content checks
    missing_hints = 0
    missing_solution_steps = 0
    missing_visuals = 0
    for q in all_qs:
        hint = getattr(q, "hint", None)
        if not hint:
            missing_hints += 1
        steps = getattr(q, "solution_steps", None)
        if not steps or len(steps) == 0:
            missing_solution_steps += 1
        svg = getattr(q, "visual_svg", None)
        if not svg:
            missing_visuals += 1

    return {
        "total_questions": total_questions,
        "by_curriculum": dict(by_curriculum),
        "by_grade": {int(k): v for k, v in sorted(by_grade.items())},
        "by_difficulty_tier": dict(by_difficulty_tier),
        "review_stats": review_stats,
        "flagged_questions": flagged_questions,
        "question_accuracy": combined_accuracy,
        "interaction_modes": dict(interaction_modes),
        "missing_hints": missing_hints,
        "missing_solution_steps": missing_solution_steps,
        "missing_visuals": missing_visuals,
    }


# ---------------------------------------------------------------------------
# 2. GET /admin/analytics/engagement
# ---------------------------------------------------------------------------

@router.get("/admin/analytics/engagement")
def analytics_engagement(
    email: str = Query(..., description="Admin email"),
    days: int = Query(30, ge=1, le=365, description="Lookback period in days"),
):
    """User engagement metrics."""
    _require_admin(email)

    states = gamification._cache
    total_users = len(states)

    now = datetime.now(timezone.utc)
    cutoff_ts = (now - timedelta(days=days)).timestamp() * 1000  # epoch_ms

    # Filter responses within period
    period_responses = [
        r for r in response_logger._buffer
        if r.get("epoch_ms", 0) >= cutoff_ts
    ]

    total_responses = len(response_logger._buffer)

    # Active users in period
    active_user_ids = set()
    for r in period_responses:
        uid = r.get("user_id", "")
        if uid:
            active_user_ids.add(uid)
    active_users_period = len(active_user_ids)

    # Total sessions across all users
    total_sessions = sum(s.sessions_completed for s in states.values())

    # Avg sessions per user
    avg_sessions_per_user = round(_safe_div(total_sessions, total_users), 2)

    # Avg accuracy
    total_attempts_all = sum(s.total_attempts for s in states.values())
    total_correct_all = sum(s.total_correct for s in states.values())
    avg_accuracy = round(_safe_div(total_correct_all, total_attempts_all), 4)

    # Streaks
    streaks = [s.streak_current for s in states.values()]
    avg_streak = round(_safe_div(sum(streaks), len(streaks)), 2) if streaks else 0.0

    # Streak distribution
    streak_dist = {"0": 0, "1-3": 0, "4-7": 0, "8-14": 0, "15+": 0}
    for s in streaks:
        if s == 0:
            streak_dist["0"] += 1
        elif s <= 3:
            streak_dist["1-3"] += 1
        elif s <= 7:
            streak_dist["4-7"] += 1
        elif s <= 14:
            streak_dist["8-14"] += 1
        else:
            streak_dist["15+"] += 1

    # Top 10 users by XP
    sorted_users = sorted(states.items(), key=lambda x: x[1].xp_total, reverse=True)[:10]
    top_users = []
    for uid, st in sorted_users:
        acc = round(_safe_div(st.total_correct, st.total_attempts), 4)
        top_users.append({
            "user_id": uid,
            "sessions": st.sessions_completed,
            "accuracy": acc,
            "streak": st.streak_current,
            "xp": st.xp_total,
        })

    # Grade distribution from responses
    grade_dist: Dict[int, int] = defaultdict(int)
    for r in response_logger._buffer:
        g = r.get("grade", 0)
        if g and g > 0:
            grade_dist[g] += 1

    # Daily activity (last `days` days)
    daily_activity: Dict[str, Dict[str, Any]] = {}
    for i in range(days):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_activity[d] = {"date": d, "responses": 0, "users": set()}

    for r in period_responses:
        epoch_ms = r.get("epoch_ms", 0)
        if epoch_ms:
            dt = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
            d = dt.strftime("%Y-%m-%d")
            if d in daily_activity:
                daily_activity[d]["responses"] += 1
                uid = r.get("user_id", "")
                if uid:
                    daily_activity[d]["users"].add(uid)

    daily_list = []
    for d in sorted(daily_activity.keys()):
        entry = daily_activity[d]
        daily_list.append({
            "date": entry["date"],
            "responses": entry["responses"],
            "users": len(entry["users"]) if isinstance(entry["users"], set) else entry["users"],
        })

    # Hints used total
    hints_used_total = sum(s.hints_used for s in states.values())

    # Avg response time
    all_times = [r.get("response_time_ms", 0) for r in response_logger._buffer if r.get("response_time_ms")]
    avg_response_time_ms = round(_safe_div(sum(all_times), len(all_times))) if all_times else 0

    return {
        "total_users": total_users,
        "active_users_period": active_users_period,
        "total_sessions": total_sessions,
        "total_responses": total_responses,
        "avg_sessions_per_user": avg_sessions_per_user,
        "avg_accuracy": avg_accuracy,
        "avg_streak": avg_streak,
        "streak_distribution": streak_dist,
        "top_users": top_users,
        "grade_distribution": {int(k): v for k, v in sorted(grade_dist.items())},
        "daily_activity": daily_list,
        "hints_used_total": hints_used_total,
        "avg_response_time_ms": avg_response_time_ms,
    }


# ---------------------------------------------------------------------------
# 3. GET /admin/analytics/learning
# ---------------------------------------------------------------------------

@router.get("/admin/analytics/learning")
def analytics_learning(
    email: str = Query(..., description="Admin email"),
    grade: Optional[int] = Query(None, description="Filter by grade"),
):
    """Learning outcomes and mastery stats."""
    _require_admin(email)

    # Skill ability data
    abilities = skill_ability_store._memory  # user_id -> {skill_id -> theta}

    # Optionally filter by grade using response_logger
    user_grades: Dict[str, int] = {}
    if grade is not None:
        for r in response_logger._buffer:
            uid = r.get("user_id", "")
            g = r.get("grade", 0)
            if uid and g:
                user_grades[uid] = g
        filtered_users = {uid for uid, g in user_grades.items() if g == grade}
    else:
        filtered_users = None  # No filter, use all

    # Aggregate skills
    skill_thetas: Dict[str, List[float]] = defaultdict(list)
    user_skill_counts: Dict[str, int] = defaultdict(int)  # user -> mastered skills count

    for uid, skills in abilities.items():
        if filtered_users is not None and uid not in filtered_users:
            continue
        mastered = 0
        for skill_id, theta in skills.items():
            skill_thetas[skill_id].append(theta)
            if theta >= 0.5:  # threshold for "mastered"
                mastered += 1
        user_skill_counts[uid] = mastered

    total_skills_tracked = len(skill_thetas)

    # Avg mastery rate: proportion of skill-user pairs where theta >= 0.5
    total_pairs = sum(len(thetas) for thetas in skill_thetas.values())
    mastered_pairs = sum(
        1 for thetas in skill_thetas.values() for t in thetas if t >= 0.5
    )
    avg_mastery_rate = round(_safe_div(mastered_pairs, total_pairs), 4)

    # Skills mastered distribution per user
    mastered_dist = {"0": 0, "1-3": 0, "4-7": 0, "8+": 0}
    for uid, count in user_skill_counts.items():
        if count == 0:
            mastered_dist["0"] += 1
        elif count <= 3:
            mastered_dist["1-3"] += 1
        elif count <= 7:
            mastered_dist["4-7"] += 1
        else:
            mastered_dist["8+"] += 1

    # Also count users with abilities but 0 mastered who weren't counted
    # (they are already counted above)

    # FSRS stats
    total_scheduled = 0
    due_now = 0
    stabilities: List[float] = []
    difficulties: List[float] = []
    recalls: List[float] = []

    for uid, skills in spaced_review_store._memory.items():
        if filtered_users is not None and uid not in filtered_users:
            continue
        for skill_id, schedule in skills.items():
            total_scheduled += 1
            if schedule.is_due:
                due_now += 1
            stabilities.append(schedule.stability)
            difficulties.append(schedule.difficulty)
            recalls.append(schedule.estimated_recall)

    fsrs_stats = {
        "total_scheduled_reviews": total_scheduled,
        "due_now": due_now,
        "avg_stability": round(_safe_div(sum(stabilities), len(stabilities)), 2) if stabilities else 0.0,
        "avg_difficulty": round(_safe_div(sum(difficulties), len(difficulties)), 2) if difficulties else 0.0,
        "avg_recall": round(_safe_div(sum(recalls), len(recalls)), 4) if recalls else 0.0,
    }

    # Skill gaps (weakest 10 skills by avg theta)
    skill_avgs = []
    for skill_id, thetas in skill_thetas.items():
        avg_t = _safe_div(sum(thetas), len(thetas))
        skill_avgs.append({
            "skill_id": skill_id,
            "avg_theta": round(avg_t, 4),
            "student_count": len(thetas),
        })

    sorted_skills = sorted(skill_avgs, key=lambda x: x["avg_theta"])
    skill_gaps = sorted_skills[:10]
    strongest_skills = sorted_skills[-10:][::-1] if len(sorted_skills) > 10 else []

    # Mistake patterns
    total_tracked = 0
    skill_mistake_counts: Dict[str, int] = defaultdict(int)
    for uid, logs in mistake_tracker._mistake_log.items():
        if filtered_users is not None and uid not in filtered_users:
            continue
        for record in logs:
            total_tracked += 1
            sid = getattr(record, "skill_id", "") or getattr(record, "topic", "")
            if sid:
                skill_mistake_counts[sid] += 1

    top_mistake_skills = sorted(
        skill_mistake_counts.items(), key=lambda x: x[1], reverse=True
    )[:10]

    mistake_patterns = {
        "total_tracked": total_tracked,
        "top_skills": [
            {"skill_id": sid, "mistake_count": cnt} for sid, cnt in top_mistake_skills
        ],
    }

    # Improvement funnel — estimate from gamification states
    states = gamification._cache
    started_diagnostic = 0
    completed_diagnostic = 0
    started_practice = 0
    reached_mastery = 0

    for uid, st in states.items():
        if filtered_users is not None and uid not in filtered_users:
            continue
        if st.total_attempts > 0:
            started_diagnostic += 1
        if st.sessions_completed >= 1:
            completed_diagnostic += 1
        if st.sessions_completed >= 3:
            started_practice += 1
        if st.topics_mastered_count >= 1:
            reached_mastery += 1

    return {
        "mastery_overview": {
            "total_skills_tracked": total_skills_tracked,
            "avg_mastery_rate": avg_mastery_rate,
            "skills_mastered_distribution": mastered_dist,
        },
        "fsrs_stats": fsrs_stats,
        "skill_gaps": skill_gaps,
        "strongest_skills": strongest_skills,
        "mistake_patterns": mistake_patterns,
        "improvement_funnel": {
            "started_diagnostic": started_diagnostic,
            "completed_diagnostic": completed_diagnostic,
            "started_practice": started_practice,
            "reached_mastery": reached_mastery,
        },
    }


# ---------------------------------------------------------------------------
# 4. GET /admin/analytics/revenue
# ---------------------------------------------------------------------------

@router.get("/admin/analytics/revenue")
def analytics_revenue(email: str = Query(..., description="Admin email")):
    """Revenue, premium, and virtual economy metrics."""
    _require_admin(email)

    states = gamification._cache
    total_signups = len(states)
    premium_users = len(_PREMIUM_USERS)
    premium_rate = round(_safe_div(premium_users, total_signups), 4)

    # Coin economy
    total_coins_in_circulation = sum(s.kiwi_coins for s in states.values())
    total_coins_earned = sum(s.lifetime_coins_earned for s in states.values())
    avg_coins_per_user = round(_safe_div(total_coins_in_circulation, total_signups), 2)

    # Gem economy
    total_gems = sum(s.gems for s in states.values())
    avg_gems_per_user = round(_safe_div(total_gems, total_signups), 2)

    # Topic unlocks
    topic_unlocks: Dict[str, int] = defaultdict(int)
    for uid, topics in _UNLOCK_STORE.items():
        for topic_id in topics:
            topic_unlocks[topic_id] += 1

    # Paywall funnel
    hit_paywall = 0
    unlocked_with_coins = 0
    for uid, topics in _UNLOCK_STORE.items():
        if topics:
            hit_paywall += 1
            unlocked_with_coins += 1  # They unlocked something with coins
    went_premium = premium_users

    # More nuanced: users who have any unlock OR are premium "hit" the paywall
    users_with_unlocks = set(_UNLOCK_STORE.keys())
    users_premium = set(_PREMIUM_USERS.keys())
    hit_paywall = len(users_with_unlocks | users_premium)

    return {
        "total_signups": total_signups,
        "premium_users": premium_users,
        "premium_rate": premium_rate,
        "coin_economy": {
            "total_coins_in_circulation": total_coins_in_circulation,
            "total_coins_earned": total_coins_earned,
            "avg_coins_per_user": avg_coins_per_user,
        },
        "gem_economy": {
            "total_gems": total_gems,
            "avg_gems_per_user": avg_gems_per_user,
        },
        "topic_unlocks": dict(topic_unlocks),
        "paywall_funnel": {
            "total_users": total_signups,
            "hit_paywall": hit_paywall,
            "unlocked_with_coins": len(users_with_unlocks),
            "went_premium": went_premium,
        },
    }


# ---------------------------------------------------------------------------
# 5. GET /admin/analytics/overview
# ---------------------------------------------------------------------------

@router.get("/admin/analytics/overview")
def analytics_overview(email: str = Query(..., description="Admin email")):
    """Quick KPI summary combining top-level metrics from all areas."""
    _require_admin(email)

    # Content KPIs
    all_dicts = _all_questions_dicts()
    total_questions = len(all_dicts)
    flagged = len(flag_store._flags) if hasattr(flag_store, "_flags") else 0

    # Engagement KPIs
    states = gamification._cache
    total_users = len(states)
    total_sessions = sum(s.sessions_completed for s in states.values())
    total_responses = len(response_logger._buffer)
    total_attempts = sum(s.total_attempts for s in states.values())
    total_correct = sum(s.total_correct for s in states.values())
    avg_accuracy = round(_safe_div(total_correct, total_attempts), 4)

    # Learning KPIs
    abilities = skill_ability_store._memory
    total_skills_tracked = len(
        set(sid for user_skills in abilities.values() for sid in user_skills.keys())
    )
    total_reviews_scheduled = sum(
        len(skills) for skills in spaced_review_store._memory.values()
    )

    # Revenue KPIs
    premium_users = len(_PREMIUM_USERS)
    premium_rate = round(_safe_div(premium_users, total_users), 4)
    total_coins = sum(s.kiwi_coins for s in states.values())

    return {
        "total_questions": total_questions,
        "flagged_questions": flagged,
        "total_users": total_users,
        "total_sessions": total_sessions,
        "total_responses": total_responses,
        "avg_accuracy": avg_accuracy,
        "total_skills_tracked": total_skills_tracked,
        "total_reviews_scheduled": total_reviews_scheduled,
        "premium_users": premium_users,
        "premium_rate": premium_rate,
        "total_coins_in_circulation": total_coins,
    }
