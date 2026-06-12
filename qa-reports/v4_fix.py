#!/usr/bin/env python3
"""Fix pass for v4_issues.json findings. stdlib only."""
import json, re, glob, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', 'content-live', 'content-v4', 'adaptive'))
DRY = '--dry' in sys.argv

issues = json.load(open(os.path.join(HERE, 'v4_issues.json')))
by_check = defaultdict(list)
for i in issues:
    by_check[i['check']].append(i)

NUMTOK = r'\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?'
NUMTOK_RE = re.compile(NUMTOK)

def nums_in(t): return [m.group(0) for m in NUMTOK_RE.finditer(t or '')]
def answer_value(q):
    ch = q.get('choices') or []
    ca = q.get('correct_answer')
    if ch:
        return (ch[ca], 'choice') if isinstance(ca, int) and 0 <= ca < len(ch) else (None, 'oob')
    cv = q.get('correct_value')
    return (cv, 'value') if cv is not None else (None, 'none')
def to_num(s):
    if isinstance(s, (int, float)): return float(s)
    s = str(s).strip()
    m = re.fullmatch(r'-?\s*(?:' + NUMTOK + r')\s*(?:cm|m|mm|km|kg|g|l|ml|min|minutes|hours|hr|sq\.?\s*cm|sq\.?\s*m|units?|rupees|paise)?\.?', s, re.I)
    if not m: return None
    mm = re.search(r'-?(?:' + NUMTOK + r')', s)
    return float(mm.group(0).replace(',', '')) if mm else None
def fmt(x): return str(int(x)) if float(x) == int(x) else str(x)

# ---------- build work sets ----------
delete_reason = {}   # id -> reason
for chk, reason in [('stem_unanswerable_no_info', 'unanswerable_no_info'),
                    ('missing_visual_unsolvable', 'missing_visual_unsolvable'),
                    ('stem_tautological', 'tautological_dead_weight')]:
    for i in by_check[chk]:
        delete_reason[i['id']] = reason
# recycled pictograph group (identical SVG, wrong Mon/Tue/Wed chart) — full group
wpr = json.load(open(os.path.join(ROOT, 'grade1', 'g1-word-problems.json')))
target_svg = next(q['visual_svg'] for q in wpr['questions'] if q['id'] == 'A1-WPR-0285')
picto_group = [q['id'] for q in wpr['questions'] if q.get('visual_svg') == target_svg]
for qid in picto_group:
    delete_reason[qid] = 'recycled_pictograph_chart_dependent'
# essential-no-svg not solvable from text
delete_reason['A3-FRC-0018'] = 'essential_visual_missing_unsolvable'
# count-mismatch grid question, needs visual
delete_reason['A3-SHP-0409'] = 'visual_count_mismatch_unsolvable'
# placeholder caption-box SVG + stem needs the (absent) chart data
for qid in ('A2-WPR-0024', 'A2-WPR-0029', 'A4-ASB-0122'):
    delete_reason[qid] = 'placeholder_svg_chart_dependent'

placeholder_ids = {i['id'] for i in by_check['visual_placeholder']} - set(delete_reason)
alt_ids = {i['id'] for i in by_check['duplicate_choice_alt']} - set(delete_reason)
alt_sev = {}
for i in by_check['duplicate_choice_alt']:
    alt_sev[i['id']] = i['severity']
leak_ids = {i['id'] for i in by_check['hint_answer_leak']}
essential_ids = {i['id'] for i in by_check['essential_no_svg']} - set(delete_reason)
mismatch_ids = ({i['id'] for i in by_check['visual_count_mismatch']}
                | {i['id'] for i in by_check['visual_type_mismatch']}
                | {i['id'] for i in by_check['visual_object_mismatch']}) - set(delete_reason)

fixes = Counter()
deleted = []
del_by_reason = Counter()
file_counts = {}

TPL_RE = re.compile(r'\s*(?:Try working out the calculation step-by-step\.\s*)?Compare your result to the choices:.*$', re.S)

def strip_template(h):
    n = 0
    for k in ('level_0', 'level_1', 'level_2'):
        v = h.get(k)
        if v and 'Compare your result to the choices' in v:
            new = TPL_RE.sub('', v).rstrip()
            if new.endswith('='):
                new += ' ?'
            new = re.sub(r'=\s+\?$', '= ?', new)
            if new.strip():
                h[k] = new
                n += 1
    return n

