#!/usr/bin/env python3
"""
Kiwimath Content Scaler — Generate new questions for a topic to reach 300 per grade.

Usage:
    python scripts/scale_content.py --topic counting_observation --grade 1 --batch 50
"""

import json, random, re, copy, hashlib, os, sys
from pathlib import Path
from typing import List, Dict, Any, Optional

CONTENT_DIR = Path(os.environ.get("KIWIMATH_V2_CONTENT_DIR",
    str(Path(__file__).parent.parent / "content-v2")))

# ── Topic metadata ────────────────────────────────────────────
TOPIC_MAP = {
    "counting_observation": {
        "dir": "topic-1-counting",
        "prefix": "T1",
        "visual_pct": 0.29,
    },
    "arithmetic_missing_numbers": {
        "dir": "topic-2-arithmetic",
        "prefix": "T2",
        "visual_pct": 0.36,
    },
    "patterns_sequences": {
        "dir": "topic-3-patterns",
        "prefix": "PAT",
        "visual_pct": 0.99,
    },
    "logic_ordering": {
        "dir": "topic-4-logic",
        "prefix": "LOG",
        "visual_pct": 0.58,
    },
    "spatial_reasoning_3d": {
        "dir": "topic-5-spatial",
        "prefix": "SPA",
        "visual_pct": 0.81,
    },
    "shapes_folding_symmetry": {
        "dir": "topic-6-shapes",
        "prefix": "SHP",
        "visual_pct": 0.73,
    },
    "word_problems_stories": {
        "dir": "topic-7-word-problems",
        "prefix": "WRD",
        "visual_pct": 0.27,
    },
    "number_puzzles_games": {
        "dir": "topic-8-puzzles",
        "prefix": "PUZ",
        "visual_pct": 0.76,
    },
}

# ── Grade-specific difficulty distribution ────────────────────
# G1: 80% easy + 20% medium (scores 1-50)
# G2: 60% medium + 40% hard  (scores 51-100)
GRADE_DIST = {
    1: {"easy": 0.80, "medium": 0.20, "hard": 0.00},
    2: {"easy": 0.00, "medium": 0.60, "hard": 0.40},
}

TARGET_PER_GRADE = 300


def load_topic(topic_id: str) -> Dict:
    """Load existing questions for a topic."""
    meta = TOPIC_MAP[topic_id]
    qpath = CONTENT_DIR / meta["dir"] / "questions.json"
    return json.loads(qpath.read_text())


def get_existing_ids(questions: List[Dict]) -> set:
    return {q["id"] for q in questions}


def get_existing_stems(questions: List[Dict]) -> set:
    """Normalized stems for dedup."""
    return {re.sub(r'\s+', ' ', q["stem"].lower().strip()) for q in questions}


def compute_qa_score(q: Dict) -> int:
    """Run basic QA checks and return score out of 10."""
    score = 0
    checks = []

    # 1. Has stem
    if q.get("stem") and len(q["stem"]) > 10:
        score += 1
        checks.append("has_stem")

    # 2. Has 4 choices
    choices = q.get("choices", [])
    if len(choices) == 4:
        score += 1
        checks.append("four_choices")

    # 3. All choices unique
    if len(set(str(c).strip().lower() for c in choices)) == 4:
        score += 1
        checks.append("unique_choices")

    # 4. Correct answer in range
    if 0 <= q.get("correct_answer", -1) <= 3:
        score += 1
        checks.append("valid_correct")

    # 5. Stem ends with ?
    if q.get("stem", "").strip().endswith("?"):
        score += 1
        checks.append("ends_question_mark")

    # 6. Has difficulty info
    if q.get("difficulty_tier") in ("easy", "medium", "hard"):
        score += 1
        checks.append("has_difficulty")

    # 7. Has tags
    if q.get("tags") and len(q["tags"]) >= 1:
        score += 1
        checks.append("has_tags")

    # 8. Correct answer is actually in choices
    ca = q.get("correct_answer", 0)
    if 0 <= ca < len(choices):
        score += 1
        checks.append("correct_in_choices")

    # 9. No duplicate meaning (approximate)
    if len(choices) == 4:
        vals = [str(c).strip() for c in choices]
        if len(set(vals)) == 4:
            score += 1
            checks.append("no_dup_values")

    # 10. Has hints
    hint = q.get("hint", {})
    if isinstance(hint, dict) and len(hint) >= 3:
        score += 1
        checks.append("has_hints")

    return score


