#!/usr/bin/env python3
"""Kiwimath content-production full QA pass. Schema 5.0.
Usage: python3 prod_qa_script.py [--apply]   (default = dry run)
"""
import json, glob, re, sys, os, random, collections

_dir = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CP_ROOT", os.path.abspath(os.path.join(_dir, "../archive/content-production")))
OUT = os.environ.get("QA_OUT", _dir)
APPLY = "--apply" in sys.argv

issues = []          # {check, severity, id, file, detail}
counts = collections.Counter()
autofix_files = set()

def add(check, sev, qid, f, detail):
    issues.append({"check": check, "severity": sev, "id": qid, "file": f, "detail": detail})
    counts[(check, sev)] += 1

# ---------- helpers ----------
NUM_RE = re.compile(r'\d+(?:\.\d+)?')
def nums_in(text):
    return NUM_RE.findall(text or "")

def parse_num(s):
    """Extract a numeric value from a choice string like '12 apples', 'Rs 15', '6%', '3/4'."""
    if s is None: return None
    s = str(s).strip().replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").replace("$", "").strip()
    m = re.fullmatch(r'(-?\d+(?:\.\d+)?)\s*(?:%|[a-zA-Z .]*)?', s)
    if m:
        try: return float(m.group(1))
        except: return None
    m = re.fullmatch(r'(\d+)\s*/\s*(\d+)', s)
    if m and int(m.group(2)) != 0:
        return int(m.group(1)) / int(m.group(2))
    return None

def keyed_value(q):
    ch = q.get("choices") or []
    ca = q.get("correct_answer")
    if ch and isinstance(ca, int) and 0 <= ca < len(ch):
        return parse_num(ch[ca]), "mcq"
    if "correct_value" in q and q["correct_value"] is not None:
        try: return float(q["correct_value"]), "value"
        except: return None, None
    return None, None

def fnum(x):
    if x is None: return None
    return int(x) if abs(x - round(x)) < 1e-9 else round(x, 6)

OPS = {"+": lambda a,b: a+b, "-": lambda a,b: a-b,
       "×": lambda a,b: a*b, "x": lambda a,b: a*b, "X": lambda a,b: a*b, "*": lambda a,b: a*b,
       "÷": lambda a,b: (a/b if b else None), "/": lambda a,b: (a/b if b else None)}

NUMG = r'\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?'   # comma-grouped or plain
def tonum(s):
    return float(s.replace(",", ""))

# expression must directly follow a cue verb; ops: × ÷ * / or spaced x or + - (spaced)
CUE_EXPR = re.compile(
    r'(?:what is|calculate|solve|compute|evaluate|work out|find the value of|add|subtract|multiply|divide)\s*[:,]?\s+'
    r'(' + NUMG + r')\s*([+\-×÷*/]|x(?=\s))\s*(' + NUMG + r')'
    r'(?:\s*([+\-×÷*/]|x(?=\s))\s*(' + NUMG + r'))?'
    r'\s*(?:=\s*\?)?\s*(?:$|[?.!](?![\d.]))', re.I)
FRACTION_IN_STEM = re.compile(r'\d+\s*/\s*\d+')
ALGEBRA = re.compile(r'\b\d*[a-wyz]\s*[+\-=]|\b[a-wyz]\s*=|\d+[a-wyz]\b|\bequals\b')

SHAPE_GUARD = re.compile(r'triangle|circle|semicircle|cut|remove|remaining|shaded|fold|attach|made up|combined|border|fence post|diagonal|circumscrib|inscrib', re.I)

