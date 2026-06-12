#!/usr/bin/env python3
"""Kiwimath content-v4 adaptive QA scan v2 (calibrated). stdlib only.
Usage: python3 qa_scan.py [--fix]
"""
import json, re, glob, sys, os, random
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'content-live', 'content-v4', 'adaptive'))
FIX = '--fix' in sys.argv

issues = []
fixes = Counter()
fix_examples = defaultdict(list)
scanned = Counter()
clean = Counter()

def add_issue(check, sev, qid, fname, detail):
    issues.append({"check": check, "severity": sev, "id": qid, "file": fname, "detail": detail})

# ---------------- helpers ----------------
NUMTOK = r'\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?'
NUMTOK_RE = re.compile(NUMTOK)

def denum(s):
    return float(s.replace(',', ''))

def nums_in(text):
    return [m.group(0) for m in NUMTOK_RE.finditer(text or '')]

def answer_value(q):
    ch = q.get('choices') or []
    ca = q.get('correct_answer')
    if ch:
        if isinstance(ca, int) and 0 <= ca < len(ch):
            return ch[ca], 'choice'
        return None, 'index_oob'
    cv = q.get('correct_value')
    return (cv, 'value') if cv is not None else (None, 'no_value')

def to_num(s):
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    m = re.fullmatch(r'-?\s*(?:' + NUMTOK + r')\s*(?:cm|m|mm|km|kg|g|l|ml|min|minutes|hours|hr|sq\.?\s*cm|sq\.?\s*m|units?|rupees|paise)?\.?', s, re.I)
    if not m:
        return None
    mm = re.search(r'-?' + NUMTOK.replace('(?:', '(?:'), s)
    mm = re.search(r'-?(?:' + NUMTOK + r')', s)
    return float(mm.group(0).replace(',', '')) if mm else None

def fmt(x):
    return str(int(x)) if float(x) == int(x) else str(x)

SENT_SPLIT = re.compile(r'(?<=[.!?])\s+')

# ---------------- check 1: stems ----------------
FILLER_RES = [
    (re.compile(r'\bworkspace\b', re.I), 'filler:workspace'),
    (re.compile(r'\bHelp calculate\b', re.I), 'filler:Help calculate'),
    (re.compile(r'\bneeds to work out\b', re.I), 'filler:needs to work out'),
    (re.compile(r'\bNeeds the GCD\b', re.I), 'filler:Needs the GCD'),
    (re.compile(r'\bAnalysis:'), 'artifact:Analysis:'),
    (re.compile(r'\bChapter \d+\b'), 'artifact:Chapter N'),
    (re.compile(r'\(\s*[A-D]\s*\)\s+[A-Z]'), 'artifact:embedded option label (A)/(B)/...'),
]
COMMON_CAPS = set('''The A An I If What When Where Which Who How Why Now Then There This That These Those It Is Are Was Were Can Could Will Would Should Do Does Did Find Count Help Look Solve Use Choose Pick Add Subtract Multiply Divide Write Read Draw Match Circle Tick Cross Each Every All Some One Two Three Four Five Six Seven Eight Nine Ten Monday Tuesday Wednesday Thursday Friday Saturday Sunday January February March April May June July August September October November December But And Or So Not You We They He She His Her Their Our My In On At To For Of From With Yes No Show Put Take Make Let Today Tomorrow Yesterday First Second Third Last Next Imagine Suppose Remember Hint Note Example During After Before Both Many Much More Most Less Half Double Mr Mrs Ms Dr Rs Calculate Answer Question Together Maths Math Step Venn Diwali Holi Lego True False Indian India Roman Even Odd Red Blue Green Yellow Orange Purple Pink Black White Brown Start End Left Right Top Bottom North South East West'''.split())

SPECIAL_REPAIRS = {
    'A1-CNT-0546': ('toy store,  has 3 shelves', 'toy store, there are 3 shelves'),
    'A1-CNT-0609': ('magical garden,  3 rows', 'magical garden, there are 3 rows'),
}

