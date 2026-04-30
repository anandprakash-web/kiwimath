#!/usr/bin/env python3
"""
Generate 300 Grade 5-6 Arithmetic & Missing Numbers questions (T2-901 to T2-1200)
for the Kiwimath math olympiad app.
"""

import json, random, math
from fractions import Fraction

random.seed(42)

CHARACTERS = [
    "Captain Kiwi", "Professor Panda", "Detective Dolphin", "Astronaut Ava",
    "Robot Rex", "Wizard Wally", "Pirate Penny", "Chef Cheetah",
    "Explorer Emma", "Ninja Nemo", "Knight Koko", "Agent Apollo",
    "Scientist Sam", "Dragon Dash", "Ranger Rosie"
]

def char():
    return random.choice(CHARACTERS)

def tier(score):
    if score <= 230: return "advanced"
    if score <= 270: return "expert"
    return "olympiad"

def make_hint(topic_hint, step_hints):
    """Build 6-level hint ladder."""
    return {
        "level_0": "Take a deep breath and think carefully before answering.",
        "level_1": topic_hint,
        "level_2": step_hints[0],
        "level_3": step_hints[1],
        "level_4": step_hints[2],
        "level_5": step_hints[3]
    }

def shuffle_choices(correct, wrongs, diagnostics_correct, diagnostics_wrongs):
    """Shuffle choices and return (choices, correct_index, diagnostics)."""
    items = [(correct, diagnostics_correct)] + list(zip(wrongs, diagnostics_wrongs))
    random.shuffle(items)
    choices = [str(item[0]) for item in items]
    diag = {}
    correct_idx = None
    for i, (val, msg) in enumerate(items):
        if val == correct and correct_idx is None:
            correct_idx = i
            diag[str(i)] = "Correct! " + msg
        else:
            diag[str(i)] = msg
    return choices, correct_idx, diag

questions = []
qid = 901

