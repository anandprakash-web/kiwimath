#!/usr/bin/env python3
"""
Content QA Scanner for Kiwimath Question Bank
Scans for:
1. Visual-stem mismatches (visual shows different operation than stem asks)
2. "Chikoo" prefix questions with English errors
3. Pattern questions with unnecessary/redundant visuals
"""

import json
import glob
import re
import os

BASE = '/sessions/optimistic-laughing-franklin/mnt/Downloads/kiwimath/content-v2'

def load_all_questions():
    """Load all questions from all JSON files."""
    all_questions = []
    files = glob.glob(os.path.join(BASE, '**/*.json'), recursive=True)
    skip = ['manifest', 'visual_registry', 'visual_updates', 'questions_needing_visuals', 'all_questions_combined']
    for f in files:
        basename = os.path.splitext(os.path.basename(f))[0]
        if any(s in basename for s in skip):
            continue
        try:
            with open(f) as fh:
                data = json.load(fh)
            qs = data.get('questions', []) if isinstance(data, dict) else data if isinstance(data, list) else []
            for q in qs:
                if isinstance(q, dict) and 'id' in q:
                    q['_source_file'] = f
                    all_questions.append(q)
        except (json.JSONDecodeError, TypeError):
            pass
    return all_questions


def check_visual_stem_mismatch(questions):
    """
    Issue 1: Find questions where visual_svg contradicts stem.
    Look for arithmetic operation mismatches.
    """
    findings = []

    add_words = ['add', 'plus', 'sum', 'total', 'altogether', 'together', 'more get on', 'join', 'combine']
    sub_words = ['subtract', 'minus', 'take away', 'left', 'remain', 'fewer', 'less than', 'fall down', 'ate', 'gave away', 'lost', 'plucked', 'removed']
    mul_words = ['multiply', 'times', 'product', 'groups of']
    div_words = ['divide', 'share equally', 'split', 'quotient']

    def detect_operation_stem(stem):
        s = stem.lower()
        ops = set()
        if any(w in s for w in add_words) or re.search(r'\d+\s*\+\s*\d+', s):
            ops.add('addition')
        if any(w in s for w in sub_words) or re.search(r'\d+\s*-\s*\d+', s):
            ops.add('subtraction')
        if any(w in s for w in mul_words) or re.search(r'\d+\s*[×]\s*\d+', s):
            ops.add('multiplication')
        if any(w in s for w in div_words) or re.search(r'\d+\s*[÷/]\s*\d+', s):
            ops.add('division')
        # NxN dimension notation (2x2, 3x3) is NOT multiplication
        # Only count 'x' as multiply if NOT in NxN pattern
        if re.search(r'\d+\s*x\s*\d+', s) and not re.search(r'\d+x\d+', s):
            ops.add('multiplication')
        return ops

    def detect_operation_alt(alt):
        a = alt.lower()
        ops = set()
        # Skip generic placeholder alt text (hyphenated topic names are not subtraction)
        if re.match(r'^topic-\d+-\w+ visual$', a):
            return ops
        if '+' in a or 'add' in a or 'plus' in a or 'addition' in a:
            ops.add('addition')
        if 'subtract' in a or 'minus' in a or 'subtraction' in a:
            ops.add('subtraction')
        if re.search(r'\d+\s*-\s*\d+', a):
            ops.add('subtraction')
        if 'multiply' in a or 'multiplication' in a or 'times' in a:
            ops.add('multiplication')
        if '÷' in a or 'divide' in a or 'division' in a:
            ops.add('division')
        if re.search(r'\d+\s*\+\s*\d+', a):
            ops.add('addition')
        if re.search(r'\d+\s*[x×]\s*\d+', a):
            ops.add('multiplication')
        return ops

    for q in questions:
        visual = q.get('visual_svg')
        if not visual:
            continue
        stem = q.get('stem', '')
        alt = q.get('visual_alt', '') or ''

        stem_ops = detect_operation_stem(stem)
        alt_ops = detect_operation_alt(alt)

        if not stem_ops or not alt_ops:
            continue

        # Check for contradiction: stem says one operation, alt shows a DIFFERENT one
        # Only flag if they are contradictory (e.g., stem=addition, alt=subtraction)
        contradictions = {
            ('addition', 'subtraction'),
            ('subtraction', 'addition'),
            ('multiplication', 'division'),
            ('division', 'multiplication'),
        }

        for s_op in stem_ops:
            for a_op in alt_ops:
                if (s_op, a_op) in contradictions and s_op not in alt_ops and a_op not in stem_ops:
                    # True mismatch - one operation in stem, contradicting in visual
                    findings.append({
                        'id': q['id'],
                        'stem': stem,
                        'visual_svg': visual,
                        'visual_alt': alt,
                        'stem_operation': s_op,
                        'visual_operation': a_op,
                        'source': q['_source_file'],
                        'tags': q.get('tags', []),
                    })
                    break

        # Also check: visual filename or alt contains a specific equation that contradicts stem
        # E.g., alt says "9 - 2 = ?" but stem asks "What is 9 + 2?"
        alt_equations = re.findall(r'(\d+)\s*([+\-×÷xX])\s*(\d+)', alt)
        stem_equations = re.findall(r'(\d+)\s*([+\-×÷xX])\s*(\d+)', stem)

        if alt_equations and stem_equations:
            for ae in alt_equations:
                for se in stem_equations:
                    # Same numbers but different operator
                    if ae[0] == se[0] and ae[2] == se[2] and ae[1] != se[1]:
                        findings.append({
                            'id': q['id'],
                            'stem': stem,
                            'visual_svg': visual,
                            'visual_alt': alt,
                            'stem_operation': f"{se[0]}{se[1]}{se[2]}",
                            'visual_operation': f"{ae[0]}{ae[1]}{ae[2]}",
                            'source': q['_source_file'],
                            'tags': q.get('tags', []),
                            'type': 'equation_mismatch'
                        })

    # Deduplicate
    seen = set()
    unique = []
    for f in findings:
        if f['id'] not in seen:
            seen.add(f['id'])
            unique.append(f)
    return unique


