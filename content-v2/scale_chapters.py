#!/usr/bin/env python3
"""
Scale curriculum chapter content so every chapter has at least 50 questions.
Generates new questions using parametric templates with proper IRT params,
hints, diagnostics, and solution steps.
"""

import json
import os
import random
import math
from pathlib import Path

random.seed(42)

BASE = Path(__file__).parent
TARGET_MIN = 50

# --- File discovery ---

def get_content_files():
    """Return list of (curriculum, grade, filepath) tuples."""
    files = []
    for g in range(1, 7):
        # NCERT
        if g <= 2:
            p = BASE / f"ncert-curriculum/grade{g}/questions.json"
        else:
            p = BASE / f"ncert-curriculum/grade{g}/ncert_g{g}_questions.json"
        if p.exists():
            files.append(("NCERT", g, p))

        # ICSE
        p = BASE / f"icse-curriculum/grade{g}/icse_g{g}_questions.json"
        if p.exists():
            files.append(("ICSE", g, p))

        # IGCSE
        p = BASE / f"igcse-curriculum/grade{g}/igcse_grade{g}.json"
        if p.exists():
            files.append(("IGCSE", g, p))

    return files


# --- IRT parameter generation ---

def generate_irt_params(difficulty_tier):
    """Generate IRT parameters correlated with difficulty."""
    if difficulty_tier == "easy":
        b = round(random.uniform(-1.5, -0.5), 2)
    elif difficulty_tier == "medium":
        b = round(random.uniform(-0.5, 0.5), 2)
    else:  # hard
        b = round(random.uniform(0.5, 1.5), 2)
    a = round(random.uniform(0.8, 1.8), 2)
    c = 0.25  # guessing param for 4-choice
    return {"a": a, "b": b, "c": c}


def difficulty_tier_from_score(score, grade):
    """Determine tier from score within grade range."""
    low = (grade - 1) * 50 + 1
    high = grade * 50
    span = high - low
    relative = (score - low) / span
    if relative < 0.33:
        return "easy"
    elif relative < 0.67:
        return "medium"
    else:
        return "hard"


# --- Template-based question generators by topic ---

def gen_numbers_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate number/place value questions."""
    questions = []
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        if grade <= 2:
            num = random.randint(10, 99)
            place = "tens"
            answer = num // 10
            distractors = make_distinct_distractors(answer, 0, 9, 3)
        elif grade == 3:
            num = random.randint(1000, 9999)
            places = ["thousands", "hundreds", "tens", "ones"]
            place = random.choice(places)
            idx = places.index(place)
            digits = [int(d) for d in str(num)]
            answer = digits[idx]
            distractors = make_distinct_distractors(answer, 0, 9, 3)
        elif grade == 4:
            num = random.randint(10000, 99999)
            places = ["ten-thousands", "thousands", "hundreds", "tens", "ones"]
            place = random.choice(places)
            idx = places.index(place)
            digits = [int(d) for d in str(num)]
            answer = digits[idx]
            distractors = make_distinct_distractors(answer, 0, 9, 3)
        else:
            num = random.randint(100000, 999999)
            places = ["lakhs", "ten-thousands", "thousands", "hundreds", "tens", "ones"]
            place = random.choice(places[:4])
            idx = places.index(place)
            digits = [int(d) for d in str(num)]
            answer = digits[idx]
            distractors = make_distinct_distractors(answer, 0, 9, 3)

        choices, correct_idx = build_choices(str(answer), [str(d) for d in distractors])

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=f"What is the digit in the {place} place of {num:,}?",
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["numbers", "place_value"],
            irt=irt,
            hint={
                "level_0": "Think about what each position in a number represents.",
                "level_1": f"In {num:,}, count the positions from right: ones, tens, hundreds...",
                "level_2": f"The {place} digit in {num:,} is {answer}."
            },
            diagnostics={"1": "Confused place positions", "2": "Counted from wrong end", "3": "Mixed up digit values"},
            solution_steps=[
                f"Write out the number: {num:,}",
                f"Identify positions from right: ones, tens, hundreds, thousands...",
                f"The digit in the {place} place is {answer}."
            ]
        )
        questions.append(q)
    return questions


def gen_addition_subtraction_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate addition and subtraction questions."""
    questions = []
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        is_add = random.choice([True, False])
        if grade <= 2:
            a = random.randint(5, 50)
            b = random.randint(5, min(a, 50))
        elif grade == 3:
            a = random.randint(100, 9999)
            b = random.randint(100, min(a, 9999))
        elif grade == 4:
            a = random.randint(1000, 99999)
            b = random.randint(1000, min(a, 99999))
        else:
            a = random.randint(10000, 999999)
            b = random.randint(10000, min(a, 999999))

        if is_add:
            answer = a + b
            stem = f"What is {a:,} + {b:,}?"
            op = "addition"
        else:
            answer = a - b
            stem = f"What is {a:,} - {b:,}?"
            op = "subtraction"

        # Plausible distractors: off-by-one, wrong carry, digit swap
        d1 = answer + random.choice([1, -1, 10, -10])
        d2 = answer + random.choice([100, -100, 11, -11])
        d3 = answer + random.choice([2, -2, 20, -20])
        distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])

        choices, correct_idx = build_choices(str(answer), [str(d) for d in distractors])

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["arithmetic", op],
            irt=irt,
            hint={
                "level_0": f"This is an {op} problem.",
                "level_1": f"Line up the digits by place value and {'add' if is_add else 'subtract'}.",
                "level_2": f"{a:,} {'+ ' if is_add else '- '}{b:,} = {answer:,}"
            },
            diagnostics={"1": "Carry/borrow error", "2": "Wrong operation used", "3": "Digit alignment mistake"},
            solution_steps=[
                f"Write numbers aligned by place value: {a:,} and {b:,}",
                f"{'Add' if is_add else 'Subtract'} column by column from right to left",
                f"The answer is {answer:,}"
            ]
        )
        questions.append(q)
    return questions


