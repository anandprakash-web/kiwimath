#!/usr/bin/env python3
"""Fix pass for content-v2 QA findings (v2_issues.json).

Run AFTER v2_qa.py has produced v2_issues.json. Applies targeted repairs:
  - class2: Topic-2 stem/key mismatches from story-rewrite (restore math from original_stem)
  - class3: truncated-name logic stems / age chains / missing-side / missing-recipient
  - class4: T8 divisibility-constraint family (restore/repair range, re-key, or delete)
  - class5: arithmetically-false hint workings (recompute true equation)
  - class6: hint answer leaks (unsolve final equation / drop leak sentence)
  - class7: T1-1182 choice value -> 3332 (verified by inclusion-exclusion)
  - class8/9: "Help" truncations & missing-divisor stems (restore from original_stem or delete)
  - class10: bare-verb sentences (prepend unambiguous subject)
  - class11: visual_context "clock" on number-line questions

Anything broken beyond safe repair is DELETED from the file and the full question
object appended to v2_deleted_questions.json.
"""
import json, re, os, math, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', 'content-live', 'content-v2'))
ISSUES = json.load(open(os.path.join(HERE, 'v2_issues.json'), encoding='utf-8'))

counts = collections.Counter()
examples = collections.defaultdict(list)
deleted_log = []

ROSTER_JR = ['Kiwi', 'Chikoo', 'Aarohi', 'Vanya', 'Riya']
ROSTER_SR = ['Kiwi', 'Ved', 'Nuha', 'Google', 'Veronica']
ALL_ROSTER = set(ROSTER_JR) | set(ROSTER_SR)

SENT_SPLIT = re.compile(r'(?<=[.!?])\s+')
NUMPAT = r'\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?'
EQ_RE = re.compile(r'((?:(?:%s)\s*[\+\-×\*÷]\s*)+(?:%s))\s*=\s*(%s)' % (NUMPAT, NUMPAT, NUMPAT))
LEAK_RE = re.compile(r'(?:answer is|answer[:=]|correct answer is)\s*[\$₹]?\s*(-?[\d/]+(?:\.\d+)?|[A-E]\b)', re.I)
ORPHAN_RE = re.compile(r"\b(with|to|of|by|from|and|for|at|into|than|is|are|was|near|beside|'s)\s+[.,]")
TRUNC_Q_RE = re.compile(r'\b(how old is|who is|what is|where is)\s*\?\s*$', re.I)
VERB_START_RE = re.compile(r'(?:^|[.!?]\s+)(Has|Arranges|Buys|Sells|Gets|Gives|Sees|Counts|Finds|Makes|Puts|Takes|Needs|Wants|Eats|Reads|Writes|Draws|Collects|Shares|Picks|Sorts|Builds|Plants|Bakes|Packs|Saves|Spends|Holds|Catches|Wins|Loses)\s+\d')
TITLE_NAME = re.compile(r'\b(?:Captain|Detective|Professor|Chef|Knight|Ranger|Builder|Wizard|Pirate|Robot|Ninja|Astronaut|Farmer|Doctor|Coach|Sage)\s+([A-Z][a-z]+)\b')

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

def fnum(x):
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else ('%g' % x)

def safe_eval(ex):
    e = ex.replace('×', '*').replace('÷', '/').replace('−', '-')
    e = re.sub(r'(?<=[\d\s])[xX](?=[\d\s])', '*', e)
    e = e.replace(',', '')
    if not re.match(r'^[\d\s\.\+\-\*/\(\)]+$', e): return None
    if not re.search(r'\d', e): return None
    try:
        return float(eval(e, {'__builtins__': {}}, {}))
    except Exception:
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

def keyed_value(q):
    ch = q.get('choices') or []
    ai = ans_index(q)
    if ai is None: return None, None
    return ai, parse_num(ch[ai])

def set_choice_value(q, idx, val):
    """Replace a choice's text value, preserving string correct_answer if needed."""
    old = q['choices'][idx]
    q['choices'][idx] = str(val)
    ca = q.get('correct_answer')
    if isinstance(ca, str) and ca.strip() == str(old).strip():
        q['correct_answer'] = str(val)

# ---------------- file io ----------------
DOCS, RAWFMT, DIRTY = {}, {}, set()
to_delete = collections.defaultdict(set)

def getdoc(rel):
    if rel not in DOCS:
        p = os.path.join(ROOT, rel)
        raw = open(p, 'rb').read()
        RAWFMT[rel] = {'ascii': not any(b > 127 for b in raw), 'nl': raw.endswith(b'\n')}
        DOCS[rel] = json.loads(raw.decode('utf-8'))
    return DOCS[rel]

def qlist(doc):
    return doc['questions'] if isinstance(doc, dict) else doc

def getq(rel, qid):
    if rel.startswith('benjamin'): return None  # quarantined
    if not os.path.exists(os.path.join(ROOT, rel)): return None
    for q in qlist(getdoc(rel)):
        if q.get('id') == qid: return q
    return None

