#!/usr/bin/env python3
"""Generate 300 NCERT-aligned math questions each for Grade 5 and Grade 6."""

import json
import os
import random
import math

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
G5_DIR = os.path.join(BASE_DIR, "grade5")
G6_DIR = os.path.join(BASE_DIR, "grade6")
G5_VIS = os.path.join(G5_DIR, "visuals")
G6_VIS = os.path.join(G6_DIR, "visuals")

for d in [G5_DIR, G6_DIR, G5_VIS, G6_VIS]:
    os.makedirs(d, exist_ok=True)

# Indian context pools
NAMES = ["Aarav", "Priya", "Rishi", "Ananya", "Kiran", "Meera", "Arjun", "Diya", "Rohan", "Kavya",
         "Sanya", "Vivek", "Neha", "Aditya", "Ishaan", "Pooja", "Rahul", "Sneha", "Vikram", "Tanvi"]
CITIES = ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru", "Jaipur", "Hyderabad", "Pune", "Lucknow", "Kochi"]
FOODS = ["idli", "dosa", "roti", "samosa", "ladoo", "gulab jamun", "pakora", "biryani", "pani puri", "jalebi"]
FESTIVALS = ["Diwali", "Holi", "Onam", "Pongal", "Eid", "Christmas", "Baisakhi", "Navratri"]
SPORTS = ["cricket", "kabaddi", "hockey", "badminton", "football", "kho-kho"]
TRANSPORT = ["auto-rickshaw", "bus", "train", "bicycle", "car"]
RIVERS = ["Ganga", "Yamuna", "Godavari", "Krishna", "Narmada", "Brahmaputra"]
STATES = ["Rajasthan", "Kerala", "Tamil Nadu", "Maharashtra", "Gujarat", "Karnataka", "West Bengal"]

def make_svg(qid, grade, svg_content):
    """Write SVG file and return filename."""
    fname = f"{qid}.svg"
    vis_dir = G5_VIS if grade == 5 else G6_VIS
    svg = f'<svg viewBox="0 0 260 150" xmlns="http://www.w3.org/2000/svg">\n{svg_content}\n</svg>'
    with open(os.path.join(vis_dir, fname), 'w') as f:
        f.write(svg)
    return fname

def irt_params(difficulty_score, grade):
    """Generate IRT parameters based on difficulty score and grade."""
    if grade == 5:
        b = (difficulty_score / 100) * 2.0  # 0.0 to 2.0
    else:
        b = 0.5 + (difficulty_score / 100) * 2.0  # 0.5 to 2.5
    a = round(random.uniform(0.8, 2.0), 2)
    b = round(b, 2)
    c = 0.25
    return {"a": a, "b": b, "c": c}

def difficulty_tier(score):
    if score <= 25: return "easy"
    if score <= 50: return "medium"
    if score <= 75: return "hard"
    return "advanced"

# ============================================================
# GRADE 5 QUESTION GENERATORS
# ============================================================

def g5_ch1_large_numbers(qnum):
    """Chapter 1: Large Numbers"""
    questions = []
    variants = [
        lambda i: _g5_place_value(i),
        lambda i: _g5_number_names(i),
        lambda i: _g5_rounding(i),
        lambda i: _g5_comparison(i),
    ]
    for i in range(qnum):
        q = variants[i % len(variants)](i)
        questions.append(q)
    return questions

def _g5_place_value(i):
    num = random.randint(10_00_000, 9_99_99_999)
    num_str = f"{num:,}"
    places = ["ones", "tens", "hundreds", "thousands", "ten-thousands", "lakhs", "ten-lakhs", "crores"]
    s = str(num)
    digit_pos = random.randint(4, min(7, len(s)-1))
    digit = int(s[-(digit_pos+1)])
    place_name = places[digit_pos]
    place_value = digit * (10 ** digit_pos)

    wrong = [place_value * 10, digit, place_value // 10]
    choices = [str(place_value)] + [str(w) for w in wrong]
    random.shuffle(choices)
    correct = choices.index(str(place_value))

    diff = 20 + i * 2

    return {
        "stem": f"In the number {num_str}, what is the place value of the digit {digit} in the {place_name} place?",
        "choices": choices,
        "correct_answer": correct,
        "difficulty_score": min(diff, 100),
        "tags": ["large-numbers", "place-value"],
        "topic": "ncert_g5_large_numbers",
        "chapter": "Ch1: Large Numbers",
        "hint": {
            "level_0": "Think about what each place represents in the Indian number system.",
            "level_1": f"The {place_name} place means the digit is multiplied by {10**digit_pos}.",
            "level_2": f"{digit} × {10**digit_pos} = {place_value}"
        },
        "curriculum_tags": ["NCERT_5_1"],
        "visual": False,
        "visual_alt": None,
        "diagnostics": {"1": "Confused face value with place value", "2": "Wrong place identification", "3": "Multiplication error"}
    }

def _g5_number_names(i):
    num = random.randint(10_00_000, 99_99_999)
    def indian_words(n):
        if n < 100: return str(n)
        cr = n // 10000000
        rem = n % 10000000
        lk = rem // 100000
        rem2 = rem % 100000
        th = rem2 // 1000
        h = (rem2 % 1000) // 100
        rest = rem2 % 100
        parts = []
        if cr: parts.append(f"{cr} crore")
        if lk: parts.append(f"{lk} lakh")
        if th: parts.append(f"{th} thousand")
        if h: parts.append(f"{h} hundred")
        if rest: parts.append(str(rest))
        return " ".join(parts)

    correct_name = indian_words(num)
    wrong1 = indian_words(num + 100000)
    wrong2 = indian_words(num - 100000 if num > 100000 else num + 200000)
    wrong3 = indian_words(num * 10)

    choices = [correct_name, wrong1, wrong2, wrong3]
    random.shuffle(choices)
    correct_idx = choices.index(correct_name)

    num_formatted = format(num, ',')
    diff = 25
    return {
        "stem": f"Write the number name for {num_formatted} in the Indian system.",
        "choices": choices,
        "correct_answer": correct_idx,
        "difficulty_score": diff,
        "tags": ["large-numbers", "number-names"],
        "topic": "ncert_g5_large_numbers",
        "chapter": "Ch1: Large Numbers",
        "hint": {
            "level_0": "Use the Indian place value chart: ones, tens, hundreds, thousands, ten-thousands, lakhs, ten-lakhs, crores.",
            "level_1": "Start from the left and read each period separately.",
            "level_2": f"The number is {correct_name}."
        },
        "curriculum_tags": ["NCERT_5_1"],
        "visual": False,
        "visual_alt": None,
        "diagnostics": {"1": "Confused lakh and thousand", "2": "Misread digit groups", "3": "Mixed Indian/International system"}
    }

def _g5_rounding(i):
    num = random.randint(1000, 99999)
    round_to = random.choice([10, 100, 1000])
    rounded = round(num / round_to) * round_to

    wrong = [rounded + round_to, rounded - round_to, num]
    choices = [str(rounded)] + [str(w) for w in wrong if w != rounded]
    choices = choices[:4]
    while len(choices) < 4:
        choices.append(str(rounded + round_to * 2))
    random.shuffle(choices)
    correct_idx = choices.index(str(rounded))

    return {
        "stem": f"Round {num:,} to the nearest {round_to}.",
        "choices": choices,
        "correct_answer": correct_idx,
        "difficulty_score": 30,
        "tags": ["large-numbers", "rounding"],
        "topic": "ncert_g5_large_numbers",
        "chapter": "Ch1: Large Numbers",
        "hint": {
            "level_0": f"Look at the digit in the {round_to}s place and the digit to its right.",
            "level_1": "If the digit to the right is 5 or more, round up. Otherwise, round down.",
            "level_2": f"{num} rounded to the nearest {round_to} is {rounded}."
        },
        "curriculum_tags": ["NCERT_5_1"],
        "visual": False,
        "visual_alt": None,
        "diagnostics": {"1": "Rounded in wrong direction", "2": "Looked at wrong digit", "3": "Did not change digits after rounding"}
    }

def _g5_comparison(i):
    a = random.randint(10_00_000, 99_99_999)
    b = a + random.choice([-random.randint(1000, 100000), random.randint(1000, 100000)])
    if b < 0: b = a + 50000

    if a > b:
        correct = f"{a:,} > {b:,}"
        wrong = [f"{a:,} < {b:,}", f"{a:,} = {b:,}", f"{b:,} > {a:,}"]
    else:
        correct = f"{a:,} < {b:,}"
        wrong = [f"{a:,} > {b:,}", f"{a:,} = {b:,}", f"{b:,} < {a:,}"]

    choices = [correct] + wrong
    random.shuffle(choices)
    correct_idx = choices.index(correct)

    return {
        "stem": f"Compare the numbers {a:,} and {b:,}. Choose the correct statement.",
        "choices": choices,
        "correct_answer": correct_idx,
        "difficulty_score": 20,
        "tags": ["large-numbers", "comparison"],
        "topic": "ncert_g5_large_numbers",
        "chapter": "Ch1: Large Numbers",
        "hint": {
            "level_0": "Compare the numbers starting from the leftmost digit.",
            "level_1": "Count the digits first. If equal digits, compare from left to right.",
            "level_2": f"{'>' if a > b else '<'} because the leftmost differing digit decides."
        },
        "curriculum_tags": ["NCERT_5_1"],
        "visual": False,
        "visual_alt": None,
        "diagnostics": {"1": "Confused > and <", "2": "Compared from right to left", "3": "Miscounted digits"}
    }

def g5_ch2_factors_multiples(qnum):
    """Chapter 2: Factors & Multiples"""
    questions = []
    for i in range(qnum):
        variant = i % 5
        if variant == 0:
            # Prime factorization
            num = random.choice([24, 36, 48, 56, 60, 72, 84, 90, 96, 100, 108, 120, 132, 144, 150])
            def prime_factors(n):
                factors = []
                d = 2
                while d * d <= n:
                    while n % d == 0:
                        factors.append(d)
                        n //= d
                    d += 1
                if n > 1:
                    factors.append(n)
                return factors
            pf = prime_factors(num)
            correct = " × ".join(map(str, pf))
            wrong_options = []
            wrong_options.append(" × ".join(map(str, prime_factors(num + 2))))
            wrong_options.append(" × ".join(map(str, pf[:-1] + [pf[-1] + 1])))
            wrong_options.append(" × ".join(map(str, [2] + pf)))
            choices = [correct] + wrong_options[:3]
            random.shuffle(choices)
            questions.append({
                "stem": f"Find the prime factorization of {num}.",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 40,
                "tags": ["factors-multiples", "prime-factorization"],
                "topic": "ncert_g5_factors_multiples",
                "chapter": "Ch2: Factors & Multiples",
                "hint": {"level_0": "Divide by the smallest prime number repeatedly.", "level_1": f"Start: {num} ÷ 2 = {num//2 if num%2==0 else '?'}", "level_2": f"{num} = {correct}"},
                "curriculum_tags": ["NCERT_5_2"],
                "visual": True,
                "visual_alt": f"Factor tree for {num}",
                "diagnostics": {"1": "Incomplete factorization", "2": "Used non-prime factor", "3": "Arithmetic error"}
            })
        elif variant == 1:
            # LCM
            a, b = random.choice([(4,6),(6,8),(8,12),(9,12),(10,15),(12,18),(15,20),(6,9),(8,10),(12,16)])
            lcm_val = (a * b) // math.gcd(a, b)
            wrong = [a * b, lcm_val + a, lcm_val - b if lcm_val > b else lcm_val + b]
            choices = [str(lcm_val)] + [str(w) for w in wrong]
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name} has two alarm clocks. One rings every {a} minutes and the other every {b} minutes. If both ring together now, after how many minutes will they ring together again?",
                "choices": choices,
                "correct_answer": choices.index(str(lcm_val)),
                "difficulty_score": 45,
                "tags": ["factors-multiples", "lcm"],
                "topic": "ncert_g5_factors_multiples",
                "chapter": "Ch2: Factors & Multiples",
                "hint": {"level_0": "Find the LCM of the two numbers.", "level_1": f"List multiples of {a} and {b} until you find a common one.", "level_2": f"LCM({a}, {b}) = {lcm_val}"},
                "curriculum_tags": ["NCERT_5_2"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Found HCF instead of LCM", "2": "Multiplied the numbers", "3": "Listed multiples incorrectly"}
            })
        elif variant == 2:
            # HCF
            a, b = random.choice([(12,18),(16,24),(20,30),(24,36),(18,27),(15,25),(28,42),(30,45),(36,48),(21,35)])
            hcf_val = math.gcd(a, b)
            wrong = [hcf_val * 2, hcf_val + 1, min(a, b)]
            choices = [str(hcf_val)] + [str(w) for w in wrong]
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name} has {a} red beads and {b} blue beads. She wants to make necklaces with equal numbers of each colour in every necklace. What is the maximum number of necklaces she can make?",
                "choices": choices,
                "correct_answer": choices.index(str(hcf_val)),
                "difficulty_score": 50,
                "tags": ["factors-multiples", "hcf"],
                "topic": "ncert_g5_factors_multiples",
                "chapter": "Ch2: Factors & Multiples",
                "hint": {"level_0": "Find the HCF of the two numbers.", "level_1": f"Factors of {a}: list them. Factors of {b}: list them. Find the greatest common one.", "level_2": f"HCF({a}, {b}) = {hcf_val}"},
                "curriculum_tags": ["NCERT_5_2"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Found LCM instead of HCF", "2": "Divided the numbers", "3": "Found a common factor but not the greatest"}
            })
        elif variant == 3:
            # Divisibility rules
            rules = [(2, "even number (last digit 0,2,4,6,8)"), (3, "sum of digits divisible by 3"),
                     (5, "last digit 0 or 5"), (9, "sum of digits divisible by 9"), (4, "last two digits divisible by 4")]
            div, rule_text = random.choice(rules)
            num = random.randint(100, 9999)
            # Ensure one choice is divisible
            if num % div != 0:
                num = num + (div - num % div)
            wrong_nums = [num + 1, num + 3, num - 1]
            wrong_nums = [w for w in wrong_nums if w % div != 0][:3]
            choices = [str(num)] + [str(w) for w in wrong_nums]
            while len(choices) < 4:
                choices.append(str(num + div + len(choices)))
            choices = choices[:4]
            random.shuffle(choices)
            questions.append({
                "stem": f"Which of the following numbers is divisible by {div}?",
                "choices": choices,
                "correct_answer": choices.index(str(num)),
                "difficulty_score": 30,
                "tags": ["factors-multiples", "divisibility"],
                "topic": "ncert_g5_factors_multiples",
                "chapter": "Ch2: Factors & Multiples",
                "hint": {"level_0": f"Use the divisibility rule for {div}.", "level_1": f"Rule: A number is divisible by {div} if {rule_text}.", "level_2": f"{num} is divisible by {div}."},
                "curriculum_tags": ["NCERT_5_2"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Applied wrong divisibility rule", "2": "Calculation error in digit sum", "3": "Confused divisible with factor"}
            })
        else:
            # Identify primes
            num = random.randint(20, 100)
            primes_list = [p for p in range(2, 101) if all(p % d != 0 for d in range(2, int(p**0.5)+1))]
            composites = [c for c in range(20, 101) if c not in primes_list]
            prime = random.choice([p for p in primes_list if p > 20])
            comp_choices = random.sample([c for c in composites if c != prime], 3)
            choices = [str(prime)] + [str(c) for c in comp_choices]
            random.shuffle(choices)
            questions.append({
                "stem": "Which of the following is a prime number?",
                "choices": choices,
                "correct_answer": choices.index(str(prime)),
                "difficulty_score": 35,
                "tags": ["factors-multiples", "prime-numbers"],
                "topic": "ncert_g5_factors_multiples",
                "chapter": "Ch2: Factors & Multiples",
                "hint": {"level_0": "A prime number has exactly 2 factors: 1 and itself.", "level_1": "Check if the number is divisible by 2, 3, 5, 7...", "level_2": f"{prime} is prime because it has no factors other than 1 and {prime}."},
                "curriculum_tags": ["NCERT_5_2"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Confused prime and odd", "2": "Missed a factor", "3": "Thought 1 is prime"}
            })
    return questions

def g5_ch3_fractions(qnum):
    """Chapter 3: Fractions"""
    questions = []
    for i in range(qnum):
        variant = i % 4
        if variant == 0:
            # Addition of unlike fractions
            d1, d2 = random.choice([(3,4),(4,5),(3,5),(2,3),(5,6),(4,7),(3,8),(6,7)])
            n1 = random.randint(1, d1-1)
            n2 = random.randint(1, d2-1)
            lcd = (d1 * d2) // math.gcd(d1, d2)
            sum_num = n1 * (lcd // d1) + n2 * (lcd // d2)
            g = math.gcd(sum_num, lcd)
            ans_n, ans_d = sum_num // g, lcd // g
            if ans_n > ans_d:
                whole = ans_n // ans_d
                rem = ans_n % ans_d
                correct = f"{whole} {rem}/{ans_d}" if rem else str(whole)
            else:
                correct = f"{ans_n}/{ans_d}"
            wrong1 = f"{n1+n2}/{d1+d2}"
            wrong2 = f"{n1+n2}/{max(d1,d2)}"
            wrong3 = f"{sum_num}/{lcd}"
            choices = list(set([correct, wrong1, wrong2, wrong3]))[:4]
            while len(choices) < 4:
                choices.append(f"{ans_n+1}/{ans_d}")
            random.shuffle(choices)
            name = random.choice(NAMES)
            food = random.choice(FOODS)
            questions.append({
                "stem": f"{name} ate {n1}/{d1} of a plate of {food} in the morning and {n2}/{d2} in the evening. How much did {name} eat in total?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 45,
                "tags": ["fractions", "addition"],
                "topic": "ncert_g5_fractions",
                "chapter": "Ch3: Fractions",
                "hint": {"level_0": "Find a common denominator first.", "level_1": f"LCD of {d1} and {d2} is {lcd}.", "level_2": f"{n1}/{d1} + {n2}/{d2} = {n1*(lcd//d1)}/{lcd} + {n2*(lcd//d2)}/{lcd} = {correct}"},
                "curriculum_tags": ["NCERT_5_3"],
                "visual": True,
                "visual_alt": f"Fraction addition: {n1}/{d1} + {n2}/{d2}",
                "diagnostics": {"1": "Added numerators and denominators separately", "2": "Did not find LCD", "3": "Did not simplify"}
            })
        elif variant == 1:
            # Subtraction
            d = random.choice([4, 5, 6, 8, 10, 12])
            n1 = random.randint(d//2 + 1, d - 1)
            n2 = random.randint(1, n1 - 1)
            diff_n = n1 - n2
            g = math.gcd(diff_n, d)
            ans = f"{diff_n//g}/{d//g}"
            wrong = [f"{n1-n2}/{d*2}", f"{n1+n2}/{d}", f"{n2}/{d}"]
            choices = [ans] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"A water tank is {n1}/{d} full. After using some water, it is {n2}/{d} full. What fraction of water was used?",
                "choices": choices,
                "correct_answer": choices.index(ans),
                "difficulty_score": 35,
                "tags": ["fractions", "subtraction"],
                "topic": "ncert_g5_fractions",
                "chapter": "Ch3: Fractions",
                "hint": {"level_0": "Subtract the two fractions.", "level_1": f"{n1}/{d} - {n2}/{d} = ?", "level_2": f"{n1}/{d} - {n2}/{d} = {ans}"},
                "curriculum_tags": ["NCERT_5_3"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Added instead of subtracted", "2": "Subtracted denominators too", "3": "Did not simplify"}
            })
        elif variant == 2:
            # Comparison
            d1, d2 = random.choice([(3,5),(4,7),(5,8),(3,7),(4,9),(5,6)])
            n1 = random.randint(1, d1-1)
            n2 = random.randint(1, d2-1)
            val1 = n1/d1
            val2 = n2/d2
            if val1 > val2:
                correct = f"{n1}/{d1} > {n2}/{d2}"
            elif val1 < val2:
                correct = f"{n1}/{d1} < {n2}/{d2}"
            else:
                correct = f"{n1}/{d1} = {n2}/{d2}"
            wrong_opts = [f"{n1}/{d1} > {n2}/{d2}", f"{n1}/{d1} < {n2}/{d2}", f"{n1}/{d1} = {n2}/{d2}"]
            wrong_opts = [w for w in wrong_opts if w != correct]
            choices = [correct] + wrong_opts[:3]
            while len(choices) < 4:
                choices.append(f"{n2}/{d2} = {n1}/{d1}")
            random.shuffle(choices)
            questions.append({
                "stem": f"Compare {n1}/{d1} and {n2}/{d2}. Which statement is correct?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 40,
                "tags": ["fractions", "comparison"],
                "topic": "ncert_g5_fractions",
                "chapter": "Ch3: Fractions",
                "hint": {"level_0": "Convert to like fractions or compare cross-products.", "level_1": f"Cross multiply: {n1}×{d2} vs {n2}×{d1}", "level_2": f"{n1*d2} vs {n2*d1}, so {correct}"},
                "curriculum_tags": ["NCERT_5_3"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Compared numerators only", "2": "Compared denominators only", "3": "Cross-multiplication error"}
            })
        else:
            # Mixed number to improper
            whole = random.randint(1, 5)
            d = random.choice([3, 4, 5, 6, 7, 8])
            n = random.randint(1, d-1)
            improper_n = whole * d + n
            correct = f"{improper_n}/{d}"
            wrong = [f"{whole*n}/{d}", f"{whole+n}/{d}", f"{improper_n}/{d+1}"]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Convert {whole} {n}/{d} to an improper fraction.",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 30,
                "tags": ["fractions", "mixed-numbers"],
                "topic": "ncert_g5_fractions",
                "chapter": "Ch3: Fractions",
                "hint": {"level_0": "Multiply whole number by denominator, then add numerator.", "level_1": f"{whole} × {d} + {n} = ?", "level_2": f"{whole} × {d} + {n} = {improper_n}, so {correct}"},
                "curriculum_tags": ["NCERT_5_3"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Multiplied whole by numerator", "2": "Added whole and numerator only", "3": "Changed denominator"}
            })
    return questions

def g5_ch4_decimals(qnum):
    """Chapter 4: Decimals"""
    questions = []
    for i in range(qnum):
        variant = i % 4
        if variant == 0:
            # Addition
            a = round(random.uniform(1, 50), 2)
            b = round(random.uniform(1, 50), 2)
            correct = round(a + b, 2)
            wrong = [round(correct + 0.1, 2), round(a + b * 10, 2), round(correct - 1, 2)]
            choices = [str(correct)] + [str(w) for w in wrong]
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name} bought a notebook for ₹{a} and a pen for ₹{b}. How much did {name} spend in total?",
                "choices": choices,
                "correct_answer": choices.index(str(correct)),
                "difficulty_score": 30,
                "tags": ["decimals", "addition"],
                "topic": "ncert_g5_decimals",
                "chapter": "Ch4: Decimals",
                "hint": {"level_0": "Line up the decimal points and add.", "level_1": f"₹{a} + ₹{b} = ?", "level_2": f"₹{a} + ₹{b} = ₹{correct}"},
                "curriculum_tags": ["NCERT_5_4"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Misaligned decimal points", "2": "Forgot to carry", "3": "Added digits without aligning"}
            })
        elif variant == 1:
            # Multiplication by whole number
            dec = round(random.uniform(0.5, 9.9), 1)
            mult = random.randint(2, 9)
            correct = round(dec * mult, 1)
            wrong = [round(correct * 10, 1), round(dec + mult, 1), round(correct + dec, 1)]
            choices = [str(correct)] + [str(w) for w in wrong]
            random.shuffle(choices)
            food = random.choice(FOODS)
            questions.append({
                "stem": f"One {food} costs ₹{dec}. How much do {mult} of them cost?",
                "choices": choices,
                "correct_answer": choices.index(str(correct)),
                "difficulty_score": 40,
                "tags": ["decimals", "multiplication"],
                "topic": "ncert_g5_decimals",
                "chapter": "Ch4: Decimals",
                "hint": {"level_0": "Multiply the decimal by the whole number.", "level_1": f"₹{dec} × {mult} = ?", "level_2": f"₹{dec} × {mult} = ₹{correct}"},
                "curriculum_tags": ["NCERT_5_4"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Decimal point placed wrongly", "2": "Multiplication error", "3": "Added instead of multiplied"}
            })
        elif variant == 2:
            # Decimal to fraction
            dec_val = random.choice([0.25, 0.5, 0.75, 0.2, 0.4, 0.6, 0.8, 0.125, 0.375])
            from fractions import Fraction
            frac = Fraction(dec_val).limit_denominator(1000)
            correct = f"{frac.numerator}/{frac.denominator}"
            wrong = [f"{int(dec_val*100)}/10", f"{int(dec_val*10)}/100", f"{frac.numerator+1}/{frac.denominator}"]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Convert {dec_val} to a fraction in its simplest form.",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 35,
                "tags": ["decimals", "conversion"],
                "topic": "ncert_g5_decimals",
                "chapter": "Ch4: Decimals",
                "hint": {"level_0": "Write the decimal as a fraction over 10 or 100, then simplify.", "level_1": f"{dec_val} = {int(dec_val*1000)}/1000 or simpler?", "level_2": f"{dec_val} = {correct}"},
                "curriculum_tags": ["NCERT_5_4"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Did not simplify", "2": "Wrong denominator", "3": "Numerator error"}
            })
        else:
            # Subtraction
            a = round(random.uniform(10, 100), 2)
            b = round(random.uniform(1, a - 1), 2)
            correct = round(a - b, 2)
            wrong = [round(a + b, 2), round(correct + 1, 2), round(b - a + 100, 2)]
            choices = [str(correct)] + [str(w) for w in wrong]
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name} had ₹{a}. After buying a snack, {name} has ₹{b} left. How much did the snack cost?",
                "choices": choices,
                "correct_answer": choices.index(str(correct)),
                "difficulty_score": 30,
                "tags": ["decimals", "subtraction"],
                "topic": "ncert_g5_decimals",
                "chapter": "Ch4: Decimals",
                "hint": {"level_0": "Subtract to find the cost.", "level_1": f"₹{a} - ₹{b} = ?", "level_2": f"₹{a} - ₹{b} = ₹{correct}"},
                "curriculum_tags": ["NCERT_5_4"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Added instead of subtracted", "2": "Decimal alignment error", "3": "Borrowing error"}
            })
    return questions

