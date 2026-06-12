#!/usr/bin/env python3
"""
Kiwimath Grade 3-6 Content QA Audit Script v2
Fixes false positives from v1: handles multi-op expressions, fractions, remainders properly.
"""

import json
import os
import re
import sys
from fractions import Fraction
from pathlib import Path

BASE = "/sessions/optimistic-laughing-franklin/mnt/Downloads/kiwimath/content-v2"

# All files to check
FILES_TO_CHECK = []

# Topic files (1-8)
for i in range(1, 9):
    topic_dirs = [d for d in Path(BASE).iterdir() if d.is_dir() and d.name.startswith(f"topic-{i}")]
    for td in topic_dirs:
        for f in td.glob("*.json"):
            FILES_TO_CHECK.append(str(f))

# Curriculum files grade 3-6
for curriculum in ["ncert-curriculum", "icse-curriculum", "igcse-curriculum"]:
    for grade in range(3, 7):
        grade_dir = Path(BASE) / curriculum / f"grade{grade}"
        if grade_dir.exists():
            for f in grade_dir.glob("*.json"):
                FILES_TO_CHECK.append(str(f))

# Results
critical_math_errors = []
duplicate_choices = []
grammar_issues = []
visual_mismatches = []
anomalies = []

def parse_number(s):
    """Parse a number string, handling commas."""
    s = s.replace(',', '').strip()
    try:
        return float(s)
    except:
        return None

def compute_expression(expr_str):
    """Safely evaluate a math expression string using BODMAS/PEMDAS."""
    # Clean up
    expr = expr_str.strip()
    expr = expr.replace('×', '*').replace('÷', '/').replace('−', '-').replace('–', '-')
    # Replace 'x' between numbers with '*'
    expr = re.sub(r'(\d)\s*x\s*(\d)', r'\1*\2', expr)
    # Remove any non-math characters
    if not re.match(r'^[\d\s\+\-\*\/\.\(\)]+$', expr):
        return None
    try:
        result = eval(expr)
        return result
    except:
        return None

def extract_full_expression(stem):
    """Extract a full arithmetic expression from a stem, including multi-op."""
    # Look for patterns like "What is [expression]?"
    patterns = [
        r'[Ww]hat is\s+([\d]+(?:\s*[\+\-\×\÷\*\/x×÷−–]\s*[\d]+)+)\s*\??',
        r'[Cc]alculate\s*:?\s*([\d]+(?:\s*[\+\-\×\÷\*\/x×÷−–]\s*[\d]+)+)',
        r'[Ff]ind\s*:?\s*([\d]+(?:\s*[\+\-\×\÷\*\/x×÷−–]\s*[\d]+)+)',
        r'[Ss]olve\s*:?\s*([\d]+(?:\s*[\+\-\×\÷\*\/x×÷−–]\s*[\d]+)+)',
        r'[Ww]ork out\s*:?\s*([\d]+(?:\s*[\+\-\×\÷\*\/x×÷−–]\s*[\d]+)+)',
    ]
    for pat in patterns:
        m = re.search(pat, stem)
        if m:
            return m.group(1)
    return None

def extract_decimal_expression(stem):
    """Extract expressions with decimals like '9.3 + 6.9'"""
    patterns = [
        r'[Ww]hat is\s+([\d.]+(?:\s*[\+\-\×\÷\*\/x×÷−–]\s*[\d.]+)+)\s*\??',
        r'[Cc]alculate\s*:?\s*([\d.]+(?:\s*[\+\-\×\÷\*\/x×÷−–]\s*[\d.]+)+)',
        r'[Ff]ind\s*:?\s*([\d.]+(?:\s*[\+\-\×\÷\*\/x×÷−–]\s*[\d.]+)+)',
        r'[Ss]olve\s*:?\s*([\d.]+(?:\s*[\+\-\×\÷\*\/x×÷−–]\s*[\d.]+)+)',
    ]
    for pat in patterns:
        m = re.search(pat, stem)
        if m:
            return m.group(1)
    return None

def is_remainder_question(stem):
    """Check if it's a division with remainder question."""
    return 'remainder' in stem.lower() or 'quotient' in stem.lower()

def is_fraction_of_question(stem):
    """Check if it's a 'fraction of number' question like '1/5 of 25'."""
    return bool(re.search(r'\d+/\d+\s+of\s+\d+', stem))

def is_fraction_arithmetic(stem):
    """Check if it's fraction addition/subtraction/multiplication."""
    return bool(re.search(r'\d+/\d+\s*[\+\-\×\*÷\/]\s*\d+/\d+', stem))

