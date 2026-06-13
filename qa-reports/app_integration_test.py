#!/usr/bin/env python3
"""
Kiwimath LIVE INTEGRATION QA — Flutter tabs <-> FastAPI backend contract test.

Boots the backend in-process with FastAPI TestClient and replays every API
call each app tab makes, validating responses against the EXACT field
requirements of the Dart models (non-nullable casts = required fields).

Run from backend dir:
  cd <repo>/backend
  KIWIMATH_AUTH_DISABLED=1 \
  KIWIMATH_V2_CONTENT_DIR=../content-live/content-v2 \
  KIWIMATH_V4_CONTENT_DIR=../content-live/content-v4 \
  NCERT_CONTENT_DIR=../content-live/content-v2/ncert-curriculum \
  SINGAPORE_CONTENT_DIR=../content-live/content-v2/singapore-curriculum \
  USCC_CONTENT_DIR=../content-live/content-v2/us-common-core \
  ICSE_CONTENT_DIR=../content-live/content-v2/icse-curriculum \
  IGCSE_CONTENT_DIR=../content-live/content-v2/igcse-curriculum \
  python3 ../qa-reports/app_integration_test.py
"""
import json
import os
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone

# ── Env defaults (so the script is re-runnable without the long prefix) ──────
os.environ.setdefault("KIWIMATH_AUTH_DISABLED", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CL = os.path.join(REPO, "content-live")
os.environ.setdefault("KIWIMATH_V2_CONTENT_DIR", os.path.join(CL, "content-v2"))
os.environ.setdefault("KIWIMATH_V4_CONTENT_DIR", os.path.join(CL, "content-v4"))
os.environ.setdefault("NCERT_CONTENT_DIR", os.path.join(CL, "content-v2", "ncert-curriculum"))
os.environ.setdefault("SINGAPORE_CONTENT_DIR", os.path.join(CL, "content-v2", "singapore-curriculum"))
os.environ.setdefault("USCC_CONTENT_DIR", os.path.join(CL, "content-v2", "us-common-core"))
os.environ.setdefault("ICSE_CONTENT_DIR", os.path.join(CL, "content-v2", "icse-curriculum"))
os.environ.setdefault("IGCSE_CONTENT_DIR", os.path.join(CL, "content-v2", "igcse-curriculum"))

BACKEND = os.path.join(REPO, "backend")
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import logging  # noqa: E402
for noisy in ("httpx", "kiwimath", "app", "uvicorn"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)
client.__enter__()  # run startup events (content store load)
import atexit  # noqa: E402
atexit.register(lambda: client.__exit__(None, None, None))
UID = f"qa_user_{uuid.uuid4().hex[:8]}"

ROWS = []      # (tab, endpoint, status, parses, content, issues)
BUGS = []      # (severity, title, evidence)


def row(tab, endpoint, status, parses, content, issues=""):
    ROWS.append((tab, endpoint, str(status), parses, str(content), issues))


def bug(severity, title, evidence):
    BUGS.append((severity, title, evidence))


# ── Dart model validators (mirror non-nullable casts in models/*.dart) ───────

def need(j, key, typ, errs, model, nullable_ok=False):
    """Mirror Dart `json[key] as T` (non-nullable) — missing/null/wrong type crashes."""
    v = j.get(key)
    if v is None:
        if not nullable_ok:
            errs.append(f"{model}: required '{key}' missing/null (Dart `as {typ.__name__}` crashes)")
        return None
    if typ is float:
        if not isinstance(v, (int, float)):
            errs.append(f"{model}: '{key}' is {type(v).__name__}, want num")
    elif not isinstance(v, typ) or (typ is int and isinstance(v, bool)):
        errs.append(f"{model}: '{key}' is {type(v).__name__}, want {typ.__name__}")
    return v


def validate_question_v2(q, errs):
    """QuestionV2.fromJson — question_v2.dart:136-161."""
    need(q, "question_id", str, errs, "QuestionV2")
    need(q, "stem", str, errs, "QuestionV2")
    need(q, "choices", list, errs, "QuestionV2")  # `as List<dynamic>` non-null
    need(q, "topic", str, errs, "QuestionV2")
    need(q, "topic_name", str, errs, "QuestionV2")
    need(q, "correct_answer", int, errs, "QuestionV2")  # `as int` non-null


def validate_answer_check(j, errs):
    """AnswerCheckResponse.fromJson — question_v2.dart:223-257."""
    need(j, "correct", bool, errs, "AnswerCheck")
    need(j, "correct_answer", int, errs, "AnswerCheck")


def validate_olympiad_question(q, errs):
    """OlympiadQuestion.fromJson — olympiad_worksheet.dart:78-113."""
    need(q, "id", str, errs, "OlympiadQuestion")
    need(q, "stem", str, errs, "OlympiadQuestion")


def validate_student_levels(j, errs):
    """StudentLevels.fromJson — student_levels.dart:113-122 (many required casts)."""
    need(j, "user_id", str, errs, "StudentLevels")
    need(j, "grade", int, errs, "StudentLevels")
    topics = need(j, "topics", list, errs, "StudentLevels") or []
    for t in topics[:3]:
        need(t, "topic_id", str, errs, "TopicLevels")
        need(t, "topic_name", str, errs, "TopicLevels")
        need(t, "grade", int, errs, "TopicLevels")
        levels = need(t, "levels", list, errs, "TopicLevels") or []
        for lv in levels[:2]:
            for k, ty in (("level", int), ("name", str), ("status", str),
                          ("difficulty_min", int), ("difficulty_max", int)):
                need(lv, k, ty, errs, "LevelInfo")


def jget(path, tab, label=None, params=None, expect=200, headers=None):
    r = client.get(path, params=params, headers=headers)
    label = label or path
    return r, label


# ════════════════════════════════════════════════════════════════════════════
# STARTUP / CONTENT LOAD
# ════════════════════════════════════════════════════════════════════════════
print("=" * 78)
print("STARTUP")
r = client.get("/health")
print(f"/health -> {r.status_code} {r.text[:200]}")
row("Startup", "GET /health", r.status_code, "n/a", "-",
    "" if r.status_code == 200 else "health failed")

uscc_dir = os.environ["USCC_CONTENT_DIR"]
if not os.path.isdir(uscc_dir):
    bug("HIGH", "us-common-core content dir missing",
        f"{uscc_dir} does not exist; USCC curriculum will have 0 chapters/questions")

# v2/v4 content counts (poke internal stores)
try:
    from app.api.questions_v2 import store_v2 as _s2
    v2_count = len(getattr(_s2, "questions", {}) or getattr(_s2, "_questions", {}))
except Exception:
    v2_count = "?"
try:
    from app.api.questions_v4 import store_v4 as _s4
    v4_count = sum(len(v) for v in getattr(_s4, "_topic_questions", {}).values()) or "?"
except Exception:
    v4_count = "?"
print(f"v2 store question count: {v2_count}; v4 store: {v4_count}")

# ════════════════════════════════════════════════════════════════════════════
# TAB: PRACTICE / OLYMPIAD
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("PRACTICE TAB")
TAB = "Practice"

# /v2/topics per grade
for g in range(1, 7):
    r = client.get("/v2/topics", params={"grade": g})
    errs, n = [], 0
    if r.status_code == 200:
        topics = r.json()
        n = len(topics)
        for t in topics:
            need(t, "topic_id", str, errs, "TopicV2")
            need(t, "topic_name", str, errs, "TopicV2")
            if (t.get("total_questions") or 0) == 0:
                errs.append(f"topic {t.get('topic_id')} has 0 questions")
        if n == 0:
            errs.append("no topics for grade")
    else:
        errs.append(r.text[:120])
    row(TAB, f"GET /v2/topics?grade={g}", r.status_code,
        "yes" if not errs else "NO", f"{n} topics", "; ".join(errs[:3]))

# edge: grade=9
r = client.get("/v2/topics", params={"grade": 9})
row(TAB, "GET /v2/topics?grade=9 (edge)", r.status_code, "n/a",
    len(r.json()) if r.status_code == 200 else "-",
    "" if r.status_code in (200, 400, 422) else "unexpected status")

# unified session
sample_qid = None
for g in (1, 3, 6):
    r = client.get("/v2/session/unified", params={"user_id": UID, "grade": g, "size": 10})
    errs, n = [], 0
    if r.status_code == 200:
        j = r.json()
        qs = j.get("questions") or []
        n = len(qs)
        if n == 0:
            errs.append("unified session returned 0 questions")
        for q in qs[:5]:
            if not q.get("question_id"):
                errs.append("plan item missing question_id")
        if qs and sample_qid is None:
            sample_qid = qs[0]["question_id"]
    else:
        errs.append(r.text[:150])
    row(TAB, f"GET /v2/session/unified?grade={g}", r.status_code,
        "yes" if not errs else "NO", f"{n} questions", "; ".join(errs[:3]))

# fetch a question by id + verify sentinel + hint ladder
hint_levels_seen = None
if sample_qid:
    r = client.get(f"/v2/questions/{sample_qid}")
    errs = []
    if r.status_code == 200:
        q = r.json()
        validate_question_v2(q, errs)
        ca = q.get("correct_answer")
        if ca != -1:
            errs.append(f"correct_answer={ca}, expected -1 sentinel (answer leak!)")
            bug("CRITICAL", "correct_answer leaked at fetch time",
                f"GET /v2/questions/{sample_qid} returned correct_answer={ca}")
        ladder = q.get("hint_ladder")
        if ladder:
            hint_levels_seen = [k for k in ladder if ladder[k]]
            if not any(ladder.get(f"level_{i}") for i in range(6)):
                errs.append("hint_ladder present but all 6 levels empty")
    else:
        errs.append(r.text[:120])
    row(TAB, f"GET /v2/questions/{{id}}", r.status_code,
        "yes" if not errs else "NO",
        f"hint levels: {hint_levels_seen}", "; ".join(errs[:3]))

# /v2/questions/next (topic-locked practice mode) — use a REAL topic_id from /v2/topics
topic_ids = [t["topic_id"] for t in client.get("/v2/topics", params={"grade": 2}).json()]
first_topic_id = topic_ids[0] if topic_ids else "counting_observation"
next_qid = None
r = client.get("/v2/questions/next",
               params={"topic": first_topic_id, "grade": 2, "user_id": UID, "window": 10})
errs = []
if r.status_code == 200:
    q = r.json()
    validate_question_v2(q, errs)
    next_qid = q.get("question_id")
    if q.get("correct_answer") != -1:
        errs.append(f"correct_answer={q.get('correct_answer')} not -1 sentinel")
else:
    errs.append(r.text[:150])
row(TAB, "GET /v2/questions/next (topic mode)", r.status_code,
    "yes" if not errs else "NO", next_qid or "-", "; ".join(errs[:3]))

# answer check + idempotency double-submit
if next_qid:
    idem = str(uuid.uuid4())
    body = {"question_id": next_qid, "selected_answer": 0, "user_id": UID,
            "time_taken_ms": 4200}
    r1 = client.post("/v2/answer/check", json=body,
                     headers={"X-Idempotency-Key": idem})
    errs = []
    if r1.status_code == 200:
        validate_answer_check(r1.json(), errs)
        j = r1.json()
        if j.get("correct_answer", -1) < 0:
            errs.append("verdict did not reveal true correct_answer")
        for fld in ("xp_earned", "coins_earned"):
            if fld not in j:
                errs.append(f"reward field '{fld}' missing")
    else:
        errs.append(r1.text[:150])
    row(TAB, "POST /v2/answer/check", r1.status_code,
        "yes" if not errs else "NO",
        f"correct={r1.json().get('correct') if r1.status_code==200 else '-'}",
        "; ".join(errs[:3]))

    # double submit, same key → identical response
    r2 = client.post("/v2/answer/check", json=body,
                     headers={"X-Idempotency-Key": idem})
    same = r2.status_code == 200 and r2.json() == r1.json()
    row(TAB, "POST /v2/answer/check (dup idem key)", r2.status_code,
        "n/a", "identical" if same else "DIFFERENT",
        "" if same else "idempotency replay returned different body")
    if not same and r2.status_code == 200:
        d1, d2 = r1.json(), r2.json()
        diff = {k: (d1.get(k), d2.get(k)) for k in set(d1) | set(d2) if d1.get(k) != d2.get(k)}
        bug("HIGH", "Idempotency key not honored on /v2/answer/check",
            f"second POST with same X-Idempotency-Key differs: {str(diff)[:300]}")

# visual endpoint — find a v2 question with an svg (scan real topics)
svg_qid = None
for tid in topic_ids:
    r = client.get("/v2/questions", params={"topic": tid, "limit": 50})
    if r.status_code != 200:
        continue
    for q in r.json():
        if q.get("visual_svg"):
            svg_qid = q["question_id"]
            break
    if svg_qid:
        break
if svg_qid:
    r = client.get(f"/v2/questions/{svg_qid}/visual")
    ok = r.status_code == 200 and r.text.lstrip().startswith("<svg")
    row(TAB, "GET /v2/questions/{id}/visual", r.status_code, "n/a",
        f"{len(r.text)}B svg" if ok else r.text[:60],
        "" if ok else "visual URL advertised in question payload but endpoint fails")
    if not ok:
        bug("HIGH", "ALL Practice-tab visuals broken: /v2/questions/{id}/visual 404s "
            "for inline-SVG questions",
            "3,736 v2 questions store inline '<svg...' markup in visual_svg (0 are file "
            "refs). questions_v2.py:212 advertises visual_svg='/v2/questions/{id}/visual' "
            "so the app renders an AuthedSvg box (question_screen_v2.dart:1104), but "
            "questions_v2.py:904 calls store_v2.get_svg(topic, q.visual_svg) which only "
            "does a file lookup (content_store_v2.py:440-467) and never returns inline "
            "markup -> 404 for every visual incl. 'essential' ones")
else:
    row(TAB, "GET /v2/questions/{id}/visual", "-", "n/a", "-",
        "no v2 question with visual_svg found to test")

# nonexistent question id (edge)
r = client.get("/v2/questions/NOPE-9999")
row(TAB, "GET /v2/questions/NOPE-9999 (edge)", r.status_code, "n/a", "-",
    "" if r.status_code == 404 else f"expected 404, got {r.status_code}")

# bookmarks (saved questions)
if next_qid:
    r = client.post("/v2/bookmarks/toggle", json={"user_id": UID, "question_id": next_qid})
    errs = []
    if r.status_code == 200:
        if "bookmarked" not in r.json():
            errs.append("missing 'bookmarked'")
    else:
        errs.append(r.text[:100])
    row(TAB, "POST /v2/bookmarks/toggle", r.status_code,
        "yes" if not errs else "NO", str(r.json() if r.status_code == 200 else "-")[:40],
        "; ".join(errs))
    r = client.get("/v2/bookmarks/list", params={"user_id": UID})
    n = len((r.json() or {}).get("questions", [])) if r.status_code == 200 else 0
    row(TAB, "GET /v2/bookmarks/list", r.status_code,
        "yes" if r.status_code == 200 else "NO", f"{n} bookmarks",
        "" if r.status_code == 200 and n >= 1 else "toggled bookmark not returned")
    r = client.get("/v2/bookmarks/check", params={"user_id": UID, "question_id": next_qid})
    row(TAB, "GET /v2/bookmarks/check", r.status_code, "yes" if r.status_code == 200 else "NO",
        str(r.json().get("bookmarked")) if r.status_code == 200 else "-", "")

# flag submission
r = client.post("/flag/submit", json={"question_id": next_qid or "T1-0001",
                                      "student_id": UID, "flag_type": "hint_not_good",
                                      "comment": "qa test flag"})
row(TAB, "POST /flag/submit", r.status_code,
    "yes" if r.status_code == 200 else "NO",
    str(r.json())[:50] if r.status_code == 200 else r.text[:80], "")

# question feedback
r = client.post(f"/v2/questions/{next_qid or 'T1-0001'}/feedback",
                json={"feedback_type": "too_easy", "user_id": UID})
row(TAB, "POST /v2/questions/{id}/feedback", r.status_code,
    "yes" if r.status_code == 200 else "NO", "-",
    "" if r.status_code == 200 else r.text[:100])

# session plan + student levels + mastery overview (home/practice shell calls)
r = client.get("/v2/session/plan", params={"user_id": UID, "grade": 2, "size": 10})
row(TAB, "GET /v2/session/plan", r.status_code, "yes" if r.status_code == 200 else "NO",
    len((r.json() or {}).get("questions", [])) if r.status_code == 200 else "-",
    "" if r.status_code == 200 else r.text[:100])

r = client.get("/v2/student/levels", params={"user_id": UID, "grade": 2})
errs = []
if r.status_code == 200:
    validate_student_levels(r.json(), errs)
else:
    errs.append(r.text[:120])
row(TAB, "GET /v2/student/levels", r.status_code, "yes" if not errs else "NO",
    f"{len(r.json().get('topics', []))} topics" if r.status_code == 200 else "-",
    "; ".join(errs[:3]))

r = client.get("/v2/mastery/overview", params={"user_id": UID, "grade": 2})
row(TAB, "GET /v2/mastery/overview", r.status_code,
    "yes" if r.status_code == 200 else "NO", "-",
    "" if r.status_code == 200 else r.text[:100])

# unified session complete (smart session end-of-session)
r = client.post("/v2/session/unified/complete",
                json={"user_id": UID, "grade": 2,
                      "results": [{"question_id": next_qid or "T1-0001", "correct": True,
                                   "time_taken_ms": 5000}]},
                headers={"X-Idempotency-Key": str(uuid.uuid4())})
row(TAB, "POST /v2/session/unified/complete", r.status_code,
    "yes" if r.status_code == 200 else "NO", "-",
    "" if r.status_code == 200 else r.text[:150])
if r.status_code == 500:
    bug("CRITICAL", "Smart-session completion always 500s",
        "questions_v2.py:1679 declares results: List[Dict] but line 1718 does "
        "r.question_id (attribute access on dict) -> AttributeError on every "
        "POST /v2/session/unified/complete; app's session-complete screen always errors")

# paywall status
r = client.get("/v2/paywall/status", params={"user_id": UID})
row(TAB, "GET /v2/paywall/status", r.status_code, "yes" if r.status_code == 200 else "NO",
    len(r.json()) if r.status_code == 200 else "-", "" if r.status_code == 200 else r.text[:100])

# ════════════════════════════════════════════════════════════════════════════
# TAB: DPP / WORKSHEETS (olympiad) + WAVEBOOK + PILLARS (olympiad v2)
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("DPP / WORKSHEETS TAB")
TAB = "Worksheets"

oly_visual_qid = None
for g in range(1, 7):
    r = client.get("/olympiad/worksheets/list", params={"grade": g})
    errs, n = [], 0
    if r.status_code == 200:
        j = r.json()
        days = j.get("days") or []
        sheets = j.get("worksheets") or []
        n = len(sheets)
        if not days:
            errs.append("'days' missing/empty (legacy Dart parser crashes: days as List)")
        if not sheets:
            errs.append("'worksheets' missing/empty")
        for w in sheets[:3]:
            if not isinstance(w.get("day"), int):
                errs.append("worksheet meta missing int 'day'")
            if not w.get("title"):
                errs.append("worksheet meta missing title")
    else:
        errs.append(r.text[:100])
    row(TAB, f"GET /olympiad/worksheets/list?grade={g}", r.status_code,
        "yes" if not errs else "NO", f"{n} worksheets", "; ".join(errs[:3]))

    # sample 5 days per grade
    bad_days = []
    q_total = 0
    for day in (1, 25, 50, 75, 100):
        r = client.get("/olympiad/worksheets", params={"grade": g, "day": day})
        if r.status_code != 200:
            bad_days.append(f"d{day}:{r.status_code}")
            continue
        ws = r.json()
        qs = ws.get("questions") or []
        q_total += len(qs)
        for q in qs:
            e2 = []
            validate_olympiad_question(q, e2)
            if e2:
                bad_days.append(f"d{day}:{e2[0][:60]}")
                break
            if q.get("interaction_mode", "mcq") == "mcq" and not q.get("choices"):
                bad_days.append(f"d{day}:{q['id']} mcq w/o choices")
                break
            if oly_visual_qid is None and (q.get("visual_url") or q.get("visual_ref")):
                oly_visual_qid = q["id"]
    row(TAB, f"GET /olympiad/worksheets?grade={g}&day=[1,25,50,75,100]",
        "200" if not bad_days else "MIXED",
        "yes" if not bad_days else "NO", f"{q_total} questions",
        "; ".join(bad_days[:3]))

# aggregate check: did ANY grade have worksheets?
ws_total = sum(int(r0[4].split()[0]) for r0 in ROWS
               if r0[0] == TAB and "worksheets/list" in r0[1] and r0[4].split()[0].isdigit())
if ws_total == 0:
    bug("CRITICAL", "DPP/Worksheets tab is EMPTY for all grades",
        "backend/app/api/olympiad.py:31 reads backend/content/olympiad/"
        "g{N}_olympiad_batch{1-5}.json — those 30 batch files (600 worksheets) do not "
        "exist anywhere in the repo (backend/content/ only has olympiad_v2/); "
        "every /olympiad/worksheets call returns 404 and /list returns 0")

# edge: invalid day
r = client.get("/olympiad/worksheets", params={"grade": 1, "day": 999})
row(TAB, "GET /olympiad/worksheets?grade=1&day=999 (edge)", r.status_code, "n/a", "-",
    "" if r.status_code in (404, 400, 422) else f"expected 4xx, got {r.status_code}")

# olympiad visual
if oly_visual_qid:
    r = client.get(f"/olympiad/questions/{oly_visual_qid}/visual")
    ok = r.status_code == 200 and r.text.lstrip().startswith("<svg")
    row(TAB, "GET /olympiad/questions/{id}/visual", r.status_code, "n/a",
        f"{len(r.text)}B" if ok else r.text[:60], "" if ok else "not <svg>")
else:
    row(TAB, "GET /olympiad/questions/{id}/visual", "-", "n/a", "-",
        "no worksheet question with visual found in sampled days")

# stats
r = client.get("/olympiad/stats")
row(TAB, "GET /olympiad/stats", r.status_code, "yes" if r.status_code == 200 else "NO",
    str(r.json())[:60] if r.status_code == 200 else "-", "")

# ── Wavebook ──
print("WAVEBOOK")
for g in (3, 4, 5, 6):
    r = client.get("/wavebook/topics", params={"grade": g})
    errs, names = [], []
    if r.status_code == 200:
        topics = (r.json() or {}).get("topics") or []
        for t in topics:
            if not isinstance(t.get("topic"), str):
                errs.append("topic entry missing 'topic' str (wavebook_screen.dart:341 crashes)")
            else:
                names.append(t["topic"])
        if not topics:
            errs.append("0 topics")
    else:
        errs.append(r.text[:100])
    row(TAB, f"GET /wavebook/topics?grade={g}", r.status_code,
        "yes" if not errs else "NO", f"{len(names)} topics", "; ".join(errs[:2]))

# wavebook questions + download for one topic
r = client.get("/wavebook/topics", params={"grade": 3})
first_topic = None
if r.status_code == 200 and (r.json() or {}).get("topics"):
    first_topic = r.json()["topics"][0]["topic"]
if first_topic:
    r = client.get("/wavebook/questions", params={"grade": 3, "topic": first_topic})
    errs, n = [], 0
    if r.status_code == 200:
        qs = (r.json() or {}).get("questions") or []
        n = len(qs)
        for q in qs[:5]:
            if not q.get("stem"):
                errs.append("question missing stem")
            if not q.get("choices"):
                errs.append("question missing choices")
            if "correct_answer" not in q:
                errs.append("question missing correct_answer")
        if n == 0:
            errs.append("0 questions")
    else:
        errs.append(r.text[:100])
    row(TAB, f"GET /wavebook/questions (topic='{first_topic[:25]}')", r.status_code,
        "yes" if not errs else "NO", f"{n} questions", "; ".join(errs[:3]))

    r = client.get("/wavebook/download", params={"grade": 3, "topic": first_topic})
    row(TAB, "GET /wavebook/download", r.status_code,
        "yes" if r.status_code == 200 else "NO",
        f"{len(r.content)}B", "" if r.status_code == 200 else r.text[:100])

# wavebook invalid grade (edge — app only shows G3+, but guard anyway)
r = client.get("/wavebook/topics", params={"grade": 1})
row(TAB, "GET /wavebook/topics?grade=1 (edge)", r.status_code, "n/a",
    str(r.json())[:50] if r.status_code == 200 else "-",
    "" if r.status_code in (200, 400, 404, 422) else "unexpected")

# ── Pillars (olympiad v2, pillar_api.dart) ──
print("PILLARS (olympiad v2)")
pillar_q = None
for g in (1, 3, 6):
    r = client.get("/olympiad/v2/pillars", params={"grade": g})
    errs, n = [], 0
    if r.status_code == 200:
        ps = (r.json() or {}).get("pillars")
        if ps is None:
            errs.append("'pillars' key missing (pillar_api.dart:24 crashes)")
        else:
            n = len(ps)
    else:
        errs.append(r.text[:100])
    row(TAB, f"GET /olympiad/v2/pillars?grade={g}", r.status_code,
        "yes" if not errs else "NO", f"{n} pillars", "; ".join(errs[:2]))

r = client.get("/olympiad/v2/levels", params={"pillar": "algebra", "grade": 3})
levels = (r.json() or {}).get("levels") if r.status_code == 200 else None
row(TAB, "GET /olympiad/v2/levels?pillar=algebra&grade=3", r.status_code,
    "yes" if isinstance(levels, list) else "NO",
    f"{len(levels) if isinstance(levels, list) else 0} levels",
    "" if isinstance(levels, list) else r.text[:100])

r = client.get("/olympiad/v2/topics", params={"pillar": "algebra", "level": 1})
ptopics = (r.json() or {}).get("topics") if r.status_code == 200 else None
row(TAB, "GET /olympiad/v2/topics?pillar=algebra&level=1", r.status_code,
    "yes" if isinstance(ptopics, list) else "NO",
    f"{len(ptopics) if isinstance(ptopics, list) else 0} topics",
    "" if isinstance(ptopics, list) else r.text[:100])

if ptopics:
    tname = ptopics[0].get("id") or ptopics[0].get("topic") or ptopics[0].get("name")
    r = client.get("/olympiad/v2/worksheet",
                   params={"pillar": "algebra", "level": 1, "topic": tname})
    errs, n = [], 0
    if r.status_code == 200:
        qs = (r.json() or {}).get("questions") or []
        n = len(qs)
        for q in qs[:5]:
            validate_olympiad_question(q, errs)
        if qs:
            pillar_q = qs[0]
    else:
        errs.append(r.text[:100])
    row(TAB, f"GET /olympiad/v2/worksheet (topic={str(tname)[:20]})", r.status_code,
        "yes" if not errs else "NO", f"{n} questions", "; ".join(errs[:2]))

if pillar_q:
    r = client.post("/olympiad/v2/submit",
                    json={"user_id": UID, "question_id": pillar_q["id"],
                          "answer": 0, "time_taken_seconds": 12})
    row(TAB, "POST /olympiad/v2/submit", r.status_code,
        "yes" if r.status_code == 200 else "NO",
        str(r.json())[:60] if r.status_code == 200 else r.text[:100], "")

r = client.get("/olympiad/v2/progress", params={"user_id": UID})
row(TAB, "GET /olympiad/v2/progress", r.status_code,
    "yes" if r.status_code == 200 else "NO",
    str(list((r.json() or {}).keys()))[:60] if r.status_code == 200 else "-",
    "" if r.status_code == 200 else r.text[:100])

r = client.get("/olympiad/v2/daily-challenge", params={"grade": 3})
errs = []
if r.status_code == 200:
    qq = (r.json() or {}).get("question")
    if not isinstance(qq, dict):
        errs.append("'question' missing (pillar_api.dart:144 crashes)")
    else:
        validate_olympiad_question(qq, errs)
row(TAB, "GET /olympiad/v2/daily-challenge?grade=3", r.status_code,
    "yes" if not errs and r.status_code in (200, 404) else "NO", "-",
    "; ".join(errs[:2]) or ("" if r.status_code in (200, 404) else r.text[:100]))

# ════════════════════════════════════════════════════════════════════════════
# TAB: SCHOOL (curriculum_screen.dart: cambridge/ncert/singapore/icse)
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("SCHOOL TAB")
TAB = "School"
CURRICULA = ["cambridge", "ncert", "singapore", "icse", "uscc"]  # uscc kept for impact check
school_summary = {}
for cur in CURRICULA:
    shown = 0
    loaded = 0
    empty_chapters = []
    statuses = defaultdict(int)
    for g in range(1, 7):
        r = client.get("/v2/chapters", params={"curriculum": cur, "grade": g})
        if r.status_code != 200:
            statuses[r.status_code] += 1
            continue
        chapters = r.json()
        shown += len(chapters)
        for ch in chapters:
            chname = ch.get("name") or ch.get("title") or ""
            rq = client.get("/v2/questions/next",
                            params={"user_id": UID, "grade": g, "chapter": chname,
                                    "curriculum": cur, "window": 10})
            if rq.status_code == 200 and rq.json().get("question_id"):
                loaded += 1
            else:
                empty_chapters.append(f"g{g}:{chname[:30]}")
    school_summary[cur] = (shown, loaded, empty_chapters)
    pct = f"{loaded}/{shown}" if shown else "0/0"
    row(TAB, f"{cur}: chapters x G1-6 + first question", "200",
        "yes" if shown and loaded else "NO",
        f"{shown} chapters shown, {loaded} load questions",
        ("empty: " + "; ".join(empty_chapters[:4]) + ("..." if len(empty_chapters) > 4 else ""))
        if empty_chapters else "")

# aggregate school check
total_shown = sum(s for s, _, _ in school_summary.values())
if total_shown < 30:
    bug("CRITICAL", "School tab nearly empty — curriculum content missing from content-live/content-v2",
        "curriculum_screen.dart:63 calls GET /v2/chapters which derives chapters from "
        "questions loaded into store_v2. On-disk live curriculum content: ncert 11 q, "
        "icse 5 q, igcse 58 q, singapore 325 q (ALL 325 fail QuestionV2 validation: "
        "id 'SING-G1-SMC-021' rejected by content_store_v2.py:148 regex + "
        "correct_answer is letter 'B' not int), us-common-core dir absent. "
        "The full school banks (19,919 q incl. Cambridge 3,600/NCERT 4,373/Singapore "
        "1,200/USCC 1,200) live in content-v4 and are served by /v4/school/* — but the "
        "app's School tab never calls v4 endpoints")

# edge: bogus curriculum
r = client.get("/v2/chapters", params={"curriculum": "hogwarts", "grade": 1})
row(TAB, "GET /v2/chapters?curriculum=hogwarts (edge)", r.status_code, "n/a",
    len(r.json()) if r.status_code == 200 else "-", "")

# ── v4 school (where the real curriculum content lives; app has client methods
#    getCurriculaV4/getChaptersV4 but curriculum_screen.dart never calls them) ──
v4_school = {}
v4_500 = 0
for g in range(1, 7):
    r = client.get(f"/v4/school/curricula/{g}")
    if r.status_code != 200:
        continue
    for cur in r.json().get("curricula", []):
        rc = client.get(f"/v4/school/{cur}/{g}")
        if rc.status_code != 200:
            continue
        chapters = rc.json()
        shown, loaded = 0, 0
        for ch in chapters:
            shown += 1
            ch_id = ch.get("chapter_id") or ch.get("id") or ch.get("name")
            rq = client.get(f"/v4/school/{cur}/{g}/{ch_id}")
            if rq.status_code == 500:
                v4_500 += 1
            elif rq.status_code == 200 and (rq.json().get("questions") or []):
                loaded += 1
        s0, l0 = v4_school.get(cur, (0, 0))
        v4_school[cur] = (s0 + shown, l0 + loaded)
for cur, (shown, loaded) in sorted(v4_school.items()):
    row(TAB, f"v4 school '{cur}' chapters G1-6 (NOT wired in app)", "200",
        "yes" if loaded else "NO", f"{shown} chapters, {loaded} with questions",
        "" if loaded == shown else f"{shown-loaded} chapters resolve to 0 questions")
if v4_500:
    bug("HIGH", f"/v4/school/{{cur}}/{{grade}}/{{chapter}} 500s on every chapter "
        f"({v4_500} chapters tested)",
        "questions_v4.py:238 serializes q.options but content_store_v4 QuestionV2 "
        "has 'choices', no 'options' attribute -> AttributeError -> 500. This is the "
        "ONLY endpoint exposing the 19,919-question school bank's chapter questions")

# ════════════════════════════════════════════════════════════════════════════
# TAB: CLAN
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("CLAN TAB")
TAB = "Clan"

LEADER = f"qa_leader_{uuid.uuid4().hex[:6]}"
MEMBER = f"qa_member_{uuid.uuid4().hex[:6]}"
clan_id, invite = None, None

r = client.post("/v4/clans", json={"name": "QA Kiwis", "grade": 3,
                                   "leader_uid": LEADER, "parent_uid": LEADER,
                                   "crest_shape": "bolt", "crest_color": "#FF6D00"})
errs = []
if r.status_code in (200, 201):
    j = r.json()
    clan_id = j.get("clan_id")
    invite = j.get("invite_code")
    if not clan_id:
        errs.append("no clan_id in create response")
    if not j.get("clan_level"):
        errs.append("no clan_level object")
else:
    errs.append(r.text[:150])
row(TAB, "POST /v4/clans (create)", r.status_code, "yes" if not errs else "NO",
    clan_id or "-", "; ".join(errs[:2]))

if clan_id:
    r = client.post("/v4/clans/join", json={"invite_code": invite, "uid": MEMBER,
                                            "parent_uid": MEMBER, "grade": 3})
    row(TAB, "POST /v4/clans/join", r.status_code,
        "yes" if r.status_code == 200 else "NO",
        (r.json().get("member_count") if r.status_code == 200 else "-"),
        "" if r.status_code == 200 else r.text[:120])

    r = client.get("/v4/clans/mine", params={"user_uid": LEADER})
    row(TAB, "GET /v4/clans/mine", r.status_code, "yes" if r.status_code == 200 else "NO",
        (r.json().get("clan_id") if r.status_code == 200 else "-"),
        "" if r.status_code == 200 else r.text[:120])

    r = client.get(f"/v4/clans/{clan_id}", params={"user_uid": LEADER})
    row(TAB, "GET /v4/clans/{id}", r.status_code, "yes" if r.status_code == 200 else "NO",
        "-", "" if r.status_code == 200 else r.text[:120])

    r = client.get("/v4/clans/leaderboard/3", params={"limit": 20})
    errs, n = [], 0
    if r.status_code == 200:
        lb = r.json()
        if not isinstance(lb, list):
            errs.append("leaderboard not a JSON list (Dart `as List` crashes)")
        else:
            n = len(lb)
    else:
        errs.append(r.text[:100])
    row(TAB, "GET /v4/clans/leaderboard/3", r.status_code,
        "yes" if not errs else "NO", f"{n} entries", "; ".join(errs[:2]))

    r = client.post(f"/v4/clans/{clan_id}/react", json={"uid": MEMBER, "emoji": "fire"})
    row(TAB, "POST /v4/clans/{id}/react (token 'fire')", r.status_code,
        "yes" if r.status_code == 200 else "NO", "-",
        "" if r.status_code == 200 else r.text[:120])
    r = client.post(f"/v4/clans/{clan_id}/react", json={"uid": MEMBER, "emoji": "🎉"})
    row(TAB, "POST /v4/clans/{id}/react (raw emoji, edge)", r.status_code, "n/a", "-",
        "backend accepts only token names {brain,star,muscle,fire,high_five} — "
        "any UI sending a literal emoji char gets 400" if r.status_code == 400 else "")

    r = client.post(f"/v4/clans/{clan_id}/invite", params={"uid": LEADER})
    row(TAB, "POST /v4/clans/{id}/invite (regen)", r.status_code,
        "yes" if r.status_code == 200 else "NO",
        (r.json().get("invite_code", "-") if r.status_code == 200 else "-"),
        "" if r.status_code == 200 else r.text[:120])

# active challenge → progress → guess → answer
r = client.get("/v4/challenges/active", params={"grade": 3})
ch_id = None
if r.status_code == 200 and r.json().get("status") != "none":
    ch_id = r.json().get("challenge_id")
row(TAB, "GET /v4/challenges/active?grade=3", r.status_code,
    "yes" if r.status_code in (200, 404) else "NO", ch_id or "none",
    "" if r.status_code in (200, 404) else r.text[:120])

if ch_id and clan_id:
    r = client.get(f"/v4/challenges/{ch_id}/progress/{clan_id}")
    row(TAB, "GET /v4/challenges/{id}/progress/{clan}", r.status_code,
        "yes" if r.status_code == 200 else "NO",
        (f"{r.json().get('blocks_revealed')}/{r.json().get('total_blocks')} blocks"
         if r.status_code == 200 else "-"),
        "" if r.status_code == 200 else r.text[:120])

    r = client.post(f"/v4/challenges/{ch_id}/guess",
                    json={"clan_id": clan_id, "uid": MEMBER, "guess_text": "a star map"})
    row(TAB, "POST /v4/challenges/{id}/guess", r.status_code,
        "yes" if r.status_code == 200 else "NO", "-",
        "" if r.status_code == 200 else r.text[:120])

    r = client.get(f"/v4/challenges/{ch_id}/guesses/{clan_id}")
    n = len(r.json()) if r.status_code == 200 and isinstance(r.json(), list) else 0
    row(TAB, "GET /v4/challenges/{id}/guesses/{clan}", r.status_code,
        "yes" if r.status_code == 200 else "NO", f"{n} guesses",
        "" if r.status_code == 200 else r.text[:120])

    r = client.post(f"/v4/challenges/{ch_id}/answer",
                    json={"clan_id": clan_id, "uid": LEADER, "answer": "test answer"})
    row(TAB, "POST /v4/challenges/{id}/answer", r.status_code,
        "yes" if r.status_code in (200, 400, 403) else "NO", "-",
        "" if r.status_code in (200, 400, 403) else r.text[:120])

# ── Daily puzzle (engagement_service.dart + daily_puzzle_screen) ──
puzzle = None
r = client.get("/v4/daily-puzzle", params={"grade": 3})
errs = []
if r.status_code == 200:
    puzzle = r.json()
    # Dart DailyPuzzle reads hint1/hint2 (engagement.dart:57-58) — check both spellings
    if "hint1" not in puzzle and "hint_1" in puzzle:
        errs.append("backend sends 'hint_1'/'hint_2' but Dart reads json['hint1']/['hint2'] "
                    "→ hints always empty in app (engagement.dart:57)")
        bug("MEDIUM", "Daily puzzle hint field name mismatch",
            "backend daily_puzzle.py DailyPuzzleResponse uses hint_1/hint_2; "
            "app/lib/models/engagement.dart:57-58 parses json['hint1']/json['hint2'] → hints lost")
    if not puzzle.get("puzzle_id"):
        errs.append("missing puzzle_id")
    if "is_active" not in puzzle:
        errs.append("missing is_active (Dart defaults false → puzzle may show as closed)")
elif r.status_code == 404:
    errs.append("no puzzle today (pool may not cover this date)")
else:
    errs.append(r.text[:120])
row(TAB, "GET /v4/daily-puzzle?grade=3", r.status_code,
    "yes" if not errs else "PARTIAL", puzzle.get("puzzle_id") if puzzle else "-",
    "; ".join(errs[:3]))

if puzzle:
    idem = str(uuid.uuid4())
    body = {"uid": UID, "puzzle_id": puzzle["puzzle_id"],
            "answer": (puzzle.get("options") or ["42"])[0], "time_taken_seconds": 30}
    r1 = client.post("/v4/daily-puzzle/submit", json=body, headers={"X-Idempotency-Key": idem})
    errs = []
    if r1.status_code == 200:
        j = r1.json()
        # daily_puzzle_screen expects result.correct + result.pointsEarned
        if "correct" not in j:
            errs.append("missing 'correct'")
        if "points_earned" not in j:
            errs.append("missing 'points_earned'")
    else:
        errs.append(r1.text[:150])
    row(TAB, "POST /v4/daily-puzzle/submit", r1.status_code,
        "yes" if not errs else "NO",
        (f"correct={r1.json().get('correct')} pts={r1.json().get('points_earned')}"
         if r1.status_code == 200 else "-"),
        "; ".join(errs[:3]))

    # double submit → must replay same result
    r2 = client.post("/v4/daily-puzzle/submit", json=body, headers={"X-Idempotency-Key": idem})
    same = (r2.status_code == 200 and r1.status_code == 200 and
            r2.json().get("points_earned") == r1.json().get("points_earned") and
            r2.json().get("correct") == r1.json().get("correct"))
    row(TAB, "POST /v4/daily-puzzle/submit (double)", r2.status_code, "n/a",
        "replayed" if same else "DIFFERENT",
        "" if same else "double-submit not deduped")
    if not same:
        bug("HIGH", "Daily puzzle double-submit not idempotent",
            f"first: {str(r1.json())[:120]} second: {str(r2.json())[:120]}")

r = client.get("/v4/daily-puzzle/leaderboard", params={"grade": 3, "period": "daily"})
ok = r.status_code == 200 and isinstance(r.json(), list)
row(TAB, "GET /v4/daily-puzzle/leaderboard", r.status_code, "yes" if ok else "NO",
    len(r.json()) if ok else "-",
    "" if ok else "Dart expects JSON list (engagement_service.dart:132)")

r = client.get(f"/v4/streaks/{UID}")
row(TAB, "GET /v4/streaks/{uid}", r.status_code,
    "yes" if r.status_code in (200, 404) else "NO",
    (f"streak={r.json().get('current_streak')}" if r.status_code == 200 else "-"),
    "" if r.status_code in (200, 404) else r.text[:100])

r = client.get("/v4/leagues/status", params={"uid": UID})
row(TAB, "GET /v4/leagues/status", r.status_code,
    "yes" if r.status_code in (200, 404) else "NO",
    (r.json().get("league") if r.status_code == 200 else "-"),
    "" if r.status_code in (200, 404) else r.text[:100])

r = client.get("/v4/clan-wars/current", params={"clan_id": clan_id or "none"})
row(TAB, "GET /v4/clan-wars/current", r.status_code,
    "yes" if r.status_code in (200, 404) else "NO",
    (r.json().get("war_id", "-") if r.status_code == 200 else "-"),
    "" if r.status_code in (200, 404) else r.text[:120])

r = client.get(f"/v4/rewards/{UID}")
errs = []
if r.status_code == 200:
    j = r.json()
    for k in ("stickers_collected", "mystery_boxes_available", "daily_calendar", "total_gems"):
        if k not in j:
            errs.append(f"missing '{k}'")
elif r.status_code != 404:
    errs.append(r.text[:100])
row(TAB, "GET /v4/rewards/{uid}", r.status_code, "yes" if not errs else "NO",
    (f"gems={r.json().get('total_gems')}" if r.status_code == 200 else "-"),
    "; ".join(errs[:3]))

r = client.post(f"/v4/rewards/{UID}/claim-daily")
row(TAB, "POST /v4/rewards/{uid}/claim-daily", r.status_code,
    "yes" if r.status_code in (200, 400, 409) else "NO",
    str(r.json())[:50] if r.status_code == 200 else "-",
    "" if r.status_code in (200, 400, 409) else r.text[:100])
if r.status_code == 404:
    bug("LOW", "claim-daily 404s for brand-new users",
        "POST /v4/rewards/{uid}/claim-daily returns 404 'Reward data not found' before "
        "the user has any reward state; engagement_service.dart:298 throws ApiException "
        "on non-200 — main.dart:623 claim flow shows an error for day-1 users")

r = client.post(f"/v4/pledges/{UID}", json={"target_puzzles": 5})
row(TAB, "POST /v4/pledges/{uid}", r.status_code,
    "yes" if r.status_code in (200, 201) else "NO", "-",
    "" if r.status_code in (200, 201) else r.text[:100])

if clan_id:
    r = client.get(f"/v4/pledges/clan/{clan_id}")
    ok = r.status_code == 200 and isinstance(r.json(), list)
    row(TAB, "GET /v4/pledges/clan/{id}", r.status_code, "yes" if ok else "NO",
        len(r.json()) if ok else "-",
        "" if ok else f"Dart casts body `as List` but got: {r.text[:60]}")
    if r.status_code == 200 and isinstance(r.json(), dict):
        bug("HIGH", "Clan pledges response shape mismatch — Dart cast crashes",
            "engagement.py:750 GET /v4/pledges/clan/{id} returns an object "
            '{"clan_id":..., "pledges":[...]} but engagement_service.dart:345 does '
            "`jsonDecode(res.body) as List<dynamic>` -> TypeError; called from "
            "main.dart:334 on clan load")

# ════════════════════════════════════════════════════════════════════════════
# TAB: GROWTH
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("GROWTH TAB")
TAB = "Growth"

# benchmark create + submit roundtrip first (so growth has data)
r = client.post("/v2/benchmark/create",
                params={"user_id": UID, "grade": 3, "benchmark_type": "diagnostic"})
test_id, bm_questions = None, []
errs = []
if r.status_code == 200:
    j = r.json()
    test_id = j.get("test_id")
    bm_questions = j.get("questions") or []
    if len(bm_questions) != 20:
        errs.append(f"expected 20 questions, got {len(bm_questions)}")
    # grade filtering: question grades should be in {2,3} (G-1 + G)
    bad_grade = [q for q in bm_questions
                 if q.get("grade") not in (None, 2, 3)]
    if bad_grade:
        errs.append(f"{len(bad_grade)} questions outside grade 2-3 filter")
else:
    errs.append(r.text[:150])
row(TAB, "POST /v2/benchmark/create (g3)", r.status_code,
    "yes" if not errs else "NO", f"{len(bm_questions)} questions", "; ".join(errs[:3]))
if r.status_code == 200 and 0 < len(bm_questions) < 20:
    bug("MEDIUM", f"Benchmark test short: {len(bm_questions)}/20 questions (grade 3)",
        "benchmark_test.py blueprint cannot fill all 20 slots from the grade-filtered "
        "pool in content-live (grade 2-3 core content gaps after filtering)")

if test_id and bm_questions:
    responses = [{"question_id": q.get("question_id") or q.get("id"),
                  "selected_answer": 0, "time_taken_ms": 8000}
                 for q in bm_questions]
    r = client.post("/v2/benchmark/submit",
                    json={"user_id": UID, "test_id": test_id, "responses": responses})
    errs = []
    bench_result = {}
    if r.status_code == 200:
        bench_result = r.json()
        for k in ("scale_score", "proficiency_level", "theta"):
            if k not in str(bench_result):
                errs.append(f"result missing '{k}'?")
    else:
        errs.append(r.text[:200])
    row(TAB, "POST /v2/benchmark/submit", r.status_code,
        "yes" if not errs else "NO", str(bench_result)[:60], "; ".join(errs[:2]))

r = client.get("/v2/benchmark/history", params={"user_id": UID})
row(TAB, "GET /v2/benchmark/history", r.status_code,
    "yes" if r.status_code == 200 else "NO", "-",
    "" if r.status_code == 200 else r.text[:100])

# proficiency
r = client.get("/v2/proficiency", params={"user_id": UID, "grade": 3})
row(TAB, "GET /v2/proficiency", r.status_code, "yes" if r.status_code == 200 else "NO",
    str(list((r.json() or {}).keys()))[:60] if r.status_code == 200 else "-",
    "" if r.status_code == 200 else r.text[:120])

r = client.get("/v2/proficiency/levels")
row(TAB, "GET /v2/proficiency/levels", r.status_code,
    "yes" if r.status_code == 200 else "NO", "-",
    "" if r.status_code == 200 else r.text[:100])

# growth endpoints (growth_service.dart)
r = client.get("/growth/has-diagnostic", params={"user_id": UID})
has_diag = r.status_code == 200 and (r.json() or {}).get("has_diagnostic")
row(TAB, "GET /growth/has-diagnostic", r.status_code,
    "yes" if r.status_code == 200 else "NO", str(has_diag), "")

# save a baseline explicitly (mirrors benchmark flow in app)
r = client.post("/growth/diagnostic/save-baseline",
                json={"user_id": UID, "grade": 3, "benchmark_id": test_id or "qa",
                      "theta": 0.2, "per_topic_theta": {"topic-2-arithmetic": 0.3}})
row(TAB, "POST /growth/diagnostic/save-baseline", r.status_code,
    "yes" if r.status_code == 200 else "NO", "-",
    "" if r.status_code == 200 else r.text[:120])

r = client.get("/growth/journey", params={"user_id": UID, "grade": 3})
errs = []
if r.status_code == 200:
    j = r.json()
    if not isinstance(j.get("current"), dict):
        errs.append("'current' missing/not-map — GrowthJourney.fromJson CRASHES (growth.dart:33)")
        bug("HIGH", "/growth/journey 'current' missing",
            f"response keys: {list(j.keys())}; growth.dart:33 does json['current'] as Map (non-null)")
elif r.status_code == 404:
    pass  # Dart returns null — OK
else:
    errs.append(r.text[:120])
row(TAB, "GET /growth/journey", r.status_code,
    "yes" if not errs and r.status_code in (200, 404) else "NO",
    str(list((r.json() or {}).keys()))[:60] if r.status_code == 200 else "-",
    "; ".join(errs[:2]))

r = client.get("/growth/topics", params={"user_id": UID, "grade": 3})
errs = []
if r.status_code == 200:
    if not isinstance((r.json() or {}).get("topics"), list):
        errs.append("'topics' missing — growth_service.dart:97 `as List` crashes")
else:
    errs.append(r.text[:120])
row(TAB, "GET /growth/topics", r.status_code, "yes" if not errs else "NO",
    len((r.json() or {}).get("topics", [])) if r.status_code == 200 else "-",
    "; ".join(errs[:2]))

r = client.get("/growth/timeline", params={"user_id": UID})
row(TAB, "GET /growth/timeline", r.status_code, "yes" if r.status_code == 200 else "NO",
    len((r.json() or {}).get("snapshots", [])) if r.status_code == 200 else "-",
    "" if r.status_code == 200 else r.text[:100])

r = client.get("/growth/milestones", params={"user_id": UID, "grade": 3})
errs = []
if r.status_code == 200:
    if not isinstance((r.json() or {}).get("milestones"), list):
        errs.append("'milestones' missing — growth_service.dart:146 `as List` crashes")
else:
    errs.append(r.text[:120])
row(TAB, "GET /growth/milestones", r.status_code, "yes" if not errs else "NO",
    len((r.json() or {}).get("milestones", [])) if r.status_code == 200 else "-",
    "; ".join(errs[:2]))

# learning path (growth tab "what's next")
r = client.get("/v2/learning-path", params={"user_id": UID, "grade": 3})
row(TAB, "GET /v2/learning-path", r.status_code, "yes" if r.status_code == 200 else "NO",
    "-", "" if r.status_code == 200 else r.text[:120])

# onboarding benchmark (diagnostic entry point)
r = client.get("/v2/onboarding/benchmark/questions", params={"grade": 3, "count": 10})
errs, n = [], 0
if r.status_code == 200:
    qs = r.json()
    n = len(qs)
    for q in qs[:5]:
        validate_question_v2(q, errs)
else:
    errs.append(r.text[:120])
row(TAB, "GET /v2/onboarding/benchmark/questions", r.status_code,
    "yes" if not errs else "NO", f"{n} questions", "; ".join(errs[:3]))

# ════════════════════════════════════════════════════════════════════════════
# TAB: PARENT
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("PARENT TAB")
TAB = "Parent"
r = client.get("/v2/parent/dashboard", params={"user_id": UID})
errs = []
if r.status_code == 200:
    j = r.json()
    # parent_dashboard_screen.dart:159-179 — all defaulted, but verify shape
    for k in ("overall_accuracy", "total_questions", "topics"):
        if k not in j:
            errs.append(f"missing '{k}'")
    if not isinstance(j.get("topics", []), list):
        errs.append("'topics' not a list")
else:
    errs.append(r.text[:150])
row(TAB, "GET /v2/parent/dashboard", r.status_code, "yes" if not errs else "NO",
    f"{len((r.json() or {}).get('topics', []))} topics" if r.status_code == 200 else "-",
    "; ".join(errs[:3]))

r = client.get("/v2/parent/weekly-report", params={"user_id": UID})
row(TAB, "GET /v2/parent/weekly-report", r.status_code,
    "yes" if r.status_code == 200 else "NO", "-",
    "" if r.status_code == 200 else r.text[:120])

# ════════════════════════════════════════════════════════════════════════════
# TAB: PROFILE (gamification / economy / companion)
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("PROFILE TAB")
TAB = "Profile"

r = client.get("/user/profile", params={"user_id": UID})
errs = []
if r.status_code == 200:
    j = r.json()
    for k in ("xp_total", "kiwi_coins", "streak_current"):
        if k not in j:
            errs.append(f"missing '{k}'")
    if "gems" not in j and "mastery_gems" not in j:
        errs.append("neither 'gems' nor 'mastery_gems' present (user_profile.dart:75)")
else:
    errs.append(r.text[:150])
row(TAB, "GET /user/profile", r.status_code, "yes" if not errs else "NO",
    (f"xp={j.get('xp_total')} coins={j.get('kiwi_coins')}" if r.status_code == 200 else "-"),
    "; ".join(errs[:3]))

r = client.get("/companion/config",
               params={"chosen_primary": "kiwi", "age_tier": "k2", "app_version": 1})
row(TAB, "GET /companion/config", r.status_code, "yes" if r.status_code == 200 else "NO",
    "-", "" if r.status_code == 200 else r.text[:100])

r = client.get("/companion/cast", params={"app_version": 1})
row(TAB, "GET /companion/cast", r.status_code, "yes" if r.status_code == 200 else "NO",
    "-", "" if r.status_code == 200 else r.text[:100])

r = client.post("/v2/student/profile", params={"user_id": UID},
                json={"child_name": "QA Kid", "grade": 3, "curriculum": "ncert"})
row(TAB, "POST /v2/student/profile", r.status_code,
    "yes" if r.status_code == 200 else "NO", "-",
    "" if r.status_code == 200 else r.text[:120])

# ════════════════════════════════════════════════════════════════════════════
# AUTH POSTURE (static note — not live-tested; routers carry user_auth deps)
# ════════════════════════════════════════════════════════════════════════════
row("Auth", "router auth deps (static check)", "-", "n/a", "-",
    "All user routers include user_auth dependency (app/main.py:104-122); "
    "live auth not tested because KIWIMATH_AUTH_DISABLED=1 is process-wide")

# ════════════════════════════════════════════════════════════════════════════
# REPORT
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("PER-TAB RESULTS")
cur_tab = None
for tab, ep, status, parses, content, issues in ROWS:
    if tab != cur_tab:
        print(f"\n--- {tab} ---")
        cur_tab = tab
    flag = "" if parses in ("yes", "n/a") and not issues else "  <<<"
    print(f"  [{status:>5}] parse:{parses:<7} {ep:<58} {content:<28} {issues}{flag}")

print("\n" + "=" * 78)
print("SCHOOL TAB CONTENT SUMMARY (what a child sees)")
for cur, (shown, loaded, empty) in school_summary.items():
    print(f"  {cur:<10} chapters shown: {shown:>3}  load questions: {loaded:>3}  "
          f"empty: {len(empty):>3}")
    for e in empty[:10]:
        print(f"      - {e}")
    if len(empty) > 10:
        print(f"      ... and {len(empty)-10} more")

print("\n" + "=" * 78)
print("BUGS (ranked)")
order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
for sev, title, ev in sorted(BUGS, key=lambda b: order.get(b[0], 9)):
    print(f"  [{sev}] {title}\n      {ev}")
if not BUGS:
    print("  none recorded by automated checks")

fails = [r for r in ROWS if r[3] == "NO" or (r[5] and r[3] != "n/a")]
print(f"\nTOTAL: {len(ROWS)} checks, {len(fails)} with issues, {len(BUGS)} bugs flagged")
