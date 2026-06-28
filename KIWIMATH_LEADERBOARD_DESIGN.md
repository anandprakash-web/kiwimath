# Kiwimath — Competitive Layer & Leaderboards: Design Plan

*A game-design spec for a fixed-time **Daily Contest** + **Daily / Weekly / Monthly** leaderboards + a persistent **Kiwi Rating**, for a primarily **Grade 6–10 olympiad-track** audience (L3–L7: pre-olympiad → IOQM → RMO → INMO), with a gentler mode for younger tiers.*

---

## 0. The big idea (one screen)

Kiwimath becomes a place you **show up every day at the same time** to compete, climb, and be **rated** — the way chess.com and Codeforces hook competitive minds, rebuilt for 11–16-year-old math-olympiad students.

Three nested loops, each a different reason to return:

- **Daily** → the **Daily Contest** (fixed time, biggest points). The *heartbeat / appointment*.
- **Weekly** → your **League** (a ~30-student cohort with promotion & relegation). The *rivalry*.
- **Long-term** → your **Kiwi Rating** (a persistent chess-style number) and **monthly Seasons**. The *identity & prestige*.

Why nest three loops: a single leaderboard is either unwinnable (global) or stale (same faces). A fast loop (daily), a medium loop (weekly cohort), and a slow loop (rating/season) mean there's always a fresh goal at *some* timescale — the core of long-term retention.

---

## 1. PRD

### 1.1 Audience & positioning
- **Primary — Grade 6–10 olympiad track (L3–L7).** Competitive, self-driven, status-motivated; comfortable with real rankings and a rating. This is the chess.com/Codeforces mindset.
- **Secondary — Grade 1–5 (L1–L3).** Keep a **gentler, cohort-league-only** experience: no public rating, effort-first framing, so younger kids are never discouraged. *Competitiveness is age-tiered.*
- **Parents.** Want proof of engagement **and** genuine progress, and reassurance it's healthy. The parent view reframes competition as effort/consistency and ships a master off-switch.

### 1.1a Level tiering — one engine, three presentation tiers
A 6-year-old (L1) and a 15-year-old IOQM aspirant (L5) need very different competitive experiences — but you do **not** want three systems to maintain. The design is **one LP / Rating / League engine** with **three presentation tiers** that change *visibility, stakes, framing, and safety defaults*. Matchmaking is always **within-level**, so the tiers never mix.

| | **Junior** (L1–L2) | **Middle** (L3–L4) | **Senior** (L5–L7) |
|---|---|---|---|
| Rating | hidden | a friendly "belt" / tier | full chess-style number + titles |
| Daily contest | playful, generous timing | timed but forgiving | strict timed, contest-grade |
| Relegation | none / very soft | gentle | real |
| Boards | cohort only | cohort | cohort **+ global division** |
| Feel | story / mascot, big celebration | balanced | sleek sports / chess app |
| Seasons | light, no pressure | yes | full + Hall of Fame |
| Competition default | **off → parent opt-in** | on, parent-controllable | on |

The **mechanics are identical** across tiers — LP from contest + effort, rating from contests. The numbers *auto-scale* because they're tied to each level's content difficulty (the `skill_difficulty` tag), so you tune **presentation and guardrails, never the math**. This keeps one codebase honest from age 6 to 16.

### 1.2 Goals
- **Habit** — a daily appointment (the Contest) lifts D1/D7/D30 retention.
- **Depth** — more questions/day, more *new skills* cleared, longer streaks.
- **Aspiration** — a visible rating to chase → long-term retention + word-of-mouth ("I'm a Candidate Master on Kiwimath").
- **Social** — clan + cohort rivalry → invites + accountability.

