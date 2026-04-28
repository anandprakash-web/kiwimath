# Kiwimath — Complete Technical Specifications

**Owner:** Anand Prakash (anand.prakash@vedantu.com)
**Version:** 1.0 — April 27, 2026
**Purpose:** Single source of truth for all adaptive engine formulas, Socratic methodology, gamification design, and content quality rules.

---

## ⚠️ Code Audit Notes (April 27, 2026)

The following gaps exist between Anand's original specifications and the current codebase:

| Spec | Anand's Design | Code Reality | Action Needed |
|------|---------------|--------------|---------------|
| K-factor | Fixed K=24 (ELO) | Dynamic schedule: K=1.0→0.6→0.4→0.25 | Code is more sophisticated — update spec or align |
| Ability scale | 50-1000 (ELO rating) | -3.0 to +3.0 (logit/theta) | Code uses IRT theta directly — functionally equivalent |
| Difficulty ramp | +2-3 correct, -5 wrong | ELO delta with behavioral modifiers | Code approach is better — update spec |
| XP rewards | 10 correct, 3 wrong | Base 5 + 10 correct bonus | Align to one system |
| Hint multipliers | [1.0, 0.9, 0.75, 0.6, 0.5, 0.5] | **NOT IMPLEMENTED** | Must add to gamification.py |
| Level formula | floor(XP/150)+1 | Hardcoded tier boundaries [0-99, 100-299, etc.] | Decide which approach to use |

**Priority fix:** Hint multipliers are missing from the reward calculation — students get full XP regardless of hints used.

---

## 1. Adaptive Engine (ELO/IRT Model)

### 1.1 Core Probability Model — Rasch 1PL IRT

```
P(correct) = 1 / (1 + exp(-(θ - b)))
```

| Symbol | Meaning | Range |
|--------|---------|-------|
| θ (theta) | Student ability | -3.0 to +3.0 |
| b | Question difficulty (logit scale) | -3.0 to +3.0 |
| P | Probability of correct response | 0.0 to 1.0 |

**Difficulty mapping:** Raw difficulty 1-100 maps linearly to theta -3.0 to +3.0.
```
θ = -3.0 + (raw_difficulty - 1) * (6.0 / 99)
```

**Target zone:** P(correct) ≈ 0.72 — the sweet spot where learning is maximized (not too easy, not frustrating).

### 1.2 Ability Score Update (ELO-style)

```
new_ability = old_ability + K * (outcome - expected)
```

| Parameter | Value | Notes |
|-----------|-------|-------|
| K-factor | 24 | How fast ability adjusts |
| outcome | 1 if correct, 0 if wrong | Binary |
| expected | P(correct) from IRT | Between 0 and 1 |
| Ability clamp | [50, 1000] | Floor and ceiling |
| Starting ability | 500 | All new students |

### 1.3 Difficulty Selection

**Starting behavior:** New students begin at difficulty 20-30 (easy end).

**After each answer:**
- Correct → increase difficulty by 2-3 points
- Wrong → decrease difficulty by 5 points (faster drop to prevent frustration)

**Question selection:** From the available pool, pick the question whose difficulty gives P(correct) closest to 0.72 for the student's current ability.

**Grade-difficulty mapping:**
| Grade | Level | Difficulty Range |
|-------|-------|-----------------|
| Grade 1-2 | Level 1 | 1-50 |
| Grade 3-4 | Level 2 | 51-100 |
| Grade 5-6 | Level 3 | 101-150 (future) |

### 1.4 Latency × Accuracy Behavioral Matrix

| | Correct | Wrong |
|---|---------|-------|
| **Fast** (<median time) | **MASTERY** — student knows it cold | **GUESSING** — clicked without thinking |
| **Slow** (>median time) | **STRUGGLE_WIN** — worked hard, got it | **FRUSTRATED** — stuck and confused |

Each state triggers different adaptive responses:
- **MASTERY:** Ramp difficulty faster (+3 instead of +2)
- **GUESSING:** Don't increase difficulty; flag for re-test
- **STRUGGLE_WIN:** Hold difficulty steady; reward effort heavily
- **FRUSTRATED:** Drop difficulty by 5; offer hint; consider intervention

---

## 2. Student State Detection

The engine continuously classifies each student into behavioral states:

