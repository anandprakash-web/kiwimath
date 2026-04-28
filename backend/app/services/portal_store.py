"""
Kiwimath Portal Store — Payments, User Flow, Economy & Team RBAC data.

Provides demo data for local dev (no Firestore/Play Billing).
When Firestore is connected, reads real gamification state for Economy.
"""

from __future__ import annotations
import hashlib, logging, os, random, sqlite3, time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kiwimath.portal")


def _get_db():
    from app.services.firestore_service import _get_db as _fs_get_db
    return _fs_get_db()

def _is_available() -> bool:
    from app.services.firestore_service import is_firestore_available
    return is_firestore_available()

# ══════════════════════════════════════════════════════════════
# PAYMENTS MODULE
# ══════════════════════════════════════════════════════════════

def _demo_payment_overview() -> Dict[str, Any]:
    return {
        "mrr": 0, "mrr_formatted": "$0",
        "total_subscribers": 0, "active_trials": 0,
        "trial_conversion_rate": 0.0,
        "churn_rate_30d": 0.0,
        "ltv_estimate": 0.0,
        "note": "Google Play Billing not yet connected. This module will show live data once the Play Developer API is integrated and subscriptions are active.",
        "status": "not_connected",
    }

def _demo_subscriptions() -> List[Dict[str, Any]]:
    return []

def _demo_revenue_chart() -> List[Dict[str, Any]]:
    today = date.today()
    return [{"date": (today - timedelta(days=i)).isoformat(), "revenue": 0, "new_subs": 0, "churned": 0} for i in range(29, -1, -1)]

def _demo_plans() -> List[Dict[str, Any]]:
    return [
        {"plan_id": "monthly_premium", "name": "Monthly Premium", "price": "$4.99/mo", "subscribers": 0, "status": "planned"},
        {"plan_id": "yearly_premium", "name": "Yearly Premium", "price": "$39.99/yr", "subscribers": 0, "status": "planned"},
        {"plan_id": "family_plan", "name": "Family (up to 3)", "price": "$7.99/mo", "subscribers": 0, "status": "planned"},
    ]

def get_payment_overview() -> Dict[str, Any]:
    return _demo_payment_overview()

