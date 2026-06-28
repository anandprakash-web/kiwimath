#!/usr/bin/env python3
"""Kiwimath content-production QA FIX pass (schema 5.0).

Fixes the findings in prod_issues.json / prod_summary.json:
 1. terminal hint answer-leaks scrubbed (unsolve "= ANS" -> "= ?", drop/neutralise revealing sentence)
 2. broken-name logic stems rebuilt (comparison chains, age clues, possession chains, does-have, orphans)
 3. unanswerable missing-visual questions deleted (verified individually; answerable ones kept/reworded)
 4. junk "(alt)" distractors replaced with plausible distinct values
 5. wrong-and-unfixable answers fixed individually (verified)
 6. 3-level topic-aware hints generated for all wavebook hint=null questions
 7. interaction modes: tap_to_reveal -> mcq, null -> mcq/integer
 8. multiple_choice -> mcq normalisation (backend convention: content_store_v2.QuestionV2 'mcq')
 9. stem-vs-SVG object mismatches: SVG nulled where text-solvable
10. g1/g2-shapes direction questions: shape-template hints replaced with direction ladders
11. off-grade G1 items listed (NOT deleted) in prod_offgrade_report.json

Usage: python3 prod_fix_script.py [--apply]   (default = dry run, prints plan)
"""
import json, glob, re, os, sys, collections

_dir = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CP_ROOT", os.path.abspath(os.path.join(_dir, "../archive/content-production")))
OUT = os.environ.get("QA_OUT", _dir)
APPLY = "--apply" in sys.argv

log = collections.Counter()
deleted = []      # full objects
changes = []      # audit trail
offgrade = []
hint_samples = []

def rec(action, f, qid, detail=""):
    log[action] += 1
    changes.append({"action": action, "file": f, "id": qid, "detail": detail})

# ---------------- shared helpers (mirrors prod_qa_script.py) ----------------
def parse_num(s):
    if s is None: return None
    s = str(s).strip().replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").replace("$", "").strip()
    m = re.fullmatch(r'(-?\d+(?:\.\d+)?)\s*(?:%|[a-zA-Z .²]*)?', s)
    if m:
        try: return float(m.group(1))
        except Exception: return None
    m = re.fullmatch(r'(\d+)\s*/\s*(\d+)', s)
    if m and int(m.group(2)) != 0:
        return int(m.group(1)) / int(m.group(2))
    return None

def fnum(x):
    if x is None: return None
    return int(x) if abs(x - round(x)) < 1e-9 else round(x, 6)

def ans_strings(q):
    out = []
    ch = q.get("choices") or []
    ca = q.get("correct_answer")
    if ch and isinstance(ca, int) and 0 <= ca < len(ch):
        out.append(str(ch[ca]).strip())
        pv = parse_num(ch[ca])
        if pv is not None: out.append(str(fnum(pv)))
    if q.get("correct_value") is not None:
        out.append(str(q["correct_value"]))
        try: out.append(str(fnum(float(q["correct_value"]))))
        except Exception: pass
    # dedupe, longest first so '₹10' is handled before '10'
    return sorted(set(a for a in out if a), key=len, reverse=True)

def leak_check(text, ansstrs):
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

SENT_SPLIT = re.compile(r'(?<=[.!?])\s+')

# ---------------- 1. hint leak scrubber ----------------
def scrub_level(text, ansstrs):
    """Remove terminal answer reveals; keep level non-empty. Returns new text."""
    t = text
    for _ in range(4):
        changed = False
        for a in ansstrs:
            ae = re.escape(a)
            # "... = ANS" terminal -> "= ?"
            new = re.sub(r'=\s*' + ae + r'\s*([.!]?)\s*$', r'= ?', t)
            if new != t: t, changed = new, True; continue
            # "answer is/: ANS" anywhere -> "answer is ?"
            new = re.sub(r'(answer\s*(?:is|:)\s*)' + ae + r'\b', r'\1?', t, flags=re.I)
            if new != t: t, changed = new, True; continue
            # "gives us ANS" -> "gives us ?"
            new = re.sub(r'(gives us\s*)' + ae + r'\b', r'\1?', t, flags=re.I)
            if new != t: t, changed = new, True; continue
            # terminal "... is ANS." -> drop sentence (if others remain) else "... is ?"
            if re.search(r'\bis\s*' + ae + r'\s*[.!]?\s*$', t, re.I):
                parts = SENT_SPLIT.split(t.strip())
                if len(parts) >= 2:
                    t = ' '.join(parts[:-1]).strip()
                else:
                    t = re.sub(r'\bis\s*' + ae + r'\s*[.!]?\s*$', 'is ?', t, flags=re.I)
                changed = True
        if not changed:
            break
    t = re.sub(r'\s+', ' ', t).strip()
    if not t:
        t = "Work it out one step at a time - what do you get?"
    return t

def scrub_hints(q, f):
    h = q.get("hint")
    if not isinstance(h, dict): return False
    ansstrs = ans_strings(q)
    if not ansstrs: return False
    mod = False
    for k in list(h.keys()):
        v = h.get(k)
        if v and leak_check(v, ansstrs):
            nv = scrub_level(v, ansstrs)
            if leak_check(nv, ansstrs):           # stubborn -> drop offending tail hard
                parts = SENT_SPLIT.split(nv.strip())
                while parts and leak_check(' '.join(parts), ansstrs):
                    parts = parts[:-1]
                nv = ' '.join(parts).strip() or "Work it out one step at a time - what do you get?"
            h[k] = nv
            rec("hint_leak_scrubbed", f, q.get("id"), f"{k}: ...{v[-50:]!r} -> ...{nv[-50:]!r}")
            mod = True
    return mod

def dedupe_hint_levels(q, f):
    """If two hint levels are identical, soften the earlier one into a method nudge."""
    h = q.get("hint")
    if not isinstance(h, dict): return False
    keys = sorted(k for k in h if h.get(k))
    mod = False
    for i in range(len(keys) - 1):
        for j in range(i + 1, len(keys)):
            if h[keys[i]].strip() == h[keys[j]].strip():
                h[keys[i]] = "Set it up yourself first: which numbers from the question do you need, and which operation connects them?"
                rec("hint_levels_deduped", f, q.get("id"), keys[i])
                mod = True
                break
    return mod

# ---------------- 2. broken-name stem repair ----------------
CAST = ["Kiwi", "Chikoo", "Aarohi", "Vanya", "Riya", "Ved", "Nuha", "Google", "Veronica"]
NON_NAME_CHOICES = re.compile(r'cannot|not |both|equal|none|all |determин|determine', re.I)
GENUINE_BROKEN = [
    re.compile(r'(?:^|[:!.?]\s+)is \d+(?: years old)?\.'),                                  # orphan age
    re.compile(r'\b(?:more|fewer|less|older|younger|taller|shorter|bigger|smaller|heavier|lighter|faster|slower) than\s*[.,?]'),
    re.compile(r'(?:^|[.!?]\s+)(?:Is|Was)\s+(?:older|younger|taller|shorter|bigger|smaller|heavier|lighter)\b'),
    re.compile(r'(?:^|[.!?]\s+)[Hh]as\s+(?:a stack of )?\d'),                               # orphan "Has 7 ..."
    # orphan sentence-initial lowercase "has ..." ("clue: has 5 blocks.");
    # the '!' lookbehind keeps factorials like "n! has 4 trailing zeros" safe
    re.compile(r'(?:^|[.?:]\s+|(?<![0-9nN])!\s+)has\s'),
    re.compile(r'\bdoes\s+have\b'),
    re.compile(r'(?:^|[.?:]\s+|(?<![0-9nN])!\s+)(?:is|and|or|plots|gives|splits?)\s'),      # lowercase orphan verb
    re.compile(r'\bgives \d+ to[.?!]'),
    re.compile(r'\bequally with[.?!]'),
    re.compile(r'\bHow old is\?'),
]
def is_genuine_broken(stem):
    return any(p.search(stem) for p in GENUINE_BROKEN)

def name_choices(q):
    out = []
    for c in q.get("choices") or []:
        c = str(c).strip()
        if re.fullmatch(r'[A-Z][a-z]+', c) and not NON_NAME_CHOICES.search(c):
            out.append(c)
    return out

def intro_name(stem):
    for n in CAST:
        if re.search(r'\b' + n + r'\b', stem):
            return n
    m = re.match(r'([A-Z][a-z]+)\s', stem)
    return m.group(1) if m else None

def fresh_names(stem, q, count, exclude=()):
    pool = [c for c in name_choices(q) if c not in exclude and not re.search(r'\b' + c + r'\b', stem)]
    extra = [n for n in ["Meera", "Tara", "Kabir", "Dev", "Sita", "Veer", "Asha", "Rohan"]
             if n not in exclude and not re.search(r'\b' + n + r'\b', stem) and n not in pool]
    pool += extra
    return pool[:count]

SUPER_MAP = {  # superlative -> (comparative, keyed-side)
    "oldest": ("older", "top"), "youngest": ("older", "bottom"),
    "tallest": ("taller", "top"), "shortest": ("taller", "bottom"),
    "biggest": ("bigger", "top"), "smallest": ("bigger", "bottom"),
    "heaviest": ("heavier", "top"), "lightest": ("heavier", "bottom"),
    "fastest": ("faster", "top"), "slowest": ("faster", "bottom"),
}