| State | Trigger | Response |
|-------|---------|----------|
| **NEW_USER** | First session, no history | Start at difficulty 20-30, extra encouragement |
| **STRUGGLING** | 2+ consecutive wrong answers | Reduce difficulty, offer hints, increase rewards for effort |
| **GUESSING** | Wrong answer in <3 seconds | Don't advance difficulty, gently redirect ("Take your time!") |
| **FLOWING** | 4+ consecutive correct answers | In the zone — maintain pace, sprinkle variable rewards |
| **CONFIDENT** | Correct without using any hints | Ready for harder material, ramp up |
| **FATIGUED** | >90 seconds on a question + wrong | Suggest break, reduce session, show encouragement |

### 2.1 Intervention Recommendations

Based on state detection, the system recommends interventions:
- **Struggling → Easier questions + hint nudge:** "Try tapping the hint button!"
- **Guessing → Pace check:** "Read the question carefully before answering"
- **Fatigued → Session end suggestion:** "Great effort today! Come back tomorrow for more"
- **Flowing → Streak celebration:** Keep the dopamine flowing with variable rewards

---

## 3. Mastery Score

```
mastery = 100 × (0.55 × accuracy + 0.25 × attemptConfidence + 0.20 × abilityComponent)
```

| Component | Weight | Calculation |
|-----------|--------|-------------|
| accuracy | 55% | correct_answers / total_attempts |
| attemptConfidence | 25% | min(total_attempts / 20, 1.0) — confidence grows with more data |
| abilityComponent | 20% | (ability_score - 50) / 950 — normalized from [50,1000] to [0,1] |

**Mastery thresholds:**
- < 40%: Needs practice
- 40-69%: Developing
- 70-79%: Proficient
- ≥ 80%: Mastered (unlocks Mastery Gems)

---

## 4. PoP — Proof of Progress Model

The behavioral prediction engine that keeps students engaged:

### 4.1 Flow State Equilibrium

```
Engagement = (Variable Reward × Perceived Progress) / (Friction + Predictability)
```

**Design implication:** Maximize the numerator (surprising rewards + visible progress) while minimizing the denominator (reduce friction, keep things unpredictable).

### 4.2 Probability of Abandonment

```
P(abandon) = 0.35 × wrong_streak_signal
           + 0.25 × accuracy_trend_signal
           + 0.20 × latency_trend_signal
           + 0.20 × session_fatigue_signal
```

| Signal | Weight | What it measures |
|--------|--------|-----------------|
| wrong_streak | 35% | Consecutive wrong answers (biggest predictor) |
| accuracy_trend | 25% | Rolling accuracy going down |
| latency_trend | 20% | Response times increasing (losing focus) |
| session_fatigue | 20% | Time in session × questions attempted |

**When P(abandon) > 0.7:** Trigger intervention (easier question, encouragement, suggest break).

---

## 5. Socratic 6-Level Hint Ladder

**Core philosophy:** "A hint is asking a better question, NOT giving the answer."

### 5.1 The Six Levels

| Level | Name | Purpose | Example |
|-------|------|---------|---------|
| **L0** | Pause | Give time to think | "Take a deep breath. Look at the picture again." |
| **L1** | Attention | Direct focus to key info | "Count all the shapes in the top row." |
| **L2** | Thinking Question | Prompt reasoning | "What happens if you group them in pairs?" |
| **L3** | Scaffolded Step | Break problem down | "First, find how many are in each group. Then add the groups." |
| **L4** | Guided Reveal | Show the method | "There are 3 groups of 4. What is 3 × 4?" |
| **L5** | Teach + Retry | Explain concept, give new attempt | Full worked explanation + similar problem to try |

### 5.2 Hint Rules

1. **Always start at L0** — never jump to the answer
2. **Student must request each level** — hints are never forced
3. **Each level unlocks the next** — can't skip from L0 to L4
4. **Track hints_used per question** — affects XP/coin rewards
5. **L5 counts as "taught"** — question may be re-served later at different parameters
6. **Hint cost:** Each hint level reduces the XP earned for that question:
   - 0 hints = 100% XP
   - 1 hint = 90% XP
   - 2 hints = 75% XP
   - 3 hints = 60% XP
   - 4+ hints = 50% XP

### 5.3 Hint Design Principles

- **L0-L1:** No math content — just metacognitive support
- **L2:** Ask, don't tell — Socratic questioning
- **L3:** Break the problem into visible steps
- **L4:** Show the specific method for THIS problem
- **L5:** Full teaching moment — explain WHY the method works
- **Every hint must be age-appropriate** — Grade 1-2 uses simple language, visual cues
- **Hints should reference the visual/SVG** when applicable

