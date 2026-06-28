# 02 · Fork vs. Rebuild — what you keep, reconfigure, or build fresh

This is the core deliverable. It tells the new cowork **exactly** which parts of Kiwimath to carry over untouched, which to edit (config only), and which to build from scratch (content + branding). File paths are relative to the Kiwimath repo root (`~/Downloads/kiwimath`).

---

## First: fork the `/v3` stack, ignore the rest

The repo has **years of layers**. Only the newest one — the **`/v3` "level" stack** — is the clean, current spine. Fork that. Treat everything else as archaeology.

**The golden path (fork these):**
- Backend services: `adaptive_skill.py`, `content_store_level.py`, `contest_service.py`, `league_service.py`, `economy_service.py`, `store_service.py`, `gamification.py`, `firestore_service.py`, `core/auth.py`
- Backend API: `api/level.py`, `api/contest.py`, `api/store.py` (the `/v3` routes)
- App: `app/lib/v3/*` + `app/lib/main_v3.dart`
- Content: `content-live/` (the served bank) + `content-books/` (the library)
- Tests: `backend/tests/smoke_level_v3.py`, `smoke_adaptive_skill.py`, `smoke_contest_league.py`, `smoke_store.py`

**Leave behind (legacy — do NOT carry into the new app):** `content_store_v2.py`, `content_store_v4.py`, `content_store.py`, `questions_v2.py`, `questions_v4.py`, the Clan system (`clan_*`), Wavebook, Benjamin-olympiad, the v8 6-tab `main.dart`, and the `content-v2/`/`content-v4/` banks. They're superseded and exam-irrelevant. Carrying them will only confuse the build.

> If in doubt: if a file isn't in the golden-path list above and isn't obviously needed, don't fork it. A lean fork is the whole point.

---

## Category A — Reuse AS-IS (copy, do not touch the logic)

These are pure machinery. They read `difficulty`, `skill_id`, right/wrong, wallets, and timestamps. They contain **no subject knowledge**. Copy them and move on.

| Component | File(s) | What it does | Why it's safe to reuse |
|-----------|---------|--------------|------------------------|
| **Adaptive engine** | `backend/app/services/adaptive_skill.py` | Picks the next question; skill-ladder (right→advance, wrong→drill variants); persists position per user. | Operates on tags + difficulty + correctness only. |
| **Economy** | `economy_service.py`, `gamification.py` | One wallet (coins/gems/XP/streak); earn on practice, spend in store; idempotent. | Currency has nothing to do with subject. |
| **Contest** | `contest_service.py` | Deterministic daily set, server-side grading, one-attempt, score = speed × streak × correctness. | Generic timed-quiz logic. |
| **League** | `league_service.py` | Weekly cohorts (~30 users), tiers, promote/relegate, rollover. | Generic ranking logic. |
| **Store backend** | `api/store.py` | Catalog, entitlements, claim/unlock, gated content bytes, covers. | Catalog *rows* change; the API doesn't. |
| **Reader (app)** | `app/lib/v3/html_book_reader.dart`, `book_reader.dart`, `books_browse.dart` | In-app reader (HTML/PDF), painted covers, filters, download-to-read. | A reader doesn't care what the book is about. |
| **Contest UI** | `app/lib/v3/contest_screens.dart` | Lobby → timed quiz → results + leaderboard. | Generic. |
| **Persistence** | `firestore_service.py` (`FirestoreBackedStore`) | Durable per-user state + in-memory fallback. | Generic key-value store. |
| **Auth** | `backend/app/core/auth.py` | Firebase token verify, `assert_user_match` (blocks cross-user access). | Generic. |
| **Concept tagger** | `content-live/qa-reports/cluster_concepts.py` | Groups near-duplicate questions into concepts (`skill_id`), orders them by difficulty into a ladder. | Works on text signatures + difficulty; re-run it on *any* question bank. |

**Rule for Category A:** if you're editing the *logic* of one of these, you've probably taken a wrong turn. You edit their *inputs* (the content), not them.

---

## Category B — Reconfigure (edit config / labels only, not logic)

These need small, surgical edits: change the list of subjects, the catalog rows, the branding. The code structure stays.

