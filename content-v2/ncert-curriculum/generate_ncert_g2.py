#!/usr/bin/env python3
"""
Generate 300 NCERT-aligned Grade 2 Math questions for Kiwimath.
Covers all 11 chapters of NCERT Class 2 "Math Magic" / NEP 2020.
Produces questions.json + SVG visuals in grade2/ directory.
"""

import json
import os
import random
import math

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grade2")
VISUALS_DIR = os.path.join(OUTPUT_DIR, "visuals")
os.makedirs(VISUALS_DIR, exist_ok=True)

# Indian names and contexts
NAMES = ["Ria", "Arjun", "Priya", "Kavya", "Ravi", "Ananya", "Rohan", "Meera", "Aarav", "Diya",
         "Vivaan", "Ishaan", "Saanvi", "Anika", "Vihaan", "Aditi", "Krishna", "Nisha", "Dev", "Tara"]

OBJECTS_FOOD = ["mangoes", "bananas", "apples", "guavas", "oranges", "laddoos", "jalebis",
                "samosas", "rotis", "dosas", "idlis", "chapatis", "parathas", "pakoras"]
OBJECTS_SCHOOL = ["pencils", "crayons", "erasers", "notebooks", "stickers", "books", "chalk pieces"]
OBJECTS_PLAY = ["marbles", "kites", "balloons", "toy cars", "shells", "beads", "bangles"]
OBJECTS_MISC = ["flowers", "diyas", "rangoli colours", "stamps", "coins", "buttons", "ribbons"]

CONTEXTS = ["at the school fair", "during Diwali", "at the mango market", "in the playground",
            "at a birthday party", "during Holi", "at the village mela", "in the kitchen",
            "at the chai stall", "during Pongal", "at the bookshop", "on the school bus",
            "at the temple", "during Onam", "at Grandma's house", "in the garden",
            "at the auto stand", "during Eid", "at the sweet shop", "in art class"]

COLORS_SVG = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD",
              "#FF8C42", "#98D8C8", "#F7DC6F", "#85C1E9", "#F1948A", "#82E0AA"]


def irt_params(difficulty):
    """Generate IRT parameters based on difficulty tier."""
    if difficulty == "easy":
        b = round(random.uniform(-2.0, -1.0), 2)
        score = random.randint(10, 35)
    elif difficulty == "medium":
        b = round(random.uniform(-1.0, 0.0), 2)
        score = random.randint(36, 65)
    else:
        b = round(random.uniform(0.0, 1.0), 2)
        score = random.randint(66, 95)
    return {"a": round(random.uniform(0.8, 1.5), 2), "b": b, "c": 0.25}, score


def make_id(n):
    return f"NCERT-G2-{n:03d}"


def svg_header():
    return '<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">\n'


def svg_footer():
    return '</svg>'


# ============================================================
# CHAPTER 1: Numbers up to 100
# ============================================================
def gen_ch1_questions(start_id):
    questions = []
    qid = start_id

    # --- Place value questions ---
    for i in range(5):
        num = random.randint(20, 99)
        tens = num // 10
        ones = num % 10
        name = random.choice(NAMES)
        diffs = ["easy", "easy", "medium", "medium", "hard"]
        diff = diffs[i]
        irt, score = irt_params(diff)

        if i < 2:
            stem = f"{name} sees the number {num} on a bus. How many tens are in {num}?"
            choices = [str(tens), str(ones), str(tens + 1), str(num)]
            correct = 0
            diag = {"1": f"That's the ones digit, not tens.", "2": f"Count the tens digit carefully.", "3": f"That's the whole number, not just tens."}
        elif i < 4:
            stem = f"What is the expanded form of {num}?"
            choices = [f"{tens*10} + {ones}", f"{tens} + {ones}", f"{num} + 0", f"{ones*10} + {tens}"]
            correct = 0
            diag = {"1": "Remember tens place means groups of 10.", "2": "Adding 0 doesn't show place value.", "3": "You swapped tens and ones."}
        else:
            num2 = random.randint(20, 99)
            while num2 == num:
                num2 = random.randint(20, 99)
            stem = f"Which number is greater: {num} or {num2}?"
            bigger = max(num, num2)
            smaller = min(num, num2)
            choices = [str(bigger), str(smaller), str(bigger + smaller), "They are equal"]
            correct = 0
            diag = {"1": f"{smaller} has fewer tens than {bigger}.", "2": "That's their sum, not a comparison.", "3": f"They are different numbers."}

        svg_file = None
        svg_alt = None
        if i < 3:
            svg_file = f"{make_id(qid)}.svg"
            svg_alt = f"Base-10 blocks showing {num}: {tens} tens rods and {ones} unit cubes"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#FFF9E6" rx="5"/>\n'
            svg += f'  <text x="100" y="15" text-anchor="middle" font-size="10" fill="#333">Number: {num}</text>\n'
            # Draw tens rods
            for t in range(tens):
                x = 10 + t * 18
                svg += f'  <rect x="{x}" y="22" width="12" height="60" fill="#45B7D1" rx="2" stroke="#333" stroke-width="0.5"/>\n'
            # Draw ones cubes
            for o in range(ones):
                x = 10 + o * 14
                svg += f'  <rect x="{x}" y="90" width="10" height="10" fill="#FF6B6B" rx="1" stroke="#333" stroke-width="0.5"/>\n'
            svg += f'  <text x="100" y="115" text-anchor="middle" font-size="8" fill="#666">Tens (blue) | Ones (red)</text>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": diff,
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": diag,
            "tags": ["place_value", "numbers_to_100"],
            "topic": "ncert_g2_numbers",
            "chapter": "Ch1: Numbers up to 100",
            "hint": {
                "level_0": "Think about groups of ten and leftover ones.",
                "level_1": "The tens digit tells how many groups of 10.",
                "level_2": f"In {num}, the tens digit is {tens} (meaning {tens*10}) and ones digit is {ones}."
            },
            "curriculum_tags": ["NCERT_2_1"],
            "irt_params": irt
        })
        qid += 1

    # --- Ordering numbers ---
    for i in range(5):
        nums = random.sample(range(10, 99), 4)
        sorted_nums = sorted(nums)
        name = random.choice(NAMES)
        context = random.choice(["houses on a street", "pages in a book", "seats in an autorickshaw queue", "ticket numbers at the mela"])
        diff = ["easy", "medium", "medium", "hard", "hard"][i]
        irt, score = irt_params(diff)

        if i % 2 == 0:
            stem = f"Arrange these {context} numbers from smallest to largest: {nums[0]}, {nums[1]}, {nums[2]}, {nums[3]}"
            correct_str = ", ".join(str(x) for x in sorted_nums)
            wrong1 = ", ".join(str(x) for x in sorted(nums, reverse=True))
            wrong2 = ", ".join(str(x) for x in [nums[1], nums[0], nums[2], nums[3]])
            wrong3 = ", ".join(str(x) for x in [nums[2], nums[3], nums[0], nums[1]])
        else:
            stem = f"Arrange from largest to smallest: {nums[0]}, {nums[1]}, {nums[2]}, {nums[3]}"
            sorted_desc = sorted(nums, reverse=True)
            correct_str = ", ".join(str(x) for x in sorted_desc)
            wrong1 = ", ".join(str(x) for x in sorted_nums)
            wrong2 = ", ".join(str(x) for x in [nums[2], nums[0], nums[3], nums[1]])
            wrong3 = ", ".join(str(x) for x in [nums[1], nums[3], nums[0], nums[2]])

        choices = [correct_str, wrong1, wrong2, wrong3]
        random.shuffle(choices)
        correct = choices.index(correct_str)

        diag = {"1": "Compare tens digits first, then ones.", "2": "Check the order direction — smallest or largest first?", "3": "Look at each tens digit carefully."}

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": diff,
            "difficulty_score": score,
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": diag,
            "tags": ["ordering", "numbers_to_100"],
            "topic": "ncert_g2_numbers",
            "chapter": "Ch1: Numbers up to 100",
            "hint": {
                "level_0": "Compare tens digits first.",
                "level_1": "If tens are the same, look at the ones digit.",
                "level_2": f"Start by finding the smallest/largest tens digit among the numbers."
            },
            "curriculum_tags": ["NCERT_2_1"],
            "irt_params": irt
        })
        qid += 1

    # --- Skip counting ---
    for i in range(5):
        skip = random.choice([2, 5, 10])
        start = random.randint(1, 10) * skip
        seq = [start + skip * j for j in range(5)]
        blank_pos = random.randint(1, 3)
        display = [str(x) if j != blank_pos else "___" for j, x in enumerate(seq)]
        answer = seq[blank_pos]
        name = random.choice(NAMES)
        diff = ["easy", "easy", "medium", "medium", "hard"][i]
        irt, score = irt_params(diff)

        stem = f"{name} counts by {skip}s: {', '.join(display)}. What is the missing number?"
        wrong1 = answer + skip
        wrong2 = answer - 1
        wrong3 = answer + 1
        choices = [str(answer), str(wrong1), str(wrong2), str(wrong3)]
        random.shuffle(choices)
        correct = choices.index(str(answer))

        svg_file = f"{make_id(qid)}.svg"
        svg_alt = f"Number line showing skip counting by {skip}s with a gap"
        svg = svg_header()
        svg += f'  <rect width="200" height="120" fill="#F0FFF0" rx="5"/>\n'
        svg += f'  <line x1="10" y1="60" x2="190" y2="60" stroke="#333" stroke-width="1.5"/>\n'
        for j, val in enumerate(seq):
            x = 20 + j * 40
            color = "#FF6B6B" if j == blank_pos else "#45B7D1"
            svg += f'  <circle cx="{x}" cy="60" r="12" fill="{color}" stroke="#333" stroke-width="0.5"/>\n'
            label = "?" if j == blank_pos else str(val)
            svg += f'  <text x="{x}" y="64" text-anchor="middle" font-size="9" fill="white" font-weight="bold">{label}</text>\n'
        svg += f'  <text x="100" y="100" text-anchor="middle" font-size="9" fill="#666">Skip counting by {skip}s</text>\n'
        svg += svg_footer()
        with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
            f.write(svg)

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": diff,
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": {"1": f"Add {skip} to the number before the blank.", "2": "Don't just add 1, add the skip amount.", "3": f"Each jump is +{skip}, not +1."},
            "tags": ["skip_counting", "numbers_to_100"],
            "topic": "ncert_g2_numbers",
            "chapter": "Ch1: Numbers up to 100",
            "hint": {
                "level_0": f"You are counting by {skip}s. What comes next?",
                "level_1": f"Add {skip} to the number before the blank.",
                "level_2": f"The number before the blank is {seq[blank_pos-1]}. Add {skip} to get {answer}."
            },
            "curriculum_tags": ["NCERT_2_1"],
            "irt_params": irt
        })
        qid += 1

    # --- Number names / before-after ---
    for i in range(5):
        num = random.randint(11, 98)
        diff = ["easy", "easy", "medium", "hard", "hard"][i]
        irt, score = irt_params(diff)
        name = random.choice(NAMES)

        if i < 2:
            stem = f"What number comes just after {num}?"
            answer = num + 1
            choices = [str(answer), str(num - 1), str(num + 2), str(num + 10)]
        elif i < 4:
            stem = f"What number comes just before {num}?"
            answer = num - 1
            choices = [str(answer), str(num + 1), str(num - 2), str(num - 10)]
        else:
            stem = f"What number is between {num} and {num + 2}?"
            answer = num + 1
            choices = [str(answer), str(num), str(num + 2), str(num + 3)]

        random.shuffle(choices)
        correct = choices.index(str(answer))

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": diff,
            "difficulty_score": score,
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": {"1": "Think about the number line.", "2": "'Before' means one less, 'after' means one more.", "3": "Between means the number in the middle."},
            "tags": ["number_sequence", "numbers_to_100"],
            "topic": "ncert_g2_numbers",
            "chapter": "Ch1: Numbers up to 100",
            "hint": {
                "level_0": "Use a number line in your head.",
                "level_1": "After means +1, before means -1.",
                "level_2": f"Count: ...{num-1}, {num}, {num+1}, {num+2}..."
            },
            "curriculum_tags": ["NCERT_2_1"],
            "irt_params": irt
        })
        qid += 1

    # --- Odd/Even and tens/ones word problems ---
    for i in range(10):
        diff = ["easy", "medium", "medium", "hard", "easy", "medium", "hard", "easy", "medium", "hard"][i]
        irt, score = irt_params(diff)
        name = random.choice(NAMES)

        if i < 3:
            num = random.randint(12, 88)
            tens = num // 10
            ones = num % 10
            obj = random.choice(OBJECTS_FOOD)
            stem = f"{name} has {num} {obj}. She puts them in bags of 10. How many full bags and how many left over?"
            answer = f"{tens} bags and {ones} left over"
            wrong1 = f"{ones} bags and {tens} left over"
            wrong2 = f"{tens+1} bags and 0 left over"
            wrong3 = f"{tens-1} bags and {ones+10} left over"
            choices = [answer, wrong1, wrong2, wrong3]
            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Tens digit = full bags, ones digit = leftover.", "2": "You can't have more than 9 left over.", "3": "Tens and ones are swapped."}
            tags = ["place_value", "word_problem"]
        else:
            # Comparison word problem
            n1 = random.randint(20, 90)
            n2 = random.randint(20, 90)
            while n1 == n2:
                n2 = random.randint(20, 90)
            obj = random.choice(OBJECTS_SCHOOL)
            name2 = random.choice([n for n in NAMES if n != name])
            stem = f"{name} has {n1} {obj} and {name2} has {n2} {obj}. Who has more?"
            winner = name if n1 > n2 else name2
            choices = [winner, name if winner == name2 else name2, "Both have the same", f"Cannot tell"]
            correct = 0
            diag = {"1": "Compare the two numbers carefully.", "2": "They are different amounts.", "3": "You can compare by looking at tens first."}
            tags = ["comparison", "word_problem"]

        svg_file = None
        svg_alt = None
        if i in [0, 1, 4]:
            svg_file = f"{make_id(qid)}.svg"
            svg_alt = f"Visual comparison or grouping illustration"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#FFF0F5" rx="5"/>\n'
            svg += f'  <text x="100" y="15" text-anchor="middle" font-size="9" fill="#333">Grouping into tens</text>\n'
            if i < 3:
                for t in range(min(tens, 8)):
                    x = 12 + (t % 4) * 48
                    y = 25 + (t // 4) * 40
                    svg += f'  <rect x="{x}" y="{y}" width="40" height="30" fill="#96CEB4" rx="3" stroke="#333" stroke-width="0.5"/>\n'
                    svg += f'  <text x="{x+20}" y="{y+18}" text-anchor="middle" font-size="8" fill="#333">10</text>\n'
                if ones > 0:
                    svg += f'  <text x="100" y="110" text-anchor="middle" font-size="9" fill="#FF6B6B">+ {ones} extra</text>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": diff,
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": diag,
            "tags": tags,
            "topic": "ncert_g2_numbers",
            "chapter": "Ch1: Numbers up to 100",
            "hint": {
                "level_0": "Break the number into tens and ones.",
                "level_1": "How many groups of 10 can you make?",
                "level_2": "Divide by 10: quotient = bags, remainder = leftovers."
            },
            "curriculum_tags": ["NCERT_2_1"],
            "irt_params": irt
        })
        qid += 1

    return questions, qid


