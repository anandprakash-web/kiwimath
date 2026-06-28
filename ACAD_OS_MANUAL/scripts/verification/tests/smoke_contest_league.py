"""Smoke test — Daily Contest + Weekly League MVP."""
import os
os.environ["KIWIMATH_AUTH_DISABLED"] = "1"
os.environ["KIWIMATH_CONTEST_ALWAYS_OPEN"] = "1"
os.environ.setdefault("KIWIMATH_OLYMPIAD_CONTENT_DIR", os.path.abspath("../content-live/olympiad"))
os.environ.setdefault("KIWIMATH_CURRICULUM_CONTENT_DIR", os.path.abspath("../content-live/curriculum"))

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.core.auth import verify_token
from app.core import auth
from app.services.content_store_level import level_store, bootstrap_level_from_env
bootstrap_level_from_env()
from app.api.contest import router as contest_router
from app.services.contest_service import contest
from app.services.league_service import league, iso_week, _member, _cohort

app = FastAPI(); app.include_router(contest_router, dependencies=[Depends(verify_token)])
c = TestClient(app)
fails = []
def P(ok, msg):
    print(("[PASS] " if ok else "[FAIL] ") + msg)
    if not ok: fails.append(msg)

LV = "L4"

# 1) deterministic set, same per (date,level), differs by level
s1 = contest.todays_qids(LV); s2 = contest.todays_qids(LV)
P(len(s1) == 8 and s1 == s2, f"contest set deterministic ({len(s1)} qs, stable)")
P(contest.todays_qids("L5") != s1, "different level → different set")
# increasing difficulty
bs = [(level_store.get(q).irt_b or 0) for q in s1]
P(bs == sorted(bs), "set ordered by increasing difficulty")

# 2) get_contest serves questions live, NO answer leak
gc = c.get(f"/v3/contest/today?user_id=stu1&level={LV}").json()
P(gc["status"] == "live" and gc["attempted"] is False and len(gc.get("questions", [])) == 8, "today: live, 8 questions, not attempted")
P(all("correct_answer" not in q and "correct_value" not in q for q in gc["questions"]), "contest questions do NOT leak the answer")

def ans_for(qid, correct=True):
    q = level_store.get(qid)
    if q.choices:
        ci = int(q.correct_answer)
        return {"qid": qid, "selected_index": ci if correct else (ci + 1) % len(q.choices), "time_ms": 5000}
    return {"qid": qid, "selected_value": q.correct_value if correct else (float(q.correct_value) + 1), "time_ms": 5000}

# 3) submit all-correct → score + LP, economy awarded
w0 = c.get("/v3/me/wallet?user_id=stu1") if False else None
sub = c.post("/v3/contest/submit", json={"user_id": "stu1", "level": LV, "name": "Aarav K.",
             "answers": [ans_for(q, True) for q in s1]}).json()
P(sub["correct"] == 8 and sub["score"] > 0 and sub["lp"] == sub["score"], f"all-correct → {sub['correct']}/8, score {sub['score']}")
P(sub["rank"] == 1, "submitter is rank 1 on an empty board")

# 4) one attempt — re-submit replays, no double award
sub2 = c.post("/v3/contest/submit", json={"user_id": "stu1", "level": LV,
              "answers": [ans_for(q, True) for q in s1]}).json()
P(sub2.get("replayed") is True and sub2["score"] == sub["score"], "second submit replays (one attempt, no double-award)")

# 5) second student, fewer correct → board ranks by score
sub_b = c.post("/v3/contest/submit", json={"user_id": "stu2", "level": LV, "name": "Nuha R.",
               "answers": [ans_for(q, i < 3) for i, q in enumerate(s1)]}).json()
P(sub_b["correct"] == 3 and sub_b["score"] < sub["score"], f"student 2 → 3/8, lower score {sub_b['score']}")
lb = c.get(f"/v3/contest/leaderboard?level={LV}").json()
P(lb["total"] == 2 and lb["rows"][0]["score"] >= lb["rows"][1]["score"], "leaderboard ranks by score")

# 6) league standings — cohort, my rank, zones
st = c.get(f"/v3/league/me?user_id=stu1&level={LV}").json()
P(st["tier"] == "Bronze" and st["my_rank"] == 1 and st["cohort_size"] >= 2, f"league: Bronze, rank {st['my_rank']}, cohort {st['cohort_size']}")
P(any(r["me"] for r in st["rows"]) and st["rows"][0]["zone"] == "promote", "standings: my row flagged + promotion zone present")
P(st["promote_to"] == "Silver", "promotes to Silver")

# 7) practice LP nudges the league (answer/check) — stu1 already has contest LP; add practice
lp_before = st["rows"][[r["me"] for r in st["rows"]].index(True)]["lp"]
league.add_lp("stu1", LV, 5)
lp_after = league.standings("stu1", LV)["rows"][0]["lp"]
P(lp_after == lp_before + 5, f"practice LP accrues ({lp_before} → {lp_after})")

# 8) rollover — seed a 20-strong Gold cohort, promote top7 / relegate bottom7
wk = iso_week(); CK = f"{wk}|{LV}|Gold|0"
members = {f"r{i}": {"name": f"R{i}", "lp": 1000 - i * 10} for i in range(20)}
_cohort.set(CK, {"week": wk, "level": LV, "tier": "Gold", "idx": 0, "members": members})
for i in range(20):
    _member.set(f"r{i}", {"week": wk, "level": LV, "tier": "Gold", "cohort_key": CK, "name": f"R{i}"})
roll = league.rollover(wk)
P(roll["promoted"] >= 7 and roll["relegated"] >= 7, f"rollover: promoted {roll['promoted']}, relegated {roll['relegated']}")
P(_member.get("r0")["tier"] == "Platinum" and _member.get("r19")["tier"] == "Silver" and _member.get("r10")["tier"] == "Gold",
  "rollover: top→Platinum, bottom→Silver, middle stays Gold")

# 9) persistence — a fresh service instance reads the saved contest result + LP
from app.services.contest_service import ContestService
fresh = ContestService()
P(fresh.get_contest("stu1", LV)["attempted"] is True, "re-login: contest result persists (still attempted)")

# 10) AUTH — a real (non-dev) token can't touch another user's contest/league
app2 = FastAPI(); app2.include_router(contest_router)
app2.dependency_overrides[auth.verify_token] = lambda: {"uid": "userA"}
c2 = TestClient(app2)
P(c2.get(f"/v3/contest/today?user_id=userA&level={LV}").status_code == 200, "auth: own contest → 200")
P(c2.get(f"/v3/contest/today?user_id=userB&level={LV}").status_code == 403, "auth: other's contest → 403 (IDOR closed)")
P(c2.get(f"/v3/league/me?user_id=userB&level={LV}").status_code == 403, "auth: other's league → 403")
P(c2.post("/v3/contest/submit", json={"user_id": "userB", "level": LV, "answers": []}).status_code == 403, "auth: submit as other → 403")

# 11) rollover endpoint — dev/admin/internal may trigger; a normal user can't
rr = c.post("/v3/internal/league-rollover")
P(rr.status_code == 200 and rr.json().get("ok") is True, "rollover endpoint: dev/internal → 200")
P(c2.post("/v3/internal/league-rollover").status_code == 403, "rollover endpoint: normal user → 403")

print("\nDONE" if not fails else f"\nFAILURES ({len(fails)}): {fails}")
import sys; sys.exit(1 if fails else 0)