def scrub_leaks(q):
    h = q.get('hint')
    if not isinstance(h, dict): return 0
    val, _ = answer_value(q)
    n = to_num(val) if val is not None else None
    if n is None: return 0
    a = re.escape(fmt(n))
    stem_nums = set(nums_in(q.get('stem') or ''))
    cnt = 0
    for k in ('level_0', 'level_1', 'level_2'):
        v = (h.get(k) or '').strip()
        if not v: continue
        new = v
        if re.fullmatch(r'(Next|Sum|Total|Answer)\s*[:=]\s*' + a + r'\s*[.!]?\s*', new, re.I):
            h[k] = 'Apply the rule to the last number to find the next term.'
            cnt += 1
            continue
        m = re.search(r'=\s*' + a + r'\s*[.!]?\s*$', new)
        if m:
            new = new[:m.start()] + '= ?'
        else:
            m = re.search(r'\bequals\s+' + a + r'\s*[.!]?\s*$', new, re.I)
            if m:
                new = new[:m.start()] + 'equals ?'
            else:
                m = re.search(r'\banswer(?:\s+is|:)\s*' + a + r'\b', new, re.I)
                if m:
                    # drop the sentence containing the leak
                    sents = re.split(r'(?<=[.!?])\s+', new)
                    keep = [s for s in sents if not re.search(r'\banswer(?:\s+is|:)\s*' + a + r'\b', s, re.I)]
                    cand = ' '.join(keep).strip()
                    had = stem_nums & set(nums_in(v))
                    if not cand or (had and not (stem_nums & set(nums_in(cand)))):
                        cand = re.sub(r'(\banswer(?:\s+is|:)\s*)' + a + r'\b', r'\g<1>?', new, flags=re.I)
                    new = cand
        if new != v and new.strip():
            h[k] = new.strip()
            cnt += 1
    return cnt

OBJ_POOL = ['apples', 'bananas', 'oranges', 'mangoes', 'stars', 'balls', 'books', 'pencils', 'kites', 'crayons']
DAY_POOL = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

def fmt_like(val, ref):
    if '.' in ref:
        dec = len(ref.split('.')[1])
        return f'{val:.{dec}f}'
    return str(int(round(val)))

def gen_distractor(base, taken, allow_nonpos):
    t = {c.strip() for c in taken}
    if not re.search(r'\d', base):
        pool = DAY_POOL if base in DAY_POOL else OBJ_POOL
        for c in pool:
            if c not in t: return c
        return None
    m = re.fullmatch(r'(-?\d+)\s+(\d+)/(\d+)', base)
    if m:  # mixed number: perturb whole part
        w = int(m.group(1))
        for d in (-1, 1, -2, 2):
            c = f'{w+d} {m.group(2)}/{m.group(3)}'
            if w + d > 0 and c not in t: return c
    m = re.fullmatch(r'(-?)(\d+)/(\d+)', base)
    if m:  # fraction: perturb denominator
        sg, num, den = m.group(1), int(m.group(2)), int(m.group(3))
        for d in (1, -1, 2, -2, 3):
            nd = den + d
            c = f'{sg}{num}/{nd}'
            if nd > 1 and nd != num and c not in t: return c
    m = re.fullmatch(r"(\d+) o'clock(?: \(alt\))?", base)
    if m:
        hh = int(m.group(1))
        for d in (1, -1, 2, -2, 3):
            nh = hh + d
            c = f"{nh} o'clock"
            if 1 <= nh <= 12 and c not in t: return c
    m = re.fullmatch(r'(\d{1,2}):(\d{2})', base)
    if m:
        hh = int(m.group(1))
        for d in (-1, 1, -2, 2):
            nh = hh + d
            c = f'{nh}:{m.group(2)}'
            if 1 <= nh <= 23 and c not in t: return c
    if re.fullmatch(r'\d+( \+ \d+)+', base):  # expanded form: x10 the lead term
        mm = re.match(r'\d+', base)
        c = str(int(mm.group(0)) * 10) + base[mm.end():]
        if c not in t: return c
    m = re.fullmatch(r'(\d+)°', base) or re.fullmatch(r'(\d+)°', base)
    if m:  # bare angle
        n = int(m.group(1))
        for d in (90, -90, 45, -45, 30):
            c = f'{n+d}°' if '°' in base else f'{n+d}°'
            if n + d > 0 and c not in t: return c
    # default: perturb first number token
    mm = NUMTOK_RE.search(base)
    n = float(mm.group(0).replace(',', ''))
    is_dec = '.' in mm.group(0)
    if is_dec:
        deltas = [0.1, -0.1, 0.2, -0.2, 1, -1, 0.3, -0.3]
    elif n <= 20:
        deltas = [1, -1, 2, -2, 3, -3, 4, -4]
    else:
        deltas = [round(n * 0.1) or 1, -(round(n * 0.1) or 1), 10, -10, 1, -1, 2, -2]
    for d in deltas:
        nv = n + d
        if nv <= 0 and not allow_nonpos: continue
        c = base[:mm.start()] + fmt_like(nv, mm.group(0)) + base[mm.end():]
        if c not in t: return c
    return None