# ============================================================
# CHAPTER 2: Addition with carry
# ============================================================
def gen_ch2_questions(start_id):
    questions = []
    qid = start_id

    addition_contexts = [
        ("{name} collected {a} shells on Monday and {b} shells on Tuesday. How many shells in all?", "shells"),
        ("{name} has {a} stickers and gets {b} more at the school fair. How many stickers now?", "stickers"),
        ("There are {a} students in Class 2A and {b} in Class 2B. How many students altogether?", "students"),
        ("{name} scored {a} runs in the first match and {b} runs in the second. Total runs?", "runs"),
        ("An autorickshaw carried {a} passengers in the morning and {b} in the evening. Total passengers?", "passengers"),
        ("{name} made {a} rotis for lunch and {b} rotis for dinner. How many rotis in total?", "rotis"),
        ("{name} planted {a} marigold seeds and {b} sunflower seeds. How many seeds total?", "seeds"),
        ("A train had {a} passengers. At the next station, {b} more got on. How many passengers now?", "passengers"),
        ("{name} read {a} pages yesterday and {b} pages today. How many pages read?", "pages"),
        ("{name} has {a} red bangles and {b} green bangles. How many bangles altogether?", "bangles"),
    ]

    for i in range(27):
        diff = ["easy", "easy", "easy", "easy", "easy", "easy", "easy", "easy", "easy",
                "medium", "medium", "medium", "medium", "medium", "medium", "medium", "medium", "medium",
                "hard", "hard", "hard", "hard", "hard", "hard", "hard", "hard", "hard"][i]
        irt, score = irt_params(diff)
        name = random.choice(NAMES)

        if diff == "easy":
            a = random.randint(10, 40)
            b = random.randint(5, 20)
            # No carry for easy
            for _ in range(100):
                if (a % 10 + b % 10) < 10:
                    break
                a = random.randint(10, 40)
                b = random.randint(5, 20)
        elif diff == "medium":
            a = random.randint(20, 50)
            b = random.randint(15, 40)
            # Ensure carry
            for _ in range(100):
                if (a % 10 + b % 10) >= 10 and a + b <= 99:
                    break
                a = random.randint(20, 50)
                b = random.randint(15, 40)
        else:
            a = random.randint(35, 55)
            b = random.randint(25, 40)
            for _ in range(100):
                if a + b <= 99 and (a % 10 + b % 10) >= 10:
                    break
                a = random.randint(35, 55)
                b = random.randint(25, 40)

        answer = a + b
        template, obj = random.choice(addition_contexts)
        stem = template.format(name=name, a=a, b=b)

        # Generate wrong answers
        wrong1 = answer + 10  # forgot to carry
        wrong2 = answer - 10  # subtracted carry
        wrong3 = abs(a - b)   # subtracted instead
        wrongs = list(set([wrong1, wrong2, wrong3]) - {answer})
        while len(wrongs) < 3:
            wrongs.append(answer + random.choice([-1, 1, 2, -2]))
        wrongs = [w for w in wrongs if w != answer][:3]

        choices = [str(answer)] + [str(w) for w in wrongs[:3]]
        random.shuffle(choices)
        correct = choices.index(str(answer))

        svg_file = None
        svg_alt = None
        if i % 3 != 2:  # ~66% get SVG
            svg_file = f"{make_id(qid)}.svg"
            svg_alt = f"Addition: {a} + {b} shown with place value columns"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#F0F8FF" rx="5"/>\n'
            svg += f'  <text x="100" y="15" text-anchor="middle" font-size="10" fill="#333" font-weight="bold">Add</text>\n'
            # Column addition
            svg += f'  <text x="130" y="40" text-anchor="end" font-size="14" fill="#45B7D1">{a}</text>\n'
            svg += f'  <text x="90" y="60" text-anchor="end" font-size="14" fill="#333">+</text>\n'
            svg += f'  <text x="130" y="60" text-anchor="end" font-size="14" fill="#FF6B6B">{b}</text>\n'
            svg += f'  <line x1="85" y1="67" x2="135" y2="67" stroke="#333" stroke-width="1.5"/>\n'
            svg += f'  <text x="130" y="85" text-anchor="end" font-size="14" fill="#96CEB4">?</text>\n'
            # Place value labels
            svg += f'  <text x="115" y="105" text-anchor="middle" font-size="7" fill="#999">T | O</text>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": diff,
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": {
                "1": "Did you forget to carry the 1 to the tens place?" if diff != "easy" else "Add the ones first, then the tens.",
                "2": "You may have subtracted instead of adding.",
                "3": "Check your ones column addition carefully."
            },
            "tags": ["addition", "carry" if diff != "easy" else "no_carry", "word_problem"],
            "topic": "ncert_g2_addition",
            "chapter": "Ch2: Addition with carry",
            "hint": {
                "level_0": "Add ones first, then tens. Carry if ones sum is 10 or more.",
                "level_1": f"Ones: {a%10} + {b%10} = {a%10+b%10}. If ≥10, carry 1 to tens.",
                "level_2": f"Ones: {a%10}+{b%10}={a%10+b%10}. Tens: {a//10}+{b//10}{'+1' if (a%10+b%10)>=10 else ''}={(a//10+b//10+ (1 if (a%10+b%10)>=10 else 0))}. Answer: {answer}."
            },
            "curriculum_tags": ["NCERT_2_2"],
            "irt_params": irt
        })
        qid += 1

    return questions, qid