def visual_qa(q: Dict, svg_content: str) -> List[str]:
    """Additional QA for visual questions. Returns list of issues."""
    issues = []

    if not svg_content:
        issues.append("SVG content is empty")
        return issues

    # Check SVG is valid-ish
    if "<svg" not in svg_content.lower():
        issues.append("Missing <svg> tag")

    if "</svg>" not in svg_content.lower():
        issues.append("Missing closing </svg> tag")

    # Check SVG has viewBox
    if "viewBox" not in svg_content and "viewbox" not in svg_content:
        issues.append("Missing viewBox attribute")

    # Check SVG isn't too small
    if len(svg_content) < 100:
        issues.append("SVG suspiciously small (<100 chars)")

    # Check stem references something visual
    stem = q.get("stem", "").lower()
    visual_words = ["look", "see", "picture", "image", "figure", "diagram",
                    "shown", "below", "above", "drawing", "shape", "grid",
                    "pattern", "count", "observe"]
    if not any(w in stem for w in visual_words):
        # Not necessarily an issue but worth flagging
        issues.append("WARN: Stem may not reference the visual")

    # Check visual_alt exists
    if not q.get("visual_alt"):
        issues.append("Missing visual_alt text")

    return issues


# ── COUNTING & OBSERVATION question generators ────────────────

def _counting_g1_easy_templates():
    """Grade 1 easy counting questions (scores 1-40ish)."""
    templates = []

    # Simple addition counting
    items = [
        ("apples", "basket"), ("books", "shelf"), ("crayons", "box"),
        ("toys", "chest"), ("cookies", "plate"), ("stars", "sky"),
        ("butterflies", "garden"), ("fish", "pond"), ("birds", "tree"),
        ("flowers", "vase"), ("marbles", "bag"), ("beads", "string"),
        ("coins", "piggy bank"), ("pebbles", "jar"), ("stamps", "album"),
        ("stickers", "book"), ("buttons", "tin"), ("shells", "bucket"),
        ("pencils", "case"), ("sweets", "bowl"),
    ]

    colors = ["red", "blue", "green", "yellow", "pink", "orange", "purple", "white"]
    names = ["Ria", "Aman", "Zara", "Leo", "Mia", "Sam", "Tom", "Priya", "Ravi",
             "Anika", "Dev", "Noor", "Kiran", "Tara", "Veer", "Isha", "Arjun", "Sia"]

    for item, container in items:
        for _ in range(3):
            c1, c2 = random.sample(colors, 2)
            n1 = random.randint(1, 9)
            n2 = random.randint(1, 9)
            total = n1 + n2
            wrong = [total + 1, total - 1, total + 2]
            wrong = [w for w in wrong if w > 0 and w != total][:3]
            while len(wrong) < 3:
                wrong.append(total + random.randint(2, 4))
            random.shuffle(wrong)
            choices = [str(total)] + [str(w) for w in wrong[:3]]
            correct_idx = 0

            # Shuffle choices
            combined = list(enumerate(choices))
            random.shuffle(combined)
            new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)
            shuffled_choices = [c for _, c in combined]

            name = random.choice(names)
            templates.append({
                "stem": f"{name} has {n1} {c1} {item} and {n2} {c2} {item} in a {container}. How many {item} are there altogether?",
                "choices": shuffled_choices,
                "correct_answer": new_correct,
                "tags": ["counting", "addition", "easy"],
                "needs_visual": random.random() < 0.25,
            })

    # Subtraction counting
    for item, container in items[:10]:
        for _ in range(2):
            total = random.randint(6, 15)
            taken = random.randint(1, total - 1)
            answer = total - taken
            wrong = [answer + 1, answer - 1, answer + 2]
            wrong = [w for w in wrong if w >= 0 and w != answer][:3]
            while len(wrong) < 3:
                wrong.append(answer + random.randint(2, 5))
            choices = [str(answer)] + [str(w) for w in wrong[:3]]
            combined = list(enumerate(choices))
            random.shuffle(combined)
            new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

            name = random.choice(names)
            verbs = ["gives away", "eats", "loses", "drops", "shares"]
            verb = random.choice(verbs)

            templates.append({
                "stem": f"{name} has {total} {item}. {name} {verb} {taken}. How many {item} does {name} have left?",
                "choices": [c for _, c in combined],
                "correct_answer": new_correct,
                "tags": ["counting", "subtraction", "easy"],
                "needs_visual": random.random() < 0.2,
            })

    # "How many" observation questions
    animals = [("dogs", 4), ("cats", 4), ("birds", 2), ("spiders", 8),
               ("ants", 6), ("octopus", 8), ("butterflies", 6)]
    for animal, legs in animals:
        for count in range(1, 5):
            answer = count * legs
            body_part = "legs" if legs in (4, 6, 8) else "wings"
            if animal == "octopus":
                body_part = "arms"
            wrong = [answer + legs, answer - legs, answer + 1]
            wrong = [w for w in wrong if w > 0 and w != answer][:3]
            while len(wrong) < 3:
                wrong.append(answer + random.randint(1, 5))
            choices = [str(answer)] + [str(w) for w in wrong[:3]]
            combined = list(enumerate(choices))
            random.shuffle(combined)
            new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

            templates.append({
                "stem": f"Captain Kiwi met {count} {animal}. How many {body_part} do they have in total?",
                "choices": [c for _, c in combined],
                "correct_answer": new_correct,
                "tags": ["counting", "multiplication", "easy"],
                "needs_visual": True,
            })

    # Skip counting
    for step in [2, 5, 10]:
        for start_idx in range(3, 8):
            seq = [step * i for i in range(1, start_idx + 1)]
            answer = step * (start_idx + 1)
            display = ", ".join(str(s) for s in seq)
            wrong = [answer + step, answer - step, answer + 1]
            wrong = [w for w in wrong if w > 0 and w != answer][:3]
            while len(wrong) < 3:
                wrong.append(answer + random.randint(1, 10))
            choices = [str(answer)] + [str(w) for w in wrong[:3]]
            combined = list(enumerate(choices))
            random.shuffle(combined)
            new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

            templates.append({
                "stem": f"Captain Kiwi is counting by {step}s: {display}, ... What number comes next?",
                "choices": [c for _, c in combined],
                "correct_answer": new_correct,
                "tags": ["counting", "skip-counting", "easy"],
                "needs_visual": False,
            })

    # Comparison questions
    for _ in range(20):
        name1, name2 = random.sample(names, 2)
        item = random.choice(["marbles", "stickers", "candies", "books", "toys"])
        n1 = random.randint(3, 15)
        n2 = random.randint(3, 15)
        while n1 == n2:
            n2 = random.randint(3, 15)
        diff = abs(n1 - n2)
        more_name = name1 if n1 > n2 else name2
        wrong = [diff + 1, diff - 1, diff + 2]
        wrong = [w for w in wrong if w > 0 and w != diff][:3]
        while len(wrong) < 3:
            wrong.append(diff + random.randint(2, 5))
        choices = [str(diff)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"{name1} has {n1} {item} and {name2} has {n2} {item}. How many more {item} does {more_name} have?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "comparison", "easy"],
            "needs_visual": random.random() < 0.2,
        })

    # Grouping/sharing
    for _ in range(15):
        total = random.choice([6, 8, 9, 10, 12, 15, 16, 18, 20])
        groups = random.choice([g for g in [2, 3, 4, 5] if total % g == 0])
        answer = total // groups
        name = random.choice(names)
        item = random.choice(["candies", "stickers", "marbles", "pencils", "cookies"])
        wrong = [answer + 1, answer - 1, answer + 2]
        wrong = [w for w in wrong if w > 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 4))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"{name} has {total} {item} and shares them equally among {groups} friends. How many {item} does each friend get?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "division", "easy"],
            "needs_visual": random.random() < 0.2,
        })

    # Ordinal/position questions
    ordinals = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh"]
    for _ in range(10):
        count = random.randint(5, 8)
        pos = random.randint(1, count)
        item = random.choice(["children", "animals", "flowers", "books", "toys"])
        from_dir = random.choice(["left", "right", "front", "back"])

        templates.append({
            "stem": f"There are {count} {item} in a row. Which position from the {from_dir} is the {ordinals[min(pos-1, 6)]}?",
            "choices": [str(pos), str(pos+1), str(pos-1 if pos > 1 else pos+2), str(count)],
            "correct_answer": 0,
            "tags": ["counting", "ordinal", "easy"],
            "needs_visual": random.random() < 0.3,
        })

    return templates