def gen_multiplication_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate multiplication questions."""
    questions = []
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        if grade <= 3:
            a = random.randint(2, 12)
            b = random.randint(2, 12)
        elif grade == 4:
            a = random.randint(10, 99)
            b = random.randint(2, 12)
        else:
            a = random.randint(10, 999)
            b = random.randint(2, 99)

        answer = a * b
        stem = f"What is {a} × {b}?"

        d1 = a * (b + 1)
        d2 = a * (b - 1) if b > 1 else a * (b + 2)
        d3 = answer + a
        distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])

        choices, correct_idx = build_choices(str(answer), [str(d) for d in distractors])

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["arithmetic", "multiplication"],
            irt=irt,
            hint={
                "level_0": "Think of multiplication as repeated addition.",
                "level_1": f"{a} × {b} means adding {a} a total of {b} times.",
                "level_2": f"{a} × {b} = {answer}"
            },
            diagnostics={"1": "Table recall error", "2": "Added instead of multiplied", "3": "Off by one group"},
            solution_steps=[
                f"Multiply {a} × {b}",
                f"Use known facts or break into parts",
                f"The answer is {answer}"
            ]
        )
        questions.append(q)
    return questions


def gen_division_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate division questions."""
    questions = []
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        if grade <= 3:
            b = random.randint(2, 10)
            answer = random.randint(2, 12)
        elif grade == 4:
            b = random.randint(2, 12)
            answer = random.randint(10, 50)
        else:
            b = random.randint(2, 25)
            answer = random.randint(10, 100)

        a = answer * b
        stem = f"What is {a} ÷ {b}?"

        d1 = answer + 1
        d2 = answer - 1 if answer > 1 else answer + 2
        d3 = answer + b
        distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])

        choices, correct_idx = build_choices(str(answer), [str(d) for d in distractors])

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["arithmetic", "division"],
            irt=irt,
            hint={
                "level_0": "Division is splitting into equal groups.",
                "level_1": f"How many groups of {b} fit into {a}?",
                "level_2": f"{a} ÷ {b} = {answer}"
            },
            diagnostics={"1": "Remainder confusion", "2": "Used wrong operation", "3": "Table recall error"},
            solution_steps=[
                f"Divide {a} by {b}",
                f"Think: {b} × ? = {a}",
                f"The answer is {answer}"
            ]
        )
        questions.append(q)
    return questions


