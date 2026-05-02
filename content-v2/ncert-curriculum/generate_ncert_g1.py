#!/usr/bin/env python3
"""
NCERT Grade 1 Mathematics Question Generator for Kiwimath
Generates 300 questions across all 13 chapters with SVG visuals.
"""

import json
import os
import random
import math

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grade1")
VISUALS_DIR = os.path.join(OUTPUT_DIR, "visuals")
os.makedirs(VISUALS_DIR, exist_ok=True)

# Indian names and context
NAMES_GIRL = ["Ria", "Priya", "Ananya", "Meera", "Kavya", "Diya", "Isha", "Neha", "Saanvi", "Aisha", "Pooja", "Shreya"]
NAMES_BOY = ["Arjun", "Rohan", "Aarav", "Vivaan", "Karan", "Aditya", "Ravi", "Dev", "Siddharth", "Nikhil", "Raj", "Amit"]
ALL_NAMES = NAMES_GIRL + NAMES_BOY

INDIAN_OBJECTS = {
    "fruits": ["mangoes", "bananas", "guavas", "papayas", "coconuts", "oranges", "apples", "litchis"],
    "food": ["rotis", "samosas", "laddoos", "jalebis", "idlis", "dosas", "pakoras", "puris"],
    "animals": ["peacocks", "elephants", "parrots", "cows", "monkeys", "butterflies", "sparrows", "squirrels"],
    "vehicles": ["autorickshaws", "buses", "cycles", "scooters", "trains", "bullock carts"],
    "items": ["bangles", "diyas", "kites", "marbles", "pencils", "crayons", "erasers", "stickers", "toffees", "balloons"],
    "flowers": ["marigolds", "roses", "lotuses", "jasmine flowers", "sunflowers"],
}

COLORS_SVG = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"]
SHAPE_COLORS = {"circle": "#FF6B6B", "square": "#4ECDC4", "triangle": "#FFEAA7", "rectangle": "#85C1E9"}

questions = []
svg_files = {}


def get_name():
    return random.choice(ALL_NAMES)

def get_girl():
    return random.choice(NAMES_GIRL)

def get_boy():
    return random.choice(NAMES_BOY)

def get_objects(category=None):
    if category:
        return random.choice(INDIAN_OBJECTS[category])
    cat = random.choice(list(INDIAN_OBJECTS.keys()))
    return random.choice(INDIAN_OBJECTS[cat])

def irt_params(difficulty):
    if difficulty == "easy":
        b = round(random.uniform(-2.5, -1.5), 2)
    elif difficulty == "medium":
        b = round(random.uniform(-1.5, -0.5), 2)
    else:
        b = round(random.uniform(-0.5, 0.5), 2)
    a = round(random.uniform(0.8, 1.4), 2)
    return {"a": a, "b": b, "c": 0.25}

def difficulty_score(difficulty):
    if difficulty == "easy":
        return random.randint(10, 35)
    elif difficulty == "medium":
        return random.randint(36, 65)
    else:
        return random.randint(66, 90)

def make_id(n):
    return f"NCERT-G1-{n:03d}"

def make_svg_filename(qid):
    return f"{qid}.svg"

def wrong_choices(correct, low, high, count=3):
    """Generate wrong answer choices distinct from correct."""
    choices = set()
    attempts = 0
    while len(choices) < count and attempts < 100:
        w = random.randint(low, high)
        if w != correct:
            choices.add(w)
        attempts += 1
    result = list(choices)[:count]
    while len(result) < count:
        result.append(correct + len(result) + 1)
    return result


# ============================================================
# SVG GENERATORS
# ============================================================

def svg_counting_objects(count, obj_type="circle", color=None):
    """Generate SVG with countable objects arranged nicely."""
    if color is None:
        color = random.choice(COLORS_SVG)
    svg = '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '  <rect width="200" height="120" fill="#FFFEF5" rx="8"/>\n'

    cols = min(count, 5)
    rows = math.ceil(count / 5)
    x_start = 20
    y_start = 15
    x_gap = 35
    y_gap = 35

    for i in range(count):
        r = i // 5
        c = i % 5
        cx = x_start + c * x_gap + 15
        cy = y_start + r * y_gap + 15

        if obj_type == "circle":
            svg += f'  <circle cx="{cx}" cy="{cy}" r="12" fill="{color}" stroke="#333" stroke-width="1"/>\n'
        elif obj_type == "star":
            points = []
            for j in range(5):
                angle = math.radians(j * 72 - 90)
                px = cx + 12 * math.cos(angle)
                py = cy + 12 * math.sin(angle)
                points.append(f"{px:.1f},{py:.1f}")
                angle2 = math.radians(j * 72 - 90 + 36)
                px2 = cx + 5 * math.cos(angle2)
                py2 = cy + 5 * math.sin(angle2)
                points.append(f"{px2:.1f},{py2:.1f}")
            svg += f'  <polygon points="{" ".join(points)}" fill="{color}" stroke="#333" stroke-width="1"/>\n'
        elif obj_type == "mango":
            svg += f'  <ellipse cx="{cx}" cy="{cy}" rx="10" ry="13" fill="#F4D03F" stroke="#E67E22" stroke-width="1.5"/>\n'
            svg += f'  <path d="M{cx},{cy-13} Q{cx+3},{cy-18} {cx+6},{cy-16}" fill="#27AE60" stroke="#27AE60" stroke-width="1"/>\n'
        elif obj_type == "flower":
            for k in range(5):
                angle = math.radians(k * 72)
                px = cx + 7 * math.cos(angle)
                py = cy + 7 * math.sin(angle)
                svg += f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{color}" opacity="0.8"/>\n'
            svg += f'  <circle cx="{cx}" cy="{cy}" r="4" fill="#F39C12"/>\n'
        elif obj_type == "triangle_obj":
            svg += f'  <polygon points="{cx},{cy-12} {cx-10},{cy+8} {cx+10},{cy+8}" fill="{color}" stroke="#333" stroke-width="1"/>\n'
        elif obj_type == "balloon":
            svg += f'  <ellipse cx="{cx}" cy="{cy-3}" rx="9" ry="12" fill="{color}"/>\n'
            svg += f'  <line x1="{cx}" y1="{cy+9}" x2="{cx}" y2="{cy+18}" stroke="#666" stroke-width="0.8"/>\n'

    svg += '</svg>'
    return svg


def svg_shapes(shape, color=None):
    """SVG showing a geometric shape."""
    if color is None:
        color = SHAPE_COLORS.get(shape, random.choice(COLORS_SVG))
    svg = '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '  <rect width="200" height="120" fill="#FFFEF5" rx="8"/>\n'

    if shape == "circle":
        svg += f'  <circle cx="100" cy="60" r="40" fill="{color}" stroke="#333" stroke-width="2"/>\n'
    elif shape == "square":
        svg += f'  <rect x="55" y="15" width="90" height="90" fill="{color}" stroke="#333" stroke-width="2"/>\n'
    elif shape == "triangle":
        svg += f'  <polygon points="100,10 40,110 160,110" fill="{color}" stroke="#333" stroke-width="2"/>\n'
    elif shape == "rectangle":
        svg += f'  <rect x="30" y="25" width="140" height="70" fill="{color}" stroke="#333" stroke-width="2"/>\n'

    svg += '</svg>'
    return svg


def svg_comparison(items_left, items_right, obj_type="circle"):
    """SVG showing two groups for comparison."""
    color_l = random.choice(COLORS_SVG)
    color_r = random.choice(COLORS_SVG)
    while color_r == color_l:
        color_r = random.choice(COLORS_SVG)

    svg = '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '  <rect width="200" height="120" fill="#FFFEF5" rx="8"/>\n'
    svg += '  <line x1="100" y1="5" x2="100" y2="115" stroke="#CCC" stroke-width="1" stroke-dasharray="4"/>\n'
    svg += '  <text x="50" y="12" text-anchor="middle" font-size="8" fill="#666">Group A</text>\n'
    svg += '  <text x="150" y="12" text-anchor="middle" font-size="8" fill="#666">Group B</text>\n'

    for i in range(items_left):
        r = i // 3
        c = i % 3
        cx = 15 + c * 28 + 12
        cy = 20 + r * 28 + 12
        svg += f'  <circle cx="{cx}" cy="{cy}" r="10" fill="{color_l}" stroke="#333" stroke-width="1"/>\n'

    for i in range(items_right):
        r = i // 3
        c = i % 3
        cx = 110 + c * 28 + 12
        cy = 20 + r * 28 + 12
        svg += f'  <circle cx="{cx}" cy="{cy}" r="10" fill="{color_r}" stroke="#333" stroke-width="1"/>\n'

    svg += '</svg>'
    return svg


def svg_pattern(pattern_items, missing_index=-1):
    """SVG showing a repeating pattern with optional missing piece."""
    svg = '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '  <rect width="200" height="120" fill="#FFFEF5" rx="8"/>\n'

    n = len(pattern_items)
    gap = 180 / (n + 1)

    for i, item in enumerate(pattern_items):
        cx = 10 + (i + 1) * gap
        cy = 60

        if i == missing_index:
            svg += f'  <rect x="{cx-12}" y="{cy-12}" width="24" height="24" fill="none" stroke="#999" stroke-width="2" stroke-dasharray="3"/>\n'
            svg += f'  <text x="{cx}" y="{cy+4}" text-anchor="middle" font-size="14" fill="#999">?</text>\n'
        else:
            shape, color = item
            if shape == "circle":
                svg += f'  <circle cx="{cx}" cy="{cy}" r="12" fill="{color}" stroke="#333" stroke-width="1"/>\n'
            elif shape == "square":
                svg += f'  <rect x="{cx-10}" y="{cy-10}" width="20" height="20" fill="{color}" stroke="#333" stroke-width="1"/>\n'
            elif shape == "triangle":
                svg += f'  <polygon points="{cx},{cy-12} {cx-10},{cy+8} {cx+10},{cy+8}" fill="{color}" stroke="#333" stroke-width="1"/>\n'

    svg += '</svg>'
    return svg


def svg_number_line(start, end, highlight=None):
    """SVG showing a number line segment."""
    svg = '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '  <rect width="200" height="120" fill="#FFFEF5" rx="8"/>\n'

    count = end - start + 1
    x_start = 15
    x_end = 185
    gap = (x_end - x_start) / (count - 1) if count > 1 else 0
    y = 70

    svg += f'  <line x1="{x_start}" y1="{y}" x2="{x_end}" y2="{y}" stroke="#333" stroke-width="2"/>\n'

    for i in range(count):
        x = x_start + i * gap
        num = start + i
        svg += f'  <line x1="{x}" y1="{y-5}" x2="{x}" y2="{y+5}" stroke="#333" stroke-width="1.5"/>\n'

        if highlight is not None and num == highlight:
            svg += f'  <circle cx="{x}" cy="{y}" r="8" fill="#FF6B6B" opacity="0.5"/>\n'
            svg += f'  <text x="{x}" y="{y+20}" text-anchor="middle" font-size="9" fill="#FF6B6B" font-weight="bold">{num}</text>\n'
        else:
            svg += f'  <text x="{x}" y="{y+20}" text-anchor="middle" font-size="8" fill="#333">{num}</text>\n'

    svg += '</svg>'
    return svg


def svg_coins(coins_list):
    """SVG showing Indian coins."""
    svg = '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '  <rect width="200" height="120" fill="#FFFEF5" rx="8"/>\n'

    coin_colors = {1: "#C0C0C0", 2: "#C0C0C0", 5: "#C0C0C0", 10: "#DAA520"}
    coin_sizes = {1: 14, 2: 16, 5: 18, 10: 20}

    n = len(coins_list)
    gap = 180 / (n + 1)

    for i, val in enumerate(coins_list):
        cx = 10 + (i + 1) * gap
        cy = 60
        r = coin_sizes.get(val, 15)
        color = coin_colors.get(val, "#C0C0C0")

        svg += f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" stroke="#8B7355" stroke-width="2"/>\n'
        svg += f'  <circle cx="{cx}" cy="{cy}" r="{r-3}" fill="none" stroke="#8B7355" stroke-width="0.5"/>\n'
        svg += f'  <text x="{cx}" y="{cy-2}" text-anchor="middle" font-size="7" fill="#333">₹</text>\n'
        svg += f'  <text x="{cx}" y="{cy+8}" text-anchor="middle" font-size="9" fill="#333" font-weight="bold">{val}</text>\n'

    svg += '</svg>'
    return svg


def svg_measurement(type_m, val1, val2):
    """SVG for measurement comparisons."""
    svg = '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '  <rect width="200" height="120" fill="#FFFEF5" rx="8"/>\n'

    if type_m == "length":
        w1 = 20 + val1 * 15
        w2 = 20 + val2 * 15
        svg += f'  <rect x="20" y="30" width="{w1}" height="15" fill="#4ECDC4" stroke="#333" stroke-width="1" rx="3"/>\n'
        svg += f'  <text x="10" y="42" font-size="8" fill="#333">A</text>\n'
        svg += f'  <rect x="20" y="70" width="{w2}" height="15" fill="#FF6B6B" stroke="#333" stroke-width="1" rx="3"/>\n'
        svg += f'  <text x="10" y="82" font-size="8" fill="#333">B</text>\n'
    elif type_m == "weight":
        # Simple balance scale
        svg += '  <line x1="100" y1="20" x2="100" y2="50" stroke="#666" stroke-width="3"/>\n'
        svg += '  <polygon points="95,20 105,20 100,10" fill="#666"/>\n'
        tilt = 5 if val1 > val2 else (-5 if val2 > val1 else 0)
        svg += f'  <line x1="40" y1="{55+tilt}" x2="160" y2="{55-tilt}" stroke="#333" stroke-width="2"/>\n'
        svg += f'  <rect x="25" y="{55+tilt}" width="35" height="25" fill="#4ECDC4" stroke="#333" rx="3"/>\n'
        svg += f'  <text x="42" y="{72+tilt}" text-anchor="middle" font-size="8" fill="#333">A</text>\n'
        svg += f'  <rect x="140" y="{55-tilt}" width="35" height="25" fill="#FF6B6B" stroke="#333" rx="3"/>\n'
        svg += f'  <text x="157" y="{72-tilt}" text-anchor="middle" font-size="8" fill="#333">B</text>\n'

    svg += '</svg>'
    return svg


def svg_tally(count):
    """SVG showing tally marks."""
    svg = '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '  <rect width="200" height="120" fill="#FFFEF5" rx="8"/>\n'

    groups = count // 5
    remainder = count % 5
    x = 20

    for g in range(groups):
        for i in range(4):
            lx = x + i * 8
            svg += f'  <line x1="{lx}" y1="35" x2="{lx}" y2="85" stroke="#333" stroke-width="2.5"/>\n'
        svg += f'  <line x1="{x-3}" y1="60" x2="{x+27}" y2="50" stroke="#FF6B6B" stroke-width="2.5"/>\n'
        x += 40

    for i in range(remainder):
        lx = x + i * 8
        svg += f'  <line x1="{lx}" y1="35" x2="{lx}" y2="85" stroke="#333" stroke-width="2.5"/>\n'

    svg += '</svg>'
    return svg


