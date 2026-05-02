#!/usr/bin/env python3
"""Generate 300 NCERT-aligned math questions each for Grade 3 and Grade 4."""

import json
import os
import random
import math

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
G3_DIR = os.path.join(BASE_DIR, "grade3")
G4_DIR = os.path.join(BASE_DIR, "grade4")
os.makedirs(os.path.join(G3_DIR, "visuals"), exist_ok=True)
os.makedirs(os.path.join(G4_DIR, "visuals"), exist_ok=True)

# Indian names for context
NAMES = ["Aarav", "Priya", "Rohan", "Ananya", "Vihaan", "Ishita", "Arjun", "Diya",
         "Kabir", "Meera", "Aditya", "Saanvi", "Reyansh", "Kavya", "Arnav", "Pooja",
         "Siddharth", "Nisha", "Dhruv", "Tanvi", "Ravi", "Sunita", "Amit", "Deepa"]
CITIES = ["Delhi", "Mumbai", "Bengaluru", "Chennai", "Kolkata", "Jaipur", "Lucknow", "Pune"]
ITEMS_FOOD = ["mangoes", "guavas", "bananas", "apples", "oranges", "laddoos", "samosas", "pakoras"]
ITEMS_SCHOOL = ["notebooks", "pencils", "erasers", "crayons", "books", "stickers", "rulers", "sharpeners"]
FESTIVALS = ["Diwali", "Holi", "Pongal", "Onam", "Baisakhi", "Navratri"]

def pick_name():
    return random.choice(NAMES)

def pick_city():
    return random.choice(CITIES)

def make_svg_bar_chart(qid, labels, values, title, grade_dir):
    """Create a simple bar chart SVG."""
    max_val = max(values) if values else 1
    bar_w = 35
    gap = 15
    total_w = len(values) * (bar_w + gap)
    start_x = (240 - total_w) // 2
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]

    bars = ""
    for i, (label, val) in enumerate(zip(labels, values)):
        h = int((val / max_val) * 80) if max_val > 0 else 0
        x = start_x + i * (bar_w + gap)
        y = 110 - h
        c = colors[i % len(colors)]
        bars += f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" fill="{c}" rx="3"/>\n'
        bars += f'<text x="{x + bar_w//2}" y="125" text-anchor="middle" font-size="8" fill="#333">{label}</text>\n'
        bars += f'<text x="{x + bar_w//2}" y="{y - 4}" text-anchor="middle" font-size="7" fill="#333">{val}</text>\n'

    svg = f'''<svg viewBox="0 0 240 140" xmlns="http://www.w3.org/2000/svg">
<rect width="240" height="140" fill="#FFFEF5" rx="8"/>
<text x="120" y="16" text-anchor="middle" font-size="9" font-weight="bold" fill="#2C3E50">{title}</text>
{bars}
</svg>'''
    path = os.path.join(grade_dir, "visuals", f"{qid}.svg")
    with open(path, "w") as f:
        f.write(svg)
    return f"{qid}.svg"

def make_svg_fraction(qid, numerator, denominator, grade_dir):
    """Create a fraction circle SVG."""
    cx, cy, r = 120, 70, 45
    slices = ""
    angle_per = 360 / denominator
    for i in range(denominator):
        start_angle = i * angle_per - 90
        end_angle = start_angle + angle_per
        sa = math.radians(start_angle)
        ea = math.radians(end_angle)
        x1 = cx + r * math.cos(sa)
        y1 = cy + r * math.sin(sa)
        x2 = cx + r * math.cos(ea)
        y2 = cy + r * math.sin(ea)
        large = 1 if angle_per > 180 else 0
        color = "#FF6B6B" if i < numerator else "#F0F0F0"
        slices += f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large},1 {x2:.1f},{y2:.1f} Z" fill="{color}" stroke="#333" stroke-width="1"/>\n'

    svg = f'''<svg viewBox="0 0 240 140" xmlns="http://www.w3.org/2000/svg">
<rect width="240" height="140" fill="#FFFEF5" rx="8"/>
<text x="120" y="16" text-anchor="middle" font-size="10" font-weight="bold" fill="#2C3E50">{numerator}/{denominator} shaded</text>
{slices}
</svg>'''
    path = os.path.join(grade_dir, "visuals", f"{qid}.svg")
    with open(path, "w") as f:
        f.write(svg)
    return f"{qid}.svg"

def make_svg_shape(qid, shape_type, dims, grade_dir):
    """Create a shape with dimensions SVG."""
    elements = ""
    if shape_type == "rectangle":
        l, w = dims
        elements = f'''<rect x="60" y="30" width="120" height="80" fill="#AED6F1" stroke="#2C3E50" stroke-width="2" rx="2"/>
<text x="120" y="75" text-anchor="middle" font-size="10" fill="#2C3E50">{l} cm x {w} cm</text>
<text x="120" y="23" text-anchor="middle" font-size="9" fill="#555">{l} cm</text>
<text x="45" y="72" text-anchor="middle" font-size="9" fill="#555">{w} cm</text>'''
    elif shape_type == "square":
        s = dims[0]
        elements = f'''<rect x="70" y="30" width="100" height="100" fill="#ABEBC6" stroke="#2C3E50" stroke-width="2" rx="2"/>
<text x="120" y="83" text-anchor="middle" font-size="10" fill="#2C3E50">{s} cm</text>
<text x="120" y="23" text-anchor="middle" font-size="9" fill="#555">{s} cm</text>'''
    elif shape_type == "triangle":
        elements = f'''<polygon points="120,25 60,115 180,115" fill="#F9E79F" stroke="#2C3E50" stroke-width="2"/>
<text x="120" y="130" text-anchor="middle" font-size="9" fill="#555">Base = {dims[0]} cm, Height = {dims[1]} cm</text>'''

    svg = f'''<svg viewBox="0 0 240 140" xmlns="http://www.w3.org/2000/svg">
<rect width="240" height="140" fill="#FFFEF5" rx="8"/>
{elements}
</svg>'''
    path = os.path.join(grade_dir, "visuals", f"{qid}.svg")
    with open(path, "w") as f:
        f.write(svg)
    return f"{qid}.svg"

