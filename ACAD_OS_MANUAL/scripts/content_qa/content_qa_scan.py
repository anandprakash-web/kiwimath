#!/usr/bin/env python3
"""
Kiwimath content QA scanner (READ-ONLY — reports, never edits).

Runs the programmatic detectors behind the Mistakes Repository so a new import
can be checked for regressions in one command.

Usage:
    cd ~/Downloads/kiwimath/content-live && python3 qa-reports/content_qa_scan.py

Covers the machine-checkable mistake types:
  A  unsubstituted template placeholders ({b}, {j}, {rem}, raw LaTeX accents)
  B  wrong answer key — ratio larger/smaller angle  + remainder-theorem sanity
  C  wrong figure — semicircle/sector drawn as a full circle
  D  confusing formation — stem promises a figure that isn't shown
  E  spoiler figure — Venn region-sum / tree leaf-count equals the answer

Detectors are deliberately conservative (favor precision); they print example
IDs so a human can confirm before any fix pass. See qa-reports/MISTAKES_REPOSITORY.md.
"""
import json, glob, re, os, sys, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # content-live/
OLY = sorted(glob.glob(os.path.join(ROOT, "olympiad", "L*", "L*_*.json")))
CUR = sorted(glob.glob(os.path.join(ROOT, "curriculum", "*", "grade*", "questions.json")))
FILES = [f for f in (OLY + CUR) if os.path.getsize(f) > 1000]

def questions(f):
    d = json.load(open(f))
    return d.get("questions", d if isinstance(d, list) else [])

def ival(q):
    """Numeric answer VALUE. Prefer correct_value; for MCQ parse the keyed choice
    (correct_answer is a 0-3 index there, not the value)."""
    v = q.get("correct_value")
    if v is None:
        ca, ch = q.get("correct_answer"), q.get("choices")
        if isinstance(ca, int) and ch and 0 <= ca < len(ch):
            m = re.search(r'-?\d+(?:\.\d+)?', str(ch[ca]))
            if m: return int(float(m.group())) if float(m.group()).is_integer() else float(m.group())
        v = ca
    try: return int(float(v)) if float(v).is_integer() else float(v)
    except Exception: return None

def short(f): return os.path.basename(f)

MATH = re.compile(r'\$[^$]*\$')
# Placeholder = a short LOWERCASE token in braces ({b}, {n}, {rem}, {j}).
# Excludes set notation ({Elephant}, {Tiger, Lion}) and LaTeX groups (math-stripped).
PH   = re.compile(r'(?<![\\_^])\{[a-z][a-z0-9_]{0,5}\}')
ACCENT = re.compile(r'\\[A-Za-z]\{[a-z]\}')   # \H{o} etc. rendered in prose

def scan_placeholders():
    hits = []
    for f in FILES:
        for q in questions(f):
            vs = q.get("visual_svg")
            if isinstance(vs, str) and PH.search(vs):
                hits.append((q["id"], short(f), "svg", PH.findall(vs)))
            for fld in ("stem", "hint", "solution", "solution_steps", "choices"):
                v = q.get(fld)
                if v is None: continue
                txt = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
                clean = MATH.sub(" ", txt)
                toks = PH.findall(clean)
                if ACCENT.search(txt): toks = toks + ["<latex-accent>"]
                if toks:
                    hits.append((q["id"], short(f), fld, toks))
    return hits

NTERM = re.compile(r'(\d+)\s*:\s*(\d+)(?:\s*:\s*(\d+))?(?:\s*:\s*(\d+))?')
def scan_ratio_angle():
    bad = []
    for f in FILES:
        for q in questions(f):
            s = q.get("stem", ""); sl = s.lower()
            if not re.search(r'\bangle', sl) or "similar" in sl or "side" in sl: continue
            m = NTERM.search(s)
            if not m: continue
            terms = [int(g) for g in m.groups() if g]
            if "straight line" in sl or "supplementary" in sl or ("two angles" in sl): W, need = 180, 2
            elif "triangle" in sl: W, need = 180, 3
            elif "complementary" in sl: W, need = 90, 2
            elif "quadrilateral" in sl: W, need = 360, 4
            else: continue
            if len(terms) < need: continue
            terms = terms[:need]; k = W / sum(terms)
            want = "larger" if re.search(r'larg|great', sl) else ("smaller" if re.search(r'small|least', sl) else None)
            if want is None: continue
            truth = (max(terms) if want == "larger" else min(terms)) * k
            c = ival(q)
            if c is None or abs(c - truth) > 1e-6:
                bad.append((q["id"], short(f), terms, want, c, round(truth, 3)))
    return bad

