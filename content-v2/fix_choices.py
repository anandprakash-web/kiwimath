#!/usr/bin/env python3
"""
Fix NCERT G4 questions that have only 3 answer choices by adding a plausible 4th distractor.

QA audit found 24 questions with fewer than 4 choices in:
  ncert-curriculum/grade4/ncert_g4_questions.json

This script generates contextually appropriate distractors based on the question's
topic, stem, existing choices, and correct answer.
"""

import json
import os
import random

random.seed(42)  # Reproducibility

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "ncert-curriculum/grade4/ncert_g4_questions.json")


def generate_distractor(question):
    """Generate a plausible but incorrect 4th choice based on question context."""
    stem = question["stem"]
    choices = question["choices"]
    correct_idx = question["correct_answer"]
    correct_answer = choices[correct_idx]
    tags = question.get("tags", [])

    # Strategy varies by topic
    if "rounding" in tags:
        # For rounding questions, add a nearby thousand value not already present
        existing_nums = [int(c) for c in choices]
        # Add a value one step further away
        step = existing_nums[1] - existing_nums[0] if len(existing_nums) > 1 else 1000
        candidates = [existing_nums[-1] + step, existing_nums[0] - step]
        for c in candidates:
            if c > 0 and c not in existing_nums:
                return str(c)
        return str(existing_nums[0] - 1000)

    elif "LCM" in tags:
        # For LCM questions, generate a plausible wrong multiple
        existing_nums = [int(c) for c in choices]
        correct_val = int(correct_answer)
        # Common LCM mistakes: double the LCM, or product of numbers
        candidates = [correct_val * 2, correct_val + existing_nums[0], correct_val * 3]
        for c in candidates:
            if c not in existing_nums and c > 0:
                return str(c)
        return str(correct_val + 6)

    elif "HCF" in tags:
        # For HCF questions, add a plausible wrong factor
        existing_nums = [int(c) for c in choices]
        correct_val = int(correct_answer)
        candidates = [correct_val // 2, correct_val * 2, correct_val + 1, 6, 4, 8]
        for c in candidates:
            if c not in existing_nums and c > 0:
                return str(c)
        return str(correct_val + 2)

    elif "money" in tags or "decimals" in tags:
        # For rupee decimal questions like "Write Rs X and Y paise as a decimal"
        # Existing distractors typically: correct (e.g. 186.25), sum (e.g. 211), concatenation (e.g. 18625)
        # Add a plausible wrong decimal (off by a decimal place)
        correct_str = correct_answer
        if "." in correct_str:
            # e.g. correct is "₹186.25" -> distractor could be "₹1.8625" or "₹1862.5"
            # Strip the rupee sign for manipulation
            num_part = correct_str.replace("₹", "")
            val = float(num_part)
            distractor_val = val / 10  # shift decimal
            distractor = f"₹{distractor_val:.2f}"
            if distractor not in choices:
                return distractor
            distractor_val = val * 10
            distractor = f"₹{distractor_val:.0f}.0"
            return distractor
        else:
            # Correct answer doesn't have decimal; add one that does in wrong way
            return choices[0].replace("₹", "₹0") if "₹" in choices[0] else choices[0] + ".0"

    elif "24_hour" in tags:
        # For time conversion to 24-hour format
        existing = choices[:]
        correct_str = correct_answer
        # Parse hours and minutes
        parts = correct_str.split(":")
        h, m = int(parts[0]), int(parts[1])
        # Common mistakes: off by 1 hour, or confusing AM/PM offset
        candidates = [
            f"{(h + 1) % 24:02d}:{m:02d}",
            f"{(h - 1) % 24:02d}:{m:02d}",
            f"{(h + 12) % 24:02d}:{m:02d}",
            f"{(h - 2) % 24:02d}:{m:02d}",
        ]
        for c in candidates:
            if c not in existing:
                return c
        return f"{(h + 2) % 24:02d}:{m:02d}"

    elif "12_hour" in tags:
        # For 24-hour to 12-hour conversion
        existing = choices[:]
        correct_str = correct_answer
        # e.g. "7:00 AM" -> distractors might be wrong hour or wrong AM/PM
        if "AM" in correct_str:
            parts = correct_str.replace(" AM", "").split(":")
            h, m = int(parts[0]), int(parts[1])
            candidates = [
                f"{h + 1}:{m:02d} AM",
                f"{h - 1}:{m:02d} AM" if h > 1 else f"{h + 2}:{m:02d} AM",
                f"{h}:{m:02d} PM",
                f"{h + 2}:{m:02d} AM",
            ]
        else:
            parts = correct_str.replace(" PM", "").split(":")
            h, m = int(parts[0]), int(parts[1])
            candidates = [
                f"{h + 1}:{m:02d} PM",
                f"{h - 1}:{m:02d} PM" if h > 1 else f"{h + 2}:{m:02d} PM",
                f"{h}:{m:02d} AM",
                f"{h + 2}:{m:02d} PM",
            ]
        for c in candidates:
            if c not in existing:
                return c
        return candidates[-1]

    elif "duration" in tags or "difference" in tags:
        # Time duration/difference questions
        existing = choices[:]
        correct_str = correct_answer
        # Parse time format like "12:15" or "4 hr 0 min"
        if "hr" in correct_str:
            # Format: "X hr Y min"
            parts = correct_str.split()
            h = int(parts[0])
            m = int(parts[2])
            candidates = [
                f"{h + 1} hr {m} min",
                f"{h} hr {m + 15} min",
                f"{h - 1} hr {m + 30} min",
            ]
        else:
            # Format: "HH:MM"
            parts = correct_str.split(":")
            h, m = int(parts[0]), int(parts[1])
            candidates = [
                f"{h + 1:02d}:{m:02d}" if h < 23 else f"{h - 1:02d}:{m:02d}",
                f"{h:02d}:{(m + 15) % 60:02d}",
                f"{h - 1:02d}:{m:02d}" if h > 0 else f"{h + 2:02d}:{m:02d}",
            ]
        for c in candidates:
            if c not in existing:
                return c
        return candidates[0]

    elif "maps" in tags or "scale" in tags:
        # Map scale questions
        existing_nums = []
        for c in choices:
            num = "".join(ch for ch in c if ch.isdigit())
            if num:
                existing_nums.append(int(num))

        correct_num = int("".join(ch for ch in correct_answer if ch.isdigit()))
        # Common mistakes: multiply instead of divide, off by scale factor
        candidates = [correct_num + 3, correct_num * 2, correct_num + 5, correct_num - 1]
        for c in candidates:
            if c > 0 and c not in existing_nums:
                return f"{c} km"
        return f"{correct_num + 2} km"

    else:
        # Generic fallback: create a choice close to the correct answer
        # Try numeric manipulation
        try:
            correct_val = int(correct_answer)
            existing_nums = [int(c) for c in choices]
            candidates = [correct_val + 1, correct_val - 1, correct_val + 2, correct_val * 2]
            for c in candidates:
                if c not in existing_nums and c > 0:
                    return str(c)
        except (ValueError, TypeError):
            pass
        # Non-numeric fallback
        return correct_answer + " (approx)"


def main():
    # Load the JSON file
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    questions = data["questions"]
    fixed = []

    for q in questions:
        if len(q["choices"]) < 4:
            distractor = generate_distractor(q)
            # Insert the distractor at a random position (not always last)
            insert_pos = random.randint(0, len(q["choices"]))

            # Adjust correct_answer index if we insert before it
            if insert_pos <= q["correct_answer"]:
                q["correct_answer"] += 1

            q["choices"].insert(insert_pos, distractor)

            # Also update diagnostics if present (add entry for new choice)
            if "diagnostics" in q:
                # Renumber diagnostics keys to account for insertion
                old_diag = q["diagnostics"]
                new_diag = {}
                for key, val in old_diag.items():
                    k = int(key)
                    if k >= insert_pos:
                        new_diag[str(k + 1)] = val
                    else:
                        new_diag[str(k)] = val
                # Add diagnostic for new distractor
                new_diag[str(insert_pos)] = "Distractor: common misconception"
                q["diagnostics"] = new_diag

            fixed.append({
                "id": q["id"],
                "stem": q["stem"],
                "added_choice": distractor,
                "position": insert_pos,
                "new_choices": q["choices"],
                "correct_answer_idx": q["correct_answer"],
            })

    # Save the fixed file
    with open(INPUT_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Report results
    print(f"=" * 70)
    print(f"NCERT G4 Questions Fix Report")
    print(f"=" * 70)
    print(f"Total questions in file: {len(questions)}")
    print(f"Questions fixed (had <4 choices): {len(fixed)}")
    print(f"=" * 70)
    print()

    for item in fixed:
        print(f"  Question: {item['id']}")
        print(f"  Stem: {item['stem']}")
        print(f"  Added choice: \"{item['added_choice']}\" at position {item['position']}")
        print(f"  Final choices: {item['new_choices']}")
        print(f"  Correct answer index: {item['correct_answer_idx']}")
        print(f"  ---")
        print()

    print(f"File saved: {INPUT_FILE}")
    print(f"All {len(fixed)} questions now have 4 choices.")


if __name__ == "__main__":
    main()
