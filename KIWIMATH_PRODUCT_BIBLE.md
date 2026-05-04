# KIWIMATH — Product Bible

> "The 35,000ft view of what we're building, why, and how it all connects."

**Version:** 1.0 | **Date:** May 2, 2026 | **Author:** Anand Prakash + Claude

---

## PART 1: HEAD OF PRODUCT — The Vision

### What Is Kiwimath?

Kiwimath is a K-6 adaptive mathematics learning app that gives every child a personal math tutor — one that knows exactly where they are, what they've forgotten, what they're ready for next, and how fast they're growing.

### Who Is It For?

| User | Role | Need |
|------|------|------|
| **Child (age 5-12)** | Learner | Fun, rewarding practice at exactly the right level |
| **Parent** | Buyer + Monitor | Know if my child is on track, where they struggle, confidence they're improving |
| **School/Tutor** | Distribution | Supplement classroom teaching with personalized practice |

### The North Star Metric

**Weekly active learners who demonstrate measurable skill growth.**

Not sessions played. Not questions answered. Actual theta movement (ability growth) confirmed over time.

### What Makes Kiwimath Different (The Moat)

| Competitor | Their approach | Our edge |
|-----------|--------------|----------|
| Cuemath/Byjus | Video lessons + worksheets | We're pure adaptive practice — no passive watching |
| Khan Academy | Topic-locked practice | We pull from ALL curricula simultaneously, cross-pollinate skills |
| Photomath | Answer-checking | We BUILD understanding through scaffolded practice |
| Kumon | Fixed worksheets | We adapt in real-time, never too easy or too hard |

**The REAL moat is NOT the engine. It's:**

1. **Content quality** — Every question is mathematically correct, pedagogically sound, with visuals where needed
2. **Explanation quality** — Hints that scaffold understanding, "Why?" that teaches the misconception
3. **Parent trust** — Clear, honest communication about where their child actually is
4. **Visible child delight** — The child feels "I can win. This is fun. I'm getting smarter."

The adaptive engine (IRT + FSRS + skill graph) is the delivery mechanism. But if we deliver bad content faster, we lose. The engine is necessary but not sufficient.

**The engine provides:**
- 21,330 questions across 5 curricula (Olympiad, CBSE/NCERT, ICSE, Cambridge Primary, Singapore)
- 37-node prerequisite skill graph
- Per-skill IRT tracking
- FSRS forgetting curves
- Cross-skill transfer

**But the moat is the CONTENT passing through the engine.**
→ See `CONTENT_QUALITY_GATE.md` for the 7-gate quality framework.

### Product Positioning

```
"Kiwimath is the smartest math practice app for Indian kids —
 it adapts to your child's exact level, draws from world-class curricula,
 and shows you exactly how they're growing."
```

### The User Promise

| To the child | To the parent |
|-------------|---------------|
| "Every session is just right for you" | "You'll see exactly where your child stands" |
| "You'll never be stuck or bored" | "Skills are retained, not just passed" |
| "Math feels like a game — I can win" | "Clear weekly progress you can track" |

### Product Danger Zone

> "The app may become too engineering-led."

IRT, FSRS, theta, transfer coefficients are powerful internally — but the child and parent should NEVER feel the complexity.

- **Child should feel:** "This is fun. I can win."
- **Parent should feel:** "I understand exactly what is happening."

If we ever catch ourselves explaining theta to a parent, we've failed.

### Business Model (Designed, Not Yet Live)

- **Free tier:** 1 topic (Counting), limited sessions/day
- **Premium ($):** All topics, all curricula, unlimited practice, parent dashboard
- **Institutional ($$):** School/tutor bulk licensing with class-level analytics

---

## PART 2: HEAD OF DESIGN — All Screens & Flows

### Information Architecture