def gen_fractions_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate fractions questions."""
    questions = []
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        denom = random.choice([2, 3, 4, 5, 6, 8, 10])
        numer = random.randint(1, denom - 1)

        # Only allow compare if denom > 2 (otherwise only 1 possible numerator)
        variants = ["identify", "equivalent"]
        if denom > 2:
            variants.append("compare")
        variant = random.choice(variants)
        if variant == "identify":
            stem = f"What fraction of a whole is {numer} parts out of {denom} equal parts?"
            answer = f"{numer}/{denom}"
            d1 = f"{denom}/{numer}" if numer != denom else f"{numer+1}/{denom}"
            d2 = f"{numer}/{denom+1}"
            d3 = f"{numer+1}/{denom}"
            distractors = [d1, d2, d3]
        elif variant == "compare":
            n2 = random.randint(1, denom - 1)
            while n2 == numer:
                n2 = random.randint(1, denom - 1)
            bigger = max(numer, n2)
            stem = f"Which is larger: {numer}/{denom} or {n2}/{denom}?"
            answer = f"{bigger}/{denom}"
            smaller = min(numer, n2)
            d1 = f"{smaller}/{denom}"
            d2 = f"{denom}/{bigger}"
            d3 = f"{bigger}/{denom+1}"
            distractors = [d1, d2, d3]
        else:  # equivalent
            mult = random.randint(2, 4)
            eq_n = numer * mult
            eq_d = denom * mult
            stem = f"Which fraction is equivalent to {numer}/{denom}?"
            answer = f"{eq_n}/{eq_d}"
            d1 = f"{eq_n + 1}/{eq_d}"
            d2 = f"{eq_n}/{eq_d + 1}"
            d3 = f"{numer + 1}/{denom}"
            distractors = [d1, d2, d3]

        # Ensure all distinct
        all_opts = [answer] + distractors
        seen = set()
        unique = []
        for o in all_opts:
            if o not in seen:
                seen.add(o)
                unique.append(o)
        while len(unique) < 4:
            unique.append(f"{random.randint(1,9)}/{random.randint(2,10)}")
            unique = list(dict.fromkeys(unique))

        choices, correct_idx = build_choices(unique[0], unique[1:4])

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["fractions"],
            irt=irt,
            hint={
                "level_0": "A fraction shows parts of a whole.",
                "level_1": f"The denominator ({denom}) tells how many equal parts total.",
                "level_2": f"The answer is {answer}."
            },
            diagnostics={"1": "Swapped numerator/denominator", "2": "Did not simplify", "3": "Wrong comparison"},
            solution_steps=[
                "Identify numerator and denominator",
                "Apply the operation (compare, simplify, or find equivalent)",
                f"The answer is {answer}"
            ]
        )
        questions.append(q)
    return questions


def gen_money_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate money/currency questions."""
    questions = []
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        if grade <= 2:
            price = random.randint(5, 50)
            paid = price + random.randint(1, 20)
        else:
            price = random.randint(10, 500)
            paid = price + random.choice([10, 20, 50, 100])

        change = paid - price
        stem = f"You buy an item costing ₹{price} and pay ₹{paid}. How much change do you get?"
        answer = change
        d1 = change + random.choice([1, 5, 10])
        d2 = change - random.choice([1, 5]) if change > 5 else change + 15
        d3 = paid + price  # common mistake: adding instead
        distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])

        choices, correct_idx = build_choices(f"₹{answer}", [f"₹{d}" for d in distractors])

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["money", "subtraction"],
            irt=irt,
            hint={
                "level_0": "Change = Amount paid - Cost.",
                "level_1": f"Subtract: ₹{paid} - ₹{price}",
                "level_2": f"The change is ₹{change}."
            },
            diagnostics={"1": "Added instead of subtracted", "2": "Subtraction error", "3": "Confused cost and paid"},
            solution_steps=[
                f"Change = Amount paid - Cost",
                f"= ₹{paid} - ₹{price}",
                f"= ₹{change}"
            ]
        )
        questions.append(q)
    return questions