def compute_expected(stem):
    """Return (value, rule) or (None, None). Very conservative."""
    s = stem
    sl = s.lower()
    if 'magic square' in sl:
        return None, None

    # ---- missing number: full simple equation "a op ? = c" only ----
    BLANK = r'(?:\?|_+|□|☐)'
    TERM = r'(?:' + NUMG + '|' + BLANK + r')'
    eqs = re.findall(r'(?<![\d=+\-×x*÷/_☐?])(' + TERM + r'(?:\s*[+\-×x*÷/]\s*' + TERM + r')+\s*=\s*' + TERM + r'(?:\s*[+\-×x*÷/]\s*' + TERM + r')*)(?!\s*[\d=+\-×x*÷/_☐?])', s)
    if len(eqs) == 1:
        eq = eqs[0]
        toks = re.findall(NUMG + '|' + BLANK + r'|[+\-×x*÷/=]', eq)
        if len(toks) == 5 and toks[3] == '=':
            t1, op, t2, _, t3 = toks
            blanks = [t for t in (t1, t2, t3) if re.fullmatch(BLANK, t)]
            if len(blanks) == 1 and op in OPS:
                try:
                    if re.fullmatch(BLANK, t3):
                        v = OPS[op](tonum(t1), tonum(t2))
                    elif re.fullmatch(BLANK, t1):
                        b, c = tonum(t2), tonum(t3)
                        v = {'+': c-b, '-': c+b, '×': (c/b if b else None), 'x': (c/b if b else None),
                             '*': (c/b if b else None), '÷': c*b, '/': c*b}.get(op)
                    else:
                        a, c = tonum(t1), tonum(t3)
                        v = {'+': c-a, '-': a-c, '×': (c/a if a else None), 'x': (c/a if a else None),
                             '*': (c/a if a else None), '÷': (a/c if c else None), '/': (a/c if c else None)}.get(op)
                    if v is not None:
                        return v, "missing_number"
                except Exception:
                    pass

    # ---- percent of: "what is N% of M" adjacency, no algebra ----
    if not ALGEBRA.search(s) and sl.count('%') == 1:
        m = re.search(r'(?:what is|find|calculate)\s+(\d+(?:\.\d+)?)\s*%\s*of\s*(?:₹|rs\.?\s*|\$)?(' + NUMG + r')\s*[?.!]', sl)
        if m:
            return float(m.group(1)) * tonum(m.group(2)) / 100, "percent_of"

    # ---- fraction of: exactly one fraction in stem ----
    fracs = re.findall(r'(?<![\d/])(\d+)\s*/\s*(\d+)(?![\d/])', s)
    if len(fracs) == 1:
        m = re.search(r'(?<![\d/])(\d+)\s*/\s*(\d+)\s+of\s+(?:₹|Rs\.?\s*|\$)?(' + NUMG + r')(?![\d/])', s)
        if m and int(m.group(2)) and ' of ' in sl and sl.count(' of ') == 1:
            return int(m.group(1)) / int(m.group(2)) * tonum(m.group(3)), "fraction_of"

    # ---- double / half: cue-adjacent only ----
    m = re.search(r'(?:what is|find)\s+(double|twice|half)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*[?.!]', sl)
    if m and 'fold' not in sl:
        v = float(m.group(2))
        return (v/2 if m.group(1) == "half" else v*2), "double_half"

    # ---- coins: sum ALL "N coins of M" groups ----
    cm = re.findall(r'(\d+)\s+coins?\s+of\s+(?:₹|Rs\.?\s*|\$)?\s*(\d+)', s, re.I)
    if cm and re.search(r'\b(total|how much|how many rupees|altogether|in all)\b', sl) \
       and not re.search(r'note|bill|paise', sl):
        return float(sum(int(a)*int(b) for a, b in cm)), "coins"

    # ---- rectangle / square perimeter & area: single clean shape only ----
    if not SHAPE_GUARD.search(sl):
        if 'rectangle' in sl or 'rectangular' in sl:
            if 'square' not in sl.replace('square cm','').replace('square m','').replace('sq cm','').replace('sq m','').replace('square unit',''):
                ml = re.search(r'(?:length|long)\D{0,12}?(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:cm|m|km|mm|units?|inches|feet)?\s+long', sl)
                mw = re.search(r'(?:width|breadth|wide)\D{0,12}?(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:cm|m|km|mm|units?|inches|feet)?\s+wide', sl)
                if ml and mw:
                    L = float(ml.group(1) or ml.group(2)); W = float(mw.group(1) or mw.group(2))
                    if 'perimeter' in sl and 'area' not in sl:
                        return 2*(L+W), "rect_perimeter"
                    if 'area' in sl and 'perimeter' not in sl:
                        return L*W, "rect_area"
        elif re.search(r'\ba square\b', sl):
            ms = re.search(r'side\D{0,12}?(\d+(?:\.\d+)?)', sl)
            if ms and 'squares' not in sl:
                sd = float(ms.group(1))
                if 'perimeter' in sl and 'area' not in sl:
                    return 4*sd, "square_perimeter"
                if 'area' in sl and 'perimeter' not in sl:
                    return sd*sd, "square_area"

    # ---- place value: cue-adjacent, no face-value/product chaining ----
    if 'face value' not in sl and 'product' not in sl and 'sum' not in sl and 'difference' not in sl:
        m = re.search(r'place value of (?:the )?(?:digit )?(\d) in (?:the number )?(' + NUMG + r')\s*[?.!]', sl)
        if m:
            d, n = m.group(1), m.group(2).replace(",", "")
            digits = n.replace(".", "")
            if digits.count(d) == 1:
                if '.' in n:
                    ip, fp = n.split('.')
                    if d in ip:
                        idx = ip.find(d)
                        return float(d) * (10 ** (len(ip) - idx - 1)), "place_value"
                    idx = fp.find(d)
                    return float(d) / (10 ** (idx + 1)), "place_value"
                idx = n.find(d)
                return float(d) * (10 ** (len(n) - idx - 1)), "place_value"

    # ---- constant-step pattern "a, b, c, d, ?" (plain small ints only) ----
    m = re.search(r'(?<![\d,])((?:\d{1,4},\s+){3,})(?:\?|_+|□|☐)', s)
    if m:
        seq = [int(x) for x in re.findall(r'\d+', m.group(1))]
        if len(seq) >= 4:
            diffs = {seq[i+1]-seq[i] for i in range(len(seq)-1)}
            if len(diffs) == 1:
                return float(seq[-1] + diffs.pop()), "pattern_step"

    # ---- plain expression: cue-adjacent, correct precedence, no parens/algebra/fractions/rounding ----
    if not ALGEBRA.search(s) and not FRACTION_IN_STEM.search(s) and 'round' not in sl and 'estimate' not in sl:
        cands = list(CUE_EXPR.finditer(s))
        if len(cands) == 1:
            m = cands[0]
            span_txt = s[max(0, m.start()-2):m.end()+2]
            if '(' not in span_txt and ')' not in span_txt and ' of ' not in span_txt.lower():
                a, op1, b = tonum(m.group(1)), m.group(2), tonum(m.group(3))
                try:
                    if m.group(4):
                        op2, c = m.group(4), tonum(m.group(5))
                        prec = lambda o: 2 if o in '×÷*/xX' else 1
                        if prec(op2) > prec(op1):
                            v2 = OPS[op2](b, c)
                            v = OPS[op1](a, v2) if v2 is not None else None
                        else:
                            v1 = OPS[op1](a, b)
                            v = OPS[op2](v1, c) if v1 is not None else None
                    else:
                        v = OPS[op1](a, b)
                except Exception:
                    v = None
                if v is not None:
                    return v, "expression"

    return None, None

