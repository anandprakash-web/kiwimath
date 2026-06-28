# CLAUDE.md — {APP_NAME} (seed working memory)

> Drop this in the new app's repo root as `CLAUDE.md`. It's the starter brain for the Cowork/Claude session building this app. Fill the `{PLACEHOLDERS}`, then grow it as you work. It is intentionally **content-light** — this app's content comes from authoritative sources, never from the model (see the Golden Rule below).

---

## ⚠️ GOLDEN RULE — read before any content work

**The AI builds the machine. Authoritative sources supply the content. The AI never authors, solves, re-keys, or judges the difficulty of a subject question.**

This app teaches **{EXAM}** ({SUBJECTS}). Unlike arithmetic, these answers **cannot be recomputed by a language model** — attempting to generate or "verify" them produces confident, wrong output, and one wrong answer key destroys student trust. So:
- ✅ Convert source items into question records, tag them, format them, run mechanical QA, keep a skip log.
- ❌ Never write new questions/solutions, never solve to make/confirm a key, never "improve" a source key, never guess difficulty.
- When a source is unclear: **skip and log for a human.** Prefer a gap over a wrong answer, always.

Full detail: `04_CONTENT_GUARDRAILS.md` in the handover pack.

---

## What this app is

A fork of the **Kiwimath `/v3` adaptive-learning platform**, re-skinned for {EXAM}. The platform is content-agnostic: a "question" is just a record with a stem, options/answer, hint, solution, difficulty, tags, and a concept id. The engine, economy, contest, library, and store read those fields — they don't know the subject. We swapped the **content + labels**, not the machine.

**Surfaces:** adaptive practice · daily quiz · daily contest + league · library/reader/store · progress/profile.

---

## Architecture (inherited, do not rewrite)

| Layer | What | Key files |
|-------|------|-----------|
| Adaptive engine | Picks next question; skill-ladder; persists per-user position | `backend/app/services/adaptive_skill.py` |
| Content store | Loads question records; holds the taxonomy config | `backend/app/services/content_store_level.py` |
| API (`/v3`) | Practice/quiz/contest/store routes; server-side grading | `backend/app/api/level.py`, `api/contest.py`, `api/store.py` |
| Economy | One wallet (coins/gems/XP/streak), earn/spend | `economy_service.py`, `gamification.py` |
| Contest + League | Daily scored event + weekly cohorts/tiers | `contest_service.py`, `league_service.py` |
| Store | Catalog + entitlements + gated book bytes | `store_service.py`, `api/store.py` |
| Persistence | Durable per-user state (+ in-mem fallback) | `firestore_service.py` |
| Auth | Firebase verify + cross-user guard | `backend/app/core/auth.py` |
| Concept tagger | Clusters near-duplicate questions → concepts → ladder | `content-live/qa-reports/cluster_concepts.py` |
| App | Flutter shell + the surface screens | `app/lib/main_v3.dart`, `app/lib/v3/*` |

**Taxonomy:** Subject ({SUBJECTS}) → Chapter → Concept (`skill_id`). Configured in `content_store_level.py` (the strand list) + the topic config. One exam tier (not multi-level).

**Content on disk:** JSON question records under `content-live/...`; reference books under `content-books/...`. Baked into the backend image at deploy.

---

## The content record (the one object everything flows from)

```
id · stem · choices · answer · hint · solution · difficulty · tags · skill_id · source · visual
```
Supported answer modes: **single-choice MCQ** and **typed numeric/text** (with an accept-range for decimals). Add multi-correct/other modes only if a real exam needs it and it can't be expressed as MCQ — keep new modes minimal.

---

## How to ship

- **Backend / content change:** `cd backend && ./deploy.sh` (content is baked in → no app rebuild).
- **App UI change:** Flutter build of `app/` (entry `lib/main_v3.dart`).
- **Always keep green:** `backend/tests/smoke_level_v3.py`, `smoke_adaptive_skill.py`, `smoke_contest_league.py`, `smoke_store.py`. Run them after every change.

---

## Working principles (carried from Kiwimath)

- **Slow and certain on content.** "We can be slow, only 100% certain." A wrong key is worse than a missing chapter.
- **Batch then QA.** Ingest one chapter-batch, QA it, re-tag, keep smoke green, then continue.
- **Mechanical QA only.** The QA the AI runs is mechanical (every question answered? duplicates? answer hidden pre-submit? figures render?) — never "is this physics answer right?" That's a human/source job.
- **Difficulty: seed from source, refine from data.** Never from the model's opinion.
- **Rights first.** Only ingest content you can legally serve.
- **Don't fork the legacy layers.** Only the `/v3` stack above is current; ignore older `content_store_v2/v4`, clan, wavebook, etc.

---

## Current status — {FILL IN AS YOU GO}

- [ ] Phase 0: lean fork boots, smoke tests green on baseline content
- [ ] Phase 1: taxonomy relabeled for {EXAM}
- [ ] Phase 2: one real chapter ingested end-to-end (proof)
- [ ] Phase 3: content scaling (chapter batches) — _progress: …_
- [ ] Phase 4: library + store + economy
- [ ] Phase 5: branding + app build
- [ ] Phase 6: shipped + instrumented

## Me
{Your name + role}. Building {APP_NAME} on the Kiwimath platform. Stack: Flutter + FastAPI + Firebase.

## Pointers
- Handover pack: `00_README` → `01_SYSTEM_MAP` → `02_FORK_VS_REBUILD` → `03_BUILD_PLAYBOOK` → `04_CONTENT_GUARDRAILS` → `05_PRODUCT_AND_MONETIZATION`.
- Start every content task with: *"Treat every question and answer key as read-only truth from the source. Format and plumb it; don't solve, author, re-key, or judge difficulty. If unclear, skip and list it."*
