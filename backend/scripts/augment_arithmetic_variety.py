"""Generate a small set of stem-variety arithmetic questions for G3-4.

The existing content-v2/topic-2-arithmetic G3-4 corpus has ~80% of stems
matching the template "What is N + M?" — the quality report flagged it.
This script generates ~120 questions that frame the same arithmetic in
varied real-world contexts (money, time, measurement, comparisons, mental
math tricks, missing-number puzzles), and writes them to
`content-v2/topic-2-arithmetic/grade34_variety_questions.json`.

The content_store_v2 loader already auto-discovers any `*questions*.json`
file in each topic folder, so the file is picked up at startup with no
config changes.

Usage:
    python3 backend/scripts/augment_arithmetic_variety.py \\
        --content-dir content-v2 --count 120 --seed 4729

Run idempotently: re-running with the same seed reproduces the same set.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Callable


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

NAMES = [
    "Aarav", "Diya", "Kabir", "Riya", "Vihaan", "Saanvi", "Arjun", "Anika",
    "Yara", "Zayn", "Mira", "Theo", "Sage", "Iris", "Cyrus", "Amara",
]

ITEMS_COUNTABLE = ["marbles", "stickers", "buttons", "shells", "rocks", "beads"]
SNACKS = ["cookies", "biscuits", "candies", "chips", "raisins"]


def _names(rng: random.Random, n: int = 1) -> list[str]:
    return rng.sample(NAMES, n)


def _kid_friendly_diff(diff: int) -> str:
    if diff <= 130:
        return "advanced"
    if diff <= 170:
        return "expert"
    return "olympiad"


# ---------------------------------------------------------------------------
# Generators — each returns a (stem, choices, correct_index, diagnostics, tags)
# tuple keyed off `rng` so reruns with same seed reproduce.
# ---------------------------------------------------------------------------


def _gen_money(rng, diff):
    name = _names(rng)[0]
    paid = rng.randint(50, 500)
    item = rng.choice(["a comic book", "a soft toy", "stickers", "a pencil case", "a board game"])
    cost = rng.randint(10, paid - 5)
    change = paid - cost
    distractors = [change + rng.choice([-3, -2, 2, 3, 5]) for _ in range(3)]
    distractors = [d for d in distractors if d != change and d > 0][:3]
    while len(distractors) < 3:
        distractors.append(change + rng.randint(4, 9))
    choices = [str(change)] + [str(d) for d in distractors]
    rng.shuffle(choices)
    correct_index = choices.index(str(change))
    stem = f"{name} pays ₹{paid} for {item} that costs ₹{cost}. How much change does {name} get back?"
    return stem, choices, correct_index, {
        "wrong_subtract_order": "Always subtract the cost from the money paid.",
        "off_by_one": "Line up the digits and subtract carefully.",
    }, ["money", "subtraction", "context"]


def _gen_time(rng, diff):
    h = rng.randint(1, 11)
    m = rng.choice([0, 15, 30, 45])
    add_min = rng.choice([15, 30, 45, 60, 75, 90, 105, 120])
    total_m = h * 60 + m + add_min
    final_h = (total_m // 60) % 12 or 12
    final_m = total_m % 60
    answer = f"{final_h}:{final_m:02d}"
    distractors = []
    for offset in [-15, 15, -30, 30, -60, 60]:
        t = h * 60 + m + add_min + offset
        h2 = (t // 60) % 12 or 12
        m2 = t % 60
        opt = f"{h2}:{m2:02d}"
        if opt != answer and opt not in distractors:
            distractors.append(opt)
        if len(distractors) >= 3:
            break
    choices = [answer] + distractors[:3]
    rng.shuffle(choices)
    correct_index = choices.index(answer)
    stem = f"It is {h}:{m:02d}. What time will it be after {add_min} minutes?"
    return stem, choices, correct_index, {
        "minutes_overflow": "60 minutes makes a new hour. Carry the extra into the hour.",
        "wrong_direction": "We are adding minutes — so move forward.",
    }, ["time", "addition", "carrying"]


def _gen_compare(rng, diff):
    a = rng.randint(50, 999)
    b = rng.randint(50, 999)
    while b == a:
        b = rng.randint(50, 999)
    diff_val = abs(a - b)
    bigger = max(a, b)
    smaller = min(a, b)
    distractors = sorted({diff_val + rng.choice([-1, 1, -10, 10, -2, 2]) for _ in range(8)})
    distractors = [str(d) for d in distractors if d != diff_val and d > 0][:3]
    choices = [str(diff_val)] + distractors
    rng.shuffle(choices)
    correct_index = choices.index(str(diff_val))
    stem = (f"On Monday {bigger} children visited the park. On Tuesday only "
            f"{smaller} children visited. How many more children came on Monday "
            f"than on Tuesday?")
    return stem, choices, correct_index, {
        "wrong_op": "'How many more' means subtract — bigger minus smaller.",
        "swapped": "Be careful which day had more.",
    }, ["compare", "subtraction", "context"]


def _gen_mental_math(rng, diff):
    """Frame addition as a 'trick' — round-and-adjust, doubles, etc."""
    a = rng.choice([19, 29, 39, 49, 59, 69, 79, 89, 98, 198, 297])
    b = rng.randint(13, 84)
    answer = a + b
    near10 = a + 1 if a % 10 == 9 else a + (10 - a % 10)
    distractors = [answer + rng.choice([-2, -1, 1, 2, 9, 10]) for _ in range(6)]
    distractors = list({d for d in distractors if d != answer and d > 0})[:3]
    choices = [str(answer)] + [str(d) for d in distractors]
    rng.shuffle(choices)
    correct_index = choices.index(str(answer))
    stem = (f"Use a smart trick: {a} is close to {near10}. "
            f"What is {a} + {b}?")
    return stem, choices, correct_index, {
        "round_only": "After rounding up to add, you must subtract the amount you added.",
        "off_by_one": "If you used +1 to round, take 1 back at the end.",
    }, ["mental_math", "addition", "rounding_trick"]


def _gen_missing(rng, diff):
    target = rng.randint(40, 250)
    a = rng.randint(10, target - 5)
    answer = target - a
    op = "+"
    if rng.random() < 0.4:
        op = "-"
        big = rng.randint(target + 5, target + 200)
        a = big
        answer = a - target
    distractors = sorted({answer + rng.choice([-3, -2, 2, 3, 5, 10]) for _ in range(8)})
    distractors = [d for d in distractors if d != answer and d > 0][:3]
    choices = [str(answer)] + [str(d) for d in distractors]
    rng.shuffle(choices)
    correct_index = choices.index(str(answer))
    if op == "+":
        stem = f"Fill in the missing number: {a} + ___ = {target}"
    else:
        stem = f"Fill in the missing number: {a} - ___ = {target}"
    return stem, choices, correct_index, {
        "guessed_subtract": "Try plugging your answer back in to check.",
    }, ["missing_number", "inverse", op]


def _gen_doubling(rng, diff):
    """Doubling / halving framing."""
    if rng.random() < 0.5:
        a = rng.randint(15, 95)
        answer = a * 2
        stem = f"What is double {a}?"
        tag = "double"
    else:
        a = rng.randint(8, 60) * 2
        answer = a // 2
        stem = f"What is half of {a}?"
        tag = "half"
    distractors = sorted({answer + rng.choice([-3, -1, 1, 2, 5]) for _ in range(8)})
    distractors = [str(d) for d in distractors if d != answer and d > 0][:3]
    choices = [str(answer)] + distractors
    rng.shuffle(choices)
    correct_index = choices.index(str(answer))
    return stem, choices, correct_index, {
        "wrong_op": "Double = ×2. Half = ÷2.",
    }, ["doubling", tag]


def _gen_ratio_share(rng, diff):
    parts = rng.choice([2, 3, 4, 5])
    each = rng.randint(4, 25)
    total = parts * each
    answer = each
    name = _names(rng)[0]
    distractors = list({each + rng.choice([-2, -1, 1, 2, 3]) for _ in range(8)})
    distractors = [d for d in distractors if d != answer and d > 0][:3]
    choices = [str(answer)] + [str(d) for d in distractors]
    rng.shuffle(choices)
    correct_index = choices.index(str(answer))
    item = rng.choice(SNACKS + ITEMS_COUNTABLE)
    stem = (f"{name} shares {total} {item} equally among {parts} friends. "
            f"How many {item} does each friend get?")
    return stem, choices, correct_index, {
        "wrong_op": "Sharing equally means dividing.",
    }, ["division", "share", "context"]


GENERATORS: list[Callable] = [
    _gen_money,
    _gen_time,
    _gen_compare,
    _gen_mental_math,
    _gen_missing,
    _gen_doubling,
    _gen_ratio_share,
]


# ---------------------------------------------------------------------------
# Build full question records in the same schema as existing G3-4 questions.
# ---------------------------------------------------------------------------


def _build_record(qid: str, diff: int, gen_fn: Callable, rng: random.Random) -> dict:
    stem, choices, correct_idx, diagnostics, tags = gen_fn(rng, diff)
    return {
        "id": qid,
        "stem": stem,
        "choices": choices,
        "correct_answer": correct_idx,
        "difficulty_tier": _kid_friendly_diff(diff),
        "difficulty_score": diff,
        "visual_svg": None,
        "visual_alt": None,
        "diagnostics": diagnostics,
        "tags": tags + ["g3-4", "variety_pack"],
        "topic": "arithmetic_missing_numbers",
        "topic_name": "Arithmetic & Missing Numbers",
        "original_stem": stem,
        "hint": {
            "level_0": "Read the problem one more time — what is being asked?",
            "level_1": "What information do you have? What do you need to find?",
            "level_2": "Pick the right operation: add, subtract, multiply, or divide?",
            "level_3": "Write the numbers down and line them up by place value.",
            "level_4": "Do the operation step by step — don't try to do it all in your head.",
            "level_5": "Check your answer by plugging it back into the problem.",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--content-dir", default="content-v2")
    ap.add_argument("--count", type=int, default=120,
                    help="Number of variety questions to generate.")
    ap.add_argument("--seed", type=int, default=4729,
                    help="Random seed for reproducibility.")
    ap.add_argument("--id-start", type=int, default=901,
                    help="Starting numeric ID for question_id (Tx-NNNN).")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    out_path = Path(args.content_dir) / "topic-2-arithmetic" / "grade34_variety_questions.json"

    questions: list[dict] = []
    # Spread across difficulty 105..195 evenly, round-robin generators.
    for i in range(args.count):
        diff = 105 + (i * 90 // max(args.count - 1, 1))
        gen_fn = GENERATORS[i % len(GENERATORS)]
        qid = f"T2-{args.id_start + i:04d}"
        questions.append(_build_record(qid, diff, gen_fn, rng))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"questions": questions}, indent=2) + "\n")
    print(f"Wrote {out_path}")
    print(f"  count: {len(questions)}, difficulty: {questions[0]['difficulty_score']}-{questions[-1]['difficulty_score']}")
    print(f"  generator mix: {[g.__name__ for g in GENERATORS]}")


if __name__ == "__main__":
    main()