def repair_stem(q, f):
    """Try to repair a genuinely-broken stem. Returns True if repaired, 'delete' if unrepairable."""
    stem = q["stem"]; qid = q.get("id")
    ch = q.get("choices") or []
    ca = q.get("correct_answer")
    keyed = str(ch[ca]).strip() if (ch and isinstance(ca, int) and 0 <= ca < len(ch)) else None

    # R-A: age-clue template "is 14 years old. Rani is 12. Dev is 5. Who is the youngest/oldest?"
    mq = re.search(r'Who is the (youngest|oldest)\?', stem)
    clues = list(re.finditer(r'(?:([A-Z][a-z]+) )?is (\d+)(?: years old)?\.', stem))
    if mq and len(clues) >= 2 and keyed and re.fullmatch(r'[A-Z][a-z]+', keyed) \
       and any(c.group(1) is None for c in clues):
        ages = [int(c.group(2)) for c in clues]
        ext = min(ages) if mq.group(1) == "youngest" else max(ages)
        if ages.count(ext) == 1:
            target_slot = ages.index(ext)
            names = [c.group(1) for c in clues]
            # place keyed name on the extreme slot
            if keyed in names and names.index(keyed) != target_slot:
                names[names.index(keyed)] = None     # free it; will be refilled
            names[target_slot] = keyed
            # de-duplicate any repeated visible names (source data has e.g. two "Chikoo" slots)
            seen = set()
            for i, n in enumerate(names):
                if n in seen:
                    names[i] = None
                elif n:
                    seen.add(n)
            used = {n for n in names if n}
            fills = fresh_names(stem, q, len(names), exclude=used)
            fi = 0
            for i, n in enumerate(names):
                if n is None:
                    if fi >= len(fills): return "delete"
                    names[i] = fills[fi]; fi += 1
            head = stem[:clues[0].start()]
            tail = stem[clues[-1].end():]
            mid = f"{names[0]} is {ages[0]} years old. " + " ".join(
                f"{names[i]} is {ages[i]}." for i in range(1, len(ages)))
            q["stem"] = (head + mid + " " + tail.strip()).strip()
            rec("stem_rebuilt_age_clue", f, qid, q["stem"][:120])
            return True

    # R-B: comparison chain "Is older than X. X is older than Y. Who is the oldest?"
    mq = re.search(r'Who is the (\w+est)\?', stem)
    if mq and mq.group(1) in SUPER_MAP and keyed and re.fullmatch(r'[A-Z][a-z]+', keyed):
        comp, side = SUPER_MAP[mq.group(1)]
        if re.search(comp + r' than', stem):
            chain_names = re.findall(r'([A-Z][a-z]+) is ' + comp, stem) + re.findall(comp + r' than ([A-Z][a-z]+)', stem)
            others = []
            for n in chain_names:
                if n != keyed and n not in others and re.fullmatch(r'[A-Z][a-z]+', n):
                    others.append(n)
            others += [n for n in fresh_names(stem, q, 2, exclude={keyed, *others}) if n not in others]
            if len(others) >= 2:
                a, b = others[0], others[1]
                # keep intro only up to the last full sentence before the first clue fragment
                intro_txt = stem[:stem.lower().find(comp + ' than')]
                mlast = None
                for mm2 in re.finditer(r'[.!?:]', intro_txt):
                    mlast = mm2
                intro_txt = intro_txt[:mlast.end()] if mlast else ""
                intro_txt = ' '.join(s for s in SENT_SPLIT.split(intro_txt.strip())
                                     if s and not is_genuine_broken(s + ' ') and comp + ' than' not in s)
                if side == "top":
                    mid = f"{keyed} is {comp} than {a}. {a} is {comp} than {b}."
                else:
                    mid = f"{a} is {comp} than {b}. {b} is {comp} than {keyed}."
                q["stem"] = (intro_txt + " " + mid + f" Who is the {mq.group(1)}?").strip()
                rec("stem_rebuilt_chain", f, qid, q["stem"][:120])
                return True
        return "delete"

    # R-C: possession chain "has N obj. has more than. has fewer than. Who has the most/fewest?"
    mq = re.search(r'Who has the (most|fewest|least)\?', stem)
    mo = re.search(r'has (?:a stack of )?(\d+) (\w+)', stem)
    if mq and mo and keyed and re.fullmatch(r'[A-Z][a-z]+', keyed) and 'more than' in stem:
        n, obj = mo.group(1), mo.group(2)
        anchors = re.findall(r'([A-Z][a-z]+) has \d+ \w+', stem)
        anchor = next((x for x in anchors if x != keyed), None)
        pool = [x for x in fresh_names(stem, q, 3, exclude={keyed}) ]
        if anchor is None:
            if not pool: return "delete"
            anchor = pool.pop(0)
        third = next((x for x in name_choices(q) if x not in (keyed, anchor)), None) or \
                next((x for x in pool if x != anchor), None)
        if third is None: return "delete"
        intro_txt = stem[:stem.find(mo.group(0))].strip()
        intro_txt = ' '.join(s for s in SENT_SPLIT.split(intro_txt) if s and not is_genuine_broken(s + ' '))
        if mq.group(1) == "most":
            mid = f"{anchor} has {n} {obj}. {keyed} has more than {anchor}. {third} has fewer than {anchor}."
        else:
            mid = f"{anchor} has {n} {obj}. {third} has more than {anchor}. {keyed} has fewer than {anchor}."
        q["stem"] = (intro_txt + " " + mid + f" Who has the {mq.group(1)}?").strip()
        rec("stem_rebuilt_possession", f, qid, q["stem"][:120])
        return True

    # R-D: "X is d years older than. Together their ages add up to T. How old is?"
    md = re.search(r'([A-Z][a-z]+) is (\d+) years older than\.\s*Together their ages add up to (\d+)\.\s*How old is\?', stem)
    if md and keyed:
        nm, d, t = md.group(1), int(md.group(2)), int(md.group(3))
        kv = parse_num(keyed)
        if kv is not None and (t - d) % 2 == 0:
            younger, older = (t - d) // 2, (t + d) // 2
            partner = fresh_names(stem, q, 1, exclude={nm})
            if not partner: return "delete"
            p = partner[0]
            if abs(kv - younger) < 1e-9:
                new = f"{nm} is {d} years older than {p}. Together their ages add up to {t}. How old is {p}?"
            elif abs(kv - older) < 1e-9:
                new = f"{nm} is {d} years older than {p}. Together their ages add up to {t}. How old is {nm}?"
            else:
                return "delete"
            q["stem"] = stem[:md.start()] + new + stem[md.end():]
            rec("stem_rebuilt_age_sum", f, qid, q["stem"][:120])
            return True
        return "delete"

    s = stem
    # R-G: "Has A <obj> ready. B more arrive. How many ... now?" — key decides the rewrite
    mg = re.search(r'[Hh]as (\d+) ([\w ]+?) ready\.\s*(\d+) more arrive\.\s*How many [\w ]+ are there now\?', s)
    if mg and keyed is not None:
        A, obj, B = int(mg.group(1)), mg.group(2), int(mg.group(3))
        kv = parse_num(keyed)
        subj0 = intro_name(s) or "Kiwi"
        if kv is None:
            return "delete"
        if abs(kv - (A + B)) < 1e-9:
            new = f"{subj0} has {A} {obj} ready. {B} more arrive. How many {obj} are there now?"
        elif abs(kv - abs(A - B)) < 1e-9 and A != B:
            if B > A:
                new = f"{subj0} has {A} {obj} ready and needs {B} in total. How many more {obj} are needed?"
            else:
                new = f"{subj0} has {A} {obj} ready but only {B} are needed. How many extra {obj} are there?"
        else:
            # keyed choice is wrong, but the true sum may sit among the choices -> re-key
            hit = next((i for i, c in enumerate(ch) if parse_num(c) is not None
                        and abs(parse_num(c) - (A + B)) < 1e-9), None)
            if hit is not None:
                q["correct_answer"] = hit
                new = f"{subj0} has {A} {obj} ready. {B} more arrive. How many {obj} are there now?"
                rec("answer_rekeyed_ready_arrive", f, qid, f"key -> choice[{hit}]={ch[hit]!r} (= {A}+{B})")
            else:
                return "delete"
        q["stem"] = s[:mg.start()] + new + s[mg.end():]
        rec("stem_rebuilt_ready_arrive", f, qid, q["stem"][:120])
        return True

    # R-E: fruit list "Which fruit does have the MOST of?"
    mf = re.search(r'Which fruit does have the (MOST|FEWEST|LEAST) of\?', s)
    if mf and keyed:
        counts = re.findall(r'(\d+)\s+([a-z]+)', s)
        if counts:
            pick = max if mf.group(1) == "MOST" else min
            best = pick(counts, key=lambda x: int(x[0]))[1]
            if best == keyed or best.rstrip('s') == keyed.rstrip('s'):
                q["stem"] = s.replace(mf.group(0), f"Which fruit is there the {mf.group(1)} of?")
                rec("stem_fixed_does_have_fruit", f, qid, q["stem"][:120])
                return True
        return "delete"

    # R-F: generic does-have / orphan-verb / orphan-Has repairs (need a subject)
    subj = intro_name(s)
    if subj:
        new = s
        # sentence-initial "Has/has ..." -> "<Name> has ..."; pick a FRESH name when the
        # sentence already names someone else ("has 16 flowers and Kiwi has 18")
        pat_has = re.compile(r'(^|[.?:]\s+|(?<![0-9nN])!\s+)[Hh]as\s')
        guard = 0
        while guard < 6:
            m = pat_has.search(new)
            if not m: break
            m2 = re.search(r'[.!?]', new[m.end():])
            seg = new[m.end(): m.end() + (m2.end() if m2 else len(new))]
            names_in_seg = re.findall(r'\b([A-Z][a-z]+)\b', seg)
            if not names_in_seg:
                filler = subj
            else:
                fl = fresh_names(new, q, 1, exclude={subj, *names_in_seg})
                filler = fl[0] if fl else subj
            new = new[:m.end(1)] + filler + ' has ' + new[m.end():]
            guard += 1
        new = re.sub(r'(How many(?: \w+)?) does have\b', r'\1 does ' + subj + ' have', new)
        new = re.sub(r'\bdoes have\b', 'does ' + subj + ' have', new)
        new = re.sub(r'(^|[.!?]\s+)gives (\d+) more\.', r'\g<1>A friend gives \2 more.', new)
        new = re.sub(r'(^|[.!?]\s+)gives ([A-Z][a-z]+) (\d+) more\.', r'\g<1>A friend gives \2 \3 more.', new)
        new = re.sub(r' and gave (?:him|her) ', ' and was given ', new)
        new = re.sub(r'(^|[.!?:]\s+)is thinking of', r'\g<1>' + subj + ' is thinking of', new)
        new = re.sub(r'(^|[.!?:]\s+)is at the\b', r'\g<1>' + subj + ' is at the', new)
        new = re.sub(r'(^|[.!?:]\s+)is ([a-z]+ing)\b', r'\g<1>' + subj + r' is \2', new)
        new = re.sub(r'(^|[.!?:]\s+)plots\b', r'\g<1>' + subj + ' plots', new)
        new = re.sub(r'(^|[.!?:]\s+)splits?\b', r'\g<1>' + subj + ' splits', new)
        new = re.sub(r'\.\s+and ([A-Z][a-z]+) split\b', '. ' + subj + r' and \1 split', new)
        new = re.sub(r'shares them equally with([.?!])', r'shares them equally with ' + subj + r'\1', new) \
              if subj not in new.split('shares')[0][-40:] else new
        # "shares ... with." where subject IS the sharer -> share with a friend
        new = re.sub(r'equally with([.?!])', r'equally with a friend\1', new)
        new = re.sub(r'gives (\d+) to([.?!])', r'gives \1 to a friend\2', new)
        if new != s:
            q["stem"] = new
            rec("stem_fixed_orphan", f, qid, new[:120])
            return True
    return "delete" if is_genuine_broken(s) else False

