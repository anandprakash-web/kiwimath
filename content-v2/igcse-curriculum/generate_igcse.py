#!/usr/bin/env python3
"""Generate IGCSE curriculum content for Grades 1-6 for KiwiMath app."""

import json
import os
import random
import math

random.seed(42)

OUTPUT_DIR = "/sessions/optimistic-laughing-franklin/mnt/Downloads/kiwimath/content-v2/igcse-curriculum"

INDIAN_NAMES = ["Aarav", "Priya", "Riya", "Kabir", "Ananya", "Arjun", "Meera", "Vivaan", "Ishaan", "Diya", "Aanya", "Rohan", "Saanvi", "Advait", "Zara", "Vihaan", "Kiara", "Aditya", "Nisha", "Reyansh"]

CHAPTERS = {
    1: [
        ("Ch1: Counting and Numbers (1-20)", "counting_numbers"),
        ("Ch2: Place Value", "place_value"),
        ("Ch3: Addition (within 20)", "addition"),
        ("Ch4: Subtraction (within 20)", "subtraction"),
        ("Ch5: Shapes and Patterns", "shapes_patterns"),
        ("Ch6: Length and Height", "length_height"),
        ("Ch7: Weight and Capacity", "weight_capacity"),
        ("Ch8: Time", "time"),
        ("Ch9: Money", "money"),
        ("Ch10: Data Handling", "data_handling"),
        ("Ch11: Position and Direction", "position_direction"),
        ("Ch12: Doubling and Halving", "doubling_halving"),
    ],
    2: [
        ("Ch1: Numbers to 100", "numbers_100"),
        ("Ch2: Place Value and Ordering", "place_value_ordering"),
        ("Ch3: Addition (2-digit)", "addition_2digit"),
        ("Ch4: Subtraction (2-digit)", "subtraction_2digit"),
        ("Ch5: Multiplication (2, 5, 10 tables)", "multiplication"),
        ("Ch6: Division", "division"),
        ("Ch7: Fractions (halves, quarters)", "fractions"),
        ("Ch8: 2D and 3D Shapes", "shapes"),
        ("Ch9: Measurement", "measurement"),
        ("Ch10: Time", "time"),
        ("Ch11: Data Handling", "data_handling"),
        ("Ch12: Position and Movement", "position_movement"),
    ],
    3: [
        ("Ch1: Numbers to 1000", "numbers_1000"),
        ("Ch2: Place Value", "place_value"),
        ("Ch3: Addition and Subtraction (3-digit)", "add_sub_3digit"),
        ("Ch4: Multiplication (2-10 tables)", "multiplication"),
        ("Ch5: Division", "division"),
        ("Ch6: Fractions", "fractions"),
        ("Ch7: Money", "money"),
        ("Ch8: Measurement", "measurement"),
        ("Ch9: Time", "time"),
        ("Ch10: Geometry", "geometry"),
        ("Ch11: Data Handling", "data_handling"),
        ("Ch12: Symmetry", "symmetry"),
    ],
    4: [
        ("Ch1: Numbers to 10000", "numbers_10000"),
        ("Ch2: Place Value and Rounding", "place_value_rounding"),
        ("Ch3: Addition and Subtraction", "add_sub"),
        ("Ch4: Multiplication", "multiplication"),
        ("Ch5: Division", "division"),
        ("Ch6: Fractions and Decimals", "fractions_decimals"),
        ("Ch7: Measurement", "measurement"),
        ("Ch8: Perimeter and Area", "perimeter_area"),
        ("Ch9: Time", "time"),
        ("Ch10: Geometry and Angles", "geometry_angles"),
        ("Ch11: Data Handling", "data_handling"),
        ("Ch12: Coordinates", "coordinates"),
    ],
    5: [
        ("Ch1: Large Numbers", "large_numbers"),
        ("Ch2: Decimals", "decimals"),
        ("Ch3: Fractions", "fractions"),
        ("Ch4: Percentages", "percentages"),
        ("Ch5: Addition and Subtraction", "add_sub"),
        ("Ch6: Multiplication and Division", "mult_div"),
        ("Ch7: Ratio and Proportion", "ratio_proportion"),
        ("Ch8: Geometry", "geometry"),
        ("Ch9: Measurement and Area", "measurement_area"),
        ("Ch10: Data Handling", "data_handling"),
        ("Ch11: Algebra Basics", "algebra_basics"),
        ("Ch12: Problem Solving", "problem_solving"),
    ],
    6: [
        ("Ch1: Integers and Number Properties", "integers_properties"),
        ("Ch2: Fractions, Decimals, Percentages", "frac_dec_pct"),
        ("Ch3: Ratio and Proportion", "ratio_proportion"),
        ("Ch4: Algebra", "algebra"),
        ("Ch5: Equations", "equations"),
        ("Ch6: Geometry", "geometry"),
        ("Ch7: Transformations", "transformations"),
        ("Ch8: Measurement", "measurement"),
        ("Ch9: Area and Volume", "area_volume"),
        ("Ch10: Statistics", "statistics"),
        ("Ch11: Probability", "probability"),
        ("Ch12: Problem Solving", "problem_solving"),
    ],
}

def get_difficulty(idx, total):
    """Get difficulty tier and score based on position."""
    score = max(1, min(100, int((idx / (total - 1)) * 99) + 1)) if total > 1 else 50
    if score <= 20:
        tier = "easy"
    elif score <= 40:
        tier = "medium"
    elif score <= 60:
        tier = "hard"
    elif score <= 80:
        tier = "advanced"
    else:
        tier = "expert"
    return tier, score

def get_irt_params(difficulty_score):
    """Generate IRT parameters correlated with difficulty."""
    b = -3.0 + (difficulty_score / 100.0) * 6.0  # maps 1-100 to -3 to +3
    a = round(random.uniform(0.8, 1.5), 2)
    b = round(b, 2)
    return a, b, 0.25

def name():
    return random.choice(INDIAN_NAMES)

def generate_grade1_questions():
    """Generate 200 questions for Grade 1."""
    questions = []
    chapters = CHAPTERS[1]
    qs_per_chapter = [17, 17, 17, 17, 16, 16, 17, 17, 16, 17, 16, 17]

    q_idx = 0
    for ch_idx, (ch_name, ch_slug) in enumerate(chapters):
        num_qs = qs_per_chapter[ch_idx]
        for i in range(num_qs):
            q_idx += 1
            tier, score = get_difficulty(i, num_qs)
            a, b, c = get_irt_params(score)

            if ch_slug == "counting_numbers":
                q = _g1_counting(i, num_qs)
            elif ch_slug == "place_value":
                q = _g1_place_value(i, num_qs)
            elif ch_slug == "addition":
                q = _g1_addition(i, num_qs)
            elif ch_slug == "subtraction":
                q = _g1_subtraction(i, num_qs)
            elif ch_slug == "shapes_patterns":
                q = _g1_shapes(i, num_qs)
            elif ch_slug == "length_height":
                q = _g1_length(i, num_qs)
            elif ch_slug == "weight_capacity":
                q = _g1_weight(i, num_qs)
            elif ch_slug == "time":
                q = _g1_time(i, num_qs)
            elif ch_slug == "money":
                q = _g1_money(i, num_qs)
            elif ch_slug == "data_handling":
                q = _g1_data(i, num_qs)
            elif ch_slug == "position_direction":
                q = _g1_position(i, num_qs)
            elif ch_slug == "doubling_halving":
                q = _g1_doubling(i, num_qs)

            question = {
                "id": f"IGCSE-G1-{q_idx:03d}",
                "stem": q["stem"],
                "choices": q["choices"],
                "correct_answer": q["correct_answer"],
                "difficulty_tier": tier,
                "difficulty_score": score,
                "visual_svg": None,
                "visual_alt": None,
                "diagnostics": q["diagnostics"],
                "tags": q.get("tags", [ch_slug, "grade1"]),
                "topic": f"igcse_g1_{ch_slug}",
                "chapter": ch_name,
                "hint": q["hint"],
                "curriculum_tags": [f"IGCSE_1_{ch_idx+1}"],
                "irt_params": {"a": a, "b": b, "c": c},
                "irt_a": a,
                "irt_b": b,
                "irt_c": c,
            }
            questions.append(question)

    return questions

# Grade 1 question generators
def _g1_counting(i, total):
    difficulty = i / max(total - 1, 1)
    if difficulty < 0.3:
        n = random.randint(1, 10)
        stem = f"What number comes after {n}?"
        correct = n + 1
        wrong = [n - 1 if n > 1 else n + 2, n + 2, n]
        choices = [str(correct), str(wrong[0]), str(wrong[1]), str(wrong[2])]
        random.shuffle(choices)
        correct_idx = choices.index(str(correct))
    elif difficulty < 0.6:
        n = random.randint(5, 18)
        stem = f"What number comes before {n}?"
        correct = n - 1
        wrong = [n + 1, n - 2 if n > 2 else n + 2, n]
        choices = [str(correct), str(wrong[0]), str(wrong[1]), str(wrong[2])]
        random.shuffle(choices)
        correct_idx = choices.index(str(correct))
    else:
        start = random.randint(3, 15)
        missing_pos = random.randint(1, 3)
        seq = [start + j for j in range(5)]
        answer = seq[missing_pos]
        display = [str(x) if j != missing_pos else "___" for j, x in enumerate(seq)]
        stem = f"Fill in the missing number: {', '.join(display)}"
        correct = answer
        wrong = [answer + 1, answer - 1 if answer > 1 else answer + 2, answer + 2]
        choices = [str(correct), str(wrong[0]), str(wrong[1]), str(wrong[2])]
        random.shuffle(choices)
        correct_idx = choices.index(str(correct))

    diag = _make_diagnostics(correct_idx, [
        "Remember to count forward, not backward.",
        "Count carefully - check the sequence again.",
        "Look at the pattern and count one by one."
    ])
    hint = {
        "level_0": "Think about counting in order.",
        "level_1": "Count on your fingers if it helps.",
        "level_2": f"The answer is {correct}. Count from the numbers given."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["counting", "numbers", "grade1"]}

def _g1_place_value(i, total):
    difficulty = i / max(total - 1, 1)
    if difficulty < 0.4:
        n = random.randint(11, 19)
        tens = n // 10
        ones = n % 10
        stem = f"How many ones are in the number {n}?"
        correct = ones
        wrong = [tens, n, ones + 1 if ones < 9 else ones - 1]
        choices = [str(correct), str(wrong[0]), str(wrong[1]), str(wrong[2])]
        random.shuffle(choices)
        correct_idx = choices.index(str(correct))
    else:
        n = random.randint(11, 19)
        tens = n // 10
        ones = n % 10
        stem = f"The number {n} has ___ ten(s) and ___ one(s). What goes in the blanks?"
        correct = f"{tens} ten and {ones} ones"
        w1 = f"{ones} tens and {tens} ones"
        w2 = f"{tens} tens and {tens} ones"
        w3 = f"{tens+1} ten and {ones-1 if ones>0 else ones+1} ones"
        choices = [correct, w1, w2, w3]
        random.shuffle(choices)
        correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Remember: the ones digit is on the right.",
        "Tens are on the left, ones on the right.",
        "Break the number into tens and ones carefully."
    ])
    hint = {
        "level_0": "Think about what each digit represents.",
        "level_1": "The right digit shows ones, the left shows tens.",
        "level_2": f"The number {n} = {tens} ten + {ones} ones."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["place_value", "grade1"]}