def is_composite_area(stem):
    """Check if it's a composite shape area (two rectangles, rect+triangle, etc)."""
    return ('two rectangles' in stem.lower() or
            'triangle' in stem.lower() and 'rectangle' in stem.lower() or
            'composite' in stem.lower() or
            'total area' in stem.lower())

def is_palindrome_question(stem):
    """Check if it's a reverse-and-add palindrome question."""
    return 'palindrome' in stem.lower() or 'reverse' in stem.lower()

def verify_simple_arithmetic(stem, choices, correct_idx):
    """Verify simple arithmetic: single or multi-op with integers only, no fractions."""
    # Skip special question types
    if is_remainder_question(stem):
        return None
    if is_fraction_of_question(stem):
        return verify_fraction_of(stem, choices, correct_idx)
    if is_fraction_arithmetic(stem):
        return verify_fraction_arithmetic(stem, choices, correct_idx)
    if is_composite_area(stem):
        return verify_composite_area(stem, choices, correct_idx)
    if is_palindrome_question(stem):
        return None  # These are correct format: "444 (palindrome)"

    # Extract expression
    expr = extract_full_expression(stem)
    if not expr:
        expr = extract_decimal_expression(stem)
    if not expr:
        return None

    # Skip if it contains fractions (slashes between digits)
    if re.search(r'\d+/\d+', expr):
        return None

    result = compute_expression(expr)
    if result is None:
        return None

    # Format result
    if isinstance(result, float):
        # Handle floating point precision
        rounded = round(result, 10)
        if abs(rounded - round(rounded)) < 1e-9:
            result_str = str(int(round(rounded)))
        else:
            result_str = f"{rounded:.10g}"
    else:
        result_str = str(result)

    stated = choices[correct_idx]
    stated_norm = normalize_answer(stated)
    result_norm = normalize_answer(result_str)

    # Compare
    if stated_norm != result_norm:
        # Check if floating point issue (e.g., 16.2 vs 16.200000000000003)
        try:
            if abs(float(stated_norm) - float(result_norm)) < 0.001:
                return None  # Floating point rounding, not a real error
        except:
            pass
        return (result_str, stated, stem)

    return None

def verify_fraction_of(stem, choices, correct_idx):
    """Verify 'What is 1/N of X?' questions."""
    m = re.search(r'(\d+)/(\d+)\s+of\s+(\d+)', stem)
    if not m:
        return None
    num, den, whole = int(m.group(1)), int(m.group(2)), int(m.group(3))
    result = Fraction(num, den) * whole
    expected = str(result) if result.denominator != 1 else str(result.numerator)
    stated = choices[correct_idx]
    stated_norm = normalize_answer(stated)
    if stated_norm != normalize_answer(expected):
        return (expected, stated, stem)
    return None

def verify_fraction_arithmetic(stem, choices, correct_idx):
    """Verify fraction addition/subtraction."""
    # Match: a/b + c/d or a/b - c/d or a/b × c/d
    m = re.search(r'(\d+)/(\d+)\s*([\+\-\×\*÷\/])\s*(\d+)/(\d+)', stem)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    op = m.group(3)
    c, d = int(m.group(4)), int(m.group(5))

    f1 = Fraction(a, b)
    f2 = Fraction(c, d)

    if op == '+':
        result = f1 + f2
    elif op == '-' or op == '−' or op == '–':
        result = f1 - f2
    elif op in ('×', '*'):
        result = f1 * f2
    elif op in ('÷', '/'):
        if f2 == 0:
            return None
        result = f1 / f2
    else:
        return None

    # Format result as fraction
    if result.denominator == 1:
        expected = str(result.numerator)
    else:
        expected = f"{result.numerator}/{result.denominator}"

    stated = choices[correct_idx].strip()
    # Normalize stated answer - try to parse as fraction
    stated_frac = None
    m2 = re.match(r'(-?\d+)/(\d+)', stated)
    if m2:
        stated_frac = Fraction(int(m2.group(1)), int(m2.group(2)))
    else:
        try:
            stated_frac = Fraction(stated)
        except:
            pass

    if stated_frac is not None:
        if stated_frac != result:
            return (expected, stated, stem)
    else:
        if normalize_answer(expected) != normalize_answer(stated):
            return (expected, stated, stem)

    return None