def g5_ch5_measurement(qnum):
    """Chapter 5: Measurement"""
    questions = []
    for i in range(qnum):
        variant = i % 4
        if variant == 0:
            # Length conversion
            km = random.randint(1, 20)
            m = random.randint(100, 900)
            total_m = km * 1000 + m
            correct = str(total_m)
            wrong = [str(km * 100 + m), str(km * 10000 + m), str(km + m)]
            choices = [correct] + wrong
            random.shuffle(choices)
            city1, city2 = random.sample(CITIES, 2)
            questions.append({
                "stem": f"The distance from {city1} station to a village is {km} km {m} m. Express this distance in metres.",
                "choices": [c + " m" for c in choices],
                "correct_answer": [c + " m" for c in choices].index(correct + " m"),
                "difficulty_score": 25,
                "tags": ["measurement", "length-conversion"],
                "topic": "ncert_g5_measurement",
                "chapter": "Ch5: Measurement",
                "hint": {"level_0": "1 km = 1000 m", "level_1": f"{km} km = {km * 1000} m, then add {m} m", "level_2": f"{km} × 1000 + {m} = {total_m} m"},
                "curriculum_tags": ["NCERT_5_5"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Used 100 instead of 1000", "2": "Forgot to add remaining metres", "3": "Multiplied by 10000"}
            })
        elif variant == 1:
            # Weight conversion
            kg = random.randint(1, 10)
            g = random.randint(100, 900)
            total_g = kg * 1000 + g
            correct = str(total_g)
            wrong = [str(kg * 100 + g), str(kg + g), str(total_g + 1000)]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            food = random.choice(["rice", "wheat", "sugar", "dal"])
            questions.append({
                "stem": f"{name}'s mother bought {kg} kg {g} g of {food}. How many grams is that in total?",
                "choices": [c + " g" for c in choices],
                "correct_answer": [c + " g" for c in choices].index(correct + " g"),
                "difficulty_score": 25,
                "tags": ["measurement", "weight-conversion"],
                "topic": "ncert_g5_measurement",
                "chapter": "Ch5: Measurement",
                "hint": {"level_0": "1 kg = 1000 g", "level_1": f"{kg} kg = {kg*1000} g", "level_2": f"{kg*1000} + {g} = {total_g} g"},
                "curriculum_tags": ["NCERT_5_5"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Used wrong conversion factor", "2": "Forgot to add grams", "3": "Subtracted instead of added"}
            })
        elif variant == 2:
            # Perimeter of rectangle
            l = random.randint(5, 30)
            w = random.randint(3, l - 1)
            perimeter = 2 * (l + w)
            correct = str(perimeter)
            wrong = [str(l * w), str(l + w), str(4 * l)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"A rectangular garden has length {l} m and width {w} m. What is its perimeter?",
                "choices": [c + " m" for c in choices],
                "correct_answer": [c + " m" for c in choices].index(correct + " m"),
                "difficulty_score": 30,
                "tags": ["measurement", "perimeter"],
                "topic": "ncert_g5_measurement",
                "chapter": "Ch5: Measurement",
                "hint": {"level_0": "Perimeter = 2 × (length + width)", "level_1": f"P = 2 × ({l} + {w})", "level_2": f"P = 2 × {l+w} = {perimeter} m"},
                "curriculum_tags": ["NCERT_5_5"],
                "visual": True,
                "visual_alt": f"Rectangle with length {l} m and width {w} m",
                "diagnostics": {"1": "Calculated area instead", "2": "Added only once (l+w)", "3": "Multiplied l×w"}
            })
        else:
            # Area of rectangle
            l = random.randint(5, 20)
            w = random.randint(3, 15)
            area = l * w
            correct = str(area)
            wrong = [str(2*(l+w)), str(l+w), str(area + l)]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name} wants to tile a floor that is {l} m long and {w} m wide. What is the area of the floor?",
                "choices": [c + " sq m" for c in choices],
                "correct_answer": [c + " sq m" for c in choices].index(correct + " sq m"),
                "difficulty_score": 30,
                "tags": ["measurement", "area"],
                "topic": "ncert_g5_measurement",
                "chapter": "Ch5: Measurement",
                "hint": {"level_0": "Area of rectangle = length × width", "level_1": f"A = {l} × {w}", "level_2": f"A = {area} sq m"},
                "curriculum_tags": ["NCERT_5_5"],
                "visual": True,
                "visual_alt": f"Rectangle with length {l}m and width {w}m showing grid",
                "diagnostics": {"1": "Calculated perimeter instead", "2": "Added dimensions", "3": "Forgot units"}
            })
    return questions

def g5_ch6_percentage(qnum):
    """Chapter 6: Percentage"""
    questions = []
    for i in range(qnum):
        variant = i % 4
        if variant == 0:
            # Fraction to percentage
            n, d = random.choice([(1,4),(1,2),(3,4),(1,5),(2,5),(3,5),(1,8),(3,8),(1,10),(3,10)])
            pct = (n/d) * 100
            correct = f"{int(pct)}%" if pct == int(pct) else f"{pct}%"
            wrong = [f"{int(pct/2)}%", f"{int(pct*2)}%", f"{n*d}%"]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Convert {n}/{d} to a percentage.",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 30,
                "tags": ["percentage", "conversion"],
                "topic": "ncert_g5_percentage",
                "chapter": "Ch6: Percentage",
                "hint": {"level_0": "Multiply the fraction by 100.", "level_1": f"({n}/{d}) × 100 = ?", "level_2": f"({n}/{d}) × 100 = {correct}"},
                "curriculum_tags": ["NCERT_5_6"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Divided instead of multiplied by 100", "2": "Forgot to multiply by 100", "3": "Calculation error"}
            })
        elif variant == 1:
            # Percentage of a number
            total = random.choice([50, 80, 100, 120, 150, 200, 250, 300, 400, 500])
            pct = random.choice([10, 20, 25, 30, 40, 50, 60, 75])
            answer = int(total * pct / 100)
            wrong = [total - answer, answer * 2, total + answer]
            choices = [str(answer)] + [str(w) for w in wrong]
            random.shuffle(choices)
            name = random.choice(NAMES)
            sport = random.choice(SPORTS)
            questions.append({
                "stem": f"In a school of {total} students, {pct}% play {sport}. How many students play {sport}?",
                "choices": choices,
                "correct_answer": choices.index(str(answer)),
                "difficulty_score": 40,
                "tags": ["percentage", "of-a-number"],
                "topic": "ncert_g5_percentage",
                "chapter": "Ch6: Percentage",
                "hint": {"level_0": f"Find {pct}% of {total}.", "level_1": f"{pct}/100 × {total} = ?", "level_2": f"{pct}/100 × {total} = {answer}"},
                "curriculum_tags": ["NCERT_5_6"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Divided by percentage", "2": "Used wrong formula", "3": "Arithmetic error"}
            })
        elif variant == 2:
            # Decimal to percentage
            dec = random.choice([0.15, 0.25, 0.3, 0.45, 0.5, 0.6, 0.72, 0.8, 0.05, 0.9])
            pct = int(dec * 100)
            correct = f"{pct}%"
            wrong = [f"{pct//10}%", f"{pct*10}%", f"{pct+5}%"]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Convert {dec} to a percentage.",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 25,
                "tags": ["percentage", "decimal-conversion"],
                "topic": "ncert_g5_percentage",
                "chapter": "Ch6: Percentage",
                "hint": {"level_0": "Multiply by 100 to convert decimal to percentage.", "level_1": f"{dec} × 100 = ?", "level_2": f"{dec} × 100 = {pct}%"},
                "curriculum_tags": ["NCERT_5_6"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Divided by 100", "2": "Moved decimal wrong direction", "3": "Forgot % sign"}
            })
        else:
            # Word problem
            total = random.choice([40, 50, 60, 80, 100])
            part = random.randint(total // 5, total * 4 // 5)
            pct = (part / total) * 100
            correct = f"{int(pct)}%" if pct == int(pct) else f"{pct:.1f}%"
            wrong = [f"{int(100-pct)}%", f"{part}%", f"{total-part}%"]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name} scored {part} out of {total} in a test. What is the percentage score?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 40,
                "tags": ["percentage", "word-problem"],
                "topic": "ncert_g5_percentage",
                "chapter": "Ch6: Percentage",
                "hint": {"level_0": "Percentage = (part/total) × 100", "level_1": f"({part}/{total}) × 100 = ?", "level_2": f"({part}/{total}) × 100 = {correct}"},
                "curriculum_tags": ["NCERT_5_6"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Divided total by part", "2": "Forgot to multiply by 100", "3": "Subtraction error"}
            })
    return questions

