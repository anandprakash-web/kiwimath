#!/usr/bin/env python3
"""Repair pattern 'what X comes next?' questions whose visual went missing.

ROOT CAUSE: a content pass shortened the served `stem` to a bare "What colour
bead comes next?" expecting a visual, but `visual_svg` is empty/None -> the
pattern is gone -> unanswerable. We REBUILD a valid pattern visual so the cycle
yields the keyed `correct_answer`:
  - exact sequence from `original_stem` when present & consistent;
  - else a 2-item repeat [answer, other] where `other` comes from the
    diagnostics ("which colour follows X") or a distractor.
Only `visual_svg` (+ `visual_alt`) is written; answer/choices/etc. are untouched.

Usage: python3 fix_pattern_visuals.py --kind color [--apply]
"""
import json, re, glob, os, sys, datetime, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # content-live/
COLORS = {"red":"#E53935","blue":"#1E88E5","green":"#43A047","purple":"#8E24AA",
          "orange":"#FB8C00","yellow":"#FDD835","white":"#FFFFFF","black":"#212121",
          "pink":"#EC407A","brown":"#8D6E63","grey":"#9E9E9E","gray":"#9E9E9E"}
SHAPES = {"circle","square","triangle","star","heart","diamond","rectangle",
          "oval","pentagon","hexagon","moon","arrow"}

def empty(v): return v is None or (isinstance(v, str) and v.strip() == "")

def period(seq):
    n = len(seq)
    for p in range(1, n):
        if n % p == 0 and all(seq[i] == seq[i % p] for i in range(n)):
            return p
    return n

def bead_svg(seq):
    n = len(seq) + 1; W = 44*n + 16; H = 70; cy = 38
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           f'<line x1="14" y1="{cy}" x2="{W-14}" y2="{cy}" stroke="#C9BFA8" stroke-width="3"/>']
    for i, c in enumerate(seq):
        cx = 30 + i*44; hexc = COLORS.get(c.lower(), "#BDBDBD")
        edge = "#9E9E9E" if c.lower() == "white" else hexc
        out.append(f'<circle cx="{cx}" cy="{cy}" r="16" fill="{hexc}" stroke="{edge}" stroke-width="2"/>')
    cx = 30 + len(seq)*44
    out.append(f'<circle cx="{cx}" cy="{cy}" r="16" fill="#F1F1F1" stroke="#FF6F00" stroke-width="2.5" stroke-dasharray="4 3"/>')
    out.append(f'<text x="{cx}" y="{cy+6}" font-size="20" font-weight="800" text-anchor="middle" fill="#FF6F00">?</text></svg>')
    return "".join(out)

def _ngon(cx, cy, r, k, rot=-math.pi/2):
    return " ".join(f"{cx+r*math.cos(rot+i*2*math.pi/k):.1f},{cy+r*math.sin(rot+i*2*math.pi/k):.1f}" for i in range(k))

def shape_el(name, cx, cy, r):
    n = name.lower(); fill = "#5C9CE6"; st = "#1E5FA8"; sw = 'stroke="'+st+'" stroke-width="2"'
    if n == "circle":    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" {sw}/>'
    if n == "square":    return f'<rect x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}" rx="3" fill="{fill}" {sw}/>'
    if n == "rectangle": return f'<rect x="{cx-r*1.3:.0f}" y="{cy-r*0.78:.0f}" width="{2.6*r:.0f}" height="{1.56*r:.0f}" rx="3" fill="{fill}" {sw}/>'
    if n == "oval":      return f'<ellipse cx="{cx}" cy="{cy}" rx="{r*1.3:.0f}" ry="{r*0.85:.0f}" fill="{fill}" {sw}/>'
    if n == "triangle":  return f'<polygon points="{cx},{cy-r} {cx+r},{cy+r} {cx-r},{cy+r}" fill="{fill}" {sw} stroke-linejoin="round"/>'
    if n == "diamond":   return f'<polygon points="{cx},{cy-r} {cx+r},{cy} {cx},{cy+r} {cx-r},{cy}" fill="{fill}" {sw} stroke-linejoin="round"/>'
    if n == "pentagon":  return f'<polygon points="{_ngon(cx,cy,r,5)}" fill="{fill}" {sw} stroke-linejoin="round"/>'
    if n == "hexagon":   return f'<polygon points="{_ngon(cx,cy,r,6,0)}" fill="{fill}" {sw} stroke-linejoin="round"/>'
    if n == "star":
        pts = " ".join(f"{cx+(r if i%2==0 else r*0.42)*math.cos(-math.pi/2+i*math.pi/5):.1f},{cy+(r if i%2==0 else r*0.42)*math.sin(-math.pi/2+i*math.pi/5):.1f}" for i in range(10))
        return f'<polygon points="{pts}" fill="{fill}" {sw} stroke-linejoin="round"/>'
    if n == "heart":
        return (f'<path d="M {cx} {cy+r*0.72:.1f} C {cx-r*1.4:.1f} {cy-r*0.3:.1f}, {cx-r*0.5:.1f} {cy-r*1.1:.1f}, {cx} {cy-r*0.28:.1f} '
                f'C {cx+r*0.5:.1f} {cy-r*1.1:.1f}, {cx+r*1.4:.1f} {cy-r*0.3:.1f}, {cx} {cy+r*0.72:.1f} Z" fill="{fill}" {sw}/>')
    if n == "moon":      return f'<path d="M {cx+r*0.4:.0f} {cy-r:.0f} A {r} {r} 0 1 0 {cx+r*0.4:.0f} {cy+r:.0f} A {r*0.8:.0f} {r*0.8:.0f} 0 1 1 {cx+r*0.4:.0f} {cy-r:.0f} Z" fill="{fill}" {sw}/>'
    if n == "arrow":     return f'<path d="M {cx-r} {cy-r*0.4:.0f} h {r:.0f} v {-r*0.4:.0f} l {r:.0f} {r*0.8:.0f} l {-r:.0f} {r*0.8:.0f} v {-r*0.4:.0f} h {-r:.0f} Z" fill="{fill}" {sw} stroke-linejoin="round"/>'
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" {sw}/>'