# ---------------- 3. junk "(alt)" distractor replacement ----------------
# NOTE: "(same)" is NOT treated as junk - e.g. 'Right (same)' is a meaningful
# reflection-question choice (A2-SHP-0083 / T5-327).
WORD_POOL = ["crayons", "erasers", "kites", "marbles", "stickers", "shells", "beads", "buttons"]
DAY_POOL = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ALT_RE = re.compile(r'\((?:alt|dup|placeholder|v2)\)')

def _alt_candidates(base, stem):
    """Yield plausible replacement distractor strings for the given base value."""
    # mixed number "a b/c"
    m = re.fullmatch(r'(\d+) (\d+)/(\d+)', base)
    if m:
        w, n, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        for cand in (f"{w} {n+1}/{d}" if n + 1 < d else None,
                     f"{w} {n-1}/{d}" if n - 1 >= 1 else None,
                     f"{w+1} {n}/{d}", f"{w-1} {n}/{d}" if w >= 2 else None,
                     f"{w+2} {n}/{d}"):
            if cand: yield cand
        return
    # plain fraction "a/b"
    m = re.fullmatch(r'(\d+)/(\d+)', base)
    if m:
        n, d = int(m.group(1)), int(m.group(2))
        for cand in (f"{n+1}/{d}" if n + 1 != d else None,
                     f"{n-1}/{d}" if n - 1 >= 1 else None,
                     f"{n+2}/{d}", f"{n}/{d+1}", f"{n}/{d-1}" if d - 1 > n else None):
            if cand: yield cand
        return
    # colon pair "a:b" (ratio or time)
    m = re.fullmatch(r'(\d+):(\d+)', base)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        yield f"{b}:{a}"
        yield f"{a+1}:{b}"
        yield f"{a}:{b+1}"
        yield f"{max(1, a-1)}:{b}"
        return
    # "N o'clock"
    m = re.fullmatch(r"(\d+) o'clock", base)
    if m:
        h = int(m.group(1))
        for nh in (h + 1 if h < 12 else 1, h - 1 if h > 1 else 12, h + 2 if h + 2 <= 12 else h - 2):
            yield f"{nh} o'clock"
        return
    # "x = N" style
    m = re.fullmatch(r'([a-z]) = (\d+)', base)
    if m:
        v, n = m.group(1), int(m.group(2))
        for nn in (n + 1, n - 1 if n > 1 else n + 2, n + 2):
            yield f"{v} = {nn}"
        return
    # expanded form "30 + 0", "900 + 0 + 0" -> reversed order distractor
    if re.fullmatch(r'\d+(?: \+ \d+)+', base):
        parts = base.split(' + ')
        yield ' + '.join(reversed(parts))
        parts2 = list(parts); parts2[0] = parts2[0].rstrip('0') or parts2[0]
        yield ' + '.join(parts2)
        return
    # day abbreviations
    if base in DAY_POOL:
        for dpool in DAY_POOL:
            yield dpool
        return
    # generic numeric (handles ₹N, N°, N units, N%, decimals)
    m = re.match(r'^(₹|Rs\.?\s*|\$)?\s*(-?\d+(?:\.\d+)?)(.*)$', base)
    if m and parse_num(base) is not None:
        prefix, num, suffix = m.group(1) or "", float(m.group(2)), m.group(3)
        is_int = abs(num - round(num)) < 1e-9
        for cv in (num + 1, num - 1, num + 2, num - 2, num + 10, max(1, round(num * 0.9)),
                   round(num * 1.1, 2), num + 3, num - 3, num + 5):
            if cv <= 0: continue
            cvf = fnum(round(cv) if is_int else round(cv, 2))
            yield f"{prefix}{cvf}{suffix}"
        return
    # plain word (survey objects etc.)
    for w in WORD_POOL:
        yield w if base.endswith('s') else w.rstrip('s')

def fix_alt_choices(q, f):
    ch = q.get("choices") or []
    mod = False
    for i, c in enumerate(ch):
        cs = str(c)
        if not ALT_RE.search(cs): continue
        base = re.sub(r'\s*\((?:alt|dup|placeholder|v2)\)\s*', '', cs).strip()
        others_txt = {str(x).strip().lower() for j, x in enumerate(ch) if j != i}
        others_num = {fnum(parse_num(x)) for j, x in enumerate(ch) if j != i and parse_num(x) is not None}
        new = None
        for cand in _alt_candidates(base, q.get("stem") or ""):
            if cand is None: continue
            if cand.strip().lower() in others_txt: continue
            cv = parse_num(cand)
            if cv is not None and fnum(cv) in others_num: continue
            if cand.lower() in (q.get("stem") or "").lower() and not parse_num(cand): continue
            new = cand
            break
        if new is None:
            continue  # leave untouched rather than insert garbage
        ch[i] = new
        rec("alt_distractor_replaced", f, q.get("id"), f"{cs!r} -> {new!r}")
        mod = True
    return mod

# ---------------- 4. wavebook hint generation ----------------
def seq_in(stem):
    m = re.search(r'((?:\d+(?:\.\d+)?\s*,\s*){2,}\d*(?:\.\d+)?)', stem)
    if not m: return None
    parts = [p for p in re.findall(r'\d+(?:\.\d+)?', m.group(1))]
    return parts if len(parts) >= 3 else None

