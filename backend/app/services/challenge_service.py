"""
The Climb — adaptive Challenge (a sequential mini-CAT, GRE/GMAT-style).

A short, ability-adaptive test that finds the edge of a learner's ability and
reports how high they reached. It is SEPARATE from the skill-ladder Practice
(the moat): it touches no content, no skill/cluster tags, and no ladder engine.
It reuses the existing 3PL toolkit (app/assessment/irt_model.py) and the SAME
200–800 scale the Progress tab shows (proficiency_levels.theta_to_scale_score),
so the rating never disagrees with the rest of the app (no disjoint).

Loop per answer:
  ask near current θ → re-estimate θ + SE from all answers (EAP) → pick the
  unseen item with the most Fisher information at θ (random among the top-K, for
  exposure control) → stop at the length cap → score θ → 200–800 "Climb rating".

⚠️ Calibration caveat: item difficulties (irt_b) are heuristic and discrimination
is fixed (a = 1.0). The rating is therefore presented *modestly* and sharpens as
real responses feed scripts/irt_calibrator.py over time. v1 is measurement-only —
it does NOT write to the economy ledger (the contest already covers rewarded tests).

State (durable Firestore + in-mem fallback):
  challenge_sessions/{user_id}        → the in-progress climb (one active, resume-safe)
  challenge_best/{user_id}|{level}    → best rating + recent history
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.assessment.irt_model import ItemParameters, estimate_ability_eap
from app.services.content_store_level import level_store, numeric_correct
from app.services.proficiency_levels import (
    theta_to_scale_score,
    get_proficiency_for_display,
)
from app.services.state_store import FirestoreBackedStore

# --- tunables (v1, founder-approved) ---------------------------------------
CLIMB_LENGTH = 10          # fixed-length climb
PRIOR_SD = 1.5             # EAP prior width (uncertain start)
TOP_K = 6                  # exposure control: random pick among the K most-informative
GUESS_MCQ = 0.20           # pseudo-guessing for choice questions; ~0 for typed
FIXED_DISCRIM = 1.0        # a — fixed until empirical calibration

_sessions = FirestoreBackedStore("challenge_sessions")
_best = FirestoreBackedStore("challenge_best")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public(q) -> Dict[str, Any]:
    """No-leak question payload (mirrors contest._public — NO answer fields)."""
    return {
        "id": q.id,
        "stem": q.stem,
        "choices": q.choices,
        "interaction_mode": getattr(q, "interaction_mode", "mcq"),
        "visual_svg": q.visual_svg,
        "visual_png": getattr(q, "visual_png", None),
    }


def _grade(q, selected_index, selected_value) -> bool:
    """Server-side grading (mirrors contest._correct)."""
    if selected_index is not None and q.choices:
        try:
            return int(selected_index) == int(q.correct_answer)
        except (TypeError, ValueError):
            return str(selected_index).strip() == str(q.correct_answer).strip()
    if selected_value is not None and getattr(q, "correct_value", None) is not None:
        return numeric_correct(q, selected_value)
    if selected_value is not None and q.choices:
        try:
            return str(selected_value).strip() == str(q.choices[int(q.correct_answer)]).strip()
        except (IndexError, ValueError, TypeError):
            return False
    return False


class ChallengeEngine:
    def __init__(self) -> None:
        self._pool_cache: Dict[str, List[ItemParameters]] = {}
        self._pmap_cache: Dict[str, Dict[str, ItemParameters]] = {}

    # ---- item pool (built once per level) ----------------------------------
    def _pool(self, level: str) -> List[ItemParameters]:
        if level not in self._pool_cache:
            self._build_pool(level)
        return self._pool_cache[level]

    def _pmap(self, level: str) -> Dict[str, ItemParameters]:
        if level not in self._pmap_cache:
            self._build_pool(level)
        return self._pmap_cache[level]

    def _build_pool(self, level: str) -> None:
        items: List[ItemParameters] = []
        for t in level_store.topics(level):
            for q in getattr(t, "questions", []) or []:
                if q.irt_b is None:
                    continue
                c = GUESS_MCQ if q.choices else 0.0
                items.append(ItemParameters(item_id=q.id, a=FIXED_DISCRIM, b=float(q.irt_b), c=c))
        self._pool_cache[level] = items
        self._pmap_cache[level] = {it.item_id: it for it in items}

    def _climb_len(self, level: str) -> int:
        return min(CLIMB_LENGTH, len(self._pool(level)))

    # ---- CAT primitives ----------------------------------------------------
    def _select(self, level: str, theta: float, asked: set, rng: random.Random) -> Optional[str]:
        cands = [it for it in self._pool(level) if it.item_id not in asked]
        if not cands:
            return None
        cands.sort(key=lambda it: it.information(theta), reverse=True)
        return rng.choice(cands[:TOP_K]).item_id

    def _estimate(self, level: str, asked_ids: List[str], responses: List[bool],
                  prior_mean: float) -> tuple:
        pm = self._pmap(level)
        items = [pm[i] for i in asked_ids[:len(responses)] if i in pm]
        if not items:
            return prior_mean, PRIOR_SD
        return estimate_ability_eap(items, responses, prior_mean=prior_mean, prior_sd=PRIOR_SD)

    # ---- lifecycle ---------------------------------------------------------
    def start(self, user_id: str, level: str) -> Dict[str, Any]:
        sess = _sessions.get(user_id)
        if sess and sess.get("status") == "active" and sess.get("level") == level and sess.get("pending"):
            q = level_store.get(sess["pending"])
            if q:
                return self._state_payload(sess, _public(q))  # resume — same pending question

        if not self._pool(level):
            return {"error": "no_pool", "message": "This level has no calibrated questions yet."}

        # Warm start: prior = last completed climb's θ for this level, else neutral.
        best = _best.get(f"{user_id}|{level}") or {}
        prior_mean = float(best.get("last_theta", 0.0) or 0.0)
        rng = random.Random(uuid.uuid4().int)
        first = self._select(level, prior_mean, set(), rng)
        if first is None:
            return {"error": "no_pool", "message": "This level has no calibrated questions yet."}

        sess = {
            "session_id": uuid.uuid4().hex[:12],
            "user_id": user_id, "level": level, "status": "active",
            "prior_mean": prior_mean,
            "asked": [first], "responses": [], "selected": [],
            "pending": first, "theta": prior_mean, "se": PRIOR_SD,
            "started_at": _now(),
        }
        _sessions.set(user_id, sess)
        return self._state_payload(sess, _public(level_store.get(first)))

    def answer(self, user_id: str, session_id: Optional[str], qid: str,
               selected_index=None, selected_value=None, time_ms: int = 0) -> Dict[str, Any]:
        sess = _sessions.get(user_id)
        if not sess or sess.get("status") != "active":
            return {"error": "no_active_session"}
        if session_id and sess.get("session_id") != session_id:
            return {"error": "session_mismatch"}
        # Idempotency / no-regress: only the pending item advances; anything else
        # just replays the current state (so a double-tap never corrupts the climb).
        if qid != sess.get("pending"):
            q = level_store.get(sess.get("pending")) if sess.get("pending") else None
            return self._state_payload(sess, _public(q) if q else None)

        q = level_store.get(qid)
        if not q:
            return {"error": "bad_question"}

        ok = _grade(q, selected_index, selected_value)
        sess["responses"].append(bool(ok))
        sess["selected"].append({"qid": qid, "i": selected_index, "v": selected_value})

        theta, se = self._estimate(sess["level"], sess["asked"], sess["responses"], sess["prior_mean"])
        sess["theta"], sess["se"] = theta, se

        if len(sess["responses"]) >= self._climb_len(sess["level"]):
            return self._finish(sess, ok)

        rng = random.Random(uuid.uuid4().int)
        nxt = self._select(sess["level"], theta, set(sess["asked"]), rng)
        if nxt is None:
            return self._finish(sess, ok)
        sess["asked"].append(nxt)
        sess["pending"] = nxt
        _sessions.set(user_id, sess)
        out = self._state_payload(sess, _public(level_store.get(nxt)))
        out["last_correct"] = bool(ok)
        return out

    def _finish(self, sess: Dict[str, Any], just_correct: bool) -> Dict[str, Any]:
        sess["status"] = "done"
        sess["pending"] = None
        theta = sess["theta"]
        rating = theta_to_scale_score(theta)
        disp = get_proficiency_for_display(theta)

        pm = self._pmap(sess["level"])
        peak_b = None
        for i, qid in enumerate(sess["asked"]):
            if i < len(sess["responses"]) and sess["responses"][i] and qid in pm:
                b = pm[qid].b
                if peak_b is None or b > peak_b:
                    peak_b = b
        correct_n = sum(1 for r in sess["responses"] if r)

        result = {
            "rating": rating,
            "theta": round(theta, 3),
            "se": round(sess["se"], 3),
            "band": disp.get("name", ""),
            "band_emoji": disp.get("emoji", ""),
            "band_color": disp.get("color", ""),
            "peak_rating": theta_to_scale_score(peak_b) if peak_b is not None else rating,
            "correct": correct_n,
            "of": len(sess["responses"]),
            "last_correct": bool(just_correct),
            "ts": _now(),
        }
        sess["result"] = result
        _sessions.set(sess["user_id"], sess)

        bkey = f"{sess['user_id']}|{sess['level']}"
        best = _best.get(bkey) or {"plays": 0, "best_rating": 0, "history": []}
        new_best = max(int(best.get("best_rating", 0) or 0), rating)
        best.update({
            "plays": int(best.get("plays", 0) or 0) + 1,
            "last_theta": round(theta, 3),
            "last_rating": rating,
            "best_rating": new_best,
        })
        hist = list(best.get("history", []))
        hist.append({"rating": rating, "correct": correct_n,
                     "of": len(sess["responses"]), "ts": result["ts"]})
        best["history"] = hist[-20:]
        _best.set(bkey, best)

        return {"done": True, "result": result,
                "best_rating": new_best, "is_personal_best": rating >= new_best,
                "plays": best["plays"]}

    def _state_payload(self, sess: Dict[str, Any], question: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "done": False,
            "session_id": sess["session_id"],
            "level": sess["level"],
            "index": len(sess["responses"]),       # how many answered so far (0-based pos)
            "total": self._climb_len(sess["level"]),
            "question": question,
        }

    def me(self, user_id: str, level: str) -> Dict[str, Any]:
        best = _best.get(f"{user_id}|{level}") or {}
        sess = _sessions.get(user_id)
        active = bool(sess and sess.get("status") == "active" and sess.get("level") == level)
        return {
            "level": level,
            "best_rating": int(best.get("best_rating", 0) or 0),
            "last_rating": int(best.get("last_rating", 0) or 0),
            "plays": int(best.get("plays", 0) or 0),
            "history": best.get("history", []),
            "active": active,
        }


challenge = ChallengeEngine()