def gen_measurement_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate measurement questions (length, weight, capacity)."""
    questions = []
    units = [("cm", "m", 100), ("mm", "cm", 10), ("g", "kg", 1000), ("mL", "L", 1000)]
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        small, big, factor = random.choice(units)
        val = random.randint(1, 20)
        converted = val * factor

        variant = random.choice(["to_small", "to_big"])
        if variant == "to_small":
            stem = f"Convert {val} {big} to {small}."
            answer = converted
            d1 = val * (factor // 10) if factor >= 100 else val * factor + 10
            d2 = val + factor
            d3 = converted + factor
        else:
            small_val = random.randint(1, 10) * factor
            big_val = small_val // factor
            stem = f"Convert {small_val} {small} to {big}."
            answer = big_val
            d1 = big_val * 10
            d2 = big_val + 1
            d3 = small_val

        distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])
        choices, correct_idx = build_choices(f"{answer} {big if variant == 'to_big' else small}",
                                            [f"{d} {big if variant == 'to_big' else small}" for d in distractors])

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["measurement", "conversion"],
            irt=irt,
            hint={
                "level_0": f"Remember: 1 {big} = {factor} {small}.",
                "level_1": f"To convert, multiply or divide by {factor}.",
                "level_2": f"The answer is {answer}."
            },
            diagnostics={"1": "Wrong conversion factor", "2": "Multiplied instead of divided", "3": "Unit confusion"},
            solution_steps=[
                f"Recall: 1 {big} = {factor} {small}",
                f"Apply conversion",
                f"The answer is {answer}"
            ]
        )
        questions.append(q)
    return questions


def gen_time_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate time questions."""
    questions = []
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        hour = random.randint(1, 12)
        minute = random.choice([0, 15, 30, 45, 5, 10, 20, 25, 35, 40, 50, 55])
        add_min = random.choice([15, 30, 45, 60, 90, 120])

        total_min = hour * 60 + minute + add_min
        new_hour = (total_min // 60) % 12
        if new_hour == 0:
            new_hour = 12
        new_min = total_min % 60

        stem = f"If the time is {hour}:{minute:02d}, what time will it be after {add_min} minutes?"
        answer = f"{new_hour}:{new_min:02d}"

        # Distractors
        d1 = f"{new_hour}:{(new_min + 10) % 60:02d}"
        d2 = f"{(new_hour % 12) + 1}:{new_min:02d}"
        d3 = f"{new_hour}:{abs(new_min - 15) % 60:02d}"

        all_opts = list(dict.fromkeys([answer, d1, d2, d3]))
        while len(all_opts) < 4:
            all_opts.append(f"{random.randint(1,12)}:{random.choice([0,15,30,45]):02d}")
            all_opts = list(dict.fromkeys(all_opts))

        choices, correct_idx = build_choices(all_opts[0], all_opts[1:4])

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["time", "elapsed_time"],
            irt=irt,
            hint={
                "level_0": "Add the minutes to the current time.",
                "level_1": f"Start at {hour}:{minute:02d} and add {add_min} minutes.",
                "level_2": f"The new time is {answer}."
            },
            diagnostics={"1": "Hour rollover error", "2": "Added to hour instead of minutes", "3": "Subtracted instead of added"},
            solution_steps=[
                f"Start time: {hour}:{minute:02d}",
                f"Add {add_min} minutes",
                f"New time: {answer}"
            ]
        )
        questions.append(q)
    return questions


