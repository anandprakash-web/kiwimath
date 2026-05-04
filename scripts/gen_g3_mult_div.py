#!/usr/bin/env python3
"""Generate additional G3 multiplication and division questions to fix topic imbalance."""

import json
import os
import random
from datetime import datetime

V4 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'content-v4')

random.seed(42)

def make_question(qid, stem, correct_value, skill_id, irt_b, diagnostics, hint, solution_steps, tags, interaction_mode="integer", choices=None):
    """Build a full v4 question dict."""
    if irt_b < -1.5:
        tier = "intro"
        diff_tier = "easy"
    elif irt_b < 0:
        tier = "developing"
        diff_tier = "medium"
    elif irt_b < 1.5:
        tier = "proficient"
        diff_tier = "medium"
    else:
        tier = "advanced"
        diff_tier = "hard"

    return {
        "id": qid,
        "stem": stem,
        "choices": choices or [],
        "correct_answer": 0,
        "difficulty_tier": diff_tier,
        "difficulty_score": max(1, min(5, int((irt_b + 3) / 1.2) + 1)),
        "visual_svg": None,
        "visual_alt": None,
        "diagnostics": diagnostics,
        "tags": tags,
        "topic": f"g3_{skill_id}",
        "chapter": f"Ch: {'Multiplication' if 'mult' in skill_id else 'Division'}",
        "hint": hint,
        "curriculum_tags": [],
        "irt_params": {"a": round(random.uniform(0.8, 1.5), 2), "b": irt_b, "c": 0.25},
        "irt_a": round(random.uniform(0.8, 1.5), 2),
        "irt_b": irt_b,
        "irt_c": 0.25,
        "solution_steps": solution_steps,
        "interaction_mode": interaction_mode,
        "correct_value": correct_value,
        "level": 3,
        "level_name": "Thinker",
        "universal_skill_id": f"{'MULT_FACTS' if 'mult' in skill_id else 'DIV_BASIC'}_3",
        "skill_id": skill_id,
        "skill_domain": "arithmetic",
        "maturity_bucket": "calibrating",
        "visual_requirement": "none",
        "visual_type": "none",
        "visual_ai_verified": False,
        "media_id": None,
        "media_hash": None,
        "misconception_ids": [],
        "why_quality": "ai_generated",
        "why_framework": "3R",
        "hint_quality": {"layers": 3, "quality": "good", "has_3_layers": True},
        "curriculum_source": "generated",
        "curriculum_map": {},
        "school_grade": 3,
        "avg_time_to_solve_ms": None,
        "times_served": 0,
        "flag_count": 0,
        "schema_version": "4.1",
        "adaptive_topic_id": f"g3-{'multiplication' if 'mult' in skill_id else 'division'}",
        "adaptive_topic_name": "Multiplication" if "mult" in skill_id else "Division",
        "adaptive_topic_emoji": "✖️" if "mult" in skill_id else "➗",
        "adaptive_grade": 3,
        "dual_tagged": False,
        "content_source": "generated",
        "sequence_id": 0,
        "difficulty_tier_in_topic": tier,
        "locale_ids": ["india", "singapore", "us", "global"],
        "fixed_at": datetime.now().isoformat(),
    }