# ============================================================
# CATEGORY 1: Order of Operations (30 questions, IDs 901-930)
# ============================================================
def gen_order_of_ops():
    global qid
    templates = []

    # Sub-type A: Nested brackets (10q)
    expressions_a = [
        ("(12 + 8) × (15 - 9)", (12+8)*(15-9), [100, 130, 110]),
        ("(25 - 7) × (4 + 6)", (25-7)*(4+6), [170, 190, 160]),
        ("{[3 × (4 + 5)] - 7} × 2", (3*(4+5)-7)*2, [44, 54, 40]),
        ("[(8 + 2) × 5] - (3 × 4)", (8+2)*5 - 3*4, [36, 42, 30]),
        ("(100 - 36) ÷ (4 × 2)", (100-36)//(4*2), [9, 6, 12]),
        ("{[(2 + 3) × 4] + 5} × 2", ((2+3)*4+5)*2, [45, 55, 40]),
        ("(7 × 8 - 6) ÷ (2 + 3)", (7*8-6)//(2+3), [11, 9, 12]),
        ("[(15 + 25) ÷ 5] × (9 - 3)", (15+25)//5*(9-3), [46, 50, 42]),
        ("(6 × 9) - [(4 + 8) ÷ 3]", 6*9 - (4+8)//3, [52, 48, 56]),
        ("[(100 ÷ 4) + 15] × 2", (100//4+15)*2, [75, 85, 70]),
    ]
    for expr, ans, wrongs in expressions_a:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} needs your help! Evaluate: {expr}",
            "choices": None,
            "correct_answer": None,
            "difficulty_tier": tier(score),
            "difficulty_score": score,
            "visual_svg": None,
            "visual_alt": None,
            "diagnostics": None,
            "tags": ["order-of-operations", "PEMDAS", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Remember PEMDAS: Parentheses first, then Exponents, Multiplication/Division, Addition/Subtraction.",
                ["Start by solving what's inside the innermost brackets.",
                 f"After solving the innermost brackets, work outward step by step.",
                 f"Almost there! Combine the final operation carefully.",
                 f"The answer is {ans}. Work through each bracket level from inside out."]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Well done! You navigated the brackets perfectly! 🎉",
            ["Check the order — did you handle the brackets from inside out?",
             "Careful! Make sure you multiply/divide before adding/subtracting outside brackets.",
             "Not quite. Re-read the expression and track each bracket level."]
        )
        q["choices"] = choices
        q["correct_answer"] = ci
        q["diagnostics"] = diag
        questions.append(q)
        qid += 1

    # Sub-type B: PEMDAS tricky (10q)
    expressions_b = [
        ("8 + 2 × 5 - 3", 8+2*5-3, [17, 13, 19]),
        ("24 ÷ 6 + 3 × 7", 24//6+3*7, [28, 21, 30]),
        ("5 × 4 + 12 ÷ 3 - 2", 5*4+12//3-2, [20, 24, 16]),
        ("36 ÷ 6 × 3 + 4 - 1", 36//6*3+4-1, [17, 23, 15]),
        ("15 - 3 × 4 + 8 ÷ 2", 15-3*4+8//2, [10, 5, 9]),
        ("2 × 3 + 4 × 5 - 6", 2*3+4*5-6, [24, 44, 16]),
        ("48 ÷ 8 + 7 × 2 - 5", 48//8+7*2-5, [13, 15, 11]),
        ("9 + 16 ÷ 4 × 2 - 1", 9+16//4*2-1, [15, 16, 13]),
        ("100 - 8 × 11 + 5 × 2", 100-8*11+5*2, [22, 18, 24]),
        ("3 × 3 × 3 - 3 × 3 + 3", 3*3*3-3*3+3, [19, 24, 18]),
    ]
    for expr, ans, wrongs in expressions_b:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} set a challenge! What is {expr}?",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["order-of-operations", "PEMDAS", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Multiplication and division come before addition and subtraction!",
                ["First, find all multiplication and division operations.",
                 "Compute each multiplication/division, then add/subtract left to right.",
                 f"You're close! Double-check your arithmetic.",
                 f"The answer is {ans}. Remember: × and ÷ before + and −."]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Perfect! You nailed the order of operations! 🎉",
            ["You may have done operations left to right — remember PEMDAS!",
             "Double-check: did you multiply before adding?",
             "Not quite. Try computing × and ÷ first, then + and −."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

    # Sub-type C: Missing operator/number (10q)
    missing_ops = [
        ("7 ☐ 3 + 2 = 23", "×", ["÷", "+", "−"], "What operation on 7 and 3 gives 21, so 21+2=23?"),
        ("(12 ☐ 4) × 5 = 40", "−", ["÷", "+", "×"], "12 minus something gives 8, so 8×5=40."),
        ("(☐ + 7) × 3 = 36", "5", ["4", "6", "3"], "Something plus 7 = 12, and 12×3 = 36."),
        ("45 ÷ ☐ + 3 = 12", "5", ["9", "3", "15"], "45 ÷ ☐ = 9, so ☐ = 5."),
        ("☐ × 8 - 14 = 50", "8", ["7", "9", "6"], "☐ × 8 = 64, so ☐ = 8."),
        ("(20 + ☐) ÷ 6 = 5", "10", ["8", "12", "6"], "20 + ☐ = 30, so ☐ = 10."),
        ("3 × ☐ + 4 × 5 = 41", "7", ["8", "6", "9"], "3 × ☐ = 21, so ☐ = 7."),
        ("(☐ − 15) × 4 = 60", "30", ["25", "35", "20"], "☐ − 15 = 15, so ☐ = 30."),
        ("100 ÷ (2 × ☐) = 10", "5", ["4", "10", "2"], "2 × ☐ = 10, so ☐ = 5."),
        ("☐ × ☐ + 1 = 50 (☐ is the same number)", "7", ["8", "6", "9"], "☐² = 49, so ☐ = 7."),
    ]
    for expr, ans, wrongs, expl in missing_ops:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} found a mystery puzzle: {expr}. What goes in the ☐?",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["order-of-operations", "missing-number", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Work backwards from the answer to find the missing piece.",
                ["Look at the equation and isolate the unknown part.",
                 expl,
                 f"Try plugging in {ans} and see if it works!",
                 f"The answer is {ans}. {expl}"]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Brilliant! You cracked the code! 🎉",
            ["Close, but plug this back in and check — it doesn't balance.",
             "Try substituting this value — the equation won't hold.",
             "Not quite. Work backwards from the result to find the missing value."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

gen_order_of_ops()

# ============================================================
# CATEGORY 2: Exponents & Powers (25 questions, IDs 931-955)
# ============================================================
def gen_exponents():
    global qid

    # Computing powers (8q)
    power_qs = [
        ("2^10", 2**10, [1000, 512, 2048]),
        ("3^5", 3**5, [245, 243, 225]),  # fix: 3^5=243, need a wrong that's not 243
        ("5^4", 5**4, [600, 500, 650]),
        ("4^4", 4**4, [128, 512, 64]),
        ("7^3", 7**3, [353, 337, 349]),
        ("2^12", 2**12, [4000, 2048, 8192]),
        ("6^3", 6**3, [180, 256, 200]),
        ("9^3", 9**3, [729, 719, 739]),  # 9^3=729
    ]
    # Fix: 3^5 = 243, so wrongs shouldn't include 243
    power_qs[1] = ("3^5", 243, [245, 225, 235])
    # Fix: 9^3 = 729
    power_qs[7] = ("9^3", 729, [719, 739, 749])

    for expr, ans, wrongs in power_qs:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} asks: What is {expr}?",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["exponents", "powers", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                f"Remember, {expr} means multiplying the base by itself that many times.",
                [f"Write out the multiplication: e.g., 2^3 = 2 × 2 × 2.",
                 f"Compute step by step, multiplying one factor at a time.",
                 f"You're almost there — check your last multiplication!",
                 f"The answer is {ans}."]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Excellent! You computed the power correctly! 🎉",
            ["That's not quite right — try multiplying step by step.",
             "Double-check your multiplication chain.",
             "Close! Recount how many times you multiply the base."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

    # Comparing powers (8q)
    compare_qs = [
        ("Which is larger: 2^8 or 3^5?", "3^5 = 243", "2^8 = 256", "2^8",
         ["3^5", "They are equal", "Cannot determine"],
         "2^8 = 256 and 3^5 = 243, so 2^8 is larger."),
        ("Which is larger: 5^3 or 2^7?", "2^7 = 128", "5^3 = 125", "2^7",
         ["5^3", "They are equal", "Cannot determine"],
         "5^3 = 125 and 2^7 = 128, so 2^7 is larger."),
        ("Which is larger: 4^3 or 3^4?", "3^4 = 81", "4^3 = 64", "3^4",
         ["4^3", "They are equal", "Cannot determine"],
         "4^3 = 64 and 3^4 = 81, so 3^4 is larger."),
        ("Which is smaller: 6^2 or 2^6?", "6^2 = 36", "2^6 = 64", "6^2",
         ["2^6", "They are equal", "Cannot determine"],
         "6^2 = 36 < 2^6 = 64, so 6^2 is smaller."),
        ("Which is larger: 10^3 or 5^5?", "5^5 = 3125", "10^3 = 1000", "5^5",
         ["10^3", "They are equal", "Cannot determine"],
         "10^3 = 1000, 5^5 = 3125, so 5^5 is larger."),
        ("Which is larger: 2^10 or 10^3?", "2^10 = 1024", "10^3 = 1000", "2^10",
         ["10^3", "They are equal", "Cannot determine"],
         "2^10 = 1024 > 10^3 = 1000."),
        ("Arrange in order from smallest: 2^5, 3^3, 4^2", "2^5=32, 3^3=27, 4^2=16", "", "4^2 < 3^3 < 2^5",
         ["3^3 < 4^2 < 2^5", "2^5 < 3^3 < 4^2", "4^2 < 2^5 < 3^3"],
         "4^2=16, 3^3=27, 2^5=32."),
        ("What is 2^6 + 2^6?", "2 × 64", "", "128",
         ["64", "256", "96"],
         "2^6 = 64, so 64 + 64 = 128 = 2^7."),
    ]
    for i, item in enumerate(compare_qs):
        stem_text = item[0]
        ans = item[3]
        wrongs = item[4]
        explanation = item[5]
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} challenges you: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["exponents", "comparing-powers", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Compute each power separately, then compare.",
                ["Calculate the first power.", "Calculate the second power.",
                 "Now compare the two values.", explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Great comparison skills! 🎉",
            ["Compute both powers carefully before comparing.",
             "Not quite — double-check your calculations.",
             "Try computing each power step by step."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

    # Last digit patterns (9q)
    last_digit_qs = [
        ("What is the last digit of 7^100?", 1, [7, 9, 3], "Powers of 7 cycle: 7,9,3,1. 100÷4=25 remainder 0, so last digit is 1."),
        ("What is the last digit of 3^2023?", 7, [3, 9, 1], "Powers of 3 cycle: 3,9,7,1. 2023÷4 remainder 3, so last digit is 7."),
        ("What is the last digit of 2^50?", 4, [2, 8, 6], "Powers of 2 cycle: 2,4,8,6. 50÷4 remainder 2, so last digit is 4."),
        ("What is the last digit of 8^75?", 2, [8, 4, 6], "Powers of 8 cycle: 8,4,2,6. 75÷4 remainder 3, so last digit is 2."),
        ("What is the last digit of 4^200?", 6, [4, 2, 8], "Powers of 4 cycle: 4,6. 200÷2=100 remainder 0, so last digit is 6."),
        ("What is the last digit of 9^99?", 9, [1, 3, 7], "Powers of 9 cycle: 9,1. 99÷2 remainder 1, so last digit is 9."),
        ("What is the last digit of 6^500?", 6, [2, 4, 8], "Any power of 6 ends in 6."),
        ("What is the last digit of 13^42?", 9, [3, 1, 7], "Only the last digit matters: 3^42. Cycle: 3,9,7,1. 42÷4 remainder 2, so last digit is 9."),
        ("What is the units digit of 17^2024?", 1, [7, 9, 3], "Last digit of 7^2024. Cycle: 7,9,3,1. 2024÷4=506 remainder 0, so last digit is 1."),
    ]
    for stem_text, ans, wrongs, explanation in last_digit_qs:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} poses a tricky question: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["exponents", "last-digit", "patterns", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "The last digit of powers follows a repeating pattern (cycle).",
                ["Find the cycle of last digits for the base.",
                 "Determine the cycle length and divide the exponent by it.",
                 "Use the remainder to find the position in the cycle.",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Amazing! You mastered last-digit patterns! 🎉",
            ["Check the repeating cycle of last digits for this base.",
             "Not quite — find the cycle length and use the remainder.",
             "Try writing out the first few powers to spot the pattern."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

gen_exponents()

# ============================================================
# CATEGORY 3: Divisibility & Factors (30 questions, IDs 956-985)
# ============================================================
def gen_divisibility():
    global qid

    # GCD questions (10q)
    gcd_data = [
        (48, 36, math.gcd(48,36), [6, 8, 18]),
        (72, 54, math.gcd(72,54), [9, 6, 36]),
        (120, 84, math.gcd(120,84), [6, 24, 8]),
        (144, 60, math.gcd(144,60), [6, 24, 18]),
        (210, 154, math.gcd(210,154), [7, 28, 21]),
        (360, 240, math.gcd(360,240), [60, 40, 24]),
        (315, 189, math.gcd(315,189), [21, 9, 7]),
        (256, 192, math.gcd(256,192), [32, 16, 128]),
        (1001, 143, math.gcd(1001,143), [7, 13, 77]),
        (462, 330, math.gcd(462,330), [22, 33, 11]),
    ]
    for a, b, ans, wrongs in gcd_data:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} needs the GCD! What is the greatest common divisor of {a} and {b}?",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["GCD", "factors", "divisibility", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "The GCD is the largest number that divides both numbers evenly.",
                [f"Find the prime factorization of {a} and {b}.",
                 "Identify the common prime factors and their lowest powers.",
                 "Multiply the common factors together.",
                 f"GCD({a}, {b}) = {ans}."]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "You found the GCD! Excellent! 🎉",
            ["That's a common factor, but not the greatest one.",
             "Check your factorization — this doesn't divide both numbers.",
             "Close! Try listing all common factors to find the greatest."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

    # LCM questions (10q)
    lcm = lambda a, b: a * b // math.gcd(a, b)
    lcm_data = [
        (12, 18, lcm(12,18), [48, 72, 24]),
        (15, 20, lcm(15,20), [30, 120, 45]),
        (8, 14, lcm(8,14), [28, 112, 48]),
        (24, 36, lcm(24,36), [48, 144, 36]),
        (35, 25, lcm(35,25), [125, 350, 75]),
        (16, 28, lcm(16,28), [56, 224, 64]),
        (45, 60, lcm(45,60), [90, 360, 120]),
        (30, 42, lcm(30,42), [60, 420, 126]),
        (48, 72, lcm(48,72), [72, 288, 96]),
        (56, 84, lcm(56,84), [84, 336, 112]),
    ]
    for a, b, ans, wrongs in lcm_data:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} asks: What is the least common multiple of {a} and {b}?",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["LCM", "multiples", "divisibility", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "The LCM is the smallest number that both numbers divide into evenly.",
                [f"Find the prime factorizations of {a} and {b}.",
                 "Take the highest power of each prime factor.",
                 "Multiply them together to get the LCM.",
                 f"LCM({a}, {b}) = {ans}."]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Perfect! You found the LCM! 🎉",
            ["That's a common multiple, but not the least one.",
             "Check again — is this really a multiple of both numbers?",
             "Try listing multiples of each number until you find the first match."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

    # Factor counting & divisibility rules (10q)
    def count_factors(n):
        c = 0
        for i in range(1, n+1):
            if n % i == 0: c += 1
        return c

    factor_qs = [
        (f"How many factors does 72 have?", count_factors(72), [10, 14, 8], "72 = 2³ × 3², factors = (3+1)(2+1) = 12."),
        (f"How many factors does 100 have?", count_factors(100), [8, 12, 6], "100 = 2² × 5², factors = (2+1)(2+1) = 9."),
        (f"How many factors does 360 have?", count_factors(360), [20, 28, 18], "360 = 2³ × 3² × 5, factors = 4×3×2 = 24."),
        ("Which number is divisible by both 4 and 9?", 108, [102, 114, 98], "108 ÷ 4 = 27, 108 ÷ 9 = 12. Both work!"),
        ("Which of these is divisible by 11?", 253, [257, 249, 261], "253 ÷ 11 = 23. Check: 2-5+3 = 0, divisible by 11."),
        (f"How many factors does 48 have?", count_factors(48), [8, 12, 6], "48 = 2⁴ × 3, factors = 5×2 = 10."),
        ("A number is divisible by 6 if it is divisible by both 2 and 3. Which is divisible by 6?", 234, [235, 232, 245], "234: even (div by 2) and 2+3+4=9 (div by 3)."),
        ("What is the sum of all factors of 28?", 56, [48, 64, 42], "Factors of 28: 1,2,4,7,14,28. Sum = 56. (28 is a perfect number!)"),
        ("How many factors does 120 have?", count_factors(120), [12, 18, 14], "120 = 2³×3×5, factors = 4×2×2 = 16."),
        ("What is the smallest number divisible by 2, 3, 5, and 7?", 210, [150, 180, 420], "LCM(2,3,5,7) = 2×3×5×7 = 210."),
    ]
    for stem_text, ans, wrongs, explanation in factor_qs:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} wonders: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["factors", "divisibility-rules", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Use prime factorization to count factors systematically.",
                ["Break the number into prime factors.",
                 "Use the formula: multiply (exponent+1) for each prime.",
                 "Almost there! Check your factorization carefully.",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Wonderful! You're a divisibility expert! 🎉",
            ["Not quite — try a different factorization approach.",
             "Check your prime factorization carefully.",
             "Close! Recount the factors systematically."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

gen_divisibility()

# ============================================================
# CATEGORY 4: Prime Numbers (25 questions, IDs 986-1010)
# ============================================================
def gen_primes():
    global qid

    def is_prime(n):
        if n < 2: return False
        for i in range(2, int(n**0.5)+1):
            if n % i == 0: return False
        return True

    # Prime identification (8q)
    prime_id = [
        ("Which of these is a prime number?", 97, [91, 93, 95], "97 has no factors other than 1 and 97."),
        ("Which of these is NOT a prime number?", 51, [53, 59, 61], "51 = 3 × 17, so it's not prime."),
        ("What is the largest prime below 100?", 97, [93, 91, 89], "97 is prime. 98=2×49, 99=9×11."),
        ("How many prime numbers are there between 1 and 30?", 10, [8, 9, 11], "Primes: 2,3,5,7,11,13,17,19,23,29 = 10 primes."),
        ("What is the sum of the first 5 prime numbers?", 28, [26, 30, 25], "2+3+5+7+11 = 28."),
        ("Which is the only even prime number?", 2, [4, 6, 0], "2 is the only even prime — all other evens are divisible by 2."),
        ("What is the 15th prime number?", 47, [43, 51, 49], "Primes: 2,3,5,7,11,13,17,19,23,29,31,37,41,43,47."),
        ("How many primes are between 50 and 80?", 7, [6, 8, 5], "53,59,61,67,71,73,79 = 7 primes."),
    ]
    for stem_text, ans, wrongs, explanation in prime_id:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} asks: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["primes", "prime-identification", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "A prime number has exactly two factors: 1 and itself.",
                ["Check if the number is divisible by 2, 3, 5, or 7.",
                 "You only need to test prime divisors up to the square root.",
                 "If no small prime divides it, it's prime!",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "You know your primes! 🎉",
            ["Check divisibility more carefully.",
             "That number has a hidden factor — can you find it?",
             "Try testing small primes as divisors."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

    # Prime factorization (9q)
    pf_qs = [
        ("What is the prime factorization of 180?", "2² × 3² × 5", ["2³ × 3 × 5", "2 × 3² × 10", "2² × 3 × 15"], "180 = 4×45 = 2²×3²×5."),
        ("What is the prime factorization of 252?", "2² × 3² × 7", ["2³ × 3 × 7", "2 × 3³ × 7", "2² × 3 × 21"], "252 = 4×63 = 2²×3²×7."),
        ("What is the prime factorization of 420?", "2² × 3 × 5 × 7", ["2³ × 3 × 5 × 7", "2 × 3 × 5 × 14", "2² × 3 × 35"], "420 = 4×105 = 2²×3×5×7."),
        ("How many prime factors does 60 have (counting distinct)?", "3", ["4", "2", "5"], "60 = 2²×3×5: three distinct primes."),
        ("What is the prime factorization of 540?", "2² × 3³ × 5", ["2³ × 3² × 5", "2 × 3³ × 10", "2² × 3² × 15"], "540 = 4×135 = 2²×3³×5."),
        ("If n = 2³ × 5², what is n?", "200", ["150", "250", "100"], "2³×5² = 8×25 = 200."),
        ("The prime factorization of a number is 2 × 3 × 5 × 7. What is the number?", "210", ["180", "240", "315"], "2×3×5×7 = 210."),
        ("What is the prime factorization of 1001?", "7 × 11 × 13", ["7 × 11 × 11", "7 × 13 × 11", "11 × 13 × 7"],
         "1001 ÷ 7 = 143 = 11 × 13."),
        ("How many prime factors does 2310 have?", "5", ["4", "6", "3"], "2310 = 2×3×5×7×11: five distinct primes."),
    ]
    # Fix: "7 × 11 × 13" and "7 × 13 × 11" and "11 × 13 × 7" are the same. Fix wrongs:
    pf_qs[7] = ("What is the prime factorization of 1001?", "7 × 11 × 13", ["7 × 143", "11 × 91", "13 × 77"], "1001 ÷ 7 = 143 = 11 × 13.")

    for stem_text, ans, wrongs, explanation in pf_qs:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} challenges you: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["primes", "prime-factorization", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Divide by the smallest prime (2, then 3, then 5...) repeatedly.",
                ["Start by checking if the number is even.",
                 "Keep dividing by primes until you reach 1.",
                 "Write all the prime factors with their exponents.",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Prime factorization master! 🎉",
            ["Not fully factored — some factors aren't prime.",
             "Check your division steps again.",
             "Almost! Verify by multiplying your factors back together."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

    # Advanced prime questions (8q)
    adv_prime = [
        ("Twin primes are primes that differ by 2. How many twin prime pairs are there between 1 and 50?", "5", ["4", "6", "3"],
         "(3,5), (5,7), (11,13), (17,19), (29,31), but (29,31) — wait: (41,43) also. Let me recount: (3,5),(5,7),(11,13),(17,19),(29,31),(41,43) = 6 pairs up to 50."),
        ("What is the product of the two primes closest to 50?", "2491", ["2397", "2550", "2501"],
         "47 × 53 = 2491."),
        ("If p is prime and p² = 169, what is p?", "13", ["11", "17", "12"],
         "√169 = 13, and 13 is prime."),
        ("What is the sum of all prime numbers less than 20?", "77", ["73", "80", "75"],
         "2+3+5+7+11+13+17+19 = 77."),
        ("A number n satisfies n = p × q where p and q are consecutive primes. If n = 143, what are p and q?",
         "11 and 13", ["7 and 11", "13 and 17", "9 and 13"],
         "11 × 13 = 143."),
        ("How many numbers less than 30 are relatively prime to 30 (share no common factor)?", "8", ["10", "6", "12"],
         "Euler's totient: φ(30) = 30×(1-1/2)×(1-1/3)×(1-1/5) = 8."),
        ("What is the smallest prime greater than 100?", "101", ["103", "107", "109"],
         "101 is prime — not divisible by 2,3,5,7 (only need to check up to √101 ≈ 10)."),
        ("Goldbach's conjecture says every even number > 2 is the sum of two primes. Express 100 as a sum of two primes.",
         "47 + 53", ["49 + 51", ["45 + 55"], "43 + 57"],
         "47 and 53 are both prime, and 47 + 53 = 100."),
    ]
    # Fix twin primes answer
    adv_prime[0] = ("Twin primes are primes that differ by 2. How many twin prime pairs are there between 1 and 50?", "6", ["4", "5", "7"],
         "(3,5), (5,7), (11,13), (17,19), (29,31), (41,43) = 6 pairs.")
    # Fix Goldbach wrongs (nested list issue)
    adv_prime[7] = ("Goldbach's conjecture says every even number > 2 is the sum of two primes. Express 100 as a sum of two primes.",
         "47 + 53", ["49 + 51", "45 + 55", "43 + 57"],
         "47 and 53 are both prime, and 47 + 53 = 100.")

    for stem_text, ans, wrongs, explanation in adv_prime:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} has an advanced puzzle: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["primes", "advanced", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Think carefully about prime number properties.",
                ["List out the relevant primes first.",
                 "Check each candidate systematically.",
                 "Almost! Verify your answer satisfies all conditions.",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Brilliant prime number reasoning! 🎉",
            ["Check if all the numbers involved are actually prime.",
             "Not quite — verify by testing primality.",
             "Close! Double-check the conditions in the problem."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

gen_primes()

# ============================================================
# CATEGORY 5: Fractions & Decimals (30 questions, IDs 1011-1040)
# ============================================================
def gen_fractions():
    global qid

    frac_qs = [
        ("What is 3/4 + 5/6?", "19/12", ["8/10", "15/24", "4/5"], "3/4 + 5/6 = 9/12 + 10/12 = 19/12."),
        ("What is 7/8 − 2/3?", "5/24", ["5/8", "1/3", "5/5"], "7/8 − 2/3 = 21/24 − 16/24 = 5/24."),
        ("What is 5/6 × 3/10?", "1/4", ["15/60", "8/16", "3/12"], "5/6 × 3/10 = 15/60 = 1/4."),
        ("What is 7/9 ÷ 2/3?", "7/6", ["7/27", "14/9", "2/3"], "7/9 ÷ 2/3 = 7/9 × 3/2 = 21/18 = 7/6."),
        ("Simplify: 48/72", "2/3", ["4/6", "24/36", "3/4"], "48/72: GCD=24, so 48÷24/72÷24 = 2/3."),
        ("What is 2 1/3 + 1 3/4?", "4 1/12", ["3 4/7", "4 1/4", "3 7/12"], "7/3 + 7/4 = 28/12 + 21/12 = 49/12 = 4 1/12."),
        ("What is 3 1/2 × 2 2/5?", "8 2/5", ["6 3/10", "5 7/10", "7 1/2"], "7/2 × 12/5 = 84/10 = 42/5 = 8 2/5."),
        ("Convert 0.375 to a fraction in simplest form.", "3/8", ["375/1000", "15/40", "37/100"], "0.375 = 375/1000 = 3/8."),
        ("Convert 5/11 to a decimal (rounded to 3 places).", "0.455", ["0.454", "0.545", "0.445"], "5 ÷ 11 = 0.454545... ≈ 0.455."),
        ("Which is larger: 5/7 or 7/10?", "5/7", ["7/10", "They are equal", "Cannot tell"], "5/7 ≈ 0.714, 7/10 = 0.700. So 5/7 > 7/10."),
        ("What is 1/2 + 1/3 + 1/4?", "13/12", ["3/9", "1", "11/12"], "6/12 + 4/12 + 3/12 = 13/12."),
        ("What is (3/5)²?", "9/25", ["6/10", "9/10", "3/10"], "(3/5)² = 9/25."),
        ("If 2/5 of a number is 36, what is the number?", "90", ["72", "18", "45"], "2/5 × n = 36, n = 36 × 5/2 = 90."),
        ("What is 0.125 + 0.875?", "1", ["0.900", "1.1", "0.975"], "0.125 + 0.875 = 1.000."),
        ("Convert 7/8 to a decimal.", "0.875", ["0.785", "0.857", "0.870"], "7 ÷ 8 = 0.875."),
        ("What is 5/12 + 7/18?", "29/36", ["12/30", "1", "35/216"], "15/36 + 14/36 = 29/36."),
        ("Arrange from smallest to largest: 3/5, 5/8, 7/11", "3/5 < 7/11 < 5/8", ["5/8 < 3/5 < 7/11", "7/11 < 3/5 < 5/8", "3/5 < 5/8 < 7/11"],
         "3/5=0.600, 7/11≈0.636, 5/8=0.625. So 3/5 < 5/8 < 7/11... wait: 0.625 < 0.636, so 3/5 < 5/8 < 7/11."),
        ("What is 2.4 × 0.15?", "0.36", ["0.036", "3.6", "0.24"], "2.4 × 0.15 = 0.36."),
        ("What is 4.56 ÷ 1.2?", "3.8", ["3.6", "4.2", "3.5"], "4.56 ÷ 1.2 = 3.8."),
        ("What fraction of 1 hour is 45 minutes?", "3/4", ["4/5", "9/12", "45/100"], "45/60 = 3/4."),
        ("If 3/8 of a class of 40 students are girls, how many are boys?", "25", ["15", "30", "20"], "Girls = 3/8 × 40 = 15, Boys = 40 - 15 = 25."),
        ("What is 0.̄3 (0.333...) as a fraction?", "1/3", ["3/10", "33/100", "3/9"], "0.333... = 1/3."),
        ("What is the reciprocal of 2 1/2?", "2/5", ["5/2", "1/2", "4/10"], "2 1/2 = 5/2, reciprocal = 2/5."),
        ("Compute: 1 − 1/2 + 1/3 − 1/4", "7/12", ["5/12", "1/2", "1/4"], "12/12 − 6/12 + 4/12 − 3/12 = 7/12."),
        ("What is 15% as a fraction in simplest form?", "3/20", ["15/100", "1/15", "3/10"], "15% = 15/100 = 3/20."),
        ("What is 2/3 of 3/4 of 120?", "60", ["80", "45", "90"], "3/4 × 120 = 90, then 2/3 × 90 = 60."),
        ("Subtract: 5 1/6 − 2 3/4", "2 5/12", ["3 2/3", "2 1/3", "3 5/12"], "31/6 − 11/4 = 62/12 − 33/12 = 29/12 = 2 5/12."),
        ("What is 0.16̄ (0.1666...) as a fraction?", "1/6", ["16/100", "4/25", "1/60"], "0.1666... = 1/6."),
        ("If a/b = 3/5 and b = 45, what is a?", "27", ["15", "9", "35"], "a = 3/5 × 45 = 27."),
        ("What is (1/2 + 1/3) × (1/2 − 1/3)?", "5/36", ["1/6", "1/36", "2/6"], "(5/6) × (1/6) = 5/36."),
    ]
    # Fix q17: 3/5=0.600, 5/8=0.625, 7/11≈0.636 => 3/5 < 5/8 < 7/11
    frac_qs[16] = ("Arrange from smallest to largest: 3/5, 5/8, 7/11", "3/5 < 5/8 < 7/11",
                   ["5/8 < 3/5 < 7/11", "7/11 < 3/5 < 5/8", "3/5 < 7/11 < 5/8"],
                   "3/5=0.600, 5/8=0.625, 7/11≈0.636.")

    for stem_text, ans, wrongs, explanation in frac_qs:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} asks: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["fractions", "decimals", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Find a common denominator when adding or subtracting fractions.",
                ["Identify what operation is needed.",
                 "Convert to the same form (common denominator or decimal).",
                 "Compute step by step and simplify.",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Fraction wizard! Perfectly done! 🎉",
            ["Check your common denominator.",
             "Make sure you simplified correctly.",
             "Not quite — try converting to decimals to verify."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

gen_fractions()

# ============================================================
# CATEGORY 6: Number Theory (30 questions, IDs 1041-1070)
# ============================================================
def gen_number_theory():
    global qid

    nt_qs = [
        ("What is the remainder when 257 is divided by 7?", "5", ["3", "4", "6"], "257 = 36×7 + 5."),
        ("What is the remainder when 1000 is divided by 13?", "12", ["10", "11", "1"], "1000 = 76×13 + 12."),
        ("What is the digit sum of 9876?", "30", ["28", "32", "27"], "9+8+7+6 = 30."),
        ("What is the remainder when 3^100 is divided by 4?", "1", ["3", "2", "0"], "3 ≡ −1 (mod 4), so 3^100 ≡ 1 (mod 4)."),
        ("What is the remainder when 2^50 is divided by 7?", "4", ["1", "2", "3"], "Powers of 2 mod 7 cycle: 2,4,1. 50÷3 remainder 2, so 2^50 ≡ 4 (mod 7)."),
        ("If the digit sum of a number is 18, is it divisible by 9?", "Yes", ["No", "Only if even", "Sometimes"], "A number is divisible by 9 if its digit sum is divisible by 9. 18÷9=2."),
        ("What is the sum of all digits of 2^10 (which is 1024)?", "7", ["10", "6", "8"], "1+0+2+4 = 7."),
        ("Find the missing digit: 4_6 is divisible by 9.", "8", ["5", "9", "3"], "4+_+6 = multiple of 9. 10+_ must = 18, so _ = 8."),
        ("What is 123456789 mod 9?", "0", ["1", "9", "3"], "Digit sum = 1+2+3+4+5+6+7+8+9 = 45, divisible by 9."),
        ("How many 3-digit numbers are divisible by both 5 and 8?", "23", ["22", "24", "25"], "Divisible by LCM(5,8)=40. From 120 to 960: (960-120)/40 + 1 = 22. Actually: 40,80,120,...960 but 3-digit starts at 120. 120/40=3, 960/40=24, count=24-3+1=22."),
        ("What is the remainder when 7^7 is divided by 5?", "3", ["2", "4", "1"], "7≡2 mod 5. 2^7=128≡3 mod 5."),
        ("A number leaves remainder 3 when divided by 5 and remainder 2 when divided by 3. What is the smallest such positive number?", "8", ["13", "23", "18"], "8÷5=1 R 3, 8÷3=2 R 2. ✓"),
        ("What is the sum of all digits of 999999 × 2?", "54", ["36", "45", "27"], "999999 × 2 = 1999998. Digit sum = 1+9+9+9+9+9+8 = 54."),
        ("How many zeros does 100! end with?", "24", ["20", "25", "10"], "⌊100/5⌋ + ⌊100/25⌋ = 20 + 4 = 24."),
        ("What is the digital root of 987654?", "3", ["9", "6", "0"], "9+8+7+6+5+4=39, 3+9=12, 1+2=3."),
        ("What is the remainder when 11^11 is divided by 3?", "2", ["1", "0", "3"], "11≡2 mod 3. 2^11=2048≡2 mod 3."),
        ("A 3-digit number ABC (where A, B, C are digits) is divisible by 11 if A−B+C is divisible by 11. Is 759 divisible by 11?", "No (7−5+9=11, so YES)", ["Yes", "Only if 7+5+9 div by 11", "Cannot tell"], "Actually 7−5+9=11, which IS divisible by 11. So 759 IS divisible by 11."),
        ("What is the largest 3-digit number divisible by 7?", "994", ["997", "993", "990"], "999÷7 = 142 R 5, so 999−5 = 994."),
        ("How many positive integers less than 100 are divisible by neither 2 nor 3?", "33", ["30", "36", "25"], "By inclusion-exclusion: 99 − 49 − 33 + 16 = 33."),
        ("What is the sum of all two-digit multiples of 7?", "728", ["735", "700", "756"], "14+21+28+...+98. This is an AP: a=14, l=98, n=13. Sum=13×(14+98)/2 = 13×56 = 728."),
        ("If n! has exactly 4 trailing zeros, what is the smallest n?", "20", ["15", "25", "24"], "⌊20/5⌋ + ⌊20/25⌋ = 4 + 0 = 4."),
        ("What is 2023 mod 11?", "10", ["1", "4", "7"], "2023 = 183×11 + 10."),
        ("What is the alternating digit sum (for div by 11 test) of 8294?", "5", ["3", "11", "7"], "8−2+9−4 = 11. Wait: that's 11. Let me recheck: yes 8-2+9-4=11."),
        ("The number 72□ is divisible by 8. What digit goes in the □?", "0", ["4", "8", "2"], "720 ÷ 8 = 90. ✓ Also 728÷8=91 works. Smallest: 720."),
        ("How many numbers from 1 to 1000 are perfect squares?", "31", ["30", "32", "33"], "√1000 ≈ 31.6, so 31 perfect squares (1² through 31²)."),
        ("What is the remainder when 123456 is divided by 11?", "3", ["1", "5", "7"], "1−2+3−4+5−6 = −3 ≡ 8 mod 11. Actually: 123456/11 = 11223 R 3. Let me verify: 11×11223 = 123453, 123456−123453=3."),
        ("What number am I? I am between 100 and 200. I am divisible by 3, 5, and 7.", "105", ["135", "140", "210"], "LCM(3,5,7)=105, and 105 is between 100 and 200."),
        ("How many factors of 60 are even?", "10", ["6", "8", "12"], "Factors of 60: 1,2,3,4,5,6,10,12,15,20,30,60. Even ones: 2,4,6,10,12,20,30,60 = 8."),
        ("What is the product of all single-digit primes?", "210", ["150", "180", "120"], "2×3×5×7 = 210."),
        ("A clock shows 3:00. After 1000 hours, what time does it show?", "7:00", ["5:00", "3:00", "11:00"], "1000 mod 12 = 4. 3:00 + 4 hours = 7:00."),
    ]
    # Fix q10: 3-digit multiples of 40: 120,160,...,960 -> (960-120)/40+1=22
    nt_qs[9] = ("How many 3-digit numbers are divisible by both 5 and 8?", "22", ["23", "24", "25"],
                "LCM(5,8)=40. 3-digit multiples of 40: 120,160,...,960. Count=(960-120)/40+1=22.")
    # Fix q16: 759 IS divisible by 11
    nt_qs[16] = ("Is 759 divisible by 11? (Test: A−B+C for ABC)", "Yes", ["No", "Only if even", "Cannot tell"],
                 "7−5+9 = 11, which is divisible by 11, so yes!")
    # Fix q22: 8-2+9-4=11
    nt_qs[22] = ("What is the alternating digit sum (for div by 11 test) of 8294?", "11", ["5", "3", "7"],
                 "8−2+9−4 = 11.")
    # Fix q23: both 720 and 728 work. Let's rephrase.
    nt_qs[23] = ("The number 72□ is divisible by 8. What is the smallest digit that goes in the □?", "0", ["4", "8", "2"],
                 "720 ÷ 8 = 90. ✓")
    # Fix q25: digit alternating sum check
    nt_qs[25] = ("What is the remainder when 123456 is divided by 11?", "3", ["1", "5", "7"],
                 "123456 = 11223×11 + 3.")
    # Fix q27: even factors of 60
    nt_qs[27] = ("How many factors of 60 are even?", "8", ["6", "10", "12"],
                 "Factors of 60: 1,2,3,4,5,6,10,12,15,20,30,60. Even: 2,4,6,10,12,20,30,60 = 8.")

    for stem_text, ans, wrongs, explanation in nt_qs:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} presents: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["number-theory", "remainders", "modular-arithmetic", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Look for patterns in remainders or use divisibility rules.",
                ["Identify the key operation: division, digit sum, or modular arithmetic.",
                 "Apply the relevant rule or formula.",
                 "Check your answer by plugging it back in.",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Number theory genius! 🎉",
            ["Check your division carefully.",
             "Apply the divisibility rule more carefully.",
             "Not quite — try a different approach."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

gen_number_theory()

# ============================================================
# CATEGORY 7: Algebraic Thinking (30 questions, IDs 1071-1100)
# ============================================================
def gen_algebra():
    global qid

    alg_qs = [
        ("If 3x + 7 = 28, what is x?", "7", ["8", "6", "9"], "3x = 21, x = 7."),
        ("If 5(n − 3) = 40, what is n?", "11", ["8", "13", "5"], "n − 3 = 8, n = 11."),
        ("If 2a + 3b = 23 and a = 4, what is b?", "5", ["3", "7", "4"], "8 + 3b = 23, 3b = 15, b = 5."),
        ("Find x: x/4 + 5 = 12", "28", ["48", "7", "32"], "x/4 = 7, x = 28."),
        ("If n × n = 196, what is n?", "14", ["13", "15", "12"], "√196 = 14."),
        ("What value of y makes 4y − 9 = 3y + 6?", "15", ["3", "12", "9"], "4y − 3y = 6 + 9, y = 15."),
        ("☐ + ☐ + ☐ = 45 (all three ☐ are the same). What is ☐?", "15", ["12", "18", "9"], "3☐ = 45, ☐ = 15."),
        ("If 100 − 4x = 60, what is x?", "10", ["8", "15", "12"], "4x = 40, x = 10."),
        ("Find the missing number: 2, 6, 18, 54, ☐", "162", ["108", "72", "216"], "Each term × 3. 54 × 3 = 162."),
        ("Find the missing number: 1, 4, 9, 16, 25, ☐", "36", ["30", "35", "49"], "Perfect squares! 6² = 36."),
        ("If a = 3 and b = −2, what is a² + b² + 2ab?", "1", ["5", "13", "7"], "(a+b)² = (3−2)² = 1."),
        ("Solve: 7x − 5 = 3x + 19", "6", ["4", "8", "3"], "4x = 24, x = 6."),
        ("If 3(x + 2) = 2(x + 7), find x.", "8", ["4", "10", "6"], "3x + 6 = 2x + 14, x = 8."),
        ("What is the 10th term of the sequence 3, 7, 11, 15, ...?", "39", ["43", "35", "41"], "a_n = 3 + (n−1)×4. a_10 = 3 + 36 = 39."),
        ("If the sum of three consecutive numbers is 84, what is the largest?", "29", ["28", "30", "27"], "n + (n+1) + (n+2) = 84, 3n+3=84, n=27. Largest = 29."),
        ("The product of two consecutive even numbers is 168. What are they?", "12 and 14", ["10 and 12", "14 and 16", "8 and 10"],
         "12 × 14 = 168. ✓"),
        ("If x + y = 15 and x − y = 5, what is x?", "10", ["5", "15", "8"], "Adding: 2x = 20, x = 10."),
        ("What number squared gives 2025?", "45", ["40", "50", "55"], "45² = 2025."),
        ("If 1/x + 1/x = 1/5, what is x?", "10", ["5", "15", "20"], "2/x = 1/5, x = 10."),
        ("Find x: 2^x = 64", "6", ["5", "7", "8"], "2^6 = 64."),
        ("In the pattern 1, 1, 2, 3, 5, 8, 13, what comes next?", "21", ["18", "20", "26"], "Fibonacci: 8 + 13 = 21."),
        ("If (x+3)(x−3) = 40, what is x²?", "49", ["43", "46", "52"], "x²−9 = 40, x² = 49."),
        ("The average of 5 numbers is 24. If four of them are 20, 22, 25, 28, what is the fifth?", "25", ["24", "23", "26"],
         "Sum = 120. 20+22+25+28 = 95. Fifth = 120−95 = 25."),
        ("If f(n) = 2n + 3, what is f(10) − f(5)?", "10", ["8", "12", "15"], "f(10)=23, f(5)=13. 23−13=10."),
        ("What is the sum 1+2+3+...+50?", "1275", ["1250", "1300", "1225"], "50×51/2 = 1275."),
        ("If 2^x × 2^3 = 2^10, what is x?", "7", ["3", "30", "13"], "2^(x+3) = 2^10, x+3=10, x=7."),
        ("Find the missing number: 3, ☐, 27, 81, 243", "9", ["12", "15", "6"], "Geometric: ×3. 3×3 = 9."),
        ("If a number is tripled and then 15 is subtracted, the result is 60. What is the number?", "25", ["20", "30", "15"], "3n − 15 = 60, 3n = 75, n = 25."),
        ("What is the sum of the first 20 odd numbers?", "400", ["380", "420", "200"], "Sum of first n odd numbers = n². 20² = 400."),
        ("Solve: |2x − 8| = 12", "10 or −2", ["10", "−2", "2 or 10"], "2x−8=12 → x=10, or 2x−8=−12 → x=−2."),
    ]

    for stem_text, ans, wrongs, explanation in alg_qs:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} challenges: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["algebraic-thinking", "equations", "missing-number", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Isolate the unknown by doing the same operation to both sides.",
                ["Identify what you're solving for.",
                 "Use inverse operations to simplify.",
                 "Check your answer by substituting back.",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Algebraic thinking at its finest! 🎉",
            ["Check your inverse operation.",
             "Substitute back to verify — this doesn't work.",
             "Close! Try solving step by step again."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

gen_algebra()

# ============================================================
# CATEGORY 8: Integer Properties (25 questions, IDs 1101-1125)
# ============================================================
def gen_integers():
    global qid

    int_qs = [
        ("What is (−3) × (−5) × (−2)?", "−30", ["30", "−15", "10"], "Negative × negative = positive, × negative = negative. 3×5×2=30, so −30."),
        ("What is |−15| + |−8|?", "23", ["7", "−23", "−7"], "|−15|=15, |−8|=8. 15+8=23."),
        ("Is the product of 99 negative numbers positive or negative?", "Negative", ["Positive", "Zero", "Cannot tell"],
         "Odd number of negatives → negative product."),
        ("What is (−4)³?", "−64", ["64", "−12", "12"], "(−4)³ = −4 × −4 × −4 = 16 × (−4) = −64."),
        ("What is (−1)^100 + (−1)^101?", "0", ["2", "−2", "1"], "(−1)^100=1, (−1)^101=−1. 1+(−1)=0."),
        ("If a number is even and negative, which of these could it be?", "−24", ["−15", "−33", "−7"], "−24 is even (divisible by 2) and negative."),
        ("True or false: The sum of two odd numbers is always even.", "True", ["False", "Only if positive", "Only if they differ by 2"],
         "Odd + Odd = Even. Always!"),
        ("What is the value of (−2)^4 − (−3)^2?", "7", ["−7", "25", "−5"], "16 − 9 = 7."),
        ("If a × b > 0 and a < 0, what do we know about b?", "b < 0", ["b > 0", "b = 0", "Cannot tell"],
         "If product is positive and a is negative, b must be negative too."),
        ("What is |3 − 8| − |8 − 3|?", "0", ["10", "−10", "5"], "|−5| − |5| = 5 − 5 = 0."),
        ("The sum of 5 consecutive integers is 0. What is the largest?", "2", ["5", "3", "1"],
         "−2,−1,0,1,2. Sum=0. Largest=2."),
        ("If n is odd, is n² + n even or odd?", "Even", ["Odd", "Depends on n", "Cannot tell"],
         "n² + n = n(n+1). One of consecutive numbers is even, so product is even."),
        ("What is (−6) + (−4) − (−10)?", "0", ["−20", "10", "−10"], "−6 + (−4) − (−10) = −10 + 10 = 0."),
        ("How many negative integers are greater than −10?", "9", ["10", "8", "Infinite"],
         "−9, −8, −7, −6, −5, −4, −3, −2, −1 = 9 integers."),
        ("What is the absolute value of (5 − 12)?", "7", ["−7", "17", "5"], "|5−12| = |−7| = 7."),
        ("If x² = 49, how many integer values can x have?", "2", ["1", "3", "49"], "x = 7 or x = −7."),
        ("What is (−1) + (−1)² + (−1)³ + (−1)⁴?", "0", ["−2", "2", "4"], "−1+1+(−1)+1 = 0."),
        ("Is 0 even, odd, or neither?", "Even", ["Odd", "Neither", "Both"], "0 is even because 0 = 2×0."),
        ("The product of three integers is negative. At most how many can be negative?", "3", ["1", "2", "All must be"],
         "All 3 can be negative: neg × neg × neg = neg."),
        ("What is (−5)² − 5²?", "0", ["−50", "50", "−25"], "(−5)² = 25, 5² = 25. 25−25=0."),
        ("If |x − 3| = 5, what are the possible values of x?", "8 and −2", ["8 only", "−2 only", "3 and 5"],
         "x−3=5 → x=8, or x−3=−5 → x=−2."),
        ("The sum of an even number and an odd number is always...?", "Odd", ["Even", "It depends", "Prime"],
         "Even + Odd = Odd. Always."),
        ("What is (−2) × (−3) × 4 × (−1)?", "−24", ["24", "12", "−12"], "6 × 4 × (−1) = −24."),
        ("How many integers between −5 and 5 (exclusive) are there?", "9", ["10", "11", "8"],
         "−4,−3,−2,−1,0,1,2,3,4 = 9 integers."),
        ("If n is any integer, is n² − n always even?", "Yes", ["No", "Only if n is even", "Only if n > 0"],
         "n² − n = n(n−1). Product of consecutive integers is always even."),
    ]

    for stem_text, ans, wrongs, explanation in int_qs:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} asks: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["integers", "even-odd", "absolute-value", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Think about the sign rules for multiplication and properties of even/odd numbers.",
                ["Consider the signs of each number.",
                 "Apply the rule: negative × negative = positive.",
                 "Count the number of negative factors.",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Integer property expert! 🎉",
            ["Watch the signs carefully!",
             "Reconsider the even/odd property.",
             "Not quite — try with specific examples."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

gen_integers()

# ============================================================
# CATEGORY 9: Ratios & Proportions (25 questions, IDs 1126-1150)
# ============================================================
def gen_ratios():
    global qid

    ratio_qs = [
        ("If the ratio of cats to dogs at a shelter is 3:5 and there are 40 animals total (cats and dogs only), how many cats are there?", "15", ["20", "24", "12"],
         "3+5=8 parts. 40÷8=5 per part. Cats = 3×5 = 15."),
        ("A recipe calls for flour and sugar in the ratio 5:2. If you use 350g of flour, how much sugar do you need?", "140g", ["100g", "175g", "70g"],
         "350÷5=70 per part. Sugar = 2×70 = 140g."),
        ("A car travels 240 km in 3 hours. At the same speed, how far will it travel in 5 hours?", "400 km", ["350 km", "450 km", "360 km"],
         "Speed = 80 km/h. Distance = 80 × 5 = 400 km."),
        ("If 8 workers can build a wall in 12 days, how many days will 6 workers take?", "16 days", ["14 days", "18 days", "10 days"],
         "Total work = 8×12 = 96 worker-days. 96÷6 = 16 days."),
        ("The ratio of boys to girls in a class is 4:3. If there are 12 girls, how many students total?", "28", ["24", "16", "35"],
         "3 parts = 12, 1 part = 4. Boys = 16. Total = 28."),
        ("A map has scale 1:50000. If two towns are 4 cm apart on the map, what is the actual distance?", "2 km", ["4 km", "200 m", "20 km"],
         "4 × 50000 = 200000 cm = 2000 m = 2 km."),
        ("If 5 oranges cost $3.50, how much do 12 oranges cost?", "$8.40", ["$7.00", "$9.60", "$8.00"],
         "1 orange = $0.70. 12 × $0.70 = $8.40."),
        ("Mix paint in ratio Red:Blue = 3:7. To make 500 mL, how much blue is needed?", "350 mL", ["300 mL", ["400 mL"], "250 mL"],
         "7/10 × 500 = 350 mL."),
        ("A shadow of a 6m pole is 4m long. A nearby tree casts a 10m shadow. How tall is the tree?", "15 m", ["12 m", ["18 m"], "10 m"],
         "6/4 = tree/10. Tree = 15m."),
        ("Speed, distance, time: If speed doubles and time halves, what happens to distance?", "Stays the same", ["Doubles", "Halves", "Quadruples"],
         "d = s×t. If s→2s and t→t/2, d = 2s × t/2 = s×t. Same."),
        ("Three friends split a bill in the ratio 2:3:5. The total is $200. How much does the person paying the most pay?", "$100", ["$80", ["$120"], "$60"],
         "5/10 × 200 = $100."),
        ("If x:y = 2:3 and y:z = 4:5, what is x:z?", "8:15", ["2:5", "6:15", "4:5"],
         "x:y = 8:12, y:z = 12:15. So x:z = 8:15."),
        ("A train travels 360 km at 90 km/h. How long does the journey take?", "4 hours", ["3 hours", "5 hours", "3.5 hours"],
         "360 ÷ 90 = 4 hours."),
        ("If 3/4 of a number equals 2/3 of 90, what is the number?", "80", ["60", ["90"], "75"],
         "2/3 × 90 = 60. 3/4 × n = 60. n = 80."),
        ("Unit rate: $4.80 for 6 apples. What is the cost per apple?", "$0.80", ["$0.60", "$0.96", "$1.00"],
         "4.80 ÷ 6 = 0.80."),
        ("A recipe for 4 people uses 600g of pasta. How much for 10 people?", "1500g", ["1200g", "1000g", "2400g"],
         "600/4 = 150g per person. 150 × 10 = 1500g."),
        ("If x is directly proportional to y, and x=12 when y=8, what is x when y=20?", "30", ["24", "36", "15"],
         "x/y = 12/8 = 3/2. x = 3/2 × 20 = 30."),
        ("In a bag, red to blue marbles are 5:3. If 10 more blue marbles are added, the ratio becomes 5:5. How many red marbles are there?", "25", ["20", "30", "15"],
         "5k red, 3k blue. 3k+10=5k → 2k=10 → k=5. Red = 25."),
        ("If it takes 5 machines 8 hours to produce 1000 items, how many items can 10 machines produce in 4 hours?", "1000", ["2000", "500", "800"],
         "Rate = 1000/(5×8) = 25 items/machine-hour. 10×4×25 = 1000."),
        ("The ratio of pencils to pens is 7:3. If there are 42 pencils, how many pens are there?", "18", ["21", "15", "12"],
         "7 parts = 42, 1 part = 6. Pens = 3×6 = 18."),
        ("A scale model is 1:200. The model building is 15 cm tall. How tall is the real building?", "30 m", ["3 m", "300 m", "3000 cm"],
         "15 × 200 = 3000 cm = 30 m."),
        ("If A:B = 1:2 and B:C = 3:4, find A:B:C.", "3:6:8", ["1:2:4", "3:6:4", "1:3:4"],
         "A:B = 3:6, B:C = 6:8. So A:B:C = 3:6:8."),
        ("Two gears mesh together. Gear A has 20 teeth, Gear B has 30. If A makes 60 rotations, how many does B make?", "40", ["90", "30", "45"],
         "20×60 = 30×B. B = 40."),
        ("A solution has water and acid in ratio 9:1. How much acid is in 500 mL?", "50 mL", ["100 mL", "45 mL", "55.5 mL"],
         "1/10 × 500 = 50 mL."),
        ("If the price of 15 pens is $45, what is the price of 25 pens?", "$75", ["$65", "$80", "$70"],
         "1 pen = $3. 25 × $3 = $75."),
    ]
    # Fix nested lists in wrongs
    ratio_qs[7] = ("Mix paint in ratio Red:Blue = 3:7. To make 500 mL, how much blue is needed?", "350 mL", ["300 mL", "400 mL", "250 mL"],
         "7/10 × 500 = 350 mL.")
    ratio_qs[8] = ("A shadow of a 6m pole is 4m long. A nearby tree casts a 10m shadow. How tall is the tree?", "15 m", ["12 m", "18 m", "10 m"],
         "6/4 = tree/10. Tree = 15m.")
    ratio_qs[10] = ("Three friends split a bill in the ratio 2:3:5. The total is $200. How much does the person paying the most pay?", "$100", ["$80", "$120", "$60"],
         "5/10 × 200 = $100.")
    ratio_qs[13] = ("If 3/4 of a number equals 2/3 of 90, what is the number?", "80", ["60", "90", "75"],
         "2/3 × 90 = 60. 3/4 × n = 60. n = 80.")

    for stem_text, ans, wrongs, explanation in ratio_qs:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} presents: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["ratios", "proportions", "unit-rates", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Set up a proportion: a/b = c/d and cross-multiply.",
                ["Identify the ratio or rate given.",
                 "Set up the proportion with the unknown.",
                 "Cross-multiply and solve.",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Ratio and proportion champion! 🎉",
            ["Check your cross-multiplication.",
             "Reread the ratio — you may have the parts swapped.",
             "Try setting up the proportion differently."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

gen_ratios()

# ============================================================
# CATEGORY 10: Estimation & Mental Math (25 questions, IDs 1151-1175)
# ============================================================
def gen_estimation():
    global qid

    est_qs = [
        ("Estimate 49 × 51 without a calculator.", "2499", ["2500", "2401", "2601"],
         "49×51 = (50−1)(50+1) = 2500 − 1 = 2499."),
        ("What is 998 × 5 using a mental math trick?", "4990", ["4985", ["5000"], "4995"],
         "(1000−2)×5 = 5000−10 = 4990."),
        ("Estimate √50 to the nearest whole number.", "7", ["8", "6", "5"],
         "7²=49, 8²=64. √50 ≈ 7."),
        ("What is 25 × 36 using mental math?", "900", ["850", "950", "800"],
         "25×36 = 25×4×9 = 100×9 = 900."),
        ("Estimate: 3.97 × 8.02", "≈ 32", ["≈ 24", "≈ 36", "≈ 28"],
         "≈ 4 × 8 = 32."),
        ("What is 125 × 8?", "1000", ["900", "1100", "800"],
         "125 × 8 = 1000."),
        ("Round 7.4999 to the nearest whole number.", "7", ["8", "7.5", "6"],
         "7.4999 < 7.5, so it rounds down to 7."),
        ("Estimate 999 + 998 + 997 + 996", "3990", ["4000", "3980", "3996"],
         "Each is about 1000, minus 1,2,3,4 = 3990. Exact: 999+998+997+996=3990."),
        ("What is 50² − 49²?", "99", ["100", "1", "50"],
         "a²−b² = (a+b)(a−b) = 99×1 = 99."),
        ("What is 76 × 25 using mental math?", "1900", ["1800", "2000", "1750"],
         "76×25 = 76×100÷4 = 7600÷4 = 1900."),
        ("Estimate 197 × 3.", "591", ["600", "580", "597"],
         "(200−3)×3 = 600−9 = 591."),
        ("What is 99² using a trick?", "9801", ["9901", "9800", "9810"],
         "99² = (100−1)² = 10000−200+1 = 9801."),
        ("What is 33 × 33 + 67 × 67 + 2 × 33 × 67?", "10000", ["9900", "10100", "5000"],
         "This is (33+67)² = 100² = 10000."),
        ("Estimate: 1/7 ≈ ?", "0.143", ["0.125", "0.166", "0.111"],
         "1÷7 ≈ 0.142857... ≈ 0.143."),
        ("What is 2^15 (hint: 2^10 = 1024)?", "32768", ["16384", "65536", "8192"],
         "2^15 = 2^10 × 2^5 = 1024 × 32 = 32768."),
        ("Estimate which is closest to √200.", "14", ["15", "13", "16"],
         "14² = 196, 15² = 225. √200 ≈ 14.14."),
        ("What is 37 × 3 + 37 × 7?", "370", ["377", "360", "740"],
         "37 × (3+7) = 37 × 10 = 370."),
        ("What is 88 × 12 ÷ 8?", "132", ["128", "136", "120"],
         "88 × 12 = 1056. 1056 ÷ 8 = 132."),
        ("Estimate 5.1² + 4.9².", "≈ 50", ["≈ 52", "≈ 48", "≈ 100"],
         "5.1²+4.9² = 26.01+24.01 = 50.02 ≈ 50."),
        ("What is 1001 × 999?", "999999", ["1000000", "998999", "1000999"],
         "(1000+1)(1000−1) = 1000²−1 = 999999."),
        ("Compute quickly: 64 × 125", "8000", ["7500", "8500", "6400"],
         "64 × 125 = 8 × 8 × 125 = 8 × 1000 = 8000."),
        ("What is 11 × 11 × 11?", "1331", ["1221", "1441", "1210"],
         "11³ = 121 × 11 = 1331."),
        ("Estimate 301 × 299.", "89999", ["90000", "89700", "90300"],
         "(300+1)(300−1) = 90000−1 = 89999."),
        ("What is 15% of 200 using mental math?", "30", ["20", "25", "35"],
         "10% = 20, 5% = 10. 15% = 30."),
        ("What is 17 × 6 without a calculator?", "102", ["96", "108", "112"],
         "17×6 = 10×6 + 7×6 = 60+42 = 102."),
    ]
    # Fix nested list
    est_qs[1] = ("What is 998 × 5 using a mental math trick?", "4990", ["4985", "5000", "4995"],
         "(1000−2)×5 = 5000−10 = 4990.")

    for stem_text, ans, wrongs, explanation in est_qs:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} tests your mental math: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["estimation", "mental-math", "tricks", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Look for patterns like difference of squares or rounding tricks.",
                ["Can you rewrite the numbers to make calculation easier?",
                 "Try breaking the problem into simpler parts.",
                 "Use algebraic identities like (a+b)(a−b) = a²−b².",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Mental math master! 🎉",
            ["Try a different mental math strategy.",
             "Check your arithmetic — close but not exact.",
             "Use rounding or factoring to simplify."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

gen_estimation()

# ============================================================
# CATEGORY 11: Word Problems (25 questions, IDs 1176-1200)
# ============================================================
def gen_word_problems():
    global qid

    wp_qs = [
        ("A bookstore sells 3 novels for $24 and 5 comics for $15. How much do 6 novels and 10 comics cost?",
         "$78", ["$72", "$84", "$39"],
         "6 novels = $48, 10 comics = $30. Total = $78."),
        ("A train leaves at 9:15 AM and arrives at 2:47 PM. How long is the journey in minutes?",
         "332 minutes", ["327 minutes", ["337 minutes"], "322 minutes"],
         "9:15 to 2:47 = 5h 32min = 332 min."),
        ("A tank is 1/3 full. After adding 40 liters, it is 5/6 full. What is the tank's capacity?",
         "80 liters", ["60 liters", "120 liters", "100 liters"],
         "5/6 − 1/3 = 5/6 − 2/6 = 3/6 = 1/2. So 40L = 1/2 tank. Capacity = 80L."),
        ("A school has 360 students. 5/9 are boys. How many more boys than girls are there?",
         "40", ["60", "80", "20"],
         "Boys = 200, Girls = 160. Difference = 40."),
        ("A farmer has chickens and cows. There are 30 heads and 80 legs total. How many cows?",
         "10", ["15", "20", "8"],
         "c + h = 30, 4c + 2h = 80. Solving: 2c = 20, c = 10."),
        ("Three consecutive even numbers sum to 78. What is the largest?",
         "28", ["26", "30", "24"],
         "n + (n+2) + (n+4) = 78. 3n+6 = 78. n = 24. Largest = 28."),
        ("A rectangle's length is twice its width. The perimeter is 60 cm. What is the area?",
         "200 cm²", ["150 cm²", "300 cm²", "180 cm²"],
         "2(2w + w) = 60, 6w = 60, w = 10. l = 20. Area = 200."),
        ("A car uses 8 liters of fuel per 100 km. How much fuel for 350 km?",
         "28 liters", ["24 liters", "32 liters", "35 liters"],
         "8 × 3.5 = 28 liters."),
        ("Alice is twice as old as Bob. In 5 years, Alice will be 1.5 times Bob's age. How old is Bob now?",
         "10", ["5", "15", "8"],
         "Now: A=2B. In 5 years: 2B+5 = 1.5(B+5). 0.5B = 2.5. B = 5... Wait: 2(5)+5=15, 1.5(5+5)=15. ✓ B=5."),
        ("A class has 40 students. 60% passed math, 70% passed science, and 45% passed both. What percentage passed at least one?",
         "85%", ["90%", "80%", "75%"],
         "P(M∪S) = 60 + 70 − 45 = 85%."),
        ("A shopkeeper buys an item for $80 and sells it for $100. What is the profit percentage?",
         "25%", ["20%", "30%", "80%"],
         "Profit = $20. Profit% = 20/80 × 100 = 25%."),
        ("A swimming pool can be filled in 6 hours by pipe A and 8 hours by pipe B. How long to fill it with both pipes open?",
         "3 3/7 hours", ["3 hours", "4 hours", "7 hours"],
         "Rate = 1/6 + 1/8 = 7/24 pool/hour. Time = 24/7 = 3 3/7 hours."),
        ("An investment of $500 earns 4% simple interest per year. What is the total after 3 years?",
         "$560", ["$520", "$600", "$512"],
         "Interest = 500 × 0.04 × 3 = $60. Total = $560."),
        ("A ball is dropped from 81 m. Each bounce reaches 1/3 of the previous height. After 3 bounces, how high does it go?",
         "3 m", ["9 m", "1 m", "27 m"],
         "81 → 27 → 9 → 3 m."),
        ("Two trains 300 km apart travel toward each other at 80 km/h and 70 km/h. When do they meet?",
         "2 hours", ["3 hours", "1.5 hours", "2.5 hours"],
         "Combined speed = 150 km/h. Time = 300/150 = 2 hours."),
        ("A store has a 20% off sale. An additional 10% discount is applied at checkout. What is the total discount on a $100 item?",
         "$28", ["$30", "$25", "$32"],
         "After 20%: $80. After 10%: $72. Discount = $28."),
        ("A clock gains 5 minutes every hour. If set correctly at noon, what time does it show at 6 PM?",
         "6:30 PM", ["6:25 PM", "6:35 PM", "6:05 PM"],
         "6 hours × 5 min = 30 min gained. Shows 6:30 PM."),
        ("A worker earns $12/hour on weekdays and $18/hour on weekends. She works 40 weekday hours and 8 weekend hours. Total earnings?",
         "$624", ["$600", "$648", "$576"],
         "40×12 + 8×18 = 480 + 144 = $624."),
        ("In a test, the average of 25 students is 72. If the top scorer (who scored 100) is removed, what is the new average?",
         "70.83", ["71", "70", "72"],
         "Total = 25×72 = 1800. Without top: 1700. Avg = 1700/24 ≈ 70.83."),
        ("A garden is 12m × 8m. A path 1m wide runs inside along all edges. What is the area of the path?",
         "36 m²", ["40 m²", "32 m²", "44 m²"],
         "Inner garden: 10×6 = 60. Total: 96. Path = 96−60 = 36."),
        ("A shop sells pens at 3 for $5. How many pens can you buy with $35?",
         "21", ["18", "24", "15"],
         "$35 ÷ $5 = 7 sets. 7 × 3 = 21 pens."),
        ("A sequence starts at 5 and each term adds 3 more than the previous addition: 5, 8, 14, 23, ... What is the next term?",
         "35", ["32", "38", "29"],
         "Differences: 3, 6, 9, 12. Next = 23 + 12 = 35."),
        ("A bakery made 240 cupcakes. They sold 3/8 in the morning and 1/4 of the remainder in the afternoon. How many are left?",
         "112", ["120", "90", "105"],
         "Morning: sold 90, left 150. Afternoon: sold 150/4=37.5 → let me fix: 1/4 of 150 = 37.5, hmm. Let's say sold 37, left 113... Actually 150×1/4 = 37.5. Let me recheck: 240×3/8=90, left=150. 150×1/4=37.5 — non-integer. Fix needed."),
        ("A number is increased by 25% and then decreased by 20%. Is the final number equal to, greater than, or less than the original?",
         "Equal", ["Greater", "Less", "Cannot tell"],
         "100 × 1.25 = 125. 125 × 0.80 = 100. Equal!"),
        ("Three friends pooled their money: $45, $60, and $75. They split it equally. How much does each person get or give?",
         "$60 each", ["$45 each", "$75 each", "$55 each"],
         "Total = $180. Each gets $60."),
    ]
    # Fix nested list in q1
    wp_qs[1] = ("A train leaves at 9:15 AM and arrives at 2:47 PM. How long is the journey in minutes?",
         "332 minutes", ["327 minutes", "337 minutes", "322 minutes"],
         "9:15 to 2:47 = 5h 32min = 332 min.")
    # Fix q8: Bob=5, not 10
    wp_qs[8] = ("Alice is twice as old as Bob. In 5 years, Alice will be 1.5 times Bob's age. How old is Bob now?",
         "5", ["10", "15", "8"],
         "Now: A=2B. In 5 years: 2B+5 = 1.5(B+5). 0.5B = 2.5. B = 5.")
    # Fix q22: cupcake non-integer issue
    wp_qs[21] = ("A sequence starts at 5 and each term adds 3 more than the previous addition: 5, 8, 14, 23, ... What is the next term?",
         "35", ["32", "38", "29"],
         "Differences: 3, 6, 9, next diff=12. 23+12=35.")
    wp_qs[22] = ("A bakery made 240 cupcakes. They sold 1/3 in the morning and 1/4 of the remainder in the afternoon. How many are left?",
         "120", ["80", "160", "100"],
         "Morning: sold 80, left 160. Afternoon: sold 40, left 120.")

    for stem_text, ans, wrongs, explanation in wp_qs:
        score = 201 + (qid - 901)
        q = {
            "id": f"T2-{qid}",
            "stem": f"{char()} shares a problem: {stem_text}",
            "choices": None, "correct_answer": None,
            "difficulty_tier": tier(score), "difficulty_score": score,
            "visual_svg": None, "visual_alt": None, "diagnostics": None,
            "tags": ["word-problems", "multi-step", "arithmetic", "grade-5-6"],
            "topic": "arithmetic_missing_numbers",
            "topic_name": "Arithmetic & Missing Numbers",
            "hint": make_hint(
                "Break the problem into smaller steps and solve each part.",
                ["Identify what the question is really asking.",
                 "Set up the relevant equations or calculations.",
                 "Solve step by step and check if the answer makes sense.",
                 explanation]
            )
        }
        choices, ci, diag = shuffle_choices(
            ans, wrongs,
            "Word problem master! Fantastic reasoning! 🎉",
            ["Re-read the problem — you may have missed a detail.",
             "Check your arithmetic in each step.",
             "Try a different approach to the problem."]
        )
        q["choices"] = choices; q["correct_answer"] = ci; q["diagnostics"] = diag
        questions.append(q); qid += 1

gen_word_problems()

# ============================================================
# Final assembly and validation
# ============================================================

# Reassign difficulty scores linearly from 201 to 300
for i, q in enumerate(questions):
    score = 201 + int(i * 99 / 299)
    q["difficulty_score"] = score
    q["difficulty_tier"] = tier(score)

# Verify we have exactly 300 questions
assert len(questions) == 300, f"Expected 300 questions, got {len(questions)}"

# Verify IDs
for i, q in enumerate(questions):
    expected_id = f"T2-{901 + i}"
    q["id"] = expected_id  # Ensure sequential IDs

# Verify all questions have valid structure
for q in questions:
    assert len(q["choices"]) == 4, f"{q['id']}: Expected 4 choices, got {len(q['choices'])}"
    assert 0 <= q["correct_answer"] <= 3, f"{q['id']}: Invalid correct_answer {q['correct_answer']}"
    assert len(q["diagnostics"]) == 4, f"{q['id']}: Expected 4 diagnostics"
    assert len(q["hint"]) == 6, f"{q['id']}: Expected 6 hint levels"
    assert q["topic"] == "arithmetic_missing_numbers"
    assert 201 <= q["difficulty_score"] <= 300

# Count categories by tag
from collections import Counter
tag_counts = Counter()
for q in questions:
    for tag in q["tags"]:
        tag_counts[tag] += 1

# Count tiers
tier_counts = Counter(q["difficulty_tier"] for q in questions)

# Save
output = json.dumps(questions, indent=2, ensure_ascii=False)
with open("/sessions/optimistic-laughing-franklin/mnt/Downloads/kiwimath/content-v2/topic-2-arithmetic/g56_questions.json", "w") as f:
    f.write(output)

print(f"✅ Generated {len(questions)} questions")
print(f"\nID range: {questions[0]['id']} to {questions[-1]['id']}")
print(f"Difficulty range: {questions[0]['difficulty_score']} to {questions[-1]['difficulty_score']}")
print(f"\nDifficulty tiers:")
for t in ["advanced", "expert", "olympiad"]:
    print(f"  {t}: {tier_counts.get(t, 0)}")
print(f"\nCategory distribution (by primary tags):")
categories = [
    ("order-of-operations", "Order of Operations"),
    ("exponents", "Exponents & Powers"),
    ("GCD", "GCD"), ("LCM", "LCM"), ("factors", "Factors/Divisibility"),
    ("primes", "Prime Numbers"),
    ("fractions", "Fractions & Decimals"),
    ("number-theory", "Number Theory"),
    ("algebraic-thinking", "Algebraic Thinking"),
    ("integers", "Integer Properties"),
    ("ratios", "Ratios & Proportions"),
    ("estimation", "Estimation & Mental Math"),
    ("word-problems", "Word Problems"),
]
for tag, name in categories:
    print(f"  {name}: {tag_counts.get(tag, 0)}")
print(f"\nFile saved to: g56_questions.json")
print(f"File size: {len(output)} bytes")
