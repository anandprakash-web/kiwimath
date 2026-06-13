#!/usr/bin/env python3
"""
Validate regenerated olympiad worksheet batches against the schema required by
backend/app/api/olympiad.py and app/lib/models/olympiad_worksheet.dart, then
boot the backend with TestClient and exercise the live endpoints.

Run from anywhere:  python3 backend/content/olympiad/_validate_worksheets.py
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BANK = os.path.join(REPO, "content-live", "content-v2")

ERRORS = []
def err(msg):
    ERRORS.append(msg)
    if len(ERRORS) <= 30:
        print("  ERROR:", msg)

VALID_TIERS = {"warmup", "practice", "challenge"}
VALID_MODES = {"mcq", "integer"}

# ── source answer index for verbatim-answer check ────────────────────────────
import glob
src = {}
for p in glob.glob(os.path.join(BANK, "topic-*", "*.json")):
    d = json.load(open(p))
    for q in (d if isinstance(d, list) else d.get("questions", [])):
        src[q["id"]] = q

svg_store = json.load(open(os.path.join(HERE, "svg_components", "svg_store.json")))

# ── file-level validation ────────────────────────────────────────────────────
total_ws, total_q = 0, 0
for grade in range(1, 7):
    days_seen = set()
    grade_q_usage = Counter()
    for batch in range(1, 6):
        path = os.path.join(HERE, f"g{grade}_olympiad_batch{batch}.json")
        if not os.path.exists(path):
            err(f"missing file g{grade}_olympiad_batch{batch}.json")
            continue
        data = json.load(open(path))  # raises if unparseable
        if not isinstance(data, list) or len(data) != 20:
            err(f"g{grade} batch{batch}: expected list of 20 worksheets, got {len(data)}")
        for ws in data:
            total_ws += 1
            for key, typ in (("grade", int), ("day", int), ("title", str),
                             ("subtitle", str), ("dominant_topic", str),
                             ("difficulty_distribution", dict), ("questions", list)):
                if not isinstance(ws.get(key), typ):
                    err(f"g{grade} d{ws.get('day')}: bad worksheet field {key}")
            if ws["grade"] != grade:
                err(f"g{grade} batch{batch}: grade mismatch {ws['grade']}")
            if ws["day"] in days_seen:
                err(f"g{grade}: duplicate day {ws['day']}")
            days_seen.add(ws["day"])

            qs = ws["questions"]
            if len(qs) != 12:
                err(f"g{grade} d{ws['day']}: {len(qs)} questions (want 12)")
            ids_in_ws = set()
            dist = Counter()
            for i, q in enumerate(qs):
                total_q += 1
                # Dart non-nullable / required
                if not isinstance(q.get("id"), str) or not q["id"]:
                    err(f"g{grade} d{ws['day']} q{i}: bad id"); continue
                qid = q["id"]
                if qid in ids_in_ws:
                    err(f"g{grade} d{ws['day']}: duplicate question {qid} in worksheet")
                ids_in_ws.add(qid)
                grade_q_usage[qid] += 1
                if not isinstance(q.get("stem"), str) or not q["stem"].strip():
                    err(f"{qid}: bad stem")
                if q.get("interaction_mode") not in VALID_MODES:
                    err(f"{qid}: bad interaction_mode {q.get('interaction_mode')}")
                if not isinstance(q.get("topic"), str) or not q["topic"]:
                    err(f"{qid}: bad topic")
                if q.get("difficulty_tier") not in VALID_TIERS:
                    err(f"{qid}: bad difficulty_tier {q.get('difficulty_tier')}")
                dist[q["difficulty_tier"]] += 1
                if q.get("question_number") != i + 1:
                    err(f"{qid}: question_number {q.get('question_number')} != {i+1}")
                ch = q.get("choices")
                if not isinstance(ch, list) or len(ch) < 2 or not all(isinstance(c, str) for c in ch):
                    err(f"{qid}: bad choices")
                ca = q.get("correct_answer")
                if not isinstance(ca, int) or isinstance(ca, bool) or not (0 <= ca < len(ch)):
                    err(f"{qid}: correct_answer {ca} out of range")
                if q["interaction_mode"] == "integer":
                    cv = q.get("correct_value")
                    if not isinstance(cv, int) or str(cv) != ch[ca]:
                        err(f"{qid}: integer correct_value {cv} != choice {ch[ca]}")
                if not isinstance(q.get("approach"), str) or "Answer:" not in q["approach"]:
                    err(f"{qid}: bad approach")
                hl = q.get("hint_ladder")
                if not isinstance(hl, dict) or not all(isinstance(v, str) for v in hl.values()):
                    err(f"{qid}: bad hint_ladder")
                vr = q.get("visual_ref")
                if vr is not None:
                    if not isinstance(vr, dict):  # Dart casts to Map<String,dynamic>
                        err(f"{qid}: visual_ref not an object")
                    elif vr.get("key") not in svg_store:
                        err(f"{qid}: visual_ref key missing from svg_store")
                    elif not isinstance(q.get("visual_alt"), str):
                        err(f"{qid}: visual with no visual_alt")
                # verbatim answer check vs QA-verified source
                s = src.get(qid)
                if s is None:
                    err(f"{qid}: not found in source bank")
                else:
                    if int(s["correct_answer"]) != ca or [str(c) for c in s["choices"]] != ch:
                        err(f"{qid}: answer/choices differ from source")
            if dist != Counter(ws["difficulty_distribution"]) - Counter():
                if dict(dist) != {k: v for k, v in ws["difficulty_distribution"].items() if v}:
                    err(f"g{grade} d{ws['day']}: difficulty_distribution {ws['difficulty_distribution']} != actual {dict(dist)}")
    if days_seen != set(range(1, 101)):
        err(f"g{grade}: days {len(days_seen)} != 1..100")
    reused = {k: v for k, v in grade_q_usage.items() if v > 1}
    if reused:
        err(f"g{grade}: {len(reused)} questions reused within grade")

print(f"\nStatic validation: {total_ws} worksheets, {total_q} questions, {len(ERRORS)} errors")
if ERRORS:
    sys.exit(1)

# ── live endpoint validation (TestClient boot, as in qa-reports) ─────────────
print("\nBooting backend with TestClient ...")
os.environ.setdefault("KIWIMATH_AUTH_DISABLED", "1")
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

import logging
for noisy in ("httpx", "kiwimath", "app", "uvicorn"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

from fastapi.testclient import TestClient
from app.main import app

fails = 0
with TestClient(app, raise_server_exceptions=False) as client:
    for g in range(1, 7):
        r = client.get(f"/olympiad/worksheets/list?grade={g}")
        ok = r.status_code == 200 and r.json().get("total_worksheets") == 100
        print(f"GET /olympiad/worksheets/list?grade={g} -> {r.status_code}, "
              f"total={r.json().get('total_worksheets') if r.status_code==200 else '-'} {'OK' if ok else 'FAIL'}")
        fails += 0 if ok else 1

    r = client.get("/olympiad/worksheets?grade=3&day=7")
    ws = r.json() if r.status_code == 200 else {}
    ok = (r.status_code == 200 and len(ws.get("questions", [])) == 12
          and ws.get("title") and ws.get("day") == 7)
    print(f"GET /olympiad/worksheets?grade=3&day=7 -> {r.status_code}, "
          f"title={ws.get('title')!r}, q={len(ws.get('questions', []))} {'OK' if ok else 'FAIL'}")
    fails += 0 if ok else 1

    # visual_url injection + visual endpoint
    vis_q = None
    for g in range(1, 7):
        for d in range(1, 101):
            w = client.get(f"/olympiad/worksheets?grade={g}&day={d}").json()
            for q in w["questions"]:
                if q.get("visual_ref"):
                    vis_q = q
                    break
            if vis_q:
                break
        if vis_q:
            break
    if vis_q is None:
        print("No visual question found FAIL"); fails += 1
    else:
        if not vis_q.get("visual_url"):
            print(f"{vis_q['id']}: visual_ref present but no visual_url FAIL"); fails += 1
        r = client.get(f"/olympiad/questions/{vis_q['id']}/visual")
        ok = r.status_code == 200 and r.text.lstrip().startswith("<svg") \
            and r.headers["content-type"].startswith("image/svg")
        print(f"GET /olympiad/questions/{vis_q['id']}/visual -> {r.status_code}, "
              f"{len(r.text)}B, svg={r.text.lstrip()[:5]!r} {'OK' if ok else 'FAIL'}")
        fails += 0 if ok else 1

    r = client.get("/olympiad/stats")
    ok = r.status_code == 200
    if ok:
        st = r.json()["stats"]
        for g in range(1, 7):
            s = st[f"grade_{g}"]
            line_ok = s["worksheets"] == 100 and s["total_questions"] == 1200
            print(f"stats grade_{g}: ws={s['worksheets']} q={s['total_questions']} "
                  f"visuals={s['questions_with_visuals']} modes={s['interaction_modes']} "
                  f"{'OK' if line_ok else 'FAIL'}")
            fails += 0 if line_ok else 1
    else:
        print(f"GET /olympiad/stats -> {r.status_code} FAIL"); fails += 1

print(f"\nLive endpoint validation: {'ALL PASS' if fails == 0 else f'{fails} FAILURES'}")
sys.exit(1 if fails else 0)
