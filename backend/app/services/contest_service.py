"""
Daily Contest — the flagship appointment event.

Every day at a fixed time (6 PM IST) a short **rated set** opens for each level.
Everyone in a level gets the **same set that day** (fair comparison), drawn
deterministically from the level bank by the (date, level) seed and ordered by
increasing difficulty. One attempt. Server-graded. Awards the **economy**
(coins/gems/xp via `gamification`, so it stays the one ledger) **and League
Points** (via `league`, the period-scoped competitive score).

State (`FirestoreBackedStore`, durable + in-mem fallback):
  contest_results  "{date}|{level}|{user}" -> {score, lp, correct, answers, ts}
  contest_board    "{date}|{level}"        -> {entries: {uid: {name, score, correct}}}
"""

from __future__ import annotations

import datetime
import hashlib
import os
import random
import threading
from datetime import timezone, timedelta
from typing import Any, Dict, List, Optional

from app.services.content_store_level import level_store
from app.services.state_store import FirestoreBackedStore
from app.services.gamification import gamification
from app.services.league_service import league

IST = timezone(timedelta(hours=5, minutes=30))
OPEN_HOUR = 18          # 6 PM IST
WINDOW_HOURS = 4
N_QUESTIONS = 8
ONTIME_WINDOW_MIN = 60  # first hour → on-time bonus

BASE = {"easy": 100, "med": 200, "hard": 350}

_results = FirestoreBackedStore("contest_results")
_board = FirestoreBackedStore("contest_board")


def _always_open() -> bool:
    return os.environ.get("KIWIMATH_CONTEST_ALWAYS_OPEN") == "1"