# ============================================================
# CHAPTER 3: Subtraction with borrow
# ============================================================
def gen_ch3_questions(start_id):
    questions = []
    qid = start_id

    sub_contexts = [
        ("{name} had {a} {obj}. She gave {b} to her friend. How many are left?", "gave away"),
        ("A basket had {a} {obj}. {b} were eaten. How many remain?", "eaten"),
        ("{name} had {a} {obj}. {b} fell and broke. How many are left?", "broke"),
        ("There were {a} {obj} on the tree. {b} were plucked. How many still on the tree?", "plucked"),
        ("{name} had ₹{a}. He spent ₹{b} on a toy. How much money is left?", "spent"),
        ("A bus had {a} passengers. {b} got off at the market stop. How many are still on the bus?", "got off"),
        ("{name} made {a} paper boats. {b} sank in the pond. How many are floating?", "sank"),
        ("{name} had {a} balloons. {b} popped during Holi. How many are left?", "popped"),
    ]

    for i in range(27):
        diff = ["easy"]*9 + ["medium"]*9 + ["hard"]*9
        d = diff[i]
        irt, score = irt_params(d)
        name = random.choice(NAMES)
        obj = random.choice(OBJECTS_FOOD + OBJECTS_PLAY)

        if d == "easy":
            a = random.randint(25, 50)
            b = random.randint(5, 19)
            for _ in range(100):
                if (a % 10) >= (b % 10) and a > b:
                    break
                a = random.randint(25, 50)
                b = random.randint(5, 19)
        elif d == "medium":
            a = random.randint(30, 70)
            b = random.randint(10, 30)
            for _ in range(100):
                if (a % 10) < (b % 10) and a > b:
                    break
                a = random.randint(30, 70)
                b = random.randint(10, 30)
        else:
            a = random.randint(50, 90)
            b = random.randint(20, 45)
            for _ in range(100):
                if (a % 10) < (b % 10) and a > b:
                    break
                a = random.randint(50, 90)
                b = random.randint(20, 45)

        answer = a - b
        template, action = random.choice(sub_contexts)
        stem = template.format(name=name, a=a, b=b, obj=obj)

        wrong1 = a + b  # added instead
        wrong2 = answer + 10  # forgot borrow
        wrong3 = answer - 1
        wrongs = list(set([wrong1, wrong2, wrong3]) - {answer})
        while len(wrongs) < 3:
            wrongs.append(answer + random.choice([2, -2, 5]))
        wrongs = [w for w in wrongs if w != answer and w > 0][:3]
        while len(wrongs) < 3:
            wrongs.append(answer + random.randint(1, 5))

        choices = [str(answer)] + [str(w) for w in wrongs[:3]]
        random.shuffle(choices)
        correct = choices.index(str(answer))

        svg_file = None
        svg_alt = None
        if i % 3 != 2:
            svg_file = f"{make_id(qid)}.svg"
            svg_alt = f"Subtraction: {a} - {b} with column method"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#FFF5EE" rx="5"/>\n'
            svg += f'  <text x="100" y="15" text-anchor="middle" font-size="10" fill="#333" font-weight="bold">Subtract</text>\n'
            svg += f'  <text x="130" y="40" text-anchor="end" font-size="14" fill="#45B7D1">{a}</text>\n'
            svg += f'  <text x="90" y="60" text-anchor="end" font-size="14" fill="#333">−</text>\n'
            svg += f'  <text x="130" y="60" text-anchor="end" font-size="14" fill="#FF6B6B">{b}</text>\n'
            svg += f'  <line x1="85" y1="67" x2="135" y2="67" stroke="#333" stroke-width="1.5"/>\n'
            svg += f'  <text x="130" y="85" text-anchor="end" font-size="14" fill="#96CEB4">?</text>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": d,
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": {
                "1": "You added instead of subtracting." if wrong1 in [int(c) for c in choices if c.isdigit()] else "Check your ones column.",
                "2": "Remember to borrow from tens if ones digit is too small." if d != "easy" else "Subtract ones first, then tens.",
                "3": "Recheck your calculation step by step."
            },
            "tags": ["subtraction", "borrow" if d != "easy" else "no_borrow", "word_problem"],
            "topic": "ncert_g2_subtraction",
            "chapter": "Ch3: Subtraction with borrow",
            "hint": {
                "level_0": "Subtract ones first. If you can't, borrow from tens.",
                "level_1": f"Can you take {b%10} from {a%10}? If not, borrow 10 from the tens place.",
                "level_2": f"{a} - {b}: Ones: {a%10 if a%10>=b%10 else a%10+10}-{b%10}={(a%10 if a%10>=b%10 else a%10+10)-b%10}. Tens: {a//10 if a%10>=b%10 else a//10-1}-{b//10}={answer//10}. Answer: {answer}."
            },
            "curriculum_tags": ["NCERT_2_3"],
            "irt_params": irt
        })
        qid += 1

    return questions, qid


# ============================================================
# CHAPTER 4: Numbers up to 999
# ============================================================
def gen_ch4_questions(start_id):
    questions = []
    qid = start_id

    for i in range(27):
        diff = ["easy"]*9 + ["medium"]*9 + ["hard"]*9
        d = diff[i]
        irt, score = irt_params(d)
        name = random.choice(NAMES)

        if i < 5:
            # Place value of 3-digit numbers
            num = random.randint(100, 999)
            h, t, o = num // 100, (num // 10) % 10, num % 10
            if i < 2:
                stem = f"In the number {num}, what is the value of the digit {h}?"
                answer = h * 100
                choices = [str(answer), str(h), str(h*10), str(num)]
            elif i < 4:
                stem = f"What is the expanded form of {num}?"
                answer = f"{h*100} + {t*10} + {o}"
                choices = [answer, f"{h} + {t} + {o}", f"{o*100} + {t*10} + {h}", f"{h*100} + {t} + {o*10}"]
            else:
                stem = f"Which digit is in the tens place of {num}?"
                answer = str(t)
                choices = [str(t), str(h), str(o), str(t+h)]

            random.shuffle(choices)
            correct = choices.index(answer if isinstance(answer, str) else str(answer))
            diag = {"1": "Hundreds place = leftmost digit x 100.", "2": "Tens is the middle digit.", "3": "Don't confuse place with face value."}
            tags = ["place_value_3digit", "numbers_to_999"]

        elif i < 12:
            # Skip counting by 10 and 100
            skip = random.choice([10, 100])
            start = random.randint(100, 500)
            seq = [start + skip * j for j in range(5)]
            blank_pos = random.randint(1, 3)
            display = [str(x) if j != blank_pos else "___" for j, x in enumerate(seq)]
            answer = seq[blank_pos]
            stem = f"Count by {skip}s: {', '.join(display)}. What is the missing number?"
            choices = [str(answer), str(answer + skip), str(answer - 1), str(answer + 1)]
            random.shuffle(choices)
            correct = choices.index(str(answer))
            diag = {"1": f"Each jump is +{skip}.", "2": "Look at the pattern between numbers.", "3": f"Add {skip} to the previous number."}
            tags = ["skip_counting", "numbers_to_999"]

        elif i < 18:
            # Comparison
            n1 = random.randint(100, 999)
            n2 = random.randint(100, 999)
            while n1 == n2:
                n2 = random.randint(100, 999)
            name2 = random.choice([n for n in NAMES if n != name])
            obj = random.choice(["pages in their book", "beads in their collection", "stamps"])
            stem = f"{name} has {n1} {obj} and {name2} has {n2}. Who has more?"
            winner = name if n1 > n2 else name2
            choices = [winner, name if winner == name2 else name2, "Both same", "Cannot tell"]
            correct = 0
            diag = {"1": "Compare hundreds first, then tens, then ones.", "2": "They are not equal.", "3": "You can always compare two numbers."}
            tags = ["comparison", "numbers_to_999"]

        else:
            # Number names and representation
            num = random.randint(100, 999)
            h, t, o = num // 100, (num // 10) % 10, num % 10
            stem = f"How many hundreds, tens, and ones are in {num}?"
            answer = f"{h} hundreds, {t} tens, {o} ones"
            wrong1 = f"{o} hundreds, {t} tens, {h} ones"
            wrong2 = f"{h} hundreds, {o} tens, {t} ones"
            wrong3 = f"{t} hundreds, {h} tens, {o} ones"
            choices = [answer, wrong1, wrong2, wrong3]
            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Read from left to right: hundreds, tens, ones.", "2": "The leftmost digit is hundreds.", "3": "Don't swap the positions."}
            tags = ["place_value_3digit", "numbers_to_999"]

        svg_file = None
        svg_alt = None
        if i % 3 != 2:
            svg_file = f"{make_id(qid)}.svg"
            if i < 5:
                num_disp = num
                h_d, t_d, o_d = h, t, o
            else:
                num_disp = random.randint(100, 999)
                h_d, t_d, o_d = num_disp // 100, (num_disp // 10) % 10, num_disp % 10
            svg_alt = f"Place value chart showing {num_disp}"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#F5F0FF" rx="5"/>\n'
            svg += f'  <text x="100" y="15" text-anchor="middle" font-size="9" fill="#333" font-weight="bold">Place Value: {num_disp}</text>\n'
            # Three boxes
            svg += f'  <rect x="15" y="25" width="50" height="60" fill="#FF6B6B" rx="5" opacity="0.3"/>\n'
            svg += f'  <rect x="75" y="25" width="50" height="60" fill="#45B7D1" rx="5" opacity="0.3"/>\n'
            svg += f'  <rect x="135" y="25" width="50" height="60" fill="#96CEB4" rx="5" opacity="0.3"/>\n'
            svg += f'  <text x="40" y="45" text-anchor="middle" font-size="8" fill="#333">Hundreds</text>\n'
            svg += f'  <text x="100" y="45" text-anchor="middle" font-size="8" fill="#333">Tens</text>\n'
            svg += f'  <text x="160" y="45" text-anchor="middle" font-size="8" fill="#333">Ones</text>\n'
            svg += f'  <text x="40" y="70" text-anchor="middle" font-size="18" fill="#FF6B6B" font-weight="bold">{h_d}</text>\n'
            svg += f'  <text x="100" y="70" text-anchor="middle" font-size="18" fill="#45B7D1" font-weight="bold">{t_d}</text>\n'
            svg += f'  <text x="160" y="70" text-anchor="middle" font-size="18" fill="#96CEB4" font-weight="bold">{o_d}</text>\n'
            svg += f'  <text x="40" y="100" text-anchor="middle" font-size="7" fill="#666">={h_d*100}</text>\n'
            svg += f'  <text x="100" y="100" text-anchor="middle" font-size="7" fill="#666">={t_d*10}</text>\n'
            svg += f'  <text x="160" y="100" text-anchor="middle" font-size="7" fill="#666">={o_d}</text>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": d,
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": diag,
            "tags": tags,
            "topic": "ncert_g2_numbers_999",
            "chapter": "Ch4: Numbers up to 999",
            "hint": {
                "level_0": "A 3-digit number has hundreds, tens, and ones places.",
                "level_1": "Read from left: first digit is hundreds, second is tens, third is ones.",
                "level_2": "Break the number into H×100 + T×10 + O×1."
            },
            "curriculum_tags": ["NCERT_2_4"],
            "irt_params": irt
        })
        qid += 1

    return questions, qid