| Component | File(s) | The edit |
|-----------|---------|----------|
| **Taxonomy / strands** | `content_store_level.py` → the `OLYMPIAD_STRANDS` list + `PILLAR_NAMES` | Replace the 9 math strands with your exam's subjects (NEET → Physics/Chemistry/Biology; JEE → Physics/Chemistry/Math). It's a list of `{code, name}` dicts. Also the level/grade labels. |
| **Content store loader** | `content_store_level.py` (the `LQ` class + load paths) | Point it at your new content folders; keep the record fields. Add a field only if a new answer-type needs it (see Category C). |
| **API labels** | `api/level.py` | Endpoint *paths* stay (`/v3/...`). Any user-facing strings (level names, "Olympiad") get renamed. The route logic stays. |
| **Store catalog** | `store_service.py` → `_CATALOG` + `_BOOK_FILES` | Replace the math-book rows with your exam's books (past-paper compilations, formula books). Same row shape: id, title, subject, levels, pricing, file. |
| **App shell / tabs** | `app/lib/v3/kiwi_v3.dart` | Rename tabs, swap the subject pickers, point at the new taxonomy. The tab *machinery* stays. |
| **Branding / theme** | `app/lib/main_v3.dart` | App name, colors (Kiwimath orange → your palette), logo, splash. |
| **Daily-quiz pool rule** | `contest_service.py` (`todays_qids`) | Already prefers the "verified" pool — just make sure your trusted content is tagged `verified`/has a `source`. No logic change, only data. |

**Rule for Category B:** these are find-and-replace + config edits. If an edit turns into rewriting a function body, re-read `01` — you may be fighting the platform instead of using it.

---

## Category C — Build fresh (the real work, and it's mostly NOT code)

This is where the new app actually gets made. Notice how little of it is engineering.

### C1. The content packs — **sourced, never generated** (biggest effort)
The questions themselves. For exam prep these come from **authoritative sources**: official past papers (PYQs), licensed question banks, and subject-expert-authored material. They get transformed into the question-record format from `01`. **The AI's job is the transformation plumbing and the formatting — never inventing the question or its answer key.** Full method + guardrails in `04`.

### C2. The taxonomy content
The actual chapter and concept lists for each subject (e.g. NEET Biology's chapter list). This is reference data you pull from the official syllabus — not something to improvise. Drop it into the config from Category B.

### C3. New answer-types (only if needed — small)
The schema already handles **single-choice MCQ** and **typed numeric/text** (with an accept-range for decimals). Some exams add modes the math app didn't use heavily:
- **Multiple-correct MCQ** (JEE) — store the answer as a *set* of indices; grading compares sets. Small addition to the grading function.
- **Assertion–Reason / Matrix-Match** (some exams) — usually expressible as single-choice once authored, so often **no code change** — just author them as 4-option MCQs. Prefer this; don't build new UI unless a mode truly can't be expressed as MCQ.

> Keep new modes to a minimum. Every new mode is new grading + new UI + new bug surface. Most exam content fits MCQ + typed-numeric, which already exist.

### C4. Branding & store assets
App icon, name, cover art for the books, color palette. Design work, not engineering.

### C5. Difficulty calibration
The engine needs each question's `difficulty` to order the ladder. For sourced content, seed difficulty from the **source's own signal** (PYQ year/section, the bank's stated level, or expert tagging) — **do not ask the AI to judge how hard a physics problem is.** Refine later from real learner right/wrong data (the platform already logs it).

---

## Category D — Decisions to make once, early

| Decision | Options | Note |
|----------|---------|------|
| One app per exam, or one app many exams? | Start: one clean fork (e.g. NEET). Then: shared core + content packs. | See `05`. Don't over-engineer the shared core before app #1 ships. |
| Levels/tiers? | Exam prep is usually **one tier** (you're prepping for *the* exam), unlike K-6's 8 levels. | Collapse the Level layer to a single tier; lean on Subject → Chapter → Concept. |
| Free vs. paid surfaces? | Practice free, books paid? Contest free? | The economy + store already support both; it's a pricing config, not a build. |

---

## The honest "what's reusable" scorecard

- **~80% of the engineering carries over untouched or with config edits** (Categories A + B). The platform, the engine, the economy, the contest, the reader, the store, the persistence, the auth — all reusable.
- **The ~20% that's new is mostly content + branding** (Category C), and the content is **sourced and human-validated, not built by the AI.**

That ratio is the reason this is a "mini-app" and not a new product. The build plan in `03` walks the new cowork through it phase by phase.
