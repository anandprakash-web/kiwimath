# ACAD OS — The Operating Manual

**What this is.** The complete, canonical documentation of the academic operating system built across the Kiwimath cowork spaces: how content is created, how the library is built, how the codebase fits together, the scripts that run it, and — just as important — **how it was approached, what changed, and every class of mistake we hit and solved.** It is written so a fresh Cowork/Claude session (or a new teammate) can pick up the whole system and keep building.

**Owner:** Anand Prakash (anand.prakash@vedantu.com) — founder.
**Built on:** Flutter (app) + FastAPI (backend) + Firebase, with content as JSON files baked into the backend image.

---

## What "ACAD OS" means

It is **not** a math app. It is a **content-agnostic academic platform** — an operating system for adaptive learning — that currently runs a K-6 math instance (Kiwimath) and is being forked into exam instances (JEE/NEET). The OS has four layers, and only the top one knows what subject it's teaching:

```
   ┌──────────────────────────────────────────────────────────────┐
   │  CONTENT  — questions, taxonomy, QA, adaptive tagging          │  ← subject lives here
   ├──────────────────────────────────────────────────────────────┤
   │  LIBRARY  — books (faithful / authored / interactive), reader  │
   ├──────────────────────────────────────────────────────────────┤
   │  ENGINE   — adaptivity, economy, contest/league, persistence   │  ← subject-blind
   ├──────────────────────────────────────────────────────────────┤
   │  APP      — Flutter shell, the surfaces the learner touches     │
   └──────────────────────────────────────────────────────────────┘
```

The engine and app are **subject-blind**: they read a question's difficulty, its concept id, and whether the learner got it right — never its meaning. That is the whole reason new exam apps are cheap to make (see `06` and the separate `HANDOVER_MINIAPP/` pack).

---

## How to use this manual

Read `00` once, then live in the file that matches your job:

| File | Read it when you need to… |
|------|---------------------------|
| `00_START_HERE.md` | Understand the whole system + the operating principles (this file). |
| `01_CONTENT_SYSTEM.md` | Create, ingest, validate, or QA questions; understand the taxonomy and the adaptive tagging. |
| `02_LIBRARY_SYSTEM.md` | Build a book (faithful-render / authored / interactive), wire it into the store, or touch the reader. |
| `03_CODEBASE.md` | Understand the backend services, the `/v3` API, the app, persistence, and how to deploy. |
| `04_MISTAKES_AND_LEARNINGS.md` | **Read before any content work.** Every defect class (content + engineering + process) and how to avoid re-introducing it. |
| `05_SCRIPTS.md` | Run any of the reusable scripts (collected in `scripts/`). |
| `06_APPROACH_AND_EVOLUTION.md` | Understand *why* the system is shaped the way it is — the decisions, reversals, and method. |
| `ACAD_OS_THE_STORY.md` | A single linear narrative of the whole journey, start to finish. Good first read for orientation. |
| `scripts/` | The actual reusable code: content QA, ingestion, book builders, verification. |

There is also a companion pack, `HANDOVER_MINIAPP/`, focused specifically on forking the platform for a **new exam**. This manual is the *full* system; that pack is the *fork recipe*.

---

## The operating principles (non-negotiable)

These are distilled from hundreds of hours of work. Every one was learned the hard way (the war stories are in `04` and `06`). A new cowork that internalizes only this list will avoid most of our mistakes.

### On content
1. **Content comes from authoritative sources or domain experts — the AI never invents it.** For math, single-step arithmetic *can* be machine-verified; for Physics/Chem/Bio it cannot, so the rule is absolute: copy from source, never author or re-key.
2. **A figure is an *aid*, never the *answer*.** If summing/counting the figure's marks yields the answer, the figure is wrong. Show *givens*, not the worked decomposition.
3. **Never reference a picture you don't show.** If the stem says "shown / the figure / dots / shaded," a real figure must exist — else reword to pure self-contained text.
4. **Math-check every answer key in a computable family.** `correct_answer` is *not* sacred. Build a validator per family. This is how we caught keys where a kid does it right and is told they're wrong — the most trust-destroying defect.
5. **Plain language beats clever framing.** The wording must never be harder than the concept.
6. **Visuals only where genuinely required.** Default to no figure; geometry is where figures earn their place.

### On every edit
7. **Fix one field, touch one field.** Back up first, diff against the backup, and assert *only* the intended field changed. `correct_answer`, `choices`, `hint`, `difficulty`, the adaptive tags are **locked** unless the fix is specifically about them.
8. **Render before you ship a figure.** Generate the image and look at it (cairosvg) — never trust the markup.
9. **Detect, don't eyeball.** Every mistake class becomes a re-runnable detector in the scanner, so we never re-introduce it and never have to inspect tens of thousands of items by hand.

### On the workflow
10. **Batch then QA.** Ingest/edit one batch, QA it, re-tag, keep the smoke tests green, *then* continue. Never a big-bang change.
11. **Slow and certain.** "We can be slow, only 100% certain." A missing item costs nothing; a wrong item costs a user. Always prefer the gap.
12. **Keep green.** After every change: the A–N scanner, `pre_deploy_check.py`, and the smoke tests must pass. A green baseline is the safety net for the next change.
13. **Parallelize with subagents, verify centrally.** Big jobs (writing 20 book chapters) fan out to subagents that each brute-force-verify their own math; one central pass QAs the whole.

---

## The canonical content loop (memorize this)

Everything in the content layer is one loop:

```
   ingest / author  →  cluster (tag concepts)  →  scan (A–N detectors)
        →  fix flagged items (one field, backed up)  →  re-scan until 0
        →  pre_deploy_check + smoke tests  →  deploy
```

The scripts in `scripts/` are the tools for each step. The defect classes the scan looks for are in `04`. The deploy is one command (`03`).

---

## Current state (snapshot)

- **Served question bank:** ~19.6k olympiad (levels L1–L7; L8/IMO intentionally empty) + ~10.3k school-curriculum questions, all concept-clustered for the adaptive ladder.
- **Library:** faithful-render upper-tier books + grade workbooks + two from-scratch authored books (L2, L3) + an interactive Number Sense book (ongoing). Purchase → download → read-offline flow, all free for now.
- **Engine:** adaptive skill-ladder, one shared economy, daily contest + weekly league, durable per-user state.
- **App:** Flutter `/v3` stack (the current spine). Older v2/v4/v8 layers are superseded — ignore them.
- **Status:** core systems green (the smoke suites pass); remaining work is content depth, the un-validated answer-key families, and on-device app polish. Full open-items list in `04` and `06`.

Start with `ACAD_OS_THE_STORY.md` for the narrative, then dive into the layer you need.
