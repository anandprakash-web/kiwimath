#!/usr/bin/env python3
"""
Regenerate Kiwimath DPP olympiad worksheets (g{1-6}_olympiad_batch{1-5}.json).

Source bank : content-live/content-v2/topic-*/  (8,280 QA-verified questions)
Output      : backend/content/olympiad/g{N}_olympiad_batch{B}.json
              (grades 1-6 x 5 batches x 20 worksheets = 100 days/grade, 12 Q each)
              + svg_components/svg_store.json + svg_components/visual_ref_renderer.py

Schema authority:
  - backend/app/api/olympiad.py        (loader: ws["day"], ws["questions"],
        q["id"], q["interaction_mode"], q["topic"], q.get("visual_ref"),
        ws.get("title"/"subtitle"/"dominant_topic"/"difficulty_distribution"))
  - app/lib/models/olympiad_worksheet.dart (Dart non-nullable: id, stem;
        mcq: choices + correct_answer(index); integer: correct_value;
        difficulty_tier in warmup/practice/challenge; hint_ladder Map<String,String>;
        visual_ref must be a JSON object; approach string)

Answers are copied verbatim from the QA-verified source bank.
Deterministic (seeded) — re-runnable, idempotent.
"""
from __future__ import annotations

import glob
import json
import os
import random
import re
import zlib
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BANK = os.path.join(REPO, "content-live", "content-v2")
SEED = 20260612

# ── canonical topic slugs (Flutter _topicConfig keys + 2 extras) ─────────────
TOPIC_NORM = {
    "counting_observation": "counting_observation",
    "arithmetic_missing_numbers": "arithmetic_missing_numbers",
    "patterns_sequences": "patterns_sequences",
    "logic_ordering": "logic_ordering",
    "logic_deduction": "logic_ordering",
    "spatial_reasoning_3d": "spatial_reasoning_3d",
    "spatial_reasoning": "spatial_reasoning_3d",
    "spatial_thinking": "spatial_reasoning_3d",
    "shapes_folding_symmetry": "shapes_folding_symmetry",
    "shapes_geometry": "shapes_folding_symmetry",
    "word_problems_stories": "word_problems_stories",
    "word_problems": "word_problems_stories",
    "number_puzzles_games": "number_puzzles_games",
    "puzzles_games": "number_puzzles_games",
}
TOPIC_DISPLAY = {
    "counting_observation": "Counting & Observation",
    "arithmetic_missing_numbers": "Arithmetic",
    "patterns_sequences": "Patterns & Sequences",
    "logic_ordering": "Logic & Reasoning",
    "spatial_reasoning_3d": "Spatial Reasoning",
    "shapes_folding_symmetry": "Shapes & Symmetry",
    "word_problems_stories": "Word Problems",
    "number_puzzles_games": "Number Puzzles",
}
PILLAR = {
    "counting_observation": "combinatorics",
    "arithmetic_missing_numbers": "number_theory",
    "patterns_sequences": "algebra",
    "logic_ordering": "combinatorics",
    "spatial_reasoning_3d": "geometry",
    "shapes_folding_symmetry": "geometry",
    "word_problems_stories": "number_theory",
    "number_puzzles_games": "number_theory",
}
ALL_TOPICS = list(TOPIC_DISPLAY.keys())
GRADE_LEVEL = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 5}

# Day-rotation of dominant focus. Flutter's worksheet list only recognizes 6
# topic slugs for grouping; spatial/puzzles days are labelled 'mixed' but the
# selection still prefers those topics.
DOM_CYCLE = [
    ("counting_observation", "counting_observation"),
    ("arithmetic_missing_numbers", "arithmetic_missing_numbers"),
    ("patterns_sequences", "patterns_sequences"),
    ("logic_ordering", "logic_ordering"),
    ("shapes_folding_symmetry", "shapes_folding_symmetry"),
    ("word_problems_stories", "word_problems_stories"),
    ("spatial_reasoning_3d", "mixed"),
    ("number_puzzles_games", "mixed"),
]

