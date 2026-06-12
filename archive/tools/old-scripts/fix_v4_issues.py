#!/usr/bin/env python3
"""
Kiwimath Content v4 — Issue Fixer
===================================
Addresses all issues identified in the quality review:

1. Domain classification fixes (algebra, data, percentage)
2. Identical diagnostic deduplication
3. Misleading pattern diagnostics
4. Hint spoiler remediation
5. country_context extraction to shared config
6. school_grade population
7. Visual dependency cataloging
8. Index file regeneration
"""

import json
import glob
import os
import re
import copy
from collections import defaultdict
from datetime import datetime

V4 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'content-v4')

# ─── Shared locale config (extracted from country_context) ───
LOCALE_CONFIG = {
    "india": {
        "currency": "₹", "currency_name": "rupees",
        "names": ["Aarav", "Priya", "Arjun", "Diya", "Rohan", "Ananya", "Vihaan", "Isha"],
        "objects": ["mangoes", "rotis", "sweets", "bangles", "diyas"],
        "units": "km/kg/L"
    },
    "singapore": {
        "currency": "$", "currency_name": "dollars",
        "names": ["Wei", "Mei", "Jun", "Ling", "Hao", "Xin", "Kai", "Yan"],
        "objects": ["durians", "mooncakes", "orchids", "kites", "lanterns"],
        "units": "km/kg/L"
    },
    "us": {
        "currency": "$", "currency_name": "dollars",
        "names": ["Alex", "Emma", "Liam", "Sophia", "Noah", "Olivia", "James", "Mia"],
        "objects": ["apples", "cookies", "stickers", "marbles", "crayons"],
        "units": "mi/lb/gal"
    }
}

stats = defaultdict(int)


def fix_domain_classification(data):
    """Fix #2: Correct domain assignments for misclassified topics."""
    name_lower = data['topic_name'].lower()
    original_domain = data['domain']

    if 'algebra' in name_lower and original_domain != 'algebra':
        data['domain'] = 'algebra'
        stats['domain_fixed'] += 1
    elif ('data' in name_lower and 'statistic' in name_lower) and original_domain != 'data':
        data['domain'] = 'data'
        stats['domain_fixed'] += 1
    elif 'percentage' in name_lower or 'percent' in name_lower:
        if original_domain not in ('ratio', 'numbers'):
            data['domain'] = 'ratio'
            stats['domain_fixed'] += 1

    # Also fix domain on individual questions
    for q in data['questions']:
        if q.get('adaptive_topic_id') == data['topic_id']:
            # Questions in algebra topics should reflect the topic domain
            if data['domain'] == 'algebra' and q.get('skill_domain') != 'algebra':
                pass  # Keep original skill_domain (it's the skill's true domain)


def fix_identical_diagnostics(q):
    """Fix #3: Deduplicate identical diagnostic messages."""
    diag = q.get('diagnostics', {})
    if not diag or len(diag) < 2:
        return

    vals = {}
    for k, v in diag.items():
        v_str = str(v) if not isinstance(v, str) else v
        vals.setdefault(v_str, []).append(k)

    duplicated = {v: keys for v, keys in vals.items() if len(keys) > 1}
    if not duplicated:
        return

    stem = q.get('stem', '')
    choices = q.get('choices', [])
    correct = q.get('correct_answer', 0)

    for dup_text, dup_keys in duplicated.items():
        for i, key in enumerate(dup_keys[1:], 1):  # Skip the first occurrence
            key_int = int(key) if key.isdigit() else None
            if key_int is not None and key_int < len(choices):
                wrong_choice = choices[key_int]
                correct_choice = choices[correct] if correct < len(choices) else '?'

                # Generate differentiated feedback
                new_diag = _generate_specific_diagnostic(
                    stem, wrong_choice, correct_choice, key_int, dup_text
                )
                diag[key] = new_diag
                stats['diagnostics_fixed'] += 1