def g5_ch7_geometry(qnum):
    """Chapter 7: Geometry"""
    questions = []
    for i in range(qnum):
        variant = i % 4
        if variant == 0:
            # Angle types
            angle = random.randint(1, 179)
            if angle < 90:
                correct = "Acute angle"
            elif angle == 90:
                correct = "Right angle"
            else:
                correct = "Obtuse angle"
            choices = ["Acute angle", "Right angle", "Obtuse angle", "Straight angle"]
            random.shuffle(choices)
            questions.append({
                "stem": f"An angle measuring {angle}° is called a:",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 20,
                "tags": ["geometry", "angles"],
                "topic": "ncert_g5_geometry",
                "chapter": "Ch7: Geometry",
                "hint": {"level_0": "Acute < 90°, Right = 90°, Obtuse > 90° and < 180°", "level_1": f"Is {angle}° less than, equal to, or greater than 90°?", "level_2": f"{angle}° is {correct.lower()}."},
                "curriculum_tags": ["NCERT_5_7"],
                "visual": True,
                "visual_alt": f"An angle of {angle} degrees",
                "diagnostics": {"1": "Confused acute and obtuse", "2": "Thought all angles > 45 are obtuse", "3": "Did not check against 90"}
            })
        elif variant == 1:
            # Triangle angles
            a1 = random.randint(30, 80)
            a2 = random.randint(30, 140 - a1)
            a3 = 180 - a1 - a2
            correct = str(a3)
            wrong = [str(a3 + 10), str(180 - a1), str(a1 + a2)]
            choices = [correct + "°"] + [w + "°" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"Two angles of a triangle are {a1}° and {a2}°. What is the third angle?",
                "choices": choices,
                "correct_answer": choices.index(correct + "°"),
                "difficulty_score": 35,
                "tags": ["geometry", "triangles"],
                "topic": "ncert_g5_geometry",
                "chapter": "Ch7: Geometry",
                "hint": {"level_0": "Sum of angles in a triangle = 180°", "level_1": f"Third angle = 180° - {a1}° - {a2}°", "level_2": f"180 - {a1} - {a2} = {a3}°"},
                "curriculum_tags": ["NCERT_5_7"],
                "visual": True,
                "visual_alt": f"Triangle with angles {a1}°, {a2}°, and ?",
                "diagnostics": {"1": "Used 360 instead of 180", "2": "Subtracted only one angle", "3": "Added all three"}
            })
        elif variant == 2:
            # Types of lines
            correct_pair = random.choice([
                ("Parallel lines", "Lines that never meet and are always the same distance apart"),
                ("Perpendicular lines", "Lines that meet at a right angle (90°)"),
                ("Intersecting lines", "Lines that cross each other at a point"),
            ])
            all_types = ["Parallel lines", "Perpendicular lines", "Intersecting lines", "Curved lines"]
            choices = all_types[:]
            random.shuffle(choices)
            questions.append({
                "stem": f"Which term describes: {correct_pair[1]}?",
                "choices": choices,
                "correct_answer": choices.index(correct_pair[0]),
                "difficulty_score": 20,
                "tags": ["geometry", "lines"],
                "topic": "ncert_g5_geometry",
                "chapter": "Ch7: Geometry",
                "hint": {"level_0": "Think about how the lines relate to each other.", "level_1": correct_pair[1], "level_2": f"The answer is {correct_pair[0]}."},
                "curriculum_tags": ["NCERT_5_7"],
                "visual": True,
                "visual_alt": f"Diagram showing {correct_pair[0].lower()}",
                "diagnostics": {"1": "Confused parallel and perpendicular", "2": "Mixed up definitions", "3": "Did not visualize correctly"}
            })
        else:
            # Complementary/supplementary
            angle = random.randint(20, 80)
            comp_type = random.choice(["complementary", "supplementary"])
            if comp_type == "complementary":
                answer = 90 - angle
                total = 90
            else:
                answer = 180 - angle
                total = 180
            correct = str(answer)
            wrong = [str(total - answer + 10), str(angle), str(total)]
            choices = [correct + "°"] + [w + "°" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"Find the {comp_type} angle of {angle}°.",
                "choices": choices,
                "correct_answer": choices.index(correct + "°"),
                "difficulty_score": 35,
                "tags": ["geometry", "angle-pairs"],
                "topic": "ncert_g5_geometry",
                "chapter": "Ch7: Geometry",
                "hint": {"level_0": f"{'Complementary angles add up to 90°' if comp_type=='complementary' else 'Supplementary angles add up to 180°'}", "level_1": f"{total}° - {angle}° = ?", "level_2": f"{total} - {angle} = {answer}°"},
                "curriculum_tags": ["NCERT_5_7"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Used wrong total (90 vs 180)", "2": "Added instead of subtracted", "3": "Confused complementary and supplementary"}
            })
    return questions

def g5_ch8_perimeter_area(qnum):
    """Chapter 8: Perimeter & Area"""
    questions = []
    for i in range(qnum):
        variant = i % 3
        if variant == 0:
            # Area of triangle
            base = random.randint(4, 20)
            height = random.randint(3, 15)
            area = base * height / 2
            correct = str(int(area)) if area == int(area) else str(area)
            wrong = [str(base * height), str(base + height), str(int(area) + base)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Find the area of a triangle with base {base} cm and height {height} cm.",
                "choices": [c + " sq cm" for c in choices],
                "correct_answer": [c + " sq cm" for c in choices].index(correct + " sq cm"),
                "difficulty_score": 40,
                "tags": ["area", "triangle"],
                "topic": "ncert_g5_perimeter_area",
                "chapter": "Ch8: Perimeter & Area",
                "hint": {"level_0": "Area of triangle = ½ × base × height", "level_1": f"½ × {base} × {height} = ?", "level_2": f"½ × {base} × {height} = {correct} sq cm"},
                "curriculum_tags": ["NCERT_5_8"],
                "visual": True,
                "visual_alt": f"Triangle with base {base} cm and height {height} cm",
                "diagnostics": {"1": "Forgot to divide by 2", "2": "Added base and height", "3": "Multiplied by 2 instead of dividing"}
            })
        elif variant == 1:
            # Perimeter of irregular shape (L-shape)
            a = random.randint(3, 8)
            b = random.randint(3, 8)
            c = random.randint(2, a-1)
            d = random.randint(2, b-1)
            perimeter = 2*a + 2*b
            correct = str(perimeter)
            wrong = [str(a*b), str(perimeter + a), str(a+b+c+d)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"An L-shaped room has outer dimensions {a} m × {b} m with a rectangular piece of {c} m × {d} m cut from one corner. What is the perimeter of the room?",
                "choices": [c + " m" for c in choices],
                "correct_answer": [c + " m" for c in choices].index(correct + " m"),
                "difficulty_score": 55,
                "tags": ["perimeter", "irregular-shapes"],
                "topic": "ncert_g5_perimeter_area",
                "chapter": "Ch8: Perimeter & Area",
                "hint": {"level_0": "The perimeter of an L-shape with a corner cut is the same as the rectangle's perimeter!", "level_1": "The cut adds two sides but removes two equal sides.", "level_2": f"Perimeter = 2×({a}+{b}) = {perimeter} m"},
                "curriculum_tags": ["NCERT_5_8"],
                "visual": True,
                "visual_alt": f"L-shaped figure with dimensions marked",
                "diagnostics": {"1": "Calculated area instead", "2": "Added all given numbers", "3": "Thought perimeter changes with cut"}
            })
        else:
            # Area of composite shape
            l1 = random.randint(4, 10)
            w1 = random.randint(3, 8)
            l2 = random.randint(2, 5)
            w2 = random.randint(2, 4)
            area = l1 * w1 + l2 * w2
            correct = str(area)
            wrong = [str(l1*w1), str((l1+l2)*(w1+w2)), str(area - l2*w2 + l2+w2)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"A figure is made of two rectangles: one is {l1} cm × {w1} cm and the other is {l2} cm × {w2} cm. What is the total area?",
                "choices": [c + " sq cm" for c in choices],
                "correct_answer": [c + " sq cm" for c in choices].index(correct + " sq cm"),
                "difficulty_score": 45,
                "tags": ["area", "composite-shapes"],
                "topic": "ncert_g5_perimeter_area",
                "chapter": "Ch8: Perimeter & Area",
                "hint": {"level_0": "Find the area of each rectangle and add them.", "level_1": f"Area 1 = {l1}×{w1} = {l1*w1}, Area 2 = {l2}×{w2} = {l2*w2}", "level_2": f"Total = {l1*w1} + {l2*w2} = {area} sq cm"},
                "curriculum_tags": ["NCERT_5_8"],
                "visual": True,
                "visual_alt": f"Composite figure of two rectangles",
                "diagnostics": {"1": "Only calculated one rectangle", "2": "Multiplied areas", "3": "Added dimensions instead of areas"}
            })
    return questions

def g5_ch9_data_handling(qnum):
    """Chapter 9: Data Handling"""
    questions = []
    for i in range(qnum):
        variant = i % 3
        if variant == 0:
            # Mean
            n = random.randint(4, 6)
            data = [random.randint(5, 50) for _ in range(n)]
            mean = sum(data) / n
            correct = str(int(mean)) if mean == int(mean) else f"{mean:.1f}"
            wrong = [str(max(data)), str(min(data)), str(sum(data))]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            sport = random.choice(SPORTS)
            questions.append({
                "stem": f"{name} scored {', '.join(map(str, data))} runs in {n} {sport} matches. What is the average (mean) score?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 40,
                "tags": ["data-handling", "mean"],
                "topic": "ncert_g5_data_handling",
                "chapter": "Ch9: Data Handling",
                "hint": {"level_0": "Mean = sum of all values ÷ number of values", "level_1": f"Sum = {sum(data)}, Number = {n}", "level_2": f"Mean = {sum(data)} ÷ {n} = {correct}"},
                "curriculum_tags": ["NCERT_5_9"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Forgot to divide", "2": "Divided by wrong number", "3": "Addition error"}
            })
        elif variant == 1:
            # Mode
            data = [random.randint(1, 10) for _ in range(7)]
            mode_val = random.choice(data)
            data.append(mode_val)
            data.append(mode_val)
            random.shuffle(data)
            from collections import Counter
            cnt = Counter(data)
            actual_mode = cnt.most_common(1)[0][0]
            correct = str(actual_mode)
            others = [str(v) for v in set(data) if v != actual_mode]
            wrong = others[:3]
            while len(wrong) < 3:
                wrong.append(str(actual_mode + 1))
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Find the mode of the data: {', '.join(map(str, data))}",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 30,
                "tags": ["data-handling", "mode"],
                "topic": "ncert_g5_data_handling",
                "chapter": "Ch9: Data Handling",
                "hint": {"level_0": "Mode is the value that appears most often.", "level_1": "Count how many times each number appears.", "level_2": f"{actual_mode} appears {cnt[actual_mode]} times, more than any other."},
                "curriculum_tags": ["NCERT_5_9"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Found mean instead of mode", "2": "Chose the largest number", "3": "Miscounted frequencies"}
            })
        else:
            # Probability
            total = random.choice([6, 8, 10, 12])
            favorable = random.randint(1, total - 1)
            from fractions import Fraction
            frac = Fraction(favorable, total)
            correct = f"{frac.numerator}/{frac.denominator}"
            wrong = [f"{total-favorable}/{total}", f"{favorable}/{total+favorable}", f"1/{total}"]
            choices = [correct] + wrong
            random.shuffle(choices)
            colors = ["red", "blue", "green", "yellow", "white"]
            color = random.choice(colors)
            questions.append({
                "stem": f"A bag has {total} balls. {favorable} are {color}. If you pick one ball without looking, what is the probability of getting a {color} ball?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 45,
                "tags": ["data-handling", "probability"],
                "topic": "ncert_g5_data_handling",
                "chapter": "Ch9: Data Handling",
                "hint": {"level_0": "Probability = favorable outcomes / total outcomes", "level_1": f"Favorable = {favorable}, Total = {total}", "level_2": f"P = {favorable}/{total} = {correct}"},
                "curriculum_tags": ["NCERT_5_9"],
                "visual": True,
                "visual_alt": f"Bag with {total} balls, {favorable} colored {color}",
                "diagnostics": {"1": "Swapped favorable and total", "2": "Used unfavorable outcomes", "3": "Did not simplify"}
            })
    return questions

def g5_ch10_patterns(qnum):
    """Chapter 10: Patterns"""
    questions = []
    for i in range(qnum):
        variant = i % 3
        if variant == 0:
            # Arithmetic sequence
            start = random.randint(2, 10)
            diff = random.randint(2, 7)
            seq = [start + diff * j for j in range(5)]
            next_val = seq[-1] + diff
            correct = str(next_val)
            wrong = [str(next_val + diff), str(next_val - 1), str(seq[-1] * 2)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"What is the next number in the pattern: {', '.join(map(str, seq))}, ...?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 25,
                "tags": ["patterns", "sequences"],
                "topic": "ncert_g5_patterns",
                "chapter": "Ch10: Patterns",
                "hint": {"level_0": "Find the common difference between consecutive terms.", "level_1": f"Each number increases by {diff}.", "level_2": f"{seq[-1]} + {diff} = {next_val}"},
                "curriculum_tags": ["NCERT_5_10"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Wrong common difference", "2": "Multiplied instead of added", "3": "Pattern recognition error"}
            })
        elif variant == 1:
            # nth term
            a = random.randint(1, 5)
            d = random.randint(2, 6)
            n = random.randint(8, 15)
            nth = a + (n - 1) * d
            correct = str(nth)
            wrong = [str(a + n * d), str(nth + d), str(a * n)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"In the sequence {a}, {a+d}, {a+2*d}, {a+3*d}, ..., what is the {n}th term?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 55,
                "tags": ["patterns", "nth-term"],
                "topic": "ncert_g5_patterns",
                "chapter": "Ch10: Patterns",
                "hint": {"level_0": "Use the formula: nth term = first term + (n-1) × common difference", "level_1": f"= {a} + ({n}-1) × {d}", "level_2": f"= {a} + {(n-1)*d} = {nth}"},
                "curriculum_tags": ["NCERT_5_10"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Used n instead of n-1", "2": "Wrong common difference", "3": "Arithmetic error"}
            })
        else:
            # Pattern rule
            mult = random.randint(2, 4)
            start = random.randint(1, 5)
            seq = [start * (mult ** j) for j in range(4)]
            next_val = seq[-1] * mult
            correct = str(next_val)
            wrong = [str(seq[-1] + seq[-2]), str(seq[-1] * 2), str(next_val + mult)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Find the next number: {', '.join(map(str, seq))}, ...?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 40,
                "tags": ["patterns", "geometric"],
                "topic": "ncert_g5_patterns",
                "chapter": "Ch10: Patterns",
                "hint": {"level_0": "Look at the ratio between consecutive terms.", "level_1": f"Each term is multiplied by {mult}.", "level_2": f"{seq[-1]} × {mult} = {next_val}"},
                "curriculum_tags": ["NCERT_5_10"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Assumed addition pattern", "2": "Wrong multiplier", "3": "Added instead of multiplied"}
            })
    return questions

def g5_ch11_volume(qnum):
    """Chapter 11: Volume"""
    questions = []
    for i in range(qnum):
        variant = i % 3
        if variant == 0:
            # Volume of cuboid
            l = random.randint(3, 12)
            w = random.randint(2, 8)
            h = random.randint(2, 8)
            vol = l * w * h
            correct = str(vol)
            wrong = [str(l*w + w*h + l*h), str(2*(l*w+w*h+l*h)), str(l+w+h)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Find the volume of a box with length {l} cm, width {w} cm, and height {h} cm.",
                "choices": [c + " cu cm" for c in choices],
                "correct_answer": [c + " cu cm" for c in choices].index(correct + " cu cm"),
                "difficulty_score": 35,
                "tags": ["volume", "cuboid"],
                "topic": "ncert_g5_volume",
                "chapter": "Ch11: Volume",
                "hint": {"level_0": "Volume = length × width × height", "level_1": f"V = {l} × {w} × {h}", "level_2": f"V = {vol} cu cm"},
                "curriculum_tags": ["NCERT_5_11"],
                "visual": True,
                "visual_alt": f"Cuboid with dimensions {l}×{w}×{h} cm",
                "diagnostics": {"1": "Calculated surface area", "2": "Added dimensions", "3": "Multiplied only two dimensions"}
            })
        elif variant == 1:
            # Volume of cube
            s = random.randint(2, 10)
            vol = s ** 3
            correct = str(vol)
            wrong = [str(s**2), str(6*s**2), str(s*4)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"A cube has side length {s} cm. What is its volume?",
                "choices": [c + " cu cm" for c in choices],
                "correct_answer": [c + " cu cm" for c in choices].index(correct + " cu cm"),
                "difficulty_score": 30,
                "tags": ["volume", "cube"],
                "topic": "ncert_g5_volume",
                "chapter": "Ch11: Volume",
                "hint": {"level_0": "Volume of cube = side × side × side", "level_1": f"V = {s}³", "level_2": f"V = {s} × {s} × {s} = {vol} cu cm"},
                "curriculum_tags": ["NCERT_5_11"],
                "visual": True,
                "visual_alt": f"Cube with side {s} cm",
                "diagnostics": {"1": "Calculated surface area (6s²)", "2": "Found s² not s³", "3": "Used wrong formula"}
            })
        else:
            # Capacity word problem
            l = random.randint(20, 50)
            w = random.randint(15, 30)
            h = random.randint(10, 25)
            vol_cm3 = l * w * h
            litres = vol_cm3 / 1000
            correct = str(int(litres)) if litres == int(litres) else f"{litres:.1f}"
            wrong = [str(vol_cm3), str(int(litres*10)), str(int(litres/10) if litres > 10 else int(litres)+5)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"A fish tank is {l} cm long, {w} cm wide, and {h} cm deep. How many litres of water can it hold? (1 litre = 1000 cu cm)",
                "choices": [c + " litres" for c in choices],
                "correct_answer": [c + " litres" for c in choices].index(correct + " litres"),
                "difficulty_score": 50,
                "tags": ["volume", "capacity"],
                "topic": "ncert_g5_volume",
                "chapter": "Ch11: Volume",
                "hint": {"level_0": "First find volume in cu cm, then convert to litres.", "level_1": f"V = {l}×{w}×{h} = {vol_cm3} cu cm", "level_2": f"{vol_cm3} ÷ 1000 = {correct} litres"},
                "curriculum_tags": ["NCERT_5_11"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Forgot to convert to litres", "2": "Divided by 100 instead of 1000", "3": "Multiplication error"}
            })
    return questions