def _counting_g1_medium_templates():
    """Grade 1 medium counting questions (scores 41-50)."""
    templates = []
    names = ["Ria", "Aman", "Zara", "Leo", "Mia", "Sam", "Tom", "Priya", "Ravi",
             "Anika", "Dev", "Noor", "Kiran", "Tara", "Veer", "Isha", "Arjun", "Sia"]

    # Multi-step counting
    for _ in range(30):
        n1 = random.randint(5, 15)
        n2 = random.randint(2, 8)
        n3 = random.randint(1, 5)
        answer = n1 + n2 - n3
        name = random.choice(names)
        item = random.choice(["marbles", "stickers", "candies", "books", "toys", "coins"])
        verb_add = random.choice(["finds", "gets", "receives", "wins"])
        verb_sub = random.choice(["gives away", "loses", "drops", "shares"])

        wrong = [answer + 1, answer - 1, n1 + n2, n1 - n3]
        wrong = [w for w in wrong if w > 0 and w != answer]
        wrong = list(set(wrong))[:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 5))

        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"{name} has {n1} {item}. {name} {verb_add} {n2} more, then {verb_sub} {n3}. How many {item} does {name} have now?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "multi-step", "medium"],
            "needs_visual": random.random() < 0.3,
        })

    # Pattern recognition in counting
    for _ in range(15):
        step = random.choice([2, 3, 4, 5])
        start = random.randint(1, 5)
        seq = [start + step * i for i in range(5)]
        # Remove one element
        miss_idx = random.randint(1, 3)
        answer = seq[miss_idx]
        display = [str(s) if i != miss_idx else "___" for i, s in enumerate(seq)]

        wrong = [answer + 1, answer - 1, answer + step]
        wrong = [w for w in wrong if w > 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 6))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"Find the missing number: {', '.join(display)}",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "pattern", "medium"],
            "needs_visual": False,
        })

    # Venn diagram / overlap counting
    for _ in range(15):
        total = random.randint(15, 25)
        a = random.randint(5, 12)
        b = random.randint(5, 12)
        both = random.randint(1, min(a, b) - 1)
        neither = total - a - b + both

        if neither < 0:
            continue

        name = random.choice(names)
        group_a = random.choice(["glasses", "hats", "scarves", "badges"])
        group_b = random.choice(["shoes", "ties", "gloves", "watches"])
        while group_a == group_b:
            group_b = random.choice(["shoes", "ties", "gloves", "watches"])

        # Ask different questions
        q_type = random.choice(["neither", "only_a", "only_b"])
        if q_type == "neither":
            answer = neither
            q_text = f"In a class of {total} children, {a} wear {group_a} and {b} wear {group_b}. {both} children wear both. How many children wear neither?"
        elif q_type == "only_a":
            answer = a - both
            q_text = f"In a class of {total} children, {a} wear {group_a} and {b} wear {group_b}. {both} children wear both. How many wear only {group_a}?"
        else:
            answer = b - both
            q_text = f"In a class of {total} children, {a} wear {group_a} and {b} wear {group_b}. {both} children wear both. How many wear only {group_b}?"

        if answer < 0:
            continue

        wrong = [answer + 1, answer - 1, both, total - a]
        wrong = [w for w in wrong if w >= 0 and w != answer]
        wrong = list(set(wrong))[:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 5))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": q_text,
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "venn-diagram", "medium"],
            "needs_visual": random.random() < 0.35,
        })

    return templates