def _generate_specific_diagnostic(stem, wrong_answer, correct_answer, choice_idx, original_text):
    """Generate a differentiated diagnostic for a specific wrong answer."""
    try:
        wrong_num = float(str(wrong_answer).replace(',', '').replace('$', '').replace('₹', ''))
        correct_num = float(str(correct_answer).replace(',', '').replace('$', '').replace('₹', ''))
        diff = wrong_num - correct_num

        if abs(diff) < 0.01:
            return original_text

        if diff > 0:
            return f"Your answer is {abs(diff):g} too high. Double-check your working — look at each step carefully."
        else:
            return f"Your answer is {abs(diff):g} too low. Recheck your calculation — did you miss a step?"
    except (ValueError, TypeError):
        # Non-numeric: differentiate by position
        position_hints = [
            "Look at the problem again — are you reading all the information correctly?",
            "Try a different approach. What is the question really asking?",
            "Go back to the basics. Can you draw or model this problem?",
        ]
        return position_hints[choice_idx % len(position_hints)]


def fix_pattern_diagnostics(q, topic_name):
    """Fix #4: Fix misleading diagnostics for pattern/sequence questions."""
    if 'pattern' not in topic_name.lower() and 'sequence' not in topic_name.lower():
        return

    stem = q.get('stem', '').lower()
    diag = q.get('diagnostics', {})

    # Detect multiplicative patterns in the stem
    is_multiplicative = False
    numbers_in_stem = re.findall(r'\d+', stem)
    if len(numbers_in_stem) >= 3:
        nums = [int(n) for n in numbers_in_stem[:4]]
        # Check if ratio is constant (geometric)
        if all(nums[i] != 0 for i in range(len(nums)-1)):
            ratios = [nums[i+1]/nums[i] for i in range(len(nums)-1)]
            if len(set(round(r, 2) for r in ratios)) == 1 and ratios[0] != 1:
                is_multiplicative = True

    if not is_multiplicative:
        return

    # Fix diagnostics that say "adding" for multiplicative patterns
    for key, val in diag.items():
        if isinstance(val, str) and ('adding' in val.lower() or 'add the same' in val.lower()):
            ratio = round(ratios[0], 1) if ratios else '?'
            diag[key] = f"This is a multiplicative pattern — each number is multiplied by {ratio}. Look at the ratio between consecutive terms, not the difference."
            stats['pattern_diagnostics_fixed'] += 1


def fix_hint_spoilers(q):
    """Fix #5: Address hint spoiler risk."""
    hq = q.get('hint_quality')
    if not isinstance(hq, dict) or hq.get('quality') != 'spoiler':
        return

    hint = q.get('hint')
    if not isinstance(hint, dict):
        return

    correct = q.get('correct_answer', 0)
    choices = q.get('choices', [])
    correct_text = str(choices[correct]) if correct < len(choices) else ''

    # Check if any hint level directly reveals the answer
    spoiler_fixed = False
    for level_key in ['level_0', 'level_1', 'level_2']:
        level_text = hint.get(level_key, '')
        if correct_text and correct_text in level_text and len(correct_text) > 1:
            # Remove the direct answer from early hint levels
            hint[level_key] = re.sub(
                re.escape(correct_text),
                '___',
                level_text
            )
            spoiler_fixed = True

    if spoiler_fixed:
        hq['quality'] = 'good'
        hq['spoiler_remediated'] = True
        stats['spoilers_fixed'] += 1


def fix_country_context(q):
    """Fix #6: Replace inline country_context with locale_id reference."""
    cc = q.get('country_context')
    if not cc:
        return

    # Replace the full dict with a reference key
    q['locale_ids'] = list(cc.keys())
    del q['country_context']
    stats['country_context_extracted'] += 1


def fix_school_grade(q, grade):
    """Fix #7: Populate null school_grade from adaptive_grade."""
    if q.get('school_grade') is None:
        q['school_grade'] = grade
        stats['school_grade_fixed'] += 1


def catalog_visual_deps(q, visual_catalog):
    """Fix #8: Build visual dependency catalog."""
    svg = q.get('visual_svg')
    if svg:
        visual_catalog['has_svg'].append({
            'id': q['id'],
            'svg': svg,
            'verified': q.get('visual_ai_verified', False),
            'type': q.get('visual_type', 'unknown'),
            'requirement': q.get('visual_requirement', 'unknown'),
        })
    elif q.get('visual_requirement') == 'essential':
        visual_catalog['essential_missing'].append({
            'id': q['id'],
            'requirement': 'essential',
            'type': q.get('visual_type', 'unknown'),
        })