def svg_clock_simple(description):
    """Simple clock-like visual for time questions."""
    svg = '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '  <rect width="200" height="120" fill="#FFFEF5" rx="8"/>\n'
    svg += '  <circle cx="100" cy="60" r="45" fill="#FFF" stroke="#333" stroke-width="2"/>\n'
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        x1 = 100 + 38 * math.cos(angle)
        y1 = 60 + 38 * math.sin(angle)
        x2 = 100 + 42 * math.cos(angle)
        y2 = 60 + 42 * math.sin(angle)
        svg += f'  <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#333" stroke-width="2"/>\n'
        tx = 100 + 33 * math.cos(angle)
        ty = 60 + 33 * math.sin(angle) + 3
        svg += f'  <text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" font-size="7" fill="#333">{i if i > 0 else 12}</text>\n'
    svg += '</svg>'
    return svg


# ============================================================
# CHAPTER QUESTION GENERATORS
# ============================================================

def gen_ch1_numbers_1_to_9():
    """Chapter 1: Numbers 1 to 9"""
    qs = []

    # Type 1: Count objects
    for i in range(6):
        count = random.randint(1, 9)
        obj = random.choice(["mangoes", "flowers", "balloons", "stars", "diyas"])
        obj_svg = {"mangoes": "mango", "flowers": "flower", "balloons": "balloon", "stars": "star", "diyas": "circle"}
        name = get_name()
        qid = make_id(len(questions) + len(qs) + 1)

        svg_content = svg_counting_objects(count, obj_svg[obj])
        svg_files[qid] = svg_content

        wrongs = wrong_choices(count, 1, 9)
        all_choices = [str(count)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(count))

        qs.append({
            "id": qid,
            "stem": f"{name} sees some {obj} in the picture. How many {obj} are there?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"{count} {obj} arranged in rows",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Try counting each object one by one, pointing to each as you count.",
                str((correct_idx + 2) % 4): "Be careful not to skip any objects. Count slowly.",
                str((correct_idx + 3) % 4): "Make sure you count each object only once."
            },
            "tags": ["counting", "numbers_1_9", "visual_counting"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch1: Numbers 1 to 9",
            "hint": {
                "level_0": "Count means telling how many things are there.",
                "level_1": "Touch each object and say the number aloud: 1, 2, 3...",
                "level_2": f"Point to each {obj[:-1] if obj.endswith('s') else obj} one by one and count. The last number you say is the answer."
            },
            "curriculum_tags": ["NCERT_1_1"],
            "irt_params": irt_params("easy")
        })

    # Type 2: Number names
    number_words = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine"}
    for i in range(5):
        num = random.randint(1, 9)
        qid = make_id(len(questions) + len(qs) + 1)

        correct = number_words[num]
        wrong_nums = [n for n in range(1, 10) if n != num]
        wrongs = [number_words[w] for w in random.sample(wrong_nums, 3)]
        all_choices = [correct] + wrongs
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": f"What is the number name for {num}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Think about the counting song: one, two, three, four...",
                str((correct_idx + 2) % 4): "Try counting from one up to this number.",
                str((correct_idx + 3) % 4): "Remember the order: one, two, three, four, five, six, seven, eight, nine."
            },
            "tags": ["number_names", "numbers_1_9"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch1: Numbers 1 to 9",
            "hint": {
                "level_0": "Every number has a word name.",
                "level_1": "Count on your fingers: one, two, three... which finger matches this number?",
                "level_2": f"Count up: one (1), two (2), three (3)... keep going until you reach {num}."
            },
            "curriculum_tags": ["NCERT_1_1"],
            "irt_params": irt_params("easy")
        })

    # Type 3: Which number comes after/before
    for i in range(5):
        num = random.randint(2, 8)
        direction = random.choice(["after", "before"])
        correct = num + 1 if direction == "after" else num - 1
        qid = make_id(len(questions) + len(qs) + 1)

        wrongs = wrong_choices(correct, 1, 9)
        all_choices = [str(correct)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(correct))

        name = get_name()
        qs.append({
            "id": qid,
            "stem": f"{name} is counting. Which number comes just {direction} {num}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy" if direction == "after" else "medium",
            "difficulty_score": difficulty_score("easy" if direction == "after" else "medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): f"Think about counting forward or backward from {num}.",
                str((correct_idx + 2) % 4): f"'{direction.capitalize()}' means the number that comes next when counting {'up' if direction == 'after' else 'down'}.",
                str((correct_idx + 3) % 4): "Use the number line in your mind: 1, 2, 3, 4, 5, 6, 7, 8, 9."
            },
            "tags": ["number_sequence", "numbers_1_9", "before_after"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch1: Numbers 1 to 9",
            "hint": {
                "level_0": f"'{direction.capitalize()}' means the very next number when counting {'up' if direction == 'after' else 'backward'}.",
                "level_1": f"Say the numbers: ...{num-1}, {num}, ___. What goes in the blank?",
                "level_2": f"Count {'forward' if direction == 'after' else 'backward'} from {num}. The next number is {correct}."
            },
            "curriculum_tags": ["NCERT_1_1"],
            "irt_params": irt_params("easy" if direction == "after" else "medium")
        })

    # Type 4: Comparing numbers
    for i in range(4):
        a, b = random.sample(range(1, 10), 2)
        compare = random.choice(["greater", "smaller"])
        correct = max(a, b) if compare == "greater" else min(a, b)
        qid = make_id(len(questions) + len(qs) + 1)

        svg_content = svg_comparison(a, b)
        svg_files[qid] = svg_content

        wrongs = wrong_choices(correct, 1, 9)
        all_choices = [str(correct)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(correct))

        qs.append({
            "id": qid,
            "stem": f"Look at Group A ({a}) and Group B ({b}). Which number is {compare}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"Two groups of circles: Group A has {a}, Group B has {b}",
            "diagnostics": {
                str((correct_idx + 1) % 4): f"'{compare.capitalize()}' means {'more' if compare == 'greater' else 'less'}.",
                str((correct_idx + 2) % 4): "Count both groups carefully and compare.",
                str((correct_idx + 3) % 4): "The group with more circles has the greater number."
            },
            "tags": ["comparing", "numbers_1_9", "greater_smaller"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch1: Numbers 1 to 9",
            "hint": {
                "level_0": f"'{compare.capitalize()}' means the number that is {'bigger' if compare == 'greater' else 'smaller'}.",
                "level_1": "Count the objects in each group. Which group has more (or fewer)?",
                "level_2": f"Group A has {a} and Group B has {b}. {correct} is {compare} because it is {'more' if compare == 'greater' else 'less'}."
            },
            "curriculum_tags": ["NCERT_1_1"],
            "irt_params": irt_params("medium")
        })

    # Type 5: Story-based counting
    for i in range(3):
        obj = get_objects("fruits")
        count = random.randint(2, 9)
        name = get_name()
        qid = make_id(len(questions) + len(qs) + 1)

        svg_content = svg_counting_objects(count, "mango" if "mango" in obj else "circle")
        svg_files[qid] = svg_content

        wrongs = wrong_choices(count, 1, 9)
        all_choices = [str(count)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(count))

        contexts = [
            f"{name} has a basket. Count the {obj} in {name}'s basket. How many are there?",
            f"{name} went to the market and bought some {obj}. Count them in the picture.",
            f"At {name}'s birthday party, there are {obj} on the table. How many can you count?"
        ]

        qs.append({
            "id": qid,
            "stem": random.choice(contexts),
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"{count} {obj} shown in picture",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Count carefully, one by one.",
                str((correct_idx + 2) % 4): "Touch each one as you count to not miss any.",
                str((correct_idx + 3) % 4): "Start from the top-left and count row by row."
            },
            "tags": ["counting", "numbers_1_9", "word_problem"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch1: Numbers 1 to 9",
            "hint": {
                "level_0": "Look at the picture carefully and count each item.",
                "level_1": "Point to each item as you count: 1, 2, 3...",
                "level_2": f"Count each {obj[:-1] if obj.endswith('s') else obj} in the picture from left to right."
            },
            "curriculum_tags": ["NCERT_1_1"],
            "irt_params": irt_params("easy")
        })

    return qs


def gen_ch2_numbers_10_to_20():
    """Chapter 2: Numbers 10 to 20"""
    qs = []

    # Type 1: Count objects (10-20)
    for i in range(5):
        count = random.randint(10, 20)
        obj = random.choice(["balloons", "stars", "flowers", "diyas"])
        obj_svg = {"balloons": "balloon", "stars": "star", "flowers": "flower", "diyas": "circle"}
        name = get_name()
        qid = make_id(len(questions) + len(qs) + 1)

        svg_content = svg_counting_objects(count, obj_svg[obj])
        svg_files[qid] = svg_content

        wrongs = wrong_choices(count, 10, 20)
        all_choices = [str(count)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(count))

        qs.append({
            "id": qid,
            "stem": f"{name} decorated the classroom with {obj}. Count the {obj} in the picture.",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"{count} {obj} arranged in rows",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Try counting in groups of 5 to make it easier.",
                str((correct_idx + 2) % 4): "Count each row carefully, then add the rows together.",
                str((correct_idx + 3) % 4): "With bigger numbers, count row by row: 5, 10, 15..."
            },
            "tags": ["counting", "numbers_10_20", "visual_counting"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch2: Numbers 10 to 20",
            "hint": {
                "level_0": "For bigger numbers, try grouping into tens and ones.",
                "level_1": "Count the first row (5), then continue from there.",
                "level_2": f"Count row by row. Each full row has 5. Count all rows and any extra ones."
            },
            "curriculum_tags": ["NCERT_1_2"],
            "irt_params": irt_params("medium")
        })

    # Type 2: Tens and ones
    for i in range(5):
        num = random.randint(11, 19)
        tens = 1
        ones = num - 10
        qid = make_id(len(questions) + len(qs) + 1)

        question_types = [
            (f"The number {num} has 1 ten and how many ones?", str(ones)),
            (f"What number has 1 ten and {ones} ones?", str(num)),
        ]
        stem, correct = random.choice(question_types)

        if correct == str(ones):
            wrongs = wrong_choices(ones, 0, 9)
        else:
            wrongs = wrong_choices(num, 10, 19)

        all_choices = [correct] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "A 'ten' is a group of 10. 'Ones' are the leftover single items.",
                str((correct_idx + 2) % 4): "Think of teen numbers as 10 + something.",
                str((correct_idx + 3) % 4): f"{num} = 10 + {ones}. The digit after 1 tells you the ones."
            },
            "tags": ["place_value", "numbers_10_20", "tens_ones"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch2: Numbers 10 to 20",
            "hint": {
                "level_0": "Teen numbers are made of 1 ten plus some ones.",
                "level_1": f"Think: {num} is the same as 10 + how many more?",
                "level_2": f"{num} = 10 + {ones}. So there is 1 ten and {ones} ones."
            },
            "curriculum_tags": ["NCERT_1_2"],
            "irt_params": irt_params("medium")
        })

    # Type 3: Number sequence 10-20
    for i in range(5):
        start = random.randint(10, 16)
        missing_pos = random.randint(1, 3)
        sequence = list(range(start, start + 5))
        missing_val = sequence[missing_pos]
        qid = make_id(len(questions) + len(qs) + 1)

        display = [str(n) if idx != missing_pos else "___" for idx, n in enumerate(sequence)]

        wrongs = wrong_choices(missing_val, 10, 20)
        all_choices = [str(missing_val)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(missing_val))

        qs.append({
            "id": qid,
            "stem": f"Fill in the missing number: {', '.join(display)}",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Read the numbers in order. What comes between the two around the blank?",
                str((correct_idx + 2) % 4): "These numbers go up by 1 each time.",
                str((correct_idx + 3) % 4): "Count forward: each number is one more than the last."
            },
            "tags": ["number_sequence", "numbers_10_20", "missing_number"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch2: Numbers 10 to 20",
            "hint": {
                "level_0": "The numbers are in counting order.",
                "level_1": f"Look at the number before the blank ({sequence[missing_pos-1]}) and count one more.",
                "level_2": f"After {sequence[missing_pos-1]} comes {missing_val}."
            },
            "curriculum_tags": ["NCERT_1_2"],
            "irt_params": irt_params("easy")
        })

    # Type 4: Before/after/between for teen numbers
    for i in range(4):
        num = random.randint(11, 19)
        qtype = random.choice(["before", "after", "between"])
        qid = make_id(len(questions) + len(qs) + 1)

        if qtype == "between":
            correct = num
            stem_text = f"Which number comes between {num-1} and {num+1}?"
        elif qtype == "after":
            correct = num + 1
            stem_text = f"Which number comes just after {num}?"
        else:
            correct = num - 1
            stem_text = f"Which number comes just before {num}?"

        wrongs = wrong_choices(correct, 10, 20)
        all_choices = [str(correct)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(correct))

        qs.append({
            "id": qid,
            "stem": stem_text,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): f"Think of the counting sequence around {num}.",
                str((correct_idx + 2) % 4): f"'{qtype}' tells you the position relative to the given number.",
                str((correct_idx + 3) % 4): "Use the number line: 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20."
            },
            "tags": ["number_sequence", "numbers_10_20", "before_after_between"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch2: Numbers 10 to 20",
            "hint": {
                "level_0": f"Think about counting order around {num}.",
                "level_1": f"Say the numbers: ...{num-1}, {num}, {num+1}...",
                "level_2": f"The number {qtype} {num} is {correct}."
            },
            "curriculum_tags": ["NCERT_1_2"],
            "irt_params": irt_params("easy")
        })

    # Type 5: Writing teen numbers in words
    teen_words = {10: "Ten", 11: "Eleven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen",
                  15: "Fifteen", 16: "Sixteen", 17: "Seventeen", 18: "Eighteen", 19: "Nineteen", 20: "Twenty"}
    for i in range(4):
        num = random.randint(10, 20)
        qid = make_id(len(questions) + len(qs) + 1)
        correct = teen_words[num]
        wrong_nums = [n for n in range(10, 21) if n != num]
        wrongs = [teen_words[w] for w in random.sample(wrong_nums, 3)]
        all_choices = [correct] + wrongs
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": f"What is the number name for {num}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Teen numbers have special names. Try saying them: ten, eleven, twelve...",
                str((correct_idx + 2) % 4): "Remember: 13 is thir-teen, 14 is four-teen, 15 is fif-teen...",
                str((correct_idx + 3) % 4): "Some teen number names don't follow the pattern (eleven, twelve)."
            },
            "tags": ["number_names", "numbers_10_20"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch2: Numbers 10 to 20",
            "hint": {
                "level_0": "Each number from 10 to 20 has a special name.",
                "level_1": "Count up saying the names: ten, eleven, twelve, thirteen...",
                "level_2": f"The number {num} is written as '{correct}'."
            },
            "curriculum_tags": ["NCERT_1_2"],
            "irt_params": irt_params("medium")
        })

    return qs