def gen_geometry_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate geometry questions."""
    questions = []
    shapes = [
        ("square", lambda s: s*4, "perimeter", "side"),
        ("rectangle", lambda l, w: 2*(l+w), "perimeter", "length and width"),
        ("triangle", lambda a, b, c: a+b+c, "perimeter", "sides"),
    ]
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        variant = random.choice(["perimeter_square", "perimeter_rect", "sides", "angles"])

        if variant == "perimeter_square":
            side = random.randint(3, 20)
            answer = side * 4
            stem = f"What is the perimeter of a square with side {side} cm?"
            d1 = side * side  # area mistake
            d2 = side * 3
            d3 = side * 4 + side
            distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])
            choices, correct_idx = build_choices(f"{answer} cm", [f"{d} cm" for d in distractors])
            tags = ["geometry", "perimeter", "square"]
            steps = [f"Perimeter of square = 4 × side", f"= 4 × {side}", f"= {answer} cm"]
            hint_text = {
                "level_0": "Perimeter is the total distance around.",
                "level_1": "A square has 4 equal sides.",
                "level_2": f"4 × {side} = {answer} cm"
            }
        elif variant == "perimeter_rect":
            l = random.randint(5, 25)
            w = random.randint(3, l - 1)
            answer = 2 * (l + w)
            stem = f"What is the perimeter of a rectangle with length {l} cm and width {w} cm?"
            d1 = l * w  # area
            d2 = l + w
            d3 = 2 * l + w
            distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])
            choices, correct_idx = build_choices(f"{answer} cm", [f"{d} cm" for d in distractors])
            tags = ["geometry", "perimeter", "rectangle"]
            steps = [f"Perimeter = 2 × (length + width)", f"= 2 × ({l} + {w})", f"= {answer} cm"]
            hint_text = {
                "level_0": "Perimeter = 2 × (length + width).",
                "level_1": f"Add {l} + {w} first, then multiply by 2.",
                "level_2": f"2 × {l + w} = {answer} cm"
            }
        elif variant == "sides":
            shape_name = random.choice(["triangle", "quadrilateral", "pentagon", "hexagon"])
            sides_map = {"triangle": 3, "quadrilateral": 4, "pentagon": 5, "hexagon": 6}
            answer = sides_map[shape_name]
            stem = f"How many sides does a {shape_name} have?"
            possible = [3, 4, 5, 6, 7, 8]
            distractors = [x for x in possible if x != answer][:3]
            choices, correct_idx = build_choices(str(answer), [str(d) for d in distractors])
            tags = ["geometry", "shapes", "properties"]
            steps = [f"A {shape_name} is a polygon", f"Count its sides", f"It has {answer} sides"]
            hint_text = {
                "level_0": "Think about the name prefix.",
                "level_1": f"'Tri' = 3, 'Quad' = 4, 'Penta' = 5, 'Hexa' = 6",
                "level_2": f"A {shape_name} has {answer} sides."
            }
        else:  # angles
            angle_sum = random.choice([180, 360])
            shape_for_angle = "triangle" if angle_sum == 180 else "quadrilateral"
            stem = f"What is the sum of angles in a {shape_for_angle}?"
            answer = angle_sum
            distractors = make_distinct_distractors_from_list(answer, [180 if answer == 360 else 360, answer + 90, answer - 90])
            choices, correct_idx = build_choices(f"{answer}°", [f"{d}°" for d in distractors])
            tags = ["geometry", "angles"]
            steps = [f"Recall angle sum property", f"Sum of angles in a {shape_for_angle}", f"= {answer}°"]
            hint_text = {
                "level_0": "Recall the angle sum property of polygons.",
                "level_1": f"Triangle = 180°, Quadrilateral = 360°.",
                "level_2": f"Sum of angles = {answer}°"
            }

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=tags,
            irt=irt,
            hint=hint_text,
            diagnostics={"1": "Confused perimeter/area", "2": "Wrong formula", "3": "Counting error"},
            solution_steps=steps
        )
        questions.append(q)
    return questions


def gen_data_handling_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate data handling / statistics questions."""
    questions = []
    items = ["apples", "oranges", "bananas", "mangoes", "books", "pencils", "balls", "stars"]
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        n_items = random.randint(3, 5)
        chosen = random.sample(items, n_items)
        values = [random.randint(2, 20) for _ in range(n_items)]

        variant = random.choice(["most", "total", "difference"])
        if variant == "most":
            max_idx = values.index(max(values))
            stem = f"In a class survey, {', '.join(f'{chosen[j]}: {values[j]}' for j in range(n_items))}. Which item has the most?"
            answer = chosen[max_idx]
            distractors = [c for c in chosen if c != answer][:3]
            choices, correct_idx = build_choices(answer, distractors)
            ans_display = answer
        elif variant == "total":
            total = sum(values)
            stem = f"A tally shows: {', '.join(f'{chosen[j]}: {values[j]}' for j in range(n_items))}. What is the total?"
            answer = total
            d1 = total + random.randint(1, 5)
            d2 = total - random.randint(1, 5)
            d3 = max(values) * n_items
            distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])
            choices, correct_idx = build_choices(str(answer), [str(d) for d in distractors])
            ans_display = str(answer)
        else:
            max_v = max(values)
            min_v = min(values)
            diff = max_v - min_v
            stem = f"Data: {', '.join(f'{chosen[j]}: {values[j]}' for j in range(n_items))}. What is the difference between the highest and lowest?"
            answer = diff
            d1 = diff + 1
            d2 = max_v
            d3 = min_v
            distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])
            choices, correct_idx = build_choices(str(answer), [str(d) for d in distractors])
            ans_display = str(answer)

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["data_handling", "statistics"],
            irt=irt,
            hint={
                "level_0": "Read the data carefully.",
                "level_1": "Compare or add the values as needed.",
                "level_2": f"The answer is {ans_display}."
            },
            diagnostics={"1": "Misread data", "2": "Wrong operation", "3": "Counting error"},
            solution_steps=[
                "Read all values from the data",
                f"Apply the required operation ({variant})",
                f"The answer is {ans_display}"
            ]
        )
        questions.append(q)
    return questions


