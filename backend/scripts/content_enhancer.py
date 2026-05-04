#!/usr/bin/env python3
"""
Content Enhancement Pipeline for Kiwimath
==========================================
Systematically improves question quality across all topic directories.

Usage:
    python content_enhancer.py --audit --all
    python content_enhancer.py --fix-modes --topic topic-1-counting
    python content_enhancer.py --add-why --fix-hints --dedup --all
    python content_enhancer.py --audit --fix-modes --add-why --fix-hints --dedup --all --dry-run
"""

import argparse
import json
import os
import re
import sys
import copy
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONTENT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "content-v2",
)
CONTENT_DIR = os.path.normpath(CONTENT_DIR)

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

# Canonical interaction mode
CANONICAL_MODE = "multiple_choice"

# Generic hint patterns (level_0) that add no pedagogical value
GENERIC_HINT_PATTERNS = [
    r"(?i)look at the problem carefully",
    r"(?i)read the (question|problem) (again|carefully)",
    r"(?i)think about (it|this)",
    r"(?i)try (again|harder)",
    r"(?i)take your time",
    r"(?i)don'?t rush",
    r"(?i)focus on the question",
    r"(?i)what do you think",
    r"(?i)^count (each|the|carefully)",
    r"(?i)^think carefully",
]

# Tags that indicate counting-type questions (valid for tap_to_count)
COUNTING_TAGS = {
    "counting", "count", "observation", "tally-charts", "tally",
    "count-objects", "how-many", "number-counting",
}


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def load_questions_file(filepath):
    """Load a JSON file and return (questions_list, file_format).
    file_format is 'dict' if wrapped in {topic, questions:[...]}, else 'list'.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data, "list", None
    elif isinstance(data, dict) and "questions" in data:
        return data["questions"], "dict", data
    else:
        return [], "unknown", data


def save_questions_file(filepath, questions, file_format, wrapper):
    """Write questions back in the original format."""
    if file_format == "list":
        data = questions
    elif file_format == "dict":
        wrapper = dict(wrapper)  # shallow copy
        wrapper["questions"] = questions
        wrapper["total_questions"] = len(questions)
        data = wrapper
    else:
        return  # skip unknown formats

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def iter_topic_files(topic_dir):
    """Yield (filepath, questions, file_format, wrapper) for every JSON file
    in a topic directory that contains questions."""
    if not os.path.isdir(topic_dir):
        return
    for fname in sorted(os.listdir(topic_dir)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(topic_dir, fname)
        if not os.path.isfile(fpath):
            continue
        questions, fmt, wrapper = load_questions_file(fpath)
        if questions:
            yield fpath, questions, fmt, wrapper


def get_topic_dirs(args):
    """Return list of topic directory paths based on CLI args."""
    if args.all:
        return [os.path.join(CONTENT_DIR, t) for t in TOPIC_DIRS]
    elif args.topic:
        td = os.path.join(CONTENT_DIR, args.topic)
        if not os.path.isdir(td):
            print(f"Error: topic directory not found: {td}", file=sys.stderr)
            sys.exit(1)
        return [td]
    else:
        print("Error: specify --topic <name> or --all", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def strip_numbers(text):
    """Replace all numbers with # for template matching."""
    return re.sub(r"\d+", "#", text)


def normalize_stem(stem):
    """Normalize a stem for near-duplicate detection."""
    s = stem.lower().strip()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return strip_numbers(s)


def is_generic_hint(text):
    """Check if hint text matches known generic patterns."""
    if not text:
        return False
    for pat in GENERIC_HINT_PATTERNS:
        if re.search(pat, text.strip()):
            return True
    return False


def detect_topic_from_tags(tags):
    """Infer the broad topic category from question tags."""
    if not tags:
        return "general"
    tag_set = set(t.lower() for t in tags)
    if tag_set & {"addition", "subtraction", "multiplication", "division",
                  "add", "subtract", "multiply", "divide", "arithmetic",
                  "missing-number"}:
        return "arithmetic"
    if tag_set & COUNTING_TAGS:
        return "counting"
    if tag_set & {"pattern", "patterns", "sequence", "series",
                  "number-pattern", "growing-pattern"}:
        return "patterns"
    if tag_set & {"shape", "shapes", "geometry", "polygon", "circle",
                  "triangle", "rectangle", "square", "3d-shapes"}:
        return "shapes"
    if tag_set & {"logic", "comparison", "ordering", "classify",
                  "odd-one-out", "sorting"}:
        return "logic"
    if tag_set & {"spatial", "direction", "left-right", "symmetry",
                  "reflection", "rotation", "position"}:
        return "spatial"
    if tag_set & {"word_problem", "word-problem", "story", "real-world"}:
        return "word_problems"
    if tag_set & {"puzzle", "riddle", "brain-teaser", "sudoku"}:
        return "puzzles"
    return "general"