def _counting_g2_medium_templates():
    """Grade 2 medium counting questions (scores 51-80)."""
    templates = []
    names = ["Ria", "Aman", "Zara", "Leo", "Mia", "Sam", "Tom", "Priya", "Ravi",
             "Anika", "Dev", "Noor", "Kiran", "Tara", "Veer", "Isha", "Arjun", "Sia"]

    # Dice/card counting
    for _ in range(20):
        num_dice = random.randint(2, 4)
        faces = [random.randint(1, 6) for _ in range(num_dice)]
        total = sum(faces)
        face_str = " and ".join(str(f) for f in faces)

        wrong = [total + 1, total - 1, total + 2]
        wrong = [w for w in wrong if w > 0 and w != total][:3]
        while len(wrong) < 3:
            wrong.append(total + random.randint(2, 5))
        choices = [str(total)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"Captain Kiwi rolled {num_dice} dice and got {face_str}. What is the total?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "dice", "medium"],
            "needs_visual": True,
        })

    # Grid counting
    for _ in range(20):
        rows = random.randint(2, 5)
        cols = random.randint(2, 5)
        answer = rows * cols

        wrong = [answer + 1, answer - 1, rows + cols]
        wrong = [w for w in wrong if w > 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 5))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        shape = random.choice(["squares", "dots", "circles", "stars"])
        templates.append({
            "stem": f"A grid has {rows} rows and {cols} columns of {shape}. How many {shape} are there in total?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "grid", "medium"],
            "needs_visual": True,
        })

    # Hidden faces on cubes
    for _ in range(15):
        num_cubes = random.randint(1, 3)
        visible = random.randint(2 * num_cubes, 5 * num_cubes)
        total_faces = 6 * num_cubes
        hidden = total_faces - visible

        wrong = [hidden + 1, hidden - 1, total_faces]
        wrong = [w for w in wrong if w >= 0 and w != hidden][:3]
        while len(wrong) < 3:
            wrong.append(hidden + random.randint(2, 4))
        choices = [str(hidden)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"{'A cube has' if num_cubes == 1 else f'{num_cubes} cubes are stacked. They have'} {total_faces} faces total. You can see {visible} faces. How many faces are hidden?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "cube-faces", "medium"],
            "needs_visual": True,
        })

    # Handshake/line problems
    for _ in range(15):
        n = random.randint(3, 7)
        # Each person shakes hands with every other person
        answer = n * (n - 1) // 2

        wrong = [answer + 1, n * (n - 1), n * n]
        wrong = [w for w in wrong if w > 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 5))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"{n} friends meet at a party. Each friend shakes hands with every other friend exactly once. How many handshakes happen in total?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "combinatorics", "medium"],
            "needs_visual": random.random() < 0.3,
        })

    # Calendar/time counting
    for _ in range(15):
        month_days = random.choice([28, 30, 31])
        day_type = random.choice(["Mondays", "Tuesdays", "Sundays", "Saturdays"])
        answer = month_days // 7
        if month_days % 7 > 0:
            answer_options = [4, 5]
        else:
            answer_options = [4]
        answer = random.choice(answer_options)

        wrong = [answer + 1, answer - 1, answer + 2]
        wrong = [w for w in wrong if w > 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 4))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        month = random.choice(["January", "March", "April", "May", "June", "October"])
        templates.append({
            "stem": f"How many {day_type} can {month} have at most?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "calendar", "medium"],
            "needs_visual": False,
        })

    # Digit counting
    for _ in range(15):
        end = random.choice([20, 30, 50, 100])
        digit = random.choice([1, 2, 3, 5])
        answer = sum(1 for n in range(1, end + 1) for d in str(n) if int(d) == digit)

        wrong = [answer + 1, answer - 1, answer + 2]
        wrong = [w for w in wrong if w >= 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 5))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        name = random.choice(names)
        templates.append({
            "stem": f"{name} writes all numbers from 1 to {end}. How many times does the digit '{digit}' appear?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "digits", "medium"],
            "needs_visual": False,
        })

    return templates