def g5_ch12_speed(qnum):
    """Chapter 12: Speed/Distance/Time"""
    questions = []
    for i in range(qnum):
        variant = i % 3
        if variant == 0:
            # Find distance
            speed = random.choice([40, 50, 60, 80, 100, 120])
            time = random.choice([2, 3, 4, 5])
            dist = speed * time
            correct = str(dist)
            wrong = [str(speed + time), str(speed // time), str(dist + speed)]
            choices = [correct] + wrong
            random.shuffle(choices)
            transport = random.choice(TRANSPORT)
            city1, city2 = random.sample(CITIES, 2)
            questions.append({
                "stem": f"A {transport} travels at {speed} km/h. How far will it go in {time} hours?",
                "choices": [c + " km" for c in choices],
                "correct_answer": [c + " km" for c in choices].index(correct + " km"),
                "difficulty_score": 30,
                "tags": ["speed", "distance"],
                "topic": "ncert_g5_speed",
                "chapter": "Ch12: Speed/Distance/Time",
                "hint": {"level_0": "Distance = Speed × Time", "level_1": f"D = {speed} × {time}", "level_2": f"D = {dist} km"},
                "curriculum_tags": ["NCERT_5_12"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Divided instead of multiplied", "2": "Added speed and time", "3": "Used wrong formula"}
            })
        elif variant == 1:
            # Find time
            speed = random.choice([30, 40, 50, 60, 80])
            dist = speed * random.randint(2, 6)
            time = dist // speed
            correct = str(time)
            wrong = [str(dist * speed), str(time + 1), str(dist - speed)]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name} cycles at {speed} km/h. How long will it take to cover {dist} km?",
                "choices": [c + " hours" for c in choices],
                "correct_answer": [c + " hours" for c in choices].index(correct + " hours"),
                "difficulty_score": 35,
                "tags": ["speed", "time"],
                "topic": "ncert_g5_speed",
                "chapter": "Ch12: Speed/Distance/Time",
                "hint": {"level_0": "Time = Distance ÷ Speed", "level_1": f"T = {dist} ÷ {speed}", "level_2": f"T = {time} hours"},
                "curriculum_tags": ["NCERT_5_12"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Multiplied instead of divided", "2": "Divided speed by distance", "3": "Arithmetic error"}
            })
        else:
            # Find speed
            time = random.choice([2, 3, 4, 5, 6])
            dist = random.choice([60, 80, 100, 120, 150, 180, 200, 240, 300])
            speed = dist // time
            if dist % time != 0:
                dist = speed * time
            correct = str(speed)
            wrong = [str(dist * time), str(dist + time), str(speed + 10)]
            choices = [correct] + wrong
            random.shuffle(choices)
            transport = random.choice(TRANSPORT)
            questions.append({
                "stem": f"A {transport} covers {dist} km in {time} hours. What is its speed?",
                "choices": [c + " km/h" for c in choices],
                "correct_answer": [c + " km/h" for c in choices].index(correct + " km/h"),
                "difficulty_score": 35,
                "tags": ["speed", "find-speed"],
                "topic": "ncert_g5_speed",
                "chapter": "Ch12: Speed/Distance/Time",
                "hint": {"level_0": "Speed = Distance ÷ Time", "level_1": f"S = {dist} ÷ {time}", "level_2": f"S = {speed} km/h"},
                "curriculum_tags": ["NCERT_5_12"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Multiplied instead of divided", "2": "Divided time by distance", "3": "Arithmetic error"}
            })
    return questions

def g5_ch13_profit_loss(qnum):
    """Chapter 13: Profit & Loss"""
    questions = []
    for i in range(qnum):
        variant = i % 3
        if variant == 0:
            # Find profit
            cp = random.choice([100, 150, 200, 250, 300, 400, 500])
            profit_pct = random.choice([10, 15, 20, 25, 30, 50])
            sp = cp + cp * profit_pct // 100
            profit = sp - cp
            correct = str(profit)
            wrong = [str(sp), str(cp), str(profit + cp)]
            choices = ["₹" + correct] + ["₹" + w for w in wrong]
            random.shuffle(choices)
            name = random.choice(NAMES)
            item = random.choice(["toy", "book", "bag", "watch", "pen set"])
            questions.append({
                "stem": f"{name} bought a {item} for ₹{cp} and sold it for ₹{sp}. What is the profit?",
                "choices": choices,
                "correct_answer": choices.index("₹" + correct),
                "difficulty_score": 30,
                "tags": ["profit-loss", "profit"],
                "topic": "ncert_g5_profit_loss",
                "chapter": "Ch13: Profit & Loss",
                "hint": {"level_0": "Profit = Selling Price - Cost Price", "level_1": f"Profit = ₹{sp} - ₹{cp}", "level_2": f"Profit = ₹{profit}"},
                "curriculum_tags": ["NCERT_5_13"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Found SP instead of profit", "2": "Added SP and CP", "3": "Subtracted wrong way"}
            })
        elif variant == 1:
            # Find loss
            cp = random.choice([200, 300, 400, 500, 600, 800])
            loss_pct = random.choice([10, 15, 20, 25])
            loss = cp * loss_pct // 100
            sp = cp - loss
            correct = str(loss)
            wrong = [str(sp), str(cp), str(loss + 50)]
            choices = ["₹" + correct] + ["₹" + w for w in wrong]
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name} bought a bicycle for ₹{cp} and sold it for ₹{sp}. What is the loss?",
                "choices": choices,
                "correct_answer": choices.index("₹" + correct),
                "difficulty_score": 30,
                "tags": ["profit-loss", "loss"],
                "topic": "ncert_g5_profit_loss",
                "chapter": "Ch13: Profit & Loss",
                "hint": {"level_0": "Loss = Cost Price - Selling Price", "level_1": f"Loss = ₹{cp} - ₹{sp}", "level_2": f"Loss = ₹{loss}"},
                "curriculum_tags": ["NCERT_5_13"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Subtracted wrong way", "2": "Found SP instead", "3": "Added CP and SP"}
            })
        else:
            # Profit/Loss percentage
            cp = random.choice([200, 250, 400, 500, 800, 1000])
            change = random.choice([20, 25, 40, 50, 80, 100, 125, 200])
            is_profit = random.choice([True, False])
            if is_profit:
                sp = cp + change
                pct = (change / cp) * 100
                q_type = "profit"
            else:
                sp = cp - change
                pct = (change / cp) * 100
                q_type = "loss"
            correct = f"{int(pct)}%" if pct == int(pct) else f"{pct:.1f}%"
            wrong = [f"{int(pct/2)}%", f"{int(pct*2)}%", f"{change}%"]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name} bought a phone for ₹{cp} and sold it for ₹{sp}. Find the {q_type} percentage.",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 50,
                "tags": ["profit-loss", "percentage"],
                "topic": "ncert_g5_profit_loss",
                "chapter": "Ch13: Profit & Loss",
                "hint": {"level_0": f"{q_type.capitalize()} % = ({q_type.capitalize()}/CP) × 100", "level_1": f"{q_type.capitalize()} = ₹{change}, CP = ₹{cp}", "level_2": f"({change}/{cp}) × 100 = {correct}"},
                "curriculum_tags": ["NCERT_5_13"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Used SP instead of CP in denominator", "2": "Forgot to multiply by 100", "3": "Confused profit and loss"}
            })
    return questions

def g5_ch14_symmetry(qnum):
    """Chapter 14: Symmetry & Tessellations"""
    questions = []
    shapes = [("equilateral triangle", 3), ("square", 4), ("rectangle", 2), ("regular pentagon", 5), ("regular hexagon", 6), ("circle", "infinite"), ("isosceles triangle", 1), ("scalene triangle", 0)]
    for i in range(qnum):
        variant = i % 2
        if variant == 0:
            shape, lines = random.choice(shapes)
            correct = str(lines)
            all_opts = ["0", "1", "2", "3", "4", "5", "6", "infinite"]
            wrong = [o for o in all_opts if o != correct][:3]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"How many lines of symmetry does a {shape} have?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 30,
                "tags": ["symmetry", "lines-of-symmetry"],
                "topic": "ncert_g5_symmetry",
                "chapter": "Ch14: Symmetry & Tessellations",
                "hint": {"level_0": "A line of symmetry divides the shape into two identical halves.", "level_1": f"Think about how many ways you can fold a {shape} so both halves match.", "level_2": f"A {shape} has {lines} line(s) of symmetry."},
                "curriculum_tags": ["NCERT_5_14"],
                "visual": True,
                "visual_alt": f"{shape} showing lines of symmetry",
                "diagnostics": {"1": "Confused with rotational symmetry", "2": "Counted edges instead", "3": "Did not test all possible fold lines"}
            })
        else:
            # Rotational symmetry
            shape_rot = random.choice([("square", 4), ("equilateral triangle", 3), ("regular hexagon", 6), ("rectangle", 2), ("rhombus", 2)])
            shape_name, order = shape_rot
            correct = str(order)
            wrong = [str(order + 1), str(order - 1) if order > 1 else "3", str(order * 2)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"What is the order of rotational symmetry of a {shape_name}?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 45,
                "tags": ["symmetry", "rotational"],
                "topic": "ncert_g5_symmetry",
                "chapter": "Ch14: Symmetry & Tessellations",
                "hint": {"level_0": "Order of rotational symmetry = number of times a shape looks the same in one full turn.", "level_1": f"Rotate the {shape_name} — how many times does it match before completing 360°?", "level_2": f"A {shape_name} has order {order} rotational symmetry."},
                "curriculum_tags": ["NCERT_5_14"],
                "visual": True,
                "visual_alt": f"{shape_name} showing rotational symmetry",
                "diagnostics": {"1": "Confused with line symmetry", "2": "Counted total rotation degrees", "3": "Miscounted matching positions"}
            })
    return questions

def g5_ch15_maps(qnum):
    """Chapter 15: Maps & Scale"""
    questions = []
    for i in range(qnum):
        variant = i % 3
        if variant == 0:
            # Scale calculation
            scale_cm = random.choice([1, 2, 5])
            scale_km = random.choice([5, 10, 20, 50, 100])
            map_dist = random.randint(2, 10)
            actual = map_dist * scale_km // scale_cm
            correct = str(actual)
            wrong = [str(map_dist * scale_cm), str(actual + scale_km), str(map_dist)]
            choices = [correct + " km"] + [w + " km" for w in wrong]
            random.shuffle(choices)
            city1, city2 = random.sample(CITIES, 2)
            questions.append({
                "stem": f"On a map, {scale_cm} cm represents {scale_km} km. If the distance between {city1} and {city2} on the map is {map_dist} cm, what is the actual distance?",
                "choices": choices,
                "correct_answer": choices.index(correct + " km"),
                "difficulty_score": 45,
                "tags": ["maps", "scale"],
                "topic": "ncert_g5_maps",
                "chapter": "Ch15: Maps & Scale",
                "hint": {"level_0": "Use the scale to convert map distance to actual distance.", "level_1": f"If {scale_cm} cm = {scale_km} km, then {map_dist} cm = ?", "level_2": f"{map_dist} × {scale_km}/{scale_cm} = {actual} km"},
                "curriculum_tags": ["NCERT_5_15"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Multiplied by scale_cm instead", "2": "Did not scale properly", "3": "Used wrong operation"}
            })
        elif variant == 1:
            # Direction
            directions = ["North", "South", "East", "West", "North-East", "North-West", "South-East", "South-West"]
            opposites = {"North": "South", "South": "North", "East": "West", "West": "East",
                        "North-East": "South-West", "South-West": "North-East", "North-West": "South-East", "South-East": "North-West"}
            dir1 = random.choice(list(opposites.keys()))
            correct = opposites[dir1]
            wrong = [d for d in directions if d != correct][:3]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name} walks towards {dir1}. What direction is directly behind {name}?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 20,
                "tags": ["maps", "directions"],
                "topic": "ncert_g5_maps",
                "chapter": "Ch15: Maps & Scale",
                "hint": {"level_0": "The direction behind is the opposite direction.", "level_1": f"Opposite of {dir1} is?", "level_2": f"Opposite of {dir1} is {correct}."},
                "curriculum_tags": ["NCERT_5_15"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Confused left/right with opposite", "2": "Named adjacent direction", "3": "Mixed up compass points"}
            })
        else:
            # Map reading
            scale_factor = random.choice([2, 5, 10])
            map_length = random.randint(3, 8)
            map_width = random.randint(2, 6)
            actual_l = map_length * scale_factor
            actual_w = map_width * scale_factor
            actual_area = actual_l * actual_w
            correct = str(actual_area)
            wrong = [str(map_length * map_width), str(actual_l * actual_w * scale_factor), str(actual_l + actual_w)]
            choices = [correct + " sq km"] + [w + " sq km" for w in wrong]
            random.shuffle(choices)
            state = random.choice(STATES)
            questions.append({
                "stem": f"A park on a map is {map_length} cm × {map_width} cm. Scale: 1 cm = {scale_factor} km. What is the actual area of the park?",
                "choices": choices,
                "correct_answer": choices.index(correct + " sq km"),
                "difficulty_score": 60,
                "tags": ["maps", "area-from-scale"],
                "topic": "ncert_g5_maps",
                "chapter": "Ch15: Maps & Scale",
                "hint": {"level_0": "Convert each dimension using the scale, then find area.", "level_1": f"Actual: {map_length}×{scale_factor} = {actual_l} km, {map_width}×{scale_factor} = {actual_w} km", "level_2": f"Area = {actual_l} × {actual_w} = {actual_area} sq km"},
                "curriculum_tags": ["NCERT_5_15"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Used map dimensions for area", "2": "Scaled area by factor not factor²", "3": "Added dimensions instead of multiplying"}
            })
    return questions

# ============================================================
# GRADE 6 QUESTION GENERATORS (Ganita Prakash)
# ============================================================

def g6_ch1_patterns(qnum):
    """Chapter 1: Patterns in Mathematics"""
    questions = []
    for i in range(qnum):
        variant = i % 5
        if variant == 0:
            # Triangular numbers
            n = random.randint(5, 12)
            tri = n * (n + 1) // 2
            correct = str(tri)
            wrong = [str(n * n), str(tri + n), str(n * (n-1) // 2)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"The triangular numbers are 1, 3, 6, 10, 15, ... What is the {n}th triangular number?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 50,
                "tags": ["patterns", "figurate-numbers"],
                "topic": "ncert_g6_patterns",
                "chapter": "Ch1: Patterns in Mathematics",
                "hint": {"level_0": "The nth triangular number = n(n+1)/2", "level_1": f"T({n}) = {n} × {n+1} / 2", "level_2": f"T({n}) = {n * (n+1)} / 2 = {tri}"},
                "curriculum_tags": ["NCERT_6_1"],
                "visual": True,
                "visual_alt": f"Dot pattern showing triangular number T({n})",
                "diagnostics": {"1": "Used n² instead", "2": "Forgot to divide by 2", "3": "Used n-1 instead of n"}
            })
        elif variant == 1:
            # Square numbers
            n = random.randint(6, 15)
            sq = n * n
            correct = str(sq)
            wrong = [str(2*n), str(n*(n+1)), str(sq + 1)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"What is the {n}th square number?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 30,
                "tags": ["patterns", "square-numbers"],
                "topic": "ncert_g6_patterns",
                "chapter": "Ch1: Patterns in Mathematics",
                "hint": {"level_0": "Square numbers: 1, 4, 9, 16, 25, ... (n×n)", "level_1": f"The {n}th square number = {n} × {n}", "level_2": f"{n} × {n} = {sq}"},
                "curriculum_tags": ["NCERT_6_1"],
                "visual": True,
                "visual_alt": f"Square dot arrangement for {n}×{n}",
                "diagnostics": {"1": "Added n to itself", "2": "Used n(n+1) (rectangular number)", "3": "Counting error"}
            })
        elif variant == 2:
            # Collatz sequence
            start = random.choice([7, 11, 13, 15, 17, 19, 21, 23, 25, 27])
            seq = [start]
            n = start
            for _ in range(6):
                if n % 2 == 0:
                    n = n // 2
                else:
                    n = 3 * n + 1
                seq.append(n)
            next_val = seq[-1] // 2 if seq[-1] % 2 == 0 else 3 * seq[-1] + 1
            correct = str(next_val)
            wrong = [str(seq[-1] * 2), str(seq[-1] + 1), str(seq[-1] - 1)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"In the Collatz sequence (if even: divide by 2; if odd: multiply by 3 and add 1), starting from {start}: {', '.join(map(str, seq))}. What comes next?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 55,
                "tags": ["patterns", "collatz"],
                "topic": "ncert_g6_patterns",
                "chapter": "Ch1: Patterns in Mathematics",
                "hint": {"level_0": "Check if the last number is even or odd, then apply the rule.", "level_1": f"{seq[-1]} is {'even' if seq[-1]%2==0 else 'odd'}.", "level_2": f"{'Divide by 2' if seq[-1]%2==0 else 'Multiply by 3, add 1'}: {next_val}"},
                "curriculum_tags": ["NCERT_6_1"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Applied wrong rule (even/odd)", "2": "Forgot to add 1 for odd", "3": "Multiplied even number by 3"}
            })
        elif variant == 3:
            # Sum patterns
            n = random.randint(4, 10)
            # Sum of first n odd numbers = n²
            odds = [2*k - 1 for k in range(1, n+1)]
            sum_val = n * n
            correct = str(sum_val)
            wrong = [str(sum(odds) + 2), str(n * (n+1)), str(2*n*n)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Find the sum: {' + '.join(map(str, odds))} = ?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 45,
                "tags": ["patterns", "sum-of-odds"],
                "topic": "ncert_g6_patterns",
                "chapter": "Ch1: Patterns in Mathematics",
                "hint": {"level_0": "The sum of first n odd numbers has a beautiful pattern!", "level_1": f"1=1, 1+3=4, 1+3+5=9, 1+3+5+7=16... See the pattern?", "level_2": f"Sum of first {n} odd numbers = {n}² = {sum_val}"},
                "curriculum_tags": ["NCERT_6_1"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Added incorrectly", "2": "Did not recognize the n² pattern", "3": "Counted wrong number of terms"}
            })
        else:
            # Fibonacci-like
            a, b = random.choice([(1,1),(2,1),(1,3),(2,3)])
            seq = [a, b]
            for _ in range(5):
                seq.append(seq[-1] + seq[-2])
            next_val = seq[-1] + seq[-2]
            correct = str(next_val)
            wrong = [str(seq[-1] * 2), str(next_val + 1), str(seq[-1] + 1)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Each number is the sum of the two before it: {', '.join(map(str, seq))}. What comes next?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 35,
                "tags": ["patterns", "fibonacci"],
                "topic": "ncert_g6_patterns",
                "chapter": "Ch1: Patterns in Mathematics",
                "hint": {"level_0": "Add the last two numbers to get the next.", "level_1": f"{seq[-2]} + {seq[-1]} = ?", "level_2": f"{seq[-2]} + {seq[-1]} = {next_val}"},
                "curriculum_tags": ["NCERT_6_1"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Added wrong pair", "2": "Multiplied instead of adding", "3": "Used wrong rule"}
            })
    return questions