def stem_check(q, fname):
    qid = q['id']
    stem = q.get('stem') or ''
    orig = stem
    scanned['stems'] += 1
    flagged = False

    # targeted repair of dropped-word stems found during calibration
    if qid in SPECIAL_REPAIRS:
        old, new = SPECIAL_REPAIRS[qid]
        if old in stem:
            stem = stem.replace(old, new)
            fixes['stem_dropped_word_repaired'] += 1
            fix_examples['stem_dropped_word_repaired'].append((qid, old, new))

    # unanswerable family: "What color does X like?" with no info about X
    m = re.search(r'What colou?r does (\w+) like\?', stem)
    if m and m.group(1) not in stem[:m.start()]:
        add_issue('stem_unanswerable_no_info', 'critical', qid, fname,
                  f'question asks about {m.group(1)!r} but stem gives no information about them — unanswerable guessing game: {stem[:130]!r}')
        flagged = True

    # auto-fix: spacing / stray punctuation (conservative)
    s = stem
    s = re.sub(r'  +', ' ', s)
    s = re.sub(r'(?<=[\w)\]])\s+([.,;])', r'\1', s)   # word . -> word.  (leave "= ?" alone)
    s = re.sub(r'(?<!\?)\?\?(?!\?)', '?', s)
    s = re.sub(r',,+', ',', s)
    if s != stem:
        fixes['stem_punct_spacing'] += 1
        if len(fix_examples['stem_punct_spacing']) < 8:
            fix_examples['stem_punct_spacing'].append((qid, repr(stem[:100]), repr(s[:100])))
        stem = s

    # auto-fix: exact duplicated sentences
    sents = SENT_SPLIT.split(stem)
    if len(sents) > 1:
        seen, out, dropped = set(), [], False
        for sent in sents:
            key = sent.strip()
            if len(key) > 10 and key in seen:
                dropped = True
                continue
            seen.add(key)
            out.append(sent)
        if dropped:
            stem = ' '.join(out)
            fixes['stem_dup_sentence'] += 1
            if len(fix_examples['stem_dup_sentence']) < 8:
                fix_examples['stem_dup_sentence'].append((qid, repr(orig[:140])))

    for rex, label in FILLER_RES:
        if rex.search(stem):
            add_issue('stem_filler', 'medium', qid, fname, f'{label}: {stem[:130]!r}')
            flagged = True

    # disconnected character-name sentence (tight: non-first, short, no digits/?/:, no 'than')
    sents = SENT_SPLIT.split(stem)
    if len(sents) > 1:
        for i, sent in enumerate(sents[1:], start=1):
            st = sent.strip()
            stl = st.lower()
            if ('?' in st or ':' in st or NUMTOK_RE.search(st) or 'than' in stl
                    or len(st.split()) > 8 or len(st) < 4
                    or st.startswith('(') or re.match(r'^\w+ likes \w+\.?$', st)
                    or re.match(r'^\w+ (?:has|have) an? \w+\.?$', st)
                    or re.search(r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twice|double|half|equal|equally|split|each|every|all|none|nobody|some|dice|die|find|express|height|weight|length|total|sum|left|remaining|share|both)\b', stl)):
                continue
            words = re.findall(r'\b[A-Z][a-z]{2,}\b', st)
            names = [w for w in words if w not in COMMON_CAPS and not st.startswith(w)]
            if st and st.split()[0][0].isupper() and st.split()[0].strip('.,!') not in COMMON_CAPS \
               and re.fullmatch(r'[A-Z][a-z]{2,}', st.split()[0].strip('.,!')):
                names.append(st.split()[0].strip('.,!'))
            names = [n for n in set(names)]
            if not names:
                continue
            rest = ' '.join(sents[:i] + sents[i+1:])
            if not any(n in rest for n in names):
                add_issue('stem_disconnected_name', 'medium', qid, fname,
                          f'sentence mentions {sorted(names)} never used again, adds nothing: {st[:100]!r}')
                flagged = True
                break

    if not flagged and stem == orig:
        clean['stems'] += 1
    if stem != orig:
        q['stem'] = stem
        return True, flagged
    return False, flagged

# ---------------- check 4 parser (needed by visual check) ----------------
OPC = {'+': '+', '-': '-', '−': '-', '×': '*', 'x': '*', '*': '*', '÷': '/'}
CHAIN_RE = re.compile(r'(?<![\d.,/\-])(?:-\s?)?(?:' + NUMTOK + r')(?:\s*[+\-−×x*÷]\s*(?:-\s?)?(?:' + NUMTOK + r'))+(?![\w.,/%])')
EXPR_BLOCKERS = re.compile(r'[()]|%|estimate|round|grid|\brule\b|even or odd|remainder|how many (?:squares|rectangles|triangles)|toothpick|digit|pattern|sequence|fraction|difference|\bterm\b|magic|solve for', re.I)

def eval_chain(text):
    expr = text.replace(',', '').replace('−', '-').replace('×', '*').replace('x', '*').replace('÷', '/')
    if not re.fullmatch(r'[\d\s+\-*/.]+', expr):
        return None
    try:
        return eval(expr, {'__builtins__': {}}, {})
    except Exception:
        return None

def compute_expected(stem):
    s = stem
    sl = s.lower()
    if re.search(r'[_□]|missing|fill in the blank', sl):
        return None
    m = re.search(r'(' + NUMTOK + r')\s*%\s*of\s*(?:rs\.?\s*|₹\s*|\$\s*)?(' + NUMTOK + r')', sl)
    if m:
        return denum(m.group(1)) / 100 * denum(m.group(2)), 'percent_of'
    m = re.search(r'(\d+)\s*/\s*(\d+)(?:th|rd|nd)?\s+of\s+(' + NUMTOK + r')', sl)
    if m and int(m.group(2)) != 0:
        return int(m.group(1)) / int(m.group(2)) * denum(m.group(3)), 'fraction_of'
    m = re.search(r'\b(?:double|twice)(?:\s+of)?\s+(' + NUMTOK + r')\b', sl)
    if m:
        return 2 * denum(m.group(1)), 'double'
    m = re.search(r'\bhalf\s+of\s+(' + NUMTOK + r')\b', sl)
    if m:
        return denum(m.group(1)) / 2, 'half'
    m = re.search(r"\b(ones|unit'?s?|tens|hundreds|thousands)\s+(?:place\s+)?digit\s+(?:of|in)\s+(" + NUMTOK + r')', sl) or \
        re.search(r"digit\s+(?:is\s+)?in\s+the\s+(ones|unit'?s?|tens|hundreds|thousands)\s+place\s+(?:of|in)\s+(" + NUMTOK + r')', sl)
    if m:
        place = {'ones': 0, 'unit': 0, 'units': 0, "unit's": 0, 'tens': 1, 'hundreds': 2, 'thousands': 3}[m.group(1).rstrip("'s") if m.group(1).startswith('unit') else m.group(1)]
        num = m.group(2).replace(',', '')
        return (float(num[-(place + 1)]), 'place_value') if len(num) > place else None
    m = re.search(r'which (?:number |one )?is (greater|bigger|larger|smaller)\b[^0-9]{0,15}?(-?(?:' + NUMTOK + r'))\s+or\s+(-?(?:' + NUMTOK + r'))', sl)
    if m:
        a, b = denum(m.group(2)), denum(m.group(3))
        if a == b:
            return None
        return (max(a, b) if m.group(1) != 'smaller' else min(a, b)), 'comparison'
    # pattern next-term
    if 'rule' not in sl and not re.search(r'\d+(?:st|nd|rd|th)\s+term', sl):
        m = re.search(r'((?:\d+(?:\.\d+)?\s*,\s*){2,}\d+(?:\.\d+)?)\s*,?\s*(?:\?|_+|…|\.\.\.)', s)
        if m and ('next' in sl or 'comes after' in sl or re.search(r'(?:\?|_+|…|\.\.\.)', s[m.start(1):])):
            if 'next' in sl or re.search(r'(?:_+|\?)\s*$', s.strip()) or 'complete' in sl or 'missing' not in sl:
                seq = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', m.group(1))]
                if len(seq) >= 3:
                    diffs = [round(seq[i+1] - seq[i], 6) for i in range(len(seq)-1)]
                    if len(set(diffs)) == 1 and diffs[0] != 0:
                        return seq[-1] + diffs[0], 'pattern_diff'
                    if all(x != 0 for x in seq):
                        ratios = [round(seq[i+1] / seq[i], 6) for i in range(len(seq)-1)]
                        if len(set(ratios)) == 1 and ratios[0] not in (0, 1):
                            return seq[-1] * ratios[0], 'pattern_ratio'
            return None
    # rectangle / square (strict)
    if 'perimeter' in sl or 'area' in sl:
        if 'difference' in sl or ('perimeter' in sl and 'area' in sl):
            return None
        if 'rectangle' in sl and 'rectangles' not in sl and 'l-shape' not in sl:
            ml = re.search(r'length[^0-9]{0,15}(' + NUMTOK + r')', sl)
            mw = re.search(r'(?:width|breadth)[^0-9]{0,15}(' + NUMTOK + r')', sl)
            if not (ml and mw):
                mb = re.search(r'(' + NUMTOK + r')\s*(?:cm|m|mm|km|units?)?\s*(?:by|×|x)\s*(' + NUMTOK + r')\s*(?:cm|m|mm|km|units?)?\b', sl)
                if mb and len(nums_in(sl)) == 2:
                    l, w = denum(mb.group(1)), denum(mb.group(2))
                else:
                    return None
            else:
                l, w = denum(ml.group(1)), denum(mw.group(1))
            return (2 * (l + w), 'rect_perimeter') if 'perimeter' in sl else (l * w, 'rect_area')
        if re.search(r'\bsquare\b', sl) and 'squares' not in sl and 'side' in sl and len(nums_in(sl)) == 1:
            mside = re.search(r'side[^0-9]{0,15}(' + NUMTOK + r')', sl)
            if mside:
                n = denum(mside.group(1))
                return (4 * n, 'square_perimeter') if 'perimeter' in sl else (n * n, 'square_area')
        return None
    # explicit arithmetic chain (strict)
    if EXPR_BLOCKERS.search(sl):
        return None
    chains = CHAIN_RE.findall(s) if False else [m.group(0) for m in CHAIN_RE.finditer(s)]
    if len(chains) != 1:
        return None
    m = CHAIN_RE.search(s)
    before, after = s[:m.start()], s[m.end():m.end() + 8]
    ctx_ok = bool(re.search(r'=\s*\?|^\s*=|\?', after)) or \
             bool(re.search(r'(what is|calculate|find|solve|add:|subtract:|multiply:|divide:|sum of|product of)\s*$', before.lower().strip() + ' ') or
                  re.search(r'(what is|calculate|solve|add:|subtract:)[^0-9]*$', before.lower()))
    if not ctx_ok:
        return None
    if re.search(r'\d\s*[-−]\s*(digit|sided|step|year|day|legged|inch|cm|m)\b', sl):
        return None
    v = eval_chain(m.group(0))
    if v is None:
        return None
    if v < 0 and '-' + '' not in m.group(0).replace(' ', '')[:1] and not re.search(r'(?:^|[^\d])-\s?\d', m.group(0)):
        return None  # negative result without explicit negative operands -> likely misparse
    return v, 'expression'

SAFE_FIX_LABELS = {'expression', 'percent_of', 'fraction_of', 'double', 'half', 'place_value',
                   'pattern_diff', 'pattern_ratio', 'rect_perimeter', 'rect_area',
                   'square_perimeter', 'square_area', 'comparison'}

def answer_check(q, fname):
    qid = q['id']
    scanned['answers'] += 1
    ch = q.get('choices') or []
    ca = q.get('correct_answer')
    stem = q.get('stem') or ''
    grade = q.get('adaptive_grade') or q.get('school_grade')
    changed = False

    if ch:
        if not (isinstance(ca, int) and 0 <= ca < len(ch)):
            add_issue('answer_index_oob', 'critical', qid, fname, f'correct_answer={ca} but {len(ch)} choices')
            return changed
        if len(set(map(str, ch))) < len(ch):
            dups = [c for c, n in Counter(map(str, ch)).items() if n > 1]
            add_issue('duplicate_choices', 'high', qid, fname, f'duplicate choices {dups}: {ch}')
    val, src = answer_value(q)
    n = to_num(val) if val is not None else None
    if n is not None and n < 0 and grade in (1, 2):
        add_issue('negative_answer_junior', 'high', qid, fname, f'grade {grade} keyed answer negative: {val!r}')

    res = compute_expected(stem)
    if res is None:
        clean['answers_unparsed'] += 1
        return changed
    expected, label = res
    scanned['answers_parseable'] += 1
    if n is None:
        return changed  # keyed answer non-numeric -> question asks something else
    if abs(n - expected) < 1e-6:
        clean['answers_parseable_ok'] += 1
        return changed
    if ch:
        numeric_choices = [c for c in ch if to_num(c) is not None]
        if len(numeric_choices) < 3:
            return changed
        matches = [i for i, c in enumerate(ch) if to_num(c) is not None and abs(to_num(c) - expected) < 1e-6]
        if len(matches) == 1 and label in SAFE_FIX_LABELS:
            old = ca
            q['correct_answer'] = matches[0]
            fixes['answer_rekeyed'] += 1
            fix_examples['answer_rekeyed'].append((qid, fname, label,
                f'idx {old} ({val!r}) -> idx {matches[0]} ({ch[matches[0]]!r}); expected {fmt(expected)}; stem={stem[:100]!r}'))
            return True
        add_issue('answer_mismatch', 'critical', qid, fname,
                  f'[{label}] computed {fmt(expected)} but keyed {val!r}; choices={ch}; stem={stem[:120]!r}')
    else:
        add_issue('answer_mismatch_value', 'critical', qid, fname,
                  f'[{label}] computed {fmt(expected)} but correct_value={val!r}; stem={stem[:120]!r}')
    return changed

# ---------------- check 2: visuals ----------------
OBJ_SYNONYMS = {
    'coin': ['₹', 'rs', 'rupee', 'money', 'paise', 'cost', 'price', 'pay', 'change', 'cent', 'dollar', '$', 'buy', 'spend'],
    'ball': ['sphere'], 'block': ['cube', 'tower'], 'candy': ['sweet', 'chocolate', 'toffee'],
    'candies': ['sweet', 'chocolate', 'toffee'], 'star': ['sky', 'night'], 'dot': ['domino', 'dice', 'die'],
}
COUNT_OBJECTS = ['apple', 'coin', 'bird', 'star', 'balloon', 'flower', 'candy', 'candies', 'book', 'pencil',
                 'marble', 'cookie', 'fish', 'car', 'ball', 'dot', 'block', 'button', 'sticker', 'egg',
                 'cupcake', 'butterfly', 'frog', 'duck', 'crayon', 'kite', 'shell', 'heart']
KIND_CHECKS = [
    (re.compile(r'\bclock\b'), 'clock', lambda s: '<circle' in s and ('<line' in s or '<path' in s)),
    (re.compile(r'\bbar (?:graph|chart)\b'), 'bar graph', lambda s: len(re.findall(r'<rect', s)) >= 3),
    (re.compile(r'\bpictograph\b'), 'pictograph', lambda s: len(re.findall(r'<(use|image|text|circle)', s)) >= 3),
    (re.compile(r'\bpie\b'), 'pie chart', lambda s: '<path' in s or '<circle' in s),
    (re.compile(r'\bnumber line\b'), 'number line', lambda s: ('<line' in s or '<path' in s) and len(re.findall(r'<text', s)) >= 3),
]
COUNT_EXCLUDE = re.compile(r'crore|lakh|digit|place|tens\b|hundreds\b|thousand|sides|corners|edges|faces|vertices|symmetry|angles|weeks|days|months|hours|minutes', re.I)

def svg_groups(svg):
    groups = Counter()
    for m in re.finditer(r'<use\b[^>]*(?:href|xlink:href)="([^"]+)"', svg):
        groups['use:' + m.group(1)] += 1
    for m in re.finditer(r'<circle\b[^>]*?r="([^"]+)"[^>]*?fill="([^"]+)"', svg):
        groups['circle:%s:%s' % (m.group(1), m.group(2))] += 1
    for m in re.finditer(r'<circle\b[^>]*?cy="([^"]+)"[^>]*?fill="([^"]+)"', svg):
        groups['circlerow:%s:%s' % (m.group(1), m.group(2))] += 1
    for m in re.finditer(r'<text\b[^>]*?y="([^"]+)"[^>]*>([^<]{1,4})</text>', svg):
        t = m.group(2).strip()
        if t and not re.fullmatch(r'[\d.,:+\-=?% ]+', t):
            groups['glyphrow:%s:%s' % (m.group(1), t)] += 1
    for m in re.finditer(r'<rect\b[^>]*?width="([^"]+)"[^>]*?height="([^"]+)"[^>]*?fill="([^"]+)"', svg):
        groups['rect:%s:%s:%s' % m.groups()] += 1
    for m in re.finditer(r'<text\b[^>]*>([^<]{1,4})</text>', svg):
        t = m.group(1).strip()
        if t and not re.fullmatch(r'[\d.,:+\-=?% ]+', t):
            groups['glyph:' + t] += 1
    for m in re.finditer(r'<(ellipse|polygon|path)\b[^>]*?fill="([^"]+)"', svg):
        groups['%s:%s' % m.groups()] += 1
    return {k: v for k, v in groups.items() if v >= 2}

def visual_check(q, fname):
    qid = q['id']
    svg = q.get('visual_svg')
    if not svg:
        return
    scanned['visuals'] += 1
    stem = q.get('stem') or ''
    alt = (q.get('visual_alt') or '')
    ctx = (q.get('visual_context') or '')
    meta = (alt + ' ' + ctx).lower()
    stem_l = stem.lower()
    flagged = False

    body = re.sub(r'</?svg[^>]*>', '', svg)
    tagc = Counter(re.findall(r'<(\w+)[\s>]', body))
    if set(tagc) <= {'rect', 'text'} and tagc.get('text', 0) <= 1 and tagc.get('rect', 0) <= 1:
        add_issue('visual_placeholder', 'high', qid, fname,
                  'SVG is a caption-in-a-box placeholder, not a real visual: ' + svg[:150])
        scanned['visual_flagged'] += 1
        return

    for rex, kind, ok in KIND_CHECKS:
        if rex.search(meta) and not ok(svg):
            stem_agrees = bool(rex.search(stem_l))
            add_issue('visual_type_mismatch', 'high', qid, fname,
                      f'visual_context/alt says "{kind}" but SVG lacks expected elements'
                      + ('' if stem_agrees else ' (stem does not mention it either — metadata likely stale)')
                      + f'; stem={stem[:80]!r}')
            flagged = True
            break

    for obj in COUNT_OBJECTS:
        if re.search(r'\b' + re.escape(obj) + r's?\b', ctx.lower()):
            base = obj.rstrip('s')
            syns = OBJ_SYNONYMS.get(obj, [])
            if base not in stem_l and not any(t in stem_l for t in syns):
                add_issue('visual_object_mismatch', 'medium', qid, fname,
                          f'visual_context mentions "{obj}" but stem does not: stem={stem[:90]!r}')
                flagged = True
            break

    # counting cross-check: pure counting questions only
    if (re.search(r'\bhow many\b|\bcount the\b|\bcount:', stem_l)
            and not COUNT_EXCLUDE.search(stem_l)
            and compute_expected(stem) is None
            and len(nums_in(stem)) <= 1):
        val, src = answer_value(q)
        n = to_num(val) if val is not None else None
        if n is not None and 0 < n <= 30 and n == int(n):
            groups = svg_groups(svg)
            if groups:
                counts = set(groups.values())
                total = sum(groups.values())
                top = sorted(groups.values(), reverse=True)
                ok = (int(n) in counts or total == int(n)
                      or (len(top) >= 2 and top[0] + top[1] == int(n))
                      or max(counts) > 30)
                if not ok:
                    add_issue('visual_count_mismatch', 'high', qid, fname,
                              f'keyed answer {fmt(n)} but SVG repeated-element counts {dict(sorted(groups.items(), key=lambda kv: -kv[1])[:6])} (total {total}); stem={stem[:100]!r}')
                    flagged = True
    if flagged:
        scanned['visual_flagged'] += 1
    else:
        clean['visuals'] += 1

# ---------------- check 3: missing visuals ----------------
REF_RE = re.compile(r'\b(shown below|shown above|shown here|as shown|shown in the (?:picture|image|figure|chart)|in the picture|in the image|in the figure|the figure|the diagram|look at the|given below|see below|pictured|picture below|image below|figure below|shown)\b', re.I)
REMOVABLE = [r'\s*\(shown below\)', r'\s+shown below', r'\s+shown above', r'\s+shown here',
             r'\s+as shown(?: below| above)?', r'\s+shown in the (?:picture|image|figure)',
             r'\s+given below', r'\s+shown']

def missing_visual_check(q, fname):
    qid = q['id']
    svg = q.get('visual_svg')
    stem = q.get('stem') or ''
    vr = q.get('visual_requirement')
    scanned['missing_visual'] += 1
    changed = False
    if not svg:
        m = REF_RE.search(stem)
        if m:
            ns = nums_in(stem)
            solvable = (len(ns) >= 2 and re.search(r'[+\-×x*÷=]| more | left | altogether | in all | total ', stem.lower())) \
                       or re.search(r'\d+\s*[+\-×x*÷]\s*\d+', stem)
            if solvable:
                new = stem
                for pat in REMOVABLE:
                    new = re.sub(pat + r'(?=[\s.,:;?]|$)', '', new, flags=re.I)
                new = re.sub(r'  +', ' ', new).strip()
                if new != stem and REF_RE.search(new) is None and len(new) > 15:
                    q['stem'] = new
                    fixes['missing_visual_ref_removed'] += 1
                    if len(fix_examples['missing_visual_ref_removed']) < 8:
                        fix_examples['missing_visual_ref_removed'].append((qid, repr(stem[:100]), repr(new[:100])))
                    changed = True
                else:
                    add_issue('missing_visual_ref', 'medium', qid, fname,
                              f'stem references visual ({m.group(0)!r}), svg null, could not safely strip: {stem[:110]!r}')
            else:
                add_issue('missing_visual_unsolvable', 'critical', qid, fname,
                          f'stem needs a visual ({m.group(0)!r}) but svg is null; not solvable from text: {stem[:120]!r}')
        if vr == 'essential':
            add_issue('essential_no_svg', 'critical', qid, fname,
                      f'visual_requirement=essential but no svg: {stem[:110]!r}')
        elif vr == 'required':
            add_issue('required_no_svg', 'medium', qid, fname,
                      f'visual_requirement=required but no svg: {stem[:90]!r}')
    return changed

# ---------------- check 5: hints ----------------
GARBLE1 = re.compile(r'\d[A-Z][a-z]')
GARBLE2 = re.compile(r'(?<!\.)\.\.(?!\.)')

def hint_check(q, fname):
    qid = q['id']
    h = q.get('hint')
    if not isinstance(h, dict):
        return False
    scanned['hints'] += 1
    stem = q.get('stem') or ''
    levels = [h.get('level_0') or '', h.get('level_1') or '', h.get('level_2') or '']
    changed = False
    flagged = False

    for i, lv in enumerate(levels):
        if not lv.strip():
            add_issue('hint_empty_level', 'high', qid, fname, f'level_{i} is empty')
            flagged = True

    norm = [lv.strip().lower() for lv in levels]
    pairs = [(i, j) for i in range(3) for j in range(i + 1, 3) if norm[i] and norm[i] == norm[j]]
    if pairs:
        steps = q.get('solution_steps') or []
        if steps and len(' '.join(steps)) > 15:
            i, j = pairs[0]
            h['level_%d' % j] = 'Step by step: ' + '. '.join(s.rstrip('.') for s in steps) + '.'
            fixes['hint_dup_level_replaced'] += 1
            changed = True
        else:
            add_issue('hint_identical_levels', 'medium', qid, fname,
                      f'levels {pairs} identical, no solution_steps to derive variant: {levels[pairs[0][0]][:80]!r}')
            flagged = True
        levels = [h.get('level_0') or '', h.get('level_1') or '', h.get('level_2') or '']

    stem_nums = set(nums_in(stem))
    if stem_nums:
        hint_nums = set(nums_in(' '.join(levels)))
        if not (stem_nums & hint_nums):
            add_issue('hint_all_generic', 'medium', qid, fname,
                      f'no hint level references any stem number {sorted(stem_nums)[:5]}: l1={levels[1][:70]!r}')
            flagged = True

    val, srcv = answer_value(q)
    n = to_num(val) if val is not None else None
    if n is not None:
        a = fmt(n)
        leak_res = [re.compile(r'=\s*' + re.escape(a) + r'\s*[.!]?\s*$'),
                    re.compile(r'\banswer(?:\s+is|:)\s*' + re.escape(a) + r'\b', re.I),
                    re.compile(r'\bequals\s+' + re.escape(a) + r'\s*[.!]?\s*$', re.I)]
        done = False
        for i, lv in enumerate(levels):
            for rex in leak_res:
                if rex.search(lv.strip()):
                    add_issue('hint_answer_leak', 'high', qid, fname,
                              f'level_{i} ends by handing over the answer {a!r}: ...{lv.strip()[-80:]!r}')
                    flagged = True
                    done = True
                    break
            if done:
                break

    for i, lv in enumerate(levels):
        mg = GARBLE1.search(lv) or GARBLE2.search(lv)
        if mg:
            add_issue('hint_garbled', 'medium', qid, fname, f'level_{i} garbled near {mg.group(0)!r}: {lv[:90]!r}')
            flagged = True
            break

    if not flagged:
        clean['hints'] += 1
    return changed

# ---------------- main ----------------
random.seed(42)
sample_pool = []
files = sorted(glob.glob(os.path.join(ROOT, 'grade*', 'g*-*.json')))
assert files, ROOT
for path in files:
    fname = os.path.relpath(path, ROOT)
    with open(path) as f:
        data = json.load(f)
    qs = data['questions']
    file_changed = False
    for q in qs:
        ch1, _ = stem_check(q, fname)
        ch4 = answer_check(q, fname)
        visual_check(q, fname)
        ch3 = missing_visual_check(q, fname)
        ch5 = hint_check(q, fname)
        if ch1 or ch3 or ch4 or ch5:
            file_changed = True
    k = max(1, round(60 * len(qs) / 20056))
    for q in random.sample(qs, min(k, len(qs))):
        sample_pool.append((fname, q))
    if FIX and file_changed:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=True)
        json.load(open(path))  # verify parse