def check_chikoo_errors(questions):
    """
    Issue 2: Find "Chikoo" prefix questions with grammatical errors.
    """
    findings = []

    for q in questions:
        stem = q.get('stem', '')
        if 'Chikoo' not in stem and 'chikoo' not in stem.lower():
            continue

        issues = []

        # Check for repeated phrases
        words = stem.split()
        # Check repeated 2-3 word phrases
        for n in range(2, 5):
            for i in range(len(words) - 2*n):
                phrase = ' '.join(words[i:i+n]).lower().strip('.,;:')
                rest = ' '.join(words[i+n:]).lower()
                if phrase in rest and len(phrase) > 5:
                    issues.append(f"Repeated phrase: '{phrase}'")
                    break

        # Check for "at a party" or location phrase repeated
        location_phrases = re.findall(r'(at (?:a|the) \w+)', stem.lower())
        if len(location_phrases) > 1:
            issues.append(f"Repeated location: {location_phrases}")

        # Check for irrelevant prefix that doesn't connect to the math
        # Pattern: "Chikoo is [doing X]: [actual question]"
        prefix_match = re.match(r"(?:Help )?Chikoo (?:is )?([\w\s]+?):\s*(.+)", stem)
        if prefix_match:
            prefix_activity = prefix_match.group(1).strip()
            actual_q = prefix_match.group(2).strip()
            # Check if the prefix activity is completely unrelated to the question
            # e.g., "exploring shapes:" followed by a direction question
            pass

        # Check for double spaces
        if '  ' in stem:
            issues.append("Double spaces in stem")

        # Check for common grammar issues
        if re.search(r'\b(is is|the the|a a|an an)\b', stem.lower()):
            issues.append("Repeated articles/words")

        # Check subject-verb agreement issues
        if re.search(r'Chikoo are\b', stem):
            issues.append("Subject-verb disagreement: 'Chikoo are'")

        # Check for "at a party at a party" style repetitions
        if re.search(r'(at a \w+).*(at a \w+)', stem.lower()):
            matches = re.findall(r'at a (\w+)', stem.lower())
            if len(matches) >= 2 and matches[0] == matches[1]:
                issues.append(f"Repeated 'at a {matches[0]}'")

        # Flag ALL Chikoo questions for review (prefix relevance check)
        if not issues:
            # Check if prefix is just filler
            if re.match(r"(?:Help )?Chikoo (?:is )?(?:exploring|practising|figuring out|measuring)", stem):
                issues.append("Generic filler prefix (review for relevance)")

        findings.append({
            'id': q['id'],
            'stem': stem,
            'issues': issues,
            'source': q['_source_file'],
            'tags': q.get('tags', []),
        })

    return findings


