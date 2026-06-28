# 05 · Product & Monetization — the JEE/NEET play

How the platform becomes a business in the exam-prep market, and how to run it as *many* apps without multiplying the work. This is strategy, not engineering — adapt it to what you know about the market today.

> Plug in current market figures yourself (aspirant counts, competitor pricing, conversion benchmarks change yearly). This doc gives the *shape* of the strategy, not dated numbers.

---

## How exam prep differs from K-6 (and what that changes)

| | Kiwimath (K-6) | JEE/NEET app |
|---|---|---|
| Who pays | Parent | Student (often parent-funded, but the **student** chooses and uses) |
| What they want | Engagement, gentle growth, "my kid likes it" | **A rank / a seat.** Outcome-driven, anxious, competitive. |
| Time horizon | Years, relaxed | 1–2 intense years, deadline-driven |
| Trust bar | "Is it fun and roughly right?" | "**Is every answer correct?**" — a wrong key is fatal |
| Natural hook | Stickers, mascot, streak | **Rank, percentile, beating peers** |

**The big implication:** the parts of Kiwimath you'd think are "just for kids" — the **daily contest, the league, the leaderboard** — are actually a *better* fit for competitive-exam aspirants than for K-6. Aspirants are already obsessed with rank and percentile; a daily timed contest with promotion/relegation tiers mirrors the real exam's competition and is genuinely motivating. **Lead with it.**

The economy (coins/gems/XP) should stay understated and tasteful for this older, outcome-focused audience — useful for unlocking content and sustaining streaks, but "money never buys rank" matters even more here. Rank must be earned, always.

---

## Positioning

A clean three-part promise, all built on the existing surfaces:

1. **Adaptive PYQ practice** — work official past-paper and trusted-bank questions, with the engine steering you to what you're weak on. (Practice surface + adaptive engine.)
2. **Daily contest + rank** — a timed daily set, scored, leaderboard, leagues. The social/competitive heartbeat. (Contest + league.)
3. **Reference library** — past-paper compilations, formula and revision books, read in-app. (Library + reader + store.)

One line: **"Practise the real questions, compete every day, climb the rank."**

The differentiator vs. the crowded field of exam apps is **trustworthy, source-verified content + the daily competitive loop**, not feature count. Don't try to out-feature incumbents; out-trust and out-engage them.

---

## The multi-app strategy: one platform, many skins

Don't build three codebases. Build **one platform** and ship **per-exam content packs + branding**.

**Sequencing:**
1. **App #1 — pick the simplest exam first.** Recommend **NEET** (almost all single-choice MCQ → least new engineering). Build it as a clean fork to prove the end-to-end pattern (`03`).
2. **Extract the shared core** *after* app #1 ships — not before. Premature "platformization" slows the first launch and you'll guess the seams wrong. Let app #1 teach you where they are.
3. **App #2, #3** (JEE, then state/other exams) = new content pack + branding + a config file on the shared core. Each is a fraction of the effort of #1.

**Rule of thumb:** the first app is a *product*; the second app is what turns it into a *platform business*. Don't claim the platform leverage until app #2 actually reuses the core cheaply.

---

## Monetization

The economy + store already support **earn-or-buy** and free/paid surfaces, so monetization is a **pricing config, not a build**. Options, roughly in order of fit:

- **Freemium + subscription** (most natural). Free: a daily quota of adaptive practice + the daily contest (keeps the competitive loop open to everyone → drives DAU and word-of-mouth). Paid: unlimited practice, full PYQ archives, the reference library, detailed analytics. A monthly/annual sub is the cleanest fit for a 1–2 year prep cycle.
- **Content unlocks** (the store, already built). Individual premium books/compilations unlockable with coins (earned) or money — the dual path the store already implements. Good for monetizing without a hard paywall.
- **Cosmetic / streak economy** (least important here). Keep it light; this audience isn't here for avatars.

**Keep the contest and rank free.** It's your growth engine and your trust-builder; don't gate the thing that makes people come back daily.

---

## The moat

Three layers, in order of durability:

1. **Trustworthy content** — source-verified questions with correct keys and real solutions. Boring, hard, and exactly why most AI-built exam apps will fail (they'll hallucinate keys; see `04`). This is your #1 defensible asset. **Protect it obsessively.**
2. **Adaptivity from real data** — once learners are practising, the right/wrong logs let you calibrate difficulty and personalize better than anyone starting cold. Compounds over time.
3. **The daily competitive loop** — rank, leagues, streaks. Social gravity that's hard to copy once a cohort forms.

Notice the moat is **content + data + engagement**, not code. The code is a means; guard the content and the data.

---

## The Vedantu advantage (use it deliberately)

You're inside Vedantu. That is a structural unfair advantage for *exactly* the two hardest problems:

- **Content sourcing & validation** — Vedantu has subject faculty who can author and **answer-key-verify** Physics/Chem/Bio content. That is the single thing the AI can't do (`04`). Faculty review is your hallucination firewall. Wire it into the pipeline as the mandatory human check before any batch ships.
- **Distribution** — an existing aspirant audience, brand trust, and channels. App #1 doesn't launch into a vacuum.

Treat faculty validation as a **product requirement, not a nice-to-have.** It's both your moat (layer 1) and your safety net.

---

## Risks to name out loud

- **Content accuracy** — the existential one. Mitigation: the `04` guardrails + mandatory faculty sign-off. No batch ships unreviewed.
- **Content rights / IP** — past papers and your/licensed material are fine; third-party textbooks usually aren't redistributable. Decide rights *before* ingesting, not after. (This already bit the math content.)
- **Crowded market** — many JEE/NEET apps exist. Don't compete on feature count; compete on trust + the daily loop + Vedantu distribution.
- **Over-platformizing too early** — see the sequencing rule. Ship app #1 before building the shared core.

---

## The 30-second pitch

> Take the proven Kiwimath engine — adaptive practice, a daily ranked contest, an in-app library, one shared economy — point it at **source-verified exam content** validated by Vedantu faculty, and ship a focused app per exam on the same spine. The first app proves it; the rest are content + branding. The moat is correct content and the daily rank loop, neither of which an AI-built competitor can fake.
