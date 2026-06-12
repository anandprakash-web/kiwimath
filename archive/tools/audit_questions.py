#!/usr/bin/env python3
"""
Kiwimath Grade 3-6 Content QA Audit Script
Checks math accuracy, stem clarity, choices quality, visual relevance, and anomalies.
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

def extract_arithmetic(stem):
    """Try to extract a computable arithmetic expression from the stem."""
    # Pattern: "What is X op Y?" or similar
    patterns = [
        # Basic: "What is 22 × 13?"
        r'[Ww]hat is\s+([\d,.]+)\s*[×x\*]\s*([\d,.]+)',
        r'[Ww]hat is\s+([\d,.]+)\s*[÷/]\s*([\d,.]+)',
        r'[Ww]hat is\s+([\d,.]+)\s*[\+]\s*([\d,.]+)',
        r'[Ww]hat is\s+([\d,.]+)\s*[\-−–]\s*([\d,.]+)',
        # "Calculate X op Y"
        r'[Cc]alculate\s+([\d,.]+)\s*[×x\*]\s*([\d,.]+)',
        r'[Cc]alculate\s+([\d,.]+)\s*[÷/]\s*([\d,.]+)',
        r'[Cc]alculate\s+([\d,.]+)\s*[\+]\s*([\d,.]+)',
        r'[Cc]alculate\s+([\d,.]+)\s*[\-−–]\s*([\d,.]+)',
        # "Find X op Y"
        r'[Ff]ind\s+([\d,.]+)\s*[×x\*]\s*([\d,.]+)',
        r'[Ff]ind\s+([\d,.]+)\s*[÷/]\s*([\d,.]+)',
        r'[Ff]ind\s+([\d,.]+)\s*[\+]\s*([\d,.]+)',
        r'[Ff]ind\s+([\d,.]+)\s*[\-−–]\s*([\d,.]+)',
        # "Solve: X op Y"
        r'[Ss]olve:?\s*([\d,.]+)\s*[×x\*]\s*([\d,.]+)',
        r'[Ss]olve:?\s*([\d,.]+)\s*[÷/]\s*([\d,.]+)',
        r'[Ss]olve:?\s*([\d,.]+)\s*[\+]\s*([\d,.]+)',
        r'[Ss]olve:?\s*([\d,.]+)\s*[\-−–]\s*([\d,.]+)',
    ]

    # Detect operation from stem
    ops_map = {
        '×': 'mul', 'x': 'mul', '*': 'mul', '\\*': 'mul',
        '÷': 'div', '/': 'div',
        '+': 'add',
        '-': 'sub', '−': 'sub', '–': 'sub',
    }

    for i, pat in enumerate(patterns):
        m = re.search(pat, stem)
        if m:
            a_str = m.group(1).replace(',', '')
            b_str = m.group(2).replace(',', '')
            try:
                a = float(a_str)
                b = float(b_str)
            except ValueError:
                continue
            op_idx = i % 4  # 0=mul, 1=div, 2=add, 3=sub
            if op_idx == 0:
                result = a * b
            elif op_idx == 1:
                if b == 0:
                    continue
                result = a / b
            elif op_idx == 2:
                result = a + b
            else:
                result = a - b
            # Return as int if whole number
            if result == int(result):
                return str(int(result))
            return str(result)
    return None

def extract_multi_op(stem):
    """Extract multi-operation expressions like 'What is 12 + 5 × 3?'"""
    # Look for expressions with multiple ops
    m = re.search(r'[Ww]hat is\s+([\d]+(?:\s*[\+\-\×\÷\*\/x]\s*[\d]+)+)', stem)
    if not m:
        m = re.search(r'[Cc]alculate\s+([\d]+(?:\s*[\+\-\×\÷\*\/x]\s*[\d]+)+)', stem)
    if not m:
        m = re.search(r'[Ff]ind\s+([\d]+(?:\s*[\+\-\×\÷\*\/x]\s*[\d]+)+)', stem)
    if not m:
        m = re.search(r'[Ss]olve:?\s*([\d]+(?:\s*[\+\-\×\÷\*\/x]\s*[\d]+)+)', stem)
    if m:
        expr = m.group(1)
        # Replace unicode operators
        expr = expr.replace('×', '*').replace('÷', '/').replace('−', '-').replace('–', '-')
        # Replace 'x' between numbers with '*'
        expr = re.sub(r'(\d)\s*x\s*(\d)', r'\1*\2', expr)
        try:
            result = eval(expr)
            if isinstance(result, float) and result == int(result):
                return str(int(result))
            return str(result)
        except:
            pass
    return None

def check_perimeter_rectangle(stem, choices, correct_idx):
    """Check perimeter of rectangle questions."""
    m = re.search(r'[Pp]erimeter.*?rectangle.*?(\d+(?:\.\d+)?)\s*(?:cm|m|mm|units?).*?(\d+(?:\.\d+)?)\s*(?:cm|m|mm|units?)', stem)
    if not m:
        m = re.search(r'rectangle.*?(\d+(?:\.\d+)?)\s*(?:cm|m|mm|units?).*?(\d+(?:\.\d+)?)\s*(?:cm|m|mm|units?).*?[Pp]erimeter', stem)
    if not m:
        m = re.search(r'[Pp]erimeter.*?length\s*(?:=|is|of)?\s*(\d+(?:\.\d+)?).*?(?:width|breadth)\s*(?:=|is|of)?\s*(\d+(?:\.\d+)?)', stem)
    if m:
        l, w = float(m.group(1)), float(m.group(2))
        result = 2 * (l + w)
        if result == int(result):
            return str(int(result))
        return str(result)
    return None

def check_area_rectangle(stem, choices, correct_idx):
    """Check area of rectangle questions."""
    m = re.search(r'[Aa]rea.*?rectangle.*?(\d+(?:\.\d+)?)\s*(?:cm|m|mm|units?).*?(\d+(?:\.\d+)?)\s*(?:cm|m|mm|units?)', stem)
    if not m:
        m = re.search(r'rectangle.*?(\d+(?:\.\d+)?)\s*(?:cm|m|mm|units?).*?(\d+(?:\.\d+)?)\s*(?:cm|m|mm|units?).*?[Aa]rea', stem)
    if not m:
        m = re.search(r'[Aa]rea.*?length\s*(?:=|is|of)?\s*(\d+(?:\.\d+)?).*?(?:width|breadth)\s*(?:=|is|of)?\s*(\d+(?:\.\d+)?)', stem)
    if m:
        l, w = float(m.group(1)), float(m.group(2))
        result = l * w
        if result == int(result):
            return str(int(result))
        return str(result)
    return None

def check_percentage(stem):
    """Check percentage questions like 'What is 20% of 150?'"""
    m = re.search(r'[Ww]hat is\s+([\d.]+)\s*%\s*of\s+([\d,.]+)', stem)
    if not m:
        m = re.search(r'[Ff]ind\s+([\d.]+)\s*%\s*of\s+([\d,.]+)', stem)
    if not m:
        m = re.search(r'[Cc]alculate\s+([\d.]+)\s*%\s*of\s+([\d,.]+)', stem)
    if m:
        pct = float(m.group(1))
        num = float(m.group(2).replace(',', ''))
        result = pct * num / 100
        if result == int(result):
            return str(int(result))
        return str(result)
    return None

def check_square_of(stem):
    """Check 'square of X' or 'X squared'"""
    m = re.search(r'[Ss]quare of\s+(\d+)', stem)
    if not m:
        m = re.search(r'(\d+)\s*squared', stem)
    if not m:
        m = re.search(r'(\d+)\s*²', stem)
    if m:
        n = int(m.group(1))
        return str(n * n)
    return None

def check_cube_of(stem):
    """Check 'cube of X' or 'X cubed'"""
    m = re.search(r'[Cc]ube of\s+(\d+)', stem)
    if not m:
        m = re.search(r'(\d+)\s*cubed', stem)
    if not m:
        m = re.search(r'(\d+)\s*³', stem)
    if m:
        n = int(m.group(1))
        return str(n * n * n)
    return None

def check_fraction_simplify(stem):
    """Check fraction simplification: 'Simplify 12/18'"""
    m = re.search(r'[Ss]implif[yied]+\s*:?\s*(\d+)\s*/\s*(\d+)', stem)
    if not m:
        m = re.search(r'[Ss]implest form.*?(\d+)\s*/\s*(\d+)', stem)
    if not m:
        m = re.search(r'[Rr]educe\s*:?\s*(\d+)\s*/\s*(\d+)', stem)
    if m:
        n, d = int(m.group(1)), int(m.group(2))
        f = Fraction(n, d)
        return f"{f.numerator}/{f.denominator}"
    return None

def check_place_value(stem):
    """Check place value questions like 'digit in the thousands place of 2824'"""
    m = re.search(r'digit in the (\w+) place (?:of|in) (\d+)', stem)
    if m:
        place = m.group(1).lower()
        number = m.group(2)
        places = {'ones': -1, 'units': -1, 'tens': -2, 'hundreds': -3, 'thousands': -4, 'ten-thousands': -5, 'ten thousands': -5}
        if place in places:
            idx = places[place]
            if abs(idx) <= len(number):
                return number[idx]
    return None

def check_expanded_form(stem, choices, correct_idx):
    """Check expanded form questions."""
    m = re.search(r'expanded form of (\d+)', stem)
    if m:
        number = int(m.group(1))
        # Build expected expanded form
        digits = str(number)
        parts = []
        for i, d in enumerate(digits):
            if int(d) != 0:
                place_val = int(d) * (10 ** (len(digits) - 1 - i))
                parts.append(str(place_val))
        expected = " + ".join(parts)
        # Check if the correct answer matches
        if correct_idx < len(choices):
            correct_choice = choices[correct_idx].replace(" ", "").replace("+", "+")
            expected_norm = expected.replace(" ", "").replace("+", "+")
            # Parse and sum both
            try:
                correct_sum = sum(int(x.strip()) for x in choices[correct_idx].split("+"))
                if correct_sum != number:
                    return f"Sum should be {number}, got {correct_sum}"
            except:
                pass
    return None

def normalize_answer(ans):
    """Normalize answer string for comparison."""
    ans = str(ans).strip()
    # Remove trailing .0
    if ans.endswith('.0'):
        ans = ans[:-2]
    # Remove commas
    ans = ans.replace(',', '')
    # Remove units
    ans = re.sub(r'\s*(cm|m|mm|km|kg|g|ml|l|sq\s*cm|sq\s*m|units?|°).*$', '', ans)
    return ans.strip()

def verify_math(q):
    """Try to verify the math in a question. Returns (expected, actual) if mismatch found."""
    stem = q.get('stem', '')
    choices = q.get('choices', [])
    correct_idx = q.get('correct_answer')

    if correct_idx is None or not choices or correct_idx >= len(choices):
        return None

    stated_answer = choices[correct_idx]

    # Try various checks
    computed = extract_arithmetic(stem)
    if not computed:
        computed = extract_multi_op(stem)
    if not computed:
        computed = check_percentage(stem)
    if not computed:
        computed = check_square_of(stem)
    if not computed:
        computed = check_cube_of(stem)
    if not computed:
        computed = check_perimeter_rectangle(stem, choices, correct_idx)
    if not computed:
        computed = check_area_rectangle(stem, choices, correct_idx)
    if not computed:
        computed = check_place_value(stem)

    if computed:
        norm_computed = normalize_answer(computed)
        norm_stated = normalize_answer(stated_answer)
        if norm_computed != norm_stated:
            # Double check - maybe computed is in choices but at wrong index
            return (computed, stated_answer, stem)

    # Check expanded form
    result = check_expanded_form(stem, choices, correct_idx)
    if result:
        return (result, stated_answer, stem)

    # Check fraction simplification
    computed = check_fraction_simplify(stem)
    if computed:
        norm_computed = normalize_answer(computed)
        norm_stated = normalize_answer(stated_answer)
        if norm_computed != norm_stated:
            # Check if answer format might differ (e.g., "2/3" vs "2/3")
            return (computed, stated_answer, stem)

    return None

def check_grammar(stem):
    """Check for basic grammar issues."""
    issues = []

    # "An" before consonant sounds
    m = re.findall(r'\b[Aa]n\s+([bcdfghjklmnpqrstvwxyz])', stem)
    if m:
        for word_start in m:
            # Exceptions: "an hour", "an honest" etc.
            pass  # Too many false positives, skip

    # "A" before vowel sounds
    m = re.findall(r'\b[Aa]\s+([aeiou]\w+)', stem, re.IGNORECASE)
    # This has too many exceptions, skip

    # Repeated words
    m = re.search(r'\b(\w+)\s+\1\b', stem)
    if m:
        issues.append(f"Repeated word: '{m.group(1)}'")

    # Double spaces
    if '  ' in stem:
        issues.append("Double space found")

    # Missing question mark for questions
    if stem.strip() and any(stem.lower().startswith(w) for w in ['what', 'which', 'how many', 'how much', 'find the', 'calculate']):
        if not stem.strip().endswith('?') and not stem.strip().endswith('.'):
            pass  # Many stems don't end with punctuation, skip

    # Empty or very short stem
    if len(stem.strip()) < 10:
        issues.append(f"Very short stem: '{stem}'")

    return issues

def check_choices_quality(choices):
    """Check for duplicate choices and other issues."""
    issues = []

    if not choices:
        issues.append("No choices provided")
        return issues

    if len(choices) < 4:
        issues.append(f"Only {len(choices)} choices (expected 4)")

    # Check duplicates (case-insensitive, whitespace-normalized)
    normalized = [str(c).strip().lower().replace(' ', '') for c in choices]
    seen = {}
    for i, n in enumerate(normalized):
        if n in seen:
            issues.append(f"Duplicate choice: '{choices[i]}' (positions {seen[n]} and {i})")
        else:
            seen[n] = i

    # Check empty choices
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
        # Check if visual_alt topic aligns with stem topic
        stem_lower = stem.lower()
        alt_lower = visual_alt.lower()

        # Mismatch cases
        if 'number line' in alt_lower and not any(w in stem_lower for w in ['number', 'line', 'between', 'position', 'mark', 'place', 'value', 'expanded', 'digit']):
            if any(w in stem_lower for w in ['area', 'perimeter', 'angle', 'shape', 'triangle', 'rectangle', 'circle']):
                issues.append(f"Visual mismatch: alt='{visual_alt}' but stem is about geometry")

        if 'pie chart' in alt_lower or 'bar graph' in alt_lower or 'bar chart' in alt_lower:
            if not any(w in stem_lower for w in ['graph', 'chart', 'data', 'survey', 'table', 'represent', 'show']):
                issues.append(f"Visual mismatch: alt='{visual_alt}' but stem doesn't mention data/charts")

        if ('triangle' in alt_lower or 'rectangle' in alt_lower or 'circle' in alt_lower):
            if not any(w in stem_lower for w in ['triangle', 'rectangle', 'circle', 'shape', 'area', 'perimeter', 'angle', 'side', 'figure', 'polygon']):
                if any(w in stem_lower for w in ['multiply', 'divide', 'add', 'subtract', '×', '÷', '+', '-']):
                    issues.append(f"Visual mismatch: alt='{visual_alt}' but stem is arithmetic")

    return issues

def audit_question(q, filename):
    """Audit a single question."""
    qid = q.get('id', 'NO_ID')
    stem = q.get('stem', '')
    choices = q.get('choices', [])
    correct_idx = q.get('correct_answer')
    difficulty_score = q.get('difficulty_score', 0)

    # Only check G3-G6 range (difficulty 101-300) for topic files, all for curriculum files
    is_topic_file = 'topic-' in filename
    if is_topic_file and (difficulty_score < 101 or difficulty_score > 300):
        return

    # Math accuracy check
    math_result = verify_math(q)
    if math_result:
        critical_math_errors.append({
            'id': qid,
            'file': os.path.basename(filename),
            'expected': math_result[0],
            'stated': math_result[1],
            'stem': math_result[2]
        })

    # Choices quality
    choice_issues = check_choices_quality(choices)
    for issue in choice_issues:
        duplicate_choices.append({
            'id': qid,
            'file': os.path.basename(filename),
            'issue': issue,
            'choices': choices
        })

    # Grammar
    gram_issues = check_grammar(stem)
    for issue in gram_issues:
        grammar_issues.append({
            'id': qid,
            'file': os.path.basename(filename),
            'issue': issue,
            'stem': stem
        })

    # Visual check
    vis_issues = check_visual(q)
    for issue in vis_issues:
        visual_mismatches.append({
            'id': qid,
            'file': os.path.basename(filename),
            'issue': issue
        })

    # Anomalies
    if not stem.strip():
        anomalies.append({'id': qid, 'file': os.path.basename(filename), 'issue': 'Empty stem'})
    if correct_idx is not None and choices and correct_idx >= len(choices):
        anomalies.append({'id': qid, 'file': os.path.basename(filename), 'issue': f'correct_answer index {correct_idx} out of range (only {len(choices)} choices)'})
    if correct_idx is None:
        anomalies.append({'id': qid, 'file': os.path.basename(filename), 'issue': 'No correct_answer specified'})

def process_file(filepath):
    """Process a single JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        anomalies.append({'id': 'FILE', 'file': filepath, 'issue': f'Cannot parse: {e}'})
        return

    questions = data.get('questions', [])
    if not questions:
        return

    for q in questions:
        audit_question(q, filepath)