# ============================================================
# CHAPTER 5: Multiplication introduction
# ============================================================
def gen_ch5_questions(start_id):
    questions = []
    qid = start_id

    mult_contexts = [
        ("There are {groups} plates with {per} {obj} on each. How many {obj} in all?", "plates"),
        ("{name} has {groups} bags with {per} {obj} in each bag. How many {obj} total?", "bags"),
        ("There are {groups} rows of {per} {obj}. How many {obj} altogether?", "rows"),
        ("{name} gives {per} {obj} to each of {groups} friends. How many {obj} needed?", "gives"),
        ("An autorickshaw makes {groups} trips carrying {per} passengers each. Total passengers?", "trips"),
        ("{name} puts {per} {obj} on each of {groups} shelves. How many {obj} used?", "shelves"),
    ]

    for i in range(27):
        diff = ["easy"]*9 + ["medium"]*9 + ["hard"]*9
        d = diff[i]
        irt, score = irt_params(d)
        name = random.choice(NAMES)
        obj = random.choice(OBJECTS_FOOD + OBJECTS_PLAY + OBJECTS_SCHOOL)

        if d == "easy":
            table = random.choice([2, 5])
            groups = random.randint(2, 5)
        elif d == "medium":
            table = random.choice([2, 3, 4, 5])
            groups = random.randint(3, 7)
        else:
            table = random.choice([3, 4, 5])
            groups = random.randint(5, 10)

        per = table
        answer = groups * per

        if i < 9:
            # Repeated addition style
            template, ctx = random.choice(mult_contexts)
            stem = template.format(name=name, groups=groups, per=per, obj=obj)
        elif i < 18:
            # Times table
            stem = f"What is {groups} × {per}?"
            if i % 3 == 0:
                stem = f"{name} needs to find {groups} times {per}. What is the answer?"
        else:
            # Word problem with multiplication
            template, ctx = random.choice(mult_contexts)
            stem = template.format(name=name, groups=groups, per=per, obj=obj)

        wrong1 = answer + per
        wrong2 = answer - per
        wrong3 = groups + per
        wrongs = list(set([wrong1, wrong2, wrong3]) - {answer})
        while len(wrongs) < 3:
            wrongs.append(answer + random.choice([1, -1, 2]))
        wrongs = [w for w in wrongs if w != answer and w > 0][:3]
        while len(wrongs) < 3:
            wrongs.append(answer + random.randint(2, 5))

        choices = [str(answer)] + [str(w) for w in wrongs[:3]]
        random.shuffle(choices)
        correct = choices.index(str(answer))

        svg_file = None
        svg_alt = None
        if i % 3 != 2:
            svg_file = f"{make_id(qid)}.svg"
            svg_alt = f"{groups} groups of {per} objects shown as dots in circles"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#FFFFF0" rx="5"/>\n'
            svg += f'  <text x="100" y="12" text-anchor="middle" font-size="8" fill="#333">{groups} groups of {per}</text>\n'
            cols = min(groups, 5)
            rows_needed = math.ceil(groups / cols)
            for g in range(groups):
                col = g % cols
                row = g // cols
                cx = 20 + col * 38
                cy = 35 + row * 45
                svg += f'  <ellipse cx="{cx+15}" cy="{cy+15}" rx="16" ry="14" fill="none" stroke="#DDA0DD" stroke-width="1.5" stroke-dasharray="3,2"/>\n'
                # dots inside
                for d_idx in range(min(per, 5)):
                    dx = cx + 5 + (d_idx % 3) * 10
                    dy = cy + 8 + (d_idx // 3) * 10
                    color = random.choice(COLORS_SVG)
                    svg += f'  <circle cx="{dx}" cy="{dy}" r="3" fill="{color}"/>\n'
                if per > 5:
                    svg += f'  <text x="{cx+15}" y="{cy+28}" text-anchor="middle" font-size="6" fill="#666">({per})</text>\n'
            svg += f'  <text x="100" y="112" text-anchor="middle" font-size="8" fill="#333">{groups} × {per} = ?</text>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        rep_add = " + ".join([str(per)] * min(groups, 6))
        if groups > 6:
            rep_add += " + ..."

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": d if isinstance(d, str) else diff[i],
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": {
                "1": "Multiplication is repeated addition. Count the groups.",
                "2": f"You need {groups} groups of {per}, not {groups}+{per}.",
                "3": f"Try adding {per} exactly {groups} times."
            },
            "tags": ["multiplication", "repeated_addition", "times_tables"],
            "topic": "ncert_g2_multiplication",
            "chapter": "Ch5: Multiplication introduction",
            "hint": {
                "level_0": "Multiplication means adding the same number many times.",
                "level_1": f"Add {per} a total of {groups} times: {rep_add}",
                "level_2": f"{groups} × {per} = {rep_add} = {answer}"
            },
            "curriculum_tags": ["NCERT_2_5"],
            "irt_params": irt
        })
        qid += 1

    return questions, qid


# ============================================================
# CHAPTER 6: Shapes & Patterns
# ============================================================
def gen_ch6_questions(start_id):
    questions = []
    qid = start_id

    shapes_2d = ["circle", "square", "rectangle", "triangle", "oval"]
    shapes_3d = ["cube", "sphere", "cylinder", "cone", "cuboid"]

    for i in range(27):
        diff = ["easy"]*9 + ["medium"]*9 + ["hard"]*9
        d = diff[i]
        irt, score = irt_params(d)
        name = random.choice(NAMES)

        if i < 7:
            # Shape identification
            shape = random.choice(shapes_2d)
            sides_map = {"circle": 0, "square": 4, "rectangle": 4, "triangle": 3, "oval": 0}
            sides = sides_map[shape]

            if i < 3:
                stem = f"How many sides does a {shape} have?"
                answer = str(sides)
                choices = [str(sides), str(sides+1) if sides > 0 else "1", str(sides+2) if sides > 0 else "2", "5"]
            elif i < 5:
                stem = f"Which shape has 3 sides and 3 corners?"
                answer = "Triangle"
                choices = ["Triangle", "Square", "Rectangle", "Circle"]
            else:
                stem = f"{name} sees a shape with 4 equal sides. What shape is it?"
                answer = "Square"
                choices = ["Square", "Rectangle", "Triangle", "Circle"]

            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Count the straight sides of the shape.", "2": "A circle has no straight sides.", "3": "Equal sides means all sides are the same length."}
            tags = ["shapes_2d", "identification"]

        elif i < 14:
            # 3D shapes
            shape = random.choice(shapes_3d)
            real_objects = {
                "cube": ["dice", "Rubik's cube", "sugar cube", "ice cube"],
                "sphere": ["cricket ball", "ladoo", "marble", "globe"],
                "cylinder": ["bangle", "pipe", "candle", "glass"],
                "cone": ["ice cream cone", "birthday cap", "funnel", "megaphone"],
                "cuboid": ["brick", "matchbox", "book", "eraser"]
            }
            obj_example = random.choice(real_objects[shape])
            stem = f"A {obj_example} is shaped like a ___."
            answer = shape.capitalize()
            other_shapes = [s.capitalize() for s in shapes_3d if s != shape]
            choices = [answer] + random.sample(other_shapes, 3)
            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Think about the shape you can hold in your hand.", "2": "A sphere is round like a ball.", "3": "A cube has 6 equal square faces."}
            tags = ["shapes_3d", "real_world"]

        elif i < 20:
            # Patterns
            patterns = [
                ("🔴🔵🔴🔵🔴___", "🔵", ["🔵", "🔴", "🟢", "🟡"], "The pattern alternates red, blue."),
                ("△○△○△___", "○", ["○", "△", "□", "☆"], "Shapes alternate: triangle, circle."),
                ("1, 3, 5, 7, ___", "9", ["9", "8", "10", "11"], "Odd numbers: add 2 each time."),
                ("2, 4, 6, 8, ___", "10", ["10", "9", "12", "11"], "Even numbers: add 2 each time."),
                ("AB, AB, AB, ___", "AB", ["AB", "BA", "AA", "BB"], "The group AB repeats."),
                ("🌸🌸🌺🌸🌸🌺___", "🌸", ["🌸", "🌺", "🌻", "🌹"], "Pattern: flower flower star, repeats."),
            ]
            pat = patterns[i - 14]
            stem = f"What comes next in the pattern? {pat[0]}"
            answer = pat[1]
            choices = pat[2]
            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": pat[3], "2": "Look for the repeating group.", "3": "Cover part of the pattern and see what repeats."}
            tags = ["patterns", "continuation"]

        else:
            # Symmetry
            sym_objects = [
                ("butterfly", True), ("leaf", True), ("letter A", True),
                ("your hand print", False), ("letter B", True), ("letter R", False),
                ("rangoli design", True)
            ]
            obj, is_sym = sym_objects[i - 20]
            stem = f"Does a {obj} have a line of symmetry (can you fold it into two matching halves)?"
            if is_sym:
                answer = "Yes"
                choices = ["Yes", "No", "Only sometimes", "Cannot tell"]
            else:
                answer = "No"
                choices = ["No", "Yes", "Only sometimes", "Cannot tell"]
            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Imagine folding it in half. Do both sides match?", "2": "Symmetry means both halves are mirror images.", "3": "Try drawing a line down the middle."}
            tags = ["symmetry", "shapes"]

        svg_file = None
        svg_alt = None
        if i < 7 or (14 <= i < 20):
            svg_file = f"{make_id(qid)}.svg"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#F0FFF0" rx="5"/>\n'
            if i < 7:
                svg_alt = f"A {shape} shape drawn with bright colors"
                if shape == "circle":
                    svg += f'  <circle cx="100" cy="60" r="35" fill="#FF6B6B" stroke="#333" stroke-width="1"/>\n'
                elif shape == "square":
                    svg += f'  <rect x="65" y="25" width="70" height="70" fill="#45B7D1" stroke="#333" stroke-width="1"/>\n'
                elif shape == "rectangle":
                    svg += f'  <rect x="40" y="30" width="120" height="60" fill="#96CEB4" stroke="#333" stroke-width="1"/>\n'
                elif shape == "triangle":
                    svg += f'  <polygon points="100,20 50,100 150,100" fill="#FFEAA7" stroke="#333" stroke-width="1"/>\n'
                elif shape == "oval":
                    svg += f'  <ellipse cx="100" cy="60" rx="60" ry="35" fill="#DDA0DD" stroke="#333" stroke-width="1"/>\n'
                svg += f'  <text x="100" y="115" text-anchor="middle" font-size="9" fill="#333">{shape.capitalize()}</text>\n'
            else:
                svg_alt = "Pattern sequence visual"
                svg += f'  <text x="100" y="60" text-anchor="middle" font-size="12" fill="#333">Pattern: find what comes next</text>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": d,
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": diag,
            "tags": tags,
            "topic": "ncert_g2_shapes",
            "chapter": "Ch6: Shapes & Patterns",
            "hint": {
                "level_0": "Look carefully at the shape or pattern.",
                "level_1": "Count sides, look for repeating groups.",
                "level_2": "Shapes: count straight edges. Patterns: find the smallest repeating unit."
            },
            "curriculum_tags": ["NCERT_2_6"],
            "irt_params": irt
        })
        qid += 1

    return questions, qid