def mark_delete(rel, q, reason):
    if q['id'] in to_delete[rel]: return
    to_delete[rel].add(q['id'])
    deleted_log.append({'file': rel, 'reason': reason, 'question': q})
    counts['deleted'] += 1
    counts['deleted::' + reason.split(':')[0]] += 1
    DIRTY.add(rel)

def flagged(check):
    out = []
    seen = set()
    for i in ISSUES:
        if i['check'] != check: continue
        k = (i['file'], i['id'])
        if k in seen or i['file'].startswith('benjamin'): continue
        seen.add(k); out.append(k)
    return out

# ---------------- text helpers ----------------
FILLERS = [
    r"^Help\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(?:solve this|with this|figure (?:this|it) out)[:!.]\s*",
    r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(?:needs your help|presents|challenges you|asks|wonders|says|needs to work out|needs to figure out|wants to solve|is working on[^:]{0,40}|is solving[^:]{0,40}|checks? the [^:]{0,30})[:!.]\s*",
    r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+is (?:helping|counting|sorting)\s[^.!?]*[.!?]\s*",
]
def strip_filler(text):
    t = (text or '').strip()
    changed = True
    while changed:
        changed = False
        for f in FILLERS:
            new = re.sub(f, '', t, count=1)
            if new != t:
                t = new.strip(); changed = True
    return TITLE_NAME.sub(lambda m: m.group(1), t)

def story_intro(stem):
    parts = SENT_SPLIT.split((stem or '').strip())
    keep = []
    for s in parts:
        if re.search(r'\d', s): break
        if ' than ' in s: break
        if re.match(r'(?:Has|Arranges|Buys|Gets|Gives|Is|Are|Help)\b', s): break
        if re.search(r'\bHow (?:many|much|old)\b|\bWhat (?:is|goes|fraction|number)\b|\bWho (?:is|has)\b|\bWhich\b', s): break
        keep.append(s)
        if len(keep) >= 2: break
    return ' '.join(keep).strip()

def roster_for(rel):
    return ROSTER_SR if ('grade34' in rel or 'g56' in rel) else ROSTER_JR

def intro_name(intro, rel):
    for n in re.findall(r'[A-Z][a-z]+', intro or ''):
        if n in ALL_ROSTER: return n
    return roster_for(rel)[0]

def fresh_name(rel, used_text):
    for n in roster_for(rel):
        if not re.search(r'\b' + n + r'\b', used_text): return n
    return 'Chikoo'