# ---------- stem cleaning ----------
def clean_stem(stem):
    """Return (new_stem, fixes_list). Auto-fixable items only."""
    fixes = []
    s = stem
    # stray punctuation
    if re.search(r'\?\?+', s):
        s = re.sub(r'\?\?+', '?', s); fixes.append("multi_question_mark")
    if re.search(r'(?<!\.)\.\.(?!\.)', s):
        s = re.sub(r'(?<!\.)\.\.(?!\.)', '.', s); fixes.append("double_period")
    if re.search(r'\s+([.,!?;:])', s):
        s = re.sub(r'\s+([.,!?;:])', r'\1', s); fixes.append("space_before_punct")
    if re.search(r'  +', s):
        s = re.sub(r'  +', ' ', s); fixes.append("double_space")
    if s != s.strip():
        s = s.strip(); fixes.append("strip_ws")
    # exact duplicate sentences (len>10, must look like a complete sentence)
    parts = re.split(r'(?<=[.!?])\s+', s)
    if len(parts) > 1:
        seen, out, removed = set(), [], False
        for p in parts:
            key = p.strip()
            if len(key) > 10 and key in seen and re.match(r'^[A-Z0-9"\'“]', key):
                removed = True
                continue
            seen.add(key)
            out.append(p)
        if removed:
            s = ' '.join(out); fixes.append("dup_sentence_removed")
    return s, fixes