def gen_ch3_addition():
    """Chapter 3: Addition (single digit, sum up to 9)"""
    qs = []

    # Type 1: Simple addition with pictures
    for i in range(6):
        a = random.randint(1, 5)
        b = random.randint(1, 9 - a)
        total = a + b
        obj = random.choice(["mangoes", "balloons", "stars", "flowers"])
        obj_svg = {"mangoes": "mango", "balloons": "balloon", "stars": "star", "flowers": "flower"}
        name = get_name()
        qid = make_id(len(questions) + len(qs) + 1)

        svg_content = svg_comparison(a, b, "circle")
        svg_files[qid] = svg_content

        wrongs = wrong_choices(total, 1, 9)
        all_choices = [str(total)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(total))

        contexts = [
            f"{name} has {a} {obj}. {get_name()} gives {b} more. How many does {name} have now?",
            f"There are {a} {obj} on one plate and {b} on another. How many {obj} in all?",
            f"{name} picked {a} {obj} in the morning and {b} in the evening. How many total?",
        ]

        qs.append({
            "id": qid,
            "stem": random.choice(contexts),
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy" if total <= 5 else "medium",
            "difficulty_score": difficulty_score("easy" if total <= 5 else "medium"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"Two groups: {a} and {b} objects",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Addition means putting groups together.",
                str((correct_idx + 2) % 4): f"Start with {a} and count on {b} more.",
                str((correct_idx + 3) % 4): "Count all the objects in both groups together."
            },
            "tags": ["addition", "single_digit", "word_problem"],
            "topic": "ncert_g1_addition",
            "chapter": "Ch3: Addition",
            "hint": {
                "level_0": "Adding means finding how many in all when you put groups together.",
                "level_1": f"Start from {a} and count on: {a+1}, {a+2}... count {b} more times.",
                "level_2": f"{a} + {b} = {total}. Start at {a}, count {b} more: {', '.join(str(a+k) for k in range(1, b+1))}."
            },
            "curriculum_tags": ["NCERT_1_3"],
            "irt_params": irt_params("easy" if total <= 5 else "medium")
        })

    # Type 2: Addition number sentence
    for i in range(5):
        a = random.randint(1, 5)
        b = random.randint(1, 9 - a)
        total = a + b
        qid = make_id(len(questions) + len(qs) + 1)

        wrongs = wrong_choices(total, 1, 9)
        all_choices = [str(total)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(total))

        qs.append({
            "id": qid,
            "stem": f"What is {a} + {b} = ?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Use your fingers to add.",
                str((correct_idx + 2) % 4): f"Hold up {a} fingers, then raise {b} more.",
                str((correct_idx + 3) % 4): f"Count on from {a}: say {a}, then count {b} more numbers."
            },
            "tags": ["addition", "single_digit", "number_sentence"],
            "topic": "ncert_g1_addition",
            "chapter": "Ch3: Addition",
            "hint": {
                "level_0": "The + sign means add the numbers together.",
                "level_1": f"Use your fingers: show {a}, then show {b} more. Count all fingers.",
                "level_2": f"{a} + {b}: Start at {a}, count forward {b} times to get {total}."
            },
            "curriculum_tags": ["NCERT_1_3"],
            "irt_params": irt_params("easy")
        })

    # Type 3: Story problems with Indian context
    for i in range(6):
        a = random.randint(1, 5)
        b = random.randint(1, 9 - a)
        total = a + b
        name1 = get_boy()
        name2 = get_girl()
        qid = make_id(len(questions) + len(qs) + 1)

        stories = [
            f"{name1} has {a} marbles. He wins {b} more in a game. How many marbles does he have now?",
            f"{name2} made {a} rotis. Her mother made {b} more. How many rotis are there altogether?",
            f"There are {a} parrots on a tree. {b} more parrots fly in. How many parrots are on the tree now?",
            f"{name1} has {a} toy cars. His uncle gives him {b} more on Diwali. How many toy cars does he have?",
            f"{name2} planted {a} marigold seeds and {b} rose seeds. How many seeds did she plant in total?",
            f"At the bus stop, {a} people were waiting. {b} more people came. How many people are waiting now?",
        ]

        wrongs = wrong_choices(total, 1, 9)
        all_choices = [str(total)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(total))

        qs.append({
            "id": qid,
            "stem": stories[i % len(stories)],
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Look for words like 'more', 'altogether', 'total' — they mean add.",
                str((correct_idx + 2) % 4): f"Find the two numbers in the story ({a} and {b}) and add them.",
                str((correct_idx + 3) % 4): "Draw circles on paper to help you count."
            },
            "tags": ["addition", "word_problem", "indian_context"],
            "topic": "ncert_g1_addition",
            "chapter": "Ch3: Addition",
            "hint": {
                "level_0": "This is an addition story. Find the two numbers and add them.",
                "level_1": f"The story tells you about {a} and {b} things being put together.",
                "level_2": f"{a} + {b} = {total}."
            },
            "curriculum_tags": ["NCERT_1_3"],
            "irt_params": irt_params("medium")
        })

    # Type 4: Addition with zero
    for i in range(3):
        a = random.randint(1, 9)
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()
        obj = get_objects("items")

        wrongs = wrong_choices(a, 0, 9)
        all_choices = [str(a)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(a))

        qs.append({
            "id": qid,
            "stem": f"{name} has {a} {obj}. Nobody gives any more. How many {obj} does {name} have? ({a} + 0 = ?)",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Adding zero means nothing new is added.",
                str((correct_idx + 2) % 4): "Zero means 'nothing'. The number stays the same.",
                str((correct_idx + 3) % 4): "Any number plus zero equals that same number."
            },
            "tags": ["addition", "zero_property", "single_digit"],
            "topic": "ncert_g1_addition",
            "chapter": "Ch3: Addition",
            "hint": {
                "level_0": "Adding zero means you don't get any more.",
                "level_1": "If you have some things and get zero more, you still have the same amount.",
                "level_2": f"{a} + 0 = {a}. The answer is always the number itself."
            },
            "curriculum_tags": ["NCERT_1_3"],
            "irt_params": irt_params("easy")
        })

    # Type 5: Find the missing addend
    for i in range(3):
        total = random.randint(3, 9)
        a = random.randint(1, total - 1)
        b = total - a
        qid = make_id(len(questions) + len(qs) + 1)

        wrongs = wrong_choices(b, 0, 9)
        all_choices = [str(b)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(b))

        qs.append({
            "id": qid,
            "stem": f"{a} + ___ = {total}. What number goes in the blank?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Think: what do I add to the first number to get the total?",
                str((correct_idx + 2) % 4): f"Count up from {a} until you reach {total}.",
                str((correct_idx + 3) % 4): f"You can also think: {total} - {a} = ?"
            },
            "tags": ["addition", "missing_addend", "single_digit"],
            "topic": "ncert_g1_addition",
            "chapter": "Ch3: Addition",
            "hint": {
                "level_0": "Find what number you add to the first number to make the total.",
                "level_1": f"Start at {a} and count how many steps to reach {total}.",
                "level_2": f"{a} + {b} = {total}. The missing number is {b}."
            },
            "curriculum_tags": ["NCERT_1_3"],
            "irt_params": irt_params("hard")
        })

    return qs


def gen_ch4_subtraction():
    """Chapter 4: Subtraction (within 9)"""
    qs = []

    # Type 1: Taking away with visuals
    for i in range(6):
        total = random.randint(4, 9)
        taken = random.randint(1, total - 1)
        remaining = total - taken
        obj = random.choice(["laddoos", "toffees", "balloons", "mangoes", "kites"])
        name = get_name()
        qid = make_id(len(questions) + len(qs) + 1)

        svg_content = svg_counting_objects(total, "circle")
        svg_files[qid] = svg_content

        wrongs = wrong_choices(remaining, 0, 9)
        all_choices = [str(remaining)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(remaining))

        contexts = [
            f"{name} had {total} {obj}. {name} ate {taken}. How many are left?",
            f"There were {total} {obj}. {taken} flew away. How many remain?",
            f"{name} had {total} {obj} and gave {taken} to a friend. How many does {name} have now?",
        ]

        qs.append({
            "id": qid,
            "stem": random.choice(contexts),
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy" if remaining >= 3 else "medium",
            "difficulty_score": difficulty_score("easy" if remaining >= 3 else "medium"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"{total} objects shown (before taking away)",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Subtraction means taking away. Count what's left.",
                str((correct_idx + 2) % 4): f"Start with {total}, cross out {taken}, then count the rest.",
                str((correct_idx + 3) % 4): "Cover some with your hand and count the uncovered ones."
            },
            "tags": ["subtraction", "taking_away", "within_9"],
            "topic": "ncert_g1_subtraction",
            "chapter": "Ch4: Subtraction",
            "hint": {
                "level_0": "Subtraction means taking some away from a group.",
                "level_1": f"Start with {total}, take away {taken}. Count what remains.",
                "level_2": f"{total} - {taken} = {remaining}. Count backward {taken} times from {total}."
            },
            "curriculum_tags": ["NCERT_1_4"],
            "irt_params": irt_params("easy" if remaining >= 3 else "medium")
        })

    # Type 2: Subtraction number sentences
    for i in range(5):
        a = random.randint(3, 9)
        b = random.randint(1, a - 1)
        result = a - b
        qid = make_id(len(questions) + len(qs) + 1)

        wrongs = wrong_choices(result, 0, 9)
        all_choices = [str(result)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(result))

        qs.append({
            "id": qid,
            "stem": f"What is {a} - {b} = ?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Use your fingers: show the bigger number, then put down some.",
                str((correct_idx + 2) % 4): f"Start at {a} and count back {b} times.",
                str((correct_idx + 3) % 4): "The minus sign (-) means take away."
            },
            "tags": ["subtraction", "number_sentence", "within_9"],
            "topic": "ncert_g1_subtraction",
            "chapter": "Ch4: Subtraction",
            "hint": {
                "level_0": "The minus sign means take away.",
                "level_1": f"Hold up {a} fingers. Put down {b}. Count the ones still up.",
                "level_2": f"{a} - {b}: Count back from {a}: {', '.join(str(a-k) for k in range(1, b+1))}. Answer is {result}."
            },
            "curriculum_tags": ["NCERT_1_4"],
            "irt_params": irt_params("easy")
        })

    # Type 3: Story problems
    for i in range(6):
        a = random.randint(4, 9)
        b = random.randint(1, a - 1)
        result = a - b
        name = get_name()
        qid = make_id(len(questions) + len(qs) + 1)

        stories = [
            f"{name} had {a} crayons. {b} broke. How many good crayons are left?",
            f"A tree had {a} parrots. {b} flew away. How many are still on the tree?",
            f"{name} had {a} rotis on the plate. The family ate {b}. How many rotis are left?",
            f"There were {a} children playing. {b} went home. How many are still playing?",
            f"{name} had {a} stickers. {b} fell off and got lost. How many stickers remain?",
            f"The autorickshaw had {a} passengers. {b} got off at the next stop. How many are still riding?",
        ]

        wrongs = wrong_choices(result, 0, 9)
        all_choices = [str(result)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(result))

        qs.append({
            "id": qid,
            "stem": stories[i % len(stories)],
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Look for words like 'left', 'remain', 'flew away' — they mean subtract.",
                str((correct_idx + 2) % 4): f"Find the two numbers ({a} and {b}) — subtract the smaller from the bigger.",
                str((correct_idx + 3) % 4): "Draw pictures to help: draw the first amount, cross out the second."
            },
            "tags": ["subtraction", "word_problem", "indian_context"],
            "topic": "ncert_g1_subtraction",
            "chapter": "Ch4: Subtraction",
            "hint": {
                "level_0": "Words like 'left', 'remain', 'went away' tell you to subtract.",
                "level_1": f"You started with {a} and lost {b}. What remains?",
                "level_2": f"{a} - {b} = {result}."
            },
            "curriculum_tags": ["NCERT_1_4"],
            "irt_params": irt_params("medium")
        })

    # Type 4: Subtraction from itself (result 0)
    for i in range(2):
        n = random.randint(2, 9)
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()
        obj = get_objects("food")

        wrongs = wrong_choices(0, 0, 5)
        all_choices = [str(0)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(0))

        qs.append({
            "id": qid,
            "stem": f"{name} had {n} {obj} and ate all {n}. How many {obj} are left? ({n} - {n} = ?)",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "If you take away everything, nothing is left.",
                str((correct_idx + 2) % 4): "Any number minus itself equals zero.",
                str((correct_idx + 3) % 4): "Zero means nothing remains."
            },
            "tags": ["subtraction", "zero_result", "within_9"],
            "topic": "ncert_g1_subtraction",
            "chapter": "Ch4: Subtraction",
            "hint": {
                "level_0": "If all items are taken away, nothing is left.",
                "level_1": f"All {n} were eaten. What remains?",
                "level_2": f"{n} - {n} = 0. Nothing is left."
            },
            "curriculum_tags": ["NCERT_1_4"],
            "irt_params": irt_params("easy")
        })

    # Type 5: Difference/comparison
    for i in range(4):
        a = random.randint(3, 9)
        b = random.randint(1, a - 1)
        diff = a - b
        name1 = get_boy()
        name2 = get_girl()
        qid = make_id(len(questions) + len(qs) + 1)

        svg_content = svg_comparison(a, b)
        svg_files[qid] = svg_content

        wrongs = wrong_choices(diff, 0, 9)
        all_choices = [str(diff)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(diff))

        qs.append({
            "id": qid,
            "stem": f"{name1} has {a} marbles and {name2} has {b}. How many more does {name1} have?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"Two groups: {a} and {b} circles for comparison",
            "diagnostics": {
                str((correct_idx + 1) % 4): "'How many more' means find the difference.",
                str((correct_idx + 2) % 4): "Match the objects in pairs. The unmatched ones are the difference.",
                str((correct_idx + 3) % 4): "Subtract the smaller number from the bigger number."
            },
            "tags": ["subtraction", "comparison", "difference"],
            "topic": "ncert_g1_subtraction",
            "chapter": "Ch4: Subtraction",
            "hint": {
                "level_0": "'How many more' means finding the difference between two numbers.",
                "level_1": f"Compare {a} and {b}. Count how many extra the bigger group has.",
                "level_2": f"{a} - {b} = {diff}. {name1} has {diff} more than {name2}."
            },
            "curriculum_tags": ["NCERT_1_4"],
            "irt_params": irt_params("hard")
        })

    return qs