def gen_patterns_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate pattern/sequence questions."""
    questions = []
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        pattern_type = random.choice(["arithmetic", "geometric", "skip"])
        if pattern_type == "arithmetic":
            start = random.randint(1, 20)
            step = random.randint(2, 10)
            seq = [start + step * j for j in range(5)]
            answer = seq[-1]
            stem = f"What comes next: {', '.join(str(x) for x in seq[:-1])}, ?"
            d1 = answer + step
            d2 = answer - 1
            d3 = answer + 1
        elif pattern_type == "geometric":
            start = random.randint(1, 5)
            mult = random.choice([2, 3])
            seq = [start * (mult ** j) for j in range(5)]
            answer = seq[-1]
            stem = f"What comes next: {', '.join(str(x) for x in seq[:-1])}, ?"
            d1 = seq[-2] + seq[-2]  # common mistake
            d2 = answer + mult
            d3 = answer * 2
        else:
            start = random.randint(1, 10)
            skip = random.randint(3, 7)
            seq = [start + skip * j for j in range(5)]
            answer = seq[-1]
            stem = f"Find the next number: {', '.join(str(x) for x in seq[:-1])}, ?"
            d1 = answer + 1
            d2 = answer - skip + 1
            d3 = answer + skip

        distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])
        choices, correct_idx = build_choices(str(answer), [str(d) for d in distractors])

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["patterns", "sequences"],
            irt=irt,
            hint={
                "level_0": "Look for a pattern between consecutive numbers.",
                "level_1": f"Find the difference or ratio between terms.",
                "level_2": f"The next number is {answer}."
            },
            diagnostics={"1": "Wrong pattern identified", "2": "Arithmetic error", "3": "Skipped a term"},
            solution_steps=[
                "Find the rule connecting consecutive terms",
                "Apply the rule to the last known term",
                f"The next number is {answer}"
            ]
        )
        questions.append(q)
    return questions


def gen_area_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate area questions."""
    questions = []
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        variant = random.choice(["square", "rectangle"])
        if variant == "square":
            side = random.randint(2, 15)
            answer = side * side
            stem = f"What is the area of a square with side {side} cm?"
            d1 = side * 4  # perimeter
            d2 = answer + side
            d3 = answer - 1
            unit = "sq cm"
        else:
            l = random.randint(3, 20)
            w = random.randint(2, l)
            answer = l * w
            stem = f"What is the area of a rectangle with length {l} cm and width {w} cm?"
            d1 = 2 * (l + w)  # perimeter
            d2 = l + w
            d3 = answer + l
            unit = "sq cm"

        distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])
        choices, correct_idx = build_choices(f"{answer} {unit}", [f"{d} {unit}" for d in distractors])

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["geometry", "area"],
            irt=irt,
            hint={
                "level_0": "Area = length × width.",
                "level_1": f"For a {variant}, multiply the sides.",
                "level_2": f"Area = {answer} {unit}"
            },
            diagnostics={"1": "Used perimeter formula", "2": "Multiplication error", "3": "Wrong formula"},
            solution_steps=[
                f"Area of {variant} = {'side × side' if variant == 'square' else 'length × width'}",
                f"= {f'{side} × {side}' if variant == 'square' else f'{l} × {w}'}",
                f"= {answer} {unit}"
            ]
        )
        questions.append(q)
    return questions


def gen_symmetry_questions(grade, chapter, topic, count, start_id, curriculum):
    """Generate symmetry questions."""
    questions = []
    shapes_lines = [
        ("square", 4), ("rectangle", 2), ("equilateral triangle", 3),
        ("circle", "infinite"), ("isosceles triangle", 1), ("regular pentagon", 5),
        ("regular hexagon", 6), ("rhombus", 2)
    ]
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        variant = random.choice(["lines_of_symmetry", "is_symmetric"])
        if variant == "lines_of_symmetry":
            shape, lines = random.choice([(s, l) for s, l in shapes_lines if isinstance(l, int)])
            stem = f"How many lines of symmetry does a {shape} have?"
            answer = lines
            possible = [1, 2, 3, 4, 5, 6]
            distractors = [x for x in possible if x != answer][:3]
            choices, correct_idx = build_choices(str(answer), [str(d) for d in distractors])
            ans_text = str(answer)
        else:
            letters_sym = [("A", "Yes"), ("B", "Yes"), ("M", "Yes"), ("T", "Yes"),
                          ("F", "No"), ("G", "No"), ("J", "No"), ("P", "No")]
            letter, sym = random.choice(letters_sym)
            stem = f"Does the letter '{letter}' have a line of symmetry?"
            answer = sym
            choices = ["Yes", "No", "Only horizontal", "Only diagonal"]
            correct_idx = 0 if sym == "Yes" else 1
            ans_text = answer

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["geometry", "symmetry"],
            irt=irt,
            hint={
                "level_0": "A line of symmetry divides a shape into two equal mirror halves.",
                "level_1": "Try folding the shape along different lines.",
                "level_2": f"The answer is {ans_text}."
            },
            diagnostics={"1": "Confused symmetry with rotation", "2": "Missed a line of symmetry", "3": "Counted incorrectly"},
            solution_steps=[
                "Identify possible fold lines",
                "Check if both halves match exactly",
                f"The answer is {ans_text}"
            ]
        )
        questions.append(q)
    return questions


