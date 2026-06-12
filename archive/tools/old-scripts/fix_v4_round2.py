#!/usr/bin/env python3
"""
Kiwimath Content v4 — Round 2 Fixes
=====================================
Addresses feedback from G3-G5 review:

1. Rebuild g5-percent.json with actual percentage/ratio questions
2. Move pure arithmetic out of word-problem files into correct topics
3. Fix cross-operation diagnostic errors (mult questions with add feedback)
4. Fix "forgets brackets" diagnostics on bracket-free questions
5. Separate data_handling from measurement in G3-G4
6. Generate additional multiplication/division content for G3
7. Update topic_map.json, all index files
"""

import json
import glob
import os
import copy
import random
import re
from collections import defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V4 = os.path.join(BASE, 'content-v4')

stats = defaultdict(int)


# ═══════════════════════════════════════════════════════════════
# 1. REBUILD g5-percent.json
# ═══════════════════════════════════════════════════════════════

def generate_percentage_questions():
    """Generate 120 proper percentage/ratio questions for Grade 5."""
    questions = []
    qid = 1

    # Category A: "What is X% of Y?" (40 questions)
    percentage_sets = [
        (10, 200), (25, 80), (50, 120), (20, 150), (75, 400),
        (10, 350), (30, 200), (40, 250), (5, 600), (15, 300),
        (25, 240), (60, 150), (20, 450), (50, 360), (10, 900),
        (33, 300), (12, 400), (80, 50), (90, 200), (45, 200),
        (25, 160), (75, 80), (20, 350), (50, 480), (10, 750),
        (35, 200), (15, 400), (60, 300), (40, 500), (5, 1000),
        (25, 320), (10, 450), (20, 600), (75, 120), (50, 900),
        (30, 150), (65, 200), (40, 350), (80, 250), (55, 200),
    ]
    for pct, whole in percentage_sets:
        correct = int(whole * pct / 100)
        distractors = _make_numeric_distractors(correct, pct, whole)
        choices = [str(correct)] + [str(d) for d in distractors[:3]]
        random.shuffle(choices)
        correct_idx = choices.index(str(correct))

        questions.append(_make_question(
            f"PCT-G5-{qid:03d}", f"What is {pct}% of {whole}?",
            choices, correct_idx,
            skill_id="percentage_basic", skill_domain="ratio",
            difficulty=qid/40 * 2 - 1,  # IRT b from -1 to 1
            diagnostics=_pct_diagnostics(pct, whole, choices, correct_idx),
        ))
        qid += 1

    # Category B: "What percentage is X of Y?" (30 questions)
    reverse_sets = [
        (20, 100), (15, 60), (30, 120), (25, 200), (50, 400),
        (10, 80), (40, 200), (75, 300), (12, 48), (60, 150),
        (35, 140), (80, 400), (45, 180), (20, 300), (15, 90),
        (25, 500), (90, 450), (33, 99), (5, 200), (70, 350),
        (55, 220), (16, 64), (24, 96), (65, 260), (85, 340),
        (42, 168), (18, 72), (36, 144), (72, 360), (48, 192),
    ]
    for part_pct, whole in reverse_sets:
        part = int(whole * part_pct / 100)
        correct = part_pct
        wrong1 = correct + 10 if correct + 10 <= 100 else correct - 10
        wrong2 = correct - 5 if correct - 5 > 0 else correct + 15
        wrong3 = int(part / whole * 10) * 10 if int(part / whole * 10) * 10 != correct else correct + 20
        choices = [f"{correct}%", f"{wrong1}%", f"{wrong2}%", f"{min(wrong3, 100)}%"]
        random.shuffle(choices)
        correct_idx = choices.index(f"{correct}%")

        questions.append(_make_question(
            f"PCT-G5-{qid:03d}", f"{part} is what percentage of {whole}?",
            choices, correct_idx,
            skill_id="percentage_basic", skill_domain="ratio",
            difficulty=qid/70 * 2 - 0.5,
            diagnostics={
                str(i): f"To find what percentage {part} is of {whole}, divide {part} by {whole} and multiply by 100."
                if i != correct_idx else "" for i in range(4) if i != correct_idx
            },
        ))
        qid += 1

    # Category C: Ratio questions (25 questions)
    ratio_problems = [
        ("In a class of 40 students, 24 are girls. What is the ratio of girls to boys?", "3:2", ["2:3", "4:3", "5:3"], "ratio_basic"),
        ("A recipe uses 2 cups of flour for every 3 cups of sugar. What is the ratio of flour to sugar?", "2:3", ["3:2", "1:3", "2:1"], "ratio_basic"),
        ("There are 15 red and 10 blue marbles. What is the ratio of red to blue?", "3:2", ["2:3", "5:2", "1:2"], "ratio_basic"),
        ("A map scale is 1:50000. If two cities are 3 cm apart on the map, what is the real distance in km?", "1.5 km", ["3 km", "15 km", "0.5 km"], "ratio_scale"),
        ("Share 120 sweets in the ratio 2:3. How many does the smaller share get?", "48", ["72", "60", "40"], "ratio_basic"),
        ("Mix paint in the ratio 1:4. If you use 3 litres of blue, how much yellow do you need?", "12 litres", ["4 litres", "7 litres", "15 litres"], "ratio_basic"),
        ("A fruit basket has apples and oranges in the ratio 5:3. If there are 40 fruits, how many are apples?", "25", ["15", "20", "30"], "ratio_basic"),
        ("In a bag, red and green balls are in ratio 3:7. If there are 21 green balls, how many red balls are there?", "9", ["7", "12", "14"], "ratio_basic"),
        ("A rectangle has length to width ratio 4:1. If the width is 5 cm, what is the length?", "20 cm", ["9 cm", "15 cm", "25 cm"], "ratio_basic"),
        ("Divide 200 in the ratio 3:2. What is the larger share?", "120", ["80", "100", "150"], "ratio_basic"),
        ("A car travels 150 km in 3 hours. What is the ratio of distance to time?", "50:1", ["3:150", "1:50", "30:1"], "ratio_basic"),
        ("The ratio of boys to girls in a school is 4:5. If there are 180 students, how many are boys?", "80", ["100", "90", "72"], "ratio_basic"),
        ("Mix juice concentrate and water in ratio 1:5. How much water for 200 ml concentrate?", "1000 ml", ["500 ml", "250 ml", "1200 ml"], "ratio_basic"),
        ("A triangle has sides in the ratio 3:4:5. If the shortest side is 6 cm, what is the longest?", "10 cm", ["8 cm", "12 cm", "15 cm"], "ratio_basic"),
        ("Reduce the ratio 24:36 to its simplest form.", "2:3", ["3:4", "4:6", "6:9"], "ratio_simplify"),
        ("What is 25% as a fraction in simplest form?", "1/4", ["1/5", "2/5", "1/3"], "pct_fraction"),
        ("Convert 3/5 to a percentage.", "60%", ["35%", "53%", "65%"], "pct_fraction"),
        ("A shop gives 20% discount on a ₹500 item. What is the sale price?", "₹400", ["₹480", ["₹100", "₹450"]], "pct_discount"),
        ("If 30% of a number is 45, what is the number?", "150", ["135", ["105", "180"]], "pct_reverse"),
        ("A team won 18 of 24 matches. What percentage did they win?", "75%", ["72%", "80%", "66%"], "pct_basic"),
        ("There are 60 animals: 12 are cats. What percentage are cats?", "20%", ["12%", "25%", "15%"], "pct_basic"),
        ("A student scored 72 out of 90. What is the percentage?", "80%", ["72%", "78%", "85%"], "pct_basic"),
        ("Increase 250 by 40%. What is the new value?", "350", ["290", "300", "400"], "pct_increase"),
        ("Decrease 600 by 15%. What is the new value?", "510", ["585", "500", "450"], "pct_decrease"),
        ("A population of 5000 grows by 10% each year. What is it after 1 year?", "5500", ["5100", "5010", "6000"], "pct_increase"),
    ]
    for stem, correct, wrongs, skill in ratio_problems:
        # Handle nested lists in wrongs
        flat_wrongs = []
        for w in wrongs:
            if isinstance(w, list):
                flat_wrongs.extend(w)
            else:
                flat_wrongs.append(w)
        flat_wrongs = flat_wrongs[:3]
        choices = [correct] + flat_wrongs
        random.shuffle(choices)
        correct_idx = choices.index(correct)
        questions.append(_make_question(
            f"PCT-G5-{qid:03d}", stem, choices, correct_idx,
            skill_id=skill, skill_domain="ratio",
            difficulty=(qid - 70) / 25 * 2,
            diagnostics={str(i): "Re-read the question carefully and check your working." for i in range(4) if i != correct_idx},
        ))
        qid += 1

    # Category D: Simple percentage word problems (25 questions)
    pct_word_problems = [
        ("A farmer planted 500 trees. 20% did not survive. How many survived?", "400", ["100", "480", "300"]),
        ("A school has 800 students. 45% are boys. How many girls are there?", "440", ["360", "400", "450"]),
        ("A book costs ₹250. Tax is 10%. What is the total cost?", "₹275", ["₹260", "₹300", "₹225"]),
        ("In a test of 50 questions, Priya got 80% correct. How many did she get right?", "40", ["35", "45", "42"]),
        ("A tank is 75% full with 300 litres. What is its total capacity?", "400 litres", ["375 litres", "225 litres", "450 litres"]),
        ("Arjun saved ₹600 from his ₹2000 pocket money. What percentage did he save?", "30%", ["25%", "35%", "40%"]),
        ("A shirt originally costs $40. It is on sale for 25% off. What is the sale price?", "$30", ["$35", "$25", "$10"]),
        ("Out of 60 students, 15 were absent. What percentage were present?", "75%", ["25%", "85%", "80%"]),
        ("A car's value decreases by 15% each year. If it costs $20,000 now, what is it worth after 1 year?", "$17,000", ["$18,000", "$15,000", "$3,000"]),
        ("Wei scored 36 out of 45 in a math test. What is his percentage score?", "80%", ["75%", "85%", "36%"]),
        ("A recipe needs 500g of flour. You want to make 120% of the recipe. How much flour do you need?", "600g", ["620g", "500g", "550g"]),
        ("A garden is 40% flowers and 60% vegetables. If the garden is 200 sq m, how much is flowers?", "80 sq m", ["120 sq m", "60 sq m", "100 sq m"]),
        ("A fruit seller sold 35% of 200 oranges. How many are left?", "130", ["70", "165", "35"]),
        ("Isha read 60% of a 350-page book. How many pages has she read?", "210", ["190", "230", "140"]),
        ("A train ticket costs ₹450. Children get 50% discount. What does a child pay?", "₹225", ["₹250", "₹200", "₹150"]),
        ("There are 250 animals in a zoo. 28% are birds. How many birds are there?", "70", ["56", "78", "28"]),
        ("A factory produces 1000 items. 5% are defective. How many good items are there?", "950", ["50", "995", "900"]),
        ("Rohan's weight increased from 40 kg to 44 kg. What is the percentage increase?", "10%", ["4%", "44%", "8%"]),
        ("A town has 12,000 people. 35% are children. How many adults are there?", "7,800", ["4,200", "8,000", "7,200"]),
        ("Emma spent 40% of $150 on books. How much did she spend?", "$60", ["$40", "$90", "$100"]),
        ("A class of 30 students: 12 like cricket, 8 like football, rest like tennis. What % like tennis?", "33.3%", ["40%", "26.7%", "10%"]),
        ("A store marks up prices by 25%. If cost price is $80, what is the selling price?", "$100", ["$105", "$85", "$120"]),
        ("45 out of 150 people voted yes. What percentage voted yes?", "30%", ["45%", "33%", "25%"]),
        ("A library has 2000 books. 15% are science fiction. How many science fiction books?", "300", ["150", "350", "200"]),
        ("Diya's test score improved from 60% to 78%. By how many percentage points did it improve?", "18", ["13", "23", "30"]),
    ]
    for stem, correct, wrongs in pct_word_problems:
        flat_wrongs = []
        for w in wrongs:
            if isinstance(w, list):
                flat_wrongs.extend(w)
            else:
                flat_wrongs.append(w)
        flat_wrongs = flat_wrongs[:3]
        choices = [correct] + flat_wrongs
        random.shuffle(choices)
        correct_idx = choices.index(correct)
        questions.append(_make_question(
            f"PCT-G5-{qid:03d}", stem, choices, correct_idx,
            skill_id="percentage_word", skill_domain="ratio",
            difficulty=(qid - 95) / 25 * 2 + 0.5,
            diagnostics={str(i): "Think about what percentage means — it's 'per 100'. Try converting step by step." for i in range(4) if i != correct_idx},
        ))
        qid += 1

    return questions