def gen_wb_hint(q, topic):
    s = q["stem"]; sl = s.lower()
    nums = re.findall(r'\d+(?:\.\d+)?', s.replace(",", ""))
    t = topic.lower()

    def lad(l0, l1, l2):
        return {"level_0": l0, "level_1": l1, "level_2": l2}

    # --- number sequence in stem ---
    seq = seq_in(s)
    if seq and ('pattern' in sl or 'next' in sl or 'complete' in sl or 'missing' in sl):
        a, b, c = seq[0], seq[1], seq[2]; last = seq[-1]
        return lad(
            f"The pattern shows {', '.join(seq)}. What rule takes you from one number to the next?",
            f"Find the jump between neighbours: from {a} to {b}, then from {b} to {c}. Is the jump the same every time?",
            f"Work out the jump ({b} − {a} = ?), then apply that same jump to {last} to get the missing number: {last} ± jump = ?")
    # --- shaded / unit-square grids ---
    if ('shaded' in sl or 'square represents' in sl or 'each square' in sl) and 'area' in sl:
        return lad(
            "Each small square of the grid counts as one unit of area. What is being asked — the total covered?",
            "You don't need a formula here: count the unit squares the region covers, row by row.",
            "Number of covered squares × area of one square = ?")
    # --- percent increase on a shape ---
    if 'increased by' in sl and '%' in s:
        mi = re.search(r'increased by (\d+)\s*%', sl)
        pi = mi.group(1) if mi else "the given percent"
        return lad(
            f"The sides grow by {pi}%. What happens to each side length first, before the area?",
            f"New side = old side + {pi}% of it. Find the new side first.",
            "Then: new area = new side × new side = ?")
    # --- perimeter ---
    if 'perimeter' in sl:
        if re.search(r'\(\s*\d*[a-z]\s*[+\-]', s):
            return lad(
                "The sides are algebraic expressions. Perimeter still means: add ALL the sides around the shape.",
                "A rectangle has two lengths and two breadths, so each expression is used twice.",
                "Perimeter = 2 × (length + breadth) — add the two expressions inside the bracket first, then double = ?")
        m = re.search(r'square.*?(?:side|of)\D{0,8}(\d+(?:\.\d+)?)', sl) or re.search(r'side (\d+(?:\.\d+)?) cm', sl)
        if m and 'rect' not in sl and 'triangle' not in sl:
            sd = m.group(1)
            return lad(
                f"We know each side of the square is {sd}. What is the perimeter — the total distance around the shape?",
                f"A square has 4 equal sides, each {sd}. Add them: {sd} + {sd} + {sd} + {sd}, or multiply.",
                f"Perimeter of a square = 4 × side = 4 × {sd} = ?")
        ml = re.search(r'length\D{0,10}(\d+(?:\.\d+)?)', sl); mb = re.search(r'(?:breadth|width)\D{0,10}(\d+(?:\.\d+)?)', sl)
        if ml and mb:
            L, B = ml.group(1), mb.group(1)
            return lad(
                f"We know the rectangle is {L} long and {B} wide. What is its perimeter — the distance all the way around?",
                f"A rectangle has TWO lengths and TWO breadths. So you need {L} twice and {B} twice.",
                f"Perimeter = 2 × (length + breadth) = 2 × ({L} + {B}) = ?")
        mt = re.search(r'equilateral triangle.*?side (\d+(?:\.\d+)?)', sl)
        if mt:
            sd = mt.group(1)
            return lad(
                f"An equilateral triangle has all sides equal — here each side is {sd} cm. What is the perimeter?",
                f"All 3 sides are the same: {sd} + {sd} + {sd}.",
                f"Perimeter = 3 × side = 3 × {sd} = ?")
        return lad("Perimeter means the total distance around the outside of the shape. Which side lengths do you know?",
                   "Walk around the shape edge by edge and add every side length once." + (f" The numbers given are: {', '.join(nums[:4])}." if nums else ""),
                   "Add ALL the side lengths together: side + side + ... = ?")
    # --- area ---
    if 'area' in sl:
        mg = re.search(r'(\d+)\s*columns?,?\s*(\d+)\s*rows?', sl)
        if mg:
            ccol, rrow = mg.group(1), mg.group(2)
            return lad(
                f"The grid has {ccol} columns and {rrow} rows, and each small square is 1 cm². What is the total area?",
                f"Each row holds {ccol} squares, and there are {rrow} rows of them.",
                f"Area = columns × rows = {ccol} × {rrow} = ? cm²")
        mt = re.search(r'triangle.*?base (\d+(?:\.\d+)?).*?height (\d+(?:\.\d+)?)', sl)
        if mt:
            b, h = mt.group(1), mt.group(2)
            return lad(
                f"We know the triangle has base {b} cm and height {h} cm. What is its area?",
                f"A triangle is HALF of a rectangle with the same base and height. First find {b} × {h}.",
                f"Area of triangle = ½ × base × height = ½ × {b} × {h} = ?")
        ml = re.search(r'length\D{0,10}(\d+(?:\.\d+)?)', sl); mb = re.search(r'(?:breadth|width)\D{0,10}(\d+(?:\.\d+)?)', sl)
        if ml and mb:
            L, B = ml.group(1), mb.group(1)
            return lad(
                f"The rectangle is {L} long and {B} wide. How many unit squares cover it — that is, what is the area?",
                f"Think of {B} rows with {L} squares in each row.",
                f"Area = length × breadth = {L} × {B} = ?")
        ms = re.search(r'square.*?side\D{0,8}(\d+(?:\.\d+)?)', sl) or re.search(r'side of square is of (\d+(?:\.\d+)?)', sl) or re.search(r'each side of square is of (\d+(?:\.\d+)?)', sl)
        if ms:
            sd = ms.group(1)
            return lad(
                f"Each side of the square is {sd}. What is the area — the space the square covers?",
                f"A square's length and width are the same, both {sd}.",
                f"Area = side × side = {sd} × {sd} = ?")
        return lad("Area is the space a shape covers. Which measurements are given?",
                   "Pick the right formula: rectangle = length × breadth, square = side × side, triangle = ½ × base × height." + (f" The numbers here: {', '.join(nums[:4])}." if nums else ""),
                   "Put the given numbers into the formula and work it out: ... = ?")
    # --- average ---
    if 'average' in sl:
        mfn = re.search(r'first (\d+) (?:natural|odd|even) numbers', sl)
        lst = seq_in(s)
        if mfn:
            n = mfn.group(1)
            kind = 'odd' if 'odd' in sl else ('even' if 'even' in sl else 'natural')
            return lad(
                f"What are the first {n} {kind} numbers? Write them out first.",
                f"List them, add them all, then divide the total by {n}.",
                f"Average = (sum of the {n} numbers) ÷ {n} = ?")
        if lst:
            return lad(
                f"We have the numbers {', '.join(lst)}. The average is the total shared out equally — what is it?",
                f"First add them all: {' + '.join(lst)}. Then divide by how many numbers there are ({len(lst)}).",
                f"Average = ({' + '.join(lst)}) ÷ {len(lst)} = ?")
        return lad("Average = total ÷ how many. What totals do you know here?",
                   f"Find the sum first, then divide by the count." + (f" Numbers given: {', '.join(nums[:6])}." if nums else ""),
                   "Average = sum ÷ count = ?")
    # --- HCF / LCM / GCD ---
    if re.search(r'h\.?c\.?f|g\.?c\.?d|highest common factor|greatest common', sl):
        ab = nums[:3]
        if any('.' in a for a in ab):
            return lad(
                f"We need the greatest common divisor of the decimals {', '.join(ab)}.",
                "Make them whole numbers first: multiply ALL of them by the same power of 10 (×100 here).",
                "Find the H.C.F. of those whole numbers, then divide it back by the same power of 10 = ?")
        if len(ab) >= 2:
            return lad(
                f"We need the H.C.F. of {ab[0]} and {ab[1]} — the LARGEST number that divides both exactly.",
                f"List the factors of {ab[0]} and the factors of {ab[1]}. Circle the ones they share.",
                f"Of the common factors of {ab[0]} and {ab[1]}, the largest one = ?")
    if re.search(r'l\.?c\.?m|least common|lowest common', sl):
        ab = nums[:2]
        if len(ab) == 2:
            return lad(
                f"We need the L.C.M. of {ab[0]} and {ab[1]} — the SMALLEST number both divide into.",
                f"Write the times tables of {ab[0]} and {ab[1]}. Look for the first number in both lists.",
                f"Multiples of {ab[0]}: {ab[0]}, ... Multiples of {ab[1]}: {ab[1]}, ... First shared one = ?")
    # --- divisibility ---
    if 'divisib' in sl:
        rules = {"2": "the last digit is even", "3": "the sum of the digits divides by 3",
                 "4": "the last two digits divide by 4", "5": "the last digit is 0 or 5",
                 "6": "it divides by both 2 and 3", "8": "the last three digits divide by 8",
                 "9": "the sum of the digits divides by 9", "10": "the last digit is 0",
                 "11": "the alternating digit sum divides by 11"}
        md = re.search(r'divisible by (\d+)', sl)
        if md and md.group(1) in rules:
            d = md.group(1)
            return lad(
                f"When is a number divisible by {d}? Recall the rule before checking anything.",
                f"Rule: a number divides by {d} when {rules[d]}.",
                f"Apply the rule to the number in the question, step by step: does it pass the test for {d}? = ?")
        if md:
            d = md.group(1)
            return lad(
                f"There's no single rule for {d} — but {d} can be split into smaller factors with known rules.",
                f"Break {d} into two CO-PRIME factors (factors that share nothing, like 9 and 10 for 90). A number divisible by both is divisible by their product.",
                f"Check each choice: are its two factors co-prime, and do they multiply to {d}? = ?")
    # --- face value vs place value ---
    if 'face value' in sl and 'place value' in sl:
        mfp = re.search(r'face value of (?:the digit )?(\d).{0,40}?place value of (?:the digit )?(\d) in (?:the number )?(\d[\d,]*)', sl)
        a, b, n = (mfp.group(1), mfp.group(2), mfp.group(3)) if mfp else (None, None, None)
        return lad(
            "Two different things: FACE value is just the digit itself; PLACE value depends on the digit's position.",
            (f"Face value of {a} = {a}. For the place value of {b} in {n}, find which position {b} sits in (ones, tens, hundreds...)."
             if a else "Find the face value (the digit itself) and the place value (digit × position value) separately."),
            "Now combine them the way the question asks (product = multiply, sum = add): ... = ?")
    # --- place value ---
    if 'place value' in sl or 'place' in sl and 'digit' in sl:
        mp = re.search(r'digit (\d).{0,30}?(\d[\d,]*)', s)
        return lad(
            "Each digit's value depends on its POSITION: ones, tens, hundreds, thousands...",
            ("Write the number with each digit under its place name. " +
             (f"Find where the digit {mp.group(1)} sits in {mp.group(2)}." if mp else "Find the position the question asks about.")),
            "Place value = digit × value of its position (1, 10, 100, 1000, ...) = ?")
    # --- percentage ---
    mp = re.search(r'(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)', sl)
    if mp:
        p, n = mp.group(1), mp.group(2)
        return lad(
            f"We need {p}% of {n}. Percent means 'out of 100'.",
            f"{p}% is the fraction {p}/100. 'Of' means multiply.",
            f"({p} ÷ 100) × {n} = ?")
    mp = re.search(r'express (\d+(?:\.\d+)?) as a percent of (\d+(?:\.\d+)?)', sl)
    if mp:
        a, b = mp.group(1), mp.group(2)
        return lad(
            f"How big is {a} compared with {b}, written as a percentage?",
            f"First write it as a fraction: {a}/{b}. To turn a fraction into a percent, multiply by 100.",
            f"({a} ÷ {b}) × 100 = ? %")
    if 'profit' in sl or 'gain' in sl or 'loss' in sl and t.startswith('profit'):
        return lad(
            "Sort the numbers first: what was PAID in total (cost price) and what was RECEIVED (selling price)?",
            f"Profit = selling price − total cost. Loss = total cost − selling price." + (f" Numbers here: {', '.join(nums[:4])}." if nums else ""),
            "Percent: (profit or loss ÷ cost price) × 100 = ? %")
    # --- ratio / proportion ---
    if 'proportion' in sl:
        return lad(
            "In a proportion a : b = c : d, the cross-products are equal." + (f" The numbers given: {', '.join(nums[:4])}." if nums else ""),
            "Multiply the outer pair together and the inner pair together — they must match.",
            "Set outer product = inner product, then solve for the missing value: ... = ?")
    if re.search(r'\d+\s*:\s*\d+', s) and ('equivalent' in sl or 'ratio' in sl):
        mr = re.search(r'(\d+)\s*:\s*(\d+)', s)
        a, b = mr.group(1), mr.group(2)
        return lad(
            f"The ratio is {a} : {b}. An equivalent ratio multiplies (or divides) BOTH parts by the same number.",
            f"Try a multiplier: {a} × k and {b} × k. Which choice keeps the two parts in that exact relationship?",
            f"Check each choice: divide its two parts — do you get back to {a} : {b}? = ?")
    # --- clock / calendar / time ---
    if 'angle between' in sl and 'hand' in sl:
        mt2 = re.search(r'at (\d{1,2}):(\d{2})', sl)
        tt = f"{mt2.group(1)}:{mt2.group(2)}" if mt2 else "the given time"
        return lad(
            f"At {tt}, where exactly does each hand point on the clock face?",
            "The clock face is 360° and has 12 hour marks, so each hour gap is 360 ÷ 12 = 30°.",
            f"Count the hour gaps between the two hands at {tt}, then: gaps × 30° = ?")
    if 'leap year' in sl and re.search(r'how many days', sl):
        return lad(
            "An ordinary year and a leap year differ by exactly one day. Which one is asked about?",
            "An ordinary year has 365 days. In a leap year, February gets one extra day.",
            "Days in a leap year = 365 + 1 = ?")
    if 'leap year' in sl:
        return lad(
            "What makes a year a leap year? Recall the rule before checking the choices.",
            "Rule: the year must divide exactly by 4. BUT century years (ending 00) must divide by 400.",
            "Test each choice: divide by 4 (and by 400 if it ends in 00). Which one passes? = ?")
    if re.search(r'minutes? are there in|convert.*hours|hours.*minutes', sl):
        mh = re.search(r'(\d+) hours? (\d+) minutes?', sl)
        if mh:
            h, mn = mh.group(1), mh.group(2)
            return lad(
                f"We must turn {h} hours {mn} minutes into minutes only.",
                f"Each hour is 60 minutes. So {h} hours = {h} × 60 minutes.",
                f"{h} × 60 + {mn} = ?")
    mwd = re.search(r'(\w+ \d+) is a (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday).*what day (?:of the week )?is (\w+ \d+)', s, re.I)
    if mwd:
        d1, wd, d2 = mwd.group(1), mwd.group(2), mwd.group(3)
        return lad(
            f"We know {d1} is a {wd}, and we want the weekday of {d2}.",
            f"Weekdays repeat every 7 days. Count how many days lie between {d1} and {d2}, then find the remainder after dividing by 7.",
            f"Move that remainder of days forward from {wd}: {wd} + remainder days = ?")
    if 'days' in sl and ('year' in sl or 'month' in sl or 'week' in sl):
        return lad(
            "What do we know about the calendar here? Re-read what period the question asks about.",
            "Useful facts: 1 week = 7 days, a year = 365 days, a LEAP year has one extra day in February.",
            "Use the right calendar fact and work it out: ... = ?")
    if t.startswith('clock') and len(nums) >= 2:
        return lad(
            f"What is known ({', '.join(nums[:3])}) and what is asked? Say it in your own words.",
            "Convert everything to the SAME unit first (seconds or minutes). 1 minute = 60 seconds.",
            "Total time ÷ number of items = time for one item = ?")
    # --- metric conversion ---
    conv = [("ml", "litre", "1 litre = 1000 mL", "÷ 1000"), ("cm", "m", "1 m = 100 cm", "÷ 100"),
            ("m", "km", "1 km = 1000 m", "÷ 1000"), ("g", "kg", "1 kg = 1000 g", "÷ 1000"),
            ("paise", "rs", "Rs 1 = 100 paise", "÷ 100"), ("mm", "cm", "1 cm = 10 mm", "÷ 10")]
    if 'convert' in sl or t.startswith('metric'):
        for small, big, fact, op in conv:
            if small in sl and big in sl:
                return lad(
                    f"Which units appear here, and which way are we converting? The numbers: {', '.join(nums[:3]) if nums else '—'}.",
                    f"Key fact: {fact}. Going small → big means dividing; big → small means multiplying.",
                    f"Apply the fact: {nums[0] if nums else 'amount'} {op} (or × the other way) = ?")
    # --- pictograph / pie ---
    if 'pictograph' in sl or 'symbol' in sl:
        ms2 = re.search(r'(\d+) symbols?.*?(\d+)', sl)
        if ms2:
            a, b = ms2.group(1), ms2.group(2)
            return lad(
                f"Each symbol stands for {b}, and there are {a} symbols. What total do they show?",
                f"That's {a} groups of {b}.",
                f"{a} × {b} = ?")
    if 'pie chart' in sl or 'pie graph' in sl:
        return lad(
            "A pie chart is a full circle split into slices. What does the whole circle stand for?",
            "The whole circle is one complete turn — think about how many degrees a full turn is.",
            "Slice value = (slice angle ÷ full turn) × total. Work the question's numbers into this = ?")
    # --- venn / sets ---
    if 'venn' in sl or t.startswith('sets'):
        if len(nums) >= 3:
            return lad(
                f"The groups overlap. Note each number: {', '.join(nums[:4])}. Who is counted where?",
                "People 'in both' sit in the overlap — they get counted inside each circle too. Don't count them twice.",
                "Only-one-group = that group's total − the overlap. Then: total − (only A + only B + both) = ?")
        return lad("Look at each region of the Venn diagram: only-left, only-right, and the overlap.",
                   "The overlap belongs to BOTH circles at once. Each circle's total includes its overlap.",
                   "Pick the region the question asks about and read/compute its value = ?")
    # --- coding ---
    if 'coded' in sl or 'written as' in sl or ('code' in sl and t.startswith('mental')):
        ws = re.findall(r'\b([A-Z]{2,})\b', s)
        if len(ws) >= 2:
            return lad(
                f"{ws[0]} becomes {ws[1]}. What happened to each letter?",
                f"Line them up letter by letter: {ws[0][0]}→{ws[1][0]}, {ws[0][1] if len(ws[0])>1 else ''}→{ws[1][1] if len(ws[1])>1 else ''}... How far does each letter move in the alphabet?",
                f"Apply the same letter-shift to {ws[2] if len(ws) > 2 else 'the new word'}, one letter at a time = ?")
    # --- mirror ---
    if 'mirror' in sl:
        if re.search(r'\d{1,2}:\d{2}', s):
            mt3 = re.search(r'(\d{1,2}:\d{2})', s).group(1)
            return lad(
                f"A mirror swaps left and right. Where would the hands of {mt3} appear in the mirror?",
                "Mirror-time trick: subtract the time from 12:00 (use 11:60 if you need to borrow minutes).",
                f"11:60 − {mt3} = ?")
        return lad("A mirror flips things LEFT-RIGHT (a rear-view mirror too).",
                   "Imagine the object pressed against the mirror — the left side appears on the right.",
                   "Flip the figure/word/number left-to-right in your head (or on paper) — what do you see? = ?")
    # --- blood relation ---
    if t.startswith('blood'):
        return lad(
            "Whose relationship to whom is asked? Underline the two people before anything else.",
            "Work from the END of the sentence backwards, drawing a mini family tree node by node.",
            "Label each person (M/F, generation up or down) on your tree, then read off the relationship = ?")
    # --- direction sense ---
    if t.startswith('direction') or ('faces' in sl and 'turn' in sl) or ('walks' in sl and ('north' in sl or 'south' in sl or 'east' in sl or 'west' in sl)):
        return lad(
            "Draw it! Mark the starting point and the four directions: N up, S down, E right, W left.",
            "Trace each move with an arrow, one step at a time. Right turn = one step clockwise (N→E→S→W); left = the other way.",
            "Compare the FINAL position/facing with the START on your sketch — which direction is it? = ?")
    # --- logical reasoning ---
    if t.startswith('logic') or ('all ' in sl and 'are' in sl and 'conclusion' in sl):
        return lad(
            "Which statements are FACTS here, and what exactly is being asked?",
            "Draw a circle for each group. 'All A are B' = circle A fully inside circle B. 'Some' = circles overlap.",
            "Test each choice against your circle drawing — keep only what MUST be true = ?")
    # --- paper folding ---
    if 'fold' in sl:
        return lad(
            "Track two things: how many LAYERS the folds make, and where the cut goes through them.",
            "Each fold doubles the layers: 1 fold = 2 layers, 2 folds = 4 layers. One cut goes through every layer.",
            "Unfold step by step in your head — each layer shows its own copy of the cut. How many copies / what shape? = ?")
    # --- counting figures ---
    if t.startswith('counting') or ('how many' in sl and ('triangle' in sl or 'square' in sl) and 'figure' in sl):
        return lad(
            "Don't count at random — you'll miss some. What sizes of shapes could be hiding in the figure?",
            "Count by size: first all the smallest ones, then the ones made of 2 pieces, then bigger combinations.",
            "Add up your counts: smallest + medium + largest = ?")
    # --- painted big-cube puzzles ---
    if 'painted' in sl and 'cube' in sl:
        mc3 = re.search(r'(\d+) cubes', sl)
        ntxt = mc3.group(1) if mc3 else None
        return lad(
            "A big painted cube was cut into small cubes. Where a small cube sat decides how many painted faces it has.",
            "Corners get 3 painted faces, edge cubes get 2, face-centre cubes get 1 — and the cubes hidden INSIDE get 0.",
            (f"The big cube is n × n × n with n³ = {ntxt}, so find n. Hidden inner cubes = (n − 2) × (n − 2) × (n − 2) = ?"
             if ntxt else "For an n × n × n cube, the hidden inner block is (n − 2)³. Work out n first, then (n − 2)³ = ?"))
    # --- cubes and dice ---
    if 'cube' in sl or 'dice' in sl or 'die' in sl:
        return lad(
            "Picture a real dice in your hand (or grab one!). What feature does the question ask about?",
            "Turn it slowly: count the flat surfaces, the straight edges where two surfaces meet, or the sharp corners.",
            "Count systematically — top/bottom, then the ring around the middle. Total = ?")
    # --- algebra ---
    if t.startswith('algebra') or re.search(r'\b\d*x\b', s):
        mv = re.search(r'when ([a-z]) = (\d+)', sl)
        if mv:
            var, v = mv.group(1), mv.group(2)
            return lad(
                f"We know {var} = {v}. The expression asks us to use that value.",
                f"Replace every {var} in the expression with {v}, keeping the other numbers as they are (remember {var}² means {v} × {v}).",
                f"Now compute, powers and multiplication before addition/subtraction: ... = ?")
        if 'coefficient' in sl:
            return lad(
                "A coefficient is the NUMBER multiplying a letter (variable).",
                "Find the exact term the question names — watch the sign in front of it (+ or −).",
                "Read off the number stuck to that variable, including its sign = ?")
        if 'terms' in sl:
            return lad(
                "Terms are the chunks separated by + and − signs.",
                "Underline each chunk between the + / − signs, including the lone constant at the end.",
                "Count the underlined chunks = ?")
        if 'like terms' in sl:
            return lad(
                "When can two algebra terms be added together directly?",
                "Compare the LETTER parts: 3xy and 5xy match; 3xy and 3x do not.",
                "Like terms have identical variable parts (same letters, same powers). Which choice says that? = ?")
    # --- magic square / money ---
    if 'magic square' in sl:
        return lad(
            "In a magic square every row, column and diagonal adds to the SAME magic total.",
            f"Use the given total and the cells you know to find the missing cells one line at a time." + (f" Numbers: {', '.join(nums[:4])}." if nums else ""),
            "Magic total − (sum of the known cells in that line) = the missing cell = ?")
    if 'coins make' in sl or 'paise coins' in sl:
        return lad(
            "How much is ONE coin worth, and what total do we need to reach?",
            "First: how many of these coins make 1 rupee? (100 paise = Rs 1.)",
            "Coins for Rs 1 × number of rupees needed = ?")
    # --- data handling ---
    if 'range' in sl and seq_in(s):
        lst = seq_in(s)
        return lad(
            f"The data is {', '.join(lst)}. The range measures how spread out it is.",
            "Find the largest value and the smallest value in the list.",
            "Range = largest − smallest = ?")
    if 'mean' in sl or 'median' in sl or 'mode' in sl:
        return lad(
            "Three different 'middles': mean, median, mode. Which one does the question want?",
            "Mean = add all ÷ count. Median = middle value AFTER sorting. Mode = the value appearing most often.",
            "Apply the right one to the data given = ?")
    # --- angles ---
    if 'complement' in sl or 'supplement' in sl:
        ma = re.search(r'(\d+)°', s)
        a = ma.group(1) if ma else 'the angle'
        if 'complement' in sl:
            return lad(f"Complementary angles make a corner — they add to 90°. One of them is {a}°." if ma else "Complementary angles add to 90°.",
                       f"So the partner of {a}° is whatever is left out of 90°.",
                       f"90° − {a}° = ?")
        return lad(f"Supplementary angles make a straight line — they add to 180°. One is {a}°." if ma else "Supplementary angles add to 180°.",
                   f"The partner of {a}° is what remains of 180°.",
                   f"180° − {a}° = ?")
    if re.search(r'angle.*(?:called|classified|measures)', sl) or ('angle' in sl and '°' in s):
        return lad(
            "Angle families: acute < 90°, right = 90°, obtuse between 90° and 180°, straight = 180°, reflex > 180°.",
            "Place the angle from the question on that scale.",
            "Which family's range does it fall into? = ?")
    # --- polygons ---
    if 'polygon' in sl or 'quadrilateral' in sl:
        return lad(
            "What property of the polygon is asked — sides, angles, or a name?",
            "Useful facts: exterior angles of ANY polygon total 360°; a quadrilateral's interior angles total 360°; a triangle's total 180°.",
            "Pick the fact that matches the question and apply it = ?")
    # --- symmetry ---
    if 'symmetry' in sl:
        return lad(
            "A line of symmetry folds the shape onto itself exactly — both halves match.",
            "Test each shape in your head: fold it top-to-bottom, left-to-right, and along the diagonals.",
            "Count the folds that work perfectly for each choice — which fits what the question asks? = ?")
    # --- decimals ---
    if re.search(r'\d\.\d', s) and ('+' in s or '-' in s or 'add' in sl):
        ds = re.findall(r'\d+\.\d+|\d+', s)[:3]
        return lad(
            f"We are combining the decimals {', '.join(ds)}. Line them up before adding.",
            "Stack them with the decimal POINTS in a straight column; fill empty places with zeros.",
            f"Add column by column from the right: {' + '.join(ds)} = ?")
    if 'rounded' in sl or 'round' in sl:
        mr2 = re.search(r'(\d+\.?\d*) rounded to the nearest (\w+)', sl)
        if mr2:
            v, unit = mr2.group(1), mr2.group(2)
            return lad(
                f"We must round {v} to the nearest {unit}.",
                f"Find the {unit} digit in {v}, then look at the digit just AFTER it: 5 or more rounds up, less than 5 keeps it.",
                f"Apply the rule to {v} = ?")
    if 'simplest form' in sl or 'simplify' in sl:
        return lad(
            "Simplest form = divide top and bottom by everything they share.",
            "First write the decimal/fraction as a plain fraction (0.44 → 44/100 style), then find a common factor of top and bottom.",
            "Keep dividing both by common factors until nothing divides both = ?")
    if 'descending' in sl or 'ascending' in sl or ('order' in sl and 'fraction' in sl):
        return lad(
            "Descending = biggest first; ascending = smallest first. Which is asked?",
            "To compare fractions, give them the SAME denominator (or compare each to 1: how far away is it?).",
            "Sort the values once they're comparable, then match against the choices = ?")
    # --- roman numerals ---
    if 'roman' in sl:
        return lad(
            "Roman numeral rules: I=1, V=5, X=10, L=50, C=100. A letter never repeats more than 3 times.",
            "V and L are never repeated at all, and only smaller symbols are subtracted (IV, IX, XL...).",
            "Check each choice against these rules — which one breaks (or follows) them? = ?")
    # --- prime / co-prime ---
    if 'prime' in sl:
        return lad(
            "A prime number has exactly two factors: 1 and itself. Co-primes share NO common factor except 1.",
            f"Check the numbers in the question one by one: list their factors." + (f" Numbers: {', '.join(nums[:3])}." if nums else ""),
            "Use the definitions on the given numbers and match the choice that fits = ?")
    # --- statements / assertion ---
    if 'statement' in sl or 'assertion' in sl:
        return lad(
            "Judge each statement on its OWN first — true or false?",
            "Recall the exact math fact each statement uses; test it with a small example if unsure.",
            "Now combine your verdicts and pick the choice that matches them = ?")
    # --- multiplication/division word ---
    mm = re.search(r'(\d+)\s*(?:x|×)\s*(\d+)', s)
    if mm and t.startswith(('multiplication', 'addition')):
        a, b = mm.group(1), mm.group(2)
        return lad(
            f"The expression uses {a} and {b}. What is the question really asking about them?",
            f"Break it apart: {a} × {b} can be split by place value ({a} × tens + {a} × ones).",
            f"Work each part out and compare with the choices: {a} × {b} = ?")
    if 'sum of' in sl and 'odd' in sl:
        return lad(
            "Write out the numbers being summed before adding anything.",
            "Pair them up — first + last, second + second-last. Each pair adds to the same total!",
            "Number of pairs × pair total = ?")
    if re.search(r'a \+ b = (\d+) and a - b = (\d+)', sl):
        m2 = re.search(r'a \+ b = (\d+) and a - b = (\d+)', sl)
        p1, p2 = m2.group(1), m2.group(2)
        return lad(
            f"Two facts: a + b = {p1} and a − b = {p2}. We want one of the letters.",
            "Add the two equations together — the b's cancel out, leaving only a's.",
            f"2a = {p1} + {p2}, so a = ({p1} + {p2}) ÷ 2 = ?")
    # --- generic with numbers ---
    if nums:
        return lad(
            f"What is known ({', '.join(nums[:4])}) and what exactly is asked? Say it in your own words.",
            f"Choose the operation the story needs (add, subtract, multiply, divide) and set it up with {', '.join(nums[:3])}.",
            "Write the calculation out and solve it step by step: ... = ?")
    # --- generic, no numbers ---
    return lad(
        "Read the question again slowly — what is given, and what is asked?",
        "Recall the key fact or rule for this topic, then test each choice against it.",
        "Eliminate the choices that break the rule; check the one that remains = ?")

