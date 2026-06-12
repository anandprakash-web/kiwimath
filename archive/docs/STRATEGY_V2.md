# KIWIMATH STRATEGY v2 — The Rethink

> "One math product. Own curriculum. Levels replace grades.
> Adapts to the child, not to the school system."

**Date:** May 2, 2026 | **Triggered by:** Anand's academic vision

---

## THE CORE SHIFT

### Before (v1 thinking)
- "Which grade are you in?" → show that grade's content
- NCERT/ICSE/Cambridge are primary navigation
- Grade = Level (1:1 mapping)
- Curriculum drives the experience

### After (v2 thinking)
- "Here's where you actually ARE in math" → adapt from there
- Kiwimath has its OWN curriculum (mapped to all others behind the scenes)
- Levels ≠ Grades. A Grade 3 kid might be Level 2 (behind) or Level 4 (ahead)
- The CHILD's ability drives the experience. School curriculum is a tab, not the core.

### The Iron Rule
> **Grades are important ONLY in the Curriculum tab.**
> Many parents want school alignment — we serve that in a dedicated tab.
> But the core PLAY experience never mentions grades. It's always Levels.
> A child's grade never limits what they can access in the core product.

---

## THE LEVEL SYSTEM

### 6 Levels — The Kiwimath Progression

| Level | Rough age | Math scope | KiwiScore range |
|-------|-----------|-----------|-----------------|
| **Level 1: Explorer** | 5-6 | Counting, basic shapes, single-digit add/sub | 140-170 |
| **Level 2: Builder** | 6-7 | 2-digit arithmetic, intro geometry, patterns | 170-200 |
| **Level 3: Thinker** | 7-8 | Multiplication, fractions intro, measurement | 200-225 |
| **Level 4: Solver** | 8-9 | Multi-digit operations, fraction arithmetic, area | 225-250 |
| **Level 5: Strategist** | 9-10 | Decimals, ratios, complex geometry, data | 250-270 |
| **Level 6: Master** | 10-12 | Pre-algebra, statistics, advanced problem-solving | 270-300 |

**Key insight:** "Rough age" is only a guideline. A sharp 7-year-old can be Level 4. A struggling 10-year-old can be Level 2. The benchmark places them honestly.

### Each Level Has 8-10 Topics

```
LEVEL 3: THINKER (example)
├── Topic 1: Multiplication Foundations (× tables, area model)
├── Topic 2: Division as Sharing (equal groups, remainders)
├── Topic 3: Fractions — What Are They? (halves, quarters, thirds)
├── Topic 4: Fractions — Comparing & Ordering
├── Topic 5: Measurement — Length & Perimeter
├── Topic 6: Measurement — Mass & Capacity
├── Topic 7: Time — Reading, Elapsed, Calendar
├── Topic 8: Geometry — Angles & Turns
├── Topic 9: Data — Reading Graphs & Tables
├── Topic 10: Problem Solving — Multi-Step (capstone)
```

### Behind-the-Scenes Mapping (invisible to user)

Every question carries metadata:

```json
{
  "question_id": "KM-L3-T1-047",
  "level": 3,
  "topic": "multiplication_foundations",
  "irt": { "a": 1.2, "b": 0.3, "c": 0.15 },
  "skill_node": "multiplication_facts",
  "curriculum_map": {
    "cbse": { "grade": 3, "chapter": "Multiplication", "ncf_code": "M3.4" },
    "icse": { "grade": 3, "chapter": "Multiplication & Division" },
    "cambridge": { "grade": 3, "unit": "3Nc.04" },
    "singapore": { "grade": 3, "topic": "Whole Numbers — Multiplication" }
  },
  "country_context": {
    "india": { "currency": "₹", "names": ["Ria", "Arjun"], "units": "km/kg" },
    "singapore": { "currency": "$", "names": ["Wei", "Mei"], "units": "km/kg" },
    "global": { "currency": "coins", "names": ["Alex", "Sam"], "units": "km/kg" }
  },
  "interaction_mode": "integer_input",
  "visual_requirement": "essential",       // "essential" | "optional" | "none"
  "visual_type": "array_model_2d",         // "2d" | "3d_rotatable" | "number_line" | "chart" | etc.
  "visual_ai_verified": true,              // LLM recheck: visual matches math logic
  "difficulty_within_topic": 47
}
```

**The parent/child NEVER sees:** curriculum_map, irt, skill_node, country_context selection (auto-detected from locale/onboarding)

**The parent/child SEES:** Level 3 → Topic 1 → Question 47 → with a visual of an array model

---

## THE CHILD EXPERIENCE

### Core Loop (unchanged — always adaptive)

```
HOME SCREEN
┌─────────────────────────────────────┐
│ 🥝 Hi Arjun!                        │
│ Level 3: Thinker     [KiwiScore 212]│
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ 🎯 PLAY  (Smart Practice)       │ │  ← THE core. Adaptive. Cross-topic.
│ │ "Today: Fractions + Review ×"   │ │     Never changes. Always right level.
│ └─────────────────────────────────┘ │
│                                      │
│ Your Topics:                         │
│ ● Multiplication ████████░░ Lv 7/10 │
│ ● Fractions      ████░░░░░░ Lv 4/10 │
│ ● Geometry       ██░░░░░░░░ Lv 2/10 │
│ ...                                  │
│                                      │
│ 🏆 3 topics mastered this level!     │
│ 🔓 4 more to unlock Level 4         │
│                                      │
│ [🏠 Play] [📚 Curriculum] [👨‍👩‍👧 Parent]│
└─────────────────────────────────────┘
```