BROKEN_NAME = [
    re.compile(r'\b(?:is|are|has|have)\s+(?:taller|shorter|older|younger|bigger|smaller|heavier|lighter|faster|slower|more|fewer|less)\s+than\s*[.,?]'),
    # '!' lookbehind added (2026-06-12 fix pass): factorial notation ("n! has 4 trailing
    # zeros") is not an orphaned sentence
    re.compile(r'(?:^|[.?:]\s+|(?<![0-9nN])!\s+)(?:is|has|was|and|or|plots|splits?)\s'),
    re.compile(r'(?:^|[.!?]\s+)(?:Is|Was)\s+(?:older|younger|taller|shorter|bigger|smaller|heavier|lighter)\b'),
    re.compile(r'(?:^|[.!?]\s+)Has\s+\d'),
    # refined (2026-06-12 fix pass): old r'\s(?:to|than|from|with)[.?!]' flagged legitimate
    # English ("start with?", "add up to?", "listen to?", "FB is to GD as PM is to?").
    # Keep only genuinely-orphaned forms: dangling "than."/"from." and verb+object drops.
    re.compile(r'\s(?:than|from)[.?!]'),
    re.compile(r'\bgives \d+ to[.?!]'),
    re.compile(r'\bequally with[.?!]'),
    re.compile(r'\bdoes\s+have\b'),
]

FILLER_PATTS = [
    (re.compile(r'\bworkspace\b', re.I), "workspace"),
    (re.compile(r'\bHelp calculate\b', re.I), "help_calculate"),
    (re.compile(r'\bNeeds to work out\b', re.I), "needs_to_work_out"),
]

VIS_REF = re.compile(r'\b(picture|figure(?!s?\s+(?:out|this))|image|diagram|shown below|shown above|shown here|look at the (?:number bond|graph|chart|pattern|objects)|see the (?:graph|chart|number bond)|in the visual|pictured|graph below|count the objects)\b', re.I)
PURE_VIS_SENT = re.compile(r'^(look at|see) the (picture|figure|image|diagram|number bond|graph|chart)( below| above| carefully)?[.!]?$', re.I)

GRAPH_GROUPS = {
    "bar graph": ["bar graph", "bar chart"],
    "pictograph": ["pictograph", "picture graph"],
    "pie chart": ["pie chart", "pie graph", "circle graph"],
    "line graph": ["line graph"],
    "tally": ["tally chart", "tally marks"],
}
def graph_type(text):
    tl = (text or "").lower()
    found = set()
    for g, alts in GRAPH_GROUPS.items():
        if any(a in tl for a in alts):
            found.add(g)
    return found

OBJ_VOCAB = ["apple","orange","banana","mango","grape","star","balloon","flower","car","bus",
             "bird","fish","cat","dog","tree","book","pencil","ball","cookie","candy",
             "butterfly","bee","duck","frog","kite","cupcake","strawberry","cherry","heart","triangle",
             "circle","rectangle","sticker","marble","shell","leaf","egg","cup","hat","boat"]
def objs_in(text):
    tl = (text or "").lower()
    return {o for o in OBJ_VOCAB if re.search(r'\b' + o + r's?\b', tl)}