def gen_ch5_numbers_21_to_50():
    """Chapter 5: Numbers 21 to 50"""
    qs = []

    # Type 1: Skip counting by 2s
    for i in range(4):
        start = random.choice([20, 22, 24, 30, 32])
        seq = list(range(start, start + 10, 2))
        missing_idx = random.randint(1, 3)
        missing_val = seq[missing_idx]
        display = [str(n) if idx != missing_idx else "___" for idx, n in enumerate(seq)]
        qid = make_id(len(questions) + len(qs) + 1)

        wrongs = wrong_choices(missing_val, 21, 50)
        all_choices = [str(missing_val)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(missing_val))

        qs.append({
            "id": qid,
            "stem": f"Skip count by 2: {', '.join(display)}. What is the missing number?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Skip counting by 2 means adding 2 each time.",
                str((correct_idx + 2) % 4): f"Look at the numbers around the blank. They go up by 2.",
                str((correct_idx + 3) % 4): "Each number is 2 more than the one before it."
            },
            "tags": ["skip_counting", "numbers_21_50", "count_by_2"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch5: Numbers 21 to 50",
            "hint": {
                "level_0": "Skip counting by 2 means jumping over one number each time.",
                "level_1": f"The number before the blank is {seq[missing_idx-1]}. Add 2.",
                "level_2": f"{seq[missing_idx-1]} + 2 = {missing_val}."
            },
            "curriculum_tags": ["NCERT_1_5"],
            "irt_params": irt_params("medium")
        })

    # Type 2: Skip counting by 10s
    for i in range(4):
        seq = [10, 20, 30, 40, 50]
        missing_idx = random.randint(1, 3)
        missing_val = seq[missing_idx]
        display = [str(n) if idx != missing_idx else "___" for idx, n in enumerate(seq)]
        qid = make_id(len(questions) + len(qs) + 1)

        wrongs = wrong_choices(missing_val, 10, 50)
        all_choices = [str(missing_val)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(missing_val))

        name = get_name()
        qs.append({
            "id": qid,
            "stem": f"{name} is counting by tens: {', '.join(display)}. What number is missing?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Counting by 10: each jump adds 10.",
                str((correct_idx + 2) % 4): "The tens go: 10, 20, 30, 40, 50.",
                str((correct_idx + 3) % 4): "Add 10 to the number before the blank."
            },
            "tags": ["skip_counting", "numbers_21_50", "count_by_10"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch5: Numbers 21 to 50",
            "hint": {
                "level_0": "Skip counting by 10 means adding 10 each time.",
                "level_1": f"What is {seq[missing_idx-1]} + 10?",
                "level_2": f"{seq[missing_idx-1]} + 10 = {missing_val}."
            },
            "curriculum_tags": ["NCERT_1_5"],
            "irt_params": irt_params("easy")
        })

    # Type 3: Tens and ones in 21-50
    for i in range(5):
        num = random.randint(21, 50)
        tens = num // 10
        ones = num % 10
        qid = make_id(len(questions) + len(qs) + 1)

        q_variant = random.choice(["tens", "ones", "number"])
        if q_variant == "tens":
            stem = f"How many tens are in the number {num}?"
            correct = str(tens)
            wrongs = wrong_choices(tens, 1, 5)
        elif q_variant == "ones":
            stem = f"How many ones are in the number {num}?"
            correct = str(ones)
            wrongs = wrong_choices(ones, 0, 9)
        else:
            stem = f"Which number has {tens} tens and {ones} ones?"
            correct = str(num)
            wrongs = wrong_choices(num, 21, 50)

        all_choices = [correct] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "The first digit tells tens, the second digit tells ones.",
                str((correct_idx + 2) % 4): f"In {num}, the left digit ({tens}) is tens and right digit ({ones}) is ones.",
                str((correct_idx + 3) % 4): "Tens are groups of 10. Ones are the single items."
            },
            "tags": ["place_value", "numbers_21_50", "tens_ones"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch5: Numbers 21 to 50",
            "hint": {
                "level_0": "Two-digit numbers have a tens place and a ones place.",
                "level_1": f"Look at {num}: the first digit is tens, second is ones.",
                "level_2": f"{num} = {tens} tens + {ones} ones = {tens}0 + {ones}."
            },
            "curriculum_tags": ["NCERT_1_5"],
            "irt_params": irt_params("medium")
        })

    # Type 4: Ordering/comparing numbers 21-50
    for i in range(5):
        nums = random.sample(range(21, 50), 2)
        a, b = nums
        compare = random.choice(["greater", "smaller"])
        correct = max(a, b) if compare == "greater" else min(a, b)
        qid = make_id(len(questions) + len(qs) + 1)

        wrongs = wrong_choices(correct, 21, 50)
        all_choices = [str(correct)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(correct))

        qs.append({
            "id": qid,
            "stem": f"Which number is {compare}: {a} or {b}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): f"Compare the tens first. If they're the same, compare ones.",
                str((correct_idx + 2) % 4): "The number further along when counting is greater.",
                str((correct_idx + 3) % 4): "Think about the number line: numbers to the right are greater."
            },
            "tags": ["comparing", "numbers_21_50", "greater_smaller"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch5: Numbers 21 to 50",
            "hint": {
                "level_0": f"'{compare.capitalize()}' means {'bigger' if compare == 'greater' else 'smaller'}.",
                "level_1": "First compare the tens digit. If equal, compare the ones digit.",
                "level_2": f"Between {a} and {b}, {correct} is {compare}."
            },
            "curriculum_tags": ["NCERT_1_5"],
            "irt_params": irt_params("medium")
        })

    # Type 5: Number sequence fill-in
    for i in range(5):
        start = random.randint(21, 45)
        seq = list(range(start, start + 5))
        missing_idx = random.randint(1, 3)
        missing_val = seq[missing_idx]
        display = [str(n) if idx != missing_idx else "___" for idx, n in enumerate(seq)]
        qid = make_id(len(questions) + len(qs) + 1)

        wrongs = wrong_choices(missing_val, 21, 50)
        all_choices = [str(missing_val)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(missing_val))

        qs.append({
            "id": qid,
            "stem": f"What number is missing? {', '.join(display)}",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "These numbers go up by 1 each time.",
                str((correct_idx + 2) % 4): "Look at the number before the blank and add 1.",
                str((correct_idx + 3) % 4): "Count forward from the beginning of the sequence."
            },
            "tags": ["number_sequence", "numbers_21_50", "missing_number"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch5: Numbers 21 to 50",
            "hint": {
                "level_0": "These are counting numbers — each one is 1 more than the last.",
                "level_1": f"The number before the blank is {seq[missing_idx-1]}. What comes next?",
                "level_2": f"{seq[missing_idx-1]} + 1 = {missing_val}."
            },
            "curriculum_tags": ["NCERT_1_5"],
            "irt_params": irt_params("easy")
        })

    return qs


def gen_ch6_numbers_51_to_100():
    """Chapter 6: Numbers 51 to 100"""
    qs = []

    # Type 1: Before/after/between
    for i in range(5):
        num = random.randint(52, 98)
        qtype = random.choice(["before", "after", "between"])
        qid = make_id(len(questions) + len(qs) + 1)

        if qtype == "between":
            correct = num
            stem_text = f"Which number comes between {num-1} and {num+1}?"
        elif qtype == "after":
            correct = num + 1
            stem_text = f"Which number comes just after {num}?"
        else:
            correct = num - 1
            stem_text = f"Which number comes just before {num}?"

        wrongs = wrong_choices(correct, 51, 100)
        all_choices = [str(correct)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(correct))

        qs.append({
            "id": qid,
            "stem": stem_text,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): f"Think about counting around {num}.",
                str((correct_idx + 2) % 4): "Before means one less, after means one more.",
                str((correct_idx + 3) % 4): "Count carefully: ...the number, then the next..."
            },
            "tags": ["number_sequence", "numbers_51_100", "before_after_between"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch6: Numbers 51 to 100",
            "hint": {
                "level_0": f"Think of counting order near {num}.",
                "level_1": f"...{num-1}, {num}, {num+1}...",
                "level_2": f"The answer is {correct}."
            },
            "curriculum_tags": ["NCERT_1_6"],
            "irt_params": irt_params("medium")
        })

    # Type 2: Number patterns (skip counting by 5)
    for i in range(4):
        start = random.choice([50, 55, 60, 65, 70])
        seq = list(range(start, start + 25, 5))[:5]
        missing_idx = random.randint(1, 3)
        missing_val = seq[missing_idx]
        display = [str(n) if idx != missing_idx else "___" for idx, n in enumerate(seq)]
        qid = make_id(len(questions) + len(qs) + 1)

        wrongs = wrong_choices(missing_val, 50, 100)
        all_choices = [str(missing_val)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(missing_val))

        qs.append({
            "id": qid,
            "stem": f"Skip count by 5: {', '.join(display)}. What is the missing number?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Each number is 5 more than the previous one.",
                str((correct_idx + 2) % 4): "Add 5 to the number before the blank.",
                str((correct_idx + 3) % 4): "Skip counting by 5: the ones digit goes 0, 5, 0, 5..."
            },
            "tags": ["skip_counting", "numbers_51_100", "count_by_5"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch6: Numbers 51 to 100",
            "hint": {
                "level_0": "Skip counting by 5 means adding 5 each time.",
                "level_1": f"What is {seq[missing_idx-1]} + 5?",
                "level_2": f"{seq[missing_idx-1]} + 5 = {missing_val}."
            },
            "curriculum_tags": ["NCERT_1_6"],
            "irt_params": irt_params("medium")
        })

    # Type 3: Place value 51-100
    for i in range(5):
        num = random.randint(51, 99)
        tens = num // 10
        ones = num % 10
        qid = make_id(len(questions) + len(qs) + 1)

        q_variant = random.choice(["tens", "ones", "expanded"])
        if q_variant == "tens":
            stem = f"How many tens are in {num}?"
            correct = str(tens)
            wrongs = wrong_choices(tens, 1, 9)
        elif q_variant == "ones":
            stem = f"How many ones are in {num}?"
            correct = str(ones)
            wrongs = wrong_choices(ones, 0, 9)
        else:
            stem = f"What is {tens}0 + {ones}?"
            correct = str(num)
            wrongs = wrong_choices(num, 51, 99)

        all_choices = [correct] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "The tens digit is on the left, ones digit on the right.",
                str((correct_idx + 2) % 4): f"In {num}, look at which position the digit is in.",
                str((correct_idx + 3) % 4): "Tens represent groups of ten, ones are singles."
            },
            "tags": ["place_value", "numbers_51_100", "tens_ones"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch6: Numbers 51 to 100",
            "hint": {
                "level_0": "Every 2-digit number has tens (left) and ones (right).",
                "level_1": f"In {num}: the {tens} is in the tens place, {ones} is in the ones place.",
                "level_2": f"{num} = {tens} tens + {ones} ones."
            },
            "curriculum_tags": ["NCERT_1_6"],
            "irt_params": irt_params("medium")
        })

    # Type 4: Comparing numbers
    for i in range(5):
        a = random.randint(51, 99)
        b = random.randint(51, 99)
        while b == a:
            b = random.randint(51, 99)
        compare = random.choice(["greatest", "smallest"])
        correct = max(a, b) if compare == "greatest" else min(a, b)
        qid = make_id(len(questions) + len(qs) + 1)

        # Add two more options
        extras = random.sample([n for n in range(51, 100) if n != a and n != b], 2)
        options = [a, b] + extras
        if compare == "greatest":
            correct = max(options)
        else:
            correct = min(options)

        all_choices = [str(n) for n in options]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(correct))

        qs.append({
            "id": qid,
            "stem": f"Which is the {compare} number?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Compare tens digits first, then ones.",
                str((correct_idx + 2) % 4): f"The {compare} means the {'biggest' if compare == 'greatest' else 'smallest'}.",
                str((correct_idx + 3) % 4): "Look at all four numbers and find which is largest/smallest."
            },
            "tags": ["comparing", "numbers_51_100", "ordering"],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch6: Numbers 51 to 100",
            "hint": {
                "level_0": f"Find the {'biggest' if compare == 'greatest' else 'smallest'} number.",
                "level_1": "First compare the tens digits. Higher tens = bigger number.",
                "level_2": f"Looking at all choices, {correct} is the {compare}."
            },
            "curriculum_tags": ["NCERT_1_6"],
            "irt_params": irt_params("hard")
        })

    # Type 5: Ordering numbers
    for i in range(4):
        nums = sorted(random.sample(range(51, 100), 4))
        order = random.choice(["ascending", "descending"])
        if order == "descending":
            correct_seq = list(reversed(nums))
        else:
            correct_seq = nums
        qid = make_id(len(questions) + len(qs) + 1)

        shuffled = nums.copy()
        random.shuffle(shuffled)

        # Present as "which comes first"
        correct = correct_seq[0]
        all_choices = [str(n) for n in shuffled]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(correct))

        direction = "smallest to largest" if order == "ascending" else "largest to smallest"
        qs.append({
            "id": qid,
            "stem": f"If we arrange {', '.join(str(n) for n in shuffled)} from {direction}, which number comes first?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): f"'{direction}' means starting with the {'smallest' if order == 'ascending' else 'largest'}.",
                str((correct_idx + 2) % 4): "Compare all the numbers and find the one that goes first.",
                str((correct_idx + 3) % 4): "Compare tens first, then ones, to find the right order."
            },
            "tags": ["ordering", "numbers_51_100", order],
            "topic": "ncert_g1_numbers",
            "chapter": "Ch6: Numbers 51 to 100",
            "hint": {
                "level_0": f"Find the {'smallest' if order == 'ascending' else 'largest'} number — it goes first.",
                "level_1": "Look at the tens digit of each number first.",
                "level_2": f"The first number in {direction} order is {correct}."
            },
            "curriculum_tags": ["NCERT_1_6"],
            "irt_params": irt_params("hard")
        })

    return qs


