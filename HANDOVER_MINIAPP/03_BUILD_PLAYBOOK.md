# 03 · Build Playbook — phased plan + paste-ready prompts

This is the execution plan for a **new Cowork/Claude session** building the first exam mini-app. Work **one phase at a time**; don't skip ahead. Each phase has a goal, the steps, a **paste-ready prompt** (edit the `{PLACEHOLDERS}`), and a guardrail.

Pick **one exam to go first** (recommend NEET — it's almost entirely single-choice MCQ, the simplest fit). Prove the whole pattern end-to-end on one chapter before scaling.

Throughout, `{EXAM}` = e.g. "NEET", `{SUBJECTS}` = e.g. "Physics, Chemistry, Biology", `{APP_NAME}` = your brand.

---

## Phase 0 — Lean fork of the golden path

**Goal:** a new repo that contains only the `/v3` spine (per `02`), boots, and passes the smoke tests with the *old* math content still in place. Don't touch content yet — first prove the machine runs.

**Steps**
1. Copy the golden-path files listed in `02` into a fresh repo. Skip all legacy layers.
2. Get the backend running locally; run the four smoke tests (`smoke_level_v3`, `smoke_adaptive_skill`, `smoke_contest_league`, `smoke_store`). They should pass against the existing content.
3. Get the Flutter `main_v3` app building.

**Paste-ready prompt**
> "Here is a fork of an adaptive-learning platform (the `/v3` stack). **Do not add or change any subject content in this phase.** Your only job: make the backend boot and pass the four smoke tests in `backend/tests/` (`smoke_level_v3.py`, `smoke_adaptive_skill.py`, `smoke_contest_league.py`, `smoke_store.py`), and make the Flutter app in `app/` (entry `lib/main_v3.dart`) build. Fix wiring/import errors only. Report what passed and what you changed. Read `01_SYSTEM_MAP.md` and `02_FORK_VS_REBUILD.md` first."

**Guardrail:** if the smoke tests don't pass with the *original* content, stop and fix that before anything else. A green baseline is the safety net for every later change.

---

## Phase 1 — Reconfigure the taxonomy (labels only)

**Goal:** the platform now speaks `{EXAM}`'s language — its subjects and chapters — while still serving the old questions. This proves the relabeling works before content arrives.

**Steps**
1. In `content_store_level.py`, replace the strand list (`OLYMPIAD_STRANDS` / `PILLAR_NAMES`) with `{SUBJECTS}`.
2. Collapse the multi-level structure to a **single exam tier** (see `02` Category D).
3. Pull the official **chapter list** per subject from the syllabus (reference data, not invented) into the topic config.
4. Rename user-facing strings in `api/level.py` and `app/lib/v3/kiwi_v3.dart` (e.g. "Olympiad" → "{EXAM}").

**Paste-ready prompt**
> "Reconfigure the taxonomy for **{EXAM}**. Subjects are **{SUBJECTS}**. Collapse the platform's multi-level structure to a single exam tier. I will give you the **official chapter list per subject** — use exactly that, do not invent chapters. Edit only the taxonomy config (`OLYMPIAD_STRANDS`/`PILLAR_NAMES` in `content_store_level.py`) and the user-facing labels in `api/level.py` and `app/lib/v3/kiwi_v3.dart`. Do not touch engine, economy, or contest logic. Keep the smoke tests green."

**Guardrail:** chapters come from **you** (pasted from the official syllabus), never from the model's memory. Syllabi change year to year and the model will confidently produce a stale or wrong one.

---

## Phase 2 — Seed ONE chapter of real content end-to-end (the proof)

**Goal:** one real `{EXAM}` chapter, fully sourced and formatted, flowing through practice + quiz + contest. This is the most important phase — it de-risks everything. **Read `04_CONTENT_GUARDRAILS.md` before starting.**

**Steps**
1. Take **one chapter** from an authoritative source you have rights to (official past papers / licensed bank / expert-authored).
2. Transform each item into the question-record format (`01`). The AI does the **formatting and plumbing**; it copies the stem, options, the **source's** answer key, and the **source's** solution verbatim — it does not author or "check" them.
3. Tag with subject + chapter; set `difficulty` from the source's own signal (year/section/level), not from the model's judgment.
4. Run the concept tagger (`cluster_concepts.py`) to assign `skill_id`s and build the ladder.
5. Verify it appears in practice, quiz, and contest; verify grading works; verify the answer is never sent to the client before submission.

**Paste-ready prompt**
> "I'm giving you **one chapter** of {EXAM} content from an authoritative source (file attached). Convert each question into the platform's question-record format. **Copy the stem, the options, the answer key, and the worked solution exactly from the source. Do NOT solve anything yourself, do NOT change any answer key, do NOT invent questions, hints, or solutions.** If the source is ambiguous or you can't read an item cleanly, **skip it and list it for me** — never guess. For figures, keep the source figure as an image; don't redraw. Set `difficulty` from the source's own level/section, not your own judgment. Then run `cluster_concepts.py` to tag concepts, and confirm the chapter shows up in practice/quiz/contest with answers hidden until submit. Report counts and every item you skipped."

**Guardrail (the big one):** the model must treat the answer key as **read-only truth from the source**. The moment it "recomputes to verify" a physics/chem/bio answer, it can corrupt a correct key. The only allowed validations are *mechanical*: did every question get an answer? are option labels clean? is the answer hidden before submit? are there duplicates? (See `04`.)

---

## Phase 3 — Scale content chapter by chapter

**Goal:** the rest of the subjects, same pipeline, in batches.

**Steps**
1. Repeat Phase 2's pipeline per chapter, **in small batches**, QA each batch, then continue. (This batch-then-QA loop is exactly how Kiwimath ingested its banks.)
2. After each batch: re-run the concept tagger, re-run the mechanical QA scan, keep smoke green.
3. Maintain a **skip log** of every item the model couldn't ingest cleanly, for a human to review.

**Paste-ready prompt**
> "Continue ingesting {EXAM} content one chapter-batch at a time using the Phase-2 rules (copy from source, never generate or re-key, skip-and-log anything unclear). After each batch: re-run `cluster_concepts.py`, re-run the mechanical QA scan, keep the smoke tests green, and give me a per-batch report with counts and the skip list. Stop after each batch and wait for my go-ahead."

**Guardrail:** **slow is correct here.** Anand's standing rule on Kiwimath content is "we can be slow, only 100% certain." A wrong answer key in exam prep destroys trust faster than a missing chapter.

---

## Phase 4 — Library, store, economy

**Goal:** reference books on the shelf, unlockable; economy live.

**Steps**
1. Faithful-render your reference material (past-paper compilations, formula/revision books) into the library format Kiwimath already uses for its books (PDF pages or self-contained HTML).
2. Add catalog rows in `store_service.py` (`_CATALOG` + `_BOOK_FILES`) — same row shape as today.
3. The economy + store backend (`economy_service.py`, `api/store.py`) and the in-app reader need **no logic change** — only catalog data + branding.

**Paste-ready prompt**
> "Add {EXAM} reference books to the library. For each book I provide, render it faithfully into the existing book format used in `content-books/`, add a catalog row in `store_service.py` (`_CATALOG` + `_BOOK_FILES`) matching the existing row shape, and confirm it appears in the Library, unlocks via the economy, and opens in the reader. Don't modify the economy or reader logic. Keep `smoke_store.py` green."

**Guardrail:** only ship books you have the **rights** to distribute. Third-party reference texts are usually *not* redistributable; your own and licensed material is. (This bit Kiwimath — see the IP note in its memory.)

---

## Phase 5 — Branding & app build

**Goal:** it looks like `{APP_NAME}`, not Kiwimath.

**Steps**
1. App name, icon, splash, color palette in `main_v3.dart` + assets.
2. Tab labels and copy in `kiwi_v3.dart`.
3. Build the app; on-device QA the core loop (practice → answer → reward; quiz; contest; open a book).

**Paste-ready prompt**
> "Rebrand the app to **{APP_NAME}**: name, icon, splash, color palette (replace the orange theme with {COLORS}), and all user-facing copy in `app/lib/v3/`. Don't change navigation structure or any service logic. Produce a build and give me an on-device QA checklist for: adaptive practice, daily quiz, contest, and opening a library book."

**Guardrail:** branding is the *last* mile, not the first. Don't let polish start before content is trustworthy.

---

## Phase 6 — Ship + instrument

**Goal:** live, and learning from real usage.

**Steps**
1. Deploy backend (`deploy.sh`); build + release the app.
2. Watch the right/wrong logs the platform already records — that real data is what you use to **recalibrate difficulty** (replacing the seed difficulty from Phase 2).
3. Loop: more content batches, difficulty refinement from data, more books.

**Guardrail:** the difficulty numbers from Phase 2 were seeds. Real learner data is the truth — let it correct the ladder over time. That feedback loop is the product's long-term moat.

---

## The whole plan on one line

> **Fork the spine (P0) → relabel it for the exam (P1) → prove one real chapter end-to-end (P2) → scale content slowly and carefully (P3) → shelves + economy (P4) → brand it (P5) → ship and learn (P6).**

Every phase keeps the smoke tests green and never lets the AI author or re-key subject content. Do that and the first mini-app is a content-and-branding project on a proven engine — exactly as intended.