```
APP
├── Onboarding (one-time)
│   ├── Welcome splash
│   ├── Child's name
│   ├── Curriculum picker (NCERT / ICSE / Cambridge Primary / Olympiad-only)
│   ├── Grade picker (1-6)
│   ├── Diagnostic test (10 questions)
│   └── Learning plan reveal
│
├── Main App (3-tab bottom nav)
│   ├── 🏠 HOME
│   │   ├── Header: "Hi [Name]!" + Grade badge (TAPPABLE to change grade)
│   │   ├── Smart Practice hero card (→ unified adaptive session)
│   │   ├── [Olympiad | Curriculum] segment toggle
│   │   ├── IF Olympiad: Topic cards with levels (Counting Lv4, Arithmetic Lv2...)
│   │   ├── IF Curriculum: Chapter list with progress (Ch1: Numbers — 80% done)
│   │   └── Badge/streak section
│   │
│   ├── 🛤️ PATH (Learning Journey)
│   │   ├── [Chapters | Olympiad] toggle
│   │   ├── Chapters: sequential chapter list with mastery dots
│   │   ├── Olympiad: 8-topic grid with level indicators
│   │   └── Overall mastery: "X of 37 skills mastered"
│   │
│   └── 👨‍👩‍👧 PARENT (Behind parental gate — PIN, not math problem)
│       ├── Header: "[Name] · Grade N · CBSE" (shows context!)
│       ├── HERO: Academic Height (below/at/above grade level) ← NOT accuracy!
│       ├── Growth this week (+X KiwiScore)
│       ├── Skills mastered (X/37)
│       ├── Retention rate (FSRS pass %)
│       ├── Accuracy (supporting metric, not hero)
│       ├── Strengths + Needs practice
│       ├── Weekly report card
│       └── Settings (change grade, curriculum, notifications)
│
├── Question Flow (from any entry point)
│   ├── Loading (fetch questions)
│   ├── Question screen (visual + stem + hints + options)
│   ├── Correct answer (green bar + coins + continue)
│   ├── Wrong answer (orange bar + "Why?" + got it)
│   ├── Why? bottom sheet (wrong vs correct + explanation)
│   └── Session complete → Celebration → POST results
│
└── Settings / Profile
    ├── Change grade
    ├── Change curriculum
    ├── Change child name
    └── Reset diagnostic
```

### Screen-to-Screen Flow Map

```
┌──────────────────────────────────────────────────────────────────┐
│                        ENTRY POINTS                               │
└───────┬──────────────────┬────────────────────┬──────────────────┘
        │                  │                    │
        ▼                  ▼                    ▼
   [Smart Practice]   [Topic Card tap]    [Chapter tap]
        │                  │                    │
        ▼                  ▼                    ▼
   GET /session/       GET /questions/     GET /questions/
   unified             next (topic)        next (chapter+curriculum)
        │                  │                    │
        └──────────────────┴────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  QUESTION LOOP  │ ← 10 questions
                  │                 │
                  │  Show Q → Wait  │
                  │  Check → Result │
                  │  Correct/Wrong  │
                  │  → Next Q       │
                  └────────┬────────┘
                           │
                           ▼ (after last Q)
                  ┌─────────────────┐
                  │  POST results   │ → /session/unified/complete
                  │  (skill thetas  │
                  │   updated,      │
                  │   FSRS scheduled│
                  │   mastery check)│
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  CELEBRATION    │
                  │  XP + coins +   │
                  │  streak + badge │
                  └────────┬────────┘
                           │
                           ▼
                    Back to HOME
                    (refreshes mastery)
```

### Grade Change Flow (PROPOSED — currently missing)

```
Option A (Recommended): Tappable grade badge in home header
┌──────────────────────────────────┐
│ Hi Arjun! [Grade 3 ▼] 🔥 5-day  │  ← Tap "Grade 3" opens picker
└──────────────────────────────────┘
         │
         ▼
   ┌──────────────┐
   │  Grade 1     │
   │  Grade 2     │
   │ ▸Grade 3◂   │  ← Bottom sheet with grade list
   │  Grade 4     │
   │  Grade 5     │
   └──────────────┘
         │ Select
         ▼
   Reloads home with new grade content
   (No re-onboarding needed)
```

### Design Principles