# ---------------- core verification (original_stem math vs keyed answer) ----------------
def verify_core(core, q):
    """True = verified consistent; False = contradicts key; None = unverifiable."""
    ai, kv = keyed_value(q)
    ch = q.get('choices') or []
    c = core
    m = re.search(r'What is (\d+)\s*\^\s*(\d+)\?', c)
    if m and kv is not None:
        return abs(int(m.group(1)) ** int(m.group(2)) - kv) < 1e-9
    m = re.search(r'least common multiple of (\d+) and (\d+)', c, re.I)
    if m and kv is not None:
        a, b = int(m.group(1)), int(m.group(2))
        return abs(a * b // math.gcd(a, b) - kv) < 1e-9
    m = re.search(r'greatest common (?:divisor|factor) of (\d+) and (\d+)', c, re.I)
    if m and kv is not None:
        return abs(math.gcd(int(m.group(1)), int(m.group(2))) - kv) < 1e-9
    m = re.search(r'remainder when (\d+)(?:\s*\^\s*(\d+))? is divided by (\d+)', c, re.I)
    if m and kv is not None:
        return pow(int(m.group(1)), int(m.group(2) or 1), int(m.group(3))) == int(kv)
    m = re.search(r'divisible by both (\d+) and (\d+)', c, re.I)
    if m and ai is not None:
        a, b = int(m.group(1)), int(m.group(2))
        vals = [parse_num(x) for x in ch]
        good = [i for i, v in enumerate(vals) if v is not None and v % a == 0 and v % b == 0]
        return len(good) == 1 and good[0] == ai
    m = re.search(r'[Ww]hich is larger:\s*(\d+)\^(\d+) or (\d+)\^(\d+)', c)
    if m and ai is not None:
        v1 = int(m.group(1)) ** int(m.group(2)); v2 = int(m.group(3)) ** int(m.group(4))
        want = '%s^%s' % (m.group(1), m.group(2)) if v1 > v2 else ('%s^%s' % (m.group(3), m.group(4)) if v2 > v1 else 'equal')
        return str(ch[ai]).replace(' ', '') == want
    m = re.search(r'(\d+)\s*([+\-−×÷])\s*___\s*=\s*(\d+)', c)
    if m and kv is not None:
        a, op, r2 = float(m.group(1)), m.group(2), float(m.group(3))
        v = {'+': r2 - a, '-': a - r2, '−': a - r2,
             '×': (r2 / a if a else None), '÷': (a / r2 if r2 else None)}[op]
        return v is not None and abs(v - kv) < 1e-9
    m = re.search(r'___\s*([+\-−×÷])\s*(\d+)\s*=\s*(\d+)', c)
    if m and kv is not None:
        b, op, r2 = float(m.group(2)), m.group(1), float(m.group(3))
        v = {'+': r2 - b, '-': r2 + b, '−': r2 + b,
             '×': (r2 / b if b else None), '÷': r2 * b}[op]
        return v is not None and abs(v - kv) < 1e-9
    m = re.search(r'What is ((?:\d|[\s,\.\+\-×÷*/()−])+)\?', c)
    if m and kv is not None and re.search(r'[\+\-×÷*/−]', m.group(1)):
        v = safe_eval(m.group(1))
        if v is not None: return abs(v - kv) < 1e-9
    m = re.search(r'Evaluate:\s*([\d\s,\.\+\-×÷*/()−]+)', c)
    if m and kv is not None:
        v = safe_eval(m.group(1))
        if v is not None: return abs(v - kv) < 1e-9
    # word-problem shapes used by help-artifact originals
    m = re.search(r'(\d+) rows and (\d+) columns', c)
    if m and kv is not None:
        return abs(int(m.group(1)) * int(m.group(2)) - kv) < 1e-9
    m = re.search(r'(\d+) bunches of \w+ with (\d+)', c)
    if m and kv is not None:
        return abs(int(m.group(1)) * int(m.group(2)) - kv) < 1e-9
    m = re.search(r'prints (\d+) pages per minute\. How many pages in (\d+) minutes', c)
    if m and kv is not None:
        return abs(int(m.group(1)) * int(m.group(2)) - kv) < 1e-9
    m = re.search(r'shares (\d+) \w+ equally among (\d+)', c)
    if m and kv is not None and int(m.group(2)):
        return abs(int(m.group(1)) / int(m.group(2)) - kv) < 1e-9
    m = re.search(r'rectangle has length (\d+) cm and width (\d+) cm\. What is its perimeter', c, re.I)
    if m and kv is not None:
        return abs(2 * (int(m.group(1)) + int(m.group(2))) - kv) < 1e-9
    m = re.search(r'(\d+) cubes long, (\d+) cubes wide, and (\d+) cubes tall', c)
    if m and kv is not None:
        a, b, d = (int(m.group(i)) for i in (1, 2, 3))
        return abs(a * b * d - kv) < 1e-9
    return None

# ---------------- class 4: T8 divisibility-constraint family ----------------
def fix_t8():
    items = flagged('missing-constraint') + flagged('missing-constraint-bad-key')
    for rel, qid in items:
        q = getq(rel, qid)
        if q is None or qid in to_delete[rel]: continue
        stem = q['stem']
        ai, kv = keyed_value(q)
        m_div = re.search(r'It is divisible by (\d+)\. What is it\?', stem)
        if m_div is None or ai is None or kv is None or abs(kv - round(kv)) > 1e-9:
            mark_delete(rel, q, 'class4: unparseable constraint/key'); continue
        k = int(round(kv)); d = int(m_div.group(1))
        # strip stray title-word junk before the constraint ("... Ranger I am thinking ...")
        stem = re.sub(r'(?<=[.!?] )(?:Ranger|Captain|Chef|Knight|Builder|Detective|Wizard|Pirate|Robot|Professor|Ninja|Astronaut)\s+(?=I am)', '', stem)
        # restore the range sentence from original_stem if missing
        m_rng = re.search(r'greater than (\d+) and less than (\d+)', stem)
        if not m_rng:
            orig = q.get('original_stem') or ''
            mo = re.search(r'(I am thinking of a number greater than \d+ and less than \d+\.)\s*It is divisible by', orig)
            if mo:
                stem = stem.replace('It is divisible by', mo.group(1) + ' It is divisible by', 1)
                m_rng = re.search(r'greater than (\d+) and less than (\d+)', stem)
        def set_range(s, lo, hi):
            if re.search(r'greater than \d+ and less than \d+', s):
                return re.sub(r'greater than \d+ and less than \d+', 'greater than %d and less than %d' % (lo, hi), s, count=1)
            return s.replace('It is divisible by', 'I am thinking of a number greater than %d and less than %d. It is divisible by' % (lo, hi), 1)
        fixed = False
        if k % d == 0 and d >= 2:
            if m_rng:
                lo, hi = int(m_rng.group(1)), int(m_rng.group(2))
                sols = [x for x in range(lo + 1, hi) if x % d == 0]
                if sols == [k]:
                    fixed = True  # already consistent (maybe only the sentence was missing)
            if not fixed:
                stem = set_range(stem, k - d, k + d)  # unique multiple of d in open interval = k
                fixed = True
        else:
            # key not divisible by stated divisor
            if m_rng:
                lo, hi = int(m_rng.group(1)), int(m_rng.group(2))
                sols = [x for x in range(lo + 1, hi) if d and x % d == 0]
                if len(sols) == 1:
                    t = sols[0]
                    others = [parse_num(c) for i, c in enumerate(q['choices']) if i != ai]
                    if not any(o is not None and abs(o - t) < 1e-9 for o in others):
                        set_choice_value(q, ai, t)  # true unique answer replaces placeholder key value
                        fixed = True
            if not fixed:
                divs = [x for x in range(12, 1, -1) if k % x == 0]
                if divs:
                    d2 = divs[0]
                    stem = re.sub(r'It is divisible by \d+\.', 'It is divisible by %d.' % d2, stem, count=1)
                    stem = set_range(stem, k - d2, k + d2)
                    fixed = True
        if fixed:
            q['stem'] = stem
            counts['class4-fixed'] += 1
            DIRTY.add(rel)
        else:
            mark_delete(rel, q, 'class4: cannot make exactly one valid answer')

# ---------------- class 2: topic-2 stem/key mismatches ----------------
def fix_class2():
    for rel, qid in flagged('computed-not-in-choices-wp'):
        q = getq(rel, qid)
        if q is None or qid in to_delete[rel]: continue
        before = q['stem']
        ai, kv = keyed_value(q)
        orig = (q.get('original_stem') or '').strip()
        if not orig or kv is None:
            mark_delete(rel, q, 'class2: no original_stem/keyed value to recover from'); continue
        core = strip_filler(orig)
        intro = story_intro(before)
        name = intro_name(intro, rel)
        mn = re.search(r'\b\d+\s+([a-z][a-z]+(?:\s[a-z]+)?)\s+ready\b', before) or \
             re.search(r'Arranges\s+([a-z][a-z]+(?:\s[a-z]+)?)\s+in\s+\d+', before)
        noun = mn.group(1) if mn else 'marbles'
        new_op = None
        m = re.match(r'What is (\d+(?:,\d{3})*)\s*([+\-−×÷*/])\s*(\d+(?:,\d{3})*)\?$', core)
        if m:
            a = float(m.group(1).replace(',', '')); b = float(m.group(3).replace(',', '')); op = m.group(2)
            if op in '-−' and abs((a - b) - kv) < 1e-9:
                new_op = '%s has %s %s ready and gives away %s of them. How many %s are left?' % (
                    name, fnum(a), noun, fnum(b), noun)
            elif op in '÷/' and b and abs(a / b - kv) < 1e-9:
                new_op = '%s has %s %s and shares them equally among %s boxes. How many %s go in each box?' % (
                    name, fnum(a), noun, fnum(b), noun)
            elif op in '×*' and abs(a * b - kv) < 1e-9:
                new_op = '%s arranges %s in %s rows with %s in each row. How many %s are there in total?' % (
                    name, noun, fnum(a), fnum(b), noun)
            elif op == '+' and abs(a + b - kv) < 1e-9:
                new_op = '%s has %s %s ready. %s more arrive. How many %s are there now?' % (
                    name, fnum(a), noun, fnum(b), noun)
        if new_op is not None:
            new = (intro + ' ' if intro else '') + new_op
            kind = 'story-rewrite'
        else:
            ok = verify_core(core, q)
            if ok is False:
                mark_delete(rel, q, 'class2: original_stem math contradicts keyed answer'); continue
            new = (intro + ' ' if intro else '') + core
            kind = 'restored-original' + ('' if ok else '-unverified')
        q['stem'] = new
        counts['class2-fixed'] += 1
        counts['class2::' + kind] += 1
        DIRTY.add(rel)
        if len(examples['class2']) < 8:
            examples['class2'].append({'id': qid, 'before': before, 'after': new})

# ---------------- class 3: truncated stems ----------------
REL_MORE = re.compile(r'\b([A-Z][a-z]+) (?:has more(?: \w+)? than|is (?:older|taller|faster|bigger|heavier|stronger) than) ([A-Z][a-z]+)')
REL_LESS = re.compile(r'\b([A-Z][a-z]+) (?:has (?:fewer|less)(?: \w+)? than|is (?:younger|shorter|slower|smaller|lighter) than) ([A-Z][a-z]+)')

def solve_chain(core):
    m = re.search(r'Who (?:has the most|is the (?:oldest|tallest|fastest|biggest))\?', core)
    hi = True
    if not m:
        m = re.search(r'Who (?:has the (?:fewest|least)|is the (?:youngest|shortest|slowest|smallest))\?', core)
        hi = False
        if not m: return None
    edges = list(REL_MORE.findall(core)) + [(b, a) for a, b in REL_LESS.findall(core)]
    names = set(n for e in edges for n in e)
    if not edges or len(names) < 2: return None
    greater = {n: set() for n in names}
    for a, b in edges: greater[a].add(b)
    changed = True
    while changed:
        changed = False
        for a in names:
            for b in list(greater[a]):
                for c2 in greater.get(b, ()):
                    if c2 not in greater[a]:
                        greater[a].add(c2); changed = True
    if any(n in greater[n] for n in names): return None  # contradiction
    if hi:
        cand = [n for n in names if all(o == n or o in greater[n] for o in names)]
    else:
        cand = [n for n in names if all(o == n or n in greater[o] for o in names)]
    return cand[0] if len(cand) == 1 else 'Cannot'

def wp_verify(stem, kv):
    """start + buys - gives arithmetic check for simple fill-ins."""
    m = re.search(r'\bhas (\d+)\b', stem)
    if not m or kv is None: return False
    total = int(m.group(1))
    rest = stem[m.end():]
    for g in re.finditer(r'\bbuys (\d+) more\b', rest): total += int(g.group(1))
    for g in re.finditer(r'\bgives (\d+) to\b', rest): total -= int(g.group(1))
    if re.search(r'shares them equally with [A-Z][a-z]+', stem):
        m2 = re.search(r'has (\d+)', stem)
        return abs(int(m2.group(1)) / 2 - kv) < 1e-9
    return abs(total - kv) < 1e-9

def fix_truncated():
    for rel, qid in flagged('truncated-sentence'):
        q = getq(rel, qid)
        if q is None or qid in to_delete[rel]: continue
        before = q['stem']
        ai, kv = keyed_value(q)
        ch = q.get('choices') or []
        fixed = None
        # --- T6: missing quadrilateral side ---
        m = re.search(r'A quadrilateral has sides (\d+), (\d+), (\d+), and \? cm\. The perimeter is (\d+) cm\. What is \?', before)
        if m:
            s1, s2, s3, P = (int(m.group(i)) for i in (1, 2, 3, 4))
            miss = P - s1 - s2 - s3
            if kv is not None and miss > 0 and abs(miss - kv) < 1e-9:
                fixed = before.replace('What is ?', 'What is the length of the missing side in cm?')
            else:
                mark_delete(rel, q, 'class3: missing-side value contradicts key'); continue
        # --- surgical fills on current stem (T7 / T1-098 style) ---
        if fixed is None and not re.search(r'(?:^|[.!?]\s+)[A-Za-z]*\s*(?:is|Is) (?:older|younger|taller)', before) \
                and ' than .' not in before and 'How old is ?' not in before:
            s = before
            ms = re.search(r'\b([A-Z][a-z]+) has \d+', s)
            sname = ms.group(1) if ms else intro_name(story_intro(s), rel)
            s = re.sub(r'(?<=[.!?] )Has (\d+)', sname + r' has \1', s)
            s = re.sub(r'(?<=[.!?] )buys\b', sname + ' buys', s)
            rname = fresh_name(rel, s)
            s = re.sub(r'\bgives (\d+) to \.', r'gives \1 to ' + rname + '.', s)
            s = re.sub(r'\bshares them equally with \.', 'shares them equally with ' + rname + '.', s)
            s = re.sub(r'\bHow many does have\b', 'How many does ' + sname + ' have', s)
            if s != before and wp_verify(s, kv) and not ORPHAN_RE.search(s) and not TRUNC_Q_RE.search(s):
                fixed = s
        # --- original_stem based: comparison chains & age sums ---
        if fixed is None and q.get('original_stem'):
            core = strip_filler(q['original_stem'])
            res = solve_chain(core)
            if res is not None and ai is not None:
                keyed_text = str(ch[ai]).strip()
                ok = (res == 'Cannot' and keyed_text.lower().startswith('cannot')) or keyed_text == res
                if ok:
                    intro = story_intro(before)
                    fixed = ((intro + ' ') if intro else '') + core
                else:
                    mark_delete(rel, q, 'class3: chain conclusion does not match keyed answer'); continue
            else:
                m2 = re.search(r'([A-Z][a-z]+) is (\d+) years older than ([A-Z][a-z]+)\. Together their ages add up to (\d+)\. How old is ([A-Z][a-z]+)\?', core)
                if m2 and kv is not None:
                    A, k2, B, S, X = m2.group(1), int(m2.group(2)), m2.group(3), int(m2.group(4)), m2.group(5)
                    if (S - k2) % 2 == 0 and X in (A, B):
                        younger = (S - k2) // 2
                        want = younger + k2 if X == A else younger
                        if abs(want - kv) < 1e-9:
                            intro = story_intro(before)
                            text = m2.group(0)
                            for nm in {A, B} - ALL_ROSTER:
                                rep = fresh_name(rel, text + ' ' + (intro or ''))
                                text = re.sub(r'\b' + nm + r'\b', rep, text)
                            fixed = ((intro + ' ') if intro else '') + text
                if fixed is None:
                    m3 = re.search(r'([A-Z][a-z]+) has (\d+) (\w+) and shares them equally with ([A-Z][a-z]+)\. How many .*\?', core)
                    if m3 and kv is not None and abs(int(m3.group(2)) / 2 - kv) < 1e-9:
                        intro = story_intro(before)
                        text = m3.group(0)
                        for nm in {m3.group(1), m3.group(4)} - ALL_ROSTER:
                            rep = fresh_name(rel, text + ' ' + (intro or ''))
                            text = re.sub(r'\b' + nm + r'\b', rep, text)
                        fixed = ((intro + ' ') if intro else '') + text
        if fixed is not None and not ORPHAN_RE.search(fixed) and not TRUNC_Q_RE.search(fixed):
            q['stem'] = fixed
            counts['class3-fixed'] += 1
            DIRTY.add(rel)
            if len(examples['class3']) < 8:
                examples['class3'].append({'id': qid, 'before': before, 'after': fixed})
        else:
            mark_delete(rel, q, 'class3: truncated beyond safe repair')

# ---------------- class 8/9: Help truncations ----------------
def fix_help():
    for rel, qid in flagged('help-artifact'):
        q = getq(rel, qid)
        if q is None or qid in to_delete[rel]: continue
        before = q['stem']
        orig = (q.get('original_stem') or '').strip()
        if not orig:
            mark_delete(rel, q, 'class8: Help-truncation lost the problem, no original_stem'); continue
        core = strip_filler(orig)
        ok = verify_core(core, q)
        if ok is False:
            mark_delete(rel, q, 'class8: original_stem math contradicts keyed answer'); continue
        idx = before.find(' Help ')
        intro = before[:idx + 1].strip() if idx > 0 else story_intro(before)
        # rename a leading non-roster subject (e.g. "Sage shares 66 ...")
        mlead = re.match(r'([A-Z][a-z]+)\s+(?:shares|has|buys|counts|makes)\b', core)
        if mlead and mlead.group(1) not in ALL_ROSTER:
            core = re.sub(r'\b' + mlead.group(1) + r'\b', intro_name(intro, rel), core)
        q['stem'] = ((intro + ' ') if intro else '') + core
        counts['class8-fixed'] += 1
        DIRTY.add(rel)

# ---------------- class 7: T1-1182 ----------------
def fix_t1_1182():
    # recompute: integers 1..10000 divisible by exactly one of 4,5,6
    N = 10000
    cnt = sum(1 for x in range(1, N + 1) if (x % 4 == 0) + (x % 5 == 0) + (x % 6 == 0) == 1)
    assert cnt == 3332, cnt
    q = getq('topic-1-counting/g56_questions.json', 'T1-1182')
    if q is None: return
    ai = ans_index(q)
    if ai is not None and str(q['choices'][ai]) != '3332':
        set_choice_value(q, ai, 3332)
        counts['class7-fixed'] += 1
        DIRTY.add('topic-1-counting/g56_questions.json')

# ---------------- class 11: visual_context clock -> number line ----------------
def fix_visual_context():
    for rel, qid in flagged('visual-context-mismatch'):
        q = getq(rel, qid)
        if q is None or qid in to_delete[rel]: continue
        vc = q.get('visual_context') or ''
        if 'clock' in vc.lower() and 'number line' in q.get('stem', '').lower():
            q['visual_context'] = 'A number line with marked positions and jump arrows.'
            counts['class11-fixed'] += 1
            DIRTY.add(rel)

# ---------------- class 10: bare-verb sentences ----------------
def fix_missing_subject():
    for rel, qid in flagged('missing-subject'):
        q = getq(rel, qid)
        if q is None or qid in to_delete[rel]: continue
        stem = q['stem']; changed = False
        for _ in range(3):
            m = VERB_START_RE.search(stem)
            if not m: break
            pre = stem[:m.start() + 1]
            names = {n for n in re.findall(r'[A-Z][a-z]+', pre) if n in ALL_ROSTER}
            if len(names) != 1: break
            nm = names.pop()
            seg = m.group(0).replace(m.group(1), nm + ' ' + m.group(1).lower(), 1)
            stem = stem[:m.start()] + seg + stem[m.end():]
            changed = True
        names = {n for n in re.findall(r'[A-Z][a-z]+', stem) if n in ALL_ROSTER}
        if len(names) == 1:
            nm = next(iter(names))
            new = re.sub(r'\bdoes have (now|left)\b', 'does %s have \\1' % nm, stem)
            new = re.sub(r'\bdoes have\?', 'does %s have?' % nm, new)
            if new != stem:
                stem = new; changed = True
        if changed:
            q['stem'] = stem
            counts['class10-fixed'] += 1
            DIRTY.add(rel)
        else:
            counts['class10-left'] += 1

# ---------------- classes 5/6: hints ----------------
def stem_chain_exprs(stem):
    ints = [float(x) for x in re.findall(r'\d+', (stem or '').replace(',', ''))][:5]
    out = []
    if len(ints) >= 2:
        out.append((' + '.join(fnum(x) for x in ints), sum(ints)))
    for i in range(len(ints)):
        for j in range(len(ints)):
            if i == j: continue
            a, b = ints[i], ints[j]
            out.append(('%s + %s' % (fnum(a), fnum(b)), a + b))
            out.append(('%s - %s' % (fnum(a), fnum(b)), a - b))
            out.append(('%s × %s' % (fnum(a), fnum(b)), a * b))
            if b: out.append(('%s ÷ %s' % (fnum(a), fnum(b)), a / b))
    if len(ints) >= 3:
        a, b, c = ints[0], ints[1], ints[2]
        out.append(('%s - %s - %s' % (fnum(a), fnum(b), fnum(c)), a - b - c))
        out.append(('%s + %s - %s' % (fnum(a), fnum(b), fnum(c)), a + b - c))
        out.append(('(%s + %s) × %s' % (fnum(a), fnum(b), fnum(c)), (a + b) * c))
        out.append(('%s × %s + %s' % (fnum(a), fnum(b), fnum(c)), a * b + c))
    return out

def fix_false_equations(text, stem, ans_val, level_key):
    out = text
    for m in EQ_RE.finditer(text):
        pre = text[:m.start()].rstrip()
        if pre and (pre[-1].isdigit() or pre[-1] in '+-×*÷='): continue
        lhs, rhs = m.group(1), m.group(2)
        r = safe_eval(lhs); c = parse_num(rhs)
        if r is None or c is None or abs(r - c) < 1e-6: continue
        nums = [float(x.replace(',', '')) for x in re.findall(NUMPAT, lhs)]
        ops = re.findall(r'[\+\-×\*÷]', lhs)
        repl = None
        # a) integer division with remainder ("47 ÷ 4 = 11")
        if len(ops) == 1 and ops[0] == '÷' and len(nums) == 2 and nums[1]:
            a, b = nums
            if abs(a - round(a)) < 1e-9 and abs(b - round(b)) < 1e-9 and int(a) % int(b) != 0 \
                    and int(a) // int(b) == int(round(c)) and abs(c - round(c)) < 1e-9:
                repl = '%s ÷ %s gives %s remainder %d' % (fnum(a), fnum(b), fnum(c), int(a) % int(b))
        # b) expression recomputed from the stem that yields the stated result
        if repl is None:
            for expr, val in stem_chain_exprs(stem):
                if abs(val - c) < 1e-9:
                    repl = '%s = %s' % (expr, fnum(c)); break
        # c) same operands, corrected operator(s)
        if repl is None and len(nums) == 2:
            a, b = nums
            for sym, val in (('+', a + b), ('-', a - b), ('×', a * b), ('÷', a / b if b else None)):
                if val is not None and abs(val - c) < 1e-9:
                    repl = '%s %s %s = %s' % (fnum(a), sym, fnum(b), fnum(c)); break
        if repl is None and len(nums) == 3:
            a, b, d = nums
            for f_, val in (('{0} + {1} + {2}', a + b + d), ('{0} - {1} - {2}', a - b - d),
                            ('{0} + {1} - {2}', a + b - d), ('({0} + {1}) × {2}', (a + b) * d),
                            ('{0} × {1} + {2}', a * b + d), ('{0} × {1} × {2}', a * b * d)):
                if abs(val - c) < 1e-9:
                    repl = f_.format(fnum(a), fnum(b), fnum(d)) + ' = %s' % fnum(c); break
        # d) keep LHS, correct the RHS (true result); mask if it would leak the answer
        if repl is None:
            true_rhs = '?' if (ans_val is not None and abs(r - ans_val) < 1e-9 and not level_key.endswith('2')) else fnum(r)
            repl = '%s = %s' % (lhs, true_rhs)
            if not all(any(abs(n - sv) < 1e-9 for sv in
                           [float(x) for x in re.findall(r'\d+', (stem or '').replace(',', ''))])
                       for n in nums):
                # LHS numbers not grounded in the stem -> drop the equation sentence
                repl = None
        if repl is not None:
            # leak guard: equation ending a non-solution level with "= answer"
            if ans_val is not None and not level_key.endswith('2'):
                tail = out.split(m.group(0))[-1].strip() if m.group(0) in out else ''
                mr = re.match(r'^.*=\s*(-?\d+(?:\.\d+)?)$', repl)
                if mr and abs(float(mr.group(1)) - ans_val) < 1e-9 and tail in ('', '.', '!'):
                    repl = repl[:repl.rfind('=')] + '= ?'
            out = out.replace(m.group(0), repl, 1)
        else:
            sents = SENT_SPLIT.split(out)
            keepers = []
            for s in sents:
                if m.group(0) in s:
                    keepers.append('Add the numbers step by step.' if '+' in lhs else 'Work it out step by step.')
                else:
                    keepers.append(s)
            out = ' '.join(keepers)
    return out

def scrub_leaks(text, ans_val, level_key):
    if ans_val is None or level_key.endswith('2'): return text
    out = text
    m = re.search(r'=\s*[\$₹]?(-?\d+(?:\.\d+)?)\s*([.!]?)\s*$', out)
    if m and abs(float(m.group(1)) - ans_val) < 1e-9:
        out = out[:m.start()] + '= ?' + (m.group(2) or '')
    sents = SENT_SPLIT.split(out)
    kept = []
    for s in sents:
        lm = LEAK_RE.search(s)
        if lm:
            v = parse_num(lm.group(1))
            if v is not None and abs(v - ans_val) < 1e-9:
                continue  # drop leaking sentence
        kept.append(s)
    out2 = ' '.join(kept).strip()
    if not out2:
        out2 = "You're one step away — finish the calculation yourself."
    return out2

def fix_hints():
    eq_items = flagged('hint-wrong-working') + flagged('hint-garbled-math')
    leak_items = flagged('hint-answer-leak')
    for kind, items in (('eq', eq_items), ('leak', leak_items)):
        for rel, qid in items:
            q = getq(rel, qid)
            if q is None or qid in to_delete[rel]: continue
            h = q.get('hint')
            if h is None: continue
            ai, kv = keyed_value(q)
            if q.get('interaction_mode') == 'integer' and q.get('correct_value') is not None:
                kv = parse_num(q.get('correct_value'))
            was_str = isinstance(h, str)
            hd = {'level_0': h} if was_str else dict(h)
            changed = False
            for lk in list(hd.keys()):
                v = hd.get(lk)
                if not isinstance(v, str) or not v.strip(): continue
                nv = v
                if kind == 'eq':
                    nv = fix_false_equations(nv, q.get('stem', ''), kv, lk)
                else:
                    nv = scrub_leaks(nv, kv, lk)
                if nv != v:
                    hd[lk] = nv; changed = True
            if changed:
                q['hint'] = hd['level_0'] if was_str else hd
                counts['class5-hints-fixed' if kind == 'eq' else 'class6-leaks-fixed'] += 1
                DIRTY.add(rel)

# ---------------- run ----------------
def total_questions():
    tot = 0
    import glob as g
    for f in (g.glob(os.path.join(ROOT, 'topic-*', '*.json'))
              + g.glob(os.path.join(ROOT, 'wavebook', '*.json'))
              + sum((g.glob(os.path.join(ROOT, cur + '-curriculum', '*', '*.json'))
                     for cur in ('ncert', 'singapore', 'igcse', 'icse')), [])):
        if 'manifest' in f: continue
        try:
            doc = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        tot += len(doc['questions'] if isinstance(doc, dict) else doc)
    return tot

before_total = total_questions()

fix_t8()
fix_class2()
fix_truncated()
fix_help()
fix_t1_1182()
fix_visual_context()
fix_missing_subject()
fix_hints()

# apply deletions and write dirty files
for rel, ids in to_delete.items():
    doc = DOCS[rel]
    ql = qlist(doc)
    ql[:] = [x for x in ql if x.get('id') not in ids]
    if isinstance(doc, dict) and 'total_questions' in doc:
        doc['total_questions'] = len(ql)

for rel in sorted(DIRTY):
    fmt = RAWFMT[rel]
    p = os.path.join(ROOT, rel)
    with open(p, 'w', encoding='utf-8') as fh:
        json.dump(DOCS[rel], fh, indent=2, ensure_ascii=fmt['ascii'])
        if fmt['nl']: fh.write('\n')
    json.load(open(p, encoding='utf-8'))  # parse check

# deleted-questions log (append)
dlog_path = os.path.join(HERE, 'v2_deleted_questions.json')
existing = []
if os.path.exists(dlog_path):
    try:
        existing = json.load(open(dlog_path, encoding='utf-8'))
    except Exception:
        existing = []
existing.extend(deleted_log)
with open(dlog_path, 'w', encoding='utf-8') as fh:
    json.dump(existing, fh, indent=1, ensure_ascii=False)

after_total = total_questions()

report = {
    'counts': dict(counts),
    'files_written': sorted(DIRTY),
    'questions_before': before_total,
    'questions_after': after_total,
    'deleted_total': len(deleted_log),
    'examples': {k: v for k, v in examples.items()},
}
with open(os.path.join(HERE, 'v2_fix_report.json'), 'w', encoding='utf-8') as fh:
    json.dump(report, fh, indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in report.items() if k != 'examples'}, indent=1))
print('\nEXAMPLES class2:')
for e in examples['class2'][:5]:
    print(' -', e['id'], '\n   BEFORE:', e['before'][:160], '\n   AFTER :', e['after'][:160])
print('\nEXAMPLES class3:')
for e in examples['class3'][:5]:
    print(' -', e['id'], '\n   BEFORE:', e['before'][:160], '\n   AFTER :', e['after'][:160])