def g6_ch2_lines_angles(qnum):
    """Chapter 2: Lines and Angles"""
    questions = []
    for i in range(qnum):
        variant = i % 5
        if variant == 0:
            # Complementary
            angle = random.randint(15, 75)
            comp = 90 - angle
            correct = str(comp)
            wrong = [str(180 - angle), str(angle), str(90 + angle)]
            choices = [correct + "°"] + [w + "°" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"What is the complement of {angle}°?",
                "choices": choices,
                "correct_answer": choices.index(correct + "°"),
                "difficulty_score": 30,
                "tags": ["lines-angles", "complementary"],
                "topic": "ncert_g6_lines_angles",
                "chapter": "Ch2: Lines and Angles",
                "hint": {"level_0": "Complementary angles add up to 90°.", "level_1": f"90° - {angle}° = ?", "level_2": f"90° - {angle}° = {comp}°"},
                "curriculum_tags": ["NCERT_6_2"],
                "visual": True,
                "visual_alt": f"Two complementary angles: {angle}° and ?",
                "diagnostics": {"1": "Used 180° instead of 90°", "2": "Added instead of subtracted", "3": "Confused with supplementary"}
            })
        elif variant == 1:
            # Supplementary
            angle = random.randint(30, 150)
            supp = 180 - angle
            correct = str(supp)
            wrong = [str(90 - angle if angle < 90 else angle - 90), str(angle), str(360 - angle)]
            choices = [correct + "°"] + [w + "°" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"What is the supplement of {angle}°?",
                "choices": choices,
                "correct_answer": choices.index(correct + "°"),
                "difficulty_score": 30,
                "tags": ["lines-angles", "supplementary"],
                "topic": "ncert_g6_lines_angles",
                "chapter": "Ch2: Lines and Angles",
                "hint": {"level_0": "Supplementary angles add up to 180°.", "level_1": f"180° - {angle}° = ?", "level_2": f"180° - {angle}° = {supp}°"},
                "curriculum_tags": ["NCERT_6_2"],
                "visual": True,
                "visual_alt": f"Linear pair showing {angle}° and ?",
                "diagnostics": {"1": "Used 90° instead of 180°", "2": "Used 360°", "3": "Confused with complementary"}
            })
        elif variant == 2:
            # Vertically opposite
            angle = random.randint(20, 160)
            correct = str(angle)
            wrong = [str(180 - angle), str(90 - angle if angle < 90 else angle - 90), str(angle + 10)]
            choices = [correct + "°"] + [w + "°" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"Two straight lines cross. One of the angles formed is {angle}°. What is the vertically opposite angle?",
                "choices": choices,
                "correct_answer": choices.index(correct + "°"),
                "difficulty_score": 35,
                "tags": ["lines-angles", "vertically-opposite"],
                "topic": "ncert_g6_lines_angles",
                "chapter": "Ch2: Lines and Angles",
                "hint": {"level_0": "Vertically opposite angles are equal.", "level_1": "When two lines cross, opposite angles are the same.", "level_2": f"The vertically opposite angle is also {angle}°."},
                "curriculum_tags": ["NCERT_6_2"],
                "visual": True,
                "visual_alt": f"Two intersecting lines with angle {angle}° marked",
                "diagnostics": {"1": "Found supplementary instead", "2": "Found complementary instead", "3": "Thought vertically opposite means 180°-angle"}
            })
        elif variant == 3:
            # Angles on a line
            a1 = random.randint(30, 120)
            a2 = random.randint(20, 180 - a1 - 10)
            a3 = 180 - a1 - a2
            correct = str(a3)
            wrong = [str(360 - a1 - a2), str(a1 + a2), str(90 - a3 if a3 < 90 else a3 + 10)]
            choices = [correct + "°"] + [w + "°" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"Three angles on a straight line are {a1}°, {a2}°, and x°. Find x.",
                "choices": choices,
                "correct_answer": choices.index(correct + "°"),
                "difficulty_score": 40,
                "tags": ["lines-angles", "angles-on-line"],
                "topic": "ncert_g6_lines_angles",
                "chapter": "Ch2: Lines and Angles",
                "hint": {"level_0": "Angles on a straight line add up to 180°.", "level_1": f"x = 180° - {a1}° - {a2}°", "level_2": f"x = 180 - {a1} - {a2} = {a3}°"},
                "curriculum_tags": ["NCERT_6_2"],
                "visual": True,
                "visual_alt": f"Three angles on a straight line",
                "diagnostics": {"1": "Used 360° instead of 180°", "2": "Added angles instead of subtracting", "3": "Arithmetic error"}
            })
        else:
            # Angle types identification
            angle = random.randint(1, 359)
            if angle < 90: atype = "acute"
            elif angle == 90: atype = "right"
            elif angle < 180: atype = "obtuse"
            elif angle == 180: atype = "straight"
            elif angle < 360: atype = "reflex"
            else: atype = "complete"
            correct = atype
            all_types = ["acute", "right", "obtuse", "straight", "reflex"]
            wrong = [t for t in all_types if t != correct][:3]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"An angle of {angle}° is classified as:",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 25,
                "tags": ["lines-angles", "angle-types"],
                "topic": "ncert_g6_lines_angles",
                "chapter": "Ch2: Lines and Angles",
                "hint": {"level_0": "Acute: <90°, Right: 90°, Obtuse: 90°-180°, Straight: 180°, Reflex: 180°-360°", "level_1": f"Where does {angle}° fall?", "level_2": f"{angle}° is {atype}."},
                "curriculum_tags": ["NCERT_6_2"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Confused obtuse and reflex", "2": "Did not know reflex angles", "3": "Wrong boundary check"}
            })
    return questions

def g6_ch3_number_play(qnum):
    """Chapter 3: Number Play"""
    questions = []
    for i in range(qnum):
        variant = i % 5
        if variant == 0:
            # Palindrome
            num = random.randint(100, 999)
            rev = int(str(num)[::-1])
            total = num + rev
            is_pal = str(total) == str(total)[::-1]
            if not is_pal:
                total2 = total + int(str(total)[::-1])
                correct = str(total)
                wrong = [str(rev), str(num * 2), str(total + 1)]
            else:
                correct = str(total)
                wrong = [str(rev), str(num * 2), str(total - 1)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Add {num} and its reverse. What do you get?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 35,
                "tags": ["number-play", "palindromes"],
                "topic": "ncert_g6_number_play",
                "chapter": "Ch3: Number Play",
                "hint": {"level_0": "Reverse the digits of the number, then add.", "level_1": f"Reverse of {num} is {rev}.", "level_2": f"{num} + {rev} = {total}"},
                "curriculum_tags": ["NCERT_6_3"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Reversed incorrectly", "2": "Subtracted instead of added", "3": "Arithmetic error"}
            })
        elif variant == 1:
            # Kaprekar routine (4-digit)
            num = random.choice([3087, 1234, 4321, 6174, 2005, 8730])
            digits = sorted(str(num).zfill(4))
            desc = int(''.join(reversed(digits)))
            asc = int(''.join(digits))
            result = desc - asc
            correct = str(result)
            wrong = [str(desc + asc), str(desc), str(asc)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"In the Kaprekar routine: arrange digits of {str(num).zfill(4)} in descending order, subtract ascending order. What do you get? (Desc: {desc}, Asc: {asc})",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 50,
                "tags": ["number-play", "kaprekar"],
                "topic": "ncert_g6_number_play",
                "chapter": "Ch3: Number Play",
                "hint": {"level_0": "Descending - Ascending = ?", "level_1": f"{desc} - {asc} = ?", "level_2": f"{desc} - {asc} = {result}"},
                "curriculum_tags": ["NCERT_6_3"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Added instead of subtracted", "2": "Arranged digits wrong", "3": "Subtracted in wrong order"}
            })
        elif variant == 2:
            # Divisibility puzzle
            num = random.randint(100, 999)
            digit_sum = sum(int(d) for d in str(num))
            div_by_3 = digit_sum % 3 == 0
            correct = "Yes" if div_by_3 else "No"
            reason = f"because digit sum {digit_sum} {'is' if div_by_3 else 'is not'} divisible by 3"
            choices = [f"Yes, {reason}", f"No, {reason.replace('is not','is').replace('is','is not') if div_by_3 else reason.replace('is not','is')}",
                      f"Yes, because {num} is odd", f"No, because {num} ends in {str(num)[-1]}"]
            correct_choice = choices[0] if div_by_3 else choices[0].replace("Yes", "No")
            # Simplify
            choices = ["Yes", "No", "Only if the last digit is 3", "Cannot determine"]
            correct_idx = 0 if div_by_3 else 1
            questions.append({
                "stem": f"Is {num} divisible by 3? (Hint: add its digits: {' + '.join(str(d) for d in str(num))} = {digit_sum})",
                "choices": choices,
                "correct_answer": correct_idx,
                "difficulty_score": 35,
                "tags": ["number-play", "divisibility"],
                "topic": "ncert_g6_number_play",
                "chapter": "Ch3: Number Play",
                "hint": {"level_0": "A number is divisible by 3 if the sum of its digits is divisible by 3.", "level_1": f"Digit sum = {digit_sum}. Is {digit_sum} divisible by 3?", "level_2": f"{digit_sum} ÷ 3 = {digit_sum/3:.1f}, so {'yes' if div_by_3 else 'no'}."},
                "curriculum_tags": ["NCERT_6_3"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Added digits wrong", "2": "Used wrong divisibility rule", "3": "Checked last digit only"}
            })
        elif variant == 3:
            # Number puzzle
            a = random.randint(10, 50)
            b = random.randint(10, 50)
            product = a * b
            summ = a + b
            correct = str(a) + " and " + str(b)
            wrong = [f"{a+1} and {b-1}", f"{a*2} and {b//2}", f"{a-1} and {b+1}"]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Two numbers have a sum of {summ} and a product of {product}. What are the numbers?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 60,
                "tags": ["number-play", "puzzle"],
                "topic": "ncert_g6_number_play",
                "chapter": "Ch3: Number Play",
                "hint": {"level_0": "Try pairs that add up to the sum and check their product.", "level_1": f"Think: what × what = {product}, and those same numbers add to {summ}?", "level_2": f"{a} + {b} = {summ} and {a} × {b} = {product}"},
                "curriculum_tags": ["NCERT_6_3"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Only checked sum condition", "2": "Only checked product condition", "3": "Arithmetic verification error"}
            })
        else:
            # Magic constant
            n = 3
            magic_const = 15
            correct = str(magic_const)
            wrong = ["12", "18", "21"]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": "In a 3×3 magic square using numbers 1-9, what is the magic constant (sum of each row, column, and diagonal)?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 40,
                "tags": ["number-play", "magic-square"],
                "topic": "ncert_g6_number_play",
                "chapter": "Ch3: Number Play",
                "hint": {"level_0": "Sum of 1 to 9 = 45. Divide equally among 3 rows.", "level_1": "Magic constant = (sum of all numbers) / (number of rows)", "level_2": "45 ÷ 3 = 15"},
                "curriculum_tags": ["NCERT_6_3"],
                "visual": True,
                "visual_alt": "3x3 magic square grid",
                "diagnostics": {"1": "Divided by wrong number", "2": "Used wrong total sum", "3": "Guessed without calculation"}
            })
    return questions