def generate_multiplication_questions():
    """Generate ~185 multiplication questions across difficulty levels."""
    questions = []
    idx = 0

    # --- EASY (irt_b -3 to -1.5): Single-digit × single-digit ---
    tables = list(range(2, 11))
    for a in tables:
        for b in range(1, 11):
            if idx >= 50:
                break
            product = a * b
            irt_b = round(-3.0 + (idx / 50) * 1.5, 2)
            qid = f"GEN-G3M-{idx+1:03d}"
            questions.append(make_question(
                qid=qid,
                stem=f"What is {a} × {b}?",
                correct_value=product,
                skill_id="multiplication_facts",
                irt_b=irt_b,
                diagnostics={
                    "1": f"Not quite. {a} × {b} means {a} groups of {b}. Count again.",
                    "2": f"You may have confused the tables. {a} × {b} = {product}.",
                },
                hint={
                    "level_0": "Think about multiplication as repeated addition.",
                    "level_1": f"How much is {a} groups of {b}?",
                    "level_2": f"Add {b} to itself {a} times.",
                },
                solution_steps=[f"Think of {a} groups of {b}", f"{a} × {b} = {product}"],
                tags=["multiplication", "times_tables", "grade3"],
            ))
            idx += 1
        if idx >= 50:
            break

    # --- MEDIUM (irt_b -1.5 to 0.5): 2-digit × 1-digit ---
    medium_pairs = []
    for a in range(11, 30):
        for b in range(2, 10):
            medium_pairs.append((a, b))
    random.shuffle(medium_pairs)

    for a, b in medium_pairs[:60]:
        product = a * b
        irt_b = round(-1.5 + (len(questions) - 50) / 60 * 2.0, 2)
        qid = f"GEN-G3M-{len(questions)+1:03d}"
        questions.append(make_question(
            qid=qid,
            stem=f"Calculate {a} × {b}.",
            correct_value=product,
            skill_id="multiplication_facts",
            irt_b=irt_b,
            diagnostics={
                "1": f"Break it down: {a} = {a//10*10} + {a%10}. Multiply each part by {b} and add.",
                "2": f"Double-check: ({a//10*10} × {b}) + ({a%10} × {b}) = {a//10*10*b} + {a%10*b} = {product}.",
            },
            hint={
                "level_0": "Break the bigger number into tens and ones.",
                "level_1": f"Split {a} into {a//10*10} and {a%10}. Multiply each by {b}.",
                "level_2": f"({a//10*10} × {b}) + ({a%10} × {b}) = ?",
            },
            solution_steps=[f"Split: {a} = {a//10*10} + {a%10}", f"{a//10*10} × {b} = {a//10*10*b}", f"{a%10} × {b} = {a%10*b}", f"Add: {a//10*10*b} + {a%10*b} = {product}"],
            tags=["multiplication", "2digit_by_1digit", "grade3"],
        ))

    # --- MEDIUM-HARD: Word problems with multiplication ---
    names = ["Aarav", "Priya", "Wei", "Emma", "Rohan", "Mei", "Liam", "Diya"]
    objects = ["stickers", "marbles", "pencils", "books", "cookies", "flowers", "stamps", "beads"]
    word_problems = []
    for i in range(40):
        name = names[i % len(names)]
        obj = objects[i % len(objects)]
        groups = random.randint(3, 9)
        per_group = random.randint(4, 12)
        total = groups * per_group
        irt_b = round(0.0 + i / 40 * 1.5, 2)
        qid = f"GEN-G3M-{len(questions)+1:03d}"
        questions.append(make_question(
            qid=qid,
            stem=f"{name} has {groups} bags with {per_group} {obj} in each bag. How many {obj} does {name} have in all?",
            correct_value=total,
            skill_id="multiplication_facts",
            irt_b=irt_b,
            diagnostics={
                "1": f"You need to multiply, not add. {groups} bags × {per_group} {obj} = ?",
                "2": f"Count {groups} groups of {per_group}. That gives {total}.",
            },
            hint={
                "level_0": "How many groups are there? How many in each group?",
                "level_1": f"There are {groups} bags with {per_group} in each. Multiply them.",
                "level_2": f"{groups} × {per_group} = ?",
            },
            solution_steps=[f"Identify: {groups} groups of {per_group}", f"Multiply: {groups} × {per_group} = {total}"],
            tags=["multiplication", "word_problem", "grade3"],
        ))

    # --- HARD (irt_b 1.5 to 3.0): 2-digit × 2-digit and missing factor ---
    for i in range(35):
        if i < 20:
            a = random.randint(11, 25)
            b = random.randint(11, 20)
            product = a * b
            irt_b = round(1.5 + i / 20 * 1.0, 2)
            qid = f"GEN-G3M-{len(questions)+1:03d}"
            questions.append(make_question(
                qid=qid,
                stem=f"What is {a} × {b}?",
                correct_value=product,
                skill_id="multiplication_facts",
                irt_b=irt_b,
                diagnostics={
                    "1": f"Use the standard method: multiply {a} by ones digit of {b}, then tens digit.",
                    "2": f"Step by step: {a}×{b%10} = {a*(b%10)}, {a}×{b//10*10} = {a*(b//10)*10}. Add them.",
                },
                hint={
                    "level_0": "Use long multiplication or break the numbers apart.",
                    "level_1": f"Try ({a} × {b%10}) + ({a} × {b//10} × 10).",
                    "level_2": f"{a*(b%10)} + {a*(b//10)*10} = ?",
                },
                solution_steps=[f"{a} × {b%10} = {a*(b%10)}", f"{a} × {b//10} × 10 = {a*(b//10)*10}", f"Add: {a*(b%10)} + {a*(b//10)*10} = {product}"],
                tags=["multiplication", "2digit_by_2digit", "grade3"],
            ))
        else:
            # Missing factor
            a = random.randint(3, 12)
            product = a * random.randint(3, 12)
            b = product // a
            irt_b = round(2.0 + (i - 20) / 15 * 1.0, 2)
            qid = f"GEN-G3M-{len(questions)+1:03d}"
            questions.append(make_question(
                qid=qid,
                stem=f"{a} × ___ = {product}. What is the missing number?",
                correct_value=b,
                skill_id="multiplication_facts",
                irt_b=irt_b,
                diagnostics={
                    "1": f"Think: what number times {a} gives {product}? Try using division.",
                    "2": f"{product} ÷ {a} = {b}. So the missing number is {b}.",
                },
                hint={
                    "level_0": "Division is the inverse of multiplication.",
                    "level_1": f"Divide {product} by {a} to find the missing factor.",
                    "level_2": f"{product} ÷ {a} = ?",
                },
                solution_steps=[f"Think: {a} × ? = {product}", f"Divide: {product} ÷ {a} = {b}"],
                tags=["multiplication", "missing_factor", "grade3"],
            ))

    return questions