def gen_ch7_addition_subtraction():
    """Chapter 7: Addition & Subtraction together"""
    qs = []

    # Type 1: Fact families
    for i in range(5):
        a = random.randint(1, 7)
        b = random.randint(1, 9 - a)
        c = a + b
        qid = make_id(len(questions) + len(qs) + 1)

        fact_q = random.choice([
            (f"If {a} + {b} = {c}, then {c} - {b} = ?", a),
            (f"If {a} + {b} = {c}, then {c} - {a} = ?", b),
        ])
        stem, correct = fact_q

        wrongs = wrong_choices(correct, 0, 9)
        all_choices = [str(correct)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(correct))

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Addition and subtraction are related — they undo each other.",
                str((correct_idx + 2) % 4): "If you know an addition fact, you also know a subtraction fact.",
                str((correct_idx + 3) % 4): f"These three numbers ({a}, {b}, {c}) make a fact family."
            },
            "tags": ["fact_family", "addition_subtraction", "related_facts"],
            "topic": "ncert_g1_operations",
            "chapter": "Ch7: Addition & Subtraction Together",
            "hint": {
                "level_0": "Addition and subtraction are opposites — they are in the same family.",
                "level_1": f"If adding {a} and {b} gives {c}, then taking {b} from {c} gives back {a}.",
                "level_2": f"The answer is {correct}."
            },
            "curriculum_tags": ["NCERT_1_7"],
            "irt_params": irt_params("medium")
        })

    # Type 2: Missing number in addition/subtraction
    for i in range(5):
        a = random.randint(2, 8)
        b = random.randint(1, a - 1)
        c = a - b
        qid = make_id(len(questions) + len(qs) + 1)

        variants = [
            (f"___ + {b} = {a}", c),
            (f"{a} - ___ = {c}", b),
            (f"{c} + ___ = {a}", b),
        ]
        stem, correct = random.choice(variants)

        wrongs = wrong_choices(correct, 0, 9)
        all_choices = [str(correct)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(correct))

        qs.append({
            "id": qid,
            "stem": f"Find the missing number: {stem}",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Think about what number makes the equation true.",
                str((correct_idx + 2) % 4): "Try each choice in the blank and see which one works.",
                str((correct_idx + 3) % 4): "Use the inverse operation to find the missing number."
            },
            "tags": ["missing_number", "addition_subtraction", "algebra_readiness"],
            "topic": "ncert_g1_operations",
            "chapter": "Ch7: Addition & Subtraction Together",
            "hint": {
                "level_0": "What number makes both sides equal?",
                "level_1": "Try putting each answer choice in the blank to check.",
                "level_2": f"The missing number is {correct}."
            },
            "curriculum_tags": ["NCERT_1_7"],
            "irt_params": irt_params("hard")
        })

    # Type 3: Two-step word problems
    for i in range(5):
        a = random.randint(2, 5)
        b = random.randint(1, 3)
        c = random.randint(1, 3)
        name = get_name()
        qid = make_id(len(questions) + len(qs) + 1)

        stories = [
            (f"{name} had {a} pencils. Got {b} more, then lost {c}. How many now?", a + b - c),
            (f"{name} had {a} toffees, ate {c}, then got {b} more. How many now?", a - c + b),
            (f"{name} had {a} stickers. Gave away {c} and then found {b} more. How many now?", a - c + b),
            (f"There were {a} birds. {b} more came, then {c} flew away. How many remain?", a + b - c),
            (f"{name} had {a} laddoos. Ate {c} in the morning and got {b} from grandma. How many now?", a - c + b),
        ]
        stem, correct = stories[i % len(stories)]

        wrongs = wrong_choices(correct, 0, 9)
        all_choices = [str(correct)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(correct))

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "This problem has two steps. Do one at a time.",
                str((correct_idx + 2) % 4): "First do the first action, then do the second action.",
                str((correct_idx + 3) % 4): "'Got more' means add, 'lost/gave/ate' means subtract."
            },
            "tags": ["two_step", "addition_subtraction", "word_problem"],
            "topic": "ncert_g1_operations",
            "chapter": "Ch7: Addition & Subtraction Together",
            "hint": {
                "level_0": "Break it into two steps: do the first action, then the second.",
                "level_1": f"Start with {a}. Then do the first change, then the second change.",
                "level_2": f"Step by step: the final answer is {correct}."
            },
            "curriculum_tags": ["NCERT_1_7"],
            "irt_params": irt_params("hard")
        })

    # Type 4: Choose operation
    for i in range(4):
        a = random.randint(2, 6)
        b = random.randint(1, 3)
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        if random.random() < 0.5:
            obj = get_objects("items")
            stem = f"{name} had {a} {obj} and got {b} more. Which operation do we use?"
            correct = "Addition (+)"
            wrongs = ["Subtraction (-)", "Both (+ and -)", "Neither"]
        else:
            obj = get_objects("food")
            stem = f"{name} had {a} {obj} and ate {b}. Which operation do we use?"
            correct = "Subtraction (-)"
            wrongs = ["Addition (+)", "Both (+ and -)", "Neither"]

        all_choices = [correct] + wrongs
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "'Got more' means we add. 'Ate/gave/lost' means we subtract.",
                str((correct_idx + 2) % 4): "Think: are things increasing or decreasing?",
                str((correct_idx + 3) % 4): "Addition makes things bigger, subtraction makes things smaller."
            },
            "tags": ["operation_choice", "addition_subtraction", "reasoning"],
            "topic": "ncert_g1_operations",
            "chapter": "Ch7: Addition & Subtraction Together",
            "hint": {
                "level_0": "Does the story add things or take things away?",
                "level_1": "Getting more = add (+). Losing/eating/giving = subtract (-).",
                "level_2": f"The correct operation is {correct}."
            },
            "curriculum_tags": ["NCERT_1_7"],
            "irt_params": irt_params("medium")
        })

    # Type 5: Add/subtract with number line
    for i in range(4):
        a = random.randint(2, 7)
        b = random.randint(1, 3)
        op = random.choice(["+", "-"])
        result = a + b if op == "+" else a - b
        qid = make_id(len(questions) + len(qs) + 1)

        svg_content = svg_number_line(0, 9, highlight=a)
        svg_files[qid] = svg_content

        wrongs = wrong_choices(result, 0, 9)
        all_choices = [str(result)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(result))

        direction = "forward" if op == "+" else "backward"
        qs.append({
            "id": qid,
            "stem": f"Start at {a} on the number line. Jump {b} places {direction}. Where do you land?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"Number line from 0 to 9 with {a} highlighted",
            "diagnostics": {
                str((correct_idx + 1) % 4): f"Forward means add, backward means subtract.",
                str((correct_idx + 2) % 4): f"Start at {a} and count {b} jumps {direction}.",
                str((correct_idx + 3) % 4): "Use the number line to help you count the jumps."
            },
            "tags": ["number_line", "addition_subtraction", "visual"],
            "topic": "ncert_g1_operations",
            "chapter": "Ch7: Addition & Subtraction Together",
            "hint": {
                "level_0": f"Jumping {direction} on the number line means {'adding' if op == '+' else 'subtracting'}.",
                "level_1": f"Put your finger on {a}, then jump {b} places to the {'right' if op == '+' else 'left'}.",
                "level_2": f"{a} {op} {b} = {result}."
            },
            "curriculum_tags": ["NCERT_1_7"],
            "irt_params": irt_params("medium")
        })

    return qs


def gen_ch8_shapes():
    """Chapter 8: Shapes"""
    qs = []
    shapes = ["circle", "square", "triangle", "rectangle"]
    shape_props = {
        "circle": {"sides": 0, "corners": 0, "desc": "round with no corners"},
        "square": {"sides": 4, "corners": 4, "desc": "4 equal sides and 4 corners"},
        "triangle": {"sides": 3, "corners": 3, "desc": "3 sides and 3 corners"},
        "rectangle": {"sides": 4, "corners": 4, "desc": "4 sides (2 long, 2 short) and 4 corners"},
    }

    # Type 1: Identify shape from picture
    for i in range(6):
        shape = shapes[i % 4] if i < 4 else random.choice(shapes)
        qid = make_id(len(questions) + len(qs) + 1)

        svg_content = svg_shapes(shape)
        svg_files[qid] = svg_content

        correct = shape.capitalize()
        wrongs = [s.capitalize() for s in shapes if s != shape]
        all_choices = [correct] + wrongs[:3]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": "What shape do you see in the picture?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"A colored {shape}",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Look at the number of sides and corners.",
                str((correct_idx + 2) % 4): "A circle is round. A triangle has 3 sides. A square has 4 equal sides.",
                str((correct_idx + 3) % 4): "Count the corners of the shape."
            },
            "tags": ["shapes", "identification", "geometry"],
            "topic": "ncert_g1_shapes",
            "chapter": "Ch8: Shapes",
            "hint": {
                "level_0": "Look carefully at the shape — is it round? Does it have corners?",
                "level_1": f"This shape is {shape_props[shape]['desc']}.",
                "level_2": f"It is a {shape}."
            },
            "curriculum_tags": ["NCERT_1_8"],
            "irt_params": irt_params("easy")
        })

    # Type 2: Properties of shapes
    for i in range(5):
        shape = random.choice(shapes)
        qid = make_id(len(questions) + len(qs) + 1)

        if shape == "circle":
            stem = f"How many corners does a circle have?"
            correct = "0"
            wrongs = ["1", "2", "4"]
        elif shape == "triangle":
            stem = f"How many sides does a triangle have?"
            correct = "3"
            wrongs = ["2", "4", "5"]
        elif shape == "square":
            prop = random.choice(["sides", "corners"])
            stem = f"How many {prop} does a square have?"
            correct = "4"
            wrongs = ["3", "5", "6"]
        else:
            prop = random.choice(["sides", "corners"])
            stem = f"How many {prop} does a rectangle have?"
            correct = "4"
            wrongs = ["3", "5", "2"]

        all_choices = [correct] + wrongs
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Draw the shape and count carefully.",
                str((correct_idx + 2) % 4): "Sides are the straight lines. Corners are where sides meet.",
                str((correct_idx + 3) % 4): "A circle has no sides or corners — it's perfectly round."
            },
            "tags": ["shapes", "properties", "geometry"],
            "topic": "ncert_g1_shapes",
            "chapter": "Ch8: Shapes",
            "hint": {
                "level_0": "Think about what makes each shape special.",
                "level_1": f"Draw a {shape} in the air with your finger and count.",
                "level_2": f"A {shape} has {shape_props[shape]['sides']} sides and {shape_props[shape]['corners']} corners."
            },
            "curriculum_tags": ["NCERT_1_8"],
            "irt_params": irt_params("easy")
        })

    # Type 3: Real-world shape identification
    for i in range(6):
        real_objects = {
            "circle": ["a coin", "a bangle", "a roti", "a wheel", "a plate"],
            "square": ["a carrom board", "a window pane", "a chess board", "a handkerchief"],
            "triangle": ["a samosa", "a slice of pizza", "a roof shape", "a traffic sign"],
            "rectangle": ["a door", "a book", "a brick", "a mobile phone", "a blackboard"],
        }
        shape = random.choice(shapes)
        obj = random.choice(real_objects[shape])
        qid = make_id(len(questions) + len(qs) + 1)

        correct = shape.capitalize()
        wrongs = [s.capitalize() for s in shapes if s != shape]
        all_choices = [correct] + wrongs[:3]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": f"What shape is {obj}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Think about the object. Is it round? Does it have corners?",
                str((correct_idx + 2) % 4): "Imagine tracing around the edge of the object.",
                str((correct_idx + 3) % 4): "Compare it to the basic shapes you know."
            },
            "tags": ["shapes", "real_world", "indian_context"],
            "topic": "ncert_g1_shapes",
            "chapter": "Ch8: Shapes",
            "hint": {
                "level_0": "Think about what the object looks like when you see it from the front.",
                "level_1": f"Think about {obj} — trace its outline in your mind.",
                "level_2": f"{obj.capitalize()} is shaped like a {shape}."
            },
            "curriculum_tags": ["NCERT_1_8"],
            "irt_params": irt_params("medium")
        })

    # Type 4: Shape sorting / odd one out
    for i in range(3):
        target = random.choice(shapes)
        others = [s for s in shapes if s != target]
        odd = random.choice(others)
        qid = make_id(len(questions) + len(qs) + 1)

        items = [target, target, target, odd]
        random.shuffle(items)
        odd_pos = items.index(odd)

        # Create SVG with multiple shapes
        svg = '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">\n'
        svg += '  <rect width="200" height="120" fill="#FFFEF5" rx="8"/>\n'
        positions = [(35, 60), (85, 60), (135, 60), (175, 60)]
        labels = ["A", "B", "C", "D"]
        for idx, (cx, cy) in enumerate(positions):
            s = items[idx]
            color = SHAPE_COLORS[s]
            if s == "circle":
                svg += f'  <circle cx="{cx}" cy="{cy}" r="18" fill="{color}" stroke="#333" stroke-width="1.5"/>\n'
            elif s == "square":
                svg += f'  <rect x="{cx-16}" y="{cy-16}" width="32" height="32" fill="{color}" stroke="#333" stroke-width="1.5"/>\n'
            elif s == "triangle":
                svg += f'  <polygon points="{cx},{cy-18} {cx-16},{cy+14} {cx+16},{cy+14}" fill="{color}" stroke="#333" stroke-width="1.5"/>\n'
            elif s == "rectangle":
                svg += f'  <rect x="{cx-20}" y="{cy-12}" width="40" height="24" fill="{color}" stroke="#333" stroke-width="1.5"/>\n'
            svg += f'  <text x="{cx}" y="{cy+35}" text-anchor="middle" font-size="10" fill="#333">{labels[idx]}</text>\n'
        svg += '</svg>'
        svg_files[qid] = svg

        correct = labels[odd_pos]
        wrongs = [l for l in labels if l != correct]
        all_choices = labels[:]
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": "Which shape is different from the others?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"Four shapes: three {target}s and one {odd}",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Look at all four shapes. Three are the same type — one is different.",
                str((correct_idx + 2) % 4): "Compare the shapes by their number of sides.",
                str((correct_idx + 3) % 4): "The odd one out has a different number of corners."
            },
            "tags": ["shapes", "odd_one_out", "classification"],
            "topic": "ncert_g1_shapes",
            "chapter": "Ch8: Shapes",
            "hint": {
                "level_0": "Three shapes are alike. Find the one that is not like the others.",
                "level_1": f"Most shapes here are {target}s. Which one is not?",
                "level_2": f"Shape {correct} ({odd}) is different from the three {target}s."
            },
            "curriculum_tags": ["NCERT_1_8"],
            "irt_params": irt_params("medium")
        })

    # Type 5: Difference between square and rectangle
    for i in range(3):
        qid = make_id(len(questions) + len(qs) + 1)

        diff_questions = [
            ("A square has all sides ___.", "Equal", ["Different", "Curved", "Missing"]),
            ("Which shape has all 4 sides of the same length?", "Square", ["Rectangle", "Triangle", "Circle"]),
            ("A rectangle has two long sides and two short sides. A square has ___.", "All sides equal", ["No sides", "3 sides", "Curved sides"]),
        ]
        stem, correct, wrongs = diff_questions[i % len(diff_questions)]

        all_choices = [correct] + wrongs
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "A square is a special rectangle where all sides are the same.",
                str((correct_idx + 2) % 4): "Think about what makes a square different from a rectangle.",
                str((correct_idx + 3) % 4): "In a square, all four sides have the same length."
            },
            "tags": ["shapes", "properties", "square_rectangle"],
            "topic": "ncert_g1_shapes",
            "chapter": "Ch8: Shapes",
            "hint": {
                "level_0": "A square is special because all 4 sides are the same length.",
                "level_1": "Compare: a rectangle has 2 long and 2 short sides, but a square...",
                "level_2": f"The answer is '{correct}'."
            },
            "curriculum_tags": ["NCERT_1_8"],
            "irt_params": irt_params("hard")
        })

    return qs


