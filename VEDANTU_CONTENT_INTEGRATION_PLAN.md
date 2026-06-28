# Kiwimath × Vedantu Content Library — Integration Plan
*Prepared for Anand Prakash · 2026-06-22 · "go through this content, understand it, then present the plan with all the working so far"*

---

## 0. TL;DR (the one-paragraph version)

Your team's six Google Sheets are a **professionally-built, competition-sourced math curriculum from Grade 3 all the way to ISI/CMI/Putnam** — ~205 topic/session assignment PDFs (each with problems + answer key + **full worked solutions** + competition provenance), ~60 reference textbooks, ~250 video lessons, and online DPP tests. I verified I can extract the assignment PDFs cleanly through the Drive connector. This content slots **almost one-to-one** onto the taxonomy we already built (Levels + NT/ALG/GEO/COM pillars), and it fills the exact gap that's thinnest today: **L4–L7 currently have only 800/900/800/550 questions each** — these assignments can multiply that several times over, *with* solutions and video links we don't currently have. My recommendation: ingest **L5/L6/L7 topic assignments first** (highest ROI, pillar-aligned, fully extractable), then L3/L4 courses, then turn the assignments + reference notes into interactive **books**. One hard caveat to decide up front: the **third-party reference textbooks are copyrighted** and can't go in a paid store — your team's *own* assignments/notes/videos can.

---

## 1. What this content actually is

A single index sheet ("Grade wise content for Anand Sir") points to **six libraries**, each a Google Sheet your acad team maintains:

| # | Sheet (their naming) | Their grade band | Structure | What's inside |
|---|---|---|---|---|
| 1 | **Level 3** | Grade 3–4 | 40 dated class sessions | Topic + DPP (online test) + **Assignment PDF** + 10-test exam schedule w/ syllabus |
| 2 | **Level 4** | Grade 5–6 | 40 dated class sessions ("OMM Level 4") | same as above |
| 3 | **Level 5** | Grade 7–8 | **Topic bank** by pillar | 38 topic assignments (NT·ALG·Arith·GEO·Comb) + 6 reference books |
| 4 | **Level 6** | Grade 9–10 (RMO) | **Topic bank** by pillar | ~40 topic assignments (+Trig) + 10 reference books |
| 5 | **Level 7** | Grade 8–12 (IOQM+RMO) | **Topic bank** by pillar | 60 topic assignments (deepest) + 15 reference books |
| 6 | **ISI/CMI + Full Math Mastery** | College entrance / JEE-adv / Putnam | Chapter bank | 26 chapters × (VDPP + Tatva notes + ISI PYQ + extra) + 34 books + ~250 video lessons |