def _g1_addition(i, total):
    difficulty = i / max(total - 1, 1)
    if difficulty < 0.3:
        a_val = random.randint(1, 5)
        b_val = random.randint(1, 5)
    elif difficulty < 0.6:
        a_val = random.randint(3, 9)
        b_val = random.randint(3, 9)
        while a_val + b_val > 18:
            b_val = random.randint(3, 9)
    else:
        a_val = random.randint(7, 12)
        b_val = random.randint(5, 10)
        while a_val + b_val > 20:
            b_val = random.randint(5, 10)

    correct = a_val + b_val
    templates = [
        f"What is {a_val} + {b_val}?",
        f"{name()} has {a_val} apples and gets {b_val} more. How many apples does {name()} have now?",
        f"Add: {a_val} + {b_val} = ?",
        f"There are {a_val} birds on a tree. {b_val} more birds come. How many birds are there in all?",
    ]
    stem = random.choice(templates)
    wrong = [correct + 1, correct - 1 if correct > 1 else correct + 2, correct + 2]
    choices = [str(correct), str(wrong[0]), str(wrong[1]), str(wrong[2])]
    random.shuffle(choices)
    correct_idx = choices.index(str(correct))

    diag = _make_diagnostics(correct_idx, [
        "Try counting on from the bigger number.",
        "Use your fingers to add the two numbers.",
        "Check your addition carefully."
    ])
    hint = {
        "level_0": "Put the numbers together.",
        "level_1": f"Start at {a_val} and count up {b_val} more.",
        "level_2": f"{a_val} + {b_val} = {correct}"
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["addition", "grade1"]}

def _g1_subtraction(i, total):
    difficulty = i / max(total - 1, 1)
    if difficulty < 0.3:
        a_val = random.randint(3, 10)
        b_val = random.randint(1, a_val - 1)
    elif difficulty < 0.6:
        a_val = random.randint(8, 15)
        b_val = random.randint(3, a_val - 1)
    else:
        a_val = random.randint(12, 20)
        b_val = random.randint(5, a_val - 1)

    correct = a_val - b_val
    templates = [
        f"What is {a_val} - {b_val}?",
        f"{name()} has {a_val} sweets. She gives away {b_val}. How many are left?",
        f"Subtract: {a_val} - {b_val} = ?",
        f"There are {a_val} balloons. {b_val} pop. How many are left?",
    ]
    stem = random.choice(templates)
    wrong = [correct + 1, correct - 1 if correct > 0 else correct + 2, a_val + b_val]
    choices = [str(correct), str(wrong[0]), str(wrong[1]), str(wrong[2])]
    random.shuffle(choices)
    correct_idx = choices.index(str(correct))

    diag = _make_diagnostics(correct_idx, [
        "Count backward from the bigger number.",
        "Subtraction means taking away.",
        "Try again - count how many are left."
    ])
    hint = {
        "level_0": "Take away means subtract.",
        "level_1": f"Start at {a_val} and count back {b_val}.",
        "level_2": f"{a_val} - {b_val} = {correct}"
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["subtraction", "grade1"]}

def _g1_shapes(i, total):
    shapes_info = [
        ("circle", "0", "round"),
        ("square", "4", "4 equal sides"),
        ("triangle", "3", "3 sides"),
        ("rectangle", "4", "2 long and 2 short sides"),
    ]
    difficulty = i / max(total - 1, 1)
    if difficulty < 0.5:
        shape = random.choice(shapes_info)
        stem = f"How many sides does a {shape[0]} have?"
        correct = shape[1]
        all_options = ["0", "3", "4", "5", "6"]
        wrong = [x for x in all_options if x != correct][:3]
        choices = [correct] + wrong
        random.shuffle(choices)
        correct_idx = choices.index(correct)
    else:
        patterns = [
            ("circle, square, circle, square, circle, ___", "square", ["circle", "triangle", "rectangle"]),
            ("red, blue, red, blue, red, ___", "blue", ["red", "green", "yellow"]),
            ("1, 2, 1, 2, 1, ___", "2", ["1", "3", "4"]),
            ("triangle, triangle, square, triangle, triangle, ___", "square", ["triangle", "circle", "rectangle"]),
        ]
        pat = random.choice(patterns)
        stem = f"What comes next in the pattern? {pat[0]}"
        correct = pat[1]
        wrong = pat[2]
        choices = [correct] + wrong
        random.shuffle(choices)
        correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Look at the shape carefully and count the sides.",
        "Think about the repeating pattern.",
        "Compare with shapes you know."
    ])
    hint = {
        "level_0": "Think about the properties of each shape.",
        "level_1": "A triangle has 3 sides, a square has 4, a circle has 0.",
        "level_2": f"The correct answer is {correct}."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["shapes", "patterns", "grade1"]}

def _g1_length(i, total):
    difficulty = i / max(total - 1, 1)
    objects = [("pencil", "eraser"), ("ruler", "crayon"), ("book", "notebook"), ("rope", "ribbon")]
    obj = random.choice(objects)
    if difficulty < 0.5:
        stem = f"Which is longer: a {obj[0]} or an {obj[1]}?"
        correct = obj[0]
        choices = [obj[0], obj[1], "Both are equal", "Cannot tell"]
        correct_idx = 0
    else:
        lengths = sorted(random.sample(range(3, 18), 4))
        stem = f"Arrange from shortest to longest: {lengths[2]} cm, {lengths[0]} cm, {lengths[3]} cm, {lengths[1]} cm"
        correct = f"{lengths[0]}, {lengths[1]}, {lengths[2]}, {lengths[3]}"
        w1 = f"{lengths[3]}, {lengths[2]}, {lengths[1]}, {lengths[0]}"
        w2 = f"{lengths[1]}, {lengths[0]}, {lengths[3]}, {lengths[2]}"
        w3 = f"{lengths[0]}, {lengths[2]}, {lengths[1]}, {lengths[3]}"
        choices = [correct, w1, w2, w3]
        random.shuffle(choices)
        correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Compare the sizes carefully.",
        "Shorter means smaller length.",
        "Order from smallest number to largest."
    ])
    hint = {
        "level_0": "Think about which object is bigger.",
        "level_1": "Compare the numbers - smaller number means shorter.",
        "level_2": f"The correct answer is: {correct}"
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["length", "measurement", "grade1"]}

def _g1_weight(i, total):
    difficulty = i / max(total - 1, 1)
    if difficulty < 0.5:
        heavy = random.choice(["elephant", "car", "table", "refrigerator"])
        light = random.choice(["feather", "leaf", "pencil", "button"])
        stem = f"Which is heavier: a {heavy} or a {light}?"
        correct = heavy
        choices = [heavy, light, "Both weigh the same", "Cannot tell"]
        correct_idx = 0
    else:
        items = random.choice([
            ("bag of rice", "5 kg", "bottle of water", "1 kg"),
            ("watermelon", "3 kg", "apple", "200 g"),
            ("school bag", "4 kg", "pencil box", "500 g"),
        ])
        stem = f"A {items[0]} weighs {items[1]} and a {items[2]} weighs {items[3]}. Which is heavier?"
        correct = f"The {items[0]}"
        choices = [f"The {items[0]}", f"The {items[2]}", "Both are equal", "Cannot compare"]
        correct_idx = 0

    diag = _make_diagnostics(correct_idx, [
        "Think about which object feels heavier to lift.",
        "Compare the weights - bigger number means heavier.",
        "Remember: kg is more than g."
    ])
    hint = {
        "level_0": "Heavy objects are hard to lift.",
        "level_1": "Compare the weight numbers.",
        "level_2": f"The answer is: {correct}"
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["weight", "capacity", "grade1"]}

def _g1_time(i, total):
    difficulty = i / max(total - 1, 1)
    if difficulty < 0.4:
        hour = random.randint(1, 12)
        stem = f"What time does the clock show when the short hand points to {hour} and the long hand points to 12?"
        correct = f"{hour} o'clock"
        wrong_hours = random.sample([h for h in range(1, 13) if h != hour], 3)
        choices = [correct] + [f"{h} o'clock" for h in wrong_hours]
        random.shuffle(choices)
        correct_idx = choices.index(correct)
    else:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        idx_d = random.randint(0, 5)
        stem = f"What day comes after {days[idx_d]}?"
        correct = days[idx_d + 1]
        wrong = [d for d in days if d != correct and d != days[idx_d]][:3]
        choices = [correct] + wrong
        random.shuffle(choices)
        correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "The short hand shows the hour.",
        "Think about the days of the week in order.",
        "Remember the sequence carefully."
    ])
    hint = {
        "level_0": "Think about the clock or the calendar.",
        "level_1": "The short hand on a clock shows hours. Days go Mon, Tue, Wed...",
        "level_2": f"The correct answer is {correct}."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["time", "grade1"]}

def _g1_money(i, total):
    difficulty = i / max(total - 1, 1)
    if difficulty < 0.4:
        coins = [1, 2, 5, 10]
        c = random.choice(coins)
        stem = f"{name()} has a {c} rupee coin. How much money does he have?"
        correct = f"₹{c}"
        wrong = [f"₹{x}" for x in coins if x != c][:3]
        choices = [correct] + wrong
        random.shuffle(choices)
        correct_idx = choices.index(correct)
    else:
        a_val = random.choice([2, 5, 10])
        b_val = random.choice([1, 2, 5])
        while a_val + b_val > 15:
            b_val = random.choice([1, 2])
        total_val = a_val + b_val
        stem = f"{name()} has a ₹{a_val} coin and a ₹{b_val} coin. How much money does she have in total?"
        correct = f"₹{total_val}"
        wrong = [f"₹{total_val + 1}", f"₹{total_val - 1}", f"₹{a_val * b_val}"]
        choices = [correct] + wrong
        random.shuffle(choices)
        correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Add the values of all coins together.",
        "Each coin has a value printed on it.",
        "Count the rupees carefully."
    ])
    hint = {
        "level_0": "Add up all the coin values.",
        "level_1": "Put the coin values together using addition.",
        "level_2": f"The answer is {correct}."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["money", "rupees", "grade1"]}

def _g1_data(i, total):
    difficulty = i / max(total - 1, 1)
    fruits = ["apples", "bananas", "oranges", "mangoes"]
    counts = random.sample(range(2, 10), 4)
    max_fruit = fruits[counts.index(max(counts))]
    min_fruit = fruits[counts.index(min(counts))]

    if difficulty < 0.5:
        data_str = ", ".join([f"{fruits[j]}: {counts[j]}" for j in range(4)])
        stem = f"In a fruit basket there are {data_str}. Which fruit has the most?"
        correct = max_fruit
        wrong = [f for f in fruits if f != max_fruit][:3]
        choices = [correct] + wrong
        random.shuffle(choices)
        correct_idx = choices.index(correct)
    else:
        data_str = ", ".join([f"{fruits[j]}: {counts[j]}" for j in range(4)])
        stem = f"Fruits in a basket: {data_str}. How many more {max_fruit} than {min_fruit} are there?"
        diff = max(counts) - min(counts)
        correct = str(diff)
        wrong = [str(diff + 1), str(diff - 1) if diff > 1 else str(diff + 2), str(max(counts))]
        choices = [correct] + wrong
        random.shuffle(choices)
        correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Compare the numbers for each item.",
        "The biggest number means the most.",
        "Subtract to find how many more."
    ])
    hint = {
        "level_0": "Look at the numbers and compare.",
        "level_1": "Find the largest count for 'most', subtract for 'how many more'.",
        "level_2": f"The answer is {correct}."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["data_handling", "grade1"]}

