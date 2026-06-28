# ACAD OS — The Story

*A single linear read of the whole journey: how it was approached, what changed, the mistakes, the learnings, and where it's going. This is the orientation doc — read it first, then dive into the manual (`00`–`06`) and the scripts.*

---

## The starting point

It began as **Kiwimath** — an adaptive math app for K-6 kids, built on Flutter + FastAPI + Firebase. The founder, Anand Prakash, is an Olympiad-cleared maths expert at Vedantu. The early app already had a lot: tens of thousands of questions, a clan/social layer, a daily-puzzle system, a parent dashboard, an IRT-based adaptive engine. But it had grown in layers, and the content — the thing that actually matters — was uneven. The real work of the cowork spaces was to turn a sprawling app into a **trustworthy academic operating system**.

The thesis that emerged, and that everything now rests on: **this is not a math app. It's a content-agnostic learning platform that happens to be full of math.** The engine, economy, contest, library, and store don't know the subject — they read difficulty, concept tags, and right/wrong. Only the content layer knows it's math. That realization is what makes the platform forkable into JEE/NEET apps later.

---

## Act I — Putting the house in order

The first move was a **reorganization**. Content was scattered across overlapping banks (`content-v2`, `content-v4`) with grade-based tags. We consolidated everything served into one place — `content-live/` — and made a key structural decision: **separate the olympiad ladder from the school curriculum.** The olympiad section was re-tagged from grades into **levels L1–L8** (L1 = Grade 1-2 up to L8 = IMO), each with a pillar/strand and a friendly topic name. The school curriculum stayed grade-tagged, by board. *Why it mattered:* a competition progression and a school syllabus are different things for different users; conflating them mis-placed questions and muddled the UI.

With the structure clean, we could finally see the content clearly — and it needed work.

---

## Act II — The content QA campaign (the heart of the trust)

This was the longest and most important arc. The bank was full of defects, and we went after them class by class, each time building a **re-runnable detector** so the defect could never silently return. Over many passes we found and fixed: decorative story-filler glued before the real question (~6,900 stems), fake placeholder grey-box "figures" (~2,461), answer-leaking hints (thousands), generic boilerplate solutions that never used the question's actual numbers (~3,340), mismatched template images (a clock drawn on a rotation question), and subtler ones — figures that *revealed* the answer (a Venn diagram showing the derived regions; a triangle labelling its own hypotenuse), unanswerable questions that referenced a picture that wasn't shown, and pattern questions whose visual had been stripped away.

The most dangerous discovery was **wrong answer keys.** A live bug — *"Raju has 7 watermelons, gets 5 more,"* keyed to 2 instead of 12 — revealed that prior QA had treated `correct_answer` as sacred and never math-checked it. That is the worst possible defect: the child does the math right and is told they're wrong. The fix was a philosophy, not a patch: **every computable answer-key family gets its own validator** that recomputes and flags mismatches. We built validators for single-step arithmetic, percentages, and ratios — catching keys that pointed at distractors — and we know which families still need one (fractions, multi-step, combinatorics, probability).

By the end, whole levels (L1, L2) reached **zero defects across all fourteen detectors (A–N)**. The detectors live in `content_qa_scan.py`; the full catalogue is in `04` and the canonical `MISTAKES_REPOSITORY.md`. The meta-lesson of this whole act: **detect, don't eyeball; nothing is sacred; fix one field at a time, backed up and diffed.**

---

## Act III — Making it adaptive

A clean bank is still just a pile of questions. To *adapt*, we needed to know which questions are the *same idea*. We built **concept clustering**: each question's stem is reduced to a signature (numbers blanked, names stripped, operators normalized) and grouped with its near-twins. ~30,000 questions collapsed into ~8,200 concepts. (An early attempt chained unrelated questions into giant blobs; the fix was leader-clustering at a Jaccard threshold.)

On top of the concepts we built the **adaptive skill-ladder engine**: get a concept right and you advance to the next; get it wrong and you drill its easier variants until one clicks; your position is remembered so re-login never sends you backward. This is the heart of the learning product, and — crucially — it's completely subject-blind.

---

## Act IV — The game layer