def _counting_g2_hard_templates():
    """Grade 2 hard counting questions (scores 81-100)."""
    templates = []
    names = ["Ria", "Aman", "Zara", "Leo", "Mia", "Sam", "Tom", "Priya"]

    # Chickens and rabbits
    for _ in range(15):
        chickens = random.randint(2, 10)
        rabbits = random.randint(2, 10)
        heads = chickens + rabbits
        legs = 2 * chickens + 4 * rabbits

        wrong = [chickens + 1, chickens - 1, rabbits]
        wrong = [w for w in wrong if w > 0 and w != chickens][:3]
        while len(wrong) < 3:
            wrong.append(chickens + random.randint(2, 4))
        choices = [str(chickens)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"A farmer has chickens and rabbits. There are {heads} heads and {legs} legs. How many chickens are there?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "logic", "hard"],
            "needs_visual": random.random() < 0.3,
        })

    # Grid coloring constraints
    for _ in range(10):
        grid_size = random.choice([3, 4, 5])
        colored_per_row = random.randint(1, grid_size - 1)
        answer = grid_size * colored_per_row

        wrong = [answer + 1, answer - 1, grid_size * grid_size]
        wrong = [w for w in wrong if w > 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 5))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"In a {grid_size}x{grid_size} grid, you must colour exactly {colored_per_row} squares in each row and each column. How many squares are coloured?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "grid-constraint", "hard"],
            "needs_visual": True,
        })

    # Tournament/match counting
    for _ in range(10):
        teams = random.randint(4, 8)
        # Round-robin
        answer = teams * (teams - 1) // 2

        wrong = [answer + 1, teams * (teams - 1), teams * teams]
        wrong = [w for w in wrong if w > 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 5))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"In a tournament, {teams} teams play each other exactly once. How many matches are there in total?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "combinatorics", "hard"],
            "needs_visual": random.random() < 0.2,
        })

    # Path counting on grids
    for _ in range(10):
        rows = random.choice([2, 3])
        cols = random.choice([2, 3])
        # Shortest paths from top-left to bottom-right
        from math import comb
        answer = comb(rows + cols, rows)

        wrong = [answer + 1, answer - 1, answer * 2]
        wrong = [w for w in wrong if w > 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 5))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"On a {rows + 1}x{cols + 1} grid, how many shortest paths are there from the top-left corner to the bottom-right corner if you can only move right or down?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "paths", "hard"],
            "needs_visual": True,
        })

    # Number puzzles
    for _ in range(15):
        # Sum of digits
        target = random.randint(15, 50)
        n = random.randint(2, 3)
        answer = sum(int(d) for d in str(target))

        wrong = [answer + 1, answer - 1, target // 10]
        wrong = [w for w in wrong if w >= 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 4))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        name = random.choice(names)
        templates.append({
            "stem": f"What is the sum of the digits of the number {target}?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "digits", "hard"],
            "needs_visual": False,
        })

    # Staircase/triangle number counting
    for _ in range(10):
        rows = random.randint(3, 7)
        answer = rows * (rows + 1) // 2

        wrong = [answer + 1, answer - 1, rows * rows]
        wrong = [w for w in wrong if w > 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(2, 5))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"A staircase is built with blocks. Row 1 has 1 block, Row 2 has 2 blocks, Row 3 has 3 blocks, and so on up to Row {rows}. How many blocks are used in total?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "triangle-numbers", "hard"],
            "needs_visual": True,
        })

    # Clock/time puzzles
    for _ in range(10):
        hour = random.randint(1, 12)
        chimes = hour
        # Some clocks also chime once on the half hour
        total_in_day = sum(range(1, 13)) * 2  # 12-hour cycle twice
        answer = total_in_day

        wrong = [answer + 6, answer - 12, 12 * 12]
        wrong = [w for w in wrong if w > 0 and w != answer][:3]
        while len(wrong) < 3:
            wrong.append(answer + random.randint(5, 15))
        choices = [str(answer)] + [str(w) for w in wrong[:3]]
        combined = list(enumerate(choices))
        random.shuffle(combined)
        new_correct = next(i for i, (orig, _) in enumerate(combined) if orig == 0)

        templates.append({
            "stem": f"A clock chimes the number of the hour (1 chime at 1 o'clock, 2 at 2 o'clock, etc.). How many times does the clock chime in a full day (24 hours)?",
            "choices": [c for _, c in combined],
            "correct_answer": new_correct,
            "tags": ["counting", "clock", "hard"],
            "needs_visual": False,
        })

    return templates


