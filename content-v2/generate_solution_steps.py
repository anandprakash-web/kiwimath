#!/usr/bin/env python3
"""
Generate solution_steps for all Kiwimath question JSON files.
Processes ~7,841 questions across NCERT, ICSE, IGCSE, Olympiad (topic-*) curricula.
Also runs QA checks and reports flagged issues.
"""

import json
import os
import re
import glob
from pathlib import Path

BASE_DIR = Path(__file__).parent

# QA issue tracking
qa_issues = []

def classify_question(question):
    """Classify question type based on tags, stem, and topic."""
    stem = question.get("stem", "").lower()
    tags = [t.lower() for t in question.get("tags", [])]
    topic = question.get("topic", "").lower()
    qid = question.get("id", "")

    # Check tags first
    tag_str = " ".join(tags)

    if any(t in tag_str for t in ["pattern", "sequence", "series"]):
        return "patterns"
    if any(t in tag_str for t in ["counting", "count", "how_many", "data_handling"]):
        return "counting"
    if any(t in tag_str for t in ["shape", "geometry", "spatial", "symmetry", "reflection", "rotation", "angle"]):
        return "geometry"
    if any(t in tag_str for t in ["logic", "puzzle", "reasoning", "deduction"]):
        return "logic"
    if any(t in tag_str for t in ["word_problem", "story"]):
        return "word_problem"
    if any(t in tag_str for t in ["addition", "subtraction", "multiplication", "division", "arithmetic", "place_value", "fraction", "decimal"]):
        return "arithmetic"

    # Check topic path
    if "topic-1" in str(qid) or "counting" in topic:
        return "counting"
    if "topic-2" in str(qid) or "arithmetic" in topic:
        return "arithmetic"
    if "topic-3" in str(qid) or "pattern" in topic:
        return "patterns"
    if "topic-4" in str(qid) or "logic" in topic:
        return "logic"
    if "topic-5" in str(qid) or "spatial" in topic:
        return "geometry"
    if "topic-6" in str(qid) or "shape" in topic:
        return "geometry"
    if "topic-7" in str(qid) or "word" in topic:
        return "word_problem"
    if "topic-8" in str(qid) or "puzzle" in topic:
        return "logic"

    # Check stem content
    if re.search(r'\d+\s*[\+\-\×\÷\*\/]\s*\d+', stem):
        return "arithmetic"
    if "what is" in stem and re.search(r'\d+\s*[\+\-\×\÷\*\/]\s*\d+', stem):
        return "arithmetic"
    if any(w in stem for w in ["add", "subtract", "multiply", "divide", "sum", "difference", "product", "quotient", "plus", "minus", "times"]):
        return "arithmetic"
    if any(w in stem for w in ["how many", "count", "total number"]):
        return "counting"
    if any(w in stem for w in ["pattern", "next", "sequence", "comes after", "what comes"]):
        return "patterns"
    if any(w in stem for w in ["shape", "triangle", "square", "circle", "rectangle", "sides", "angle", "symmetr"]):
        return "geometry"
    if any(w in stem for w in ["puzzle", "clue", "logic", "which statement"]):
        return "logic"
    if len(stem.split()) > 20:
        return "word_problem"

    # Default based on ID prefix
    if qid.startswith("T1"):
        return "counting"
    if qid.startswith("T2"):
        return "arithmetic"
    if qid.startswith("T3"):
        return "patterns"
    if qid.startswith("T4"):
        return "logic"
    if qid.startswith("T5") or qid.startswith("T6"):
        return "geometry"
    if qid.startswith("T7"):
        return "word_problem"
    if qid.startswith("T8"):
        return "logic"

    return "arithmetic"  # fallback


def get_num_steps(question):
    """Determine number of steps based on difficulty."""
    score = question.get("difficulty_score", 30)
    if score < 20:
        return 2
    elif score <= 60:
        return 3
    else:
        return 4


def extract_numbers(stem):
    """Extract numbers from stem."""
    return re.findall(r'\d+', stem)