# ============================================================
# CHAPTER 7: Measurement
# ============================================================
def gen_ch7_questions(start_id):
    questions = []
    qid = start_id

    for i in range(27):
        diff = ["easy"]*9 + ["medium"]*9 + ["hard"]*9
        d = diff[i]
        irt, score = irt_params(d)
        name = random.choice(NAMES)

        if i < 9:
            # Length (cm/m)
            lengths = [
                (f"{name}'s pencil is 15 cm long and {random.choice(NAMES)}'s pencil is 12 cm. Which is longer?", "easy"),
                (f"A table is 1 metre long. How many centimetres is that?", "easy"),
                (f"{name} measured a ribbon as 50 cm. Is that more or less than 1 metre?", "medium"),
                (f"A door is about 2 metres tall. About how many centimetres is that?", "medium"),
                (f"{name}'s skipping rope is 150 cm. How many metres and cm is that?", "hard"),
            ]
            if i < 2:
                obj1_len = random.randint(10, 25)
                obj2_len = random.randint(10, 25)
                while obj1_len == obj2_len:
                    obj2_len = random.randint(10, 25)
                longer = max(obj1_len, obj2_len)
                obj1 = random.choice(["pencil", "ribbon", "stick", "thread"])
                obj2 = random.choice(["crayon", "straw", "rope piece", "ruler"])
                stem = f"{name}'s {obj1} is {obj1_len} cm and the {obj2} is {obj2_len} cm. Which is longer?"
                answer = f"The {obj1}" if obj1_len > obj2_len else f"The {obj2}"
                choices = [f"The {obj1}", f"The {obj2}", "Both are same", "Cannot tell"]
                correct = 0 if obj1_len > obj2_len else 1
            elif i < 5:
                metres = random.randint(1, 3)
                stem = f"How many centimetres are in {metres} metre{'s' if metres > 1 else ''}?"
                answer = str(metres * 100)
                choices = [str(metres * 100), str(metres * 10), str(metres * 1000), str(metres + 100)]
                random.shuffle(choices)
                correct = choices.index(answer)
            else:
                cm_val = random.choice([120, 150, 200, 250, 175])
                m = cm_val // 100
                leftover = cm_val % 100
                stem = f"A cloth piece is {cm_val} cm long. How many metres and extra cm is that?"
                answer = f"{m} m {leftover} cm"
                choices = [f"{m} m {leftover} cm", f"{leftover} m {m} cm", f"{m+1} m 0 cm", f"{cm_val} m"]
                random.shuffle(choices)
                correct = choices.index(answer)

            diag = {"1": "1 metre = 100 cm.", "2": "Compare the numbers — bigger number means longer.", "3": "Divide by 100 to convert cm to m."}
            tags = ["measurement", "length", "cm_m"]

        elif i < 18:
            # Weight (kg/g)
            if i < 12:
                w1 = random.randint(1, 10)
                obj1 = random.choice(["bag of rice", "watermelon", "school bag", "pumpkin"])
                stem = f"{name}'s {obj1} weighs {w1} kg. How many grams is that?"
                answer = str(w1 * 1000)
                choices = [str(w1 * 1000), str(w1 * 100), str(w1 * 10), str(w1)]
                random.shuffle(choices)
                correct = choices.index(answer)
            elif i < 15:
                items = [("apple", 150), ("mango", 200), ("banana", 100), ("orange", 180)]
                item, weight = random.choice(items)
                count = random.randint(2, 5)
                total = weight * count
                stem = f"Each {item} weighs about {weight} g. How much do {count} {item}s weigh together?"
                answer = str(total)
                choices = [str(total), str(total + weight), str(total - weight), str(weight)]
                random.shuffle(choices)
                correct = choices.index(answer)
            else:
                kg_val = random.choice([2, 3, 5])
                g_val = random.choice([200, 500, 750])
                total_g = kg_val * 1000 + g_val
                stem = f"A bag weighs {kg_val} kg {g_val} g. How many grams is that in total?"
                answer = str(total_g)
                choices = [str(total_g), str(kg_val + g_val), str(kg_val * g_val), str(total_g + 1000)]
                random.shuffle(choices)
                correct = choices.index(answer)

            diag = {"1": "1 kg = 1000 g.", "2": "Multiply to convert kg to g.", "3": "Add the kg part (×1000) and g part together."}
            tags = ["measurement", "weight", "kg_g"]

        else:
            # Capacity (litres)
            if i < 23:
                containers = [("bucket", 10), ("glass", 1), ("bottle", 2), ("jug", 3), ("tank", 50)]
                cont, cap = random.choice(containers)
                count = random.randint(2, 5)
                total = cap * count
                stem = f"Each {cont} holds {cap} litre{'s' if cap > 1 else ''}. How many litres do {count} {cont}s hold?"
                answer = str(total)
                choices = [str(total), str(total + cap), str(cap), str(count)]
                random.shuffle(choices)
                correct = choices.index(answer)
            else:
                big = random.choice([5, 10, 20])
                small = random.choice([1, 2])
                stem = f"A tank holds {big} litres. {name} fills it using a {small}-litre jug. How many jugs needed?"
                answer = str(big // small)
                choices = [str(big // small), str(big * small), str(big - small), str(big + small)]
                random.shuffle(choices)
                correct = choices.index(answer)

            diag = {"1": "Multiply number of containers × capacity each.", "2": "To find how many jugs, divide total by jug size.", "3": "Think: how many times does the small fit into the big?"}
            tags = ["measurement", "capacity", "litres"]

        svg_file = None
        svg_alt = None
        if i % 3 != 2:
            svg_file = f"{make_id(qid)}.svg"
            svg_alt = "Measurement illustration"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#FFF8DC" rx="5"/>\n'
            if i < 9:
                # Ruler visual
                svg += f'  <rect x="20" y="50" width="160" height="20" fill="#FFEAA7" stroke="#333" stroke-width="0.5"/>\n'
                for tick in range(17):
                    x = 20 + tick * 10
                    h = 15 if tick % 5 == 0 else 8
                    svg += f'  <line x1="{x}" y1="50" x2="{x}" y2="{50-h}" stroke="#333" stroke-width="0.5"/>\n'
                    if tick % 5 == 0:
                        svg += f'  <text x="{x}" y="{45-h}" text-anchor="middle" font-size="6" fill="#333">{tick}</text>\n'
                svg += f'  <text x="100" y="85" text-anchor="middle" font-size="8" fill="#333">cm ruler</text>\n'
            elif i < 18:
                # Scale visual
                svg += f'  <polygon points="100,20 60,90 140,90" fill="none" stroke="#333" stroke-width="1.5"/>\n'
                svg += f'  <line x1="60" y1="90" x2="140" y2="90" stroke="#333" stroke-width="2"/>\n'
                svg += f'  <circle cx="100" cy="90" r="3" fill="#FF6B6B"/>\n'
                svg += f'  <text x="100" y="110" text-anchor="middle" font-size="8" fill="#333">Weighing scale</text>\n'
            else:
                # Bottle visual
                svg += f'  <rect x="80" y="30" width="40" height="70" fill="#45B7D1" rx="5" opacity="0.5" stroke="#333" stroke-width="0.5"/>\n'
                svg += f'  <rect x="90" y="20" width="20" height="15" fill="#45B7D1" rx="3" stroke="#333" stroke-width="0.5"/>\n'
                svg += f'  <text x="100" y="70" text-anchor="middle" font-size="8" fill="#333">L</text>\n'
                svg += f'  <text x="100" y="115" text-anchor="middle" font-size="8" fill="#333">Capacity in litres</text>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": d,
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": diag,
            "tags": tags,
            "topic": "ncert_g2_measurement",
            "chapter": "Ch7: Measurement",
            "hint": {
                "level_0": "Remember: 1 m = 100 cm, 1 kg = 1000 g.",
                "level_1": "To convert bigger to smaller units, multiply.",
                "level_2": "Break it into parts: convert each unit separately, then combine."
            },
            "curriculum_tags": ["NCERT_2_7"],
            "irt_params": irt
        })
        qid += 1

    return questions, qid


# ============================================================
# CHAPTER 8: Time
# ============================================================
def gen_ch8_questions(start_id):
    questions = []
    qid = start_id

    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for i in range(27):
        diff = ["easy"]*9 + ["medium"]*9 + ["hard"]*9
        d = diff[i]
        irt, score = irt_params(d)
        name = random.choice(NAMES)

        if i < 10:
            # Reading clock
            hour = random.randint(1, 12)
            half = random.choice([True, False]) if d != "easy" else False
            time_str = f"{hour}:30" if half else f"{hour}:00"
            time_words = f"half past {hour}" if half else f"{hour} o'clock"

            stem = f"The clock shows {time_words}. What time is it?"
            answer = time_str
            if half:
                choices = [f"{hour}:30", f"{hour}:00", f"{hour+1 if hour<12 else 1}:00", f"{hour}:15"]
            else:
                choices = [f"{hour}:00", f"{hour}:30", f"{hour+1 if hour<12 else 1}:00", f"{hour-1 if hour>1 else 12}:00"]
            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "The short hand shows hours, long hand shows minutes.", "2": "O'clock means :00, half past means :30.", "3": "When the long hand points to 6, it's half past."}
            tags = ["time", "clock_reading"]

            # SVG for clock
            svg_file = f"{make_id(qid)}.svg"
            svg_alt = f"Clock showing {time_words}"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#F0F8FF" rx="5"/>\n'
            svg += f'  <circle cx="100" cy="60" r="45" fill="white" stroke="#333" stroke-width="2"/>\n'
            # Hour markers
            for h in range(12):
                angle = math.radians(h * 30 - 90)
                x1 = 100 + 38 * math.cos(angle)
                y1 = 60 + 38 * math.sin(angle)
                x2 = 100 + 42 * math.cos(angle)
                y2 = 60 + 42 * math.sin(angle)
                svg += f'  <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#333" stroke-width="1.5"/>\n'
                # Number
                nx = 100 + 33 * math.cos(angle)
                ny = 60 + 33 * math.sin(angle)
                svg += f'  <text x="{nx:.1f}" y="{ny+3:.1f}" text-anchor="middle" font-size="7" fill="#333">{h if h > 0 else 12}</text>\n'
            # Hour hand
            hour_angle = math.radians((hour % 12) * 30 + (30 if half else 0) - 90)
            hx = 100 + 22 * math.cos(hour_angle)
            hy = 60 + 22 * math.sin(hour_angle)
            svg += f'  <line x1="100" y1="60" x2="{hx:.1f}" y2="{hy:.1f}" stroke="#333" stroke-width="3" stroke-linecap="round"/>\n'
            # Minute hand
            min_angle = math.radians((30 if half else 0) * 6 - 90)  # 0 or 180 degrees
            if half:
                min_angle = math.radians(180 - 90)
            else:
                min_angle = math.radians(-90)
            mx = 100 + 32 * math.cos(min_angle)
            my = 60 + 32 * math.sin(min_angle)
            svg += f'  <line x1="100" y1="60" x2="{mx:.1f}" y2="{my:.1f}" stroke="#FF6B6B" stroke-width="2" stroke-linecap="round"/>\n'
            svg += f'  <circle cx="100" cy="60" r="3" fill="#333"/>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        elif i < 18:
            # Calendar / months / days
            svg_file = None
            svg_alt = None
            if i < 13:
                month_idx = random.randint(0, 11)
                stem = f"Which month comes right after {months[month_idx]}?"
                answer = months[(month_idx + 1) % 12]
                others = random.sample([m for m in months if m != answer], 3)
                choices = [answer] + others
                random.shuffle(choices)
                correct = choices.index(answer)
            elif i < 16:
                day_idx = random.randint(0, 6)
                stem = f"If today is {days[day_idx]}, what day is tomorrow?"
                answer = days[(day_idx + 1) % 7]
                others = random.sample([d2 for d2 in days if d2 != answer], 3)
                choices = [answer] + others
                random.shuffle(choices)
                correct = choices.index(answer)
            else:
                stem = f"How many days are there in a week?"
                answer = "7"
                choices = ["7", "5", "6", "10"]
                random.shuffle(choices)
                correct = choices.index(answer)

            diag = {"1": "Remember the order of months/days.", "2": "After means the next one in sequence.", "3": "A week has 7 days."}
            tags = ["time", "calendar"]

        else:
            # Duration / daily routine
            svg_file = None
            svg_alt = None
            activities = [
                (f"{name} starts homework at 4 o'clock and finishes at 5 o'clock. How long did it take?", "1 hour", ["1 hour", "2 hours", "30 minutes", "4 hours"]),
                (f"School starts at 8 o'clock and ends at 2 o'clock. How many hours is that?", "6 hours", ["6 hours", "4 hours", "8 hours", "10 hours"]),
                (f"{name} sleeps at 9 o'clock at night. She wakes up after 10 hours. What time does she wake?", "7 o'clock", ["7 o'clock", "8 o'clock", "6 o'clock", "10 o'clock"]),
                (f"Lunch break is for half an hour. How many minutes is that?", "30 minutes", ["30 minutes", "60 minutes", "15 minutes", "45 minutes"]),
                (f"A cartoon show is 30 minutes long. {name} watches 2 shows. How long is that?", "60 minutes", ["60 minutes", "30 minutes", "90 minutes", "45 minutes"]),
                (f"If it is 3 o'clock now, what time will it be in 2 hours?", "5 o'clock", ["5 o'clock", "4 o'clock", "6 o'clock", "1 o'clock"]),
                (f"{name} takes a 1-hour bus ride starting at 7 o'clock. When does he arrive?", "8 o'clock", ["8 o'clock", "7 o'clock", "9 o'clock", "6 o'clock"]),
                (f"How many months are there in a year?", "12", ["12", "10", "7", "30"]),
                (f"Which is longer: 1 hour or 30 minutes?", "1 hour", ["1 hour", "30 minutes", "Both are same", "Cannot tell"]),
            ]
            act = activities[i - 18]
            stem = act[0]
            answer = act[1]
            choices = act[2]
            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Count the hours between start and end.", "2": "1 hour = 60 minutes.", "3": "Add the hours/minutes to the start time."}
            tags = ["time", "duration"]

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": d,
            "difficulty_score": score,
            "visual_svg": svg_file if 'svg_file' in dir() and svg_file else None,
            "visual_alt": svg_alt if 'svg_alt' in dir() and svg_alt else None,
            "diagnostics": diag,
            "tags": tags,
            "topic": "ncert_g2_time",
            "chapter": "Ch8: Time",
            "hint": {
                "level_0": "Think about the clock hands and calendar order.",
                "level_1": "Short hand = hours, long hand = minutes. 1 hour = 60 min.",
                "level_2": "Count forward on the clock or calendar to find the answer."
            },
            "curriculum_tags": ["NCERT_2_8"],
            "irt_params": irt
        })
        qid += 1

    return questions, qid