# ---------------- 5. direction-hint replacement (g1/g2 shapes) ----------------
DIR_STEM = re.compile(r'faces? (North|South|East|West)\b.*turn(?:s|ed)? ?(left|right|around)', re.I)
COORD_STEM = re.compile(r'\((\d+)\s*,\s*(\d+)\)')
SHAPE_HINT = re.compile(r'sides|corners|Triangle = 3|3D shapes|Cube: 6 faces|edges', re.I)

def fix_direction_hints(q, f):
    h = q.get("hint")
    if not isinstance(h, dict): return False
    ht = ' '.join(str(v) for v in h.values())
    if not SHAPE_HINT.search(ht): return False
    s = q["stem"]
    md = DIR_STEM.search(s)
    if md:
        d, turn = md.group(1).capitalize(), md.group(2).lower()
        step = {"left": "one step counter-clockwise (the opposite way of N→E→S→W)",
                "right": "one step clockwise (N→E→S→W)",
                "around": "two steps (a half turn, straight to the opposite side)"}[turn]
        q["hint"] = {
            "level_0": f"Someone is facing {d} and then makes a {turn} turn. Which way are they facing after the turn?",
            "level_1": "Picture a compass: going clockwise the order is North → East → South → West → back to North. A right turn moves one step along this order; a left turn moves one step backwards; turning around jumps to the opposite direction.",
            "level_2": f"Put your finger on {d} on the compass and move {step}. The direction you land on = ?",
        }
        rec("hint_direction_rebuilt", f, q.get("id"))
        return True
    mc = COORD_STEM.search(s)
    if mc:
        x, y = mc.group(1), mc.group(2)
        q["hint"] = {
            "level_0": f"The point ({x}, {y}) has two parts: the first number and the second number. What does each one tell you?",
            "level_1": f"On a grid, the FIRST number ({x}) says how far to go ACROSS (right), and the SECOND number ({y}) says how far to go UP.",
            "level_2": f"Start at the corner (0, 0). Move {x} across, then {y} up. Where are you / what do you find there? = ?",
        }
        rec("hint_coordinate_rebuilt", f, q.get("id"))
        return True
    return False

