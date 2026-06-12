#!/usr/bin/env python3
"""
Terry Chew-Style "Why" Explanation Rewriter
============================================
Rewrites generic template "why" explanations in all_questions.json
with specific, math-aware, step-by-step explanations following
Terry Chew's Olympiad pedagogy:

1. Use ACTUAL numbers from the problem
2. Show each arithmetic step explicitly
3. State the key insight/principle
4. Arrive at a clear answer
5. Never give generic advice

Usage:
    python scripts/terry_chew_rewriter.py [--dry-run] [--sample N]
"""

import json
import re
import sys
import os
from pathlib import Path

QUESTIONS_PATH = Path(__file__).parent.parent / "static" / "all_questions.json"


def extract_numbers(text):
    """Extract all numbers from text."""
    return [int(x) for x in re.findall(r'\b\d+\b', text)]


def extract_number_sequence(stem):
    """Extract a sequence of numbers from pattern questions like '1, 2, 4, 8, ?'"""
    # Match patterns like "2, 4, 6, 8, ?" or "What comes next: 1, 3, 5, ?"
    m = re.search(r'(\d+(?:\s*,\s*\d+){2,})\s*,?\s*\?', stem)
    if m:
        return [int(x.strip()) for x in m.group(1).split(',')]
    return None


def extract_currency(text):
    """Extract currency amounts like ₹6, $10, etc."""
    amounts = re.findall(r'[₹$£]\s*(\d+(?:\.\d+)?)', text)
    return [float(x) for x in amounts]


def extract_measurement(text):
    """Extract measurement values and units."""
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*(cm|mm|mL|ml|km|kg|m|g|l|L)\b', text)
    return [(float(v), u) for v, u in matches]


def extract_time(text):
    """Extract time like 8:30, 4:55."""
    matches = re.findall(r'(\d{1,2}):(\d{2})', text)
    return [(int(h), int(m)) for h, m in matches]


def extract_dimensions(text):
    """Extract length/width/side dimensions."""
    length = re.search(r'length\s+(\d+)', text, re.I)
    width = re.search(r'width\s+(\d+)', text, re.I)
    side = re.search(r'side\s+(\d+)', text, re.I)
    radius = re.search(r'radius\s+(\d+)', text, re.I)
    return {
        'length': int(length.group(1)) if length else None,
        'width': int(width.group(1)) if width else None,
        'side': int(side.group(1)) if side else None,
        'radius': int(radius.group(1)) if radius else None,
    }


# ─── Conversion factors ───────────────────────────────────────────────
CONVERSION = {
    ('m', 'cm'): 100, ('cm', 'm'): 0.01,
    ('km', 'm'): 1000, ('m', 'km'): 0.001,
    ('cm', 'mm'): 10, ('mm', 'cm'): 0.1,
    ('km', 'cm'): 100000,
    ('kg', 'g'): 1000, ('g', 'kg'): 0.001,
    ('l', 'ml'): 1000, ('ml', 'l'): 0.001,
    ('L', 'ml'): 1000, ('ml', 'L'): 0.001,
    ('l', 'mL'): 1000, ('mL', 'l'): 0.001,
    ('L', 'mL'): 1000, ('mL', 'L'): 0.001,
}

UNIT_NAMES = {
    'm': 'metre', 'cm': 'centimetre', 'mm': 'millimetre', 'km': 'kilometre',
    'g': 'gram', 'kg': 'kilogram', 'l': 'litre', 'L': 'litre', 'ml': 'millilitre',
}


def rewrite_conversion(q):
    """Rewrite unit conversion questions."""
    stem = q['s']
    answer = q['c'][q['a']]

    # Extract source value and units
    m = re.search(r'[Cc]onvert\s+(\d+(?:\.\d+)?)\s*(cm|mm|mL|ml|km|kg|m|g|l|L)', stem)
    if not m:
        return None

    val = float(m.group(1))
    from_unit = m.group(2)

    # Find target unit from answer
    m2 = re.search(r'(\d+(?:\.\d+)?)\s*(cm|mm|mL|ml|km|kg|m|g|l|L)', answer)
    if not m2:
        return None

    to_unit = m2.group(2)
    result_val = m2.group(1)

    factor_key = (from_unit, to_unit)
    if factor_key in CONVERSION:
        factor = CONVERSION[factor_key]
        if factor >= 1:
            op = "multiply"
            return (f"Key fact: 1 {from_unit} = {int(factor)} {to_unit}.\n"
                    f"So {int(val) if val == int(val) else val} {from_unit} "
                    f"= {int(val) if val == int(val) else val} × {int(factor)} "
                    f"= {result_val} {to_unit}.\n"
                    f"Answer: {answer}.")
        else:
            divisor = int(1 / factor)
            return (f"Key fact: {divisor} {from_unit} = 1 {to_unit}.\n"
                    f"So {int(val) if val == int(val) else val} {from_unit} "
                    f"÷ {divisor} = {result_val} {to_unit}.\n"
                    f"Answer: {answer}.")
    return None


def rewrite_perimeter(q):
    """Rewrite perimeter questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    dims = extract_dimensions(stem)

    if 'square' in stem.lower():
        s = dims['side']
        if s:
            return (f"A square has 4 equal sides.\n"
                    f"Perimeter = 4 × side = 4 × {s} = {4 * s} cm.\n"
                    f"Answer: {answer}.")

    if 'rectangle' in stem.lower():
        l, w = dims['length'], dims['width']
        if l and w:
            return (f"A rectangle has 2 pairs of equal sides.\n"
                    f"Perimeter = 2 × (length + width)\n"
                    f"= 2 × ({l} + {w})\n"
                    f"= 2 × {l + w}\n"
                    f"= {2 * (l + w)} cm.\n"
                    f"Answer: {answer}.")

    # Try to extract just numbers for generic polygon perimeter
    nums = extract_numbers(stem)
    if len(nums) >= 3:
        total = sum(nums)
        steps = ' + '.join(str(n) for n in nums)
        return (f"Perimeter = sum of all sides.\n"
                f"= {steps} = {total}.\n"
                f"Answer: {answer}.")

    return None


def rewrite_area(q):
    """Rewrite area questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    dims = extract_dimensions(stem)

    if 'square' in stem.lower():
        s = dims['side']
        if s:
            return (f"Area of a square = side × side.\n"
                    f"= {s} × {s} = {s * s} sq cm.\n"
                    f"Answer: {answer}.")

    if 'rectangle' in stem.lower():
        l, w = dims['length'], dims['width']
        if l and w:
            return (f"Area of a rectangle = length × width.\n"
                    f"= {l} × {w} = {l * w} sq cm.\n"
                    f"Answer: {answer}.")

    if 'triangle' in stem.lower():
        base = re.search(r'base\s+(\d+)', stem, re.I)
        height = re.search(r'height\s+(\d+)', stem, re.I)
        if base and height:
            b, h = int(base.group(1)), int(height.group(1))
            return (f"Area of a triangle = ½ × base × height.\n"
                    f"= ½ × {b} × {h}\n"
                    f"= {b * h} ÷ 2 = {b * h // 2} sq cm.\n"
                    f"Answer: {answer}.")

    return None


