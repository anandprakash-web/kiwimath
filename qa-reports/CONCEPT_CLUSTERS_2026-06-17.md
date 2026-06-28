# Concept Clustering — original concepts per level (2026-06-17)

Foundation for the adaptive layer. Every served question (olympiad L1–L7 + curriculum, **30,349** total) is now tagged with the **skill cluster** it belongs to. A "skill" = one underlying concept; the many number-varied / wording-varied copies of it collapse into that one concept.

## Headline: original concepts per level

| Level | Questions | **Original concepts** | Repetition × |
|------|-----------|----------------------|--------------|
| **L1** (G1–2) | 8,766 | **1,916** | 4.6 |
| **L2** (G3–4) | 5,374 | **461** | 11.7 |
| **L3** (G5–6) | 2,823 | **2,456** | 1.1 |
| **L4** (G7–8) | 800 | **184** | 4.3 |
| **L5** (IOQM) | 900 | **184** | 4.9 |
| **L6** (RMO) | 800 | **379** | 2.1 |
| **L7** (INMO) | 550 | **330** | 1.7 |
| **Olympiad total** | 20,013 | **5,910** | 3.4 |
| **Curriculum total** | 10,336 | **2,295** | 4.5 |
| **GRAND TOTAL** | **30,349** | **8,205** | **3.7** |

So across the whole bank there are **8,205 distinct concepts**, each backed on average by ~3.7 interchangeable questions.

## What "one concept" means here

Each stem is reduced to a concept signature — numbers → `#`, character names and "Help X figure out:" lead-ins stripped, math operators normalised (`×`→mul, `÷`→div, `−`→sub…), math structure kept — then questions are grouped when their signatures overlap enough (leader clustering, Jaccard ≥ 0.70). Examples:

- "ratio 4:5, find the larger angle" + "ratio 7:2, find the larger angle" → **1 concept** (`SK-L4-…`).
- "What comes next: 2,4,6,8?" + "Find the next number: 2,4,6,8" → **1 concept** (wording merged).
- "What is 11 × 9?" and "What is 32 ÷ 4?" stay **separate** (different operation).
- Area and perimeter of a rectangle stay **separate** concepts.

Leader clustering (each template compared only to fixed cluster leaders) avoids the chaining that would otherwise merge *number* sequences with *shape* patterns.

## Where the adaptive value is — skill-size distribution

| Level | unique (1) | small (2–4) | medium (5–15) | large (16+) |
|------|-----------|-------------|---------------|-------------|
| L1 | 1,044 | 556 | 200 | 116 |
| L2 | 266 | 57 | 51 | **87** |
| L3 | 2,295 | 141 | 18 | 2 |
| L4 | 10 | 111 | 60 | 3 |
| L5 | 23 | 80 | 78 | 3 |
| L6 | 192 | 158 | 29 | 0 |
| L7 | 248 | 63 | 19 | 0 |

Reading this:
- **L2 and L1** have big template families (87 and 116 concepts with 16+ variants each) — this is where the adaptive engine can *ladder difficulty within a concept* and *avoid repeating near-identical items*. Highest adaptive payoff.
- **L3 and L7** are mostly **unique** problems (2,295 and 248 singletons) — bespoke olympiad items. Here the adaptive engine works *across* concepts, not within (there's no ladder inside a singleton).
- **L4/L5** (IOQM / Grade 7-8 imports) are clean parametric families — almost no singletons, mostly 2–15 variants per concept.

## Concepts by pillar (olympiad)

| Level | Number Theory | Algebra | Geometry | Combinatorics |
|------|--------------|---------|----------|---------------|
| L1 | 365 | 410 | 505 | 636 |
| L2 | 193 | 129 | 117 | 22 |
| L3 | 610 | 846 | 557 | 443 |
| L4 | 41 | 41 | 50 | 52 |
| L5 | 39 | 45 | 41 | 59 |
| L6 | 84 | 94 | 121 | 80 |
| L7 | 75 | 85 | 41 | 129 |

## The tags written on every question (additive, nothing else changed)

| Field | Meaning |
|-------|---------|
| `skill_id` | the concept cluster, e.g. `SK-L2-0185` (olympiad) / `SK-NCERT-GRADE3-0042` (curriculum) |
| `skill_size` | how many questions share this concept |
| `skill_rank` | difficulty rank within the concept (0 = easiest), by `irt_b`/`difficulty_score` — the ready-made ladder |
| `is_skill_original` | `true` on exactly one canonical exemplar per concept (the "original concept question") |

Integrity: **0** existing-field changes across all 30,349 questions (only the 4 skill fields added). `pre_deploy` green, smoke 17/17.

Index: **`content-live/skill_clusters.json`** — `skill_id → {label, scope, topic_file, size, difficulty_range, members[]}` for all 8,205 concepts.

## Why this sets up the adaptive layer

The engine now has a clean three-level hierarchy: **Level → Pillar/Topic → Concept (`skill_id`) → item (`skill_rank`)**. That enables:
1. **Anti-repetition** — never show two items from the same `skill_id` back-to-back; one correct answer can "credit" the whole concept.
2. **Difficulty laddering** — within a concept, walk `skill_rank` up/down to hit the ZPD (target 65–80% success) without changing topic.
3. **Mastery accounting** — measure mastery over **8,205 concepts**, not 30k items (far more stable signal).
4. **Coverage** — the singleton-heavy levels (L3/L7) tell the engine to broaden across concepts; the family-heavy levels (L1/L2) tell it to ladder within.

Granularity is tunable: the cluster threshold (0.70) and the name/operator normalisation live in one place; re-running re-tags idempotently.