# ---------------- 6. targeted individual fixes ----------------
COMPARISON_IDS = {"A3-NUM-0220", "A3-NUM-0276", "A3-NUM-0324", "A3-NUM-0379",
                  "A3-NUM-0438", "A3-NUM-0489", "A3-NUM-0545", "A3-NUM-0592"}
PLACE_VALUE_IDS = {"A5-ARI-0671", "A5-ARI-0736", "A5-ARI-0777"}
AVERAGE_IDS = {"A4-ASB-0136", "A4-ASB-0171", "A4-ASB-0258", "A4-NUM-0179", "A4-NUM-0188"}
DELETE_IDS = {
    # 31 verified-unanswerable visual questions (scanner criticals)
    ("grade1/g1-counting.json", i) for i in
    ["A1-CNT-0373","A1-CNT-0459","A1-CNT-0583","A1-CNT-0525","A1-CNT-0637","A1-CNT-0669",
     "A1-CNT-0680","A1-CNT-0705","A1-CNT-0672","A1-CNT-0681","A1-CNT-0695","A1-CNT-0709",
     "A1-CNT-0714","A1-CNT-0810","A1-CNT-0765","A1-CNT-0797","A1-CNT-0823","A1-CNT-0899","A1-CNT-0906"]
} | {
    ("grade1/g1-measurement.json", i) for i in
    ["A1-MSR-0005","A1-MSR-0017","A1-MSR-0025","A1-MSR-0028","A1-MSR-0052"]
} | {
    ("grade1/g1-shapes.json", "A1-SHP-0536"),
    ("grade2/g2-word-problems.json", "A2-WPR-0218"),
} | {
    ("grade1/g1-word-problems.json", i) for i in
    ["A1-WPR-0266","A1-WPR-0284","A1-WPR-0290","A1-WPR-0293","A1-WPR-0294"]
} | {
    # "What comes next?" with genuinely NO sequence (text or visual)
    ("grade1/olympiad-topic-3-patterns.json", "T3-151"),
    ("grade1/olympiad-topic-3-patterns.json", "T3-171"),
    ("grade1/olympiad-topic-3-patterns.json", "T3-176"),
    ("grade2/olympiad-topic-3-patterns.json", "T3-0958"),
    ("grade5/olympiad-topic-2-arithmetic.json", "T2-1197"),
}
NULL_SVG_IDS = {  # stem-vs-svg object mismatch, text-solvable -> drop the confusing visual
    ("grade1/g1-patterns.json", "A1-PAT-0281"), ("grade1/g1-patterns.json", "A1-PAT-0292"),
    ("grade1/g1-patterns.json", "A1-PAT-0308"), ("grade2/g2-shapes.json", "A2-SHP-0510"),
    ("grade2/g2-word-problems.json", "A2-WPR-0481"), ("grade2/olympiad-topic-1-counting.json", "T1-577"),
    ("grade2/olympiad-topic-7-word-problems.json", "T7-426"),
}

