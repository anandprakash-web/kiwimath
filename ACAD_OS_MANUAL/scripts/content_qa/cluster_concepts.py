#!/usr/bin/env python3
"""
Concept clustering / skill tagging for the adaptive layer.

Tags every served question (olympiad L1-L7 + curriculum) with the SKILL CLUSTER
it belongs to: number-varied and wording-varied copies of one concept collapse
into a single skill_id. Idempotent — re-run after any new import to re-tag.

Adds (additive only): skill_id, skill_size, skill_rank, is_skill_original.
Writes content-live/skill_clusters.json (skill_id -> metadata + members).

Usage:  cd ~/Downloads/kiwimath/content-live && python3 qa-reports/cluster_concepts.py
Tunables: TH (merge threshold, 0.70), NAME lexicon (auto-built from the data).
"""
import json, re, glob, os, hashlib
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # content-live/
TH = 0.70  # leader-clustering Jaccard threshold (lower = coarser concepts)

# ---- build a character-name lexicon from the data (cap. tokens before person-verbs) ----
def build_names():
    NON = set("Who After You It One He She They We Skip Buys Half By Fill Without Calculate "
              "Let My This That Each Find Help Write Count Show Prove Solve Evaluate Determine "
              "Compute State Use The A An In On At How What Which If When Where Two Three Four "
              "Five Six Seven Eight Nine Ten Now Then Next First Second Third Last Both All Some "
              "Many Total Add Subtract Round".split())
    from collections import Counter
    cap = Counter()
    PV = re.compile(r'\b([A-Z][a-z]+)\b(?=\s+(has|have|sees|saw|finds|found|collects|buys|bought|'
                    r'makes|made|wants|gets|got|puts|gives|gave|adds|counts|practices|shares|picks|'
                    r'draws|eats|reads|runs|plays|needs|takes|met|wrote|sells|paints|builds|bakes|catches))')
    SUBJ = re.compile(r'(?:^|\.\s+|Help\s+|,\s+)([A-Z][a-z]+)\b')
    for f in FILES:
        for q in load(f):
            s = q.get("stem", "")
            for m in PV.findall(s): cap[m[0]] += 1
            for m in SUBJ.findall(s): cap[m] += 1
    names = set(w for w, c in cap.items() if c >= 3 and w not in NON)
    names |= set("Builder Detective Knight Pirate Chef Captain Ranger Professor Doctor Master King Queen Wizard".split())
    return names

def load(f):
    d = json.load(open(f))
    return d.get("questions", d if isinstance(d, list) else [])

FILES = sorted(f for f in glob.glob(os.path.join(ROOT, "olympiad", "L*", "L*.json"))
               + glob.glob(os.path.join(ROOT, "curriculum", "*", "grade*", "questions.json"))
               if os.path.getsize(f) > 800)

NAMES = build_names()
NAMEALT = '|'.join(sorted((re.escape(n) for n in NAMES), key=len, reverse=True))
HELPER = re.compile(r'^\s*(help\s+(<n>\s*)+(figure out( the count)?|with this|calculate|work out)?\s*[:!,-]?\s*)', re.I)
STOP = set("the a an of to in on at is are be how many what which find compute evaluate this that "
           "for and or with from each does do you your it as into are there given".split())
OPS = [('×', ' mul '), ('⋅', ' mul '), ('·', ' mul '), ('✕', ' mul '), ('÷', ' div '),
       ('−', ' sub '), ('–', ' sub '), ('—', ' sub '), ('%', ' pct '), ('√', ' sqrt '),
       ('²', ' sq '), ('³', ' cube ')]

def toks(stem):
    s = re.sub(r'\b(' + NAMEALT + r')\b', '<n>', stem).lower()
    for a, b in OPS: s = s.replace(a, b)
    s = re.sub(r'\d+(?:\.\d+)?', '#', s)
    s = HELPER.sub('', s)
    s = re.sub(r'(?<=[#\s])-(?=[#\s])', ' sub ', s)
    s = re.sub(r'[^\w\s#<>+*/=:^{}\\$]', ' ', s)
    s = s.replace('+', ' add ').replace('*', ' mul ').replace('/', ' div ')
    return tuple(t for t in s.split() if t not in STOP)

def jac(a, b):
    A, B = set(a), set(b)
    return len(A & B) / len(A | B) if (A or B) else 1.0

