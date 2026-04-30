"""Generator for Grade 3-4 (difficulty 101-200) Kiwimath questions.

Adds 300 new questions per topic to the existing content-v2 JSON files.
IDs continue from T*-601 to T*-900 to coexist with the Grade 1-2 corpus.

Each question has:
  - mathematically correct stem + 4 choices + correct_answer index
  - a difficulty_score in [101, 200] and difficulty_tier in
    {"medium", "hard", "advanced", "expert"}
  - per-distractor diagnostics
  - a 6-level Socratic hint ladder

Run:
    python content_tools/gen_g34_questions.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent / "content-v2"

# Each topic spec: (topic_dir, topic_id, topic_name, generator_fn, topic_num)
# Generator returns a list of (stem, correct_answer, choices, hint_ladder, tag)
# tuples.
TOPICS = [
    ("topic-1-counting",      "counting_observation",       "Counting & Observation",       1),
    ("topic-2-arithmetic",    "arithmetic_missing_numbers", "Arithmetic & Missing Numbers", 2),
    ("topic-3-patterns",      "patterns_sequences",         "Patterns & Sequences",         3),
    ("topic-4-logic",         "logic_ordering",             "Logic & Ordering",             4),
    ("topic-5-spatial",       "spatial_reasoning_3d",       "Spatial Reasoning 3D",         5),
    ("topic-6-shapes",        "shapes_folding_symmetry",    "Shapes Folding Symmetry",      6),
    ("topic-7-word-problems", "word_problems_stories",      "Word Problems & Stories",      7),
    ("topic-8-puzzles",       "number_puzzles_games",       "Number Puzzles & Games",       8),
]

QUESTIONS_PER_TOPIC = 300

# Names used in word problems
NAMES = [
    "Maya", "Aarav", "Zoe", "Kai", "Priya", "Diego", "Aria", "Leo",
    "Nora", "Ravi", "Sara", "Theo", "Lila", "Ben", "Mira", "Jay",
]


def diff_tier(score: int) -> str:
    """Tier label for a difficulty in [101, 200]."""
    if score < 130:
        return "medium"
    if score < 160:
        return "hard"
    if score < 185:
        return "advanced"
    return "expert"


def shuffle_choices(correct_value, distractors: List, rng: random.Random) -> Tuple[List[str], int]:
    """Return (choices_as_strings, correct_index) with the correct answer
    placed at a random position among the distractors."""
    options = list(distractors) + [correct_value]
    rng.shuffle(options)
    correct_idx = options.index(correct_value)
    return [str(o) for o in options], correct_idx


def make_generic_diagnostics(correct_idx: int, choices: List[str]) -> Dict[str, str]:
    msgs = [
        "Almost! Recheck your steps.",
        "Close, but try a different approach.",
        "Watch out for off-by-one slips here.",
        "Re-read the question — what is it really asking?",
    ]
    out: Dict[str, str] = {}
    for i, _ in enumerate(choices):
        if i == correct_idx:
            out[str(i)] = "Correct! Well done!"
        else:
            out[str(i)] = msgs[i % len(msgs)]
    return out


def hint_ladder(generic_topic_hint: str) -> Dict[str, str]:
    """Default 6-level Socratic hint ladder.

    Topics override level_5 with their concept tip.
    """
    return {
        "level_0": "Take a breath — what does the question ask?",
        "level_1": "What's known? What's unknown?",
        "level_2": "Can you break it into smaller steps?",
        "level_3": "Try with simpler numbers first, then scale up.",
        "level_4": "Write down what you have on each side.",
        "level_5": generic_topic_hint,
    }


# ---------------------------------------------------------------------------
# Topic generators
# ---------------------------------------------------------------------------

def gen_counting(rng: random.Random, n: int) -> List[Dict[str, Any]]:
    """T1 — Skip counting, money counting, time counting at G3-4 level."""
    out = []
    for _ in range(n):
        flavor = rng.randint(0, 3)
        if flavor == 0:
            # Skip counting by 5/10/100
            step = rng.choice([5, 10, 25, 50, 100])
            start = rng.randint(1, 10) * step
            count = rng.randint(4, 8)
            seq = [start + i * step for i in range(count)]
            stem = (
                f"Skip count by {step}s starting from {seq[0]}. "
                f"What is the {ordinal(count)} number? ({', '.join(str(s) for s in seq[:count-1])}, ?)"
            )
            ans = seq[-1]
            distractors = [ans - step, ans + step, ans - 1]
            tag = "skip-counting"
        elif flavor == 1:
            # Money counting
            n_qtr = rng.randint(0, 4)
            n_dime = rng.randint(0, 5)
            n_nick = rng.randint(0, 5)
            n_pen = rng.randint(0, 9)
            cents = 25 * n_qtr + 10 * n_dime + 5 * n_nick + 1 * n_pen
            stem = (
                f"You have {n_qtr} quarter(s), {n_dime} dime(s), "
                f"{n_nick} nickel(s), and {n_pen} penny/pennies. "
                f"How many cents in total?"
            )
            ans = cents
            distractors = [
                cents + 5,
                max(1, cents - 5),
                cents + 10,
            ]
            tag = "money"
        elif flavor == 2:
            # Time counting (minutes)
            start_h = rng.randint(1, 11)
            start_m = rng.choice([0, 15, 30, 45])
            elapsed = rng.choice([15, 30, 45, 60, 90, 120])
            total_m = start_h * 60 + start_m + elapsed
            ans_h = (total_m // 60) % 12 or 12
            ans_m = total_m % 60
            stem = (
                f"It is {start_h}:{start_m:02d}. "
                f"What time will it be in {elapsed} minutes?"
            )
            ans = f"{ans_h}:{ans_m:02d}"
            d_h = (ans_h % 12) + 1
            d_m = (ans_m + 15) % 60
            distractors = [
                f"{d_h}:{ans_m:02d}",
                f"{ans_h}:{d_m:02d}",
                f"{(ans_h + 11) % 12 or 12}:{ans_m:02d}",
            ]
            tag = "time"
        else:
            # Counting in groups
            groups = rng.randint(3, 9)
            per = rng.randint(8, 25)
            total = groups * per
            stem = (
                f"Captain Kiwi sees {groups} groups, each with {per} stickers. "
                f"How many stickers in all?"
            )
            ans = total
            distractors = [
                total + per,
                max(1, total - per),
                groups + per,
            ]
            tag = "groups"
        out.append({
            "stem": stem, "correct": ans, "distractors": distractors,
            "ladder_tip": "Skip-counting tip: keep a tally as you go.",
            "tag": tag,
        })
    return out


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def gen_arithmetic(rng: random.Random, n: int) -> List[Dict[str, Any]]:
    """T2 — Multi-digit add/subtract, multiplication, division."""
    out = []
    for _ in range(n):
        kind = rng.randint(0, 5)
        if kind == 0:
            a = rng.randint(100, 999)
            b = rng.randint(100, 999)
            ans = a + b
            stem = f"What is {a} + {b}?"
            distractors = [ans - 10, ans + 10, ans - 100]
            tag = "add-3digit"
            tip = "Line up by ones, tens, hundreds. Carry when you cross 10."
        elif kind == 1:
            a = rng.randint(500, 999)
            b = rng.randint(100, a - 1)
            ans = a - b
            stem = f"What is {a} − {b}?"
            distractors = [ans - 10, ans + 10, abs(b - a)]
            tag = "sub-3digit"
            tip = "Borrow from the next column when the top digit is smaller."
        elif kind == 2:
            a = rng.randint(2, 12)
            b = rng.randint(2, 12)
            ans = a * b
            stem = f"What is {a} × {b}?"
            distractors = [ans + a, ans - a, a + b]
            tag = "mult-table"
            tip = "Times tables — practise daily. Use arrays if stuck."
        elif kind == 3:
            b = rng.randint(2, 12)
            ans = rng.randint(2, 12)
            a = ans * b
            stem = f"What is {a} ÷ {b}?"
            distractors = [ans + 1, max(1, ans - 1), b]
            tag = "div-table"
            tip = "Division is the reverse of multiplication."
        elif kind == 4:
            # Missing number
            a = rng.randint(20, 99)
            b = rng.randint(20, 99)
            ans = b
            stem = f"Fill the blank: {a} + ___ = {a + b}"
            distractors = [b - 1, b + 1, a]
            tag = "missing-number"
            tip = "Subtract the known from the total to find the missing part."
        else:
            # Multi-step
            a = rng.randint(2, 9)
            b = rng.randint(2, 9)
            c = rng.randint(2, 30)
            ans = a * b + c
            stem = f"What is {a} × {b} + {c}?"
            distractors = [a * b - c, ans - 1, ans + b]
            tag = "multi-step"
            tip = "Multiply first (PEMDAS), then add."
        out.append({
            "stem": stem, "correct": ans, "distractors": distractors,
            "ladder_tip": tip, "tag": tag,
        })
    return out


def gen_patterns(rng: random.Random, n: int) -> List[Dict[str, Any]]:
    """T3 — Numeric and rule-based sequences."""
    out = []
    for _ in range(n):
        kind = rng.randint(0, 3)
        if kind == 0:
            # Arithmetic progression
            a = rng.randint(2, 30)
            d = rng.randint(2, 12)
            seq = [a + i * d for i in range(5)]
            ans = seq[-1] + d
            stem = (
                f"What number comes next? "
                f"{seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}, {seq[4]}, ___"
            )
            distractors = [ans + d, ans - d, seq[-1] + d + 1]
            tag = "ap"
            tip = "Look at the gap between numbers — does it stay the same?"
        elif kind == 1:
            # Geometric (small ratios so kids can manage)
            a = rng.randint(1, 5)
            r = rng.choice([2, 3])
            seq = [a * (r ** i) for i in range(4)]
            ans = seq[-1] * r
            stem = (
                f"What number comes next? "
                f"{seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}, ___"
            )
            distractors = [seq[-1] + r, ans + r, ans // r]
            tag = "gp"
            tip = "Try multiplying by the same number each time."
        elif kind == 2:
            # Square numbers
            i = rng.randint(2, 9)
            seq = [k * k for k in range(1, i + 1)]
            ans = (i + 1) ** 2
            stem = (
                f"Square numbers: {', '.join(str(s) for s in seq)}, ___"
            )
            distractors = [ans + 1, ans - 1, seq[-1] + i]
            tag = "squares"
            tip = "n × n. Try a multiplication table."
        else:
            # Custom rule: add then double
            a = rng.randint(1, 9)
            seq = [a]
            for _ in range(4):
                seq.append((seq[-1] + 1) * 2)
            ans = (seq[-1] + 1) * 2
            stem = (
                "Rule: add 1, then double. "
                f"{seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}, {seq[4]}, ___"
            )
            distractors = [seq[-1] * 2, seq[-1] + 1, ans + 1]
            tag = "rule"
            tip = "Apply the rule one step at a time."
        out.append({
            "stem": stem, "correct": ans, "distractors": distractors,
            "ladder_tip": tip, "tag": tag,
        })
    return out


def gen_logic(rng: random.Random, n: int) -> List[Dict[str, Any]]:
    """T4 — Ordering, deductive logic at G3-4 level."""
    out = []
    for _ in range(n):
        kind = rng.randint(0, 2)
        if kind == 0:
            # Smallest/largest of 4 numbers
            nums = rng.sample(range(100, 999), 4)
            want_largest = rng.random() < 0.5
            ans = max(nums) if want_largest else min(nums)
            stem = (
                f"Which is the {'largest' if want_largest else 'smallest'} number? "
                f"{nums[0]}, {nums[1]}, {nums[2]}, {nums[3]}"
            )
            distractors = [n for n in nums if n != ans][:3]
            tag = "compare"
            tip = "Compare hundreds first, then tens, then ones."
        elif kind == 1:
            # Three kids age comparison
            names = rng.sample(NAMES, 3)
            ages = sorted(rng.sample(range(7, 14), 3))
            order = list(zip(names, ages))
            rng.shuffle(order)
            n1, n2, n3 = order
            stem = (
                f"{n1[0]} is {n1[1]} years old. {n2[0]} is {n2[1]}. {n3[0]} is {n3[1]}. "
                f"Who is the youngest?"
            )
            ans = min(order, key=lambda x: x[1])[0]
            distractors = [n[0] for n in order if n[0] != ans]
            tag = "deductive-age"
            tip = "Smallest number = youngest."
        else:
            # Order coins/items by quantity
            items = rng.sample(["apples", "pears", "kiwis", "mangoes", "limes"], 4)
            counts = rng.sample(range(20, 60), 4)
            pairs = list(zip(items, counts))
            ans = max(pairs, key=lambda x: x[1])[0]
            stem = (
                ", ".join(f"{n} {it}" for it, n in pairs)
                + ". Which fruit does Captain Kiwi have the MOST of?"
            )
            distractors = [it for it, _ in pairs if it != ans]
            tag = "max-of-list"
            tip = "Look for the biggest count."
        out.append({
            "stem": stem, "correct": ans, "distractors": distractors,
            "ladder_tip": tip, "tag": tag,
        })
    return out


def gen_spatial(rng: random.Random, n: int) -> List[Dict[str, Any]]:
    """T5 — Volume, 3D counting, simple nets."""
    out = []
    for _ in range(n):
        kind = rng.randint(0, 2)
        if kind == 0:
            # Cube cuboid volume
            l = rng.randint(2, 9)
            w = rng.randint(2, 9)
            h = rng.randint(2, 6)
            ans = l * w * h
            stem = (
                f"A box is {l} cm long, {w} cm wide, and {h} cm tall. "
                f"What is its volume in cubic cm?"
            )
            distractors = [l * w + h, l + w + h, ans - l]
            tag = "volume"
            tip = "Volume = length × width × height."
        elif kind == 1:
            # Counting cubes in a stack
            l = rng.randint(2, 5)
            w = rng.randint(2, 5)
            h = rng.randint(2, 5)
            ans = l * w * h
            stem = (
                f"A solid is built from {l} × {w} cubes on the bottom, "
                f"stacked {h} layers high. How many cubes in total?"
            )
            distractors = [l * w + h, l * w * (h - 1), ans + l]
            tag = "cube-stack"
            tip = "Bottom layer × number of layers."
        else:
            # Faces / edges / vertices on cube
            stem = "How many edges does a cube have?"
            ans = 12
            distractors = [6, 8, 10]
            tag = "cube-edges"
            tip = "Cube: 6 faces, 12 edges, 8 vertices."
        out.append({
            "stem": stem, "correct": ans, "distractors": distractors,
            "ladder_tip": tip, "tag": tag,
        })
    return out


def gen_shapes(rng: random.Random, n: int) -> List[Dict[str, Any]]:
    """T6 — Perimeter, area, symmetry at G3-4."""
    out = []
    for _ in range(n):
        kind = rng.randint(0, 3)
        if kind == 0:
            # Perimeter rectangle
            l = rng.randint(3, 25)
            w = rng.randint(3, 25)
            ans = 2 * (l + w)
            stem = f"A rectangle is {l} cm by {w} cm. What is its perimeter?"
            distractors = [l + w, 2 * l + w, l * w]
            tag = "perimeter-rect"
            tip = "Perimeter = 2 × (length + width)."
        elif kind == 1:
            # Area rectangle
            l = rng.randint(3, 20)
            w = rng.randint(3, 20)
            ans = l * w
            stem = f"A rectangle is {l} cm by {w} cm. What is its area in sq cm?"
            distractors = [2 * (l + w), l + w, ans + l]
            tag = "area-rect"
            tip = "Area = length × width."
        elif kind == 2:
            # Perimeter square
            s = rng.randint(4, 30)
            ans = 4 * s
            stem = f"A square has side {s} cm. What is its perimeter?"
            distractors = [s * s, 2 * s, ans - s]
            tag = "perimeter-square"
            tip = "Perimeter of a square = 4 × side."
        else:
            # Lines of symmetry
            shape = rng.choice([
                ("equilateral triangle", 3),
                ("square", 4),
                ("regular pentagon", 5),
                ("regular hexagon", 6),
                ("rectangle (not a square)", 2),
                ("circle", 0),  # treat as "infinite/many" -> use 0 here for the false answer
            ])
            shape_name, lines = shape
            if shape_name.startswith("circle"):
                stem = "How many lines of symmetry does a NON-square rectangle have?"
                ans = 2
                distractors = [4, 1, 0]
                tag = "lines-of-symmetry"
                tip = "A non-square rectangle has 2 lines of symmetry."
            else:
                stem = f"How many lines of symmetry does an {shape_name} have?"
                ans = lines
                distractors = [lines + 1, max(0, lines - 1), lines * 2]
                tag = "lines-of-symmetry"
                tip = "Regular n-sided polygon has n lines of symmetry."
        out.append({
            "stem": stem, "correct": ans, "distractors": distractors,
            "ladder_tip": tip, "tag": tag,
        })
    return out


def gen_word_problems(rng: random.Random, n: int) -> List[Dict[str, Any]]:
    """T7 — Multi-step word problems."""
    out = []
    for _ in range(n):
        kind = rng.randint(0, 3)
        name = rng.choice(NAMES)
        if kind == 0:
            cookies = rng.randint(20, 120)
            kids = rng.randint(2, 8)
            extra = rng.randint(0, kids - 1)
            ans = (cookies - extra) // kids
            stem = (
                f"{name} has {cookies} cookies. After keeping {extra} for later, "
                f"the rest are shared equally among {kids} friends. "
                f"How many cookies does each friend get?"
            )
            distractors = [ans + 1, max(0, ans - 1), cookies // kids]
            tag = "share"
            tip = "Subtract first, then divide equally."
        elif kind == 1:
            packs = rng.randint(3, 9)
            per = rng.randint(6, 15)
            sold = rng.randint(5, packs * per - 5)
            ans = packs * per - sold
            stem = (
                f"{name} buys {packs} packs of stickers with {per} in each. "
                f"After giving away {sold}, how many are left?"
            )
            distractors = [ans + per, packs * per, abs(sold - per)]
            tag = "multiply-then-subtract"
            tip = "Multiply first, then subtract."
        elif kind == 2:
            big = rng.randint(50, 250)
            spent_a = rng.randint(10, 60)
            spent_b = rng.randint(10, 60)
            ans = big - spent_a - spent_b
            stem = (
                f"{name} starts with ₹{big}. Buys a book for ₹{spent_a}, "
                f"then a snack for ₹{spent_b}. How much money is left?"
            )
            distractors = [big - spent_a, big - spent_b, ans + 10]
            tag = "subtract-twice"
            tip = "Subtract step by step."
        else:
            steps = rng.randint(15, 60)
            day = rng.randint(2, 7)
            ans = steps * day
            stem = (
                f"{name} climbs {steps} steps each day. "
                f"In {day} days, how many steps total?"
            )
            distractors = [steps + day, ans - steps, ans + 1]
            tag = "rate-times-time"
            tip = "Per-day amount × number of days."
        out.append({
            "stem": stem, "correct": ans, "distractors": distractors,
            "ladder_tip": tip, "tag": tag,
        })
    return out


def gen_puzzles(rng: random.Random, n: int) -> List[Dict[str, Any]]:
    """T8 — Magic-square style + odd-one-out + simple algebra puzzles."""
    out = []
    for _ in range(n):
        kind = rng.randint(0, 3)
        if kind == 0:
            # Algebra-style: x + a = b
            a = rng.randint(5, 50)
            x = rng.randint(5, 50)
            b = a + x
            ans = x
            stem = f"Solve for ?: ? + {a} = {b}"
            distractors = [x + 1, x - 1, b - x]
            tag = "linear-eq"
            tip = "Subtract the known number from both sides."
        elif kind == 1:
            # Multiplication puzzle
            a = rng.randint(3, 12)
            x = rng.randint(3, 12)
            p = a * x
            ans = x
            stem = f"Solve for ?: {a} × ? = {p}"
            distractors = [x + 1, x - 1, a]
            tag = "linear-eq-mult"
            tip = "Divide both sides by the known number."
        elif kind == 2:
            # Odd one out (number not divisible)
            div = rng.choice([2, 3, 4, 5, 7])
            others = [div * rng.randint(2, 12) for _ in range(3)]
            odd = others[0] + 1
            while odd % div == 0:
                odd += 1
            choices_pool = others + [odd]
            ans = odd
            stem = (
                f"Which number is NOT divisible by {div}? "
                f"{', '.join(str(x) for x in choices_pool)}"
            )
            distractors = others
            tag = "divisibility"
            tip = "Check the remainder when you divide."
        else:
            # Sum to target
            target = rng.randint(20, 80)
            a = rng.randint(5, target - 5)
            b = target - a
            ans = b
            stem = f"What number must be added to {a} to make {target}?"
            distractors = [b + 1, b - 1, a + 1]
            tag = "sum-to-target"
            tip = "Subtract the known from the target."
        out.append({
            "stem": stem, "correct": ans, "distractors": distractors,
            "ladder_tip": tip, "tag": tag,
        })
    return out


GENERATORS: Dict[str, Callable[[random.Random, int], List[Dict[str, Any]]]] = {
    "topic-1-counting":      gen_counting,
    "topic-2-arithmetic":    gen_arithmetic,
    "topic-3-patterns":      gen_patterns,
    "topic-4-logic":         gen_logic,
    "topic-5-spatial":       gen_spatial,
    "topic-6-shapes":        gen_shapes,
    "topic-7-word-problems": gen_word_problems,
    "topic-8-puzzles":       gen_puzzles,
}


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_question(
    qid: str,
    topic_id: str,
    topic_name: str,
    record: Dict[str, Any],
    difficulty_score: int,
    rng: random.Random,
) -> Dict[str, Any]:
    correct = record["correct"]
    distractors = record["distractors"]
    # de-dup distractors and ensure they're distinct from correct
    seen = {str(correct)}
    cleaned: List = []
    for d in distractors:
        if str(d) not in seen:
            cleaned.append(d)
            seen.add(str(d))
        if len(cleaned) == 3:
            break
    # Pad if we lost some — bump by ±1
    while len(cleaned) < 3:
        candidate = (correct if isinstance(correct, int) else 0)
        if isinstance(candidate, int):
            candidate += rng.randint(1, 5) * rng.choice([-1, 1])
        if str(candidate) not in seen:
            cleaned.append(candidate)
            seen.add(str(candidate))

    choices, correct_idx = shuffle_choices(correct, cleaned, rng)
    diagnostics = make_generic_diagnostics(correct_idx, choices)

    return {
        "id": qid,
        "stem": record["stem"],
        "choices": choices,
        "correct_answer": correct_idx,
        "difficulty_tier": diff_tier(difficulty_score),
        "difficulty_score": difficulty_score,
        "visual_svg": None,
        "visual_alt": None,
        "diagnostics": diagnostics,
        "tags": [record.get("tag", "g34"), "grade-3-4"],
        "topic": topic_id,
        "topic_name": topic_name,
        "hint": hint_ladder(record["ladder_tip"]),
    }


def difficulty_for_index(i: int) -> int:
    """Spread 300 questions over difficulty 101-200 (linear)."""
    # Map i in [0, 299] to [101, 200]
    return 101 + int(i / max(1, QUESTIONS_PER_TOPIC - 1) * 99)


def main() -> int:
    if not ROOT.exists():
        print(f"ERROR: content-v2 not found at {ROOT}", file=sys.stderr)
        return 1

    grand_total = 0
    for topic_dir, topic_id, topic_name, topic_num in TOPICS:
        path = ROOT / topic_dir / "questions.json"
        if not path.exists():
            print(f"WARN: {path} missing, skipping")
            continue

        data = json.loads(path.read_text())
        existing = data.get("questions", [])
        # Skip if Grade 3-4 questions already added (check for any difficulty > 100)
        already_g34 = sum(1 for q in existing if q.get("difficulty_score", 0) > 100)
        if already_g34 >= QUESTIONS_PER_TOPIC:
            print(f"  {topic_dir}: already has {already_g34} G3-4 questions, skipping")
            continue

        # Find next sequential ID number
        max_seq = 0
        for q in existing:
            qid = q.get("id", "")
            parts = qid.split("-")
            if len(parts) == 2 and parts[1].isdigit():
                max_seq = max(max_seq, int(parts[1]))

        rng = random.Random(f"g34-{topic_id}")
        gen = GENERATORS[topic_dir]
        records = gen(rng, QUESTIONS_PER_TOPIC)

        new_qs: List[Dict[str, Any]] = []
        for i, rec in enumerate(records):
            seq = max_seq + 1 + i
            qid_num = f"{seq:03d}" if seq < 1000 else f"{seq:04d}"
            qid = f"T{topic_num}-{qid_num}"
            difficulty = difficulty_for_index(i)
            new_qs.append(
                build_question(qid, topic_id, topic_name, rec, difficulty, rng)
            )

        data["questions"] = existing + new_qs
        data["total_questions"] = len(data["questions"])

        # Refresh difficulty_distribution
        dist: Dict[str, int] = {}
        for q in data["questions"]:
            dist[q["difficulty_tier"]] = dist.get(q["difficulty_tier"], 0) + 1
        data["difficulty_distribution"] = dist

        # Pretty-print so diffs stay readable.
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"  {topic_dir}: +{len(new_qs)} G3-4 questions (now {len(data['questions'])})")
        grand_total += len(new_qs)

    print(f"\nDone. Generated {grand_total} new Grade 3-4 questions across "
          f"{len(TOPICS)} topics.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
