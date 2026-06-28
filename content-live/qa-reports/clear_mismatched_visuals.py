#!/usr/bin/env python3
"""Type I — clear MISMATCHED/decorative figures from self-contained number-logic
questions (e.g. a 'mirror' template on "Which doesn't belong: 28,21,26,20?").

A reused generic-template SVG got auto-attached to logic/number questions that
need no figure. The stem is fully answerable from its own text, so the figure is
at best decorative and at worst misleading. We CLEAR the visual on the SAFE,
unambiguous subset only (odd-one-out / missing-number / digit & place-value
puzzles with the numbers all present); everything else is flagged, not touched.

Only visual_svg / visual_alt / visual_requirement change. Usage: [--apply]
"""
import json, glob, os, re, sys, shutil, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = sorted(glob.glob(os.path.join(ROOT, "olympiad", "L1", "L1_*.json")))

def qlist(dd): return dd.get("questions", dd) if isinstance(dd, dict) else (dd if isinstance(dd, list) else [])

FIGREF = re.compile(r'\b(figure|shown|picture|diagram|below|the shape|this shape|drawn|image|grid|fold|mirror|reflect|symmetr|clock|net|dice|domino|graph|number line|array|ten.?frame|tally|chart)\b', re.I)
# SAFE self-contained number-logic stems (answer is fully determined by the text):
SAFE = re.compile(r'(does not belong|odd one out|doesn.t belong|missing number|sum of the digits|'
                  r'tens digit|ones digit|\d-digit number|how many (more|less|fewer)|'
                  r'what (is|number).{0,40}\d|greater|smaller|largest|smallest|between)', re.I)
VAR = re.compile(r'\b[A-Z]\s*[+\-×x*]\s*[A-Z]\b')  # undefined variables (A+B) -> NOT safe

def main(apply):
    bk = f"{os.path.dirname(os.path.abspath(__file__))}/backup-mismatch-visuals-{datetime.date.today()}"
    cleared = flagged = 0; flags = []
    for f in FILES:
        dd = json.load(open(f)); touched = False
        for q in qlist(dd):
            if not isinstance(q, dict):
                continue
            vs = q.get("visual_svg")
            if not (isinstance(vs, str) and vs.strip().startswith("<svg")):
                continue
            st = q.get("stem", "") or ""
            tags = set(t.lower() for t in (q.get("tags") or []))
            topic = (q.get("km_topic", "") or "").lower()
            is_logic = bool(tags & {"puzzles", "odd_one_out", "sorting", "logic"}) or "puzzle" in topic or "sort" in topic or "missing_number" in topic
            if not is_logic or FIGREF.search(st):
                continue
            # choices must be plain values (numbers/short words), not figure references
            ch = q.get("choices") or []
            if any(re.search(r'figure|shape|picture|left|right|option [A-D]', str(c), re.I) for c in ch):
                continue
            # self-contained: in a logic topic, no figure reference, no undefined
            # variables, the numbers are all in the stem -> figure is decorative.
            if not VAR.search(st) and len(re.findall(r'\d', st)) >= 2:
                q["visual_svg"] = None
                q["visual_alt"] = ""
                q["visual_requirement"] = "none"
                cleared += 1; touched = True
            else:
                flagged += 1
                if len(flags) < 25: flags.append((q.get("id"), st[:48]))
        if touched and apply:
            os.makedirs(bk, exist_ok=True)
            rel = os.path.basename(f)
            if not os.path.exists(f"{bk}/{rel}"):
                shutil.copy(f, f"{bk}/{rel}")
            json.dump(dd, open(f, "w"), indent=2, ensure_ascii=False)
    print(f"cleared={cleared}  flagged(not touched)={flagged}  apply={apply}")
    print("flagged for manual review (variables / not self-contained):")
    for fl in flags: print("  ", fl[0], "|", fl[1])

if __name__ == "__main__":
    main("--apply" in sys.argv)