1. **The child should never see an ID** — All labels human-readable
2. **3-tap rule** — Any feature reachable in ≤3 taps from home
3. **Parent gate protects settings** — Kids can't accidentally change grade
4. **Progress should feel VISUAL** — Rings, bars, dots, not numbers
5. **Every session ends with celebration** — Even bad sessions celebrate effort

---

## PART 3: HEAD OF CURRICULUM — Learning Outcomes & Measurement

### What Does a Student Learn?

Kiwimath covers K-6 mathematics across 5 domains and 37 specific skills:

| Domain | Skills | Example |
|--------|--------|---------|
| Numbers & Counting | 8 skills | Number sense, place value, comparison, ordering |
| Arithmetic | 10 skills | Addition, subtraction, multiplication, division, order of ops |
| Fractions & Decimals | 6 skills | Equivalent fractions, decimal operations, percentages |
| Geometry & Spatial | 7 skills | Shapes, angles, symmetry, coordinates, area/perimeter |
| Measurement & Data | 6 skills | Units, time, money, data interpretation, statistics |

### What "Grade Level" Means

Each grade has a theta (ability) range that defines "on track":

| Grade | Expected θ range | KiwiScore range | What it means |
|-------|-----------------|-----------------|---------------|
| Grade 1 | -2.0 to -1.0 | 140-170 | Basic counting, single-digit arithmetic |
| Grade 2 | -1.0 to -0.2 | 170-194 | Two-digit arithmetic, basic geometry |
| Grade 3 | -0.2 to +0.5 | 194-215 | Multiplication, fractions intro, measurement |
| Grade 4 | +0.5 to +1.2 | 215-236 | Multi-digit operations, fraction arithmetic |
| Grade 5 | +1.2 to +1.8 | 236-254 | Decimals, ratios, complex geometry |
| Grade 6 | +1.8 to +2.5 | 254-275 | Pre-algebra, statistics, advanced problem-solving |

### Academic Height — Where Is My Child?

Every student's position is described relative to their enrolled grade:

```
                    ┌─────────────────────────────┐
  ABOVE GRADE       │  θ > grade_max              │ → Olympiad/stretch content
  (Accelerated)     │  "Your child is ahead!"     │    Next grade preview
                    ├─────────────────────────────┤
  AT GRADE LEVEL    │  grade_min ≤ θ ≤ grade_max  │ → Standard curriculum
  (On Track)        │  "Right where they should be"│    Progressive mastery
                    ├─────────────────────────────┤
  BELOW GRADE       │  θ < grade_min              │ → Remedial scaffolding
  (Needs Support)   │  "Building foundations"      │    Previous grade content
                    └─────────────────────────────┘
```

**Parent messaging:**
- Never says "behind" or "failing" — always "building foundations"
- Shows growth trajectory: "Up 12 points this month"
- Compares to self (last week), never to other kids

### Sustained Mastery — When Is a Skill "Learned"?

A skill is mastered only when ALL of these are true:
1. ≥80% accuracy on that skill
2. Across ≥5 items
3. Over ≥2 non-consecutive sessions (prevents lucky streaks)
4. Retained on FSRS review (not forgotten after 7+ days)

This is stricter than competitors. A kid who "passes" a topic in one session hasn't mastered it — they've demonstrated short-term recall. True mastery requires durability.

### Year-Long Pacing

A school year is ~40 weeks. A typical grade has:
- 5-8 chapters (curriculum path)
- 8 topic areas (Olympiad path)
- 37 skills to master across the year

**Healthy pace:**

| Metric | Target per week | Per month | Per year |
|--------|----------------|-----------|----------|
| Sessions | 4-5 (one/day weekdays) | 16-20 | ~180 |
| Questions answered | 40-50 | 160-200 | ~1,800 |
| New skills introduced | 1-2 | 4-6 | 37 total |
| Skills mastered | 0.5-1 | 2-4 | 25-37 |
| Review sessions | 1-2/week | 4-8 | ~80 |

**Pacing algorithm:**
- If kid is ahead of pace → introduce stretch/olympiad content
- If kid is behind pace → reduce new skill intros, focus on consolidation
- If kid is way behind → flag to parent, suggest more sessions, add remedial

