# 06 · How We Worked & Why the System Evolved

This file is the *method* and the *rationale*: how the work was actually done across the cowork spaces, and why the system took the shape it did. (For the readable chronological story, see `ACAD_OS_THE_STORY.md`; for the defect detail, `04`.)

---

## 1. The working method (what made it reliable)

A handful of habits did most of the work. A new cowork should adopt them verbatim.

**Research-first.** Before building, study the sources/papers and plan. The taxonomy, the adaptive ruleset, the leaderboard, the reader — each began with reading and a written plan doc, not code. The repo is full of these plan docs (`VEDANTU_CONTENT_INTEGRATION_PLAN.md`, `KIWIMATH_LEADERBOARD_DESIGN.md`, the economy contract…). Plans first meant fewer wrong turns.

**Batch then QA.** Never a big-bang change. Ingest one chapter-batch, QA it, re-tag, keep the smoke tests green, then continue. This kept every change reversible and every regression local.

**Slow and certain.** The founder's standing rule: *"we can be slow, only 100% certain."* For content this is the difference between trust and a refund. Always prefer a gap over a wrong item.

**Detect, don't eyeball.** You cannot inspect 30,000 questions by hand. Every defect class became a re-runnable detector in `content_qa_scan.py`. When a live bug revealed a new defect, the *first* move was to write a detector for it — then fix all instances, then re-scan to zero. That's how whole levels reached "0 defects across A–N."

**Keep a green baseline.** After every change: the scanner, `pre_deploy_check.py`, and the smoke suites must pass. Green is the safety net that makes the *next* change safe.

**Fix one field, touch one field.** Back up, edit, diff against the backup, assert only the intended field changed. This single habit prevented countless silent corruptions (a figure fix that quietly alters an answer key, etc.).

**Fan out with subagents, verify centrally.** Volume work — authoring 20+ book chapters, scanning a level — was parallelized across subagents, each of which *brute-force-verifies its own math in Python and render-tests its own figures*, with one central QA pass over the whole. This is how the L2/L3 books (45 chapters, ~1,300 questions) were written with zero wrong answers.

**Render before shipping a figure.** Generate the PNG (cairosvg) and look at it — but verify in the *real* target (the browser) because the converter has quirks. Markup that looks right often renders wrong.

**Log everything in `CLAUDE.md`.** Every pass is recorded there with counts and decisions. It's the project's long-term memory and the reason this manual could be written.

---

## 2. How the founder and the AI collaborated

Worth documenting, because it shaped the cadence:
- **"Keep working on it and I'll be back"** — long autonomous runs, with the AI making sensible default decisions and reporting at the end. The task list + green baseline made this safe.
- **Screenshots drove QA.** Many of the best defect classes (Types F/G/H/I, the cricket-score oddity, the figure overlaps) were found because the founder tested on-device and sent a screenshot. The discipline that followed: *don't just fix the one screenshot — build a detector and fix the whole class.*
- **Two-round critical feedback.** For high-stakes work (the books), the founder sent detailed expert review, sometimes in two rounds, and asked to "combine both and see what's suitable." The AI's job was to apply genuine fixes, verify each in Python, and not over-correct.
- **Decisions confirmed, not assumed.** Big forks (level mapping, book format, what to badge) were posed as explicit choices before executing.

---

## 3. Why each subsystem evolved the way it did

The current shape isn't arbitrary — each piece is the residue of a problem. Understanding *why* prevents a new cowork from "simplifying" something back into a known trap.

**Content reorg (grades → levels; one `content-live/`).** Originally grade-organized with overlapping banks. Reorganized into a single served `content-live/` with the olympiad ladder (L1–L8) separated from the school curriculum. *Why:* the competition progression and the school syllabus are different things with different users; conflating them mis-placed questions and confused the UI. *Lesson baked in:* separate the ladder from the syllabus.

**The QA campaign (and its detectors).** The bank arrived full of decorative filler, fake placeholder SVGs, leaked hints, generic solutions, and — most dangerously — wrong answer keys. Each pass added a detector. *Why it grew so large:* early QA had treated `correct_answer` and figures as untouchable and only checked formatting; once we started *math-checking* keys and *classifying* figures, a long tail of defects surfaced. *Lesson baked in:* nothing is sacred; validate the thing you assumed was fine.

**The adaptive layer (clustering → skill ladder).** Raw banks are mostly near-duplicate variants. To adapt, we clustered them into concepts (`skill_id`) and built a ladder: right on a concept → next concept; wrong → drill its easier variants; remember position so re-login never regresses. *Why leader-clustering at 0.70:* the naive union-find chained unrelated content into giant blobs. *Lesson baked in:* the concept structure is what makes adaptivity meaningful — tag it well.

**Economy + contest + league.** Built as one shared ledger (coins/gems/XP/streak) feeding practice, quiz, contest, and store, with "no disjoint" (every surface agrees) and "money never buys rank." *Why one ledger:* earlier there were two gem meters and disjoint states; users saw contradictions. *Lesson baked in:* one server-authoritative economy, period.

**Store + reader + library.** A store with purchase→download→read-offline, and a reader that went through KiwiReader → EPUB → an owned HTML WebView (see `02` §5). *Why the churn:* each engine imposed limits we couldn't fix from outside. *Lesson baked in:* for a study reader, own the rendering.

**Vedantu content integration (and its reversal).** ~140 source PDFs and 6 sheets became faithful-render books + a verified daily-quiz pool. The image-based *practice questions* were then pulled (looked unfinished as standalone items) and kept only in books. *Why the two-surface split:* a faithful image is a great *book page* and a weak *practice item*. *Lesson baked in:* match content format to the surface.

**Authored books (L2, L3).** When faithful-render wasn't enough — to *bridge* the sharp level-to-level jump — original teaching books were written from scratch, with exact vector figures and brute-force-verified math, then critically audited and corrected. *Why author at all:* rendered past-papers teach *practice*, not *concepts*; the jump between levels needed real teaching. *Lesson baked in:* practice content and teaching content are different products.

**The mini-app vision.** The realization that none of the engine/economy/reader/store is math-specific led to the fork strategy: one platform, many exam skins (the `HANDOVER_MINIAPP/` pack). *Why now:* the platform had matured enough that the subject was clearly isolated to the content layer. *Lesson baked in:* build the spine subject-blind from the start and the second product is cheap.

---

## 4. The decisions that, in hindsight, mattered most

1. **Math-checking answer keys** (not treating them as locked) — caught the trust-killing defect.
2. **Faithful-image over re-typed text** for notation-heavy sources — sidestepped a whole class of silent corruption.
3. **One shared economy ledger** — killed the disjoint-state confusion.
4. **Owning the reader** — ended the engine-limit churn.
5. **Concept clustering** — turned a flat bank into an adaptive ladder.
6. **Separating ladder from syllabus, and practice from teaching** — gave each kind of content the right home.
7. **Treating the subject as a pluggable content layer** — made the platform forkable.

---

## 5. What to carry forward (the method, in one paragraph)

Research first and write the plan. Source content, never invent it. Transform faithfully; validate every computable key; tag concepts. Make every defect a detector and drive it to zero. Batch, QA, keep green, deploy. Fix one field at a time, backed up. Fan out big jobs to subagents that verify their own work. Log every pass. Be slow and certain — a missing item costs nothing, a wrong one costs a user. Do that, and the system stays trustworthy as it grows and forks.
