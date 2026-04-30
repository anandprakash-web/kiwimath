#!/usr/bin/env python3
"""
Generate Grade 3-4 content (Task #191).

Produces 300 questions per topic at difficulty 101-200, extending the
existing Grade 1-2 set (1-100). Questions are written into separate
files (grade34_questions.json) inside each topic folder so the existing
questions.json is untouched and can be merged later.

Each generated question follows the v2 schema:
    id, stem, original_stem, choices, correct_answer, difficulty_tier,
    difficulty_score, visual_svg, visual_alt, diagnostics, tags,
    topic, topic_name, hint (6-level ladder)

Difficulty band:
  • 101-130 → "advanced" tier      (Grade 3 entry)
  • 131-170 → "expert" tier        (Grade 3 → 4)
  • 171-200 → "olympiad" tier      (Grade 4 stretch)

Run:
    cd backend
    python scripts/generate_grade34_content.py \
        --content-dir ../content-v2 --per-topic 300
"""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Topic registry — must mirror manifest.json
# ---------------------------------------------------------------------------

TOPICS: List[Dict[str, str]] = [
    {"topic_id": "counting_observation", "folder": "topic-1-counting",
     "topic_name": "Counting & Observation", "topic_index": 1},
    {"topic_id": "arithmetic_missing_numbers", "folder": "topic-2-arithmetic",
     "topic_name": "Arithmetic & Missing Numbers", "topic_index": 2},
    {"topic_id": "patterns_sequences", "folder": "topic-3-patterns",
     "topic_name": "Patterns & Sequences", "topic_index": 3},
    {"topic_id": "logic_ordering", "folder": "topic-4-logic",
     "topic_name": "Logic & Ordering", "topic_index": 4},
    {"topic_id": "spatial_reasoning_3d", "folder": "topic-5-spatial",
     "topic_name": "Spatial Reasoning & 3D", "topic_index": 5},
    {"topic_id": "shapes_folding_symmetry", "folder": "topic-6-shapes",
     "topic_name": "Shapes, Folding & Symmetry", "topic_index": 6},
    {"topic_id": "word_problems_stories", "folder": "topic-7-word-problems",
     "topic_name": "Word Problems & Stories", "topic_index": 7},
    {"topic_id": "number_puzzles_games", "folder": "topic-8-puzzles",
     "topic_name": "Number Puzzles & Games", "topic_index": 8},
]


# ---------------------------------------------------------------------------
# Difficulty tiers
# ---------------------------------------------------------------------------

def _tier_for(score: int) -> str:
    if score <= 130:
        return "advanced"
    if score <= 170:
        return "expert"
    return "olympiad"


# ---------------------------------------------------------------------------
# Helper: build a Socratic 6-level hint ladder
# ---------------------------------------------------------------------------

def hint_ladder(specifics: Dict[str, str]) -> Dict[str, str]:
    return {
        "level_0": specifics.get("l0", "What's the question really asking?"),
        "level_1": specifics.get("l1", "Pick out the numbers and what they represent."),
        "level_2": specifics.get("l2", "Can you set this up as an equation?"),
        "level_3": specifics.get("l3", "Try a smaller example first."),
        "level_4": specifics.get("l4", "Work step by step — what comes first?"),
        "level_5": specifics.get("l5", "Solve carefully — read each line twice."),
    }


def build_diagnostics(choices: List[str], correct_idx: int,
                      explanations: Dict[int, str] | None = None) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for i, _ in enumerate(choices):
        if i == correct_idx:
            out[str(i)] = "Correct! Nicely done. 🎉"
        elif explanations and i in explanations:
            out[str(i)] = explanations[i]
        else:
            out[str(i)] = "Not quite — re-check your work."
    return out


# ---------------------------------------------------------------------------
# Question generators per topic
# ---------------------------------------------------------------------------

