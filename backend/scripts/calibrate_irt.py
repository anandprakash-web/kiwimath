#!/usr/bin/env python3
"""
IRT Calibration Script for Kiwimath Content System
===================================================
Assigns Item Response Theory (3PL) parameters to every question:
  - a (discrimination): 0.5 - 2.0
  - b (difficulty):     -3.0 to +3.0
  - c (guessing):       based on number of choices

Reads all JSON files across all curricula and topic folders,
computes IRT params based on metadata, writes them back,
and updates assessment_items.json with all questions.
"""

import json
import glob
import os
import shutil
import sys
from collections import defaultdict

CONTENT_DIR = "/sessions/optimistic-laughing-franklin/mnt/Downloads/kiwimath/content-v2"
BACKEND_DIR = "/sessions/optimistic-laughing-franklin/mnt/Downloads/kiwimath/backend"
ASSESSMENT_FILE = os.path.join(BACKEND_DIR, "assessment_items.json")

# ─── Grade inference ────────────────────────────────────────────────────────

def infer_grade_from_file(filepath):
    """Infer grade level from file path and parent directory."""
    parts = filepath.lower()
    # Curriculum files: .../grade3/... => 3
    for g in range(1, 7):
        if f"/grade{g}/" in parts:
            return g
    # Topic files: questions.json => grades 1-2, grade34 => 3-4, g56 => 5-6
    basename = os.path.basename(parts)
    if "g56" in basename or "g56" in parts:
        return 5  # midpoint of 5-6
    if "grade34" in basename or "grade34" in parts:
        return 3  # midpoint of 3-4
    if "geometry_measurement" in basename or "data_handling" in basename or "measurement_units" in basename:
        return 3  # supplementary files, assume middle
    if "grade34_variety" in basename:
        return 3
    # Default topic questions.json => grades 1-2
    return 1


def infer_grade_from_question(q, file_grade):
    """Try to get grade from question itself, fall back to file-level grade."""
    g = q.get("grade")
    if g and isinstance(g, (int, float)) and 1 <= g <= 6:
        return int(g)
    # Check id prefix for curriculum questions
    qid = q.get("id", "")
    for g in range(1, 7):
        if f"-G{g}-" in qid:
            return g
    return file_grade


# ─── Difficulty (b) computation ─────────────────────────────────────────────

def compute_b(difficulty_score, difficulty_tier, grade, score_max):
    """
    Compute IRT difficulty parameter b.

    Strategy:
    1. Use difficulty_score normalized by file's score_max as primary signal
    2. Apply grade-level adjustment
    3. Clamp to [-3.0, 3.0]
    """
    if difficulty_score is not None and difficulty_score > 0:
        # Normalize score to [0, 1] using the file-level max score
        normalized = difficulty_score / score_max
        # Map to b range: 0 -> -2.5, 1 -> +2.5
        raw_b = -2.5 + normalized * 5.0
    elif difficulty_tier:
        # Fallback: use tier
        tier_map = {
            "easy": -1.5,
            "medium": 0.0,
            "hard": 0.8,
            "advanced": 1.5,
            "expert": 2.0,
            "olympiad": 2.3,
        }
        raw_b = tier_map.get(difficulty_tier.lower(), 0.0)
    else:
        raw_b = 0.0

    # Grade adjustment: shift b based on grade level
    # Grade 1 questions should be easier overall, Grade 6 harder
    # Center at grade 3.5, shift by ~0.2 per grade
    grade_shift = (grade - 3.5) * 0.2
    b = raw_b + grade_shift

    # Clamp
    b = max(-3.0, min(3.0, b))
    return round(b, 2)


# ─── Discrimination (a) computation ────────────────────────────────────────

# Tags that indicate higher discrimination (precise skills)
HIGH_DISC_TAGS = {
    "arithmetic", "addition", "subtraction", "multiplication", "division",
    "place_value", "number_bonds", "fractions", "decimals", "percentages",
    "equations", "algebra", "measurement", "calculation", "computation",
    "mental_math", "long_division", "long_multiplication",
    "part_whole", "number_sequence", "number_comparison",
}

# Tags that indicate lower discrimination (broader/creative)
LOW_DISC_TAGS = {
    "spatial", "puzzle", "pattern_recognition", "creative",
    "estimation", "open_ended", "exploration", "visual_spatial",
}

# Topics with inherently higher discrimination
HIGH_DISC_TOPICS = {
    "arithmetic", "counting", "numbers", "calculation",
    "fractions", "decimals",
}