### Progress Report Design

**Weekly report (to parent):**
```
📊 This Week for [Name]:
• Practiced 5 days (streak: 12 days!)
• Answered 47 questions (38 correct — 81%)
• NEW MASTERY: Subtraction with borrowing ✓
• REVIEWING: Multiplication tables (next review: Wed)
• ACADEMIC HEIGHT: On track for Grade 3 (KiwiScore: 208, +4 from last week)
• NEXT FOCUS: Fractions — starting equivalent fractions
```

**Monthly report:**
```
📈 [Name]'s Monthly Progress:
• KiwiScore: 196 → 208 (+12 points, above average growth)
• Skills mastered this month: 3 (cumulative: 18/37)
• Strongest: Arithmetic (95% accuracy)
• Needs work: Geometry (62% accuracy)
• On pace for: Completing Grade 3 curriculum by March
• Recommendation: 10 more minutes/day on spatial reasoning
```

### Diagnostic Test — What It Tells Parents

**IMPORTANT: A 10-question diagnostic cannot reliably place a child across 37 skills.**

It provides a first estimate only. Academic Height confidence builds over time:

| Stage | When | Confidence | Parent sees |
|-------|------|-----------|-------------|
| Stage 1 | After diagnostic (10 Qs) | Low | "Initial estimate: ~Grade 2.4" |
| Stage 2 | After 3-5 sessions | Medium | "Estimate: Grade 2.6 (becoming clearer)" |
| Stage 3 | After 10+ sessions | High | "Academic Height: Grade 2.8 ✓ Confirmed" |

**What the diagnostic establishes (with low confidence):**
1. **Approximate starting theta** — rough GPS pin
2. **Obvious skill gaps** — clearly missing prerequisites
3. **Response pattern signals** — speed vs accuracy preference

**What it CANNOT do:**
- Precisely locate a child across all 37 skills (too few data points)
- Definitively say "your child is above/below grade level"
- Replace the first 5 sessions of calibration

**Parent messaging during low-confidence phase:**
- "We're still getting to know [Name]'s math level"
- "After a few more sessions, we'll have a clear picture"
- Never show a definitive "Academic Height" until confidence is High

The diagnostic is NOT a judgment. It's a GPS pin — "approximately here. Let's explore."

**Technical: If confidence interval of theta remains >0.5 after 10 Qs, extend diagnostic dynamically to 15-20 Qs.**

---

## PART 4: INSTRUCTIONAL DESIGNER — How Content Flows

### What Is "Smart Practice"?

Smart Practice is the primary session mode. It's NOT a random quiz. It's a carefully orchestrated learning experience:

```
SESSION STRUCTURE (10 questions):

[Slot 1-2: WARMUP]
  → Skills already near-mastered (P(correct) > 0.85)
  → Purpose: Build confidence, activate prior knowledge
  → Curriculum: Mix of sources (usually the child's enrolled curriculum)

[Slot 3-6: CORE SKILL PRACTICE]
  → Target skill at ZPD (P(correct) ∈ [0.60, 0.85])
  → Purpose: The actual learning happens here
  → Progressive difficulty within these 4 questions
  → Mid-session adjustment if kid is struggling or soaring

[Slot 7-8: STRETCH]
  → Slightly above current level (P(correct) ∈ [0.45, 0.65])
  → Purpose: Preview upcoming skills, test readiness
  → Often from Olympiad or higher-grade pool

[Slot 9-10: REVIEW]
  → FSRS-scheduled review of previously mastered skills
  → Purpose: Prevent forgetting, confirm retention
  → If no reviews due: revisit recent mistakes
```

### Why This Structure Works (Research)

- **Warmup reduces anxiety** — Bjork (2011): "desirable difficulties" require a warmed-up cognitive system
- **ZPD targeting** — Vygotsky + modern IRT: learning happens in the zone where challenge meets capability
- **Interleaving** — Rohrer (2012): mixing skill types in one session → 43% better retention than blocked practice
- **Spaced review at session end** — Ebbinghaus + FSRS: reviewing just before forgetting maximizes retention efficiency