def shape_svg(seq):
    n = len(seq) + 1; cell = 56; W = cell*n + 12; H = 72; cy = 38; r = 19
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    for i, s in enumerate(seq):
        out.append(shape_el(s, 30 + i*cell, cy, r))
    cx = 30 + len(seq)*cell
    out.append(f'<rect x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}" rx="5" fill="#F1F1F1" stroke="#FF6F00" stroke-width="2.5" stroke-dasharray="4 3"/>')
    out.append(f'<text x="{cx}" y="{cy+6}" font-size="20" font-weight="800" text-anchor="middle" fill="#FF6F00">?</text></svg>')
    return "".join(out)

def shape_seq(q):
    ans = str(q["choices"][q["correct_answer"]]).strip(); al = ans.lower()
    if al not in SHAPES:
        return None, "answer-not-a-shape"
    o = q.get("original_stem") or ""
    seq = [s.capitalize() for s in re.findall(r'\b(' + "|".join(SHAPES) + r')\b', o, re.I)]
    if len(seq) >= 4:
        p = period(seq)
        if seq[len(seq) % p].lower() == al:
            return seq, "original_stem"
    diag = " ".join(str(v) for v in (q.get("diagnostics") or {}).values())
    m = re.search(r'follows?\s+(?:a\s+)?(' + "|".join(SHAPES) + r')\b', diag, re.I)
    other = m.group(1).capitalize() if (m and m.group(1).lower() != al) else None
    if other is None:
        for c in q["choices"]:
            if str(c).lower() in SHAPES and str(c).lower() != al:
                other = str(c).capitalize(); break
    if other is None:
        return None, "no-other-shape"
    return [ans.capitalize(), other] * 3, "inferred:" + other

SIZES = {"tiny":9, "small":13, "short":13, "medium":18, "big":24, "large":24, "tall":24, "long":24}

def size_svg(seq):
    n = len(seq) + 1; cell = 56; W = cell*n + 12; H = 72; base = 60
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    for i, s in enumerate(seq):
        r = SIZES.get(s.lower(), 16); cx = 30 + i*cell
        out.append(f'<circle cx="{cx}" cy="{base-r}" r="{r}" fill="#5C9CE6" stroke="#1E5FA8" stroke-width="2"/>')
    cx = 30 + len(seq)*cell
    out.append(f'<rect x="{cx-18}" y="{base-36}" width="36" height="36" rx="5" fill="#F1F1F1" stroke="#FF6F00" stroke-width="2.5" stroke-dasharray="4 3"/>')
    out.append(f'<text x="{cx}" y="{base-12}" font-size="20" font-weight="800" text-anchor="middle" fill="#FF6F00">?</text></svg>')
    return "".join(out)

def size_seq(q):
    ans = str(q["choices"][q["correct_answer"]]).strip(); al = ans.lower()
    if al not in SIZES:
        return None, "answer-not-a-size"
    o = q.get("original_stem") or ""
    seq = [s.capitalize() for s in re.findall(r'\b(' + "|".join(SIZES) + r')\b', o, re.I)]
    if len(seq) >= 4:
        p = period(seq)
        if seq[len(seq) % p].lower() == al:
            return seq, "original_stem"
    other = None
    for c in q["choices"]:
        if str(c).lower() in SIZES and str(c).lower() != al:
            other = str(c).capitalize(); break
    if other is None:
        return None, "no-other-size"
    return [ans.capitalize(), other] * 3, "inferred:" + other