def fix_alt(q):
    ch = q['choices']
    fixed = 0
    for j, c in enumerate(ch):
        if isinstance(c, str) and c.endswith(' (alt)'):
            assert j != q['correct_answer'], q['id']
            base = c[:-6].strip()
            others = [str(x) for k, x in enumerate(ch) if k != j]
            nums = [to_num(x) for x in others]
            allow_nonpos = any(v is not None and v <= 0 for v in nums)
            repl = gen_distractor(base, others, allow_nonpos)
            if repl is None:
                raise RuntimeError('no distractor for %s %r %r' % (q['id'], base, ch))
            ch[j] = repl
            fixed += 1
            kind = 'alt_dup_of_correct' if alt_sev.get(q['id']) == 'critical' else 'alt_dup_of_distractor'
            fixes[kind] += 1
    return fixed

def null_visual(q, downgrade=True):
    q['visual_svg'] = None
    q['visual_alt'] = None
    q['visual_context'] = None
    if 'visual_type' in q:
        q['visual_type'] = 'none'
    if downgrade and q.get('visual_requirement') in ('essential', 'required'):
        q['visual_requirement'] = 'optional'
        fixes['visual_requirement_downgraded'] += 1

# ---------- manual fixes ----------
def manual_fix(q):
    qid = q['id']
    if qid == 'A5-MSR-0120':
        q['correct_answer'] = 0
        q['hint'] = {
            'level_0': 'Break the figure into simple shapes and add their areas.',
            'level_1': 'Rectangle area = length × width = 5 × 4. Triangle area = 1/2 × base × height = 1/2 × 3 × 1. Add the two areas.',
            'level_2': 'Work out 5 × 4 for the rectangle, then 1/2 × 3 × 1 for the triangle, and add your two results.'}
        q['solution_steps'] = ['Break into component shapes', 'Rectangle: 5 × 4',
                               'Triangle: 1/2 × 3 × 1', 'Add the two areas']
        q['diagnostics'] = {
            '1': "22 would mean the triangle has area 2 — check 1/2 × 3 × 1.",
            '2': "24 would mean the triangle has area 4 — don't forget the 1/2 in the triangle formula.",
            '3': "25.5 comes from a wrong triangle area — the base is 3 and the height is 1."}
        fixes['manual_rekey_A5-MSR-0120'] += 1
        return True
    if qid == 'A6-ARI-0355':
        q['stem'] = 'What is 50% of 24?'
        q['original_stem'] = 'What is 50% of 24?' if q.get('original_stem') == 'What is 50% of 25?' else q.get('original_stem')
        q['hint']['level_1'] = '50% = 50/100. Multiply by 24. 50/100 × 24 = ___'
        q['solution_steps'][0] = 'Identify the numbers: 50, 24'
        fixes['manual_restem_A6-ARI-0355'] += 1
        return True
    if qid == 'A6-NUM-0304':
        q['stem'] = 'What is 25% of 48?'
        q['original_stem'] = 'What is 25% of 48?' if q.get('original_stem') == 'What is 25% of 50?' else q.get('original_stem')
        q['hint']['level_1'] = '25% = 25/100. Multiply by 48. 25/100 × 48 = ___'
        q['solution_steps'][0] = 'Identify the numbers: 25, 48'
        fixes['manual_restem_A6-NUM-0304'] += 1
        return True
    if qid == 'A4-PAT-0256':
        q['stem'] = 'Next: 1600, 800, 400, 200, ?'
        if q.get('original_stem'): q['original_stem'] = 'Next: 1600, 800, 400, 200, ?'
        q['choices'] = ['90', '100', '400', '50']
        q['correct_answer'] = 1
        q['hint']['level_0'] = 'Look at how each number compares to the one before it.'
        q['hint']['level_1'] = 'Rule: halving. Each number is half of the one before. What is half of 200?'
        q['diagnostics'] = {'0': 'Check the rule: is each number half of the one before?',
                            '2': '400 is already in the list — apply the halving rule to 200.',
                            '3': "That halves 200 twice — only one more step is needed."}
        fixes['manual_resequence_A4-PAT-0256'] += 1
        return True
    if qid == 'A4-SHP-0644':
        q['hint']['level_2'] = 'Count the edges around the square base, then add the slanted edges that rise to the apex.'
        if q.get('visual_context') == 'A square with equal sides marked':
            q['visual_context'] = None
        fixes['manual_hint_A4-SHP-0644'] += 1
        return True
    return False

MANUAL = {'A5-MSR-0120', 'A6-ARI-0355', 'A6-NUM-0304', 'A4-PAT-0256', 'A4-SHP-0644'}