# ============================================================
# CHAPTER 9: Money
# ============================================================
def gen_ch9_questions(start_id):
    questions = []
    qid = start_id

    items_prices = [
        ("pencil", 5), ("eraser", 3), ("sharpener", 4), ("notebook", 20), ("ruler", 10),
        ("lollipop", 2), ("samosa", 8), ("juice box", 15), ("banana", 5), ("balloon", 3),
        ("sticker sheet", 10), ("colour pencil", 7), ("ice cream", 20), ("biscuit packet", 12),
        ("toy car", 25), ("hair clip", 6), ("rubber ball", 15), ("chocolate", 10),
        ("mango", 12), ("comb", 8)
    ]

    for i in range(27):
        diff = ["easy"]*9 + ["medium"]*9 + ["hard"]*9
        d = diff[i]
        irt, score = irt_params(d)
        name = random.choice(NAMES)

        if i < 9:
            # Simple coin/note recognition and totals
            item, price = random.choice(items_prices)
            if i < 3:
                stem = f"A {item} costs ₹{price}. {name} gives ₹{price + 5}. How much change?"
                change = 5
                choices = [f"₹{change}", f"₹{price}", f"₹{price + 5}", f"₹{change + 2}"]
            elif i < 6:
                count = random.randint(2, 4)
                total = price * count
                stem = f"{name} buys {count} {item}s at ₹{price} each. How much to pay?"
                answer_val = total
                choices = [f"₹{total}", f"₹{price}", f"₹{total + price}", f"₹{total - price}"]
            else:
                coins = random.choice([(10, 2, 5, 1), (5, 3, 2, 2), (10, 1, 5, 2)])
                total = coins[0] * coins[1] + coins[2] * coins[3]
                stem = f"{name} has {coins[1]} coins of ₹{coins[0]} and {coins[3]} coins of ₹{coins[2]}. How much money?"
                choices = [f"₹{total}", f"₹{total + 5}", f"₹{coins[0] + coins[2]}", f"₹{total - 5}"]

            if i < 3:
                answer = f"₹{change}"
            elif i < 6:
                answer = f"₹{total}"
            else:
                answer = f"₹{total}"

            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Change = amount given - price.", "2": "Multiply price × quantity for total cost.", "3": "Add up all coin values separately."}
            tags = ["money", "coins", "change"]

        elif i < 18:
            # Making amounts and giving change
            item1, p1 = random.choice(items_prices)
            item2, p2 = random.choice([(it, pr) for it, pr in items_prices if it != item1])
            total = p1 + p2
            paid = ((total // 10) + 1) * 10 if total % 10 != 0 else total + 10
            change = paid - total

            if i < 13:
                stem = f"{name} buys a {item1} (₹{p1}) and a {item2} (₹{p2}). How much total?"
                answer = f"₹{total}"
                choices = [f"₹{total}", f"₹{total + 5}", f"₹{p1}", f"₹{total - 3}"]
            else:
                stem = f"{name} buys items worth ₹{total} and pays ₹{paid}. How much change?"
                answer = f"₹{change}"
                choices = [f"₹{change}", f"₹{total}", f"₹{paid}", f"₹{change + 5}"]

            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Add prices for total. Subtract total from paid for change.", "2": "Change = paid - cost.", "3": "Make sure you're adding, not subtracting the prices."}
            tags = ["money", "shopping", "word_problem"]

        else:
            # More complex money problems
            if i < 22:
                item, price = random.choice(items_prices)
                budget = price + random.randint(5, 20)
                stem = f"{name} has ₹{budget}. A {item} costs ₹{price}. Can she buy it? If yes, how much money left?"
                leftover = budget - price
                answer = f"Yes, ₹{leftover} left"
                choices = [f"Yes, ₹{leftover} left", f"No, not enough", f"Yes, ₹{budget} left", f"Yes, ₹{price} left"]
            elif i < 25:
                items_bought = random.sample(items_prices, 3)
                total = sum(p for _, p in items_bought)
                item_names = ", ".join(f"{it} (₹{pr})" for it, pr in items_bought)
                stem = f"{name} buys: {item_names}. What is the total bill?"
                answer = f"₹{total}"
                choices = [f"₹{total}", f"₹{total + 5}", f"₹{total - 5}", f"₹{total + 10}"]
            else:
                note = random.choice([50, 100])
                item, price = random.choice([(it, pr) for it, pr in items_prices if pr < note])
                count = note // price
                stem = f"How many {item}s (₹{price} each) can {name} buy with a ₹{note} note?"
                answer = str(count)
                choices = [str(count), str(count + 1), str(count - 1), str(note)]

            random.shuffle(choices)
            correct = choices.index(answer if isinstance(answer, str) else str(answer))
            diag = {"1": "Compare your money with the price.", "2": "Subtract to find leftover money.", "3": "Divide your total money by the price per item."}
            tags = ["money", "budgeting", "word_problem"]

        svg_file = None
        svg_alt = None
        if i % 3 != 2:
            svg_file = f"{make_id(qid)}.svg"
            svg_alt = "Indian rupee coins and notes illustration"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#FFFAF0" rx="5"/>\n'
            # Draw some coins
            coin_vals = [1, 2, 5, 10]
            for ci, cv in enumerate(coin_vals[:3]):
                cx = 30 + ci * 50
                svg += f'  <circle cx="{cx}" cy="40" r="15" fill="#FFD700" stroke="#B8860B" stroke-width="1.5"/>\n'
                svg += f'  <text x="{cx}" y="44" text-anchor="middle" font-size="8" fill="#333" font-weight="bold">₹{cv}</text>\n'
            # Draw a note
            svg += f'  <rect x="40" y="70" width="70" height="35" fill="#90EE90" rx="3" stroke="#333" stroke-width="0.5"/>\n'
            svg += f'  <text x="75" y="92" text-anchor="middle" font-size="10" fill="#333" font-weight="bold">₹10</text>\n'
            svg += f'  <rect x="120" y="70" width="70" height="35" fill="#ADD8E6" rx="3" stroke="#333" stroke-width="0.5"/>\n'
            svg += f'  <text x="155" y="92" text-anchor="middle" font-size="10" fill="#333" font-weight="bold">₹50</text>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": d,
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": diag,
            "tags": tags,
            "topic": "ncert_g2_money",
            "chapter": "Ch9: Money",
            "hint": {
                "level_0": "Think about adding and subtracting money amounts.",
                "level_1": "Total cost = price × quantity. Change = paid - total.",
                "level_2": "Add all item prices. Then subtract from money given."
            },
            "curriculum_tags": ["NCERT_2_9"],
            "irt_params": irt
        })
        qid += 1

    return questions, qid


