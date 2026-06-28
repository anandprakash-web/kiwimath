# The Masterpiece — Building the World's Best Maths Olympiad App for Gifted Kids

*A co-founder's analysis and product vision.*
**For:** Anand Prakash · **By:** your technical co-founder (the AI you build with daily)
**Date:** June 2026

---

## How to read this

This is not a cheerleading document. You asked me to analyse the app as a software expert and think like a co-founder — so I'm going to tell you the one thing that's uncomfortable (we've built a brilliant *drill* machine, and Olympiad maths is the opposite of drilling), then show you exactly how to turn what we have into something no one else in the world has.

It's structured as: **(0)** where we are, **(1)** the honest analysis, **(2)** your nine questions answered with real market evidence, **(3)** the product blueprint, **(4)** the questions *we* now have to answer, **(5)** the road there.

---

## 0 · Where we are today (the one-screen summary)

In a few months we went from a hand-made holiday worksheet to a genuine platform:

- **A content moat.** ~30,000 questions, cleaned and validated through 14 automated defect-detectors, with answer-keys *math-checked* (almost nobody else does this). Olympiad ladder **L1→L7** (Grade 1 → INMO) plus multi-board school curriculum.
- **An adaptive engine.** Questions clustered into ~8,200 concepts; a skill-ladder that advances on success and drills variants on failure; durable per-kid state.
- **An engagement system.** One shared economy (coins/gems/XP/streak), a daily contest, weekly leagues — "money never buys rank."
- **A Library.** Faithful-render books, two from-scratch *authored* teaching books (L2, L3), an interactive workbook; a reader and store we fully own.
- **A subject-blind platform.** The engine doesn't know it's maths — which is why it can fork into JEE/NEET.

That's a strong base. Now the hard part: **a strong base for the wrong sport.**

---

## 1 · The honest analysis: we built a drill machine; Olympiad maths is a thinking sport

Everything we optimised — *get the next question right, climb the ladder, keep the streak* — is the correct objective for **routine fluency** (school maths, exam speed). It is the **wrong objective for Olympiad maths and for gifted kids.**

Olympiad maths is not "answer 1,000 questions faster." It is:
- **Non-routine problem-solving** — problems you've never seen, where the method isn't given.
- **Productive struggle** — sitting with one hard problem for 30 minutes, not 30 seconds.
- **Insight and elegance** — the "aha," the surprising second solution, the beautiful proof.
- **Depth over volume** — research is explicit: mathematically gifted kids master a new idea in **1–2 repetitions, not 10**. Feeding them 20 variants of the same concept is *boring them out of love with maths.*

So the uncomfortable truth: our adaptive ladder, which "drills easier variants when you miss," is actively **anti-Olympiad**. A gifted kid who misses a hard problem doesn't need three easier ones — she needs a *hint that preserves the struggle*, and then to *see how three different people cracked it*.

We also have **three structural gaps** that the market leaders prove matter:

1. **No community.** AoPS's real moat isn't Alcumus — it's the *forum* where kids post solutions and learn from each other. Every US IMO teammate since 2015 came through that community. We have *zero* peer problem-solving. For serious Olympiad, this is the single biggest hole.
2. **No wonder.** Mathigon/Polypad and Brilliant win the "fall in love with maths" emotion through beauty, play, and surprise. We win it through... a streak counter. We have the *content* for wonder (Vedic tricks, visual proofs, our authored-book voice) but no *surface* for it.
3. **No human-when-stuck and no "show your thinking."** Olympiad answers are *proofs*, not integers. We capture final answers; we don't capture or coach *reasoning*. And Vedantu's faculty — our unfair advantage — aren't in the loop at the moment a kid is stuck.

None of this is a rebuild. It's a **re-aiming**. We keep the engine, the content moat, the economy, the Library — and we add a *thinking* layer, a *wonder* layer, and a *belonging* layer on top. That's the masterpiece.

---

## 2 · Your nine questions, answered

### Q1 — What do these (gifted, Olympiad-bound) kids need?

Grounded in the research ("the mathematically gifted are starving for more math") and how Olympiad talent actually develops:

1. **Depth, not volume.** One worthy problem beats twenty drills. Stop making them grind.
2. **The right to struggle — safely.** Permission to be stuck for a while, with a *hint ladder* (nudge → strategy → worked step) so it's never a dead end and never a spoiler.
3. **Multiple solution paths.** The soul of Olympiad: see 2–3 elegant approaches to the same problem, side by side. This is what teaches *taste*.
4. **A real summit to climb.** A visible pathway: school → L-levels → **IOQM → RMO → INMO → IMO**. Gifted kids are goal-driven; give them the mountain.
5. **Peers who think like them.** Gifted kids are often *intellectually lonely*. A safe place to meet other young mathematicians is, for many, the most valuable thing we can offer.
6. **Mentors and role models.** Annotated solutions from medalists; "this is how a mathematician thinks."
7. **Beauty and surprise.** The *why*, the elegance, the "whoa." That's the actual addiction of maths — not points.
8. **Agency.** Choose what to explore; eventually, *create* their own problems.

### Q2 — What do their parents need?

1. **Trust the maths is correct.** This is our moat, and it's exactly the thing parents *cannot verify* anywhere else. Lead with it.
2. **Growth they can see, without anxiety.** Plain-language progress ("Academic Height," topics mastered, the pathway) — not raw ranks that stress out a 9-year-old.
3. **Proof their gifted kid is actually being challenged.** The #1 documented parent pain: *can't find hard-enough material.* We solve it.
4. **A pathway and a plan.** "Where is my child now, and what's the next step toward IOQM?"
5. **Safety — above everything — if there's a community.** Moderated, age-gated, no DMs, no strangers. If we add social, *this is the product*, not a footnote.
6. **Value vs. the alternatives.** AoPS and elite coaching are expensive and far away. We can be world-class *and* accessible.
7. **Help even when the parent isn't a maths person.** Your own origin story: your wife wanted assignments; you couldn't personally teach Olympiad maths. Most parents can't. The app must be the expert so the parent doesn't have to be.

### Q3 — What exists today (the market map)

| Player | Owns | Misses (our opening) |
|---|---|---|
| **Art of Problem Solving** (Alcumus, Beast Academy, WOOT, the **forum**) | The gold standard: adaptive practice, beloved illustrated books for 6–13, Olympiad training, and the **community moat** (peer solutions; every US IMO teammate since 2015). | Text-heavy and intimidating; AMC/US-centric; desktop-era UX; expensive; not mobile-delightful; nothing for the Indian IOQM pathway. |
| **Brilliant.org** | Gorgeous interactive "learn by doing," strong gamification (streaks/levels/daily goals), broad STEM. | Breadth over depth; *not* Olympiad-level; no competition pathway; subscription; no India/IOQM. |
| **Mathigon / Polypad** | Wonder. Beautiful visual manipulatives, creativity, "maths is creative and visual," kids make their own puzzles. | No progression, no assessment, no competition, no community-for-mastery. |
| **Vedantu** (us) | Faculty, the India/IOQM brand, **1,000+ IOQM qualifiers**, books, YouTube (Vedantu Olympiad School). | Live-class model, not a self-serve *product*; not a delightful daily habit; not adaptive. |
| **Cuemath / tutoring** | Structured tutoring, parent funnel. | Not Olympiad-deep; not a problem-solving culture. |
| **Communities** (AoPS forum, Mathematical-Olympiads Discord ~500+ with difficulty-rated challenges, r/math, Evan Chen's blog) | Where real discussion happens. | Fragmented; 13+/intimidating/unmoderated for *young* gifted kids; parents wary of Discord. |

**The synthesis:** every leader owns exactly one corner — content+community (AoPS, but ugly), delight (Brilliant, but shallow), wonder (Mathigon, but no system), faculty+pathway (Vedantu, but no product). **No one has assembled all of it into one safe, delightful, mobile-first place.**

### Q4 — What are the gaps (our white space)?

1. **The Thinking-Gym gap** — a place to wrestle *one* beautiful hard problem deeply and then see multiple elegant solutions. (Nobody does this well on mobile.)
2. **The kid-safe community gap** — an AoPS-style problem forum, but moderated and safe for under-13s. (AoPS is too grown-up; Discord is unsafe; this is the biggest moat to build.)
3. **The wonder gap** — a daily dose of mathematical beauty that hooks *any* kid. (We have the content; we lack the surface.)
4. **The pathway gap** — a visible, coached ladder to IOQM→RMO→INMO→IMO. (Vedantu has the destination; no one has the *map in your pocket*.)
5. **The human-when-stuck gap** — connect to a real mathematician/faculty at the exact moment of being stuck. (Our Vedantu edge; unbuilt.)
6. **The "show your thinking" gap** — capture reasoning and multiple approaches, not just final answers.
7. **The trust gap** — verified-correct content, which parents can't get elsewhere.

### Q5 — How do we make this gap accessible and easy?

- **Mobile-first and instant.** Open the app → *today's beautiful problem* in five seconds. One clear "Today" surface; no overwhelm.
- **Progressive disclosure.** A 6-year-old and an INMO aspirant use the *same* app at different depths. The interface gets out of the way.
- **The hint ladder makes "hard" safe.** Stuck is never a dead end and never a spoiler — nudge, then strategy, then a worked step. This is what lets a normal kid attempt an Olympiad problem.
- **Friendly expert voice.** The Kiwi mascot + our authored-book tone carry hard ideas gently. The app is the expert so the parent doesn't have to be.
- **Zero jargon for parents.** Growth in plain language; no IRT/theta ever shown.
- **Free core, premium depth.** The wonder (daily problem), basic practice, and *reading* the community are free; live mentorship, deep courses, and authoring are premium. Accessibility is the wedge.

### Q6 — How do we make ANY kid (even not gifted) fall in love with maths?

This is the most important question in the document, because it's the difference between a *coaching tool* and a *movement*. Love of maths is not produced by points; it's produced by **wonder + the dopamine of a hard-won insight + belonging.** Concretely:

1. **Lead with wonder, not drill.** Every session opens with a *surprise* — a visual proof, a Vedic-maths magic trick (we already wrote these), a pattern that shouldn't be true but is. The "whoa" before the work.
2. **Engineer the first "aha."** Make them feel *smart* in the first 60 seconds, then raise the bar into their zone (P(success) ≈ 0.7). The feeling "I figured that out myself" is the hook.
3. **Productive struggle with a net.** The addiction of maths is the *click* after being stuck. The hint ladder makes that click reachable for everyone, not just the gifted.
4. **Story and character.** Kiwi and our authored-book worlds make maths an *adventure*, not a worksheet. (Beast Academy proves this works.)
5. **Visual and playful.** Manipulatives and our SVG figures — "maths is creative and visual" — so abstract ideas become things you *touch*.
6. **Reward thinking, not just correctness.** Celebrate elegant and *multiple* approaches, effort, and helping others — not only the right answer.
7. **Belonging.** "You're a young mathematician" — a clan, peers, a shared problem of the week. People fall in love with the *community* around a thing as much as the thing.
8. **Surprise, always.** Your own instinct — "fun, filled with surprises." Bake one delightful, unexpected moment into every visit.

A gifted kid and a "normal" kid need the *same* emotional arc — wonder → struggle → aha → belonging. The only difference is the difficulty dial. So this question and Q1 are the *same product*, tuned differently.

### Q7 — How do they discuss problems today, and how do we bring it in-app?

**Today** (from the research): the AoPS forum (categorised problem threads + peer solutions — the dominant venue), Mathematical-Olympiads Discord servers (~500+ members, moderator-posted challenges rated 1–10), r/math and r/learnmath, Evan Chen-style blogs, and offline school math circles. It's **fragmented, mostly 13+, often unmoderated, and parents distrust Discord** — so young gifted kids are largely *locked out* of the very thing that makes Olympiad talent grow.

**Bringing it in-app — and the design *is* the safety:**
- **Per-problem threads, moderated.** Like AoPS, but age-gated, no DMs, no open chat, AI-pre-moderation + human review. The thread attaches to the problem, so discussion is always *about the maths*.
- **"Show your approach."** Kids post *how* they solved it (the method/insight), not just the answer; peers upvote elegant solutions. This teaches the core Olympiad lesson: *there are many beautiful paths.*
- **Clans as study groups.** We already have clans — turn them into collaborative problem-solving cells with group puzzles and a shared "solve-together" board.
- **Solve-Together.** One genuinely hard problem the whole community chips away at over a week; partial ideas build on each other.
- **Reputation for *helping*.** The AoPS magic is kids *teaching* kids. Reward great explanations, not just great scores. (A "Mentor-in-training" status.)
- **Medalist solutions of the week + AMAs.** Role models in-app; the human face of maths.
- **Safety architecture as a first-class feature** (Q2/Q4): this is what lets a parent say yes to a kid community. It's not a feature we bolt on — it's *the* feature.

### Q8 — What happens when the questions are exhausted for a grade/topic? What message?

First, reframe: **running out of problems is not a dead end — it's a graduation.** Treat it as one of the best moments in the product, not an error state. When a kid clears a topic/level, never show emptiness or recycle filler. Offer a *fork upward*:

- **🎖 Celebrate first.** "You've solved every problem we have in *Number Theory · Level 4*. That's genuinely rare." A real, shareable mastery moment (parents love this).
- **⬆ Level up.** "You've outgrown this — ready for Level 5 / the next pillar / the IOQM track?" Pull them up the ladder.
- **🔥 Go deeper.** A hand-picked set of *boss problems* in that topic + the Library book for it. Depth, not repetition.
- **👥 Go social.** "Discuss the hardest ones with peers" / "this week's Solve-Together is in this topic."
- **✍️ Create.** "You've solved them all — now *make* one for the community." Problem-authoring (curated) — which also **feeds our content pipeline** (Q9).
- **🧑‍🏫 Go human.** Unlock a mentor/faculty challenge set or a live session (Vedantu's edge).
- **🔁 Spaced return.** "We'll bring the trickiest ones back next week to keep you sharp" — retrieval practice, honestly framed.

And critically: **exhaustion is a product signal, not just a UX state.** Every "you've finished this" is the app telling *us* exactly where to author next. Wire it to a dashboard. The kid feels pulled forward; we get a live content-gap radar. The one rule: *never* fake it with repeated or low-quality filler — that breaks the trust moat instantly.

### Q9 — How does it all come together into the easiest, best maths app in the world?

**One app, one identity ("young mathematician"), one progression, one economy — three rooms:**

```
   ┌──────────────────────────────────────────────────────────────┐
   │   WONDER   —  fall in love     →  TRAIN  — get good           │
   │   (any kid)                       (gifted + everyone)         │
   │                     ↘            ↙                            │
   │                       BELONG  — grow together                 │
   │                       (community + mentors)                   │
   └──────────────────────────────────────────────────────────────┘
        all tied by ONE pathway (Academic Height → IOQM→IMO)
        and ONE coach-in-your-pocket that knows what you need next
```

- **WONDER** (fall in love): the daily beautiful problem, magic tricks, the visual playground. Low-stakes, all ages, *the front door*.
- **TRAIN** (get good): adaptive practice for fluency **+** the *Thinking Gym* for depth **+** the visible IOQM→IMO pathway **+** the Library. (Re-tuned so the Olympiad track rewards struggle and elegance, not speed.)
- **BELONG** (grow together): kid-safe per-problem discussion, clans/study-groups, contests & leagues, medalist mentors, and problem-authoring.

The glue is a **"coach in your pocket"** — a single, gentle intelligence that decides, today, whether you need a moment of wonder, a hard problem, a hint, a peer discussion, a level-up, or a human. It replaces our current "next question" logic with "next *right thing for this kid*."

The north star is not "drill more MCQs." It's **"make young mathematicians"** — measured by depth, joy, and real contest progression, with correctness and safety as non-negotiables.

---

## 3 · The product blueprint (the signature experiences)

Six experiences carry the whole vision. Each one is buildable on what we already have.

1. **Problem of the Day (Wonder).** One beautiful, surprising problem for *every* level, every day. A reveal, a "why this is beautiful," and a discussion thread. This is the daily habit and the front door for any kid. *(Reuses: contest engine + content + a new "wonder" content tag.)*

2. **The Thinking Gym (Depth).** The flagship. One hard problem. A **hint ladder** (nudge → strategy → worked step) so being stuck is safe. When you solve it — or give up honourably — you **see 2–3 elegant solutions side by side**, plus the best community solution, then *"now explain it in your own words."* This is the single feature that converts us from drill to thinking. *(Reuses: Library solutions + new multi-solution content + the discussion layer.)*

3. **The Path (Pathway).** A visual mountain from school maths → L-levels → **IOQM → RMO → INMO → IMO**, showing where the kid is, what they've mastered, and the next foothold — coached. *(Reuses: levels + Academic Height + adaptive state.)*

4. **The Commons (Belonging).** Kid-safe, moderated, per-problem discussion + "show your approach" + clans-as-study-groups + Solve-Together + medalist solutions. Reputation for *helping*. *(Reuses: clans + new moderated threads + safety stack.)*

5. **Make-a-Problem (Creation).** When a kid exhausts a topic, they can *author* a problem (guided, curated) for the community — solving the content-exhaustion problem and growing our bank with human-validated content. *(New, but small; curation reuses our QA harness.)*

6. **Ask a Mathematician (Human).** At the moment of being genuinely stuck, or at a mastery milestone, connect to Vedantu faculty/mentors — annotated solutions, a live nudge, a challenge set. Our unfair advantage, productised. *(Reuses: Vedantu faculty; new connect layer.)*

Plus the **Parent View**: plain-language growth, the pathway, mastery certificates, and full safety controls.

---

## 4 · The questions *we* now have to answer (the co-founder's list)

A good co-founder's job is to ask the questions that decide everything. Here are the seven I'd put on the table:

1. **Wedge: gifted-Olympiad first, or "any kid" first?** My recommendation: **win the gifted-Olympiad niche as the wedge** — it's underserved, defensible, premium, and exactly where Vedantu is credible. Then broaden to "any kid" with the Wonder layer once the depth + community moat is real. (Doing "everyone" first dilutes the moat.)
2. **Community: build, partner, or phase?** Kid-safe social is the highest-value *and* highest-liability feature. It's the moat — but it must be phased in with safety architecture first. Do we have the appetite and the moderation muscle?
3. **Human-in-the-loop economics.** "Ask a Mathematician" is our edge, but faculty time doesn't scale linearly. Where does it sit — premium tier, milestone unlock, async-annotated-solutions vs. live?
4. **Reasoning capture.** Do we invest in capturing real mathematical *thinking* (hard: free-response, proof sketches, "show your approach") or stay answer-based (limited)? For Olympiad, I think we *must* — even if it starts as "post your approach" text the community grades.
5. **Content engine mix.** Human-authored (correct, slow) vs. community-generated (scalable, needs moderation) vs. AI-assisted (risky). My take: human-authored *spine*, community-authored *volume* (curated through our QA harness), AI only as a *tool for humans*, never the author.
6. **Re-aim the engine.** Do we re-tune the adaptive objective on the Olympiad track from "next-right-answer" to "depth & struggle & elegance"? (I believe yes — it's the core insight of this doc.)
7. **Mission vs. monetisation line.** Free wonder for all; premium depth, mentorship, and creation. Where exactly is the line, and does the free tier stay generous enough to *make the movement*?

---

## 5 · The road to the masterpiece (phased, build-on-what-we-have)

**Phase 1 — Find the soul (re-aim, don't rebuild).**
Ship *Problem of the Day* and *The Thinking Gym* (hint ladder + multiple solutions). Re-tune the Olympiad track to reward struggle, not speed. Add the celebrate-and-fork "you've mastered this" moment. *Outcome: we stop being a drill app and become a thinking app.* Mostly content + UX on the existing engine.

**Phase 2 — Build belonging (the moat).**
Kid-safe per-problem discussion + "show your approach" + clans-as-study-groups + medalist solution of the week. Safety architecture as a first-class system. *Outcome: the thing AoPS has and no one safe-for-kids has.*

**Phase 3 — The pathway + the human edge.**
The visual IOQM→IMO Path, mastery certificates for parents, and "Ask a Mathematician" with Vedantu faculty. *Outcome: the map in your pocket + the human moment money can't fake.*

**Phase 4 — Creation + the movement.**
Make-a-Problem authoring → curated community content (solves exhaustion forever) and broaden the Wonder layer so *any* kid, not just the gifted, falls in love. *Outcome: a self-feeding content engine and a movement, not a tool.*

---

## The one-line version

> Everyone else owns one corner — AoPS owns content + community but it's intimidating; Brilliant owns delight but not depth; Mathigon owns wonder but not the system; Vedantu owns faculty but not a product. **We assemble all of it into one safe, delightful, mobile-first place where a stuck kid is never alone, a hard problem is never a dead end, and every child — gifted or not — gets to feel the click of figuring it out.** That's how you build the best maths learning app in the world. And the moat is the boring, beautiful thing we already do better than anyone: **the maths is actually correct.**

*Next to this document is an interactive prototype of the two experiences that carry the whole vision — Problem of the Day and The Thinking Gym — so you can feel it, not just read it.*
