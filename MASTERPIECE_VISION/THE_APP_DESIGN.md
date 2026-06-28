# The Complete App Design — Kiwi

*The full design of the app, screen by screen, flow by flow — built so we can sit down, go through it, and decide what to implement and what to cut. Every screen is tagged **REUSE** (we already have it), **ADAPT** (we have most of it, needs rework), or **NEW**, with a rough effort size, so the triage is concrete.*

**Companion:** open `masterpiece_prototype.html` to walk the hero flows; the full clickable prototype (`app_prototype_full.html`) shows every screen below.
**Strategy behind it:** `THE_MASTERPIECE.md`.

---

## 1 · Design north star & principles

**North star:** *make young mathematicians* — measured by depth, joy, and real contest progression, with **correctness** and **safety** as non-negotiables.

Eight principles that decide every screen:

1. **Wonder before work.** Every visit can start with a "whoa." The front door is delight, not a to-do list.
2. **Stuck is safe.** A hard problem is never a dead end and never spoiled — the hint ladder is everywhere.
3. **Many paths beat one answer.** We always show that a problem can be solved in more than one beautiful way.
4. **Depth over volume** (Olympiad track). Reward struggle and elegance, not speed and quantity.
5. **One identity, one climb, one wallet.** "Young mathematician," the Path, and one economy — no disjoint surfaces.
6. **Progressive disclosure.** A 6-year-old and an INMO aspirant use the *same* app; the difficulty dial and visible surfaces change, the navigation doesn't.
7. **The app is the expert.** So the parent doesn't have to be (and a stuck kid is never alone).
8. **Safety is a feature, not a setting.** Especially anywhere kids meet kids.

---

## 2 · Information architecture (the map)

Five tabs. Everything hangs off them. The **Coach** is not a tab — it's a thin intelligence that surfaces the *next right thing* as cards inside Today (and nudges elsewhere).

```
┌── TODAY ────────┬── TRAIN ─────────┬── COMMONS ───────┬── PATH ──────────┬── ME ───────────┐
│ Problem of the  │ Practice (fluency)│ Discussions      │ The mountain     │ Profile + wallet │
│   Day (Wonder)  │ Thinking Gym (deep)│ Solve-Together   │  school→IOQM→IMO │ Achievements     │
│ Coach: next step│ Library (books)   │ Clans/study grps │ Node detail      │ Shop (coins)     │
│ Daily Contest   │ Topic browser     │ Mentors / "Ask a │ Mastery          │ Settings         │
│ Streak          │ (9 strands)       │   Mathematician" │  certificates    │ ▸ Parent Zone   │
│                 │                   │ Contest + League │                  │   (PIN-gated)    │
└─────────────────┴───────────────────┴──────────────────┴──────────────────┴──────────────────┘
        ▲ first-run: Onboarding & Placement (separate flow) feeds the Path + the difficulty dial
```

**Why this IA:** it maps 1:1 to the strategy's three rooms — **Wonder (Today)** → **Train** → **Belong (Commons)** — held together by **Path** (the climb) and **Me** (identity + parent trust). Compete (contest/league) lives in Commons because it's social, but is *surfaced* on Today when live.

---

## 3 · The design system

**Palette** (already used in the prototype): Orange `#FF6F00` (primary/energy), Ink `#1E1633` (depth), with Teal `#12B5A5`, Berry `#FF5470`, Gold `#FFB12B`, Green `#37B86B`, Violet `#7A5CFF` as accents tied to meaning (teal=strategy hints, violet=insight, green=mastery/correct, berry=challenge, gold=reward).

**Type:** one friendly sans; big bold headers (28–40), readable body (15–17), tiny uppercase kickers for orientation. Maths renders as real LaTeX; figures as our SVG/PNG.

**Voice:** warm, Socratic, mascot-led (Kiwi 🥝). The reader is always a "young mathematician." We celebrate *thinking* ("nice — you used place value exactly right"), never gush. Zero engineering jargon (no IRT/theta/levels-as-numbers to parents).