def _g1_position(i, total):
    positions = ["left", "right", "above", "below", "between", "in front of", "behind"]
    difficulty = i / max(total - 1, 1)
    if difficulty < 0.5:
        pos = random.choice(["left", "right", "above", "below"])
        n = name()
        obj = random.choice(["table", "chair", "tree", "house"])
        stem = f"{n} is standing to the {pos} of the {obj}. Which direction is {n} from the {obj}?"
        correct = pos.capitalize()
        wrong = [p.capitalize() for p in positions if p != pos][:3]
        choices = [correct] + wrong
        random.shuffle(choices)
        correct_idx = choices.index(correct)
    else:
        n1, n2, n3 = random.sample(INDIAN_NAMES, 3)
        stem = f"{n1} is standing between {n2} and {n3}. Who is in the middle?"
        correct = n1
        choices = [n1, n2, n3, "None of them"]
        random.shuffle(choices)
        correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Think about where things are placed.",
        "'Between' means in the middle of two things.",
        "Read the question again carefully."
    ])
    hint = {
        "level_0": "Think about positions and directions.",
        "level_1": "Left, right, above, below - picture it in your mind.",
        "level_2": f"The answer is {correct}."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["position", "direction", "grade1"]}

def _g1_doubling(i, total):
    difficulty = i / max(total - 1, 1)
    if difficulty < 0.5:
        n = random.randint(1, 10)
        doubled = n * 2
        stem = f"What is double of {n}?"
        correct = str(doubled)
        wrong = [str(doubled + 1), str(doubled - 1) if doubled > 1 else str(doubled + 2), str(n)]
        choices = [correct] + wrong
        random.shuffle(choices)
        correct_idx = choices.index(correct)
    else:
        n = random.choice([2, 4, 6, 8, 10, 12, 14, 16, 18, 20])
        halved = n // 2
        stem = f"What is half of {n}?"
        correct = str(halved)
        wrong = [str(halved + 1), str(halved - 1) if halved > 0 else str(halved + 2), str(n)]
        choices = [correct] + wrong
        random.shuffle(choices)
        correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Double means multiply by 2.",
        "Half means divide by 2.",
        "Think of splitting into two equal groups."
    ])
    hint = {
        "level_0": "Double = add the number to itself. Half = split in two.",
        "level_1": f"Double of {n if difficulty < 0.5 else ''} means {n}+{n}. Half means ÷2.",
        "level_2": f"The answer is {correct}."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": ["doubling", "halving", "grade1"]}


# =========== Grade 2 ===========
def generate_grade2_questions():
    questions = []
    chapters = CHAPTERS[2]
    qs_per_chapter = distribute_questions(200, 12)

    q_idx = 0
    for ch_idx, (ch_name, ch_slug) in enumerate(chapters):
        num_qs = qs_per_chapter[ch_idx]
        for i in range(num_qs):
            q_idx += 1
            tier, score = get_difficulty(i, num_qs)
            a, b, c = get_irt_params(score)
            q = generate_g2_question(ch_slug, i, num_qs)

            question = {
                "id": f"IGCSE-G2-{q_idx:03d}",
                "stem": q["stem"],
                "choices": q["choices"],
                "correct_answer": q["correct_answer"],
                "difficulty_tier": tier,
                "difficulty_score": score,
                "visual_svg": None,
                "visual_alt": None,
                "diagnostics": q["diagnostics"],
                "tags": q.get("tags", [ch_slug, "grade2"]),
                "topic": f"igcse_g2_{ch_slug}",
                "chapter": ch_name,
                "hint": q["hint"],
                "curriculum_tags": [f"IGCSE_2_{ch_idx+1}"],
                "irt_params": {"a": a, "b": b, "c": c},
                "irt_a": a,
                "irt_b": b,
                "irt_c": c,
            }
            questions.append(question)
    return questions

def generate_g2_question(ch_slug, i, total):
    difficulty = i / max(total - 1, 1)

    if ch_slug == "numbers_100":
        n = random.randint(20, 99)
        if difficulty < 0.4:
            stem = f"What number comes after {n}?"
            correct = str(n + 1)
            wrong = [str(n - 1), str(n + 2), str(n + 10)]
        elif difficulty < 0.7:
            stem = f"Which number is greater: {n} or {n - random.randint(1, 15)}?"
            other = n - random.randint(1, 15)
            correct = str(n)
            wrong = [str(other), str(n + other), "They are equal"]
        else:
            nums = sorted(random.sample(range(10, 99), 4))
            stem = f"Arrange in ascending order: {nums[2]}, {nums[0]}, {nums[3]}, {nums[1]}"
            correct = f"{nums[0]}, {nums[1]}, {nums[2]}, {nums[3]}"
            wrong = [f"{nums[3]}, {nums[2]}, {nums[1]}, {nums[0]}",
                     f"{nums[0]}, {nums[2]}, {nums[1]}, {nums[3]}",
                     f"{nums[1]}, {nums[0]}, {nums[3]}, {nums[2]}"]

    elif ch_slug == "place_value_ordering":
        n = random.randint(21, 99)
        tens = n // 10
        ones = n % 10
        if difficulty < 0.5:
            stem = f"What is the tens digit of {n}?"
            correct = str(tens)
            wrong = [str(ones), str(tens + 1), str(n)]
        else:
            stem = f"Write {n} in expanded form."
            correct = f"{tens * 10} + {ones}"
            wrong = [f"{ones * 10} + {tens}", f"{tens} + {ones}", f"{n} + 0"]

    elif ch_slug == "addition_2digit":
        if difficulty < 0.3:
            a_val = random.randint(10, 30)
            b_val = random.randint(1, 9)
        elif difficulty < 0.6:
            a_val = random.randint(20, 50)
            b_val = random.randint(10, 30)
        else:
            a_val = random.randint(30, 60)
            b_val = random.randint(20, 40)
        correct_val = a_val + b_val
        n1 = name()
        templates = [
            f"What is {a_val} + {b_val}?",
            f"{n1} has {a_val} stickers and gets {b_val} more. How many stickers does {n1} have now?",
            f"Add {a_val} and {b_val}.",
        ]
        stem = random.choice(templates)
        correct = str(correct_val)
        wrong = [str(correct_val + 1), str(correct_val - 1), str(correct_val + 10)]

    elif ch_slug == "subtraction_2digit":
        if difficulty < 0.3:
            a_val = random.randint(15, 40)
            b_val = random.randint(1, 9)
        elif difficulty < 0.6:
            a_val = random.randint(30, 60)
            b_val = random.randint(10, 25)
        else:
            a_val = random.randint(50, 99)
            b_val = random.randint(20, 45)
        correct_val = a_val - b_val
        n1 = name()
        templates = [
            f"What is {a_val} - {b_val}?",
            f"{n1} had {a_val} marbles and gave away {b_val}. How many are left?",
            f"Subtract {b_val} from {a_val}.",
        ]
        stem = random.choice(templates)
        correct = str(correct_val)
        wrong = [str(correct_val + 1), str(correct_val - 1), str(a_val + b_val)]

    elif ch_slug == "multiplication":
        table = random.choice([2, 5, 10])
        mult = random.randint(1, 10)
        correct_val = table * mult
        if difficulty < 0.5:
            stem = f"What is {table} × {mult}?"
        else:
            n1 = name()
            stem = f"{n1} has {mult} bags with {table} pencils in each bag. How many pencils in total?"
        correct = str(correct_val)
        wrong = [str(correct_val + table), str(correct_val - table), str(table + mult)]

    elif ch_slug == "division":
        divisor = random.choice([2, 5, 10])
        quotient = random.randint(1, 10)
        dividend = divisor * quotient
        if difficulty < 0.5:
            stem = f"What is {dividend} ÷ {divisor}?"
        else:
            n1 = name()
            stem = f"{n1} shares {dividend} sweets equally among {divisor} friends. How many does each get?"
        correct = str(quotient)
        wrong = [str(quotient + 1), str(quotient - 1) if quotient > 1 else str(quotient + 2), str(divisor)]

    elif ch_slug == "fractions":
        if difficulty < 0.5:
            stem = f"What is half of {random.choice([4, 6, 8, 10, 12])}?"
            n = random.choice([4, 6, 8, 10, 12])
            stem = f"What is half of {n}?"
            correct = str(n // 2)
            wrong = [str(n // 2 + 1), str(n // 2 - 1) if n // 2 > 1 else str(n // 2 + 2), str(n)]
        else:
            n = random.choice([4, 8, 12, 16, 20])
            stem = f"What is one quarter of {n}?"
            correct = str(n // 4)
            wrong = [str(n // 4 + 1), str(n // 2), str(n // 4 - 1) if n // 4 > 1 else str(n // 4 + 2)]

    elif ch_slug == "shapes":
        shapes_3d = [("cube", "6 faces"), ("cuboid", "6 faces"), ("sphere", "0 flat faces"), ("cylinder", "2 flat faces"), ("cone", "1 flat face")]
        shapes_2d = [("circle", "0 corners"), ("triangle", "3 corners"), ("square", "4 corners"), ("pentagon", "5 corners")]
        if difficulty < 0.5:
            s = random.choice(shapes_2d)
            stem = f"How many corners does a {s[0]} have?"
            correct = s[1].split()[0]
            all_nums = ["0", "3", "4", "5", "6"]
            wrong = [x for x in all_nums if x != correct][:3]
        else:
            s = random.choice(shapes_3d)
            stem = f"How many flat faces does a {s[0]} have?"
            correct = s[1].split()[0]
            all_nums = ["0", "1", "2", "4", "6"]
            wrong = [x for x in all_nums if x != correct][:3]

    elif ch_slug == "measurement":
        if difficulty < 0.5:
            val = random.randint(10, 50)
            stem = f"A ribbon is {val} cm long. What is its length in cm?"
            correct = f"{val} cm"
            wrong = [f"{val + 10} cm", f"{val - 5} cm", f"{val * 2} cm"]
        else:
            val_m = random.randint(1, 5)
            stem = f"How many centimetres are in {val_m} metre(s)?"
            correct = str(val_m * 100)
            wrong = [str(val_m * 10), str(val_m * 1000), str(val_m * 50)]

    elif ch_slug == "time":
        if difficulty < 0.5:
            hour = random.randint(1, 12)
            stem = f"What time is half past {hour}?"
            correct = f"{hour}:30"
            wrong = [f"{hour}:00", f"{hour}:15", f"{hour}:45"]
        else:
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            idx_m = random.randint(0, 10)
            stem = f"Which month comes after {months[idx_m]}?"
            correct = months[idx_m + 1]
            wrong = [m for m in months if m != correct and m != months[idx_m]][:3]

    elif ch_slug == "data_handling":
        animals = ["dogs", "cats", "birds", "fish"]
        counts = random.sample(range(2, 12), 4)
        total_count = sum(counts)
        if difficulty < 0.5:
            data_str = ", ".join([f"{animals[j]}: {counts[j]}" for j in range(4)])
            stem = f"Pets owned by children: {data_str}. How many pets in total?"
            correct = str(total_count)
            wrong = [str(total_count + 1), str(total_count - 1), str(max(counts))]
        else:
            data_str = ", ".join([f"{animals[j]}: {counts[j]}" for j in range(4)])
            most = animals[counts.index(max(counts))]
            stem = f"Pets: {data_str}. Which pet is most popular?"
            correct = most
            wrong = [a for a in animals if a != most][:3]

    elif ch_slug == "position_movement":
        if difficulty < 0.5:
            turns = ["quarter turn", "half turn", "three-quarter turn", "full turn"]
            t = random.choice(turns)
            degrees = {"quarter turn": "90", "half turn": "180", "three-quarter turn": "270", "full turn": "360"}
            stem = f"How many degrees is a {t}?"
            correct = degrees[t]
            wrong = [d for d in degrees.values() if d != correct][:3]
        else:
            stem = f"If you face North and turn right, which direction do you face?"
            correct = "East"
            wrong = ["West", "South", "North"]

    else:
        stem = f"What is 10 + 10?"
        correct = "20"
        wrong = ["15", "25", "10"]

    choices = [correct] + wrong
    random.shuffle(choices)
    correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Check your calculation again.",
        "Read the question carefully.",
        "Think step by step."
    ])
    hint = {
        "level_0": "Read the question and think about what operation to use.",
        "level_1": "Break the problem into smaller steps.",
        "level_2": f"The correct answer is {correct}."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": [ch_slug, "grade2"]}


# =========== Grade 3 ===========
def generate_grade3_questions():
    questions = []
    chapters = CHAPTERS[3]
    qs_per_chapter = distribute_questions(200, 12)

    q_idx = 0
    for ch_idx, (ch_name, ch_slug) in enumerate(chapters):
        num_qs = qs_per_chapter[ch_idx]
        for i in range(num_qs):
            q_idx += 1
            tier, score = get_difficulty(i, num_qs)
            a, b, c = get_irt_params(score)
            q = generate_g3_question(ch_slug, i, num_qs)

            question = {
                "id": f"IGCSE-G3-{q_idx:03d}",
                "stem": q["stem"],
                "choices": q["choices"],
                "correct_answer": q["correct_answer"],
                "difficulty_tier": tier,
                "difficulty_score": score,
                "visual_svg": None,
                "visual_alt": None,
                "diagnostics": q["diagnostics"],
                "tags": q.get("tags", [ch_slug, "grade3"]),
                "topic": f"igcse_g3_{ch_slug}",
                "chapter": ch_name,
                "hint": q["hint"],
                "curriculum_tags": [f"IGCSE_3_{ch_idx+1}"],
                "irt_params": {"a": a, "b": b, "c": c},
                "irt_a": a,
                "irt_b": b,
                "irt_c": c,
            }
            questions.append(question)
    return questions

def generate_g3_question(ch_slug, i, total):
    difficulty = i / max(total - 1, 1)

    if ch_slug == "numbers_1000":
        n = random.randint(100, 999)
        if difficulty < 0.4:
            stem = f"What number comes after {n}?"
            correct = str(n + 1)
            wrong = [str(n - 1), str(n + 10), str(n + 2)]
        elif difficulty < 0.7:
            stem = f"Round {n} to the nearest hundred."
            rounded = round(n, -2)
            correct = str(rounded)
            others = [rounded - 100, rounded + 100, n]
            wrong = [str(int(x)) for x in others if x != rounded][:3]
        else:
            nums = sorted(random.sample(range(100, 999), 4))
            stem = f"Which is the smallest: {nums[2]}, {nums[0]}, {nums[3]}, {nums[1]}?"
            correct = str(nums[0])
            wrong = [str(nums[1]), str(nums[2]), str(nums[3])]

    elif ch_slug == "place_value":
        n = random.randint(100, 999)
        h = n // 100
        t = (n % 100) // 10
        o = n % 10
        if difficulty < 0.5:
            stem = f"What is the value of the digit {h} in {n}?"
            correct = str(h * 100)
            wrong = [str(h), str(h * 10), str(n)]
        else:
            stem = f"Write {n} in expanded form."
            correct = f"{h*100} + {t*10} + {o}"
            wrong = [f"{h} + {t} + {o}", f"{h*10} + {t*100} + {o}", f"{h*100} + {t} + {o*10}"]

    elif ch_slug == "add_sub_3digit":
        if difficulty < 0.4:
            a_val = random.randint(100, 400)
            b_val = random.randint(10, 99)
            op = random.choice(["+", "-"])
        elif difficulty < 0.7:
            a_val = random.randint(200, 600)
            b_val = random.randint(100, 300)
            op = random.choice(["+", "-"])
        else:
            a_val = random.randint(300, 700)
            b_val = random.randint(200, 400)
            op = random.choice(["+", "-"])

        if op == "-" and b_val > a_val:
            a_val, b_val = b_val, a_val

        correct_val = a_val + b_val if op == "+" else a_val - b_val
        n1 = name()
        if op == "+":
            stem = random.choice([
                f"What is {a_val} + {b_val}?",
                f"{n1} saved ₹{a_val} and then earned ₹{b_val} more. How much does {n1} have now?"
            ])
        else:
            stem = random.choice([
                f"What is {a_val} - {b_val}?",
                f"{n1} had ₹{a_val} and spent ₹{b_val}. How much is left?"
            ])
        correct = str(correct_val)
        wrong = [str(correct_val + 1), str(correct_val - 1), str(correct_val + 10)]

    elif ch_slug == "multiplication":
        table = random.randint(2, 10)
        mult = random.randint(2, 10)
        correct_val = table * mult
        if difficulty < 0.5:
            stem = f"What is {table} × {mult}?"
        else:
            n1 = name()
            stem = f"{n1} buys {mult} packs of pencils. Each pack has {table} pencils. How many pencils in total?"
        correct = str(correct_val)
        wrong = [str(correct_val + table), str(correct_val - table), str(table + mult)]

    elif ch_slug == "division":
        divisor = random.randint(2, 10)
        quotient = random.randint(2, 10)
        dividend = divisor * quotient
        if difficulty < 0.5:
            stem = f"What is {dividend} ÷ {divisor}?"
        else:
            n1 = name()
            stem = f"{n1} distributes {dividend} toffees equally among {divisor} children. How many does each child get?"
        correct = str(quotient)
        wrong = [str(quotient + 1), str(quotient - 1) if quotient > 1 else str(quotient + 2), str(divisor)]

    elif ch_slug == "fractions":
        if difficulty < 0.4:
            whole = random.choice([6, 8, 9, 10, 12])
            frac = random.choice([2, 3])
            result = whole // frac
            stem = f"What is 1/{frac} of {whole}?"
            correct = str(result)
            wrong = [str(result + 1), str(result - 1) if result > 1 else str(result + 2), str(whole)]
        elif difficulty < 0.7:
            num = random.randint(1, 5)
            den = random.choice([2, 3, 4, 5, 6])
            while num >= den:
                num = random.randint(1, den - 1)
            stem = f"Which fraction is larger: {num}/{den} or {num + 1}/{den}?"
            correct = f"{num + 1}/{den}"
            wrong = [f"{num}/{den}", "They are equal", f"{num}/{den + 1}"]
        else:
            n1 = name()
            total_items = random.choice([12, 15, 18, 20, 24])
            frac_of = random.choice([2, 3, 4])
            result = total_items // frac_of
            stem = f"{n1} ate 1/{frac_of} of {total_items} biscuits. How many did {n1} eat?"
            correct = str(result)
            wrong = [str(result + 1), str(total_items - result), str(frac_of)]

    elif ch_slug == "money":
        if difficulty < 0.4:
            price = random.randint(5, 30)
            paid = price + random.choice([5, 10, 20])
            change = paid - price
            stem = f"{name()} buys a toy for ₹{price} and pays ₹{paid}. What change does he get?"
            correct = f"₹{change}"
            wrong = [f"₹{change + 5}", f"₹{change - 5}" if change > 5 else f"₹{change + 10}", f"₹{paid}"]
        else:
            items = random.sample(range(10, 50), 3)
            total_val = sum(items)
            stem = f"{name()} buys items costing ₹{items[0]}, ₹{items[1]} and ₹{items[2]}. What is the total cost?"
            correct = f"₹{total_val}"
            wrong = [f"₹{total_val + 10}", f"₹{total_val - 5}", f"₹{max(items)}"]

    elif ch_slug == "measurement":
        if difficulty < 0.5:
            km = random.randint(1, 5)
            stem = f"How many metres are in {km} km?"
            correct = str(km * 1000)
            wrong = [str(km * 100), str(km * 10000), str(km * 500)]
        else:
            kg = random.randint(1, 5)
            stem = f"How many grams are in {kg} kg?"
            correct = str(kg * 1000)
            wrong = [str(kg * 100), str(kg * 10), str(kg * 500)]

    elif ch_slug == "time":
        if difficulty < 0.5:
            hours = random.randint(1, 5)
            stem = f"How many minutes are in {hours} hour(s)?"
            correct = str(hours * 60)
            wrong = [str(hours * 30), str(hours * 100), str(hours * 45)]
        else:
            start_h = random.randint(8, 14)
            duration = random.randint(1, 4)
            end_h = start_h + duration
            stem = f"A class starts at {start_h}:00 and lasts {duration} hours. When does it end?"
            correct = f"{end_h}:00"
            wrong = [f"{end_h + 1}:00", f"{start_h + duration - 1}:00", f"{start_h}:{duration}0"]

    elif ch_slug == "geometry":
        shapes = [("triangle", 3), ("quadrilateral", 4), ("pentagon", 5), ("hexagon", 6)]
        if difficulty < 0.5:
            s = random.choice(shapes)
            stem = f"How many sides does a {s[0]} have?"
            correct = str(s[1])
            wrong = [str(s[1] + 1), str(s[1] - 1), str(s[1] + 2)]
        else:
            stem = "What is the sum of angles in a triangle?"
            correct = "180°"
            wrong = ["90°", "360°", "270°"]

    elif ch_slug == "data_handling":
        subjects = ["Maths", "English", "Science", "Hindi"]
        scores = random.sample(range(50, 100), 4)
        n1 = name()
        if difficulty < 0.5:
            data_str = ", ".join([f"{subjects[j]}: {scores[j]}" for j in range(4)])
            stem = f"{n1}'s marks: {data_str}. In which subject did {n1} score the highest?"
            correct = subjects[scores.index(max(scores))]
            wrong = [s for s in subjects if s != correct][:3]
        else:
            data_str = ", ".join([f"{subjects[j]}: {scores[j]}" for j in range(4)])
            total_s = sum(scores)
            stem = f"{n1}'s marks: {data_str}. What is the total of all marks?"
            correct = str(total_s)
            wrong = [str(total_s + 5), str(total_s - 5), str(max(scores))]

    elif ch_slug == "symmetry":
        if difficulty < 0.5:
            shapes_sym = [("square", "4"), ("rectangle", "2"), ("circle", "infinite"), ("equilateral triangle", "3")]
            s = random.choice(shapes_sym[:3])
            stem = f"How many lines of symmetry does a {s[0]} have?"
            correct = s[1]
            wrong_opts = ["0", "1", "2", "3", "4"]
            wrong = [w for w in wrong_opts if w != correct][:3]
        else:
            stem = "Which of these letters has a line of symmetry?"
            correct = "A"
            wrong = ["F", "G", "J"]

    else:
        stem = "What is 100 + 100?"
        correct = "200"
        wrong = ["150", "250", "100"]

    choices = [correct] + wrong
    random.shuffle(choices)
    correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Check your working step by step.",
        "Re-read the question carefully.",
        "Think about the method you used."
    ])
    hint = {
        "level_0": "Think about what the question is asking.",
        "level_1": "Break the problem into smaller parts.",
        "level_2": f"The correct answer is {correct}."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": [ch_slug, "grade3"]}


# =========== Grade 4 ===========
def generate_grade4_questions():
    questions = []
    chapters = CHAPTERS[4]
    qs_per_chapter = distribute_questions(200, 12)

    q_idx = 0
    for ch_idx, (ch_name, ch_slug) in enumerate(chapters):
        num_qs = qs_per_chapter[ch_idx]
        for i in range(num_qs):
            q_idx += 1
            tier, score = get_difficulty(i, num_qs)
            a, b, c = get_irt_params(score)
            q = generate_g4_question(ch_slug, i, num_qs)

            question = {
                "id": f"IGCSE-G4-{q_idx:03d}",
                "stem": q["stem"],
                "choices": q["choices"],
                "correct_answer": q["correct_answer"],
                "difficulty_tier": tier,
                "difficulty_score": score,
                "visual_svg": None,
                "visual_alt": None,
                "diagnostics": q["diagnostics"],
                "tags": q.get("tags", [ch_slug, "grade4"]),
                "topic": f"igcse_g4_{ch_slug}",
                "chapter": ch_name,
                "hint": q["hint"],
                "curriculum_tags": [f"IGCSE_4_{ch_idx+1}"],
                "irt_params": {"a": a, "b": b, "c": c},
                "irt_a": a,
                "irt_b": b,
                "irt_c": c,
            }
            questions.append(question)
    return questions

def generate_g4_question(ch_slug, i, total):
    difficulty = i / max(total - 1, 1)

    if ch_slug == "numbers_10000":
        n = random.randint(1000, 9999)
        if difficulty < 0.4:
            stem = f"Write {n} in words. How many thousands are there?"
            correct = str(n // 1000)
            wrong = [str(n // 100), str(n // 10), str((n // 1000) + 1)]
        elif difficulty < 0.7:
            stem = f"What is {n} rounded to the nearest thousand?"
            rounded = round(n, -3)
            correct = str(rounded)
            wrong = [str(rounded + 1000), str(rounded - 1000), str(round(n, -2))]
        else:
            nums = sorted(random.sample(range(1000, 9999), 4))
            stem = f"Arrange in descending order: {nums[1]}, {nums[3]}, {nums[0]}, {nums[2]}"
            correct = f"{nums[3]}, {nums[2]}, {nums[1]}, {nums[0]}"
            wrong = [f"{nums[0]}, {nums[1]}, {nums[2]}, {nums[3]}",
                     f"{nums[3]}, {nums[1]}, {nums[2]}, {nums[0]}",
                     f"{nums[2]}, {nums[3]}, {nums[0]}, {nums[1]}"]

    elif ch_slug == "place_value_rounding":
        n = random.randint(1000, 9999)
        if difficulty < 0.5:
            stem = f"Round {n} to the nearest hundred."
            rounded = round(n, -2)
            correct = str(rounded)
            wrong = [str(rounded + 100), str(rounded - 100), str(round(n, -3))]
        else:
            stem = f"What is the place value of {str(n)[1]} in {n}?"
            digit = int(str(n)[1])
            value = digit * 100
            correct = str(value)
            wrong = [str(digit), str(digit * 10), str(digit * 1000)]

    elif ch_slug == "add_sub":
        if difficulty < 0.4:
            a_val = random.randint(1000, 4000)
            b_val = random.randint(100, 999)
        else:
            a_val = random.randint(2000, 7000)
            b_val = random.randint(1000, 4000)
        op = random.choice(["+", "-"])
        if op == "-" and b_val > a_val:
            a_val, b_val = b_val, a_val
        correct_val = a_val + b_val if op == "+" else a_val - b_val
        n1 = name()
        if op == "+":
            stem = f"A school has {a_val} boys and {b_val} girls. How many students are there in total?"
        else:
            stem = f"{n1} had ₹{a_val} and spent ₹{b_val} on books. How much money is left?"
        correct = str(correct_val)
        wrong = [str(correct_val + 10), str(correct_val - 10), str(correct_val + 100)]

    elif ch_slug == "multiplication":
        if difficulty < 0.4:
            a_val = random.randint(10, 50)
            b_val = random.randint(2, 9)
        elif difficulty < 0.7:
            a_val = random.randint(20, 99)
            b_val = random.randint(2, 9)
        else:
            a_val = random.randint(10, 50)
            b_val = random.randint(10, 30)
        correct_val = a_val * b_val
        stem = random.choice([
            f"What is {a_val} × {b_val}?",
            f"{name()} buys {b_val} notebooks at ₹{a_val} each. What is the total cost?"
        ])
        correct = str(correct_val)
        wrong = [str(correct_val + a_val), str(correct_val - b_val), str(a_val + b_val)]

    elif ch_slug == "division":
        if difficulty < 0.4:
            divisor = random.randint(2, 9)
            quotient = random.randint(10, 50)
        else:
            divisor = random.randint(5, 12)
            quotient = random.randint(20, 100)
        dividend = divisor * quotient
        stem = random.choice([
            f"What is {dividend} ÷ {divisor}?",
            f"{name()} divides {dividend} stickers equally into {divisor} groups. How many in each group?"
        ])
        correct = str(quotient)
        wrong = [str(quotient + 1), str(quotient - 1), str(divisor)]

    elif ch_slug == "fractions_decimals":
        if difficulty < 0.4:
            pairs = [("1/2", "0.5"), ("1/4", "0.25"), ("3/4", "0.75"), ("1/10", "0.1")]
            p = random.choice(pairs)
            stem = f"Convert {p[0]} to a decimal."
            correct = p[1]
            others = [x[1] for x in pairs if x[1] != p[1]]
            wrong = others[:3]
        elif difficulty < 0.7:
            a_n = random.randint(1, 5)
            b_n = random.randint(1, 5)
            den = random.choice([6, 8, 10])
            while a_n + b_n > den:
                b_n = random.randint(1, 3)
            stem = f"What is {a_n}/{den} + {b_n}/{den}?"
            correct = f"{a_n + b_n}/{den}"
            wrong = [f"{a_n + b_n}/{den * 2}", f"{a_n * b_n}/{den}", f"{a_n + b_n + 1}/{den}"]
        else:
            n1 = name()
            whole = random.choice([10, 12, 15, 20])
            num = random.randint(2, whole // 2)
            stem = f"{n1} coloured {num} out of {whole} squares. What fraction is coloured?"
            from math import gcd
            g = gcd(num, whole)
            correct = f"{num // g}/{whole // g}"
            wrong = [f"{num}/{whole}" if g > 1 else f"{num + 1}/{whole}", f"{whole - num}/{whole}", f"{num}/{whole - num}"]
            if correct == wrong[0]:
                wrong[0] = f"{num + 1}/{whole}"

    elif ch_slug == "measurement":
        if difficulty < 0.5:
            stem = f"Convert 3 km 500 m to metres."
            correct = "3500"
            wrong = ["3050", "350", "35000"]
        else:
            kg = random.randint(2, 8)
            g = random.randint(100, 900)
            stem = f"Convert {kg} kg {g} g to grams."
            correct = str(kg * 1000 + g)
            wrong = [str(kg * 100 + g), str(kg * 1000), str(kg * 1000 + g + 100)]

    elif ch_slug == "perimeter_area":
        if difficulty < 0.5:
            l = random.randint(3, 12)
            w = random.randint(2, 8)
            peri = 2 * (l + w)
            stem = f"Find the perimeter of a rectangle with length {l} cm and width {w} cm."
            correct = f"{peri} cm"
            wrong = [f"{l * w} cm", f"{l + w} cm", f"{peri + 2} cm"]
        else:
            l = random.randint(4, 15)
            w = random.randint(3, 10)
            area = l * w
            stem = f"Find the area of a rectangle with length {l} cm and width {w} cm."
            correct = f"{area} sq cm"
            wrong = [f"{2 * (l + w)} sq cm", f"{area + l} sq cm", f"{l + w} sq cm"]

    elif ch_slug == "time":
        if difficulty < 0.5:
            start_h = random.randint(8, 15)
            start_m = random.choice([0, 15, 30, 45])
            dur_h = random.randint(1, 3)
            dur_m = random.choice([0, 15, 30])
            end_m = start_m + dur_m
            end_h = start_h + dur_h + (end_m // 60)
            end_m = end_m % 60
            stem = f"A movie starts at {start_h}:{start_m:02d} and lasts {dur_h} hour(s) and {dur_m} minutes. When does it end?"
            correct = f"{end_h}:{end_m:02d}"
            wrong = [f"{end_h + 1}:{end_m:02d}", f"{end_h}:{(end_m + 15) % 60:02d}", f"{start_h + dur_h}:{start_m:02d}"]
        else:
            stem = "How many seconds are in 1 hour?"
            correct = "3600"
            wrong = ["360", "600", "60"]

    elif ch_slug == "geometry_angles":
        if difficulty < 0.5:
            angle = random.randint(10, 170)
            if angle < 90:
                correct = "Acute"
            elif angle == 90:
                correct = "Right angle"
            else:
                correct = "Obtuse"
            stem = f"An angle of {angle}° is called:"
            wrong = [x for x in ["Acute", "Obtuse", "Right angle", "Straight"] if x != correct][:3]
        else:
            angle1 = random.randint(30, 80)
            angle2 = 180 - 90 - angle1
            stem = f"In a right-angled triangle, one angle is 90° and another is {angle1}°. What is the third angle?"
            correct = f"{angle2}°"
            wrong = [f"{angle2 + 10}°", f"{angle2 - 10}°" if angle2 > 10 else f"{angle2 + 20}°", f"{180 - angle1}°"]

    elif ch_slug == "data_handling":
        values = random.sample(range(10, 50), 5)
        n1 = name()
        if difficulty < 0.5:
            mean_val = sum(values) // len(values)
            stem = f"{n1} scored {', '.join(map(str, values))} in 5 tests. What is the total?"
            correct = str(sum(values))
            wrong = [str(sum(values) + 5), str(sum(values) - 5), str(max(values))]
        else:
            sorted_vals = sorted(values)
            stem = f"Find the range of: {', '.join(map(str, values))}"
            range_val = max(values) - min(values)
            correct = str(range_val)
            wrong = [str(range_val + 5), str(range_val - 3), str(sum(values) // len(values))]

    elif ch_slug == "coordinates":
        x = random.randint(1, 8)
        y = random.randint(1, 8)
        if difficulty < 0.5:
            stem = f"What are the coordinates of a point {x} units right and {y} units up from the origin?"
            correct = f"({x}, {y})"
            wrong = [f"({y}, {x})", f"({x + 1}, {y})", f"({x}, {y + 1})"]
        else:
            x2 = random.randint(1, 8)
            y2 = random.randint(1, 8)
            stem = f"Which point is further from the origin: ({x}, {y}) or ({x2}, {y2})?"
            d1 = x * x + y * y
            d2 = x2 * x2 + y2 * y2
            if d1 > d2:
                correct = f"({x}, {y})"
                wrong = [f"({x2}, {y2})", "Both are same distance", "Cannot tell"]
            elif d2 > d1:
                correct = f"({x2}, {y2})"
                wrong = [f"({x}, {y})", "Both are same distance", "Cannot tell"]
            else:
                correct = "Both are same distance"
                wrong = [f"({x}, {y})", f"({x2}, {y2})", "Cannot tell"]

    else:
        stem = "What is 1000 + 2000?"
        correct = "3000"
        wrong = ["2000", "4000", "5000"]

    choices = [correct] + wrong
    random.shuffle(choices)
    correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Check your calculation step by step.",
        "Re-read the problem and identify key information.",
        "Think about which operation to use."
    ])
    hint = {
        "level_0": "Identify what the question is asking for.",
        "level_1": "Write down the key numbers and think about the operation needed.",
        "level_2": f"The correct answer is {correct}."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": [ch_slug, "grade4"]}


# =========== Grade 5 ===========
def generate_grade5_questions():
    questions = []
    chapters = CHAPTERS[5]
    qs_per_chapter = distribute_questions(200, 12)

    q_idx = 0
    for ch_idx, (ch_name, ch_slug) in enumerate(chapters):
        num_qs = qs_per_chapter[ch_idx]
        for i in range(num_qs):
            q_idx += 1
            tier, score = get_difficulty(i, num_qs)
            a, b, c = get_irt_params(score)
            q = generate_g5_question(ch_slug, i, num_qs)

            question = {
                "id": f"IGCSE-G5-{q_idx:03d}",
                "stem": q["stem"],
                "choices": q["choices"],
                "correct_answer": q["correct_answer"],
                "difficulty_tier": tier,
                "difficulty_score": score,
                "visual_svg": None,
                "visual_alt": None,
                "diagnostics": q["diagnostics"],
                "tags": q.get("tags", [ch_slug, "grade5"]),
                "topic": f"igcse_g5_{ch_slug}",
                "chapter": ch_name,
                "hint": q["hint"],
                "curriculum_tags": [f"IGCSE_5_{ch_idx+1}"],
                "irt_params": {"a": a, "b": b, "c": c},
                "irt_a": a,
                "irt_b": b,
                "irt_c": c,
            }
            questions.append(question)
    return questions

def generate_g5_question(ch_slug, i, total):
    difficulty = i / max(total - 1, 1)

    if ch_slug == "large_numbers":
        if difficulty < 0.4:
            n = random.randint(10000, 99999)
            stem = f"Write the number {n} in words. What is its ten-thousands digit?"
            correct = str(n // 10000)
            wrong = [str((n // 1000) % 10), str((n // 100) % 10), str(n // 10000 + 1)]
        elif difficulty < 0.7:
            n = random.randint(100000, 999999)
            stem = f"Round {n} to the nearest ten-thousand."
            rounded = round(n, -4)
            correct = str(rounded)
            wrong = [str(rounded + 10000), str(rounded - 10000), str(round(n, -3))]
        else:
            n = random.randint(1000000, 9999999)
            stem = f"What is the place value of the digit {str(n)[2]} in {n:,}?"
            digit = int(str(n)[2])
            value = digit * 100000
            correct = str(value)
            wrong = [str(digit * 10000), str(digit * 1000000), str(digit)]

    elif ch_slug == "decimals":
        if difficulty < 0.4:
            a_val = round(random.uniform(1, 10), 1)
            b_val = round(random.uniform(1, 10), 1)
            result = round(a_val + b_val, 1)
            stem = f"What is {a_val} + {b_val}?"
            correct = str(result)
            wrong = [str(round(result + 0.1, 1)), str(round(result - 0.1, 1)), str(round(a_val * b_val, 1))]
        elif difficulty < 0.7:
            a_val = round(random.uniform(5, 20), 2)
            b_val = round(random.uniform(1, a_val - 0.5), 2)
            result = round(a_val - b_val, 2)
            stem = f"What is {a_val} - {b_val}?"
            correct = str(result)
            wrong = [str(round(result + 0.1, 2)), str(round(result - 0.01, 2)), str(round(a_val + b_val, 2))]
        else:
            a_val = round(random.uniform(1, 10), 1)
            b_val = random.randint(2, 9)
            result = round(a_val * b_val, 1)
            stem = f"What is {a_val} × {b_val}?"
            correct = str(result)
            wrong = [str(round(result + a_val, 1)), str(round(result - a_val, 1)), str(round(a_val + b_val, 1))]

    elif ch_slug == "fractions":
        if difficulty < 0.4:
            den = random.choice([4, 6, 8, 10, 12])
            a_n = random.randint(1, den // 2)
            b_n = random.randint(1, den // 2)
            result_n = a_n + b_n
            stem = f"What is {a_n}/{den} + {b_n}/{den}?"
            from math import gcd
            g = gcd(result_n, den)
            correct = f"{result_n // g}/{den // g}" if g > 1 else f"{result_n}/{den}"
            wrong = [f"{result_n}/{den * 2}", f"{a_n * b_n}/{den}", f"{result_n + 1}/{den}"]
        elif difficulty < 0.7:
            den1 = random.choice([2, 3, 4, 5])
            den2 = den1 * random.choice([2, 3])
            a_n = random.randint(1, den1 - 1)
            b_n = random.randint(1, den2 - 1)
            # Convert to common denominator
            common_den = den2
            new_a = a_n * (den2 // den1)
            result_n = new_a + b_n
            from math import gcd
            g = gcd(result_n, common_den)
            stem = f"What is {a_n}/{den1} + {b_n}/{den2}?"
            correct = f"{result_n // g}/{common_den // g}" if g > 1 else f"{result_n}/{common_den}"
            wrong = [f"{a_n + b_n}/{den1 + den2}", f"{a_n + b_n}/{den2}", f"{result_n + 1}/{common_den}"]
        else:
            whole = random.randint(2, 5)
            num = random.randint(1, 3)
            den = random.choice([4, 5, 8])
            improper_num = whole * den + num
            stem = f"Convert {whole} {num}/{den} to an improper fraction."
            correct = f"{improper_num}/{den}"
            wrong = [f"{whole + num}/{den}", f"{whole * num}/{den}", f"{improper_num + 1}/{den}"]

    elif ch_slug == "percentages":
        if difficulty < 0.4:
            pct = random.choice([10, 20, 25, 50])
            val = random.choice([100, 200, 400, 500, 1000])
            result = pct * val // 100
            stem = f"What is {pct}% of {val}?"
            correct = str(result)
            wrong = [str(result + 10), str(result // 2), str(val - result)]
        elif difficulty < 0.7:
            n1 = name()
            total_marks = random.choice([50, 80, 100, 200])
            scored = random.randint(total_marks // 4, total_marks * 3 // 4)
            pct = scored * 100 // total_marks
            stem = f"{n1} scored {scored} out of {total_marks}. What percentage is that?"
            correct = f"{pct}%"
            wrong = [f"{pct + 5}%", f"{pct - 5}%", f"{scored}%"]
        else:
            original = random.choice([200, 300, 400, 500, 600])
            pct_off = random.choice([10, 15, 20, 25])
            discount = original * pct_off // 100
            sale_price = original - discount
            stem = f"A shirt costs ₹{original}. There is a {pct_off}% discount. What is the sale price?"
            correct = f"₹{sale_price}"
            wrong = [f"₹{sale_price + 10}", f"₹{discount}", f"₹{original + discount}"]

    elif ch_slug == "add_sub":
        a_val = random.randint(10000, 99999)
        b_val = random.randint(10000, 50000)
        op = random.choice(["+", "-"])
        if op == "-" and b_val > a_val:
            a_val, b_val = b_val, a_val
        correct_val = a_val + b_val if op == "+" else a_val - b_val
        stem = f"What is {a_val:,} {op} {b_val:,}?"
        correct = f"{correct_val:,}"
        wrong = [f"{correct_val + 100:,}", f"{correct_val - 100:,}", f"{correct_val + 1000:,}"]

    elif ch_slug == "mult_div":
        if difficulty < 0.5:
            a_val = random.randint(100, 999)
            b_val = random.randint(10, 99)
            correct_val = a_val * b_val
            stem = f"What is {a_val} × {b_val}?"
            correct = str(correct_val)
            wrong = [str(correct_val + a_val), str(correct_val - b_val), str(correct_val + 100)]
        else:
            divisor = random.randint(5, 25)
            quotient = random.randint(20, 100)
            dividend = divisor * quotient
            stem = f"What is {dividend} ÷ {divisor}?"
            correct = str(quotient)
            wrong = [str(quotient + 1), str(quotient - 1), str(divisor)]

    elif ch_slug == "ratio_proportion":
        if difficulty < 0.5:
            a_val = random.randint(2, 10)
            b_val = random.randint(2, 10)
            from math import gcd
            g = gcd(a_val, b_val)
            stem = f"Simplify the ratio {a_val}:{b_val}"
            correct = f"{a_val // g}:{b_val // g}"
            wrong = [f"{b_val // g}:{a_val // g}", f"{a_val}:{b_val}", f"{a_val + 1}:{b_val + 1}"]
        else:
            n1 = name()
            n2 = name()
            while n2 == n1:
                n2 = random.choice(INDIAN_NAMES)
            ratio_a = random.randint(2, 5)
            ratio_b = random.randint(2, 5)
            total_val = (ratio_a + ratio_b) * random.randint(3, 8)
            share_a = total_val * ratio_a // (ratio_a + ratio_b)
            stem = f"{n1} and {n2} share ₹{total_val} in the ratio {ratio_a}:{ratio_b}. How much does {n1} get?"
            correct = f"₹{share_a}"
            wrong = [f"₹{total_val - share_a}", f"₹{total_val // 2}", f"₹{share_a + ratio_a}"]

    elif ch_slug == "geometry":
        if difficulty < 0.4:
            stem = "How many degrees are in a straight line?"
            correct = "180°"
            wrong = ["90°", "360°", "270°"]
        elif difficulty < 0.7:
            angle1 = random.randint(20, 70)
            angle2 = random.randint(20, 70)
            angle3 = 180 - angle1 - angle2
            stem = f"Two angles of a triangle are {angle1}° and {angle2}°. What is the third angle?"
            correct = f"{angle3}°"
            wrong = [f"{angle3 + 10}°", f"{angle3 - 10}°", f"{180 - angle1}°"]
        else:
            angle = random.randint(30, 80)
            supplement = 180 - angle
            stem = f"What is the supplement of {angle}°?"
            correct = f"{supplement}°"
            wrong = [f"{90 - angle}°", f"{360 - angle}°", f"{supplement + 10}°"]

    elif ch_slug == "measurement_area":
        if difficulty < 0.5:
            l = random.randint(5, 20)
            w = random.randint(3, 15)
            area = l * w
            stem = f"Find the area of a rectangle with length {l} m and breadth {w} m."
            correct = f"{area} sq m"
            wrong = [f"{2 * (l + w)} sq m", f"{area + l} sq m", f"{l + w} sq m"]
        else:
            side = random.randint(5, 20)
            area = side * side
            stem = f"Find the area of a square with side {side} cm."
            correct = f"{area} sq cm"
            wrong = [f"{4 * side} sq cm", f"{area + side} sq cm", f"{2 * side * side} sq cm"]

    elif ch_slug == "data_handling":
        values = sorted(random.sample(range(10, 60), 5))
        if difficulty < 0.5:
            stem = f"Find the median of: {', '.join(map(str, values))}"
            correct = str(values[2])
            wrong = [str(values[1]), str(values[3]), str(sum(values) // 5)]
        else:
            mean = sum(values) // 5
            stem = f"Find the mean of: {', '.join(map(str, values))}"
            correct = str(mean)
            wrong = [str(mean + 2), str(values[2]), str(max(values) - min(values))]

    elif ch_slug == "algebra_basics":
        if difficulty < 0.4:
            a_val = random.randint(2, 10)
            b_val = random.randint(1, 10)
            result = a_val + b_val
            stem = f"If x = {a_val}, what is x + {b_val}?"
            correct = str(result)
            wrong = [str(result + 1), str(result - 1), str(a_val * b_val)]
        elif difficulty < 0.7:
            a_val = random.randint(2, 8)
            result = random.randint(10, 20)
            b_val = result - a_val
            stem = f"Solve: x + {a_val} = {result}. What is x?"
            correct = str(b_val)
            wrong = [str(b_val + 1), str(b_val - 1), str(result)]
        else:
            a_val = random.randint(2, 6)
            result = a_val * random.randint(3, 8)
            x_val = result // a_val
            stem = f"Solve: {a_val}x = {result}. What is x?"
            correct = str(x_val)
            wrong = [str(x_val + 1), str(x_val - 1), str(result - a_val)]

    elif ch_slug == "problem_solving":
        n1 = name()
        if difficulty < 0.4:
            price = random.randint(10, 50)
            qty = random.randint(2, 5)
            total_cost = price * qty
            stem = f"{n1} buys {qty} pens at ₹{price} each. How much does {n1} spend?"
            correct = f"₹{total_cost}"
            wrong = [f"₹{total_cost + price}", f"₹{price + qty}", f"₹{total_cost - price}"]
        elif difficulty < 0.7:
            speed = random.choice([40, 50, 60, 80])
            time_h = random.randint(2, 5)
            distance = speed * time_h
            stem = f"A car travels at {speed} km/h for {time_h} hours. How far does it go?"
            correct = f"{distance} km"
            wrong = [f"{distance + speed} km", f"{speed + time_h} km", f"{distance - speed} km"]
        else:
            cp = random.randint(100, 500)
            sp = cp + random.randint(20, 100)
            profit = sp - cp
            stem = f"{n1} buys a toy for ₹{cp} and sells it for ₹{sp}. What is the profit?"
            correct = f"₹{profit}"
            wrong = [f"₹{sp}", f"₹{cp}", f"₹{profit + 10}"]

    else:
        stem = "What is 1000 × 5?"
        correct = "5000"
        wrong = ["500", "50000", "5500"]

    choices = [correct] + wrong
    random.shuffle(choices)
    correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Review your calculation method.",
        "Check if you used the right operation.",
        "Try solving step by step."
    ])
    hint = {
        "level_0": "Identify the key information in the problem.",
        "level_1": "Think about which mathematical operation applies here.",
        "level_2": f"The correct answer is {correct}."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": [ch_slug, "grade5"]}


# =========== Grade 6 ===========
def generate_grade6_questions():
    questions = []
    chapters = CHAPTERS[6]
    qs_per_chapter = distribute_questions(200, 12)

    q_idx = 0
    for ch_idx, (ch_name, ch_slug) in enumerate(chapters):
        num_qs = qs_per_chapter[ch_idx]
        for i in range(num_qs):
            q_idx += 1
            tier, score = get_difficulty(i, num_qs)
            a, b, c = get_irt_params(score)
            q = generate_g6_question(ch_slug, i, num_qs)

            question = {
                "id": f"IGCSE-G6-{q_idx:03d}",
                "stem": q["stem"],
                "choices": q["choices"],
                "correct_answer": q["correct_answer"],
                "difficulty_tier": tier,
                "difficulty_score": score,
                "visual_svg": None,
                "visual_alt": None,
                "diagnostics": q["diagnostics"],
                "tags": q.get("tags", [ch_slug, "grade6"]),
                "topic": f"igcse_g6_{ch_slug}",
                "chapter": ch_name,
                "hint": q["hint"],
                "curriculum_tags": [f"IGCSE_6_{ch_idx+1}"],
                "irt_params": {"a": a, "b": b, "c": c},
                "irt_a": a,
                "irt_b": b,
                "irt_c": c,
            }
            questions.append(question)
    return questions

def generate_g6_question(ch_slug, i, total):
    difficulty = i / max(total - 1, 1)

    if ch_slug == "integers_properties":
        if difficulty < 0.3:
            a_val = random.randint(-20, -1)
            b_val = random.randint(1, 20)
            result = a_val + b_val
            stem = f"What is {a_val} + {b_val}?"
            correct = str(result)
            wrong = [str(result + 1), str(result - 1), str(abs(a_val) + b_val)]
        elif difficulty < 0.6:
            a_val = random.randint(-15, -1)
            b_val = random.randint(-15, -1)
            result = a_val * b_val
            stem = f"What is ({a_val}) × ({b_val})?"
            correct = str(result)
            wrong = [str(-result), str(a_val + b_val), str(result + 1)]
        else:
            n = random.randint(20, 100)
            factors = [i for i in range(1, n + 1) if n % i == 0]
            stem = f"How many factors does {n} have?"
            correct = str(len(factors))
            wrong = [str(len(factors) + 1), str(len(factors) - 1), str(n // 2)]

    elif ch_slug == "frac_dec_pct":
        if difficulty < 0.3:
            pairs = [("3/5", "0.6", "60%"), ("1/4", "0.25", "25%"), ("2/5", "0.4", "40%"), ("7/10", "0.7", "70%")]
            p = random.choice(pairs)
            choice_type = random.choice(["decimal", "percentage"])
            if choice_type == "decimal":
                stem = f"Convert {p[0]} to a decimal."
                correct = p[1]
                wrong = [str(round(float(p[1]) + 0.1, 1)), str(round(float(p[1]) - 0.1, 1)), p[2].replace("%", "")]
            else:
                stem = f"Convert {p[0]} to a percentage."
                correct = p[2]
                wrong = [f"{int(p[2].replace('%', '')) + 10}%", f"{int(p[2].replace('%', '')) - 10}%", p[1]]
        elif difficulty < 0.6:
            a_num = random.randint(1, 5)
            a_den = random.randint(a_num + 1, 8)
            b_num = random.randint(1, 5)
            b_den = random.randint(b_num + 1, 8)
            from math import gcd
            lcm_den = (a_den * b_den) // gcd(a_den, b_den)
            new_a = a_num * (lcm_den // a_den)
            new_b = b_num * (lcm_den // b_den)
            result_num = new_a + new_b
            g = gcd(result_num, lcm_den)
            stem = f"What is {a_num}/{a_den} + {b_num}/{b_den}?"
            correct = f"{result_num // g}/{lcm_den // g}"
            wrong = [f"{a_num + b_num}/{a_den + b_den}", f"{result_num}/{lcm_den + 1}", f"{result_num + 1}/{lcm_den}"]
        else:
            a_num = random.randint(2, 7)
            a_den = random.randint(3, 9)
            b_num = random.randint(2, 5)
            b_den = random.randint(3, 8)
            result_num = a_num * b_num
            result_den = a_den * b_den
            from math import gcd
            g = gcd(result_num, result_den)
            stem = f"What is {a_num}/{a_den} × {b_num}/{b_den}?"
            correct = f"{result_num // g}/{result_den // g}"
            wrong = [f"{a_num * b_num}/{a_den + b_den}", f"{a_num + b_num}/{a_den * b_den}", f"{result_num // g + 1}/{result_den // g}"]

    elif ch_slug == "ratio_proportion":
        if difficulty < 0.4:
            a_val = random.randint(4, 20)
            b_val = random.randint(4, 20)
            from math import gcd
            g = gcd(a_val, b_val)
            stem = f"Simplify {a_val}:{b_val}"
            correct = f"{a_val // g}:{b_val // g}"
            wrong = [f"{b_val // g}:{a_val // g}", f"{a_val}:{b_val}", f"{a_val // g + 1}:{b_val // g}"]
        elif difficulty < 0.7:
            n1 = name()
            ratio = random.choice([(2, 3), (3, 4), (1, 3), (2, 5)])
            total_val = (ratio[0] + ratio[1]) * random.randint(5, 15)
            share1 = total_val * ratio[0] // (ratio[0] + ratio[1])
            stem = f"Divide ₹{total_val} in the ratio {ratio[0]}:{ratio[1]}. What is the smaller share?"
            correct = f"₹{min(share1, total_val - share1)}"
            wrong = [f"₹{max(share1, total_val - share1)}", f"₹{total_val // 2}", f"₹{share1 + ratio[0]}"]
        else:
            # Proportion problem
            a_val = random.randint(3, 8)
            b_val = random.randint(10, 30)
            c_val = random.randint(a_val + 2, a_val + 10)
            d_val = b_val * c_val // a_val
            stem = f"If {a_val} workers can do a job in {b_val} days, how many days will {c_val} workers take? (Assume equal work rate)"
            # inverse proportion: more workers = fewer days
            result = a_val * b_val // c_val
            correct = str(result)
            wrong = [str(result + 2), str(d_val), str(b_val)]

    elif ch_slug == "algebra":
        if difficulty < 0.3:
            a_val = random.randint(2, 6)
            b_val = random.randint(1, 10)
            x_val = random.randint(2, 8)
            result = a_val * x_val + b_val
            stem = f"If x = {x_val}, find the value of {a_val}x + {b_val}."
            correct = str(result)
            wrong = [str(result + a_val), str(result - b_val), str(a_val + b_val + x_val)]
        elif difficulty < 0.6:
            a_val = random.randint(2, 5)
            b_val = random.randint(2, 5)
            stem = f"Simplify: {a_val}x + {b_val}x"
            correct = f"{a_val + b_val}x"
            wrong = [f"{a_val * b_val}x", f"{a_val + b_val}x²", f"{a_val}x + {b_val}"]
        else:
            a_val = random.randint(2, 5)
            b_val = random.randint(1, 8)
            c_val = random.randint(1, 4)
            d_val = random.randint(1, 8)
            # (ax + b) + (cx + d)
            stem = f"Simplify: ({a_val}x + {b_val}) + ({c_val}x + {d_val})"
            correct = f"{a_val + c_val}x + {b_val + d_val}"
            wrong = [f"{a_val * c_val}x + {b_val + d_val}", f"{a_val + c_val}x + {b_val * d_val}", f"{a_val + c_val + b_val + d_val}x"]

    elif ch_slug == "equations":
        if difficulty < 0.3:
            x_val = random.randint(2, 10)
            a_val = random.randint(2, 6)
            result = a_val * x_val
            stem = f"Solve: {a_val}x = {result}"
            correct = f"x = {x_val}"
            wrong = [f"x = {x_val + 1}", f"x = {x_val - 1}", f"x = {result}"]
        elif difficulty < 0.6:
            x_val = random.randint(2, 8)
            a_val = random.randint(2, 5)
            b_val = random.randint(1, 10)
            result = a_val * x_val + b_val
            stem = f"Solve: {a_val}x + {b_val} = {result}"
            correct = f"x = {x_val}"
            wrong = [f"x = {x_val + 1}", f"x = {x_val - 1}", f"x = {result - b_val}"]
        else:
            x_val = random.randint(2, 8)
            a_val = random.randint(2, 5)
            b_val = random.randint(1, 8)
            c_val = random.randint(1, 3)
            # ax + b = cx + d, solve for x
            d_val = (a_val - c_val) * x_val + b_val
            stem = f"Solve: {a_val}x + {b_val} = {c_val}x + {d_val}"
            correct = f"x = {x_val}"
            wrong = [f"x = {x_val + 1}", f"x = {x_val - 1}", f"x = {d_val - b_val}"]

    elif ch_slug == "geometry":
        if difficulty < 0.3:
            angle = random.randint(20, 80)
            complement = 90 - angle
            stem = f"What is the complement of {angle}°?"
            correct = f"{complement}°"
            wrong = [f"{180 - angle}°", f"{angle}°", f"{complement + 10}°"]
        elif difficulty < 0.6:
            stem = "What is the sum of interior angles of a quadrilateral?"
            correct = "360°"
            wrong = ["180°", "270°", "540°"]
        else:
            n = random.choice([5, 6, 8])
            angle_sum = (n - 2) * 180
            stem = f"What is the sum of interior angles of a {n}-sided polygon?"
            correct = f"{angle_sum}°"
            wrong = [f"{angle_sum + 180}°", f"{angle_sum - 180}°", f"{n * 180}°"]

    elif ch_slug == "transformations":
        if difficulty < 0.5:
            x = random.randint(1, 6)
            y = random.randint(1, 6)
            stem = f"Reflect the point ({x}, {y}) in the x-axis. What are the new coordinates?"
            correct = f"({x}, {-y})"
            wrong = [f"({-x}, {y})", f"({-x}, {-y})", f"({y}, {x})"]
        else:
            x = random.randint(1, 6)
            y = random.randint(1, 6)
            dx = random.randint(1, 5)
            dy = random.randint(1, 5)
            stem = f"Translate the point ({x}, {y}) by ({dx}, {dy}). What are the new coordinates?"
            correct = f"({x + dx}, {y + dy})"
            wrong = [f"({x - dx}, {y - dy})", f"({x + dy}, {y + dx})", f"({x * dx}, {y * dy})"]

    elif ch_slug == "measurement":
        if difficulty < 0.5:
            stem = "How many millilitres are in 2.5 litres?"
            correct = "2500"
            wrong = ["250", "25000", "25"]
        else:
            km = round(random.uniform(1.5, 8.5), 1)
            m = int(km * 1000)
            stem = f"Convert {km} km to metres."
            correct = str(m)
            wrong = [str(m + 100), str(int(km * 100)), str(m - 500)]

    elif ch_slug == "area_volume":
        if difficulty < 0.4:
            l = random.randint(3, 12)
            w = random.randint(2, 8)
            h = random.randint(2, 6)
            vol = l * w * h
            stem = f"Find the volume of a cuboid with length {l} cm, width {w} cm and height {h} cm."
            correct = f"{vol} cu cm"
            wrong = [f"{l * w} cu cm", f"{2 * (l * w + w * h + l * h)} cu cm", f"{vol + l} cu cm"]
        elif difficulty < 0.7:
            side = random.randint(3, 10)
            vol = side ** 3
            stem = f"Find the volume of a cube with side {side} cm."
            correct = f"{vol} cu cm"
            wrong = [f"{side * side} cu cm", f"{6 * side * side} cu cm", f"{vol + side} cu cm"]
        else:
            base = random.randint(4, 12)
            height = random.randint(3, 10)
            area = base * height // 2
            stem = f"Find the area of a triangle with base {base} cm and height {height} cm."
            correct = f"{area} sq cm"
            wrong = [f"{base * height} sq cm", f"{base + height} sq cm", f"{area + base} sq cm"]

    elif ch_slug == "statistics":
        values = random.sample(range(10, 60), 7)
        sorted_v = sorted(values)
        if difficulty < 0.4:
            mean = sum(values) // len(values)
            stem = f"Find the mean of: {', '.join(map(str, values))}"
            correct = str(mean)
            wrong = [str(mean + 2), str(sorted_v[3]), str(max(values) - min(values))]
        elif difficulty < 0.7:
            stem = f"Find the median of: {', '.join(map(str, values))}"
            correct = str(sorted_v[3])
            wrong = [str(sorted_v[2]), str(sorted_v[4]), str(sum(values) // len(values))]
        else:
            range_val = max(values) - min(values)
            stem = f"Find the range of: {', '.join(map(str, values))}"
            correct = str(range_val)
            wrong = [str(range_val + 2), str(range_val - 2), str(sorted_v[3])]

    elif ch_slug == "probability":
        if difficulty < 0.4:
            total_balls = random.randint(8, 15)
            red = random.randint(2, total_balls - 2)
            stem = f"A bag has {red} red balls and {total_balls - red} blue balls. What is the probability of picking a red ball?"
            correct = f"{red}/{total_balls}"
            wrong = [f"{total_balls - red}/{total_balls}", f"{red}/{total_balls - red}", f"1/{total_balls}"]
        elif difficulty < 0.7:
            stem = "A fair coin is tossed. What is the probability of getting heads?"
            correct = "1/2"
            wrong = ["1/4", "1/3", "2/3"]
        else:
            total = 6
            event = random.randint(1, 5)
            stem = f"A fair die is rolled. What is the probability of getting a number less than {event + 1}?"
            correct = f"{event}/{total}"
            from math import gcd
            g = gcd(event, total)
            if g > 1:
                correct = f"{event // g}/{total // g}"
            wrong_vals = [f"{event + 1}/{total}", f"{event}/{total + 1}", f"1/{total}"]
            wrong = wrong_vals

    elif ch_slug == "problem_solving":
        n1 = name()
        if difficulty < 0.3:
            speed = random.choice([40, 50, 60, 80, 100])
            time_h = random.randint(2, 6)
            distance = speed * time_h
            stem = f"A train travels at {speed} km/h. How far will it go in {time_h} hours?"
            correct = f"{distance} km"
            wrong = [f"{distance + speed} km", f"{speed + time_h} km", f"{distance // 2} km"]
        elif difficulty < 0.6:
            cp = random.randint(200, 1000)
            profit_pct = random.choice([10, 20, 25, 50])
            profit = cp * profit_pct // 100
            sp = cp + profit
            stem = f"{n1} buys an item for ₹{cp} and sells it at {profit_pct}% profit. What is the selling price?"
            correct = f"₹{sp}"
            wrong = [f"₹{profit}", f"₹{cp + profit_pct}", f"₹{sp + 10}"]
        else:
            principal = random.choice([1000, 2000, 5000, 10000])
            rate = random.choice([5, 8, 10, 12])
            time_y = random.choice([1, 2, 3])
            interest = principal * rate * time_y // 100
            stem = f"Find the simple interest on ₹{principal} at {rate}% per annum for {time_y} year(s)."
            correct = f"₹{interest}"
            wrong = [f"₹{interest + 100}", f"₹{principal + interest}", f"₹{interest // 2}"]

    else:
        stem = "What is 25 × 4?"
        correct = "100"
        wrong = ["75", "125", "80"]

    choices = [correct] + wrong
    random.shuffle(choices)
    correct_idx = choices.index(correct)

    diag = _make_diagnostics(correct_idx, [
        "Check your method and calculation.",
        "Make sure you applied the correct formula.",
        "Re-read the question and identify all given information."
    ])
    hint = {
        "level_0": "Identify what mathematical concept is being tested.",
        "level_1": "Write down the formula or method needed, then substitute values.",
        "level_2": f"The correct answer is {correct}."
    }
    return {"stem": stem, "choices": choices, "correct_answer": correct_idx, "diagnostics": diag, "hint": hint, "tags": [ch_slug, "grade6"]}


# =========== Utility functions ===========
def distribute_questions(total, num_chapters):
    """Distribute total questions across chapters as evenly as possible."""
    base = total // num_chapters
    remainder = total % num_chapters
    distribution = [base] * num_chapters
    for i in range(remainder):
        distribution[i] += 1
    return distribution

def _make_diagnostics(correct_idx, messages):
    """Create diagnostics dict with string keys for wrong answer indices."""
    diag = {}
    msg_idx = 0
    for i in range(4):
        if i != correct_idx:
            diag[str(i)] = messages[msg_idx % len(messages)]
            msg_idx += 1
    return diag


# =========== Main ===========
def main():
    generators = {
        1: generate_grade1_questions,
        2: generate_grade2_questions,
        3: generate_grade3_questions,
        4: generate_grade4_questions,
        5: generate_grade5_questions,
        6: generate_grade6_questions,
    }

    for grade in range(1, 7):
        print(f"Generating Grade {grade}...")
        questions = generators[grade]()

        assert len(questions) == 200, f"Grade {grade}: Expected 200 questions, got {len(questions)}"

        # Validate each question
        for q in questions:
            assert q["correct_answer"] in [0, 1, 2, 3], f"Invalid correct_answer: {q['correct_answer']} in {q['id']}"
            assert len(q["choices"]) == 4, f"Not 4 choices in {q['id']}"
            assert len(q["diagnostics"]) == 3, f"Diagnostics should have 3 entries in {q['id']}"
            assert str(q["correct_answer"]) not in q["diagnostics"], f"Correct answer in diagnostics for {q['id']}"
            assert "level_0" in q["hint"] and "level_1" in q["hint"] and "level_2" in q["hint"], f"Missing hint levels in {q['id']}"
            assert q["irt_a"] >= 0.8 and q["irt_a"] <= 1.5, f"IRT a out of range in {q['id']}"
            assert q["irt_b"] >= -3.1 and q["irt_b"] <= 3.1, f"IRT b out of range in {q['id']}"
            assert q["irt_c"] == 0.25, f"IRT c not 0.25 in {q['id']}"

        data = {
            "topic_id": f"igcse_g{grade}",
            "topic_name": f"IGCSE Grade {grade} Mathematics",
            "version": "2.0",
            "curriculum": "IGCSE",
            "grade": grade,
            "total_questions": 200,
            "questions": questions,
        }

        output_path = os.path.join(OUTPUT_DIR, f"grade{grade}", f"igcse_grade{grade}.json")
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"  Written {output_path} ({len(questions)} questions)")

    print("\nAll files generated successfully!")

if __name__ == "__main__":
    main()