TITLES = {
    "counting_observation": [
        "Counting Commandos", "Number Ninja", "The Great Count-Off", "Tally Trackers",
        "Count Like a Champ", "Eagle Eye Counters", "The Counting Quest", "Spot & Count Safari",
        "Census of the Jungle", "Counting Carnival", "The Number Detectives", "Count to Victory",
        "One, Two, Breakthrough",
    ],
    "arithmetic_missing_numbers": [
        "Missing Number Mystery", "Arithmetic Avengers", "Operation: Calculate", "The Equation Station",
        "Sum Sleuths", "Math Machine Mayhem", "Number Crunch Time", "The Calculation Caper",
        "Plus-Minus Pioneers", "Digit Dynamos", "Balance the Beam", "Arithmetic Arena",
        "The Missing Piece",
    ],
    "patterns_sequences": [
        "Pattern Detective", "Sequence Sprinters", "The Pattern Path", "Rhythm of Numbers",
        "What Comes Next?", "Pattern Power-Up", "The Repeating Riddle", "Sequence Safari",
        "Pattern Puzzle Parade", "Code of the Sequence", "Loop Masters", "The Growing Pattern",
        "Pattern Trailblazers",
    ],
    "logic_ordering": [
        "Logic Lock", "The Reasoning Room", "Brain Benders", "Order in the Court",
        "Logic Labyrinth", "True or False Trek", "The Deduction Den", "Sort It Out",
        "Clue Crackers", "Mind Maze Mission", "The Logic League", "Think Tank Trials",
        "Who Sits Where?",
    ],
    "shapes_folding_symmetry": [
        "Shape Shifters", "Symmetry Squad", "The Folding Challenge", "Mirror Mirror Math",
        "Geometry Giants", "Shape Detective Agency", "The Symmetry Search", "Polygon Patrol",
        "Fold & Behold", "Shape Safari", "The Geometry Gauntlet", "Cut, Fold, Solve",
        "Angles & Edges",
    ],
    "word_problems_stories": [
        "Story Problem Heroes", "The Word Problem Workshop", "Math Story Time", "Real World Rescue",
        "Tale of Two Numbers", "Adventure in Numbers", "The Problem Solvers Club", "Story Math Sprint",
        "Once Upon a Number", "Everyday Math Quest", "The Great Math Adventure", "Word Wizard Workout",
        "Problems with a Plot",
    ],
    "spatial_reasoning_3d": [
        "3D Vision Quest", "Cube Crusaders", "The Spatial Challenge", "Building Block Brains",
        "View From Above", "Space Cadet Math", "Mental Rotation Station", "The Block Builder",
        "Inside Out Shapes", "Dimension Detectives", "Stack & Solve", "The Hidden Face",
        "Map Makers Mission",
    ],
    "number_puzzles_games": [
        "Puzzle Palace", "Number Game Night", "The Riddle Round", "Brain Teaser Bonanza",
        "Crack the Code", "Puzzle Pirates", "The Number Trap", "Game On, Math!",
        "Mystery Math Box", "The Puzzle Vault", "Tricky Number Tricks", "Mind Games Marathon",
        "The Grand Puzzle Hunt",
    ],
}

CHOICE_REF_WORDS = re.compile(
    r"\b(which|following|option|choose|select|statement|shown|picture|figure|graph|image)\b",
    re.IGNORECASE,
)
INT_RE = re.compile(r"^(0|[1-9]\d{0,5})$")  # no leading zeros: str(int(c)) == c


# ── load bank ────────────────────────────────────────────────────────────────
def load_bank():
    def qlist(d):
        return d if isinstance(d, list) else d.get("questions", [])

    band12, band34, band56 = [], [], []
    for path in sorted(glob.glob(os.path.join(BANK, "topic-*", "*.json"))):
        name = os.path.basename(path)
        with open(path) as f:
            qs = qlist(json.load(f))
        if name.startswith("g56"):
            band56.extend(qs)
        elif name.startswith("grade34"):
            band34.extend(qs)
        else:  # questions.json + data_handling/geometry_measurement/measurement_units
            band12.extend(qs)
    return band12, band34, band56


def pct(values, p):
    vs = sorted(values)
    return vs[min(len(vs) - 1, int(len(vs) * p))]


def build_grade_pools(band12, band34, band56):
    b12 = [q["irt_b"] for q in band12]
    p40, p60 = pct(b12, 0.40), pct(b12, 0.60)
    pools = {
        1: [q for q in band12 if q["irt_b"] <= p60],
        2: [q for q in band12 if q["irt_b"] >= p40],
        3: band34 + [q for q in band12 if q["difficulty_tier"] in ("advanced", "expert", "olympiad")],
        4: band34 + [q for q in band56 if q["difficulty_tier"] == "easy"],
        5: [q for q in band56 if q["difficulty_tier"] in ("easy", "medium", "hard")],
        6: [q for q in band56 if q["difficulty_tier"] in ("medium", "hard", "olympiad")],
    }
    return pools


