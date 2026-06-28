# 01 · The System Map — Kiwimath as a content-agnostic spine

This is the mental model. Read it once and the rest of the pack clicks into place. There is **no subject content here on purpose** — the whole point is that the platform doesn't know or care what subject it's teaching.

---

## The core idea: a question is just a record

Everything in the platform flows from one humble object — a **question record**. It looks the same whether it holds a fraction problem or an organic-chemistry problem:

```
question {
  id            unique string (e.g. KM-L5-NT-0042 → could be NEET-BIO-0042)
  stem          the question text (may contain an image)
  choices       options for multiple-choice, or empty for typed answers
  answer        the correct option index, or the correct typed value
  hint          a nudge (does NOT give the answer away)
  solution      the full worked explanation, revealed after answering
  difficulty    a number used to order easy → hard
  tags          subject / chapter / concept labels
  skill_id      which "concept cluster" this belongs to (drives adaptivity)
  source        where it came from (provenance — critical for trust)
  visual        an optional figure (inline SVG, or an embedded image)
}
```

That's it. **Swap the content of these fields and you've changed subjects.** The engine, the quiz, the contest, the economy — none of them read the *meaning* of a question. They read its `difficulty`, its `skill_id`, its `tags`, and whether the learner got it right. A right/wrong signal on a biology question drives the exact same machinery as a right/wrong signal on a math question.

> **Takeaway for the new cowork:** you are not rebuilding a learning system. You are filling an existing one with a different set of these records and relabeling the shelves they sit on.

---

## The shelves: how questions are organized

Kiwimath organizes questions in a **3-level hierarchy**. The names are math-flavored today but the *shape* is universal:

```
LEVEL            →   PILLAR / STRAND     →   TOPIC          →   CONCEPT (skill_id)
(L1…L8)              (Number Theory…)        (GCD & LCM…)        (one idea, many variants)
```

Map that shape onto any exam:

| Kiwimath (math)         | NEET (example)              | JEE (example)                 |
|-------------------------|-----------------------------|-------------------------------|
| Level (grade/tier)      | (one exam tier)             | (one exam tier)               |
| Pillar / Strand         | Subject: Physics/Chem/Bio   | Subject: Physics/Chem/Math    |
| Topic                   | Chapter (e.g. Human Physiology) | Chapter (e.g. Rotational Motion) |
| Concept (skill_id)      | A single testable concept   | A single testable concept     |

The hierarchy is **just configuration** — a few lists of strings and a folder layout. There is no math logic inside it. Changing it is editing a config, not rewriting an engine. (Exact files in `02`.)

---

## The surfaces: what the learner actually touches

The platform exposes the same question bank through several **surfaces**. Each one is reusable as-is for any exam:

1. **Practice (adaptive)** — the learner works through a topic; the engine picks the next question based on how they're doing. Climb a "skill ladder": get a concept right → move on; get it wrong → drill easier variants of the same concept until it clicks. *This is the heart of the product and it is fully subject-agnostic.*

2. **Daily Quiz** — a small fixed set each day, drawn preferentially from a **"verified" pool** (content with trusted provenance). Great fit for exam prep: "today's 10 questions."

3. **Daily Contest + League** — a timed, scored, one-attempt event with a leaderboard and promotion/relegation tiers (Bronze → Legendary). Pure engagement machinery, no subject knowledge.

4. **Library + Reader + Store** — a bookshelf of reference material rendered faithfully (PDF pages or self-contained HTML), read in an in-app reader, unlocked via the economy or money. For exam prep this is gold: past-paper books, formula books, revision guides.

5. **Progress / Profile** — turns the right/wrong history into a friendly picture (a score, mastery per topic, strengths). Again, math-free machinery.

---

## The plumbing behind the surfaces

These are the services that make the surfaces work. Every one of them is content-agnostic:

- **Adaptive engine** — decides the next question (skill-ladder + difficulty). Reads `skill_id` + `difficulty` + right/wrong. Knows nothing about the subject.
- **Economy** — one shared wallet: coins, gems, XP, streak. Earned by practising, spent in the store. "Money never buys rank."
- **Contest + League** — daily scored event + weekly cohort leaderboard with tiers.
- **Persistence** — per-user state (where you are on each ladder, your wallet, your history) saved durably so re-login never loses progress.
- **Content store** — loads the question records from disk into memory and serves them. The one place that "knows the shelves," and it's driven by config + folder layout.
- **Grading** — checks a submitted answer. Two modes: pick-the-option (compare indices) and typed-value (exact match, or an accept-range for decimals). **This is the only place where "is this answer right?" lives, and it only ever compares the learner's input to the *stored* key — it never computes the key itself.** Remember that line; it's the anti-hallucination boundary.

---

## The data-flow in one picture

```
        AUTHORITATIVE CONTENT (past papers, licensed banks, expert authors)
                                   │
                                   ▼
                 [ ingestion / authoring → question records on disk ]
                                   │
                                   ▼
                 [ content store loads them into memory ]
                                   │
        ┌──────────────┬───────────┴───────────┬───────────────┐
        ▼              ▼                       ▼               ▼
    Practice        Daily Quiz            Contest+League     Library/Store
   (adaptive)      (verified pool)        (timed, scored)   (books + reader)
        │              │                       │               │
        └──────────────┴───────────┬───────────┴───────────────┘
                                   ▼
              [ economy + progress + persistence (one shared state) ]
                                   ▼
                          Flutter app (the skin)
```

The top box — content from real sources — is the **only** part that changes per exam. Everything below the first arrow is the spine you reuse.

---

## Tech stack (so the new cowork knows what it's holding)

- **Backend:** Python + FastAPI, deployed to Cloud Run. State in Firestore (with an in-memory fallback for tests).
- **App:** Flutter (Android-first), one screen-shell with tabs for the surfaces above.
- **Content:** plain JSON files on disk, baked into the backend image at deploy. No database needed to *serve* questions — they load from files.
- **Auth:** Firebase.
- **Ship:** a `deploy.sh` for the backend; a Flutter build for the app. Content changes ship with the backend (no app rebuild); UI changes need an app build.

None of these choices are exam-specific. A new app inherits all of them.

---

## Why this matters for "many mini-apps"

Because the subject lives **only** in the content + a few config lists, the marginal cost of app #2 is small:

- App #1 (first exam) = fork + prove the content pattern works end-to-end.
- App #2, #3 = a new content pack + new branding + a config file, on the **same** engine, economy, contest, reader, and store.

That's the leverage. The next file (`02`) tells you exactly which files to keep, which to reconfigure, and which to rebuild.