def generate_division_questions():
    """Generate ~220 division questions across difficulty levels."""
    questions = []

    # --- EASY: Basic division facts ---
    for i in range(50):
        divisor = random.randint(2, 10)
        quotient = random.randint(1, 10)
        dividend = divisor * quotient
        irt_b = round(-3.0 + i / 50 * 1.5, 2)
        qid = f"GEN-G3D-{len(questions)+1:03d}"
        questions.append(make_question(
            qid=qid,
            stem=f"What is {dividend} ÷ {divisor}?",
            correct_value=quotient,
            skill_id="division_basic",
            irt_b=irt_b,
            diagnostics={
                "1": f"Think: how many groups of {divisor} make {dividend}?",
                "2": f"Use your {divisor} times table. {divisor} × {quotient} = {dividend}.",
            },
            hint={
                "level_0": "Division means sharing equally into groups.",
                "level_1": f"How many times does {divisor} fit into {dividend}?",
                "level_2": f"Think: {divisor} × ? = {dividend}.",
            },
            solution_steps=[f"How many {divisor}s in {dividend}?", f"{divisor} × {quotient} = {dividend}", f"So {dividend} ÷ {divisor} = {quotient}"],
            tags=["division", "basic_facts", "grade3"],
        ))

    # --- MEDIUM: 2-digit ÷ 1-digit ---
    for i in range(60):
        divisor = random.randint(2, 9)
        quotient = random.randint(11, 30)
        dividend = divisor * quotient
        irt_b = round(-1.5 + i / 60 * 2.0, 2)
        qid = f"GEN-G3D-{len(questions)+1:03d}"
        questions.append(make_question(
            qid=qid,
            stem=f"Divide {dividend} by {divisor}.",
            correct_value=quotient,
            skill_id="division_basic",
            irt_b=irt_b,
            diagnostics={
                "1": f"Try long division: how many times does {divisor} go into {dividend//10*10}? Then handle the remainder.",
                "2": f"Break it down: {dividend} = {divisor} × {quotient}.",
            },
            hint={
                "level_0": "Use long division — divide digit by digit.",
                "level_1": f"First divide {dividend // 10 * 10} by {divisor}, then handle the rest.",
                "level_2": f"{divisor} × ? = {dividend}. Try counting up.",
            },
            solution_steps=[f"Divide: {dividend} ÷ {divisor}", f"= {quotient}"],
            tags=["division", "2digit_by_1digit", "grade3"],
        ))

    # --- MEDIUM-HARD: Division word problems ---
    names = ["Arjun", "Ananya", "Hao", "Sophia", "Vihaan", "Xin", "Noah", "Isha"]
    objects = ["sweets", "oranges", "cards", "crayons", "apples", "stickers", "toys", "coins"]
    for i in range(50):
        name = names[i % len(names)]
        obj = objects[i % len(objects)]
        groups = random.randint(3, 10)
        per_group = random.randint(3, 12)
        total = groups * per_group
        irt_b = round(0.0 + i / 50 * 1.5, 2)
        qid = f"GEN-G3D-{len(questions)+1:03d}"

        # Vary the word problem format
        if i % 3 == 0:
            stem = f"{name} has {total} {obj} to share equally among {groups} friends. How many {obj} does each friend get?"
        elif i % 3 == 1:
            stem = f"There are {total} {obj} arranged in {groups} equal rows. How many {obj} are in each row?"
        else:
            stem = f"A box of {total} {obj} is packed into bags of {per_group} each. How many bags are needed?"
            # For this variant, answer is groups
            per_group, groups = groups, per_group  # swap so correct_value works

        questions.append(make_question(
            qid=qid,
            stem=stem,
            correct_value=per_group,
            skill_id="division_basic",
            irt_b=irt_b,
            diagnostics={
                "1": f"You need to divide here, not multiply. {total} ÷ {groups} = ?",
                "2": f"Share {total} into {groups} equal parts: each gets {per_group}.",
            },
            hint={
                "level_0": "This is a sharing (division) problem.",
                "level_1": f"You have {total} things to split into {groups} equal parts.",
                "level_2": f"{total} ÷ {groups} = ?",
            },
            solution_steps=[f"Total: {total}", f"Groups: {groups}", f"{total} ÷ {groups} = {per_group}"],
            tags=["division", "word_problem", "grade3"],
        ))

    # --- HARD: Division with remainder and 3-digit ÷ 1-digit ---
    for i in range(30):
        divisor = random.randint(3, 9)
        quotient = random.randint(20, 99)
        dividend = divisor * quotient
        irt_b = round(1.5 + i / 30 * 1.5, 2)
        qid = f"GEN-G3D-{len(questions)+1:03d}"
        questions.append(make_question(
            qid=qid,
            stem=f"What is {dividend} ÷ {divisor}?",
            correct_value=quotient,
            skill_id="division_basic",
            irt_b=irt_b,
            diagnostics={
                "1": f"Use long division carefully. {divisor} goes into {dividend} exactly {quotient} times.",
                "2": f"Break it down step by step using long division.",
            },
            hint={
                "level_0": "For larger numbers, use long division.",
                "level_1": f"Start with: how many times does {divisor} go into {str(dividend)[0]}? Or into {str(dividend)[:2]}?",
                "level_2": f"Work through: {dividend} ÷ {divisor} step by step.",
            },
            solution_steps=[f"Long division: {dividend} ÷ {divisor}", f"= {quotient}"],
            tags=["division", "3digit_by_1digit", "grade3"],
        ))

    # --- HARD: Missing dividend ---
    for i in range(30):
        divisor = random.randint(3, 9)
        quotient = random.randint(4, 15)
        dividend = divisor * quotient
        irt_b = round(2.0 + i / 30 * 1.0, 2)
        qid = f"GEN-G3D-{len(questions)+1:03d}"
        questions.append(make_question(
            qid=qid,
            stem=f"___ ÷ {divisor} = {quotient}. What is the missing number?",
            correct_value=dividend,
            skill_id="division_basic",
            irt_b=irt_b,
            diagnostics={
                "1": f"To find the missing dividend, multiply: {divisor} × {quotient} = ?",
                "2": f"Multiplication undoes division: {divisor} × {quotient} = {dividend}.",
            },
            hint={
                "level_0": "Use the inverse operation — multiplication.",
                "level_1": f"If ? ÷ {divisor} = {quotient}, then ? = {divisor} × {quotient}.",
                "level_2": f"{divisor} × {quotient} = ?",
            },
            solution_steps=[f"? ÷ {divisor} = {quotient}", f"? = {divisor} × {quotient} = {dividend}"],
            tags=["division", "missing_dividend", "grade3"],
        ))

    return questions