def gen_ch9_measurement():
    """Chapter 9: Measurement"""
    qs = []

    # Type 1: Long/short comparisons with visuals
    for i in range(5):
        name = get_name()
        qid = make_id(len(questions) + len(qs) + 1)

        items = [
            ("pencil", "crayon", 8, 4),
            ("ribbon", "thread", 9, 3),
            ("stick", "twig", 7, 3),
            ("rope", "string", 9, 5),
            ("banana", "chilli", 6, 2),
        ]
        item1, item2, val1, val2 = items[i]

        svg_content = svg_measurement("length", val1, val2)
        svg_files[qid] = svg_content

        compare = random.choice(["longer", "shorter"])
        correct = f"A ({item1})" if (compare == "longer") == (val1 > val2) else f"B ({item2})"
        other = f"B ({item2})" if correct.startswith("A") else f"A ({item1})"

        all_choices = [correct, other, "Both are the same", "Cannot tell"]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": f"Look at the picture. A is a {item1} and B is a {item2}. Which is {compare}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"Two items compared: {item1} (longer) and {item2} (shorter)",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Compare the lengths by looking at both items side by side.",
                str((correct_idx + 2) % 4): f"'{compare}' means the one that takes {'more' if compare == 'longer' else 'less'} space.",
                str((correct_idx + 3) % 4): "Look at where each item ends — the one that stretches further is longer."
            },
            "tags": ["measurement", "length", "comparison"],
            "topic": "ncert_g1_measurement",
            "chapter": "Ch9: Measurement",
            "hint": {
                "level_0": f"'{compare.capitalize()}' means {'stretches more' if compare == 'longer' else 'stretches less'}.",
                "level_1": "Compare where the two items start and end.",
                "level_2": f"The {item1 if val1 > val2 else item2} is longer; the other is shorter."
            },
            "curriculum_tags": ["NCERT_1_9"],
            "irt_params": irt_params("easy")
        })

    # Type 2: Heavy/light comparisons
    for i in range(5):
        qid = make_id(len(questions) + len(qs) + 1)

        pairs = [
            ("an elephant", "a mouse", "heavier"),
            ("a feather", "a brick", "lighter"),
            ("a watermelon", "a grape", "heavier"),
            ("a school bag full of books", "an empty bag", "heavier"),
            ("a cotton ball", "a stone", "lighter"),
        ]
        obj1, obj2, relation = pairs[i]

        compare = random.choice(["heavier", "lighter"])
        if compare == "heavier":
            correct = obj1 if relation == "heavier" else obj2
        else:
            correct = obj2 if relation == "heavier" else obj1

        other = obj2 if correct == obj1 else obj1
        all_choices = [correct, other, "Both are the same", "Cannot tell"]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        svg_content = svg_measurement("weight", 8 if relation == "heavier" else 3, 3 if relation == "heavier" else 8)
        svg_files[qid] = svg_content

        qs.append({
            "id": qid,
            "stem": f"Which is {compare}: {obj1} or {obj2}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"Balance scale comparing two items",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Think about holding each thing — which would feel heavier?",
                str((correct_idx + 2) % 4): f"'{compare}' means weighs {'more' if compare == 'heavier' else 'less'}.",
                str((correct_idx + 3) % 4): "Imagine picking up each object. Which is harder to lift?"
            },
            "tags": ["measurement", "weight", "comparison"],
            "topic": "ncert_g1_measurement",
            "chapter": "Ch9: Measurement",
            "hint": {
                "level_0": f"Think about which object would be {'harder' if compare == 'heavier' else 'easier'} to lift.",
                "level_1": f"Imagine holding {obj1} in one hand and {obj2} in the other.",
                "level_2": f"{correct} is {compare}."
            },
            "curriculum_tags": ["NCERT_1_9"],
            "irt_params": irt_params("easy")
        })

    # Type 3: Tall/short
    for i in range(4):
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        pairs = [
            ("a tree", "a flower plant", "taller"),
            ("a giraffe", "a dog", "taller"),
            ("a building", "a house", "taller"),
            ("an ant", "a cat", "shorter"),
        ]
        obj1, obj2, relation = pairs[i]

        compare = random.choice(["taller", "shorter"])
        if compare == relation:
            correct = obj1
        else:
            correct = obj2

        other = obj2 if correct == obj1 else obj1
        all_choices = [correct, other, "Both are same height", "Cannot tell"]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": f"Which is {compare}: {obj1} or {obj2}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Think about how high each thing reaches.",
                str((correct_idx + 2) % 4): f"'{compare}' means reaches {'higher' if compare == 'taller' else 'lower'}.",
                str((correct_idx + 3) % 4): "Imagine the two things standing next to each other."
            },
            "tags": ["measurement", "height", "comparison"],
            "topic": "ncert_g1_measurement",
            "chapter": "Ch9: Measurement",
            "hint": {
                "level_0": f"Which reaches {'higher' if compare == 'taller' else 'lower'} from the ground?",
                "level_1": f"Picture {obj1} and {obj2} side by side.",
                "level_2": f"{correct} is {compare}."
            },
            "curriculum_tags": ["NCERT_1_9"],
            "irt_params": irt_params("easy")
        })

    # Type 4: Holds more/less (capacity)
    for i in range(4):
        qid = make_id(len(questions) + len(qs) + 1)

        pairs = [
            ("a bucket", "a cup", "more"),
            ("a spoon", "a glass", "less"),
            ("a tank", "a bottle", "more"),
            ("a bowl", "a swimming pool", "less"),
        ]
        obj1, obj2, relation = pairs[i]

        compare = random.choice(["more", "less"])
        if compare == relation:
            correct = obj1
        else:
            correct = obj2

        other = obj2 if correct == obj1 else obj1
        all_choices = [correct, other, "Both hold the same", "Cannot tell"]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": f"Which can hold {compare} water: {obj1} or {obj2}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Think about the size of each container.",
                str((correct_idx + 2) % 4): "A bigger container holds more water.",
                str((correct_idx + 3) % 4): "Imagine filling each with water — which fills up faster?"
            },
            "tags": ["measurement", "capacity", "comparison"],
            "topic": "ncert_g1_measurement",
            "chapter": "Ch9: Measurement",
            "hint": {
                "level_0": "Bigger containers can hold more water.",
                "level_1": f"Think about the size of {obj1} compared to {obj2}.",
                "level_2": f"{correct} holds {compare} water."
            },
            "curriculum_tags": ["NCERT_1_9"],
            "irt_params": irt_params("medium")
        })

    # Type 5: Non-standard measurement
    for i in range(5):
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        length_a = random.randint(3, 8)
        length_b = random.randint(3, 8)
        while length_b == length_a:
            length_b = random.randint(3, 8)

        unit = random.choice(["hand spans", "pencil lengths", "footsteps", "paper clips"])
        obj1 = random.choice(["desk", "book", "mat", "door"])
        obj2 = random.choice(["shelf", "board", "table", "window"])
        while obj2 == obj1:
            obj2 = random.choice(["shelf", "board", "table", "window"])

        compare = random.choice(["longer", "shorter"])
        correct = obj1 if (compare == "longer") == (length_a > length_b) else obj2

        all_choices = [f"The {obj1}", f"The {obj2}", "Both are the same", "Cannot tell"]
        correct_full = f"The {correct}"
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct_full)

        qs.append({
            "id": qid,
            "stem": f"{name} measured: the {obj1} is {length_a} {unit} long and the {obj2} is {length_b} {unit} long. Which is {compare}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): f"Compare the numbers: {length_a} {unit} vs {length_b} {unit}.",
                str((correct_idx + 2) % 4): f"More {unit} means longer.",
                str((correct_idx + 3) % 4): "The bigger measurement means that object is longer."
            },
            "tags": ["measurement", "non_standard", "comparison"],
            "topic": "ncert_g1_measurement",
            "chapter": "Ch9: Measurement",
            "hint": {
                "level_0": f"Compare the numbers of {unit}.",
                "level_1": f"Which number is {'bigger' if compare == 'longer' else 'smaller'}: {length_a} or {length_b}?",
                "level_2": f"The {correct} ({max(length_a,length_b) if compare=='longer' else min(length_a,length_b)} {unit}) is {compare}."
            },
            "curriculum_tags": ["NCERT_1_9"],
            "irt_params": irt_params("medium")
        })

    return qs


def gen_ch10_time():
    """Chapter 10: Time"""
    qs = []

    # Type 1: Daily routine ordering
    for i in range(5):
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        activities_ordered = [
            ("waking up", "brushing teeth", "eating breakfast", "going to school"),
            ("coming home from school", "doing homework", "playing outside", "having dinner"),
            ("having lunch", "taking a nap", "playing with friends", "eating evening snacks"),
            ("sunrise", "morning assembly", "lunch break", "sunset"),
            ("getting dressed", "morning prayer", "school bus arrives", "class starts"),
        ]

        activities = list(activities_ordered[i])
        question_type = random.choice(["first", "last"])
        correct = activities[0] if question_type == "first" else activities[-1]

        shuffled = activities.copy()
        random.shuffle(shuffled)

        all_choices = shuffled[:4]
        if correct not in all_choices:
            all_choices[0] = correct
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": f"In {name}'s day, which activity happens {question_type}?",
            "choices": [a.capitalize() for a in all_choices],
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Think about your own day. What do you do first/last?",
                str((correct_idx + 2) % 4): "Morning activities come first, night activities come last.",
                str((correct_idx + 3) % 4): "Imagine the order of a school day from start to end."
            },
            "tags": ["time", "daily_routine", "sequencing"],
            "topic": "ncert_g1_time",
            "chapter": "Ch10: Time",
            "hint": {
                "level_0": "Think about what order you do things in your day.",
                "level_1": f"Which of these would you do {'earliest' if question_type == 'first' else 'latest'} in the day?",
                "level_2": f"'{correct}' happens {question_type} among these activities."
            },
            "curriculum_tags": ["NCERT_1_10"],
            "irt_params": irt_params("easy")
        })

    # Type 2: Days of the week
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i in range(5):
        qid = make_id(len(questions) + len(qs) + 1)
        day_idx = random.randint(0, 6)

        q_types = [
            (f"Which day comes after {days[day_idx]}?", days[(day_idx + 1) % 7]),
            (f"Which day comes before {days[day_idx]}?", days[(day_idx - 1) % 7]),
            (f"What is the first day of the school week?", "Monday"),
            (f"Which day is a holiday (no school)?", "Sunday"),
            (f"How many days are in a week?", "7"),
        ]

        stem, correct = q_types[i % len(q_types)]

        if correct in days:
            other_days = [d for d in days if d != correct]
            wrongs = random.sample(other_days, 3)
        else:
            wrongs = ["5", "6", "10"]

        all_choices = [correct] + wrongs
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Say the days of the week in order to help remember.",
                str((correct_idx + 2) % 4): "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday.",
                str((correct_idx + 3) % 4): "Think about your school schedule to remember the order."
            },
            "tags": ["time", "days_of_week"],
            "topic": "ncert_g1_time",
            "chapter": "Ch10: Time",
            "hint": {
                "level_0": "Remember the order of the 7 days of the week.",
                "level_1": "Say them aloud: Mon, Tue, Wed, Thu, Fri, Sat, Sun.",
                "level_2": f"The answer is {correct}."
            },
            "curriculum_tags": ["NCERT_1_10"],
            "irt_params": irt_params("easy")
        })

    # Type 3: Earlier/Later
    for i in range(5):
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        pairs = [
            ("breakfast", "dinner", "earlier"),
            ("going to sleep", "waking up the next morning", "earlier"),
            ("lunch", "breakfast", "later"),
            ("coming home from school", "morning assembly", "later"),
            ("sunset", "sunrise", "later"),
        ]

        act1, act2, relation = pairs[i]
        compare = random.choice(["earlier", "later"])

        if compare == relation:
            correct = act1
        else:
            correct = act2

        other = act2 if correct == act1 else act1
        all_choices = [correct.capitalize(), other.capitalize(), "Both at the same time", "Cannot tell"]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct.capitalize())

        qs.append({
            "id": qid,
            "stem": f"Which happens {compare} in the day: {act1} or {act2}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): f"'{compare}' means {'before' if compare == 'earlier' else 'after'} in time.",
                str((correct_idx + 2) % 4): "Think about what you do first and what you do later.",
                str((correct_idx + 3) % 4): "Morning things are earlier, evening things are later."
            },
            "tags": ["time", "earlier_later", "sequencing"],
            "topic": "ncert_g1_time",
            "chapter": "Ch10: Time",
            "hint": {
                "level_0": f"'{compare.capitalize()}' means it happens {'first' if compare == 'earlier' else 'after the other'}.",
                "level_1": f"When in the day does {act1} happen? When does {act2} happen?",
                "level_2": f"{correct.capitalize()} happens {compare}."
            },
            "curriculum_tags": ["NCERT_1_10"],
            "irt_params": irt_params("medium")
        })

    # Type 4: How long does it take
    for i in range(4):
        qid = make_id(len(questions) + len(qs) + 1)

        duration_qs = [
            ("Which takes longer: blinking your eyes or eating lunch?", "Eating lunch", ["Blinking your eyes", "Both take the same time", "Cannot tell"]),
            ("Which takes less time: brushing your teeth or sleeping at night?", "Brushing your teeth", ["Sleeping at night", "Both take the same time", "Cannot tell"]),
            ("Which takes longer: a school day or a TV ad break?", "A school day", ["A TV ad break", "Both are the same", "Cannot tell"]),
            ("Which is faster: walking to school or going by autorickshaw?", "Going by autorickshaw", ["Walking to school", "Both take the same time", "Cannot tell"]),
        ]

        stem, correct, wrongs = duration_qs[i]
        all_choices = [correct] + wrongs
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Think about how much time each activity takes.",
                str((correct_idx + 2) % 4): "Some things take seconds, others take minutes or hours.",
                str((correct_idx + 3) % 4): "Compare: is it a quick action or a slow one?"
            },
            "tags": ["time", "duration", "comparison"],
            "topic": "ncert_g1_time",
            "chapter": "Ch10: Time",
            "hint": {
                "level_0": "Think about how long each activity takes in real life.",
                "level_1": "One takes much more time than the other.",
                "level_2": f"The answer is '{correct}'."
            },
            "curriculum_tags": ["NCERT_1_10"],
            "irt_params": irt_params("medium")
        })

    # Type 5: Yesterday/today/tomorrow
    for i in range(4):
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        day_idx = random.randint(0, 6)
        today = days[day_idx]

        q_types = [
            (f"Today is {today}. What day was yesterday?", days[(day_idx - 1) % 7]),
            (f"Today is {today}. What day will tomorrow be?", days[(day_idx + 1) % 7]),
            (f"Tomorrow is {days[(day_idx+1)%7]}. What day is today?", today),
            (f"Yesterday was {days[(day_idx-1)%7]}. What day is today?", today),
        ]
        stem, correct = q_types[i % len(q_types)]

        other_days = [d for d in days if d != correct]
        wrongs = random.sample(other_days, 3)
        all_choices = [correct] + wrongs
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Yesterday = the day before. Tomorrow = the day after.",
                str((correct_idx + 2) % 4): "Say the days in order and find where today falls.",
                str((correct_idx + 3) % 4): "Think: ...yesterday, TODAY, tomorrow..."
            },
            "tags": ["time", "yesterday_today_tomorrow", "days_of_week"],
            "topic": "ncert_g1_time",
            "chapter": "Ch10: Time",
            "hint": {
                "level_0": "Yesterday is one day back, tomorrow is one day forward.",
                "level_1": "Use the order: Mon, Tue, Wed, Thu, Fri, Sat, Sun and find the right day.",
                "level_2": f"The answer is {correct}."
            },
            "curriculum_tags": ["NCERT_1_10"],
            "irt_params": irt_params("hard")
        })

    return qs