def rewrite_pattern(q):
    """Rewrite pattern/sequence questions."""
    stem = q['s']
    answer = q['c'][q['a']]

    seq = extract_number_sequence(stem)
    if not seq or len(seq) < 3:
        return None

    # Calculate differences
    diffs = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]

    # Constant difference
    if len(set(diffs)) == 1:
        d = diffs[0]
        diff_str = ', '.join(str(d) for d in diffs)
        op = '+' if d > 0 else ''
        return (f"Write the differences between consecutive terms:\n"
                f"{diff_str} — constant difference of {abs(d)}.\n"
                f"Rule: each term {'increases' if d > 0 else 'decreases'} by {abs(d)}.\n"
                f"Next term: {seq[-1]} {op} {d} = {seq[-1] + d}.\n"
                f"Answer: {answer}.")

    # Check for multiplication pattern
    if all(seq[i] != 0 for i in range(len(seq) - 1)):
        ratios = [seq[i + 1] / seq[i] for i in range(len(seq) - 1)]
        if len(set(ratios)) == 1 and ratios[0] == int(ratios[0]):
            r = int(ratios[0])
            return (f"Check the ratio between consecutive terms:\n"
                    f"Each term is multiplied by {r}.\n"
                    f"Next term: {seq[-1]} × {r} = {seq[-1] * r}.\n"
                    f"Answer: {answer}.")

    # Increasing differences
    diff_diffs = [diffs[i + 1] - diffs[i] for i in range(len(diffs) - 1)]
    if len(set(diff_diffs)) == 1:
        dd = diff_diffs[0]
        next_diff = diffs[-1] + dd
        diff_str = ', '.join(str(d) for d in diffs)
        return (f"Write the differences between consecutive terms:\n"
                f"{diff_str}.\n"
                f"The differences increase by {dd} each time.\n"
                f"Next difference: {diffs[-1]} + {dd} = {next_diff}.\n"
                f"Next term: {seq[-1]} + {next_diff} = {seq[-1] + next_diff}.\n"
                f"Answer: {answer}.")

    # Alternating pattern
    if len(diffs) >= 4:
        even_diffs = diffs[0::2]
        odd_diffs = diffs[1::2]
        if len(set(even_diffs)) == 1 and len(set(odd_diffs)) == 1:
            return (f"The pattern alternates between adding {even_diffs[0]} and {odd_diffs[0]}.\n"
                    f"Last difference was {diffs[-1]}, so next is {diffs[-2]}.\n"
                    f"Next term: {seq[-1]} + {diffs[-2]} = {seq[-1] + diffs[-2]}.\n"
                    f"Answer: {answer}.")

    # Fallback for sequences we can't crack
    diff_str = ', '.join(str(d) for d in diffs)
    return (f"Differences between terms: {diff_str}.\n"
            f"Following this pattern, the next term is {answer}.\n"
            f"Answer: {answer}.")


def rewrite_addition(q):
    """Rewrite addition word problems."""
    stem = q['s']
    answer = q['c'][q['a']]
    nums = extract_numbers(stem)
    answer_num = extract_numbers(answer)

    if not answer_num:
        return None

    ans = answer_num[0]

    # Simple two-number addition
    if len(nums) >= 2:
        # Find which pair sums to the answer
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == ans:
                    return (f"We need to add: {nums[i]} + {nums[j]}.\n"
                            f"{nums[i]} + {nums[j]} = {ans}.\n"
                            f"Answer: {answer}.")

        # Multiple additions
        if sum(nums) == ans:
            steps = ' + '.join(str(n) for n in nums)
            return (f"Add all the amounts:\n"
                    f"{steps} = {ans}.\n"
                    f"Answer: {answer}.")

        # Just use the two largest or most likely
        if len(nums) == 2:
            return (f"Add: {nums[0]} + {nums[1]} = {nums[0] + nums[1]}.\n"
                    f"Answer: {answer}.")

    return None


def rewrite_subtraction(q):
    """Rewrite subtraction word problems."""
    stem = q['s']
    answer = q['c'][q['a']]
    nums = extract_numbers(stem)
    answer_num = extract_numbers(answer)

    if not answer_num:
        return None

    ans = answer_num[0]

    if len(nums) >= 2:
        for i in range(len(nums)):
            for j in range(len(nums)):
                if i != j and nums[i] - nums[j] == ans:
                    return (f"Subtract: {nums[i]} − {nums[j]}.\n"
                            f"{nums[i]} − {nums[j]} = {ans}.\n"
                            f"Answer: {answer}.")

    return None


def rewrite_multiplication(q):
    """Rewrite multiplication problems."""
    stem = q['s']
    answer = q['c'][q['a']]
    nums = extract_numbers(stem)
    answer_num = extract_numbers(answer)

    if not answer_num:
        return None

    ans = answer_num[0]

    if len(nums) >= 2:
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] * nums[j] == ans:
                    return (f"Multiply: {nums[i]} × {nums[j]}.\n"
                            f"{nums[i]} × {nums[j]} = {ans}.\n"
                            f"Answer: {answer}.")

    return None


def rewrite_division(q):
    """Rewrite division problems."""
    stem = q['s']
    answer = q['c'][q['a']]
    nums = extract_numbers(stem)
    answer_num = extract_numbers(answer)

    if not answer_num:
        return None

    ans = answer_num[0]

    if len(nums) >= 2:
        for i in range(len(nums)):
            for j in range(len(nums)):
                if i != j and nums[j] != 0 and nums[i] / nums[j] == ans:
                    return (f"Divide: {nums[i]} ÷ {nums[j]}.\n"
                            f"{nums[i]} ÷ {nums[j]} = {ans}.\n"
                            f"Answer: {answer}.")
                # Check remainder
                if i != j and nums[j] != 0:
                    quot = nums[i] // nums[j]
                    rem = nums[i] % nums[j]
                    if quot == ans or rem == ans:
                        return (f"Divide: {nums[i]} ÷ {nums[j]}.\n"
                                f"{nums[i]} ÷ {nums[j]} = {quot} remainder {rem}.\n"
                                f"Answer: {answer}.")

    return None


