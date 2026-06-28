#!/usr/bin/env python3
"""Generic per-level defect remover (reusable for the L2…L7 QA loop).

Removes, WITHIN a single level only:
  • value-based TRUE duplicates (same stem + option SET + resolved answer VALUE +
    visual-hash) — keep the first occurrence. Cross-level pairs are NOT touched
    (same question calibrated at a different difficulty for another tier, in a
    separate file → a student never sees both).
  • an explicit list of unrecoverable / unanswerable ids passed via --ids.

Backs up every changed file and writes a recovery manifest. Usage:
  python3 remove_level_defects.py --level L2 [--ids KM-L2-ALG-0232,KM-L2-NT-0430] [--apply]
"""
import json, glob, os, re, sys, hashlib, shutil, datetime, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def S(v): return str(v) if v is not None else ""
def answer_value(q):
    ca, ch = q.get("correct_answer"), q.get("choices") or []
    return str(ch[ca]) if isinstance(ca, int) and 0 <= ca < len(ch) else S(ca)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True)             # e.g. L2
    ap.add_argument("--ids", default="")                  # explicit unanswerable ids
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(ROOT, "olympiad", a.level, f"{a.level}_*.json")))
    explicit = set(x for x in a.ids.split(",") if x.strip())
    bk = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      f"backup-{a.level}-defects-{datetime.date.today()}")
    manifest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            f"removed_{a.level}_{datetime.date.today()}.json")

    seen = {}; remove = {}
    for f in files:
        for q in json.load(open(f)).get("questions", []):
            qid = q["id"]
            if qid in explicit:
                remove[qid] = {"reason": "unanswerable"}
            st = re.sub(r'\s+', ' ', S(q.get("stem"))).strip().lower()
            if not st:
                continue
            vs = S(q.get("visual_svg")); vk = hashlib.md5(vs.encode()).hexdigest()[:8] if vs.strip() else ""
            key = (st, tuple(sorted(S(c) for c in (q.get("choices") or []))), answer_value(q), vk)
            if key in seen:
                if qid not in remove:
                    remove[qid] = {"reason": "duplicate", "twin": seen[key]}
            else:
                seen[key] = qid
    for qid, info in remove.items():
        if info["reason"] == "duplicate":
            assert info["twin"] not in remove or remove[info["twin"]]["reason"] != "duplicate", \
                f"{qid}: twin {info['twin']} also a removed duplicate"
    by = {}
    for info in remove.values(): by[info["reason"]] = by.get(info["reason"], 0) + 1
    print(f"{a.level}: to remove {len(remove)}  {by}")

    if a.apply:
        os.makedirs(bk, exist_ok=True)
    changed = removed = 0
    for f in files:
        d = json.load(open(f)); qs = d.get("questions", [])
        kept = [q for q in qs if q["id"] not in remove]
        if len(kept) == len(qs):
            continue
        changed += 1; removed += len(qs) - len(kept)
        if a.apply:
            bn = os.path.basename(f)
            if not os.path.exists(os.path.join(bk, bn)):
                shutil.copy(f, os.path.join(bk, bn))
            d["questions"] = kept
            json.dump(d, open(f, "w"), indent=2, ensure_ascii=False)
    print(f"files changed {changed}  removed {removed}  apply={a.apply}")
    if a.apply:
        json.dump({"date": str(datetime.date.today()), "level": a.level,
                   "removed": [{"id": k, **v} for k, v in remove.items()], "by_reason": by},
                  open(manifest, "w"), indent=2, ensure_ascii=False)
        print("backup:", bk, "\nmanifest:", manifest)

if __name__ == "__main__":
    main()
