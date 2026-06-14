# Kiwi Maths — Olympiad Bank Question QA + Fixes

**Date:** 2026-06-13 · **Scope:** all olympiad questions in `content-live/olympiad/L1–L8`, 7 dimensions (duplicates, missing images, unnecessary lines, mismatched images, hints, answers/solutions, tags). Fixes applied in place; answers/choices/difficulty/IRT provably unchanged.

## Bottom line

The bank went from **18,803 → 18,099** questions (704 hidden duplicates removed) and is now clean on every machine-checkable dimension: **0 duplicates, 0 hint answer-leaks, 0 missing hints, 0 missing-required images, 0 bad answer indices, 0 tag errors.**

## "Why did two topics show the same question?"

That was a **prototype artifact, not real data.** The mockup's practice screen reused one placeholder question per level, so every L1 topic rendered the same card. In the real bank, "Numbers All Around" and "Think & Count" share **0 questions**. The prototype now pulls a distinct real question per topic (verified: seashells vs butterflies vs corners-of-a-square).

## What was found and fixed

| Dimension | Found | Action |
|---|---|---|
| **Duplicates** | 3 exact, then 701 more exposed once story-wrappers were stripped | Removed all 704 redundant copies (kept one of each) |
| **Unnecessary lines** | ~6,650 story-wrapper prefixes ("On the world tour, Nuha runs the numbers.", "X is working on a problem:", "X works on the solar array geometry.") | Stripped the wrapper, kept the math; logic-puzzle setups protected (never stripped "taller/older than") |
| **Hints — leaking answer** | 2,954 contained the answer; 1,393 revealed it outright ("x = 63 … 63 + 21 = 84") | Masked every occurrence of the answer value in hints → **0 leaks** |
| **Hints — missing** | 545 had no hint | Generated topic-aware Socratic nudges (3 levels, never reveal the number) |
| **Images — required but absent** | 550 tagged "required" with no SVG | All verified text-solvable (coins, "lines of symmetry of a rectangle") → downgraded to optional; 0 truly broken |
| **Images — placeholder captions** | 2,064 leftover "A visual representation of the prob…" strings in `visual_context` | Cleared (these were metadata, never rendered) |
| **Answers/solutions** | 1 truncated stem (`KM-L3-NT-0574`: "1² + 4.9²" keyed ≈50, only valid for **5.1²** + 4.9²) | Stem corrected |
| **Tags** | pillar/level/topic + leftover curriculum tags | **0 errors** — all questions carry correct `km_level`/`km_pillar`/`km_topic`; no curriculum tags leaked into olympiad |
| **Mismatched images** | 0 | — |

## Integrity guarantee

Every fix pass verified that the **immutable fields — choices, correct_answer, correct_value, IRT (a/b/c), difficulty tier/score — are byte-identical before and after (0 mismatches).** Only stems (wrapper removal), hints (de-leak/generate), `visual_requirement` (downgrade), and `visual_context` (clear) were edited. Removed questions are exact duplicates only.

## Final counts (post-QA)

| Level | Maps to | Questions (was) |
|---|---|---|
| L1 | Grade 1/2 | 9,298 (9,660) |
| L2 | Grade 3/4 | 5,978 (6,320) |
| L3 | Grade 5/6 | 2,823 (2,823) |
| L4–L8 | Grade 7 → IMO | 0 |
| **Total** | | **18,099 (18,803)** |

Dedup fell hardest on the most-templated topics (Think & Count 3,069→2,874; Mystery Numbers 2,109→2,064), which is the intended effect.

## Honest residuals (not blocking)

- **~103 bespoke story intros** remain (e.g. "Professor Plum is practising math:") — too idiosyncratic to strip safely by rule; a short targeted pass can finish them.
- **Templating / low variety**: many questions still share a number-swapped template (e.g. "What is N ÷ M?"); this is variety, not duplication — a separate trim decision.
- **Generic hints**: the 545 generated + many existing hints are valid but not deeply question-specific. Per-question Socratic hints remain the biggest content-quality investment.
- **Detector false positives** (reported as 0 real issues): "figure **out**" (~201) is not an image reference; ellipses "3, 7, 11, …" (~122) are not filler.