**Core components** (design once, reuse everywhere):
- **Card** (rounded 22px, soft shadow) — the atom of every screen.
- **Badge** — icon in a colored rounded square; the repeated visual motif.
- **Hint ladder** — a 3-tone progressive reveal (orange nudge → teal strategy → violet worked-step). The most important component in the app.
- **Solution tabs** — 2–4 approaches side by side, one always a community solution.
- **Buttons** — primary / ghost / soft / accent.
- **Thread** — avatar + who + approach + upvote; the unit of Commons.
- **Path node** — done / current / locked dot on a vertical climb.
- **Gauge & stat** — plain-language growth.
- **Coach card** — a friendly, dismissable "do this next" prompt.
- **Celebrate sheet** — the mastery / fork-up bottom sheet.

---

## 4 · Screen-by-screen specification

> Tag key: **REUSE** = exists today · **ADAPT** = exists but needs rework · **NEW** = build it. Effort: S / M / L.

### A · Onboarding & Placement *(first-run flow, then never again)*

| # | Screen | Purpose | Key elements | Tag · Effort |
|---|--------|---------|--------------|--------------|
| A1 | **Welcome** | Wonder-first first impression | A beautiful problem/animation, "Where young mathematicians are made," one CTA | NEW · S |
| A2 | **Who's learning** | Identity + age/grade | Name, age/grade, avatar pick | ADAPT · S |
| A3 | **Goal dial** | Set the difficulty dial + which surfaces show | 3 choices: *Love maths* · *School + stretch* · *Olympiad-bound*; sets whether the IOQM track + Commons surface early | NEW · S |
| A4 | **Find your start** | Gentle adaptive placement (not a scary test) | 5–8 adaptive problems framed as "let's find your starting line," with the hint ladder live | ADAPT · M |
| A5 | **Your Path begins** | Payoff: show where they stand + the summit | Path position on the mountain, first "next step," meet Kiwi | NEW · S |
| A6 | **Parent setup** *(skippable)* | Trust + safety from minute one | PIN, community on/off, time guardrail, notifications | ADAPT · S |

### B · Today (Home / Wonder)

| # | Screen | Purpose | Key elements | Tag · Effort |
|---|--------|---------|--------------|--------------|
| B1 | **Today home** | The front door + the daily loop | Greeting, Academic-Height micro, **Problem of the Day** card (wonder), **Coach "next step"** card, Daily-Contest banner (when live), streak, "continue practice" | NEW (assembles existing) · M |
| B2 | **Problem of the Day** | The daily "whoa" for *any* level | The beautiful problem, attempt, **reveal-why-it's-beautiful**, discuss link | NEW · M |
| B3 | **Coach route** | One tap to the next right thing | Routes to Gym / Practice / Commons / Path based on state | NEW · M |

### C · Train

| # | Screen | Purpose | Key elements | Tag · Effort |
|---|--------|---------|--------------|--------------|
| C1 | **Train hub** | Choose how to work | Three doors: **Practice** (fluency), **Thinking Gym** (depth), **Library**; + topic browser entry | ADAPT · S |
| C2 | **Practice session** | Adaptive fluency | Question (MCQ/typed), instant feedback, hint, streak, economy rewards | **REUSE** · — |
| C3 | **Thinking Gym** ⭐ | The flagship deep-problem loop | One hard problem → **hint ladder** → submit → **multiple solutions** → **explain-it-back** → discuss | NEW · L |
| C4 | **Topic browser** | Pick subject → topic → concept | 9 strands, mastery per topic, locked/empty states | ADAPT · M |
| C5 | **Library** | The bookshelf | Books grid (rendered/authored/interactive), Level/Subject filter, painted covers, get→download→read | **REUSE** · — |
| C6 | **Reader** | Read a book offline | HTML reader: font/theme/scroll, interactive slides | **REUSE** · — |
| C7 | **Mastered / exhausted** | Turn "ran out" into a graduation | Celebrate sheet → fork-up: level-up / deeper / create / discuss / mentor | NEW · M |

### D · Commons (Community) — *safety is the product here*