def gen_generic_arithmetic_questions(grade, chapter, topic, count, start_id, curriculum):
    """Fallback: generate mixed arithmetic questions."""
    questions = []
    for i in range(count):
        diff_score = get_spread_difficulty(i, count, grade)
        tier = difficulty_tier_from_score(diff_score, grade)
        irt = generate_irt_params(tier)

        op = random.choice(["+", "-", "×"])
        if grade <= 2:
            a = random.randint(2, 30)
            b = random.randint(2, 20)
        elif grade <= 4:
            a = random.randint(10, 500)
            b = random.randint(2, 50)
        else:
            a = random.randint(50, 5000)
            b = random.randint(5, 200)

        if op == "+":
            answer = a + b
        elif op == "-":
            if b > a:
                a, b = b, a
            answer = a - b
        else:
            answer = a * b

        stem = f"Calculate: {a} {op} {b} = ?"
        d1 = answer + random.choice([1, -1, 2, -2])
        d2 = answer + random.choice([10, -10, 5, -5])
        d3 = answer + random.choice([11, -11, 3, -3])
        distractors = make_distinct_distractors_from_list(answer, [d1, d2, d3])
        choices, correct_idx = build_choices(str(answer), [str(d) for d in distractors])

        q = build_question(
            qid=f"{curriculum}-G{grade}-{start_id + i:03d}",
            stem=stem,
            choices=choices,
            correct_answer=correct_idx,
            difficulty_score=diff_score,
            difficulty_tier=tier,
            chapter=chapter,
            topic=topic,
            tags=["arithmetic"],
            irt=irt,
            hint={
                "level_0": f"This is a basic {op} problem.",
                "level_1": f"Compute {a} {op} {b} step by step.",
                "level_2": f"The answer is {answer}."
            },
            diagnostics={"1": "Calculation error", "2": "Wrong operation", "3": "Place value mistake"},
            solution_steps=[
                f"Compute {a} {op} {b}",
                "Work column by column if needed",
                f"= {answer}"
            ]
        )
        questions.append(q)
    return questions


# --- Helper functions ---

def get_spread_difficulty(index, total, grade):
    """Spread difficulty scores across the grade's range."""
    low = (grade - 1) * 50 + 1
    high = grade * 50
    if total <= 1:
        return (low + high) // 2
    step = (high - low) / (total - 1) if total > 1 else 0
    return int(low + step * index)


def make_distinct_distractors(answer, lo, hi, count):
    """Generate distinct numeric distractors different from answer."""
    distractors = set()
    attempts = 0
    while len(distractors) < count and attempts < 100:
        d = random.randint(lo, hi)
        if d != answer:
            distractors.add(d)
        attempts += 1
    result = list(distractors)
    while len(result) < count:
        result.append(answer + len(result) + 1)
    return result[:count]


def make_distinct_distractors_from_list(answer, candidates):
    """Pick up to 3 distinct distractors from candidates, ensuring != answer."""
    result = []
    seen = {answer}
    for c in candidates:
        c = abs(int(c)) if c < 0 and answer >= 0 else int(c)
        if c not in seen and c != answer:
            result.append(c)
            seen.add(c)
    # Fill if needed
    attempts = 0
    while len(result) < 3 and attempts < 50:
        offset = random.choice([1, 2, 3, 5, 7, 10, -1, -2, -3, -5])
        candidate = answer + offset
        if candidate not in seen and candidate > 0:
            result.append(candidate)
            seen.add(candidate)
        attempts += 1
    return result[:3]


def build_choices(correct, distractors):
    """Shuffle choices and return (choices_list, correct_index)."""
    options = [correct] + distractors[:3]
    # Ensure exactly 4
    while len(options) < 4:
        options.append(correct + " (alt)")
    # Shuffle
    indices = list(range(4))
    random.shuffle(indices)
    shuffled = [options[i] for i in indices]
    correct_idx = shuffled.index(correct)
    return shuffled, correct_idx


def build_question(qid, stem, choices, correct_answer, difficulty_score,
                   difficulty_tier, chapter, topic, tags, irt, hint,
                   diagnostics, solution_steps):
    """Build a question dict in the standard format."""
    return {
        "id": qid,
        "stem": stem,
        "choices": choices,
        "correct_answer": correct_answer,
        "difficulty_tier": difficulty_tier,
        "difficulty_score": difficulty_score,
        "visual_svg": None,
        "visual_alt": None,
        "diagnostics": diagnostics,
        "tags": tags,
        "topic": topic,
        "chapter": chapter,
        "hint": hint,
        "curriculum_tags": [],
        "irt_params": irt,
        "irt_a": irt["a"],
        "irt_b": irt["b"],
        "irt_c": irt["c"],
        "solution_steps": solution_steps
    }