### Content Flow by Entry Point

| Entry | What happens | Session shape |
|-------|-------------|---------------|
| **Smart Practice** (home hero) | Full adaptive session, cross-curriculum | [2 warmup] [4 core] [2 stretch] [2 review] |
| **Topic card tap** (Olympiad) | Topic-focused, IRT-adaptive difficulty | 10 questions, same topic, progressive difficulty |
| **Chapter tap** (Curriculum) | Chapter-focused, curriculum-aligned | 10 questions from that chapter, IRT-adaptive |
| **Review notification** | FSRS-triggered, mix of due skills | 5-10 review questions across multiple skills |

### Hint Pedagogy

When a child is stuck, hints scaffold understanding (never give the answer):

```
LEVEL 1: "Think about what happens when you put 3 groups of 4 together..."
          (Reframe the problem, activate relevant schema)

LEVEL 2: "3 × 4 means 4 + 4 + 4. Can you add those up?"
          (Break into sub-steps, reduce cognitive load)

LEVEL 3: "4 + 4 = 8, and 8 + 4 = ?"
          (Nearly complete — one final step for the child to do)
```

Hints are NEVER: "The answer is 12" or "Choose option B."

### Wrong Answer Diagnostics

Every distractor maps to a specific misconception:

```
Question: What is 43 - 17?
Correct: 26

Distractor 36 → "You subtracted the smaller digit from the larger in each column
                 (7-3=4, 4-1=3 → 34... wait that's 34). Check the ones column."
Distractor 24 → "Small arithmetic slip in borrowing. When you borrow, the tens
                 digit decreases by 1."
Distractor 34 → "You may have subtracted each column independently without borrowing."
```

This means the "Why?" explanation is always SPECIFIC to what the child chose — not generic.

### Learning Outcome Measurement

| Metric | What it measures | How we compute it |
|--------|-----------------|-------------------|
| **Theta (θ)** | Raw ability on IRT scale | EAP estimation from all responses |
| **KiwiScore** | Parent-friendly ability number | 200 + (θ × 30) |
| **Skill mastery %** | How many of 37 skills are mastered | Count where sustained mastery = true |
| **Growth rate** | How fast theta is increasing | Δθ per week, rolling 4-week average |
| **Retention rate** | How well old skills are remembered | % of FSRS reviews passed |
| **Academic height** | Where child is vs grade expectation | θ mapped to grade range table |

---

## PART 5: PROGRAM MANAGER — How It All Fits Together

### Current State (May 2, 2026)

| Component | Status | Notes |
|-----------|--------|-------|
| Backend (FastAPI + Cloud Run) | ✅ Deployed | asia-south1, all endpoints live |
| Content (21,330 questions) | ✅ Complete | 5 curricula, all grades |
| Adaptive engine (IRT + FSRS) | ✅ Built | Per-skill theta, forgetting curves, transfer |
| Flutter app | ✅ Functional | All screens, all flows |
| Parent dashboard | ✅ Built | Behind parental gate |
| Gamification (XP, coins, badges) | ✅ Built | Dual currency system |
| Onboarding | ✅ Built | Name → Curriculum → Grade → Diagnostic → Plan |
| Play Store listing | ✅ Ready | Description, screenshots, assets |
| **Grade change post-onboarding** | ❌ Missing | Can't change grade after initial setup |
| **Home screen polish** | ❌ Needs fix | Raw IDs showing, no Olympiad/Curriculum toggle |
| **Parent context** | ❌ Partial | Doesn't show which grade/curriculum is active |
| **Academic height messaging** | ❌ Not built | Backend has theta ranges but no parent-facing message |

### Dependencies Map

```
Content (21,330 Qs)
    ↓
Skill Mapper (37 nodes) → maps every Q to skill graph
    ↓
Adaptive Engine ← takes student theta + selects questions
    ↓
API Layer (FastAPI) ← serves to Flutter
    ↓
Flutter App ← renders to child + parent
    ↓
Firestore ← persists all state (abilities, schedules, progress)
    ↓
Parent Reports ← aggregates into human-readable insights
```