# Main execution
print("=" * 80)
print("KIWIMATH GRADE 3-6 CONTENT QA AUDIT")
print("=" * 80)
print(f"\nFiles to process: {len(FILES_TO_CHECK)}")

total_questions = 0
for filepath in FILES_TO_CHECK:
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            qs = data.get('questions', [])
            total_questions += len(qs)
            for q in qs:
                audit_question(q, filepath)
        except Exception as e:
            anomalies.append({'id': 'FILE', 'file': filepath, 'issue': f'Error: {e}'})

print(f"Total questions scanned: {total_questions}")

# Report
print("\n" + "=" * 80)
print(f"CRITICAL: MATH ACCURACY ERRORS ({len(critical_math_errors)} found)")
print("=" * 80)
for err in critical_math_errors:
    print(f"\n  ID: {err['id']}")
    print(f"  File: {err['file']}")
    print(f"  Stem: {err['stem']}")
    print(f"  Computed answer: {err['expected']}")
    print(f"  Stated answer: {err['stated']}")

print("\n" + "=" * 80)
print(f"DUPLICATE/MISSING CHOICES ({len(duplicate_choices)} found)")
print("=" * 80)
for err in duplicate_choices:
    print(f"\n  ID: {err['id']}")
    print(f"  File: {err['file']}")
    print(f"  Issue: {err['issue']}")
    print(f"  Choices: {err['choices']}")

