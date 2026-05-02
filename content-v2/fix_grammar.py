#!/usr/bin/env python3
"""
Fix article (a/an) grammar errors in Grade 1 content JSON files.

Rules:
- "a" before vowel sounds (a, e, i, o, u) -> "an"
- "an" before consonant sounds -> "a"

Special cases handled:
- "L-shape" -> "an L-shape" (L = "el", vowel sound)
- Pattern names like "AB", "ABC" -> "an AB pattern" (A = "ay", vowel sound)
- "A is a pencil" -> NOT an article, it's a label (skipped)
- "statement A is true" -> NOT an article, it's a label (skipped)
- Words starting with 'u' making "yoo" sound (uniform, unit, etc.) -> use "a"
- "ones" starts with "w" sound -> "a ones place" is correct
- "NON-square" -> "a NON-square" (NON is a word, not an abbreviation)

Usage:
  python3 fix_grammar.py          # Fix errors in place
  python3 fix_grammar.py --dry    # Report only, don't modify files
"""

import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Files to scan
FILES_TO_SCAN = [
    os.path.join(BASE_DIR, "ncert-curriculum/grade1/questions.json"),
    os.path.join(BASE_DIR, "icse-curriculum/grade1/icse_g1_questions.json"),
    os.path.join(BASE_DIR, "igcse-curriculum/grade1/igcse_grade1.json"),
    os.path.join(BASE_DIR, "singapore-curriculum/grade1/singapore_g1.json"),
    os.path.join(BASE_DIR, "us-common-core/grade1/uscc_g1_questions.json"),
    os.path.join(BASE_DIR, "topic-1-counting/questions.json"),
    os.path.join(BASE_DIR, "topic-2-arithmetic/questions.json"),
    os.path.join(BASE_DIR, "topic-3-patterns/questions.json"),
    os.path.join(BASE_DIR, "topic-4-logic/questions.json"),
    os.path.join(BASE_DIR, "topic-5-spatial/questions.json"),
    os.path.join(BASE_DIR, "topic-6-shapes/questions.json"),
    os.path.join(BASE_DIR, "topic-7-word-problems/questions.json"),
    os.path.join(BASE_DIR, "topic-8-puzzles/questions.json"),
]

# Words that start with a vowel letter but have a consonant sound (use "a")
VOWEL_LETTER_CONSONANT_SOUND = {
    "uniform", "university", "unit", "units", "unique", "united", "unicorn",
    "universe", "usual", "usually", "use", "used", "useful", "user",
    "union", "universal", "one", "ones", "once",
}

# Words that start with a consonant letter but have a vowel sound (use "an")
CONSONANT_LETTER_VOWEL_SOUND = {
    "hour", "hours", "honest", "honestly", "honor", "honour", "heir",
}

# Single uppercase letters with vowel sounds (for abbreviations)
# A="ay", E="ee", F="ef", H="aitch", I="eye", L="el", M="em", N="en", O="oh", R="ar", S="es", X="ex"
VOWEL_SOUND_LETTERS = set("AEFHILMNORSX")


def should_use_an(word):
    """Determine if 'an' should be used before a word."""
    word_lower = word.lower()

    # Check special cases first
    if word_lower in VOWEL_LETTER_CONSONANT_SOUND:
        return False  # use "a"
    if word_lower in CONSONANT_LETTER_VOWEL_SOUND:
        return True  # use "an"

    # Handle abbreviations/pattern names like "AB", "ABC", "L-shape", "AAB"
    # But NOT actual words written in caps like "NON-square"
    if word[0].isupper() and len(word) >= 2:
        # Check if it looks like a short abbreviation (1-4 uppercase chars, optionally followed by -word)
        if re.match(r'^[A-Z]{1,4}(-[a-z]+)?$', word):
            base = word.split('-')[0]
            # If 3+ chars and contains vowels, it's likely a word not an abbreviation
            if len(base) >= 3 and any(c in 'AEIOU' for c in base):
                # It's a word like "NON" - use standard rules
                first_char = word[0].lower()
                return first_char in 'aeiou'
            # It's an abbreviation like "AB", "L", "ABC" - use letter name sound
            return word[0] in VOWEL_SOUND_LETTERS

    # Standard rule: vowel letter = "an", consonant letter = "a"
    first_char = word[0].lower()
    if first_char in 'aeiou':
        return True  # use "an"
    return False  # use "a"


def fix_articles(text):
    """Fix a/an article errors in text. Returns (fixed_text, list_of_changes)."""
    changes = []

    # Pattern: match "a/an" followed by a word (with word boundary)
    pattern = r'\b([Aa]n?)\s+([A-Za-z][A-Za-z\-]*)'

    def replace_article(match):
        article = match.group(1)
        word = match.group(2)
        full_match = match.group(0)

        # Skip if the word after article is "is" and article is uppercase "A"
        # This means A is a label (like "A is a pencil", "A is heavier")
        if article == 'A' and word == 'is':
            return full_match

        # Skip single letter words that aren't real words (except 'I')
        if len(word) == 1 and word not in ('I', 'a'):
            return full_match

        # Skip if not followed by a real word
        if not word[0].isalpha():
            return full_match

        # Determine correct article
        use_an = should_use_an(word)

        # Determine current state
        current_is_an = article.lower() == 'an'

        if use_an == current_is_an:
            return full_match  # Already correct

        # Fix it
        if use_an:
            if article == 'A':
                new_article = 'An'
            else:
                new_article = 'an'
        else:
            if article == 'An':
                new_article = 'A'
            else:
                new_article = 'a'

        old_text = f"{article} {word}"
        new_text = f"{new_article} {word}"
        changes.append((old_text, new_text))
        return f"{new_article} {word}"

    fixed = re.sub(pattern, replace_article, text)
    return fixed, changes


def process_file(filepath, dry_run=False):
    """Process a single JSON file, fixing article errors."""
    if not os.path.exists(filepath):
        print(f"  SKIPPED (not found): {filepath}")
        return 0

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    fixed_content, changes = fix_articles(content)

    if changes:
        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)

        rel_path = os.path.relpath(filepath, BASE_DIR)
        print(f"\n  File: {rel_path}")
        print(f"  Fixes: {len(changes)}")
        for old, new in changes:
            print(f"    '{old}' -> '{new}'")
        return len(changes)

    return 0


def main():
    dry_run = '--dry' in sys.argv

    print("=" * 60)
    print("Article (a/an) Grammar Fix Script")
    if dry_run:
        print("MODE: Dry run (no files modified)")
    else:
        print("MODE: Fix in place")
    print("Scanning Grade 1 content files...")
    print("=" * 60)

    total_fixes = 0
    files_fixed = 0

    for filepath in FILES_TO_SCAN:
        fixes = process_file(filepath, dry_run)
        if fixes > 0:
            total_fixes += fixes
            files_fixed += 1

    print("\n" + "=" * 60)
    print(f"SUMMARY: {total_fixes} fixes across {files_fixed} files")
    print("=" * 60)

    return total_fixes


if __name__ == "__main__":
    main()