**The "PLAY" tab is sacred.** It never changes shape. Always adaptive. Always cross-topic. Always at the child's actual level. This is the core product.

### The Curriculum Tab (separate, on demand)

```
📚 CURRICULUM TAB
┌─────────────────────────────────────┐
│ What do you want to study?          │
│                                      │
│ [CBSE ▼] [Grade 3 ▼]  ← picker     │
│                                      │
│ Ch 1: Numbers ████████████ Done ✓   │
│ Ch 2: Addition & Subtraction ████── │
│ Ch 3: Multiplication ██──────────── │
│ Ch 4: Division (locked - do Ch3)    │
│ ...                                  │
│                                      │
│ 📅 Your plan: 12 weeks remaining    │
│ Pace: 1 chapter/week → On Track     │
└─────────────────────────────────────┘
```

**This is the "Targeted Mastery" tab — for parents/school needs.**

Use case: "I have a test on Fractions on Friday."
→ Selecting this generates a **Weekly Plan** that runs in parallel to the Core Journey.
→ This parallel plan does NOT alter the core adaptive state (theta, level, etc.)
→ It's a separate practice lane that draws from curriculum-tagged questions only.

It generates a plan based on:
- Which curriculum they chose
- How many weeks until exams
- Current mastery level
- Whether kid just started or finishing the grade

**The core PLAY experience is never affected.** Smart Practice still adapts to the kid's actual level. The Curriculum tab is an overlay, not a replacement.

---

## THE BENCHMARK — "Height for Age"

### How It Works

Just like pediatricians plot height-for-age on a growth chart, we plot math-ability-for-grade:

```
                    KIWIMATH ACADEMIC HEIGHT CHART
                    
KiwiScore
300 ─┬─────────────────────────────────────────── Level 6
     │                                    ╱
270 ─┤                              ╱───╱   ← 95th percentile
     │                         ╱──╱
250 ─┤                    ╱──╱           ← 75th percentile
     │               ╱──╱
225 ─┤          ╱──╱                     ← 50th (median)
     │     ╱──╱
200 ─┤╱──╱                               ← 25th percentile
     │
170 ─┤                                    ← 5th percentile
     │
140 ─┼────┬────┬────┬────┬────┬────┬────
     G1   G2   G3   G4   G5   G6   G7
                School Grade
```

**What parents see after benchmark:**

```
"Arjun's math ability: KiwiScore 212 (Level 3: Thinker)
 For a Grade 3 student, this is above average.
 He's especially strong in arithmetic and ready for fractions."
 
 Confidence: ████░░░░ Building (3 more sessions for full picture)
```

### Benchmark Flow — The "AH Altimeter"

#### The Expanding Spiral Algorithm

Not a simple binary search — a multidimensional radar sweep:

```
PHASE 1: SEED
  - Use Age as "Probability Center" (prior belief in IRT)
  - 9-year-old → radar starts focused at AH 4.0 (Grade 4 content)
  - This is a PRIOR, not a cap. Engine overrides freely.

PHASE 2: ASYMMETRIC SPIRAL (the "V Jump")
  - Grade-Level Anchor question first (at the seed level)
  - If CORRECT → jump +1.5 AH levels (find ceiling fast)
  - If WRONG → drop -1.0 AH levels (find floor conservatively)
  - Asymmetric because students more likely to struggle with
    unknown concepts than to fail known ones
    
  CROSS-CURRICULUM CHECK:
  If student struggles with a US Common Core version of a skill,
  the system pivots to a Singapore Math version of the SAME skill.
  → Determines if failure is CONCEPTUAL (doesn't understand the math)
     or CONTEXTUAL (confused by currency/units/phrasing)
  → Prevents false-low placement due to unfamiliar context

PHASE 3: REFINE ("Bridge Questions")
  - If student fails a core skill, test its PREREQUISITES
  - Example: fails fraction addition → test "what is a fraction?"
  - Maps the exact depth of the gap, not just "can't do fractions"

PHASE 4: LOCK (SEM Termination)
  - Test STOPS when Standard Error of Measurement < 0.15
  - NOT a fixed question count
  - Consistent student → finishes in ~8 questions
  - "Noisy" student (hard right, easy wrong) → extends to ~16 questions
  - Result: precise Academic Height with known confidence interval
```

#### Academic Height Is 3-Dimensional

AH is not just a single number — it's a Mastery Profile:

```
AH PROFILE:
┌─────────────────────────────────────────┐
│ DEPTH (Vertical AH): 4.2               │
│   The highest complexity level reached  │
│                                         │
│ BREADTH (Horizontal AH): 73%           │
│   Percentage of topics mastered at      │
│   that depth                            │
│                                         │
│ STABILITY (Fluency): 0.85              │
│   Speed-Accuracy coefficient            │
│   (fast AND accurate = high fluency)    │
└─────────────────────────────────────────┘

Parent sees: "AH 4.2" (the simple number)
Engine uses: all three dimensions for question selection
```