def detect_topic_from_dir(topic_dir_name):
    """Map directory name to topic category."""
    mapping = {
        "topic-1-counting": "counting",
        "topic-2-arithmetic": "arithmetic",
        "topic-3-patterns": "patterns",
        "topic-4-logic": "logic",
        "topic-5-spatial": "spatial",
        "topic-6-shapes": "shapes",
        "topic-7-word-problems": "word_problems",
        "topic-8-puzzles": "puzzles",
    }
    return mapping.get(topic_dir_name, "general")


def hint_matches_topic(hint_text, topic_category):
    """Basic check: does hint text seem unrelated to the topic?"""
    if not hint_text or len(hint_text) < 10:
        return True  # too short to judge
    text = hint_text.lower()
    # Obvious mismatches
    mismatches = {
        "counting": ["multiply", "divide", "angle", "symmetry", "perimeter"],
        "arithmetic": ["symmetry", "reflection", "polygon", "classify"],
        "patterns": ["perimeter", "area", "symmetry"],
        "shapes": ["add", "subtract", "multiply", "divide", "tally"],
        "spatial": ["add", "subtract", "multiply", "tally"],
        "word_problems": [],
        "puzzles": [],
        "logic": [],
    }
    bad_words = mismatches.get(topic_category, [])
    for w in bad_words:
        if w in text and topic_category not in text:
            return False
    return True


def extract_operation_from_stem(stem):
    """Try to detect the math operation in a stem."""
    s = stem.lower()
    if "+" in stem or "add" in s or "plus" in s or "sum" in s:
        return "addition", "+"
    if "-" in stem or "subtract" in s or "minus" in s or "take away" in s:
        return "subtraction", "-"
    if "×" in stem or "x" in stem or "multipl" in s or "times" in s:
        return "multiplication", "×"
    if "÷" in stem or "/" in stem or "divid" in s or "share equally" in s:
        return "division", "÷"
    return None, None


def extract_numbers_from_stem(stem):
    """Extract all numbers from the stem."""
    return [int(x) for x in re.findall(r"\d+", stem)]


def is_counting_question(q):
    """Determine if a question is genuinely a counting question."""
    tags = set(t.lower() for t in (q.get("tags") or []))
    stem_lower = q.get("stem", "").lower()

    # Explicit counting tags
    if tags & COUNTING_TAGS:
        return True

    # Stem patterns that indicate counting
    counting_phrases = [
        "how many", "count the", "count each",
        "how much", "tally", "total number of",
    ]
    for phrase in counting_phrases:
        if phrase in stem_lower:
            return True

    return False


# ---------------------------------------------------------------------------
# 1. AUDIT
# ---------------------------------------------------------------------------