def extract_operation(stem):
    """Extract the math operation from stem."""
    if '+' in stem or 'add' in stem.lower() or 'plus' in stem.lower() or 'sum' in stem.lower():
        return 'addition'
    if '-' in stem or 'subtract' in stem.lower() or 'minus' in stem.lower() or 'difference' in stem.lower() or 'less' in stem.lower():
        return 'subtraction'
    if '×' in stem or '*' in stem or 'multiply' in stem.lower() or 'times' in stem.lower() or 'product' in stem.lower():
        return 'multiplication'
    if '÷' in stem or '/' in stem or 'divide' in stem.lower() or 'quotient' in stem.lower() or 'shared equally' in stem.lower():
        return 'division'
    return None


def generate_arithmetic_steps(question):
    """Generate steps for arithmetic questions."""
    stem = question.get("stem", "")
    nums = extract_numbers(stem)
    op = extract_operation(stem)
    n_steps = get_num_steps(question)

    # Try to parse expression like "24 + 38"
    expr_match = re.search(r'(\d+)\s*([\+\-\×\÷\*\/])\s*(\d+)', stem)

    if expr_match:
        a, operator, b = expr_match.group(1), expr_match.group(2), expr_match.group(3)
        a_int, b_int = int(a), int(b)

        if operator in ['+', '＋']:
            if a_int >= 10 and b_int >= 10:
                steps = [
                    f"Break into parts: ({a_int//10*10}+{b_int//10*10}) and ({a_int%10}+{b_int%10})",
                    f"Add tens: {a_int//10*10}+{b_int//10*10}={a_int//10*10+b_int//10*10}",
                    "Now add the ones part and combine"
                ]
            else:
                steps = [
                    f"Start with {a} and count up {b} more",
                    f"Use fingers or a number line to add",
                    "The number you land on is your answer"
                ]
        elif operator in ['-', '−']:
            if a_int >= 10:
                steps = [
                    f"Start at {a} on the number line",
                    f"Count back {b} steps",
                    "The number you land on is your answer"
                ]
            else:
                steps = [
                    f"Start with {a} objects, take away {b}",
                    "Count what remains",
                    "That's your answer"
                ]
        elif operator in ['×', '*']:
            steps = [
                f"Think of {a} groups of {b}",
                f"Add {b} to itself {a} times",
                "The total is your answer"
            ]
        elif operator in ['÷', '/']:
            steps = [
                f"Share {a} equally into {b} groups",
                "Count how many in each group",
                "That number is your answer"
            ]
        else:
            steps = [
                "Identify the operation needed",
                "Calculate step by step",
                "Check your answer makes sense"
            ]
    elif op == 'addition' and len(nums) >= 2:
        a, b = int(nums[0]), int(nums[1])
        if a >= 10 and b >= 10:
            steps = [
                f"Break into parts: ({a//10*10}+{b//10*10}) and ({a%10}+{b%10})",
                f"Add tens: {a//10*10}+{b//10*10}={a//10*10+b//10*10}",
                "Now add the ones part and combine"
            ]
        else:
            steps = [
                f"Start with {a} and count up {b} more",
                "Use fingers or a number line",
                "The number you land on is your answer"
            ]
    elif op == 'subtraction' and len(nums) >= 2:
        a, b = int(nums[0]), int(nums[1])
        steps = [
            f"Start at {a} on the number line",
            f"Count back {b} steps",
            "The number you land on is your answer"
        ]
    elif op == 'multiplication' and len(nums) >= 2:
        a, b = int(nums[0]), int(nums[1])
        steps = [
            f"Think of {a} groups of {b}",
            f"Add {b} to itself {a} times",
            "The total is your answer"
        ]
    elif op == 'division' and len(nums) >= 2:
        a, b = int(nums[0]), int(nums[1])
        steps = [
            f"Share {a} equally into {b} groups",
            "Count how many in each group",
            "That number is your answer"
        ]
    elif 'place value' in stem.lower() or 'digit' in stem.lower():
        steps = [
            "Identify the place of each digit",
            "Remember: ones, tens, hundreds from right",
            "Read the value at the asked position"
        ]
    elif 'fraction' in stem.lower():
        steps = [
            "Look at the numerator and denominator",
            "The denominator tells total equal parts",
            "The numerator tells how many parts chosen"
        ]
    elif 'greater' in stem.lower() or 'smaller' in stem.lower() or 'compare' in stem.lower():
        steps = [
            "Compare the digits from left to right",
            "The number with a larger leftmost digit is bigger",
            "If same, compare the next digit"
        ]
    else:
        # Generic arithmetic
        if nums:
            steps = [
                f"Identify the numbers: {', '.join(nums[:3])}",
                "Determine the operation needed",
                "Calculate step by step to find the answer"
            ]
        else:
            steps = [
                "Read the problem and find the numbers",
                "Identify which operation to use",
                "Calculate to find the answer"
            ]

    return steps[:n_steps]