# ── question transform ───────────────────────────────────────────────────────
def build_approach(q):
    ce = (q.get("diagnostics") or {}).get("correct_explanation") or ""
    l2 = (q.get("hint") or {}).get("level_2") or ""
    core = (ce or l2).strip()
    core = re.sub(r"^Here's the solution:\s*", "", core)
    if not core:
        core = " ".join(q.get("solution_steps") or []).strip()
    ans = str(q["choices"][q["correct_answer"]])
    if not core.lower().startswith("analysis"):
        core = "Analysis: " + core
    return f"{core}\nAnswer: {ans}."


def transform(q, tier, number, svg_store):
    topic = TOPIC_NORM.get(q["topic"], q["topic"])
    choices = [str(c) for c in q["choices"]]
    ca = int(q["correct_answer"])
    stem = q["stem"]

    mode = "integer" if (
        all(INT_RE.match(c) for c in choices)
        and not CHOICE_REF_WORDS.search(stem)
        and not q.get("visual_svg")
        and zlib.crc32(q["id"].encode()) % 4 == 0
    ) else "mcq"

    hint = q.get("hint") or {}
    ladder = {}
    for i, key in enumerate(("level_0", "level_1", "level_2"), start=1):
        if hint.get(key):
            ladder[str(i)] = str(hint[key])

    out = {
        "id": q["id"],
        "stem": stem,
        "interaction_mode": mode,
        "topic": topic,
        "difficulty_tier": tier,            # warmup | practice | challenge
        "question_number": number,
        "pillar": PILLAR.get(topic, "number_theory"),
        "choices": choices,
        "correct_answer": ca,               # verbatim from QA-verified source
        "approach": build_approach(q),
        "hint_ladder": ladder,
    }
    if mode == "integer":
        out["correct_value"] = int(choices[ca])
    sol = (q.get("hint") or {}).get("level_2") or (q.get("diagnostics") or {}).get("correct_explanation")
    if sol:
        out["model_solution"] = str(sol)
    if q.get("visual_svg"):
        svg_store[q["id"]] = q["visual_svg"]
        out["visual_ref"] = {"component": "stored_svg", "key": q["id"]}
        out["visual_alt"] = q.get("visual_alt") or TOPIC_DISPLAY.get(topic, topic)
    return out


# ── worksheet assembly ───────────────────────────────────────────────────────
def make_queues(pool, rng):
    """Sort grade pool by irt_b, split into relative tiers, group by topic."""
    pool = sorted(pool, key=lambda q: (q["irt_b"], q["id"]))
    n = len(pool)
    cut1, cut2 = int(n * 0.40), int(n * 0.75)
    buckets = {"warmup": pool[:cut1], "practice": pool[cut1:cut2], "challenge": pool[cut2:]}
    queues = {}
    for tier, qs in buckets.items():
        by_topic = defaultdict(list)
        for q in qs:
            by_topic[TOPIC_NORM.get(q["topic"], q["topic"])].append(q)
        for lst in by_topic.values():
            rng.shuffle(lst)
        queues[tier] = by_topic
    return queues


def pop_question(queues, tier, topic):
    """Pop a question for (tier, topic) with graceful fallback."""
    order = [tier] + [t for t in ("warmup", "practice", "challenge") if t != tier]
    for t in order:
        if queues[t].get(topic):
            return queues[t][topic].pop(), t
        # same tier, any topic (largest remaining queue keeps balance)
        candidates = [(len(v), k) for k, v in queues[t].items() if v]
        if candidates:
            _, k = max(candidates)
            return queues[t][k].pop(), t
    raise RuntimeError("grade pool exhausted")


