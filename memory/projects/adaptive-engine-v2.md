# Adaptive Engine v2 — The Moat

**Status:** Active, building Phase 1-5
**Started:** May 2, 2026
**Plan doc:** `ADAPTIVE_ENGINE_PLAN.md`

## What It Is

Research-backed cross-curriculum adaptive session engine. Pulls from 21,330 questions across 5 curricula, routes via a 37-node prerequisite skill graph, uses per-skill BKT with time-weighted IRT updates.

## Why It's The Moat

No other K-6 math app combines:
1. Multi-curriculum content pool (NCERT + ICSE + Singapore + Olympiad + USCC)
2. Prerequisite skill graph with mastery gating
3. Per-skill ability tracking with sustained mastery verification
4. Forgetting curve with adaptive review scheduling
5. Continuous parent intelligence messaging

## Key Files

| File | Role |
|------|------|
| `backend/app/services/skill_mapper.py` | Maps 21,330 Qs → 37 skills |
| `backend/app/services/unified_session_planner.py` | Cross-curriculum session builder |
| `backend/app/services/skill_ability_store.py` | Per-skill theta CRUD (Phase 1) |
| `backend/app/services/spaced_review_engine.py` | FSRS-lite forgetting curve (Phase 3) |
| `backend/app/assessment/path_engine.py` | 37-node prerequisite graph |
| `backend/app/assessment/irt_model.py` | 3PL IRT with EAP |
| `backend/app/services/content_store_v2.py` | Loads all curricula |

## Phases

1. Per-skill theta + sustained mastery (BUILDING)
2. Response time integration
3. FSRS-lite forgetting curve
4. Cross-skill transfer + learning rate detection
5. Parent intelligence layer

## Research Basis

- 3PL IRT with time-weighted RT (8-15% accuracy gain)
- BKT per skill (37 nodes) — DKT upgrade at 10K+ users
- ZPD targeting: P(correct) ∈ [0.60, 0.85]
- FSRS-lite spaced repetition (PNAS + Anki validated)
- Sustained mastery: ≥80% accuracy, ≥5 items, ≥2 non-consecutive sessions
- Interleaved practice (43% retention benefit)
- Cross-skill transfer from prerequisite graph distances

## Session Structure

```
[2 warmup] → [4 core] → [2 stretch] → [2 review]
```

- Warmup: mastered skill, easy confidence builder
- Core: weakest skill where prereqs ready, ZPD difficulty
- Stretch: above-level challenge
- Review: FSRS-scheduled mastered skills due for refresh
