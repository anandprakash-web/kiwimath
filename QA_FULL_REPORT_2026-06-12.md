# Kiwimath — Complete Question QA (All Banks, 5 Dimensions)

**Date:** 2026-06-12 · **Scope:** every question in content-v4/adaptive (served), content-v2 (served), content-production (successor set) — 58,603 questions scanned, then a full fix pass.
**Checks:** (1) unnecessary lines, (2) mismatched visuals, (3) missing visuals, (4) right answers, (5) Socratic hints.
**Artifacts:** all machine-readable issue lists, fix audit trails, deletion logs (full question bodies, recoverable), and re-runnable scanner/fixer scripts are in `qa-reports/`.

---

## Bottom line

| Set | Before | After | Status |
|---|---|---|---|
| content-v4/adaptive (served) | 20,056 q, 14,673 flagged issues | **19,919 q, 0 critical** | Fixed: 9,315 noisy hints, 1,094 hint leaks, 219 broken choices, 4,423 placeholder SVGs, 7 impossible answers; 137 unanswerable deleted |
| content-v2 (served) | 10,061 q, 507 critical | **9,224 q, 0 critical** | Fixed: 268 corrupted stems, 985 false/leaking hints; 28 deleted; **809 Benjamin questions quarantined** |
| content-production (successor) | 29,504 q, ~250 critical | **29,460 q, 0 critical** | Fixed: 2,416 hint leaks, 557 broken stems, 47 wrong answers, 221 junk choices, 1,090 missing hints generated, 2,686 broken interaction modes; 44 deleted |

All 307 content files re-parse cleanly. Question counts reconcile exactly with deletion logs. Index/metadata counts updated.

---

## 1. Unnecessary lines

**Found:** duplicated sentences, story-wrapper debris ("Google works on the numbers", "Has 939 wheels ready" with no subject), "Help calculate:" fragments, double spaces/stray punctuation, and — worst — **truncated stems where an earlier cleanup ate the names**: "Faiz is older than . is older than Dia. Who is the oldest?" (148 in v2, 558 in production).

**Fixed:** 3,086 punctuation/spacing fixes (prod) + 83 (v2) + 4 (v4); 694 broken-name stems rebuilt from the choices and **machine-verified against the keyed answer** (e.g. T4-0608 → "Ethan is older than Chloe. Chloe is older than Beni." key Ethan ✓); 133 subject-less sentences repaired; 8 stems restored from `original_stem`.
**Left (cosmetic, logged):** ~600 mild filler phrases per set, 1,084 non-roster character names — harmless, listed in issue JSONs.

## 2. Mismatched visuals

**Found:** the nastiest was a **recycled pictograph**: one identical chart served 23 different questions whose keyed answers ranged from 2 to 18 — at most one could match the picture. Plus 23 chart-type mismatches, 10 count-vs-answer mismatches, 8 stem-object vs image-object mismatches.
**Fixed:** wrong/mismatched SVGs nulled where the question works from text (33), questions deleted where the picture was essential (24). T3-218 ("drum circle" vs star SVG) verified a false positive and kept.

## 3. Missing visuals

**Found:** 4,470 "caption-in-a-box" placeholder SVGs that survived the earlier pass (a grey box reading "Colourful apples arranged in groups" shown to a 6-year-old); 147 essential-tagged questions with no SVG; 80 questions like "How many balloons in the picture?" with **no picture and no way to answer**.
**Fixed:** all 4,423 caption-box placeholders nulled; 146 essential tags verified text-solvable and downgraded; 21 stems enriched/reworded so the text contains what the picture was meant to show; **116 genuinely unanswerable questions deleted** (logged in full).
**Left:** 622 v4 questions tagged "required" visual with no SVG (answerable from text, flagged for future art).

## 4. Right answers

**Found and fixed — every one hand- or machine-verified:**
- **Benjamin olympiad: 75% of answers confirmed to be placeholders** (keyed to first choice). The whole set (809 questions) is now **quarantined** in `quarantine/benjamin-olympiad/` and no longer served. Re-keying requires solving each question or re-extracting keys from the PDFs (README in the folder).
- ~125 story-rewrite corruptions where addition wording was pasted over subtraction/division math while keeping the old key ("939 wheels, 585 more arrive" keyed 939−585) — stems rewritten to match the verified key, using `original_stem` as ground truth.
- 53 systematic coordinate mis-keys ("2 right" keyed as 2 up) — re-keyed.
- 219 + 221 "(alt)" choice artifacts — including **152 where a duplicate of the correct answer sat among the distractors** (child picks the right value, gets marked wrong) — replaced with format-aware distractors.
- Individual impossible answers fixed: "50% of 25 = 12", non-integer patterns, truncated averages, place-value off by ×10, 26 word problems where a child ends up with **negative money**, comparison questions whose choices contained neither compared number, T1-1182 re-solved by brute force (3332).
- Re-verification: **0 mis-keyed answers remain** among all programmatically checkable questions in all three sets.

## 5. Socratic hints

**Found:** the biggest quality gap. 9,315 hints ended by listing all the choices; 3,500+ hints terminally revealed the answer ("126 ÷ 7 = 18" as the "hint"); 863 hints showed arithmetically false working ("4 + 3 + 12 = 5"); 1,090 wavebook questions had no hints at all; 127 ladders belonged to a different topic than their question.
**Fixed:** all template noise stripped; all 3,500+ leaks unsolved ("126 ÷ 7 = ?"); all 888 false workings recomputed from the stem; **1,090 wavebook hint ladders generated** (topic-aware, cite the stem's actual numbers, never reveal — e.g. cube-painting: "Corners get 3 painted faces, edges 2, face-centres 1 — which cubes are hidden inside?"); 127 wrong-topic ladders replaced. Zero empty levels, zero leaks on re-scan.
**Left (the known moat gap):** ~18,700 hints across the sets are valid but generic (don't cite stem numbers). They work, but regenerating them with question-specific Socratic scaffolds is the single biggest content-quality investment remaining.

## Also fixed along the way

2,686 broken interaction modes in content-production (1,543 `tap_to_reveal` — the mode behind the May 3 "no options" bug — and 1,143 nulls → `mcq`; 4,030 `multiple_choice` normalized to `mcq`), metadata/topic counts re-synced, 22 off-grade G1 questions listed for re-grading (`qa-reports/prod_offgrade_report.json`).

## What this means for you

1. **Deploy to ship the fixes**: `cd ~/Downloads/kiwimath/backend && ./deploy.sh` (content is baked into the image). Commit first: `git add -A && git commit -m "Full question QA: fix answers, hints, visuals; quarantine Benjamin" && git push`.
2. **Benjamin decision**: the set stays quarantined until re-keyed. If you want it back, the honest path is re-extracting answer keys from the 17 PDFs (or I can solve them question-by-question in a future session — ~800 questions).
3. **Remaining backlog (quality, not correctness)**: generic hint regeneration (~18.7k), real SVGs for 622 visual-flagged questions, 22 off-grade G1 items, grade 5–6 depth.
4. Every deletion is recoverable: full question bodies in `qa-reports/*_deleted_questions.json`.
