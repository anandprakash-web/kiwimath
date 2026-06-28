#!/usr/bin/env python3
"""Content QA fix (2026-06-14): strip decorative filler prefixes + remove
placeholder visual SVGs across the SERVED banks (content-live/olympiad +
content-live/curriculum). Preserves choices/answers/hints/diagnostics/IRT.

Idempotent. Run from repo root.  python3 qa-reports/fix_filler_placeholder.py
"""
import json, glob, re, hashlib

FILES = sorted(glob.glob('content-live/olympiad/L*/*.json')) + \
        sorted(glob.glob('content-live/curriculum/*/grade*/questions.json'))

NAMES = ['Captain Kiwi','Kiwi','Chikoo','Aarohi','Vanya','Riya','Ved','Nuha',
         'Google','Veronica','Veer','Dev','Neha','Leela','Maya','Arjun','Zara',
         'Sam','Ravi','Priya','Mei','Tom','Lily','Anya','Omar']
NAME_RE = re.compile(r'\b(' + '|'.join(re.escape(n) for n in NAMES) + r')\b')
SCENE = re.compile(r'\b(maze|crystal|palace|machine|treasure|wizard|demon|escape room|'
    r'mirror|cipher|lighthouse|compass|castle|tower|brick|lego|kingdom|throne|vault|'
    r'asteroid|station|telescope|beast|riddle|serum|scale|festival|rail|circuit|stair|'
    r'cavern|den|tablet|spiral|foundation|expedition|berry|kitchen|grand palace|'
    r'market square|trick stairs|coded message|colour maze|color maze|dark mirror|'
    r'shifting|puzzle path|throne room)\b', re.I)
NUMWORD = re.compile(r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|'
    r'twelve|dozen|half|double|twice|triple|first|second|third|fourth|fifth)\b', re.I)

def split_sents(stem):
    parts = re.findall(r'[^.!?]*[.!?]', stem)
    tail = stem[sum(len(p) for p in parts):]
    if tail.strip(): parts.append(tail)
    return [p for p in parts if p.strip()]

def strip_filler(stem):
    ss = split_sents(stem)
    if len(ss) < 2: return stem, 0
    i = 0; removed = 0
    while i < len(ss) - 1:
        s = ss[i].strip()
        decorative = (not re.search(r'\d', s) and '?' not in s
                      and not NUMWORD.search(s)
                      and (NAME_RE.search(s) or SCENE.search(s)))
        if decorative: i += 1; removed += 1
        else: break
    if removed == 0: return stem, 0
    rest = ' '.join(x.strip() for x in ss[i:]).strip()
    if not re.search(r'\d', rest) and '?' not in rest:
        return stem, 0          # safety: never empty the question
    return rest, removed

PRIM = ('<line','<circle','<path','<polygon','<polyline','<ellipse')
def is_placeholder(svg):
    if not svg or not svg.strip(): return False
    if '#F8F9FA' in svg and '#6C757D' in svg and '<text' in svg: return True
    prims = sum(svg.count(p) for p in PRIM)
    return prims == 0 and svg.count('<rect') <= 1 and svg.count('<text') >= 1

# integrity = fields that must NEVER change
LOCK = ('choices','correct_answer','correct_value','answer','hint','diagnostics',
        'irt_params','irt_a','irt_b','irt_c','difficulty_tier','difficulty_score',
        'interaction_mode','id','km_level','km_pillar','km_topic')
def lock_hash(q):
    return hashlib.md5(json.dumps({k:q.get(k) for k in LOCK}, sort_keys=True,
                                  ensure_ascii=False).encode()).hexdigest()

filler_changed = filler_sents = ph_removed = 0
integrity_fail = []
seen_key = {}      # for duplicate exposure after strip
dups = []
total = 0

for f in FILES:
    d = json.load(open(f))
    qs = d['questions'] if isinstance(d, dict) and 'questions' in d else d
    dirty = False
    for q in qs:
        if not isinstance(q, dict): continue
        total += 1
        before = lock_hash(q)
        # (1) filler
        st = (q.get('stem','') or '')
        new, r = strip_filler(st.strip())
        if r > 0 and new != st:
            q['stem'] = new; filler_changed += 1; filler_sents += r; dirty = True
        # (2) placeholder visual
        if is_placeholder(q.get('visual_svg','') or ''):
            q['visual_svg'] = ''
            if 'visual_context' in q: q['visual_context'] = ''
            if 'visual_alt' in q: q['visual_alt'] = ''
            ph_removed += 1; dirty = True
        # integrity
        if lock_hash(q) != before:
            integrity_fail.append(q.get('id'))
        # duplicate exposure (exact stem+choices+answer)
        key = (re.sub(r'\s+',' ',q.get('stem','').strip().lower()),
               json.dumps(q.get('choices'), ensure_ascii=False),
               q.get('correct_answer'))
        if key in seen_key: dups.append((q.get('id'), seen_key[key]))
        else: seen_key[key] = q.get('id')
    if dirty:
        json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)

print('=== CONTENT QA FIX RESULTS ===')
print(f'questions scanned        : {total}')
print(f'filler stems stripped    : {filler_changed}  (sentences removed: {filler_sents})')
print(f'placeholder SVGs removed : {ph_removed}')
print(f'INTEGRITY failures       : {len(integrity_fail)}  (must be 0)')
if integrity_fail[:5]: print('  e.g.', integrity_fail[:5])
print(f'exact-duplicate questions exposed: {len(dups)}')
if dups[:5]: print('  e.g.', dups[:5])
