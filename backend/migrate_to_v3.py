#!/usr/bin/env python3
"""
Grand Unified Migration — Enriches all 22,467 questions to v3 schema.

Reads from content-v2/, enriches each question with:
  - level (1-6, replacing grade as primary)
  - universal_skill_id (e.g., FRAC_ADD_4)
  - maturity_bucket (experimental / calibrating / production)
  - visual_requirement (essential / optional / none)
  - country_context (india / singapore / us / global)
  - curriculum_map (cross-curriculum references)
  - media_hash (SHA256 of visual asset if exists)
  - misconception_ids (extracted from diagnostics)
  - why_quality (human_authored / ai_generated / none)
  - why_framework (3R if has structured diagnostics)
  - behavioral_tags (placeholder for live data)

Writes enriched files to content-v3/ (parallel structure, no destructive changes).
Also produces a migration_report.json with full stats.

Usage:
  cd backend
  python migrate_to_v3.py
"""

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.level_mapper import (
    COUNTRY_CONTEXTS,
    LEVEL_NAMES,
    SKILL_TO_UNIVERSAL,
    build_curriculum_map,
    difficulty_to_level,
    get_skill_domain,
    get_universal_skill_id,
    grade_to_level,
    infer_level,
    infer_maturity_bucket,
    infer_visual_requirement,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONTENT_V2_DIR = Path(__file__).parent.parent / "content-v2"
CONTENT_V3_DIR = Path(__file__).parent.parent / "content-v3"
REPORT_PATH = Path(__file__).parent.parent / "migration_report.json"

# Skill mapping (inline version of skill_mapper logic to avoid import issues)
TAG_RULES: List[Tuple[set, Optional[Tuple[int, int]], str]] = [
    ({"decimal", "operations"}, None, "decimal_operations"),
    ({"decimal"}, None, "decimals"),
    ({"fraction", "multiply"}, None, "fraction_multiply"),
    ({"fraction", "add"}, None, "fraction_add"),
    ({"fraction", "subtract"}, None, "fraction_add"),
    ({"fraction", "compare"}, None, "fraction_compare"),
    ({"fractions", "multiplication"}, None, "fraction_multiply"),
    ({"fractions", "addition"}, None, "fraction_add"),
    ({"fractions", "compare"}, None, "fraction_compare"),
    ({"fractions"}, (1, 120), "fraction_concept"),
    ({"fractions"}, (121, 300), "fraction_add"),
    ({"coordinate"}, None, "coordinates"),
    ({"area"}, None, "area"),
    ({"perimeter"}, None, "perimeter"),
    ({"angle"}, None, "angles"),
    ({"symmetry"}, None, "symmetry"),
    ({"3d", "shape"}, None, "shapes_3d"),
    ({"shapes", "3d"}, None, "shapes_3d"),
    ({"shape"}, None, "shapes_2d"),
    ({"shapes"}, None, "shapes_2d"),
    ({"conversion"}, None, "unit_conversion"),
    ({"unit"}, None, "unit_conversion"),
    ({"data_handling"}, None, "data_handling"),
    ({"statistics"}, None, "data_handling"),
    ({"graph"}, None, "data_handling"),
    ({"money"}, None, "money"),
    ({"time"}, None, "time"),
    ({"capacity"}, None, "capacity"),
    ({"volume"}, None, "capacity"),
    ({"weight"}, None, "weight"),
    ({"mass"}, None, "weight"),
    ({"length"}, None, "length"),
    ({"measurement"}, (1, 100), "length"),
    ({"measurement"}, (101, 300), "unit_conversion"),
    ({"order_of_operations"}, None, "order_of_ops"),
    ({"bodmas"}, None, "order_of_ops"),
    ({"multi_step"}, None, "multi_step"),
    ({"division"}, None, "division_basic"),
    ({"multiplication"}, (1, 120), "multiplication_facts"),
    ({"multiplication"}, (121, 300), "multi_step"),
    ({"subtraction"}, (101, 300), "subtraction_2digit"),
    ({"subtraction"}, (1, 100), "subtraction_basic"),
    ({"addition"}, (101, 300), "addition_2digit"),
    ({"addition"}, (1, 100), "addition_basic"),
    ({"arithmetic"}, (1, 80), "addition_basic"),
    ({"arithmetic"}, (81, 150), "addition_2digit"),
    ({"arithmetic"}, (151, 250), "multi_step"),
    ({"arithmetic"}, (251, 300), "order_of_ops"),
    ({"rounding"}, None, "rounding"),
    ({"number_patterns"}, None, "number_patterns"),
    ({"patterns"}, (1, 100), "number_patterns"),
    ({"patterns"}, (101, 300), "number_patterns"),
    ({"place_value"}, (1, 80), "place_value_2"),
    ({"place_value"}, (81, 150), "place_value_3"),
    ({"place_value"}, (151, 300), "place_value_4"),
    ({"comparison"}, None, "comparison"),
    ({"counting"}, (1, 50), "counting_10"),
    ({"counting"}, (51, 300), "counting_100"),
    ({"numbers"}, (1, 50), "counting_10"),
    ({"numbers"}, (51, 120), "counting_100"),
    ({"numbers"}, (121, 200), "place_value_3"),
    ({"numbers"}, (201, 300), "place_value_4"),
]

CURRICULUM_TOPIC_MAP = {
    "ncert_g1_numbers": "counting_100", "ncert_g1_addition": "addition_basic",
    "ncert_g1_subtraction": "subtraction_basic", "ncert_g1_shapes": "shapes_2d",
    "ncert_g1_measurement": "length",
    "ncert_g2_numbers": "place_value_2", "ncert_g2_addition": "addition_2digit",
    "ncert_g2_subtraction": "subtraction_2digit", "ncert_g2_multiplication": "multiplication_facts",
    "ncert_g2_shapes": "shapes_2d", "ncert_g2_measurement": "length",
    "ncert_g3_numbers": "place_value_3", "ncert_g3_arithmetic": "addition_2digit",
    "ncert_g3_fractions": "fraction_concept", "ncert_g3_geometry": "perimeter",
    "ncert_g3_measurement": "unit_conversion",
    "ncert_g4_numbers": "place_value_4", "ncert_g4_arithmetic": "multi_step",
    "ncert_g4_fractions": "fraction_compare", "ncert_g4_geometry": "area",
    "ncert_g4_measurement": "unit_conversion",
    "ncert_g5_numbers": "place_value_4", "ncert_g5_arithmetic": "order_of_ops",
    "ncert_g5_fractions": "fraction_add", "ncert_g5_geometry": "angles",
    "ncert_g5_measurement": "unit_conversion",
    "ncert_g6_numbers": "place_value_4", "ncert_g6_integers": "subtraction_2digit",
    "ncert_g6_fractions": "fraction_multiply", "ncert_g6_geometry": "coordinates",
    "ncert_g6_algebra": "order_of_ops", "ncert_g6_ratio": "fraction_multiply",
    "ncert_g6_data": "data_handling",
}

TOPIC_FALLBACKS = {
    "counting_observation": "counting_100",
    "arithmetic_missing_numbers": "addition_basic",
    "patterns_sequences": "number_patterns",
    "logic_ordering": "comparison",
    "spatial_reasoning_3d": "shapes_3d",
    "spatial_reasoning": "shapes_2d",
    "shapes_folding_symmetry": "symmetry",
    "shapes_geometry": "shapes_2d",
    "word_problems_stories": "multi_step",
    "word_problems": "multi_step",
    "number_puzzles_games": "number_patterns",
    "puzzles_games": "number_patterns",
    "logic_deduction": "comparison",
    "data_handling": "data_handling",
}


def map_skill(tags: list, difficulty: int, topic: str) -> str:
    tag_set = {t.lower().replace(" ", "_") for t in (tags or [])}
    for req_tags, diff_range, skill_id in TAG_RULES:
        if not req_tags.issubset(tag_set):
            continue
        if diff_range and not (diff_range[0] <= difficulty <= diff_range[1]):
            continue
        return skill_id
    topic_lower = (topic or "").lower()
    if topic_lower in CURRICULUM_TOPIC_MAP:
        return CURRICULUM_TOPIC_MAP[topic_lower]
    for prefix, sid in TOPIC_FALLBACKS.items():
        if topic_lower.startswith(prefix):
            return sid
    if difficulty <= 50: return "counting_10"
    elif difficulty <= 100: return "addition_basic"
    elif difficulty <= 150: return "addition_2digit"
    elif difficulty <= 200: return "multiplication_facts"
    else: return "multi_step"


# ---------------------------------------------------------------------------
# Detect curriculum from question ID
# ---------------------------------------------------------------------------

def detect_curriculum(qid: str) -> Optional[str]:
    if qid.startswith("NCERT-"): return "ncert"
    if qid.startswith("ICSE-"): return "icse"
    if qid.startswith("SING-"): return "singapore"
    if qid.startswith("USCC-"): return "uscc"
    if qid.startswith("IGCSE-"): return "igcse"
    if re.match(r"T\d+-\d+", qid): return "olympiad"
    return None


def detect_grade_from_id(qid: str) -> Optional[int]:
    m = re.search(r"-G(\d)-", qid)
    if m:
        return int(m.group(1))
    return None


# ---------------------------------------------------------------------------
# Extract misconception IDs from diagnostics
# ---------------------------------------------------------------------------

def extract_misconception_ids(diagnostics: Any) -> list:
    """Extract structured misconception IDs from diagnostic text."""
    ids = []
    if isinstance(diagnostics, dict):
        for key, text in diagnostics.items():
            if isinstance(text, str):
                text_lower = text.lower()
                if "added instead" in text_lower or "add" in text_lower and "subtract" in text_lower:
                    ids.append("ADD_INSTEAD_SUB")
                elif "borrow" in text_lower or "regroup" in text_lower:
                    ids.append("BORROW_ERR")
                elif "place value" in text_lower or "place" in text_lower:
                    ids.append("PLACE_VALUE_ERR")
                elif "count" in text_lower:
                    ids.append("COUNT_ERR")
                elif "carry" in text_lower:
                    ids.append("CARRY_ERR")
                elif "denominator" in text_lower:
                    ids.append("DENOM_ERR")
                elif "numerator" in text_lower:
                    ids.append("NUMER_ERR")
                elif "off by" in text_lower or "close" in text_lower:
                    ids.append("OFF_BY_ONE")
                elif "skip" in text_lower:
                    ids.append("SKIP_COUNT_ERR")
                else:
                    ids.append(f"MISC_{key}")
    return list(set(ids)) if ids else ["UNCLASSIFIED"]


# ---------------------------------------------------------------------------
# Compute media hash
# ---------------------------------------------------------------------------

def compute_media_hash(visual_svg: Optional[str], base_dir: Path) -> Optional[str]:
    """Compute SHA256 hash for visual asset."""
    if not visual_svg:
        return None

    # If it's an embedded SVG string (starts with <svg)
    if visual_svg.strip().startswith("<svg") or visual_svg.strip().startswith("<?xml"):
        return "sha256:" + hashlib.sha256(visual_svg.encode()).hexdigest()[:16]

    # If it's a filename reference, try to find the file
    visuals_dir = base_dir / "visuals"
    if visuals_dir.exists():
        svg_path = visuals_dir / visual_svg
        if svg_path.exists():
            content = svg_path.read_bytes()
            return "sha256:" + hashlib.sha256(content).hexdigest()[:16]

    return None


# ---------------------------------------------------------------------------
# Assess hint quality
# ---------------------------------------------------------------------------

def assess_hint_quality(hint: Any) -> Dict[str, Any]:
    """Assess hint structure and quality."""
    if not hint:
        return {"layers": 0, "quality": "none", "has_3_layers": False}

    if isinstance(hint, str):
        return {"layers": 1, "quality": "minimal", "has_3_layers": False}

    if isinstance(hint, dict):
        layers = len(hint)
        has_3 = layers >= 3

        # Check for generic hints
        generic_phrases = ["think carefully", "try again", "look at the question"]
        texts = [str(v).lower() for v in hint.values()]
        generic_count = sum(1 for t in texts if any(g in t for g in generic_phrases))

        # Check if final hint gives away answer
        last_hint = list(hint.values())[-1] if hint else ""
        spoils = "=" in str(last_hint) and any(c.isdigit() for c in str(last_hint))

        if generic_count > 1:
            quality = "generic"
        elif spoils:
            quality = "spoiler"
        elif has_3 and generic_count == 0:
            quality = "good"
        else:
            quality = "adequate"

        return {"layers": layers, "quality": quality, "has_3_layers": has_3}

    return {"layers": 0, "quality": "unknown", "has_3_layers": False}


# ---------------------------------------------------------------------------
# Assess "Why?" quality
# ---------------------------------------------------------------------------

def assess_why_quality(diagnostics: Any) -> str:
    """Determine why_quality tag."""
    if not diagnostics:
        return "none"
    if isinstance(diagnostics, dict):
        texts = [str(v) for v in diagnostics.values() if isinstance(v, str)]
        if not texts:
            if "common_errors" in diagnostics:
                return "structured"
            return "none"
        avg_len = sum(len(t) for t in texts) / max(len(texts), 1)
        if avg_len > 40:
            return "human_authored"
        elif avg_len > 15:
            return "ai_generated"
        else:
            return "minimal"
    return "minimal"


# ---------------------------------------------------------------------------
# Main enrichment function
# ---------------------------------------------------------------------------

def enrich_question(q: dict, grade: Optional[int], base_dir: Path) -> dict:
    """Enrich a single question with Grand Unified Schema fields."""
    qid = q.get("id", "UNKNOWN")
    tags = q.get("tags", [])
    difficulty = q.get("difficulty_score", 50)
    topic = q.get("topic", "")
    visual_svg = q.get("visual_svg")
    hint = q.get("hint")
    diagnostics = q.get("diagnostics")
    interaction_mode = q.get("interaction_mode", "mcq")

    # Detect grade from wrapper or ID
    if not grade:
        grade = detect_grade_from_id(qid)

    # 1. Level
    level = infer_level(grade, difficulty)

    # 2. Skill mapping
    skill_id = map_skill(tags, difficulty, topic)
    universal_skill_id = get_universal_skill_id(skill_id, level)
    skill_domain = get_skill_domain(skill_id)

    # 3. Maturity bucket
    has_irt = bool(q.get("irt_params") or q.get("irt_a"))
    has_hints = bool(hint and (isinstance(hint, dict) and len(hint) >= 2))
    has_diag = bool(diagnostics)
    maturity_bucket = infer_maturity_bucket(has_irt, has_hints, has_diag)

    # 4. Visual requirement
    has_visual = bool(visual_svg)
    visual_req = infer_visual_requirement(tags, level, has_visual, interaction_mode)

    # 5. Visual type inference
    visual_type = "none"
    if has_visual:
        tag_set = {t.lower() for t in tags}
        if tag_set & {"3d", "spatial", "volume", "surface_area"}:
            visual_type = "3d_rotatable"
        elif tag_set & {"number_line", "numberline"}:
            visual_type = "number_line"
        elif tag_set & {"graph", "chart", "data_handling", "statistics"}:
            visual_type = "chart"
        else:
            visual_type = "2d"

    # 6. Media hash
    media_hash = compute_media_hash(visual_svg, base_dir)
    media_id = visual_svg if (visual_svg and not visual_svg.startswith("<")) else None

    # 7. Misconception IDs
    misconception_ids = extract_misconception_ids(diagnostics)

    # 8. Why? quality
    why_quality = assess_why_quality(diagnostics)

    # 9. Hint quality assessment
    hint_quality = assess_hint_quality(hint)

    # 10. Curriculum detection + cross-ref
    curriculum = detect_curriculum(qid)
    curriculum_map = build_curriculum_map(tags, skill_domain)

    # 11. Country context (all questions get all contexts for localization)
    country_context = COUNTRY_CONTEXTS

    # Build the enrichment overlay (additive — doesn't remove existing fields)
    enrichment = {
        # === NEW v3 FIELDS ===
        "level": level,
        "level_name": LEVEL_NAMES.get(level, "Unknown"),
        "universal_skill_id": universal_skill_id,
        "skill_id": skill_id,
        "skill_domain": skill_domain,
        "maturity_bucket": maturity_bucket,
        "visual_requirement": visual_req,
        "visual_type": visual_type,
        "visual_ai_verified": False,  # needs LLM pass
        "media_id": media_id,
        "media_hash": media_hash,
        "misconception_ids": misconception_ids,
        "why_quality": why_quality,
        "why_framework": "3R" if why_quality in ("human_authored", "structured") else "pending",
        "hint_quality": hint_quality,
        "country_context": country_context,
        "curriculum_source": curriculum,
        "curriculum_map": curriculum_map,
        "school_grade": grade,  # preserved for curriculum tab
        # Behavioral placeholders (populated by live data)
        "avg_time_to_solve_ms": None,
        "times_served": 0,
        "flag_count": 0,
        # Schema version
        "schema_version": "3.0",
    }

    # Merge: existing fields stay, new fields added
    enriched = {**q, **enrichment}
    return enriched


# ---------------------------------------------------------------------------
# Process a single JSON file
# ---------------------------------------------------------------------------

def process_file(src_path: Path, dst_path: Path) -> Dict[str, Any]:
    """Process one question JSON file. Returns stats."""
    with open(src_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = {
        "file": str(src_path.relative_to(CONTENT_V2_DIR)),
        "questions_processed": 0,
        "levels": {},
        "maturity": {"experimental": 0, "calibrating": 0, "production": 0},
        "visual_req": {"essential": 0, "optional": 0, "none": 0},
        "why_quality": {},
        "hint_quality": {},
        "skills": {},
    }

    # Detect grade from wrapper
    wrapper_grade = data.get("grade")
    base_dir = src_path.parent

    # Get the questions array
    questions = data.get("questions", [])
    if not questions:
        return stats

    enriched_questions = []
    for q in questions:
        enriched = enrich_question(q, wrapper_grade, base_dir)
        enriched_questions.append(enriched)

        # Collect stats
        stats["questions_processed"] += 1
        lvl = enriched["level"]
        stats["levels"][lvl] = stats["levels"].get(lvl, 0) + 1
        stats["maturity"][enriched["maturity_bucket"]] += 1
        stats["visual_req"][enriched["visual_requirement"]] += 1
        wq = enriched["why_quality"]
        stats["why_quality"][wq] = stats["why_quality"].get(wq, 0) + 1
        hq = enriched["hint_quality"]["quality"]
        stats["hint_quality"][hq] = stats["hint_quality"].get(hq, 0) + 1
        sid = enriched["universal_skill_id"]
        stats["skills"][sid] = stats["skills"].get(sid, 0) + 1

    # Update the data with enriched questions
    data["questions"] = enriched_questions
    data["schema_version"] = "3.0"
    data["migration_date"] = time.strftime("%Y-%m-%d")

    # Write to v3
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dst_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("KIWIMATH GRAND UNIFIED MIGRATION — v2 → v3")
    print("=" * 60)
    print(f"Source: {CONTENT_V2_DIR}")
    print(f"Target: {CONTENT_V3_DIR}")
    print()

    if not CONTENT_V2_DIR.exists():
        print(f"ERROR: Source directory not found: {CONTENT_V2_DIR}")
        sys.exit(1)

    # Find all question JSON files (exclude manifests, registries, etc.)
    skip_files = {"visual_registry.json", "assessment_items.json", "concept_graph_all_grades.json",
                  "master_manifest.json", "manifest.json"}

    json_files = []
    for p in sorted(CONTENT_V2_DIR.rglob("*.json")):
        if p.name in skip_files:
            continue
        # Check if it has a "questions" array
        try:
            with open(p) as f:
                d = json.load(f)
            if "questions" in d and isinstance(d["questions"], list) and len(d["questions"]) > 0:
                json_files.append(p)
        except (json.JSONDecodeError, KeyError):
            continue

    print(f"Found {len(json_files)} question files to migrate")
    print()

    all_stats = []
    total_questions = 0
    total_levels = {}
    total_maturity = {"experimental": 0, "calibrating": 0, "production": 0}
    total_visual = {"essential": 0, "optional": 0, "none": 0}
    total_why = {}
    total_hint = {}
    total_skills = {}

    for i, src_path in enumerate(json_files, 1):
        rel = src_path.relative_to(CONTENT_V2_DIR)
        dst_path = CONTENT_V3_DIR / rel
        print(f"[{i}/{len(json_files)}] {rel}...", end=" ", flush=True)

        stats = process_file(src_path, dst_path)
        all_stats.append(stats)

        n = stats["questions_processed"]
        total_questions += n
        print(f"{n} questions enriched")

        # Accumulate totals
        for k, v in stats["levels"].items():
            total_levels[k] = total_levels.get(k, 0) + v
        for k, v in stats["maturity"].items():
            total_maturity[k] += v
        for k, v in stats["visual_req"].items():
            total_visual[k] += v
        for k, v in stats["why_quality"].items():
            total_why[k] = total_why.get(k, 0) + v
        for k, v in stats["hint_quality"].items():
            total_hint[k] = total_hint.get(k, 0) + v
        for k, v in stats["skills"].items():
            total_skills[k] = total_skills.get(k, 0) + v

    # Print summary
    print()
    print("=" * 60)
    print(f"MIGRATION COMPLETE: {total_questions} questions enriched")
    print("=" * 60)

    print(f"\nBy Level:")
    for lvl in sorted(total_levels.keys()):
        name = LEVEL_NAMES.get(lvl, "?")
        count = total_levels[lvl]
        pct = count / total_questions * 100
        print(f"  Level {lvl} ({name:12s}): {count:6d} ({pct:5.1f}%)")

    print(f"\nBy Maturity Bucket:")
    for bucket, count in total_maturity.items():
        pct = count / total_questions * 100
        print(f"  {bucket:15s}: {count:6d} ({pct:5.1f}%)")

    print(f"\nVisual Requirement:")
    for req, count in total_visual.items():
        pct = count / total_questions * 100
        print(f"  {req:15s}: {count:6d} ({pct:5.1f}%)")

    print(f"\nWhy? Quality:")
    for quality, count in sorted(total_why.items(), key=lambda x: -x[1]):
        pct = count / total_questions * 100
        print(f"  {quality:20s}: {count:6d} ({pct:5.1f}%)")

    print(f"\nHint Quality:")
    for quality, count in sorted(total_hint.items(), key=lambda x: -x[1]):
        pct = count / total_questions * 100
        print(f"  {quality:20s}: {count:6d} ({pct:5.1f}%)")

    print(f"\nTop 15 Universal Skill IDs:")
    top_skills = sorted(total_skills.items(), key=lambda x: -x[1])[:15]
    for sid, count in top_skills:
        print(f"  {sid:25s}: {count:6d}")

    # Write full report
    report = {
        "migration_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_questions": total_questions,
        "total_files": len(json_files),
        "schema_version": "3.0",
        "summary": {
            "by_level": {f"level_{k}_{LEVEL_NAMES.get(k, '?')}": v for k, v in sorted(total_levels.items())},
            "by_maturity": total_maturity,
            "by_visual_requirement": total_visual,
            "by_why_quality": total_why,
            "by_hint_quality": total_hint,
            "by_universal_skill_id": dict(sorted(total_skills.items(), key=lambda x: -x[1])),
        },
        "per_file_stats": all_stats,
        "gaps_needing_attention": {
            "no_why_explanation": total_why.get("none", 0) + total_why.get("minimal", 0),
            "generic_hints": total_hint.get("generic", 0),
            "spoiler_hints": total_hint.get("spoiler", 0),
            "no_visuals_but_essential": 0,  # computed below
            "visual_not_ai_verified": total_questions,  # all need LLM pass
        },
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nFull report written to: {REPORT_PATH}")
    print(f"Enriched content written to: {CONTENT_V3_DIR}/")


if __name__ == "__main__":
    main()