# --- Chapter to generator mapping ---

def get_generator_for_chapter(chapter_name):
    """Map chapter name to appropriate generator function."""
    ch_lower = chapter_name.lower()

    if any(k in ch_lower for k in ["number", "place value", "counting"]):
        return gen_numbers_questions
    elif "addition" in ch_lower and "subtraction" in ch_lower:
        return gen_addition_subtraction_questions
    elif "addition" in ch_lower:
        return gen_addition_subtraction_questions
    elif "subtraction" in ch_lower:
        return gen_addition_subtraction_questions
    elif "multiplication" in ch_lower and "division" in ch_lower:
        return gen_multiplication_questions
    elif "multiplication" in ch_lower:
        return gen_multiplication_questions
    elif "division" in ch_lower:
        return gen_division_questions
    elif "fraction" in ch_lower or "decimal" in ch_lower:
        return gen_fractions_questions
    elif "money" in ch_lower:
        return gen_money_questions
    elif "measurement" in ch_lower or "weight" in ch_lower or "capacity" in ch_lower or "length" in ch_lower:
        return gen_measurement_questions
    elif "time" in ch_lower:
        return gen_time_questions
    elif "geometry" in ch_lower or "shape" in ch_lower:
        return gen_geometry_questions
    elif "data" in ch_lower or "handling" in ch_lower or "statistics" in ch_lower:
        return gen_data_handling_questions
    elif "pattern" in ch_lower:
        return gen_patterns_questions
    elif "area" in ch_lower:
        return gen_area_questions
    elif "symmetry" in ch_lower:
        return gen_symmetry_questions
    else:
        return gen_generic_arithmetic_questions


# --- Main processing ---

def process_file(curriculum, grade, filepath):
    """Process a single content file, generate questions for chapters < 50."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    questions = data['questions']

    # Count per chapter
    chapter_counts = {}
    chapter_topics = {}
    for q in questions:
        ch = q.get('chapter', '')
        chapter_counts[ch] = chapter_counts.get(ch, 0) + 1
        if ch not in chapter_topics:
            t = q.get('topic')
            if t:
                chapter_topics[ch] = t

    # Find max existing ID number for this curriculum+grade
    max_id_num = 0
    prefix = f"{curriculum}-G{grade}-"
    for q in questions:
        qid = q.get('id', '')
        if qid.startswith(prefix):
            try:
                num = int(qid[len(prefix):])
                max_id_num = max(max_id_num, num)
            except ValueError:
                pass

    next_id = max_id_num + 1
    total_generated = 0
    chapter_report = []

    for chapter, count in sorted(chapter_counts.items()):
        if count >= TARGET_MIN:
            continue

        needed = TARGET_MIN - count
        topic = chapter_topics.get(chapter)
        # For ICSE which may have None topics, generate a sensible one
        if not topic:
            topic = f"{curriculum.lower()}_g{grade}_{chapter.lower().replace(' ', '_').replace(':', '').replace(',', '')}"

        generator = get_generator_for_chapter(chapter)
        new_questions = generator(grade, chapter, topic, needed, next_id, curriculum)

        questions.extend(new_questions)
        next_id += needed
        total_generated += needed
        chapter_report.append((chapter, count, needed))

    if total_generated > 0:
        data['questions'] = questions
        data['total_questions'] = len(questions)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return total_generated, chapter_report


def main():
    files = get_content_files()
    grand_total = 0
    print("=" * 70)
    print("SCALING CURRICULUM CONTENT TO 50 QUESTIONS PER CHAPTER")
    print("=" * 70)

    for curriculum, grade, filepath in files:
        generated, report = process_file(curriculum, grade, filepath)
        if generated > 0:
            print(f"\n{curriculum} Grade {grade} ({filepath.name}):")
            print(f"  Generated {generated} new questions across {len(report)} chapters:")
            for chapter, had, added in report:
                print(f"    {chapter}: {had} -> {had + added} (+{added})")
            grand_total += generated
        else:
            print(f"\n{curriculum} Grade {grade}: All chapters already have 50+ questions.")

    print("\n" + "=" * 70)
    print(f"TOTAL QUESTIONS GENERATED: {grand_total}")
    print("=" * 70)


if __name__ == "__main__":
    main()