def g6_ch4_data_handling(qnum):
    """Chapter 4: Data Handling & Presentation"""
    questions = []
    for i in range(qnum):
        variant = i % 4
        if variant == 0:
            # Mean
            n = random.randint(5, 8)
            data = sorted([random.randint(10, 95) for _ in range(n)])
            mean = sum(data) / n
            correct = f"{mean:.1f}" if mean != int(mean) else str(int(mean))
            wrong = [str(data[n//2]), str(max(data) - min(data)), str(sum(data))]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name}'s test scores are: {', '.join(map(str, data))}. What is the mean score?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 40,
                "tags": ["data-handling", "mean"],
                "topic": "ncert_g6_data_handling",
                "chapter": "Ch4: Data Handling & Presentation",
                "hint": {"level_0": "Mean = sum of all values ÷ number of values", "level_1": f"Sum = {sum(data)}, Count = {n}", "level_2": f"Mean = {sum(data)} ÷ {n} = {correct}"},
                "curriculum_tags": ["NCERT_6_4"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Found median instead", "2": "Found range instead", "3": "Division error"}
            })
        elif variant == 1:
            # Median
            n = random.choice([5, 7, 9])
            data = sorted([random.randint(5, 50) for _ in range(n)])
            median = data[n // 2]
            correct = str(median)
            wrong = [str(sum(data)//n), str(data[0]), str(data[-1])]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Find the median of: {', '.join(map(str, data))}",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 35,
                "tags": ["data-handling", "median"],
                "topic": "ncert_g6_data_handling",
                "chapter": "Ch4: Data Handling & Presentation",
                "hint": {"level_0": "Median is the middle value when data is arranged in order.", "level_1": f"There are {n} values. Middle position = {n//2 + 1}", "level_2": f"Middle value = {median}"},
                "curriculum_tags": ["NCERT_6_4"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Found mean instead", "2": "Data not sorted first", "3": "Wrong middle position"}
            })
        elif variant == 2:
            # Pie chart reading
            categories = ["Cricket", "Football", "Badminton", "Hockey"]
            percentages = [40, 25, 20, 15]
            total_students = random.choice([100, 200, 300, 400, 500])
            cat_idx = random.randint(0, 3)
            answer = total_students * percentages[cat_idx] // 100
            correct = str(answer)
            wrong = [str(percentages[cat_idx]), str(total_students - answer), str(answer + 10)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"A pie chart shows favourite sports of {total_students} students: Cricket {percentages[0]}%, Football {percentages[1]}%, Badminton {percentages[2]}%, Hockey {percentages[3]}%. How many prefer {categories[cat_idx]}?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 45,
                "tags": ["data-handling", "pie-chart"],
                "topic": "ncert_g6_data_handling",
                "chapter": "Ch4: Data Handling & Presentation",
                "hint": {"level_0": f"Find {percentages[cat_idx]}% of {total_students}.", "level_1": f"{percentages[cat_idx]}/100 × {total_students} = ?", "level_2": f"{percentages[cat_idx]/100} × {total_students} = {answer}"},
                "curriculum_tags": ["NCERT_6_4"],
                "visual": True,
                "visual_alt": "Pie chart showing sports preferences",
                "diagnostics": {"1": "Read percentage as answer", "2": "Used wrong percentage", "3": "Calculation error"}
            })
        else:
            # Range
            data = [random.randint(10, 90) for _ in range(6)]
            range_val = max(data) - min(data)
            correct = str(range_val)
            wrong = [str(max(data)), str(min(data)), str(sum(data)//len(data))]
            choices = [correct] + wrong
            random.shuffle(choices)
            festival = random.choice(FESTIVALS)
            questions.append({
                "stem": f"Temperatures (°C) recorded during {festival} week: {', '.join(map(str, data))}. What is the range?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 30,
                "tags": ["data-handling", "range"],
                "topic": "ncert_g6_data_handling",
                "chapter": "Ch4: Data Handling & Presentation",
                "hint": {"level_0": "Range = Highest value - Lowest value", "level_1": f"Highest = {max(data)}, Lowest = {min(data)}", "level_2": f"Range = {max(data)} - {min(data)} = {range_val}"},
                "curriculum_tags": ["NCERT_6_4"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Found mean instead of range", "2": "Gave max value as range", "3": "Subtracted wrong values"}
            })
    return questions

def g6_ch5_prime_time(qnum):
    """Chapter 5: Prime Time"""
    questions = []
    for i in range(qnum):
        variant = i % 5
        if variant == 0:
            # Identify primes
            primes = [p for p in range(2, 100) if all(p % d != 0 for d in range(2, int(p**0.5)+1))]
            composites = [c for c in range(4, 100) if c not in primes]
            prime = random.choice(primes[10:])
            comp_set = random.sample(composites, 3)
            choices = [str(prime)] + [str(c) for c in comp_set]
            random.shuffle(choices)
            questions.append({
                "stem": "Which of the following is a prime number?",
                "choices": choices,
                "correct_answer": choices.index(str(prime)),
                "difficulty_score": 30,
                "tags": ["prime-time", "identification"],
                "topic": "ncert_g6_prime_time",
                "chapter": "Ch5: Prime Time",
                "hint": {"level_0": "A prime number has exactly two factors: 1 and itself.", "level_1": f"Check if {prime} is divisible by 2, 3, 5, 7...", "level_2": f"{prime} has no factors other than 1 and {prime}, so it is prime."},
                "curriculum_tags": ["NCERT_6_5"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Confused prime with odd", "2": "Missed a factor", "3": "Tested insufficient divisors"}
            })
        elif variant == 1:
            # Prime factorization
            nums = [36, 48, 60, 72, 84, 90, 96, 100, 108, 120, 132, 144, 150, 168, 180, 200, 210, 252]
            num = random.choice(nums)
            def pf(n):
                factors = []
                d = 2
                while d * d <= n:
                    while n % d == 0:
                        factors.append(d)
                        n //= d
                    d += 1
                if n > 1: factors.append(n)
                return factors
            factors = pf(num)
            from collections import Counter
            fc = Counter(factors)
            correct = " × ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(fc.items()))
            # Alternative format
            correct_alt = " × ".join(str(f) for f in factors)
            wrong = [" × ".join(str(f) for f in pf(num+2)),
                     " × ".join(str(f) for f in pf(num-2)),
                     correct_alt.replace(str(factors[0]), str(factors[0]+1), 1)]
            choices = [correct_alt] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Find the prime factorization of {num}.",
                "choices": choices,
                "correct_answer": choices.index(correct_alt),
                "difficulty_score": 45,
                "tags": ["prime-time", "factorization"],
                "topic": "ncert_g6_prime_time",
                "chapter": "Ch5: Prime Time",
                "hint": {"level_0": "Keep dividing by the smallest prime factor.", "level_1": f"{num} ÷ {factors[0]} = {num//factors[0]}", "level_2": f"{num} = {correct_alt}"},
                "curriculum_tags": ["NCERT_6_5"],
                "visual": True,
                "visual_alt": f"Factor tree for {num}",
                "diagnostics": {"1": "Stopped too early", "2": "Used a composite factor", "3": "Division error"}
            })
        elif variant == 2:
            # Twin primes
            twin_pairs = [(3,5),(5,7),(11,13),(17,19),(29,31),(41,43),(59,61),(71,73)]
            pair = random.choice(twin_pairs)
            correct = f"({pair[0]}, {pair[1]})"
            non_twins = [(7,11),(13,17),(23,29),(31,37)]
            wrong = [f"({nt[0]}, {nt[1]})" for nt in random.sample(non_twins, 3)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": "Twin primes are pairs of primes that differ by 2. Which pair below are twin primes?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 45,
                "tags": ["prime-time", "twin-primes"],
                "topic": "ncert_g6_prime_time",
                "chapter": "Ch5: Prime Time",
                "hint": {"level_0": "Check: are both numbers prime AND differ by exactly 2?", "level_1": f"Check {pair[0]} and {pair[1]}: difference = {pair[1]-pair[0]}, both prime?", "level_2": f"{pair[0]} and {pair[1]} are both prime and differ by 2."},
                "curriculum_tags": ["NCERT_6_5"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Checked only one number", "2": "Did not verify primality", "3": "Confused twin with consecutive"}
            })
        elif variant == 3:
            # Sieve question
            n = random.choice([30, 40, 50])
            primes_up_to_n = [p for p in range(2, n+1) if all(p % d != 0 for d in range(2, int(p**0.5)+1))]
            count = len(primes_up_to_n)
            correct = str(count)
            wrong = [str(count + 2), str(count - 2), str(n // 2)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Using the Sieve of Eratosthenes, how many prime numbers are there from 1 to {n}?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 50,
                "tags": ["prime-time", "sieve"],
                "topic": "ncert_g6_prime_time",
                "chapter": "Ch5: Prime Time",
                "hint": {"level_0": "Cross out multiples of 2, 3, 5, 7... Count what remains.", "level_1": f"Primes up to {n}: start with 2, 3, 5, 7, 11...", "level_2": f"There are {count} primes from 1 to {n}."},
                "curriculum_tags": ["NCERT_6_5"],
                "visual": True,
                "visual_alt": f"Number grid 1-{n} with primes highlighted",
                "diagnostics": {"1": "Included 1 as prime", "2": "Missed some primes", "3": "Included composites"}
            })
        else:
            # LCM using prime factorization
            a, b = random.choice([(12,18),(15,20),(24,36),(18,24),(20,30),(28,42)])
            lcm = (a * b) // math.gcd(a, b)
            correct = str(lcm)
            wrong = [str(a*b), str(math.gcd(a,b)), str(lcm + a)]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"Two bells ring every {a} and {b} seconds. If they ring together now, after how many seconds will they ring together again?",
                "choices": [c + " seconds" for c in choices],
                "correct_answer": [c + " seconds" for c in choices].index(correct + " seconds"),
                "difficulty_score": 50,
                "tags": ["prime-time", "lcm"],
                "topic": "ncert_g6_prime_time",
                "chapter": "Ch5: Prime Time",
                "hint": {"level_0": "Find the LCM of the two numbers.", "level_1": f"LCM({a}, {b}) = ?", "level_2": f"LCM({a}, {b}) = {lcm}"},
                "curriculum_tags": ["NCERT_6_5"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Found HCF instead", "2": "Just multiplied the numbers", "3": "Used wrong method"}
            })
    return questions

def g6_ch6_perimeter_area(qnum):
    """Chapter 6: Perimeter and Area"""
    questions = []
    for i in range(qnum):
        variant = i % 4
        if variant == 0:
            # Area of parallelogram
            base = random.randint(5, 20)
            height = random.randint(3, 15)
            area = base * height
            correct = str(area)
            wrong = [str(2*(base+height)), str(base + height), str(area + base)]
            choices = [correct + " sq cm"] + [w + " sq cm" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"Find the area of a parallelogram with base {base} cm and height {height} cm.",
                "choices": choices,
                "correct_answer": choices.index(correct + " sq cm"),
                "difficulty_score": 35,
                "tags": ["perimeter-area", "parallelogram"],
                "topic": "ncert_g6_perimeter_area",
                "chapter": "Ch6: Perimeter and Area",
                "hint": {"level_0": "Area of parallelogram = base × height", "level_1": f"A = {base} × {height}", "level_2": f"A = {area} sq cm"},
                "curriculum_tags": ["NCERT_6_6"],
                "visual": True,
                "visual_alt": f"Parallelogram with base {base} cm and height {height} cm",
                "diagnostics": {"1": "Used perimeter formula", "2": "Used ½ × base × height", "3": "Added instead of multiplied"}
            })
        elif variant == 1:
            # Circumference of circle
            r = random.randint(3, 14)
            circumference = round(2 * 3.14 * r, 2)
            correct = str(circumference)
            wrong = [str(round(3.14 * r * r, 2)), str(round(3.14 * r, 2)), str(round(2 * 3.14 * r + r, 2))]
            choices = [correct + " cm"] + [w + " cm" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"Find the circumference of a circle with radius {r} cm. (Use π = 3.14)",
                "choices": choices,
                "correct_answer": choices.index(correct + " cm"),
                "difficulty_score": 45,
                "tags": ["perimeter-area", "circle"],
                "topic": "ncert_g6_perimeter_area",
                "chapter": "Ch6: Perimeter and Area",
                "hint": {"level_0": "Circumference = 2πr", "level_1": f"C = 2 × 3.14 × {r}", "level_2": f"C = {circumference} cm"},
                "curriculum_tags": ["NCERT_6_6"],
                "visual": True,
                "visual_alt": f"Circle with radius {r} cm",
                "diagnostics": {"1": "Used πr² (area formula)", "2": "Forgot the 2", "3": "Used diameter instead of radius"}
            })
        elif variant == 2:
            # Complex polygon area
            side = random.randint(4, 10)
            # Square with triangle on top
            sq_area = side * side
            tri_height = random.randint(2, side)
            tri_area = side * tri_height // 2
            total = sq_area + tri_area
            correct = str(total)
            wrong = [str(sq_area), str(sq_area + tri_height), str(total + side)]
            choices = [correct + " sq cm"] + [w + " sq cm" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"A figure is made of a square (side {side} cm) with a triangle on top (base {side} cm, height {tri_height} cm). Find the total area.",
                "choices": choices,
                "correct_answer": choices.index(correct + " sq cm"),
                "difficulty_score": 55,
                "tags": ["perimeter-area", "composite"],
                "topic": "ncert_g6_perimeter_area",
                "chapter": "Ch6: Perimeter and Area",
                "hint": {"level_0": "Split into square + triangle and find each area.", "level_1": f"Square: {side}² = {sq_area}. Triangle: ½ × {side} × {tri_height} = {tri_area}", "level_2": f"Total = {sq_area} + {tri_area} = {total} sq cm"},
                "curriculum_tags": ["NCERT_6_6"],
                "visual": True,
                "visual_alt": "Pentagon shape (square + triangle)",
                "diagnostics": {"1": "Only found square area", "2": "Forgot ½ in triangle area", "3": "Subtracted instead of added"}
            })
        else:
            # Perimeter with missing side
            sides = [random.randint(3, 12) for _ in range(4)]
            total_p = sum(sides) + random.randint(3, 10)
            missing = total_p - sum(sides)
            correct = str(missing)
            wrong = [str(total_p), str(sum(sides)), str(missing + 2)]
            choices = [correct + " cm"] + [w + " cm" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"A pentagon has a perimeter of {total_p} cm. Four of its sides are {', '.join(map(str, sides))} cm. What is the fifth side?",
                "choices": choices,
                "correct_answer": choices.index(correct + " cm"),
                "difficulty_score": 40,
                "tags": ["perimeter-area", "missing-side"],
                "topic": "ncert_g6_perimeter_area",
                "chapter": "Ch6: Perimeter and Area",
                "hint": {"level_0": "Fifth side = Perimeter - sum of other four sides", "level_1": f"Sum of 4 sides = {sum(sides)}. Perimeter = {total_p}.", "level_2": f"{total_p} - {sum(sides)} = {missing} cm"},
                "curriculum_tags": ["NCERT_6_6"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Added all five values", "2": "Subtracted wrong way", "3": "Arithmetic error"}
            })
    return questions

def g6_ch7_fractions(qnum):
    """Chapter 7: Fractions"""
    questions = []
    for i in range(qnum):
        variant = i % 5
        if variant == 0:
            # Multiplication of fractions
            n1, d1 = random.randint(1, 5), random.choice([3, 4, 5, 6, 7, 8])
            n2, d2 = random.randint(1, 5), random.choice([3, 4, 5, 6, 7, 8])
            prod_n = n1 * n2
            prod_d = d1 * d2
            g = math.gcd(prod_n, prod_d)
            ans_n, ans_d = prod_n // g, prod_d // g
            correct = f"{ans_n}/{ans_d}" if ans_d != 1 else str(ans_n)
            wrong = [f"{n1+n2}/{d1+d2}", f"{n1*n2}/{d1+d2}", f"{ans_n+1}/{ans_d}"]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            questions.append({
                "stem": f"{name} has {n1}/{d1} of a cake. She eats {n2}/{d2} of her share. What fraction of the whole cake did she eat?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 50,
                "tags": ["fractions", "multiplication"],
                "topic": "ncert_g6_fractions",
                "chapter": "Ch7: Fractions",
                "hint": {"level_0": "Multiply numerators together and denominators together.", "level_1": f"{n1}/{d1} × {n2}/{d2} = ({n1}×{n2})/({d1}×{d2})", "level_2": f"= {prod_n}/{prod_d} = {correct}"},
                "curriculum_tags": ["NCERT_6_7"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Added fractions instead", "2": "Did not simplify", "3": "Multiplied wrong parts"}
            })
        elif variant == 1:
            # Division of fractions
            n1, d1 = random.randint(1, 6), random.choice([2, 3, 4, 5, 6])
            n2, d2 = random.randint(1, 4), random.choice([2, 3, 4, 5])
            res_n = n1 * d2
            res_d = d1 * n2
            g = math.gcd(res_n, res_d)
            ans_n, ans_d = res_n // g, res_d // g
            correct = f"{ans_n}/{ans_d}" if ans_d != 1 else str(ans_n)
            wrong = [f"{n1*n2}/{d1*d2}", f"{d1*d2}/{n1*n2}", f"{ans_n}/{ans_d+1}"]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Divide: {n1}/{d1} ÷ {n2}/{d2}",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 55,
                "tags": ["fractions", "division"],
                "topic": "ncert_g6_fractions",
                "chapter": "Ch7: Fractions",
                "hint": {"level_0": "To divide fractions, multiply by the reciprocal.", "level_1": f"{n1}/{d1} × {d2}/{n2} = ?", "level_2": f"= {res_n}/{res_d} = {correct}"},
                "curriculum_tags": ["NCERT_6_7"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Multiplied without flipping", "2": "Flipped wrong fraction", "3": "Simplification error"}
            })
        elif variant == 2:
            # Word problem with mixed numbers
            whole1 = random.randint(1, 4)
            n1, d = random.randint(1, 3), random.choice([4, 5, 6, 8])
            whole2 = random.randint(1, 3)
            n2 = random.randint(1, d-1)
            imp1 = whole1 * d + n1
            imp2 = whole2 * d + n2
            sum_n = imp1 + imp2
            g = math.gcd(sum_n, d)
            w = sum_n // d
            rem = sum_n % d
            if rem == 0:
                correct = str(w)
            else:
                correct = f"{w} {rem//math.gcd(rem,d)}/{d//math.gcd(rem,d)}"
            wrong = [f"{whole1+whole2} {n1+n2}/{d}", f"{w+1}", f"{w} {rem+1}/{d}"]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            food = random.choice(FOODS)
            questions.append({
                "stem": f"{name} ate {whole1} {n1}/{d} plates of {food} on Monday and {whole2} {n2}/{d} plates on Tuesday. How much total?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 50,
                "tags": ["fractions", "mixed-numbers"],
                "topic": "ncert_g6_fractions",
                "chapter": "Ch7: Fractions",
                "hint": {"level_0": "Convert to improper fractions, add, then convert back.", "level_1": f"{imp1}/{d} + {imp2}/{d} = {sum_n}/{d}", "level_2": f"= {correct}"},
                "curriculum_tags": ["NCERT_6_7"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Added whole parts and fraction parts separately wrong", "2": "Did not convert to improper", "3": "Simplification error"}
            })
        elif variant == 3:
            # Comparison of fractions
            fracs = [(random.randint(1,7), random.randint(2,9)) for _ in range(4)]
            fracs = [(n, d) for n, d in fracs if n < d]
            while len(fracs) < 4:
                fracs.append((random.randint(1,5), random.randint(6,9)))
            fracs_val = [(n/d, f"{n}/{d}") for n, d in fracs]
            fracs_val.sort(reverse=True)
            largest = fracs_val[0][1]
            choices = [fv[1] for fv in fracs_val]
            random.shuffle(choices)
            questions.append({
                "stem": f"Which fraction is the largest: {', '.join(fv[1] for fv in fracs_val)}?",
                "choices": choices,
                "correct_answer": choices.index(largest),
                "difficulty_score": 45,
                "tags": ["fractions", "comparison"],
                "topic": "ncert_g6_fractions",
                "chapter": "Ch7: Fractions",
                "hint": {"level_0": "Convert all fractions to the same denominator, or convert to decimals.", "level_1": "Compare by cross multiplication or finding LCD.", "level_2": f"The largest is {largest}."},
                "curriculum_tags": ["NCERT_6_7"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Chose largest numerator", "2": "Chose smallest denominator", "3": "LCD calculation error"}
            })
        else:
            # Fraction of a quantity
            total = random.choice([24, 30, 36, 40, 48, 60, 72, 80, 90, 100])
            n, d = random.choice([(1,3),(2,3),(1,4),(3,4),(1,5),(2,5),(3,5),(1,6),(5,6)])
            answer = total * n // d
            correct = str(answer)
            wrong = [str(total // n), str(total - answer), str(answer + d)]
            choices = [correct] + wrong
            random.shuffle(choices)
            name = random.choice(NAMES)
            festival = random.choice(FESTIVALS)
            questions.append({
                "stem": f"For {festival}, {name} distributed {n}/{d} of {total} sweets to neighbours. How many sweets were given?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 40,
                "tags": ["fractions", "of-quantity"],
                "topic": "ncert_g6_fractions",
                "chapter": "Ch7: Fractions",
                "hint": {"level_0": f"Find {n}/{d} of {total}.", "level_1": f"{n}/{d} × {total} = ?", "level_2": f"{n} × {total} ÷ {d} = {answer}"},
                "curriculum_tags": ["NCERT_6_7"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Divided total by numerator", "2": "Multiplied by denominator", "3": "Arithmetic error"}
            })
    return questions

def g6_ch8_constructions(qnum):
    """Chapter 8: Playing with Constructions"""
    questions = []
    for i in range(qnum):
        variant = i % 3
        if variant == 0:
            # Angle construction
            angle = random.choice([30, 45, 60, 90, 120, 135, 150])
            steps_map = {
                60: "Draw an arc from vertex, then same radius arc from intersection point",
                90: "Construct 60° then bisect the angle between 60° and the line",
                120: "Two consecutive 60° arcs",
                30: "Bisect a 60° angle",
                45: "Bisect a 90° angle",
                135: "Construct 90° + bisect remaining 90°",
                150: "Construct 120° + bisect the 60° above it"
            }
            correct = steps_map[angle]
            all_steps = list(steps_map.values())
            wrong = [s for s in all_steps if s != correct][:3]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"Which method correctly constructs an angle of {angle}° using only a compass and ruler?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 55,
                "tags": ["constructions", "angle"],
                "topic": "ncert_g6_constructions",
                "chapter": "Ch8: Playing with Constructions",
                "hint": {"level_0": "Think about which standard angles you can construct and combine.", "level_1": f"60° is the basic constructible angle. How do you get {angle}° from it?", "level_2": correct},
                "curriculum_tags": ["NCERT_6_8"],
                "visual": True,
                "visual_alt": f"Construction steps for {angle}° angle",
                "diagnostics": {"1": "Mixed up angle construction steps", "2": "Confused bisection with construction", "3": "Wrong base angle used"}
            })
        elif variant == 1:
            # Triangle construction possibility
            a, b, c = sorted([random.randint(3, 15) for _ in range(3)])
            possible = (a + b > c)
            correct = "Yes" if possible else "No"
            reason = f"because {a} + {b} {'>' if possible else '≤'} {c}"
            choices = ["Yes, triangle inequality is satisfied", "No, triangle inequality is not satisfied",
                      "Yes, if it's a right triangle", "Cannot determine"]
            correct_idx = 0 if possible else 1
            questions.append({
                "stem": f"Can a triangle be drawn with sides {a} cm, {b} cm, and {c} cm?",
                "choices": choices,
                "correct_answer": correct_idx,
                "difficulty_score": 45,
                "tags": ["constructions", "triangle-inequality"],
                "topic": "ncert_g6_constructions",
                "chapter": "Ch8: Playing with Constructions",
                "hint": {"level_0": "Triangle inequality: sum of any two sides must be greater than the third.", "level_1": f"Check: {a}+{b}={a+b} vs {c}", "level_2": f"{a}+{b}={a+b} {'>' if possible else '≤'} {c}, so {'possible' if possible else 'not possible'}."},
                "curriculum_tags": ["NCERT_6_8"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Did not check all three pairs", "2": "Used wrong inequality direction", "3": "Added wrong sides"}
            })
        else:
            # Perpendicular bisector
            length = random.randint(4, 12)
            midpoint = length / 2
            correct = str(midpoint) if midpoint != int(midpoint) else str(int(midpoint))
            wrong = [str(length), str(int(midpoint) + 1), str(length * 2)]
            choices = [correct + " cm"] + [w + " cm" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"You construct the perpendicular bisector of a line segment AB = {length} cm. At what distance from A does it cross AB?",
                "choices": choices,
                "correct_answer": choices.index(correct + " cm"),
                "difficulty_score": 30,
                "tags": ["constructions", "perpendicular-bisector"],
                "topic": "ncert_g6_constructions",
                "chapter": "Ch8: Playing with Constructions",
                "hint": {"level_0": "A perpendicular bisector passes through the midpoint.", "level_1": f"Midpoint of {length} cm = ?", "level_2": f"Midpoint = {length}/2 = {correct} cm"},
                "curriculum_tags": ["NCERT_6_8"],
                "visual": True,
                "visual_alt": f"Line segment {length} cm with perpendicular bisector",
                "diagnostics": {"1": "Used full length", "2": "Calculated wrong midpoint", "3": "Confused bisector with median"}
            })
    return questions

def g6_ch9_symmetry(qnum):
    """Chapter 9: Symmetry"""
    questions = []
    shapes_sym = [("equilateral triangle", 3, 3), ("square", 4, 4), ("regular pentagon", 5, 5),
                  ("regular hexagon", 6, 6), ("rectangle", 2, 2), ("rhombus", 2, 2),
                  ("isosceles triangle", 1, 1), ("circle", "infinite", "infinite")]
    for i in range(qnum):
        variant = i % 4
        if variant == 0:
            # Lines of symmetry
            shape, lines, rot_order = random.choice(shapes_sym[:-1])
            correct = str(lines)
            wrong = [str(lines + 1), str(lines - 1) if lines > 1 else "2", str(lines * 2)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"How many lines of symmetry does a {shape} have?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 30,
                "tags": ["symmetry", "lines-of-symmetry"],
                "topic": "ncert_g6_symmetry",
                "chapter": "Ch9: Symmetry",
                "hint": {"level_0": "A line of symmetry divides the shape into two mirror-image halves.", "level_1": f"For regular polygons with n sides, there are n lines of symmetry.", "level_2": f"A {shape} has {lines} lines of symmetry."},
                "curriculum_tags": ["NCERT_6_9"],
                "visual": True,
                "visual_alt": f"{shape} with lines of symmetry shown",
                "diagnostics": {"1": "Counted sides instead", "2": "Confused with rotational order", "3": "Missed diagonal symmetry lines"}
            })
        elif variant == 1:
            # Rotational symmetry order
            shape, lines, rot_order = random.choice(shapes_sym[:-1])
            correct = str(rot_order)
            wrong = [str(int(rot_order) + 1 if isinstance(rot_order, int) else 5),
                     str(int(rot_order) - 1 if isinstance(rot_order, int) and rot_order > 1 else 3),
                     str(int(rot_order) * 2 if isinstance(rot_order, int) else 8)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"What is the order of rotational symmetry of a {shape}?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 40,
                "tags": ["symmetry", "rotational"],
                "topic": "ncert_g6_symmetry",
                "chapter": "Ch9: Symmetry",
                "hint": {"level_0": "Order = how many times the shape looks identical in one full 360° turn.", "level_1": f"Rotate by {360//int(rot_order) if isinstance(rot_order,int) and rot_order > 0 else 60}° each time.", "level_2": f"A {shape} has rotational symmetry of order {rot_order}."},
                "curriculum_tags": ["NCERT_6_9"],
                "visual": True,
                "visual_alt": f"{shape} showing rotational symmetry",
                "diagnostics": {"1": "Confused with line symmetry count", "2": "Used angle instead of count", "3": "Miscounted positions"}
            })
        elif variant == 2:
            # Rangoli/Indian pattern symmetry
            patterns = [("traditional rangoli with 4 petals", 4), ("star pattern", 6),
                       ("kolam with 8 loops", 8), ("swastik pattern", 4), ("lotus design", 8)]
            pattern, sym_lines = random.choice(patterns)
            correct = str(sym_lines)
            wrong = [str(sym_lines + 2), str(sym_lines - 2) if sym_lines > 2 else "6", str(sym_lines // 2)]
            choices = [correct] + wrong
            random.shuffle(choices)
            questions.append({
                "stem": f"A {pattern} has how many lines of symmetry?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 35,
                "tags": ["symmetry", "rangoli"],
                "topic": "ncert_g6_symmetry",
                "chapter": "Ch9: Symmetry",
                "hint": {"level_0": "Count how many ways you can fold the pattern so both halves match.", "level_1": f"A pattern with {sym_lines} equal parts around the centre has {sym_lines} lines of symmetry.", "level_2": f"This pattern has {sym_lines} lines of symmetry."},
                "curriculum_tags": ["NCERT_6_9"],
                "visual": True,
                "visual_alt": f"{pattern} with symmetry lines",
                "diagnostics": {"1": "Counted petals/loops instead", "2": "Only counted vertical/horizontal", "3": "Missed diagonal lines"}
            })
        else:
            # Angle of rotation
            shape, _, rot_order = random.choice([(s, l, r) for s, l, r in shapes_sym if isinstance(r, int) and r > 1])
            angle_rot = 360 // rot_order
            correct = str(angle_rot)
            wrong = [str(angle_rot * 2), str(angle_rot // 2) if angle_rot > 30 else str(angle_rot + 30), "180"]
            choices = [correct + "°"] + [w + "°" for w in wrong]
            random.shuffle(choices)
            questions.append({
                "stem": f"A {shape} looks the same after rotation of what minimum angle?",
                "choices": choices,
                "correct_answer": choices.index(correct + "°"),
                "difficulty_score": 45,
                "tags": ["symmetry", "angle-of-rotation"],
                "topic": "ncert_g6_symmetry",
                "chapter": "Ch9: Symmetry",
                "hint": {"level_0": "Minimum angle of rotation = 360° ÷ order of rotational symmetry", "level_1": f"Order = {rot_order}, so angle = 360° ÷ {rot_order}", "level_2": f"360° ÷ {rot_order} = {angle_rot}°"},
                "curriculum_tags": ["NCERT_6_9"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Used 180° instead of 360°", "2": "Multiplied instead of dividing", "3": "Used wrong order"}
            })
    return questions

def g6_ch10_integers(qnum):
    """Chapter 10: The Other Side of Zero"""
    questions = []
    for i in range(qnum):
        variant = i % 5
        if variant == 0:
            # Addition of integers
            a = random.randint(-20, 20)
            b = random.randint(-20, 20)
            result = a + b
            correct = str(result)
            wrong = [str(a - b), str(abs(a) + abs(b)), str(-(a + b))]
            choices = [correct] + [w for w in wrong if w != correct][:3]
            while len(choices) < 4:
                choices.append(str(result + random.choice([-1, 1, 2])))
            random.shuffle(choices)
            questions.append({
                "stem": f"Calculate: ({a}) + ({b}) = ?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 35,
                "tags": ["integers", "addition"],
                "topic": "ncert_g6_integers",
                "chapter": "Ch10: The Other Side of Zero",
                "hint": {"level_0": "Use the number line: start at first number, move right for positive, left for negative.", "level_1": f"Start at {a}, move {'right' if b > 0 else 'left'} by {abs(b)}.", "level_2": f"({a}) + ({b}) = {result}"},
                "curriculum_tags": ["NCERT_6_10"],
                "visual": True,
                "visual_alt": f"Number line showing {a} + {b}",
                "diagnostics": {"1": "Sign error", "2": "Subtracted instead of adding", "3": "Wrong direction on number line"}
            })
        elif variant == 1:
            # Subtraction of integers
            a = random.randint(-15, 15)
            b = random.randint(-15, 15)
            result = a - b
            correct = str(result)
            wrong = [str(a + b), str(b - a), str(-result)]
            choices = [correct] + [w for w in wrong if w != correct][:3]
            while len(choices) < 4:
                choices.append(str(result + random.choice([-2, 2, 3])))
            random.shuffle(choices)
            questions.append({
                "stem": f"Calculate: ({a}) - ({b}) = ?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 45,
                "tags": ["integers", "subtraction"],
                "topic": "ncert_g6_integers",
                "chapter": "Ch10: The Other Side of Zero",
                "hint": {"level_0": "Subtracting is the same as adding the opposite.", "level_1": f"({a}) - ({b}) = ({a}) + ({-b})", "level_2": f"= {a} + {-b} = {result}"},
                "curriculum_tags": ["NCERT_6_10"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Added instead of subtracted", "2": "Wrong sign for negative subtraction", "3": "Reversed operands"}
            })
        elif variant == 2:
            # Ordering integers
            nums = random.sample(range(-20, 21), 5)
            sorted_nums = sorted(nums)
            correct = ", ".join(map(str, sorted_nums))
            wrong1 = ", ".join(map(str, sorted(nums, reverse=True)))
            wrong2 = ", ".join(map(str, sorted(nums, key=abs)))
            wrong3 = ", ".join(map(str, [sorted_nums[0], sorted_nums[2], sorted_nums[1], sorted_nums[3], sorted_nums[4]]))
            choices = [correct, wrong1, wrong2, wrong3]
            random.shuffle(choices)
            questions.append({
                "stem": f"Arrange in ascending order: {', '.join(map(str, nums))}",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 35,
                "tags": ["integers", "ordering"],
                "topic": "ncert_g6_integers",
                "chapter": "Ch10: The Other Side of Zero",
                "hint": {"level_0": "Negative numbers are always less than positive. Among negatives, the one farther from 0 is smaller.", "level_1": f"Most negative first: {sorted_nums[0]}", "level_2": f"Order: {correct}"},
                "curriculum_tags": ["NCERT_6_10"],
                "visual": True,
                "visual_alt": "Number line with integers marked",
                "diagnostics": {"1": "Sorted by absolute value", "2": "Confused ascending/descending", "3": "Put negatives in wrong order"}
            })
        elif variant == 3:
            # Real-world context
            contexts = [
                ("temperature", "°C", -10, 40),
                ("depth below sea level", "m", -100, 0),
                ("bank balance", "₹", -500, 5000),
                ("floors (basement)", "floors", -3, 10),
            ]
            ctx_name, unit, low, high = random.choice(contexts)
            start = random.randint(low, high)
            change = random.randint(-15, 15)
            result = start + change
            correct = str(result)
            wrong = [str(start - change), str(abs(start + change)), str(start)]
            choices = [correct + f" {unit}"] + [w + f" {unit}" for w in wrong]
            random.shuffle(choices)
            name = random.choice(NAMES)
            city = random.choice(CITIES)
            if ctx_name == "temperature":
                stem = f"The temperature in {city} was {start}°C. It {'rose' if change > 0 else 'dropped'} by {abs(change)}°C. What is the new temperature?"
            elif ctx_name == "depth below sea level":
                stem = f"A submarine is at {start} m. It {'rises' if change > 0 else 'dives'} {abs(change)} m. What is its new position?"
            elif ctx_name == "bank balance":
                stem = f"{name}'s bank balance is ₹{start}. After a {'deposit' if change > 0 else 'withdrawal'} of ₹{abs(change)}, what is the balance?"
            else:
                stem = f"{name} is on floor {start}. The lift goes {'up' if change > 0 else 'down'} {abs(change)} floors. Which floor is {name} on now?"
            questions.append({
                "stem": stem,
                "choices": choices,
                "correct_answer": choices.index(correct + f" {unit}"),
                "difficulty_score": 40,
                "tags": ["integers", "real-world"],
                "topic": "ncert_g6_integers",
                "chapter": "Ch10: The Other Side of Zero",
                "hint": {"level_0": f"{'Rise/deposit/up means add.' if change > 0 else 'Drop/withdrawal/down means subtract.'}", "level_1": f"{start} {'+ ' if change > 0 else '- '}{abs(change)} = ?", "level_2": f"= {result} {unit}"},
                "curriculum_tags": ["NCERT_6_10"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Applied change in wrong direction", "2": "Sign confusion", "3": "Arithmetic error"}
            })
        else:
            # Multiplication of integers (sign rules)
            a = random.randint(-12, 12)
            b = random.randint(-12, 12)
            if a == 0: a = random.choice([-5, 5])
            if b == 0: b = random.choice([-3, 3])
            result = a * b
            correct = str(result)
            wrong = [str(-result), str(a + b), str(abs(a * b))]
            choices = [correct] + [w for w in wrong if w != correct][:3]
            while len(choices) < 4:
                choices.append(str(result + random.choice([-3, 3])))
            random.shuffle(choices)
            questions.append({
                "stem": f"Calculate: ({a}) × ({b}) = ?",
                "choices": choices,
                "correct_answer": choices.index(correct),
                "difficulty_score": 40,
                "tags": ["integers", "multiplication"],
                "topic": "ncert_g6_integers",
                "chapter": "Ch10: The Other Side of Zero",
                "hint": {"level_0": "Same signs → positive result. Different signs → negative result.", "level_1": f"({'+' if a > 0 else '-'}) × ({'+' if b > 0 else '-'}) = {'+'  if (a>0)==(b>0) else '-'}", "level_2": f"({a}) × ({b}) = {result}"},
                "curriculum_tags": ["NCERT_6_10"],
                "visual": False,
                "visual_alt": None,
                "diagnostics": {"1": "Wrong sign rule applied", "2": "Multiplication error", "3": "Added instead of multiplied"}
            })
    return questions

# ============================================================
# SVG GENERATION
# ============================================================

def generate_svg_for_question(q, grade):
    """Generate appropriate SVG visual for a question."""
    qid = q["id"]
    tags = q["tags"]

    if "perimeter" in tags or "area" in tags or "rectangle" in tags:
        return svg_rectangle(qid, grade)
    elif "triangle" in tags:
        return svg_triangle(qid, grade)
    elif "angle" in tags or "angles" in tags:
        return svg_angle(qid, grade)
    elif "circle" in tags:
        return svg_circle(qid, grade)
    elif "cube" in tags or "cuboid" in tags:
        return svg_cuboid(qid, grade)
    elif "number-line" in tags or "integers" in tags:
        return svg_number_line(qid, grade)
    elif "pie-chart" in tags:
        return svg_pie_chart(qid, grade)
    elif "factor" in tags or "factorization" in tags or "factor-tree" in tags:
        return svg_factor_tree(qid, grade)
    elif "symmetry" in tags or "rotational" in tags or "rangoli" in tags:
        return svg_symmetry(qid, grade)
    elif "probability" in tags:
        return svg_probability_bag(qid, grade)
    elif "parallelogram" in tags:
        return svg_parallelogram(qid, grade)
    elif "composite" in tags or "irregular" in tags:
        return svg_composite(qid, grade)
    elif "lines" in tags or "vertically-opposite" in tags or "angles-on-line" in tags or "complementary" in tags or "supplementary" in tags:
        return svg_lines(qid, grade)
    elif "figurate" in tags or "square-numbers" in tags:
        return svg_dot_pattern(qid, grade)
    elif "magic-square" in tags:
        return svg_magic_square(qid, grade)
    elif "sieve" in tags:
        return svg_number_grid(qid, grade)
    elif "perpendicular-bisector" in tags:
        return svg_bisector(qid, grade)
    elif "lines-of-symmetry" in tags:
        return svg_symmetry(qid, grade)
    else:
        return svg_generic(qid, grade)

def svg_rectangle(qid, grade):
    content = '''  <rect x="40" y="30" width="180" height="90" fill="none" stroke="#2196F3" stroke-width="2"/>
  <text x="130" y="140" text-anchor="middle" font-size="11" fill="#333">length</text>
  <text x="20" y="80" text-anchor="middle" font-size="11" fill="#333" transform="rotate(-90,20,80)">width</text>
  <line x1="40" y1="125" x2="220" y2="125" stroke="#666" stroke-width="0.5" stroke-dasharray="3"/>'''
    return make_svg(qid, grade, content)

def svg_triangle(qid, grade):
    content = '''  <polygon points="130,20 40,130 220,130" fill="none" stroke="#4CAF50" stroke-width="2"/>
  <line x1="130" y1="20" x2="130" y2="130" stroke="#FF9800" stroke-width="1" stroke-dasharray="4"/>
  <text x="130" y="145" text-anchor="middle" font-size="10" fill="#333">base</text>
  <text x="138" y="80" font-size="10" fill="#FF9800">h</text>'''
    return make_svg(qid, grade, content)

def svg_angle(qid, grade):
    content = '''  <line x1="30" y1="120" x2="230" y2="120" stroke="#333" stroke-width="2"/>
  <line x1="30" y1="120" x2="160" y2="30" stroke="#333" stroke-width="2"/>
  <path d="M 60 120 A 30 30 0 0 0 48 100" fill="none" stroke="#E91E63" stroke-width="2"/>
  <text x="65" y="105" font-size="11" fill="#E91E63">?°</text>'''
    return make_svg(qid, grade, content)

def svg_circle(qid, grade):
    content = '''  <circle cx="130" cy="75" r="55" fill="none" stroke="#9C27B0" stroke-width="2"/>
  <line x1="130" y1="75" x2="185" y2="75" stroke="#FF5722" stroke-width="2"/>
  <circle cx="130" cy="75" r="3" fill="#333"/>
  <text x="155" y="68" font-size="11" fill="#FF5722">r</text>'''
    return make_svg(qid, grade, content)

def svg_cuboid(qid, grade):
    content = '''  <polygon points="60,50 180,50 180,120 60,120" fill="none" stroke="#2196F3" stroke-width="2"/>
  <polygon points="60,50 90,30 210,30 180,50" fill="none" stroke="#2196F3" stroke-width="2"/>
  <polygon points="180,50 210,30 210,100 180,120" fill="none" stroke="#2196F3" stroke-width="2"/>
  <text x="120" y="135" font-size="10" fill="#333">l</text>
  <text x="195" y="75" font-size="10" fill="#333">h</text>
  <text x="195" y="25" font-size="10" fill="#333">w</text>'''
    return make_svg(qid, grade, content)

def svg_number_line(qid, grade):
    content = '''  <line x1="10" y1="75" x2="250" y2="75" stroke="#333" stroke-width="2"/>
  <polygon points="250,75 245,72 245,78" fill="#333"/>'''
    for i, val in enumerate(range(-5, 6)):
        x = 30 + i * 20
        content += f'\n  <line x1="{x}" y1="70" x2="{x}" y2="80" stroke="#333" stroke-width="1.5"/>'
        content += f'\n  <text x="{x}" y="95" text-anchor="middle" font-size="9" fill="#333">{val}</text>'
    content += '\n  <circle cx="130" cy="75" r="4" fill="#E91E63"/>'
    return make_svg(qid, grade, content)

def svg_pie_chart(qid, grade):
    content = '''  <circle cx="130" cy="75" r="60" fill="#E3F2FD" stroke="#1976D2" stroke-width="1"/>
  <path d="M 130 75 L 130 15 A 60 60 0 0 1 182 45 Z" fill="#1976D2"/>
  <path d="M 130 75 L 182 45 A 60 60 0 0 1 190 75 Z" fill="#4CAF50"/>
  <path d="M 130 75 L 190 75 A 60 60 0 0 1 130 135 Z" fill="#FF9800"/>
  <path d="M 130 75 L 130 135 A 60 60 0 0 1 130 15 Z" fill="#9C27B0" opacity="0.7"/>
  <text x="155" y="40" font-size="8" fill="white">40%</text>
  <text x="165" y="70" font-size="8" fill="white">25%</text>
  <text x="150" y="110" font-size="8" fill="white">20%</text>
  <text x="100" y="85" font-size="8" fill="white">15%</text>'''
    return make_svg(qid, grade, content)

def svg_factor_tree(qid, grade):
    content = '''  <text x="130" y="20" text-anchor="middle" font-size="12" fill="#333" font-weight="bold">N</text>
  <line x1="120" y1="25" x2="90" y2="50" stroke="#666" stroke-width="1"/>
  <line x1="140" y1="25" x2="170" y2="50" stroke="#666" stroke-width="1"/>
  <circle cx="90" cy="58" r="12" fill="#E3F2FD" stroke="#1976D2" stroke-width="1"/>
  <circle cx="170" cy="58" r="12" fill="#E3F2FD" stroke="#1976D2" stroke-width="1"/>
  <line x1="80" y1="68" x2="60" y2="93" stroke="#666" stroke-width="1"/>
  <line x1="100" y1="68" x2="120" y2="93" stroke="#666" stroke-width="1"/>
  <circle cx="60" cy="100" r="10" fill="#C8E6C9" stroke="#4CAF50" stroke-width="1"/>
  <circle cx="120" cy="100" r="10" fill="#C8E6C9" stroke="#4CAF50" stroke-width="1"/>
  <text x="60" y="104" text-anchor="middle" font-size="9" fill="#333">p</text>
  <text x="120" y="104" text-anchor="middle" font-size="9" fill="#333">q</text>'''
    return make_svg(qid, grade, content)

def svg_symmetry(qid, grade):
    content = '''  <polygon points="130,20 170,55 155,100 105,100 90,55" fill="#E8F5E9" stroke="#4CAF50" stroke-width="2"/>
  <line x1="130" y1="15" x2="130" y2="105" stroke="#FF5722" stroke-width="1" stroke-dasharray="4"/>
  <line x1="85" y1="55" x2="175" y2="75" stroke="#FF5722" stroke-width="1" stroke-dasharray="4"/>
  <line x1="175" y1="55" x2="85" y2="75" stroke="#FF5722" stroke-width="1" stroke-dasharray="4"/>'''
    return make_svg(qid, grade, content)

def svg_probability_bag(qid, grade):
    content = '''  <path d="M 80 40 Q 80 30 100 30 L 160 30 Q 180 30 180 40 L 185 50 L 75 50 Z" fill="#795548" stroke="#5D4037" stroke-width="1"/>
  <ellipse cx="130" cy="90" rx="55" ry="50" fill="#EFEBE9" stroke="#795548" stroke-width="2"/>
  <circle cx="110" cy="80" r="10" fill="#F44336"/>
  <circle cx="135" cy="75" r="10" fill="#F44336"/>
  <circle cx="150" cy="90" r="10" fill="#2196F3"/>
  <circle cx="120" cy="100" r="10" fill="#2196F3"/>
  <circle cx="145" cy="105" r="10" fill="#4CAF50"/>
  <circle cx="105" cy="100" r="10" fill="#4CAF50"/>'''
    return make_svg(qid, grade, content)

def svg_parallelogram(qid, grade):
    content = '''  <polygon points="70,120 40,40 200,40 230,120" fill="none" stroke="#FF5722" stroke-width="2"/>
  <line x1="200" y1="40" x2="200" y2="120" stroke="#2196F3" stroke-width="1" stroke-dasharray="4"/>
  <text x="135" y="135" text-anchor="middle" font-size="10" fill="#333">base</text>
  <text x="208" y="85" font-size="10" fill="#2196F3">h</text>'''
    return make_svg(qid, grade, content)

def svg_composite(qid, grade):
    content = '''  <path d="M 40 130 L 40 40 L 160 40 L 160 80 L 220 80 L 220 130 Z" fill="#E3F2FD" stroke="#1976D2" stroke-width="2"/>
  <text x="100" y="35" text-anchor="middle" font-size="9" fill="#333">a</text>
  <text x="30" y="90" font-size="9" fill="#333">b</text>
  <text x="190" y="75" font-size="9" fill="#333">c</text>
  <text x="228" y="110" font-size="9" fill="#333">d</text>'''
    return make_svg(qid, grade, content)

def svg_lines(qid, grade):
    content = '''  <line x1="20" y1="100" x2="240" y2="100" stroke="#333" stroke-width="2"/>
  <line x1="60" y1="140" x2="200" y2="30" stroke="#333" stroke-width="2"/>
  <path d="M 115 100 A 20 20 0 0 0 108 85" fill="none" stroke="#E91E63" stroke-width="2"/>
  <text x="100" y="82" font-size="10" fill="#E91E63">a°</text>
  <text x="125" y="95" font-size="10" fill="#2196F3">b°</text>'''
    return make_svg(qid, grade, content)

def svg_dot_pattern(qid, grade):
    content = ''
    # Draw a triangular dot pattern
    rows = 4
    for r in range(rows):
        for c in range(r + 1):
            x = 130 - r * 10 + c * 20
            y = 20 + r * 30
            content += f'\n  <circle cx="{x}" cy="{y}" r="5" fill="#1976D2"/>'
    return make_svg(qid, grade, content)

def svg_magic_square(qid, grade):
    content = '''  <rect x="65" y="15" width="130" height="130" fill="none" stroke="#333" stroke-width="2"/>'''
    for i in range(3):
        for j in range(3):
            x = 65 + j * 43.3
            y = 15 + i * 43.3
            content += f'\n  <rect x="{x}" y="{y}" width="43.3" height="43.3" fill="none" stroke="#333" stroke-width="1"/>'
    # Fill with magic square values
    vals = [[2,7,6],[9,5,1],[4,3,8]]
    for i in range(3):
        for j in range(3):
            x = 65 + j * 43.3 + 21.6
            y = 15 + i * 43.3 + 28
            content += f'\n  <text x="{x}" y="{y}" text-anchor="middle" font-size="14" fill="#1976D2">{vals[i][j]}</text>'
    return make_svg(qid, grade, content)

def svg_number_grid(qid, grade):
    content = ''
    # 5x6 grid
    for i in range(5):
        for j in range(6):
            x = 20 + j * 40
            y = 10 + i * 28
            num = i * 6 + j + 1
            is_prime = num > 1 and all(num % d != 0 for d in range(2, int(num**0.5)+1))
            fill = "#C8E6C9" if is_prime else "#FFF"
            content += f'\n  <rect x="{x}" y="{y}" width="38" height="26" fill="{fill}" stroke="#999" stroke-width="0.5"/>'
            content += f'\n  <text x="{x+19}" y="{y+17}" text-anchor="middle" font-size="10" fill="#333">{num}</text>'
    return make_svg(qid, grade, content)

def svg_bisector(qid, grade):
    content = '''  <line x1="40" y1="75" x2="220" y2="75" stroke="#333" stroke-width="2"/>
  <line x1="130" y1="20" x2="130" y2="130" stroke="#E91E63" stroke-width="1.5" stroke-dasharray="4"/>
  <circle cx="40" cy="75" r="3" fill="#333"/>
  <circle cx="220" cy="75" r="3" fill="#333"/>
  <circle cx="130" cy="75" r="3" fill="#E91E63"/>
  <text x="35" y="92" font-size="10" fill="#333">A</text>
  <text x="215" y="92" font-size="10" fill="#333">B</text>
  <text x="135" y="92" font-size="10" fill="#E91E63">M</text>'''
    return make_svg(qid, grade, content)

def svg_generic(qid, grade):
    content = '''  <rect x="30" y="20" width="200" height="110" rx="10" fill="#F3E5F5" stroke="#9C27B0" stroke-width="1"/>
  <text x="130" y="75" text-anchor="middle" font-size="12" fill="#6A1B9A">Think!</text>
  <text x="130" y="95" text-anchor="middle" font-size="9" fill="#666">Visual reasoning question</text>'''
    return make_svg(qid, grade, content)

# ============================================================
# MAIN GENERATION
# ============================================================

def generate_grade5():
    """Generate 300 questions for Grade 5."""
    questions = []

    # Distribution across 15 chapters (total 300)
    chapter_counts = {
        'ch1': 20, 'ch2': 22, 'ch3': 22, 'ch4': 20, 'ch5': 20,
        'ch6': 20, 'ch7': 22, 'ch8': 20, 'ch9': 20, 'ch10': 18,
        'ch11': 20, 'ch12': 20, 'ch13': 18, 'ch14': 20, 'ch15': 18
    }

    generators = {
        'ch1': g5_ch1_large_numbers,
        'ch2': g5_ch2_factors_multiples,
        'ch3': g5_ch3_fractions,
        'ch4': g5_ch4_decimals,
        'ch5': g5_ch5_measurement,
        'ch6': g5_ch6_percentage,
        'ch7': g5_ch7_geometry,
        'ch8': g5_ch8_perimeter_area,
        'ch9': g5_ch9_data_handling,
        'ch10': g5_ch10_patterns,
        'ch11': g5_ch11_volume,
        'ch12': g5_ch12_speed,
        'ch13': g5_ch13_profit_loss,
        'ch14': g5_ch14_symmetry,
        'ch15': g5_ch15_maps,
    }

    for ch, count in chapter_counts.items():
        ch_questions = generators[ch](count)
        questions.extend(ch_questions)

    # Assign IDs and finalize
    final_questions = []
    for idx, q in enumerate(questions[:300]):
        qid = f"NCERT-G5-{idx+1:03d}"
        diff_score = q.get("difficulty_score", 50)

        fq = {
            "id": qid,
            "stem": q["stem"],
            "choices": q["choices"],
            "correct_answer": q["correct_answer"],
            "difficulty_tier": difficulty_tier(diff_score),
            "difficulty_score": diff_score,
            "visual_svg": None,
            "visual_alt": q.get("visual_alt"),
            "diagnostics": q.get("diagnostics", {}),
            "tags": q["tags"],
            "topic": q["topic"],
            "chapter": q["chapter"],
            "hint": q["hint"],
            "curriculum_tags": q["curriculum_tags"],
            "irt_params": irt_params(diff_score, 5)
        }

        # Generate visual for ~40% of questions
        if q.get("visual", False) or (random.random() < 0.4 and not q.get("visual", False)):
            svg_file = generate_svg_for_question(fq, 5)
            fq["visual_svg"] = svg_file

        final_questions.append(fq)

    return final_questions

def generate_grade6():
    """Generate 300 questions for Grade 6."""
    questions = []

    # Distribution across 10 chapters (total 300)
    chapter_counts = {
        'ch1': 30, 'ch2': 30, 'ch3': 30, 'ch4': 30, 'ch5': 30,
        'ch6': 30, 'ch7': 30, 'ch8': 30, 'ch9': 30, 'ch10': 30
    }

    generators = {
        'ch1': g6_ch1_patterns,
        'ch2': g6_ch2_lines_angles,
        'ch3': g6_ch3_number_play,
        'ch4': g6_ch4_data_handling,
        'ch5': g6_ch5_prime_time,
        'ch6': g6_ch6_perimeter_area,
        'ch7': g6_ch7_fractions,
        'ch8': g6_ch8_constructions,
        'ch9': g6_ch9_symmetry,
        'ch10': g6_ch10_integers,
    }

    for ch, count in chapter_counts.items():
        ch_questions = generators[ch](count)
        questions.extend(ch_questions)

    # Assign IDs and finalize
    final_questions = []
    for idx, q in enumerate(questions[:300]):
        qid = f"NCERT-G6-{idx+1:03d}"
        diff_score = q.get("difficulty_score", 50)

        fq = {
            "id": qid,
            "stem": q["stem"],
            "choices": q["choices"],
            "correct_answer": q["correct_answer"],
            "difficulty_tier": difficulty_tier(diff_score),
            "difficulty_score": diff_score,
            "visual_svg": None,
            "visual_alt": q.get("visual_alt"),
            "diagnostics": q.get("diagnostics", {}),
            "tags": q["tags"],
            "topic": q["topic"],
            "chapter": q["chapter"],
            "hint": q["hint"],
            "curriculum_tags": q["curriculum_tags"],
            "irt_params": irt_params(diff_score, 6)
        }

        if q.get("visual", False) or (random.random() < 0.4 and not q.get("visual", False)):
            svg_file = generate_svg_for_question(fq, 6)
            fq["visual_svg"] = svg_file

        final_questions.append(fq)

    return final_questions

def main():
    print("Generating NCERT Grade 5 questions...")
    g5_questions = generate_grade5()

    g5_output = {
        "topic_id": "ncert_g5",
        "topic_name": "NCERT Grade 5 Mathematics",
        "version": "2.0",
        "curriculum": "NCERT",
        "grade": 5,
        "total_questions": len(g5_questions),
        "questions": g5_questions
    }

    g5_path = os.path.join(G5_DIR, "ncert_g5_questions.json")
    with open(g5_path, 'w') as f:
        json.dump(g5_output, f, indent=2)
    print(f"  Grade 5: {len(g5_questions)} questions written to {g5_path}")

    print("Generating NCERT Grade 6 questions...")
    g6_questions = generate_grade6()

    g6_output = {
        "topic_id": "ncert_g6",
        "topic_name": "NCERT Grade 6 Mathematics (Ganita Prakash)",
        "version": "2.0",
        "curriculum": "NCERT",
        "grade": 6,
        "total_questions": len(g6_questions),
        "questions": g6_questions
    }

    g6_path = os.path.join(G6_DIR, "ncert_g6_questions.json")
    with open(g6_path, 'w') as f:
        json.dump(g6_output, f, indent=2)
    print(f"  Grade 6: {len(g6_questions)} questions written to {g6_path}")

    # Statistics
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    for grade, questions, label in [(5, g5_questions, "Grade 5"), (6, g6_questions, "Grade 6")]:
        print(f"\n{label}:")
        print(f"  Total questions: {len(questions)}")

        # By chapter
        chapters = {}
        for q in questions:
            ch = q["chapter"]
            chapters[ch] = chapters.get(ch, 0) + 1
        print(f"  Chapters covered: {len(chapters)}")
        for ch, cnt in sorted(chapters.items()):
            print(f"    {ch}: {cnt} questions")

        # By difficulty
        tiers = {}
        for q in questions:
            t = q["difficulty_tier"]
            tiers[t] = tiers.get(t, 0) + 1
        print(f"  Difficulty distribution:")
        for t in ["easy", "medium", "hard", "advanced"]:
            print(f"    {t}: {tiers.get(t, 0)}")

        # Visuals
        vis_count = sum(1 for q in questions if q["visual_svg"])
        print(f"  Questions with visuals: {vis_count} ({vis_count*100//len(questions)}%)")

        # IRT range
        b_vals = [q["irt_params"]["b"] for q in questions]
        print(f"  IRT b range: {min(b_vals):.2f} to {max(b_vals):.2f}")

    # Print samples
    print("\n" + "="*60)
    print("SAMPLE QUESTIONS")
    print("="*60)

    for grade, questions, label in [(5, g5_questions, "Grade 5"), (6, g6_questions, "Grade 6")]:
        print(f"\n--- {label} Samples ---")
        samples = random.sample(questions, 5)
        for s in samples:
            print(f"\n  [{s['id']}] {s['chapter']} | {s['difficulty_tier']}")
            print(f"  Q: {s['stem']}")
            for idx, c in enumerate(s['choices']):
                marker = " *" if idx == s['correct_answer'] else ""
                print(f"     {chr(65+idx)}) {c}{marker}")
            if s['visual_svg']:
                print(f"  [Visual: {s['visual_svg']}]")

if __name__ == "__main__":
    main()
