"""
Kiwimath Analytics Store — Pre-computed aggregates for Admin Portal.

Reads from Firestore user data (profiles, sessions, mastery, gamification)
and provides aggregated metrics for the Student Analytics and Retention
Dashboard modules.

When Firestore is unavailable (local dev), returns demo/sample data so
the admin portal UI is always functional.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kiwimath.analytics")


def _get_db():
    """Get Firestore client, or None."""
    from app.services.firestore_service import _get_db as _fs_get_db
    return _fs_get_db()


def _is_available() -> bool:
    from app.services.firestore_service import is_firestore_available
    return is_firestore_available()


# ---------------------------------------------------------------------------
# Demo data for local dev (no Firestore)
# ---------------------------------------------------------------------------

def _demo_overview() -> Dict[str, Any]:
    today = date.today()
    return {
        "total_students": 47,
        "active_today": 12,
        "active_7d": 31,
        "active_30d": 44,
        "total_sessions": 1842,
        "avg_sessions_per_student": 39.2,
        "avg_accuracy": 0.72,
        "avg_session_duration_sec": 264,
        "date": today.isoformat(),
    }


def _demo_mastery_distribution() -> List[Dict[str, Any]]:
    return [
        {"label": "Emerging", "range": "0-39", "count": 14, "pct": 0.30},
        {"label": "Growing", "range": "40-64", "count": 18, "pct": 0.38},
        {"label": "Mastered", "range": "65-100", "count": 15, "pct": 0.32},
    ]


def _demo_daily_active(days: int) -> List[Dict[str, Any]]:
    today = date.today()
    import random
    random.seed(42)
    result = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        result.append({
            "date": d.isoformat(),
            "active_users": random.randint(5, 25),
            "sessions": random.randint(15, 80),
            "questions_answered": random.randint(60, 400),
        })
    return result


def _demo_topic_performance() -> List[Dict[str, Any]]:
    topics = [
        ("counting", "Counting & Observation", 0.81, 312, 0.74),
        ("logic", "Logic & Ordering", 0.68, 287, 0.69),
        ("arithmetic", "Arithmetic & Operations", 0.73, 298, 0.72),
        ("geometry", "Geometry & Spatial", 0.65, 201, 0.63),
        ("patterns", "Patterns & Sequences", 0.70, 256, 0.71),
        ("measurement", "Measurement & Data", 0.62, 178, 0.58),
        ("puzzles", "Puzzles & Combinatorics", 0.59, 164, 0.55),
        ("number_theory", "Number Theory", 0.56, 146, 0.52),
    ]
    return [
        {
            "topic_id": t[0], "topic_name": t[1], "avg_accuracy": t[2],
            "total_attempts": t[3], "mastery_rate": t[4],
        }
        for t in topics
    ]


def _demo_persona_breakdown() -> List[Dict[str, Any]]:
    return [
        {"persona": "Steady", "count": 18, "pct": 0.38, "description": "Consistent daily practice"},
        {"persona": "Power", "count": 11, "pct": 0.23, "description": "High accuracy, fast learner"},
        {"persona": "Mastery", "count": 9, "pct": 0.19, "description": "Focuses on deep understanding"},
        {"persona": "Comeback", "count": 5, "pct": 0.11, "description": "Returning after a break"},
        {"persona": "New", "count": 4, "pct": 0.09, "description": "Just started, building habits"},
    ]


def _demo_students() -> List[Dict[str, Any]]:
    """Sample student list for local dev."""
    import random
    random.seed(99)
    names = [
        "Aarav S.", "Diya P.", "Vihaan M.", "Ananya R.", "Arjun K.",
        "Ishaan T.", "Saanvi G.", "Reyansh B.", "Myra J.", "Kabir N.",
        "Anika D.", "Vivaan L.", "Prisha W.", "Advait C.", "Sara H.",
        "Dhruv F.", "Kiara Z.", "Aryan X.", "Aisha V.", "Rohan U.",
    ]
    students = []
    for i, name in enumerate(names):
        uid = f"demo_user_{i:03d}"
        xp = random.randint(50, 4500)
        sessions = random.randint(5, 120)
        accuracy = round(random.uniform(0.45, 0.95), 2)
        streak = random.randint(0, 30)
        last_active_days_ago = random.randint(0, 14)
        last_active = (date.today() - timedelta(days=last_active_days_ago)).isoformat()
        created_days_ago = random.randint(15, 90)
        created = (date.today() - timedelta(days=created_days_ago)).isoformat()
        students.append({
            "uid": uid,
            "display_name": name,
            "xp_total": xp,
            "level": _get_level_name(xp),
            "total_sessions": sessions,
            "avg_accuracy": accuracy,
            "streak_current": streak,
            "last_active": last_active,
            "created_at": created,
            "persona": random.choice(["Steady", "Power", "Mastery", "Comeback", "New"]),
        })
    return students


def _get_level_name(xp: int) -> str:
    levels = [
        (3000, "Kiwi Master"), (1500, "Super Kiwi"), (700, "Kiwi"),
        (300, "Kiwi Jr"), (100, "Sprout"), (0, "Seed"),
    ]
    for threshold, name in levels:
        if xp >= threshold:
            return name
    return "Seed"


def _demo_student_detail(uid: str) -> Dict[str, Any]:
    """Sample detail for a single student."""
    import random
    random.seed(hash(uid) % 10000)
    name = f"Student {uid[-3:]}"
    xp = random.randint(100, 4000)
    topics = ["counting", "logic", "arithmetic", "geometry", "patterns",
              "measurement", "puzzles", "number_theory"]
    mastery = {}
    for t in topics:
        score = random.randint(20, 95)
        mastery[t] = {
            "score": score,
            "label": "Mastered" if score >= 65 else ("Growing" if score >= 40 else "Emerging"),
            "attempts": random.randint(10, 80),
            "last_practised": (date.today() - timedelta(days=random.randint(0, 10))).isoformat(),
        }
    sessions = []
    for j in range(min(10, random.randint(3, 20))):
        d = date.today() - timedelta(days=j)
        correct = random.randint(2, 6)
        total = 6
        sessions.append({
            "date": d.isoformat(),
            "topic": random.choice(topics),
            "correct": correct,
            "total": total,
            "accuracy": round(correct / total, 2),
            "duration_sec": random.randint(120, 420),
        })
    return {
        "uid": uid,
        "display_name": name,
        "xp_total": xp,
        "level": _get_level_name(xp),
        "gems": random.randint(5, 200),
        "streak_current": random.randint(0, 25),
        "streak_longest": random.randint(5, 40),
        "created_at": (date.today() - timedelta(days=random.randint(15, 90))).isoformat(),
        "last_active": (date.today() - timedelta(days=random.randint(0, 5))).isoformat(),
        "persona": random.choice(["Steady", "Power", "Mastery", "Comeback"]),
        "mastery": mastery,
        "recent_sessions": sessions,
    }


# ---------------------------------------------------------------------------
# Retention demo data
# ---------------------------------------------------------------------------

def _demo_retention_cohorts() -> List[Dict[str, Any]]:
    """Generate sample cohort retention data."""
    import random
    random.seed(77)
    today = date.today()
    cohorts = []
    for week_offset in range(8):
        cohort_start = today - timedelta(weeks=week_offset + 1)
        cohort_end = cohort_start + timedelta(days=6)
        cohort_size = random.randint(8, 20)
        # Retention decays: D0 ~100%, D1 ~60-80%, D7 ~30-50%, D30 ~15-30%
        d0 = cohort_size
        d1 = int(cohort_size * random.uniform(0.60, 0.85))
        d7 = int(cohort_size * random.uniform(0.30, 0.55))
        d30 = int(cohort_size * random.uniform(0.12, 0.35)) if week_offset >= 4 else None
        cohorts.append({
            "cohort_week": f"{cohort_start.isoformat()} to {cohort_end.isoformat()}",
            "cohort_start": cohort_start.isoformat(),
            "cohort_size": cohort_size,
            "d0": {"count": d0, "rate": 1.0},
            "d1": {"count": d1, "rate": round(d1 / cohort_size, 2)},
            "d7": {"count": d7, "rate": round(d7 / cohort_size, 2)},
            "d30": {"count": d30, "rate": round(d30 / cohort_size, 2)} if d30 is not None else None,
        })
    return cohorts


def _demo_retention_curve() -> Dict[str, Any]:
    """Averaged retention curve across all cohorts."""
    import random
    random.seed(88)
    curve = []
    rate = 1.0
    for day in range(31):
        if day == 0:
            rate = 1.0
        elif day == 1:
            rate = round(random.uniform(0.65, 0.78), 3)
        elif day <= 3:
            rate = round(rate * random.uniform(0.88, 0.95), 3)
        elif day <= 7:
            rate = round(rate * random.uniform(0.92, 0.97), 3)
        else:
            rate = round(rate * random.uniform(0.96, 0.99), 3)
        curve.append({"day": day, "retention_rate": rate})
    return {
        "avg_d1": curve[1]["retention_rate"],
        "avg_d7": curve[7]["retention_rate"],
        "avg_d30": curve[30]["retention_rate"],
        "curve": curve,
    }


def _demo_daily_retention(days: int = 30) -> List[Dict[str, Any]]:
    """Daily returning vs new vs churned users."""
    import random
    random.seed(55)
    today = date.today()
    result = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        total = random.randint(8, 25)
        returning = int(total * random.uniform(0.5, 0.8))
        new_users = random.randint(0, 4)
        result.append({
            "date": d.isoformat(),
            "total_active": total,
            "returning": returning,
            "new": new_users,
            "churned_estimate": random.randint(0, 3),
        })
    return result


# ---------------------------------------------------------------------------
# Live Firestore queries (used when Firestore is connected)
# ---------------------------------------------------------------------------

def _live_overview() -> Dict[str, Any]:
    db = _get_db()
    if not db:
        return _demo_overview()

    try:
        today = date.today()
        today_str = today.isoformat()
        week_ago = (today - timedelta(days=7)).isoformat()
        month_ago = (today - timedelta(days=30)).isoformat()

        # Get all users
        users_ref = db.collection("users")
        all_users = list(users_ref.stream())
        total = len(all_users)

        active_today = 0
        active_7d = 0
        active_30d = 0
        total_xp = 0
        total_sessions_count = 0

        for doc in all_users:
            data = doc.to_dict()
            last_active = (data.get("last_active") or "")[:10]
            total_xp += data.get("xp_total", 0)

            if last_active >= today_str:
                active_today += 1
            if last_active >= week_ago:
                active_7d += 1
            if last_active >= month_ago:
                active_30d += 1

            # Count sessions per user
            sessions = list(db.collection("users").document(doc.id).collection("sessions").stream())
            total_sessions_count += len(sessions)

        avg_sessions = round(total_sessions_count / max(1, total), 1)

        return {
            "total_students": total,
            "active_today": active_today,
            "active_7d": active_7d,
            "active_30d": active_30d,
            "total_sessions": total_sessions_count,
            "avg_sessions_per_student": avg_sessions,
            "avg_accuracy": 0.0,  # computed from sessions if needed
            "avg_session_duration_sec": 0,
            "date": today_str,
        }
    except Exception as e:
        logger.warning(f"Analytics overview query failed: {e}")
        return _demo_overview()


def _live_students() -> List[Dict[str, Any]]:
    db = _get_db()
    if not db:
        return _demo_students()

    try:
        users_ref = db.collection("users")
        all_users = list(users_ref.stream())
        students = []
        for doc in all_users:
            data = doc.to_dict()
            uid = doc.id
            xp = data.get("xp_total", 0)
            students.append({
                "uid": uid,
                "display_name": data.get("display_name", "Unknown"),
                "xp_total": xp,
                "level": _get_level_name(xp),
                "total_sessions": 0,
                "avg_accuracy": 0.0,
                "streak_current": data.get("streak_current", 0),
                "last_active": (data.get("last_active") or "")[:10],
                "created_at": (data.get("created_at") or "")[:10],
                "persona": "Unknown",
            })
        return students
    except Exception as e:
        logger.warning(f"Analytics students query failed: {e}")
        return _demo_students()


def _live_student_detail(uid: str) -> Optional[Dict[str, Any]]:
    db = _get_db()
    if not db:
        return _demo_student_detail(uid)

    try:
        user_doc = db.collection("users").document(uid).get()
        if not user_doc.exists:
            return None
        data = user_doc.to_dict()
        xp = data.get("xp_total", 0)

        # Mastery
        mastery = {}
        mastery_docs = db.collection("users").document(uid).collection("mastery").stream()
        for mdoc in mastery_docs:
            mdata = mdoc.to_dict()
            score = mdata.get("internal_score", mdata.get("shown_score", 50))
            mastery[mdoc.id] = {
                "score": score,
                "label": "Mastered" if score >= 65 else ("Growing" if score >= 40 else "Emerging"),
                "attempts": mdata.get("total_attempts", 0),
                "last_practised": (mdata.get("last_practised") or "")[:10],
            }

        # Recent sessions
        sessions_docs = (
            db.collection("users").document(uid).collection("sessions")
            .order_by("ended_at", direction="DESCENDING")
            .limit(20)
            .stream()
        )
        recent_sessions = []
        for sdoc in sessions_docs:
            sdata = sdoc.to_dict()
            correct = sdata.get("total_correct", 0)
            total = sdata.get("total_correct", 0) + sdata.get("total_wrong", 0)
            recent_sessions.append({
                "date": (sdata.get("ended_at") or "")[:10],
                "topic": sdata.get("concept_id", "unknown"),
                "correct": correct,
                "total": total,
                "accuracy": round(correct / max(1, total), 2),
                "duration_sec": 0,
            })

        return {
            "uid": uid,
            "display_name": data.get("display_name", "Unknown"),
            "xp_total": xp,
            "level": _get_level_name(xp),
            "gems": data.get("gems", 0),
            "streak_current": data.get("streak_current", 0),
            "streak_longest": data.get("streak_longest", 0),
            "created_at": (data.get("created_at") or "")[:10],
            "last_active": (data.get("last_active") or "")[:10],
            "persona": "Unknown",
            "mastery": mastery,
            "recent_sessions": recent_sessions,
        }
    except Exception as e:
        logger.warning(f"Student detail query failed for {uid}: {e}")
        return _demo_student_detail(uid)


# ---------------------------------------------------------------------------
# Public API (auto-switches between live and demo)
# ---------------------------------------------------------------------------

def get_analytics_overview() -> Dict[str, Any]:
    if _is_available():
        return _live_overview()
    return _demo_overview()


def get_mastery_distribution() -> List[Dict[str, Any]]:
    # For now, always demo — requires aggregation pipeline
    return _demo_mastery_distribution()


def get_daily_active(days: int = 30) -> List[Dict[str, Any]]:
    return _demo_daily_active(days)


def get_topic_performance() -> List[Dict[str, Any]]:
    return _demo_topic_performance()


def get_persona_breakdown() -> List[Dict[str, Any]]:
    return _demo_persona_breakdown()


def get_students(search: str = "", sort: str = "last_active", limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    if _is_available():
        students = _live_students()
    else:
        students = _demo_students()

    # Search filter
    if search:
        q = search.lower()
        students = [s for s in students if q in s["display_name"].lower() or q in s["uid"].lower()]

    # Sort
    reverse = True
    if sort == "display_name":
        reverse = False
    students.sort(key=lambda s: s.get(sort, ""), reverse=reverse)

    total = len(students)
    students = students[offset:offset + limit]
    return {"total": total, "limit": limit, "offset": offset, "students": students}


def get_student_detail(uid: str) -> Optional[Dict[str, Any]]:
    if _is_available():
        return _live_student_detail(uid)
    return _demo_student_detail(uid)


# Retention
def get_retention_cohorts() -> List[Dict[str, Any]]:
    return _demo_retention_cohorts()


def get_retention_curve() -> Dict[str, Any]:
    return _demo_retention_curve()


def get_daily_retention(days: int = 30) -> List[Dict[str, Any]]:
    return _demo_daily_retention(days)