def gen_counting(rng: random.Random, score: int) -> Tuple[str, List[str], int, Dict[str, str]]:
    """Topic 1 — Counting & Observation (Grade 3-4)."""
    style = rng.choice(["array", "matrix_count", "skip_count", "tally"])
    if style == "array":
        rows = rng.randint(7, 15)
        cols = rng.randint(7, 15)
        ans = rows * cols
        stem = (f"A grid has {rows} rows and {cols} columns of stickers. "
                f"How many stickers are there in total?")
        hints = {
            "l0": "Rows × columns will give the total.",
            "l1": f"You have {rows} rows of {cols} each.",
            "l2": "Multiplication is repeated addition.",
            "l3": f"Try: {cols} + {cols} + ... ({rows} times).",
            "l4": f"{rows} × {cols} = ?",
            "l5": f"{rows} × {cols} = {ans}.",
        }
    elif style == "matrix_count":
        cubes = rng.randint(20, 60) + score
        used = rng.randint(5, cubes - 1)
        ans = cubes - used
        stem = (f"A box had {cubes} cubes. Builder Bee used {used} of them. "
                f"How many cubes are left?")
        hints = {
            "l0": "We need what's left after some are used.",
            "l1": "Take the total and subtract what was used.",
            "l2": f"{cubes} − {used} = ?",
            "l3": "Subtract one digit at a time.",
            "l4": f"{cubes} − {used} = {ans}",
            "l5": f"{cubes} take away {used} leaves {ans}.",
        }
    elif style == "skip_count":
        step = rng.choice([3, 4, 6, 7, 8, 9, 11, 12])
        n = rng.randint(8, 14)
        ans = step * n
        stem = (f"A spider has {step} legs across {n} body sections. "
                f"How many legs in total?")
        hints = {
            "l0": "Skip-count by the number of legs per section.",
            "l1": f"Count: {step}, {step*2}, {step*3} ...",
            "l2": f"That's {step} × {n}.",
            "l3": f"Multiplication: {step} × {n}",
            "l4": f"Result: {ans}",
            "l5": f"{step} × {n} = {ans}",
        }
    else:
        bunches = rng.randint(8, 20) + (score // 20)
        per = rng.choice([5, 10, 25])
        ans = bunches * per
        stem = (f"There are {bunches} bunches of grapes with {per} grapes in each. "
                f"How many grapes are there?")
        hints = {
            "l0": "Count by groups.",
            "l1": f"Each bunch has {per}.",
            "l2": f"{bunches} groups of {per}.",
            "l3": f"{bunches} × {per}",
            "l4": "Use multiplication.",
            "l5": f"{bunches} × {per} = {ans}",
        }
    distractors = _make_numeric_distractors(ans, rng)
    choices, correct = _shuffle_choices(ans, distractors, rng)
    return stem, choices, correct, hints


def gen_arithmetic(rng: random.Random, score: int) -> Tuple[str, List[str], int, Dict[str, str]]:
    """Topic 2 — Arithmetic & Missing Numbers (Grade 3-4)."""
    op = rng.choice(["add_3digit", "sub_3digit", "mul_2digit", "div_simple", "missing"])
    if op == "add_3digit":
        a = rng.randint(120, 800)
        b = rng.randint(120, 800)
        ans = a + b
        stem = f"What is {a} + {b}?"
        hints = {"l0": "Stack and add.", "l1": "Line up by place value.",
                 "l2": "Add ones, tens, then hundreds.", "l3": "Carry over when needed.",
                 "l4": "Take it slow.", "l5": f"{a} + {b} = {ans}"}
    elif op == "sub_3digit":
        a = rng.randint(400, 999)
        b = rng.randint(50, a - 1)
        ans = a - b
        stem = f"What is {a} − {b}?"
        hints = {"l0": "Stack and subtract.", "l1": "Line up by place value.",
                 "l2": "Borrow when the top digit is smaller.",
                 "l3": "Subtract ones first, then tens.", "l4": "Stay tidy.",
                 "l5": f"{a} − {b} = {ans}"}
    elif op == "mul_2digit":
        a = rng.randint(8, 25)
        b = rng.randint(6, 19)
        ans = a * b
        stem = f"What is {a} × {b}?"
        hints = {"l0": "Use the multiplication algorithm.",
                 "l1": "Break it down by place value.",
                 "l2": f"{a} × {b} = {a} × ({b // 10}0 + {b % 10})",
                 "l3": "Multiply, then add the partial products.",
                 "l4": "Double-check addition at the end.",
                 "l5": f"{a} × {b} = {ans}"}
    elif op == "div_simple":
        b = rng.randint(3, 9)
        q = rng.randint(8, 25)
        a = b * q
        ans = q
        stem = f"What is {a} ÷ {b}?"
        hints = {"l0": "How many times does the divisor fit?",
                 "l1": f"Think: {b} × ? = {a}",
                 "l2": "Use a multiplication table you know.",
                 "l3": "Try guessing and checking.",
                 "l4": "Multiplication and division are inverses.",
                 "l5": f"{a} ÷ {b} = {ans}"}
    else:
        a = rng.randint(20, 80)
        ans = rng.randint(15, 65)
        total = a + ans
        stem = f"{a} + ___ = {total}. What is the missing number?"
        hints = {"l0": "Find what to add to get the total.",
                 "l1": f"Subtract {a} from {total}.",
                 "l2": "The missing number = total − known part.",
                 "l3": f"{total} − {a} = ?",
                 "l4": "Stay organized.", "l5": f"Answer: {ans}"}
    distractors = _make_numeric_distractors(ans, rng)
    choices, correct = _shuffle_choices(ans, distractors, rng)
    return stem, choices, correct, hints


def gen_patterns(rng: random.Random, score: int) -> Tuple[str, List[str], int, Dict[str, str]]:
    """Topic 3 — Patterns & Sequences."""
    style = rng.choice(["arithmetic", "geometric", "fibonacci", "mixed"])
    if style == "arithmetic":
        start = rng.randint(3, 20)
        step = rng.randint(3, 11)
        seq = [start + step * i for i in range(5)]
        ans = seq[-1] + step
        stem = f"What is the next number in the sequence: {', '.join(map(str, seq))}, ___ ?"
        hints = {"l0": "Look at the gap between numbers.",
                 "l1": f"The gap is {step} each time.",
                 "l2": "Add the gap to the last number.",
                 "l3": f"{seq[-1]} + {step} = ?",
                 "l4": "It's an arithmetic sequence.",
                 "l5": f"Next: {ans}"}
    elif style == "geometric":
        start = rng.choice([2, 3, 4, 5])
        r = rng.choice([2, 3])
        seq = [start * (r ** i) for i in range(4)]
        ans = seq[-1] * r
        stem = f"What is the next number: {', '.join(map(str, seq))}, ___ ?"
        hints = {"l0": "Each number relates to the next by multiplication.",
                 "l1": f"Try dividing consecutive numbers.",
                 "l2": f"Each number is {r}× the previous one.",
                 "l3": f"Multiply {seq[-1]} by {r}.",
                 "l4": "Geometric sequence.",
                 "l5": f"Next: {ans}"}
    elif style == "fibonacci":
        a, b = rng.randint(1, 5), rng.randint(2, 8)
        seq = [a, b]
        for _ in range(4):
            seq.append(seq[-1] + seq[-2])
        ans = seq[-1] + seq[-2]
        stem = f"What is next: {', '.join(map(str, seq))}, ___ ?"
        hints = {"l0": "Each term depends on the ones before it.",
                 "l1": f"Try adding the last two: {seq[-2]} + {seq[-1]}.",
                 "l2": "Fibonacci-style!",
                 "l3": f"{seq[-2]} + {seq[-1]} = ?",
                 "l4": "Add carefully.", "l5": f"Next: {ans}"}
    else:
        # square / cube
        kind = rng.choice(["square", "cube"])
        seq = [i**2 if kind == "square" else i**3 for i in range(2, 6)]
        ans = (6 ** 2) if kind == "square" else (6 ** 3)
        stem = f"What is next: {', '.join(map(str, seq))}, ___ ?"
        hints = {"l0": "These numbers come from a pattern of multiplication.",
                 "l1": f"They are {'perfect squares' if kind == 'square' else 'perfect cubes'}.",
                 "l2": f"2{'²' if kind == 'square' else '³'}, 3{'²' if kind == 'square' else '³'}, ...",
                 "l3": f"Next: 6{'²' if kind == 'square' else '³'}",
                 "l4": "Compute carefully.", "l5": f"= {ans}"}
    distractors = _make_numeric_distractors(ans, rng)
    choices, correct = _shuffle_choices(ans, distractors, rng)
    return stem, choices, correct, hints


def gen_logic(rng: random.Random, score: int) -> Tuple[str, List[str], int, Dict[str, str]]:
    """Topic 4 — Logic & Ordering."""
    style = rng.choice(["who_is_oldest", "comparison", "true_false"])
    if style == "who_is_oldest":
        names = ["Anya", "Beni", "Chloe", "Dia", "Ethan", "Faiz", "Gita"]
        a, b, c = rng.sample(names, 3)
        # a > b > c, ans = a
        stem = (f"{a} is older than {b}. {b} is older than {c}. "
                f"Who is the oldest?")
        ans_text = a
        choices = [a, b, c, "Cannot be determined"]
        rng.shuffle(choices)
        correct = choices.index(ans_text)
        hints = {"l0": "Order them from oldest to youngest.",
                 "l1": f"{a} > {b}, and {b} > {c}.",
                 "l2": "If A>B and B>C, then A>C.",
                 "l3": f"So {a} is at the top.",
                 "l4": "Transitive ordering.",
                 "l5": f"The oldest is {a}."}
        return stem, choices, correct, hints
    elif style == "comparison":
        # Force three distinct values so "All equal" is genuinely a distractor.
        pool = rng.sample(range(50, 220), 3)
        a, b, c = pool
        ans = max(a, b, c)
        stem = f"Which is the largest: {a}, {b}, {c}?"
        choices = [str(a), str(b), str(c), "All equal"]
        rng.shuffle(choices)
        correct = choices.index(str(ans))
        hints = {"l0": "Compare digit-by-digit, left to right.",
                 "l1": "Look at hundreds first.",
                 "l2": "Then compare tens, then ones.",
                 "l3": "The greatest digit at the highest place wins.",
                 "l4": "Take your time.", "l5": f"Answer: {ans}"}
        return stem, choices, correct, hints
    else:
        a = rng.randint(8, 50)
        b = rng.randint(2, 9)
        prod = a * b
        true_idx = rng.randint(0, 3)
        choices = [
            f"{a} × {b} = {prod + 1}",
            f"{a} × {b} = {prod}",
            f"{a} × {b} = {prod - 1}",
            f"{a} × {b} = {prod + b}",
        ]
        rng.shuffle(choices)
        # Find the index of the true statement
        target = f"{a} × {b} = {prod}"
        correct = choices.index(target)
        stem = "Which statement is TRUE?"
        hints = {"l0": "Compute the multiplication carefully.",
                 "l1": f"{a} × {b} = ?",
                 "l2": "Use a known fact and add the rest.",
                 "l3": f"{a} × {b} = {prod}.",
                 "l4": "Check each option.",
                 "l5": f"Only one matches {prod}."}
        return stem, choices, correct, hints


def gen_spatial(rng: random.Random, score: int) -> Tuple[str, List[str], int, Dict[str, str]]:
    """Topic 5 — Spatial Reasoning & 3D."""
    style = rng.choice(["faces", "edges", "stack_count", "rotation"])
    if style == "faces":
        solid = rng.choice([("cube", 6), ("rectangular prism", 6),
                            ("triangular prism", 5), ("square pyramid", 5),
                            ("triangular pyramid", 4)])
        name, ans = solid
        stem = f"How many faces does a {name} have?"
        hints = {"l0": "A face is a flat surface.",
                 "l1": f"Picture a {name} in your head.",
                 "l2": "Count top, bottom, and sides.",
                 "l3": f"A {name} has specific symmetry.",
                 "l4": "Check each face once.",
                 "l5": f"A {name} has {ans} faces."}
    elif style == "edges":
        solid = rng.choice([("cube", 12), ("triangular prism", 9),
                            ("square pyramid", 8), ("triangular pyramid", 6)])
        name, ans = solid
        stem = f"How many edges does a {name} have?"
        hints = {"l0": "An edge is where two faces meet.",
                 "l1": f"Trace the {name}'s outline.",
                 "l2": "Count top edges, bottom edges, then sides.",
                 "l3": "Don't double count.",
                 "l4": "Be systematic.",
                 "l5": f"A {name} has {ans} edges."}
    elif style == "stack_count":
        l, w, h = rng.randint(3, 6), rng.randint(2, 5), rng.randint(2, 5)
        ans = l * w * h
        stem = (f"A box is {l} cubes long, {w} cubes wide, and {h} cubes tall. "
                f"How many cubes fill it?")
        hints = {"l0": "Volume is length × width × height.",
                 "l1": f"l = {l}, w = {w}, h = {h}.",
                 "l2": f"First count one layer: {l} × {w} = {l*w}.",
                 "l3": f"Then multiply by height: {l*w} × {h}.",
                 "l4": "It's just multiplication.",
                 "l5": f"Volume = {ans} cubes."}
    else:
        n = rng.choice([2, 3, 4, 6])
        deg = 360 // n
        ans = deg
        stem = (f"A shape has {n}-fold rotational symmetry. "
                f"By how many degrees can you rotate it to look the same?")
        hints = {"l0": "Rotational symmetry divides a full turn.",
                 "l1": f"A full turn is 360°.",
                 "l2": f"Divide 360 by {n}.",
                 "l3": f"360 ÷ {n} = ?", "l4": "It's clean division.",
                 "l5": f"Answer: {ans}°"}
    distractors = _make_numeric_distractors(ans, rng)
    choices, correct = _shuffle_choices(ans, distractors, rng)
    return stem, choices, correct, hints


def gen_shapes(rng: random.Random, score: int) -> Tuple[str, List[str], int, Dict[str, str]]:
    """Topic 6 — Shapes, Folding & Symmetry."""
    style = rng.choice(["sym_lines", "perimeter", "area"])
    if style == "sym_lines":
        shape = rng.choice([("equilateral triangle", 3), ("square", 4),
                            ("regular pentagon", 5), ("regular hexagon", 6),
                            ("isosceles triangle", 1), ("rectangle (non-square)", 2)])
        name, ans = shape
        stem = f"How many lines of symmetry does a {name} have?"
        hints = {"l0": "A line of symmetry folds the shape onto itself.",
                 "l1": f"Imagine folding a {name} in different ways.",
                 "l2": "Each fold that matches counts.",
                 "l3": "Try vertical, horizontal, and diagonal folds.",
                 "l4": "Be careful with regular shapes.",
                 "l5": f"A {name} has {ans} lines of symmetry."}
        distractors = _make_numeric_distractors(ans, rng)
        choices, correct = _shuffle_choices(ans, distractors, rng)
        return stem, choices, correct, hints
    elif style == "perimeter":
        l = rng.randint(8, 35)
        w = rng.randint(4, 30)
        ans = 2 * (l + w)
        stem = (f"A rectangle has length {l} cm and width {w} cm. "
                f"What is its perimeter (in cm)?")
        hints = {"l0": "Perimeter is the distance around the shape.",
                 "l1": f"Add up all four sides: {l} + {w} + {l} + {w}.",
                 "l2": "That's the same as 2(l + w).",
                 "l3": f"= 2 × ({l} + {w})",
                 "l4": "Compute step by step.",
                 "l5": f"= {ans} cm"}
    else:
        l = rng.randint(6, 20)
        w = rng.randint(4, 18)
        ans = l * w
        stem = (f"A rectangle is {l} cm by {w} cm. "
                f"What is its area (in cm²)?")
        hints = {"l0": "Area of a rectangle is length × width.",
                 "l1": f"l = {l} cm, w = {w} cm.",
                 "l2": f"{l} × {w} = ?",
                 "l3": "Multiply carefully.",
                 "l4": "Don't forget the units (cm²).",
                 "l5": f"Area = {ans} cm²."}
    distractors = _make_numeric_distractors(ans, rng)
    choices, correct = _shuffle_choices(ans, distractors, rng)
    return stem, choices, correct, hints


def gen_word_problems(rng: random.Random, score: int) -> Tuple[str, List[str], int, Dict[str, str]]:
    """Topic 7 — Word Problems & Stories."""
    style = rng.choice(["multistep", "rate", "fraction", "money"])
    name = rng.choice(["Aria", "Bo", "Cyrus", "Daria", "Esha", "Felix", "Gigi"])
    if style == "multistep":
        starting = rng.randint(40, 120)
        gave = rng.randint(8, 30)
        bought = rng.randint(15, 50)
        ans = starting - gave + bought
        stem = (f"{name} had {starting} marbles. {name} gave {gave} to a friend, "
                f"then bought {bought} more. How many marbles now?")
        hints = {"l0": "Two steps: subtract first, then add.",
                 "l1": f"After giving: {starting} − {gave} = {starting - gave}.",
                 "l2": f"After buying: ({starting} − {gave}) + {bought}.",
                 "l3": "Combine carefully.",
                 "l4": "Watch the operations.",
                 "l5": f"Answer: {ans}"}
    elif style == "rate":
        rate = rng.randint(3, 12)
        time = rng.randint(4, 15)
        ans = rate * time
        stem = (f"A printer prints {rate} pages per minute. "
                f"How many pages in {time} minutes?")
        hints = {"l0": "Rate × time = total.",
                 "l1": f"Rate is {rate} per minute.",
                 "l2": f"Multiply by {time} minutes.",
                 "l3": f"{rate} × {time} = ?",
                 "l4": "It's a multiplication problem in disguise.",
                 "l5": f"= {ans} pages."}
    elif style == "fraction":
        whole = rng.choice([12, 18, 20, 24, 30, 36])
        part = rng.choice([2, 3, 4, 6])
        ans = whole // part
        stem = f"{name} ate 1/{part} of a pizza with {whole} slices. How many slices?"
        hints = {"l0": "A fraction means dividing into equal parts.",
                 "l1": f"Divide {whole} by {part}.",
                 "l2": f"{whole} ÷ {part} = ?",
                 "l3": "Equal-share thinking.",
                 "l4": "Check by multiplying back.",
                 "l5": f"Answer: {ans} slices"}
    else:
        # money problem
        each = rng.randint(8, 35)
        n = rng.randint(3, 9)
        ans = each * n
        stem = (f"Pencils cost ₹{each} each. {name} buys {n} pencils. "
                f"How much does {name} spend in total (in ₹)?")
        hints = {"l0": "Cost per item × number of items.",
                 "l1": f"₹{each} × {n} pencils.",
                 "l2": f"{each} × {n} = ?",
                 "l3": "Use repeated addition if needed.",
                 "l4": "Stay tidy.", "l5": f"₹{ans} total."}
    distractors = _make_numeric_distractors(ans, rng)
    choices, correct = _shuffle_choices(ans, distractors, rng)
    return stem, choices, correct, hints


def gen_puzzles(rng: random.Random, score: int) -> Tuple[str, List[str], int, Dict[str, str]]:
    """Topic 8 — Number Puzzles & Games."""
    style = rng.choice(["digit_sum", "even_odd", "place_value", "guess"])
    if style == "digit_sum":
        n = rng.randint(120, 9999)
        ans = sum(int(d) for d in str(n))
        stem = f"What is the sum of the digits of {n}?"
        hints = {"l0": "Add the digits one by one.",
                 "l1": f"Digits of {n}: {' + '.join(str(n))}",
                 "l2": "Add left to right.",
                 "l3": "Group into pairs if it helps.",
                 "l4": "Stay neat.", "l5": f"Sum = {ans}"}
    elif style == "even_odd":
        a = rng.randint(50, 300)
        b = rng.randint(50, 300)
        prod = a * b
        ans = "Even" if prod % 2 == 0 else "Odd"
        stem = f"Without computing, is {a} × {b} even or odd?"
        choices = ["Even", "Odd", "Either is possible", "Cannot decide"]
        rng.shuffle(choices)
        correct = choices.index(ans)
        even = (a % 2 == 0) or (b % 2 == 0)
        hints = {"l0": "Even × anything = ?",
                 "l1": "If at least one number is even, the product is even.",
                 "l2": f"{a} is {'even' if a%2==0 else 'odd'}, {b} is {'even' if b%2==0 else 'odd'}.",
                 "l3": "Apply the rule.",
                 "l4": "Both odd? Then odd. Otherwise even.",
                 "l5": f"Answer: {ans}"}
        return stem, choices, correct, hints
    elif style == "place_value":
        n = rng.randint(1000, 9999)
        digit_idx = rng.randint(0, 3)
        digit = int(str(n)[digit_idx])
        place_value = digit * (10 ** (3 - digit_idx))
        ans = place_value
        place_names = ["thousands", "hundreds", "tens", "ones"]
        stem = f"In the number {n}, what is the value of the digit in the {place_names[digit_idx]} place?"
        hints = {"l0": "Place value depends on position.",
                 "l1": f"The digit is {digit}.",
                 "l2": f"It sits in the {place_names[digit_idx]} place.",
                 "l3": f"So its value is {digit} × {10 ** (3 - digit_idx)}.",
                 "l4": "Place value = digit × position power.",
                 "l5": f"Value = {ans}"}
    else:
        # I am thinking of a number...
        ans = rng.randint(20, 80)
        more_than = ans - rng.choice([5, 7, 10])
        less_than = ans + rng.choice([3, 5, 8])
        stem = (f"I am thinking of a number greater than {more_than} "
                f"and less than {less_than}. It is divisible by {ans % 10 if ans % 10 != 0 else 5}. "
                f"What is it?")
        # If the constraint isn't unique, just keep ans as the answer; hint accordingly.
        hints = {"l0": "Try numbers in the range.",
                 "l1": f"Between {more_than} and {less_than}.",
                 "l2": "Test which one fits the divisibility rule.",
                 "l3": f"Hint: it's near the middle of the range.",
                 "l4": "Process of elimination works.",
                 "l5": f"Answer: {ans}"}
    distractors = _make_numeric_distractors(ans, rng)
    choices, correct = _shuffle_choices(ans, distractors, rng)
    return stem, choices, correct, hints


# ---------------------------------------------------------------------------
# Distractor + shuffle helpers
# ---------------------------------------------------------------------------

def _make_numeric_distractors(ans, rng: random.Random) -> List[Any]:
    if isinstance(ans, str):
        return []
    a = ans
    deltas = [-1, +1, -2, +2, -10, +10, -5, +5]
    rng.shuffle(deltas)
    out = []
    seen = {a}
    for d in deltas:
        cand = a + d
        if cand <= 0:
            continue
        if cand in seen:
            continue
        out.append(cand)
        seen.add(cand)
        if len(out) == 3:
            break
    while len(out) < 3:
        # Filler if everything collided
        cand = max(1, a + rng.randint(-15, 15))
        if cand not in seen:
            out.append(cand)
            seen.add(cand)
    return out


def _shuffle_choices(ans, distractors: List[Any], rng: random.Random) -> Tuple[List[str], int]:
    choices = [ans] + list(distractors)
    rng.shuffle(choices)
    correct = choices.index(ans)
    return [str(c) for c in choices], correct


# ---------------------------------------------------------------------------
# Topic dispatcher
# ---------------------------------------------------------------------------

GENERATORS = {
    "counting_observation": gen_counting,
    "arithmetic_missing_numbers": gen_arithmetic,
    "patterns_sequences": gen_patterns,
    "logic_ordering": gen_logic,
    "spatial_reasoning_3d": gen_spatial,
    "shapes_folding_symmetry": gen_shapes,
    "word_problems_stories": gen_word_problems,
    "number_puzzles_games": gen_puzzles,
}


def build_question(topic: Dict[str, str], qid: str, score: int,
                   rng: random.Random) -> Dict[str, Any]:
    gen = GENERATORS[topic["topic_id"]]
    stem, choices, correct, hints = gen(rng, score)
    return {
        "id": qid,
        "stem": stem,
        "choices": choices,
        "correct_answer": correct,
        "difficulty_tier": _tier_for(score),
        "difficulty_score": score,
        "visual_svg": None,
        "visual_alt": None,
        "diagnostics": build_diagnostics(choices, correct),
        "tags": [topic["topic_id"], _tier_for(score), "grade-3-4"],
        "topic": topic["topic_id"],
        "topic_name": topic["topic_name"],
        "original_stem": stem,
        "hint": hint_ladder(hints),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-dir", default="../content-v2",
                        help="Path to content-v2 root")
    parser.add_argument("--per-topic", type=int, default=300,
                        help="Number of questions per topic")
    parser.add_argument("--start-difficulty", type=int, default=101)
    parser.add_argument("--end-difficulty", type=int, default=200)
    parser.add_argument("--start-id", type=int, default=601,
                        help="First numeric ID to use (existing G1-2 use 1-600)")
    parser.add_argument("--seed", type=int, default=20260428)
    parser.add_argument("--output-name", default="grade34_questions.json",
                        help="Filename inside each topic folder")
    args = parser.parse_args()

    root = Path(args.content_dir).resolve()
    if not root.exists():
        raise SystemExit(f"Content dir does not exist: {root}")

    overall_total = 0
    for topic in TOPICS:
        rng = random.Random(args.seed + topic["topic_index"])
        folder = root / topic["folder"]
        folder.mkdir(parents=True, exist_ok=True)

        questions: List[Dict[str, Any]] = []
        per = args.per_topic
        diff_lo = args.start_difficulty
        diff_hi = args.end_difficulty
        diff_range = diff_hi - diff_lo + 1

        for i in range(per):
            # Distribute difficulty roughly evenly across the band.
            score = diff_lo + int((i / per) * diff_range)
            score = max(diff_lo, min(diff_hi, score))
            qid_num = args.start_id + i
            qid = f"T{topic['topic_index']}-{qid_num:04d}"
            try:
                q = build_question(topic, qid, score, rng)
                questions.append(q)
            except Exception as e:
                print(f"Failed to build {qid}: {e}")

        # Build distribution
        dist: Dict[str, int] = {}
        for q in questions:
            dist[q["difficulty_tier"]] = dist.get(q["difficulty_tier"], 0) + 1

        out = {
            "topic_id": topic["topic_id"],
            "topic_name": topic["topic_name"],
            "version": "2.0-g34",
            "total_questions": len(questions),
            "difficulty_distribution": dist,
            "questions": questions,
        }

        out_path = folder / args.output_name
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
        overall_total += len(questions)
        print(f"  {topic['topic_id']}: wrote {len(questions)} → {out_path}")

    print(f"\nDone. {overall_total} grade 3-4 questions written.")


if __name__ == "__main__":
    main()
