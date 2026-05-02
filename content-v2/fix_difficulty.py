#!/usr/bin/env python3
"""
fix_difficulty.py - Identify and fix misclassified Grade 1 questions.

Scans Olympiad topic files (T1-T8) for questions with difficulty_score 1-50
that contain content too advanced for Grade 1 (ages 5-6), and bumps them
to an appropriate difficulty band.

Difficulty bands:
  1-50   = Grade 1
  51-100 = Grade 2
  101-150 = Grade 3
  151-200 = Grade 4
  201-250 = Grade 5
  251-300 = Grade 6

Rules for bumping:
  - Numbers 100-999 in stem -> Grade 2 (difficulty 51-100)
  - Numbers 1000+, multiplication, division -> Grade 3 (difficulty 101-150)
  - Angles, fractions, decimals, percentages -> Grade 4 (difficulty 151-200)
"""

import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOPIC_DIRS = [
    "topic-1-counting",
    "topic-2-arithmetic",
    "topic-3-patterns",
    "topic-4-logic",
    "topic-5-spatial",
    "topic-6-shapes",
    "topic-7-word-problems",
    "topic-8-puzzles",
]

# Keywords that indicate Grade 4+ content (angles, fractions, decimals, percentages)
G4_KEYWORDS = re.compile(
    r'\b(angle|angles|degree|degrees|protractor|fraction|fractions|decimal|decimals|'
    r'percentage|percentages|percent|numerator|denominator|improper\s+fraction|'
    r'mixed\s+number|acute|obtuse|reflex|right\s+angle)\b|°',
    re.IGNORECASE
)

# Keywords that indicate Grade 3 content (multiplication, division)
G3_KEYWORDS = re.compile(
    r'\b(multiply|multiplied|multiplication|times|product|divide|divided|division|'
    r'quotient|remainder|factor|factors|multiple|multiples)\b|[×÷]',
    re.IGNORECASE
)

# Pattern to find numbers in the stem (excluding question IDs like T1-001)
NUMBER_PATTERN = re.compile(r'(?<![A-Z]-)(?<![A-Z]\d)\b(\d+)\b')

# Pattern for question IDs to exclude from number scanning
QID_PATTERN = re.compile(r'T\d+-\d+')


def extract_numbers_from_stem(stem):
    """Extract all numbers from the stem, excluding question ID patterns."""
    # Remove question ID patterns first
    cleaned = QID_PATTERN.sub('', stem)
    numbers = [int(m.group(1)) for m in NUMBER_PATTERN.finditer(cleaned)]
    return numbers


def classify_misclassification(question):
    """
    Check if a G1 question (difficulty 1-50) is misclassified.

    Returns:
        None if correctly classified
        (new_difficulty, reason) if misclassified
    """
    stem = question.get("stem", "")
    choices = question.get("choices", [])

    # Combine stem and choices for analysis
    full_text = stem + " " + " ".join(str(c) for c in choices)

    # Check Grade 4 keywords first (highest bump)
    g4_match = G4_KEYWORDS.search(full_text)
    if g4_match:
        # Bump to Grade 4 band: 151-200
        # Place proportionally within band based on original score
        orig = question.get("difficulty_score", 25)
        new_diff = 151 + int((orig / 50.0) * 49)
        new_diff = min(new_diff, 200)
        return (new_diff, f"G4 content detected: '{g4_match.group()}'")

    # Check Grade 3 keywords (multiplication/division)
    g3_match = G3_KEYWORDS.search(full_text)
    if g3_match:
        orig = question.get("difficulty_score", 25)
        new_diff = 101 + int((orig / 50.0) * 49)
        new_diff = min(new_diff, 150)
        return (new_diff, f"G3 content detected: '{g3_match.group()}'")

    # Check numbers in the stem and choices
    numbers = extract_numbers_from_stem(full_text)

    if numbers:
        max_num = max(numbers)

        if max_num >= 1000:
            # Numbers 1000+ -> Grade 3
            orig = question.get("difficulty_score", 25)
            new_diff = 101 + int((orig / 50.0) * 49)
            new_diff = min(new_diff, 150)
            return (new_diff, f"Large number detected: {max_num} (>=1000)")

        elif max_num > 100:
            # Numbers 101-999 -> Grade 2
            orig = question.get("difficulty_score", 25)
            new_diff = 51 + int((orig / 50.0) * 49)
            new_diff = min(new_diff, 100)
            return (new_diff, f"Medium number detected: {max_num} (101-999)")

    return None


def process_topic(topic_dir):
    """Process a single topic's questions.json file."""
    filepath = os.path.join(BASE_DIR, topic_dir, "questions.json")
    if not os.path.exists(filepath):
        print(f"  [SKIP] {filepath} not found")
        return []

    with open(filepath, "r") as f:
        data = json.load(f)

    questions = data.get("questions", [])
    changes = []

    for q in questions:
        diff = q.get("difficulty_score", 0)
        if diff < 1 or diff > 50:
            continue  # Only check G1 range

        result = classify_misclassification(q)
        if result:
            new_diff, reason = result
            old_diff = q["difficulty_score"]
            q["difficulty_score"] = new_diff
            changes.append({
                "id": q.get("id", "unknown"),
                "topic": topic_dir,
                "old_difficulty": old_diff,
                "new_difficulty": new_diff,
                "reason": reason,
                "stem_preview": q.get("stem", "")[:80],
            })

    if changes:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    return changes


def main():
    print("=" * 70)
    print("Kiwimath Grade 1 Difficulty Misclassification Fix")
    print("=" * 70)
    print()

    all_changes = []

    for topic_dir in TOPIC_DIRS:
        print(f"Scanning {topic_dir}...")
        changes = process_topic(topic_dir)
        all_changes.extend(changes)
        if changes:
            print(f"  Found {len(changes)} misclassified question(s)")
        else:
            print(f"  No issues found")

    print()
    print("=" * 70)
    print(f"SUMMARY: {len(all_changes)} questions reclassified")
    print("=" * 70)

    if all_changes:
        print()
        print(f"{'ID':<10} {'Old':<5} {'New':<5} {'Reason'}")
        print("-" * 70)
        for c in all_changes:
            print(f"{c['id']:<10} {c['old_difficulty']:<5} {c['new_difficulty']:<5} {c['reason']}")

        print()
        print("Breakdown by bump target:")
        g2_bumps = [c for c in all_changes if 51 <= c['new_difficulty'] <= 100]
        g3_bumps = [c for c in all_changes if 101 <= c['new_difficulty'] <= 150]
        g4_bumps = [c for c in all_changes if 151 <= c['new_difficulty'] <= 200]
        print(f"  -> Grade 2 (51-100):  {len(g2_bumps)} questions")
        print(f"  -> Grade 3 (101-150): {len(g3_bumps)} questions")
        print(f"  -> Grade 4 (151-200): {len(g4_bumps)} questions")

        print()
        print("Breakdown by topic:")
        from collections import Counter
        topic_counts = Counter(c['topic'] for c in all_changes)
        for topic, count in sorted(topic_counts.items()):
            print(f"  {topic}: {count}")

    return len(all_changes)


if __name__ == "__main__":
    n = main()
    sys.exit(0)
