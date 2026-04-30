#!/usr/bin/env python3
"""
Kiwimath Pre-Deployment Verification
Run this BEFORE deploy.sh to confirm content is correct.

Usage: python3 pre_deploy_check.py
"""
import json, os, glob, sys, hashlib
from collections import defaultdict

content_dir = os.path.join(os.path.dirname(__file__), '..', 'content-v2')
content_dir = os.path.abspath(content_dir)

print(f"=== Kiwimath Pre-Deploy Check ===")
print(f"Content dir: {content_dir}\n")

errors = []
warnings = []

if not os.path.isdir(content_dir):
    print(f"FATAL: content-v2 directory not found at {content_dir}")
    sys.exit(1)

expected_topics = [
    'topic-1-counting', 'topic-2-arithmetic', 'topic-3-patterns', 'topic-4-logic',
    'topic-5-spatial', 'topic-6-shapes', 'topic-7-word-problems', 'topic-8-puzzles'
]

question_files = [
    "questions.json", "grade34_questions.json", "grade34_variety_questions.json",
    "g56_questions.json", "data_handling.json", "geometry_measurement.json",
    "measurement_units.json",
]

# Difficulty score ranges — wide range accepted since content was scaled
score_ranges = {
    "questions.json": (1, 300),
    "grade34_questions.json": (1, 300),
    "grade34_variety_questions.json": (1, 300),
    "g56_questions.json": (1, 300),
    "data_handling.json": (1, 300),
    "geometry_measurement.json": (1, 300),
    "measurement_units.json": (1, 300),
}

total_questions = 0
topic_counts = {}
all_ids = set()
total_visuals = 0
missing_svgs = 0

for topic in expected_topics:
    topic_path = os.path.join(content_dir, topic)
    if not os.path.isdir(topic_path):
        errors.append(f"Missing topic directory: {topic}")
        continue

    topic_total = 0
    for qfile in question_files:
        fpath = os.path.join(topic_path, qfile)
        if not os.path.exists(fpath):
            continue

        data = json.load(open(fpath))
        if isinstance(data, dict):
            questions = data.get('questions', [])
        elif isinstance(data, list):
            questions = data
        else:
            continue

        topic_total += len(questions)
        total_questions += len(questions)

        lo, hi = score_ranges.get(qfile, (1, 300))

        for q in questions:
            qid = q.get('id', '?')

            # Unique ID check
            if qid in all_ids:
                errors.append(f"DUPLICATE ID: {qid} in {topic}/{qfile}")
            all_ids.add(qid)

            # Required fields
            for field in ['id', 'stem', 'choices', 'correct_answer', 'difficulty_tier', 'difficulty_score']:
                if field not in q:
                    errors.append(f"{qid}: missing '{field}'")

            if q.get('correct_answer', 0) not in [0, 1, 2, 3]:
                errors.append(f"{qid}: correct_answer={q.get('correct_answer')}")

            score = q.get('difficulty_score', 0)
            if score < lo or score > hi:
                errors.append(f"{qid}: difficulty_score={score} (expected {lo}-{hi})")

            if len(q.get('choices', [])) != 4:
                errors.append(f"{qid}: {len(q.get('choices', []))} choices (need 4)")

            # SVG check
            svg = q.get('visual_svg')
            if svg:
                total_visuals += 1
                svg_path = os.path.join(topic_path, 'visuals', svg)
                if not os.path.exists(svg_path):
                    # Case-insensitive fallback
                    visuals_dir = os.path.join(topic_path, 'visuals')
                    if os.path.isdir(visuals_dir):
                        actual = [f for f in os.listdir(visuals_dir) if f.lower() == svg.lower()]
                        if not actual:
                            missing_svgs += 1
                            errors.append(f"{qid}: SVG '{svg}' not found")

    topic_counts[topic] = topic_total

# SVG hash check
svg_hashes = defaultdict(list)
for svg_file in glob.glob(os.path.join(content_dir, 'topic-*/visuals/*.svg')):
    content = open(svg_file).read()
    h = hashlib.md5(content.encode()).hexdigest()
    svg_hashes[h].append(os.path.basename(svg_file))

# Report
print(f"Questions: {total_questions} across {len(topic_counts)} topics")
for tid, count in sorted(topic_counts.items()):
    print(f"  {tid}: {count}")

print(f"\nVisuals: {total_visuals} questions have SVGs, {missing_svgs} missing")
print(f"Unique SVGs: {len(svg_hashes)}")

if errors:
    print(f"\n❌ ERRORS ({len(errors)}) — must fix before deploying:")
    for e in errors[:20]:
        print(f"  • {e}")
    if len(errors) > 20:
        print(f"  ... and {len(errors)-20} more")
    sys.exit(1)

if warnings:
    print(f"\n⚠️  WARNINGS ({len(warnings)}):")
    for w in warnings:
        print(f"  • {w}")

print(f"\n✅ ALL CHECKS PASSED — safe to deploy!")
print(f"   {total_questions} questions, {total_visuals} visuals, {len(all_ids)} unique IDs")
sys.exit(0)