def rewrite_money(q):
    """Rewrite money questions."""
    stem = q['s']
    answer = q['c'][q['a']]

    amounts = extract_currency(stem)
    answer_amounts = extract_currency(answer)

    s_lower = stem.lower()

    if 'change' in s_lower and len(amounts) >= 2:
        paid = max(amounts)
        cost = min(amounts)
        change = paid - cost
        return (f"Change = Amount paid − Cost.\n"
                f"= ₹{int(paid)} − ₹{int(cost)}\n"
                f"= ₹{int(change)}.\n"
                f"Answer: {answer}.")

    if ('total' in s_lower or 'altogether' in s_lower or 'all' in s_lower) and len(amounts) >= 2:
        total = sum(amounts)
        steps = ' + '.join(f'₹{int(a)}' for a in amounts)
        return (f"Add all the amounts:\n"
                f"{steps} = ₹{int(total)}.\n"
                f"Answer: {answer}.")

    if len(amounts) >= 2 and answer_amounts:
        ans = answer_amounts[0]
        # Try subtraction
        for i in range(len(amounts)):
            for j in range(len(amounts)):
                if i != j and amounts[i] - amounts[j] == ans:
                    return (f"₹{int(amounts[i])} − ₹{int(amounts[j])} = ₹{int(ans)}.\n"
                            f"Answer: {answer}.")
        # Try addition
        if sum(amounts) == ans:
            steps = ' + '.join(f'₹{int(a)}' for a in amounts)
            return (f"{steps} = ₹{int(ans)}.\n"
                    f"Answer: {answer}.")

    return None


def rewrite_time(q):
    """Rewrite time questions."""
    stem = q['s']
    answer = q['c'][q['a']]

    times = extract_time(stem)
    mins_match = re.search(r'(\d+)\s*minutes?', stem)
    hours_match = re.search(r'(\d+)\s*hours?', stem)

    if times and (mins_match or hours_match):
        h, m = times[0]
        add_mins = int(mins_match.group(1)) if mins_match else 0
        add_hours = int(hours_match.group(1)) if hours_match else 0

        total_mins = m + add_mins
        new_h = h + add_hours + total_mins // 60
        new_m = total_mins % 60
        if new_h >= 24:
            new_h -= 24

        if add_hours and not add_mins:
            return (f"Start: {h}:{m:02d}.\n"
                    f"Add {add_hours} hour{'s' if add_hours > 1 else ''}: "
                    f"{h}:{m:02d} → {new_h}:{new_m:02d}.\n"
                    f"Answer: {answer}.")
        elif add_mins and not add_hours:
            if total_mins < 60:
                return (f"Start: {h}:{m:02d}.\n"
                        f"Add {add_mins} minutes: {m} + {add_mins} = {total_mins} minutes.\n"
                        f"Time: {new_h}:{new_m:02d}.\n"
                        f"Answer: {answer}.")
            else:
                extra_h = total_mins // 60
                leftover = total_mins % 60
                return (f"Start: {h}:{m:02d}.\n"
                        f"Add {add_mins} minutes: {m} + {add_mins} = {total_mins} minutes.\n"
                        f"{total_mins} minutes = {extra_h} hour{'s' if extra_h > 1 else ''} "
                        f"and {leftover} minutes.\n"
                        f"{h} + {extra_h} = {h + extra_h} hours, {leftover} minutes → {new_h}:{new_m:02d}.\n"
                        f"Answer: {answer}.")

    return None


def rewrite_counting(q):
    """Rewrite counting/observation questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    nums = extract_numbers(stem)
    answer_num = extract_numbers(answer)

    if not answer_num:
        return None

    ans = answer_num[0]

    # Multiple groups being counted and added
    if len(nums) >= 2:
        if sum(nums) == ans:
            groups = ' + '.join(str(n) for n in nums)
            return (f"Count each group and add:\n"
                    f"{groups} = {ans}.\n"
                    f"Answer: {answer}.")

        # Try finding pairs that add/subtract to answer
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == ans:
                    return (f"{nums[i]} + {nums[j]} = {ans}.\n"
                            f"Answer: {answer}.")
                if abs(nums[i] - nums[j]) == ans:
                    big, small = max(nums[i], nums[j]), min(nums[i], nums[j])
                    return (f"{big} − {small} = {ans}.\n"
                            f"Answer: {answer}.")

    return None


def rewrite_comparison(q):
    """Rewrite comparison/ordering questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    # Transitive comparison: A > B > C
    names = re.findall(r'\b([A-Z][a-z]+)\b', stem)

    if ('taller' in s_lower or 'shorter' in s_lower or
        'heavier' in s_lower or 'lighter' in s_lower or
        'older' in s_lower or 'younger' in s_lower):

        if names:
            return (f"Line up from the clues:\n"
                    f"From the given information, {answer} is the answer.\n"
                    f"Answer: {answer}.")

    # How many more/fewer
    if 'how many more' in s_lower or 'how many fewer' in s_lower:
        nums = extract_numbers(stem)
        answer_num = extract_numbers(answer)
        if len(nums) >= 2 and answer_num:
            big, small = max(nums[0], nums[1]), min(nums[0], nums[1])
            diff = big - small
            return (f"Difference = larger − smaller.\n"
                    f"= {big} − {small} = {diff}.\n"
                    f"Answer: {answer}.")

    return None