def leader_cluster(qs):
    groups = defaultdict(list)
    for q in qs:
        groups[toks(q.get("stem", "")) or ("<e>",)].append(q)
    tmpls = sorted(groups.keys(), key=lambda s: (-len(groups[s]), s))
    leaders, assign = [], {}
    for s in tmpls:
        best, bestj = None, TH
        for li, lead in enumerate(leaders):
            j = jac(s, lead)
            if j >= bestj: best, bestj = li, j
        if best is None:
            leaders.append(s); assign[s] = len(leaders) - 1
        else:
            assign[s] = best
    cl = defaultdict(list)
    for s in tmpls: cl[assign[s]].extend(groups[s])
    return cl

def difficulty(q):
    for k in ("irt_b", "difficulty_score"):
        v = q.get(k)
        if isinstance(v, (int, float)): return float(v)
    return 0.0

def scope_of(f):
    b = os.path.basename(f)
    if b[0] == "L" and b[1].isdigit(): return b[:2]
    p = f.replace(ROOT, "").strip("/").split("/")   # curriculum/board/gradeN/...
    return f"{p[1]}-{p[2]}"

SK = {"skill_id", "skill_label", "skill_size", "skill_rank", "is_skill_original",
      "skill_seq", "skill_difficulty"}
def corehash(q):
    return hashlib.md5(json.dumps({k: v for k, v in q.items() if k not in SK},
                                  sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def main():
    index, serial, bad, total = {}, defaultdict(int), 0, 0
    per = defaultdict(lambda: {"q": 0, "sk": 0})
    for f in FILES:
        scope = scope_of(f)
        data = json.load(open(f))
        qs = data.get("questions", data if isinstance(data, list) else [])
        before = {q["id"]: corehash(q) for q in qs}
        for q in qs:                                   # idempotent strip
            for k in list(q):
                if k in SK: q.pop(k, None)
        file_clusters = []
        for ci, members in sorted(leader_cluster(qs).items(),
                                  key=lambda kv: min(x.get("id", "") for x in kv[1])):
            serial[scope] += 1
            sid = f"SK-{scope.upper()}-{serial[scope]:04d}"
            ms = sorted(members, key=lambda q: (difficulty(q), q.get("id", "")))
            label = min((m.get("stem", "") for m in members if m.get("stem")), key=len, default="")[:90]
            ex = ms[0]["id"]
            for rank, m in enumerate(ms):
                m["skill_id"] = sid; m["skill_size"] = len(members)
                m["skill_rank"] = rank; m["is_skill_original"] = (m["id"] == ex)
            index[sid] = {"label": label, "scope": scope, "topic_file": os.path.basename(f),
                          "size": len(members),
                          "difficulty_range": [round(difficulty(ms[0]), 2), round(difficulty(ms[-1]), 2)],
                          "members": [m["id"] for m in ms]}
            per[scope]["sk"] += 1
            file_clusters.append((sid, ms, difficulty(ms[0])))
        # Difficulty LADDER within this topic: order skills by the skill (parent)
        # question's difficulty; every cluster question inherits the parent's
        # difficulty tag and the same ladder position (skill_seq).
        file_clusters.sort(key=lambda t: (t[2], t[0]))
        for seq, (sid, ms, pdiff) in enumerate(file_clusters):
            index[sid]["skill_seq"] = seq
            for m in ms:
                m["skill_seq"] = seq
                m["skill_difficulty"] = round(pdiff, 3)
        per[scope]["q"] += len(qs); total += len(qs)
        for q in qs:
            if before[q["id"]] != corehash(q): bad += 1
        json.dump(data, open(f, "w"), ensure_ascii=False, indent=2)
    json.dump(index, open(os.path.join(ROOT, "skill_clusters.json"), "w"), ensure_ascii=False, indent=1)
    print(f"tagged {total} questions into {len(index)} concepts | integrity_bad={bad}")
    for L in ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]:
        if L in per: print(f"  {L}: {per[L]['q']:>6} q -> {per[L]['sk']:>5} concepts")
    cur = [k for k in per if "-" in k]
    print(f"  curriculum: {sum(per[k]['q'] for k in cur)} q -> {sum(per[k]['sk'] for k in cur)} concepts")

if __name__ == "__main__":
    main()