def verify_composite_area(stem, choices, correct_idx):
    """Verify composite area questions (two rectangles, rect+triangle)."""
    # Two rectangles: "one is A cm × B cm and the other is C cm × D cm"
    m = re.search(r'(\d+)\s*(?:cm|m)\s*[×x\*]\s*(\d+)\s*(?:cm|m).*?(\d+)\s*(?:cm|m)\s*[×x\*]\s*(\d+)\s*(?:cm|m)', stem)
    if m:
        a, b, c, d = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        total = a * b + c * d
        stated = choices[correct_idx]
        stated_num = normalize_answer(stated)
        if stated_num != str(total):
            return (str(total), stated, stem)
        return None

    # Rectangle + triangle: "rectangle AmxBm + triangle (base Cm, height Dm)"
    m = re.search(r'rectangle\s*(\d+)\s*m?\s*[×x\*]\s*(\d+)\s*m?.*?triangle.*?base\s*(\d+)\s*m?.*?height\s*(\d+)\s*m?', stem)
    if m:
        rl, rw = int(m.group(1)), int(m.group(2))
        tb, th = int(m.group(3)), int(m.group(4))
        total = rl * rw + (tb * th) / 2
        if total == int(total):
            expected = str(int(total))
        else:
            expected = str(total)
        stated = choices[correct_idx]
        stated_num = normalize_answer(stated)
        if stated_num != expected:
            return (expected, stated, stem)

    return None

def verify_place_value(stem, choices, correct_idx):
    """Verify place value questions."""
    m = re.search(r'digit in the (\w+) place (?:of|in) (\d+)', stem)
    if not m:
        return None
    place = m.group(1).lower()
    number = m.group(2)
    places = {'ones': -1, 'units': -1, 'tens': -2, 'hundreds': -3, 'thousands': -4,
              'ten-thousands': -5, 'tenthousands': -5}
    if place in places:
        idx = places[place]
        if abs(idx) <= len(number):
            expected = number[idx]
            stated = choices[correct_idx].strip()
            if expected != stated:
                return (expected, stated, stem)
    return None

def verify_expanded_form(stem, choices, correct_idx):
    """Verify expanded form questions."""
    m = re.search(r'expanded form of (\d+)', stem)
    if not m:
        return None
    number = int(m.group(1))
    if correct_idx >= len(choices):
        return None
    # Check if the correct choice sums to the number
    choice = choices[correct_idx]
    try:
        parts = [int(x.strip()) for x in choice.split('+')]
        total = sum(parts)
        if total != number:
            return (f"Sum should be {number}, got {total}", choice, stem)
    except:
        pass
    return None

def verify_percentage(stem, choices, correct_idx):
    """Verify percentage questions."""
    m = re.search(r'(\d+(?:\.\d+)?)\s*%\s*of\s+([\d,.]+)', stem)
    if not m:
        return None
    pct = float(m.group(1))
    num = float(m.group(2).replace(',', ''))
    result = pct * num / 100
    if result == int(result):
        expected = str(int(result))
    else:
        expected = str(result)
    stated = choices[correct_idx]
    if normalize_answer(expected) != normalize_answer(stated):
        return (expected, stated, stem)
    return None

def verify_square(stem, choices, correct_idx):
    """Verify square/cube questions."""
    m = re.search(r'[Ss]quare of\s+(\d+)', stem)
    if not m:
        m = re.search(r'(\d+)\s*squared', stem)
    if not m:
        m = re.search(r'(\d+)²', stem)
    if m:
        n = int(m.group(1))
        expected = str(n * n)
        stated = choices[correct_idx]
        if normalize_answer(expected) != normalize_answer(stated):
            return (expected, stated, stem)

    m = re.search(r'[Cc]ube of\s+(\d+)', stem)
    if not m:
        m = re.search(r'(\d+)\s*cubed', stem)
    if not m:
        m = re.search(r'(\d+)³', stem)
    if m:
        n = int(m.group(1))
        expected = str(n * n * n)
        stated = choices[correct_idx]
        if normalize_answer(expected) != normalize_answer(stated):
            return (expected, stated, stem)
    return None

def verify_remainder(stem, choices, correct_idx):
    """Verify division with remainder questions."""
    if not is_remainder_question(stem):
        return None
    m = re.search(r'(\d+)\s*[÷/]\s*(\d+)', stem)
    if not m:
        return None
    dividend, divisor = int(m.group(1)), int(m.group(2))
    quotient = dividend // divisor
    remainder = dividend % divisor

    stated = choices[correct_idx]
    # Check format: "Q remainder R"
    m2 = re.search(r'(\d+)\s*(?:remainder|rem|r)\s*(\d+)', stated, re.IGNORECASE)
    if m2:
        stated_q, stated_r = int(m2.group(1)), int(m2.group(2))
        if stated_q != quotient or stated_r != remainder:
            return (f"{quotient} remainder {remainder}", stated, stem)
    return None