---

## 6. Gamification — The Kiwi Brain Reward System

### 6.1 Three Currencies

| Currency | Behavior | Earning Logic |
|----------|----------|--------------|
| **XP** (Experience Points) | Never decreases | Earned on every answer (correct or wrong with effort) |
| **Kiwi Coins** | Effort-based, spendable | Earned for correct answers, streaks, daily login |
| **Mastery Gems** | Milestone-based, premium | Earned only when topic mastery ≥ 80% |

### 6.2 XP Calculation

```
base_xp = 10 (correct) or 3 (wrong but attempted)
hint_multiplier = [1.0, 0.9, 0.75, 0.6, 0.5, 0.5][hints_used]
streak_bonus = min(streak_count * 2, 20)
final_xp = base_xp * hint_multiplier + streak_bonus
```

### 6.3 Coin Rewards

```
base_coins = 5 (correct) or 1 (wrong)
difficulty_bonus = floor(question_difficulty / 25)  # 0-3 bonus
streak_bonus = 2 per streak count (max 10)
final_coins = base_coins + difficulty_bonus + streak_bonus
```

### 6.4 Mastery Gems

Awarded at milestones only:
- Topic mastery reaches 80% → 5 gems
- Topic mastery reaches 90% → 10 gems
- Complete all questions in a topic → 20 gems
- Perfect session (10/10) → 3 gems

### 6.5 Level System

```
Level = floor(XP / 150) + 1
```

| Level Range | Tier | Title |
|-------------|------|-------|
| 1-5 | Seed | "Math Seed" |
| 6-15 | Sprout | "Math Sprout" |
| 16-30 | Kiwi Jr | "Kiwi Jr" |
| 31-50 | Kiwi | "Kiwi Mathematician" |
| 51-75 | Super Kiwi | "Super Kiwi" |
| 76+ | Kiwi Master | "Kiwi Master" |

### 6.6 Streaks

- **Correct streak:** Consecutive correct answers in a session
- **Daily streak:** Consecutive days with at least 1 completed session
- **Streak rewards:** Multiplied at milestones (3, 5, 7, 10 correct in a row)
- **Streak protection:** 1 wrong answer doesn't break daily streak if ≥5 questions attempted

### 6.7 Badges (12-18 planned)

Categories:
- **Topic mastery:** "Counting Champion", "Geometry Guru", etc.
- **Effort:** "Hint Explorer" (used all 6 hint levels), "Never Give Up" (10 wrong then correct)
- **Streaks:** "Hot Streak" (10 in a row), "Weekly Warrior" (7-day streak)
- **Milestones:** "Century" (100 questions), "Brain Builder" (500 questions)

### 6.8 Kiwi Brain 30-Day Psychology Journey

| Phase | Days | Psychology | Focus |
|-------|------|-----------|-------|
| **1. Discovery** | 1-3 | Novelty + quick wins | Easy questions, frequent rewards, "wow" moments |
| **2. Competence** | 4-10 | "I can do this!" | Difficulty ramps, first badges, streak building |
| **3. Challenge** | 11-17 | Healthy struggle | Harder questions, hint ladder usage, resilience building |
| **4. Mastery** | 18-24 | "I'm getting good" | Topic mastery milestones, gem earning, visible progress |
| **5. Identity** | 25-30 | "I am a math person" | Titles, achievements, comparing to past self |

### 6.9 Learner Types (Adaptive Rewards)

| Type | Detection | Reward Strategy |
|------|-----------|----------------|
| **Explorer** | Tries many topics, uses hints | Reward breadth, "Curious Mind" badge |
| **Achiever** | Focuses on mastery, completionist | Reward depth, mastery gems, completion % |
| **Socializer** | (Future) shares, competes | Leaderboards, challenges, sharing |
| **Competitor** | Fast answers, high streaks | Streak bonuses, speed badges, rankings |

---

## 7. Content Specifications

### 7.1 Question Structure

Every question must have:
1. **Parametric stem** — the question text
2. **4 choices** (A, B, C, D) — only 1 correct
3. **SVG visual** — illustration/diagram for the question
4. **Correct answer** — which choice is right
5. **Diagnostics per wrong answer** — WHY each wrong answer is wrong
6. **Difficulty** — 1-100 scale
7. **6-level Socratic hint ladder** — L0 through L5
8. **Topic** — one of 8 topics
9. **Grade** — target grade level

