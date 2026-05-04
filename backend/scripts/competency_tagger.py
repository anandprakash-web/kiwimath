#!/usr/bin/env python3
"""
Competency Taxonomy Tagger — Classify all questions as Knowing/Applying/Reasoning.

Based on the Vedantu Learning Outcomes framework (aligned with TIMSS/NCERT):
  K (Knowing)    — Recall, recognize, compute. Direct calculation or fact retrieval.
  A (Applying)   — Use known procedures in familiar contexts. Word problems, multi-step.
  R (Reasoning)  — Analyze, justify, generalize. Unfamiliar contexts, non-routine problems.

Classification uses a multi-signal approach:
  1. Stem language analysis (strongest signal)
  2. Difficulty tier mapping (supporting signal)
  3. Tag-based heuristics (supporting signal)
  4. Question structure (MCQ vs open-ended, number of steps)

Usage:
  python competency_tagger.py                    # Tag all questions
  python competency_tagger.py --dry-run          # Preview without writing
  python competency_tagger.py --stats            # Show distribution only
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Competency classification rules
# ---------------------------------------------------------------------------

# Stem patterns that strongly indicate each competency level
KNOWING_PATTERNS = [
    r'\bwhat is\b.*\+',
    r'\bwhat is\b.*\-',
    r'\bwhat is\b.*[×x✕]\b',
    r'\bwhat is\b.*÷',
    r'\bcalculate\b',
    r'\bcompute\b',
    r'\bcount\b.*how many',
    r'\bhow many\b.*(?:are there|in all|total|altogether)',
    r'\bname the\b',
    r'\bidentify\b',
    r'\brecognize\b',
    r'\bwhat number\b',
    r'\bwhat comes\b',
    r'\bfill in\b',
    r'\bcomplete the\b.*(?:sequence|pattern|series)',
    r'\bwhat is the (?:sum|difference|product|quotient)\b',
    r'\bwhat is the value\b',
    r'\bsolve\b.*=',
    r'\bfind\b.*\+',
    r'\bfind\b.*\-',
    r'\bsimplify\b',
    r'\breduce\b',
    r'\bwrite\b.*(?:number|numeral|digit)',
    r'\bread the\b.*(?:number|time|clock)',
    r'\btell the time\b',
    r'\bwhat shape\b',
    r'\bwhich shape\b',
    r'\bmatch\b',
    r'\bselect\b.*(?:correct|right|answer)',
    r'\bwhich of\b.*(?:is correct|is right|equals)',
    r'\bconvert\b',
]

APPLYING_PATTERNS = [
    r'\bhow many\b.*(?:left|remaining|more|fewer|less)',
    r'\bhow much\b.*(?:change|cost|total|save|spend|pay|left|remaining)',
    r'\bhow (?:far|long|tall|wide|heavy|deep)\b',
    r'\bword problem\b',
    r'\bstory\b',
    r'\bif\b.*\bthen\b',
    r'\bif\b.*\bhow\b',
    r'\bgives away\b',
    r'\bbuys\b',
    r'\bsells\b',
    r'\bears\b',
    r'\bspends?\b',
    r'\bsaves?\b',
    r'\bshares?\b.*(?:equal|friend|among)',
    r'\bdivides?\b.*(?:equal|friend|among|group)',
    r'\bdistributes?\b',
    r'\bfind the (?:area|perimeter|volume|circumference)\b',
    r'\bmeasure\b',
    r'\bestimate\b',
    r'\bround\b.*(?:nearest|to the)',
    r'\barrange\b.*order',
    r'\bsort\b',
    r'\bcompare\b',
    r'\bgreater\b.*\bless\b',
    r'\bwhat fraction\b',
    r'\bwhat percent\b',
    r'\bfind the\b.*(?:missing|unknown)',
    r'\b(?:walks?|runs?|drives?|travels?)\b.*(?:km|miles?|meters?|minutes?|hours?)',
    r'\brecipe\b',
    r'\bprice\b',
    r'\bdiscount\b',
    r'\bprofit\b',
    r'\bloss\b',
    r'\binterest\b',
    r'\bratio\b',
    r'\bproportion\b',
    r'\bscale\b',
    r'\bmap\b.*(?:distance|scale)',
    r'\bgraph\b.*(?:read|show|represent)',
    r'\btable\b.*(?:read|show|complete)',
    r'\bchart\b.*(?:read|show|bar|pie)',
    r'\bdata\b.*(?:read|show|table|chart)',
]

REASONING_PATTERNS = [
    r'\bwhy\b',
    r'\bexplain\b',
    r'\bjustify\b',
    r'\bprove\b',
    r'\bwhat (?:if|would happen|happens when)\b',
    r'\bwhich (?:statement|claim)\b.*(?:true|false|correct|incorrect)',
    r'\balways\b.*(?:true|false)',
    r'\bnever\b.*(?:true|false)',
    r'\bsometimes\b.*(?:true|false)',
    r'\bmust be\b',
    r'\bcannot be\b',
    r'\bimpossible\b',
    r'\bpossible\b.*(?:values?|outcomes?|answers?)',
    r'\bhow many (?:ways|different|possible)\b',
    r'\bfind (?:all|every)\b.*(?:possible|solutions?|ways?|combinations?)',
    r'\bpattern\b.*(?:rule|next|predict|continue|describe)',
    r'\bwhat is the rule\b',
    r'\bpredict\b',
    r'\bgeneralize\b',
    r'\bwhich\b.*(?:does not belong|is different|is the odd one)',
    r'\bsmallest\b.*(?:number|value|sum|difference).*(?:possible|can)',
    r'\blargest\b.*(?:number|value|sum|difference).*(?:possible|can)',
    r'\bmaximum\b',
    r'\bminimum\b',
    r'\boptimize\b',
    r'\bbest\b.*(?:strategy|way|method|approach)',
    r'\blogic\b',
    r'\bpuzzle\b',
    r'\bif.*and.*then\b',
    r'\bdeduction\b',
    r'\bconclusion\b',
    r'\binfer\b',
    r'\brelationship\b.*(?:between|among)',
    r'\bcompare\b.*(?:strategies|methods|approaches)',
    r'\berror\b.*(?:find|identify|correct|mistake)',
    r'\bmistake\b',
    r'\bwhat went wrong\b',
    r'\bwhat is wrong\b',
    r'\bcounter.?example\b',
    r'\bdisprove\b',
]

# Tags that suggest competency level
KNOWING_TAGS = {
    'addition', 'subtraction', 'multiplication', 'division',
    'counting', 'number-recognition', 'place-value', 'skip-counting',
    'number-names', 'before-after', 'comparison', 'ordering',
    'fractions-basic', 'time-reading', 'money-identification',
    'shapes-identify', 'measurement-units', 'conversion',
}

APPLYING_TAGS = {
    'word-problem', 'story-problem', 'real-world', 'application',
    'missing-number', 'area', 'perimeter', 'volume', 'measurement',
    'money-calculation', 'time-calculation', 'data-reading',
    'graph-reading', 'estimation', 'rounding', 'fractions-operations',
    'decimals-operations', 'percentage-calculation', 'ratio',
    'proportion', 'geometry-calculation', 'multi-step',
}

REASONING_TAGS = {
    'pattern-rule', 'pattern-extension', 'logic', 'puzzle',
    'deduction', 'spatial-reasoning', 'symmetry', 'transformation',
    'proof', 'error-analysis', 'always-sometimes-never',
    'optimization', 'strategy', 'non-routine', 'olympiad',
    'advanced', 'challenge', 'critical-thinking',
}


def classify_competency(question: Dict) -> Tuple[str, float]:
    """Classify a question as K (Knowing), A (Applying), or R (Reasoning).

    Returns (competency, confidence) where confidence is 0.0-1.0.
    """
    stem = (question.get('stem') or question.get('original_stem') or '').lower()
    tags = set(t.lower() for t in (question.get('tags') or []))
    difficulty = question.get('difficulty_score', 0)
    difficulty_tier = (question.get('difficulty_tier') or '').lower()
    choices = question.get('choices') or []
    solution_steps = question.get('solution_steps') or []

    scores = {'K': 0.0, 'A': 0.0, 'R': 0.0}

    # 1. Stem pattern matching (strongest signal, weight=3)
    for pattern in KNOWING_PATTERNS:
        if re.search(pattern, stem, re.IGNORECASE):
            scores['K'] += 3.0
            break  # One match is enough per category

    for pattern in APPLYING_PATTERNS:
        if re.search(pattern, stem, re.IGNORECASE):
            scores['A'] += 3.0
            break

    for pattern in REASONING_PATTERNS:
        if re.search(pattern, stem, re.IGNORECASE):
            scores['R'] += 3.0
            break

    # 2. Tag matching (weight=2)
    tag_overlap_k = tags & KNOWING_TAGS
    tag_overlap_a = tags & APPLYING_TAGS
    tag_overlap_r = tags & REASONING_TAGS

    scores['K'] += len(tag_overlap_k) * 2.0
    scores['A'] += len(tag_overlap_a) * 2.0
    scores['R'] += len(tag_overlap_r) * 2.0

    # 3. Difficulty tier as supporting signal (weight=1)
    if difficulty_tier in ('easy',):
        scores['K'] += 1.5
    elif difficulty_tier in ('medium',):
        scores['A'] += 1.0
    elif difficulty_tier in ('hard', 'advanced', 'expert'):
        scores['R'] += 1.0
        scores['A'] += 0.5

    # 4. Difficulty score ranges
    if difficulty <= 50:
        scores['K'] += 1.0
    elif difficulty <= 150:
        scores['A'] += 0.5
    elif difficulty > 200:
        scores['R'] += 0.5

    # 5. Story/context detection (word problems → Applying)
    story_indicators = ['has', 'gives', 'buys', 'sells', 'walks', 'runs',
                        'shares', 'earns', 'saves', 'collects', 'bakes',
                        'plants', 'reads', 'makes', 'builds', 'friend',
                        'shop', 'store', 'market', 'school', 'garden']
    story_count = sum(1 for w in story_indicators if w in stem)
    if story_count >= 2:
        scores['A'] += 2.0

    # 6. Multi-step detection (more steps → higher cognitive demand)
    if len(solution_steps) >= 3:
        scores['A'] += 1.0
    if len(solution_steps) >= 5:
        scores['R'] += 1.0

    # 7. Number of operations in stem (multiple ops → Applying/Reasoning)
    ops = len(re.findall(r'[+\-×÷*/]', stem))
    if ops >= 2:
        scores['A'] += 1.0
    if ops >= 3:
        scores['R'] += 0.5

    # 8. Pure arithmetic without context → Knowing
    is_pure_arithmetic = bool(re.match(
        r'^(?:what is |find |solve |calculate )?[\d\s+\-×÷x*/=().,]+\s*\??$',
        stem.strip(), re.IGNORECASE
    ))
    if is_pure_arithmetic:
        scores['K'] += 4.0
        scores['A'] -= 1.0

    # Default: if no signals at all, use difficulty as primary guide
    if max(scores.values()) == 0:
        if difficulty <= 80:
            scores['K'] = 1.0
        elif difficulty <= 180:
            scores['A'] = 1.0
        else:
            scores['R'] = 1.0

    # Pick winner
    winner = max(scores, key=scores.get)
    total = sum(scores.values()) or 1
    confidence = scores[winner] / total

    return winner, round(confidence, 3)


# ---------------------------------------------------------------------------
# Competency descriptions per grade band
# ---------------------------------------------------------------------------

COMPETENCY_DESCRIPTIONS = {
    'K': {
        'name': 'Knowing',
        'short': 'Recall & Compute',
        'grade_1_2': 'Can recognize numbers, count objects, and do basic calculations.',
        'grade_3_4': 'Can recall math facts, identify shapes, and perform standard operations.',
        'grade_5_6': 'Can recall formulas, execute procedures, and convert between representations.',
    },
    'A': {
        'name': 'Applying',
        'short': 'Use & Solve',
        'grade_1_2': 'Can use addition and subtraction to solve simple word problems.',
        'grade_3_4': 'Can apply math to familiar real-world problems with multiple steps.',
        'grade_5_6': 'Can model situations mathematically and solve multi-step problems.',
    },
    'R': {
        'name': 'Reasoning',
        'short': 'Analyze & Justify',
        'grade_1_2': 'Can spot patterns and explain simple mathematical relationships.',
        'grade_3_4': 'Can analyze problems, find patterns, and explain their thinking.',
        'grade_5_6': 'Can justify solutions, generalize patterns, and solve non-routine problems.',
    },
}


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_file(filepath: Path, dry_run: bool = False) -> Dict:
    """Process a single content JSON file, adding competency tags."""
    data = json.loads(filepath.read_text())
    questions = data.get('questions', data) if isinstance(data, dict) else data
    if not isinstance(questions, list):
        return {'file': str(filepath), 'total': 0, 'tagged': 0, 'distribution': {}}

    stats = Counter()
    tagged = 0

    for q in questions:
        competency, confidence = classify_competency(q)
        stats[competency] += 1
        tagged += 1

        if not dry_run:
            q['competency_level'] = competency
            q['competency_confidence'] = confidence
            q['competency_name'] = COMPETENCY_DESCRIPTIONS[competency]['name']

    if not dry_run and tagged > 0:
        if isinstance(data, dict):
            data['questions'] = questions
            # Add competency distribution to file metadata
            data['competency_distribution'] = dict(stats)
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    return {
        'file': filepath.name,
        'total': len(questions),
        'tagged': tagged,
        'distribution': dict(stats),
    }


def main():
    parser = argparse.ArgumentParser(description="Competency Taxonomy Tagger")
    parser.add_argument('--content-dir', type=Path,
                        default=Path(__file__).resolve().parent.parent.parent / 'content-v2')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    parser.add_argument('--stats', action='store_true', help='Show distribution only')
    args = parser.parse_args()

    content_dir = args.content_dir
    if not content_dir.exists():
        print(f"Content directory not found: {content_dir}")
        sys.exit(1)

    all_stats = Counter()
    file_results = []

    # Process all JSON files recursively
    json_files = sorted(content_dir.rglob('*.json'))
    json_files = [f for f in json_files
                  if 'visual_registry' not in f.name
                  and 'manifest' not in f.name]

    for filepath in json_files:
        result = process_file(filepath, dry_run=args.dry_run or args.stats)
        if result['tagged'] > 0:
            file_results.append(result)
            for k, v in result['distribution'].items():
                all_stats[k] += v

    # Print results
    total = sum(all_stats.values())
    print(f"\n{'=' * 60}")
    print(f"Competency Taxonomy Tagging {'(DRY RUN)' if args.dry_run or args.stats else 'COMPLETE'}")
    print(f"{'=' * 60}")
    print(f"Total questions tagged: {total}")
    print(f"\nDistribution:")
    for level in ['K', 'A', 'R']:
        count = all_stats.get(level, 0)
        pct = (count / total * 100) if total else 0
        desc = COMPETENCY_DESCRIPTIONS[level]
        bar = '█' * int(pct / 2)
        print(f"  {level} ({desc['name']:10s}): {count:5d} ({pct:5.1f}%) {bar}")

    print(f"\nPer-file breakdown:")
    for r in file_results:
        k = r['distribution'].get('K', 0)
        a = r['distribution'].get('A', 0)
        reas = r['distribution'].get('R', 0)
        print(f"  {r['file']:40s}  K={k:4d}  A={a:4d}  R={reas:4d}  total={r['total']}")

    if not args.dry_run and not args.stats:
        print(f"\nAll {total} questions tagged with competency_level field.")


if __name__ == '__main__':
    main()
