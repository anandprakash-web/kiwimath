# Kiwimath Strategic Plan — Living Document

**Created:** May 2, 2026
**Status:** Active — revisit regularly as we iterate

## What This Is

Anand requested a 35,000ft view of Kiwimath from 6 leadership perspectives.
We've been so deep in execution (376 tasks completed) that we risk losing the forest for the trees.

This document captures the INTENT and DIRECTION. The full deliverable is in:
→ `KIWIMATH_PRODUCT_BIBLE.md` (comprehensive document)

## The 6 Perspectives

| Role | Question It Answers |
|------|-------------------|
| Head of Product | What are we building and why? Who is it for? What's the north star? |
| Head of Design | How does every screen connect? What's the full UX flow? |
| Head of Curriculum | What do students learn? How do we measure growth? What's "grade level"? |
| Instructional Designer | How does content flow? What is "smart practice"? Session design? |
| Program Manager | How do all pieces fit together? What ships when? Dependencies? |
| Head of Engineering | Architecture? Data flow? How do systems talk to each other? |

## Key Design Decisions (to remember)

1. **Grade change** — Must be possible post-onboarding (currently broken)
2. **Home screen** — Should have Olympiad/Curriculum toggle (like Path tab does)
3. **Topic labels** — Show full names, not IDs ("Numbers up to 20" not "ch1")
4. **Curriculum is optional** — Olympiad users don't need NCERT/ICSE selection
5. **Academic height** — Each student has a theta range that maps to grade level
6. **Remedial vs stretch** — Below grade range = remedial; above = olympiad/next grade
7. **Year-long pacing** — A grade curriculum spans ~40 weeks; we need pace guidance
8. **Parent communication** — Must clearly tell parents WHERE their kid is vs grade level

## Decisions Made (May 2, 2026 feedback session)

1. **The moat is content quality, not the engine** — Engine is delivery mechanism only
2. **IGCSE → Cambridge Primary** — IGCSE is Grade 9-10, not K-6
3. **Curriculum picker:** CBSE / ICSE / Cambridge Primary / Singapore / Olympiad
4. **Diagnostic is weak** — 10 Qs can't place across 37 skills. Use staged confidence.
5. **Parent hero = Academic Height + Growth** — NOT accuracy ring
6. **Parental gate = PIN** — Math problem fails for Olympiad kids
7. **Olympiad = Boss Levels** — Not a separate track. Integrated into curriculum path.
8. **Offline mode needed** — Download session batch, sync on complete
9. **Review cap** — Max 3 reviews per session, never all-review sessions
10. **Content Quality Gate** — 7 mandatory checks before any Q enters production

## Decisions Made (May 2, 2026 — Strategy V2 refinement)

11. **Spiral Diagnostic** — Starts at G3 anchor, binary-searches ±2 grade jumps. Age is IRT prior, engine overrides.
12. **Academic Height as continuous metric** — AH 3.4 = between G3 and G4 ability. Not capped by age.
13. **Goal Height + Velocity** — Parent sets target AH + timeline. Engine calculates velocity and adjusts intensity.
14. **3-Layer Hints with option elimination** — Hint1: conceptual. Hint2: 1 option fades. Hint3: 50/50.
15. **Visual requirement tagging** — Essential/Optional/None per Q. AI recheck validates visual matches math.
16. **3D for spatial** — Volume, surface area, geometry with interactive rotation.
17. **Skip = High Uncertainty** — Triggers remedial warmup next session.
18. **Targeted Mastery** — "Test on Friday" parallel plan in Curriculum tab. Doesn't alter core state.
19. **Smart Auto-Flagging** — 3 high-theta students miss same Q → auto-quarantine.
20. **Year-End Pacing** — Standard (wk 1-30) → Crunch (wk 31-40, retrieval only, no new levels).
21. **Universal Mapping Layer** — Locale-appropriate context (₹/mangoes vs $/apples) via GPS auto-detect.
22. **Curricula are "skins"** — CBSE/ICSE/Cambridge/Singapore/Common Core = backend mapping layers only.

## Decisions Made (May 2, 2026 — CLM + Spiral v2)

23. **Expanding Spiral Algorithm** — Age-based seed (not fixed G3), asymmetric V-jumps (+1.5/-1.0), cross-curriculum check for conceptual vs contextual failure.
24. **SEM-based termination** — Diagnostic stops at SEM < 0.15, not fixed Q count. 8-16 Qs adaptive.
25. **3D Academic Height** — Depth (vertical AH) + Breadth (% topics mastered) + Stability (fluency coefficient).
26. **Altimeter diagnostic UI** — Kiwi bird flying higher, dynamic backgrounds Forest→Clouds→Space.
27. **High Uncertainty Recovery** — Noisy profile → first week = Extended Benchmarking with parent messaging.
28. **Grand Unified Question Schema** — Universal_Skill_ID, IRT params, curriculum_map, country_context, behavioral tags, media integrity hash.
29. **Question Maturity Lifecycle** — Bucket A (Experimental N<100) → B (Calibrating 100-1K) → C (Production N>1K). Only C used for AH benchmarking.
30. **Hash-Linked Content Integrity** — media_hash + media_id in JSON, CI/CD pre-deploy validation, build fails on mismatch.
31. **3-R "Why?" Framework** — Re-Contextualize → Redirect → Reinforce (micro-question). Few-shot LLM generation path.
32. **Universal Pull Logic** — Sample from pre-compiled probability distribution, not search. Nightly rebuild.
33. **Admin Pulse Dashboard** — Weekly top-50 contested questions. One-click edit in JSON portal.
34. **High-Theta Auto-Lock** — High-AH students miss "easy" Q → auto-lock, difficulty mismatch suspected.

## Open Questions (for future sessions)

- Should we merge Path tab into Home? (currently 3 tabs, could be 2)
- How should grade change work? (top bar picker vs settings vs swipe) — LEANING: tappable badge
- What's the monetization gate? 7-day trial → 1 session/day (not topic-locked)
- When do we show Academic Height? Only after confidence = High (10+ sessions)
- How to handle "Help Me" when kid is stuck across 3+ sessions?
- Do we need a full design system doc (component library, spacing, typography)?
- How does Goal Height interact with Level progression? (AH is continuous, Levels are discrete)
- What happens when a kid hits their goal height mid-year? Auto-extend?

## Documents Created

| Doc | Path | Purpose |
|-----|------|---------|
| Product Bible | `KIWIMATH_PRODUCT_BIBLE.md` | 35,000ft view, all 6 perspectives |
| Content Quality Gate | `CONTENT_QUALITY_GATE.md` | 7-gate framework for content QA |
| Adaptive Engine Plan | `ADAPTIVE_ENGINE_PLAN.md` | Technical plan + research citations |
| Strategy V2 | `STRATEGY_V2.md` | Levels replace grades, full rethink |
| This file | `memory/projects/kiwimath-strategic-plan.md` | Decisions + open questions |