SEMI = ("semicircle", "semi-circle", "half circle", "quarter circle", "quarter-circle", "sector", "arc of")
# a full circle is CORRECT for these contexts, so don't flag them as "drawn as full circle"
SEMI_OK = ("inscribed", "subtend", "folded", "fold ", "central angle")
def scan_semicircle():
    bad = []
    for f in FILES:
        for q in questions(f):
            s = q.get("stem", "").lower(); vs = q.get("visual_svg")
            if not vs or not any(k in s for k in SEMI): continue
            if any(w in s for w in SEMI_OK): continue
            big = [c for c in re.findall(r'<circle[^>]*\br="([\d.]+)"', vs) if float(c) >= 15]
            arc = bool(re.search(r'<path[^>]*\bd="[^"]*[Aa][\s\d.]', vs))
            if big and not arc:
                bad.append((q["id"], short(f)))
    return bad

# Require an explicit reference to a figure/diagram — NOT bare "dots" (a counting noun
# in lower grades: "Aarohi has 8 dots and gets 2 more") nor bare "shown".
PROMISE = re.compile(r'figure number|\bthe figure\b|\bthe diagram\b|in the figure|in the diagram|as shown|shaded (region|part|portion|area)|the (grid|graph) (shown|below|above)', re.I)
def scan_absent_figure():
    bad = []
    for f in FILES:
        for q in questions(f):
            s = q.get("stem", "")
            s_noltx = re.sub(r'\\[a-z]*dots', '', s)   # drop \cdots/\ldots
            if PROMISE.search(s_noltx) and not (q.get("visual_svg") or q.get("visual_png")):
                bad.append((q["id"], short(f), s[:80]))
    return bad

def scan_spoiler_figures():
    venn = []; tree = []
    for f in FILES:
        for q in questions(f):
            vs = q.get("visual_svg")
            if not isinstance(vs, str): continue
            s = q.get("stem", ""); sl = s.lower(); A = ival(q)
            if A is None: continue
            nums = [int(x) for x in re.findall(r'>(-?\d+)<', vs)]
            stem_nums = set(int(x) for x in re.findall(r'\b(\d+)\b', s))
            big = len(re.findall(r'<circle[^>]*\br="(?:[4-9]\d|\d{3})', vs))
            ncirc = len(re.findall(r'<circle', vs)); nline = len(re.findall(r'<line', vs))
            if big >= 2 and len(nums) >= 2:
                setkw = any(k in sl for k in ["both", "neither", "at least one", "only", "like ", "play ", "study "])
                derived = [n for n in nums if n not in stem_nums]
                if setkw and (sum(nums) == A or A in nums) and derived:
                    venn.append((q["id"], short(f), nums, A))
            if nline >= 6 and ncirc >= 4 and A <= 40:
                cntkw = any(k in sl for k in ["how many ways", "pick one", "one of each", "outcomes", "combinations", "arrange"])
                if cntkw and A <= ncirc <= A + 8:
                    tree.append((q["id"], short(f), ncirc, A))
    return venn, tree

_GEO_WORDS = re.compile(r'hypotenuse|triangle|\bside\b|\bangle\b|polygon|quadrilateral|rectangle|\bsquare\b|diagonal|\bleg', re.I)
_CLOCKISH = re.compile(r'clock|mirror|number line|\bgraph\b|\bbar\b|pictograph|tally|spinner|dice|reflect', re.I)
def scan_answer_in_figure():
    """Geometry figure that LABELS the quantity being asked (e.g. a right triangle
    with the hypotenuse '5' drawn on it). Flags when the integer answer appears as
    a figure label and is NOT a value given in the stem. Excludes clock/number-line/
    graph figures (their scale numerals legitimately collide with small answers)."""
    bad = []
    for f in FILES:
        for q in questions(f):
            vs = q.get("visual_svg")
            if not isinstance(vs, str) or "<polygon" not in vs:
                continue
            s = q.get("stem", "")
            if not _GEO_WORDS.search(s) or _CLOCKISH.search(s):
                continue
            A = ival(q)
            if A is None or A != int(A):
                continue
            labels = set(re.findall(r'>\s*(-?\d+)\s*(?:cm|°)?\s*<', vs))
            stem_nums = set(re.findall(r'-?\d+', s))
            if str(int(A)) in labels and str(int(A)) not in stem_nums:
                bad.append((q["id"], short(f), int(A)))
    return bad