def color_seq(q):
    """Return (sequence_list, source) or (None, reason)."""
    ans = str(q["choices"][q["correct_answer"]]).strip()
    al = ans.lower()
    if al not in COLORS:
        return None, "answer-not-a-colour"
    # 1) exact sequence from original_stem
    o = q.get("original_stem") or ""
    seq = re.findall(r'\b(' + "|".join(COLORS) + r')\b', o, re.I)
    seq = [s.capitalize() for s in seq]
    if len(seq) >= 4:
        p = period(seq)
        nxt = seq[len(seq) % p]
        if nxt.lower() == al:
            return seq, "original_stem"
    # 2) infer the "other" colour from diagnostics, else a distractor
    diag = " ".join(str(v) for v in (q.get("diagnostics") or {}).values())
    m = re.search(r'follows?\s+(' + "|".join(COLORS) + r')\b', diag, re.I)
    other = None
    if m and m.group(1).lower() != al:
        other = m.group(1).capitalize()
    if other is None:
        no = set(x.lower() for x in re.findall(r"\b(" + "|".join(COLORS) + r")\b(?=[^.]*does(?:n't| not) appear)", diag, re.I))
        for c in q["choices"]:
            cl = str(c).lower()
            if cl in COLORS and cl != al and cl not in no:
                other = str(c).capitalize(); break
    if other is None:
        return None, "no-other-colour"
    # seq ends in 'other' so the next item is the answer
    return [ans.capitalize(), other] * 3, "inferred:" + other

def run(kind, apply):
    files = [f for f in glob.glob(f"{ROOT}/olympiad/**/*.json", recursive=True) +
             glob.glob(f"{ROOT}/curriculum/**/*.json", recursive=True) if "qa-reports" not in f]
    fixed = skipped = 0; per_file = {}; skips = []
    backup = f"{ROOT}/qa-reports/backup-pattern-visuals-{datetime.date.today()}"
    for f in files:
        try:
            dd = json.load(open(f))
        except Exception:
            continue
        qs = dd.get("questions", dd) if isinstance(dd, dict) else dd
        if not isinstance(qs, list):
            continue
        touched = False
        for q in qs:
            if not isinstance(q, dict):
                continue
            if "comes next" not in (q.get("stem", "") or "").lower() or not empty(q.get("visual_svg")):
                continue
            ch = [str(c).lower() for c in q.get("choices", [])]
            if kind == "color":
                if not (ch and all(c in COLORS for c in ch)): continue
                seq, src = color_seq(q)
                svg = bead_svg(seq) if seq else None
                alt = ("Bead pattern: " + ", ".join(seq) + ", ?") if seq else None
            elif kind == "shape":
                if not (ch and all(c in SHAPES for c in ch)): continue
                seq, src = shape_seq(q)
                svg = shape_svg(seq) if seq else None
                alt = ("Shape pattern: " + ", ".join(seq) + ", ?") if seq else None
            elif kind == "size":
                if not (ch and all(c in SIZES for c in ch)): continue
                seq, src = size_seq(q)
                svg = size_svg(seq) if seq else None
                alt = ("Size pattern: " + ", ".join(seq) + ", ?") if seq else None
            else:
                continue
            if seq is None:
                skipped += 1; skips.append((q.get("id"), src)); continue
            q["visual_svg"] = svg
            q["visual_alt"] = alt
            fixed += 1; per_file[f] = per_file.get(f, 0) + 1; touched = True
        if touched and apply:
            import shutil
            os.makedirs(backup, exist_ok=True)
            rel = f.split("content-live/")[-1].replace("/", "__")
            if not os.path.exists(f"{backup}/{rel}"):   # back up original once, before overwrite
                shutil.copy(f, f"{backup}/{rel}")
            json.dump(dd, open(f, "w"), indent=2, ensure_ascii=False)  # match repo formatting
    print(f"kind={kind} fixed={fixed} skipped={skipped} apply={apply}")
    for f, n in sorted(per_file.items(), key=lambda x: -x[1]):
        print(f"  {n:3}  {f.split('content-live/')[-1]}")
    if skips:
        print("SKIPS:", skips[:20])

if __name__ == "__main__":
    kind = "color"
    apply = "--apply" in sys.argv
    for a in sys.argv:
        if a.startswith("--kind"):
            pass
    if "--kind" in sys.argv:
        kind = sys.argv[sys.argv.index("--kind") + 1]
    run(kind, apply)
