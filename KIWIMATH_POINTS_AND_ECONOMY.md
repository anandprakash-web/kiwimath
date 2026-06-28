# Kiwimath — Points & Economy, explained
*For Anand · 2026-06-22 · answers: what each point system means, how they connect, and how Library content feeds the Quiz*

---

## 1. What each point system means (this is what Profile should say)

Think of them in **two families**: things you **earn-and-spend** (the wallet), and things that **rank you** (the competition). Keep them in their lanes and the confusion disappears.

### The wallet (earn → spend)
| Point | Plain-English meaning | How you earn it | What it's for |
|---|---|---|---|
| **XP** | "How much I've learned." A lifetime counter that only goes up. | A little for every question answered. | Drives your **level/progress** — your sense of growing. Never spent. |
| **Kiwi Coins** | "Effort money." | Every correct answer / completed session. | **Spent** in the Library/Store (unlock books, avatar items). The everyday currency. |
| **Gems** | "Premium money." Rarer, feels special. | Mastery milestones, achievements, big wins. | **Spent** on premium unlocks (premium books, special items). One gem meter — keep it that way. |
| **Streak** | "Did I show up?" Consecutive days practised. | Practise something every day. | A habit nudge; powers streak rewards. Resets if you miss a day. |

### The competition (rank, don't spend)
| Point | Plain-English meaning | How you earn it | What it's for |
|---|---|---|---|
| **LP (League Points)** | "This week's standing." Resets weekly. | Daily Contest + practice. | Your spot in the weekly **League** (Bronze → Legendary). Short-term, resets so everyone keeps a fresh shot. |
| **Kiwi Rating** | "My true strength." Persistent, chess/Elo-style. | Daily Contests only. | Long-term skill number that *doesn't* reset — the magnet for serious Grade 6–10 students. |

**The golden rule:** XP and Rating only go up (growth + strength). Coins and Gems go up *and down* (you spend them). LP and Streak reset (weekly / on a miss). If a number doesn't fit one of those jobs, it shouldn't exist.

---

## 2. How they all connect (the part that matters technically)

There is **one server-side ledger** (the gamification state). Every screen — wallet, Progress, Profile, Clan — **reads the same state**, so they can never disagree ("no disjoint"). That's already true in the v3 build and it's the right design; protect it.

```
            ┌─────────────── ONE LEDGER (server) ───────────────┐
 answer a   │  +XP   +Coins   (maybe) +Gems   streak++           │
 question → │                                                    │ → Wallet chip (Coins, Gems)
 contest  → │  +LP   +Rating  +XP  +Coins                        │ → Progress (XP, level, academic height)
 daily     →│  streak++  (+Gems on milestones)                   │ → Profile (all of the above)
 spend     → │  −Coins / −Gems  (book unlock, shop)              │ → Clan / League (LP, rating)
            └────────────────────────────────────────────────────┘
```

Two things to keep honest as you grow:
- **Money is different.** Before real cash buys anything, the coin/gem **debit must be a single database transaction** (so a double-tap can't double-spend). It's on the roadmap; don't skip it.
- **Never let money buy rank.** Coins/Gems buy *books and cosmetics*, never LP or Rating. The competition has to stay pure or it dies.

---

## 3. How Library content feeds the Quiz (your question #2)

This is the clean part of the new premium-content plan, and it's already wired:

```
 Vedantu academic content (your team's curriculum)
        │
        ├──►  LIBRARY  : per-pillar-per-level interactive BOOKS  (read & study; unlock with Coins/Gems)
        │
        └──►  every gradeable problem is brute-force-validated → tagged "verified"
                     │
                     └──►  DAILY QUIZ : the contest now PREFERS the "Verified" pool
                            (premium, solution-backed questions lead; machine questions
                             only fill in if a level doesn't have enough verified yet)
```

So the *same* curriculum shows up two ways: **read it in the Library**, then **test it in the Daily Quiz** — and the quiz quietly upgrades to "premium" on each level as soon as that level has enough verified content. A student earns Coins/XP from the quiz, and can spend Coins to unlock the matching book. The loop closes on itself.

---

## 4. My recommendation (so Profile reads clean)

You don't have a currency *problem* anymore — the v3 wallet is already down to **Coins / Gems / XP / Streak** + **LP / Rating**. The only thing left is to make each one's **job legible** to a kid and a parent:

- **Profile, kid view:** show **XP** (how much I've learned), **Streak** (showing up), **Coins** + **Gems** (my money), and **Rating** (my strength). One line each, with the plain-English meaning above as the subtitle. Drop any raw counter that doesn't map to a felt job.
- **Profile, parent view:** show **none of the currencies** — only mastery, accuracy, academic height (you already do this; keep it). Parents trust learning signals, not coins.
- **Anywhere you still see a second gem-like meter** (a legacy "engagement gems / totalGems" from the older build): fold it into the single **Gems**. One premium currency, full stop.

If you want a one-sentence north star for the economy: **XP and Rating measure you, Coins and Gems reward you, Streak and LP keep you coming back — and money never buys either of the first two.**