class ContestService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._set_cache: Dict[str, List[str]] = {}

    # --------------------------------------------------------- scheduling
    def today(self) -> str:
        return datetime.datetime.now(IST).strftime("%Y-%m-%d")

    def status(self, now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        now = now or datetime.datetime.now(IST)
        open_dt = now.replace(hour=OPEN_HOUR, minute=0, second=0, microsecond=0)
        close_dt = open_dt + timedelta(hours=WINDOW_HOURS)
        if _always_open():
            s = "live"
        elif now < open_dt:
            s = "upcoming"
        elif now < close_dt:
            s = "live"
        else:
            s = "closed"
        return {"status": s, "opens_at": open_dt.isoformat(), "closes_at": close_dt.isoformat(),
                "on_time": _always_open() or now <= open_dt + timedelta(minutes=ONTIME_WINDOW_MIN)}

    # ------------------------------------------------------------- set gen
    def _gradeable_pool(self, level: str, verified_only: bool = False):
        out = []
        for t in level_store.topics(level):
            for q in t.questions:
                if verified_only and not getattr(q, "verified", False):
                    continue
                if (q.choices and len(q.choices) >= 2) or getattr(q, "correct_value", None) is not None:
                    out.append(q)
        return out

    def todays_qids(self, level: str, date: Optional[str] = None) -> List[str]:
        date = date or self.today()
        ck = f"{date}|{level}"
        if ck in self._set_cache:
            return self._set_cache[ck]
        # Prefer the VERIFIED pool (human-authored, competition-sourced, key-validated)
        # when a level has enough to fill a full contest; else fall back to the full pool.
        vpool = self._gradeable_pool(level, verified_only=True)
        pool = vpool if len(vpool) >= N_QUESTIONS else self._gradeable_pool(level)
        pool.sort(key=lambda q: ((q.irt_b if q.irt_b is not None else 0.0), q.id))
        if not pool:
            self._set_cache[ck] = []
            return []
        seed = int(hashlib.md5(ck.encode()).hexdigest(), 16)
        rnd = random.Random(seed)
        n = min(N_QUESTIONS, len(pool))
        binsize = len(pool) / n
        qids = []
        for i in range(n):                       # one pick per difficulty band → increasing difficulty
            lo = int(i * binsize)
            hi = max(lo + 1, int((i + 1) * binsize))
            qids.append(pool[rnd.randrange(lo, min(hi, len(pool)))].id)
        self._set_cache[ck] = qids
        return qids

    @staticmethod
    def _public(q) -> Dict[str, Any]:
        return {"id": q.id, "stem": q.stem, "choices": q.choices,
                "interaction_mode": getattr(q, "interaction_mode", "mcq"),
                "visual_svg": q.visual_svg, "visual_png": getattr(q, "visual_png", None),
                "verified": getattr(q, "verified", False),     # show the "Verified" badge
                "source": getattr(q, "source", None),
                "irt_b": q.irt_b}   # NO correct_answer / correct_value

    def get_contest(self, user_id: str, level: str) -> Dict[str, Any]:
        date = self.today()
        st = self.status()
        qids = self.todays_qids(level, date)
        res = _results.get(f"{date}|{level}|{user_id}")
        payload = {"date": date, "level": level, "status": st["status"],
                   "opens_at": st["opens_at"], "closes_at": st["closes_at"],
                   "on_time": st["on_time"], "attempted": bool(res),
                   "n_questions": len(qids), "time_limit_s": 90}
        if res:
            payload["result"] = {"score": res["score"], "lp": res["lp"], "correct": res["correct"]}
        elif qids and st["status"] == "live":
            payload["questions"] = [self._public(level_store.get(q)) for q in qids if level_store.get(q)]
        return payload

    # ---------------------------------------------------------- grading
    @staticmethod
    def _correct(q, ans: Dict[str, Any]) -> bool:
        si, sv = ans.get("selected_index"), ans.get("selected_value")
        if si is not None and q.choices:
            try:
                return int(si) == int(q.correct_answer)
            except (TypeError, ValueError):
                return str(si).strip() == str(q.correct_answer).strip()
        if sv is not None and getattr(q, "correct_value", None) is not None:
            from app.services.content_store_level import numeric_correct
            return numeric_correct(q, sv)   # range-aware (fraction/decimal) or exact
        if sv is not None and q.choices:
            try:
                return str(sv).strip() == str(q.choices[int(q.correct_answer)]).strip()
            except (IndexError, ValueError, TypeError):
                return False
        return False

    @staticmethod
    def _band(q) -> str:
        b = q.irt_b if q.irt_b is not None else 0.0
        return "easy" if b <= 0 else ("med" if b <= 1.0 else "hard")

    def submit(self, user_id: str, level: str, answers: List[Dict[str, Any]],
               name: Optional[str] = None) -> Dict[str, Any]:
        date = self.today()
        rkey = f"{date}|{level}|{user_id}"
        existing = _results.get(rkey)
        if existing:                                   # one attempt — replay, never double-award
            existing["replayed"] = True
            existing["rank"] = self._rank(date, level, user_id)
            return existing

        qids = set(self.todays_qids(level, date))
        ans_by_q = {a.get("qid"): a for a in (answers or [])}
        st = self.status()
        streak = int(getattr(gamification.get_state(user_id), "streak_current", 0) or 0)
        streak_mult = min(2.0, 1.0 + 0.1 * min(streak, 7))
        ontime_mult = 1.5 if st["on_time"] else 1.0

        raw = 0.0
        correct_n = 0
        for qid in self.todays_qids(level, date):
            q = level_store.get(qid)
            if not q:
                continue
            a = ans_by_q.get(qid, {})
            ok = self._correct(q, a) if a else False
            if ok:
                correct_n += 1
                t = (a.get("time_ms") or 0) / 1000.0
                speed = 1.0 + 0.5 * max(0.0, 1.0 - (t / 90.0)) if t else 1.0
                raw += BASE[self._band(q)] * speed
            # economy flows through the ONE ledger (coins/gems/xp/streak)
            meta = level_store.meta(qid)
            topic = meta[1] if meta else level
            try:
                gamification.record_answer(
                    user_id=user_id, topic_id=topic, is_correct=ok,
                    difficulty=int(getattr(q, "difficulty_score", 0) or 0), question_id=qid)
            except Exception:
                pass

        score = int(round(raw * streak_mult * ontime_mult))
        lp_total = league.add_lp(user_id, level, score, name)

        result = {"score": score, "lp": score, "correct": correct_n,
                  "of": len(qids), "league_lp": lp_total, "replayed": False,
                  "on_time": st["on_time"], "streak_mult": round(streak_mult, 2),
                  "ts": datetime.datetime.now(timezone.utc).isoformat()}
        _results.set(rkey, result)
        self._add_to_board(date, level, user_id, name or "Player", score, correct_n)
        result["rank"] = self._rank(date, level, user_id)
        return result

    # --------------------------------------------------------- leaderboard
    def _add_to_board(self, date: str, level: str, user_id: str, name: str, score: int, correct: int) -> None:
        bk = f"{date}|{level}"
        with self._lock:
            doc = _board.get(bk) or {"entries": {}}
            doc["entries"][user_id] = {"name": name, "score": score, "correct": correct}
            _board.set(bk, doc)

    def _ranked(self, date: str, level: str) -> List[Any]:
        doc = _board.get(f"{date}|{level}") or {"entries": {}}
        return sorted(((uid, v) for uid, v in doc["entries"].items()),
                      key=lambda kv: (-int(kv[1]["score"]), kv[0]))

    def _rank(self, date: str, level: str, user_id: str) -> Optional[int]:
        for i, (uid, _v) in enumerate(self._ranked(date, level)):
            if uid == user_id:
                return i + 1
        return None

    def leaderboard(self, level: str, date: Optional[str] = None, top: int = 50) -> Dict[str, Any]:
        date = date or self.today()
        ranked = self._ranked(date, level)
        return {"date": date, "level": level, "total": len(ranked),
                "rows": [{"rank": i + 1, "name": v["name"], "score": int(v["score"]),
                          "correct": int(v["correct"])} for i, (_uid, v) in enumerate(ranked[:top])]}


contest = ContestService()