### 7.2 Topics (8 total)

1. Counting
2. Logic
3. Arithmetic
4. Geometry
5. Patterns
6. Spatial Reasoning
7. Measurement
8. Data Handling

### 7.3 Difficulty Distribution Per Topic

| Difficulty | Percentage | Count (per 300) |
|------------|-----------|-----------------|
| Easy (L1-L2) | 40% | 120 |
| Medium (L3-L4) | 40% | 120 |
| Difficult (L5-L6) | 20% | 60 |

### 7.4 Content Volume Targets

| Grade Level | Questions/Topic | Total |
|-------------|----------------|-------|
| Grade 1-2 (current) | 300 | 2,400 |
| Grade 3-4 (planned) | 300 | 2,400 |
| Grade 5-6 (planned) | 300 | 2,400 |
| **Grand total** | — | **7,200** |

Current state: 100 questions per topic × 8 topics = 800 total (Grade 1-2 only).

### 7.5 10-Point QA Checklist

Every question must pass:

1. **Stem clarity** — Is the question unambiguous for the target age?
2. **Visual-stem match** — Does the SVG accurately represent the question?
3. **Single correct answer** — Is exactly one choice correct?
4. **No duplicate options** — Are all 4 choices distinct?
5. **Answer position randomized** — Correct answer not always in same position
6. **Diagnostics meaningful** — Each wrong answer has a specific misconception explanation
7. **Difficulty calibrated** — Rating matches actual complexity for target grade
8. **Hint ladder complete** — All 6 levels present and progressively helpful
9. **Age-appropriate language** — Vocabulary matches grade level
10. **Question mark present** — Stem ends with ? where grammatically expected

### 7.6 Difficulty Levels (Detailed)

| Level | Raw Score | Description |
|-------|-----------|-------------|
| L1 | 1-15 | Direct counting, single-step, visual answer |
| L2 | 16-30 | Simple operation, 2 objects, pattern recognition |
| L3 | 31-45 | Two-step problem, simple reasoning |
| L4 | 46-60 | Multi-step, requires strategy |
| L5 | 61-80 | Competition-level, multiple concepts |
| L6+ | 81-100 | Olympiad-level, creative problem-solving |

---

## 8. Architecture Reference

### 8.1 Backend (Python FastAPI)

| Component | File | Purpose |
|-----------|------|---------|
| Adaptive Engine | `adaptive_engine_v2.py` | IRT model, ability tracking, question selection |
| Gamification | `gamification.py` | Kiwi Brain rewards, state detection, interventions |
| Content Store | `content_store_v2.py` | JSON loader, difficulty queries, grade filtering |
| API | `questions_v2.py` | REST endpoints with grade param + hint support |

**Deployment:** Google Cloud Run (project: kiwimath-801c1, region: asia-south1)

### 8.2 Frontend (Flutter)

| Component | File | Purpose |
|-----------|------|---------|
| Auth | `auth_service.dart` | Firebase email/Google/phone |
| API Client | `api_client.dart` | All v2 endpoints + retry |
| Questions | `question_screen_v2.dart` | 10-Q sessions + gamification UI |
| Hints | `hint_ladder_bar.dart` | 6-level Socratic UI |
| Theme | `kiwi_theme.dart` | Grade-adaptive theming |

### 8.3 Key API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v2/topics` | GET | List topics (with ?grade= filter) |
| `/v2/questions/next` | GET | Get next adaptive question |
| `/v2/answer/check` | POST | Submit answer, get result + rewards |
| `/v2/student/summary` | GET | Student stats, mastery, level |

---

## 9. Product Vision

**"Duolingo for Maths"** — Specifically for Indian K-5 students preparing for math olympiads (Kangaroo, Felix, SOF IMO).

**Design philosophy:**
- Beast Academy depth + Duolingo engagement mechanics
- Every child should feel like a "math person" within 30 days
- Adaptive difficulty means no child is bored AND no child is frustrated
- Socratic hints teach problem-solving, not just answers
- Parent dashboard shows real progress, not just time spent

**Competition style:** Questions modeled after Kangaroo Ecolier, Felix workbooks, and Beast Academy materials — visual, creative, reasoning-based (not rote arithmetic).

---

*This document is the single source of truth for all Kiwimath technical specifications. Update this when formulas or systems change.*