def make_svg_number_line(qid, start, end, marked, grade_dir):
    """Create a number line SVG."""
    x_start, x_end = 20, 220
    y = 70
    ticks = ""
    num_ticks = min(end - start + 1, 11)
    step = max(1, (end - start) // (num_ticks - 1))
    for i in range(num_ticks):
        val = start + i * step
        x = x_start + (x_end - x_start) * i / (num_ticks - 1)
        ticks += f'<line x1="{x:.0f}" y1="{y-5}" x2="{x:.0f}" y2="{y+5}" stroke="#333" stroke-width="1.5"/>\n'
        ticks += f'<text x="{x:.0f}" y="{y+18}" text-anchor="middle" font-size="8" fill="#333">{val}</text>\n'

    # Mark the point
    if start <= marked <= end:
        mx = x_start + (x_end - x_start) * (marked - start) / (end - start)
        ticks += f'<circle cx="{mx:.0f}" cy="{y}" r="5" fill="#E74C3C"/>\n'
        ticks += f'<text x="{mx:.0f}" y="{y-12}" text-anchor="middle" font-size="9" fill="#E74C3C">?</text>\n'

    svg = f'''<svg viewBox="0 0 240 140" xmlns="http://www.w3.org/2000/svg">
<rect width="240" height="140" fill="#FFFEF5" rx="8"/>
<text x="120" y="20" text-anchor="middle" font-size="9" font-weight="bold" fill="#2C3E50">Number Line</text>
<line x1="{x_start}" y1="{y}" x2="{x_end}" y2="{y}" stroke="#333" stroke-width="2"/>
<polygon points="{x_end},{y} {x_end-6},{y-4} {x_end-6},{y+4}" fill="#333"/>
{ticks}
</svg>'''
    path = os.path.join(grade_dir, "visuals", f"{qid}.svg")
    with open(path, "w") as f:
        f.write(svg)
    return f"{qid}.svg"

def make_svg_grid_area(qid, rows, cols, shaded, grade_dir):
    """Create a grid for area counting."""
    cell = 12
    ox = (240 - cols * cell) // 2
    oy = (140 - rows * cell) // 2
    cells = ""
    count = 0
    for r in range(rows):
        for c in range(cols):
            color = "#AED6F1" if count < shaded else "#F0F0F0"
            cells += f'<rect x="{ox + c*cell}" y="{oy + r*cell}" width="{cell}" height="{cell}" fill="{color}" stroke="#666" stroke-width="0.5"/>\n'
            count += 1
    svg = f'''<svg viewBox="0 0 240 140" xmlns="http://www.w3.org/2000/svg">
<rect width="240" height="140" fill="#FFFEF5" rx="8"/>
<text x="120" y="12" text-anchor="middle" font-size="8" fill="#2C3E50">Count the shaded squares</text>
{cells}
</svg>'''
    path = os.path.join(grade_dir, "visuals", f"{qid}.svg")
    with open(path, "w") as f:
        f.write(svg)
    return f"{qid}.svg"

def make_svg_clock(qid, hour, minute, grade_dir):
    """Create a clock face SVG."""
    cx, cy, r = 120, 75, 50
    # Hour hand
    h_angle = math.radians((hour % 12 + minute / 60) * 30 - 90)
    hx = cx + 30 * math.cos(h_angle)
    hy = cy + 30 * math.sin(h_angle)
    # Minute hand
    m_angle = math.radians(minute * 6 - 90)
    mx = cx + 42 * math.cos(m_angle)
    my = cy + 42 * math.sin(m_angle)

    numbers = ""
    for i in range(1, 13):
        a = math.radians(i * 30 - 90)
        nx = cx + 40 * math.cos(a)
        ny = cy + 40 * math.sin(a) + 3
        numbers += f'<text x="{nx:.0f}" y="{ny:.0f}" text-anchor="middle" font-size="7" fill="#333">{i}</text>\n'

    svg = f'''<svg viewBox="0 0 240 140" xmlns="http://www.w3.org/2000/svg">
<rect width="240" height="140" fill="#FFFEF5" rx="8"/>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="white" stroke="#2C3E50" stroke-width="3"/>
{numbers}
<line x1="{cx}" y1="{cy}" x2="{hx:.0f}" y2="{hy:.0f}" stroke="#2C3E50" stroke-width="3" stroke-linecap="round"/>
<line x1="{cx}" y1="{cy}" x2="{mx:.0f}" y2="{my:.0f}" stroke="#E74C3C" stroke-width="2" stroke-linecap="round"/>
<circle cx="{cx}" cy="{cy}" r="3" fill="#2C3E50"/>
</svg>'''
    path = os.path.join(grade_dir, "visuals", f"{qid}.svg")
    with open(path, "w") as f:
        f.write(svg)
    return f"{qid}.svg"

def make_svg_symmetry(qid, shape, grade_dir):
    """Create a symmetry visual."""
    if shape == "butterfly":
        elements = '''<line x1="120" y1="20" x2="120" y2="120" stroke="#E74C3C" stroke-width="1.5" stroke-dasharray="4,2"/>
<ellipse cx="95" cy="55" rx="25" ry="30" fill="#AED6F1" stroke="#333" stroke-width="1.5"/>
<ellipse cx="145" cy="55" rx="25" ry="30" fill="#AED6F1" stroke="#333" stroke-width="1.5"/>
<ellipse cx="100" cy="95" rx="15" ry="20" fill="#F9E79F" stroke="#333" stroke-width="1.5"/>
<ellipse cx="140" cy="95" rx="15" ry="20" fill="#F9E79F" stroke="#333" stroke-width="1.5"/>'''
    else:
        elements = '''<line x1="120" y1="20" x2="120" y2="120" stroke="#E74C3C" stroke-width="1.5" stroke-dasharray="4,2"/>
<polygon points="120,30 80,110 160,110" fill="#ABEBC6" stroke="#333" stroke-width="1.5"/>'''

    svg = f'''<svg viewBox="0 0 240 140" xmlns="http://www.w3.org/2000/svg">
<rect width="240" height="140" fill="#FFFEF5" rx="8"/>
<text x="120" y="135" text-anchor="middle" font-size="8" fill="#555">Line of symmetry shown in red</text>
{elements}
</svg>'''
    path = os.path.join(grade_dir, "visuals", f"{qid}.svg")
    with open(path, "w") as f:
        f.write(svg)
    return f"{qid}.svg"

def make_svg_pattern(qid, pattern_nums, grade_dir):
    """Create a number pattern visual."""
    elements = ""
    n = len(pattern_nums)
    spacing = min(40, 200 // n)
    start_x = 120 - (n * spacing) // 2
    for i, num in enumerate(pattern_nums):
        x = start_x + i * spacing + spacing // 2
        elements += f'<circle cx="{x}" cy="70" r="18" fill="#AED6F1" stroke="#2C3E50" stroke-width="1.5"/>\n'
        label = "?" if num is None else str(num)
        color = "#E74C3C" if num is None else "#2C3E50"
        elements += f'<text x="{x}" y="74" text-anchor="middle" font-size="10" font-weight="bold" fill="{color}">{label}</text>\n'

    svg = f'''<svg viewBox="0 0 240 140" xmlns="http://www.w3.org/2000/svg">
<rect width="240" height="140" fill="#FFFEF5" rx="8"/>
<text x="120" y="20" text-anchor="middle" font-size="9" font-weight="bold" fill="#2C3E50">Find the missing number</text>
{elements}
<text x="120" y="120" text-anchor="middle" font-size="8" fill="#555">What comes next in the pattern?</text>
</svg>'''
    path = os.path.join(grade_dir, "visuals", f"{qid}.svg")
    with open(path, "w") as f:
        f.write(svg)
    return f"{qid}.svg"


# ============================================================
# GRADE 3 QUESTION GENERATORS
# ============================================================

def g3_chapter1_numbers(qid_num):
    """Numbers up to 9999"""
    questions = []
    templates = [
        "place_value", "expanded_form", "compare", "successor",
        "predecessor", "largest_smallest", "number_names", "roman"
    ]
    for i in range(22):
        qid = f"NCERT-G3-{qid_num:03d}"
        t = templates[i % len(templates)]

        if t == "place_value":
            n = random.randint(1000, 9999)
            place = random.choice(["thousands", "hundreds", "tens", "ones"])
            digit_map = {"thousands": n // 1000, "hundreds": (n // 100) % 10,
                        "tens": (n // 10) % 10, "ones": n % 10}
            correct = digit_map[place]
            wrong = [d for d in range(10) if d != correct]
            random.shuffle(wrong)
            choices = [str(correct), str(wrong[0]), str(wrong[1]), str(wrong[2])]
            correct_idx = 0
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            q = {
                "id": qid, "stem": f"What is the digit in the {place} place of {n}?",
                "choices": choices, "correct_answer": correct_idx,
                "difficulty_tier": "easy", "difficulty_score": random.randint(15, 30),
                "visual_svg": None, "visual_alt": None,
                "diagnostics": {"1": f"Confused {place} with another place",
                               "2": "Read the number incorrectly",
                               "3": "Does not understand place value"},
                "tags": ["numbers", "place_value"], "topic": "ncert_g3_arithmetic",
                "chapter": "Ch1: Numbers up to 9999",
                "hint": {"level_0": "Think about what each position means.",
                        "level_1": f"In {n}, count from right: ones, tens, hundreds, thousands.",
                        "level_2": f"The {place} digit in {n} is {correct}."},
                "curriculum_tags": ["NCERT_3_1"],
                "irt_params": {"a": round(random.uniform(0.8, 1.4), 2),
                              "b": round(random.uniform(-1.5, -0.5), 2), "c": 0.25}
            }
        elif t == "expanded_form":
            n = random.randint(1000, 9999)
            th, h, te, o = n // 1000, (n // 100) % 10, (n // 10) % 10, n % 10
            correct_exp = f"{th*1000} + {h*100} + {te*10} + {o}"
            wrong1 = f"{th*100} + {h*1000} + {te*10} + {o}"
            wrong2 = f"{th*1000} + {h*10} + {te*100} + {o}"
            wrong3 = f"{th*1000} + {h*100} + {te} + {o*10}"
            choices = [correct_exp, wrong1, wrong2, wrong3]
            random.shuffle(choices)
            correct_idx = choices.index(correct_exp)
            q = {
                "id": qid, "stem": f"Write the expanded form of {n}.",
                "choices": choices, "correct_answer": correct_idx,
                "difficulty_tier": "easy", "difficulty_score": random.randint(20, 35),
                "visual_svg": None, "visual_alt": None,
                "diagnostics": {"1": "Mixed up place values in expansion",
                               "2": "Multiplied digits by wrong powers",
                               "3": "Does not understand expanded notation"},
                "tags": ["numbers", "expanded_form"], "topic": "ncert_g3_arithmetic",
                "chapter": "Ch1: Numbers up to 9999",
                "hint": {"level_0": "Break the number into thousands, hundreds, tens, ones.",
                        "level_1": f"{n} = {th} thousands + {h} hundreds + {te} tens + {o} ones.",
                        "level_2": f"Expanded form: {correct_exp}"},
                "curriculum_tags": ["NCERT_3_1"],
                "irt_params": {"a": round(random.uniform(0.8, 1.3), 2),
                              "b": round(random.uniform(-1.3, -0.3), 2), "c": 0.25}
            }
        elif t == "compare":
            a = random.randint(1000, 9999)
            b = random.randint(1000, 9999)
            while b == a:
                b = random.randint(1000, 9999)
            if a > b:
                correct = f"{a} > {b}"
            else:
                correct = f"{a} < {b}"
            wrong_choices = [f"{a} > {b}" if a < b else f"{a} < {b}",
                           f"{a} = {b}", f"{b} > {a}" if a > b else f"{b} < {a}"]
            choices = [correct] + wrong_choices[:3]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            q = {
                "id": qid, "stem": f"Compare {a} and {b}. Which is correct?",
                "choices": choices, "correct_answer": correct_idx,
                "difficulty_tier": "easy", "difficulty_score": random.randint(15, 30),
                "visual_svg": None, "visual_alt": None,
                "diagnostics": {"1": "Confused > and < symbols",
                               "2": "Compared digits incorrectly",
                               "3": "Does not understand comparison"},
                "tags": ["numbers", "comparison"], "topic": "ncert_g3_arithmetic",
                "chapter": "Ch1: Numbers up to 9999",
                "hint": {"level_0": "Compare from the leftmost digit.",
                        "level_1": "The number with bigger thousands digit is larger.",
                        "level_2": f"{max(a,b)} is greater than {min(a,b)}."},
                "curriculum_tags": ["NCERT_3_1"],
                "irt_params": {"a": round(random.uniform(0.8, 1.2), 2),
                              "b": round(random.uniform(-1.5, -0.5), 2), "c": 0.25}
            }
        elif t == "successor":
            n = random.randint(1000, 9998)
            correct = str(n + 1)
            choices = [correct, str(n + 2), str(n + 10), str(n - 1)]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            q = {
                "id": qid, "stem": f"What is the successor of {n}?",
                "choices": choices, "correct_answer": correct_idx,
                "difficulty_tier": "easy", "difficulty_score": random.randint(10, 25),
                "visual_svg": None, "visual_alt": None,
                "diagnostics": {"1": "Added 10 instead of 1",
                               "2": "Subtracted 1 instead of adding",
                               "3": "Does not know what successor means"},
                "tags": ["numbers", "successor"], "topic": "ncert_g3_arithmetic",
                "chapter": "Ch1: Numbers up to 9999",
                "hint": {"level_0": "Successor means the number that comes just after.",
                        "level_1": f"Add 1 to {n}.",
                        "level_2": f"Successor of {n} is {n+1}."},
                "curriculum_tags": ["NCERT_3_1"],
                "irt_params": {"a": round(random.uniform(0.9, 1.3), 2),
                              "b": round(random.uniform(-1.5, -1.0), 2), "c": 0.25}
            }
        elif t == "predecessor":
            n = random.randint(1001, 9999)
            correct = str(n - 1)
            choices = [correct, str(n + 1), str(n - 10), str(n - 2)]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            q = {
                "id": qid, "stem": f"What is the predecessor of {n}?",
                "choices": choices, "correct_answer": correct_idx,
                "difficulty_tier": "easy", "difficulty_score": random.randint(10, 25),
                "visual_svg": None, "visual_alt": None,
                "diagnostics": {"1": "Subtracted 10 instead of 1",
                               "2": "Added instead of subtracting",
                               "3": "Does not know what predecessor means"},
                "tags": ["numbers", "predecessor"], "topic": "ncert_g3_arithmetic",
                "chapter": "Ch1: Numbers up to 9999",
                "hint": {"level_0": "Predecessor means the number just before.",
                        "level_1": f"Subtract 1 from {n}.",
                        "level_2": f"Predecessor of {n} is {n-1}."},
                "curriculum_tags": ["NCERT_3_1"],
                "irt_params": {"a": round(random.uniform(0.9, 1.3), 2),
                              "b": round(random.uniform(-1.5, -1.0), 2), "c": 0.25}
            }
        elif t == "largest_smallest":
            nums = random.sample(range(1000, 9999), 4)
            ask = random.choice(["largest", "smallest"])
            correct = str(max(nums)) if ask == "largest" else str(min(nums))
            choices = [str(n) for n in nums]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            q = {
                "id": qid, "stem": f"Which is the {ask} number: {', '.join(str(n) for n in nums)}?",
                "choices": choices, "correct_answer": correct_idx,
                "difficulty_tier": "easy", "difficulty_score": random.randint(15, 30),
                "visual_svg": None, "visual_alt": None,
                "diagnostics": {"1": f"Picked {('smallest','largest')[ask=='smallest']} instead",
                               "2": "Compared only last digits",
                               "3": "Random guess"},
                "tags": ["numbers", "comparison"], "topic": "ncert_g3_arithmetic",
                "chapter": "Ch1: Numbers up to 9999",
                "hint": {"level_0": f"Look for the {ask} number by comparing thousands first.",
                        "level_1": "Compare thousands digits, then hundreds, tens, ones.",
                        "level_2": f"The {ask} is {correct}."},
                "curriculum_tags": ["NCERT_3_1"],
                "irt_params": {"a": round(random.uniform(0.8, 1.2), 2),
                              "b": round(random.uniform(-1.2, -0.2), 2), "c": 0.25}
            }
        elif t == "number_names":
            n = random.randint(1000, 9999)
            th, h, te, o = n // 1000, (n // 100) % 10, (n // 10) % 10, n % 10
            ones_w = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
            tens_w = ["", "ten", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
            teens_w = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]

            def num_to_words(num):
                if num == 0: return "zero"
                parts = []
                if num >= 1000:
                    parts.append(f"{ones_w[num//1000]} thousand")
                    num %= 1000
                if num >= 100:
                    parts.append(f"{ones_w[num//100]} hundred")
                    num %= 100
                if num >= 20:
                    w = tens_w[num//10]
                    if num % 10:
                        w += f" {ones_w[num%10]}"
                    parts.append(w)
                elif num >= 10:
                    parts.append(teens_w[num-10])
                elif num > 0:
                    parts.append(ones_w[num])
                return " ".join(parts)

            correct_name = num_to_words(n)
            # Generate wrong by swapping digits
            wrong_nums = [n + 1000 if n < 9000 else n - 1000,
                         n + 100 if n < 9900 else n - 100,
                         n + 10 if n < 9990 else n - 10]
            choices = [correct_name] + [num_to_words(w) for w in wrong_nums]
            random.shuffle(choices)
            correct_idx = choices.index(correct_name)
            q = {
                "id": qid, "stem": f"What is the number name for {n}?",
                "choices": choices, "correct_answer": correct_idx,
                "difficulty_tier": "medium", "difficulty_score": random.randint(30, 50),
                "visual_svg": None, "visual_alt": None,
                "diagnostics": {"1": "Mixed up place values in words",
                               "2": "Incorrect tens/ones naming",
                               "3": "Cannot convert digits to words"},
                "tags": ["numbers", "number_names"], "topic": "ncert_g3_arithmetic",
                "chapter": "Ch1: Numbers up to 9999",
                "hint": {"level_0": "Read each digit by its place.",
                        "level_1": f"{th} thousand, {h} hundred, {te} tens, {o} ones.",
                        "level_2": f"The answer is: {correct_name}."},
                "curriculum_tags": ["NCERT_3_1"],
                "irt_params": {"a": round(random.uniform(0.9, 1.4), 2),
                              "b": round(random.uniform(-1.0, 0.0), 2), "c": 0.25}
            }
        else:  # roman
            roman_map = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
            n = random.randint(1, 20)
            def to_roman(num):
                result = ""
                for val, sym in roman_map:
                    while num >= val:
                        result += sym
                        num -= val
                return result
            correct = to_roman(n)
            wrong = [to_roman(n+1 if n < 20 else n-1),
                    to_roman(n+2 if n < 19 else n-2),
                    to_roman(n-1 if n > 1 else n+3)]
            choices = [correct] + wrong
            # Deduplicate
            choices = list(dict.fromkeys(choices))
            while len(choices) < 4:
                choices.append(to_roman(random.randint(1, 20)))
            choices = choices[:4]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            q = {
                "id": qid, "stem": f"Write {n} in Roman numerals.",
                "choices": choices, "correct_answer": correct_idx,
                "difficulty_tier": "medium", "difficulty_score": random.randint(35, 55),
                "visual_svg": None, "visual_alt": None,
                "diagnostics": {"1": "Confused I and V values",
                               "2": "Wrong subtraction rule (IV vs VI)",
                               "3": "Does not know Roman numeral system"},
                "tags": ["numbers", "roman_numerals"], "topic": "ncert_g3_arithmetic",
                "chapter": "Ch1: Numbers up to 9999",
                "hint": {"level_0": "I=1, V=5, X=10. Put smaller before larger to subtract.",
                        "level_1": f"Think: how many Xs, Vs, and Is make {n}?",
                        "level_2": f"{n} in Roman numerals is {correct}."},
                "curriculum_tags": ["NCERT_3_1"],
                "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                              "b": round(random.uniform(-0.5, 0.5), 2), "c": 0.25}
            }

        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter2_add_sub(qid_num):
    """Addition & Subtraction — 4-digit, word problems"""
    questions = []
    for i in range(22):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 6

        if variant == 0:  # simple addition
            a = random.randint(1000, 5000)
            b = random.randint(1000, 4999)
            correct = a + b
            choices = [str(correct), str(correct + 10), str(correct - 100), str(a + b - 1)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            stem = f"Add: {a} + {b} = ?"
            tags = ["addition", "4_digit"]
            diag = {"1": "Carry error", "2": "Added incorrectly in ones place", "3": "Forgot to regroup"}
        elif variant == 1:  # subtraction
            a = random.randint(5000, 9999)
            b = random.randint(1000, a - 1)
            correct = a - b
            choices = [str(correct), str(correct + 10), str(correct - 10), str(a - b + 100)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            stem = f"Subtract: {a} - {b} = ?"
            tags = ["subtraction", "4_digit"]
            diag = {"1": "Borrowing error", "2": "Subtracted smaller from larger in each place", "3": "Did not regroup"}
        elif variant == 2:  # word problem addition
            name = pick_name()
            item = random.choice(ITEMS_SCHOOL)
            a = random.randint(100, 3000)
            b = random.randint(100, 3000)
            correct = a + b
            stem = f"{name}'s school ordered {a} {item} in January and {b} more in February. How many {item} in all?"
            choices = [str(correct), str(correct + 10), str(abs(a - b)), str(correct - 100)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["addition", "word_problem"]
            diag = {"1": "Subtracted instead of adding", "2": "Arithmetic error in addition", "3": "Misread the numbers"}
        elif variant == 3:  # word problem subtraction
            name = pick_name()
            total = random.randint(3000, 9000)
            sold = random.randint(1000, total - 500)
            correct = total - sold
            item = random.choice(ITEMS_FOOD)
            stem = f"A shop in {pick_city()} had {total} {item}. They sold {sold}. How many are left?"
            choices = [str(correct), str(correct + 100), str(total + sold), str(correct - 10)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["subtraction", "word_problem"]
            diag = {"1": "Added instead of subtracting", "2": "Borrowing error", "3": "Misunderstood 'left'"}
        elif variant == 4:  # estimation
            a = random.randint(100, 5000)
            b = random.randint(100, 4000)
            actual = a + b
            rounded_a = round(a, -2)
            rounded_b = round(b, -2)
            estimate = rounded_a + rounded_b
            stem = f"Estimate {a} + {b} by rounding to the nearest hundred."
            choices = [str(estimate), str(actual), str(estimate + 100), str(estimate - 200)]
            choices = list(dict.fromkeys(choices))[:4]
            while len(choices) < 4:
                choices.append(str(estimate + random.choice([-300, 200, 500])))
            random.shuffle(choices)
            correct_idx = choices.index(str(estimate))
            tags = ["addition", "estimation"]
            diag = {"1": "Gave exact answer instead of estimate", "2": "Rounded incorrectly", "3": "Does not understand estimation"}
        else:  # regrouping focus
            a = random.randint(1000, 4999)
            b = random.randint(1000, 4999)
            correct = a + b
            stem = f"Find the sum with regrouping: {a} + {b}"
            choices = [str(correct), str(correct - 10), str(correct + 100), str(correct - 1000)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["addition", "regrouping"]
            diag = {"1": "Did not carry over", "2": "Carried wrong amount", "3": "Multiple regrouping errors"}

        has_visual = variant in [2, 3] and random.random() < 0.4
        vis_svg = None
        vis_alt = None
        if has_visual and variant == 2:
            vis_svg = make_svg_bar_chart(qid, ["Jan", "Feb"], [a, b], f"{item.title()} Ordered", G3_DIR)
            vis_alt = f"Bar chart showing {a} in January and {b} in February"

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "easy" if variant < 2 else "medium",
            "difficulty_score": random.randint(20, 50),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": diag, "tags": tags, "topic": "ncert_g3_arithmetic",
            "chapter": "Ch2: Addition & Subtraction",
            "hint": {"level_0": "Line up the numbers by place value.",
                    "level_1": "Start adding/subtracting from the ones place. Regroup if needed.",
                    "level_2": f"The answer is {correct}."},
            "curriculum_tags": ["NCERT_3_2"],
            "irt_params": {"a": round(random.uniform(0.8, 1.4), 2),
                          "b": round(random.uniform(-1.3, 0.0), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter3_mult(qid_num):
    """Multiplication — tables, 2-digit x 1-digit, word problems"""
    questions = []
    for i in range(22):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # tables
            a = random.randint(2, 10)
            b = random.randint(2, 10)
            correct = a * b
            choices = [str(correct), str(correct + a), str(correct - a), str(correct + 1)]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            stem = f"What is {a} × {b}?"
            tags = ["multiplication", "tables"]
            diag = {"1": "Off by one multiple", "2": "Confused with addition", "3": "Does not know the table"}
        elif variant == 1:  # 2-digit x 1-digit
            a = random.randint(11, 99)
            b = random.randint(2, 9)
            correct = a * b
            choices = [str(correct), str(correct + b), str(correct - b), str(correct + 10)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            stem = f"Multiply: {a} × {b} = ?"
            tags = ["multiplication", "2digit_1digit"]
            diag = {"1": "Error in tens multiplication", "2": "Forgot to add carry", "3": "Only multiplied ones digit"}
        elif variant == 2:  # word problem
            name = pick_name()
            item = random.choice(ITEMS_FOOD)
            packs = random.randint(3, 9)
            per_pack = random.randint(6, 15)
            correct = packs * per_pack
            stem = f"{name} bought {packs} packets of {item}. Each packet has {per_pack} pieces. How many {item} in total?"
            choices = [str(correct), str(correct + per_pack), str(packs + per_pack), str(correct - packs)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["multiplication", "word_problem"]
            diag = {"1": "Added instead of multiplying", "2": "Multiplication error", "3": "Misidentified operation"}
        elif variant == 3:  # properties
            a = random.randint(2, 10)
            b = random.randint(2, 10)
            stem = f"Which shows that multiplication is commutative? {a} × {b} = ?"
            correct = f"{b} × {a}"
            choices = [correct, f"{a} + {b}", f"{b} + {a}", f"{a} × {a}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["multiplication", "properties"]
            diag = {"1": "Confused with addition", "2": "Does not understand commutative", "3": "Picked wrong operation"}
        else:  # missing factor
            a = random.randint(2, 9)
            b = random.randint(2, 9)
            product = a * b
            stem = f"Fill in the blank: ___ × {b} = {product}"
            correct = str(a)
            choices = [correct, str(a + 1), str(a - 1 if a > 1 else a + 2), str(b)]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["multiplication", "missing_factor"]
            diag = {"1": "Divided incorrectly", "2": "Guessed from the options", "3": "Does not understand inverse"}

        has_visual = random.random() < 0.3
        vis_svg = None
        vis_alt = None

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": ["easy", "medium", "medium", "medium", "medium"][variant],
            "difficulty_score": random.randint(20, 55),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": diag, "tags": tags, "topic": "ncert_g3_arithmetic",
            "chapter": "Ch3: Multiplication",
            "hint": {"level_0": "Think of multiplication as repeated addition.",
                    "level_1": f"Use skip counting or tables to find the answer.",
                    "level_2": f"The answer is {correct if variant >= 3 else correct}."},
            "curriculum_tags": ["NCERT_3_3"],
            "irt_params": {"a": round(random.uniform(0.9, 1.5), 2),
                          "b": round(random.uniform(-1.2, 0.2), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter4_division(qid_num):
    """Division — basic, remainders, word problems"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # exact division
            b = random.randint(2, 9)
            a = b * random.randint(2, 10)
            correct = a // b
            choices = [str(correct), str(correct + 1), str(correct - 1), str(b)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            stem = f"Divide: {a} ÷ {b} = ?"
            tags = ["division", "exact"]
        elif variant == 1:  # with remainder
            b = random.randint(2, 9)
            quotient = random.randint(3, 10)
            remainder = random.randint(1, b - 1)
            a = b * quotient + remainder
            correct = f"{quotient} remainder {remainder}"
            wrong1 = f"{quotient + 1} remainder {remainder}"
            wrong2 = f"{quotient} remainder {remainder + 1}"
            wrong3 = f"{quotient - 1} remainder {b}"
            choices = [correct, wrong1, wrong2, wrong3]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            stem = f"What is {a} ÷ {b}? (Write quotient and remainder)"
            tags = ["division", "remainder"]
        elif variant == 2:  # word problem equal sharing
            name = pick_name()
            item = random.choice(ITEMS_FOOD)
            friends = random.randint(3, 8)
            total = friends * random.randint(3, 12)
            correct = total // friends
            stem = f"{name} has {total} {item} to share equally among {friends} friends. How many does each friend get?"
            choices = [str(correct), str(correct + 1), str(correct - 1), str(friends)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["division", "word_problem", "sharing"]
        elif variant == 3:  # word problem grouping
            name = pick_name()
            item = random.choice(ITEMS_SCHOOL)
            per_group = random.randint(4, 8)
            groups = random.randint(3, 10)
            total = per_group * groups
            correct = groups
            stem = f"{name} has {total} {item}. She puts {per_group} in each box. How many boxes does she need?"
            choices = [str(correct), str(correct + 1), str(per_group), str(total)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["division", "word_problem", "grouping"]
        else:  # division fact family
            a = random.randint(2, 9)
            b = random.randint(2, 9)
            product = a * b
            stem = f"If {a} × {b} = {product}, then {product} ÷ {a} = ?"
            correct = str(b)
            choices = [correct, str(a), str(product), str(a + b)]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["division", "fact_family"]

        diag = {"1": "Multiplication error when checking", "2": "Wrong operation chosen", "3": "Cannot relate division to multiplication"}

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium" if variant in [1, 3] else "easy",
            "difficulty_score": random.randint(25, 55),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": diag, "tags": tags, "topic": "ncert_g3_arithmetic",
            "chapter": "Ch4: Division",
            "hint": {"level_0": "Division is splitting into equal groups.",
                    "level_1": "Think: how many times does the divisor fit into the dividend?",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_3_4"],
            "irt_params": {"a": round(random.uniform(0.9, 1.4), 2),
                          "b": round(random.uniform(-1.0, 0.3), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter5_fractions(qid_num):
    """Fractions — proper fractions, comparing, equivalent"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # identify fraction from figure
            denom = random.choice([2, 3, 4, 6, 8])
            numer = random.randint(1, denom - 1)
            correct = f"{numer}/{denom}"
            wrong1 = f"{denom}/{numer}"
            wrong2 = f"{numer}/{denom+1}"
            wrong3 = f"{numer+1}/{denom}"
            choices = [correct, wrong1, wrong2, wrong3]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            stem = f"What fraction of the shape is shaded? (See figure)"
            vis_svg = make_svg_fraction(qid, numer, denom, G3_DIR)
            vis_alt = f"Circle divided into {denom} parts with {numer} shaded"
            tags = ["fractions", "identify"]
        elif variant == 1:  # compare fractions same denom
            denom = random.choice([4, 5, 6, 8])
            a = random.randint(1, denom - 2)
            b = a + random.randint(1, denom - a - 1)
            correct = f"{b}/{denom}"
            stem = f"Which is greater: {a}/{denom} or {b}/{denom}?"
            choices = [f"{b}/{denom}", f"{a}/{denom}", "They are equal", f"{a+b}/{denom}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["fractions", "compare"]
        elif variant == 2:  # equivalent fractions
            numer = random.randint(1, 4)
            denom = random.randint(numer + 1, 6)
            mult = random.randint(2, 3)
            correct = f"{numer * mult}/{denom * mult}"
            wrong1 = f"{numer + mult}/{denom + mult}"
            wrong2 = f"{numer * mult}/{denom}"
            wrong3 = f"{numer}/{denom * mult}"
            choices = [correct, wrong1, wrong2, wrong3]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            stem = f"Which fraction is equivalent to {numer}/{denom}?"
            vis_svg = make_svg_fraction(qid, numer, denom, G3_DIR)
            vis_alt = f"Fraction {numer}/{denom} shown as circle"
            tags = ["fractions", "equivalent"]
        elif variant == 3:  # fraction of a number
            denom = random.choice([2, 3, 4, 5])
            whole = denom * random.randint(2, 8)
            numer = 1
            correct = whole // denom
            stem = f"Find 1/{denom} of {whole}."
            choices = [str(correct), str(correct + 1), str(whole), str(denom)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            vis_svg = None
            vis_alt = None
            tags = ["fractions", "fraction_of_number"]
        else:  # word problem
            name = pick_name()
            item = random.choice(["pizza", "cake", "chocolate bar", "roti"])
            denom = random.choice([4, 6, 8])
            numer = random.randint(1, denom - 1)
            stem = f"{name} ate {numer} out of {denom} equal pieces of a {item}. What fraction did {name} eat?"
            correct = f"{numer}/{denom}"
            wrong1 = f"{denom}/{numer}" if numer != 0 else "1/1"
            wrong2 = f"{numer}/{denom+2}"
            wrong3 = f"{denom-numer}/{denom}"
            choices = [correct, wrong1, wrong2, wrong3]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["fractions", "word_problem"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(30, 60),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": {"1": "Confused numerator and denominator",
                           "2": "Does not understand equal parts",
                           "3": "Cannot identify shaded portion"},
            "tags": tags, "topic": "ncert_g3_arithmetic",
            "chapter": "Ch5: Fractions",
            "hint": {"level_0": "A fraction shows parts out of a whole.",
                    "level_1": "Numerator = shaded parts, Denominator = total parts.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_3_5"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(-0.8, 0.5), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter6_money(qid_num):
    """Money — bills, making change, profit/loss"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # making change
            paid = random.choice([50, 100, 200, 500])
            cost = random.randint(10, paid - 5)
            correct = paid - cost
            name = pick_name()
            item = random.choice(["notebook", "pencil box", "water bottle", "tiffin box", "bag"])
            stem = f"{name} buys a {item} for ₹{cost} and pays ₹{paid}. How much change will {name} get?"
            choices = [f"₹{correct}", f"₹{correct + 10}", f"₹{cost}", f"₹{correct - 5}"]
            random.shuffle(choices)
            correct_idx = choices.index(f"₹{correct}")
            tags = ["money", "change"]
        elif variant == 1:  # total bill
            items = random.sample(["pen ₹15", "eraser ₹5", "ruler ₹20", "sharpener ₹10", "glue ₹25"], 3)
            prices = [int(i.split("₹")[1]) for i in items]
            total = sum(prices)
            name = pick_name()
            item_str = ", ".join(items)
            stem = f"{name} buys: {item_str}. What is the total cost?"
            correct = f"₹{total}"
            choices = [correct, f"₹{total + 5}", f"₹{total - 10}", f"₹{total + 15}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["money", "bill"]
        elif variant == 2:  # rupees and paise
            rupees = random.randint(10, 99)
            paise = random.choice([25, 50, 75])
            total_paise = rupees * 100 + paise
            stem = f"Convert ₹{rupees}.{paise:02d} to paise."
            correct = f"{total_paise} paise"
            choices = [correct, f"{rupees + paise} paise", f"{rupees * 10 + paise} paise", f"{total_paise + 100} paise"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["money", "conversion"]
        elif variant == 3:  # profit/loss
            cost = random.randint(20, 100)
            sell = cost + random.choice([-10, -5, 5, 10, 15, 20])
            if sell > cost:
                pl = "profit"
                amount = sell - cost
            else:
                pl = "loss"
                amount = cost - sell
            name = pick_name()
            stem = f"{name} bought a toy for ₹{cost} and sold it for ₹{sell}. Is it profit or loss, and how much?"
            correct = f"{pl.title()} of ₹{amount}"
            wrong_pl = "Loss" if pl == "profit" else "Profit"
            choices = [correct, f"{wrong_pl} of ₹{amount}", f"{pl.title()} of ₹{amount + 5}", f"{wrong_pl} of ₹{cost}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["money", "profit_loss"]
        else:  # word problem
            name = pick_name()
            festival = random.choice(FESTIVALS)
            items_bought = random.randint(3, 6)
            price_each = random.choice([25, 30, 40, 50])
            total = items_bought * price_each
            stem = f"For {festival}, {name} bought {items_bought} gifts costing ₹{price_each} each. What is the total spent?"
            correct = f"₹{total}"
            choices = [correct, f"₹{total + price_each}", f"₹{items_bought + price_each}", f"₹{total - price_each}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["money", "word_problem"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(30, 55),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Arithmetic error with money", "2": "Wrong operation", "3": "Confused rupees and paise"},
            "tags": tags, "topic": "ncert_g3_arithmetic",
            "chapter": "Ch6: Money",
            "hint": {"level_0": "Think about what operation fits the situation.",
                    "level_1": "₹1 = 100 paise. Change = Amount paid - Cost.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_3_6"],
            "irt_params": {"a": round(random.uniform(0.9, 1.4), 2),
                          "b": round(random.uniform(-1.0, 0.3), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter7_measurement(qid_num):
    """Measurement — mm/cm/m/km, g/kg, mL/L"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # cm to m
            cm = random.choice([100, 200, 350, 450, 500, 750])
            m = cm / 100
            stem = f"Convert {cm} cm to metres."
            correct = f"{m} m" if m == int(m) else f"{m} m"
            choices = [correct, f"{cm * 100} m", f"{cm / 10} m", f"{cm + 100} m"]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["measurement", "length", "conversion"]
        elif variant == 1:  # kg/g
            kg = random.randint(1, 5)
            g = kg * 1000
            stem = f"How many grams are there in {kg} kg?"
            correct = f"{g} g"
            choices = [correct, f"{kg * 100} g", f"{kg * 10} g", f"{g + 500} g"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["measurement", "weight", "conversion"]
        elif variant == 2:  # mL/L
            l = random.randint(1, 5)
            ml = l * 1000
            stem = f"Convert {l} litres to millilitres."
            correct = f"{ml} mL"
            choices = [correct, f"{l * 100} mL", f"{l * 10} mL", f"{ml + 500} mL"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["measurement", "capacity", "conversion"]
        elif variant == 3:  # word problem
            name = pick_name()
            ribbon_cm = random.randint(100, 500)
            pieces = random.randint(2, 5)
            each = ribbon_cm // pieces
            stem = f"{name} has a ribbon {ribbon_cm} cm long. She cuts it into {pieces} equal pieces. How long is each piece?"
            correct = f"{each} cm"
            choices = [correct, f"{each + 10} cm", f"{ribbon_cm} cm", f"{pieces} cm"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["measurement", "word_problem"]
        else:  # comparison
            a = random.randint(1, 5)
            b = random.randint(100, 900)
            total_cm = a * 100 + b // 10
            stem = f"Which is longer: {a} m {b // 10} cm or {total_cm + random.choice([-20, 20])} cm?"
            actual = a * 100 + b // 10
            other = total_cm + random.choice([-20, 20])
            longer = max(actual, other)
            correct = f"{longer} cm"
            choices = [f"{actual} cm", f"{other} cm", "They are equal", f"{actual + other} cm"]
            correct_idx = choices.index(f"{longer} cm")
            tags = ["measurement", "comparison"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(30, 55),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Wrong conversion factor", "2": "Confused units", "3": "Arithmetic error in conversion"},
            "tags": tags, "topic": "ncert_g3_measurement",
            "chapter": "Ch7: Measurement",
            "hint": {"level_0": "Remember: 1 m = 100 cm, 1 kg = 1000 g, 1 L = 1000 mL.",
                    "level_1": "Multiply or divide by the conversion factor.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_3_7"],
            "irt_params": {"a": round(random.uniform(0.9, 1.4), 2),
                          "b": round(random.uniform(-1.0, 0.2), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter8_time(qid_num):
    """Time — reading clock, duration, am/pm"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # read clock
            hour = random.randint(1, 12)
            minute = random.choice([0, 15, 30, 45, 5, 10, 20, 25, 35, 40, 50, 55])
            correct = f"{hour}:{minute:02d}"
            wrong1 = f"{hour}:{(minute + 15) % 60:02d}"
            wrong2 = f"{(hour % 12) + 1}:{minute:02d}"
            wrong3 = f"{hour}:{(minute + 30) % 60:02d}"
            choices = [correct, wrong1, wrong2, wrong3]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            stem = "What time does the clock show?"
            vis_svg = make_svg_clock(qid, hour, minute, G3_DIR)
            vis_alt = f"Clock showing {hour}:{minute:02d}"
            tags = ["time", "reading_clock"]
        elif variant == 1:  # duration
            start_h = random.randint(8, 14)
            start_m = random.choice([0, 15, 30])
            dur_h = random.randint(1, 3)
            dur_m = random.choice([0, 15, 30, 45])
            end_m = start_m + dur_m
            end_h = start_h + dur_h + end_m // 60
            end_m = end_m % 60
            name = pick_name()
            stem = f"{name} starts studying at {start_h}:{start_m:02d} and studies for {dur_h} hour{'s' if dur_h > 1 else ''} and {dur_m} minutes. What time does {name} finish?"
            correct = f"{end_h}:{end_m:02d}"
            wrong1 = f"{end_h + 1}:{end_m:02d}"
            wrong2 = f"{end_h}:{(end_m + 15) % 60:02d}"
            wrong3 = f"{end_h - 1}:{end_m:02d}"
            choices = [correct, wrong1, wrong2, wrong3]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["time", "duration"]
        elif variant == 2:  # am/pm
            activities = [("breakfast", 8, "AM"), ("lunch", 1, "PM"), ("dinner", 8, "PM"),
                         ("school starts", 9, "AM"), ("bedtime", 9, "PM"), ("snack", 4, "PM")]
            act, hr, period = random.choice(activities)
            stem = f"Is {act} time ({hr}:00) in the AM or PM?"
            correct = period
            choices = ["AM", "PM", "Both", "Neither"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["time", "am_pm"]
        elif variant == 3:  # elapsed time
            start = random.randint(1, 10)
            end = start + random.randint(1, 4)
            elapsed = end - start
            stem = f"A movie starts at {start}:00 PM and ends at {end}:00 PM. How long is the movie?"
            correct = f"{elapsed} hours"
            choices = [correct, f"{elapsed + 1} hours", f"{elapsed - 1} hours" if elapsed > 1 else "30 minutes", f"{start + end} hours"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["time", "elapsed"]
        else:  # conversion
            hours = random.randint(1, 3)
            mins = hours * 60
            stem = f"How many minutes are in {hours} hour{'s' if hours > 1 else ''}?"
            correct = f"{mins} minutes"
            choices = [correct, f"{hours * 100} minutes", f"{hours * 30} minutes", f"{mins + 30} minutes"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["time", "conversion"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(30, 55),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": {"1": "Confused hour and minute hands", "2": "Error in time calculation", "3": "Does not understand AM/PM"},
            "tags": tags, "topic": "ncert_g3_measurement",
            "chapter": "Ch8: Time",
            "hint": {"level_0": "Short hand = hours, long hand = minutes.",
                    "level_1": "1 hour = 60 minutes. AM = before noon, PM = after noon.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_3_8"],
            "irt_params": {"a": round(random.uniform(0.9, 1.4), 2),
                          "b": round(random.uniform(-0.8, 0.3), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter9_geometry(qid_num):
    """Geometry — lines, angles, perimeter"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # perimeter rectangle
            l = random.randint(3, 15)
            w = random.randint(2, 10)
            correct = 2 * (l + w)
            stem = f"Find the perimeter of a rectangle with length {l} cm and width {w} cm."
            choices = [f"{correct} cm", f"{l * w} cm", f"{l + w} cm", f"{correct + 2} cm"]
            random.shuffle(choices)
            correct_idx = choices.index(f"{correct} cm")
            vis_svg = make_svg_shape(qid, "rectangle", [l, w], G3_DIR)
            vis_alt = f"Rectangle with length {l} cm and width {w} cm"
            tags = ["geometry", "perimeter", "rectangle"]
        elif variant == 1:  # perimeter square
            s = random.randint(3, 12)
            correct = 4 * s
            stem = f"Find the perimeter of a square with side {s} cm."
            choices = [f"{correct} cm", f"{s * s} cm", f"{2 * s} cm", f"{correct + 4} cm"]
            random.shuffle(choices)
            correct_idx = choices.index(f"{correct} cm")
            vis_svg = make_svg_shape(qid, "square", [s], G3_DIR)
            vis_alt = f"Square with side {s} cm"
            tags = ["geometry", "perimeter", "square"]
        elif variant == 2:  # identify shapes
            shapes = ["triangle", "rectangle", "square", "circle"]
            props = [("3 sides and 3 corners", "triangle"),
                    ("4 equal sides and 4 right angles", "square"),
                    ("2 long sides and 2 short sides", "rectangle"),
                    ("no corners and no sides", "circle")]
            prop_text, correct = random.choice(props)
            stem = f"Which shape has {prop_text}?"
            choices = shapes[:]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["geometry", "shapes", "identify"]
        elif variant == 3:  # lines
            types = [("goes on forever in both directions", "Line"),
                    ("has two endpoints", "Line segment"),
                    ("starts at one point and goes on forever", "Ray")]
            desc, correct = random.choice(types)
            stem = f"What {desc}?"
            choices = ["Line", "Line segment", "Ray", "Curve"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["geometry", "lines"]
        else:  # perimeter word problem
            name = pick_name()
            l = random.randint(5, 20)
            w = random.randint(3, 15)
            correct = 2 * (l + w)
            stem = f"{name}'s garden is rectangular, {l} m long and {w} m wide. How much fencing is needed to go around it?"
            choices = [f"{correct} m", f"{l * w} m", f"{l + w} m", f"{correct + 10} m"]
            random.shuffle(choices)
            correct_idx = choices.index(f"{correct} m")
            vis_svg = None
            vis_alt = None
            tags = ["geometry", "perimeter", "word_problem"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(30, 60),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": {"1": "Confused perimeter with area", "2": "Added only 2 sides", "3": "Used wrong formula"},
            "tags": tags, "topic": "ncert_g3_geometry",
            "chapter": "Ch9: Geometry",
            "hint": {"level_0": "Perimeter = distance around the shape.",
                    "level_1": "For rectangle: P = 2×(length + width). For square: P = 4×side.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_3_9"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(-0.8, 0.5), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter10_patterns(qid_num):
    """Patterns — growing patterns, sequences, rules"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # arithmetic sequence
            start = random.randint(2, 10)
            step = random.randint(2, 7)
            seq = [start + j * step for j in range(5)]
            missing_idx = random.randint(3, 4)
            answer = seq[missing_idx]
            display = seq[:missing_idx] + [None]
            stem = f"Find the next number: {', '.join(str(x) for x in seq[:missing_idx])}, ?"
            correct = str(answer)
            choices = [correct, str(answer + step), str(answer - step), str(answer + 1)]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_pattern(qid, seq[:missing_idx] + [None], G3_DIR)
            vis_alt = f"Number pattern: {', '.join(str(x) for x in seq[:missing_idx])}, ?"
            tags = ["patterns", "arithmetic_sequence"]
        elif variant == 1:  # multiplication pattern
            base = random.randint(2, 5)
            seq = [base * (j + 1) for j in range(5)]
            stem = f"What comes next: {', '.join(str(x) for x in seq[:4])}, ?"
            correct = str(seq[4])
            choices = [correct, str(seq[4] + base), str(seq[4] - 1), str(seq[3] + 1)]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_pattern(qid, seq[:4] + [None], G3_DIR)
            vis_alt = f"Pattern: multiples of {base}"
            tags = ["patterns", "multiplication_pattern"]
        elif variant == 2:  # rule finding
            start = random.randint(1, 5)
            rule = random.choice([3, 4, 5, 6])
            seq = [start + j * rule for j in range(4)]
            stem = f"The pattern is: {', '.join(str(x) for x in seq)}. What is the rule?"
            correct = f"Add {rule}"
            choices = [correct, f"Add {rule + 1}", f"Multiply by {rule}", f"Add {rule - 1}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["patterns", "rule"]
        elif variant == 3:  # decreasing pattern
            start = random.randint(50, 100)
            step = random.randint(5, 10)
            seq = [start - j * step for j in range(5)]
            stem = f"Find the next number: {', '.join(str(x) for x in seq[:4])}, ?"
            correct = str(seq[4])
            choices = [correct, str(seq[4] + step), str(seq[4] - step * 2), str(seq[3])]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["patterns", "decreasing"]
        else:  # shape pattern
            shapes = ["triangle", "square", "circle"]
            pattern = random.sample(shapes, 2)
            seq_display = (pattern * 4)[:7]
            next_shape = pattern[len(seq_display) % len(pattern)]
            stem = f"The pattern is: {', '.join(seq_display)}. What comes next?"
            correct = next_shape
            choices = shapes + ["pentagon"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["patterns", "shape_pattern"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(30, 55),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": {"1": "Did not identify the rule", "2": "Applied rule incorrectly", "3": "Confused increasing/decreasing"},
            "tags": tags, "topic": "ncert_g3_patterns",
            "chapter": "Ch10: Patterns",
            "hint": {"level_0": "Look at how each number changes to the next.",
                    "level_1": "Find the difference between consecutive numbers.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_3_10"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(-0.7, 0.4), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter11_data(qid_num):
    """Data Handling — bar graphs, tables"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 4

        fruits = random.sample(["Mango", "Apple", "Banana", "Guava", "Orange"], 4)
        values = [random.randint(5, 30) for _ in range(4)]

        if variant == 0:  # read bar graph - most
            max_idx = values.index(max(values))
            stem = "Look at the bar graph. Which fruit is liked by the most students?"
            correct = fruits[max_idx]
            choices = fruits[:]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_bar_chart(qid, fruits, values, "Favourite Fruits", G3_DIR)
            vis_alt = f"Bar graph of favourite fruits: {dict(zip(fruits, values))}"
            tags = ["data", "bar_graph", "most"]
        elif variant == 1:  # total from graph
            total = sum(values)
            stem = "How many students were surveyed in total? (Look at the bar graph)"
            correct = str(total)
            choices = [str(total), str(total + 5), str(max(values)), str(total - min(values))]
            random.shuffle(choices)
            correct_idx = choices.index(str(total))
            vis_svg = make_svg_bar_chart(qid, fruits, values, "Favourite Fruits Survey", G3_DIR)
            vis_alt = f"Bar graph showing survey results"
            tags = ["data", "bar_graph", "total"]
        elif variant == 2:  # difference
            if len(values) >= 2:
                idx1, idx2 = 0, 1
                diff = abs(values[idx1] - values[idx2])
                stem = f"How many more students like {fruits[idx1]} than {fruits[idx2]}?" if values[idx1] > values[idx2] else f"How many more students like {fruits[idx2]} than {fruits[idx1]}?"
                correct = str(diff)
                choices = [str(diff), str(diff + 2), str(values[idx1] + values[idx2]), str(diff - 1 if diff > 1 else diff + 3)]
                random.shuffle(choices)
                correct_idx = choices.index(str(diff))
            else:
                correct = str(values[0])
                choices = [correct, "0", "10", "5"]
                correct_idx = 0
                stem = "How many like the first fruit?"
            vis_svg = make_svg_bar_chart(qid, fruits, values, "Fruit Preferences", G3_DIR)
            vis_alt = f"Bar graph comparing fruit preferences"
            tags = ["data", "bar_graph", "difference"]
        else:  # table reading
            subjects = random.sample(["Maths", "Hindi", "English", "EVS", "Art"], 4)
            marks = [random.randint(60, 100) for _ in range(4)]
            name = pick_name()
            max_subj = subjects[marks.index(max(marks))]
            stem = f"{name}'s marks: {', '.join(f'{s}: {m}' for s, m in zip(subjects, marks))}. In which subject did {name} score the highest?"
            correct = max_subj
            choices = subjects[:]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["data", "table", "highest"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(30, 55),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": {"1": "Misread the bar height", "2": "Confused most with least", "3": "Addition error when finding total"},
            "tags": tags, "topic": "ncert_g3_data",
            "chapter": "Ch11: Data Handling",
            "hint": {"level_0": "Read the graph/table carefully.",
                    "level_1": "Compare the heights of bars or values in the table.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_3_11"],
            "irt_params": {"a": round(random.uniform(0.9, 1.4), 2),
                          "b": round(random.uniform(-0.8, 0.3), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter12_area(qid_num):
    """Area — counting squares, estimating"""
    questions = []
    for i in range(22):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 4

        if variant == 0:  # count squares
            rows = random.randint(2, 5)
            cols = random.randint(2, 6)
            shaded = rows * cols
            stem = f"Count the squares in the grid to find the area."
            correct = f"{shaded} square units"
            choices = [correct, f"{shaded + 2} square units", f"{2*(rows+cols)} square units", f"{shaded - 1} square units"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_grid_area(qid, rows, cols, shaded, G3_DIR)
            vis_alt = f"Grid of {rows} rows and {cols} columns, all shaded"
            tags = ["area", "counting_squares"]
        elif variant == 1:  # partial shading
            rows = random.randint(3, 5)
            cols = random.randint(3, 6)
            shaded = random.randint(rows, rows * cols - 2)
            stem = f"How many squares are shaded (blue) in the grid?"
            correct = str(shaded)
            choices = [str(shaded), str(shaded + 2), str(rows * cols), str(shaded - 1)]
            random.shuffle(choices)
            correct_idx = choices.index(str(shaded))
            vis_svg = make_svg_grid_area(qid, rows, cols, shaded, G3_DIR)
            vis_alt = f"Grid with {shaded} out of {rows*cols} squares shaded"
            tags = ["area", "counting_squares"]
        elif variant == 2:  # area of rectangle
            l = random.randint(3, 10)
            w = random.randint(2, 8)
            area = l * w
            stem = f"Find the area of a rectangle with length {l} cm and width {w} cm."
            correct = f"{area} sq cm"
            choices = [f"{area} sq cm", f"{2*(l+w)} sq cm", f"{l + w} sq cm", f"{area + l} sq cm"]
            random.shuffle(choices)
            correct_idx = choices.index(f"{area} sq cm")
            vis_svg = make_svg_shape(qid, "rectangle", [l, w], G3_DIR)
            vis_alt = f"Rectangle {l} cm by {w} cm"
            tags = ["area", "rectangle"]
        else:  # comparison
            l1, w1 = random.randint(3, 8), random.randint(2, 6)
            l2, w2 = random.randint(3, 8), random.randint(2, 6)
            a1, a2 = l1 * w1, l2 * w2
            while a1 == a2:
                l2 = random.randint(3, 8)
                a2 = l2 * w2
            bigger = "A" if a1 > a2 else "B"
            stem = f"Shape A: {l1} cm × {w1} cm. Shape B: {l2} cm × {w2} cm. Which has more area?"
            correct = f"Shape {bigger}"
            choices = ["Shape A", "Shape B", "Both are equal", "Cannot tell"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["area", "comparison"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(30, 60),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": {"1": "Confused area with perimeter", "2": "Miscounted squares", "3": "Used wrong formula"},
            "tags": tags, "topic": "ncert_g3_geometry",
            "chapter": "Ch12: Area",
            "hint": {"level_0": "Area = number of square units that fit inside.",
                    "level_1": "For rectangle: Area = length × width.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_3_12"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(-0.5, 0.5), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter13_weight_capacity(qid_num):
    """Weight & Capacity — comparing, word problems"""
    questions = []
    for i in range(22):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 4

        if variant == 0:  # compare weights
            items = [("watermelon", random.randint(2, 5)), ("apple", 0), ("book", 0), ("bag of rice", random.randint(1, 10))]
            a_item = random.choice(["watermelon", "bag of rice", "pumpkin"])
            a_wt = random.randint(2, 8)
            b_item = random.choice(["apple", "orange", "pencil"])
            b_wt_g = random.randint(100, 500)
            stem = f"Which is heavier: a {a_item} weighing {a_wt} kg or a {b_item} weighing {b_wt_g} g?"
            correct = f"{a_item} ({a_wt} kg)"
            choices = [correct, f"{b_item} ({b_wt_g} g)", "Both weigh the same", "Cannot compare"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["weight", "comparison"]
        elif variant == 1:  # addition of weights
            name = pick_name()
            w1 = random.randint(1, 5)
            w2 = random.randint(1, 5)
            total = w1 + w2
            stem = f"{name} bought {w1} kg of potatoes and {w2} kg of onions. What is the total weight?"
            correct = f"{total} kg"
            choices = [f"{total} kg", f"{total + 1} kg", f"{w1 * w2} kg", f"{total - 1} kg"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["weight", "addition"]
        elif variant == 2:  # capacity
            name = pick_name()
            bottles = random.randint(3, 8)
            each_ml = random.choice([250, 500, 200, 750])
            total = bottles * each_ml
            stem = f"{name} has {bottles} bottles, each holding {each_ml} mL. What is the total capacity?"
            correct = f"{total} mL"
            choices = [f"{total} mL", f"{total + each_ml} mL", f"{bottles + each_ml} mL", f"{total - each_ml} mL"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["capacity", "multiplication"]
        else:  # conversion word problem
            litres = random.randint(2, 5)
            ml = litres * 1000
            glasses = random.choice([200, 250, 500])
            num_glasses = ml // glasses
            stem = f"A jug holds {litres} litres of water. How many glasses of {glasses} mL can be filled?"
            correct = str(num_glasses)
            choices = [str(num_glasses), str(num_glasses + 1), str(litres), str(num_glasses - 1)]
            random.shuffle(choices)
            correct_idx = choices.index(str(num_glasses))
            tags = ["capacity", "division", "word_problem"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(30, 55),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Wrong conversion (kg to g or L to mL)", "2": "Arithmetic error", "3": "Chose wrong operation"},
            "tags": tags, "topic": "ncert_g3_measurement",
            "chapter": "Ch13: Weight & Capacity",
            "hint": {"level_0": "1 kg = 1000 g, 1 L = 1000 mL.",
                    "level_1": "Convert to same units before comparing.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_3_13"],
            "irt_params": {"a": round(random.uniform(0.9, 1.4), 2),
                          "b": round(random.uniform(-0.8, 0.3), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g3_chapter14_symmetry(qid_num):
    """Symmetry — mirror images, folding"""
    questions = []
    for i in range(22):
        qid = f"NCERT-G3-{qid_num:03d}"
        variant = i % 4

        if variant == 0:  # identify symmetric
            shapes = [("circle", "Yes"), ("square", "Yes"), ("rectangle", "Yes"),
                     ("scalene triangle", "No"), ("equilateral triangle", "Yes")]
            shape, ans = random.choice(shapes)
            stem = f"Does a {shape} have a line of symmetry?"
            correct = ans
            choices = ["Yes", "No", "Only sometimes", "Cannot tell"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_symmetry(qid, "butterfly" if ans == "Yes" else "triangle", G3_DIR)
            vis_alt = f"Shape showing symmetry line"
            tags = ["symmetry", "identify"]
        elif variant == 1:  # lines of symmetry count
            data = [("square", 4), ("rectangle", 2), ("equilateral triangle", 3), ("circle", "infinite")]
            shape, count = random.choice(data[:3])  # skip circle for MCQ
            stem = f"How many lines of symmetry does a {shape} have?"
            correct = str(count)
            choices = [str(count), str(count + 1), str(count - 1) if count > 1 else "0", "0"]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(str(count))
            vis_svg = None
            vis_alt = None
            tags = ["symmetry", "count_lines"]
        elif variant == 2:  # mirror image
            letters = [("A", "Yes"), ("B", "Yes"), ("C", "No"), ("D", "Yes"), ("E", "No"), ("M", "Yes")]
            letter, sym = random.choice(letters)
            stem = f"Does the letter '{letter}' have vertical symmetry?"
            correct = sym
            choices = ["Yes", "No", "Only horizontal", "Both"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["symmetry", "letters"]
        else:  # folding
            stem = "If you fold a shape along its line of symmetry, the two halves will:"
            correct = "Match exactly"
            choices = ["Match exactly", "Be different sizes", "Not overlap", "Make a new shape"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_symmetry(qid, "butterfly", G3_DIR)
            vis_alt = "Butterfly shape with line of symmetry"
            tags = ["symmetry", "folding"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(25, 50),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": {"1": "Does not understand mirror image", "2": "Confused symmetry with rotation", "3": "Cannot identify the fold line"},
            "tags": tags, "topic": "ncert_g3_geometry",
            "chapter": "Ch14: Symmetry",
            "hint": {"level_0": "Symmetry means one half is the mirror image of the other.",
                    "level_1": "Fold along the line — do both sides match?",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_3_14"],
            "irt_params": {"a": round(random.uniform(0.9, 1.4), 2),
                          "b": round(random.uniform(-0.5, 0.5), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num


# ============================================================
# GRADE 4 QUESTION GENERATORS
# ============================================================

def g4_chapter1_numbers(qid_num):
    """Numbers beyond 9999 — lakhs, Indian system"""
    questions = []
    for i in range(22):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 6

        if variant == 0:  # place value in lakhs
            n = random.randint(10000, 99999)
            place = random.choice(["ten thousands", "thousands", "hundreds", "tens", "ones"])
            digits = {"ten thousands": n // 10000, "thousands": (n // 1000) % 10,
                     "hundreds": (n // 100) % 10, "tens": (n // 10) % 10, "ones": n % 10}
            correct = str(digits[place])
            wrong = [str(d) for d in range(10) if str(d) != correct]
            random.shuffle(wrong)
            choices = [correct, wrong[0], wrong[1], wrong[2]]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            stem = f"In the number {n:,}, what is the digit in the {place} place?"
            tags = ["numbers", "place_value", "5_digit"]
        elif variant == 1:  # Indian number system
            n = random.randint(100000, 999999)
            # Format Indian style
            s = str(n)
            indian = s[:-3] + "," + s[-3:] if len(s) > 3 else s
            if len(s) > 5:
                indian = s[:-5] + "," + s[-5:-3] + "," + s[-3:]
            stem = f"Write {n} in the Indian number system with commas."
            correct = indian
            # Wrong formats
            intl = f"{n:,}"  # international
            wrong1 = s[:-2] + "," + s[-2:] if len(s) > 2 else s
            wrong2 = s[:-4] + "," + s[-4:] if len(s) > 4 else s
            choices = [correct, intl, wrong1, wrong2]
            choices = list(dict.fromkeys(choices))[:4]
            while len(choices) < 4:
                choices.append(str(n + 1000))
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["numbers", "indian_system"]
        elif variant == 2:  # expanded form
            n = random.randint(10000, 99999)
            tt, th, h, t, o = n//10000, (n//1000)%10, (n//100)%10, (n//10)%10, n%10
            correct = f"{tt*10000} + {th*1000} + {h*100} + {t*10} + {o}"
            wrong1 = f"{tt*1000} + {th*10000} + {h*100} + {t*10} + {o}"
            wrong2 = f"{tt*10000} + {th*100} + {h*1000} + {t*10} + {o}"
            wrong3 = f"{tt*10000} + {th*1000} + {h*100} + {t} + {o*10}"
            choices = [correct, wrong1, wrong2, wrong3]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            stem = f"Write the expanded form of {n}."
            tags = ["numbers", "expanded_form"]
        elif variant == 3:  # compare 5-digit
            a = random.randint(10000, 99999)
            b = random.randint(10000, 99999)
            while a == b:
                b = random.randint(10000, 99999)
            correct = f"{max(a,b)}"
            stem = f"Which is greater: {a} or {b}?"
            choices = [str(a), str(b), "They are equal", str(a + b)]
            correct_idx = choices.index(correct)
            tags = ["numbers", "comparison"]
        elif variant == 4:  # rounding
            n = random.randint(10000, 99999)
            rounded = round(n, -3)
            stem = f"Round {n} to the nearest thousand."
            correct = str(rounded)
            choices = [str(rounded), str(rounded + 1000), str(rounded - 1000), str(round(n, -2))]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(str(rounded))
            tags = ["numbers", "rounding"]
        else:  # form numbers
            digits = random.sample(range(1, 9), 4)
            digits_sorted_desc = sorted(digits, reverse=True)
            largest = int("".join(str(d) for d in digits_sorted_desc))
            stem = f"Form the largest 4-digit number using digits {', '.join(str(d) for d in digits)} (each used once)."
            correct = str(largest)
            smallest = int("".join(str(d) for d in sorted(digits)))
            choices = [str(largest), str(smallest), str(largest - 1000), str(int("".join(str(d) for d in digits)))]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(str(largest))
            tags = ["numbers", "form_numbers"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "easy" if variant < 2 else "medium",
            "difficulty_score": random.randint(20, 50),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Confused place values", "2": "Wrong Indian format", "3": "Comparison error"},
            "tags": tags, "topic": "ncert_g4_arithmetic",
            "chapter": "Ch1: Numbers beyond 9999",
            "hint": {"level_0": "Indian system: ones, tens, hundreds, thousands, ten-thousands, lakhs.",
                    "level_1": "Commas in Indian system: after hundreds, then every 2 digits.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_1"],
            "irt_params": {"a": round(random.uniform(0.8, 1.4), 2),
                          "b": round(random.uniform(-0.5, 0.8), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter2_multiplication(qid_num):
    """Multiplication — 3-digit × 2-digit"""
    questions = []
    for i in range(22):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # 3-digit × 1-digit
            a = random.randint(100, 999)
            b = random.randint(2, 9)
            correct = a * b
            stem = f"Multiply: {a} × {b} = ?"
            choices = [str(correct), str(correct + b), str(correct - a), str(correct + 100)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["multiplication", "3digit_1digit"]
        elif variant == 1:  # 2-digit × 2-digit
            a = random.randint(11, 99)
            b = random.randint(11, 50)
            correct = a * b
            stem = f"Find the product: {a} × {b}"
            choices = [str(correct), str(correct + a), str(correct - b), str(correct + 10)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["multiplication", "2digit_2digit"]
        elif variant == 2:  # 3-digit × 2-digit
            a = random.randint(100, 500)
            b = random.randint(11, 30)
            correct = a * b
            stem = f"Calculate: {a} × {b} = ?"
            choices = [str(correct), str(correct + a), str(correct + b * 10), str(correct - 100)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["multiplication", "3digit_2digit"]
        elif variant == 3:  # word problem
            name = pick_name()
            city = pick_city()
            per_day = random.randint(50, 200)
            days = random.randint(12, 30)
            correct = per_day * days
            stem = f"A factory in {city} makes {per_day} toys per day. How many toys in {days} days?"
            choices = [str(correct), str(correct + per_day), str(per_day + days), str(correct - 100)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["multiplication", "word_problem"]
        else:  # estimation
            a = random.randint(100, 500)
            b = random.randint(11, 50)
            ra = round(a, -2)
            rb = round(b, -1)
            estimate = ra * rb
            stem = f"Estimate {a} × {b} by rounding."
            actual = a * b
            choices = [str(estimate), str(actual), str(estimate + 1000), str(estimate - 500)]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(str(estimate))
            tags = ["multiplication", "estimation"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium" if variant < 3 else "hard",
            "difficulty_score": random.randint(35, 65),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Carry/regrouping error", "2": "Partial product error", "3": "Did not align partial products"},
            "tags": tags, "topic": "ncert_g4_arithmetic",
            "chapter": "Ch2: Multiplication",
            "hint": {"level_0": "Break into parts: multiply by ones, then by tens.",
                    "level_1": "Use partial products method: multiply each digit separately.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_2"],
            "irt_params": {"a": round(random.uniform(1.0, 1.6), 2),
                          "b": round(random.uniform(-0.3, 1.0), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter3_division(qid_num):
    """Division — long division, checking"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # exact 3-digit ÷ 1-digit
            b = random.randint(2, 9)
            q_val = random.randint(20, 150)
            a = b * q_val
            correct = q_val
            stem = f"Divide: {a} ÷ {b} = ?"
            choices = [str(correct), str(correct + 1), str(correct - 1), str(b)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["division", "exact", "3digit"]
        elif variant == 1:  # with remainder
            b = random.randint(3, 9)
            q_val = random.randint(30, 100)
            r = random.randint(1, b - 1)
            a = b * q_val + r
            stem = f"Divide {a} by {b}. What is the remainder?"
            correct = str(r)
            choices = [str(r), str(r + 1), "0", str(b - r)]
            random.shuffle(choices)
            correct_idx = choices.index(str(r))
            tags = ["division", "remainder"]
        elif variant == 2:  # 4-digit ÷ 1-digit
            b = random.randint(2, 9)
            q_val = random.randint(100, 1000)
            a = b * q_val
            correct = q_val
            stem = f"What is {a} ÷ {b}?"
            choices = [str(correct), str(correct + 10), str(correct - 10), str(correct * 2)]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["division", "4digit", "long_division"]
        elif variant == 3:  # checking division
            b = random.randint(3, 9)
            q_val = random.randint(20, 80)
            r = random.randint(0, b - 1)
            a = b * q_val + r
            stem = f"Check: if {a} ÷ {b} = {q_val} remainder {r}, then {b} × {q_val} + {r} = ?"
            correct = str(a)
            choices = [str(a), str(a + 1), str(b * q_val), str(a - r)]
            random.shuffle(choices)
            correct_idx = choices.index(str(a))
            tags = ["division", "verification"]
        else:  # word problem
            name = pick_name()
            total = random.randint(100, 500)
            groups = random.randint(3, 9)
            each = total // groups
            remainder = total % groups
            if remainder == 0:
                stem = f"{name} has {total} stickers to distribute equally among {groups} friends. How many does each get?"
                correct = str(each)
            else:
                stem = f"{name} divides {total} beads equally into {groups} boxes. How many are left over?"
                correct = str(remainder)
            choices = [correct, str(int(correct) + 1), str(groups), str(total)]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["division", "word_problem"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(35, 60),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Long division step error", "2": "Forgot remainder", "3": "Wrong placement of quotient digits"},
            "tags": tags, "topic": "ncert_g4_arithmetic",
            "chapter": "Ch3: Division",
            "hint": {"level_0": "Divide step by step from the leftmost digit.",
                    "level_1": "Check: Divisor × Quotient + Remainder = Dividend.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_3"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(-0.2, 1.0), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter4_factors(qid_num):
    """Multiples & Factors — LCM, HCF, primes"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 6

        if variant == 0:  # factors
            n = random.choice([12, 15, 18, 20, 24, 30, 36])
            factors = [x for x in range(1, n + 1) if n % x == 0]
            test = random.choice([random.choice(factors), random.randint(1, n)])
            is_factor = test in factors
            stem = f"Is {test} a factor of {n}?"
            correct = "Yes" if is_factor else "No"
            choices = ["Yes", "No", f"Only if {n} is even", "Cannot tell"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["factors"]
        elif variant == 1:  # multiples
            n = random.randint(3, 9)
            mult = [n * i for i in range(1, 6)]
            test = random.choice(mult + [mult[-1] + 1])
            is_mult = test % n == 0
            stem = f"Is {test} a multiple of {n}?"
            correct = "Yes" if is_mult else "No"
            choices = ["Yes", "No", "Sometimes", "Cannot tell"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["multiples"]
        elif variant == 2:  # prime
            n = random.choice([7, 11, 13, 17, 19, 23, 4, 9, 15, 21, 25])
            is_prime = all(n % i != 0 for i in range(2, int(n**0.5) + 1)) and n > 1
            stem = f"Is {n} a prime number?"
            correct = "Yes" if is_prime else "No"
            choices = ["Yes", "No", "It is composite", "Cannot tell"]
            if not is_prime:
                choices[2] = "Yes, it is prime"
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["prime_numbers"]
        elif variant == 3:  # LCM
            a = random.randint(2, 8)
            b = random.randint(2, 8)
            lcm_val = (a * b) // math.gcd(a, b)
            stem = f"Find the LCM of {a} and {b}."
            correct = str(lcm_val)
            choices = [str(lcm_val), str(a * b), str(math.gcd(a, b)), str(lcm_val + a)]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(str(lcm_val))
            tags = ["LCM"]
        elif variant == 4:  # HCF
            a = random.choice([12, 16, 18, 20, 24, 30])
            b = random.choice([8, 12, 15, 16, 20, 24])
            hcf_val = math.gcd(a, b)
            stem = f"Find the HCF of {a} and {b}."
            correct = str(hcf_val)
            choices = [str(hcf_val), str(hcf_val * 2), str(a * b // hcf_val), str(hcf_val + 1)]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(str(hcf_val))
            tags = ["HCF"]
        else:  # common multiples
            a = random.randint(2, 6)
            b = random.randint(2, 6)
            lcm_val = (a * b) // math.gcd(a, b)
            common = [lcm_val * i for i in range(1, 4)]
            stem = f"Which is a common multiple of {a} and {b}?"
            correct = str(common[0])
            wrong = [str(common[0] + 1), str(a + b), str(a * 3 + 1)]
            choices = [correct] + wrong
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["common_multiples"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium" if variant < 3 else "hard",
            "difficulty_score": random.randint(40, 70),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Confused factors with multiples", "2": "Incomplete factor list", "3": "LCM/HCF confusion"},
            "tags": tags, "topic": "ncert_g4_arithmetic",
            "chapter": "Ch4: Multiples & Factors",
            "hint": {"level_0": "Factors divide evenly. Multiples are products.",
                    "level_1": "LCM = smallest common multiple. HCF = largest common factor.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_4"],
            "irt_params": {"a": round(random.uniform(1.0, 1.6), 2),
                          "b": round(random.uniform(0.0, 1.2), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter5_fractions(qid_num):
    """Fractions — add/sub like fractions, mixed numbers"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # add like fractions
            denom = random.choice([5, 6, 7, 8, 9, 10])
            a = random.randint(1, denom - 2)
            b = random.randint(1, denom - a - 1)
            correct_n = a + b
            stem = f"Add: {a}/{denom} + {b}/{denom} = ?"
            correct = f"{correct_n}/{denom}"
            choices = [correct, f"{a + b}/{denom * 2}", f"{a * b}/{denom}", f"{correct_n + 1}/{denom}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_fraction(qid, correct_n, denom, G4_DIR)
            vis_alt = f"Fraction showing {correct_n}/{denom}"
            tags = ["fractions", "addition"]
        elif variant == 1:  # subtract like fractions
            denom = random.choice([5, 6, 7, 8, 10])
            a = random.randint(3, denom - 1)
            b = random.randint(1, a - 1)
            correct_n = a - b
            stem = f"Subtract: {a}/{denom} - {b}/{denom} = ?"
            correct = f"{correct_n}/{denom}"
            choices = [correct, f"{a + b}/{denom}", f"{correct_n}/{denom * 2}", f"{correct_n + 1}/{denom}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["fractions", "subtraction"]
        elif variant == 2:  # mixed to improper
            whole = random.randint(1, 5)
            denom = random.choice([3, 4, 5, 6, 8])
            numer = random.randint(1, denom - 1)
            improper_n = whole * denom + numer
            stem = f"Convert {whole} {numer}/{denom} to an improper fraction."
            correct = f"{improper_n}/{denom}"
            choices = [correct, f"{whole + numer}/{denom}", f"{numer}/{whole * denom}", f"{improper_n + 1}/{denom}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["fractions", "mixed_numbers"]
        elif variant == 3:  # improper to mixed
            denom = random.choice([3, 4, 5, 6, 7])
            whole = random.randint(2, 5)
            numer_part = random.randint(1, denom - 1)
            improper = whole * denom + numer_part
            stem = f"Convert {improper}/{denom} to a mixed number."
            correct = f"{whole} {numer_part}/{denom}"
            choices = [correct, f"{whole + 1} {numer_part}/{denom}", f"{whole} {numer_part + 1}/{denom}", f"{improper} {0}/{denom}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["fractions", "mixed_numbers", "conversion"]
        else:  # word problem
            name = pick_name()
            denom = random.choice([4, 5, 6, 8])
            ate = random.randint(1, denom - 2)
            more = random.randint(1, denom - ate - 1)
            total = ate + more
            item = random.choice(["pizza", "cake", "watermelon"])
            stem = f"{name} ate {ate}/{denom} of a {item} in the morning and {more}/{denom} in the evening. How much did {name} eat in all?"
            correct = f"{total}/{denom}"
            choices = [correct, f"{ate * more}/{denom}", f"{total}/{denom * 2}", f"{total + 1}/{denom}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_fraction(qid, total, denom, G4_DIR)
            vis_alt = f"Fraction circle showing {total}/{denom}"
            tags = ["fractions", "word_problem", "addition"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(35, 60),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": {"1": "Added/subtracted denominators", "2": "Conversion error with mixed numbers", "3": "Did not simplify"},
            "tags": tags, "topic": "ncert_g4_arithmetic",
            "chapter": "Ch5: Fractions",
            "hint": {"level_0": "For like fractions, only add/subtract the numerators.",
                    "level_1": "Mixed → Improper: (whole × denom) + numerator over denom.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_5"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(-0.3, 0.8), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter6_decimals(qid_num):
    """Decimals — tenths, hundredths, money"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # fraction to decimal
            choices_data = [(1, 10, "0.1"), (3, 10, "0.3"), (7, 10, "0.7"),
                          (1, 4, "0.25"), (1, 2, "0.5"), (3, 4, "0.75")]
            numer, denom, dec = random.choice(choices_data)
            stem = f"Convert {numer}/{denom} to a decimal."
            correct = dec
            choices = [dec, str(float(dec) + 0.1), str(numer), f"{numer}.{denom}"]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["decimals", "conversion"]
        elif variant == 1:  # place value in decimal
            n = round(random.uniform(1, 99) + random.choice([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]), 1)
            tenths_digit = int(str(n).split('.')[1][0])
            stem = f"In {n}, what is the digit in the tenths place?"
            correct = str(tenths_digit)
            wrong = [str((tenths_digit + 1) % 10), str((tenths_digit + 3) % 10), str(int(n) % 10)]
            choices = [correct] + wrong[:3]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["decimals", "place_value"]
        elif variant == 2:  # compare decimals
            a = round(random.uniform(1, 10), 1)
            b = round(random.uniform(1, 10), 1)
            while a == b:
                b = round(random.uniform(1, 10), 1)
            correct = str(max(a, b))
            stem = f"Which is greater: {a} or {b}?"
            choices = [str(a), str(b), "They are equal", str(a + b)]
            correct_idx = choices.index(correct)
            tags = ["decimals", "comparison"]
        elif variant == 3:  # money as decimal
            rupees = random.randint(10, 200)
            paise = random.choice([25, 50, 75, 10, 20])
            decimal_form = f"{rupees}.{paise:02d}"
            stem = f"Write ₹{rupees} and {paise} paise as a decimal."
            correct = f"₹{decimal_form}"
            choices = [f"₹{decimal_form}", f"₹{rupees}{paise}", f"₹{rupees}.{paise}", f"₹{rupees + paise}"]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["decimals", "money"]
        else:  # addition of decimals
            a = round(random.uniform(1, 20), 1)
            b = round(random.uniform(1, 20), 1)
            correct = round(a + b, 1)
            stem = f"Add: {a} + {b} = ?"
            choices = [str(correct), str(round(correct + 0.1, 1)), str(round(correct - 1, 1)), str(round(a * b, 1))]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(str(correct))
            tags = ["decimals", "addition"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(35, 60),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Confused tenths and hundredths", "2": "Decimal point placement error", "3": "Did not align decimal points"},
            "tags": tags, "topic": "ncert_g4_arithmetic",
            "chapter": "Ch6: Decimals",
            "hint": {"level_0": "The first digit after the decimal point is tenths.",
                    "level_1": "Line up decimal points when adding. ₹1 = 100 paise.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_6"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(-0.2, 1.0), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter7_measurement(qid_num):
    """Measurement — advanced conversions"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # km to m
            km = random.randint(1, 10)
            extra_m = random.randint(0, 999)
            total_m = km * 1000 + extra_m
            stem = f"Convert {km} km {extra_m} m to metres."
            correct = f"{total_m} m"
            choices = [f"{total_m} m", f"{km * 100 + extra_m} m", f"{km + extra_m} m", f"{total_m + 1000} m"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["measurement", "length", "km"]
        elif variant == 1:  # kg and g
            kg = random.randint(1, 8)
            g = random.randint(100, 900)
            total_g = kg * 1000 + g
            stem = f"Express {kg} kg {g} g in grams."
            correct = f"{total_g} g"
            choices = [f"{total_g} g", f"{kg * 100 + g} g", f"{kg + g} g", f"{total_g + 100} g"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["measurement", "weight"]
        elif variant == 2:  # word problem
            name = pick_name()
            dist1 = random.randint(2, 5)
            dist2_m = random.randint(200, 800)
            total = dist1 * 1000 + dist2_m
            stem = f"{name} walked {dist1} km and then {dist2_m} m more. What is the total distance in metres?"
            correct = f"{total} m"
            choices = [f"{total} m", f"{dist1 + dist2_m} m", f"{total + 1000} m", f"{dist1 * dist2_m} m"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["measurement", "word_problem"]
        elif variant == 3:  # subtraction of measurements
            a_kg = random.randint(3, 10)
            a_g = random.randint(200, 800)
            b_kg = random.randint(1, a_kg - 1)
            b_g = random.randint(100, 700)
            total_a = a_kg * 1000 + a_g
            total_b = b_kg * 1000 + b_g
            diff = total_a - total_b
            stem = f"Subtract: {a_kg} kg {a_g} g - {b_kg} kg {b_g} g = ? (answer in grams)"
            correct = f"{diff} g"
            choices = [f"{diff} g", f"{diff + 1000} g", f"{(a_kg - b_kg) * 1000} g", f"{diff - 100} g"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["measurement", "subtraction"]
        else:  # comparison
            a = random.randint(2, 5)
            b_cm = random.randint(100, 500)
            a_cm = a * 100
            stem = f"Which is longer: {a} m or {b_cm} cm?"
            longer = f"{a} m" if a_cm > b_cm else f"{b_cm} cm"
            choices = [f"{a} m", f"{b_cm} cm", "They are equal", "Cannot compare"]
            if a_cm == b_cm:
                correct_idx = choices.index("They are equal")
            else:
                correct_idx = choices.index(longer)
            tags = ["measurement", "comparison"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(35, 60),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Wrong conversion factor", "2": "Did not convert to same unit", "3": "Subtraction error with units"},
            "tags": tags, "topic": "ncert_g4_measurement",
            "chapter": "Ch7: Measurement",
            "hint": {"level_0": "Convert to same units first. 1 km = 1000 m, 1 kg = 1000 g.",
                    "level_1": "Convert bigger unit to smaller, then calculate.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_7"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(-0.2, 1.0), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter8_perimeter_area(qid_num):
    """Perimeter & Area — rectangles, squares, composite"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # perimeter rectangle
            l = random.randint(5, 20)
            w = random.randint(3, 15)
            correct = 2 * (l + w)
            stem = f"Find the perimeter of a rectangle with length {l} cm and breadth {w} cm."
            choices = [f"{correct} cm", f"{l * w} cm", f"{l + w} cm", f"{correct + 4} cm"]
            random.shuffle(choices)
            correct_idx = choices.index(f"{correct} cm")
            vis_svg = make_svg_shape(qid, "rectangle", [l, w], G4_DIR)
            vis_alt = f"Rectangle {l} cm × {w} cm"
            tags = ["perimeter", "rectangle"]
        elif variant == 1:  # area rectangle
            l = random.randint(4, 15)
            w = random.randint(3, 12)
            area = l * w
            stem = f"Find the area of a rectangle with length {l} m and breadth {w} m."
            correct = f"{area} sq m"
            choices = [f"{area} sq m", f"{2*(l+w)} sq m", f"{l + w} sq m", f"{area + l} sq m"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_shape(qid, "rectangle", [l, w], G4_DIR)
            vis_alt = f"Rectangle {l} m × {w} m"
            tags = ["area", "rectangle"]
        elif variant == 2:  # area square
            s = random.randint(3, 15)
            area = s * s
            stem = f"Find the area of a square with side {s} cm."
            correct = f"{area} sq cm"
            choices = [f"{area} sq cm", f"{4*s} sq cm", f"{2*s} sq cm", f"{area + s} sq cm"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_shape(qid, "square", [s], G4_DIR)
            vis_alt = f"Square with side {s} cm"
            tags = ["area", "square"]
        elif variant == 3:  # word problem
            name = pick_name()
            l = random.randint(8, 25)
            w = random.randint(5, 15)
            area = l * w
            perim = 2 * (l + w)
            ask = random.choice(["area", "perimeter"])
            if ask == "area":
                correct_val = area
                unit = "sq m"
                stem = f"{name}'s room is {l} m long and {w} m wide. What is the area of the floor?"
            else:
                correct_val = perim
                unit = "m"
                stem = f"{name} wants to put a border around a rectangular garden {l} m by {w} m. How much border is needed?"
            correct = f"{correct_val} {unit}"
            choices = [f"{correct_val} {unit}", f"{area if ask == 'perimeter' else perim} {unit}",
                      f"{correct_val + 10} {unit}", f"{l + w} {unit}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = [ask, "word_problem"]
        else:  # find missing side
            area = random.choice([24, 30, 36, 40, 48, 56])
            l = random.choice([d for d in range(2, area) if area % d == 0 and d < area // d + 5])
            w = area // l
            stem = f"A rectangle has area {area} sq cm and length {l} cm. What is the breadth?"
            correct = f"{w} cm"
            choices = [f"{w} cm", f"{w + 1} cm", f"{l} cm", f"{area - l} cm"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["area", "missing_dimension"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(35, 65),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": {"1": "Confused area and perimeter formulas", "2": "Used wrong formula", "3": "Arithmetic error"},
            "tags": tags, "topic": "ncert_g4_geometry",
            "chapter": "Ch8: Perimeter & Area",
            "hint": {"level_0": "Perimeter = sum of all sides. Area = length × breadth.",
                    "level_1": "Rectangle: P = 2(l+b), A = l×b. Square: P = 4s, A = s×s.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_8"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(-0.2, 1.0), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter9_geometry(qid_num):
    """Geometry — angles, triangles, nets"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # angle types
            angle = random.randint(10, 170)
            if angle < 90:
                correct = "Acute"
            elif angle == 90:
                correct = "Right"
            else:
                correct = "Obtuse"
            stem = f"An angle of {angle}° is called:"
            choices = ["Acute", "Right", "Obtuse", "Straight"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["geometry", "angles", "types"]
        elif variant == 1:  # triangle classification by sides
            types = [("All three sides are equal", "Equilateral"),
                    ("Two sides are equal", "Isosceles"),
                    ("No sides are equal", "Scalene")]
            desc, correct = random.choice(types)
            stem = f"A triangle where {desc.lower()} is called:"
            choices = ["Equilateral", "Isosceles", "Scalene", "Right"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["geometry", "triangles", "classification"]
        elif variant == 2:  # angle sum
            a1 = random.randint(30, 80)
            a2 = random.randint(30, 80)
            a3 = 180 - a1 - a2
            stem = f"Two angles of a triangle are {a1}° and {a2}°. What is the third angle?"
            correct = f"{a3}°"
            choices = [f"{a3}°", f"{a3 + 10}°", f"{180}°", f"{a1 + a2}°"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["geometry", "triangles", "angle_sum"]
        elif variant == 3:  # identify angles in shapes
            shape = random.choice(["rectangle", "square"])
            if shape in ["rectangle", "square"]:
                correct = "90°"
                stem = f"What is the measure of each angle in a {shape}?"
                choices = ["90°", "60°", "180°", "45°"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["geometry", "angles", "shapes"]
        else:  # nets
            shapes_3d = [("cube", "6 squares"), ("cuboid", "6 rectangles"),
                        ("cylinder", "2 circles and 1 rectangle"), ("cone", "1 circle and 1 sector")]
            shape, net = random.choice(shapes_3d)
            stem = f"The net of a {shape} is made up of:"
            correct = net
            all_nets = ["6 squares", "6 rectangles", "2 circles and 1 rectangle", "1 circle and 1 sector"]
            choices = [correct] + [n for n in all_nets if n != correct][:3]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["geometry", "nets", "3D"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium" if variant < 3 else "hard",
            "difficulty_score": random.randint(35, 65),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Confused angle types", "2": "Wrong triangle classification", "3": "Does not know angle sum property"},
            "tags": tags, "topic": "ncert_g4_geometry",
            "chapter": "Ch9: Geometry",
            "hint": {"level_0": "Acute < 90°, Right = 90°, Obtuse > 90°.",
                    "level_1": "Angles in a triangle add up to 180°.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_9"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(0.0, 1.2), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter10_patterns(qid_num):
    """Patterns & Sequences — complex patterns, algebraic thinking"""
    questions = []
    for i in range(22):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # arithmetic sequence
            start = random.randint(3, 20)
            step = random.randint(3, 12)
            seq = [start + j * step for j in range(6)]
            stem = f"Find the next number: {', '.join(str(x) for x in seq[:5])}, ?"
            correct = str(seq[5])
            choices = [str(seq[5]), str(seq[5] + step), str(seq[5] - 1), str(seq[4] + 1)]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_pattern(qid, seq[:5] + [None], G4_DIR)
            vis_alt = f"Pattern: {', '.join(str(x) for x in seq[:5])}, ?"
            tags = ["patterns", "arithmetic"]
        elif variant == 1:  # geometric pattern
            start = random.choice([2, 3])
            seq = [start * (2 ** j) for j in range(5)]
            stem = f"What comes next: {', '.join(str(x) for x in seq[:4])}, ?"
            correct = str(seq[4])
            choices = [str(seq[4]), str(seq[3] + seq[2]), str(seq[4] + 2), str(seq[3] * 3)]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_pattern(qid, seq[:4] + [None], G4_DIR)
            vis_alt = f"Doubling pattern"
            tags = ["patterns", "geometric"]
        elif variant == 2:  # find the rule
            a = random.randint(1, 5)
            b = random.randint(2, 8)
            inputs = list(range(1, 5))
            outputs = [a * x + b for x in inputs]
            stem = f"Input: {inputs}, Output: {outputs}. If input is 5, output is?"
            correct = str(a * 5 + b)
            choices = [str(a * 5 + b), str(a * 5), str(5 + b), str(outputs[-1] + 1)]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["patterns", "rule", "algebraic"]
        elif variant == 3:  # square numbers
            seq = [1, 4, 9, 16, 25, 36]
            pos = random.randint(4, 5)
            stem = f"In the pattern 1, 4, 9, 16, ..., what is the {pos+1}th number?"
            correct = str(seq[pos])
            choices = [str(seq[pos]), str(seq[pos] + 1), str(seq[pos-1] + seq[pos-2]), str(seq[pos] - 2)]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["patterns", "square_numbers"]
        else:  # triangular numbers
            seq = [1, 3, 6, 10, 15, 21, 28]
            stem = f"Find the next: 1, 3, 6, 10, 15, ?"
            correct = "21"
            choices = ["21", "20", "18", "25"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_pattern(qid, [1, 3, 6, 10, 15, None], G4_DIR)
            vis_alt = "Triangular number pattern"
            tags = ["patterns", "triangular_numbers"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "hard", "difficulty_score": random.randint(45, 75),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": {"1": "Did not identify the growing difference", "2": "Applied wrong rule", "3": "Confused arithmetic and geometric"},
            "tags": tags, "topic": "ncert_g4_patterns",
            "chapter": "Ch10: Patterns & Sequences",
            "hint": {"level_0": "Look at the differences between consecutive numbers.",
                    "level_1": "Is the pattern adding same number each time, or is the difference growing?",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_10"],
            "irt_params": {"a": round(random.uniform(1.1, 1.6), 2),
                          "b": round(random.uniform(0.2, 1.5), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter11_data(qid_num):
    """Data Handling — line graphs, average, pie chart"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # average
            nums = [random.randint(40, 100) for _ in range(4)]
            avg = sum(nums) // len(nums)
            name = pick_name()
            stem = f"{name}'s test scores are {', '.join(str(n) for n in nums)}. What is the average?"
            correct = str(avg)
            choices = [str(avg), str(avg + 2), str(max(nums)), str(sum(nums))]
            random.shuffle(choices)
            correct_idx = choices.index(str(avg))
            tags = ["data", "average"]
            vis_svg = None
            vis_alt = None
        elif variant == 1:  # bar graph reading
            days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
            temps = [random.randint(25, 40) for _ in range(5)]
            max_day = days[temps.index(max(temps))]
            stem = f"On which day was the temperature highest?"
            correct = max_day
            choices = days[:4]
            if correct not in choices:
                choices[3] = correct
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = make_svg_bar_chart(qid, days, temps, "Temperature This Week (°C)", G4_DIR)
            vis_alt = f"Bar graph of temperatures: {dict(zip(days, temps))}"
            tags = ["data", "bar_graph"]
        elif variant == 2:  # total/difference from graph
            items = ["Maths", "Science", "English", "Hindi"]
            marks = [random.randint(60, 95) for _ in range(4)]
            total = sum(marks)
            stem = f"What is the total of all marks shown in the graph?"
            correct = str(total)
            choices = [str(total), str(total + 10), str(max(marks) * 4), str(total - min(marks))]
            random.shuffle(choices)
            correct_idx = choices.index(str(total))
            vis_svg = make_svg_bar_chart(qid, items, marks, "Marks in Subjects", G4_DIR)
            vis_alt = f"Bar graph of marks"
            tags = ["data", "bar_graph", "total"]
        elif variant == 3:  # pie chart
            categories = ["Food", "Rent", "Travel", "Savings"]
            percents = [30, 35, 15, 20]
            random.shuffle(list(zip(categories, percents)))
            q_cat = random.choice(categories)
            q_pct = percents[categories.index(q_cat)]
            stem = f"In a family budget pie chart, {q_cat} is {q_pct}%. If total income is ₹{10000}, how much is spent on {q_cat}?"
            correct = f"₹{q_pct * 100}"
            choices = [f"₹{q_pct * 100}", f"₹{q_pct * 10}", f"₹{q_pct}", f"₹{q_pct * 1000}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            vis_svg = None
            vis_alt = None
            tags = ["data", "pie_chart", "percentage"]
        else:  # interpret data
            cities_data = random.sample(CITIES, 4)
            populations = [random.randint(1000, 5000) for _ in range(4)]
            diff = max(populations) - min(populations)
            stem = f"Difference between highest and lowest values in the data: {dict(zip(cities_data, populations))}"
            correct = str(diff)
            choices = [str(diff), str(diff + 100), str(sum(populations)), str(max(populations))]
            random.shuffle(choices)
            correct_idx = choices.index(str(diff))
            vis_svg = make_svg_bar_chart(qid, cities_data, populations, "Population (in thousands)", G4_DIR)
            vis_alt = "Bar graph comparing city populations"
            tags = ["data", "interpretation"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(35, 60),
            "visual_svg": vis_svg, "visual_alt": vis_alt,
            "diagnostics": {"1": "Calculation error in average", "2": "Misread graph values", "3": "Confused percentage with absolute"},
            "tags": tags, "topic": "ncert_g4_data",
            "chapter": "Ch11: Data Handling",
            "hint": {"level_0": "Average = Sum ÷ Number of items.",
                    "level_1": "Read graphs carefully. Percentage of total = (percent/100) × total.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_11"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(-0.2, 1.0), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter12_time(qid_num):
    """Time — 24-hour clock, time zones, word problems"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # 12 to 24 hour
            hour_12 = random.randint(1, 12)
            minute = random.choice([0, 15, 30, 45])
            period = random.choice(["AM", "PM"])
            if period == "AM":
                hour_24 = hour_12 if hour_12 != 12 else 0
            else:
                hour_24 = hour_12 + 12 if hour_12 != 12 else 12
            stem = f"Convert {hour_12}:{minute:02d} {period} to 24-hour format."
            correct = f"{hour_24:02d}:{minute:02d}"
            wrong1 = f"{(hour_24 + 12) % 24:02d}:{minute:02d}"
            wrong2 = f"{hour_12:02d}:{minute:02d}"
            wrong3 = f"{(hour_24 - 1) % 24:02d}:{minute:02d}"
            choices = [correct, wrong1, wrong2, wrong3]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["time", "24_hour"]
        elif variant == 1:  # 24 to 12 hour
            hour_24 = random.randint(0, 23)
            minute = random.choice([0, 15, 30, 45])
            if hour_24 == 0:
                hour_12, period = 12, "AM"
            elif hour_24 < 12:
                hour_12, period = hour_24, "AM"
            elif hour_24 == 12:
                hour_12, period = 12, "PM"
            else:
                hour_12, period = hour_24 - 12, "PM"
            stem = f"Convert {hour_24:02d}:{minute:02d} to 12-hour format."
            correct = f"{hour_12}:{minute:02d} {period}"
            wrong_period = "AM" if period == "PM" else "PM"
            choices = [correct, f"{hour_12}:{minute:02d} {wrong_period}",
                      f"{hour_24}:{minute:02d} {period}", f"{hour_12 + 1}:{minute:02d} {period}"]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["time", "12_hour"]
        elif variant == 2:  # duration
            start_h = random.randint(8, 16)
            start_m = random.choice([0, 15, 30, 45])
            dur_h = random.randint(1, 4)
            dur_m = random.choice([0, 15, 30, 45])
            end_m = start_m + dur_m
            end_h = start_h + dur_h + end_m // 60
            end_m = end_m % 60
            name = pick_name()
            stem = f"{name}'s train departs at {start_h:02d}:{start_m:02d} and the journey takes {dur_h} hr {dur_m} min. When does it arrive?"
            correct = f"{end_h:02d}:{end_m:02d}"
            choices = [correct, f"{end_h + 1:02d}:{end_m:02d}", f"{end_h:02d}:{(end_m + 15) % 60:02d}", f"{start_h + dur_h:02d}:{start_m:02d}"]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["time", "duration", "word_problem"]
        elif variant == 3:  # time difference
            h1 = random.randint(8, 12)
            m1 = random.choice([0, 15, 30])
            h2 = h1 + random.randint(2, 5)
            m2 = random.choice([0, 15, 30, 45])
            diff_total = (h2 * 60 + m2) - (h1 * 60 + m1)
            diff_h = diff_total // 60
            diff_m = diff_total % 60
            stem = f"How much time passes from {h1}:{m1:02d} to {h2}:{m2:02d}?"
            correct = f"{diff_h} hr {diff_m} min"
            choices = [correct, f"{diff_h + 1} hr {diff_m} min", f"{diff_h} hr {diff_m + 15} min", f"{h2 - h1} hr 0 min"]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["time", "difference"]
        else:  # days/weeks
            weeks = random.randint(2, 8)
            days = weeks * 7
            stem = f"How many days are there in {weeks} weeks?"
            correct = str(days)
            choices = [str(days), str(weeks * 5), str(days + 7), str(weeks + 7)]
            random.shuffle(choices)
            correct_idx = choices.index(str(days))
            tags = ["time", "weeks_days"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium", "difficulty_score": random.randint(35, 60),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "AM/PM confusion", "2": "12/24 hour conversion error", "3": "Duration calculation error"},
            "tags": tags, "topic": "ncert_g4_measurement",
            "chapter": "Ch12: Time",
            "hint": {"level_0": "24-hour: add 12 for PM times (except 12 PM stays 12).",
                    "level_1": "For duration, subtract start from end. 1 week = 7 days.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_12"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(-0.1, 1.0), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter13_money(qid_num):
    """Money — budgets, bills, discounts"""
    questions = []
    for i in range(22):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # bill calculation
            items = [("Rice 5kg", random.randint(200, 400)),
                    ("Dal 2kg", random.randint(100, 250)),
                    ("Oil 1L", random.randint(100, 200)),
                    ("Sugar 2kg", random.randint(60, 120))]
            selected = random.sample(items, 3)
            total = sum(p for _, p in selected)
            item_str = ", ".join(f"{n}: ₹{p}" for n, p in selected)
            name = pick_name()
            stem = f"{name} buys: {item_str}. What is the total bill?"
            correct = f"₹{total}"
            choices = [f"₹{total}", f"₹{total + 50}", f"₹{total - 30}", f"₹{total + 100}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["money", "bill"]
        elif variant == 1:  # discount
            price = random.choice([100, 200, 300, 400, 500, 600])
            discount_pct = random.choice([10, 20, 25, 50])
            discount_amt = price * discount_pct // 100
            final = price - discount_amt
            name = pick_name()
            stem = f"A book costs ₹{price}. There is {discount_pct}% off. What is the price after discount?"
            correct = f"₹{final}"
            choices = [f"₹{final}", f"₹{discount_amt}", f"₹{price + discount_amt}", f"₹{final + 10}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["money", "discount"]
        elif variant == 2:  # budget
            name = pick_name()
            pocket_money = random.choice([200, 300, 500, 400])
            spent_food = random.randint(50, pocket_money // 3)
            spent_books = random.randint(30, pocket_money // 3)
            saved = pocket_money - spent_food - spent_books
            stem = f"{name} gets ₹{pocket_money} pocket money. Spends ₹{spent_food} on food and ₹{spent_books} on books. How much is saved?"
            correct = f"₹{saved}"
            choices = [f"₹{saved}", f"₹{spent_food + spent_books}", f"₹{pocket_money}", f"₹{saved + 50}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["money", "budget", "savings"]
        elif variant == 3:  # profit/loss
            name = pick_name()
            cost = random.randint(50, 500)
            sell = cost + random.choice([-20, -10, 10, 20, 50, 30])
            if sell > cost:
                profit = sell - cost
                stem = f"{name} buys a toy for ₹{cost} and sells it for ₹{sell}. What is the profit?"
                correct = f"₹{profit}"
                choices = [f"₹{profit}", f"₹{sell}", f"₹{cost}", f"₹{profit + 10}"]
            else:
                loss = cost - sell
                stem = f"{name} buys a bag for ₹{cost} and sells it for ₹{sell}. What is the loss?"
                correct = f"₹{loss}"
                choices = [f"₹{loss}", f"₹{cost}", f"₹{sell}", f"₹{loss + 5}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["money", "profit_loss"]
        else:  # change making
            name = pick_name()
            total_bill = random.randint(100, 900)
            paid = random.choice([500, 1000, 2000])
            while paid < total_bill:
                paid = random.choice([500, 1000, 2000])
            change = paid - total_bill
            stem = f"{name}'s bill is ₹{total_bill}. They pay with a ₹{paid} note. What change do they receive?"
            correct = f"₹{change}"
            choices = [f"₹{change}", f"₹{change + 50}", f"₹{total_bill}", f"₹{change - 10}"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["money", "change"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium" if variant < 2 else "hard",
            "difficulty_score": random.randint(35, 65),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Arithmetic error with money", "2": "Percentage calculation wrong", "3": "Confused profit with selling price"},
            "tags": tags, "topic": "ncert_g4_arithmetic",
            "chapter": "Ch13: Money",
            "hint": {"level_0": "Discount = price × percentage ÷ 100. Profit = SP - CP.",
                    "level_1": "Savings = Income - Expenses. Change = Paid - Bill.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_13"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(0.0, 1.3), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num

def g4_chapter14_maps(qid_num):
    """Maps & Directions — scale, distance, N/S/E/W"""
    questions = []
    for i in range(21):
        qid = f"NCERT-G4-{qid_num:03d}"
        variant = i % 5

        if variant == 0:  # directions
            starts = [("North", "right", "East"), ("North", "left", "West"),
                     ("East", "right", "South"), ("East", "left", "North"),
                     ("South", "right", "West"), ("South", "left", "East"),
                     ("West", "right", "North"), ("West", "left", "South")]
            facing, turn, result = random.choice(starts)
            name = pick_name()
            stem = f"{name} is facing {facing} and turns {turn}. Which direction is {name} facing now?"
            correct = result
            choices = ["North", "South", "East", "West"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["maps", "directions"]
        elif variant == 1:  # scale
            scale_cm = random.randint(1, 5)
            scale_km = random.choice([2, 5, 10, 20])
            map_cm = random.randint(2, 10)
            actual_km = (map_cm // scale_cm) * scale_km if map_cm % scale_cm == 0 else map_cm * scale_km // scale_cm
            actual_km = map_cm * scale_km // scale_cm
            stem = f"On a map, {scale_cm} cm = {scale_km} km. If two cities are {map_cm} cm apart on the map, what is the actual distance?"
            correct = f"{actual_km} km"
            choices = [f"{actual_km} km", f"{map_cm * scale_cm} km", f"{actual_km + scale_km} km", f"{map_cm} km"]
            choices = list(dict.fromkeys(choices))[:4]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["maps", "scale"]
        elif variant == 2:  # opposite directions
            pairs = [("North", "South"), ("East", "West")]
            dir1, dir2 = random.choice(pairs)
            stem = f"What is the opposite direction of {dir1}?"
            correct = dir2
            choices = ["North", "South", "East", "West"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["maps", "directions", "opposite"]
        elif variant == 3:  # distance word problem
            name = pick_name()
            d1 = random.randint(2, 10)
            d2 = random.randint(2, 10)
            direction1 = random.choice(["North", "East"])
            direction2 = random.choice(["South", "West"])
            total = d1 + d2
            stem = f"{name} walks {d1} km {direction1} and then {d2} km {direction2}. What is the total distance walked?"
            correct = f"{total} km"
            choices = [f"{total} km", f"{abs(d1 - d2)} km", f"{d1} km", f"{total + 2} km"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["maps", "distance", "word_problem"]
        else:  # locate on grid
            name = pick_name()
            stem = f"On a map, {name}'s house is 3 blocks East and 2 blocks North of the school. If the school is at (0,0), where is the house?"
            correct = "(3, 2)"
            choices = ["(3, 2)", "(2, 3)", "(3, -2)", "(-3, 2)"]
            random.shuffle(choices)
            correct_idx = choices.index(correct)
            tags = ["maps", "coordinates"]

        q = {
            "id": qid, "stem": stem, "choices": choices, "correct_answer": correct_idx,
            "difficulty_tier": "medium" if variant < 3 else "hard",
            "difficulty_score": random.randint(35, 65),
            "visual_svg": None, "visual_alt": None,
            "diagnostics": {"1": "Left/right turn confusion", "2": "Scale multiplication error", "3": "Confused total distance with displacement"},
            "tags": tags, "topic": "ncert_g4_geometry",
            "chapter": "Ch14: Maps & Directions",
            "hint": {"level_0": "Turn right from North = East. Opposite of North = South.",
                    "level_1": "Use the scale to multiply map distance to get actual distance.",
                    "level_2": f"The answer is {choices[correct_idx]}."},
            "curriculum_tags": ["NCERT_4_14"],
            "irt_params": {"a": round(random.uniform(1.0, 1.5), 2),
                          "b": round(random.uniform(0.0, 1.3), 2), "c": 0.25}
        }
        questions.append(q)
        qid_num += 1
    return questions, qid_num


# ============================================================
# MAIN GENERATION
# ============================================================

def generate_grade3():
    """Generate 300 questions for Grade 3."""
    all_questions = []
    qid = 1

    generators = [
        g3_chapter1_numbers, g3_chapter2_add_sub, g3_chapter3_mult,
        g3_chapter4_division, g3_chapter5_fractions, g3_chapter6_money,
        g3_chapter7_measurement, g3_chapter8_time, g3_chapter9_geometry,
        g3_chapter10_patterns, g3_chapter11_data, g3_chapter12_area,
        g3_chapter13_weight_capacity, g3_chapter14_symmetry
    ]

    for gen in generators:
        questions, qid = gen(qid)
        all_questions.extend(questions)

    # Trim or pad to exactly 300
    all_questions = all_questions[:300]

    # Ensure ~50% have visuals by adding visuals to questions that don't have them
    visual_count = sum(1 for q in all_questions if q["visual_svg"] is not None)
    target_visuals = 150

    for q in all_questions:
        if visual_count >= target_visuals:
            break
        if q["visual_svg"] is None:
            tags_str = str(q.get("tags", []))
            if "arithmetic" in q.get("topic", "") or "number" in tags_str:
                start = random.randint(0, 50) * 100
                end = start + 1000
                marked = random.randint(start, end)
                q["visual_svg"] = make_svg_number_line(q["id"], start, end, marked, G3_DIR)
                q["visual_alt"] = f"Number line from {start} to {end}"
                visual_count += 1
            elif "measurement" in q.get("topic", "") or "money" in tags_str:
                labels = ["A", "B", "C", "D"]
                vals = [random.randint(5, 30) for _ in range(4)]
                q["visual_svg"] = make_svg_bar_chart(q["id"], labels, vals, "Data", G3_DIR)
                q["visual_alt"] = "Bar chart"
                visual_count += 1
            elif random.random() < 0.6:
                start = random.randint(0, 50) * 100
                end = start + 1000
                marked = random.randint(start, end)
                q["visual_svg"] = make_svg_number_line(q["id"], start, end, marked, G3_DIR)
                q["visual_alt"] = f"Number line from {start} to {end}"
                visual_count += 1

    output = {
        "topic_id": "ncert_g3",
        "topic_name": "NCERT Grade 3 Mathematics",
        "version": "2.0",
        "curriculum": "NCERT",
        "grade": 3,
        "total_questions": len(all_questions),
        "questions": all_questions
    }

    output_path = os.path.join(G3_DIR, "ncert_g3_questions.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    return output

def generate_grade4():
    """Generate 300 questions for Grade 4."""
    all_questions = []
    qid = 1

    generators = [
        g4_chapter1_numbers, g4_chapter2_multiplication, g4_chapter3_division,
        g4_chapter4_factors, g4_chapter5_fractions, g4_chapter6_decimals,
        g4_chapter7_measurement, g4_chapter8_perimeter_area, g4_chapter9_geometry,
        g4_chapter10_patterns, g4_chapter11_data, g4_chapter12_time,
        g4_chapter13_money, g4_chapter14_maps
    ]

    for gen in generators:
        questions, qid = gen(qid)
        all_questions.extend(questions)

    # Pad to 300 if short by adding extra from first few chapters
    while len(all_questions) < 300:
        extra_q, qid = g4_chapter1_numbers(qid)
        all_questions.extend(extra_q[:300 - len(all_questions)])

    all_questions = all_questions[:300]

    # Ensure ~50% have visuals - be aggressive
    visual_count = sum(1 for q in all_questions if q["visual_svg"] is not None)
    target_visuals = 150

    for q in all_questions:
        if visual_count >= target_visuals:
            break
        if q["visual_svg"] is None:
            tags_str = str(q.get("tags", []))
            if "number" in tags_str or "arithmetic" in q.get("topic", ""):
                start = random.randint(0, 500) * 100
                end = start + 5000
                marked = random.randint(start, end)
                q["visual_svg"] = make_svg_number_line(q["id"], start, end, marked, G4_DIR)
                q["visual_alt"] = f"Number line from {start} to {end}"
                visual_count += 1
            elif "pattern" in tags_str:
                q["visual_svg"] = make_svg_pattern(q["id"], [1, 2, 3, None], G4_DIR)
                q["visual_alt"] = "Pattern visualization"
                visual_count += 1
            elif "measurement" in q.get("topic", "") or "money" in tags_str:
                labels = ["Item A", "Item B", "Item C", "Item D"]
                vals = [random.randint(10, 50) for _ in range(4)]
                q["visual_svg"] = make_svg_bar_chart(q["id"], labels, vals, "Data Chart", G4_DIR)
                q["visual_alt"] = "Bar chart illustration"
                visual_count += 1
            elif "geometry" in q.get("topic", ""):
                s = random.randint(3, 10)
                q["visual_svg"] = make_svg_shape(q["id"], "square", [s], G4_DIR)
                q["visual_alt"] = f"Shape illustration"
                visual_count += 1
            elif random.random() < 0.7:
                start = random.randint(0, 200) * 100
                end = start + 3000
                marked = random.randint(start, end)
                q["visual_svg"] = make_svg_number_line(q["id"], start, end, marked, G4_DIR)
                q["visual_alt"] = f"Number line from {start} to {end}"
                visual_count += 1

    output = {
        "topic_id": "ncert_g4",
        "topic_name": "NCERT Grade 4 Mathematics",
        "version": "2.0",
        "curriculum": "NCERT",
        "grade": 4,
        "total_questions": len(all_questions),
        "questions": all_questions
    }

    output_path = os.path.join(G4_DIR, "ncert_g4_questions.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    return output


if __name__ == "__main__":
    print("=" * 60)
    print("NCERT Grade 3 & Grade 4 Question Generator")
    print("=" * 60)

    print("\nGenerating Grade 3 questions...")
    g3 = generate_grade3()
    print(f"  Total questions: {g3['total_questions']}")
    g3_visuals = sum(1 for q in g3['questions'] if q['visual_svg'] is not None)
    print(f"  Questions with visuals: {g3_visuals} ({g3_visuals*100//g3['total_questions']}%)")

    # Count by chapter
    g3_chapters = {}
    for q in g3['questions']:
        ch = q['chapter']
        g3_chapters[ch] = g3_chapters.get(ch, 0) + 1
    print("  Questions per chapter:")
    for ch, count in sorted(g3_chapters.items()):
        print(f"    {ch}: {count}")

    # Difficulty distribution
    g3_diff = {"easy": 0, "medium": 0, "hard": 0}
    for q in g3['questions']:
        g3_diff[q['difficulty_tier']] += 1
    print(f"  Difficulty: Easy={g3_diff['easy']}, Medium={g3_diff['medium']}, Hard={g3_diff['hard']}")

    print("\nGenerating Grade 4 questions...")
    g4 = generate_grade4()
    print(f"  Total questions: {g4['total_questions']}")
    g4_visuals = sum(1 for q in g4['questions'] if q['visual_svg'] is not None)
    print(f"  Questions with visuals: {g4_visuals} ({g4_visuals*100//g4['total_questions']}%)")

    g4_chapters = {}
    for q in g4['questions']:
        ch = q['chapter']
        g4_chapters[ch] = g4_chapters.get(ch, 0) + 1
    print("  Questions per chapter:")
    for ch, count in sorted(g4_chapters.items()):
        print(f"    {ch}: {count}")

    g4_diff = {"easy": 0, "medium": 0, "hard": 0}
    for q in g4['questions']:
        g4_diff[q['difficulty_tier']] += 1
    print(f"  Difficulty: Easy={g4_diff['easy']}, Medium={g4_diff['medium']}, Hard={g4_diff['hard']}")

    # IRT param ranges
    g3_b = [q['irt_params']['b'] for q in g3['questions']]
    g4_b = [q['irt_params']['b'] for q in g4['questions']]
    print(f"\n  G3 IRT b range: [{min(g3_b):.2f}, {max(g3_b):.2f}]")
    print(f"  G4 IRT b range: [{min(g4_b):.2f}, {max(g4_b):.2f}]")

    # Sample questions
    print("\n" + "=" * 60)
    print("SAMPLE QUESTIONS")
    print("=" * 60)

    print("\n--- Grade 3 Samples ---")
    for q in random.sample(g3['questions'], 5):
        print(f"\n  [{q['id']}] {q['chapter']}")
        print(f"  Q: {q['stem']}")
        print(f"  Choices: {q['choices']}")
        print(f"  Answer: {q['choices'][q['correct_answer']]}")
        print(f"  Visual: {'Yes' if q['visual_svg'] else 'No'}")

    print("\n--- Grade 4 Samples ---")
    for q in random.sample(g4['questions'], 5):
        print(f"\n  [{q['id']}] {q['chapter']}")
        print(f"  Q: {q['stem']}")
        print(f"  Choices: {q['choices']}")
        print(f"  Answer: {q['choices'][q['correct_answer']]}")
        print(f"  Visual: {'Yes' if q['visual_svg'] else 'No'}")

    # Count SVG files
    g3_svg_count = len([f for f in os.listdir(os.path.join(G3_DIR, "visuals")) if f.endswith('.svg')])
    g4_svg_count = len([f for f in os.listdir(os.path.join(G4_DIR, "visuals")) if f.endswith('.svg')])
    print(f"\n  SVG files generated: G3={g3_svg_count}, G4={g4_svg_count}")
    print(f"\nOutput files:")
    print(f"  {os.path.join(G3_DIR, 'ncert_g3_questions.json')}")
    print(f"  {os.path.join(G4_DIR, 'ncert_g4_questions.json')}")
    print("\nDone!")