def generate_counting_steps(question):
    """Generate steps for counting questions."""
    stem = question.get("stem", "")
    n_steps = get_num_steps(question)
    nums = extract_numbers(stem)

    if "bar graph" in stem.lower() or "graph" in stem.lower() or "table" in stem.lower() or "chart" in stem.lower():
        steps = [
            "Read the values from the graph carefully",
            "Identify the numbers for each item mentioned",
            "Use the right operation on those numbers",
            "Check your answer matches the question"
        ]
    elif "more" in stem.lower() or "fewer" in stem.lower() or "less" in stem.lower():
        steps = [
            "Find the two quantities to compare",
            "Subtract the smaller from the larger",
            "The difference is your answer"
        ]
    elif "picture" in stem.lower() or "image" in stem.lower() or "sees" in stem.lower():
        steps = [
            "Look at the picture carefully",
            "Count each object one by one",
            "The last number you say is the total"
        ]
    elif "how many" in stem.lower() and nums:
        steps = [
            "Identify what you need to count",
            "Count systematically, left to right",
            "The total count is your answer"
        ]
    else:
        steps = [
            "Look at what you need to count",
            "Count systematically one by one",
            "The total is your answer"
        ]

    return steps[:n_steps]


def generate_pattern_steps(question):
    """Generate steps for pattern questions."""
    stem = question.get("stem", "")
    n_steps = get_num_steps(question)
    nums = extract_numbers(stem)

    if nums and len(nums) >= 3:
        # Try to detect if it's a number sequence
        int_nums = [int(n) for n in nums[:5]]
        if len(int_nums) >= 3:
            diff1 = int_nums[1] - int_nums[0]
            diff2 = int_nums[2] - int_nums[1]
            if diff1 == diff2:
                steps = [
                    f"Look at the differences: {int_nums[1]}-{int_nums[0]}={diff1}",
                    f"The pattern adds {diff1} each time",
                    f"Add {diff1} to the last number to find next"
                ]
            else:
                steps = [
                    "Look at how the numbers change each step",
                    "Find the rule connecting consecutive numbers",
                    "Apply the rule to find the missing number"
                ]
        else:
            steps = [
                "Look at what changes between items",
                "Find the rule (adding, subtracting, repeating?)",
                "Apply the rule to find what comes next"
            ]
    elif "repeat" in stem.lower() or "colour" in stem.lower() or "color" in stem.lower():
        steps = [
            "Identify the repeating group of items",
            "Count position to find where in the cycle",
            "Match the position to the repeating unit"
        ]
    else:
        steps = [
            "Look at what changes between items",
            "Find the rule (adding, subtracting, repeating?)",
            "Apply the rule to find what comes next"
        ]

    return steps[:n_steps]