def compute_a(tags, topic, num_choices, difficulty_tier, diagnostics):
    """
    Compute IRT discrimination parameter a.

    Higher a = question better differentiates ability levels.
    """
    a = 1.0  # base

    # Check tags for precision indicators
    tag_set = set(t.lower() for t in (tags or []))

    high_tag_count = len(tag_set & HIGH_DISC_TAGS)
    low_tag_count = len(tag_set & LOW_DISC_TAGS)

    if high_tag_count > 0:
        a += min(high_tag_count * 0.1, 0.3)
    if low_tag_count > 0:
        a -= min(low_tag_count * 0.1, 0.3)

    # Topic-based adjustment
    topic_lower = (topic or "").lower()
    for ht in HIGH_DISC_TOPICS:
        if ht in topic_lower:
            a += 0.1
            break

    # Good distractors boost discrimination
    # If diagnostics have specific misconception feedback, distractors are well-designed
    if diagnostics:
        if isinstance(diagnostics, dict):
            # Check for detailed diagnostics (common_errors format or keyed feedback)
            if "common_errors" in diagnostics:
                errors = diagnostics["common_errors"]
                if isinstance(errors, list) and len(errors) >= 2:
                    a += 0.15
            elif len(diagnostics) >= 3:
                a += 0.1
        elif isinstance(diagnostics, list) and len(diagnostics) >= 2:
            a += 0.15

    # Number of choices: fewer choices = less discriminating
    if num_choices == 3:
        a -= 0.1
    elif num_choices == 0:
        # Free response: can be highly discriminating
        a += 0.2

    # Higher difficulty tiers tend to be more discriminating
    tier_boost = {
        "easy": -0.05,
        "medium": 0.0,
        "hard": 0.05,
        "advanced": 0.1,
        "expert": 0.15,
        "olympiad": 0.2,
    }
    if difficulty_tier:
        a += tier_boost.get(difficulty_tier.lower(), 0.0)

    # Clamp to [0.5, 2.0]
    a = max(0.5, min(2.0, a))
    return round(a, 2)


# ─── Guessing (c) computation ──────────────────────────────────────────────

def compute_c(num_choices):
    """Compute guessing parameter based on number of answer choices."""
    if num_choices == 0:
        return 0.05  # free response
    elif num_choices == 2:
        return 0.50
    elif num_choices == 3:
        return 0.33
    elif num_choices >= 4:
        return 0.25
    else:
        return 0.25  # default


# ─── Domain inference for assessment_items ──────────────────────────────────

def infer_domain(tags, topic, chapter):
    """Infer the mathematical domain from tags/topic/chapter."""
    all_text = " ".join([
        " ".join(tags or []),
        topic or "",
        chapter or "",
    ]).lower()

    if any(w in all_text for w in ["counting", "numbers", "number_sequence", "place_value", "number_bond"]):
        return "numbers"
    if any(w in all_text for w in ["addition", "subtraction", "multiplication", "division", "arithmetic", "calculation"]):
        return "arithmetic"
    if any(w in all_text for w in ["fraction", "decimal", "percentage", "ratio"]):
        return "fractions"
    if any(w in all_text for w in ["geometry", "shape", "spatial", "symmetry", "angle", "area", "perimeter"]):
        return "geometry"
    if any(w in all_text for w in ["pattern", "sequence", "algebra"]):
        return "patterns"
    if any(w in all_text for w in ["measurement", "units", "weight", "length", "time", "capacity"]):
        return "measurement"
    if any(w in all_text for w in ["word_problem", "word problem", "story"]):
        return "word_problems"
    if any(w in all_text for w in ["data", "graph", "chart", "statistics"]):
        return "data_handling"
    if any(w in all_text for w in ["logic", "puzzle", "reasoning"]):
        return "logic"
    return "general"


# ─── File loading ───────────────────────────────────────────────────────────

def load_all_questions():
    """Load all questions from all JSON files in the content directory."""
    all_questions = []  # list of (question_dict, filepath, file_data_ref)
    file_records = []   # list of (filepath, data, is_list_format)

    json_files = glob.glob(os.path.join(CONTENT_DIR, "**", "*.json"), recursive=True)

    skip_files = {"manifest.json", "master_manifest.json", "visual_registry.json", "tag_clusters.py"}

    for filepath in sorted(json_files):
        basename = os.path.basename(filepath)
        if basename in skip_files:
            continue

        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  WARN: Could not load {filepath}: {e}")
            continue

        questions = []
        is_list = False

        if isinstance(data, dict) and "questions" in data and isinstance(data["questions"], list):
            questions = data["questions"]
            is_list = False
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "id" in data[0]:
            questions = data
            is_list = True
        else:
            continue  # Not a questions file

        if not questions:
            continue

        file_grade = infer_grade_from_file(filepath)

        # Compute the max difficulty_score in this file for normalization
        scores_in_file = [q.get("difficulty_score", 0) for q in questions
                          if q.get("difficulty_score") is not None and q.get("difficulty_score") > 0]
        score_max = max(scores_in_file) if scores_in_file else 100

        file_records.append((filepath, data, is_list, file_grade, score_max))

        for q in questions:
            all_questions.append((q, filepath, file_grade, score_max))

    return all_questions, file_records