print("\n" + "=" * 80)
print(f"GRAMMAR ISSUES ({len(grammar_issues)} found)")
print("=" * 80)
for err in grammar_issues:
    print(f"\n  ID: {err['id']}")
    print(f"  File: {err['file']}")
    print(f"  Issue: {err['issue']}")
    print(f"  Stem: {err['stem'][:100]}")

print("\n" + "=" * 80)
print(f"VISUAL MISMATCHES ({len(visual_mismatches)} found)")
print("=" * 80)
for err in visual_mismatches:
    print(f"\n  ID: {err['id']}")
    print(f"  File: {err['file']}")
    print(f"  Issue: {err['issue']}")

print("\n" + "=" * 80)
print(f"OTHER ANOMALIES ({len(anomalies)} found)")
print("=" * 80)
for err in anomalies:
    print(f"\n  ID: {err['id']}")
    print(f"  File: {err['file']}")
    print(f"  Issue: {err['issue']}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"  Total questions audited: {total_questions}")
print(f"  Critical math errors: {len(critical_math_errors)}")
print(f"  Duplicate/missing choices: {len(duplicate_choices)}")
print(f"  Grammar issues: {len(grammar_issues)}")
print(f"  Visual mismatches: {len(visual_mismatches)}")
print(f"  Other anomalies: {len(anomalies)}")