| # | Screen | Purpose | Key elements | Tag · Effort |
|---|--------|---------|--------------|--------------|
| D1 | **Commons home** | The belonging surface | Safety banner, **Solve-Together** (weekly), recent discussions, **solution of the week**, your clan, Compete entry | NEW · M |
| D2 | **Problem thread** | Discuss one problem, safely | Moderated approaches, upvotes, "show your approach" composer; no DMs, age-gated | NEW · L |
| D3 | **Post your approach** | Capture *thinking*, not just answers | Composer (text + math), "method not answer" nudge, pre-moderation | NEW · M |
| D4 | **Clan / study group** | Small-group problem-solving | Members, group puzzle, guess board, clan score | **REUSE/ADAPT** · S |
| D5 | **Solve-Together** | One hard problem, the whole community | The collective problem, contributed ideas building on each other | NEW · M |
| D6 | **Mentors / Ask a Mathematician** | The human edge | Medalist solutions, AMA, **connect-to-faculty** (milestone/premium) | NEW · L |
| D7 | **Daily Contest** | Timed, scored, one attempt | Lobby → timed quiz → results + leaderboard | **REUSE** · — |
| D8 | **League** | Weekly cohort competition | Tiers Bronze→Legendary, standings, promote/relegate | **REUSE** · — |

### E · Path

| # | Screen | Purpose | Key elements | Tag · Effort |
|---|--------|---------|--------------|--------------|
| E1 | **The mountain** | The visible climb | school → L1–L7 → **IOQM → RMO → INMO → IMO**, current position, mastery, next foothold | NEW (data exists) · M |
| E2 | **Node detail** | Inside a level/pillar | Topics, mastery %, what's left, boss problems, the book for it | ADAPT · M |
| E3 | **Mastery certificate** | A proud, shareable milestone | Certificate, share-to-parent | NEW · S |

### F · Me / Profile

| # | Screen | Purpose | Key elements | Tag · Effort |
|---|--------|---------|--------------|--------------|
| F1 | **Profile** | Identity + growth | "Young mathematician," Academic Height, strand radar, wallet (coins/gems/XP/streak), achievements | ADAPT · S |
| F2 | **Shop / wallet** | Spend what you earn | Cosmetics + book unlocks, earn-or-buy, "money never buys rank" | **REUSE** · — |
| F3 | **Settings** | The basics | Account, notifications, accessibility | REUSE · — |
| F4 | **Parent Zone** (PIN) | Trust, safety, plan | Plain-language growth, the Path, **safety controls** (community/DMs/time), certificates, billing | ADAPT · M |

---

## 5 · The core flows (how screens connect)

1. **First run → first aha.** A1 Welcome → A2 who → A3 goal dial → A4 placement (with hints) → A5 Path begins → (A6 parent) → B1 Today. *Goal: a win + a glimpse of the summit in the first 3 minutes.*
2. **Daily loop.** Open → B1 Today → B2 Problem of the Day (wonder) → Coach card → C3 Gym *or* C2 Practice → reward/streak → optional D1 Commons. *Goal: a habit that starts with delight.*
3. **Deep-problem loop (the flagship).** C3 Gym: problem → struggle → hint ladder (nudge→strategy→step) → submit *or* honourable give-up → multiple solutions → explain-it-back → D2 discuss. *Goal: convert drill into thinking.*
4. **Content-exhaustion fork.** Finish a topic → C7 celebrate sheet → level-up (E1) / deeper (C3+book) / create (D3) / discuss (D2) / mentor (D6). *Goal: "ran out" feels like graduation; also our content-gap radar.*
5. **Community loop.** See a problem → D3 post approach → upvotes/reputation → help others → "mentor-in-training." *Goal: kids teaching kids, safely.*
6. **Pathway loop.** Climb levels (E1/E2) → unlock IOQM track → E3 certificate → parent sees it (F4). *Goal: a real mountain + parent trust.*
7. **Compete loop.** B1 banner → D7 contest → score → D8 league movement. *Goal: rank that's earned, never bought.*
8. **Stuck at the edge → human.** Gym/Path → D6 Ask a Mathematician. *Goal: the moment money can't fake.*
9. **Parent loop.** Me → F4 PIN → growth + safety + certificate + upgrade. *Goal: visibility without anxiety.*

---

## 6 · The Coach & notifications (the connective tissue)

**The Coach** is the single intelligence that replaces "next question" with "next *right thing for this kid*." It reads the same signals the engine already logs (mastery, struggle, streak, recency) and decides, each session, among: a moment of wonder, a deep problem, a practice set, a hint, a peer discussion, a level-up nudge, a spaced-return, or a human. It appears as **one friendly Coach card on Today** (and quiet nudges elsewhere) — never a chatty assistant, never a tab.