### 1.3 Non-goals
No stranger chat/DMs · no global "you are #84,201" · no pay-to-win (money/coins can't buy rank or rating) · no public full names · the leaderboard does **not** replace Academic Height (that stays the honest, parent-facing mastery signal).

### 1.4 Success metrics (instrument from day one)
- **Daily Contest participation** (% of DAU who attempt it) — the north star.
- D1/D7/D30 retention; streak-length distribution.
- Weekly-league completion (% finishing in a promotion or safe zone, not quitting mid-week).
- Avg questions/day and **new-skills-cleared/week** (learning, not just grinding).
- Rating-distribution health (no runaway inflation/deflation).
- Wellbeing guardrails: % hitting the daily soft-cap, late-night usage, parent off-switch usage.

### 1.5 Personas
- **Aarav, 14, IOQM aspirant** — lives for the daily contest, refreshes his league rank hourly, wants a rating to show friends. *Hook: rating + contest adrenaline.*
- **Nuha, 12, improving** — not the strongest, but consistent. *Hook: a cohort league she can win on effort + streak.*
- **Parent** — wants engagement + real learning, and reassurance it isn't toxic. *Hook: parent dashboard + off-switch.*

### 1.6 FLAGSHIP — the Daily Contest ("Daily Olympiad")
The centerpiece.

- **Fixed time:** opens daily at **6:00 PM IST** (after school / prime study). Runs as a **live window** (e.g. 6:00–10:00 PM) so kids on different schedules can play — but the **on-time bonus** is biggest in the first 30–60 min, creating a real "be there at 6" moment without punishing latecomers.
- **Format:** a short, level-appropriate **rated set** — 6–10 questions, increasing difficulty, drawn by the adaptive engine from the student's level (L1–L7). Everyone in a level gets the **same set that day** (fair comparison). Per-question timer.
- **Scoring:** correctness × difficulty + speed bonus + streak; partial credit on the hardest item. (Formula §4.3.)
- **Live leaderboard:** rank updates as people submit — "you're #4 in your level right now."
- **Biggest points of the day** → feeds the Daily board, the Weekly League, and your Rating. **Missing it forgoes the day's biggest points** (loss aversion → the appointment habit).
- **One attempt.** Anti-cheese: server-graded, time-boxed, randomized option order; rating moves only from contests, so practice can't be farmed.
- **Recommendation:** **unify the existing 4 PM Daily Puzzle into this** — one flagship daily event, not two competing ones (keep the puzzle as an optional casual warm-up if you like).

### 1.7 The three leaderboards
- **Daily board** — today's contest + a little bonus practice LP. Resets midnight IST. Small daily medal + streak credit. *Fast dopamine.*
- **Weekly League** — the core loop. A **cohort of ~30** similar-level students, Mon–Sun. Earn **League Points (LP)** all week (the contest is the biggest source). Top ~7 **promote**, bottom ~7 **relegate**, the middle holds. Tiers: **Bronze → Silver → Gold → Platinum → Diamond → Legendary** (extends your existing set). A fresh cohort every week = renewed hope.
- **Monthly Season** — a 4-week season. Cumulative season points + best contest finishes → **Season Champions**, a **Hall of Fame**, and **exclusive cosmetics** (avatar gear, themes, titles) that retire at season end (FOMO + collection).

### 1.8 Kiwi Rating — the Grade 6–10 magnet
- A **chess/Codeforces-style number** (start ~1000, seeded from Academic Height for a sane day-1 placement). After each contest it updates by performance **vs expectation** (Elo/Glicko-lite): beat students rated above you → it jumps; underperform → a small dip. K-factor is high for new accounts (fast calibration), low once established (stability).
- **Titles at thresholds** (aspirational, not babyish): e.g. **Rookie < 1200 · Specialist 1200 · Expert 1400 · Candidate Master 1600 · Master 1800 · Grandmaster 2000+** (tune later). The number is the status; titles are the milestones.
- **Only contests move rating** (never practice) → grind-proof; practice stays about learning.
- **Relationship to Academic Height** (the 200–800 IRT mastery score): AH = your *true mastery* (private, parent-facing, slow-moving). Rating = your *competitive performance* (public-ish, contest-driven, reactive). They correlate but serve different audiences — keep both.
- **Younger tiers (L1–L2):** rating hidden; they see only the cohort league. *(Wellbeing.)*

### 1.9 Matchmaking / cohorts
- Weekly leagues group ~30 students by **level + recent activity** (winnable and similarly paced), anonymized to safe display names. Backfill small cohorts. In early days, seed with clanmates + clearly-capped pace-setting "ghosts" (replay of prior-week scores) so boards aren't empty — phase out as the base grows.
- Rating pools by level so each contest's "expectation" is fair.

### 1.10 Rewards (what you win)
- **League:** promotion = badge + a coins/gems bonus + a celebration; weekly top-3 = trophy + extra.
- **Daily:** a contest medal (gold/silver/bronze of the day in your cohort), streak credit, a mystery box on milestones.
- **Season:** **exclusive cosmetics** (avatar items, profile themes, animated borders), a permanent "Season N Champion" badge, Hall-of-Fame entry.
- **Rating:** titles, an animated rating-up moment, and a **rating graph** (kids love the curve).
- **All rewards are cosmetic / identity — never power.** No pay-to-win, no gameplay advantage. This protects fairness and parent trust.

### 1.11 Safety & wellbeing (first-class; tuned for tweens/teens)
- **Safe identity:** display name = first name + last initial, or a chosen, moderated handle; avatar not a photo; no full names, no DMs, no stranger chat; cohorts anonymized.
- **Real competition is fine for this age — but bounded:**
  - **Effort still counts** — LP rewards showing up and improving, so a hard-working mid-tier kid can top their cohort; rating is *separate*, so a lower rating never blocks league success.
  - **Daily soft-cap / diminishing returns** on *grind* LP → no incentive to play till 2 AM; a gentle "wrap up for today" nudge after the cap. The contest is one-shot, so it can't be farmed.
  - **Gentle relegation** language ("Moved to Silver — climb back this week!"), never "you lost".
  - **No global humiliation rank** — only your cohort (≤30) + your division band; never "rank 84,201 of 2M".
- **Parent controls:** the dashboard shows effort/consistency/improvement (not a stress-rank); a **master switch** disables public competition (kid then sees only personal-best + clan); a quiet-hours / no-late-night option.
- **Self-competition lane:** personal bests + "beat your last contest" for kids who dislike comparison — nobody is left out.

### 1.12 Edge cases
- **Missed contest / sick day** → a **streak freeze** (earned, limited) so one miss doesn't nuke a 40-day streak.
- **Time zones** → the window + on-time bonus handle most; rating expectation is per-contest, so playing late isn't unfair.
- **Tiny cohorts early** → ghosts/backfill (§1.9).
- **Cheating** → server-graded, randomized, one-shot; rating from contests only; anomaly detection (impossible speed) → shadow-flag.
- **New user** → first 3 contests are "calibration" (rating volatile, then stabilizes); placed gently mid-pack.

### 1.13 Phased rollout
- **MVP (~2–3 weeks):** Daily Contest (one level-set), Daily board, Weekly League with promotion/relegation, LP, streaks, basic rewards. Reuse the clan/engagement infra, `FirestoreBackedStore`, and the adaptive engine for question selection.
- **V2:** Kiwi Rating + divisions + titles; Monthly Seasons + cosmetics; Hall of Fame.
- **V3:** clan-vs-clan contest events; special weekend contests (double-LP / "boss"); rating-based matchmaking; parent-control polish.

### 1.14 Tech / data model / API (rides on what already exists)
- **Currency:** add **LP** (period-scoped) and **rating** + **rating_history** to the gamification state. These are *new fields on the one economy*, not a parallel economy (keeps the "no disjoint" rule — every tab reads the same source).
- **Stores** (`FirestoreBackedStore`, mirroring `adaptive_skill_state`): `contest_results` (per user per day), `weekly_league` (cohort membership + LP), `season_state`, `rating_state` (durable + in-mem fallback).
- **Contest content:** the adaptive engine picks the day's set per level (one shared set/level for fairness), reusing `level_store` + the `skill_seq` difficulty ordering we just built.
- **Endpoints** (new `/v3/contest`, `/v3/league`): `GET /contest/today` · `POST /contest/submit` (server-graded; awards LP + rating + economy via the existing `gamification.record_answer`) · `GET /league/me` (cohort board) · `GET /league/season` · `GET /me/rating`. Auth: `assert_user_match` (the pattern we just hardened).
- **Cron** (reuse the `clan_cron` Cloud Scheduler pattern): midnight-IST daily rollover (Daily reset + streak check); Sunday-night weekly promotion/relegation + new cohorts; month-end season settle + reward grant.
- **Anti-cheat:** one attempt, server time-box, randomized option order, rating only from contests.

---

## 2. UI/UX

*(See the interactive mockup `kiwimath_leaderboard_mockup.html` — phone frames for every screen below.)*

- **Daily Contest flow** — a **lobby with a live countdown** ("Daily Olympiad in 1h 42m", a "remind me" bell) → the **timed quiz** (one question at a time, a slim per-question timer, no answer leak) → **instant results + the live board** ("you placed #4 of 28, +420 LP, rating +18").
- **Weekly League** — the cohort board with **your row highlighted and pinned**, a green **promotion zone** (top 7) and red **relegation zone** (bottom 7), a week countdown, and each row showing avatar · safe name · LP · trend arrow.
- **Monthly Season / Champions** — season standings, the **Hall of Fame**, and the retiring cosmetic rewards.
- **Rating card** — the big number, current **title + division badge**, and the **rating graph** over time.
- **Parent view** — competition reframed as **effort / consistency / improvement**, plus the **master off-switch** and quiet-hours.
- **Celebrations** — promotion burst, rating-up animation, contest-medal moment (the dopamine payoffs).

**Visual language:** Kiwimath orange `#FF6F00`, brilliant.org-style line icons, clean phone frames, **big legible numbers** (teen-pro, not babyish). The competitive screens feel like a sports/chess app, not a toddler game.

---

## 3. Branching & connection to every tab

The leaderboard is a *layer*, not a tab — it threads through everything, and everything feeds one economy.

- **Practice / Olympiad** — every correct answer earns LP (anti-grind weighted by `skill_difficulty`); the header carries your **league rank** + a **"Daily Contest in 2h"** pill.
- **Worksheets / DPP / Daily Puzzle** — the Daily Puzzle is **absorbed into / feeds** the Daily Contest; completion → LP.
- **School / Curriculum** — curriculum practice **also earns LP**, so school work counts toward the league (non-olympiad effort still rewarded).
- **Clan** — the clan board = sum of members' LP; **clan-vs-clan weekly**; the contest drives clan points too. The new system **unifies with** your existing clan league rather than competing with it.
- **Growth** — your **rating graph**, league history, best contest finishes, and season trophies live here: the "personal progress + bragging shelf".
- **Parent** — the wellbeing-framed competition summary + controls.
- **Profile** — division badge, title, trophy shelf, current streak, rating.
- **One economy** — LP / rating / coins / gems / streak all flow from the same server state (§1.14), so no two tabs ever disagree (the "no disjoint" rule you already enforce).

```
                       ┌─────────────────────────────┐
                       │   DAILY CONTEST  (6 PM IST)  │  ← flagship, biggest LP + rating
                       └──────────────┬──────────────┘
        LP + rating + economy (one server-graded submit)
   ┌───────────────┬───────────────┬──────┴───────┬───────────────┬─────────────┐
   ▼               ▼               ▼              ▼               ▼             ▼
 Practice        School          Clan          Growth          Parent        Profile
 (LP/answer)   (LP/answer)   (clan board,   (rating graph,  (effort view,  (badge,title,
  + rank pill   + rank pill   clan-vs-clan)   trophies)       off-switch)    streak,rating)
   └───────────────┴───────────────┴──────┬───────┴───────────────┴─────────────┘
                                  WEEKLY LEAGUE (cohort ~30, promote/relegate)
                                           │
                                  MONTHLY SEASON (champions, hall of fame, cosmetics)
```

---

## 4. Point systems & the hook design — *"what gets them hooked"*

### 4.1 The layered currencies (keep them distinct & legible)

| Currency | Earned for | Resets? | Purpose | Who sees it |
|---|---|---|---|---|
| **Kiwi Coins** | effort (any practice) | no (spendable) | shop / cosmetics | kid |
| **Mastery Gems** | skill / achievements | no | prestige unlocks | kid |
| **XP** | per question | no | account level | kid |
| **League Points (LP)** | contest + practice + streak, this period | **weekly** | the leaderboard rank | kid + cohort |
| **Kiwi Rating** | contest performance vs expectation | persistent (slight season decay) | the prestige ladder / title | kid (+ optional public) |
| **Academic Height** | true mastery (IRT) | slow | the honest progress signal | parent + kid |

**Why separate:** a **resetting** LP keeps the weekly race fair and re-engaging; a **persistent** rating gives long-term identity; **coins/gems** stay the spendable economy (so you can't *buy* rank); **AH** stays the honest parent-facing truth (undistorted by gamification). Different jobs → different meters.

### 4.2 LP earning (the effort + mastery + performance blend)

| Action | LP | Notes |
|---|---|---|
| **Daily Contest** | up to ~500 | the apex — base + difficulty + speed + rank bonus |
| Clear a **new skill** (adaptive ladder) | +25 | rewards real progress, not grinding |
| Correct practice answer | +2…+10 | scaled by `skill_difficulty`; + first-try bonus |
| Daily streak | ×1.0 → ×2.0 | multiplier grows across a 7-day streak |
| Worksheet / puzzle completed | +20…+50 | |
| Clan-challenge contribution | + LP | feeds the clan board too |
| Re-doing a cleared skill | ~0 | anti-grind (engine won't re-serve it; manual = token LP) |
| **Daily soft-cap on grind LP** | — | beyond the cap, practice LP decays → no all-nighters *(wellbeing)* |

The contest **dwarfs** grinding, so the appointment is the optimal play — and you can't out-grind it at 2 AM.

### 4.3 Daily Contest score (per question, then summed)
`score = base(difficulty) × correctness × speed_factor × streak_mult`
- `base`: easy 100 / medium 200 / hard 350 (from `skill_difficulty` / `irt_b`).
- `speed_factor`: 1.5 → 1.0 linear over the time limit (fast = more, but never below 1.0, so accuracy still pays).
- partial credit on the hardest item (rewards *attempting* the stretch question).
- **rank bonus**: the top 10% of the cohort that day get a flat LP bonus.

### 4.4 Rating update (Elo/Glicko-lite — contests only)
- Expected score `E = 1 / (1 + 10^((field_rating − your_rating) / 400))`.
- `new_rating = your_rating + K × (actual_percentile − E)`; `K` = 40 (new) → 16 (established).
- Seed from Academic Height for a sane day-1 placement.
- **Only contests move it** (never practice) → grind-proof.

### 4.5 The hooks — and the psychology (each one designed *healthy*)
1. **Appointment mechanic** (fixed-time daily contest) — the single strongest habit former; you build a 6 PM ritual. *Healthy because it's a bounded event, not infinite scroll.*
2. **Loss aversion** (miss the contest = forgo the day's biggest points; promotion/relegation zones) — returns are driven by not *losing ground*. *Bounded: one event, gentle relegation language.*
3. **Fresh-start effect** (weekly/monthly resets) — everyone re-engages at 0; last week's straggler has hope. *The anti-burnout opposite of an ever-growing global board.*
4. **Variable reward & near-miss** ("12 LP from 1st!", mystery boxes) — the dopamine of the close gap. *Used to celebrate, never to gate progress behind chance.*
5. **Streaks + freezes** (endowed progress; don't-break-the-chain) — commitment escalates over time. *Freezes + quiet-hours stop it becoming pressure.*
6. **Small cohorts** (~30 named peers) — winnable + social proof; you can actually be #1. *Avoids global-rank despair.*
7. **Rating prestige + titles** (chess-style) — slow-burn status and identity ("I'm a Candidate Master"). *The Grade 6–10 magnet — aspirational, not punishing.*
8. **Seasons + exclusive cosmetics** — FOMO + collection + a reason to return monthly. *Cosmetic only — no power — so collecting is harmless.*
9. **Clan belonging** — social accountability ("don't let the clan down") + co-op. *Positive peer pressure, pointed at learning.*
10. **Progress made visible** (rating graph, trophy shelf, "skills mastered") — the most underrated hook: *seeing yourself improve.* The healthiest one — it ties engagement directly to real growth.
11. **Surprise & delight** (double-LP weekends, "boss" contests, promotion animations) — breaks routine and re-spikes interest.
12. **Self-competition lane** (personal bests) — a hook for the comparison-averse, so nobody is excluded.

### 4.6 Wellbeing guardrails (the spine that keeps it healthy)
Effort-weighted LP (strugglers can win cohorts) · rating *separate* from league (a low rating never blocks league joy) · daily soft-cap + no-all-nighter design · gentle language · cohort-only visibility (no global humiliation) · parent dashboard + master off-switch + quiet hours · cosmetic-only rewards (no pay-to-win) · "great effort" recognition independent of rank.

---

## 5. Recommended next step
Build the **MVP** (§1.13): the Daily Contest + Weekly League + LP + streaks, riding on the existing economy, the adaptive engine (for the daily set), and `FirestoreBackedStore`. That alone delivers the appointment habit + the cohort rivalry — the two biggest retention levers — in ~2–3 weeks. Rating, Seasons, and cosmetics follow in V2.