def normalize_answer(ans):
    """Normalize answer string for comparison."""
    ans = str(ans).strip()
    if ans.endswith('.0'):
        ans = ans[:-2]
    ans = ans.replace(',', '')
    # Remove units at end
    ans = re.sub(r'\s*(cm²|m²|sq\s*cm|sq\s*m|cm|m|mm|km|kg|g|ml|l|units?|°)\s*$', '', ans)
    return ans.strip()

def verify_math(q):
    """Try to verify math. Returns (expected, actual, stem) if mismatch."""
    stem = q.get('stem', '')
    choices = q.get('choices', [])
    correct_idx = q.get('correct_answer')

    if correct_idx is None or not choices or correct_idx >= len(choices):
        return None

    # Try each verifier
    result = verify_simple_arithmetic(stem, choices, correct_idx)
    if result:
        return result

    result = verify_place_value(stem, choices, correct_idx)
    if result:
        return result

    result = verify_expanded_form(stem, choices, correct_idx)
    if result:
        return result

    result = verify_percentage(stem, choices, correct_idx)
    if result:
        return result

    result = verify_square(stem, choices, correct_idx)
    if result:
        return result

    result = verify_remainder(stem, choices, correct_idx)
    if result:
        return result

    return None

def check_grammar(stem):
    """Check for grammar issues."""
    issues = []
    # Repeated words (but skip numeric patterns like "3 3/5")
    matches = re.finditer(r'\b(\w+)\s+\1\b', stem)
    for m in matches:
        word = m.group(1)
        # Skip if it's a number (common in fractions like "3 3/5")
        if word.isdigit():
            # Check if it's a mixed fraction pattern
            pos = m.start()
            after = stem[m.end():]
            if re.match(r'\s*/\s*\d+', after):
                continue  # It's a mixed fraction
        issues.append(f"Repeated word: '{word}'")

    if '  ' in stem:
        issues.append("Double space found")

    if len(stem.strip()) < 10 and stem.strip():
        issues.append(f"Very short stem: '{stem}'")

    return issues

def check_choices_quality(choices):
    """Check for duplicate/missing choices."""
    issues = []
    if not choices:
        issues.append("No choices provided")
        return issues
    if len(choices) < 4:
        issues.append(f"Only {len(choices)} choices (expected 4)")

    normalized = [str(c).strip().lower().replace(' ', '') for c in choices]
    seen = {}
    for i, n in enumerate(normalized):
        if n in seen:
            issues.append(f"Duplicate choice: '{choices[i]}' (positions {seen[n]} and {i})")
        else:
            seen[n] = i

    for i, c in enumerate(choices):
        if not str(c).strip():
            issues.append(f"Empty choice at position {i}")

    return issues

def check_visual(q):
    """Check visual relevance."""
    issues = []
    visual_svg = q.get('visual_svg')
    visual_alt = q.get('visual_alt')
    stem = q.get('stem', '')

    if visual_svg and visual_alt:
        stem_lower = stem.lower()
        alt_lower = visual_alt.lower()

        # Bar graph/chart visual but no data question
        if ('bar graph' in alt_lower or 'bar chart' in alt_lower or 'pie chart' in alt_lower):
            if not any(w in stem_lower for w in ['graph', 'chart', 'data', 'survey', 'table', 'represent', 'show', 'read', 'look', 'pictograph', 'tally', 'favourite', 'favorite', 'how many', 'most', 'least', 'total']):
                issues.append(f"Visual mismatch: alt='{visual_alt[:60]}' but stem doesn't reference data/charts")

        # Geometry visual but arithmetic question
        if ('triangle' in alt_lower or 'rectangle' in alt_lower or 'circle' in alt_lower) and 'number' not in alt_lower:
            if not any(w in stem_lower for w in ['triangle', 'rectangle', 'circle', 'shape', 'area', 'perimeter', 'angle', 'side', 'figure', 'polygon', 'square']):
                if any(w in stem_lower for w in ['×', '÷', 'multiply', 'divide']):
                    issues.append(f"Visual mismatch: geometry visual but arithmetic stem")

    return issues