def gen_ch11_money():
    """Chapter 11: Money"""
    qs = []

    # Type 1: Identify coins
    for i in range(4):
        coins = [1, 2, 5, 10]
        coin_val = coins[i]
        qid = make_id(len(questions) + len(qs) + 1)

        svg_content = svg_coins([coin_val])
        svg_files[qid] = svg_content

        correct = f"₹{coin_val}"
        wrongs = [f"₹{c}" for c in coins if c != coin_val]
        all_choices = [correct] + wrongs
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": "What is the value of this coin?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"A ₹{coin_val} coin",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Look at the number written on the coin.",
                str((correct_idx + 2) % 4): "Indian coins show their value in rupees (₹).",
                str((correct_idx + 3) % 4): "The size of the coin can help — bigger coins are usually worth more."
            },
            "tags": ["money", "coins", "identification"],
            "topic": "ncert_g1_money",
            "chapter": "Ch11: Money",
            "hint": {
                "level_0": "Look at the number on the coin to know its value.",
                "level_1": "Indian coins come as ₹1, ₹2, ₹5, and ₹10.",
                "level_2": f"This coin shows ₹{coin_val}."
            },
            "curriculum_tags": ["NCERT_1_11"],
            "irt_params": irt_params("easy")
        })

    # Type 2: Count total money (multiple coins)
    for i in range(6):
        num_coins = random.randint(2, 4)
        coin_options = [1, 2, 5, 10]
        selected_coins = [random.choice(coin_options) for _ in range(num_coins)]
        total = sum(selected_coins)
        qid = make_id(len(questions) + len(qs) + 1)

        svg_content = svg_coins(selected_coins)
        svg_files[qid] = svg_content

        name = get_name()
        wrongs = wrong_choices(total, max(1, total - 5), total + 5)
        all_choices = [f"₹{total}"] + [f"₹{w}" for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(f"₹{total}")

        coins_text = " + ".join([f"₹{c}" for c in selected_coins])
        qs.append({
            "id": qid,
            "stem": f"{name} has these coins: {coins_text}. How much money in total?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium" if total <= 15 else "hard",
            "difficulty_score": difficulty_score("medium" if total <= 15 else "hard"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"Coins showing {coins_text}",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Add the value of each coin together.",
                str((correct_idx + 2) % 4): "Start with the biggest coin and add the rest one by one.",
                str((correct_idx + 3) % 4): f"Count: {coins_text} = ?"
            },
            "tags": ["money", "addition", "counting_coins"],
            "topic": "ncert_g1_money",
            "chapter": "Ch11: Money",
            "hint": {
                "level_0": "Add up the value of each coin to find the total.",
                "level_1": f"Add step by step: {coins_text}.",
                "level_2": f"{coins_text} = ₹{total}."
            },
            "curriculum_tags": ["NCERT_1_11"],
            "irt_params": irt_params("medium" if total <= 15 else "hard")
        })

    # Type 3: Shopping word problems
    for i in range(5):
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        items_prices = [
            ("a pencil", 2), ("an eraser", 3), ("a sharpener", 5),
            ("a toffee", 1), ("a lollipop", 5), ("a small notebook", 10),
            ("a biscuit packet", 5), ("a banana", 2),
        ]

        item1, price1 = random.choice(items_prices)
        item2, price2 = random.choice([(it, pr) for it, pr in items_prices if it != item1])
        total = price1 + price2

        wrongs = wrong_choices(total, max(1, total-4), total + 5)
        all_choices = [f"₹{total}"] + [f"₹{w}" for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(f"₹{total}")

        qs.append({
            "id": qid,
            "stem": f"{name} buys {item1} for ₹{price1} and {item2} for ₹{price2}. How much money does {name} spend?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Add the prices of both items.",
                str((correct_idx + 2) % 4): f"₹{price1} + ₹{price2} = ?",
                str((correct_idx + 3) % 4): "Total spent = price of first item + price of second item."
            },
            "tags": ["money", "addition", "shopping", "indian_context"],
            "topic": "ncert_g1_money",
            "chapter": "Ch11: Money",
            "hint": {
                "level_0": "To find total spent, add the prices of all items bought.",
                "level_1": f"Add: ₹{price1} + ₹{price2}.",
                "level_2": f"₹{price1} + ₹{price2} = ₹{total}."
            },
            "curriculum_tags": ["NCERT_1_11"],
            "irt_params": irt_params("medium")
        })

    # Type 4: Making amounts with coins
    for i in range(4):
        qid = make_id(len(questions) + len(qs) + 1)
        target = random.choice([3, 6, 7, 8, 11, 12, 15])

        combos = [
            ([1, 2, 5, 10], target),
        ]

        # Generate choices as coin combinations
        options = []
        # Correct option
        remaining = target
        coins_used = []
        for c in [10, 5, 2, 1]:
            while remaining >= c:
                coins_used.append(c)
                remaining -= c
        correct = " + ".join([f"₹{c}" for c in coins_used])

        # Wrong options (different totals)
        wrong_totals = wrong_choices(target, max(1, target-3), target + 4)
        wrongs = []
        for wt in wrong_totals:
            r = wt
            wc = []
            for c in [10, 5, 2, 1]:
                while r >= c:
                    wc.append(c)
                    r -= c
            wrongs.append(" + ".join([f"₹{c}" for c in wc]))

        all_choices = [correct] + wrongs[:3]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": f"Which coins make ₹{target}?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Add up the coins in each choice and see which makes the target.",
                str((correct_idx + 2) % 4): "Try adding the coins in each option to check the total.",
                str((correct_idx + 3) % 4): f"The correct coins should add up to exactly ₹{target}."
            },
            "tags": ["money", "making_amounts", "coins"],
            "topic": "ncert_g1_money",
            "chapter": "Ch11: Money",
            "hint": {
                "level_0": "Add the coins in each choice. The one that equals the target amount is correct.",
                "level_1": f"Which group of coins adds up to ₹{target}?",
                "level_2": f"{correct} = ₹{target}."
            },
            "curriculum_tags": ["NCERT_1_11"],
            "irt_params": irt_params("hard")
        })

    # Type 5: Enough money?
    for i in range(4):
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        has = random.choice([5, 10, 7, 8])
        price = random.randint(1, has + 3)
        can_buy = price <= has

        item = random.choice(["a toy car", "a pencil box", "a ball", "a doll", "a book"])

        correct = "Yes" if can_buy else "No"

        all_choices = ["Yes", "No", "Maybe", "Need more information"]
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": f"{name} has ₹{has}. A shop sells {item} for ₹{price}. Can {name} buy it?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): f"Compare: does {name} have enough money (₹{has}) for the item (₹{price})?",
                str((correct_idx + 2) % 4): "If you have more money than the price, you can buy it.",
                str((correct_idx + 3) % 4): f"₹{has} {'≥' if can_buy else '<'} ₹{price}."
            },
            "tags": ["money", "comparison", "real_life"],
            "topic": "ncert_g1_money",
            "chapter": "Ch11: Money",
            "hint": {
                "level_0": "If your money is equal to or more than the price, you can buy it.",
                "level_1": f"Compare: {name} has ₹{has} and needs ₹{price}.",
                "level_2": f"₹{has} {'is enough for' if can_buy else 'is not enough for'} ₹{price}. Answer: {correct}."
            },
            "curriculum_tags": ["NCERT_1_11"],
            "irt_params": irt_params("medium")
        })

    return qs


def gen_ch12_data_handling():
    """Chapter 12: Data Handling"""
    qs = []

    # Type 1: Count from picture (tally)
    for i in range(5):
        count = random.randint(3, 12)
        obj = random.choice(["apples", "cars", "birds", "flowers", "books"])
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        svg_content = svg_tally(count)
        svg_files[qid] = svg_content

        wrongs = wrong_choices(count, max(1, count-3), count + 4)
        all_choices = [str(count)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(count))

        qs.append({
            "id": qid,
            "stem": f"{name} counted {obj} and made tally marks. How many {obj} are shown by these tally marks?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"Tally marks showing {count}",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Count each tally mark. A group of 5 has a diagonal line across.",
                str((correct_idx + 2) % 4): "Each group with a crossing line = 5. Count the extras.",
                str((correct_idx + 3) % 4): "Count: 5, 10, 15... for each complete group, then add the singles."
            },
            "tags": ["data_handling", "tally_marks", "counting"],
            "topic": "ncert_g1_data",
            "chapter": "Ch12: Data Handling",
            "hint": {
                "level_0": "Tally marks use groups of 5 (four lines + one crossing).",
                "level_1": f"Count the complete groups of 5, then count any extra marks.",
                "level_2": f"There are {count // 5} groups of 5 = {(count // 5) * 5}, plus {count % 5} extra = {count}."
            },
            "curriculum_tags": ["NCERT_1_12"],
            "irt_params": irt_params("medium")
        })

    # Type 2: Reading simple table
    for i in range(5):
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        categories = random.sample(["Apples", "Bananas", "Oranges", "Mangoes", "Grapes"], 3)
        counts = [random.randint(2, 8) for _ in range(3)]

        table_str = " | ".join([f"{categories[j]}: {counts[j]}" for j in range(3)])

        q_type = random.choice(["most", "least", "how_many"])
        if q_type == "most":
            max_idx = counts.index(max(counts))
            correct = categories[max_idx]
            stem = f"{name}'s class counted fruits: {table_str}. Which fruit has the most?"
            wrongs = [c for c in categories if c != correct]
            wrongs.append("All are equal")
        elif q_type == "least":
            min_idx = counts.index(min(counts))
            correct = categories[min_idx]
            stem = f"Fruits in the basket: {table_str}. Which fruit has the least?"
            wrongs = [c for c in categories if c != correct]
            wrongs.append("All are equal")
        else:
            ask_idx = random.randint(0, 2)
            correct = str(counts[ask_idx])
            stem = f"Fruits in {name}'s basket: {table_str}. How many {categories[ask_idx]} are there?"
            wrongs = [str(c) for c in counts if str(c) != correct]
            while len(wrongs) < 3:
                wrongs.append(str(random.randint(1, 9)))

        all_choices = [correct] + wrongs[:3]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Read the numbers carefully in the data.",
                str((correct_idx + 2) % 4): "'Most' means the biggest number, 'least' means smallest.",
                str((correct_idx + 3) % 4): "Compare all the numbers to find the answer."
            },
            "tags": ["data_handling", "reading_table", "comparison"],
            "topic": "ncert_g1_data",
            "chapter": "Ch12: Data Handling",
            "hint": {
                "level_0": "Look at the numbers for each item in the data.",
                "level_1": f"The data shows: {table_str}.",
                "level_2": f"The answer is {correct}."
            },
            "curriculum_tags": ["NCERT_1_12"],
            "irt_params": irt_params("medium")
        })

    # Type 3: Counting in picture groups
    for i in range(5):
        qid = make_id(len(questions) + len(qs) + 1)

        counts_data = {"red": random.randint(2, 6), "blue": random.randint(2, 6), "green": random.randint(2, 6)}
        obj = random.choice(["balloons", "flowers", "balls", "stars"])

        # Create multi-color counting SVG
        svg = '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">\n'
        svg += '  <rect width="200" height="120" fill="#FFFEF5" rx="8"/>\n'
        colors_map = {"red": "#FF6B6B", "blue": "#5DADE2", "green": "#58D68D"}
        x = 10
        for color_name, cnt in counts_data.items():
            for j in range(cnt):
                cy = 20 + j * 18
                svg += f'  <circle cx="{x + 15}" cy="{cy}" r="7" fill="{colors_map[color_name]}" stroke="#333" stroke-width="0.5"/>\n'
            svg += f'  <text x="{x + 15}" y="115" text-anchor="middle" font-size="7" fill="{colors_map[color_name]}">{color_name}</text>\n'
            x += 60
        svg += '</svg>'
        svg_files[qid] = svg

        ask_color = random.choice(list(counts_data.keys()))
        correct = str(counts_data[ask_color])
        wrongs = [str(c) for c in counts_data.values() if str(c) != correct]
        while len(wrongs) < 3:
            wrongs.append(str(random.randint(1, 8)))

        all_choices = [correct] + wrongs[:3]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": f"Look at the picture. How many {ask_color} {obj} are there?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"Groups of colored {obj}: red={counts_data['red']}, blue={counts_data['blue']}, green={counts_data['green']}",
            "diagnostics": {
                str((correct_idx + 1) % 4): f"Count only the {ask_color} ones.",
                str((correct_idx + 2) % 4): "Look at the correct color column and count.",
                str((correct_idx + 3) % 4): "Be careful to count only the asked color, not all."
            },
            "tags": ["data_handling", "counting_groups", "visual"],
            "topic": "ncert_g1_data",
            "chapter": "Ch12: Data Handling",
            "hint": {
                "level_0": f"Look only at the {ask_color} column.",
                "level_1": f"Count the {ask_color} circles in the picture.",
                "level_2": f"There are {correct} {ask_color} {obj}."
            },
            "curriculum_tags": ["NCERT_1_12"],
            "irt_params": irt_params("easy")
        })

    # Type 4: More/fewer questions from data
    for i in range(4):
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        items = random.sample(["pencils", "books", "toys", "crayons", "marbles"], 2)
        c1 = random.randint(3, 8)
        c2 = random.randint(3, 8)
        while c2 == c1:
            c2 = random.randint(3, 8)

        diff = abs(c1 - c2)
        stem = f"{name} has {c1} {items[0]} and {c2} {items[1]}. How many more {items[0] if c1 > c2 else items[1]} than {items[1] if c1 > c2 else items[0]}?"
        correct = str(diff)

        wrongs = wrong_choices(diff, 0, 8)
        all_choices = [correct] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "'How many more' means find the difference.",
                str((correct_idx + 2) % 4): "Subtract the smaller number from the bigger number.",
                str((correct_idx + 3) % 4): f"{max(c1,c2)} - {min(c1,c2)} = ?"
            },
            "tags": ["data_handling", "comparison", "difference"],
            "topic": "ncert_g1_data",
            "chapter": "Ch12: Data Handling",
            "hint": {
                "level_0": "'How many more' means subtract to find the difference.",
                "level_1": f"Compare {c1} and {c2}. What is the difference?",
                "level_2": f"{max(c1,c2)} - {min(c1,c2)} = {diff}."
            },
            "curriculum_tags": ["NCERT_1_12"],
            "irt_params": irt_params("hard")
        })

    # Type 5: Total from data
    for i in range(4):
        qid = make_id(len(questions) + len(qs) + 1)
        name = get_name()

        items = random.sample(["birds", "fish", "animals", "flowers", "vegetables"], 2)
        c1 = random.randint(2, 6)
        c2 = random.randint(2, 6)
        total = c1 + c2

        stem = f"{name} saw {c1} {items[0]} and {c2} {items[1]} in the garden. How many did {name} see in total?"
        correct = str(total)

        wrongs = wrong_choices(total, max(2, total-4), total + 4)
        all_choices = [correct] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct)

        qs.append({
            "id": qid,
            "stem": stem,
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "'Total' means add everything together.",
                str((correct_idx + 2) % 4): f"Add {c1} + {c2}.",
                str((correct_idx + 3) % 4): "Count all the things mentioned in the story."
            },
            "tags": ["data_handling", "total", "addition"],
            "topic": "ncert_g1_data",
            "chapter": "Ch12: Data Handling",
            "hint": {
                "level_0": "To find total, add all the counts together.",
                "level_1": f"Add: {c1} + {c2}.",
                "level_2": f"{c1} + {c2} = {total}."
            },
            "curriculum_tags": ["NCERT_1_12"],
            "irt_params": irt_params("easy")
        })

    return qs


