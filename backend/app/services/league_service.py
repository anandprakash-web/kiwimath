"""
Weekly League — the core competitive loop.

Students are placed in a **cohort of ~30** of the same level and tier (Bronze →
Silver → Gold → Platinum → Diamond → Legendary). They earn **League Points (LP)**
all week (the Daily Contest is the biggest source; practice adds a little). At the
week's end the top promote, the bottom relegate, the middle stays — and fresh
cohorts form. LP is period-scoped (it does NOT touch the spendable economy:
coins/gems/xp keep flowing through `gamification`, so there's no disjoint).

Durable state via `FirestoreBackedStore` (in-memory fallback for local/tests).
Cohort mutations are read-modify-write (last-write-wins is acceptable here: a
cohort of 29–31 or an LP write that loses a microscopic race is harmless; money
is never touched).
"""

from __future__ import annotations

import datetime
import threading
from typing import Any, Dict, List, Optional, Tuple

from app.services.state_store import FirestoreBackedStore

TIERS = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Legendary"]
COHORT_SIZE = 30
PROMOTE = 7
RELEGATE = 7

_member = FirestoreBackedStore("league_member")    # user -> {week, level, tier, cohort_key, name}
_cohort = FirestoreBackedStore("league_cohort")    # cohort_key -> {week, level, tier, idx, members:{uid:{name,lp}}}
_ptr = FirestoreBackedStore("league_ptr")          # "{week}|{level}|{tier}" -> {idx, count}


_IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

def iso_week(d: Optional[datetime.date] = None) -> str:
    # Weeks are IST-aligned (Monday 00:00 IST) to match the Daily Contest day,
    # so the rollover cron fires Sunday 23:55 IST (= 18:25 UTC).
    d = d or datetime.datetime.now(_IST).date()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


class LeagueService:
    def __init__(self) -> None:
        self._lock = threading.Lock()

    # --------------------------------------------------------- assignment
    def _assign_cohort(self, week: str, level: str, tier: str, user_id: str, name: str) -> str:
        pk = f"{week}|{level}|{tier}"
        with self._lock:
            ptr = _ptr.get(pk) or {"idx": 0, "count": 0}
            idx, count = int(ptr.get("idx", 0)), int(ptr.get("count", 0))
            if count >= COHORT_SIZE:
                idx, count = idx + 1, 0
            cohort_key = f"{week}|{level}|{tier}|{idx}"
            doc = _cohort.get(cohort_key) or {"week": week, "level": level, "tier": tier, "idx": idx, "members": {}}
            if user_id not in doc["members"]:
                doc["members"][user_id] = {"name": name, "lp": 0}
                count += 1
            _cohort.set(cohort_key, doc)
            _ptr.set(pk, {"idx": idx, "count": count})
            return cohort_key

    def ensure_member(self, user_id: str, level: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Return the user's membership for THIS week, assigning a cohort if the
        week rolled over (carrying their tier from last week)."""
        week = iso_week()
        m = _member.get(user_id)
        nm = name or (m.get("name") if m else None) or "Player"
        if m and m.get("week") == week and m.get("level") == level and m.get("cohort_key"):
            return m
        tier = (m.get("tier") if m else None) or "Bronze"
        if tier not in TIERS:
            tier = "Bronze"
        cohort_key = self._assign_cohort(week, level, tier, user_id, nm)
        m = {"week": week, "level": level, "tier": tier, "cohort_key": cohort_key, "name": nm}
        _member.set(user_id, m)
        return m

    # ----------------------------------------------------------------- lp
    def add_lp(self, user_id: str, level: str, delta: int, name: Optional[str] = None) -> int:
        if delta == 0:
            return self._user_lp(user_id)
        m = self.ensure_member(user_id, level, name)
        with self._lock:
            doc = _cohort.get(m["cohort_key"])
            if not doc:
                return 0
            mem = doc["members"].setdefault(user_id, {"name": m["name"], "lp": 0})
            mem["lp"] = int(mem.get("lp", 0)) + int(delta)
            _cohort.set(m["cohort_key"], doc)
            return mem["lp"]

    def _user_lp(self, user_id: str) -> int:
        m = _member.get(user_id)
        if not m or not m.get("cohort_key"):
            return 0
        doc = _cohort.get(m["cohort_key"]) or {}
        return int(doc.get("members", {}).get(user_id, {}).get("lp", 0))

    # ---------------------------------------------------------- standings
    def standings(self, user_id: str, level: str) -> Dict[str, Any]:
        m = self.ensure_member(user_id, level)
        doc = _cohort.get(m["cohort_key"]) or {"members": {}, "tier": m["tier"]}
        rows = sorted(
            ([uid, v.get("name", "Player"), int(v.get("lp", 0))] for uid, v in doc["members"].items()),
            key=lambda r: (-r[2], r[0]),
        )
        n = len(rows)
        promote_to = min(len(TIERS) - 1, TIERS.index(m["tier"]) + 1)
        relegate_to = max(0, TIERS.index(m["tier"]) - 1)
        out_rows, my_rank = [], None
        for i, (uid, nm, lp) in enumerate(rows):
            rank = i + 1
            zone = "promote" if rank <= PROMOTE else ("relegate" if rank > n - RELEGATE and n > PROMOTE else "hold")
            if uid == user_id:
                my_rank = rank
            out_rows.append({"rank": rank, "name": nm, "lp": lp, "zone": zone, "me": uid == user_id})
        return {
            "level": level, "tier": m["tier"], "week": m["week"],
            "cohort_size": n, "my_rank": my_rank,
            "promote_zone": PROMOTE, "relegate_zone": RELEGATE,
            "promote_to": TIERS[promote_to], "relegate_to": TIERS[relegate_to],
            "ends": _week_end_iso(m["week"]),
            "rows": out_rows,
        }

    # ----------------------------------------------------------- rollover
    def rollover(self, week: Optional[str] = None) -> Dict[str, int]:
        """End-of-week: promote top, relegate bottom, set each member's tier for
        next week (their new cohort forms lazily on their next interaction)."""
        week = week or iso_week()
        promoted = relegated = 0
        for cohort_key, doc in _cohort.all(limit=5000):
            if not isinstance(doc, dict) or doc.get("week") != week:
                continue
            tier = doc.get("tier", "Bronze")
            ti = TIERS.index(tier) if tier in TIERS else 0
            rows = sorted(doc.get("members", {}).items(), key=lambda kv: (-int(kv[1].get("lp", 0)), kv[0]))
            n = len(rows)
            for i, (uid, _v) in enumerate(rows):
                rank = i + 1
                new_ti = ti
                if rank <= PROMOTE:
                    new_ti = min(len(TIERS) - 1, ti + 1); promoted += 1
                elif rank > n - RELEGATE and n > PROMOTE:
                    new_ti = max(0, ti - 1); relegated += 1
                mm = _member.get(uid) or {}
                mm["tier"] = TIERS[new_ti]
                mm["week"] = "rolled"           # force reassignment next interaction
                _member.set(uid, mm)
        return {"promoted": promoted, "relegated": relegated}


def _week_end_iso(week: str) -> str:
    try:
        y, w = week.split("-W")
        monday = datetime.date.fromisocalendar(int(y), int(w), 1)
        return (monday + datetime.timedelta(days=6)).isoformat()
    except Exception:
        return ""


league = LeagueService()
