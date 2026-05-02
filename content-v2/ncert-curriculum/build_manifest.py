#!/usr/bin/env python3
"""Build master_manifest.json and assessment_items.json from NCERT question files."""

import json
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(os.path.dirname(os.path.dirname(BASE)), "backend")

# Domain mapping rules
DOMAIN_KEYWORDS = {
    "numbers": ["counting", "number sense", "place value", "large numbers", "number play",
                "patterns", "numbers", "number", "count", "place_value", "large-numbers",
                "figurate-numbers", "sequences", "number-system"],
    "arithmetic": ["addition", "subtraction", "multiplication", "division", "operations",
                   "mental math", "arithmetic", "add", "subtract", "multiply", "divide",
                   "factors", "multiples", "lcm", "hcf", "whole-numbers", "integers",
                   "negative-numbers", "playing-with-numbers"],
    "fractions": ["fractions", "decimals", "percentage", "fraction", "decimal", "ratio",
                  "proportion"],
    "geometry": ["shapes", "angles", "lines", "symmetry", "constructions", "spatial",
                 "geometry", "triangle", "quadrilateral", "circle", "polygon", "3d",
                 "reflection", "rotation", "tessellation"],
    "measurement": ["length", "weight", "time", "money", "area", "perimeter", "volume",
                    "data handling", "speed", "maps", "measurement", "capacity", "data",
                    "statistics", "graph", "temperature", "calendar", "clock"]
}

def classify_domain(question):
    """Classify a question into a domain based on chapter, tags, and topic."""
    text = " ".join([
        question.get("chapter", ""),
        question.get("topic", ""),
        " ".join(question.get("tags", []))
    ]).lower()

    # Score each domain
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[domain] = score

    if scores:
        return max(scores, key=scores.get)
    return "numbers"  # default fallback

def get_subdomain(question):
    """Extract subdomain from tags/chapter."""
    tags = question.get("tags", [])
    if tags:
        return tags[0].replace("-", "_").replace(" ", "_")
    chapter = question.get("chapter", "")
    if chapter:
        # Extract topic from chapter name
        parts = chapter.split(":")
        if len(parts) > 1:
            return parts[1].strip().lower().replace(" ", "_")[:30]
    return "general"

# Load all grade files
GRADE_FILES = {
    "1": "grade1/questions.json",
    "2": "grade2/questions.json",
    "3": "grade3/ncert_g3_questions.json",
    "4": "grade4/ncert_g4_questions.json",
    "5": "grade5/ncert_g5_questions.json",
    "6": "grade6/ncert_g6_questions.json",
}

all_questions = []
grade_info = {}

for grade, filepath in GRADE_FILES.items():
    full_path = os.path.join(BASE, filepath)
    with open(full_path) as f:
        data = json.load(f)

    questions = data.get("questions", [])

    # Gather chapter names
    chapters = sorted(set(q.get("chapter", "Unknown") for q in questions))

    # Count visuals
    visuals = sum(1 for q in questions if q.get("visual_svg"))

    grade_info[grade] = {
        "questions": len(questions),
        "visuals": visuals,
        "chapters": chapters,
        "file": filepath
    }

    for q in questions:
        q["_grade"] = int(grade)
    all_questions.extend(questions)

# Build domain mapping
domain_mapping = defaultdict(lambda: {"question_ids": [], "count": 0})

assessment_items = []

for q in all_questions:
    domain = classify_domain(q)
    subdomain = get_subdomain(q)
    qid = q["id"]
    grade = q["_grade"]

    domain_mapping[domain]["question_ids"].append(qid)
    domain_mapping[domain]["count"] += 1

    # IRT params
    irt = q.get("irt_params", {})
    a = irt.get("a", 1.0)
    b = irt.get("b", 0.0)
    c = irt.get("c", 0.25)

    # Clamp to valid ranges
    a = max(0.3, min(3.0, a))
    b = max(-4.0, min(4.0, b))
    c = max(0.0, min(0.4, c))

    # Grade range: +/- 1
    grade_range = [max(1, grade - 1), min(6, grade + 1)]

    item = {
        "item_id": qid,
        "a": round(a, 3),
        "b": round(b, 3),
        "c": round(c, 3),
        "domain": domain,
        "subdomain": subdomain,
        "curriculum_tags": q.get("curriculum_tags", []),
        "grade_range": grade_range,
        "state": "active"
    }
    assessment_items.append(item)

# Finalize domain mapping
domain_mapping_final = {}
for domain in ["numbers", "arithmetic", "fractions", "geometry", "measurement"]:
    if domain in domain_mapping:
        domain_mapping_final[domain] = {
            "question_ids": domain_mapping[domain]["question_ids"],
            "count": domain_mapping[domain]["count"]
        }
    else:
        domain_mapping_final[domain] = {"question_ids": [], "count": 0}

# Build manifest
total_visuals = sum(g["visuals"] for g in grade_info.values())
manifest = {
    "version": "1.0",
    "generated": "2026-05-01",
    "curriculum": "NCERT",
    "total_questions": len(all_questions),
    "total_visuals": total_visuals,
    "grades": grade_info,
    "domain_mapping": domain_mapping_final
}

# Write manifest
manifest_path = os.path.join(BASE, "master_manifest.json")
with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)
print(f"Written manifest: {manifest_path}")
print(f"  Total questions: {manifest['total_questions']}")
print(f"  Total visuals: {manifest['total_visuals']}")
for g, info in grade_info.items():
    print(f"  Grade {g}: {info['questions']} questions, {info['visuals']} visuals, {len(info['chapters'])} chapters")

print("\nDomain distribution:")
for domain, data in domain_mapping_final.items():
    print(f"  {domain}: {data['count']}")

# Write assessment items
items_path = os.path.join(BACKEND, "assessment_items.json")
with open(items_path, "w") as f:
    json.dump(assessment_items, f, indent=2)
print(f"\nWritten assessment items: {items_path}")
print(f"  Total items: {len(assessment_items)}")