# ─── Main calibration ──────────────────────────────────────────────────────

def calibrate():
    print("=" * 70)
    print("IRT CALIBRATION SCRIPT - Kiwimath Content System")
    print("=" * 70)
    print()

    # Load all questions
    print("[1/5] Loading all questions...")
    all_questions, file_records = load_all_questions()
    print(f"  Loaded {len(all_questions)} questions from {len(file_records)} files")
    print()

    # Compute IRT parameters
    print("[2/5] Computing IRT parameters...")
    stats = {
        "total": 0,
        "already_had_irt": 0,
        "newly_assigned": 0,
        "b_values": [],
        "a_values": [],
        "c_values": [],
        "by_grade": defaultdict(int),
        "by_tier": defaultdict(int),
    }

    for q, filepath, file_grade, score_max in all_questions:
        grade = infer_grade_from_question(q, file_grade)
        difficulty_score = q.get("difficulty_score")
        difficulty_tier = q.get("difficulty_tier")
        tags = q.get("tags", [])
        topic = q.get("topic", "")
        chapter = q.get("chapter", "")
        num_choices = len(q.get("choices", []))
        diagnostics = q.get("diagnostics")

        # Compute parameters
        b = compute_b(difficulty_score, difficulty_tier, grade, score_max)
        a = compute_a(tags, topic, num_choices, difficulty_tier, diagnostics)
        c = compute_c(num_choices)

        # Track if it already had IRT params
        if "irt_params" in q:
            stats["already_had_irt"] += 1
        else:
            stats["newly_assigned"] += 1

        # Write IRT params into question (overwrite to ensure consistency)
        q["irt_params"] = {"a": a, "b": b, "c": c}

        # Also add flat fields
        q["irt_a"] = a
        q["irt_b"] = b
        q["irt_c"] = c

        stats["total"] += 1
        stats["b_values"].append(b)
        stats["a_values"].append(a)
        stats["c_values"].append(c)
        stats["by_grade"][grade] += 1
        stats["by_tier"][difficulty_tier or "unknown"] += 1

    print(f"  Processed {stats['total']} questions")
    print(f"  Already had IRT params: {stats['already_had_irt']}")
    print(f"  Newly assigned: {stats['newly_assigned']}")
    print()

    # Write back to files
    print("[3/5] Writing IRT parameters back to content files...")
    files_written = 0
    for filepath, data, is_list, file_grade, score_max in file_records:
        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            files_written += 1
        except IOError as e:
            print(f"  ERROR writing {filepath}: {e}")
    print(f"  Updated {files_written} files")
    print()

    # Build assessment_items.json
    print("[4/5] Building comprehensive assessment_items.json...")

    # Backup existing
    if os.path.exists(ASSESSMENT_FILE):
        backup = ASSESSMENT_FILE + ".bak"
        shutil.copy2(ASSESSMENT_FILE, backup)
        print(f"  Backed up existing file to {backup}")

    assessment_items = []
    seen_ids = set()

    for q, filepath, file_grade, score_max in all_questions:
        qid = q.get("id")
        if not qid or qid in seen_ids:
            continue
        seen_ids.add(qid)

        grade = infer_grade_from_question(q, file_grade)
        tags = q.get("tags", [])
        topic = q.get("topic", "")
        chapter = q.get("chapter", "")
        curriculum_tags = q.get("curriculum_tags", [])

        domain = infer_domain(tags, topic, chapter)

        # Grade range: current grade +/- 1
        grade_lo = max(1, grade - 1)
        grade_hi = min(6, grade + 1)

        item = {
            "item_id": qid,
            "a": q["irt_a"],
            "b": q["irt_b"],
            "c": q["irt_c"],
            "domain": domain,
            "subdomain": topic or "general",
            "curriculum_tags": curriculum_tags,
            "grade_range": [grade_lo, grade_hi],
            "state": "active",
        }
        assessment_items.append(item)

    with open(ASSESSMENT_FILE, "w") as f:
        json.dump(assessment_items, f, indent=2, ensure_ascii=False)
    print(f"  Wrote {len(assessment_items)} assessment items (was 6600)")
    print()

    # Print stats
    print("[5/5] Summary Statistics")
    print("=" * 70)
    print(f"Total questions processed: {stats['total']}")
    print(f"Unique assessment items:   {len(assessment_items)}")
    print()

    # b distribution
    b_vals = stats["b_values"]
    print("─── Difficulty (b) Distribution ───")
    buckets_b = defaultdict(int)
    for b in b_vals:
        if b < -2.0:
            buckets_b["very easy  (b < -2.0)"] += 1
        elif b < -1.0:
            buckets_b["easy       (-2.0 <= b < -1.0)"] += 1
        elif b < 0.0:
            buckets_b["medium-easy(-1.0 <= b < 0.0)"] += 1
        elif b < 1.0:
            buckets_b["medium-hard( 0.0 <= b < 1.0)"] += 1
        elif b < 2.0:
            buckets_b["hard       ( 1.0 <= b < 2.0)"] += 1
        else:
            buckets_b["very hard  ( 2.0 <= b)"] += 1

    for label in sorted(buckets_b.keys()):
        count = buckets_b[label]
        pct = count / len(b_vals) * 100
        bar = "#" * int(pct / 2)
        print(f"  {label}: {count:6d} ({pct:5.1f}%) {bar}")

    print(f"  Mean b: {sum(b_vals)/len(b_vals):.2f}")
    print(f"  Min b:  {min(b_vals):.2f}")
    print(f"  Max b:  {max(b_vals):.2f}")
    print()

    # a distribution
    a_vals = stats["a_values"]
    print("─── Discrimination (a) Distribution ───")
    buckets_a = defaultdict(int)
    for a in a_vals:
        if a < 0.7:
            buckets_a["low    (a < 0.7)"] += 1
        elif a < 1.0:
            buckets_a["medium (0.7 <= a < 1.0)"] += 1
        elif a < 1.3:
            buckets_a["good   (1.0 <= a < 1.3)"] += 1
        elif a < 1.6:
            buckets_a["high   (1.3 <= a < 1.6)"] += 1
        else:
            buckets_a["v.high (1.6 <= a)"] += 1

    for label in sorted(buckets_a.keys()):
        count = buckets_a[label]
        pct = count / len(a_vals) * 100
        bar = "#" * int(pct / 2)
        print(f"  {label}: {count:6d} ({pct:5.1f}%) {bar}")

    print(f"  Mean a: {sum(a_vals)/len(a_vals):.2f}")
    print(f"  Min a:  {min(a_vals):.2f}")
    print(f"  Max a:  {max(a_vals):.2f}")
    print()

    # c distribution
    c_vals = stats["c_values"]
    print("─── Guessing (c) Distribution ───")
    c_counts = defaultdict(int)
    for c in c_vals:
        c_counts[c] += 1
    for c_val in sorted(c_counts.keys()):
        count = c_counts[c_val]
        print(f"  c = {c_val:.2f}: {count:6d} ({count/len(c_vals)*100:.1f}%)")
    print()

    # Grade distribution
    print("─── Questions by Grade ───")
    for g in sorted(stats["by_grade"].keys()):
        count = stats["by_grade"][g]
        print(f"  Grade {g}: {count:6d}")
    print()

    # Tier distribution
    print("─── Questions by Difficulty Tier ───")
    for t in sorted(stats["by_tier"].keys()):
        count = stats["by_tier"][t]
        print(f"  {t:12s}: {count:6d}")
    print()

    # Spot check: verify Grade 1 easy questions have negative b
    print("─── Spot Checks ───")
    g1_easy = [(q, fp) for q, fp, fg, sm in all_questions
               if infer_grade_from_question(q, fg) == 1
               and q.get("difficulty_tier") == "easy"]
    if g1_easy:
        sample = g1_easy[:3]
        print("Grade 1, easy questions (should have very negative b):")
        for q, fp in sample:
            print(f"  {q['id']}: a={q['irt_a']}, b={q['irt_b']}, c={q['irt_c']}")

    g6_hard = [(q, fp) for q, fp, fg, sm in all_questions
               if infer_grade_from_question(q, fg) == 6
               and q.get("difficulty_tier") in ("hard", "expert", "advanced")]
    if g6_hard:
        sample = g6_hard[:3]
        print("Grade 6, hard/expert questions (should have positive b):")
        for q, fp in sample:
            print(f"  {q['id']}: a={q['irt_a']}, b={q['irt_b']}, c={q['irt_c']}")

    print()
    print("=" * 70)
    print("CALIBRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    calibrate()