# ============================================================
# CHAPTER 10: Data Handling
# ============================================================
def gen_ch10_questions(start_id):
    questions = []
    qid = start_id

    fruits = ["Mango", "Banana", "Apple", "Orange", "Guava"]
    animals = ["Cat", "Dog", "Parrot", "Rabbit", "Fish"]
    colours = ["Red", "Blue", "Green", "Yellow", "Pink"]

    for i in range(27):
        diff = ["easy"]*9 + ["medium"]*9 + ["hard"]*9
        d = diff[i]
        irt, score = irt_params(d)
        name = random.choice(NAMES)

        # Generate data
        categories = random.choice([fruits[:4], animals[:4], colours[:4]])
        values = [random.randint(2, 10) for _ in range(4)]

        if i < 9:
            # Reading pictograph
            cat_idx = random.randint(0, 3)
            stem = f"In a class survey, the favourite fruits are shown in a chart. How many children like {categories[cat_idx]}?"
            answer = str(values[cat_idx])
            wrongs = [str(values[cat_idx] + 1), str(values[cat_idx] - 1), str(sum(values))]
            choices = [answer] + wrongs[:3]
            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Count the symbols next to the category.", "2": "Each symbol = 1 child.", "3": "Don't add all categories — just count the one asked."}
            tags = ["data_handling", "pictograph", "reading"]

        elif i < 18:
            # Comparison from chart
            max_val = max(values)
            min_val = min(values)
            max_cat = categories[values.index(max_val)]
            min_cat = categories[values.index(min_val)]

            if i % 2 == 0:
                stem = f"Look at the chart. Which item is most popular?"
                answer = max_cat
                others = [c for c in categories if c != max_cat]
                choices = [answer] + others[:3]
            else:
                stem = f"Which item is least popular in the chart?"
                answer = min_cat
                others = [c for c in categories if c != min_cat]
                choices = [answer] + others[:3]

            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "The tallest bar or most symbols = most popular.", "2": "The shortest bar or fewest symbols = least popular.", "3": "Compare the numbers for each item."}
            tags = ["data_handling", "comparison", "bar_chart"]

        else:
            # Total / difference from chart
            if i % 2 == 0:
                stem = f"How many children were surveyed in total? (Add all categories)"
                answer = str(sum(values))
                choices = [str(sum(values)), str(sum(values) + 2), str(max(values)), str(sum(values) - 1)]
            else:
                diff_val = max(values) - min(values)
                stem = f"How many more children like {categories[values.index(max(values))]} than {categories[values.index(min(values))]}?"
                answer = str(diff_val)
                choices = [str(diff_val), str(diff_val + 1), str(max(values)), str(min(values))]

            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Add all the values for total.", "2": "Subtract smallest from largest for the difference.", "3": "Read each bar/row carefully."}
            tags = ["data_handling", "total", "difference"]

        # SVG bar chart for most questions
        svg_file = None
        svg_alt = None
        if i % 3 != 2:
            svg_file = f"{make_id(qid)}.svg"
            svg_alt = f"Bar chart showing {', '.join(categories)} with values {values}"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#FAFAFA" rx="5"/>\n'
            svg += f'  <text x="100" y="12" text-anchor="middle" font-size="7" fill="#333">Favourite Things Chart</text>\n'
            # Axes
            svg += f'  <line x1="35" y1="15" x2="35" y2="95" stroke="#333" stroke-width="0.5"/>\n'
            svg += f'  <line x1="35" y1="95" x2="195" y2="95" stroke="#333" stroke-width="0.5"/>\n'
            max_v = max(values) if max(values) > 0 else 1
            bar_colors = ["#FF6B6B", "#45B7D1", "#96CEB4", "#FFEAA7"]
            for bi, (cat, val) in enumerate(zip(categories, values)):
                x = 45 + bi * 38
                bar_h = (val / max_v) * 65
                y = 95 - bar_h
                svg += f'  <rect x="{x}" y="{y:.0f}" width="28" height="{bar_h:.0f}" fill="{bar_colors[bi]}" stroke="#333" stroke-width="0.3"/>\n'
                svg += f'  <text x="{x+14}" y="{y-3:.0f}" text-anchor="middle" font-size="7" fill="#333">{val}</text>\n'
                svg += f'  <text x="{x+14}" y="108" text-anchor="middle" font-size="5" fill="#333">{cat[:5]}</text>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": d,
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": diag,
            "tags": tags,
            "topic": "ncert_g2_data",
            "chapter": "Ch10: Data Handling",
            "hint": {
                "level_0": "Read the chart carefully — count symbols or bar height.",
                "level_1": "Each picture/bar represents a number. Compare them.",
                "level_2": "For total, add all. For difference, subtract smaller from larger."
            },
            "curriculum_tags": ["NCERT_2_10"],
            "irt_params": irt
        })
        qid += 1

    return questions, qid


