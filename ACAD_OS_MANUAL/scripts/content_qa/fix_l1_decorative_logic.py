#!/usr/bin/env python3
"""L1 Type-I tail: restore self-contained logic stems from original_stem + clear the
decorative/mismatched figure; remove the few that are unrecoverable.

These were flagged by detector I (a reused generic template SVG — 'mirror', three
'₹' coins, generic shapes — auto-attached to a self-contained logic/number question)
but NOT auto-cleared because the served stem had an undefined variable (A+B), a
missing name, or a leading narrative prefix. In every recoverable case the canonical
question lives in original_stem; we pull the stem back from the anchor (no fabrication)
and verify the keyed answer still follows, then drop the irrelevant figure.

  RESTORE+CLEAR : A+B+A (restore "If A=x and B=y…", verify x+y+x==key),
                  coin-comparison (restore full names, verify most/fewest==key),
                  which-doesn't-belong + row-of-shapes (restore clean text).
  REMOVE        : unanswerable/mismatched with nothing recoverable
                  (KM-L1-COM-0711, KM-L1-GEO-0136 pattern-no-sequence;
                   KM-L1-ALG-0533 change w/ no setup & ₹/$ mismatch;
                   KM-L1-ALG-0774 'what time' but clock shows 3:00 ≠ key 8).

Only stem / visual_svg / visual_alt / visual_requirement change on the restore set;
the remove set deletes whole items. Backs up before writing. Usage: [--apply]
"""
import json, glob, os, re, sys, shutil, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = sorted(glob.glob(os.path.join(ROOT, "olympiad", "L1", "L1_*.json")))
BK = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"backup-l1-decorative-{datetime.date.today()}")

REMOVE = {"KM-L1-COM-0711", "KM-L1-GEO-0136", "KM-L1-ALG-0533", "KM-L1-ALG-0774"}
RESTORE = {  # the 20 recoverable Type-I tail items
    "KM-L1-COM-0808","KM-L1-COM-0884","KM-L1-COM-0969","KM-L1-COM-0998","KM-L1-COM-1018",
    "KM-L1-COM-1024","KM-L1-COM-1045","KM-L1-COM-1048","KM-L1-COM-1150","KM-L1-COM-1168",
    "KM-L1-COM-1180","KM-L1-COM-1191","KM-L1-COM-1194","KM-L1-COM-1195","KM-L1-COM-1197",
    "KM-L1-COM-1216","KM-L1-COM-1421","KM-L1-COM-1612","KM-L1-COM-1625",
    "KM-L1-COM-1016","KM-L1-COM-1315","KM-L1-COM-3128",
}

def S(v): return str(v) if v is not None else ""
def keyed(q):
    ca, ch = q.get("correct_answer"), q.get("choices") or []
    return S(ch[ca]) if isinstance(ca, int) and 0 <= ca < len(ch) else S(ca)

def anchor(text):
    for pat in (r'(Which one does not belong:.*)', r'(In a row of shapes:.*)',
                r'(If A\s*=.*)', r'([A-Z][a-z]+ has \d+ coins?\..*)'):
        m = re.search(pat, text)
        if m:
            return re.sub(r'\s+', ' ', m.group(1)).strip()
    return None

def verify(stem, q):
    """Return (ok, why). Confirms the keyed answer still follows from the restored stem."""
    k = keyed(q)
    m = re.search(r'If A\s*=\s*(\d+)\s+and\s+B\s*=\s*(\d+).*A\+B\+A', stem)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return (str(a + b + a) == re.sub(r'\D', '', k), f"A+B+A={a+b+a} vs key {k}")
    if re.search(r'has \d+ coins?', stem):
        base = re.search(r'([A-Z][a-z]+) has \d+ coins?', stem)
        more = re.search(r'([A-Z][a-z]+) has more than', stem)
        fewer = re.search(r'([A-Z][a-z]+) has fewer than', stem)
        if not (base and more and fewer):
            return (False, "could not parse three people")
        want = more.group(1) if re.search(r'\bmost\b', stem, re.I) else fewer.group(1)
        return (want == k, f"expected {want} vs key {k}")
    # doesn't-belong / row-of-shapes: key must be one of the listed tokens
    listed = [t.strip().lower() for t in re.split(r'[:,.]', stem) if t.strip()]
    return (k.lower() in " ".join(listed), f"key '{k}' present in stem")

def main(apply):
    idx = {}
    for f in FILES:
        for q in json.load(open(f)).get("questions", []):
            idx[q["id"]] = (q, f)
    # build restored stems + verify
    plan = {}; fails = []
    for qid in RESTORE:
        q, f = idx[qid]
        src = q.get("original_stem") or ""
        stem = anchor(src) or anchor(S(q.get("stem"))) or S(q.get("stem"))
        ok, why = verify(stem, q)
        (plan.__setitem__(qid, stem) if ok else fails.append((qid, why, stem[:60])))
    print(f"restore planned: {len(plan)}  verify-fail: {len(fails)}")
    for fl in fails: print("  FAIL", fl[0], "|", fl[1], "|", fl[2])
    if fails:
        print("aborting — fix verify failures before applying"); return
    # apply
    if apply:
        os.makedirs(BK, exist_ok=True)
    changed_files = restored = removed = 0
    for f in FILES:
        d = json.load(open(f)); qs = d.get("questions", [])
        touched = False; out = []
        for q in qs:
            qid = q["id"]
            if qid in REMOVE:
                removed += 1; touched = True; continue
            if qid in plan:
                q["stem"] = plan[qid]
                q["visual_svg"] = None; q["visual_alt"] = ""; q["visual_requirement"] = "none"
                restored += 1; touched = True
            out.append(q)
        if touched:
            changed_files += 1
            if apply:
                bn = os.path.basename(f)
                if not os.path.exists(os.path.join(BK, bn)):
                    shutil.copy(f, os.path.join(BK, bn))
                d["questions"] = out
                json.dump(d, open(f, "w"), indent=2, ensure_ascii=False)
    print(f"files changed: {changed_files}  restored: {restored}  removed: {removed}  apply={apply}")
    if apply: print("backup:", BK)

if __name__ == "__main__":
    main("--apply" in sys.argv)