### What Ships Next (Priority Order)

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P0 | Fix grade change (add picker) | 1 day | Unblocks all parents |
| P0 | Fix home screen labels (full names) | 0.5 day | Looks professional |
| P1 | Add Olympiad/Curriculum toggle to Home | 1 day | Clean navigation |
| P1 | Academic height in Parent tab | 1 day | Key differentiator |
| P2 | Weekly report push notification | 2 days | Retention driver |
| P2 | Pacing alerts ("your child is behind/ahead") | 1 day | Parent engagement |
| P3 | School/class mode | 5 days | B2B revenue |
| P3 | Premium paywall activation | 2 days | Monetization |

### Risks

| Risk | Mitigation |
|------|-----------|
| Content quality (AI-generated Qs may have errors) | QA pipeline, user flagging, CMS approval flow |
| Cold start (new user has no data) | Diagnostic test provides initial calibration |
| Over-adaptation (kid games the system) | Anti-cheat: response time + pattern detection |
| Parent disengagement | Weekly digest, push notifications, clear "so what" messaging |
| Theta stagnation (kid practices but doesn't grow) | Mid-session adjustment, difficulty push, parent alert |

---

## PART 6: HEAD OF ENGINEERING — Architecture & Data Flow

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUTTER APP (Client)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │Home Screen│  │Question  │  │Celebration│  │Parent Dash   │   │
│  │(sessions)│  │Screen V2 │  │Screen     │  │(reports)     │   │
│  └─────┬────┘  └────┬─────┘  └─────┬────┘  └──────┬───────┘   │
└────────┼─────────────┼──────────────┼───────────────┼───────────┘
         │             │              │               │
         ▼             ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Cloud Run)                    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API LAYER (questions_v2.py)            │    │
│  │  GET /session/unified  POST /session/unified/complete    │    │
│  │  GET /questions/next   POST /answer/check                │    │
│  │  GET /skills/progress  GET /parent/weekly-report         │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               │                                   │
│  ┌────────────────────────────┼────────────────────────────┐    │
│  │              SERVICE LAYER                                │    │
│  │                                                           │    │
│  │  ┌──────────────────┐  ┌──────────────────────────┐    │    │
│  │  │ Content Store V2  │  │ Unified Session Planner   │    │    │
│  │  │ (21,330 questions)│  │ (warmup/core/stretch/rev) │    │    │
│  │  └──────────────────┘  └──────────────────────────┘    │    │
│  │                                                           │    │
│  │  ┌──────────────────┐  ┌──────────────────────────┐    │    │
│  │  │ Adaptive Engine   │  │ Skill Ability Store       │    │    │
│  │  │ (IRT 3PL + EAP)  │  │ (37 thetas per student)  │    │    │
│  │  └──────────────────┘  └──────────────────────────┘    │    │
│  │                                                           │    │
│  │  ┌──────────────────┐  ┌──────────────────────────┐    │    │
│  │  │ FSRS Review Engine│  │ Gamification Engine       │    │    │
│  │  │ (forgetting curve)│  │ (XP, coins, badges)      │    │    │
│  │  └──────────────────┘  └──────────────────────────┘    │    │
│  │                                                           │    │
│  │  ┌──────────────────┐  ┌──────────────────────────┐    │    │
│  │  │ Skill Mapper      │  │ Path Engine (37-node DAG)│    │    │
│  │  │ (Q → skill node) │  │ (prerequisites)          │    │    │
│  │  └──────────────────┘  └──────────────────────────┘    │    │
│  └───────────────────────────────────────────────────────────┘    │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FIRESTORE (Persistence)                     │
│                                                                   │
│  users/{uid}/                                                    │
│    ├── profile          (name, grade, curriculum, onboarded_at)  │
│    ├── abilities/{domain}    (domain-level theta, 5 docs)        │
│    ├── skill_abilities/{skill_id}  (per-skill theta, 37 docs)   │
│    ├── review_schedule/{skill_id}  (FSRS state per skill)        │
│    ├── gamification     (XP, coins, gems, badges, streaks)       │
│    ├── question_history/{qid}  (answered questions log)          │
│    └── session_summaries/{sid} (per-session parent summaries)    │
│                                                                   │
│  content-v2/           (bundled at Docker build time, not in FS) │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow: One Question Answered