### Three distinct asset classes
1. **Structured courses (L3, L4)** — a *sequenced teaching path*: 40 sessions each, dated, with per-session practice (DPP) + take-home assignment + a built-in test calendar and syllabus split. This is a ready-made **learning journey**, not just a question pile.
2. **Topic assignment banks (L5, L6, L7)** — organized exactly by **Number Theory / Algebra / Geometry / Combinatorics / Trig** (i.e. *our pillars*), one assignment per concept, escalating from IOQM → RMO → INMO depth.
3. **Reference + media layer (ISI/CMI sheet, and the book lists on L5–L7)** — the canonical olympiad library (Evan Chen, Burton, Xu Jiagu, Andreescu's 10x series, Mathematical Circles, Engel, Cengage…), theory notes ("Tatva"), ISI previous-year papers, and a large **YouTube video-lesson library** indexed by chapter.

### Why this content is high quality (what I saw inside)
I opened a representative assignment ("Knowing about numbers", L3 session 1). It contains:
- 15 problems in graded sections (A: warm-up MCQ, B: harder reasoning),
- a clean **answer key**,
- **full worked solutions** with the actual arithmetic,
- **competition provenance tags** — `(iOM'16)`, `(NSTSE'14)` — these are real, vetted contest problems, not filler.

That is exactly the structure our ingestion pipeline wants. It is materially **richer than what we generate today** because it ships with human-written solutions and source attribution.

> **Bonus finding:** two problems in that single PDF ("Arrange P, Q, R, S from smallest to greatest" and "add the odd numbers from the boxes below") are the *original source* of two questions I had to flag as **unanswerable** during yesterday's L2 QA — the source still has the data (P=422, Q=510… and the box figure) that got dropped when they were first ingested. **So this library doubles as a recovery key for previously-broken questions.**

---

## 2. The working we've already done (what this plugs into)

We aren't starting from zero — we have a full spine for this content to snap onto:

**Taxonomy (the skeleton).** Every question carries a **Level (L1–L8)** + an internal **Pillar (NT/ALG/GEO/COM)** + a friendly Topic name. Levels: L1=G1/2, L2=G3/4, L3=G5/6, L4=G7/8, L5=IOQM, L6=RMO, L7=INMO, L8=IMO. The new content's pillars (**NT/ALG/GEO/COM/Trig**) are *the same vocabulary* — no translation layer needed for L5–L7.

**The banks (the muscle).** ~**19,615 olympiad** + **10,336 curriculum** questions, served live via the `/v3` API, each with hints, IRT difficulty, and inline visuals. Crucially, the upper tiers are **thin**: L4 = 800, L5 = 900, L6 = 800, L7 = 550, L8 = 0. *This is the gap the new content fills.*

**Quality machinery (the immune system).** A 14-detector QA scanner (A–N), a per-level "find every mistake type, fix, repeat until zero" loop (L1 and L2 are now clean), an arithmetic answer-key validator, and an idempotent **skill-cluster** tagger that groups variants into ~8,200 concepts and orders them by difficulty.

**Adaptive engine.** A skill-ladder engine that walks a student concept-by-concept (right → next skill, wrong → drip variants), with durable per-user position. New questions tagged into the existing topics automatically join this ladder.

**Books system (the library).** A fully-owned in-app reader, a store with purchase→download→offline, and a working pipeline that already turned the **IOQM 4-pillar PDFs into interactive books** and built the **Number Sense** workbook. This is the exact mechanism we'd reuse for these assignments and reference notes.

**Engagement.** Daily contest + leagues + economy (coins/gems/XP) — the reason richer content compounds: more good questions → more contests, more book unlocks, more reasons to return.

---

## 3. The mapping — content → our taxonomy

### ⚠️ Decision #1: the level numbers don't line up — map by GRADE
Their sheet "Level N" is named on the **Vedantu OMM convention**, which is offset from our internal level numbers. If we map number-to-number we'll mis-file everything. Map by **grade band**:

| Their sheet | Their grade band | → **Kiwimath level** | Pillars present | Current bank size (the gap) |
|---|---|---|---|---|
| Level 3 | G3–4 | **L2** | NT, ALG, GEO, COM, **Logic/Puzzles** | L2 = 5,264 (already healthy) |
| Level 4 | G5–6 | **L3** | NT, ALG, GEO, COM, Logic | L3 = 2,823 |
| Level 5 | G7–8 | **L4** | NT, ALG, Arith, GEO, COM | **L4 = 800** ⟵ thin |
| Level 6 | G9–10 (RMO) | **L5 / L6** | +Trig | **L5 = 900, L6 = 800** ⟵ thin |
| Level 7 | G8–12 (IOQM+RMO) | **L6 / L7** | full olympiad | **L7 = 550** ⟵ thinnest |
| ISI/CMI | college entrance | **L8+ (new "Full Mastery" track)** | calculus, conics, linear algebra… | does not exist yet |

> Note the **L3/L4 sheets are richest in Logic/Puzzles content** (coding-decoding, blood relations, clocks, paper-folding, mirror images, magic squares) — which feeds our **Logic & Puzzles** strand and the **Clan daily-puzzle** system, not just the four pillars.

> The **ISI/CMI tier is a different animal** — it's JEE-Advanced/college calculus (integration, differential equations, matrices, conics). It doesn't fit K-10 olympiad. It's an opportunity to open a **new top tier ("Full Math Mastery")** later, but I'd treat it as out-of-scope for the core app for now.

---

## 4. The plan — two tracks off one ingestion

Everything flows from **one extraction step** (pull each assignment PDF's problems + key + solutions via the Drive connector), then forks into two products:

### Track A — Regular adaptive content (fill the bank)
Turn the ~205 assignment PDFs into tagged questions in the L3–L7 banks.

- **Per problem we capture:** stem, choices, correct answer, **worked solution** (we mostly *lack* these today), **source tag** (iOM/NSTSE/etc.), and a link to the **video solution** where one exists (the ISI/L7 video library).
- **Reuse the existing pipeline** end-to-end: the IOQM importer's shape → `content-live/olympiad/L{n}/` → skill-cluster tagger → QA scanner (A–N) → smoke/pre_deploy → `./deploy.sh`. No new infrastructure.
- **Two byproducts for free:**
  1. **Recover broken questions** — where a flagged "unanswerable" question traces back to one of these PDFs, the source restores its missing figure/data.
  2. **Solutions + video** — upgrades the *whole* upper-tier experience (today L4–L7 have terse solutions; these PDFs and the video index fix that).

### Track B — Books (the library)
Turn the same material into interactive books, reusing the IOQM-book pipeline:
- **Per-pillar / per-level practice books** (e.g. "L6 Number Theory", "L7 Combinatorics") from the topic assignments — faithful problem pages + tap-to-reveal solution + the video button, exactly like the IOQM books already shipping.
- **Theory books** from the ISI **"Tatva"** notes (clean, your team's own).
- **The reference textbook library** → store catalog — *with the IP caveat in §6*.

---

## 5. Suggested sequencing (phased, highest-ROI first)

| Phase | Scope | Why this order | Output |
|---|---|---|---|
| **0 — Prove it** | Ingest **1 topic PDF end-to-end** (e.g. L6 "GCD & LCM") → tagged, QA-clean, on the ladder | De-risks the pipeline on the new format before bulk | 1 topic live + a written "ingestion recipe" |
| **1 — Fill the thin tiers** | **L5/L6/L7 topic assignments** (~140 PDFs) | Pillar-aligned, fully extractable w/ solutions, fixes the 800/900/800/550 gap — biggest impact per hour | L4–L7 banks multiplied; solutions + source tags added |
| **2 — The courses** | **L3/L4 sessions** (~70 PDFs) → into L2/L3; route Logic topics to the Puzzles strand | Adds a *sequenced journey* + recovers broken L2/L3 logic questions | L2/L3 deepened; daily-puzzle feedstock |
| **3 — Books** | Per-pillar practice books (L5–L7) + Tatva theory books | Reuses the shipping IOQM-book pipeline | New library titles, earn-or-buy |
| **4 — New top tier (optional)** | ISI/CMI "Full Math Mastery" + the ~250-video library | Expands TAM upward (Grade 11–12 / college) | A new L8+ track |

Each phase ends green on the **same gates we already enforce**: scanner A–N = 0 for touched levels, smoke 17/17, pre_deploy pass, then `./deploy.sh`.

---

## 6. Risks & decisions I need from you

1. **Level-number reconciliation (Decision #1 above).** Confirm we map **by grade**, so their "Level 3" lands in our **L2**, etc. (Everything downstream depends on this.)
2. **IP / licensing — the big one.** The **reference textbooks** (Evan Chen, Burton, Cengage/Tewani, Andreescu, Xu Jiagu, Mathematical Circles, the "Tomato" book, Putnam compilations…) are **third-party copyrighted works**. They're perfectly fine as an internal *teacher reference*, but we **cannot redistribute them in a paid (or free public) in-app store** — that's a legal exposure. Your team's **own** material — the assignment PDFs, DPPs, Tatva notes, and your own videos — is yours to use freely. My recommendation: build the store on **our own content**, and treat third-party books as "recommended reading" links at most.
3. **Competition-question provenance.** The problems are tagged iOM/NSTSE/IOM/Kangaroo etc. Reusing past-paper problems for practice is industry-standard, but worth a conscious nod — we'll **keep the source attribution** on each item (good for trust, and the right thing).
4. **DPP online tests.** The DPP links are Vedantu's hosted test pages (not Drive files), so they're not as cleanly extractable as the PDFs — and they largely **duplicate** the assignment PDFs. Recommendation: **ignore DPPs for ingestion**, treat the assignment PDFs as the source of truth. (If you want the DPPs specifically, that's a separate Vedantu-export conversation.)
5. **Scope / effort.** ~205 PDFs is real work, but the pipeline is built and the format is consistent. Phasing keeps each drop shippable. I'd rather do L5–L7 *excellently* than all six tiers shallowly.
6. **Answer-key trust.** These ship with keys + solutions, but (as we learned the hard way) keys can still be wrong. Every ingested batch goes through the **arithmetic validator + A–N scanner** before it's served — no raw trust.

---

## 7. My expert recommendation

**Start with Phase 0 → Phase 1 (L5/L6/L7 assignments).** It is the highest-leverage move you can make on content right now: it fills the precise tiers that are thin today, it's pillar-aligned so it needs no re-taxonomy, it's fully extractable *with* human solutions and video links (things we can't auto-generate well), and it doubles as a repair kit for upper-tier questions. The L3/L4 courses come next because they also recover broken L2/L3 logic items and give us a sequenced journey. Books are a fast follow on the *same* extraction. The reference-textbook store and the ISI/CMI tier are genuine assets but gated on the IP decision and a TAM call — park them.

The crown jewel here is **your team's own assignment library with worked solutions and competition provenance.** That's a multi-year moat most ed-tech apps can't buy. Let's get it into the engine.

---

### Appendix — source index (the six libraries)
| Tier | Drive Sheet ID |
|---|---|
| Level 3 (G3–4) | `18-U4QzBBiJQ_mJoCrmXjjTXDyOAi7Y_jqXgGx8uN324` |
| Level 4 (G5–6) | `1Q4OwCiwFBw_WI_a9pJK59JcRnHtKOWUyIyGLXPzZ0C8` |
| Level 5 (G7–8) | `1HNlMTKq42siDXZ6lfW0pd87a-c5bK4Nz5ogls-2Cy_0` |
| Level 6 (G9–10) | `1PxnB7ppPX-mMZKFuH0Vcvk8qrkJDTzp-8-Io5VFKR4E` |
| Level 7 (IOQM/RMO) | `1FOVEUBO9mkUnFVOPcOnrxbGvaIc_Rp3rD28vtZiVTHk` |
| ISI/CMI + Full Mastery | `1VFabLV8p7y9IKQpLR_1zrHmF-Dw9bDW4mVsZWZOBNdM` |