def run_audit(topic_dirs):
    """Scan all questions and produce a quality report."""
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {},
        "generic_hints": [],
        "missing_explanations": [],
        "near_duplicates": [],
        "mode_inconsistencies": [],
        "hint_topic_mismatches": [],
    }

    total_questions = 0
    generic_hint_count = 0
    missing_explanation_count = 0
    mode_inconsistency_count = 0
    hint_mismatch_count = 0

    # For dedup detection
    stem_templates = defaultdict(list)

    for td in topic_dirs:
        topic_name = os.path.basename(td)
        topic_cat = detect_topic_from_dir(topic_name)

        for fpath, questions, fmt, wrapper in iter_topic_files(td):
            fname = os.path.basename(fpath)
            for q in questions:
                if q.get("_deprecated"):
                    continue
                total_questions += 1
                qid = q.get("id", "unknown")

                # 1a. Generic hints
                hint = q.get("hint", {})
                level_0 = hint.get("level_0", "")
                if is_generic_hint(level_0):
                    generic_hint_count += 1
                    report["generic_hints"].append({
                        "id": qid,
                        "file": f"{topic_name}/{fname}",
                        "hint_level_0": level_0,
                    })

                # 1b. Missing correct-answer explanations
                diag = q.get("diagnostics", {})
                correct_idx = q.get("correct_answer")
                has_explanation = False
                if isinstance(diag, dict):
                    if "correct_explanation" in diag or "why" in diag:
                        has_explanation = True
                    # Also check if the correct index has an explanation
                    if str(correct_idx) in diag:
                        has_explanation = True  # at least there's a distractor msg
                        # But we specifically want correct_explanation
                        if "correct_explanation" not in diag:
                            has_explanation = False
                if not has_explanation:
                    missing_explanation_count += 1
                    report["missing_explanations"].append({
                        "id": qid,
                        "file": f"{topic_name}/{fname}",
                    })

                # 1c. Stem template for dedup
                norm = normalize_stem(q.get("stem", ""))
                stem_templates[norm].append({
                    "id": qid,
                    "file": f"{topic_name}/{fname}",
                    "difficulty_tier": q.get("difficulty_tier"),
                    "stem": q.get("stem", "")[:120],
                })

                # 1d. interaction_mode inconsistencies
                mode = q.get("interaction_mode", "")
                if mode == "mcq":
                    mode_inconsistency_count += 1
                    report["mode_inconsistencies"].append({
                        "id": qid,
                        "file": f"{topic_name}/{fname}",
                        "current_mode": mode,
                    })

                # 1e. Hint-topic mismatch
                for level_key in ["level_1", "level_2", "level_3"]:
                    h = hint.get(level_key, "")
                    if h and not hint_matches_topic(h, topic_cat):
                        hint_mismatch_count += 1
                        report["hint_topic_mismatches"].append({
                            "id": qid,
                            "file": f"{topic_name}/{fname}",
                            "level": level_key,
                            "hint_text": h[:120],
                            "expected_topic": topic_cat,
                        })
                        break  # one per question

    # 1c. Near-duplicates: groups with >3 questions sharing a template
    dup_groups = []
    for template, items in stem_templates.items():
        if len(items) > 3:
            dup_groups.append({
                "template": template[:120],
                "count": len(items),
                "questions": items[:10],  # sample
            })
    dup_groups.sort(key=lambda g: g["count"], reverse=True)
    report["near_duplicates"] = dup_groups

    report["summary"] = {
        "total_questions_scanned": total_questions,
        "generic_hints_count": generic_hint_count,
        "missing_explanations_count": missing_explanation_count,
        "near_duplicate_groups": len(dup_groups),
        "near_duplicate_questions": sum(g["count"] for g in dup_groups),
        "mode_inconsistencies_count": mode_inconsistency_count,
        "hint_topic_mismatches_count": hint_mismatch_count,
    }

    # Write report
    workspace = os.path.join(CONTENT_DIR, "_workspace")
    os.makedirs(workspace, exist_ok=True)
    report_path = os.path.join(workspace, "audit_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Print summary
    print("\n=== AUDIT REPORT ===")
    for k, v in report["summary"].items():
        label = k.replace("_", " ").title()
        print(f"  {label}: {v}")
    print(f"\n  Full report: {report_path}")
    return report


# ---------------------------------------------------------------------------
# 2. FIX INTERACTION MODES
# ---------------------------------------------------------------------------

def run_fix_modes(topic_dirs, dry_run=False):
    """Normalize interaction modes."""
    changes = 0
    tap_fixes = 0

    for td in topic_dirs:
        topic_name = os.path.basename(td)
        for fpath, questions, fmt, wrapper in iter_topic_files(td):
            modified = False
            for q in questions:
                if q.get("_deprecated"):
                    continue
                mode = q.get("interaction_mode", "")

                # Fix mcq -> multiple_choice
                if mode == "mcq":
                    q["interaction_mode"] = CANONICAL_MODE
                    changes += 1
                    modified = True

                # Fix tap_to_count on non-counting questions
                elif mode == "tap_to_count":
                    if not is_counting_question(q):
                        q["interaction_mode"] = CANONICAL_MODE
                        tap_fixes += 1
                        modified = True

            if modified and not dry_run:
                save_questions_file(fpath, questions, fmt, wrapper)

    print(f"\n=== FIX MODES ===")
    print(f"  mcq -> {CANONICAL_MODE}: {changes}")
    print(f"  tap_to_count -> {CANONICAL_MODE} (non-counting): {tap_fixes}")
    if dry_run:
        print("  (dry run — no files written)")
    return changes + tap_fixes


# ---------------------------------------------------------------------------
# 3. ADD CORRECT-ANSWER EXPLANATIONS
# ---------------------------------------------------------------------------

def generate_explanation(q, topic_category):
    """Generate a correct_explanation based on question content."""
    stem = q.get("stem", "")
    choices = q.get("choices", [])
    correct_idx = q.get("correct_answer", 0)
    correct_val = choices[correct_idx] if correct_idx < len(choices) else "?"
    tags = set(t.lower() for t in (q.get("tags") or []))
    numbers = extract_numbers_from_stem(stem)
    operation, op_sym = extract_operation_from_stem(stem)

    # Arithmetic
    if topic_category == "arithmetic" or operation:
        if operation and len(numbers) >= 2:
            n1, n2 = numbers[0], numbers[1]
            method_map = {
                "addition": f"add {n1} and {n2}",
                "subtraction": f"subtract {n2} from {n1}",
                "multiplication": f"multiply {n1} by {n2}",
                "division": f"divide {n1} by {n2}",
            }
            method = method_map.get(operation, f"compute {n1} {op_sym} {n2}")
            return (
                f"To find the {operation} result, we {method}. "
                f"{n1} {op_sym} {n2} = {correct_val}."
            )
        return (
            f"Working through the arithmetic step by step gives us {correct_val}."
        )

    # Counting
    if topic_category == "counting" or tags & COUNTING_TAGS:
        obj_match = re.search(
            r"(?:count(?:s|ing)?|how many|number of)\s+(?:the\s+)?(\w+)",
            stem.lower(),
        )
        obj = obj_match.group(1) if obj_match else "items"
        return (
            f"Count each {obj} carefully. There are {correct_val} in total."
        )

    # Patterns
    if topic_category == "patterns" or tags & {"pattern", "patterns", "sequence"}:
        return (
            f"The pattern follows a rule. Applying that rule, "
            f"the answer is {correct_val}."
        )

    # Shapes
    if topic_category == "shapes" or tags & {"shape", "shapes", "geometry",
                                              "polygon", "3d-shapes"}:
        shape_match = re.search(
            r"\b(triangle|square|rectangle|circle|pentagon|hexagon|cube|"
            r"sphere|cylinder|cone|oval|rhombus|parallelogram)\b",
            stem.lower(),
        )
        shape = shape_match.group(1) if shape_match else "shape"
        return (
            f"A {shape} has specific properties. "
            f"Based on those properties, the answer is {correct_val}."
        )

    # Spatial
    if topic_category == "spatial" or tags & {"spatial", "direction",
                                               "left-right", "symmetry"}:
        return (
            f"By examining the spatial relationship described, "
            f"the answer is {correct_val}."
        )

    # Word problems
    if topic_category == "word_problems" or tags & {"word_problem", "word-problem"}:
        if operation and len(numbers) >= 2:
            n1, n2 = numbers[0], numbers[1]
            return (
                f"Step 1: Identify the key numbers ({n1} and {n2}). "
                f"Step 2: Apply {operation} ({n1} {op_sym} {n2}). "
                f"Step 3: The result is {correct_val}."
            )
        return (
            f"Step 1: Extract the important information from the problem. "
            f"Step 2: Determine the operation needed. "
            f"Step 3: The answer is {correct_val}."
        )

    # Logic
    if topic_category == "logic":
        return (
            f"By comparing the given items and applying logical reasoning, "
            f"we can determine that the answer is {correct_val}."
        )

    # Puzzles / fallback
    return (
        f"Working through the problem step by step, the correct answer "
        f"is {correct_val}."
    )


def run_add_why(topic_dirs, dry_run=False):
    """Add correct_explanation to every question's diagnostics."""
    added = 0
    skipped = 0

    for td in topic_dirs:
        topic_name = os.path.basename(td)
        topic_cat = detect_topic_from_dir(topic_name)

        for fpath, questions, fmt, wrapper in iter_topic_files(td):
            modified = False
            for q in questions:
                if q.get("_deprecated"):
                    continue
                diag = q.get("diagnostics")
                if diag is None:
                    q["diagnostics"] = {}
                    diag = q["diagnostics"]
                if not isinstance(diag, dict):
                    continue

                # Idempotent: skip if already present
                if "correct_explanation" in diag:
                    skipped += 1
                    continue

                tag_cat = detect_topic_from_tags(q.get("tags"))
                effective_cat = tag_cat if tag_cat != "general" else topic_cat
                explanation = generate_explanation(q, effective_cat)
                diag["correct_explanation"] = explanation
                added += 1
                modified = True

            if modified and not dry_run:
                save_questions_file(fpath, questions, fmt, wrapper)

    print(f"\n=== ADD WHY ===")
    print(f"  Explanations added: {added}")
    print(f"  Already present (skipped): {skipped}")
    if dry_run:
        print("  (dry run — no files written)")
    return added


# ---------------------------------------------------------------------------
# 4. STANDARDIZE HINT LADDER
# ---------------------------------------------------------------------------

def build_metacognitive_hint(q):
    """Level 0: Metacognitive — what is the problem asking?"""
    stem = q.get("stem", "")
    # Try to extract the question being asked
    q_match = re.search(r"((?:How many|What|Which|Where|Who|Find)\b.*?\?)", stem)
    if q_match:
        fragment = q_match.group(1)
        if len(fragment) < 80:
            return f"What is this problem asking you to find? Re-read: \"{fragment}\""
    return "What is this problem asking you to find?"


def build_strategic_hint(q, topic_cat):
    """Level 1: Strategic — what approach could you use?"""
    tags = set(t.lower() for t in (q.get("tags") or []))
    stem_lower = q.get("stem", "").lower()

    strategies = {
        "counting": "Could you point to each object as you count to keep track?",
        "arithmetic": "What operation does this problem need? Could you try a simpler number first?",
        "patterns": "Look at the differences between consecutive items. Is there a repeating rule?",
        "shapes": "What properties define this shape? Could you draw it or compare with a known shape?",
        "spatial": "Could you use your fingers to trace the position or direction?",
        "logic": "Could you eliminate wrong answers one by one?",
        "word_problems": "Underline the key numbers and the question. What operation connects them?",
        "puzzles": "Can you break this into smaller steps? Try working backwards from the choices.",
    }
    return strategies.get(topic_cat,
        "What approach could you use? Could you draw it or try a simpler number?"
    )


def build_procedural_hint(q, topic_cat):
    """Level 2: Procedural — specific step-by-step for THIS question."""
    stem = q.get("stem", "")
    choices = q.get("choices", [])
    correct_idx = q.get("correct_answer", 0)
    correct_val = choices[correct_idx] if correct_idx < len(choices) else "?"
    numbers = extract_numbers_from_stem(stem)
    operation, op_sym = extract_operation_from_stem(stem)

    if operation and len(numbers) >= 2:
        n1, n2 = numbers[0], numbers[1]
        return f"Take {n1} and {op_sym} {n2}. Work through it step by step."

    if topic_cat == "counting" and numbers:
        return f"Start from 1 and count each object. You should reach a number in the {min(numbers)}-{max(numbers)} range."
    if topic_cat == "counting":
        return f"Point to each object one at a time and count aloud."

    if topic_cat == "patterns":
        if len(numbers) >= 3:
            diffs = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
            if len(set(diffs)) == 1:
                return f"Each number changes by {diffs[0]}. Apply that rule to find the next."
        return "Find the difference between consecutive terms, then apply that rule."

    if topic_cat == "shapes":
        return "List the properties mentioned and match them to the shape definitions you know."

    if topic_cat == "spatial":
        return "Identify the reference point, then determine the relative position from there."

    if topic_cat == "word_problems" and operation and len(numbers) >= 2:
        return f"The problem gives you {numbers[0]} and {numbers[1]}. Use {operation} to combine them."

    if topic_cat == "logic":
        return "Compare the options systematically. Check each choice against the given conditions."

    # Fallback: use existing level_2 if present, otherwise generic
    existing = q.get("hint", {}).get("level_2", "")
    if existing and not is_generic_hint(existing):
        return existing
    return "Break the problem into smaller parts and solve each part."


def build_bottomout_hint(q, topic_cat):
    """Level 3: Bottom-out — shows the worked solution."""
    stem = q.get("stem", "")
    choices = q.get("choices", [])
    correct_idx = q.get("correct_answer", 0)
    correct_val = choices[correct_idx] if correct_idx < len(choices) else "?"
    numbers = extract_numbers_from_stem(stem)
    operation, op_sym = extract_operation_from_stem(stem)

    if operation and len(numbers) >= 2:
        n1, n2 = numbers[0], numbers[1]
        return f"{n1} {op_sym} {n2} = {correct_val}. The answer is {correct_val}."

    if topic_cat == "counting":
        return f"Counting each one gives {correct_val}. The answer is {correct_val}."

    if topic_cat == "patterns" and len(numbers) >= 2:
        return f"Following the pattern rule, the answer is {correct_val}."

    # Try to preserve the best existing bottom-out hint
    hint = q.get("hint", {})
    for key in ["level_5", "level_4", "level_3"]:
        existing = hint.get(key, "")
        if existing and len(existing) > 10 and not is_generic_hint(existing):
            # Ensure it mentions the answer
            if correct_val.lower() in existing.lower() or str(correct_val) in existing:
                return existing

    return f"The correct answer is {correct_val}."


def run_fix_hints(topic_dirs, dry_run=False):
    """Standardize all questions to exactly 4 hint levels."""
    fixed = 0
    already_good = 0

    for td in topic_dirs:
        topic_name = os.path.basename(td)
        topic_cat = detect_topic_from_dir(topic_name)

        for fpath, questions, fmt, wrapper in iter_topic_files(td):
            modified = False
            for q in questions:
                if q.get("_deprecated"):
                    continue

                tag_cat = detect_topic_from_tags(q.get("tags"))
                effective_cat = tag_cat if tag_cat != "general" else topic_cat

                old_hint = q.get("hint", {})
                old_keys = set(old_hint.keys())

                # Check if already exactly 4 levels with good content
                if old_keys == {"level_0", "level_1", "level_2", "level_3"}:
                    l0 = old_hint.get("level_0", "")
                    # If level_0 is already metacognitive, skip
                    if "asking" in l0.lower() or "find" in l0.lower():
                        already_good += 1
                        continue

                # Build the new 4-level ladder
                # Preserve existing good content where possible
                new_hint = {}
                new_hint["level_0"] = build_metacognitive_hint(q)
                new_hint["level_1"] = build_strategic_hint(q, effective_cat)

                # For level_2, prefer existing procedural content
                existing_procedural = None
                for key in ["level_2", "level_3", "level_4"]:
                    candidate = old_hint.get(key, "")
                    if candidate and not is_generic_hint(candidate) and len(candidate) > 15:
                        existing_procedural = candidate
                        break
                new_hint["level_2"] = existing_procedural or build_procedural_hint(
                    q, effective_cat
                )

                # For level_3, prefer existing bottom-out content
                new_hint["level_3"] = build_bottomout_hint(q, effective_cat)

                q["hint"] = new_hint
                fixed += 1
                modified = True

            if modified and not dry_run:
                save_questions_file(fpath, questions, fmt, wrapper)

    print(f"\n=== FIX HINTS ===")
    print(f"  Hints standardized to 4 levels: {fixed}")
    print(f"  Already correct (skipped): {already_good}")
    if dry_run:
        print("  (dry run — no files written)")
    return fixed


# ---------------------------------------------------------------------------
# 5. DEDUPLICATE
# ---------------------------------------------------------------------------

def run_dedup(topic_dirs, dry_run=False):
    """Find template-duplicate groups, keep best 3, mark rest deprecated."""
    # Group questions by normalized stem template within each file
    # We process per-file to keep file boundaries clean
    total_deprecated = 0
    groups_found = 0

    for td in topic_dirs:
        topic_name = os.path.basename(td)

        for fpath, questions, fmt, wrapper in iter_topic_files(td):
            # Group by normalized stem
            template_groups = defaultdict(list)
            for i, q in enumerate(questions):
                if q.get("_deprecated"):
                    continue
                norm = normalize_stem(q.get("stem", ""))
                template_groups[norm].append(i)

            modified = False
            for template, indices in template_groups.items():
                if len(indices) <= 3:
                    continue

                groups_found += 1

                # Score each question for "best" — prefer:
                # 1. Diverse difficulty tiers
                # 2. Having good hints / diagnostics
                # 3. Earlier IDs (likely hand-curated)
                def quality_score(idx):
                    q = questions[idx]
                    score = 0
                    # Has correct_explanation
                    diag = q.get("diagnostics", {})
                    if isinstance(diag, dict) and "correct_explanation" in diag:
                        score += 2
                    # Has non-generic hints
                    hint = q.get("hint", {})
                    if hint and not is_generic_hint(hint.get("level_0", "")):
                        score += 1
                    # Has solution_steps
                    if q.get("solution_steps"):
                        score += 1
                    return score

                # Sort by quality descending, then try to spread difficulty
                scored = [(quality_score(i), i) for i in indices]
                scored.sort(key=lambda x: -x[0])

                # Select best 3 with difficulty diversity
                tiers_seen = set()
                kept = []
                remaining = []
                for score, idx in scored:
                    tier = questions[idx].get("difficulty_tier", "medium")
                    if tier not in tiers_seen and len(kept) < 3:
                        kept.append(idx)
                        tiers_seen.add(tier)
                    else:
                        remaining.append(idx)

                # Fill up to 3 if we didn't get enough tier diversity
                for score, idx in scored:
                    if idx not in kept and len(kept) < 3:
                        kept.append(idx)

                # Rebuild remaining (those not kept)
                to_deprecate = [idx for idx in indices if idx not in kept]

                for idx in to_deprecate:
                    if not questions[idx].get("_deprecated"):
                        questions[idx]["_deprecated"] = True
                        total_deprecated += 1
                        modified = True

            if modified and not dry_run:
                save_questions_file(fpath, questions, fmt, wrapper)

    print(f"\n=== DEDUP ===")
    print(f"  Duplicate groups found (>3 same template): {groups_found}")
    print(f"  Questions marked _deprecated: {total_deprecated}")
    if dry_run:
        print("  (dry run — no files written)")
    return total_deprecated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Kiwimath Content Enhancement Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --audit --all
  %(prog)s --fix-modes --topic topic-1-counting
  %(prog)s --add-why --fix-hints --dedup --all
  %(prog)s --audit --fix-modes --add-why --fix-hints --dedup --all --dry-run
        """,
    )

    # Operations
    parser.add_argument("--audit", action="store_true",
                        help="Scan and produce quality report")
    parser.add_argument("--fix-modes", action="store_true",
                        help="Normalize interaction modes")
    parser.add_argument("--add-why", action="store_true",
                        help="Add correct_explanation to diagnostics")
    parser.add_argument("--fix-hints", action="store_true",
                        help="Standardize hint ladder to 4 levels")
    parser.add_argument("--dedup", action="store_true",
                        help="Mark template-duplicate questions as deprecated")

    # Scope
    parser.add_argument("--topic", type=str, default=None,
                        help="Process a single topic directory (e.g. topic-1-counting)")
    parser.add_argument("--all", action="store_true",
                        help="Process all 8 topic directories")

    # Options
    parser.add_argument("--dry-run", action="store_true",
                        help="Report changes without writing files")
    parser.add_argument("--content-dir", type=str, default=None,
                        help="Override content directory path")

    args = parser.parse_args()

    # Validate that at least one operation is specified
    ops = [args.audit, args.fix_modes, args.add_why, args.fix_hints, args.dedup]
    if not any(ops):
        parser.error("Specify at least one operation: --audit, --fix-modes, "
                      "--add-why, --fix-hints, --dedup")

    if not args.topic and not args.all:
        parser.error("Specify --topic <name> or --all")

    # Override content dir if specified
    global CONTENT_DIR
    if args.content_dir:
        CONTENT_DIR = args.content_dir

    if not os.path.isdir(CONTENT_DIR):
        print(f"Error: content directory not found: {CONTENT_DIR}", file=sys.stderr)
        sys.exit(1)

    topic_dirs = get_topic_dirs(args)

    print(f"Kiwimath Content Enhancer")
    print(f"Content dir: {CONTENT_DIR}")
    print(f"Topics: {[os.path.basename(t) for t in topic_dirs]}")
    if args.dry_run:
        print("Mode: DRY RUN (no files will be modified)")
    print("=" * 60)

    # Run operations in logical order
    if args.audit:
        run_audit(topic_dirs)

    if args.fix_modes:
        run_fix_modes(topic_dirs, dry_run=args.dry_run)

    if args.add_why:
        run_add_why(topic_dirs, dry_run=args.dry_run)

    if args.fix_hints:
        run_fix_hints(topic_dirs, dry_run=args.dry_run)

    if args.dedup:
        run_dedup(topic_dirs, dry_run=args.dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
