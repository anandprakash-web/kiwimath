# Kiwi Maths — Level/Topic Re-Tag — Content Count Report

**Date:** 2026-06-13 · **Scope:** full reorganisation of the question banks into the new **L1–L8 Level system** for the Olympiad section, with school-curriculum questions separated out.

## Headline

- **Olympiad questions tagged into Levels:** 18,803
- **School-curriculum questions (kept separate, school-only):** 10,340
- **Grand total preserved:** 29,143 (every answer, hint, difficulty & image verified byte-identical to source — 0 mismatches)

Current content is K–6 only, so all olympiad questions land in **L1–L3**. **L4–L8 taxonomy is built but empty (0 questions)** — ready to fill from IOQM/RMO/INMO/IMO sources later.

## Olympiad — questions per Level

| Level | Maps to | Questions |
|---|---|---|
| **L1** | Grade 1/2 | 9,660 |
| **L2** | Grade 3/4 | 6,320 |
| **L3** | Grade 5/6 | 2,823 |
| **L4** | Grade 7/8 | 0 |
| **L5** | Grade 9/10 (IOQM) | 0 |
| **L6** | Olympiad (RMO) | 0 |
| **L7** | Olympiad (INMO) | 0 |
| **L8** | Olympiad (IMO) | 0 |

## Per-topic counts (L1–L3)

> Pillars (NT / ALG / GEO / COM) are internal-only; learners see the display name.

### L1 — Grade 1/2 (9,660 questions)

| Pillar | Topic (display) | Questions |
|---|---|---|
| NT | Numbers All Around | 1,133 |
| NT | Number Hops | 107 |
| ALG | Pattern Play | 1,146 |
| ALG | Mystery Numbers | 2,109 |
| GEO | Shape Spotters | 962 |
| GEO | Picture Puzzles | 981 |
| COM | Sort It Out | 153 |
| COM | Think & Count | 3,069 |

### L2 — Grade 3/4 (6,320 questions)

| Pillar | Topic (display) | Questions |
|---|---|---|
| NT | Big Numbers | 1,069 |
| NT | Number Families | 230 |
| NT | Last-Digit Detective | 4 |
| ALG | Rule Finders | 575 |
| ALG | Balance the Scale | 1,832 |
| ALG | Fair Shares | 104 |
| GEO | Measure Masters | 325 |
| GEO | Turn & Flip | 975 |
| COM | List It All | 0 |
| COM | Brain Benders | 1,206 |

### L3 — Grade 5/6 (2,823 questions)

| Pillar | Topic (display) | Questions |
|---|---|---|
| NT | Prime Hunters | 607 |
| NT | Common Ground | 40 |
| NT | Clock Arithmetic | 88 |
| ALG | Parts & Wholes | 153 |
| ALG | In Proportion | 340 |
| ALG | Letter Maths | 212 |
| ALG | What Comes Next | 329 |
| GEO | Angle Chasers | 102 |
| GEO | Space & Surface | 282 |
| GEO | Map Makers | 217 |
| COM | Smart Counting | 205 |
| COM | Sock Drawer Logic | 28 |
| COM | Winning Moves | 220 |

### L4–L8 — empty (structure only)

All topics for L4 (Grade 7/8), L5 (Grade 9/10 / IOQM), L6 (RMO), L7 (INMO), L8 (IMO) exist in the taxonomy with 0 questions. Topic lists are in `content-live/olympiad/topic_map.json`.

## School curriculum (separate store, school-only) — tagged grade-wise

Every curriculum question carries a verified grade tag (`km_grade` 1–6) and lives in `content-live/curriculum/{board}/grade{n}/`. Grade is authoritative: it matches both the question's `original_id` grade and its `school_grade` field for all 10,340 questions (0 missing, 0 mismatches).

**Questions by board × grade**

| Board | G1 | G2 | G3 | G4 | G5 | G6 | Total |
|---|--:|--:|--:|--:|--:|--:|--:|
| NCERT (CBSE) | 530 | 490 | 517 | 579 | 906 | 583 | 3,605 |
| Cambridge Primary (IGCSE) | 510 | 421 | 410 | 465 | 470 | 438 | 2,714 |
| ICSE | 283 | 294 | 330 | 279 | 289 | 337 | 1,812 |
| Singapore | 201 | 255 | 199 | 217 | 243 | 204 | 1,319 |
| US Common Core | 139 | 152 | 125 | 144 | 157 | 173 | 890 |
| **Per-grade total** | **1,663** | **1,612** | **1,581** | **1,684** | **2,065** | **1,735** | **10,340** |

**Chapters by board × grade** (chapter → question refs preserved, 78% resolve)

| Board | G1 | G2 | G3 | G4 | G5 | G6 | Total |
|---|--:|--:|--:|--:|--:|--:|--:|
| NCERT (CBSE) | 13 | 11 | 14 | 14 | 23 | 16 | 91 |
| Cambridge Primary (IGCSE) | 12 | 12 | 12 | 12 | 12 | 12 | 72 |
| ICSE | 7 | 8 | 9 | 7 | 8 | 8 | 47 |
| Singapore | 8 | 7 | 8 | 7 | 8 | 7 | 45 |
| US Common Core | 4 | 4 | 4 | 5 | 5 | 5 | 27 |

## What changed (and what was preserved)

- **New consolidated stores:** all olympiad questions now live in `content-live/olympiad/L{1-8}/` (one file per topic); all curriculum questions in `content-live/curriculum/{board}/grade{n}/`.
- **New IDs:** every olympiad question got a `KM-L{level}-{PILLAR}-{serial}` id; the old id is kept as `legacy_id` (and `legacy_original_id`). `id_map.json` maps old→new.
- **Tags added:** `km_level`, `km_pillar`, `km_topic`, `km_topic_display` on each olympiad question; `km_board`, `km_grade` on each curriculum question.
- **Conflicting tags removed** from olympiad questions: `curriculum_map`, `curriculum_source`, `curriculum_tags`, `chapter`, `dual_tagged`, stale `adaptive_topic_*` and `topic` fields.
- **Preserved unchanged (verified):** stem, choices, correct_answer/value, hint ladder, solution_steps, diagnostics, IRT params, difficulty tier/score, and inline SVG/image — each bound to its own question. Within a topic, questions are ordered by IRT difficulty (ascending) but each question keeps its own data.
- **Curriculum chapter references** still resolve at 78% (9,947/12,745) — unchanged from before the reorg.

## Notable content-gap signals (for the build backlog)

- **L1 is logic/counting-heavy:** "Think & Count" (3,069) and "Mystery Numbers" (2,109) dominate; **Number Hops (107)** and **Sort It Out (153)** are thin.
- **L2 gaps:** **List It All (0)**, **Last-Digit Detective (4)**, **Fair Shares / fractions (104)** are sparse.
- **L3 gaps:** **Common Ground / HCF-LCM (40)** and **Sock Drawer / Pigeonhole (28)** are thin; L3 overall is small (2,823).
- **L4–L8 (Grade 7 → IMO): no content yet** — the biggest gap for a true olympiad-prep ladder.

## Next

1. UI/UX: level-picker for the Olympiad section (L1–L8), topic browser per level, "coming soon" for empty levels/topics.
2. Backend rewire to read `olympiad/` + `curriculum/` (the old `content-v2/` + `content-v4/` banks are now superseded; archive them at cutover).
3. Content fill: sparse L1–L3 topics + the empty L4–L8 ladder.