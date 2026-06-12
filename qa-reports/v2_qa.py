#!/usr/bin/env python3
"""Kiwimath content-v2 full QA pass. Scan + (optionally) auto-fix.
Usage: python3 v2_qa.py [--fix]
Writes v2_issues.json next to itself.
"""
import json, re, os, sys, glob, collections, random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', 'content-live', 'content-v2'))
FIX = '--fix' in sys.argv

issues = []
def add(check, severity, qid, file, detail):
    issues.append({'check': check, 'severity': severity, 'id': qid,
                   'file': file, 'detail': detail})

def reg():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'topic-*', '*.json'))):
        out.append((f, 'topic'))
    # benjamin-olympiad may be quarantined (moved to ../quarantine/) — skip if absent
    ben_orig = os.path.join(ROOT, 'benjamin-olympiad/grade6/benjamin_g6_questions.json')
    ben_var = os.path.join(ROOT, 'benjamin-olympiad/grade6/benjamin_variants.json')
    if os.path.exists(ben_orig):
        out.append((ben_orig, 'benjamin_orig'))
    if os.path.exists(ben_var):
        out.append((ben_var, 'benjamin_var'))
    for f in sorted(glob.glob(os.path.join(ROOT, 'wavebook', '*.json'))):
        out.append((f, 'wavebook'))
    for cur in ['ncert', 'singapore', 'igcse', 'icse']:
        for f in sorted(glob.glob(os.path.join(ROOT, cur + '-curriculum', '*', '*.json'))):
            if 'manifest' in f: continue
            out.append((f, 'curric'))
    return out

def load(f):
    with open(f, encoding='utf-8') as fh:
        return json.load(fh)

def get_qs(doc):
    return doc['questions'] if isinstance(doc, dict) else doc

# ---------- numeric helpers ----------
FRAC = re.compile(r'^(\d+)\s*/\s*(\d+)$')
UNIT_RE = re.compile(r'\s*(sq\.?\s*(cm|m|km|mm|in|ft|units?)?|square\s+\w+|(cm|m|km|mm|kg|g|mg|ml|l)[²³23]?|litres?|liters?|minutes?|mins?|hours?|hrs?|seconds?|secs?|days?|weeks?|years?|rupees?|dollars?|cents?|paise|units?|degrees?|°|points?|marbles?|apples?|students?|books?)\.?\s*$', re.I)
def parse_num(s):
    if s is None: return None
    if isinstance(s, (int, float)) and not isinstance(s, bool): return float(s)
    t = str(s).strip()
    t = re.sub(r'^[₹$€£]\s*|^Rs\.?\s*', '', t)
    prev = None
    while prev != t:
        prev = t; t = UNIT_RE.sub('', t).strip()
    t = t.replace(',', '').replace('²', '').replace('³', '').strip()
    m = FRAC.match(t)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return a / b if b else None
    if re.match(r'^-?\d+(\.\d+)?$', t): return float(t)
    m3 = re.match(r'^(-?\d+(\.\d+)?)\s*%$', t)
    if m3: return float(m3.group(1))
    return None

def ans_index(q):
    ca = q.get('correct_answer'); ch = q.get('choices') or []
    if isinstance(ca, bool): return None
    if isinstance(ca, int):
        return ca if 0 <= ca < len(ch) else None
    if isinstance(ca, str):
        s = ca.strip()
        if len(s) == 1 and s in 'ABCDE' and ch:
            i = ord(s) - 65
            return i if i < len(ch) else None
        for i, c in enumerate(ch):
            if str(c).strip().lower() == s.lower(): return i
        v = parse_num(s)
        if v is not None:
            for i, c in enumerate(ch):
                cv = parse_num(c)
                if cv is not None and abs(cv - v) < 1e-9: return i
    return None

def set_answer(q, idx):
    ca = q.get('correct_answer')
    if isinstance(ca, int): q['correct_answer'] = idx
    elif isinstance(ca, str) and len(ca.strip()) == 1 and ca.strip() in 'ABCDE':
        q['correct_answer'] = chr(65 + idx)
    else:
        q['correct_answer'] = str(q['choices'][idx])

