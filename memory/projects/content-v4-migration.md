# Content v4 Migration

**Status:** Complete (May 3, 2026)
**Schema version:** 4.1

## What Was Done

Reorganized all 22,467 questions from flat content-v3 into a grade-topic adaptive structure (content-v4). Questions distributed across 57 topics in 6 grades using KiwiTier level mapping, creating 36,459 total question placements (overlap from multi-grade mapping).

## KiwiTier Level→Grade Mapping

| Level | Grades | IRT adjustment |
|-------|--------|----------------|
| 1 (Explorer) | G1 + G2 | -0.2 for G2 copy |
| 2 (Thinker) | G2 + G3 | -0.2 for G3 copy |
| 3 (Solver) | G3 + G4 | -0.2 for G4 copy |
| 4 (Champion) | G4 + G5 | -0.2 for G5 copy |
| Grade 6 | Cloned from L3-L4 | +0.3 IRT bump |

## Topic Structure

**G1-G2 (8 topics each):** Counting & Numbers, Addition, Subtraction, Shapes & Geometry, Measurement, Time & Money, Patterns & Sequences, Word Problems

**G3-G6 (10-11 topics):** Numbers & Place Value, Addition & Subtraction, Multiplication, Division, Fractions, Shapes & Geometry, Measurement, Patterns & Logic, Time & Money, Word Problems, Data Handling (G3-G4), Algebra (G5-G6), Data & Statistics (G5-G6), Percentage & Ratio (G5)

## Quality Fixes Applied

### Round 1 (fix_v4_issues.py):
- 4 domain classifications corrected
- 2,883 identical diagnostics deduplicated (2 passes)
- 7,978 hint spoilers remediated (1,870 redacted + 6,108 reclassified)
- 35,939 country_context → locale_ids (160MB → 100.5MB)
- 23,194 null school_grade populated
- 6 index files regenerated
- Schema 4.0 → 4.1

### Round 2 (fix_v4_round2.py):
- g5-percent rebuilt: 5 rounding stubs → 120 percentage/ratio questions
- 433 pure arithmetic moved out of word-problem files (G3-G5)
- 43 cross-operation diagnostics fixed
- G3/G4 data_handling separated from measurement
- G3 multiplication 215→400, division 178→398

### Visual Audit:
- 9,425 over-tagged essential→optional/none
- 6,686 filename SVG references cleared from text-answerable questions
- 466 filename refs kept as asset markers for design team
- 15 inline SVGs generated for genuinely essential questions
- Final: 636 essential (all covered), 22,090 optional, 13,733 none, 1,142 inline SVGs

## Key Scripts
| Script | Purpose |
|--------|---------|
| `scripts/reorganize_v4.py` | Main reorganization from v3→v4 |
| `scripts/fix_v4_issues.py` | Round 1 quality fixes |
| `scripts/fix_v4_round2.py` | Round 2 targeted fixes |
| `scripts/gen_g3_mult_div.py` | G3 topic imbalance fix |

## Backend Integration
- `content_store_v4.py` — ContentStoreV4 class, loads from `KIWIMATH_V4_CONTENT_DIR` env var
- `next_question_adaptive(grade, topic_id, theta)` — IRT-aware selection with cluster diversity
- `get_chapters(curriculum, grade)` + `get_chapter_questions()` — School tab queries
- Reuses `QuestionV2` pydantic model from content_store_v2.py

## Deployment Readiness Assessment
See separate section in strategic plan.
