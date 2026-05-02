#!/usr/bin/env python3
"""
Fix content issues in Kiwimath question bank.
- Fix 1: Remove redundant visuals from pattern/number-sequence questions
- Fix 2: Fix Chikoo prefix issues (duplicated phrases, mismatched prefixes, grammar)
- Fix 3: Fix specific questions T1-060 and T1-037
"""

import json
import glob
import re
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# Collect all JSON files
def get_all_json_files():
    patterns = [
        os.path.join(BASE, "topic-*", "*.json"),
        os.path.join(BASE, "ncert-curriculum", "grade*", "*.json"),
        os.path.join(BASE, "icse-curriculum", "grade*", "*.json"),
        os.path.join(BASE, "igcse-curriculum", "grade*", "*.json"),
    ]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    # Deduplicate
    return sorted(set(files))


def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def get_questions(data):
    """Return list of questions from either dict or list format."""
    if isinstance(data, dict):
        return data.get("questions", [])
    elif isinstance(data, list):
        return data
    return []


# ============ FIX 1: Remove redundant visuals from pattern questions ============

def has_number_sequence_with_placeholder(stem):
    """Check if stem contains a number sequence with ? placeholder."""
    # Match patterns like "5, 9, 13, 17, ?" or "3, 6, 10, 15, 21"
    return bool(re.search(r'\d+\s*,\s*\d+\s*,\s*\d+.*\?', stem))


def visual_alt_is_redundant(visual_alt):
    """Check if visual_alt just describes a number pattern."""
    if not visual_alt:
        return False
    alt_lower = visual_alt.lower()
    keywords = ["number pattern", "number sequence", "sequence", "pattern:"]
    # Must contain pattern/sequence AND numbers
    has_keyword = any(k in alt_lower for k in keywords)
    has_numbers = bool(re.search(r'\d+', alt_lower))
    return has_keyword and has_numbers


def fix_redundant_visuals(question):
    """Fix 1: Remove redundant visuals from pattern/number-sequence questions."""
    if not question.get("visual_svg"):
        return False

    stem = question.get("stem", "")
    tags = question.get("tags", [])
    visual_alt = question.get("visual_alt", "") or ""

    # Check if it's a pattern/sequence question
    is_pattern_q = (
        has_number_sequence_with_placeholder(stem) or
        "patterns" in tags or
        "pattern" in tags
    )

    if not is_pattern_q:
        return False

    # Check if the visual alt suggests it just shows numbers
    alt_lower = visual_alt.lower()
    redundant_keywords = ["pattern", "sequence", "number"]
    if any(k in alt_lower for k in redundant_keywords):
        question["visual_svg"] = None
        question["visual_alt"] = None
        return True

    return False


# ============ FIX 2: Fix Chikoo prefix issues ============

def fix_duplicated_phrases(stem):
    """Fix 'what comes next: What comes next' and similar duplications."""
    # "figuring out what comes next: What comes next:" -> "figuring out what comes next:"
    stem = re.sub(
        r'(figuring out what comes next)[:\s]+What comes next:',
        r'\1:',
        stem,
        flags=re.IGNORECASE
    )
    # "find the pattern: What comes next:" -> "find the pattern:"
    stem = re.sub(
        r'(find the pattern)[:\s]+What comes next:',
        r'\1:',
        stem,
        flags=re.IGNORECASE
    )
    # "Find the pattern: Find the pattern:" -> "Find the pattern:"
    stem = re.sub(
        r'(Find the pattern)[:\s]+Find the pattern:',
        r'\1:',
        stem,
        flags=re.IGNORECASE
    )
    # "What comes next: What comes next:" -> "What comes next:"
    stem = re.sub(
        r'(What comes next)[:\s]+What comes next:',
        r'\1:',
        stem,
        flags=re.IGNORECASE
    )
    return stem


def fix_party_duplication(stem):
    """Fix 'at a party, 4 friends meet at a party' -> 'At a party, 4 friends meet'."""
    stem = re.sub(
        r'[Aa]t a party,\s*(\d+)\s*friends meet at a party',
        r'At a party, \1 friends meet',
        stem
    )
    return stem