def gen_ch13_patterns():
    """Chapter 13: Patterns"""
    qs = []

    # Type 1: Shape patterns - what comes next
    for i in range(6):
        qid = make_id(len(questions) + len(qs) + 1)

        pattern_types = [
            ([("circle", "#FF6B6B"), ("square", "#4ECDC4")], "AB"),
            ([("triangle", "#FFEAA7"), ("circle", "#FF6B6B"), ("square", "#4ECDC4")], "ABC"),
            ([("circle", "#FF6B6B"), ("circle", "#FF6B6B"), ("square", "#4ECDC4")], "AAB"),
            ([("square", "#4ECDC4"), ("triangle", "#FFEAA7"), ("triangle", "#FFEAA7")], "ABB"),
            ([("circle", "#FF6B6B"), ("square", "#4ECDC4"), ("circle", "#FF6B6B"), ("triangle", "#FFEAA7")], "ABAC"),
            ([("triangle", "#FFEAA7"), ("square", "#4ECDC4"), ("triangle", "#FFEAA7"), ("square", "#4ECDC4")], "ABAB"),
        ]

        base_pattern, ptype = pattern_types[i]
        # Repeat pattern and show with missing last
        full = base_pattern * 3
        shown = full[:len(base_pattern) * 2 + len(base_pattern) - 1]
        next_item = full[len(shown)]

        # Show pattern items
        display_items = shown + [None]  # None represents the blank
        svg_content = svg_pattern(shown + [next_item], missing_index=len(shown))
        svg_files[qid] = svg_content

        correct_shape = next_item[0].capitalize()
        all_shapes = ["Circle", "Square", "Triangle"]
        wrongs = [s for s in all_shapes if s != correct_shape]
        all_choices = [correct_shape] + wrongs + ["None of these"]
        all_choices = all_choices[:4]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(correct_shape)

        qs.append({
            "id": qid,
            "stem": "Look at the pattern. What shape comes next?",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy" if len(base_pattern) == 2 else "medium",
            "difficulty_score": difficulty_score("easy" if len(base_pattern) == 2 else "medium"),
            "visual_svg": make_svg_filename(qid),
            "visual_alt": f"A repeating pattern of shapes with one missing",
            "diagnostics": {
                str((correct_idx + 1) % 4): "Find the repeating part of the pattern.",
                str((correct_idx + 2) % 4): "Look at how the shapes repeat. What comes after the last shown?",
                str((correct_idx + 3) % 4): "Identify the pattern unit and continue it."
            },
            "tags": ["patterns", "shape_pattern", "next_in_sequence"],
            "topic": "ncert_g1_patterns",
            "chapter": "Ch13: Patterns",
            "hint": {
                "level_0": "A pattern repeats. Find what repeats and continue it.",
                "level_1": f"This is a {ptype} pattern. The shapes repeat in groups.",
                "level_2": f"The next shape is a {correct_shape.lower()}."
            },
            "curriculum_tags": ["NCERT_1_13"],
            "irt_params": irt_params("easy" if len(base_pattern) == 2 else "medium")
        })

    # Type 2: Number patterns
    for i in range(5):
        qid = make_id(len(questions) + len(qs) + 1)

        patterns = [
            ([1, 2, 1, 2, 1], 2, "1, 2, 1, 2, 1, ___"),
            ([2, 4, 6, 8], 10, "2, 4, 6, 8, ___"),
            ([1, 1, 2, 1, 1], 2, "1, 1, 2, 1, 1, ___"),
            ([5, 10, 5, 10], 5, "5, 10, 5, 10, ___"),
            ([1, 2, 3, 1, 2], 3, "1, 2, 3, 1, 2, ___"),
        ]

        seq, next_val, display = patterns[i]

        wrongs = wrong_choices(next_val, 1, 10)
        all_choices = [str(next_val)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(next_val))

        qs.append({
            "id": qid,
            "stem": f"What number comes next in the pattern? {display}",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "medium",
            "difficulty_score": difficulty_score("medium"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Find the rule that the pattern follows.",
                str((correct_idx + 2) % 4): "Look at how the numbers repeat or change.",
                str((correct_idx + 3) % 4): "Is it going up by the same amount? Or repeating?"
            },
            "tags": ["patterns", "number_pattern", "next_in_sequence"],
            "topic": "ncert_g1_patterns",
            "chapter": "Ch13: Patterns",
            "hint": {
                "level_0": "Look for what repeats or what rule the numbers follow.",
                "level_1": "Check: do the numbers go up by the same amount, or repeat?",
                "level_2": f"The pattern continues with {next_val}."
            },
            "curriculum_tags": ["NCERT_1_13"],
            "irt_params": irt_params("medium")
        })

    # Type 3: Color patterns
    for i in range(4):
        qid = make_id(len(questions) + len(qs) + 1)

        color_patterns = [
            (["Red", "Blue", "Red", "Blue", "Red"], "Blue"),
            (["Green", "Green", "Yellow", "Green", "Green"], "Yellow"),
            (["Red", "Yellow", "Blue", "Red", "Yellow"], "Blue"),
            (["Orange", "Orange", "Purple", "Orange", "Orange"], "Purple"),
        ]

        shown, next_color = color_patterns[i]
        display = ", ".join(shown) + ", ___"

        all_colors = ["Red", "Blue", "Green", "Yellow", "Orange", "Purple"]
        wrongs = [c for c in all_colors if c != next_color][:3]
        all_choices = [next_color] + wrongs
        random.shuffle(all_choices)
        correct_idx = all_choices.index(next_color)

        qs.append({
            "id": qid,
            "stem": f"What colour comes next? {display}",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "easy",
            "difficulty_score": difficulty_score("easy"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Look at how the colours repeat.",
                str((correct_idx + 2) % 4): "Find the repeating group and continue it.",
                str((correct_idx + 3) % 4): "Say the colours aloud — you can hear the pattern!"
            },
            "tags": ["patterns", "colour_pattern", "next_in_sequence"],
            "topic": "ncert_g1_patterns",
            "chapter": "Ch13: Patterns",
            "hint": {
                "level_0": "Colours repeat in a pattern. Find what repeats.",
                "level_1": f"The pattern is: {', '.join(shown[:3])}... it keeps repeating.",
                "level_2": f"The next colour is {next_color}."
            },
            "curriculum_tags": ["NCERT_1_13"],
            "irt_params": irt_params("easy")
        })

    # Type 4: Growing patterns
    for i in range(4):
        qid = make_id(len(questions) + len(qs) + 1)

        growing = [
            ([1, 2, 3, 4], 5, "Each time 1 more is added"),
            ([2, 4, 6, 8], 10, "Each time 2 more are added"),
            ([1, 3, 5, 7], 9, "Each time 2 more are added (odd numbers)"),
            ([10, 20, 30, 40], 50, "Each time 10 more is added"),
        ]

        seq, next_val, rule = growing[i]
        display = ", ".join(str(n) for n in seq) + ", ___"

        wrongs = wrong_choices(next_val, 1, next_val + 10)
        all_choices = [str(next_val)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(next_val))

        qs.append({
            "id": qid,
            "stem": f"This pattern grows. What comes next? {display}",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Find how much the numbers grow each time.",
                str((correct_idx + 2) % 4): f"Look at the difference between each pair of numbers.",
                str((correct_idx + 3) % 4): "Subtract each number from the next to find the rule."
            },
            "tags": ["patterns", "growing_pattern", "number_pattern"],
            "topic": "ncert_g1_patterns",
            "chapter": "Ch13: Patterns",
            "hint": {
                "level_0": "A growing pattern increases by the same amount each time.",
                "level_1": f"Rule: {rule}. Apply it to the last number.",
                "level_2": f"After {seq[-1]}, the next number is {next_val}."
            },
            "curriculum_tags": ["NCERT_1_13"],
            "irt_params": irt_params("hard")
        })

    # Type 5: Complete the pattern (middle missing)
    for i in range(4):
        qid = make_id(len(questions) + len(qs) + 1)

        sequences = [
            ([1, 3, 5, 7, 9], 2, "odd numbers pattern"),
            ([10, 20, 30, 40, 50], 2, "counting by tens"),
            ([2, 4, 6, 8, 10], 2, "even numbers"),
            ([5, 10, 15, 20, 25], 2, "counting by fives"),
        ]

        seq, missing_idx, desc = sequences[i]
        missing_val = seq[missing_idx]
        display = [str(n) if idx != missing_idx else "___" for idx, n in enumerate(seq)]

        wrongs = wrong_choices(missing_val, 1, 30)
        all_choices = [str(missing_val)] + [str(w) for w in wrongs]
        random.shuffle(all_choices)
        correct_idx = all_choices.index(str(missing_val))

        qs.append({
            "id": qid,
            "stem": f"Find the missing number in the pattern: {', '.join(display)}",
            "choices": all_choices,
            "correct_answer": correct_idx,
            "difficulty_tier": "hard",
            "difficulty_score": difficulty_score("hard"),
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {
                str((correct_idx + 1) % 4): "Look at the numbers before and after the blank.",
                str((correct_idx + 2) % 4): "Find the pattern rule (how much it goes up each time).",
                str((correct_idx + 3) % 4): "The missing number should fit the pattern exactly."
            },
            "tags": ["patterns", "missing_in_pattern", "number_pattern"],
            "topic": "ncert_g1_patterns",
            "chapter": "Ch13: Patterns",
            "hint": {
                "level_0": "Find how much the numbers change each step.",
                "level_1": f"This is a {desc}. What fits between {seq[missing_idx-1]} and {seq[missing_idx+1]}?",
                "level_2": f"The missing number is {missing_val}."
            },
            "curriculum_tags": ["NCERT_1_13"],
            "irt_params": irt_params("hard")
        })

    return qs


# ============================================================
# MAIN GENERATION
# ============================================================

print("Generating NCERT Grade 1 questions...")

# Generate all chapters
ch1 = gen_ch1_numbers_1_to_9()
questions.extend(ch1)
print(f"  Ch1 (Numbers 1-9): {len(ch1)} questions")

ch2 = gen_ch2_numbers_10_to_20()
questions.extend(ch2)
print(f"  Ch2 (Numbers 10-20): {len(ch2)} questions")

ch3 = gen_ch3_addition()
questions.extend(ch3)
print(f"  Ch3 (Addition): {len(ch3)} questions")

ch4 = gen_ch4_subtraction()
questions.extend(ch4)
print(f"  Ch4 (Subtraction): {len(ch4)} questions")

ch5 = gen_ch5_numbers_21_to_50()
questions.extend(ch5)
print(f"  Ch5 (Numbers 21-50): {len(ch5)} questions")

ch6 = gen_ch6_numbers_51_to_100()
questions.extend(ch6)
print(f"  Ch6 (Numbers 51-100): {len(ch6)} questions")

ch7 = gen_ch7_addition_subtraction()
questions.extend(ch7)
print(f"  Ch7 (Add/Sub Together): {len(ch7)} questions")

ch8 = gen_ch8_shapes()
questions.extend(ch8)
print(f"  Ch8 (Shapes): {len(ch8)} questions")

ch9 = gen_ch9_measurement()
questions.extend(ch9)
print(f"  Ch9 (Measurement): {len(ch9)} questions")

ch10 = gen_ch10_time()
questions.extend(ch10)
print(f"  Ch10 (Time): {len(ch10)} questions")

ch11 = gen_ch11_money()
questions.extend(ch11)
print(f"  Ch11 (Money): {len(ch11)} questions")

ch12 = gen_ch12_data_handling()
questions.extend(ch12)
print(f"  Ch12 (Data Handling): {len(ch12)} questions")

ch13 = gen_ch13_patterns()
questions.extend(ch13)
print(f"  Ch13 (Patterns): {len(ch13)} questions")

# If we're short of 300, we need to add more
# Let's check and add proportionally
current = len(questions)
print(f"\n  Current total: {current}")

if current < 300:
    needed = 300 - current
    print(f"  Need {needed} more questions. Adding extras...")

    # Add extra questions to bring total to 300
    extra_chapters = [
        (gen_ch1_numbers_1_to_9, "Ch1"),
        (gen_ch3_addition, "Ch3"),
        (gen_ch4_subtraction, "Ch4"),
        (gen_ch5_numbers_21_to_50, "Ch5"),
        (gen_ch7_addition_subtraction, "Ch7"),
        (gen_ch8_shapes, "Ch8"),
        (gen_ch11_money, "Ch11"),
        (gen_ch13_patterns, "Ch13"),
    ]

    random.seed(123)  # Different seed for extras
    extra_idx = 0
    while len(questions) < 300:
        gen_func, ch_name = extra_chapters[extra_idx % len(extra_chapters)]
        new_qs = gen_func()
        # Take just a few from each to avoid too much repetition
        for q in new_qs[:3]:
            if len(questions) >= 300:
                break
            # Re-assign ID
            q["id"] = make_id(len(questions) + 1)
            # Update SVG reference if exists
            old_svg_keys = [k for k in svg_files.keys() if k in [qq["id"] for qq in new_qs]]
            if q.get("visual_svg"):
                q["visual_svg"] = make_svg_filename(q["id"])
                # Generate new SVG for this ID based on question type
                if "counting" in q.get("tags", []):
                    count = random.randint(2, 9)
                    svg_files[q["id"]] = svg_counting_objects(count, random.choice(["circle", "star", "mango"]))
                elif "shapes" in q.get("tags", []):
                    svg_files[q["id"]] = svg_shapes(random.choice(["circle", "square", "triangle", "rectangle"]))
            questions.append(q)
        extra_idx += 1

# Trim to exactly 300 if over
questions = questions[:300]

print(f"\n  Final total: {len(questions)} questions")
print(f"  SVG visuals: {len(svg_files)} files")

# Build final JSON
output = {
    "topic_id": "ncert_g1",
    "topic_name": "NCERT Grade 1 Mathematics",
    "version": "2.0",
    "curriculum": "NCERT",
    "grade": 1,
    "total_questions": len(questions),
    "questions": questions
}

# Write questions.json
json_path = os.path.join(OUTPUT_DIR, "questions.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"\n  Saved: {json_path}")

# Write SVG files
svg_count = 0
for qid, svg_content in svg_files.items():
    # Only write if the question ID is in our final set
    if any(q["id"] == qid for q in questions):
        svg_path = os.path.join(VISUALS_DIR, f"{qid}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        svg_count += 1

print(f"  Saved: {svg_count} SVG files to {VISUALS_DIR}/")

# Stats
chapters_count = {}
difficulty_count = {"easy": 0, "medium": 0, "hard": 0}
visual_count = 0
for q in questions:
    ch = q["chapter"]
    chapters_count[ch] = chapters_count.get(ch, 0) + 1
    difficulty_count[q["difficulty_tier"]] += 1
    if q["visual_svg"]:
        visual_count += 1

print("\n  === CHAPTER DISTRIBUTION ===")
for ch, cnt in sorted(chapters_count.items()):
    print(f"    {ch}: {cnt} questions")

print(f"\n  === DIFFICULTY DISTRIBUTION ===")
for d, cnt in difficulty_count.items():
    print(f"    {d}: {cnt} questions ({cnt*100//len(questions)}%)")

print(f"\n  === VISUAL COVERAGE ===")
print(f"    Questions with SVG: {visual_count} ({visual_count*100//len(questions)}%)")
print(f"    Questions without SVG: {len(questions) - visual_count}")

print("\n  === SAMPLE QUESTIONS ===")
for idx in [0, 50, 100, 150, 200, 250, 299]:
    q = questions[idx]
    print(f"\n  [{q['id']}] ({q['chapter']}) [{q['difficulty_tier']}]")
    print(f"    Stem: {q['stem']}")
    print(f"    Choices: {q['choices']}")
    print(f"    Correct: {q['choices'][q['correct_answer']]}")
    print(f"    Visual: {q['visual_svg']}")

print("\n  Generation complete!")
