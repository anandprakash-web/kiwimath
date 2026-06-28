# 04 · Content Guardrails — how to not hallucinate

Short, but the most important file in the pack. This is the difference between a trustworthy exam app and a dangerous one.

---

## The core danger

Kiwimath is a **math** app. For a lot of its content, an answer can be **checked by a computer** — re-run the arithmetic, confirm the key. That safety net let the AI catch and fix wrong answer keys automatically.

**That safety net does not exist for JEE/NEET.** Physics, Chemistry, and Biology answers cannot be recomputed by a language model reliably. If you ask the AI:
- "Write 50 NEET biology questions," or
- "Solve this and tell me the right option," or
- "Double-check this chemistry answer key,"

…it will produce confident, fluent, **wrong** output. Not always — but often enough that you can never trust it, and you can't tell the good from the bad by reading it. In exam prep, **one wrong answer key destroys user trust** — a student marks themselves wrong, loses confidence, and leaves.

---

## The one rule

> **The AI builds the machine. Authoritative sources supply the content. The AI never authors, solves, or re-keys a subject question.**

Everything below is just this rule, made concrete.

---

## What "authoritative source" means

In priority order:
1. **Official past papers (PYQs)** with official answer keys — the gold standard. Provenance is the exam board itself.
2. **Licensed question banks** you have the rights to use, with their published keys and solutions.
3. **Subject-expert-authored material** — written and answer-keyed by a qualified human (e.g. a Vedantu faculty member), reviewed before it ships.

Every question that reaches a student should trace back to one of these. Store that provenance in the record's `source` field — it's also what the "verified" daily-quiz pool keys off.

---

## What the AI is allowed to do with content

✅ **Allowed (mechanical plumbing):**
- Convert a source item into the question-record format (copy stem, options, key, solution **verbatim**).
- Extract text/figures from a source PDF and keep them faithfully.
- Tag subject/chapter/concept; run the concept clusterer.
- Format math/notation for display (without changing the meaning).
- Mechanical QA: is every question answered? are options clean and non-duplicated? is the answer hidden before submit? are there exact-duplicate questions? do figures render?
- Maintain a **skip log** of anything it couldn't ingest cleanly.

❌ **Forbidden (anything that invents or judges content):**
- Writing new questions, options, hints, or solutions from scratch.
- **Solving** a question to produce or "confirm" an answer key.
- "Improving" or "correcting" a source's answer key.
- Judging how **hard** a question is (difficulty must come from the source/expert, not the model).
- Filling a gap ("this chapter is thin, generate a few more") — a thin chapter is a sourcing task, not a generation task.

When the source is unreadable or ambiguous: **skip and log for a human.** Never guess.

---

## Why "skip and log" beats "best effort"

A missing question costs you nothing — you add it later from a better scan. A **wrong** question costs you a student. So the asymmetry is huge: always prefer the gap. Build the pipeline so skipping is the easy, default path and ingesting requires a clean read.

---

## Difficulty without hallucination

The engine needs a `difficulty` number to order the ladder. Get it from signals that already exist in the source:
- PYQ **year + section** (e.g. a section known to be harder).
- The bank's **own** stated level/tag.
- An expert's tag.

Then **let real usage correct it.** The platform logs every right/wrong; after a chapter has been practised, recompute difficulty from actual success rates. That data is true; the model's guess is not. So: seed from source, refine from data, never from the model's opinion.

---

## A tiny inspection checklist (use on every batch)

Before a content batch ships, a human (or a mechanical script) confirms:
- [ ] Every question has an answer key, and it came from the source (not generated).
- [ ] `source` provenance is filled in.
- [ ] No exact-duplicate questions.
- [ ] Options are clean; nothing reveals the answer; the answer is not sent to the client pre-submit.
- [ ] Figures render and match their question.
- [ ] The skip log was reviewed.
- [ ] Spot-check N random items against the original source by eye.

None of these checks require the AI to *know the subject* — they're all mechanical or human-eyeball. That's the point.

---

## One sentence to paste at the top of any content task

> "Treat every question and answer key as read-only truth from the attached source. Your job is to format and plumb it, not to solve, author, re-key, or judge difficulty. If anything is unclear, skip it and list it — never guess."

If the next cowork internalizes only that sentence, the apps will be safe.