def scan_angle_on_right_angle():
    """An acute-angle label (e.g. '30°') drawn ON the right-angle vertex of a
    right triangle — the corner carrying the square mark is 90°, so labelling it
    with an acute value contradicts the figure. The 90° vertex is the middle
    point of the right-angle polyline mark."""
    out = []
    for f in FILES:
        for q in questions(f):
            vs = q.get("visual_svg")
            if not isinstance(vs, str) or "<polyline" not in vs:
                continue
            m = re.search(r'<polyline points="([\d.]+),([\d.]+) ([\d.]+),([\d.]+) ([\d.]+),([\d.]+)"', vs)
            if not m:
                continue
            cx, cy = float(m.group(3)), float(m.group(4))   # middle vertex = the 90° corner
            for tm in re.finditer(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*>([^<]*)</text>', vs):
                x, y, t = float(tm.group(1)), float(tm.group(2)), tm.group(3)
                if "°" in t and re.search(r'\d', t) and abs(x - cx) < 28 and abs(y - cy) < 28:
                    out.append((q["id"], short(f), t.strip()))
                    break
    return out

def scan_pattern_no_visual():
    """H · a 'what X comes next?' pattern question with an EMPTY visual_svg and no
    pattern in the stem -> unanswerable (the pattern was stripped). Skips questions
    whose stem still carries the sequence (numbers / shape words / comma list)."""
    hits = []
    for f in FILES:
        for q in questions(f):
            st = (q.get("stem") or "")
            if "comes next" not in st.lower():
                continue
            vs = q.get("visual_svg")
            if not (vs is None or (isinstance(vs, str) and vs.strip() == "")):
                continue
            if re.search(r'\d|circle|square|triangle|star|heart|diamond|,', st, re.I):
                continue  # sequence is in the stem -> answerable
            hits.append((q["id"], short(f)))
    return hits

_FIGREF = re.compile(r'\b(figure|shown|picture|diagram|below|the shape|this shape|drawn|image|grid|fold|mirror|reflect|symmetr|clock|net|dice|domino|graph|number line|array|ten.?frame|tally|chart|spinner)\b', re.I)
def scan_decorative_figure_on_logic():
    """I · a logic / sorting / odd-one-out / missing-number question that carries a
    figure its stem never refers to -> a reused generic template was mis-assigned
    (e.g. a 'mirror' figure on "which doesn't belong: 28,21,26,20?"). Review/clear."""
    hits = []
    for f in FILES:
        for q in questions(f):
            vs = q.get("visual_svg")
            if not (isinstance(vs, str) and vs.strip().startswith("<svg")):
                continue
            tags = set(t.lower() for t in (q.get("tags") or []))
            topic = (q.get("km_topic", "") or "").lower()
            if not (tags & {"puzzles", "odd_one_out", "sorting", "logic"} or "puzzle" in topic or "sort" in topic or "missing_number" in topic):
                continue
            if _FIGREF.search(q.get("stem", "") or ""):
                continue
            hits.append((q["id"], short(f)))
    return hits

def _ans_token(q):
    ca, ch = q.get("correct_answer"), q.get("choices")
    if isinstance(ca, int) and ch and 0 <= ca < len(ch):
        return str(ch[ca]).strip()
    cv = q.get("correct_value")
    return str(cv) if cv is not None else None

# An ABSENT referent: the prompt needs a pattern / sequence / list / missing-number
# that isn't in the text and isn't drawn. Guards against answerable look-alikes:
#  • "which of the following…" / "consider the following: (i)…" — the options/list ARE present
#  • "complete the pattern: AZ, BY, CX, ?" — the data is inline (any digit present, or
#    a ':' immediately followed by the sequence)
#  • a digit anywhere, or a figure, means the data is supplied
_ABSENT = re.compile(r'(\bmissing (number|value|term|digit)\b|what comes next|\bnext term\b|'
                     r'sequence of figures|find the rule|replaces the question mark|'
                     r'^\s*(arrange|classify|order|sort) the following)', re.I)
_ABSENT_OK = re.compile(r'(which of the following|consider the following|'
                        r'complete the pattern:\s*\S|\((i|ii|a|b)\))', re.I)
def scan_empty_stem():
    """J · blank stem, a single bare word ('Calculate'), or a prompt that references an
    ABSENT referent (missing number / what comes next / sequence of figures /
    arrange the following) with no number in the text and no figure to supply it.
    'Which/Consider the following…', inline patterns and concrete prompts ('…of a
    regular hexagon', 'Find all n with φ(n)|n') are answerable and NOT flagged."""
    hits = []
    for f in FILES:
        for q in questions(f):
            st = (q.get("stem") or "").strip()
            has_vis = bool((q.get("visual_svg") or "").strip())
            if not st:
                hits.append((q["id"], short(f), "empty")); continue
            if len(st.split()) < 2 and not re.search(r'[\d?=]', st):
                hits.append((q["id"], short(f), "one word: " + st)); continue
            inline_list = st.count(",") >= 2   # an inline sequence ("A, B, C, A, ?") supplies the data
            if (_ABSENT.search(st) and not _ABSENT_OK.search(st) and not inline_list
                    and not re.search(r'\d', st) and not has_vis):
                hits.append((q["id"], short(f), "absent referent: " + st[:42]))
    return hits

_COMMON_ANS = {"no", "yes", "none", "all", "some", "more", "less", "odd", "even", "true", "false", "same"}
def scan_hint_leak():
    """K · the answer is REVEALED in an early hint (level_0/level_1) — a leak. Precise:
    requires the answer in a giving-away context ('is/equals/= X', 'answer is X'), and
    skips short/common words that collide incidentally. level_2 may reveal."""
    hits = []
    for f in FILES:
        for q in questions(f):
            a = _ans_token(q)
            if not a or len(a) < 3 or a.lower() in _COMMON_ANS:
                continue
            h = q.get("hint") or {}
            if not isinstance(h, dict):
                continue
            early = " ".join(str(h.get(k, "")) for k in ("level_0", "level_1"))
            if re.search(r'(?:is|are|equals?|answer\w*\W{0,12}|=)\s*' + re.escape(a) + r'(?![\w.])', early, re.I):
                hits.append((q["id"], short(f), a))
    return hits

def answer_value(q):
    """Resolve the correct-answer VALUE. correct_answer is a 0-based INDEX into
    choices for MCQ items, so two questions with the same index but differently
    ORDERED choices have DIFFERENT actual answers — keying on the raw index would
    wrongly merge them (and miss same-value pairs whose choice order differs)."""
    ca, ch = q.get("correct_answer"), q.get("choices") or []
    if isinstance(ca, int) and 0 <= ca < len(ch):
        return str(ch[ca])
    return str(ca)

def _level_of(f):
    b = os.path.basename(f)
    m = re.match(r'(L\d)_', b)
    return m.group(1) if m else "curriculum"

def scan_duplicates():
    """L · TRUE removable duplicate — same stem + same option SET + same resolved
    answer VALUE + same visual. A pair is a removable duplicate only if it is in the
    SAME level (a student could see it twice) OR cross-level with the SAME difficulty
    (a misfile). Cross-level pairs at DIFFERENT difficulty are the same question
    intentionally calibrated for two tiers (separate files, never seen together) and
    are NOT flagged."""
    seen = {}; hits = []
    for f in FILES:
        lvl = _level_of(f)
        for q in questions(f):
            st = re.sub(r'\s+', ' ', (q.get("stem") or "")).strip().lower()
            if not st:
                continue
            # distinguish by visual: prefer svg, else the faithful-render png
            # (Vedantu items share a generic stem + empty choices, so the IMAGE is
            #  the only differentiator — png MUST be in the signature).
            vis = (q.get("visual_svg") or "").strip() or (q.get("visual_png") or "").strip()
            vkey = hashlib.md5(vis.encode()).hexdigest()[:8] if vis else ""
            key = (st, tuple(sorted(str(c) for c in (q.get("choices") or []))), answer_value(q), vkey)
            if key in seen:
                pl, pdiff = seen[key][1], seen[key][2]
                cdiff = str(q.get("irt_b")) + "|" + str(q.get("difficulty"))
                if lvl == pl or cdiff == pdiff:          # same level, or cross-level misfile
                    hits.append((q["id"], short(f), "= " + seen[key][0]))
            else:
                seen[key] = (q["id"], lvl, str(q.get("irt_b")) + "|" + str(q.get("difficulty")))
    return hits

def scan_fake_svg():
    """M · fake placeholder SVG — grey #F8F9FA box + label, no real geometry."""
    hits = []
    for f in FILES:
        for q in questions(f):
            vs = q.get("visual_svg")
            if isinstance(vs, str) and "#F8F9FA" in vs and vs.count("<") < 8:
                hits.append((q["id"], short(f)))
    return hits

# N · context-stripped unanswerable — a "Which direction … now?/facing?" rotation
# question whose setup (start compass dir + turn) was lost: no figure, no number,
# no movement/compass word in the stem, and nothing recoverable in original_stem.
# The keyed direction is underivable, so the item cannot be answered.
_DIR = re.compile(r'which direction', re.I)
_NOW = re.compile(r'(now\?|facing\s+now|facing\b)', re.I)
_SETUP = re.compile(r'(turn|left|right|clockwise|anticlock|step|move|goes|walk|roll|'
                    r'north|south|east|west|up|down|\d)', re.I)
def scan_directional_unanswerable():
    hits = []
    for f in FILES:
        for q in questions(f):
            if (q.get("visual_svg") or "").strip():
                continue
            st = q.get("stem") or ""
            if not (_DIR.search(st) and _NOW.search(st)) or _SETUP.search(st):
                continue
            os_ = q.get("original_stem") or ""
            if len(os_) > len(st) + 3 and _SETUP.search(os_):
                continue  # setup recoverable from original_stem
            hits.append((q["id"], short(f)))
    return hits

def section(title, rows, fmt, limit=12):
    print(f"\n{'='*70}\n{title}: {len(rows)}\n{'='*70}")
    for r in rows[:limit]:
        print("  " + fmt(r))
    if len(rows) > limit:
        print(f"  … and {len(rows)-limit} more")

if __name__ == "__main__":
    print(f"Scanning {len(FILES)} files under {ROOT}")
    ph = scan_placeholders()
    section("A · unsubstituted placeholders", ph, lambda r: f"{r[0]} [{r[1]}] {r[2]} {r[3]}")
    ra = scan_ratio_angle()
    section("B · ratio larger/smaller wrong key", ra, lambda r: f"{r[0]} [{r[1]}] {r[2]} want={r[3]} key={r[4]} truth={r[5]}")
    sc = scan_semicircle()
    section("C · semicircle/sector drawn as full circle", sc, lambda r: f"{r[0]} [{r[1]}]")
    af = scan_absent_figure()
    section("D · promises a figure that isn't shown", af, lambda r: f"{r[0]} [{r[1]}] {r[2]}")
    venn, tree = scan_spoiler_figures()
    section("E · Venn spoiler (regions reveal answer)", venn, lambda r: f"{r[0]} [{r[1]}] nums={r[2]} ans={r[3]}")
    section("E · tree spoiler (leaves = answer)", tree, lambda r: f"{r[0]} [{r[1]}] circles={r[2]} ans={r[3]}")
    af2 = scan_answer_in_figure()
    section("F · geometry figure labels the answer", af2, lambda r: f"{r[0]} [{r[1]}] answer {r[2]} drawn on the figure")
    ara = scan_angle_on_right_angle()
    section("G · acute-angle label on the right-angle vertex", ara, lambda r: f"{r[0]} [{r[1]}] '{r[2]}' on the 90° corner")
    pnv = scan_pattern_no_visual()
    section("H · pattern needs a visual but visual_svg empty", pnv, lambda r: f"{r[0]} [{r[1]}]")
    dfl = scan_decorative_figure_on_logic()
    section("I · mismatched/decorative figure on a logic/number question", dfl, lambda r: f"{r[0]} [{r[1]}]")
    es = scan_empty_stem()
    section("J · empty / truncated stem", es, lambda r: f"{r[0]} [{r[1]}] {r[2]}")
    hl = scan_hint_leak()
    section("K · answer leaks in an early hint", hl, lambda r: f"{r[0]} [{r[1]}] ans='{r[2]}'")
    du = scan_duplicates()
    section("L · exact duplicate question", du, lambda r: f"{r[0]} [{r[1]}] {r[2]}")
    fk = scan_fake_svg()
    section("M · fake placeholder SVG (grey box)", fk, lambda r: f"{r[0]} [{r[1]}]")
    du2 = scan_directional_unanswerable()
    section("N · context-stripped 'which direction now?' (unanswerable)", du2, lambda r: f"{r[0]} [{r[1]}]")

    total = (len(ph) + len(ra) + len(sc) + len(af) + len(venn) + len(tree) + len(af2)
             + len(ara) + len(pnv) + len(dfl) + len(es) + len(hl) + len(du) + len(fk) + len(du2))
    print(f"\n{'='*70}\nTOTAL outstanding flags: {total}")
    print("(0 = clean. Non-zero = inspect IDs above before any fix pass.)")
    sys.exit(1 if total else 0)