EMOJI_RE = re.compile(r'[\U0001F300-\U0001FAFF☀-➿]')
def svg_repeat_count(svg):
    """Most common repeated emoji glyph count in svg text elements, or None."""
    if not svg: return None
    texts = re.findall(r'<text[^>]*>(.*?)</text>', svg, re.S)
    glyphs = []
    for t in texts:
        glyphs += EMOJI_RE.findall(t)
    if not glyphs: return None
    c = collections.Counter(glyphs)
    g, n = c.most_common(1)[0]
    if len(c) == 1 and n >= 2:
        return n
    return None

HOWMANY = re.compile(r'^\s*how many \w+ (do you see|are there|are shown|can you count|are in the picture)', re.I)

GARBLE = re.compile(r'\d[A-Z][a-z]')
def leak_check(text, ansstrs):
    """terminal answer leak: hint ends with '= ANS' / 'is ANS' / 'answer: ANS'."""
    if not text: return False
    t = text.strip()
    for a in ansstrs:
        if not a: continue
        ae = re.escape(a)
        if re.search(r'(?:answer is|answer:|=|\bis)\s*' + ae + r'\s*[.!]?\s*$', t, re.I):
            return True
        if re.search(r'\banswer\s*(?:is|:)\s*' + ae + r'\b', t, re.I):
            return True
    return False

# ---------- main loop ----------
all_ids = collections.Counter()
id_files = collections.defaultdict(list)
no_hint_files = collections.Counter()
proposed_answer_fixes = []
scanned = 0
files = sorted(glob.glob(os.path.join(ROOT, "grade*", "*.json")))
random.seed(42)
sample_pool = []

