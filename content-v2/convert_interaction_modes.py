#!/usr/bin/env python3
"""
Convert ~30% of curriculum questions to "integer" mode and ~15% to "drag_drop" mode.
Remaining ~55% stay as "mcq".

Processes: ncert-curriculum, icse-curriculum, igcse-curriculum (grades 1-6).
"""

import json
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Keywords indicating the stem asks for a numeric value
INTEGER_KEYWORDS = re.compile(
    r'\b(how many|what is|find the|calculate|solve|sum|difference|product|total|perimeter|area|value)\b',
    re.IGNORECASE
)

# Keywords indicating ordering/sequencing (primary - strong signal)
DRAG_DROP_KEYWORDS = re.compile(
    r'\b(arrange|order|ascending|descending|smallest to largest|largest to smallest|sequence|which comes next|put in order|sort|rank|least to greatest|greatest to least)\b',
    re.IGNORECASE
)

# Secondary keywords - weaker signal but combined with all-numeric choices, qualifies for drag_drop
DRAG_DROP_SECONDARY_KEYWORDS = re.compile(
    r'\b(compare|greater|smaller|bigger|largest|smallest|which number comes|before|after|between|missing number|fill in|number line|counting)\b',
    re.IGNORECASE
)


def is_pure_integer(s):
    """Check if a string is a pure integer (no units, fractions, text)."""
    s = s.strip()
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False


def all_choices_are_numbers(choices):
    """Check if all choices are numeric (int or float)."""
    for c in choices:
        try:
            float(c.strip())
        except (ValueError, TypeError):
            return False
    return True


def can_convert_to_integer(q):
    """Check if a question qualifies for integer mode."""
    stem = q.get('stem', '')
    choices = q.get('choices', [])
    correct_idx = q.get('correct_answer', 0)

    if not choices or correct_idx >= len(choices):
        return False

    correct_choice = str(choices[correct_idx]).strip()

    # Must be a pure integer
    if not is_pure_integer(correct_choice):
        return False

    # Stem must contain numeric-asking keywords
    if not INTEGER_KEYWORDS.search(stem):
        return False

    return True


def can_convert_to_drag_drop(q):
    """Check if a question qualifies for drag_drop mode."""
    stem = q.get('stem', '')
    choices = q.get('choices', [])

    if len(choices) < 3:
        return False

    # Strong signal: stem has explicit ordering keywords
    if DRAG_DROP_KEYWORDS.search(stem):
        return True

    # Medium signal: all choices are numbers AND stem has comparison/sequence keywords
    if all_choices_are_numbers(choices) and DRAG_DROP_SECONDARY_KEYWORDS.search(stem):
        return True

    # Weaker signal: all choices are distinct integers (good for "arrange these numbers")
    if all_choices_are_numbers(choices) and len(choices) == 4:
        try:
            nums = [float(c.strip()) for c in choices]
            if len(set(nums)) == len(nums):
                return True
        except (ValueError, TypeError):
            pass

    return False


def determine_correct_order(stem, choices):
    """Determine the correct ordering of choices based on stem context."""
    # Try to parse all choices as numbers for sorting
    numeric_choices = []
    for i, c in enumerate(choices):
        try:
            numeric_choices.append((float(c.strip()), i))
        except (ValueError, TypeError):
            # If not all numeric, just return original order
            return list(range(len(choices)))

    stem_lower = stem.lower()

    # Determine sort direction
    if any(kw in stem_lower for kw in ['descending', 'largest to smallest', 'greatest to smallest', 'biggest to smallest']):
        # Sort descending
        numeric_choices.sort(key=lambda x: x[0], reverse=True)
    else:
        # Default: ascending
        numeric_choices.sort(key=lambda x: x[0])

    # Return the sorted values as drag_items and correct_order as [0,1,2,...]
    sorted_values = [choices[idx] for _, idx in numeric_choices]
    return sorted_values