def main():
    print("=" * 60)
    print("GENERATING G3 MULTIPLICATION & DIVISION QUESTIONS")
    print("=" * 60)

    # Generate
    mult_qs = generate_multiplication_questions()
    div_qs = generate_division_questions()
    print(f"Generated {len(mult_qs)} multiplication questions")
    print(f"Generated {len(div_qs)} division questions")

    # Load existing files
    for topic_name, new_qs in [("g3-multiplication", mult_qs), ("g3-division", div_qs)]:
        path = os.path.join(V4, "adaptive", "grade3", f"{topic_name}.json")
        with open(path) as f:
            data = json.load(f)

        existing_ids = {q["id"] for q in data["questions"]}
        added = [q for q in new_qs if q["id"] not in existing_ids]

        data["questions"].extend(added)
        # Re-sort by irt_b
        data["questions"].sort(key=lambda q: q.get("irt_b", 0))
        # Reassign sequence_id
        for i, q in enumerate(data["questions"]):
            q["sequence_id"] = i + 1
        data["total_questions"] = len(data["questions"])
        # Update difficulty range
        bs = [q["irt_b"] for q in data["questions"] if q.get("irt_b") is not None]
        if bs:
            data["difficulty_range"] = {"min_irt_b": min(bs), "max_irt_b": max(bs)}
        data["fixed_at"] = datetime.now().isoformat()

        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  {topic_name}: {len(data['questions'])} total ({len(added)} new)")

    # Regenerate index
    import glob
    grade_dir = os.path.join(V4, "adaptive", "grade3")
    topic_files = sorted(glob.glob(os.path.join(grade_dir, "g3-*.json")))
    topics = []
    total = 0
    for tf in sorted(topic_files):
        if "index" in tf:
            continue
        with open(tf) as f:
            d = json.load(f)
        topics.append({
            "id": d["topic_id"],
            "name": d["topic_name"],
            "emoji": d.get("topic_emoji", ""),
            "domain": d["domain"],
            "skills": d.get("skills", []),
            "total_questions": d["total_questions"],
            "difficulty_range": d.get("difficulty_range", {}),
            "source_breakdown": d.get("source_breakdown", {}),
        })
        total += d["total_questions"]

    index = {
        "grade": 3,
        "total_topics": len(topics),
        "total_questions": total,
        "topics": topics,
        "schema_version": "4.1",
        "generated_at": datetime.now().isoformat(),
    }
    index_path = os.path.join(grade_dir, "index.json")
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"\n  Index regenerated: {len(topics)} topics, {total:,} total questions")


if __name__ == "__main__":
    main()