# ============================================================
# CHAPTER 11: Fractions introduction
# ============================================================
def gen_ch11_questions(start_id):
    questions = []
    qid = start_id

    for i in range(27):
        diff = ["easy"]*9 + ["medium"]*9 + ["hard"]*9
        d = diff[i]
        irt, score = irt_params(d)
        name = random.choice(NAMES)

        if i < 9:
            # Half concept
            wholes = [("roti", "rotis"), ("pizza", "pizzas"), ("cake", "cakes"),
                      ("chapati", "chapatis"), ("apple", "apples"), ("watermelon", "watermelons")]
            item, items_pl = random.choice(wholes)

            if i < 3:
                stem = f"{name} cuts a {item} into 2 equal parts. What is each part called?"
                answer = "One half (½)"
                choices = ["One half (½)", "One quarter (¼)", "One whole", "Two halves"]
            elif i < 6:
                num = random.randint(2, 8) * 2  # even number
                half = num // 2
                stem = f"{name} has {num} {items_pl} and gives half to a friend. How many did she give?"
                answer = str(half)
                choices = [str(half), str(num), str(half + 1), str(half - 1)]
            else:
                stem = f"If you fold a square paper exactly in half, how many equal parts do you get?"
                answer = "2"
                choices = ["2", "1", "3", "4"]

            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Half means 2 equal parts.", "2": "Divide the total by 2 to find half.", "3": "Equal parts means same size."}
            tags = ["fractions", "half"]

        elif i < 18:
            # Quarter concept
            if i < 12:
                item = random.choice(["pizza", "cake", "roti", "paper"])
                stem = f"{name} cuts a {item} into 4 equal parts. What is each part called?"
                answer = "One quarter (¼)"
                choices = ["One quarter (¼)", "One half (½)", "One third", "One whole"]
            elif i < 15:
                num = random.choice([4, 8, 12, 16, 20])
                quarter = num // 4
                obj = random.choice(OBJECTS_FOOD)
                stem = f"There are {num} {obj}. One quarter of them are ripe. How many are ripe?"
                answer = str(quarter)
                choices = [str(quarter), str(num // 2), str(num), str(quarter + 1)]
            else:
                stem = f"How many quarters make a whole?"
                answer = "4"
                choices = ["4", "2", "3", "1"]

            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Quarter means 4 equal parts.", "2": "Divide by 4 to find one quarter.", "3": "4 quarters = 1 whole."}
            tags = ["fractions", "quarter"]

        else:
            # Three-quarters and comparison
            if i < 22:
                num = random.choice([4, 8, 12])
                three_q = (num * 3) // 4
                obj = random.choice(OBJECTS_FOOD)
                stem = f"{name} ate three-quarters of {num} {obj}. How many did she eat?"
                answer = str(three_q)
                choices = [str(three_q), str(num // 4), str(num // 2), str(num)]
            elif i < 25:
                stem = f"Which is bigger: half of a roti or a quarter of the same roti?"
                answer = "Half"
                choices = ["Half", "Quarter", "Both are same", "Cannot tell"]
            else:
                num = random.choice([8, 12, 16])
                half = num // 2
                quarter = num // 4
                stem = f"Out of {num} laddoos, {name} gives half to Ria and a quarter to Arjun. How many given away?"
                given = half + quarter
                answer = str(given)
                choices = [str(given), str(half), str(quarter), str(num)]

            random.shuffle(choices)
            correct = choices.index(answer)
            diag = {"1": "Three-quarters = 3 out of 4 parts.", "2": "Half is bigger than quarter (2 parts vs 1 part).", "3": "Add the fractions: half + quarter = three-quarters."}
            tags = ["fractions", "three_quarters", "comparison"]

        # SVG for fraction visuals
        svg_file = None
        svg_alt = None
        if i % 3 != 2:
            svg_file = f"{make_id(qid)}.svg"
            svg_alt = "Circle divided into equal parts showing fractions"
            svg = svg_header()
            svg += f'  <rect width="200" height="120" fill="#FFF5F5" rx="5"/>\n'
            # Draw a circle divided into parts
            svg += f'  <circle cx="100" cy="55" r="40" fill="#FFEAA7" stroke="#333" stroke-width="1.5"/>\n'
            if i < 9:
                # Half
                svg += f'  <line x1="100" y1="15" x2="100" y2="95" stroke="#333" stroke-width="1.5"/>\n'
                svg += f'  <text x="75" y="58" text-anchor="middle" font-size="10" fill="#FF6B6B" font-weight="bold">½</text>\n'
                svg += f'  <text x="125" y="58" text-anchor="middle" font-size="10" fill="#45B7D1" font-weight="bold">½</text>\n'
                # Shade one half
                svg += f'  <path d="M100,15 A40,40 0 0,0 100,95 Z" fill="#FF6B6B" opacity="0.3"/>\n'
            elif i < 18:
                # Quarter
                svg += f'  <line x1="100" y1="15" x2="100" y2="95" stroke="#333" stroke-width="1.5"/>\n'
                svg += f'  <line x1="60" y1="55" x2="140" y2="55" stroke="#333" stroke-width="1.5"/>\n'
                svg += f'  <path d="M100,55 L100,15 A40,40 0 0,1 140,55 Z" fill="#45B7D1" opacity="0.4"/>\n'
                svg += f'  <text x="115" y="42" text-anchor="middle" font-size="8" fill="#333">¼</text>\n'
            else:
                # Three-quarters shaded
                svg += f'  <line x1="100" y1="15" x2="100" y2="95" stroke="#333" stroke-width="1.5"/>\n'
                svg += f'  <line x1="60" y1="55" x2="140" y2="55" stroke="#333" stroke-width="1.5"/>\n'
                svg += f'  <path d="M100,55 L100,15 A40,40 0 0,1 140,55 Z" fill="#96CEB4" opacity="0.4"/>\n'
                svg += f'  <path d="M100,55 L140,55 A40,40 0 0,1 100,95 Z" fill="#96CEB4" opacity="0.4"/>\n'
                svg += f'  <path d="M100,55 L100,95 A40,40 0 0,1 60,55 Z" fill="#96CEB4" opacity="0.4"/>\n'
                svg += f'  <text x="100" y="110" text-anchor="middle" font-size="8" fill="#333">¾ shaded</text>\n'
            svg += svg_footer()
            with open(os.path.join(VISUALS_DIR, svg_file), 'w') as f:
                f.write(svg)

        questions.append({
            "id": make_id(qid),
            "stem": stem,
            "choices": choices,
            "correct_answer": correct,
            "difficulty_tier": d,
            "difficulty_score": score,
            "visual_svg": svg_file,
            "visual_alt": svg_alt,
            "diagnostics": diag,
            "tags": tags,
            "topic": "ncert_g2_fractions",
            "chapter": "Ch11: Fractions introduction",
            "hint": {
                "level_0": "A fraction means equal parts of a whole.",
                "level_1": "Half = 2 equal parts. Quarter = 4 equal parts.",
                "level_2": "To find half, divide by 2. For quarter, divide by 4. For three-quarters, multiply quarter by 3."
            },
            "curriculum_tags": ["NCERT_2_11"],
            "irt_params": irt
        })
        qid += 1

    return questions, qid


# ============================================================
# MAIN: Generate all questions and save
# ============================================================
def main():
    all_questions = []
    qid = 1

    print("Generating Chapter 1: Numbers up to 100...")
    ch1, qid = gen_ch1_questions(qid)
    all_questions.extend(ch1)
    print(f"  -> {len(ch1)} questions (IDs {ch1[0]['id']} to {ch1[-1]['id']})")

    print("Generating Chapter 2: Addition with carry...")
    ch2, qid = gen_ch2_questions(qid)
    all_questions.extend(ch2)
    print(f"  -> {len(ch2)} questions (IDs {ch2[0]['id']} to {ch2[-1]['id']})")

    print("Generating Chapter 3: Subtraction with borrow...")
    ch3, qid = gen_ch3_questions(qid)
    all_questions.extend(ch3)
    print(f"  -> {len(ch3)} questions (IDs {ch3[0]['id']} to {ch3[-1]['id']})")

    print("Generating Chapter 4: Numbers up to 999...")
    ch4, qid = gen_ch4_questions(qid)
    all_questions.extend(ch4)
    print(f"  -> {len(ch4)} questions (IDs {ch4[0]['id']} to {ch4[-1]['id']})")

    print("Generating Chapter 5: Multiplication introduction...")
    ch5, qid = gen_ch5_questions(qid)
    all_questions.extend(ch5)
    print(f"  -> {len(ch5)} questions (IDs {ch5[0]['id']} to {ch5[-1]['id']})")

    print("Generating Chapter 6: Shapes & Patterns...")
    ch6, qid = gen_ch6_questions(qid)
    all_questions.extend(ch6)
    print(f"  -> {len(ch6)} questions (IDs {ch6[0]['id']} to {ch6[-1]['id']})")

    print("Generating Chapter 7: Measurement...")
    ch7, qid = gen_ch7_questions(qid)
    all_questions.extend(ch7)
    print(f"  -> {len(ch7)} questions (IDs {ch7[0]['id']} to {ch7[-1]['id']})")

    print("Generating Chapter 8: Time...")
    ch8, qid = gen_ch8_questions(qid)
    all_questions.extend(ch8)
    print(f"  -> {len(ch8)} questions (IDs {ch8[0]['id']} to {ch8[-1]['id']})")

    print("Generating Chapter 9: Money...")
    ch9, qid = gen_ch9_questions(qid)
    all_questions.extend(ch9)
    print(f"  -> {len(ch9)} questions (IDs {ch9[0]['id']} to {ch9[-1]['id']})")

    print("Generating Chapter 10: Data Handling...")
    ch10, qid = gen_ch10_questions(qid)
    all_questions.extend(ch10)
    print(f"  -> {len(ch10)} questions (IDs {ch10[0]['id']} to {ch10[-1]['id']})")

    print("Generating Chapter 11: Fractions introduction...")
    ch11, qid = gen_ch11_questions(qid)
    all_questions.extend(ch11)
    print(f"  -> {len(ch11)} questions (IDs {ch11[0]['id']} to {ch11[-1]['id']})")

    # Fix any duplicate choices
    for q in all_questions:
        seen = set()
        for idx, c in enumerate(q['choices']):
            if c in seen:
                # Replace duplicate with a nearby plausible wrong answer
                try:
                    base = int(c.replace('₹', ''))
                    replacement = str(base + random.randint(2, 5))
                    if '₹' in c:
                        replacement = f"₹{base + random.randint(2, 5)}"
                except ValueError:
                    replacement = c + " (different)"
                q['choices'][idx] = replacement
            seen.add(q['choices'][idx])

    # Build final JSON
    output = {
        "topic_id": "ncert_g2",
        "topic_name": "NCERT Grade 2 Mathematics",
        "version": "2.0",
        "curriculum": "NCERT",
        "grade": 2,
        "total_questions": len(all_questions),
        "questions": all_questions
    }

    output_path = os.path.join(OUTPUT_DIR, "questions.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"DONE! Total questions: {len(all_questions)}")
    print(f"Output: {output_path}")
    print(f"SVGs: {VISUALS_DIR}/")

    # Count SVGs
    svg_count = sum(1 for q in all_questions if q["visual_svg"] is not None)
    print(f"Questions with visuals: {svg_count}/{len(all_questions)} ({100*svg_count//len(all_questions)}%)")

    # Difficulty distribution
    easy = sum(1 for q in all_questions if q["difficulty_tier"] == "easy")
    medium = sum(1 for q in all_questions if q["difficulty_tier"] == "medium")
    hard = sum(1 for q in all_questions if q["difficulty_tier"] == "hard")
    print(f"Difficulty: Easy={easy}, Medium={medium}, Hard={hard}")

    # Chapter distribution
    print("\nChapter distribution:")
    chapters = {}
    for q in all_questions:
        ch = q["chapter"]
        chapters[ch] = chapters.get(ch, 0) + 1
    for ch, count in sorted(chapters.items()):
        print(f"  {ch}: {count} questions")

    # Sample questions
    print("\n--- SAMPLE QUESTIONS ---")
    samples = [all_questions[0], all_questions[50], all_questions[150], all_questions[250], all_questions[-1]]
    for s in samples:
        print(f"\n[{s['id']}] ({s['difficulty_tier']}) {s['chapter']}")
        print(f"  Q: {s['stem']}")
        print(f"  Choices: {s['choices']}")
        print(f"  Answer: {s['choices'][s['correct_answer']]}")
        print(f"  SVG: {s['visual_svg']}")


if __name__ == "__main__":
    main()
