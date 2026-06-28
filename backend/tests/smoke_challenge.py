"""Smoke test — The Climb (adaptive Challenge / mini-CAT)."""
import os
os.environ["KIWIMATH_AUTH_DISABLED"] = "1"
os.environ.setdefault("KIWIMATH_OLYMPIAD_CONTENT_DIR", os.path.abspath("../content-live/olympiad"))
os.environ.setdefault("KIWIMATH_CURRICULUM_CONTENT_DIR", os.path.abspath("../content-live/curriculum"))

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.core.auth import verify_token
from app.core import auth
from app.services.content_store_level import level_store, bootstrap_level_from_env
bootstrap_level_from_env()
from app.api.challenge import router as challenge_router

app = FastAPI(); app.include_router(challenge_router, dependencies=[Depends(verify_token)])
c = TestClient(app)
fails = []
def P(ok, msg):
    print(("[PASS] " if ok else "[FAIL] ") + msg)
    if not ok: fails.append(msg)

LV = "L1"

def _isnum(x):
    try:
        float(x); return True
    except (TypeError, ValueError):
        return False

def run_climb(uid, be_correct):
    """White-box climb: read the real answer from the store and answer right/wrong."""
    r = c.post("/v3/challenge/start", json={"user_id": uid, "level": LV}).json()
    leaks, steps = 0, 0
    if "question" not in r:
        return r, 99
    while not r.get("done"):
        q = r["question"]
        if "correct_answer" in q or "correct_value" in q:
            leaks += 1
        full = level_store.get(q["id"])
        body = {"user_id": uid, "session_id": r["session_id"], "qid": q["id"], "time_ms": 4000}
        if full.choices:
            ci = int(full.correct_answer)
            body["selected_index"] = ci if be_correct else (ci + 1) % max(2, len(full.choices))
        else:
            cv = full.correct_value
            body["selected_value"] = cv if be_correct else ((float(cv) + 1000) if _isnum(cv) else "definitely_wrong_zzz")
        r = c.post("/v3/challenge/answer", json=body).json()
        steps += 1
        if steps > 40:
            break
    return r, leaks

# 1) start serves one question, fixed length, NO answer leak
s = c.post("/v3/challenge/start", json={"user_id": "hi", "level": LV}).json()
P("question" in s and s.get("done") is False, "start → a question, not done")
P(s.get("total") == 10, f"climb length = {s.get('total')} (fixed 10)")
P("correct_answer" not in s["question"] and "correct_value" not in s["question"], "start question does NOT leak the answer")

# 2) high learner (all correct) → completes, valid 200–800 rating, no leak anywhere
rh, leaks_h = run_climb("hi", True)
P(rh.get("done") is True and "result" in rh, "high learner completes the climb")
P(leaks_h == 0, "no answer leaked across the whole climb")
rating_h = rh["result"]["rating"]
P(200 <= rating_h <= 800, f"rating on the 200–800 scale ({rating_h})")
P(rh["result"]["correct"] == rh["result"]["of"], f"high learner all correct ({rh['result']['correct']}/{rh['result']['of']})")
P(rating_h >= 500, f"a perfect climb lands at/above the mean ({rating_h})")

# 3) low learner (all wrong) → completes much lower (the engine is genuinely adaptive)
rl, _ = run_climb("lo", False)
rating_l = rl["result"]["rating"]
P(rl["result"]["correct"] == 0, f"low learner none correct (0/{rl['result']['of']})")
P(rating_l <= 500, f"a zero climb lands at/below the mean ({rating_l})")
P(rating_h > rating_l, f"adaptive: high rating {rating_h} > low rating {rating_l}")

# 4) resume — re-login returns the SAME pending question, never jumps back
r0 = c.post("/v3/challenge/start", json={"user_id": "res", "level": LV}).json()
sid = r0["session_id"]; cur = r0
for _ in range(3):
    q = cur["question"]; full = level_store.get(q["id"])
    body = {"user_id": "res", "session_id": sid, "qid": q["id"], "time_ms": 3000}
    if full.choices: body["selected_index"] = int(full.correct_answer)
    else: body["selected_value"] = full.correct_value
    cur = c.post("/v3/challenge/answer", json=body).json()
pending_id = cur["question"]["id"]; idx = cur["index"]
again = c.post("/v3/challenge/start", json={"user_id": "res", "level": LV}).json()
P(again["question"]["id"] == pending_id and again["index"] == idx == 3, "re-login resumes the SAME question (no jump back)")

# 5) persistence — best rating + plays recorded and read back
me = c.get(f"/v3/challenge/me?user_id=hi&level={LV}").json()
P(me["best_rating"] == rating_h and me["plays"] >= 1, f"best rating persists ({me['best_rating']}, plays {me['plays']})")

# 6) AUTH — a real token can't climb (or read history) as another user
app2 = FastAPI(); app2.include_router(challenge_router)
app2.dependency_overrides[auth.verify_token] = lambda: {"uid": "userA"}
c2 = TestClient(app2)
P(c2.post("/v3/challenge/start", json={"user_id": "userA", "level": LV}).status_code == 200, "auth: own climb → 200")
P(c2.post("/v3/challenge/start", json={"user_id": "userB", "level": LV}).status_code == 403, "auth: other's climb → 403 (IDOR closed)")
P(c2.get(f"/v3/challenge/me?user_id=userB&level={LV}").status_code == 403, "auth: other's history → 403")

print("\nDONE" if not fails else f"\nFAILURES ({len(fails)}): {fails}")
import sys; sys.exit(1 if fails else 0)