def generate_geometry_steps(question):
    """Generate steps for geometry/shapes questions."""
    stem = question.get("stem", "")
    n_steps = get_num_steps(question)

    if "symmetry" in stem.lower() or "line of symmetry" in stem.lower():
        steps = [
            "Imagine folding the shape along a line",
            "Both halves must match exactly when folded",
            "Count how many such fold lines exist"
        ]
    elif "angle" in stem.lower():
        steps = [
            "Identify the angle type (acute/right/obtuse)",
            "Right angle = 90°, straight = 180°",
            "Compare or calculate the angle asked"
        ]
    elif "perimeter" in stem.lower():
        steps = [
            "Perimeter means total length around the shape",
            "Add up all the side lengths",
            "The sum of all sides is the perimeter"
        ]
    elif "area" in stem.lower():
        steps = [
            "Area means space inside the shape",
            "Use the formula for that shape",
            "Calculate length times width for rectangles"
        ]
    elif "sides" in stem.lower() or "vertices" in stem.lower() or "corners" in stem.lower():
        steps = [
            "Count the straight edges of the shape",
            "Each corner where edges meet is a vertex",
            "Match the count to the correct name"
        ]
    elif any(s in stem.lower() for s in ["triangle", "square", "circle", "rectangle", "pentagon", "hexagon"]):
        steps = [
            "Identify the properties of the named shape",
            "Compare sides, angles, or other features",
            "Match the property to the correct option"
        ]
    elif "reflection" in stem.lower() or "mirror" in stem.lower():
        steps = [
            "Imagine a mirror along the line given",
            "Each point flips to the other side equally",
            "The reflected shape is a mirror image"
        ]
    elif "rotation" in stem.lower() or "turn" in stem.lower():
        steps = [
            "Identify the centre and angle of rotation",
            "Turn the shape by that angle",
            "Check which option matches the turned shape"
        ]
    else:
        steps = [
            "Identify the properties to look for",
            "Compare with the given options",
            "Match the property to the correct shape"
        ]

    return steps[:n_steps]


def generate_logic_steps(question):
    """Generate steps for logic/puzzle questions."""
    stem = question.get("stem", "")
    n_steps = get_num_steps(question)

    if "odd one out" in stem.lower() or "does not belong" in stem.lower():
        steps = [
            "Find what the other items have in common",
            "Check each option against that common property",
            "The one that breaks the pattern is the answer"
        ]
    elif "true" in stem.lower() or "false" in stem.lower() or "statement" in stem.lower():
        steps = [
            "Read each statement carefully",
            "Test each against the given information",
            "Find which one is definitely correct or wrong"
        ]
    elif "clue" in stem.lower():
        steps = [
            "Read all the clues carefully",
            "Eliminate options that contradict any clue",
            "Check remaining options against all conditions",
            "The one that satisfies all clues is correct"
        ]
    elif "order" in stem.lower() or "arrange" in stem.lower() or "sequence" in stem.lower():
        steps = [
            "List all the items or events mentioned",
            "Use the given information to order them",
            "Check your arrangement satisfies all conditions"
        ]
    else:
        steps = [
            "Read the clues or conditions carefully",
            "Eliminate options that don't fit",
            "Check remaining options against all conditions"
        ]

    return steps[:n_steps]