def rewrite_shapes(q):
    """Rewrite shape identification/property questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    shape_props = {
        'triangle': {'sides': 3, 'corners': 3},
        'square': {'sides': 4, 'corners': 4},
        'rectangle': {'sides': 4, 'corners': 4},
        'pentagon': {'sides': 5, 'corners': 5},
        'hexagon': {'sides': 6, 'corners': 6},
        'circle': {'sides': 0, 'corners': 0},
    }

    if 'how many sides' in s_lower or 'how many corners' in s_lower:
        for shape, props in shape_props.items():
            if shape in s_lower:
                prop = 'sides' if 'sides' in s_lower else 'corners'
                val = props[prop]
                return (f"A {shape} has {val} {prop}.\n"
                        f"Answer: {answer}.")

    if 'which shape has' in s_lower:
        nums = extract_numbers(stem)
        if nums:
            n = nums[0]
            prop = 'sides' if 'side' in s_lower else 'corners'
            for shape, props in shape_props.items():
                if props.get(prop) == n:
                    return (f"Count the {prop} of each shape:\n"
                            f"Triangle = 3, Square = 4, Pentagon = 5, Hexagon = 6.\n"
                            f"The shape with {n} {prop} is a {shape}.\n"
                            f"Answer: {answer}.")

    return None


def rewrite_fractions(q):
    """Rewrite fraction questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    # Extract fractions like 1/2, 3/4
    fracs = re.findall(r'(\d+)\s*/\s*(\d+)', stem)

    if len(fracs) >= 2:
        n1, d1 = int(fracs[0][0]), int(fracs[0][1])
        n2, d2 = int(fracs[1][0]), int(fracs[1][1])

        if 'add' in s_lower or '+' in stem or 'sum' in s_lower:
            if d1 == d2:
                result_n = n1 + n2
                return (f"Same denominator, so add numerators:\n"
                        f"{n1}/{d1} + {n2}/{d2} = {result_n}/{d1}.\n"
                        f"Answer: {answer}.")
            else:
                lcm = d1 * d2 // gcd(d1, d2)
                new_n1 = n1 * (lcm // d1)
                new_n2 = n2 * (lcm // d2)
                result_n = new_n1 + new_n2
                return (f"Find common denominator: LCM of {d1} and {d2} = {lcm}.\n"
                        f"{n1}/{d1} = {new_n1}/{lcm}, {n2}/{d2} = {new_n2}/{lcm}.\n"
                        f"{new_n1}/{lcm} + {new_n2}/{lcm} = {result_n}/{lcm}.\n"
                        f"Answer: {answer}.")

        if 'subtract' in s_lower or '−' in stem or '-' in stem:
            if d1 == d2:
                result_n = n1 - n2
                return (f"Same denominator, so subtract numerators:\n"
                        f"{n1}/{d1} − {n2}/{d2} = {result_n}/{d1}.\n"
                        f"Answer: {answer}.")

    return None


def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def rewrite_number_before_after(q):
    """Rewrite 'what comes before/after' number questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    nums = extract_numbers(stem)
    if not nums:
        return None

    n = nums[-1]  # Usually the last number mentioned

    if 'just after' in s_lower or 'comes after' in s_lower:
        return (f"The number just after {n} is {n} + 1 = {n + 1}.\n"
                f"Answer: {answer}.")

    if 'just before' in s_lower or 'comes before' in s_lower:
        return (f"The number just before {n} is {n} − 1 = {n - 1}.\n"
                f"Answer: {answer}.")

    return None


def rewrite_logic(q):
    """Rewrite logic and ordering questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    # Transitive ordering: "A is taller than B. B is taller than C. Who is tallest?"
    comparisons = re.findall(r'(\w+)\s+is\s+(?:taller|shorter|heavier|lighter|older|younger|bigger|smaller|faster|slower)\s+than\s+(\w+)', stem, re.I)

    if comparisons:
        chain = []
        for a, b in comparisons:
            if a not in chain:
                chain.append(a)
            if b not in chain:
                idx = chain.index(a) + 1
                chain.insert(idx, b)

        if chain:
            order_str = ' > '.join(chain)
            return (f"From the clues, order them:\n"
                    f"{order_str}.\n"
                    f"Answer: {answer}.")

    return None


def rewrite_number_machine(q):
    """Rewrite number machine / function rule questions."""
    stem = q['s']
    answer = q['c'][q['a']]

    # Pattern: "When X goes in with rule '+Y'"
    m = re.search(r'[Ww]hen\s+(\d+)\s+goes\s+in\s+with\s+rule\s+[\'"]?([+\-×÷*/]\s*\d+)', stem)
    if m:
        input_val = int(m.group(1))
        rule = m.group(2).strip()

        op = rule[0]
        operand = int(re.search(r'\d+', rule).group())

        if op in ['+']:
            result = input_val + operand
            return (f"Apply the rule: {input_val} + {operand} = {result}.\n"
                    f"Answer: {answer}.")
        elif op in ['-', '−']:
            result = input_val - operand
            return (f"Apply the rule: {input_val} − {operand} = {result}.\n"
                    f"Answer: {answer}.")
        elif op in ['×', '*']:
            result = input_val * operand
            return (f"Apply the rule: {input_val} × {operand} = {result}.\n"
                    f"Answer: {answer}.")
        elif op in ['÷', '/']:
            result = input_val // operand
            return (f"Apply the rule: {input_val} ÷ {operand} = {result}.\n"
                    f"Answer: {answer}.")

    return None


def rewrite_place_value(q):
    """Rewrite place value questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    nums = extract_numbers(stem)

    if 'tens digit' in s_lower or 'tens place' in s_lower:
        if nums:
            n = nums[0]
            tens = (n // 10) % 10
            return (f"In {n}, the tens digit is {tens}.\n"
                    f"Answer: {answer}.")

    if 'ones digit' in s_lower or 'units digit' in s_lower or 'ones place' in s_lower:
        if nums:
            n = nums[0]
            ones = n % 10
            return (f"In {n}, the ones digit is {ones}.\n"
                    f"Answer: {answer}.")

    if 'hundreds digit' in s_lower or 'hundreds place' in s_lower:
        if nums:
            n = nums[0]
            hundreds = (n // 100) % 10
            return (f"In {n}, the hundreds digit is {hundreds}.\n"
                    f"Answer: {answer}.")

    if 'expanded form' in s_lower:
        if nums:
            n = nums[0]
            parts = []
            s_val = str(n)
            for i, d in enumerate(s_val):
                if d != '0':
                    place_val = int(d) * (10 ** (len(s_val) - 1 - i))
                    parts.append(str(place_val))
            expanded = ' + '.join(parts)
            return (f"{n} = {expanded}.\n"
                    f"Answer: {answer}.")

    return None


def rewrite_word_problem(q):
    """General word problem rewriter - tries addition, subtraction, multiplication."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()
    nums = extract_numbers(stem)
    answer_num = extract_numbers(answer)

    if not answer_num or not nums:
        return None

    ans = answer_num[0]

    # Determine operation from keywords
    add_kw = ['more', 'gave', 'added', 'join', 'altogether', 'total', 'both', 'all together', 'in all']
    sub_kw = ['left', 'remain', 'ate', 'lost', 'gave away', 'fewer', 'took', 'less', 'flew away', 'sold']
    mul_kw = ['each', 'every', 'per', 'groups of', 'rows of', 'sets of']
    div_kw = ['equally', 'shared', 'split', 'divided', 'each get']

    # Try to find the right operation
    if len(nums) >= 2:
        # Check subtraction first (more specific)
        if any(kw in s_lower for kw in sub_kw):
            for i in range(len(nums)):
                for j in range(len(nums)):
                    if i != j and nums[i] - nums[j] == ans:
                        return (f"{nums[i]} − {nums[j]} = {ans}.\n"
                                f"Answer: {answer}.")

        # Check multiplication
        if any(kw in s_lower for kw in mul_kw):
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    if nums[i] * nums[j] == ans:
                        return (f"{nums[i]} × {nums[j]} = {ans}.\n"
                                f"Answer: {answer}.")

        # Check division
        if any(kw in s_lower for kw in div_kw):
            for i in range(len(nums)):
                for j in range(len(nums)):
                    if i != j and nums[j] != 0 and nums[i] // nums[j] == ans:
                        return (f"{nums[i]} ÷ {nums[j]} = {ans}.\n"
                                f"Answer: {answer}.")

        # Check addition
        if any(kw in s_lower for kw in add_kw):
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    if nums[i] + nums[j] == ans:
                        return (f"{nums[i]} + {nums[j]} = {ans}.\n"
                                f"Answer: {answer}.")
            # Sum all
            if sum(nums) == ans:
                steps = ' + '.join(str(n) for n in nums)
                return (f"{steps} = {ans}.\n"
                        f"Answer: {answer}.")

        # Brute force: try all operations
        for i in range(len(nums)):
            for j in range(len(nums)):
                if i == j:
                    continue
                if nums[i] + nums[j] == ans:
                    return (f"{nums[i]} + {nums[j]} = {ans}.\n"
                            f"Answer: {answer}.")
                if nums[i] - nums[j] == ans:
                    return (f"{nums[i]} − {nums[j]} = {ans}.\n"
                            f"Answer: {answer}.")
                if nums[i] * nums[j] == ans:
                    return (f"{nums[i]} × {nums[j]} = {ans}.\n"
                            f"Answer: {answer}.")
                if nums[j] != 0 and nums[i] / nums[j] == ans:
                    return (f"{nums[i]} ÷ {nums[j]} = {ans}.\n"
                            f"Answer: {answer}.")

    return None


def rewrite_symmetry(q):
    """Rewrite symmetry questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    if 'line' in s_lower and 'symmetry' in s_lower:
        shape_lines = {
            'square': 4, 'rectangle': 2, 'circle': 'infinite',
            'equilateral triangle': 3, 'isosceles triangle': 1,
            'regular pentagon': 5, 'regular hexagon': 6,
        }
        for shape, lines in shape_lines.items():
            if shape in s_lower:
                return (f"A {shape} has {lines} line{'s' if lines != 1 else ''} of symmetry.\n"
                        f"Answer: {answer}.")

    return None


def rewrite_spatial(q):
    """Rewrite spatial reasoning questions."""
    stem = q['s']
    answer = q['c'][q['a']]

    # These are often too context-dependent for template rewriting
    # But we can at least state the answer clearly
    return None


def rewrite_bead_pattern(q):
    """Rewrite repeating bead/color pattern questions."""
    stem = q['s']
    answer = q['c'][q['a']]

    # Pattern: "Red, Blue, Red, Blue, ___"
    colors = re.findall(r'(Red|Blue|Green|Yellow|White|Black|Orange|Purple|Pink)', stem, re.I)
    if len(colors) >= 4:
        # Find repeat length
        for rep_len in range(1, len(colors) // 2 + 1):
            pattern = colors[:rep_len]
            if all(colors[i] == pattern[i % rep_len] for i in range(len(colors))):
                next_color = pattern[len(colors) % rep_len]
                pat_str = ', '.join(pattern)
                return (f"The pattern repeats: {pat_str}.\n"
                        f"Position {len(colors) + 1} in the cycle → {next_color}.\n"
                        f"Answer: {answer}.")

    return None


def rewrite_angle_sum(q):
    """Rewrite angle sum questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    angle_sums = {
        'triangle': 180, 'quadrilateral': 360, 'pentagon': 540,
        'hexagon': 720, 'straight line': 180, 'right angle': 90,
    }

    for shape, total in angle_sums.items():
        if shape in s_lower and ('angle' in s_lower or 'sum' in s_lower):
            return (f"The sum of angles in a {shape} is always {total}°.\n"
                    f"Answer: {answer}.")

    # Missing angle: "Two angles of a triangle are 40° and 60°. Find the third angle."
    angles = re.findall(r'(\d+)\s*°', stem)
    if angles and 'triangle' in s_lower:
        known = [int(a) for a in angles]
        missing = 180 - sum(known)
        steps = ' + '.join(f'{a}°' for a in known)
        return (f"Sum of angles in a triangle = 180°.\n"
                f"Known angles: {steps} = {sum(known)}°.\n"
                f"Missing angle = 180° − {sum(known)}° = {missing}°.\n"
                f"Answer: {answer}.")

    if angles and 'quadrilateral' in s_lower:
        known = [int(a) for a in angles]
        missing = 360 - sum(known)
        steps = ' + '.join(f'{a}°' for a in known)
        return (f"Sum of angles in a quadrilateral = 360°.\n"
                f"Known angles: {steps} = {sum(known)}°.\n"
                f"Missing angle = 360° − {sum(known)}° = {missing}°.\n"
                f"Answer: {answer}.")

    return None


def rewrite_which_is_longer(q):
    """Rewrite 'which is longer/shorter/heavier/lighter' comparison questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    # Extract measurements
    measurements = re.findall(r'(\d+)\s*(cm|mm|mL|ml|km|kg|m|g|l|L)', stem)
    if len(measurements) >= 2:
        v1, u1 = int(measurements[0][0]), measurements[0][1]
        v2, u2 = int(measurements[1][0]), measurements[1][1]

        if u1 == u2:
            if v1 > v2:
                return (f"Compare: {v1} {u1} vs {v2} {u2}.\n"
                        f"{v1} > {v2}, so the first is longer/heavier.\n"
                        f"Answer: {answer}.")
            elif v2 > v1:
                return (f"Compare: {v1} {u1} vs {v2} {u2}.\n"
                        f"{v2} > {v1}, so the second is longer/heavier.\n"
                        f"Answer: {answer}.")
            else:
                return (f"Compare: {v1} {u1} vs {v2} {u2}.\n"
                        f"Both are equal ({v1} = {v2}).\n"
                        f"Answer: {answer}.")

    return None


def rewrite_data_handling(q):
    """Rewrite data handling / chart / graph reading questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    nums = extract_numbers(stem)
    answer_num = extract_numbers(answer)

    if answer_num and nums:
        ans = answer_num[0]
        # Try common data operations
        if len(nums) >= 2:
            # Total
            if sum(nums) == ans:
                steps = ' + '.join(str(n) for n in nums)
                return (f"Add all values: {steps} = {ans}.\n"
                        f"Answer: {answer}.")
            # Difference (most/least)
            if max(nums) - min(nums) == ans:
                return (f"Largest = {max(nums)}, Smallest = {min(nums)}.\n"
                        f"Difference = {max(nums)} − {min(nums)} = {ans}.\n"
                        f"Answer: {answer}.")
            # Average
            if len(nums) >= 3 and sum(nums) // len(nums) == ans:
                total = sum(nums)
                return (f"Total = {total}, Number of items = {len(nums)}.\n"
                        f"Average = {total} ÷ {len(nums)} = {ans}.\n"
                        f"Answer: {answer}.")

    return None


def rewrite_odd_even(q):
    """Rewrite odd/even number questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    nums = extract_numbers(stem)

    if 'odd' in s_lower or 'even' in s_lower:
        if nums:
            n = nums[0]
            if n % 2 == 0:
                return (f"{n} ÷ 2 = {n // 2} with no remainder.\n"
                        f"So {n} is even.\n"
                        f"Answer: {answer}.")
            else:
                return (f"{n} ÷ 2 = {n // 2} remainder 1.\n"
                        f"So {n} is odd.\n"
                        f"Answer: {answer}.")

    return None


def rewrite_missing_number(q):
    """Rewrite missing number / fill-in-the-blank arithmetic."""
    stem = q['s']
    answer = q['c'][q['a']]

    # "? + 5 = 12" or "8 + ? = 15" or "15 - ? = 9"
    m = re.search(r'\?\s*([+\-×÷*/])\s*(\d+)\s*=\s*(\d+)', stem)
    if m:
        op, b, result = m.group(1), int(m.group(2)), int(m.group(3))
        if op == '+':
            missing = result - b
            return (f"? + {b} = {result}.\n"
                    f"? = {result} − {b} = {missing}.\n"
                    f"Answer: {answer}.")
        elif op in ['-', '−']:
            missing = result + b
            return (f"? − {b} = {result}.\n"
                    f"? = {result} + {b} = {missing}.\n"
                    f"Answer: {answer}.")

    m = re.search(r'(\d+)\s*([+\-×÷*/])\s*\?\s*=\s*(\d+)', stem)
    if m:
        a, op, result = int(m.group(1)), m.group(2), int(m.group(3))
        if op == '+':
            missing = result - a
            return (f"{a} + ? = {result}.\n"
                    f"? = {result} − {a} = {missing}.\n"
                    f"Answer: {answer}.")
        elif op in ['-', '−']:
            missing = a - result
            return (f"{a} − ? = {result}.\n"
                    f"? = {a} − {result} = {missing}.\n"
                    f"Answer: {answer}.")

    return None


def rewrite_race_order(q):
    """Rewrite 'in a race, order is X,Y,Z — who came Nth?' questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    # "In a race, the order is: A, B, C, D. Who came second?"
    m = re.search(r'order\s+is[:\s]+([A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+)+)', stem)
    if m:
        names = [n.strip() for n in m.group(1).split(',')]
        ordinals = {'first': 0, 'second': 1, 'third': 2, 'fourth': 3, 'fifth': 4,
                    'last': -1, '1st': 0, '2nd': 1, '3rd': 2, '4th': 3, '5th': 4}

        for word, idx in ordinals.items():
            if word in s_lower:
                order_str = ', '.join(f'{i+1}. {n}' for i, n in enumerate(names))
                return (f"The order is: {order_str}.\n"
                        f"Position {word}: {answer}.\n"
                        f"Answer: {answer}.")

    return None


def rewrite_stated_answer(q):
    """Rewrite questions where answer is directly stated in the stem."""
    stem = q['s']
    answer = q['c'][q['a']]

    # "Zara sees 9 coins in a bowl. How many coins are there?"
    answer_nums = extract_numbers(answer)
    if answer_nums:
        ans = answer_nums[0]
        stem_nums = extract_numbers(stem)
        if ans in stem_nums:
            return (f"The answer is directly stated: {ans}.\n"
                    f"Answer: {answer}.")

    return None


def rewrite_transitive_logic(q):
    """Rewrite transitive comparison logic questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    # Real-world knowledge questions: "Which is the shortest: fish, elephant, ant, cat?"
    # These rely on general knowledge, not math
    animals_by_size = ['ant', 'butterfly', 'bee', 'snail', 'frog', 'fish', 'cat', 'dog',
                       'fox', 'deer', 'horse', 'cow', 'bear', 'giraffe', 'elephant', 'whale']
    fruits_by_size = ['grape', 'cherry', 'strawberry', 'plum', 'apple', 'orange', 'mango',
                      'coconut', 'pineapple', 'watermelon', 'pumpkin']

    if 'shortest' in s_lower or 'smallest' in s_lower or 'lightest' in s_lower:
        return (f"Compare the sizes using common knowledge.\n"
                f"The smallest/shortest is {answer}.\n"
                f"Answer: {answer}.")

    if 'tallest' in s_lower or 'biggest' in s_lower or 'largest' in s_lower or 'heaviest' in s_lower:
        return (f"Compare the sizes using common knowledge.\n"
                f"The biggest/tallest is {answer}.\n"
                f"Answer: {answer}.")

    # Transitive: "A is bigger than B. B is bigger than C."
    comparisons = re.findall(
        r'(\w+)\s+(?:ball|box|bag|block|toy|)?\s*is\s+(?:\w+er|more \w+)\s+than\s+(?:the\s+)?(\w+)',
        stem, re.I)

    if comparisons:
        # Build ordering chain
        order = []
        for bigger, smaller in comparisons:
            bigger = bigger.strip().title()
            smaller = smaller.strip().title()
            if bigger not in order:
                order.append(bigger)
            if smaller not in order:
                # Insert after bigger
                idx = order.index(bigger) + 1
                order.insert(idx, smaller)

        if order:
            chain = ' > '.join(order)
            return (f"From the clues: {chain}.\n"
                    f"Answer: {answer}.")

    return None


def rewrite_spatial_simple(q):
    """Rewrite simple spatial questions where answer is in the stem."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    # "The flag is in the left hand. Which hand?" → Left
    # "The bird is to the right of the tree. Where is the bird?" → Right
    answer_lower = answer.lower().strip()

    # Check if the answer text appears in the stem
    if answer_lower in s_lower:
        return (f"From the question: the answer is stated as {answer}.\n"
                f"Answer: {answer}.")

    # Mirror/facing questions
    if 'faces you' in s_lower and ('left' in s_lower or 'right' in s_lower):
        return (f"When someone faces you, their left is your right and vice versa.\n"
                f"Answer: {answer}.")

    return None


def rewrite_3d_shapes(q):
    """Rewrite 3D shape identification questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()
    a_lower = answer.lower().strip()

    shape_map = {
        'sphere': 'A sphere is round like a ball.',
        'cube': 'A cube has 6 equal square faces.',
        'cylinder': 'A cylinder has 2 circular faces and a curved surface.',
        'cone': 'A cone has 1 circular base and comes to a point.',
        'cuboid': 'A cuboid has 6 rectangular faces.',
        'circle': 'A circle is a round flat shape with no corners.',
        'triangle': 'A triangle has 3 sides and 3 corners.',
        'square': 'A square has 4 equal sides and 4 right angles.',
        'rectangle': 'A rectangle has 4 sides with opposite sides equal.',
    }

    if a_lower in shape_map:
        return (f"{shape_map[a_lower]}\n"
                f"Answer: {answer}.")

    # "How many faces does a cube have?" → 6
    faces = {'cube': 6, 'cuboid': 6, 'cylinder': 3, 'cone': 2,
             'sphere': 0, 'pyramid': 5, 'triangular prism': 5}
    edges = {'cube': 12, 'cuboid': 12, 'cylinder': 2, 'cone': 1,
             'sphere': 0, 'pyramid': 8, 'triangular prism': 9}
    vertices = {'cube': 8, 'cuboid': 8, 'cylinder': 0, 'cone': 1,
                'sphere': 0, 'pyramid': 5, 'triangular prism': 6}

    for shape in faces:
        if shape in s_lower:
            if 'face' in s_lower:
                return (f"A {shape} has {faces[shape]} face(s).\n"
                        f"Answer: {answer}.")
            if 'edge' in s_lower:
                return (f"A {shape} has {edges[shape]} edge(s).\n"
                        f"Answer: {answer}.")
            if 'vert' in s_lower or 'corner' in s_lower:
                return (f"A {shape} has {vertices[shape]} vertex/vertices.\n"
                        f"Answer: {answer}.")

    return None


def rewrite_counting_groups(q):
    """Rewrite counting by groups (legs, wheels, etc.)."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    # "How many legs do 3 dogs have?" → 3 × 4 = 12
    legs_map = {'dog': 4, 'cat': 4, 'horse': 4, 'cow': 4, 'elephant': 4,
                'bird': 2, 'chicken': 2, 'duck': 2, 'spider': 8, 'insect': 6,
                'ant': 6, 'beetle': 6, 'octopus': 8}
    wheels_map = {'bicycle': 2, 'car': 4, 'tricycle': 3, 'truck': 4,
                  'motorcycle': 2, 'bus': 4, 'auto': 3, 'scooter': 2}

    answer_num = extract_numbers(answer)
    if not answer_num:
        return None

    ans = answer_num[0]

    # Check legs
    if 'leg' in s_lower:
        for animal, legs in legs_map.items():
            m = re.search(rf'(\d+)\s*{animal}s?', s_lower)
            if m:
                count = int(m.group(1))
                if count * legs == ans:
                    return (f"Each {animal} has {legs} legs.\n"
                            f"{count} {animal}s × {legs} legs = {ans} legs.\n"
                            f"Answer: {answer}.")

    # Check wheels
    if 'wheel' in s_lower:
        total = 0
        parts = []
        for vehicle, wheels in wheels_map.items():
            m = re.search(rf'(\d+)\s*{vehicle}s?', s_lower)
            if m:
                count = int(m.group(1))
                total += count * wheels
                parts.append(f"{count} {vehicle}{'s' if count > 1 else ''} × {wheels} = {count * wheels}")

        if total == ans and parts:
            steps = ', '.join(parts)
            return (f"Count wheels: {steps}.\n"
                    f"Total = {ans} wheels.\n"
                    f"Answer: {answer}.")

    return None


def rewrite_half_double(q):
    """Rewrite 'half of X' or 'double of X' questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()
    nums = extract_numbers(stem)
    answer_num = extract_numbers(answer)

    if not answer_num or not nums:
        return None

    ans = answer_num[0]

    if 'half' in s_lower:
        for n in nums:
            if n // 2 == ans or n / 2 == ans:
                return (f"Half of {n} = {n} ÷ 2 = {ans}.\n"
                        f"Answer: {answer}.")

    if 'double' in s_lower or 'twice' in s_lower:
        for n in nums:
            if n * 2 == ans:
                return (f"Double of {n} = {n} × 2 = {ans}.\n"
                        f"Answer: {answer}.")

    if 'third' in s_lower or 'one-third' in s_lower:
        for n in nums:
            if n // 3 == ans:
                return (f"One-third of {n} = {n} ÷ 3 = {ans}.\n"
                        f"Answer: {answer}.")

    if 'quarter' in s_lower or 'one-fourth' in s_lower:
        for n in nums:
            if n // 4 == ans:
                return (f"One-quarter of {n} = {n} ÷ 4 = {ans}.\n"
                        f"Answer: {answer}.")

    return None


def rewrite_data_comparison(q):
    """Rewrite 'which has the most/least' data questions."""
    stem = q['s']
    answer = q['c'][q['a']]
    s_lower = stem.lower()

    # "apples: 2, bananas: 6, oranges: 5, mangoes: 9. Which has the most?"
    pairs = re.findall(r'(\w+)[\s:]+(\d+)', stem)
    if len(pairs) >= 3:
        items = [(name, int(val)) for name, val in pairs if not name.lower() in
                 ['are', 'is', 'has', 'have', 'the', 'in', 'a', 'an', 'of', 'and',
                  'how', 'many', 'which', 'what', 'there', 'total']]

        if items:
            if 'most' in s_lower or 'largest' in s_lower or 'highest' in s_lower:
                items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
                listing = ', '.join(f'{n}: {v}' for n, v in items_sorted)
                return (f"Compare: {listing}.\n"
                        f"The most is {items_sorted[0][0]} with {items_sorted[0][1]}.\n"
                        f"Answer: {answer}.")

            if 'least' in s_lower or 'fewest' in s_lower or 'smallest' in s_lower or 'lowest' in s_lower:
                items_sorted = sorted(items, key=lambda x: x[1])
                listing = ', '.join(f'{n}: {v}' for n, v in items_sorted)
                return (f"Compare: {listing}.\n"
                        f"The least is {items_sorted[0][0]} with {items_sorted[0][1]}.\n"
                        f"Answer: {answer}.")

    return None


def rewrite_general_fallback(q):
    """Last resort: generate a minimal but specific explanation using the answer."""
    stem = q['s']
    answer = q['c'][q['a']]
    choices = q['c']
    correct_idx = q['a']

    # For any question with numbers, try to show WHY the answer is correct
    nums_in_stem = extract_numbers(stem)
    nums_in_answer = extract_numbers(answer)

    if nums_in_answer and nums_in_stem:
        ans = nums_in_answer[0]
        # Check all possible two-number operations
        for i in range(len(nums_in_stem)):
            for j in range(len(nums_in_stem)):
                if i == j:
                    continue
                a, b = nums_in_stem[i], nums_in_stem[j]
                if a + b == ans:
                    return f"{a} + {b} = {ans}.\nAnswer: {answer}."
                if a - b == ans:
                    return f"{a} − {b} = {ans}.\nAnswer: {answer}."
                if a * b == ans:
                    return f"{a} × {b} = {ans}.\nAnswer: {answer}."
                if b != 0 and a / b == ans:
                    return f"{a} ÷ {b} = {ans}.\nAnswer: {answer}."
                if b != 0 and a % b == ans:
                    return f"{a} ÷ {b} = {a // b} remainder {ans}.\nAnswer: {answer}."

    return None


def rewrite_question(q):
    """Main dispatcher: try all rewriters, return best result."""
    stem = q['s']
    s_lower = stem.lower()
    answer = q['c'][q['a']]

    # Already has a good explanation? Check quality
    existing = q.get('w', '')
    existing_lines = [l.strip() for l in existing.split('\n')
                      if l.strip() and not l.strip().startswith('Analysis:') and not l.strip().startswith('Answer:')]
    math_in_existing = sum(1 for l in existing_lines
                           if any(op in l for op in ['=', '×', '÷', '→']) and any(c.isdigit() for c in l))

    # If existing explanation already has 3+ math lines, keep it
    if math_in_existing >= 3 and len(existing_lines) >= 4:
        return None  # Keep existing

    # Try specific rewriters in order
    result = None

    # 1. Unit conversion
    if 'convert' in s_lower:
        result = rewrite_conversion(q)

    # 2. Perimeter
    if not result and 'perimeter' in s_lower:
        result = rewrite_perimeter(q)

    # 3. Area
    if not result and 'area' in s_lower:
        result = rewrite_area(q)

    # 4. Number before/after
    if not result and ('just before' in s_lower or 'just after' in s_lower or
                        'comes before' in s_lower or 'comes after' in s_lower):
        result = rewrite_number_before_after(q)

    # 5. Pattern/sequence
    if not result and ('?' in stem and ',' in stem):
        result = rewrite_pattern(q)

    # 6. Bead/color pattern
    if not result and any(c in stem.lower() for c in ['red', 'blue', 'green', 'bead', 'colour', 'color']):
        result = rewrite_bead_pattern(q)

    # 7. Number machine
    if not result and ('machine' in s_lower or 'rule' in s_lower):
        result = rewrite_number_machine(q)

    # 8. Place value
    if not result and ('digit' in s_lower or 'place value' in s_lower or 'expanded form' in s_lower):
        result = rewrite_place_value(q)

    # 9. Symmetry
    if not result and 'symmetry' in s_lower:
        result = rewrite_symmetry(q)

    # 10. Money
    if not result and ('₹' in stem or '$' in stem or 'cost' in s_lower or 'price' in s_lower or
                        'change' in s_lower or 'pay' in s_lower or 'buy' in s_lower):
        result = rewrite_money(q)

    # 11. Time
    if not result and (':' in stem and ('time' in s_lower or 'minute' in s_lower or 'hour' in s_lower)):
        result = rewrite_time(q)

    # 12. Shape properties
    if not result and ('sides' in s_lower or 'corners' in s_lower or 'which shape' in s_lower):
        result = rewrite_shapes(q)

    # 13. Fractions
    if not result and '/' in stem and re.search(r'\d+\s*/\s*\d+', stem):
        result = rewrite_fractions(q)

    # 14. Logic/ordering
    if not result and ('taller' in s_lower or 'shorter' in s_lower or 'heavier' in s_lower or
                        'lighter' in s_lower or 'fastest' in s_lower or 'slowest' in s_lower):
        result = rewrite_logic(q)

    # 15. Comparison (how many more/fewer)
    if not result and ('how many more' in s_lower or 'how many fewer' in s_lower or 'difference' in s_lower):
        result = rewrite_comparison(q)

    # 16. Angle sums
    if not result and ('angle' in s_lower):
        result = rewrite_angle_sum(q)

    # 17. Which is longer/shorter/heavier (measurement comparison)
    if not result and ('which is' in s_lower and re.search(r'\d+\s*(cm|mm|m|km|g|kg)', stem)):
        result = rewrite_which_is_longer(q)

    # 18. Odd/even
    if not result and ('odd' in s_lower or 'even' in s_lower):
        result = rewrite_odd_even(q)

    # 19. Missing number in equation
    if not result and '?' in stem and any(op in stem for op in ['+', '-', '×', '÷', '−']):
        result = rewrite_missing_number(q)

    # 20. Data handling
    if not result and ('data' in q.get('t', '') or 'chart' in s_lower or 'graph' in s_lower or 'tally' in s_lower):
        result = rewrite_data_handling(q)

    # 21. Explicit arithmetic in stem
    if not result:
        # "5 + 3 = ?" or "12 - 7 = ?"
        m = re.search(r'(\d+)\s*([+\-×÷*/])\s*(\d+)\s*=\s*\?', stem)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            op_map = {'+': ('+', a + b), '-': ('−', a - b), '−': ('−', a - b),
                      '×': ('×', a * b), '*': ('×', a * b),
                      '÷': ('÷', a // b if b else 0), '/': ('÷', a // b if b else 0)}
            if op in op_map:
                sym, res = op_map[op]
                result = f"{a} {sym} {b} = {res}.\nAnswer: {answer}."

    # 22. Spatial reasoning (simple)
    if not result and ('spatial' in q.get('t', '') or 'position' in q.get('t', '')):
        result = rewrite_spatial_simple(q)

    # 23. 3D shapes
    if not result and ('shape' in s_lower or 'sphere' in s_lower or 'cube' in s_lower or
                        'cylinder' in s_lower or 'cone' in s_lower or 'face' in s_lower or
                        'no corner' in s_lower or 'ball' in s_lower):
        result = rewrite_3d_shapes(q)

    # 24. Counting by groups (legs, wheels)
    if not result and ('leg' in s_lower or 'wheel' in s_lower):
        result = rewrite_counting_groups(q)

    # 25. Half/double/third
    if not result and ('half' in s_lower or 'double' in s_lower or 'twice' in s_lower or
                        'third' in s_lower or 'quarter' in s_lower):
        result = rewrite_half_double(q)

    # 26. Data comparison (most/least)
    if not result and ('most' in s_lower or 'least' in s_lower or 'fewest' in s_lower):
        result = rewrite_data_comparison(q)

    # 27. Race/order questions
    if not result and ('order' in s_lower or 'race' in s_lower or 'came' in s_lower):
        result = rewrite_race_order(q)

    # 23. Transitive logic (bigger/smaller comparisons, general knowledge)
    if not result and ('bigger' in s_lower or 'smaller' in s_lower or 'tallest' in s_lower or
                        'shortest' in s_lower or 'largest' in s_lower or 'heaviest' in s_lower or
                        'lightest' in s_lower or 'longest' in s_lower):
        result = rewrite_transitive_logic(q)

    # 24. General word problem (fallback)
    if not result:
        result = rewrite_word_problem(q)

    # 25. Answer stated directly in stem
    if not result:
        result = rewrite_stated_answer(q)

    # 26. General fallback — try all arithmetic combos
    if not result:
        result = rewrite_general_fallback(q)

    return result


def main():
    dry_run = '--dry-run' in sys.argv
    sample_n = None
    for i, arg in enumerate(sys.argv):
        if arg == '--sample' and i + 1 < len(sys.argv):
            sample_n = int(sys.argv[i + 1])

    with open(QUESTIONS_PATH) as f:
        data = json.load(f)

    print(f"Loaded {len(data)} questions")

    rewritten = 0
    kept = 0
    failed = 0

    for i, q in enumerate(data):
        if sample_n and i >= sample_n:
            break

        new_why = rewrite_question(q)

        if new_why:
            if dry_run:
                if rewritten < 20:
                    print(f"\n{'='*60}")
                    print(f"Q: {q['s'][:100]}")
                    print(f"Choices: {q['c']}")
                    print(f"OLD: {q['w']}")
                    print(f"NEW: {new_why}")
            else:
                data[i]['w'] = new_why
            rewritten += 1
        else:
            kept += 1
            if dry_run and failed < 5 and not new_why:
                existing = q.get('w', '')
                lines = [l.strip() for l in existing.split('\n')
                         if l.strip() and not l.strip().startswith('Analysis:') and not l.strip().startswith('Answer:')]
                math_lines = sum(1 for l in lines
                                 if any(op in l for op in ['=', '×', '÷', '→']) and any(c.isdigit() for c in l))
                if math_lines < 3:
                    failed += 1
                    # Not logging kept ones in dry run for cleanliness

    print(f"\nResults: {rewritten} rewritten, {kept} kept")

    if not dry_run and not sample_n:
        with open(QUESTIONS_PATH, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=None, separators=(',', ':'))
        print(f"Saved to {QUESTIONS_PATH}")


if __name__ == '__main__':
    main()