for fpath in files:
    if fpath.endswith("topics.json"):
        continue
    rel = os.path.relpath(fpath, ROOT)
    with open(fpath) as fh:
        doc = json.load(fh)
    qs = doc["questions"] if isinstance(doc, dict) else doc
    modified = False
    for q in qs:
        scanned += 1
        qid = q.get("id", "?")
        all_ids[qid] += 1
        id_files[qid].append(rel)
        stem = q.get("stem") or ""
        ch = q.get("choices") or []
        ca = q.get("correct_answer")
        sample_pool.append((rel, qid))

        # ===== check 1: stems =====
        new_stem, fixes = clean_stem(stem)
        if fixes:
            add("stem_cleanup", "auto_fixed", qid, rel, "+".join(fixes))
            if APPLY:
                q["stem"] = new_stem
                modified = True
            stem = new_stem
        for patt, name in FILLER_PATTS:
            if patt.search(stem):
                add("stem_filler", "medium", qid, rel, f"filler phrase: {name}")
        if any(p.search(stem) for p in BROKEN_NAME):
            sev = "critical" if re.search(r'who is the (oldest|youngest|tallest|shortest)|who is (oldest|youngest)', stem.lower()) else "high"
            add("stem_broken_name", sev, qid, rel, f"orphaned sentence (character name stripped): {stem[:140]!r}")

        # ===== check 2: visual mismatch =====
        svg = q.get("visual_svg")
        if svg:
            ctx = " ".join(filter(None, [q.get("visual_alt"), str(q.get("visual_context") or "")]))
            gs, gc = graph_type(stem), graph_type(ctx)
            if gs and gc and not (gs & gc):
                add("visual_mismatch", "high", qid, rel, f"stem says {sorted(gs)} but visual alt/context says {sorted(gc)}")
            # clock / number line mismatch
            for term in ["clock", "number line"]:
                in_stem = term in stem.lower()
                in_ctx = term in ctx.lower()
                if in_ctx and gs and term not in [g for g in gs] and not in_stem and (gs - {"tally"}):
                    pass  # covered above
            # object mismatch
            so, ao = objs_in(stem), objs_in(q.get("visual_alt") or "")
            if so and ao and not (so & ao):
                add("visual_object_mismatch", "medium", qid, rel, f"stem objects {sorted(so)} vs alt objects {sorted(ao)}")
            # counting cross-check: svg object count must match answer OR some stem quantity
            kv, _src = keyed_value(q)
            if kv is not None and (HOWMANY.match(stem) or q.get("interaction_mode") == "tap_to_count"):
                n = svg_repeat_count(svg)
                if n is not None and abs(kv - n) > 1e-9 and str(n) not in nums_in(stem):
                    add("visual_count_mismatch", "high", qid, rel, f"svg shows {n} repeated objects; keyed answer is {fnum(kv)}; {n} appears nowhere in stem")
        else:
            # ===== check 3: missing visuals =====
            if VIS_REF.search(stem):
                parts = re.split(r'(?<=[.!?])\s+', stem)
                pure = [p for p in parts if PURE_VIS_SENT.match(p.strip())]
                rest = [p for p in parts if not PURE_VIS_SENT.match(p.strip())]
                rest_txt = ' '.join(rest)
                if pure and rest_txt and re.search(r'\d', rest_txt) and ('?' in rest_txt or '_' in rest_txt):
                    add("missing_visual", "auto_fixed", qid, rel, f"removed pure visual-ref sentence(s): {pure}")
                    if APPLY:
                        q["stem"] = rest_txt
                        modified = True
                else:
                    sev = "critical" if not re.search(r'\d', stem) else "high"
                    add("missing_visual", sev, qid, rel, "stem references a visual but visual_svg is null/empty")

        # ===== check 4: answers =====
        if ch:
            # duplicate choices
            norm = [str(c).strip().lower() for c in ch]
            if len(set(norm)) < len(norm):
                add("duplicate_choices", "high", qid, rel, f"choices: {ch}")
            if not (isinstance(ca, int) and 0 <= ca < len(ch)):
                add("answer_index_oob", "critical", qid, rel, f"correct_answer={ca}, {len(ch)} choices")
            # junk placeholder distractors
            # "(same)" removed from the junk list (2026-06-12 fix pass): 'Right (same)' is a
            # meaningful choice on reflection questions (A2-SHP-0083 / T5-327), not a placeholder
            junk = [c for c in ch if re.search(r'\((?:alt|dup|placeholder|v2)\)|TODO|FIXME', str(c))]
            if junk:
                add("choice_junk_placeholder", "high", qid, rel, f"junk distractor(s): {junk}")
            # choice format inconsistency
            pure_num = [bool(re.fullmatch(r'-?\d+(?:\.\d+)?', str(c).strip())) for c in ch]
            num_word = [bool(re.fullmatch(r'-?\d+(?:\.\d+)?\s+[A-Za-z].*', str(c).strip())) for c in ch]
            if any(pure_num) and any(num_word):
                add("choice_format_mix", "low", qid, rel, f"mixed bare/unit choices: {ch}")

        kv, ksrc = keyed_value(q)
        exp, rule = compute_expected(stem)
        if exp is None and ch and len(ch) >= 2:
            # comparison of exactly two stem values: "Which is greater: A or B?"
            m = re.search(r'which (?:number |one |fraction )?is (?:the )?(greater|larger|bigger|smaller)\s*[:,]?\s*([\d,]+(?:/\d+)?(?:\.\d+)?)\s+or\s+([\d,]+(?:/\d+)?(?:\.\d+)?)\s*\?', stem, re.I)
            if m and 'digit' not in stem.lower():
                v1, v2 = parse_num(m.group(2)), parse_num(m.group(3))
                if v1 is not None and v2 is not None and abs(v1 - v2) > 1e-9:
                    word = m.group(1).lower()
                    bigger = word in ("greater", "larger", "bigger")
                    exp_str = m.group(2) if (v1 > v2) == bigger else m.group(3)
                    exp = parse_num(exp_str)
                    rule = "comparison"
        if exp is not None and kv is not None:
            counts[("answer_recomputed", "info")] += 1
            if abs(exp - kv) > 1e-6:
                # is computed among choices?
                hit = None
                for i, c in enumerate(ch):
                    pv = parse_num(c)
                    if pv is not None and abs(pv - exp) < 1e-6:
                        hit = i; break
                if hit is not None and ksrc == "mcq":
                    add("wrong_answer", "auto_fixed", qid, rel,
                        f"rule={rule}: stem computes {fnum(exp)}; keyed choice[{ca}]={ch[ca]!r}; fixed -> choice[{hit}]={ch[hit]!r}")
                    proposed_answer_fixes.append((rel, qid, rule, fnum(exp), ca, hit, stem[:120], list(ch)))
                    if APPLY:
                        q["correct_answer"] = hit
                        modified = True
                else:
                    add("wrong_answer", "critical", qid, rel,
                        f"rule={rule}: stem computes {fnum(exp)} but keyed answer is {fnum(kv)} and {fnum(exp)} not in choices {ch}")

        # ===== check 5: hints =====
        h = q.get("hint")
        if h is None:
            no_hint_files[rel] += 1
            counts[("hint_missing", "high")] += 1
        elif isinstance(h, dict):
            levels = [(k, (h.get(k) or "").strip()) for k in sorted(h.keys())]
            empt = [k for k, v in levels if not v]
            if empt:
                add("hint_empty_level", "high", qid, rel, f"empty levels: {empt}")
            vals = [v for _, v in levels if v]
            if len(vals) >= 2 and len(set(vals)) < len(vals):
                add("hint_identical_levels", "medium", qid, rel, "two or more hint levels are identical")
            # cites stem numbers
            stem_nums = set(nums_in(stem))
            if stem_nums and vals:
                hint_nums = set()
                for v in vals: hint_nums |= set(nums_in(v))
                if not (stem_nums & hint_nums):
                    add("hint_no_stem_numbers", "low", qid, rel, "no hint level cites any stem number")
            # leaks
            ansstrs = []
            if kv is not None:
                ansstrs.append(str(fnum(kv)))
            if ch and isinstance(ca, int) and 0 <= ca < len(ch):
                ansstrs.append(str(ch[ca]).strip())
            for k, v in levels:
                if v and leak_check(v, ansstrs):
                    add("hint_answer_leak", "high", qid, rel, f"{k} leaks answer: ...{v[-60:]!r}")
                    break
            # garbled
            for k, v in levels:
                if v and (GARBLE.search(v) or re.search(r'(?<!\.)\.\.(?!\.)', v)):
                    add("hint_garbled", "medium", qid, rel, f"{k}: {v[:80]!r}")
                    break

    if APPLY and modified:
        with open(fpath, "w") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        autofix_files.add(fpath)