**Notifications (sparing, kind):** today's beautiful problem; contest is live; "your approach got upvoted"; a mentor replied; "you're one topic from the IOQM track"; gentle streak-care (never guilt). All parent-gated for under-13s.

---

## 7 · States we must design (not just the happy path)

- **Empty / not-yet:** "No Grade-X practice yet" (honest, inviting) — already a principle we fixed once.
- **Locked:** a Path node or premium surface — show *why* and *how to unlock*, never a dead wall.
- **Exhausted:** the celebrate-and-fork sheet (C7) — *never* fake or recycle filler.
- **Stuck:** the hint ladder — always available, never a spoiler.
- **Wrong answer:** gentle, method-pointing, try-again — never a red ✗ on a correct method.
- **Offline:** downloaded books + cached practice still work.
- **Moderation pending:** a posted approach shows "being checked" before it's public.

---

## 8 · The triage table (for our "build / skip" discussion)

Everything in one place, sorted by what carries the vision. This is the sheet we argue over.

| Priority | Thing | Tag | Effort | Why it matters | Cut risk if skipped |
|---|---|---|---|---|---|
| 🥇 **Soul** | **Thinking Gym** (hint ladder + multiple solutions + explain-back) | NEW | L | Converts drill → thinking; the single most differentiating feature | Stay "just another practice app" |
| 🥇 Soul | **Problem of the Day / Wonder** surface | NEW | M | The daily habit + the "fall in love" front door | No emotional hook; retention suffers |
| 🥇 Soul | **Re-aim the Olympiad track** (reward depth/struggle, not speed) | ADAPT | M | Fixes the core mismatch for gifted kids | Bore the exact users we want |
| 🥇 Soul | **Content-exhaustion fork** (celebrate + level-up/deeper/create) | NEW | M | Turns a dead end into a graduation + content radar | Kids hit a wall and churn |
| 🥈 **Moat** | **Commons: kid-safe problem threads + show-your-approach** | NEW | L | The AoPS magic, safe for under-13s — the real moat | No community = no defensibility |
| 🥈 Moat | **Safety architecture** (moderation, age-gate, no-DM) | NEW | L | The thing that lets parents say yes | Can't ship community at all |
| 🥈 Moat | **The Path** (school→IOQM→IMO, visible) | NEW | M | The summit gifted kids climb toward; parent clarity | No sense of journey/goal |
| 🥉 **Edge** | **Ask a Mathematician** (Vedantu faculty) | NEW | L | The human moment money can't fake; our unfair advantage | Lose the Vedantu differentiator |
| 🥉 Edge | **Solve-Together** (weekly collective problem) | NEW | M | Belonging + word-of-mouth | Weaker community pull |
| 🥉 Edge | **Make-a-Problem** (authoring → curated content) | NEW | M | Self-feeding content engine; fixes exhaustion long-term | Content stays finite/manual |
| ✅ **Have** | Practice, Library/Reader, Contest, League, Economy/Wallet, Clans, Parent dashboard | REUSE | — | Already built — wire into the new IA | — |
| 🔧 **Polish** | Onboarding & placement redesign, Coach card, mastery certificates | NEW/ADAPT | S–M | First impression + connective tissue + parent delight | Rougher funnel, less glue |

**My recommended first cut (if we build nothing else):** the four 🥇 "Soul" items. They reuse the engine, need mostly content + UX, and they're what turn what we have into a *thinking* app. Everything else is sequenced after — `THE_MASTERPIECE.md` §5 has the phasing.

---

## 9 · What this design deliberately does *not* do (so we choose consciously)

- It does **not** turn the engine into a chatbot tutor. The Coach is a *router*, not a conversational AI (correctness risk).
- It does **not** open free-form chat or DMs. Discussion is always attached to a problem, moderated. (Safety.)
- It does **not** let the AI author or grade Olympiad maths. Humans + sources own correctness; the app routes, presents, and moderates.
- It does **not** show ranks/scores to young kids as the primary signal. Wonder and mastery lead; competition is opt-in and earned.

That's the complete design. Open the prototype, walk it, and let's mark up the triage table together — what we build now, what waits, what we drop.