def fix_grammar(stem):
    """Fix grammar issues like 'An watermelon' -> 'A watermelon'."""
    stem = re.sub(r'\bAn watermelon\b', 'A watermelon', stem)
    stem = re.sub(r'\ban watermelon\b', 'a watermelon', stem)
    return stem


def fix_mismatched_chikoo_prefix(question):
    """Remove Chikoo prefix when it mentions items unrelated to the question."""
    stem = question.get("stem", "")
    m = re.match(
        r'Chikoo found some (\w+) and wants to count them\.\s*(.*)',
        stem,
        re.DOTALL
    )
    if not m:
        return stem

    mentioned_item = m.group(1).lower()
    rest = m.group(2)

    # Check if the mentioned item appears in the rest of the question
    if mentioned_item.lower() not in rest.lower():
        # Mismatch - remove the prefix entirely
        return rest
    return stem


def fix_chikoo_issues(question):
    """Fix 2: Fix all Chikoo prefix issues."""
    stem = question.get("stem", "")
    original = stem

    # Fix duplicated phrases
    stem = fix_duplicated_phrases(stem)

    # Fix party duplication
    stem = fix_party_duplication(stem)

    # Fix grammar
    stem = fix_grammar(stem)

    # Fix mismatched Chikoo prefix (only for "found some X" pattern)
    question["stem"] = stem
    stem = fix_mismatched_chikoo_prefix(question)

    question["stem"] = stem
    return stem != original


# ============ FIX 3: Specific question fixes ============

def fix_specific_questions(question):
    """Fix specific known issues with T1-060 and T1-037."""
    changed = False
    qid = question.get("id", "")

    if qid == "T1-060":
        # Visual about pencils doesn't match handshake problem
        if question.get("visual_svg"):
            question["visual_svg"] = None
            question["visual_alt"] = None
            changed = True

    if qid == "T1-037":
        # Strip irrelevant marbles prefix
        stem = question.get("stem", "")
        m = re.match(
            r'Chikoo found some marbles and wants to count them\.\s*(.*)',
            stem,
            re.DOTALL
        )
        if m:
            question["stem"] = m.group(1)
            changed = True

    return changed


# ============ MAIN ============

def main():
    files = get_all_json_files()
    print(f"Found {len(files)} JSON files to process.\n")

    stats = {
        "fix1_redundant_visuals": 0,
        "fix2_chikoo_prefix": 0,
        "fix3_specific": 0,
        "files_modified": 0,
    }

    for filepath in files:
        try:
            data = load_json(filepath)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  SKIP (parse error): {filepath}: {e}")
            continue

        questions = get_questions(data)
        if not questions:
            continue

        file_changed = False

        for q in questions:
            if not isinstance(q, dict):
                continue

            # Fix 3 first (specific questions, before general fixes)
            if fix_specific_questions(q):
                stats["fix3_specific"] += 1
                file_changed = True

            # Fix 1: Redundant visuals
            if fix_redundant_visuals(q):
                stats["fix1_redundant_visuals"] += 1
                file_changed = True

            # Fix 2: Chikoo prefix issues
            if fix_chikoo_issues(q):
                stats["fix2_chikoo_prefix"] += 1
                file_changed = True

        if file_changed:
            save_json(filepath, data)
            stats["files_modified"] += 1

    # Print summary
    print("=" * 60)
    print("CONTENT FIX SUMMARY")
    print("=" * 60)
    print(f"Files scanned:                  {len(files)}")
    print(f"Files modified:                 {stats['files_modified']}")
    print(f"Fix 1 - Redundant visuals:      {stats['fix1_redundant_visuals']} questions")
    print(f"Fix 2 - Chikoo prefix issues:   {stats['fix2_chikoo_prefix']} questions")
    print(f"Fix 3 - Specific fixes (T1-060, T1-037): {stats['fix3_specific']} questions")
    print(f"Total questions fixed:          {stats['fix1_redundant_visuals'] + stats['fix2_chikoo_prefix'] + stats['fix3_specific']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