issue_counts = Counter((i['check'], i['severity']) for i in issues)
print('=== SCANNED ===')
for k, v in sorted(scanned.items()):
    print(f'  {k}: {v}')
print('=== CLEAN ===')
for k, v in sorted(clean.items()):
    print(f'  {k}: {v}')
print('=== AUTO-FIXES%s ===' % ('' if FIX else ' (DRY RUN)'))
for k, v in sorted(fixes.items()):
    print(f'  {k}: {v}')
print('=== FLAGGED ===')
for (chk, sev), v in sorted(issue_counts.items()):
    print(f'  {chk} [{sev}]: {v}')

here = os.path.dirname(os.path.abspath(__file__))
json.dump({'fixes': dict(fixes), 'scanned': dict(scanned), 'clean': dict(clean)}, open(os.path.join(here, 'scan_summary.json'), 'w'), indent=2)
json.dump(issues, open(os.path.join(here, 'v4_issues.json'), 'w'), indent=2)
json.dump(dict(fix_examples), open(os.path.join(here, 'fix_examples.json'), 'w'), indent=2, default=str)
random.shuffle(sample_pool)
json.dump([{'file': fn, 'id': q['id'], 'stem': q.get('stem'), 'choices': q.get('choices'),
            'correct_answer': q.get('correct_answer'), 'correct_value': q.get('correct_value'),
            'hint': q.get('hint'), 'grade': q.get('adaptive_grade'),
            'has_svg': bool(q.get('visual_svg')), 'visual_context': q.get('visual_context'),
            'diagnostics': q.get('diagnostics')} for fn, q in sample_pool[:60]],
          open(os.path.join(here, 'reading_sample.json'), 'w'), indent=2)
print('done. issues:', len(issues))