def fnum(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else ('%g' % x)

def safe_eval(ex):
    e = ex.replace('×', '*').replace('÷', '/').replace('−', '-')
    e = re.sub(r'(?<=[\d\s])[xX](?=[\d\s])', '*', e)
    e = e.replace(',', '')
    if not re.match(r'^[\d\s\.\+\-\*/\(\)]+$', e): return None
    if not re.search(r'\d', e): return None
    try:
        v = eval(e, {'__builtins__': {}}, {})
        return float(v)
    except Exception:
        return None

# ---------- D4 computation ----------
def all_ints(s):
    return [int(x) for x in re.findall(r'\d+', s.replace(',', ''))]

def compute(stem):
    """returns (value, confidence 'high'|'med'|'low', label) or None"""
    s = stem
    has_var = bool(re.search(r'\dx\b|\bx\d|\bx\b|\by\b|\bn\b.*term|equals?|=(?!\s*\?\s*$)', s, re.I)) and '=' in s
    # 1. explicit pure-numeric expression
    m = re.search(r'(?:what is|calculate[:\s]|compute[:\s]|evaluate[:\s])\s*([\d\s,\.\+\-×÷/\(\)\*]+?)\s*(?:=\s*\?|\?|$)', s, re.I)
    if m:
        ex = m.group(1).strip().rstrip('=').strip()
        if re.search(r'[\+\-×\*÷/]', ex) and not re.search(r'[a-wyzA-WYZ]', ex):
            v = safe_eval(ex)
            if v is not None: return v, 'high', 'expr:' + ex[:40]
    # 2. percent-of (direct only)
    m = re.search(r'(?:what is|find|calculate)\s*:?\s*(\d+(?:\.\d+)?)\s*%\s*of\s+(?:Rs\.?\s*|\$)?([\d,]+)\b', s, re.I)
    if m and not re.search(r'\bx\b|equal', s, re.I):
        return float(m.group(1)) / 100 * float(m.group(2).replace(',', '')), 'high', 'percent-of'
    # 3. fraction-of chain (direct only)
    m = re.search(r'what is\s+((?:\d+\s*/\s*\d+\s+of\s+)+)([\d,]+)\b(?!\s*/)', s, re.I)
    if m and not re.search(r'\bx\b|equal|number', s, re.I):
        v = float(m.group(2).replace(',', ''))
        for fm in re.finditer(r'(\d+)\s*/\s*(\d+)', m.group(1)):
            a, b = int(fm.group(1)), int(fm.group(2))
            if not b: return None
            v = v * a / b
        return v, 'high', 'fraction-of'
    # 4. place value
    m = re.search(r'place value of (?:the digit )?(\d) in (?:the number )?([\d,]+)', s, re.I)
    if m and re.search(r'difference|product|sum|face value|add|times', s, re.I):
        m = None
    if m:
        d, n = m.group(1), m.group(2).replace(',', '')
        if d in n:
            pos = n.index(d)
            return float(int(d) * 10 ** (len(n) - pos - 1)), 'high', 'place-value'
    # 4b. which digit is in the tens/hundreds place of N
    m = re.search(r'in the number ([\d,]+),? what digit is in the (ones|tens|hundreds|thousands) place', s, re.I)
    if m:
        n = m.group(1).replace(',', '')
        idx = {'ones': 1, 'tens': 2, 'hundreds': 3, 'thousands': 4}[m.group(2).lower()]
        if len(n) >= idx:
            return float(n[-idx]), 'high', 'digit-place'
    # 5. constant-step sequence (next term only)
    if not re.search(r'th term|term of|rule', s, re.I):
        m = re.search(r'((?:\d+(?:\.\d+)?\s*,\s*){3,})\s*(?:\?|_+|…)', s)
        if m and re.search(r'comes next|next number|next term|missing|what number|complete', s, re.I):
            nums = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', m.group(1))]
            if len(nums) >= 4:
                d = nums[1] - nums[0]
                if abs(d) > 1e-9 and all(abs(nums[i+1] - nums[i] - d) < 1e-9 for i in range(len(nums) - 1)):
                    return nums[-1] + d, 'high', 'sequence'
    # 6. geometry (single plain shape, direct ask)
    shapes = [w for w in ('square', 'rectangle', 'triangle', 'circle') if w in s.lower()]
    blocked = re.search(r'same|total|combined|attached|shaded|two|identical|half|cut|fold|remove|midpoint|joins?|smaller|larger|inscribed|diagonal|grid', s, re.I)
    ask = re.search(r'(?:what is|find)(?: the)? (perimeter|area)\b', s, re.I)
    if ask and not blocked and len(set(shapes)) == 1:
        kind = ask.group(1).lower()
        if shapes[0] == 'rectangle':
            m = re.search(r'length(?: of| is|:)?\s*(?:is\s*)?(\d+(?:\.\d+)?).{0,40}?(?:width|breadth)(?: of| is|:)?\s*(?:is\s*)?(\d+(?:\.\d+)?)', s, re.I)
            if m:
                L, W = float(m.group(1)), float(m.group(2))
                return (2 * (L + W) if kind == 'perimeter' else L * W), 'high', 'rect-' + kind
        if shapes[0] == 'square':
            m = re.search(r'side(?: length)?(?: of| is|:)?\s*(?:is\s*)?(\d+(?:\.\d+)?)', s, re.I)
            if m:
                a = float(m.group(1))
                return (4 * a if kind == 'perimeter' else a * a), 'high', 'square-' + kind
    # 7. "A less/more than B"
    m = re.search(r'number that is (\d+(?:\.\d+)?) (less|more|fewer|greater) than (\d+(?:\.\d+)?)', s, re.I)
    if m:
        a, b = float(m.group(1)), float(m.group(3))
        v = b - a if m.group(2).lower() in ('less', 'fewer') else b + a
        return v, 'high', 'rel-number'
    # 8. change from payment
    m = re.search(r'(?:for|costs?)\s+(?:Rs\.?\s*|\$|₹)?(\d+(?:\.\d+)?)\s*(?:rupees?|dollars?)?\b.{0,60}?pays? with (?:a\s*)?(?:Rs\.?\s*|\$|₹)?(\d+(?:\.\d+)?)', s, re.I)
    if m and re.search(r'change', s, re.I):
        used = [float(m.group(1)), float(m.group(2))]
        conf = 'high' if sorted(all_ints(s)) == sorted(int(u) for u in used) else 'low'
        return used[1] - used[0], conf, 'change'
    # 9. number-line jumps
    m = re.search(r'starts? at (\d+) and jumps (\d+) times by (\d+)', s, re.I)
    if m:
        st, k, j = (float(m.group(i)) for i in (1, 2, 3))
        return st + k * j, 'med', 'jumps'
    # 10. legs/wings multiplication
    m = re.search(r'\b(?:a|an|each|every|one)\s+\w+ has (\d+) (\w+?)s?\.\s*how many \2s? (?:do|does|are|will) (\d+)', s, re.I)
    if m:
        return float(m.group(1)) * float(m.group(3)), 'med', 'unit-multiply'
    # 11. rows × columns
    m = re.search(r'(\d+) rows?,? (?:of|with) (\d+)(?: \w+)? in each(?: row)?', s, re.I)
    if m and re.search(r'how many .{0,40}(total|in all|altogether|are there)', s, re.I):
        used = sorted([int(m.group(1)), int(m.group(2))])
        conf = 'med' if sorted(all_ints(s)) == used else 'low'
        return float(m.group(1)) * float(m.group(2)), conf, 'rows-cols'
    # 12. pictograph symbol value
    m = re.search(r'=\s*(\d+)\s+(\w+)\.\s.{0,80}?has (\d+)', s)
    if m and re.search(r'how many', s, re.I):
        return float(m.group(1)) * float(m.group(3)), 'med', 'pictograph'
    # 13. missing number: a op ? = c  /  ? op a = c
    m = re.search(r'(\d+(?:\.\d+)?)\s*([\+\-×÷])\s*\?\s*=\s*(\d+(?:\.\d+)?)', s)
    if m:
        a, op, c = float(m.group(1)), m.group(2), float(m.group(3))
        v = {'+': c - a, '-': a - c, '×': c / a if a else None, '÷': a / c if c else None}[op]
        if v is not None: return v, 'high', 'missing-number'
    m = re.search(r'\?\s*([\+\-×÷])\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)', s)
    if m:
        a, op, c = float(m.group(2)), m.group(1), float(m.group(3))
        v = {'+': c - a, '-': c + a, '×': c / a if a else None, '÷': c * a}[op]
        if v is not None: return v, 'high', 'missing-number'
    # 14. sum of digits
    m = re.search(r'sum of (?:the )?digits of (\d+)', s, re.I)
    if m:
        return float(sum(int(d) for d in m.group(1))), 'high', 'digit-sum'
    # 15. letter substitution: If A=3 and B=9, what is A+B+A?
    assigns = dict(re.findall(r'\b([A-Z])\s*=\s*(\d+)', s))
    m = re.search(r'what is ([A-Z](?:\s*[\+\-×]\s*[A-Z])+)\s*\?', s)
    if assigns and m:
        ex = m.group(1)
        if all(t in assigns for t in re.findall(r'[A-Z]', ex)):
            for L, n in assigns.items():
                ex = re.sub(r'\b' + L + r'\b', n, ex)
            v = safe_eval(ex)
            if v is not None: return v, 'high', 'letter-arith'
    # 16. additive/subtractive chain word problem
    v = wp_chain(s)
    if v is not None: return v
    return None

GIVE_RE = re.compile(r'\b(gives?|gave|loses?|lost|eats?|ate|sells?|sold|spends?|spent|breaks?|broke|drops?|dropped|uses?|used|pops?|donates?|flies away|fly away|melts?)\b[^.0-9]{0,40}?(\d+)', re.I)
GET_RE = re.compile(r'\b(gets?|got|buys?|bought|finds?|found|receives?|received|picks?|picked|adds?|added|wins?|won|collects?|earns?|makes?)\b[^.0-9]{0,40}?(\d+)|(\d+) more (?:\w+ )?(?:arrive|come|join|appear)|(?:another|extra) (\d+)', re.I)
def wp_chain(s):
    m = re.search(r'\b(?:has|have|had|with|are|is|holds?|contains?|owns?|counts?)\s+(\d+)\b', s, re.I)
    if not m: return None
    if not re.search(r'how (?:many|much)\b.{0,60}\b(left|remain|now|in (?:all|total)|altogether|does \w+ have)', s, re.I):
        return None
    if re.search(r'each|every|per|twice|double|half|equal|share|split|times', s, re.I):
        return None
    start = float(m.group(1)); used = [int(m.group(1))]
    rest = s[m.end():]
    val = start; found_op = False
    # "gives <someone> N more" = receiving, handle first and mask out
    for gm in re.finditer(r'\bgives? (?!away)(?:\w+ )?(\d+) more\b', rest, re.I):
        val += float(gm.group(1)); used.append(int(gm.group(1))); found_op = True
    rest2 = re.sub(r'\bgives? (?!away)(?:\w+ )?\d+ more\b', ' ', rest, flags=re.I)
    for gm in GIVE_RE.finditer(rest2):
        val -= float(gm.group(2)); used.append(int(gm.group(2))); found_op = True
    for gm in GET_RE.finditer(rest2):
        n = gm.group(2) or gm.group(3) or gm.group(4)
        if n: val += float(n); used.append(int(n)); found_op = True
    if not found_op: return None
    conf = 'med' if sorted(all_ints(s)) == sorted(used) else 'low'
    return val, conf, 'wp-chain'

def _gcd(a, b):
    while b: a, b = b, a % b
    return a

def orig_op_note(stem, ans_val):
    """guess which operation on the stem's two main numbers yields the keyed answer"""
    if ans_val is None: return ''
    ints = [n for n in all_ints(stem) if n > 1]
    if len(ints) != 2: return ''
    a, b = ints
    cands = []
    for name, v in [('a-b', a - b), ('b-a', b - a), ('a×b', a * b),
                    ('a÷b', a / b if b else None), ('a^b', float(a) ** b if b < 12 and a < 100 else None),
                    ('lcm', a * b // _gcd(a, b) if a and b else None),
                    ('gcd', _gcd(a, b)), ('a+b', a + b)]:
        if v is not None and abs(v - ans_val) < 1e-9:
            cands.append(name)
    return f' | key matches {"/".join(cands)} of {a},{b} — original op differs from rewritten stem' if cands else ''

def comparison_check(q, stem):
    m = re.search(r'which (?:number |one )?is (?:the )?(greater|greatest|larger|largest|bigger|biggest|smaller|smallest|less)', stem, re.I)
    if not m: return None
    word = m.group(1).lower()
    bigger = word in ('greater', 'greatest', 'larger', 'largest', 'bigger', 'biggest')
    # powers form: 2^10 or 10^3
    pows = re.findall(r'(\d+)\s*\^\s*(\d+)', stem)
    if pows:
        terms = [(f'{a}^{b}', float(a) ** float(b)) for a, b in pows]
        if len(terms) >= 2:
            best = max(terms, key=lambda t: t[1]) if bigger else min(terms, key=lambda t: t[1])
            if len({t[1] for t in terms}) == 1: best = ('They are equal', None)
            return ('text', best[0], [t[0] for t in terms])
    nums = [float(x.replace(',', '')) for x in re.findall(r'\d[\d,]*(?:\.\d+)?', stem)]
    if len(nums) < 2: return None
    want = max(nums) if bigger else min(nums)
    return ('num', want, nums)

# ---------- D1 text cleanup / artifacts ----------
OLD_CHARS = ['Knight Koko', 'Chef Cheetah', 'Professor Panda', 'Ninja Nemo', 'Astronaut Ava',
             'Captain Carrot', 'Detective Duck', 'Wizard Whiskers', 'Pirate Penny', 'Robot Rex']
KNOWN_CHARS = {'Kiwi', 'Chikoo', 'Aarohi', 'Vanya', 'Riya', 'Ved', 'Nuha', 'Google', 'Veronica'}
SENT_SPLIT = re.compile(r'(?<=[.!?])\s+')

def clean_stem(stem):
    fixes = []
    s = stem
    if '  ' in s and '\n' not in s and '|' not in s:
        s = re.sub(r'  +', ' ', s); fixes.append('double-space')
    # stray ' ,' between letter and following space+word
    new = re.sub(r'(?<=[a-zA-Z]) ,(?= [a-zA-Z0-9])', ',', s)
    if new != s: s = new; fixes.append('stray-comma-space')
    new = re.sub(r'([.!?]\s+)(?:calculate|challenges|solve|compute):\s+(?=["\dA-Z])', r'\1', s)
    if new != s: s = new; fixes.append('filler-colon-dropped')
    if ',,' in s:
        s = s.replace(',,', ','); fixes.append('double-comma')
    if re.search(r'\?\?+', s):
        s = re.sub(r'\?\?+', '?', s); fixes.append('double-qmark')
    sents = SENT_SPLIT.split(s)
    if ORPHAN_RE.search(s):
        sents = [s]  # truncated stems: don't mask by deduping fragments
    if len(sents) > 1:
        seen, out, dropped = set(), [], False
        for sent in sents:
            key = re.sub(r'\W+', ' ', sent).strip().lower()
            if key and len(key) > 12 and key in seen:
                dropped = True; continue
            seen.add(key); out.append(sent)
        if dropped:
            s = ' '.join(out); fixes.append('dup-sentence')
    return s.strip(), fixes

ORPHAN_RE = re.compile(r"\b(with|to|of|by|from|and|for|at|into|than|is|are|was|near|beside|'s)\s+[.,]")
TRUNC_Q_RE = re.compile(r'\b(how old is|who is|what is|where is)\s*\?\s*$', re.I)
LOWER_START_RE = re.compile(r'[.!?]\s+([a-z][a-z]+s?\b(?!.{0,3}:))')
VERB_START_RE = re.compile(r'(?:^|[.!?]\s+)(Has|Arranges|Buys|Sells|Gets|Gives|Sees|Counts|Finds|Makes|Puts|Takes|Needs|Wants|Eats|Reads|Writes|Draws|Collects|Shares|Picks|Sorts|Builds|Plants|Bakes|Packs|Saves|Spends|Holds|Catches|Wins|Loses)\s+\d')
FILLER_COLON_RE = re.compile(r'[.!?]\s+([a-z][a-z]+):\s')
NAME_RE = re.compile(r'\b([A-Z][a-z]{2,})\b')
STOPWORDS = set('''The What How Which Who When Where Why There They Then And But For Not You Your His Her She Each Every Some All
One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve First Second Third Monday Tuesday Wednesday Thursday Friday Saturday
Sunday January February March April May June July August September October November December Use Find Look Count Help Now Next After
Before During Inside Outside Both Their This That These Those From With Into Onto Can Will Does Did Are Was Were Has Have Had
Its Out Off Over Under Between Around Read Write Solve Choose Select Answer Question True False Yes Note Hint Example Total Sum
India Indian Singapore Solve If In It Is At On To Of An As Football Cricket Tennis English Maths Science Red Blue Green Yellow'''.split())
PLACE_WORDS = set('''Island City Gate Forest Express Village Kingdom Tower Mountain River Lake Garden Market Station Bakery
Academy Ring Pond Cavern Den Castle Cave Bridge Harbor Harbour Port Bay Valley Hill Camp Base Lab Shop Store Cafe Mill Farm
Park Plaza Square Street Road Trail Path Festival Tour Race Rally Circuit Chamber Vault Room Hall Deck Dock Mine Grove'''.split())
VERBS_AFTER = r'\b(?:has|had|is|was|wants|counts|buys|bought|works|says|finds|found|makes|made|collects|gives|gave|gets|got|puts|sees|saw|asks|needs|takes|took|draws|drew|eats|ate|reads|writes|builds|spots|thinks|loves|likes|plays|starts|jumps|shares|sells|sold|picks)\b'

# ---------- D2/D3 visuals ----------
VIS_PHRASE = re.compile(r'\b(shown below|given below|shown above|in the (?:picture|figure|image|diagram)|the (?:picture|figure|diagram|image) (?:below|above|shows)|as shown|see the (?:picture|figure|diagram)|look at the (?:picture|figure|diagram|graph|image)|from the (?:graph|chart|picture|figure|diagram)|in the graph|the graph shows|pictured)\b', re.I)
VIS_WORD = re.compile(r'\b(figure|diagram|picture|image|graph|chart)\b', re.I)
FIGURE_IDIOM = re.compile(r'figure (?:this|it|out|s?\b.{0,6}out)', re.I)
VIS_KEYWORDS = ['pictograph', 'bar graph', 'bar chart', 'pie chart', 'number line', 'clock', 'tally', 'venn']

def svg_repeat_count(svg):
    if not svg: return None
    texts = re.findall(r'<text[^>]*>([^<]+)</text>', svg)
    glyphs = [t.strip() for t in texts if t.strip() and len(t.strip()) <= 3 and not t.strip().isdigit()]
    counter = collections.Counter(glyphs)
    if counter:
        g, n = counter.most_common(1)[0]
        if n >= 3: return n
    uses = re.findall(r'<use\b', svg)
    if len(uses) >= 3: return len(uses)
    return None

# ---------- D5 hints ----------
LEAK_RE = re.compile(r'(?:answer is|answer[:=]|correct answer is)\s*[\$₹]?\s*(-?[\d/]+(?:\.\d+)?|[A-E]\b)', re.I)
NUMPAT = r'\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?'
EQ_RE = re.compile(r'((?:(?:%s)\s*[\+\-×\*÷]\s*)+(?:%s))\s*=\s*(%s)' % (NUMPAT, NUMPAT, NUMPAT))
OCR_WORD = re.compile(r"\b[a-z]*(?:aa|uu|hh|jj|kk|qq|vv|ww|xx|([b-df-hj-np-tv-z])\1\1)[a-z]*\b")
OCR_START = re.compile(r"\b([bcdfghjklmnpqrstvwz])\1[a-z]+\b")
OCR_WHITELIST = {'bazaar', 'trekking', 'bookkeeper', 'bookkeeping', 'llama', 'vacuum', 'continuum'}

def hint_checks(q, qid, fname, stem, ans_val, ans_text):
    h = q.get('hint')
    if h is None: return False
    mutated = False
    if isinstance(h, str): h = {'level_0': h}
    if not isinstance(h, dict): return False
    levels = [(k, (h.get(k) or '').strip() if isinstance(h.get(k), str) else '') for k in sorted(h.keys())]
    nonempty = [(k, v) for k, v in levels if v]
    for k, v in levels:
        if not v:
            add('hint-empty-level', 'warn', qid, fname, f'{k} empty')
    vals = [v for _, v in nonempty]
    if len(vals) >= 2 and len(set(vals)) < len(vals):
        add('hint-identical-levels', 'warn', qid, fname, 'identical hint levels: ' + vals[0][:60])
    stem_nums = {n for n in re.findall(r'\d+', stem) if n not in ('0', '1')}
    if stem_nums and vals:
        if not any(n in v for v in vals for n in stem_nums):
            add('hint-no-stem-numbers', 'info', qid, fname, 'no hint level references any stem number')
    for k, v in nonempty:
        if k.endswith('2'): continue
        m = LEAK_RE.search(v)
        if m and ans_val is not None:
            leaked = parse_num(m.group(1))
            if leaked is not None and abs(leaked - ans_val) < 1e-9:
                add('hint-answer-leak', 'critical', qid, fname, f'{k}: "{v[-90:]}"')
                continue
        if ans_val is not None:
            m2 = re.search(r'=\s*[\$₹]?(-?\d+(?:\.\d+)?)\s*[\.\!]?\s*$', v)
            if m2 and abs(float(m2.group(1)) - ans_val) < 1e-9:
                add('hint-answer-leak', 'critical', qid, fname, f'{k} ends with "= {m2.group(1)}"')
    # wrong-working equations
    for k, v in list(nonempty):
        for m in EQ_RE.finditer(v):
            pre = v[:m.start()].rstrip()
            if pre and (pre[-1].isdigit() or pre[-1] in '+-×*÷='):
                continue  # partial match of a longer expression
            r = safe_eval(m.group(1))
            c = parse_num(m.group(2))
            if r is None or c is None: continue
            if abs(r - c) < 1e-6: continue
            # equation wrong; is RHS the keyed answer?
            rhs_is_ans = ans_val is not None and abs(c - ans_val) < 1e-9
            sev = 'warn' if rhs_is_ans else 'critical'
            chk = 'hint-wrong-working' if rhs_is_ans else 'hint-garbled-math'
            add(chk, sev, qid, fname,
                f'{k} states "{m.group(0)}" (actually = {fnum(r)})' + (' — RHS matches keyed answer (wrong working)' if rhs_is_ans else ''))
    return mutated

# ---------- per-question ----------
def check_question(q, qid, fname, setname, ctx):
    stem = q.get('stem') or ''
    choices = q.get('choices') or []
    mode = q.get('interaction_mode', 'mcq')
    mutated = False
    if not str(stem).strip():
        add('empty-stem', 'critical', qid, fname, 'stem is empty')
        return False

    # ----- D1 -----
    new_stem, fixes = clean_stem(stem)
    if fixes:
        add('stem-cleanup', 'autofix', qid, fname, ','.join(fixes) + ' | before: ' + stem[:110])
        if FIX:
            q['stem'] = new_stem; mutated = True
        stem = new_stem
    low = stem.lower()
    for oc in OLD_CHARS:
        if oc.lower() in low:
            add('old-character', 'critical', qid, fname, f'old character "{oc}" in stem')
    if 'workspace' in low:
        add('workspace-mention', 'critical', qid, fname, 'stem mentions "workspace"')
    ocr_words = {w for w in re.findall(r'[a-z]+', low)
                 if w not in OCR_WHITELIST and len(w) > 2 and (OCR_WORD.fullmatch(w) or OCR_START.fullmatch(w))
                 and not re.search(r'\b' + w[0].upper() + re.escape(w[1:]) + r'\b', stem)
                 and not re.fullmatch(r'(?:([a-z])\1)+', w)
                 and not re.fullmatch(r'[mdclxvi]+', w)}  # roman numerals (MCMLXXXI etc.)
    if ocr_words:
        add('ocr-garbled-stem', 'critical' if len(ocr_words) >= 2 else 'warn', qid, fname,
            'OCR-doubled letters in stem: ' + ', '.join(sorted(ocr_words)[:8]))
    m = ORPHAN_RE.search(stem)
    if m:
        add('truncated-sentence', 'critical', qid, fname,
            f'orphan "{m.group(0)}" — sentence missing a word: ...{stem[max(0,m.start()-40):m.end()+10]}')
    m = TRUNC_Q_RE.search(stem)
    if m and not re.search(r'\d\s*[\+\-×÷\*/=]', stem):
        add('truncated-sentence', 'critical', qid, fname,
            f'question ends "{m.group(0).strip()}" with missing subject: ...{stem[-60:]}')
    m = re.search(r'(?:^|[.!?]\s+)(Is|Are) (older|younger|taller|shorter|bigger|smaller|faster|slower) than\b', stem)
    if m:
        add('missing-subject', 'warn', qid, fname, f'sentence starts "{m.group(1)} {m.group(2)} than" with no subject')
    m = LOWER_START_RE.search(stem)
    if m and stem[max(0, m.start() - 1)].isdigit():
        m = None
    if m and m.group(1) not in ('e', 'g', 'i', 'cm', 'mm', 'km', 'kg', 'ml', 'vs'):
        add('broken-sentence-start', 'warn', qid, fname,
            f'sentence starts lowercase: "...{stem[max(0,m.start()-20):m.end()+25]}"')
    m = VERB_START_RE.search(stem)
    if m:
        add('missing-subject', 'warn', qid, fname,
            f'sentence starts with bare verb: "{m.group(0).strip()}..."')
    m = FILLER_COLON_RE.search(stem)
    if m:
        add('filler-colon-artifact', 'warn', qid, fname, f'leftover "{m.group(1)}:" mid-stem')
    if re.search(r'\bHelp\s+(How|What|Which|Find|Who)\b', stem):
        add('help-artifact', 'critical', qid, fname,
            'truncated "Help <name> with this:" wrapper — lost context: ' + stem[:100])
    m = re.search(r'(?:^|[.!?]\s+|—[^.!?]*\.\s+)It is divisible by (\d+)\. What is it\?', stem)
    if m:
        n = int(m.group(1))
        ok = None
        ch = q.get('choices') or []
        ai0 = ans_index(q)
        if ai0 is not None:
            kv = parse_num(ch[ai0])
            rng = re.search(r'greater than (\d+) and less than (\d+)', stem)
            if rng:
                lo, hi = int(rng.group(1)), int(rng.group(2))
                sols = [x for x in range(lo + 1, hi) if n and x % n == 0]
                if len(sols) == 1 and kv is not None and abs(kv - sols[0]) < 1e-9:
                    pass  # constraint present, unique solution, correctly keyed
                elif len(sols) == 1:
                    add('missing-constraint-bad-key', 'critical', qid, fname,
                        f'range ({lo},{hi}) divisible by {n} has unique solution {sols[0]} but key is "{ch[ai0]}"')
                else:
                    add('missing-constraint', 'critical', qid, fname,
                        f'range ({lo},{hi}) divisible by {n} has {len(sols)} solutions {sols[:5]} — not uniquely answerable')
            else:
                divs = [i for i, c in enumerate(ch) if (parse_num(c) or 0.5) % n == 0]
                if kv is None or kv % n != 0:
                    add('missing-constraint-bad-key', 'critical', qid, fname,
                        f'"It is divisible by {n}" with missing constraint sentence AND key "{ch[ai0]}" not divisible by {n}')
                elif len(divs) > 1:
                    add('missing-constraint', 'critical', qid, fname,
                        f'constraint sentence missing; {len(divs)} choices divisible by {n} — ambiguous')
                else:
                    add('missing-constraint', 'warn', qid, fname,
                        f'"I am thinking of a number..." sentence missing before "It is divisible by {n}" (still uniquely answerable)')
    if setname == 'topic':
        found_names = set()
        for nm in set(NAME_RE.findall(stem)) - KNOWN_CHARS - STOPWORDS - PLACE_WORDS:
            for nmm in re.finditer(r'\b' + re.escape(nm) + r'\b', stem):
                pre = stem[:nmm.start()].rstrip()
                if re.search(r'(?:[A-Z][a-z]+|[Tt]he|Mr\.|Mrs\.|Ms\.)$', pre): continue
                if re.match(r'\s+' + VERBS_AFTER, stem[nmm.end():]):
                    found_names.add(nm)
                    break
        if found_names:
            add('unknown-character', 'warn', qid, fname,
                'non-roster character name(s): ' + ', '.join(sorted(found_names)))

    # ----- choices sanity -----
    if choices:
        normch = [str(c).strip().lower() for c in choices]
        if len(set(normch)) < len(normch):
            dups = [c for c, n in collections.Counter(normch).items() if n > 1]
            add('duplicate-choices', 'critical', qid, fname, f'duplicate choices: {dups}')
        if ans_index(q) is None:
            add('answer-not-in-choices', 'critical', qid, fname,
                f'correct_answer={q.get("correct_answer")!r} does not resolve to a choice; choices={choices[:6]}')
    elif mode == 'mcq':
        add('no-choices', 'critical', qid, fname, 'mcq question has empty choices')
    ai = ans_index(q)
    ans_text = str(choices[ai]) if (ai is not None and choices) else None
    ans_val = parse_num(ans_text) if ans_text is not None else None
    if mode == 'integer' and q.get('correct_value') is not None:
        ans_val = parse_num(q.get('correct_value'))
        ans_text = str(q.get('correct_value'))

    # ----- D4 -----
    comp = compute(stem)
    if comp:
        val, conf, label = comp
        if mode == 'integer' and q.get('correct_value') is not None:
            if ans_val is not None and abs(ans_val - val) > 1e-6:
                add('wrong-answer-integer', 'critical' if conf == 'high' else 'warn', qid, fname,
                    f'[{label}] computed {fnum(val)} but correct_value={ans_text}')
        elif choices:
            chvals = [parse_num(c) for c in choices]
            match = [i for i, cv in enumerate(chvals) if cv is not None and abs(cv - val) < 1e-6]
            numeric_choices = sum(1 for cv in chvals if cv is not None)
            if ans_val is not None and abs(ans_val - val) < 1e-6:
                pass
            elif numeric_choices < 2:
                pass
            elif match and conf in ('high', 'med'):
                add('wrong-answer-fixed', 'autofix', qid, fname,
                    f'[{label},{conf}] computed {fnum(val)} = choice {match[0]} ("{choices[match[0]]}") but key was {q.get("correct_answer")!r} ("{ans_text}")')
                if FIX:
                    set_answer(q, match[0]); mutated = True
            elif match:
                add('wrong-answer-suspect', 'warn', qid, fname,
                    f'[{label},{conf}] computed {fnum(val)} (choice {match[0]}) but key = "{ans_text}" — review')
            elif conf == 'high':
                add('computed-not-in-choices', 'critical', qid, fname,
                    f'[{label}] computed {fnum(val)} not among choices {choices[:6]}; key="{ans_text}"' + orig_op_note(stem, ans_val))
            elif conf == 'med':
                add('computed-not-in-choices-wp', 'critical', qid, fname,
                    f'[{label}] computed {fnum(val)} not among choices {choices[:6]}; key="{ans_text}" — stem/key mismatch from story rewrite' + orig_op_note(stem, ans_val))
    cmpres = comparison_check(q, stem)
    if cmpres and choices:
        kind, want, operands = cmpres
        if kind == 'text':
            tnorm = [str(c).strip().replace(' ', '') for c in choices]
            if want.replace(' ', '') in tnorm:
                widx = tnorm.index(want.replace(' ', ''))
                if ai is not None and ai != widx:
                    add('comparison-wrong-key', 'critical', qid, fname,
                        f'power comparison: correct is "{want}" (choice {widx}) but key={q.get("correct_answer")!r}')
        else:
            chvals = [parse_num(c) for c in choices]
            has_operand = any(cv is not None and any(abs(cv - n) < 1e-9 for n in operands) for cv in chvals)
            if not has_operand:
                add('comparison-choices-broken', 'critical', qid, fname,
                    f'comparison of {operands[:4]} but no operand appears in choices {choices[:6]}')
            else:
                match = [i for i, cv in enumerate(chvals) if cv is not None and abs(cv - want) < 1e-9]
                if len(match) == 1 and ans_val is not None and abs(ans_val - want) > 1e-9:
                    add('comparison-wrong-key', 'autofix', qid, fname,
                        f'comparison answer should be {fnum(want)} (choice {match[0]}) but key="{ans_text}"')
                    if FIX:
                        set_answer(q, match[0]); mutated = True

    # ----- D2/D3 -----
    svg = q.get('visual_svg')
    svg_file = q.get('svg')
    if setname == 'wavebook' and svg_file:
        base = os.path.basename(svg_file)
        if base not in ctx.get('svg_files', set()):
            add('svg-ref-missing-file', 'critical', qid, fname, f'svg ref "{svg_file}" not found in wavebook/svg/')
        elif not svg:
            pass  # file exists; ok
    has_visual = bool(svg) or bool(svg_file and os.path.basename(svg_file or '') in ctx.get('svg_files', set()))
    stem_noidiom = FIGURE_IDIOM.sub('', stem)
    phrase_hit = VIS_PHRASE.search(stem_noidiom)
    word_hit = VIS_WORD.search(stem_noidiom)
    if (phrase_hit or word_hit) and not has_visual:
        phrase = (phrase_hit or word_hit).group(0)
        solvable = compute(stem) is not None
        droppable = bool(re.search(r'\b(shown below|given below|as shown|shown)\b', phrase, re.I))
        if solvable and droppable:
            ns = re.sub(r'\s*(shown below|given below|shown above|as shown|shown)[,:]?\s*', ' ', stem, flags=re.I)
            ns = re.sub(r'  +', ' ', ns).strip()
            ns2 = FIGURE_IDIOM.sub('', ns)
            if not (VIS_PHRASE.search(ns2) or VIS_WORD.search(ns2)) and len(ns) > 20:
                add('visual-ref-dropped', 'autofix', qid, fname, f'dropped "{phrase}" reference; text-solvable')
                if FIX:
                    q['stem'] = ns; mutated = True
            else:
                add('missing-visual', 'critical', qid, fname, f'stem says "{phrase}" but no svg')
        elif phrase_hit:
            add('missing-visual', 'critical', qid, fname,
                f'stem references "{phrase}" but question has no visual' + (' (text-solvable)' if solvable else ''))
        else:
            # bare word like "figure"/"chart" — may be non-visual sense
            if not re.search(r'which figure|figure\?|shaped like', low):
                add('visual-word-no-svg', 'warn', qid, fname,
                    f'stem mentions "{phrase}" but question has no visual (verify if visual sense)')
    vctx = ((q.get('visual_context') or '') + ' ' + (q.get('visual_alt') or '')).lower()
    if vctx.strip():
        for kw in VIS_KEYWORDS:
            if kw in vctx and kw not in low:
                conflict = [k2 for k2 in VIS_KEYWORDS if k2 != kw and not (kw in k2 or k2 in kw) and k2 in low]
                if conflict:
                    add('visual-context-mismatch', 'warn', qid, fname,
                        f'visual_context says "{kw}" but stem says "{conflict[0]}"')
    if svg and re.search(r'how many', low) and ans_val is not None and float(ans_val).is_integer():
        if not re.search(r'\d', stem):
            n = svg_repeat_count(svg)
            if n is not None and abs(n - ans_val) > 0.5:
                add('svg-count-mismatch', 'warn', qid, fname,
                    f'picture-count question: svg shows ~{n} repeated elements; keyed answer {fnum(ans_val)}')

    # ----- D5 -----
    if hint_checks(q, qid, fname, stem, ans_val, ans_text):
        mutated = True
    return mutated

# ---------- main ----------
def main():
    ctx_wb = {'svg_files': set(os.listdir(os.path.join(ROOT, 'wavebook', 'svg')))}
    stats = collections.defaultdict(lambda: collections.Counter())
    ben_first = [0, 0]; ben_recalc = [0, 0, 0]
    samples = []; rnd = random.Random(42)
    referenced_svgs = set()

    for fname, setname in reg():
        rel = os.path.relpath(fname, ROOT)
        try:
            doc = load(fname)
        except Exception as e:
            add('json-parse-error', 'critical', '-', rel, str(e)); continue
        qs = get_qs(doc)
        seen_ids = set(); mutated_any = False
        ctx = ctx_wb if setname == 'wavebook' else {}
        for q in qs:
            qid = q.get('id', '?')
            if qid in seen_ids:
                add('duplicate-id', 'critical', qid, rel, 'duplicate question id within file')
            seen_ids.add(qid)
            if setname == 'wavebook' and q.get('svg'):
                referenced_svgs.add(os.path.basename(q['svg']))
            n_before = len(issues)
            m = check_question(q, qid, rel, setname, ctx)
            mutated_any = mutated_any or m
            stats[setname]['scanned'] += 1
            qissues = issues[n_before:]
            if not [i for i in qissues if i['severity'] != 'info']:
                stats[setname]['clean'] += 1
            for it in qissues:
                stats[setname][it['severity']] += 1
            if setname == 'benjamin_orig':
                ben_first[1] += 1
                if q.get('correct_answer') == 0: ben_first[0] += 1
            if setname == 'benjamin_var':
                ben_recalc[2] += 1
                if q.get('needs_answer_recalc'): ben_recalc[0] += 1
                if not q.get('answer_verified'): ben_recalc[1] += 1
            if rnd.random() < 0.0065:
                samples.append((rel, qid))
        if FIX and mutated_any:
            with open(fname, 'w', encoding='utf-8') as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write('\n')
            load(fname)

    orphan = ctx_wb['svg_files'] - referenced_svgs
    if orphan:
        add('orphan-svg-files', 'info', '-', 'wavebook/svg', f'{len(orphan)} svg files not referenced by any question (e.g. {sorted(orphan)[:5]})')

    out = os.path.join(HERE, 'v2_issues.json')
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(issues, fh, indent=1, ensure_ascii=False)
    print('ISSUES:', len(issues))
    print('by severity:', dict(collections.Counter(i['severity'] for i in issues)))
    print('by check:')
    for c, n in collections.Counter(i['check'] for i in issues).most_common():
        print(f'  {c}: {n}')
    print('\nper-set stats:')
    for s, c in stats.items():
        print(f'  {s}: scanned={c["scanned"]} clean={c["clean"]} autofix={c["autofix"]} critical={c["critical"]} warn={c["warn"]} info={c["info"]}')
    print(f'\nBenjamin originals correct_answer==0: {ben_first[0]}/{ben_first[1]} ({100*ben_first[0]/max(1,ben_first[1]):.0f}%)')
    print(f'Benjamin variants needs_answer_recalc: {ben_recalc[0]}/{ben_recalc[2]}, unverified: {ben_recalc[1]}/{ben_recalc[2]}')
    print('\nsample refs:', len(samples))
    for s in samples: print(' ', s[0], s[1])

main()
