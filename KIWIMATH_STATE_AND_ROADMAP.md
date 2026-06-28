# Kiwimath — State of the App & Expert Roadmap
*Prepared for Anand Prakash · 2026-06-22*

---

## Part 1 — What Kiwimath is today

**One line:** an adaptive math-olympiad app for roughly Grade 6–10 (olympiad-leaning), with a younger Grade 1–5 base, built on Flutter + FastAPI + Firebase, whose real moat is a large, human-curated, competition-sourced content library wrapped in an adaptive engine and a game economy.

### The content engine (the heart)
- **Taxonomy:** Levels **L1–L8** (L1 = Gr 1–2 … L5 = IOQM, L6 = RMO, L7 = INMO, L8 = IMO) × pillars **Number Theory / Algebra / Geometry / Combinatorics** + a **Logic & Puzzles** strand. One clean vocabulary the whole app speaks.
- **Banks:** ~**19,640 olympiad** questions (L1 8,478 · L2 5,264 · L3 2,823 · L4 800 · L5 900 · L6 827 · L7 550) + **10,336 curriculum** questions across 5 boards (Cambridge, NCERT, Singapore, ICSE, US Common Core), Grades 1–6. ~**30k served** through one `/v3` API.
- **Quality machinery:** a 14-detector QA scanner (A–N), a per-level "find every defect type → fix → repeat to zero" loop (**L1 and L2 are now clean**), an arithmetic answer-key validator, and a skill-clustering tagger (~**8,200 concepts**) that orders variants by difficulty.
- **Adaptive engine:** a skill-ladder (right → next skill, wrong → drip easier variants) with durable per-user position that survives re-login.

### The backend
- FastAPI on **Cloud Run (asia-south1)**, ~280 routes, **Firestore** persistence with in-memory fallback.
- Services: level/curriculum content store, adaptive skill engine, **daily contest + weekly league**, **economy** (coins/gems/XP/streak on one ledger — "no disjoint"), **store/entitlements**, **clan**, growth/proficiency/benchmark.