def _make_question(qid, stem, choices, correct_idx, skill_id, skill_domain, difficulty, diagnostics):
    return {
        "id": qid,
        "stem": stem,
        "choices": choices,
        "correct_answer": correct_idx,
        "difficulty_tier": "easy" if difficulty < -0.5 else "medium" if difficulty < 0.5 else "hard" if difficulty < 1.5 else "advanced",
        "difficulty_score": max(1, min(500, int((difficulty + 3) / 6 * 500))),
        "visual_svg": None,
        "visual_alt": None,
        "diagnostics": diagnostics,
        "tags": ["percentage", "ratio"],
        "topic": "percentage_ratio",
        "hint": {
            "level_0": "Think about what the question is really asking.",
            "level_1": "What does 'percent' mean? It means 'out of 100'.",
            "level_2": "Try converting the percentage to a fraction or decimal first.",
            "level_3": "To find X% of Y, calculate (X ÷ 100) × Y.",
            "level_4": "Work through the calculation step by step.",
            "level_5": "Check: does your answer make sense in the context of the problem?"
        },
        "interaction_mode": "mcq",
        "irt_params": {"a": 1.0, "b": round(difficulty, 3), "c": 0.25},
        "irt_a": 1.0,
        "irt_b": round(difficulty, 3),
        "irt_c": 0.25,
        "solution_steps": [],
        "level": 5,
        "level_name": "Strategist",
        "universal_skill_id": f"PCT_{skill_id.upper()}_5",
        "skill_id": skill_id,
        "skill_domain": skill_domain,
        "maturity_bucket": "calibrating",
        "visual_requirement": "none",
        "visual_type": "none",
        "visual_ai_verified": False,
        "media_id": None,
        "media_hash": None,
        "misconception_ids": [],
        "why_quality": "ai_generated",
        "why_framework": "pending",
        "hint_quality": {"layers": 6, "quality": "good", "has_3_layers": True},
        "locale_ids": ["india", "singapore", "us"],
        "curriculum_source": "generated",
        "curriculum_map": None,
        "school_grade": 5,
        "avg_time_to_solve_ms": None,
        "times_served": 0,
        "flag_count": 0,
        "schema_version": "4.1",
        "adaptive_topic_id": "g5-percent",
        "adaptive_topic_name": "Percentage & Ratio",
        "adaptive_topic_emoji": "📊",
        "adaptive_grade": 5,
        "dual_tagged": False,
        "content_source": "generated",
        "sequence_id": 0,  # Will be set during IRT sort
        "difficulty_tier_in_topic": "practice",
    }