```
1. Child taps option → Flutter sends POST /answer/check
   Body: { question_id, selected_answer, user_id, time_taken_ms, hints_used }

2. Backend:
   a. Looks up question → gets IRT params (a, b, c) + skill_id
   b. Gets current skill theta from skill_ability_store
   c. Computes: was answer correct? P(correct) given theta?
   d. Updates theta: θ_new = θ_old + time_weighted_delta
   e. Checks mastery: ≥80% over ≥5 items over ≥2 sessions?
   f. If newly mastered → schedule FSRS review, apply transfer boost
   g. Computes rewards: XP + coins based on difficulty × streak
   h. Returns: { correct, xp, coins, next_difficulty, feedback, new_badges }

3. Flutter:
   a. Shows correct/wrong animation
   b. Updates local XP/coins/streak
   c. Records result in _sessionResults list

4. After last question → Flutter POSTs _sessionResults to /session/unified/complete

5. Backend generates ParentSummary:
   { accuracy, skills_practiced, new_masteries, progress_message, next_focus }
```

### Key Engineering Decisions

| Decision | Rationale |
|----------|-----------|
| FastAPI (not Firebase Functions) | Need IRT computation, numpy, complex routing — too heavy for serverless |
| Cloud Run (not GKE) | Auto-scaling, pay-per-use, simple Docker deploy |
| Content bundled in Docker image | No runtime content loading latency; rebuild on content changes |
| In-memory + Firestore hybrid | Fast reads from memory, async persist to Firestore |
| Per-skill theta (37) not per-domain (5) | Research shows fine-grained tracking → better question selection |
| FSRS not fixed-interval review | Adaptive intervals → 2.5x better retention efficiency |
| Flutter (not React Native) | Single codebase iOS+Android, smooth animations, Dart performance |

### API Contract Summary

| Endpoint | Method | Purpose | Called when |
|----------|--------|---------|------------|
| `/v2/session/unified` | GET | Build adaptive session | "Smart Practice" tap |
| `/v2/session/unified/complete` | POST | Submit session results | Session ends |
| `/v2/questions/next` | GET | Single adaptive question | Topic/chapter practice |
| `/v2/answer/check` | POST | Check + update theta | Every answer |
| `/v2/skills/progress` | GET | 37-skill dashboard | Path tab load |
| `/v2/skills/review-status` | GET | FSRS review summary | Parent tab |
| `/v2/parent/weekly-report` | GET | Weekly digest | Parent tab |
| `/v2/chapters` | GET | Curriculum chapter list | Home (curriculum mode) |
| `/v2/mastery/overview` | GET | Quick mastery summary | Home refresh |
| `/v2/student/profile` | POST | Update grade/curriculum | Settings |

---

## APPENDIX: Definitions & Glossary

| Term | Definition |
|------|-----------|
| **θ (theta)** | Ability estimate on IRT scale. Range: -3 to +3. Higher = more skilled. |
| **KiwiScore** | 200 + (θ × 30). Parent-friendly number. "Your child's KiwiScore is 215." |
| **Academic Height** | Where θ falls relative to grade-expected range. |
| **ZPD** | Zone of Proximal Development. Where P(correct) ∈ [0.60, 0.85]. |
| **FSRS** | Free Spaced Repetition Scheduler. Computes optimal review timing per skill. |
| **Sustained Mastery** | ≥80% accuracy, ≥5 items, ≥2 non-consecutive sessions, passed FSRS review. |
| **Skill Graph** | 37-node prerequisite DAG. addition_basic → addition_2digit → multi_step. |
| **Transfer Coefficient** | When skill A is mastered, dependent skill B gets a theta boost (0.1-0.3). |
| **Smart Practice** | Cross-curriculum adaptive session: warmup → core → stretch → review. |
| **Warmup** | First 2 questions. High success probability. Confidence builder. |
| **Core** | Middle 4 questions. ZPD-targeted. Where learning happens. |
| **Stretch** | Questions 7-8. Slightly beyond current ability. Preview of next level. |
| **Review** | Last 2 questions. FSRS-scheduled skills that need retention check. |
| **Remedial** | Content from lower grade, for students below grade-level range. |
| **Parental Gate** | PIN or biometric lock. NOT a math problem (Olympiad kids will solve it). |

