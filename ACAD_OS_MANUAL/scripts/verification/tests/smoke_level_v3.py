import os
os.environ["KIWIMATH_AUTH_DISABLED"]="1"
os.environ.setdefault("KIWIMATH_OLYMPIAD_CONTENT_DIR", os.path.abspath("content-live/olympiad"))
os.environ.setdefault("KIWIMATH_CURRICULUM_CONTENT_DIR", os.path.abspath("content-live/curriculum"))
import sys; sys.path.insert(0,"backend")
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.core.auth import verify_token
from app.services.content_store_level import level_store, bootstrap_level_from_env
bootstrap_level_from_env()
from app.api.level import router as level_router
app=FastAPI(); app.include_router(level_router, dependencies=[Depends(verify_token)])
c=TestClient(app)
P=lambda ok,msg: print(("[PASS] " if ok else "[FAIL] ")+msg)

# olympiad
r=c.get("/v3/olympiad/levels").json(); P(len(r["levels"])==8 and r["levels"][0]["available"] and not r["levels"][7]["available"], "levels: 8, L1 avail, L8 (IMO) not")
t=c.get("/v3/olympiad/levels/L1/topics").json(); P(len(t["topics"])==8 and t["topics"][0]["display_name"], "L1 topics: 8")
nq=c.get("/v3/olympiad/levels/L1/topics/number_sense/next").json(); P("stem" in nq and "choices" in nq and "correct_answer" not in nq and "correct_value" not in nq, "next question served WITHOUT answer leak")
qid=nq["id"]; gq=c.get(f"/v3/olympiad/question/{qid}"); P(gq.status_code==200 and "correct_answer" not in gq.json(), "get question (no leak)")
vis=c.get(f"/v3/olympiad/question/{qid}/visual"); P(vis.status_code in (200,404), f"visual endpoint ({vis.status_code})")
el=c.get("/v3/olympiad/levels/L8/topics").json(); P(el["topics"]==[], "empty level L8 (IMO) -> no topics (scaffold hidden); level card coming-soon")

# curriculum
b=c.get("/v3/curriculum/boards").json(); P(len(b["boards"])==5, "5 boards")
ch=c.get("/v3/curriculum/ncert/grade/5/chapters").json(); idxs=[x["index"] for x in ch["chapters"]]; P(idxs==sorted(idxs), "chapters sequenced ascending")
chq=c.get(f"/v3/curriculum/ncert/grade/5/chapter/{ch['chapters'][0]['display_name']}/questions"); P(chq.status_code==200 and chq.json()["total"]>0, "chapter questions resolve")

# economy: answer a question CORRECTLY and check reward + wallet consistency
real=level_store.get(qid); ci=real.correct_answer
w0=c.get("/v3/me/wallet?user_id=dev-local").json(); coins0=w0["kiwi_coins"]
ac=c.post("/v3/answer/check", json={"user_id":"dev-local","question_id":qid,"selected_index":ci,"time_taken_ms":4000}).json()
P(ac["correct"] is True and ac["reward"]["xp"]>0, f"correct answer -> correct=True, +{ac['reward']['xp']}xp +{ac['reward']['coins']}coins")
P("correct_answer" in ac, "answer-check DOES return the answer (after answering)")
w1=ac["wallet"]; coins1=w1["kiwi_coins"]
P(coins1>=coins0+ac["reward"]["coins"], f"wallet in answer-check updated (incl. engine bonus): {coins0}->{coins1}")
w2=c.get("/v3/me/wallet?user_id=dev-local").json()
P(w2["kiwi_coins"]==coins1, f"/me/wallet matches answer-check wallet ({w2['kiwi_coins']}) — NO DISJOINT")
# wrong answer -> diagnostic possible, no crash
wrong_idx=(ci+1)%len(real.choices)
aw=c.post("/v3/answer/check", json={"user_id":"dev-local","question_id":qid,"selected_index":wrong_idx,"time_taken_ms":3000}).json()
P(aw["correct"] is False, "wrong answer -> correct=False")
# progress reads SAME state
pr=c.get("/v3/me/progress?user_id=dev-local").json()
P("scale_score" in pr and pr["scale_max"]==800 and len(pr["strands"])==4 and "logic_puzzles" in pr, f"progress: scale={pr['scale_score']}/800, verdict='{pr['verdict']}', 4 strands + logic")
# idempotency
k="test-key-123"
i1=c.post("/v3/answer/check", json={"user_id":"dev-local","question_id":qid,"selected_index":ci}, headers={"X-Idempotency-Key":k}).json()
i2=c.post("/v3/answer/check", json={"user_id":"dev-local","question_id":qid,"selected_index":ci}, headers={"X-Idempotency-Key":k}).json()
P(i1["wallet"]["kiwi_coins"]==i2["wallet"]["kiwi_coins"], "idempotency: duplicate POST replays same response (no double-award)")
st=c.get("/v3/stats").json(); P(st["olympiad_total"]==19642 and st["curriculum_total"]==10336, "stats match the bank")
print("\nDONE")