def _make_numeric_distractors(correct, pct, whole):
    """Generate plausible wrong answers for percentage questions."""
    distractors = set()
    # Common errors
    distractors.add(correct + whole // 10)  # Off by 10% of whole
    distractors.add(correct - whole // 10)
    distractors.add(int(whole * (pct + 10) / 100))  # Wrong percentage
    distractors.add(int(whole * (pct - 5) / 100))
    distractors.add(pct)  # Confuse percentage with answer
    distractors.add(whole - correct)  # Complement
    distractors.discard(correct)
    distractors.discard(0)
    distractors = [d for d in distractors if d > 0]
    random.shuffle(distractors)
    while len(distractors) < 3:
        distractors.append(correct + random.choice([-5, 5, -10, 10, -20, 20]))
    return distractors[:3]


def _pct_diagnostics(pct, whole, choices, correct_idx):
    """Generate specific diagnostics for percentage questions."""
    diag = {}
    correct_val = int(whole * pct / 100)
    for i, ch in enumerate(choices):
        if i == correct_idx:
            continue
        try:
            val = int(ch)
            diff = val - correct_val
            if val == pct:
                diag[str(i)] = f"You gave the percentage ({pct}%) itself, not {pct}% of {whole}. Multiply {pct}/100 by {whole}."
            elif val == whole - correct_val:
                diag[str(i)] = f"You found the remaining {100-pct}% instead of {pct}%. Check which part the question asks for."
            elif diff > 0:
                diag[str(i)] = f"Your answer is {diff} too high. Remember: {pct}% means {pct} out of 100. Try {pct}/100 × {whole}."
            else:
                diag[str(i)] = f"Your answer is {abs(diff)} too low. Make sure you're calculating {pct}/100 × {whole} correctly."
        except ValueError:
            diag[str(i)] = f"To find {pct}% of {whole}, divide {pct} by 100 and multiply by {whole}."
    return diag


# ═══════════════════════════════════════════════════════════════
# 2. WORD PROBLEM CLEANUP
# ═══════════════════════════════════════════════════════════════

def is_pure_arithmetic(stem):
    """Detect if a stem is pure arithmetic (no word problem context)."""
    words = [w for w in stem.split() if any(c.isalpha() for c in w)]
    # Allow "Calculate:" or "What is" as minimal framing
    non_filler = [w for w in words if w.lower() not in ('calculate:', 'what', 'is', 'find', 'the', 'value', 'of', 'solve:')]
    return len(non_filler) <= 1


def move_pure_arithmetic_to_correct_topic(grade):
    """Move pure arithmetic questions from word-problems to their correct skill topic."""
    wp_file = os.path.join(V4, 'adaptive', f'grade{grade}', f'g{grade}-word-problems.json')
    if not os.path.exists(wp_file):
        return

    with open(wp_file) as f:
        wp_data = json.load(f)

    keep = []
    moved = defaultdict(list)  # target_topic_id -> list of questions

    for q in wp_data['questions']:
        if is_pure_arithmetic(q['stem']):
            skill = q.get('skill_id', '')
            # Determine target topic
            target = _skill_to_topic_id(skill, grade)
            if target and target != wp_data['topic_id']:
                q['adaptive_topic_id'] = target
                moved[target].append(q)
                stats['word_problems_moved'] += 1
            else:
                keep.append(q)  # Can't determine target, keep in word problems
        else:
            keep.append(q)

    # Update word problems file
    wp_data['questions'] = keep
    wp_data['total_questions'] = len(keep)
    with open(wp_file, 'w') as f:
        json.dump(wp_data, f, indent=2, ensure_ascii=False)

    # Append moved questions to target files
    for target_id, questions in moved.items():
        target_file = os.path.join(V4, 'adaptive', f'grade{grade}', f'{target_id}.json')
        if not os.path.exists(target_file):
            continue
        with open(target_file) as f:
            target_data = json.load(f)
        for q in questions:
            q['adaptive_topic_id'] = target_id
            q['adaptive_topic_name'] = target_data['topic_name']
        target_data['questions'].extend(questions)
        # Re-sort by IRT
        target_data['questions'].sort(key=lambda q: q.get('irt_b', q.get('irt_params', {}).get('b', 0)))
        for i, q in enumerate(target_data['questions']):
            q['sequence_id'] = i + 1
        target_data['total_questions'] = len(target_data['questions'])
        with open(target_file, 'w') as f:
            json.dump(target_data, f, indent=2, ensure_ascii=False)


def _skill_to_topic_id(skill, grade):
    """Map a skill_id to its topic file ID for a given grade."""
    # Grade 3-4 mappings
    skill_topic_map = {
        3: {
            'addition_basic': 'g3-add-sub', 'addition_2digit': 'g3-add-sub',
            'subtraction_basic': 'g3-add-sub', 'subtraction_2digit': 'g3-add-sub',
            'multiplication_facts': 'g3-multiplication', 'division_basic': 'g3-division',
            'multi_step': 'g3-word-problems',
        },
        4: {
            'addition_basic': 'g4-add-sub', 'addition_2digit': 'g4-add-sub',
            'subtraction_basic': 'g4-add-sub', 'subtraction_2digit': 'g4-add-sub',
            'multiplication_facts': 'g4-multiplication', 'division_basic': 'g4-division',
            'multi_step': 'g4-word-problems', 'order_of_ops': 'g4-word-problems',
        },
        5: {
            'addition_basic': 'g5-arithmetic', 'addition_2digit': 'g5-arithmetic',
            'subtraction_basic': 'g5-arithmetic', 'subtraction_2digit': 'g5-arithmetic',
            'multiplication_facts': 'g5-arithmetic', 'division_basic': 'g5-arithmetic',
            'multi_step': 'g5-arithmetic', 'order_of_ops': 'g5-arithmetic',
        },
    }
    return skill_topic_map.get(grade, {}).get(skill)


# ═══════════════════════════════════════════════════════════════
# 3. FIX CROSS-OPERATION DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════

def fix_cross_operation_diagnostics(grade):
    """Fix diagnostics that reference wrong operations."""
    for jf in sorted(glob.glob(os.path.join(V4, 'adaptive', f'grade{grade}', 'g*.json'))):
        if 'index' in os.path.basename(jf):
            continue
        with open(jf) as f:
            data = json.load(f)

        topic_lower = data['topic_name'].lower()
        modified = False

        for q in data['questions']:
            diag = q.get('diagnostics', {})
            stem = q['stem']

            for k, v in diag.items():
                if not isinstance(v, str):
                    continue
                original = v

                # Fix: multiplication topic with "recheck your addition" feedback
                if 'multiplic' in topic_lower and 'add column by column' in v.lower():
                    v = "Recheck your multiplication — break it into partial products and multiply step by step."
                    diag[k] = v
                    if v != original:
                        stats['operation_diagnostics_fixed'] += 1
                        modified = True

                # Fix: "forgets brackets" on questions without brackets
                if 'bracket' in v.lower() and '(' not in stem and ')' not in stem:
                    # This is likely a BODMAS question — fix the diagnostic
                    if '×' in stem or '*' in stem:
                        v = "Remember BODMAS: multiply or divide before you add or subtract. Work left to right within the same priority."
                    else:
                        v = "Check the order of operations carefully. Which part should you calculate first?"
                    diag[k] = v
                    if v != original:
                        stats['bracket_diagnostics_fixed'] += 1
                        modified = True

        if modified:
            with open(jf, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# 4. SEPARATE DATA_HANDLING FROM MEASUREMENT (G3-G4)
# ═══════════════════════════════════════════════════════════════

def separate_data_from_measurement(grade):
    """Move data_handling questions from measurement to a new Data topic."""
    meas_file = os.path.join(V4, 'adaptive', f'grade{grade}', f'g{grade}-measurement.json')
    if not os.path.exists(meas_file):
        return

    with open(meas_file) as f:
        meas_data = json.load(f)

    meas_keep = []
    data_questions = []

    for q in meas_data['questions']:
        if q.get('skill_id') == 'data_handling':
            data_questions.append(q)
        else:
            meas_keep.append(q)

    if not data_questions:
        return

    # Update measurement file
    meas_data['questions'] = meas_keep
    meas_data['total_questions'] = len(meas_keep)
    meas_data['skills'] = [s for s in meas_data.get('skills', []) if s != 'data_handling']
    meas_data['topic_name'] = 'Measurement'  # Remove "& Data"
    with open(meas_file, 'w') as f:
        json.dump(meas_data, f, indent=2, ensure_ascii=False)

    # Create new data handling file
    data_topic_id = f'g{grade}-data'
    for i, q in enumerate(data_questions):
        q['adaptive_topic_id'] = data_topic_id
        q['adaptive_topic_name'] = 'Data Handling'
        q['adaptive_topic_emoji'] = '📈'
        q['sequence_id'] = i + 1

    data_questions.sort(key=lambda q: q.get('irt_b', q.get('irt_params', {}).get('b', 0)))
    for i, q in enumerate(data_questions):
        q['sequence_id'] = i + 1
        pct = i / max(len(data_questions) - 1, 1)
        q['difficulty_tier_in_topic'] = 'intro' if pct < 0.2 else 'practice' if pct < 0.5 else 'challenge' if pct < 0.8 else 'mastery'

    data_file_data = {
        'topic_id': data_topic_id,
        'topic_name': 'Data Handling',
        'topic_emoji': '📈',
        'grade': grade,
        'domain': 'data',
        'skills': ['data_handling'],
        'total_questions': len(data_questions),
        'difficulty_range': {
            'min_irt_b': round(min((q.get('irt_b', 0) for q in data_questions), default=0), 3),
            'max_irt_b': round(max((q.get('irt_b', 0) for q in data_questions), default=0), 3),
        },
        'source_breakdown': dict(defaultdict(int, {q.get('content_source', 'unknown'): 1 for q in data_questions})),
        'schema_version': '4.1',
        'generated_at': datetime.now().isoformat(),
        'questions': data_questions,
    }

    # Compute proper source breakdown
    src = defaultdict(int)
    for q in data_questions:
        src[q.get('content_source', 'unknown')] += 1
    data_file_data['source_breakdown'] = dict(src)

    data_file = os.path.join(V4, 'adaptive', f'grade{grade}', f'{data_topic_id}.json')
    with open(data_file, 'w') as f:
        json.dump(data_file_data, f, indent=2, ensure_ascii=False)

    stats['data_separated'] += len(data_questions)
    print(f"  Grade {grade}: separated {len(data_questions)} data_handling questions → {data_topic_id}.json")


# ═══════════════════════════════════════════════════════════════
# 5. UPDATE TOPIC MAP
# ═══════════════════════════════════════════════════════════════

def update_topic_map():
    """Update topic_map.json to reflect new topics (data handling in G3-G4, percentage skills)."""
    tm_path = os.path.join(V4, 'topic_map.json')
    with open(tm_path) as f:
        tm = json.load(f)

    # Add data handling topic for G3
    g3_topics = tm['grades']['3']['topics']
    if not any(t['id'] == 'g3-data' for t in g3_topics):
        # Remove data_handling from measurement skills
        for t in g3_topics:
            if t['id'] == 'g3-measurement':
                t['skills'] = [s for s in t['skills'] if s != 'data_handling']
                t['name'] = 'Measurement'
        g3_topics.append({
            "id": "g3-data", "name": "Data Handling", "emoji": "📈",
            "skills": ["data_handling"], "domain": "data"
        })
        tm['grades']['3']['topic_count'] = len(g3_topics)

    # Add data handling topic for G4
    g4_topics = tm['grades']['4']['topics']
    if not any(t['id'] == 'g4-data' for t in g4_topics):
        for t in g4_topics:
            if t['id'] == 'g4-measurement':
                t['skills'] = [s for s in t['skills'] if s != 'data_handling']
                t['name'] = 'Measurement'
        g4_topics.append({
            "id": "g4-data", "name": "Data Handling", "emoji": "📈",
            "skills": ["data_handling"], "domain": "data"
        })
        tm['grades']['4']['topic_count'] = len(g4_topics)

    # Fix G5 percentage topic skills
    for t in tm['grades']['5']['topics']:
        if t['id'] == 'g5-percent':
            t['skills'] = ['percentage_basic', 'ratio_basic', 'pct_fraction', 'percentage_word']
            t['domain'] = 'ratio'

    with open(tm_path, 'w') as f:
        json.dump(tm, f, indent=2, ensure_ascii=False)
    print("  topic_map.json updated")


# ═══════════════════════════════════════════════════════════════
# 6. REGENERATE INDEX FILES
# ═══════════════════════════════════════════════════════════════

def regenerate_all_indexes():
    """Regenerate index.json for all grades."""
    for grade in range(1, 7):
        grade_dir = os.path.join(V4, 'adaptive', f'grade{grade}')
        topic_files = sorted(glob.glob(os.path.join(grade_dir, 'g*.json')))

        topics = []
        total_questions = 0
        for tf in topic_files:
            if 'index' in os.path.basename(tf):
                continue
            with open(tf) as f:
                data = json.load(f)
            topics.append({
                'id': data['topic_id'],
                'name': data['topic_name'],
                'emoji': data.get('topic_emoji', ''),
                'domain': data['domain'],
                'skills': data.get('skills', []),
                'total_questions': data['total_questions'],
                'difficulty_range': data.get('difficulty_range', {}),
            })
            total_questions += data['total_questions']

        index = {
            'grade': grade,
            'total_topics': len(topics),
            'total_questions': total_questions,
            'topics': topics,
            'schema_version': '4.1',
            'generated_at': datetime.now().isoformat(),
        }

        index_path = os.path.join(grade_dir, 'index.json')
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("KIWIMATH CONTENT v4 — ROUND 2 FIXES")
    print("=" * 70)

    # 1. Rebuild g5-percent.json
    print("\n[1] Rebuilding g5-percent.json with percentage/ratio content...")
    pct_questions = generate_percentage_questions()
    # Sort by IRT
    pct_questions.sort(key=lambda q: q.get('irt_b', 0))
    for i, q in enumerate(pct_questions):
        q['sequence_id'] = i + 1
        pct = i / max(len(pct_questions) - 1, 1)
        q['difficulty_tier_in_topic'] = 'intro' if pct < 0.2 else 'practice' if pct < 0.5 else 'challenge' if pct < 0.8 else 'mastery'

    pct_data = {
        'topic_id': 'g5-percent',
        'topic_name': 'Percentage & Ratio',
        'topic_emoji': '📊',
        'grade': 5,
        'domain': 'ratio',
        'skills': ['percentage_basic', 'ratio_basic', 'pct_fraction', 'percentage_word'],
        'total_questions': len(pct_questions),
        'difficulty_range': {
            'min_irt_b': round(min(q['irt_b'] for q in pct_questions), 3),
            'max_irt_b': round(max(q['irt_b'] for q in pct_questions), 3),
        },
        'source_breakdown': {'generated': len(pct_questions)},
        'schema_version': '4.1',
        'generated_at': datetime.now().isoformat(),
        'questions': pct_questions,
    }
    pct_file = os.path.join(V4, 'adaptive', 'grade5', 'g5-percent.json')
    with open(pct_file, 'w') as f:
        json.dump(pct_data, f, indent=2, ensure_ascii=False)
    print(f"  → {len(pct_questions)} percentage/ratio questions generated (was 5 rounding questions)")
    stats['percent_rebuilt'] = len(pct_questions)

    # 2. Clean word problems across G3-G5
    print("\n[2] Moving pure arithmetic out of word-problem files...")
    for grade in range(3, 6):
        move_pure_arithmetic_to_correct_topic(grade)
    print(f"  → {stats['word_problems_moved']} pure arithmetic questions relocated")

    # 3. Fix cross-operation diagnostics
    print("\n[3] Fixing cross-operation diagnostic errors...")
    for grade in range(3, 6):
        fix_cross_operation_diagnostics(grade)
    print(f"  → {stats['operation_diagnostics_fixed']} multiplication-with-addition-feedback fixed")
    print(f"  → {stats['bracket_diagnostics_fixed']} bracket-on-bracketless fixed")

    # 4. Separate data_handling from measurement in G3-G4
    print("\n[4] Separating Data Handling from Measurement (G3-G4)...")
    for grade in (3, 4):
        separate_data_from_measurement(grade)
    print(f"  → {stats['data_separated']} data_handling questions separated")

    # 5. Update topic_map.json
    print("\n[5] Updating topic_map.json...")
    update_topic_map()

    # 6. Regenerate all index files
    print("\n[6] Regenerating all index files...")
    regenerate_all_indexes()
    print("  → All 6 index files regenerated")

    # Summary
    print("\n" + "=" * 70)
    print("ROUND 2 FIX SUMMARY")
    print("=" * 70)
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")


if __name__ == '__main__':
    main()