---

## PART 7: KNOWN HOLES & REQUIRED FIXES

### Strategic Holes

| Hole | Impact | Fix |
|------|--------|-----|
| **Parental gate is a math problem** | Olympiad-track 8-year-olds will crack it | Switch to 4-digit PIN or device biometrics |
| **No offline mode** | India has spotty connectivity; session fails mid-question | Download 10-Q batch on session start, sync results on complete |
| **Free tier too restrictive** | Parents can't see Academic Height growth before paying | Give 7-day full trial, then limit to 1 session/day (not 1 topic) |
| **"IGCSE" is wrong** | IGCSE is Grade 9-10, not K-6 | Rename to "Cambridge Primary" everywhere |
| **Olympiad as separate track** | Creates "dual progress" anxiety | Integrate Olympiad as "Boss Levels" within the curriculum path |

### Pedagogical Holes

| Hole | Impact | Fix |
|------|--------|-----|
| **10-Q diagnostic too weak** | Can't reliably place across 37 skills | Staged confidence: Low → Medium → High over 10+ sessions |
| **Theta stagnation unhandled** | Kid practices but doesn't grow; parent loses trust | After 3+ stuck sessions: parent alert + remedial path + "Help Me" flag |
| **No human intervention trigger** | AI can't solve everything | When kid is stuck across 3+ sessions on same skill: suggest tutor/parent help |
| **Content quality is biggest gap** | Adaptive engine delivers bad content faster | 7-Gate quality framework (see `CONTENT_QUALITY_GATE.md`) |

### Technical Holes

| Hole | Impact | Fix |
|------|--------|-----|
| **Review avalanche after vacation** | Kid returns to 10 review-only sessions | Cap reviews at 3/session; "Welcome Back" mode prioritizes fun warmup |
| **Multi-device concurrency** | Two Cloud Run instances → theta conflicts | Session-level locking: one active session per user; latest-timestamp-wins on write |
| **No session buffer** | Each question needs network round-trip | Pre-fetch all 10 questions; buffer answers; sync on completion |
| **Per-question POST dependency** | Stutters on 3G connections | Already partial: /answer/check needed for "correct" feedback. Mitigate: timeout + retry + optimistic UI |

### Design Holes (Missing from current spec)

| Missing | Why it matters |
|---------|---------------|
| **Screen states** (empty, loading, error, locked) | Without these, edge cases look broken |
| **Premium/locked states** | Need to show paywall gracefully |
| **Child vs parent visual language** | Currently same style for both audiences |
| **Component library** | No consistency spec = drift over time |
| **Spacing/grid rules** | Layout varies screen to screen |
| **Typography scale** | Font sizes chosen ad-hoc |
| **Animation specs** | Celebrations feel inconsistent |
| **Question type templates** | Each interaction mode needs its own layout spec |

### Content Quality (The Real Risk)

> "If the questions are AI-generated, repetitive, without visuals, or have wrong hints,
> the adaptive engine will only adapt bad content faster."

Current honest assessment:
- **Hints:** Many are generic ("think carefully") or spoil the answer
- **Visuals:** Grade 1-2 has <50% coverage (should be >80%)
- **Distractors:** Many lack named misconceptions
- **Interaction types:** Over-relies on MCQ when drag-drop/integer would be better
- **Templates:** Fixed once, but needs continuous monitoring

**→ See `CONTENT_QUALITY_GATE.md` for the complete 7-gate framework.**

---

*This document is the single source of truth for what Kiwimath is building.
Return to it whenever we need to zoom out from implementation details.
Updated with product feedback: May 2, 2026.*