# ---------- duplicate IDs ----------
dups = {i: c for i, c in all_ids.items() if c > 1}
dup_file_pairs = collections.Counter()
for i in dups:
    dup_file_pairs[tuple(sorted(set(id_files[i])))] += 1

# ---------- summary ----------
summary = {
    "scanned": scanned,
    "duplicate_ids": {"count": len(dups), "examples": list(dups.items())[:5],
                      "file_pairs": {" | ".join(k): v for k, v in dup_file_pairs.most_common(10)}},
    "no_hint": {"total": sum(no_hint_files.values()), "files": dict(sorted(no_hint_files.items()))},
    "counts": {f"{c}/{s}": n for (c, s), n in sorted(counts.items())},
    "applied": APPLY,
    "files_modified": sorted(os.path.relpath(p, ROOT) for p in autofix_files),
}
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "prod_issues.json"), "w") as fh:
    json.dump(issues, fh, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "prod_summary.json"), "w") as fh:
    json.dump(summary, fh, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "prod_answer_fix_proposals.json"), "w") as fh:
    json.dump([{"file": r, "id": i, "rule": ru, "computed": e, "old_idx": o, "new_idx": n,
                "stem": st, "choices": c} for r, i, ru, e, o, n, st, c in proposed_answer_fixes],
              fh, ensure_ascii=False, indent=1)

print(json.dumps(summary["counts"], indent=1))
print("scanned:", scanned)
print("dup ids:", len(dups))
print("no-hint total:", summary["no_hint"]["total"], "files:", len(no_hint_files))
print("answer fix proposals:", len(proposed_answer_fixes))
print("APPLY:", APPLY)