def get_subscriptions(status: str = "", limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    subs = _demo_subscriptions()
    return {"total": len(subs), "limit": limit, "offset": offset, "subscriptions": subs}

def get_revenue_chart(days: int = 30) -> List[Dict[str, Any]]:
    return _demo_revenue_chart()

def get_plans() -> List[Dict[str, Any]]:
    return _demo_plans()


# ══════════════════════════════════════════════════════════════
# USER FLOW MODULE
# ══════════════════════════════════════════════════════════════

def _demo_onboarding_funnel() -> List[Dict[str, Any]]:
    random.seed(33)
    steps = [
        ("App Install", 100),
        ("Open App", 92),
        ("Select Grade", 78),
        ("Start First Session", 64),
        ("Complete First Session", 51),
        ("Return Day 2", 38),
        ("Complete 5 Sessions", 24),
        ("Weekly Active", 18),
    ]
    return [{"step": s[0], "users": s[1], "pct": round(s[1] / 100, 2), "drop_off": round(1 - s[1] / max(1, steps[max(0, i-1)][1]), 2) if i > 0 else 0} for i, s in enumerate(steps)]

def _demo_topic_engagement() -> List[Dict[str, Any]]:
    random.seed(44)
    topics = [
        ("Counting & Observation", 312, 0.81, 264),
        ("Logic & Ordering", 287, 0.68, 301),
        ("Arithmetic & Operations", 298, 0.73, 245),
        ("Geometry & Spatial", 201, 0.65, 289),
        ("Patterns & Sequences", 256, 0.70, 273),
        ("Measurement & Data", 178, 0.62, 312),
        ("Puzzles & Combinatorics", 164, 0.59, 287),
        ("Number Theory", 146, 0.56, 334),
    ]
    return [{"topic": t[0], "sessions": t[1], "completion_rate": t[2], "avg_duration_sec": t[3], "hint_usage_rate": round(random.uniform(0.15, 0.55), 2), "drop_off_rate": round(1 - t[2], 2)} for t in topics]

def _demo_session_flow() -> Dict[str, Any]:
    random.seed(55)
    return {
        "avg_session_length": 6,
        "avg_completion_rate": 0.72,
        "avg_duration_sec": 264,
        "hint_usage_overall": 0.34,
        "questions_per_session": 6,
        "sessions_per_day_avg": 1.8,
        "peak_hours": [
            {"hour": 7, "sessions": 12}, {"hour": 8, "sessions": 28}, {"hour": 9, "sessions": 15},
            {"hour": 15, "sessions": 22}, {"hour": 16, "sessions": 45}, {"hour": 17, "sessions": 52},
            {"hour": 18, "sessions": 38}, {"hour": 19, "sessions": 25}, {"hour": 20, "sessions": 18},
        ],
        "drop_off_points": [
            {"point": "After Q1 wrong answer", "pct": 0.08},
            {"point": "After 2 consecutive wrong", "pct": 0.15},
            {"point": "After hint level 3+", "pct": 0.06},
            {"point": "Session timeout (>5min idle)", "pct": 0.04},
            {"point": "App backgrounded", "pct": 0.12},
        ],
    }

def get_onboarding_funnel() -> List[Dict[str, Any]]:
    return _demo_onboarding_funnel()

def get_topic_engagement() -> List[Dict[str, Any]]:
    return _demo_topic_engagement()

def get_session_flow() -> Dict[str, Any]:
    return _demo_session_flow()


# ══════════════════════════════════════════════════════════════
# ECONOMY MODULE
# ══════════════════════════════════════════════════════════════

def _demo_economy_overview() -> Dict[str, Any]:
    return {
        "total_coins_in_circulation": 48720,
        "total_gems_in_circulation": 2340,
        "avg_coins_per_user": 1035,
        "avg_gems_per_user": 49.8,
        "coins_earned_today": 1240,
        "gems_earned_today": 86,
        "coins_spent_today": 380,
        "gems_spent_today": 12,
        "inflation_index": 1.02,
        "health": "stable",
    }

def _demo_badge_stats() -> List[Dict[str, Any]]:
    badges = [
        ("First Steps", "Complete first session", 0.95, "common"),
        ("Streak Starter", "3-day streak", 0.68, "common"),
        ("Perfect Round", "6/6 in a session", 0.42, "uncommon"),
        ("Topic Explorer", "Try all 8 topics", 0.31, "uncommon"),
        ("Streak Master", "7-day streak", 0.24, "rare"),
        ("Speed Demon", "Complete session in <2min", 0.18, "rare"),
        ("Century Club", "100 XP milestone", 0.52, "common"),
        ("Kiwi Scholar", "Reach Kiwi Jr level", 0.35, "uncommon"),
        ("Math Wizard", "Master 3 topics", 0.15, "rare"),
        ("Legend", "Reach Kiwi Master level", 0.03, "legendary"),
        ("Iron Streak", "30-day streak", 0.05, "legendary"),
        ("Completionist", "Answer 500 questions", 0.08, "rare"),
    ]
    return [{"name": b[0], "description": b[1], "unlock_rate": b[2], "rarity": b[3]} for b in badges]

def _demo_currency_flow(days: int = 14) -> List[Dict[str, Any]]:
    random.seed(66)
    today = date.today()
    result = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        earned = random.randint(800, 1800)
        spent = random.randint(200, 600)
        result.append({
            "date": d.isoformat(),
            "coins_earned": earned, "coins_spent": spent, "net_coins": earned - spent,
            "gems_earned": random.randint(40, 120), "gems_spent": random.randint(5, 30),
        })
    return result

def _demo_avatar_adoption() -> List[Dict[str, Any]]:
    avatars = [
        ("kiwi_default", "Default Kiwi", 0.45),
        ("kiwi_ninja", "Ninja Kiwi", 0.18),
        ("kiwi_astronaut", "Astronaut Kiwi", 0.12),
        ("kiwi_wizard", "Wizard Kiwi", 0.09),
        ("kiwi_pirate", "Pirate Kiwi", 0.07),
        ("kiwi_chef", "Chef Kiwi", 0.05),
        ("kiwi_golden", "Golden Kiwi", 0.04),
    ]
    return [{"avatar_id": a[0], "name": a[1], "adoption_rate": a[2], "users": int(a[2] * 47)} for a in avatars]

def _demo_level_distribution() -> List[Dict[str, Any]]:
    levels = [
        ("Seed", 8, 0.17), ("Sprout", 12, 0.26), ("Kiwi Jr", 14, 0.30),
        ("Kiwi", 8, 0.17), ("Super Kiwi", 4, 0.09), ("Kiwi Master", 1, 0.02),
    ]
    return [{"level": l[0], "count": l[1], "pct": l[2]} for l in levels]

def get_economy_overview() -> Dict[str, Any]:
    return _demo_economy_overview()

def get_badge_stats() -> List[Dict[str, Any]]:
    return _demo_badge_stats()

def get_currency_flow(days: int = 14) -> List[Dict[str, Any]]:
    return _demo_currency_flow(days)

def get_avatar_adoption() -> List[Dict[str, Any]]:
    return _demo_avatar_adoption()

def get_level_distribution() -> List[Dict[str, Any]]:
    return _demo_level_distribution()


# ══════════════════════════════════════════════════════════════
# TEAM RBAC MODULE
# ══════════════════════════════════════════════════════════════

_team_db = None

def _get_team_db():
    global _team_db
    if _team_db is not None:
        return _team_db
    db_path = os.environ.get("KIWIMATH_CMS_DB", "/tmp/kiwimath_cms.db")
    _team_db = sqlite3.connect(db_path, check_same_thread=False)
    _team_db.row_factory = sqlite3.Row
    _team_db.execute("PRAGMA journal_mode=WAL")
    _team_db.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL DEFAULT 'viewer',
            created_at REAL NOT NULL DEFAULT (strftime('%s','now')),
            last_login REAL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)
    _team_db.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT DEFAULT '',
            details TEXT DEFAULT '',
            timestamp REAL NOT NULL DEFAULT (strftime('%s','now'))
        )
    """)
    _team_db.commit()
    # Ensure at least one admin
    existing = _team_db.execute("SELECT COUNT(*) as c FROM admin_users").fetchone()
    if existing["c"] == 0:
        _team_db.execute(
            "INSERT INTO admin_users (email, display_name, role) VALUES (?, ?, ?)",
            ("anand.prakash@vedantu.com", "Anand Prakash", "admin")
        )
        _team_db.commit()
    return _team_db

def get_team_members() -> List[Dict[str, Any]]:
    db = _get_team_db()
    rows = db.execute("SELECT * FROM admin_users ORDER BY created_at").fetchall()
    return [dict(r) for r in rows]

def add_team_member(email: str, display_name: str, role: str = "viewer") -> Dict[str, Any]:
    db = _get_team_db()
    if role not in ("admin", "editor", "viewer"):
        return {"error": "Invalid role. Must be admin, editor, or viewer."}
    try:
        db.execute(
            "INSERT INTO admin_users (email, display_name, role) VALUES (?, ?, ?)",
            (email, display_name, role)
        )
        db.commit()
        log_action(email, "user_added", f"Role: {role}")
        row = db.execute("SELECT * FROM admin_users WHERE email=?", (email,)).fetchone()
        return dict(row)
    except sqlite3.IntegrityError:
        return {"error": f"User {email} already exists."}

def update_team_member(email: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = _get_team_db()
    existing = db.execute("SELECT * FROM admin_users WHERE email=?", (email,)).fetchone()
    if not existing:
        return None
    if "role" in updates and updates["role"] not in ("admin", "editor", "viewer"):
        return {"error": "Invalid role"}
    sets, vals = [], []
    for key in ("display_name", "role", "is_active"):
        if key in updates:
            sets.append(f"{key}=?")
            vals.append(updates[key])
    if sets:
        vals.append(email)
        db.execute(f"UPDATE admin_users SET {', '.join(sets)} WHERE email=?", vals)
        db.commit()
        log_action(email, "user_updated", str(updates))
    row = db.execute("SELECT * FROM admin_users WHERE email=?", (email,)).fetchone()
    return dict(row)

def remove_team_member(email: str) -> bool:
    db = _get_team_db()
    cur = db.execute("DELETE FROM admin_users WHERE email=? AND role != 'admin'", (email,))
    db.commit()
    if cur.rowcount > 0:
        log_action(email, "user_removed", "")
        return True
    return False

def log_action(user_email: str, action: str, details: str = "", target: str = ""):
    db = _get_team_db()
    db.execute(
        "INSERT INTO audit_log (user_email, action, target, details) VALUES (?, ?, ?, ?)",
        (user_email, action, target, details)
    )
    db.commit()

def get_audit_log(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    db = _get_team_db()
    total = db.execute("SELECT COUNT(*) as c FROM audit_log").fetchone()["c"]
    rows = db.execute(
        "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ? OFFSET ?",
        (limit, offset)
    ).fetchall()
    return {"total": total, "limit": limit, "offset": offset, "entries": [dict(r) for r in rows]}

def get_role_permissions() -> Dict[str, Dict[str, bool]]:
    return {
        "admin": {"view_cms": True, "edit_content": True, "publish": True, "view_analytics": True, "manage_team": True, "view_payments": True, "export_data": True},
        "editor": {"view_cms": True, "edit_content": True, "publish": False, "view_analytics": True, "manage_team": False, "view_payments": False, "export_data": True},
        "viewer": {"view_cms": True, "edit_content": False, "publish": False, "view_analytics": True, "manage_team": False, "view_payments": False, "export_data": False},
    }