### The app (Flutter)
- Current direction is the **/v3** redesign: **Olympiad** (levels) · **School** (grades) · **Library** (books) · **Progress** · **Profile**, plus a **Compete** surface.
- Working surfaces: adaptive practice, Daily Contest + League, Clan + daily puzzle, Growth ("mountain journey," 200–800 scale scores, K/A/R competency), PIN-gated Parent dashboard, and a fully-owned **Library/Reader/Store** (your own HTML/EPUB reader; IOQM 4-pillar books, a Number Sense workbook, Euclid's Garden).

### The premium-content integration (in progress, this week)
- Your academic team's **competition-sourced curriculum (Gr 3 → ISI/CMI/Putnam)** — ~205 assignment PDFs (problems + worked solutions + video links + provenance), ~60 reference books, ~250 videos.
- **Decided architecture:** premium content gets its **own two surfaces** — **per-pillar-per-level interactive books** in the Library, and a **"Verified" pool** that headlines the Daily Quiz — so it never gets diluted in the machine-generated practice pool.
- **Done so far:** 2 topics ingested + every answer brute-force-validated; the Verified daily-quiz pool is wired and live; the downloader for the rest is in your hands now.

---

## Part 2 — Honest assessment (as your engineer)

**Strengths — genuinely rare:**
- A **content moat** most ed-tech can't buy: a real olympiad curriculum with worked solutions, plus an engine that adapts through it.
- **Engineering rigor** unusual for this stage: a reusable QA harness, answer-key validation, idempotent clustering, "one ledger" economy discipline.
- A **built-in beta audience** — the Vedantu olympiad students whose content you're ingesting.

**Risks — be honest about these:**
1. **Breadth over shipped depth.** You've built practice, contests, leagues, clans, growth, benchmark, store, reader, economy… but a lot of it is "built, needs APK rebuild + on-device QA." Surface is outrunning what's validated in real hands.
2. **Only L1–L2 are QA-clean.** L3–L7 — *the olympiad core you're positioning on* — still carry the defect types you've been killing.
3. **Money isn't safe yet.** The economy debit isn't a Firestore transaction and IAP is stubbed — fine today (virtual currency), a blocker before real revenue.
4. **No evidence of a live user/feedback loop.** Lots of features, but the roadmap below assumes you don't yet have instrumentation telling you what users actually do.
5. **Focus risk.** One founder + AI can build enormous surface area fast — which is exactly the trap. The next win is *convergence*, not more features.

---

## Part 3 — The roadmap I'd follow (opinionated, sequenced)

The through-line: **converge to one excellent, trustworthy loop → put it in real students' hands → instrument → then double down on the content moat → then monetize safely → then scale.** Resist adding surface area until a core loop is loved and measured.

### Phase 1 — Ship a rock-solid core to real students (next ~2–4 weeks)
*Goal: one delightful, trustworthy loop running flawlessly on real Android devices, in front of real olympiad students.*
- **Pick the hero loop:** open app → adaptive practice **or** the Daily Contest at **L3–L6**, with the **Verified** content leading → see progress. Make that flawless; everything else is secondary.
- **Rebuild the APK** with all pending reader/UI/Verified changes and do a real **on-device QA pass** (the pending build tasks). Deploy the backend (Verified pool + content fixes).
- **Hide, don't ship, the half-polished surfaces.** A mediocre Clan or Store tab costs more trust than it earns. Show only what's excellent.
- **Instrument before launch:** crash reporting (Crashlytics/Sentry) + product analytics (which screens, which drop-offs, D1/D7 retention, questions-per-session). You cannot prioritize without this.
- **Beta with the Vedantu students** — your unfair advantage. 20–50 real users, watch sessions, collect the bug/▼feedback that the QA harness can't.

**Done = a student opens the app daily, practices/competes without a crash, and you can see it in analytics.**

### Phase 2 — Double down on the content moat (~1–2 months)
*Goal: the premium content becomes the reason to choose Kiwimath.*
- Finish the **Vedantu integration**: build the per-pillar-per-level **books** (from the folder you're downloading) and keep growing the **Verified quiz** pool. Faithful render = notation + figures intact.
- **Finish the content QA loop for L3–L7** (the core tiers) the same way you cleaned L1–L2. This is the moat; get it to zero defects.
- Wire the **"Verified" badge + video-solution** UI so students *feel* the premium quality.

**Done = the olympiad tiers are defect-clean, and a student can read a real book and take a verified daily quiz on the same topic.**

### Phase 3 — Make it safe to charge + make it sticky (~1–2 months)
*Goal: revenue-ready and retentive — but only the loops that measurably retain.*
- **Harden the economy to a Firestore transaction** (the one true must-do before real money), then wire **IAP**.
- Decide the model: I'd test **Verified content as the premium tier** (free machine-practice volume; paid premium books + verified contests) — it maps cleanly to what you've built.
- Turn on retention loops **you've measured** — Daily Contest, Weekly League, streaks, Clan — and cut the ones that don't move D7/D30. Reader security debt (encrypt-at-rest, purge-on-signout) lands here too.

**Done = a student can pay, the ledger is transaction-safe, and at least one retention loop demonstrably lifts return rate.**

### Phase 4 — Scale & operate (ongoing)
- **CI/CD + automated test gates** (you already have smoke/scanner/pre-deploy — make them block every deploy), monitoring/alerting, and an **iOS build**.
- Growth experiments off the analytics base; content pipeline productized (the ingestion recipe you now have).

### Cross-cutting principles (the expert's nags)
- **Instrument every decision.** Ship analytics before features.
- **Quality is the moat** — content correctness, delight, and parent trust. Protect it ruthlessly (you already do on content; extend it to UX polish).
- **Converge before you expand.** Every new feature competes with *finishing* the last one.
- **Use the Vedantu students** as your continuous beta — most startups would kill for that loop.
- **Money code is different code** — transactions, idempotency, audits, before a single rupee.

---

## Part 4 — The next two weeks, concretely
1. Finish the content download (running now) → I build the first **per-pillar-per-level books**.
2. I do an **L3 QA loop** (next core tier) while books build.
3. You/we **rebuild the APK** + on-device QA of the hero loop; deploy backend.
4. Add **Crashlytics + analytics**; push a build to **a handful of Vedantu students**.
5. Watch what they actually do — and let *that* set the Phase-2 priorities.

> Open questions that would sharpen this: Is the app live with any users today? Is there a revenue target/timeline? Android-only or iOS too? Answers move the sequencing, not the principles.