#### The Diagnostic UI: "The Flight Path"

The diagnostic must feel like a Discovery Mission, not a test:

```
┌────────────────────────────────────────┐
│                              ☁️ ☁️      │
│  [ALTIMETER]          🥝✈️             │
│  ┌──────┐                              │
│  │ AH   │    ← Kiwi bird rises in     │
│  │ ▓▓▓▓ │       a plane as child       │
│  │ ▓▓▓░ │       solves problems        │
│  │ ▓▓░░ │                              │
│  │ ▓░░░ │                              │
│  └──────┘                              │
│                                         │
│  🌲🌲🌲 (Forest → Clouds → Space)     │
│                                         │
│  As AH moves G2→G5, background         │
│  transitions from Forest → Cloud Level  │
│  → Space. Instant psychological reward. │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  What is 3/4 + 1/2?            │   │
│  │  [5/6] [5/4] [1 1/4] [3/8]    │   │
│  └─────────────────────────────────┘   │
└────────────────────────────────────────┘
```

#### Post-Diagnostic Flow

```
1. PLACEMENT
   - "You're Level 3: Thinker! 🎉"
   - Shows AH Profile (Depth + Breadth + Stability)
   - Shows 2-3 strongest topics
   - Shows 1-2 areas to grow ("Air Pockets")
   
2. GOAL SETTING + VELOCITY
   → "Your Academic Height is 3.4"
   → "What is your goal height?" (parent selects, e.g. 5.0)
   → "In how many weeks?" (e.g. 20 weeks)
   → Engine calculates Velocity Requirement:
     (5.0 - 3.4) / 20 = 0.08 AH gain/week
   → Smart Practice intensity adjusts to hit velocity target
   → Options: 8 weeks (intensive) / 12 weeks (standard) / 16 weeks (relaxed)
   → Generates weekly topic schedule
   
3. CALIBRATION (first 5 sessions)
   - Theta confidence builds from Low → Medium → High
   - Level placement may adjust (up or down by 1)
   - Velocity requirement recalculated if level shifts
   - Parent notified: "We've refined Arjun's level based on 5 sessions"

4. HIGH UNCERTAINTY RECOVERY
   If diagnostic ends with a "Noisy Profile" (SEM still elevated):
   - First week of practice = "Extended Benchmarking"
   - Questions are slightly diagnostic (wider difficulty spread)
   - Parent report: "We've found your child's altitude (AH 4.2),
     but we're still mapping their 'Air Pockets' (knowledge gaps).
     Results will sharpen over the next 3 sessions."
   - Builds trust by acknowledging learning isn't a straight line
```

### The "Beginning vs End of Grade" Problem

Anand's insight: A kid starting Grade 3 (June) vs ending Grade 3 (March) has very different needs.

**Solution: We DON'T use school grade for ability placement.** The benchmark does that.

But for the **Curriculum tab**, we need to know timing:

```
Onboarding question (Curriculum tab only):
"When does your school year end?"
→ March (most Indian schools)
→ December (some international schools)
→ Not sure / homeschool

From this + current month, we compute:
- Weeks remaining in academic year
- Whether to show "full year plan" or "revision mode"
- Pacing suggestions
```

**The core PLAY experience doesn't care about this.** It always adapts from current ability upward. The timing only matters for the Curriculum tab's weekly plan.

---

## QUESTION EXPERIENCE — RETHOUGHT

### The "Why?" Must Be Powerful

Current state: Generic, often wrong. This is the #1 content quality issue.

**What "Why?" should feel like:**

```
Kid answers: 43 - 17 = 34 ❌

WHY? SCREEN:
┌─────────────────────────────────────┐
│ 🤔 Here's what happened:            │
│                                      │
│ You did:  4-1=3, 3-7=... hmm        │
│ So you got: 34                       │
│                                      │
│ The trick: When the bottom digit     │
│ is BIGGER, you need to "borrow"      │
│ from the tens place.                 │
│                                      │
│ ┌─ VISUAL ─────────────────────┐    │
│ │   4̶3  →  3|13                │    │
│ │  -17     -1|7                 │    │
│ │  ───     ─────                │    │
│ │          2| 6  = 26 ✓        │    │
│ └──────────────────────────────┘    │
│                                      │
│ 💡 Try to remember: if bottom > top, │
│    borrow from next door!            │
│                                      │
│ [Got it! →]                          │
└─────────────────────────────────────┘
```

**The 3-R Framework for every "Why?":**

1. **Re-Contextualize** — State the error neutrally. Show what the child DID.
   "It looks like you added the denominators instead of finding a common one."

2. **Redirect** — Offer a mental model. Give them a new way to think about it.
   "Think of denominators as the 'size' of the slices. You can't add different-sized slices directly!"

3. **Reinforce** — Give a small "Quick-Win" micro-question before moving on.
   "Before we try again, what is the common denominator for 1/2 and 1/3?"
   → This micro-question activates retrieval and builds confidence.