def generate_word_problem_steps(question):
    """Generate steps for word problems."""
    stem = question.get("stem", "")
    n_steps = get_num_steps(question)
    nums = extract_numbers(stem)
    op = extract_operation(stem)

    # Determine what kind of word problem
    if op == 'addition' or 'total' in stem.lower() or 'altogether' in stem.lower() or 'in all' in stem.lower():
        if nums and len(nums) >= 2:
            steps = [
                f"Given: {nums[0]} and {nums[1]} (find total)",
                "Operation needed: addition",
                f"Add {nums[0]} + {nums[1]}",
                "Check: does the total make sense?"
            ]
        else:
            steps = [
                "Identify the quantities given",
                "Since we need the total, add them",
                "Calculate the sum",
                "Check your answer makes sense"
            ]
    elif op == 'subtraction' or 'left' in stem.lower() or 'remain' in stem.lower() or 'gave away' in stem.lower():
        if nums and len(nums) >= 2:
            steps = [
                f"Given: started with {nums[0]}, removed {nums[1]}",
                "Operation needed: subtraction",
                f"Subtract: {nums[0]} - {nums[1]}",
                "Check: is the result less than what you started with?"
            ]
        else:
            steps = [
                "Identify what you start with and what's removed",
                "Subtract the smaller from the larger",
                "Calculate the difference",
                "Check your answer makes sense"
            ]
    elif op == 'multiplication' or 'each' in stem.lower() or 'every' in stem.lower():
        if nums and len(nums) >= 2:
            steps = [
                f"Given: {nums[0]} groups of {nums[1]} each",
                "Operation needed: multiplication",
                f"Multiply: {nums[0]} × {nums[1]}",
                "Check: is the product reasonable?"
            ]
        else:
            steps = [
                "Identify the groups and items per group",
                "Operation needed: multiplication",
                "Multiply groups by items per group",
                "Check your answer makes sense"
            ]
    elif op == 'division' or 'share' in stem.lower() or 'equal' in stem.lower() or 'distribute' in stem.lower():
        if nums and len(nums) >= 2:
            steps = [
                f"Given: {nums[0]} shared among {nums[1]}",
                "Operation needed: division",
                f"Divide: {nums[0]} ÷ {nums[1]}",
                "Check: multiply back to verify"
            ]
        else:
            steps = [
                "Identify total and number of groups",
                "Operation needed: division",
                "Divide total by number of groups",
                "Check your answer makes sense"
            ]
    else:
        # Generic word problem
        if nums and len(nums) >= 2:
            steps = [
                f"Identify what's given: {', '.join(nums[:3])}",
                "Determine what's being asked",
                "Choose the right operation",
                "Calculate and check your answer"
            ]
        else:
            steps = [
                "Identify what's given and what's asked",
                "Choose the right operation",
                "Set up the calculation",
                "Solve and check your answer makes sense"
            ]

    return steps[:n_steps]


def generate_solution_steps(question):
    """Generate solution steps for a question based on its type."""
    q_type = classify_question(question)

    if q_type == "arithmetic":
        return generate_arithmetic_steps(question)
    elif q_type == "counting":
        return generate_counting_steps(question)
    elif q_type == "patterns":
        return generate_pattern_steps(question)
    elif q_type == "geometry":
        return generate_geometry_steps(question)
    elif q_type == "logic":
        return generate_logic_steps(question)
    elif q_type == "word_problem":
        return generate_word_problem_steps(question)
    else:
        return generate_arithmetic_steps(question)


def qa_check(question, filepath):
    """Run QA checks on a question."""
    issues = []
    qid = question.get("id", "unknown")
    stem = question.get("stem", "")
    choices = question.get("choices", [])
    correct = question.get("correct_answer", 0)

    # Check correct_answer index >= len(choices)
    if correct >= len(choices):
        issues.append(f"[INVALID_INDEX] {qid} in {filepath}: correct_answer={correct} but only {len(choices)} choices")

    # Check duplicate choices
    if len(choices) != len(set(choices)):
        dupes = [c for c in choices if choices.count(c) > 1]
        issues.append(f"[DUPLICATE_CHOICES] {qid} in {filepath}: duplicates={list(set(dupes))}")

    # Check empty stem
    if not stem or not stem.strip():
        issues.append(f"[EMPTY_STEM] {qid} in {filepath}")

    # Check choice count
    if len(choices) < 3:
        issues.append(f"[TOO_FEW_CHOICES] {qid} in {filepath}: only {len(choices)} choices")
    elif len(choices) > 5:
        issues.append(f"[TOO_MANY_CHOICES] {qid} in {filepath}: {len(choices)} choices")

    return issues


def process_file(filepath):
    """Process a single JSON file, add solution_steps, run QA checks."""
    global qa_issues

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Determine format
    if isinstance(data, list):
        questions = data
        is_list_format = True
    elif isinstance(data, dict) and "questions" in data:
        questions = data["questions"]
        is_list_format = False
    else:
        # Skip non-question files
        return 0

    count = 0
    for q in questions:
        if not isinstance(q, dict):
            continue
        if "stem" not in q or "choices" not in q:
            continue

        # QA checks
        issues = qa_check(q, filepath)
        qa_issues.extend(issues)

        # Generate solution steps
        steps = generate_solution_steps(q)
        q["solution_steps"] = steps
        count += 1

    # Write back
    if is_list_format:
        out_data = data
    else:
        out_data = data

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)

    return count