def audit_question(q, filename):
    """Audit a single question."""
    qid = q.get('id', 'NO_ID')
    stem = q.get('stem', '')
    choices = q.get('choices', [])
    correct_idx = q.get('correct_answer')
    difficulty_score = q.get('difficulty_score', 0)

    # For topic files, only check G3-G6 range
    is_topic_file = 'topic-' in filename
    if is_topic_file and (difficulty_score < 101 or difficulty_score > 300):
        return

    # Math accuracy
    math_result = verify_math(q)
    if math_result:
        critical_math_errors.append({
            'id': qid, 'file': os.path.basename(filename),
            'expected': math_result[0], 'stated': math_result[1], 'stem': math_result[2]
        })

    # Choices
    choice_issues = check_choices_quality(choices)
    for issue in choice_issues:
        duplicate_choices.append({
            'id': qid, 'file': os.path.basename(filename),
            'issue': issue, 'choices': choices
        })

    # Grammar
    gram_issues = check_grammar(stem)
    for issue in gram_issues:
        grammar_issues.append({
            'id': qid, 'file': os.path.basename(filename),
            'issue': issue, 'stem': stem
        })

    # Visual
    vis_issues = check_visual(q)
    for issue in vis_issues:
        visual_mismatches.append({
            'id': qid, 'file': os.path.basename(filename),
            'issue': issue
        })

    # Anomalies
    if not stem.strip():
        anomalies.append({'id': qid, 'file': os.path.basename(filename), 'issue': 'Empty stem'})
    if correct_idx is not None and choices and correct_idx >= len(choices):
        anomalies.append({'id': qid, 'file': os.path.basename(filename), 'issue': f'correct_answer index {correct_idx} out of range'})
    if correct_idx is None:
        anomalies.append({'id': qid, 'file': os.path.basename(filename), 'issue': 'No correct_answer specified'})

# Main
print("=" * 80)
print("KIWIMATH GRADE 3-6 CONTENT QA AUDIT (v2 - reduced false positives)")
print("=" * 80)
print(f"\nFiles to process: {len(FILES_TO_CHECK)}")

total_questions = 0
for filepath in FILES_TO_CHECK:
    if not os.path.exists(filepath):
        continue
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        anomalies.append({'id': 'FILE', 'file': filepath, 'issue': f'Parse error: {e}'})
        continue

    # Handle both formats: {questions: [...]} and [...]
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict):
        questions = data.get('questions', [])
    else:
        continue

    total_questions += len(questions)
    for q in questions:
        if isinstance(q, dict):
            audit_question(q, filepath)

print(f"Total questions scanned: {total_questions}")

# Report
print("\n" + "=" * 80)
print(f"CRITICAL: MATH ACCURACY ERRORS ({len(critical_math_errors)} found)")
print("=" * 80)
for err in critical_math_errors:
    print(f"\n  [{err['id']}] ({err['file']})")
    print(f"    Stem: {err['stem'][:120]}")
    print(f"    Computed: {err['expected']}  |  Stated: {err['stated']}")

print("\n" + "=" * 80)
print(f"CHOICES ISSUES ({len(duplicate_choices)} found)")
print("=" * 80)
for err in duplicate_choices:
    print(f"\n  [{err['id']}] ({err['file']})")
    print(f"    Issue: {err['issue']}")
    print(f"    Choices: {err['choices']}")

print("\n" + "=" * 80)
print(f"GRAMMAR ISSUES ({len(grammar_issues)} found)")
print("=" * 80)
for err in grammar_issues:
    print(f"\n  [{err['id']}] ({err['file']})")
    print(f"    Issue: {err['issue']}")
    print(f"    Stem: {err['stem'][:120]}")

print("\n" + "=" * 80)
print(f"VISUAL MISMATCHES ({len(visual_mismatches)} found)")
print("=" * 80)
for err in visual_mismatches:
    print(f"\n  [{err['id']}] ({err['file']})")
    print(f"    {err['issue']}")

print("\n" + "=" * 80)
print(f"OTHER ANOMALIES ({len(anomalies)} found)")
print("=" * 80)
for err in anomalies:
    print(f"\n  [{err['id']}] ({err['file']})")
    print(f"    {err['issue']}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"  Total questions audited: {total_questions}")
print(f"  CRITICAL math errors: {len(critical_math_errors)}")
print(f"  Choices issues: {len(duplicate_choices)}")
print(f"  Grammar issues: {len(grammar_issues)}")
print(f"  Visual mismatches: {len(visual_mismatches)}")
print(f"  Other anomalies: {len(anomalies)}")