def process_file(filepath):
    """Process a single JSON file and convert questions."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both formats
    if isinstance(data, list):
        questions = data
        is_list_format = True
    elif isinstance(data, dict) and 'questions' in data:
        questions = data['questions']
        is_list_format = False
    else:
        return {'mcq': 0, 'integer': 0, 'drag_drop': 0, 'total': 0}

    total = len(questions)
    if total == 0:
        return {'mcq': 0, 'integer': 0, 'drag_drop': 0, 'total': 0}

    # Reset all questions to clean state
    for q in questions:
        q.pop('interaction_mode', None)
        q.pop('correct_value', None)
        q.pop('drag_items', None)
        q.pop('correct_order', None)

    max_integer = int(total * 0.30)
    max_drag_drop = int(total * 0.15)

    integer_count = 0
    drag_drop_count = 0

    # First pass: convert to integer
    for q in questions:
        if integer_count >= max_integer:
            break
        if q.get('interaction_mode') and q['interaction_mode'] != 'mcq':
            continue
        if can_convert_to_integer(q):
            correct_idx = q['correct_answer']
            correct_value = int(str(q['choices'][correct_idx]).strip())
            q['interaction_mode'] = 'integer'
            q['correct_value'] = correct_value
            integer_count += 1

    # Second pass: convert to drag_drop
    for q in questions:
        if drag_drop_count >= max_drag_drop:
            break
        if q.get('interaction_mode') and q['interaction_mode'] != 'mcq':
            continue
        if can_convert_to_drag_drop(q):
            sorted_items = determine_correct_order(q['stem'], q['choices'])
            q['interaction_mode'] = 'drag_drop'
            q['drag_items'] = sorted_items
            q['correct_order'] = list(range(len(sorted_items)))
            drag_drop_count += 1

    # Mark remaining as mcq explicitly
    for q in questions:
        if not q.get('interaction_mode'):
            q['interaction_mode'] = 'mcq'

    mcq_count = total - integer_count - drag_drop_count

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {
        'mcq': mcq_count,
        'integer': integer_count,
        'drag_drop': drag_drop_count,
        'total': total
    }


def find_curriculum_files():
    """Find all question JSON files in the 3 curricula."""
    files = []
    curricula = ['ncert-curriculum', 'icse-curriculum', 'igcse-curriculum']

    for curr in curricula:
        curr_dir = BASE_DIR / curr
        if not curr_dir.exists():
            continue
        for grade in range(1, 7):
            grade_dir = curr_dir / f'grade{grade}'
            if not grade_dir.exists():
                continue
            for json_file in grade_dir.glob('*.json'):
                files.append((curr, grade, json_file))

    return files


def main():
    files = find_curriculum_files()

    if not files:
        print("No curriculum files found!")
        return

    # Track stats per curriculum
    stats = {}
    grand_total = {'mcq': 0, 'integer': 0, 'drag_drop': 0, 'total': 0}

    print(f"Processing {len(files)} curriculum files...\n")

    for curr, grade, filepath in files:
        result = process_file(filepath)

        if curr not in stats:
            stats[curr] = {'mcq': 0, 'integer': 0, 'drag_drop': 0, 'total': 0}

        for k in result:
            stats[curr][k] += result[k]
            grand_total[k] += result[k]

        print(f"  {curr}/grade{grade}: {result['total']} total | "
              f"{result['integer']} integer ({100*result['integer']/max(result['total'],1):.1f}%) | "
              f"{result['drag_drop']} drag_drop ({100*result['drag_drop']/max(result['total'],1):.1f}%) | "
              f"{result['mcq']} mcq ({100*result['mcq']/max(result['total'],1):.1f}%)")

    print("\n" + "=" * 70)
    print("SUMMARY BY CURRICULUM")
    print("=" * 70)
    for curr, s in sorted(stats.items()):
        t = max(s['total'], 1)
        print(f"\n  {curr}:")
        print(f"    Total questions: {s['total']}")
        print(f"    Integer:   {s['integer']:5d} ({100*s['integer']/t:.1f}%)")
        print(f"    Drag/Drop: {s['drag_drop']:5d} ({100*s['drag_drop']/t:.1f}%)")
        print(f"    MCQ:       {s['mcq']:5d} ({100*s['mcq']/t:.1f}%)")

    t = max(grand_total['total'], 1)
    print(f"\n{'=' * 70}")
    print(f"GRAND TOTAL: {grand_total['total']} questions")
    print(f"  Integer:   {grand_total['integer']:5d} ({100*grand_total['integer']/t:.1f}%)")
    print(f"  Drag/Drop: {grand_total['drag_drop']:5d} ({100*grand_total['drag_drop']/t:.1f}%)")
    print(f"  MCQ:       {grand_total['mcq']:5d} ({100*grand_total['mcq']/t:.1f}%)")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