def check_pattern_unnecessary_visuals(questions):
    """
    Issue 3: Pattern questions with visuals that just repeat the numbers.
    """
    findings = []

    for q in questions:
        visual = q.get('visual_svg')
        if not visual:
            continue

        stem = q.get('stem', '')
        alt = q.get('visual_alt', '') or ''
        tags = q.get('tags', [])

        # Check if it's a number pattern question
        is_pattern = (
            'pattern' in str(tags).lower() or
            'sequence' in str(tags).lower() or
            'series' in stem.lower() or
            re.search(r'what comes next', stem.lower()) or
            re.search(r'continue the (?:sequence|pattern|series)', stem.lower()) or
            re.search(r'what (?:number|is) (?:next|missing)', stem.lower())
        )

        if not is_pattern:
            continue

        # Extract numbers from stem
        stem_numbers = re.findall(r'\d+', stem)

        if len(stem_numbers) < 3:
            continue

        # Check if visual alt just shows the same numbers
        alt_numbers = re.findall(r'\d+', alt)

        # If alt text contains "Number pattern:" and lists the same numbers, it's redundant
        is_redundant = False

        if 'number pattern' in alt.lower() or 'pattern' in alt.lower():
            # Check if alt numbers are subset of stem numbers
            if set(alt_numbers).issubset(set(stem_numbers)) or set(stem_numbers).issubset(set(alt_numbers)):
                is_redundant = True

        # Also flag if alt just says "Number pattern: X, Y, Z with next value to find"
        if re.search(r'number pattern.*with next value', alt.lower()):
            is_redundant = True

        if is_redundant:
            findings.append({
                'id': q['id'],
                'stem': stem,
                'visual_svg': visual,
                'visual_alt': alt,
                'stem_numbers': stem_numbers,
                'source': q['_source_file'],
                'tags': tags,
            })

    return findings


def main():
    print("=" * 80)
    print("KIWIMATH CONTENT QA SCAN")
    print("=" * 80)

    print("\nLoading all questions...")
    questions = load_all_questions()
    print(f"Total questions loaded: {len(questions)}")

    # Issue 1: Visual-Stem Mismatches
    print("\n" + "=" * 80)
    print("ISSUE 1: VISUAL-STEM MISMATCHES (arithmetic operation contradictions)")
    print("=" * 80)
    mismatches = check_visual_stem_mismatch(questions)
    if mismatches:
        print(f"\nFound {len(mismatches)} potential mismatches:\n")
        for m in mismatches:
            print(f"  ID: {m['id']}")
            print(f"  File: {m['source']}")
            print(f"  Stem: {m['stem']}")
            print(f"  Visual Alt: {m['visual_alt']}")
            print(f"  Stem operation: {m.get('stem_operation','?')}")
            print(f"  Visual operation: {m.get('visual_operation','?')}")
            print(f"  Tags: {m.get('tags','')}")
            print()
    else:
        print("\n  No clear visual-stem arithmetic mismatches found.")
        print("  (Note: Some mismatches may only be detectable by inspecting actual SVG files)")

    # Issue 2: Chikoo prefix errors
    print("\n" + "=" * 80)
    print("ISSUE 2: 'CHIKOO' PREFIX QUESTIONS WITH ENGLISH ERRORS")
    print("=" * 80)
    chikoo = check_chikoo_errors(questions)
    errors_only = [c for c in chikoo if c['issues'] and c['issues'] != ['Generic filler prefix (review for relevance)']]
    filler_only = [c for c in chikoo if c['issues'] == ['Generic filler prefix (review for relevance)']]

    print(f"\nTotal Chikoo questions: {len(chikoo)}")
    print(f"Questions with grammatical issues: {len(errors_only)}")
    print(f"Questions with generic filler prefix (review): {len(filler_only)}")

    if errors_only:
        print(f"\n--- Questions with grammatical errors ---\n")
        for c in errors_only:
            print(f"  ID: {c['id']}")
            print(f"  File: {c['source']}")
            print(f"  Stem: {c['stem']}")
            print(f"  Issues: {c['issues']}")
            print()

    if filler_only:
        print(f"\n--- Questions with generic filler prefix (first 20) ---\n")
        for c in filler_only[:20]:
            print(f"  ID: {c['id']}")
            print(f"  Stem: {c['stem'][:100]}...")
            print()

    # Issue 3: Pattern questions with unnecessary visuals
    print("\n" + "=" * 80)
    print("ISSUE 3: PATTERN QUESTIONS WITH REDUNDANT VISUALS")
    print("=" * 80)
    patterns = check_pattern_unnecessary_visuals(questions)
    print(f"\nFound {len(patterns)} pattern questions with redundant visuals:\n")
    for p in patterns[:30]:
        print(f"  ID: {p['id']}")
        print(f"  File: {p['source']}")
        print(f"  Stem: {p['stem'][:90]}")
        print(f"  Visual Alt: {p['visual_alt']}")
        print()
    if len(patterns) > 30:
        print(f"  ... and {len(patterns) - 30} more.")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Total questions scanned: {len(questions)}")
    print(f"  Issue 1 - Visual-stem mismatches: {len(mismatches)}")
    print(f"  Issue 2 - Chikoo grammar errors: {len(errors_only)}")
    print(f"  Issue 2 - Chikoo filler prefixes: {len(filler_only)}")
    print(f"  Issue 3 - Redundant pattern visuals: {len(patterns)}")
    print()


if __name__ == '__main__':
    main()