def place_value_compute(stem):
    m = re.search(r'place value of (?:the )?digit (\d) in ([\d,]+)', stem)
    if not m: return None
    d, n = m.group(1), m.group(2).replace(",", "")
    if n.count(d) != 1: return None
    idx = n.find(d)
    return int(d) * 10 ** (len(n) - idx - 1)

def targeted_fix(q, rel, f):
    qid = q.get("id")
    stem = q["stem"]
    # --- 8 comparison questions: choices must be the two compared numbers ---
    if qid in COMPARISON_IDS:
        m = re.search(r'Which is greater:\s*([\d,]+)\s+or\s+([\d,]+)\?', stem)
        if m:
            a, b = m.group(1), m.group(2)
            va, vb = parse_num(a), parse_num(b)
            q["choices"] = [a, b, "Both are equal", "Cannot compare"]
            q["correct_answer"] = 0 if va > vb else 1
            rec("answer_fixed_comparison", f, qid, f"choices -> [{a},{b}], key {'a' if va>vb else 'b'}")
        return
    # --- place value off x10 ---
    if qid in PLACE_VALUE_IDS:
        true = place_value_compute(stem)
        if true is not None and q.get("correct_value") != true:
            rec("answer_fixed_place_value", f, qid, f"correct_value {q.get('correct_value')} -> {true}")
            q["correct_value"] = true
        return
    # --- averages keyed as truncated ints: adjust last score ---
    if qid in AVERAGE_IDS:
        m = re.search(r'scores are ([\d, ]+)\.', stem)
        if m:
            scores = [int(x) for x in re.findall(r'\d+', m.group(1))]
            n = len(scores); kv = int(q["correct_value"])
            diff = sum(scores) - kv * n
            if diff != 0:
                old_last = scores[-1]; new_last = old_last - diff
                if new_last > 0:
                    parts = m.group(1).split(',')
                    parts[-1] = ' ' + str(new_last)
                    q["stem"] = stem.replace(m.group(1), ','.join(parts))
                    scores[-1] = new_last
                    rec("answer_fixed_average", f, qid, f"score {old_last} -> {new_last}; avg now exactly {kv}")
        # proper average hint (replaces wrong-topic bar-graph hints)
        sc = re.findall(r'\d+', re.search(r'scores are ([\d, ]+)\.', q["stem"]).group(1))
        q["hint"] = {
            "level_0": f"The scores are {', '.join(sc)}. The average shares the total out equally — what is it?",
            "level_1": f"First add all {len(sc)} scores: {' + '.join(sc)}. Then divide the total by {len(sc)}.",
            "level_2": f"Average = ({' + '.join(sc)}) ÷ {len(sc)} = ?",
        }
        return
    # --- T3-517: sequence has no rule; keyed 'Add 4 each time' ---
    if qid == "T3-517":
        q["stem"] = stem.replace("3, 16, 24, 36", "8, 12, 16, 20")
        q["hint"] = {
            "level_0": "A pattern has a rule. Find the rule first, then check it on every step.",
            "level_1": "Look at the differences between neighbours: 12 − 8, 16 − 12, 20 − 16. Are they all the same?",
            "level_2": "If every jump is the same number, the rule is 'add that number each time'. What is the jump? = ?",
        }
        rec("answer_fixed_pattern_rule", f, qid, "sequence -> 8, 12, 16, 20 (consistent +4)")
        return
    # --- T7-1090: work-rate; make together-time exactly 10 days ---
    if qid == "T7-1090" and "2/5 in 8 days" in stem:
        q["stem"] = stem.replace("2/5 in 8 days", "2/5 in 12 days")
        q["hint"] = {
            "level_0": "If A does 1/3 of the work in 5 days, how long for ALL the work? Same question for B.",
            "level_1": "A: full work = 5 × 3 = 15 days, so A does 1/15 per day. B: full work = 12 × (5/2) = 30 days, so B does 1/30 per day.",
            "level_2": "Together per day: 1/15 + 1/30 = ? per day. Days needed = 1 ÷ (that fraction) = ?",
        }
        rec("answer_fixed_workrate", f, qid, "B '2/5 in 8 days' -> '2/5 in 12 days'; 1/15+1/30=1/10 -> 10 days (keyed)")
        return
    # --- T7-1046: mixture; make water-to-add exactly 4 litres ---
    if qid == "T7-1046" and "A mixture of 40 litres" in stem:
        q["stem"] = stem.replace("A mixture of 40 litres", "A mixture of 24 litres")
        q["hint"] = {
            "level_0": "The 24 litres are split in the ratio 7 : 1. How much is milk and how much is water right now?",
            "level_1": "7 + 1 = 8 parts, so each part is 24 ÷ 8 = 3 litres. Milk = 7 parts, water = 1 part. Adding water changes only the water amount.",
            "level_2": "We need milk : water = 3 : 1. Milk stays at 21 litres, so water must become 21 ÷ 3 = 7 litres. Water to add = 7 − 3 = ?",
        }
        rec("answer_fixed_mixture", f, qid, "40 litres -> 24 litres; 21:3 + 4 = 21:7 = 3:1 (keyed 4 litres)")
        return
    # --- A6-ARI-0355 / A6-NUM-0304: percent-of must hit keyed 12 ---
    if qid == "A6-ARI-0355" and "50% of 25" in stem:
        q["stem"] = stem.replace("50% of 25", "50% of 24")
        h = q.get("hint") or {}
        for k in h: h[k] = h[k].replace("25", "24")
        rec("answer_fixed_percent", f, qid, "50% of 25 -> 50% of 24 = 12 (keyed)")
        return
    if qid == "A6-NUM-0304" and "25% of 50" in stem:
        q["stem"] = stem.replace("25% of 50", "25% of 48")
        h = q.get("hint") or {}
        for k in h: h[k] = h[k].replace("50", "48")
        rec("answer_fixed_percent", f, qid, "25% of 50 -> 25% of 48 = 12 (keyed)")
        return
    # --- T6-012: answerable general knowledge; remove visual dependency ---
    if qid == "T6-012" and "shaped like which figure" in stem:
        q["stem"] = stem.replace("Chikoo looks at the shapes. A stop sign is shaped like which figure?",
                                 "Chikoo thinks about road signs. Which shape is a stop sign?")
        rec("stem_reworded_visual_ref", f, qid)
        return
    # --- T4-072: text-solvable; remove picture reference + stale lettering ---
    if qid == "T4-072" and "Which picture shows the boy?" in stem:
        q["stem"] = re.sub(r'\s*Which picture shows the boy\?.*$', ' What is Chikoo wearing?', stem)
        rec("stem_reworded_visual_ref", f, qid)
        return
    # --- wb_L4_s10_q02: sequence lives in the SVG; mirror it into the stem ---
    if qid == "wb_L4_s10_q02" and stem.strip() == "What comes next in the sequence?":
        q["stem"] = "What comes next in the sequence? 4, 8, 12, 16, 20, 24, ___"
        rec("stem_enriched_from_svg", f, qid)
        return

