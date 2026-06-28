"""Smoke test for the adaptive skill-ladder engine + endpoints."""
import os
os.environ["KIWIMATH_AUTH_DISABLED"] = "1"
os.environ.setdefault("KIWIMATH_OLYMPIAD_CONTENT_DIR", os.path.abspath("../content-live/olympiad"))
os.environ.setdefault("KIWIMATH_CURRICULUM_CONTENT_DIR", os.path.abspath("../content-live/curriculum"))

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.core.auth import verify_token
from app.services.content_store_level import level_store, bootstrap_level_from_env
bootstrap_level_from_env()
from app.api.level import router
from app.services.adaptive_skill import engine_skill, AdaptiveSkillEngine

app = FastAPI(); app.include_router(router, dependencies=[Depends(verify_token)])
c = TestClient(app)
fails = []
def P(ok, msg):
    print(("[PASS] " if ok else "[FAIL] ") + msg)
    if not ok: fails.append(msg)

# pick an L4 topic with a RICH ladder (>5 skills + a multi-question skill) to
# exercise the cluster drip. Search topics rather than assuming the first one —
# new Vedantu single-skill topics can sort ahead of the original multi-skill banks.
LV = "L4"
TK = None
for t in level_store.topics(LV):
    if not t.questions:
        continue
    lad, _qi = engine_skill._ladder(LV, t.topic_key)
    # need >5 skills, skills 0 AND 1 each with a cluster (the API walk drips on
    # skill 1), and some skill with a 3+ cluster (the multi-drip test)
    if (len(lad) > 5 and len(lad[0][1]) >= 2 and len(lad[1][1]) >= 2
            and any(len(qs) >= 3 for _s, qs in lad)):
        TK = t.topic_key; break
ladder, qindex = engine_skill._ladder(LV, TK)
P(TK is not None and len(ladder) > 5, f"ladder built: {len(ladder)} skills in {LV}/{TK}")

def grade_body(qid, correct):
    q = level_store.get(qid)
    if q.choices:
        ci = int(q.correct_answer)
        return {"selected_index": ci if correct else (ci + 1) % len(q.choices)}
    cv = q.correct_value
    return {"selected_value": cv if correct else (float(cv) + 1)}

U = "adaptive-engine-user"
engine_skill.reset(U, LV, TK)

# 1) skill question CORRECT -> next skill, cluster skipped
q0 = engine_skill.next_qid(U, LV, TK)
P(q0 == ladder[0][1][0], "start on skill 0's skill-question (cluster parent)")
engine_skill.record(U, LV, TK, q0, True)
st = engine_skill.status(U, LV, TK)
P(st["skill_index"] == 1 and st["on_cluster_question"] == 0, "skill correct -> advance to skill 1 (cluster skipped)")
P(engine_skill.next_qid(U, LV, TK) == ladder[1][1][0], "now showing skill 1's skill-question")

# 2) skill question WRONG -> drip its cluster questions (use a skill that HAS a
#    cluster — singleton skills can't drip, so don't assume skill 1 has one)
sd = next(i for i, (s, qs) in enumerate(ladder) if len(qs) >= 2)
engine_skill._set_pos(U, LV, TK, sd, 0)
engine_skill.record(U, LV, TK, ladder[sd][1][0], False)
st = engine_skill.status(U, LV, TK)
P(st["skill_index"] == sd and st["on_cluster_question"] == 1, "skill wrong -> stay on skill, show cluster Q1")
P(engine_skill.next_qid(U, LV, TK) == ladder[sd][1][1], "showing cluster question #1 (not the parent)")

# 3) multi-drip then a cluster CORRECT -> next skill
si = next(i for i, (s, qs) in enumerate(ladder) if len(qs) >= 3)
engine_skill._set_pos(U, LV, TK, si, 0)
qs = ladder[si][1]
engine_skill.record(U, LV, TK, qs[0], False)
P(engine_skill.next_qid(U, LV, TK) == qs[1], "drip: parent wrong -> cluster Q1")
engine_skill.record(U, LV, TK, qs[1], False)
P(engine_skill.next_qid(U, LV, TK) == qs[2], "drip: cluster Q1 wrong -> cluster Q2")
engine_skill.record(U, LV, TK, qs[2], True)
P(engine_skill.status(U, LV, TK)["skill_index"] == si + 1, "cluster question correct -> advance to next skill")

# 4) cluster EXHAUSTED (all wrong) -> next skill anyway
s2 = next(i for i, (s, qs) in enumerate(ladder) if len(qs) == 2)
engine_skill._set_pos(U, LV, TK, s2, 0)
for qq in ladder[s2][1]:
    engine_skill.record(U, LV, TK, qq, False)
P(engine_skill.status(U, LV, TK)["skill_index"] == s2 + 1, "cluster exhausted (all wrong) -> advance to next skill")

# 5) PERSISTENCE: a fresh engine instance (new login / new server instance) resumes
engine_skill._set_pos(U, LV, TK, 7, 0)
saved = engine_skill.next_qid(U, LV, TK)
fresh = AdaptiveSkillEngine()       # empty cache, shares the durable state store
P(fresh.next_qid(U, LV, TK) == saved, "re-login (fresh engine) resumes the SAME question — never jumps back")

# 6) no-regress: re-answering an already-cleared earlier skill does not move back
engine_skill._set_pos(U, LV, TK, 7, 0)
engine_skill.record(U, LV, TK, ladder[2][1][0], True)   # an old skill (index 2)
P(engine_skill.status(U, LV, TK)["skill_index"] == 7, "answering a cleared earlier question does NOT regress position")

# 7) API end-to-end: next -> answer/check -> next, adaptive status flows
U2 = "adaptive-api-user"; engine_skill.reset(U2, LV, TK)
n1 = c.get(f"/v3/olympiad/levels/{LV}/topics/{TK}/next?user_id={U2}").json()
P("adaptive" in n1 and n1["adaptive"]["skill_index"] == 0 and "correct_answer" not in n1, "API next: skill 0, status present, no answer leak")
g = grade_body(n1["id"], True); g.update({"user_id": U2, "question_id": n1["id"]})
ac = c.post("/v3/answer/check", json=g).json()
P(ac["correct"] and ac["adaptive"]["skill_index"] == 1, "API correct -> ladder advanced to skill 1")
n2 = c.get(f"/v3/olympiad/levels/{LV}/topics/{TK}/next?user_id={U2}").json()
P(n2["id"] != n1["id"] and n2["adaptive"]["skill_index"] == 1, "API next: new skill's parent (cluster skipped)")
g2 = grade_body(n2["id"], False); g2.update({"user_id": U2, "question_id": n2["id"]})
ac2 = c.post("/v3/answer/check", json=g2).json()
P(not ac2["correct"] and ac2["adaptive"]["on_cluster_question"] == 1, "API wrong -> now on cluster question 1")
n3 = c.get(f"/v3/olympiad/levels/{LV}/topics/{TK}/next?user_id={U2}").json()
P(n3["adaptive"]["skill_index"] == 1 and n3["id"] != n2["id"], "API next: a cluster question of the SAME skill")
ss = c.get(f"/v3/olympiad/levels/{LV}/topics/{TK}/adaptive-status?user_id={U2}").json()
P(ss["skill_index"] == 1 and ss["skills_total"] == len(ladder), "adaptive-status endpoint reports saved position")

print("\nDONE" if not fails else f"\nFAILURES: {fails}")
import sys; sys.exit(1 if fails else 0)
