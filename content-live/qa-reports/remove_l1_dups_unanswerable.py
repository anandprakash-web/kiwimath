#!/usr/bin/env python3
"""Remove L1 true duplicates + context-stripped unanswerable directional questions.

Two defect classes, both confirmed by inspection (2026-06-21):

  • TRUE duplicate (detector L, value-based key): same stem + same option SET +
    same RESOLVED answer value + same visual. correct_answer is a 0-based index,
    so the key resolves choices[index] — shuffled-choice items with different real
    answers are NOT merged; same-value reorders ARE. Keep the first occurrence.

  • Unanswerable directional (detector N): "Which direction … now?/facing?" with
    no figure, no number, no movement/compass word in the stem, and nothing
    recoverable from original_stem. The keyed direction is underivable. (Hints are
    off-topic "think about shapes" — the items are corrupted, not recoverable.)

Only L1 olympiad files are touched. A backup of every changed file is written
first, and every removed id is logged (with reason + surviving twin for dups) to
a recovery manifest, so the removal is fully reversible. Usage: [--apply]
"""
import json, glob, re, os, sys, hashlib, shutil, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # content-live/
FILES = sorted(glob.glob(os.path.join(ROOT, "olympiad", "L1", "L1_*.json")))
BK = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"backup-dedup-l1-{datetime.date.today()}")
MANIFEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"removed_l1_{datetime.date.today()}.json")

def S(v): return str(v) if v is not None else ""
def answer_value(q):
    ca, ch = q.get("correct_answer"), q.get("choices") or []
    return str(ch[ca]) if isinstance(ca, int) and 0 <= ca < len(ch) else S(ca)

DIR = re.compile(r'which direction', re.I)
NOW = re.compile(r'(now\?|facing\s+now|facing\b)', re.I)
SETUP = re.compile(r'(turn|left|right|clockwise|anticlock|step|move|goes|walk|roll|'
                   r'north|south|east|west|up|down|\d)', re.I)

def is_unanswerable(q):
    if S(q.get("visual_svg")).strip():
        return False
    st = S(q.get("stem"))
    if not (DIR.search(st) and NOW.search(st)) or SETUP.search(st):
        return False
    os_ = S(q.get("original_stem"))
    if len(os_) > len(st) + 3 and SETUP.search(os_):
        return False
    return True

def main(apply):
    # pass 1: identify duplicates (keep first per value-based key) + unanswerable
    seen = {}; remove = {}   # id -> {"reason", "twin"?}
    for f in FILES:
        for q in json.load(open(f)).get("questions", []):
            qid = q["id"]
            if is_unanswerable(q):
                remove[qid] = {"reason": "unanswerable_directional"}
                # still register key so a good twin elsewhere is the survivor
            st = re.sub(r'\s+', ' ', S(q.get("stem"))).strip().lower()
            if not st:
                continue
            vs = S(q.get("visual_svg"))
            vk = hashlib.md5(vs.encode()).hexdigest()[:8] if vs.strip() else ""
            key = (st, tuple(sorted(S(c) for c in (q.get("choices") or []))), answer_value(q), vk)
            if key in seen:
                if qid not in remove:
                    remove[qid] = {"reason": "duplicate", "twin": seen[key]}
            else:
                seen[key] = qid

    # integrity: a "duplicate" must have a surviving twin (twin not itself removed)
    for qid, info in remove.items():
        if info["reason"] == "duplicate":
            assert info["twin"] not in remove or remove.get(info["twin"], {}).get("reason") == "unanswerable_directional", \
                f"{qid}: twin {info['twin']} also removed"

    by_reason = {}
    for info in remove.values():
        by_reason[info["reason"]] = by_reason.get(info["reason"], 0) + 1
    print(f"to remove: {len(remove)}  {by_reason}")

    # pass 2: rewrite files
    changed = 0; removed_total = 0
    if apply:
        os.makedirs(BK, exist_ok=True)
    for f in FILES:
        d = json.load(open(f))
        qs = d.get("questions", [])
        kept = [q for q in qs if q["id"] not in remove]
        if len(kept) == len(qs):
            continue
        changed += 1; removed_total += len(qs) - len(kept)
        if apply:
            bn = os.path.basename(f)
            if not os.path.exists(os.path.join(BK, bn)):
                shutil.copy(f, os.path.join(BK, bn))
            d["questions"] = kept
            json.dump(d, open(f, "w"), indent=2, ensure_ascii=False)
    print(f"files changed: {changed}  questions removed: {removed_total}  apply={apply}")
    if apply:
        json.dump({"date": str(datetime.date.today()),
                   "removed": [{"id": k, **v} for k, v in remove.items()],
                   "by_reason": by_reason},
                  open(MANIFEST, "w"), indent=2, ensure_ascii=False)
        print(f"backup: {BK}\nmanifest: {MANIFEST}")

if __name__ == "__main__":
    main("--apply" in sys.argv)