Learning needs a reason to come back. We designed and built a **one shared economy** (coins, gems, XP, streak) feeding every surface, with two iron rules: *no disjoint* (wallet, progress, and profile always agree, because there's one server ledger) and *money never buys rank*. On top of it: a **daily contest** (a timed, scored, one-attempt set with a leaderboard) and a **weekly league** (cohorts of ~30, Bronze→Legendary tiers, promotion and relegation). Independent reviews of the money code found and fixed real bugs — an IDOR, double-award/double-debit replays, a currency that wasn't pinned on spend — and flagged the one thing still to do before real money: make the coin debit a proper transaction.

---

## Act V — The Library

Then came **books**. The insight: a book is just one self-contained HTML file plus a catalog row, read in a generic in-app reader — so the marginal book is cheap. Three kinds emerged, each matched to a source and a goal:

- **Faithful-render** books, where a source PDF's pages are rendered to images and wrapped in an interactive shell (contents, tap-to-reveal video and worked solutions). Used for the upper-tier pillar books (IOQM/RMO/INMO) and grade workbooks. *Why render and not re-type:* the math notation and figures survive perfectly, sidestepping the text-mangling that corrupts extracted PDFs.
- **Authored** books — two original teaching books (L2 *Kiwi's Grand Math Adventure*, L3 *Kiwi's Math Expedition*) written from scratch like a maths expert would, Socratic and Bloom's-laddered, with exact vector figures, Kangaroo-style problems, and Vedic-maths tricks — built to **bridge the sharp jump** between levels that rendered past-papers can't teach. Chapters were fanned out to subagents that each brute-force-verified every answer in Python.
- **Interactive** books (Number Sense, K-2) where the learner answers *inside* the book — tap or type-and-check — the book's own JavaScript running in the reader's WebView.

The reader itself was a saga: we adopted a third-party reader, then EPUB/epub.js, and abandoned both because their engines imposed limits we couldn't fix (pages that wouldn't flip, flicker). We settled on **a WebView we fully own**, rendering the book's self-contained HTML. The lesson: for a *study* reader, control beats convenience.

---

## Act VI — The Vedantu content, and an instructive reversal

Vedantu's academic library — ~140 assignment PDFs and several sheets, the competition curriculum from Grade 3 up to ISI/CMI — was a goldmine. We built an ingestion pipeline (faithful image crops + brute-force-validated keys + range grading for decimals) and a **"verified" pool** so the daily quiz auto-upgrades to trusted content. Over a thousand questions were ingested.

Then the founder tested them on-device and called it: the image-based "solve the problem shown" questions looked **unfinished** anywhere except inside a book. So we **pulled all of them from the served bank** — practice, quiz, contest — and kept them only in the Library, with a backlog to convert them slowly to clean typed HTML, *only* where we're 100% certain. This reversal is one of the most useful learnings in the whole project: **a faithful image is a great book page and a weak standalone practice question — match the content format to the surface.**

---

## Act VII — The realization that became ACAD OS

By now the pattern was obvious. The content QA discipline, the adaptive engine, the economy, the contest, the library, the reader, the store — almost none of it was *math*. The subject lived entirely in the content layer. What we'd actually built was an **academic operating system**: a spine you fill with sourced, validated content and re-skin per audience. That's what makes the next chapter — **mini-apps for JEE, NEET, and other exams** — a content-and-branding project rather than a new build. (The fork recipe is the `HANDOVER_MINIAPP/` pack.)

And it surfaced the single most important rule for that future: the math app could often let a *computer* check an answer; Physics, Chemistry, and Biology cannot be. So the governing law for every new instance is **the AI builds the machine; authoritative sources and human experts supply the content** — and Vedantu's faculty are exactly the firewall that makes that safe.

---

## Where it stands

The core systems are green — the smoke suites pass, L1 and L2 are defect-free, the economy and contest and store and reader all work. The served bank is ~19.6k olympiad + ~10.3k curriculum questions, all concept-clustered. The Library has faithful-render books, two authored teaching books, and an interactive workbook in progress. The platform is proven and — by design — forkable.

The honest backlog: validate the remaining answer-key families (fractions, multi-step, combinatorics, probability); run the A–N scanner loop through L3–L7 and the curriculum; deep-audit the upper-tier solutions; finish the Number Sense book; convert the image-question backlog to typed questions; and make the coin spend a real transaction before charging real money.

---

## The through-line

If there's one sentence that carries the whole project, it's this: **be slow and certain with content, make every mistake into a detector, keep one field sacred at a time, and keep the engine blind to the subject.** Do that, and a trustworthy K-6 math app becomes an academic operating system that can grow into anything. That's the ACAD OS.

*Now read `00_START_HERE.md` for the manual map, and the layer file you need.*