# ---------------- 7. negative-money fixes ----------------
MONEY_RE = re.compile(r'starts with ₹(\d+)\. Buys a book for ₹(\d+), then a snack for ₹(\d+)')
def fix_negative_money(q, f):
    stem = q["stem"]; qid = q.get("id")
    ch = q.get("choices") or []; ca = q.get("correct_answer")
    if not (ch and isinstance(ca, int) and 0 <= ca < len(ch)): return False
    kv = parse_num(ch[ca])
    m = MONEY_RE.search(stem)
    if m:
        S, B, C = map(int, m.groups())
        if B + C > S and kv is not None and kv < 0 and abs(kv) == B + C - S:
            newS = B + C + int(abs(kv))
            q["stem"] = stem.replace(f"starts with ₹{S}.", f"starts with ₹{newS}.", 1)
            _flip_negative_choices(q, f)
            left = newS - B - C
            q["hint"] = {
                "level_0": f"Money starts at ₹{newS}, then two things are bought: ₹{B} and ₹{C}. How much remains?",
                "level_1": f"First find the total spent: ₹{B} + ₹{C}. Then take that away from ₹{newS}.",
                "level_2": f"₹{newS} − (₹{B} + ₹{C}) = ?",
            }
            rec("money_fixed", f, qid, f"start ₹{S} -> ₹{newS}; left = {left} (keyed)")
            return True
    # missing "starts with" sentence entirely (T7-777 / T7-825 class)
    m2 = re.search(r'Buys a book for ₹(\d+), then a snack for ₹(\d+)\. How much money is left\?', stem)
    if m2 and 'starts with' not in stem and kv is not None and kv < 0:
        B, C = int(m2.group(1)), int(m2.group(2))
        newS = B + C + int(abs(kv))
        subj = intro_name(stem) or "Kiwi"
        q["stem"] = stem.replace("Buys a book", f"{subj} starts with ₹{newS}. Buys a book", 1)
        _flip_negative_choices(q, f)
        q["hint"] = {
            "level_0": f"Money starts at ₹{newS}, then two things are bought: ₹{B} and ₹{C}. How much remains?",
            "level_1": f"First find the total spent: ₹{B} + ₹{C}. Then take that away from ₹{newS}.",
            "level_2": f"₹{newS} − (₹{B} + ₹{C}) = ?",
        }
        rec("money_fixed_missing_start", f, qid, f"inserted start ₹{newS}; left = {abs(int(kv))} (keyed)")
        return True
    return False

def _flip_negative_choices(q, f):
    ch = q["choices"]
    seen = {str(c).strip() for c in ch}
    for i, c in enumerate(ch):
        cs = str(c).strip()
        if re.fullmatch(r'-\d+', cs):
            pos = cs[1:]
            if pos in seen:           # collision -> nudge by 1
                pos = str(int(pos) + 1)
                while pos in seen: pos = str(int(pos) + 1)
            ch[i] = pos
            seen.add(pos)

# ---------------- file IO preserving format ----------------
def detect_fmt(path):
    raw = open(path, encoding="utf-8").read()
    m = re.search(r'\n(\s+)"', raw)
    indent = len(m.group(1)) if m else 1
    ascii_only = all(ord(c) < 128 for c in raw)
    return indent, ascii_only, raw.endswith("\n")

def save(path, doc, fmt):
    indent, ascii_only, trail_nl = fmt
    txt = json.dumps(doc, ensure_ascii=ascii_only, indent=indent)
    if trail_nl: txt += "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(txt)

# ---------------- main ----------------
files = sorted(glob.glob(os.path.join(ROOT, "grade*", "*.json")))
before_total = 0
after_total = 0
file_qcounts = {}

for fpath in files:
    if fpath.endswith("topics.json"): continue
    rel = os.path.relpath(fpath, ROOT)
    fmt = detect_fmt(fpath)
    doc = json.load(open(fpath, encoding="utf-8"))
    qs = doc["questions"] if isinstance(doc, dict) else doc
    before_total += len(qs)
    modified = False
    keep = []
    is_wavebook = os.path.basename(fpath).startswith("wavebook")
    is_g12_shapes = rel in ("grade1/g1-shapes.json", "grade2/g2-shapes.json")

    for q in qs:
        qid = q.get("id", "?")
        # ---- deletions (verified unanswerable) ----
        if (rel, qid) in DELETE_IDS:
            deleted.append({"file": rel, "id": qid, "reason": "missing_visual_unanswerable", "question": q})
            rec("deleted_missing_visual", rel, qid, q.get("stem", "")[:100])
            modified = True
            continue

        stem0 = q.get("stem") or ""
        # ---- name-concatenation artifacts ("Kiwi There are 13 bunches...") ----
        new = re.sub(r'\b(?:Kiwi|Chikoo|Aarohi|Vanya|Riya|Ved|Nuha|Google|Veronica)\s+(There (?:are|is)\b)', r'\1', stem0)
        if new != stem0:
            q["stem"] = new; modified = True
            rec("stem_fixed_name_concat", rel, qid)

        # ---- interaction modes ----
        m = q.get("interaction_mode")
        ch = q.get("choices") or []
        if m == "tap_to_reveal":
            q["interaction_mode"] = "mcq" if len(ch) >= 2 else ("integer" if q.get("correct_value") is not None else "mcq")
            rec("mode_tap_to_reveal_to_" + q["interaction_mode"], rel, qid); modified = True
        elif m == "multiple_choice":
            q["interaction_mode"] = "mcq"
            rec("mode_multiple_choice_to_mcq", rel, qid); modified = True
        elif m is None:
            if len(ch) >= 2:
                q["interaction_mode"] = "mcq"; rec("mode_null_to_mcq", rel, qid); modified = True
            elif q.get("correct_value") is not None:
                q["interaction_mode"] = "integer"; rec("mode_null_to_integer", rel, qid); modified = True

        # ---- junk (alt) distractors ----
        if any(re.search(r'\((?:alt|same|dup|placeholder|v2)\)', str(c)) for c in ch):
            if fix_alt_choices(q, rel): modified = True

        # ---- targeted individual fixes ----
        s_before = q["stem"]
        targeted_fix(q, rel, rel)
        if q["stem"] != s_before or qid in COMPARISON_IDS | PLACE_VALUE_IDS | AVERAGE_IDS:
            modified = True

        # ---- negative money ----
        if '₹' in q["stem"] and 'Buys a book' in q["stem"]:
            if fix_negative_money(q, rel): modified = True

        # ---- broken-name repairs ----
        if is_genuine_broken(q["stem"]):
            res = repair_stem(q, rel)
            if res == "delete":
                deleted.append({"file": rel, "id": qid, "reason": "broken_name_unrepairable", "question": q})
                rec("deleted_broken_name", rel, qid, q.get("stem", "")[:100])
                modified = True
                continue
            elif res:
                modified = True

        # ---- mismatched SVG nulling ----
        if (rel, qid) in NULL_SVG_IDS and q.get("visual_svg"):
            q["visual_svg"] = None
            q["visual_alt"] = None
            if "visual_type" in q: q["visual_type"] = "none"
            if "visual_requirement" in q: q["visual_requirement"] = "none"
            rec("svg_nulled_mismatch", rel, qid); modified = True

        # ---- wavebook hints ----
        if is_wavebook and q.get("hint") is None:
            q["hint"] = gen_wb_hint(q, q.get("topic") or "")
            # leak guard
            astrs = ans_strings(q)
            for k, v in list(q["hint"].items()):
                if leak_check(v, astrs):
                    q["hint"][k] = scrub_level(v, astrs)
            rec("hint_generated_wavebook", rel, qid)
            if len(hint_samples) < 30:
                hint_samples.append({"file": rel, "id": qid, "topic": q.get("topic"),
                                     "stem": q["stem"][:160], "hint": q["hint"]})
            modified = True

        # ---- g1/g2 shapes direction hints ----
        if is_g12_shapes:
            if fix_direction_hints(q, rel): modified = True

        # ---- hint leak scrub (after all hint writes) ----
        if scrub_hints(q, rel): modified = True
        if dedupe_hint_levels(q, rel): modified = True

        # ---- off-grade G1 listing (report only) ----
        if rel.startswith("grade1/"):
            og = None
            if re.search(r'km/h|km per hour|kmph', q["stem"]):
                og = "speed/rate problem in Grade 1"
            else:
                mx = re.search(r'(\d+)\s*[×x*]\s*(\d+)', q["stem"]) or \
                     re.search(r'(\d+) rows of \w+ with (\d+)', q["stem"])
                if mx and int(mx.group(1)) * int(mx.group(2)) > 25:
                    og = f"multiplication {mx.group(1)}x{mx.group(2)} beyond G1 scope"
            if og:
                offgrade.append({"file": rel, "id": qid, "issue": og, "stem": q["stem"][:120]})

        keep.append(q)

    if len(keep) != len(qs):
        if isinstance(doc, dict):
            doc["questions"] = keep
            if "total_questions" in doc:
                doc["total_questions"] = len(keep)
        modified = True
    after_total += len(keep)
    file_qcounts[rel] = len(keep)

    if modified and APPLY:
        save(fpath, doc, fmt)

# ---- topics.json + _metadata.json count sync ----
if APPLY:
    grade_totals = collections.Counter()
    for rel, n in file_qcounts.items():
        grade_totals[rel.split("/")[0]] += n
    for g in sorted(grade_totals):
        tpath = os.path.join(ROOT, g, "topics.json")
        if os.path.exists(tpath):
            fmt = detect_fmt(tpath)
            td = json.load(open(tpath, encoding="utf-8"))
            changed = False
            for t in td.get("topics", []):
                relf = f"{g}/{t.get('file')}"
                if relf in file_qcounts and t.get("total_questions") != file_qcounts[relf]:
                    t["total_questions"] = file_qcounts[relf]; changed = True
            if td.get("total_questions") != grade_totals[g]:
                td["total_questions"] = grade_totals[g]; changed = True
            if changed: save(tpath, td, fmt)
    mpath = os.path.join(ROOT, "_metadata.json")
    if os.path.exists(mpath):
        fmt = detect_fmt(mpath)
        md = json.load(open(mpath, encoding="utf-8"))
        md["total_questions"] = after_total
        for g, info in md.get("grades", {}).items():
            info["questions"] = grade_totals.get(f"grade{g}", info.get("questions"))
        save(mpath, md, fmt)

# ---- outputs ----
summary = {
    "applied": APPLY,
    "before_total": before_total,
    "after_total": after_total,
    "deleted": len(deleted),
    "actions": dict(sorted(log.items())),
    "offgrade_g1_count": len(offgrade),
}
print(json.dumps(summary, indent=1, ensure_ascii=False))
if APPLY:
    json.dump(deleted, open(os.path.join(OUT, "prod_deleted_questions.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(changes, open(os.path.join(OUT, "prod_fixes_applied.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(offgrade, open(os.path.join(OUT, "prod_offgrade_report.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(hint_samples, open(os.path.join(OUT, "prod_hint_samples.json"), "w"), indent=1, ensure_ascii=False)
else:
    json.dump(deleted, open(os.path.join(OUT, "prod_planned_deletions.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(hint_samples, open(os.path.join(OUT, "prod_hint_samples.json"), "w"), indent=1, ensure_ascii=False)