def generate_hints(q: Dict) -> Dict[str, str]:
    """Generate 6-level Socratic hint ladder for a question."""
    stem = q["stem"]
    answer = q["choices"][q["correct_answer"]]
    tier = q.get("difficulty_tier", "easy")

    hints = {
        "level_0": "What do you notice?",
        "level_1": "What information is given?",
        "level_2": "What are you asked to find?",
        "level_3": "Try breaking the problem into smaller parts.",
        "level_4": "Check your work by counting again carefully.",
        "level_5": f"The answer is {answer}. Here is how to think about it step by step.",
    }

    # Customize based on tags
    tags = q.get("tags", [])
    if "addition" in tags:
        hints["level_1"] = "How many groups do you need to add together?"
        hints["level_2"] = "Start by counting the first group, then add the second."
        hints["level_3"] = "Point to each item and count one by one."
    elif "subtraction" in tags:
        hints["level_1"] = "What do you start with?"
        hints["level_2"] = "How many are taken away?"
        hints["level_3"] = "Start from the bigger number and count backwards."
    elif "multiplication" in tags:
        hints["level_1"] = "How many groups are there?"
        hints["level_2"] = "How many are in each group?"
        hints["level_3"] = "Count by adding the same number again and again."
    elif "comparison" in tags:
        hints["level_1"] = "Which number is bigger? Which is smaller?"
        hints["level_2"] = "Find the difference between the two numbers."
        hints["level_3"] = "Subtract the smaller from the bigger."
    elif "combinatorics" in tags:
        hints["level_1"] = "Think about pairing up items systematically."
        hints["level_2"] = "Start with one item and count how many it pairs with."
        hints["level_3"] = "Be careful not to count the same pair twice!"
    elif "skip-counting" in tags:
        hints["level_1"] = "What pattern do you see in the numbers?"
        hints["level_2"] = "What is the gap between each number?"
        hints["level_3"] = "Add the same gap to the last number."

    return hints