**Requirements for powerful "Why?":**
1. Identifies the SPECIFIC misconception from the distractor chosen (3-R step 1)
2. Shows what the child likely DID (not just what's correct)
3. Includes a visual when helpful
4. Gives a memorable rule/trick (3-R step 2)
5. Ends with a micro-question reinforcement (3-R step 3)
6. Language matches the child's level

**AI Evolution path:**
- Phase 1: Human-authored "Why?" for the top 500 most-served questions
- Phase 2: **Few-Shot LLM generation** — give the model 5 perfect human-authored "Why?" examples for that specific skill as few-shot exemplars. Ensures tone is encouraging, age-appropriate, and follows the 3-R structure.
- Phase 3: LLM-generated "Why?" with human spot-check (sample 10% for quality gate)
- Phase 4: Fully automated with statistical quality monitoring

### Hints — Layered Scaffolding with Progressive Option Elimination

Three-layer hint system. Each layer reveals more AND changes the UI:

```
HINT 1 — Conceptual (no UI change to options)
┌─────────────────────┐
│ What is 7 × 8?      │
│                      │
│ 💡 "Remember,        │
│  multiplication is   │
│  repeated addition." │
│                      │
│ [48] [54] [56] [63]  │  ← All 4 options still visible
│ [Show next hint]     │
└─────────────────────┘

HINT 2 — Strategic (one wrong option fades out)
┌─────────────────────┐
│ What is 7 × 8?      │
│                      │
│ 💡 "Try counting by  │
│  7s: 7, 14, 21..."  │
│                      │
│ [48] [··] [56] [63]  │  ← One incorrect option faded/greyed
│ [Show final hint]    │
└─────────────────────┘

HINT 3 — Direct (50/50: only 2 options remain)
┌─────────────────────┐
│ What is 7 × 8?      │
│                      │
│ 💡 "Look:            │
│  7×7=49, so 7×8      │
│  is just one more 7." │
│                      │
│ [··] [··] [56] [63]  │  ← Only 2 options remain (50/50)
│                      │
│ [I'm ready →]        │
└─────────────────────┘
```

**Design rules:**
- Options slide/fade smoothly (not snapping)
- Faded options go to ~20% opacity, still slightly visible but not clickable
- Hint text takes center stage, options become secondary
- "I'm ready" restores full view with remaining options
- This feels soothing, not punishing: "I needed help" → calm scaffolding → "now I can try"
- Child always makes the final selection themselves (even at 50/50)

**Visual tagging per question:**
Every question in the DB carries a `visual_requirement` tag:
- `Essential` — visual is core to understanding (geometry, charts, place value)
- `Optional` — visual helps but isn't required (word problems)
- `None` — pure computation, visual would be decorative

**AI Recheck for visuals:**
Before any visual enters production, a secondary LLM agent validates that the generated visual actually matches the mathematical logic of the question. Catches mismatches like "stem says triangles, visual shows squares."

### Interaction Modes — Rethought

| Mode | When to use | Design principle |
|------|------------|-----------------|
| **MCQ (2×2 grid)** | Concept recognition, comparison, "which one" | Fast, low-friction, visual |
| **Integer input** | Computation, counting, measurement | Numberpad, with VALIDATION (reject impossible answers) |
| **Drag & drop** | Ordering, sequencing, matching, building | PLAYFUL. Not converted MCQs. Must feel like a toy. |
| **True/False** | Quick concept checks, warm-up | Swipe left/right or big buttons |
| **Draw/Connect** | Geometry, number lines, graphs | Finger drawing on canvas (future) |

**Drag & Drop — Rethought:**

These should NOT be "put 3,1,5,2 in order" (that's just MCQ with extra steps).

Good drag-drop questions:
- "Build the number 347 using place value blocks" (drag hundreds/tens/ones)
- "Match each fraction to its spot on the number line"
- "Put these steps in order to solve 43-17" (ordering the PROCESS)
- "Sort these shapes: has symmetry ↔ no symmetry"
- "Balance the equation: drag numbers to make both sides equal"

These are PLAYFUL, TACTILE, and teach through manipulation — not just testing recall.

### Skip Button — The "Safety Valve" Against Frustration Dropout

```
[← Skip this one]  (small, unobtrusive, top-left)
```

Rules:
- Always visible. Never locked.
- Internally logged as a **"High Uncertainty" event** (not a failure, not ignored)
- The IRT engine does NOT penalize theta for skips
- BUT it triggers a **remedial "Warmup" question** on the same skill in the NEXT session
- If kid skips 3+ in a row → "Having trouble? Want to try easier ones?"
- Skipped questions re-enter the pool later at a different angle
- Parent report shows skip rate (high skip rate = content too hard or wrong level)

### Visual Design Principles for Questions

| Principle | Rule |
|-----------|------|
| **2D default** | Most visuals are clean 2D SVG |
| **3D for spatial concepts** | Volume, surface area, geometry where rotation aids understanding |
| **3D is interactive** | Kid can rotate the shape to see different faces/angles |
| **AI recheck on every visual** | Secondary LLM validates visual matches the math logic before production |
| **No decorative visuals** | If it doesn't help understanding, remove it |
| **Level 1-2: ≥80% visual** | Young kids think in pictures |
| **Level 5-6: ≥40% visual** | Older kids handle abstract, but still need for geometry/data |
| **Tagged: Essential/Optional/None** | Every question carries `visual_requirement` enum |

---

## THE PARENT EXPERIENCE — RETHOUGHT

### Parent Dashboard Hero Metrics

```
┌─────────────────────────────────────┐
│ 📊 ARJUN'S PROGRESS                 │
│                                      │
│ ┌──────────────────────────────────┐│
│ │ ACADEMIC HEIGHT                   ││
│ │                                   ││
│ │ Level 3: Thinker                  ││
│ │ KiwiScore: 212 (+8 this week)     ││
│ │ ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░ 65% to Lv 4  ││
│ │                                   ││
│ │ For Grade 3: ABOVE AVERAGE 📈    ││
│ └──────────────────────────────────┘│
│                                      │
│ This week:                           │
│ • Growth: +8 points (strong!)        │
│ • Skills mastered: 2 new ✓           │
│ • Retention: 91% (remembered well)   │
│ • Sessions: 5/5 days 🔥              │
│                                      │
│ • Accuracy: 79% (supporting metric)  │
│                                      │
│ 🎯 Plan progress:                    │
│ Week 4 of 12 — On track             │
│ Topics this week: Fractions, Review   │
└─────────────────────────────────────┘
```

**Hierarchy:**
1. Academic Height (where is my child?)
2. Growth (is my child improving?)
3. Skills mastered (what's been learned?)
4. Retention (are they keeping it?)
5. Plan progress (are we on schedule?)
6. Accuracy (supporting, not hero)

### The Plan — Parent Sets the Pace

```
ONBOARDING (after benchmark):

"Arjun is Level 3: Thinker.
 There are 10 topics to master at this level.
 
 How quickly would you like to work through them?"
 
 [🚀 8 weeks — Intensive (5 sessions/week)]
 [📘 12 weeks — Standard (4 sessions/week)]
 [🌱 16 weeks — Relaxed (3 sessions/week)]
 [⚡ Custom — I want to set my own pace]
```

**The plan then generates:**
- Week 1-2: Topics 1-2 (Multiplication + Division)
- Week 3-4: Topics 3-4 (Fractions intro + comparing)
- Week 5: Review week (FSRS-triggered)
- Week 6-7: Topics 5-6 (Measurement)
- ...etc

**Adaptive pacing:**
- If kid is ahead → "Arjun is 2 weeks ahead of plan! 🎉"
- If kid is behind → "Arjun is 1 week behind. Suggestion: +1 session/day this week"
- Near exams → Auto-switches to revision mode

### Curriculum Tab — The School Alignment Layer

```
"Which curriculum does your school follow?"
→ CBSE (NCERT)
→ ICSE  
→ Cambridge Primary
→ Singapore Math
→ None / Homeschool

"Which grade is Arjun in at school?"
→ Grade 3

GENERATED:
┌─────────────────────────────────────┐
│ 📚 CBSE Grade 3 — Math              │
│ School year ends: March 2027         │
│ Weeks remaining: 44                  │
│                                      │
│ Ch 1: Numbers up to 1000     ✓ Done │
│ Ch 2: Addition & Subtraction ✓ Done │
│ Ch 3: Multiplication         ▶ Now  │
│ Ch 4: Division               ○ Next │
│ Ch 5: Fractions              ○      │
│ Ch 6: Money                  ○      │
│ Ch 7: Measurement            ○      │
│ Ch 8: Time                   ○      │
│ Ch 9: Geometry               ○      │
│ Ch 10: Data Handling         ○      │
│                                      │
│ 📅 Suggested pace: 1 chapter / 4 wks│
│ Status: On Track ✓                   │
└─────────────────────────────────────┘
```

**Important:** Tapping a chapter here enters a CHAPTER-SPECIFIC practice session (questions tagged to that chapter in that curriculum). But the core PLAY button still does cross-topic adaptive practice.

---

## YEAR-END PACING — Calendar-Aware Engine

The adaptive engine monitors the calendar and adjusts its strategy automatically:

### Standard Mode (Weeks 1-30 of academic year)

- Deep conceptual understanding is the priority
- Full session structure: warmup → core → stretch → review
- New topics introduced at normal pace
- "Stretch" problems (from next level) keep challenging strong students
- AH growth is the primary KPI

### Crunch Mode (Weeks 31-40 — exam season)

The engine detects approaching year-end and shifts strategy:

- **STOP** introducing new AH levels — no new ground
- **SHIFT** to Retrieval Practice — recall what you've learned
- **FOCUS** on "Solidifying Mastery" of the current level
- Session structure changes: warmup → review → review → practice test
- Interleaved questions across all mastered topics
- Weak spots get extra repetition
- Parent messaging: "Exam preparation mode active"

```
Week 30 trigger:
"Arjun has mastered 7/10 topics at Level 3.
 Switching to Exam Ready mode.
 Focus: Solidify weak topics (Fractions, Time)
 + review all mastered topics for retention."
```

**The Curriculum tab drives this even harder:** if a parent has entered exam dates, the engine can generate topic-specific revision plans down to the day.

---

## THE ADAPTIVE ENGINE — How It Changes

### Smart Practice Session (core PLAY)

Still [warmup → core → stretch → review], but now:

- **Warmup:** From topics BELOW current level (confidence builder)
- **Core:** From current level's target topics (ZPD)
- **Stretch:** From next level (preview of what's coming)
- **Review:** FSRS-scheduled from mastered topics (retention)

Questions are drawn from ALL curricula but localized (₹ for India, $ for Singapore).

### Universal Pull Logic (The Delivery Engine)

The backend doesn't "search" for questions. It **samples** from a pre-compiled probability distribution.

```
REQUEST: "Fractions question for student with theta 0.4"

1. FILTER by maturity bucket:
   - Benchmark sessions → Bucket C only (Production, N>1000)
   - Practice sessions → Bucket B + C (add 10-20% Bucket A for calibration)

2. FILTER by curriculum (if in Curriculum tab):
   - WHERE curriculum_map CONTAINS 'singapore'
   - Core PLAY → no curriculum filter (pull from ALL)

3. SAMPLE by IRT match:
   - Target: questions where Difficulty(Beta) ≈ student's Theta
   - ZPD window: P(correct) ∈ [0.60, 0.85]
   - Weighted random selection (not deterministic — avoids repetition)

4. LOCALIZE by country:
   - Auto-select country_context based on GPS/locale
   - Swap currency, names, units at render time
   - Same mathematical content, different wrapping

5. EXCLUDE already-served:
   - Session dedup (never same Q twice in one session)
   - Recent history (avoid same Q within 7 days unless FSRS-triggered review)
```

This pre-compiled distribution is built at deploy time (or nightly) so runtime queries are fast lookups, not expensive searches.

### Level Progression

To move from Level 3 → Level 4:
1. Master ≥7 of 10 topics at Level 3 (sustained mastery criteria)
2. Pass a "Level Gate" challenge (5 mixed questions from all topics)
3. KiwiScore crosses the threshold (225 for Level 4)

**Level-up is a CELEBRATION moment** — confetti, badge, parent notification.

### What Stays Constant

| Principle | Implementation |
|-----------|---------------|
| Engine adapts to child | Per-skill theta, IRT selection, ZPD targeting |
| Content is level-appropriate | Only serve questions from ±1 level of current |
| Reviews prevent forgetting | FSRS with per-skill decay rates |
| Transfer accelerates | Mastering prerequisites boosts dependent skills |
| Skip is always available | No question is mandatory |
| Parent sees growth | Weekly report, academic height, plan progress |

---

## FLAGGING & QUALITY — Continuous Improvement

### In-App Flagging

```
[🚩] (always visible, top-right of question screen)

"What's wrong with this question?"
→ Answer seems incorrect
→ Question doesn't make sense
→ Visual doesn't match
→ Too easy / Too hard for my level
→ Other: [free text]
```

### Admin Pipeline

```
User flags question → 
  Auto-categorized (answer/visual/difficulty/other) →
    IF 3+ flags on same question: auto-quarantine (remove from pool) →
      Admin reviews in CMS →
        Fix + re-approve OR permanent removal
        
For AI-fixable issues (difficulty mismatch):
  Auto-recalibrate IRT params based on response data
  
For content issues (wrong answer, bad visual):
  Human fix required → CMS queue with priority scoring
```

### Smart Auto-Flagging (No User Action Needed)

Beyond user flags, the system detects likely content errors automatically:

```
IF 3+ high-performing students (High Theta, top 20%)
   ALL miss the same question
   AND choose the same "incorrect" answer
THEN:
   → Auto-flag as "Likely Error in Question"
   → Auto-quarantine from production pool
   → Push to Admin review queue with HIGH priority
   → Tag: "Statistical anomaly — possible wrong answer key"
```

This catches the worst content bugs — where the "correct" answer is actually wrong — without waiting for user flags.

### The "Admin Pulse" Dashboard

Internal content team dashboard surfacing the top 50 "Contested Questions" weekly:

```
ADMIN PULSE (weekly digest)
┌─────────────────────────────────────────────┐
│ 🔴 HIGH PRIORITY (auto-flagged)             │
│ Q-2847: High-theta anomaly (5 top students  │
│         all chose distractor B) → LOCKED    │
│                                              │
│ 🟡 MEDIUM (user-flagged, 3+ flags)          │
│ Q-1204: "Visual doesn't match" × 4 flags    │
│ Q-3891: "Answer seems wrong" × 3 flags      │
│                                              │
│ 🟢 LOW (behavioral anomaly)                 │
│ Q-0542: Avg solve time 3× expected (confusing│
│         stem? or just hard?)                 │
│                                              │
│ [One-click edit] → JSON portal updates Q     │
│ globally across all 21K questions instantly   │
└─────────────────────────────────────────────┘
```

### High-Theta Auto-Lock (Complementary Rule)

```
IF students with HIGH Academic Height (top 20%)
   consistently MISS a question tagged as "Low Difficulty"
THEN:
   → Auto-lock question (remove from production)
   → Flag: "Difficulty mismatch — Beta too low OR wrong answer key"
   → IRT params queued for recalibration
```

This is the inverse of the smart auto-flag: catches questions that are HARDER than their metadata claims.

### Integer Input Validation

```
Question: "What is 7 × 8?"
Kid types: 5678

VALIDATION:
- Expected answer range: 1-100 (based on question type)
- Input 5678 > max_reasonable → 
  Show: "Hmm, that seems too big. The answer should be less than 100."
  Don't count as wrong. Let them try again.

- Expected: integer, kid enters: 3.5 →
  Show: "This needs a whole number answer."
```

---

## WHAT CHANGES IN THE CODEBASE

### Data Model Changes

```
# User profile
{
  "level": 3,                    # Kiwimath level (1-6)
  "kiwi_score": 212,            # Composite ability score
  "academic_height": {           # 3D AH profile
    "depth": 3.4,                # Vertical — highest complexity reached
    "breadth": 0.73,            # Horizontal — % topics mastered at depth
    "stability": 0.85           # Fluency — speed-accuracy coefficient
  },
  "goal_height": 5.0,           # Parent-set target AH (depth)
  "velocity_required": 0.08,    # AH gain/week to hit goal
  "school_grade": 3,            # For curriculum tab only
  "school_curriculum": "cbse",  # For curriculum tab only
  "country": "india",           # For localization (₹, names)
  "plan_weeks": 20,             # Parent-chosen pace to reach goal
  "plan_start_date": "2026-05-02",
  "school_year_end": "2027-03-15",
  "pacing_mode": "standard",    # "standard" (wk 1-30) | "crunch" (wk 31-40)
  "benchmark_confidence": "medium",  # low/medium/high
  "benchmark_sem": 0.12,        # Standard Error of Measurement (< 0.15 = locked)
  "age_prior": 8                # Age used as IRT prior, overridable
}
```

### Grand Unified Question Schema

Every question is a Rich JSON Object with pedagogical + technical + behavioral metadata:

```
{
  # === CORE TAXONOMY ===
  "question_id": "KM-L3-T1-047",
  "universal_skill_id": "MULT_FACTS_3.1",    # Cross-curriculum skill ID
  "level": 3,
  "topic_within_level": "multiplication_foundations",

  # === IRT PARAMETERS ===
  "irt": {
    "difficulty_beta": 0.3,                    # Difficulty estimate
    "discrimination_alpha": 1.2,               # How well it separates abilities
    "guessing_c": 0.15                         # Guessing parameter (MCQ)
  },
  "maturity_bucket": "production",             # SEE LIFECYCLE BELOW

  # === CURRICULUM MAPPING ===
  "curriculum_map": {
    "cbse": { "grade": 3, "chapter": "Multiplication", "ncf_code": "M3.4" },
    "icse": { "grade": 3, "chapter": "Multiplication & Division" },
    "cambridge": { "grade": 3, "unit": "3Nc.04" },
    "singapore": { "grade": 3, "topic": "Whole Numbers — Multiplication" },
    "common_core": { "grade": 3, "standard": "3.OA.C.7" }
  },

  # === CONTEXT TAGS ===
  "country_context": {
    "india": { "currency": "₹", "names": ["Ria", "Arjun"], "units": "km/kg" },
    "singapore": { "currency": "$", "names": ["Wei", "Mei"], "units": "km/kg" },
    "global": { "currency": "coins", "names": ["Alex", "Sam"], "units": "km/kg" }
  },
  "language": "en",                            # Multi-lang future support

  # === INTERACTION & MEDIA ===
  "interaction_mode": "integer_input",
  "visual_requirement": "essential",           # essential | optional | none
  "visual_type": "2d",                         # 2d | 3d_rotatable | number_line | chart | lottie
  "media_id": "vis-L3-T1-047",                # Links to CDN asset
  "media_hash": "sha256:a3f2...",              # Integrity hash for CI/CD validation
  "visual_ai_verified": true,                  # LLM recheck passed

  # === BEHAVIORAL TAGS (populated by live data) ===
  "avg_time_to_solve_ms": 12400,              # Mean response time
  "misconception_ids": ["MULT_COMMUTE_ERR", "ADD_INSTEAD_MULT"],
  "times_served": 4821,                       # Total serves across all students
  "flag_count": 2,                            # User flags received

  # === WHY? QUALITY ===
  "why_quality": "human_authored",             # human_authored | ai_fewshot | ai_generated
  "why_framework": "3R"                        # Re-contextualize → Redirect → Reinforce
}
```

### Question Maturity Lifecycle

Questions move through 3 buckets as real student data accumulates:

```
┌────────────────────────────────────────────────────────────┐
│ BUCKET A: EXPERIMENTAL (N < 100 serves)                    │
│ - New questions. IRT params are "Expert Estimates"          │
│ - Served only in non-benchmark sessions                    │
│ - Mixed in at 10-20% of session (never dominant)           │
│ - Purpose: collect real response data                       │
├────────────────────────────────────────────────────────────┤
│ BUCKET B: CALIBRATING (100 < N < 1000 serves)             │
│ - Real data collected. AI recalculates Beta + Alpha        │
│ - IRT params replace expert estimates with empirical fit   │
│ - Served normally in adaptive sessions                     │
│ - Still excluded from high-stakes benchmarking             │
├────────────────────────────────────────────────────────────┤
│ BUCKET C: PRODUCTION (N > 1000 serves)                     │
│ - Stable, validated questions                              │
│ - Used for Academic Height benchmarking (spiral diagnostic) │
│ - IRT params are statistically reliable                    │
│ - Only these questions inform the AH score                 │
└────────────────────────────────────────────────────────────┘

Promotion: A → B at 100 serves (automatic)
           B → C at 1000 serves IF IRT fit is stable (chi-sq < threshold)
Demotion:  Any → quarantine if flag_count > 3 OR auto-flag triggered
```

### Hash-Linked Content Integrity (CI/CD)

Prevents "question-visual mismatch" at build time:

```
Content Store (JSON):
  question.media_id = "vis-L3-T1-047"
  question.media_hash = "sha256:a3f2..."

Asset Store (CDN / S3):
  s3://kiwimath-assets/vis-L3-T1-047.svg

CI/CD Integrity Script (pre-deploy):
  1. Crawl all question JSONs
  2. For each media_id: verify file exists in Asset Store
  3. For each media_hash: verify SHA256 matches stored file
  4. Check dimensions/type match expected (SVG viewBox, PNG resolution)
  5. If ANY mismatch → BUILD FAILS → blocks deployment
  6. Report: "3 orphaned assets, 1 hash mismatch" → fix before retry
```

### API Changes

| Endpoint | Change |
|----------|--------|
| `GET /session/unified` | Add `level` param; uses Universal Pull Logic (sample, not search) |
| `GET /benchmark/start` | New — starts spiral diagnostic with age-based seed + asymmetric jumps |
| `POST /benchmark/answer` | New — submits single answer; returns next Q or SEM-locked result |
| `POST /benchmark/complete` | New — returns 3D AH profile (depth/breadth/stability) + level + confidence |
| `POST /goal/set` | New — parent sets goal height + timeline → calculates velocity |
| `GET /plan/generate` | New — creates weekly plan based on level + velocity target |
| `GET /plan/pacing-mode` | New — returns "standard" or "crunch" based on calendar |
| `GET /curriculum/chapters` | Unchanged — for curriculum tab |
| `GET /curriculum/targeted` | New — "test on Friday" parallel plan generation |
| `POST /question/flag` | Already exists — add auto-quarantine + smart auto-flag + high-theta auto-lock |
| `POST /question/skip` | New — records skip as "High Uncertainty" event |
| `GET /admin/pulse` | New — weekly top-50 contested questions dashboard |
| `POST /content/promote` | New — move question between maturity buckets (A→B→C) |
| `GET /content/integrity` | New — CI/CD hash-link validation report |

### Flutter Changes

| Screen | Change |
|--------|--------|
| Onboarding | Spiral diagnostic with Altimeter UI (Kiwi bird + dynamic backgrounds) |
| Onboarding | Goal height + velocity selection after AH placement |
| Home | Show Level + KiwiScore, not Grade |
| Question | Add skip button, 3-layer hint with progressive option elimination |
| Question | 3D rotatable visuals for spatial geometry questions |
| Why? sheet | 3-R Framework redesign (Re-contextualize → Redirect → Reinforce micro-Q) |
| Curriculum tab | Separate "Targeted Mastery" — parallel plan, doesn't affect core state |
| Parent tab | Hero = 3D Academic Height (depth + breadth + stability) + Growth |
| Parent tab | Velocity tracking: "On pace" / "Behind target" vs goal height |

---

## SUMMARY: THE STRATEGIC SHIFT

| Before | After |
|--------|-------|
| "Grade 3 student doing Grade 3 content" | "Level 3 Thinker doing Level 3 content (regardless of school grade)" |
| Curriculum drives navigation | Ability drives navigation; curriculum is a tab |
| NCERT Ch1, Ch2, Ch3 on home screen | Topics at your level on home screen |
| Fixed difficulty per grade | Adaptive difficulty per skill per child |
| "How did I do?" = accuracy % | "How did I do?" = growth + 3D academic height |
| One path for everyone in same grade | Every child on their own path through levels |
| Content quality assumed OK | Content quality is THE competitive moat |
| Fixed 10-question diagnostic | SEM-terminated spiral with asymmetric jumps |
| Questions are just questions | Questions have a maturity lifecycle (Experimental → Calibrating → Production) |
| "Search" for the right question | "Sample" from pre-compiled probability distribution |
| Generic "Why?" explanations | 3-R Framework: Re-contextualize → Redirect → Reinforce |
| Hints are text-only | 3-layer hints with progressive option elimination |
| Same pace all year | Calendar-aware: Standard Mode → Crunch Mode near exams |

**The app becomes:**
> "The smartest math tutor that knows exactly where your child is,
> meets them there, and takes them as far as they can go —
> regardless of which school they attend or which board they follow."

---

*This is the strategic direction. All implementation should align to this vision.
When in doubt, ask: "Does this help the child feel 'I can win' and the parent feel 'I understand'?"*