def build_grade(grade, pool, rng):
    queues = make_queues(pool, rng)
    title_used = Counter()
    worksheets = []
    other_rot = 0

    for day in range(1, 101):
        focus, dom_label = DOM_CYCLE[(day - 1) % 8]
        others = [t for t in ALL_TOPICS if t != focus]

        # slot plan: (tier, topic) — 4 warmup / 5 practice / 3 challenge,
        # dominant topic gets 4 slots, the rest rotate across other topics.
        slots = [("warmup", focus), ("practice", focus), ("practice", focus), ("challenge", focus)]
        fill = [("warmup", None)] * 3 + [("practice", None)] * 3 + [("challenge", None)] * 2
        for i, (tier, _) in enumerate(fill):
            slots.append((tier, others[(other_rot + i) % len(others)]))
        other_rot += len(fill)

        picked, seen = [], set()
        for tier, topic in slots:
            q, actual_tier = pop_question(queues, tier, topic)
            while q["id"] in seen:  # safety: pools are no-replacement, can't happen
                q, actual_tier = pop_question(queues, tier, topic)
            seen.add(q["id"])
            picked.append((actual_tier, q))

        tier_rank = {"warmup": 0, "practice": 1, "challenge": 2}
        picked.sort(key=lambda p: (tier_rank[p[0]], p[1]["irt_b"]))

        svg_store = SVG_STORE
        questions = [transform(q, tier, i + 1, svg_store) for i, (tier, q) in enumerate(picked)]

        dist = Counter(qq["difficulty_tier"] for qq in questions)
        topic_counts = Counter(qq["topic"] for qq in questions)
        top3 = [TOPIC_DISPLAY.get(t, t.title()) for t, _ in topic_counts.most_common(3)]

        base_titles = TITLES[focus]
        title = base_titles[title_used[focus] % len(base_titles)]
        rep = title_used[focus] // len(base_titles)
        if rep:
            title = f"{title} {rep + 1}"
        title_used[focus] += 1

        worksheets.append({
            "grade": grade,
            "day": day,
            "title": title,
            "subtitle": " • ".join(top3),
            "dominant_topic": dom_label,
            "difficulty_distribution": {
                "warmup": dist.get("warmup", 0),
                "practice": dist.get("practice", 0),
                "challenge": dist.get("challenge", 0),
            },
            "questions": questions,
        })
    return worksheets


RENDERER_SRC = '''"""SVG renderer for olympiad visual_ref objects.

Imported by backend/app/api/olympiad.py (this directory is added to sys.path).
Resolves {"component": "stored_svg", "key": <question_id>} against the
sidecar svg_store.json (inline SVGs copied from the QA-verified v2 bank).
"""
import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
_store = None


def _load():
    global _store
    if _store is None:
        path = os.path.join(_DIR, "svg_store.json")
        try:
            with open(path) as f:
                _store = json.load(f)
        except OSError:
            _store = {}
    return _store


def render_visual_ref(ref):
    if not isinstance(ref, dict):
        return None
    if ref.get("component") == "stored_svg":
        return _load().get(ref.get("key"))
    if isinstance(ref.get("svg"), str):
        return ref["svg"]
    return None
'''

SVG_STORE = {}


def main():
    band12, band34, band56 = load_bank()
    print(f"bank: g1-2={len(band12)}  g3-4={len(band34)}  g5-6={len(band56)}  "
          f"total={len(band12) + len(band34) + len(band56)}")

    pools = build_grade_pools(band12, band34, band56)
    stats = {}
    for grade in range(1, 7):
        rng = random.Random(SEED + grade)
        pool = pools[grade]
        print(f"G{grade}: pool={len(pool)}")
        worksheets = build_grade(grade, pool, rng)

        used = [q["id"] for ws in worksheets for q in ws["questions"]]
        modes = Counter(q["interaction_mode"] for ws in worksheets for q in ws["questions"])
        stats[grade] = {
            "pool": len(pool),
            "used": len(used),
            "unique": len(set(used)),
            "reused": len(used) - len(set(used)),
            "modes": dict(modes),
            "with_visual": sum(1 for ws in worksheets for q in ws["questions"] if q.get("visual_ref")),
        }

        for batch in range(1, 6):
            chunk = worksheets[(batch - 1) * 20: batch * 20]
            out_path = os.path.join(HERE, f"g{grade}_olympiad_batch{batch}.json")
            with open(out_path, "w") as f:
                json.dump(chunk, f, ensure_ascii=False, indent=1)

    svg_dir = os.path.join(HERE, "svg_components")
    os.makedirs(svg_dir, exist_ok=True)
    with open(os.path.join(svg_dir, "svg_store.json"), "w") as f:
        json.dump(SVG_STORE, f, ensure_ascii=False)
    with open(os.path.join(svg_dir, "visual_ref_renderer.py"), "w") as f:
        f.write(RENDERER_SRC)

    print(f"\nsvg_store: {len(SVG_STORE)} SVGs")
    for g, s in stats.items():
        print(f"G{g}: used={s['used']} unique={s['unique']} reused={s['reused']} "
              f"modes={s['modes']} visuals={s['with_visual']}")


if __name__ == "__main__":
    main()