def find_all_json_files():
    """Find all question JSON files to process."""
    files = []

    # NCERT curriculum
    for g in range(1, 7):
        pattern = str(BASE_DIR / f"ncert-curriculum/grade{g}/*.json")
        files.extend(glob.glob(pattern))

    # ICSE curriculum
    for g in range(1, 7):
        pattern = str(BASE_DIR / f"icse-curriculum/grade{g}/*.json")
        files.extend(glob.glob(pattern))

    # IGCSE curriculum
    for g in range(1, 7):
        pattern = str(BASE_DIR / f"igcse-curriculum/grade{g}/*.json")
        files.extend(glob.glob(pattern))

    # Topic directories (1-8)
    for t in range(1, 9):
        topic_dirs = glob.glob(str(BASE_DIR / f"topic-{t}-*"))
        for td in topic_dirs:
            # Top-level JSON files
            files.extend(glob.glob(os.path.join(td, "*.json")))
            # Grade subdirectories
            files.extend(glob.glob(os.path.join(td, "grade*", "*.json")))

    # Singapore curriculum (bonus)
    for g in range(1, 7):
        pattern = str(BASE_DIR / f"singapore-curriculum/grade{g}/*.json")
        files.extend(glob.glob(pattern))

    # US Common Core (bonus)
    for g in range(1, 7):
        pattern = str(BASE_DIR / f"us-common-core/grade{g}/*.json")
        files.extend(glob.glob(pattern))

    # Filter out manifest, visual_registry, generate scripts, etc.
    filtered = []
    for f in files:
        basename = os.path.basename(f)
        if basename.startswith("manifest") or basename.startswith("visual_registry"):
            continue
        if basename.startswith("generate_") or basename.startswith("validate_"):
            continue
        if basename.startswith("master_"):
            continue
        filtered.append(f)

    return sorted(set(filtered))


def main():
    print("=" * 70)
    print("KIWIMATH SOLUTION STEPS GENERATOR")
    print("=" * 70)

    files = find_all_json_files()
    print(f"\nFound {len(files)} JSON files to process.\n")

    total_questions = 0
    errors = []
    file_stats = {}
    samples = {}

    for filepath in files:
        try:
            count = process_file(filepath)
            total_questions += count

            # Track by curriculum
            rel = os.path.relpath(filepath, BASE_DIR)
            curriculum = rel.split('/')[0]
            file_stats[curriculum] = file_stats.get(curriculum, 0) + count

            # Collect samples
            if curriculum not in samples and count > 0:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                qs = data if isinstance(data, list) else data.get("questions", [])
                for q in qs:
                    if "solution_steps" in q:
                        samples[curriculum] = {
                            "id": q["id"],
                            "stem": q["stem"][:80],
                            "steps": q["solution_steps"]
                        }
                        break

            if count > 0:
                print(f"  ✓ {os.path.relpath(filepath, BASE_DIR)}: {count} questions")
        except Exception as e:
            errors.append(f"{filepath}: {e}")
            print(f"  ✗ ERROR: {os.path.relpath(filepath, BASE_DIR)}: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nTotal questions processed: {total_questions}")
    print(f"Total files processed: {len(files)}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  - {e}")

    print("\nQuestions by curriculum:")
    for curr, count in sorted(file_stats.items()):
        print(f"  {curr}: {count}")

    print("\n" + "=" * 70)
    print("SAMPLE SOLUTION STEPS (one per curriculum)")
    print("=" * 70)
    for curr, sample in sorted(samples.items()):
        print(f"\n  [{curr}] {sample['id']}")
        print(f"  Stem: {sample['stem']}")
        print(f"  Steps:")
        for i, step in enumerate(sample['steps'], 1):
            print(f"    {i}. {step}")

    print("\n" + "=" * 70)
    print(f"QA ISSUES ({len(qa_issues)} total)")
    print("=" * 70)
    if qa_issues:
        for issue in qa_issues[:50]:  # print first 50
            print(f"  {issue}")
        if len(qa_issues) > 50:
            print(f"\n  ... and {len(qa_issues) - 50} more issues.")
    else:
        print("  No QA issues found!")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