# ---------- main pass ----------
total_before = total_after = 0
files = sorted(glob.glob(os.path.join(ROOT, 'grade*', 'g*-*.json')))
new_counts = {}   # (grade_dir, topic_id) -> (count, min_b, max_b)
for path in files:
    rel = os.path.relpath(path, ROOT)
    raw = open(path, 'rb').read()
    is_ascii = all(b < 128 for b in raw)
    data = json.loads(raw)
    qs = data['questions']
    nb = len(qs)
    total_before += nb
    changed = False

    kept = []
    for q in qs:
        r = delete_reason.get(q['id'])
        if r:
            dq = dict(q)
            dq['_qa_deleted_from'] = rel
            dq['_qa_delete_reason'] = r
            deleted.append(dq)
            del_by_reason[r] += 1
            changed = True
        else:
            kept.append(q)
    data['questions'] = qs = kept

    for q in qs:
        h = q.get('hint')
        if isinstance(h, dict):
            n = strip_template(h)
            if n:
                fixes['template_noise_stripped'] += n
                changed = True
        if q['id'] in MANUAL:
            if manual_fix(q): changed = True
        if isinstance(h, dict) and q['id'] not in MANUAL:
            n = scrub_leaks(q)
            if n:
                fixes['leak_levels_scrubbed'] += n
                fixes['leak_qs_flagged' if q['id'] in leak_ids else 'leak_qs_extra'] += 1
                changed = True
        if q['id'] in alt_ids:
            if fix_alt(q): changed = True
        if q['id'] in placeholder_ids:
            null_visual(q)
            fixes['placeholder_svg_nulled'] += 1
            changed = True
        if q['id'] in mismatch_ids:
            null_visual(q)
            fixes['mismatch_svg_nulled'] += 1
            changed = True
        if q['id'] in essential_ids:
            if q.get('visual_requirement') == 'essential':
                q['visual_requirement'] = 'optional'
                fixes['essential_downgraded_to_optional'] += 1
                changed = True

    total_after += len(qs)
    # header counts
    if changed and 'total_questions' in data:
        data['total_questions'] = len(qs)
        if 'difficulty_range' in data and qs:
            bs = [q.get('irt_b') for q in qs if isinstance(q.get('irt_b'), (int, float))]
            if bs:
                data['difficulty_range'] = {'min_irt_b': round(min(bs), 2), 'max_irt_b': round(max(bs), 2)}
        if 'source_breakdown' in data:
            sb = Counter(q.get('content_source') or 'unknown' for q in qs)
            data['source_breakdown'] = dict(sb)
    bs = [q.get('irt_b') for q in qs if isinstance(q.get('irt_b'), (int, float))]
    new_counts[(os.path.dirname(rel), data.get('topic_id', os.path.basename(rel)[:-5]))] = (
        len(qs), round(min(bs), 2) if bs else None, round(max(bs), 2) if bs else None)

    if changed and not DRY:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=is_ascii)
        json.load(open(path))
        fixes['files_written'] += 1

# ---------- index updates ----------
for idx_path in sorted(glob.glob(os.path.join(ROOT, 'grade*', 'index.json'))):
    gdir = os.path.basename(os.path.dirname(idx_path))
    raw = open(idx_path, 'rb').read()
    is_ascii = all(b < 128 for b in raw)
    idx = json.loads(raw)
    ch = False
    tot = 0
    for t in idx.get('topics', []):
        key = (gdir, t['id'])
        if key in new_counts:
            cnt, mn, mx = new_counts[key]
            if t.get('total_questions') != cnt:
                t['total_questions'] = cnt; ch = True
            if mn is not None and 'difficulty_range' in t:
                nr = {'min_irt_b': mn, 'max_irt_b': mx}
                if t['difficulty_range'] != nr:
                    t['difficulty_range'] = nr; ch = True
            tot += cnt
        else:
            tot += t.get('total_questions', 0)
    if idx.get('total_questions') != tot:
        idx['total_questions'] = tot; ch = True
    if ch and not DRY:
        with open(idx_path, 'w') as f:
            json.dump(idx, f, indent=2, ensure_ascii=is_ascii)
        json.load(open(idx_path))
        fixes['index_files_updated'] += 1

# ---------- deleted log ----------
log_path = os.path.join(HERE, 'v4_deleted_questions.json')
if not DRY:
    existing = []
    if os.path.exists(log_path):
        existing = json.load(open(log_path))
    existing.extend(deleted)
    with open(log_path, 'w') as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

print('=== FIX COUNTS ===')
for k, v in sorted(fixes.items()): print(f'  {k}: {v}')
print('=== DELETIONS ===')
for k, v in sorted(del_by_reason.items()): print(f'  {k}: {v}')
print(f'  TOTAL deleted: {len(deleted)}')
print(f'=== TOTALS === before={total_before} after={total_after} (diff={total_before-total_after})')