def generate_svg(q: Dict, q_id: str) -> Optional[str]:
    """Generate a simple SVG visual for a counting question."""
    tags = q.get("tags", [])
    stem = q.get("stem", "")

    # Simple object grid SVGs
    svg_templates = {
        "animal_legs": """<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="120" fill="#f0f8ff" rx="8"/>
  {objects}
  <text x="100" y="110" text-anchor="middle" font-size="10" fill="#666">Count the legs!</text>
</svg>""",
        "objects_grid": """<svg viewBox="0 0 200 150" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="150" fill="#fff8f0" rx="8"/>
  {objects}
</svg>""",
        "dice": """<svg viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="100" fill="#f0fff0" rx="8"/>
  {objects}
</svg>""",
        "grid": """<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="200" fill="#f8f8ff" rx="8"/>
  {objects}
</svg>""",
        "staircase": """<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="200" fill="#fff0f5" rx="8"/>
  {objects}
</svg>""",
    }

    if "multiplication" in tags or "animal" in stem.lower() or "legs" in stem.lower():
        # Draw circles representing animals
        objects = []
        # Extract count from stem
        nums = re.findall(r'\b(\d+)\b', stem)
        count = int(nums[0]) if nums else 3
        count = min(count, 8)
        for i in range(count):
            x = 30 + (i % 4) * 45
            y = 25 + (i // 4) * 40
            objects.append(f'<circle cx="{x}" cy="{y}" r="12" fill="#4CAF50" opacity="0.8"/>')
            objects.append(f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="10" fill="white">{i+1}</text>')
        return svg_templates["objects_grid"].format(objects="\n  ".join(objects))

    elif "grid" in tags or "grid" in stem.lower() or "rows" in stem.lower():
        nums = re.findall(r'\b(\d+)\b', stem)
        rows = int(nums[0]) if len(nums) > 0 else 3
        cols = int(nums[1]) if len(nums) > 1 else 3
        rows, cols = min(rows, 6), min(cols, 6)
        objects = []
        size = min(25, 160 // max(rows, cols))
        for r in range(rows):
            for c in range(cols):
                x = 20 + c * (size + 5)
                y = 20 + r * (size + 5)
                objects.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="#2196F3" opacity="0.6" rx="3"/>')
        return svg_templates["grid"].format(objects="\n  ".join(objects))

    elif "dice" in tags or "dice" in stem.lower():
        objects = []
        nums = re.findall(r'\b([1-6])\b', stem)
        for i, val in enumerate(nums[:4]):
            x = 30 + i * 50
            objects.append(f'<rect x="{x}" y="15" width="40" height="40" fill="white" stroke="#333" stroke-width="2" rx="5"/>')
            # Simple dot for the value
            objects.append(f'<text x="{x+20}" y="42" text-anchor="middle" font-size="20" fill="#333">{val}</text>')
        return svg_templates["dice"].format(objects="\n  ".join(objects))

    elif "staircase" in stem.lower() or "triangle" in tags:
        nums = re.findall(r'\b(\d+)\b', stem)
        rows = int(nums[-1]) if nums else 4
        rows = min(rows, 7)
        objects = []
        block_size = min(20, 150 // rows)
        for r in range(rows):
            for c in range(r + 1):
                x = 20 + c * (block_size + 2)
                y = 180 - (rows - r) * (block_size + 2)
                color = f"hsl({r * 40}, 70%, 60%)"
                objects.append(f'<rect x="{x}" y="{y}" width="{block_size}" height="{block_size}" fill="{color}" rx="2"/>')
        return svg_templates["staircase"].format(objects="\n  ".join(objects))

    else:
        # Generic counting visual - colored circles
        objects = []
        nums = re.findall(r'\b(\d+)\b', stem)
        count = int(nums[0]) if nums else 5
        count = min(count, 12)
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8", "#F7DC6F"]
        for i in range(count):
            x = 25 + (i % 5) * 35
            y = 30 + (i // 5) * 35
            color = colors[i % len(colors)]
            objects.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{color}"/>')
            objects.append(f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="9" fill="white" font-weight="bold">{i+1}</text>')
        return svg_templates["objects_grid"].format(objects="\n  ".join(objects))


def generate_questions_for_topic(topic_id: str) -> Dict[str, Any]:
    """Generate all new questions for a topic."""
    print(f"\n{'='*60}")
    print(f"Generating questions for: {topic_id}")
    print(f"{'='*60}")

    data = load_topic(topic_id)
    existing = data["questions"]
    existing_ids = get_existing_ids(existing)
    existing_stems = get_existing_stems(existing)
    meta = TOPIC_MAP[topic_id]
    prefix = meta["prefix"]
    visual_pct = meta["visual_pct"]

    # Count existing per grade
    g1_existing = [q for q in existing if q["difficulty_score"] <= 50]
    g2_existing = [q for q in existing if q["difficulty_score"] > 50]
    g1_needed = TARGET_PER_GRADE - len(g1_existing)
    g2_needed = TARGET_PER_GRADE - len(g2_existing)

    print(f"  G1: have {len(g1_existing)}, need {g1_needed} more")
    print(f"  G2: have {len(g2_existing)}, need {g2_needed} more")

    # Get difficulty distribution for each grade
    g1_dist = GRADE_DIST[1]
    g2_dist = GRADE_DIST[2]

    # Generate candidate questions
    if topic_id == "counting_observation":
        g1_easy_pool = _counting_g1_easy_templates()
        g1_med_pool = _counting_g1_medium_templates()
        g2_med_pool = _counting_g2_medium_templates()
        g2_hard_pool = _counting_g2_hard_templates()
    else:
        print(f"  WARNING: No generator for {topic_id} yet, skipping")
        return {"generated": 0}

    # Select and deduplicate
    new_questions = []
    next_num = max(int(q["id"].split("-")[-1]) for q in existing) + 1

    def _add_questions(pool, tier, count, score_range):
        nonlocal next_num
        random.shuffle(pool)
        added = 0
        for q in pool:
            if added >= count:
                break
            stem_norm = re.sub(r'\s+', ' ', q["stem"].lower().strip())
            if stem_norm in existing_stems:
                continue

            # Assign ID and score
            qid = f"{prefix}-{next_num:03d}"
            score = random.randint(score_range[0], score_range[1])

            q_full = {
                "id": qid,
                "stem": q["stem"],
                "original_stem": q["stem"],
                "choices": q["choices"],
                "correct_answer": q["correct_answer"],
                "difficulty_tier": tier,
                "difficulty_score": score,
                "visual_svg": None,
                "visual_alt": None,
                "diagnostics": {},
                "topic": topic_id,
                "topic_name": data["topic_name"],
                "tags": q.get("tags", [tier]),
                "hint": generate_hints(q),
            }

            # Generate visual if needed
            needs_vis = q.get("needs_visual", False)
            if needs_vis or random.random() < visual_pct:
                svg = generate_svg(q, qid)
                if svg:
                    svg_filename = f"{qid.lower()}.svg"
                    q_full["visual_svg"] = svg_filename
                    q_full["visual_alt"] = f"Visual aid for: {q['stem'][:60]}"
                    q_full["_svg_content"] = svg  # Temporary, for writing to file

            new_questions.append(q_full)
            existing_stems.add(stem_norm)
            next_num += 1
            added += 1

        return added

    # G1 questions
    g1_easy_count = int(g1_needed * g1_dist["easy"] / (g1_dist["easy"] + g1_dist["medium"]))
    g1_med_count = g1_needed - g1_easy_count

    print(f"\n  Generating G1: {g1_easy_count} easy + {g1_med_count} medium")
    added_easy = _add_questions(g1_easy_pool, "easy", g1_easy_count, (1, 40))
    added_med = _add_questions(g1_med_pool, "medium", g1_med_count, (41, 50))
    print(f"  Added G1: {added_easy} easy + {added_med} medium = {added_easy + added_med}")

    # G2 questions
    g2_med_count = int(g2_needed * g2_dist["medium"] / (g2_dist["medium"] + g2_dist["hard"]))
    g2_hard_count = g2_needed - g2_med_count

    print(f"\n  Generating G2: {g2_med_count} medium + {g2_hard_count} hard")
    added_med2 = _add_questions(g2_med_pool, "medium", g2_med_count, (51, 80))
    added_hard = _add_questions(g2_hard_pool, "hard", g2_hard_count, (81, 100))
    print(f"  Added G2: {added_med2} medium + {added_hard} hard = {added_med2 + added_hard}")

    return {
        "topic_id": topic_id,
        "existing_count": len(existing),
        "new_questions": new_questions,
        "new_count": len(new_questions),
        "visual_count": sum(1 for q in new_questions if q.get("visual_svg")),
    }


def run_qa(questions: List[Dict], visual_dir: Path) -> Dict[str, Any]:
    """Run QA on all questions, double-check visual ones."""
    results = {"total": len(questions), "passed": 0, "failed": 0, "issues": []}

    for q in questions:
        score = compute_qa_score(q)
        q["_qa_score"] = score

        issues = []
        if score < 8:
            issues.append(f"Low QA score: {score}/10")

        # Check for duplicate choices
        if len(set(str(c).strip() for c in q.get("choices", []))) < 4:
            issues.append("Duplicate choices detected")

        # Check stem quality
        stem = q.get("stem", "")
        if len(stem) < 15:
            issues.append("Stem too short")
        if not stem.endswith("?"):
            issues.append("Missing question mark")

        # Double QA for visual questions
        if q.get("visual_svg"):
            svg_path = visual_dir / q["visual_svg"]
            svg_content = q.get("_svg_content", "")
            if svg_content:
                v_issues = visual_qa(q, svg_content)
                issues.extend(v_issues)
            else:
                issues.append("Visual referenced but no SVG content generated")

        if issues:
            results["failed"] += 1
            results["issues"].append({"id": q["id"], "issues": issues, "score": score})
        else:
            results["passed"] += 1

    return results


def save_questions(topic_id: str, new_questions: List[Dict]):
    """Save new questions into the topic's questions.json and SVG files."""
    meta = TOPIC_MAP[topic_id]
    topic_dir = CONTENT_DIR / meta["dir"]
    qpath = topic_dir / "questions.json"
    vis_dir = topic_dir / "visuals"
    vis_dir.mkdir(exist_ok=True)

    # Load existing
    data = json.loads(qpath.read_text())

    # Write SVGs and clean temp fields
    svg_count = 0
    for q in new_questions:
        svg_content = q.pop("_svg_content", None)
        q.pop("_qa_score", None)
        if svg_content and q.get("visual_svg"):
            svg_path = vis_dir / q["visual_svg"]
            svg_path.write_text(svg_content)
            svg_count += 1

    # Merge into existing
    data["questions"].extend(new_questions)

    # Re-sort by difficulty_score
    data["questions"].sort(key=lambda q: q["difficulty_score"])

    # Update total
    data["total_questions"] = len(data["questions"])

    # Write back
    qpath.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    print(f"\n  Saved {len(new_questions)} questions + {svg_count} SVGs to {topic_dir.name}/")
    return len(new_questions), svg_count


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scale Kiwimath content")
    parser.add_argument("--topic", default="counting_observation",
                        help="Topic ID to scale")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate but don't save")
    args = parser.parse_args()

    random.seed(42)  # Reproducible

    result = generate_questions_for_topic(args.topic)
    if not result.get("new_questions"):
        print("No questions generated.")
        sys.exit(1)

    new_qs = result["new_questions"]
    meta = TOPIC_MAP[args.topic]
    vis_dir = CONTENT_DIR / meta["dir"] / "visuals"

    # Run QA
    print(f"\n{'='*60}")
    print("Running QA...")
    qa = run_qa(new_qs, vis_dir)
    print(f"  Total: {qa['total']} | Passed: {qa['passed']} | Failed: {qa['failed']}")
    if qa["issues"]:
        print(f"  Issues found in {len(qa['issues'])} questions:")
        for iss in qa["issues"][:10]:
            print(f"    {iss['id']} (score {iss['score']}): {', '.join(iss['issues'][:3])}")

    # Auto-fix common issues
    fixed = 0
    for q in new_qs:
        if not q["stem"].endswith("?"):
            q["stem"] = q["stem"].rstrip(".!") + "?"
            fixed += 1
    if fixed:
        print(f"  Auto-fixed {fixed} missing question marks")

    if not args.dry_run:
        save_questions(args.topic, new_qs)
    else:
        print("\n  DRY RUN — not saving.")

    print(f"\n{'='*60}")
    print(f"SUMMARY for {args.topic}:")
    print(f"  Existing: {result['existing_count']}")
    print(f"  New: {result['new_count']}")
    print(f"  With visuals: {result['visual_count']}")
    print(f"  Total: {result['existing_count'] + result['new_count']}")
    print(f"  QA passed: {qa['passed']}/{qa['total']}")