def regenerate_index(grade, topic_files):
    """Fix #1: Generate proper index.json for each grade."""
    topics = []
    total_questions = 0

    for tf in sorted(topic_files):
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
            'source_breakdown': data.get('source_breakdown', {}),
        })
        total_questions += data['total_questions']

    index = {
        'grade': grade,
        'total_topics': len(topics),
        'total_questions': total_questions,
        'topics': topics,
        'schema_version': '4.0',
        'generated_at': datetime.now().isoformat(),
    }

    return index


def main():
    print("=" * 70)
    print("KIWIMATH CONTENT v4 — ISSUE FIXER")
    print("=" * 70)

    visual_catalog = {'has_svg': [], 'essential_missing': []}

    # Write shared locale config
    locale_path = os.path.join(V4, 'locale_config.json')
    with open(locale_path, 'w') as f:
        json.dump(LOCALE_CONFIG, f, indent=2, ensure_ascii=False)
    print(f"\n[1] Wrote shared locale config → {locale_path}")

    # Process all topic files
    for grade in range(1, 7):
        grade_dir = os.path.join(V4, 'adaptive', f'grade{grade}')
        topic_files = sorted(glob.glob(os.path.join(grade_dir, 'g*.json')))

        print(f"\n[Grade {grade}] Processing {len(topic_files)} topics...")

        for tf in topic_files:
            if 'index' in tf:
                continue

            with open(tf) as f:
                data = json.load(f)

            # Fix domain classification (topic-level)
            fix_domain_classification(data)

            # Fix individual questions
            for q in data['questions']:
                fix_identical_diagnostics(q)
                fix_pattern_diagnostics(q, data['topic_name'])
                fix_hint_spoilers(q)
                fix_country_context(q)
                fix_school_grade(q, grade)
                catalog_visual_deps(q, visual_catalog)

            # Update total_questions (in case any were removed)
            data['total_questions'] = len(data['questions'])
            data['schema_version'] = '4.1'
            data['fixed_at'] = datetime.now().isoformat()

            # Write fixed file
            with open(tf, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        # Regenerate index
        index = regenerate_index(grade, topic_files)
        index_path = os.path.join(grade_dir, 'index.json')
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        print(f"  → index.json regenerated: {index['total_topics']} topics, {index['total_questions']:,} questions")

    # Write visual dependency catalog
    catalog_path = os.path.join(V4, 'visual_catalog.json')
    catalog_summary = {
        'total_with_svg': len(visual_catalog['has_svg']),
        'total_unverified': sum(1 for v in visual_catalog['has_svg'] if not v['verified']),
        'total_essential_missing': len(visual_catalog['essential_missing']),
        'questions_with_svg': visual_catalog['has_svg'][:20],  # Sample
        'essential_missing_svg': visual_catalog['essential_missing'][:20],  # Sample
        'generated_at': datetime.now().isoformat(),
    }
    with open(catalog_path, 'w') as f:
        json.dump(catalog_summary, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 70)
    print("FIX SUMMARY")
    print("=" * 70)
    print(f"  Domain classifications fixed:    {stats['domain_fixed']}")
    print(f"  Identical diagnostics fixed:     {stats['diagnostics_fixed']}")
    print(f"  Pattern diagnostics corrected:   {stats['pattern_diagnostics_fixed']}")
    print(f"  Hint spoilers remediated:        {stats['spoilers_fixed']}")
    print(f"  country_context → locale_ids:    {stats['country_context_extracted']:,}")
    print(f"  school_grade populated:          {stats['school_grade_fixed']:,}")
    print(f"  Visual dependencies cataloged:   {len(visual_catalog['has_svg']):,} with SVG, {len(visual_catalog['essential_missing']):,} essential missing")
    print(f"  Index files regenerated:         6")
    print(f"  Schema version updated:          4.0 → 4.1")


if __name__ == '__main__':
    main()
