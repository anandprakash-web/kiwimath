# Kiwimath Adaptive Engine — Research-Backed Plan

## Executive Summary

This document synthesizes findings from academic literature on adaptive learning, IRT, knowledge tracing, mastery-based progression, and spaced repetition to define the architecture for Kiwimath's cross-curriculum adaptive session engine. The goal: build the most effective primary math practice engine by combining proven techniques from psychometrics, cognitive science, and machine learning.

---

## Part 1: Literature Review — What the Research Says

### 1.1 Item Response Theory (IRT) in CAT

**State of the art:** The 3-Parameter Logistic (3PL) model remains the gold standard for computerized adaptive testing in K-12 mathematics. Our current implementation uses:
- P(correct|θ,a,b,c) = c + (1-c)/(1+exp(-a*(θ-b)))
- EAP estimation with Gaussian quadrature (20-point)

**Key finding — Response Time Integration (2025):**
Time-sensitive IRT models significantly improve ability estimation accuracy. The insight: a student who answers correctly in 3 seconds demonstrates deeper mastery than one who takes 45 seconds. Models that integrate log(RT) into the ability update achieve 8-15% better prediction accuracy.

*Reference: "Enhancing Ability Estimation with Time-Sensitive IRT Models in CAT" (Applied Sciences, 2025)*

**Key finding — Multidimensional IRT (MIRT):**
Rather than a single θ per student, MIRT tracks multiple latent dimensions simultaneously. For math, these map naturally to skill domains (arithmetic, geometry, fractions, etc.). MIRT achieves substantial reductions in testing time while maintaining precision by leveraging correlations between dimensions.

*Reference: "A Multidimensional IRT Approach for Dynamically Monitoring Ability Growth" (Frontiers in Psychology, 2019)*

**Our gap:** We currently track θ at the *domain* level (5 domains) but route questions at the *skill* level (37 nodes). The unified planner approximates skill-level θ using domain θ — this is lossy. We need per-skill theta tracking.

---

### 1.2 Knowledge Tracing — BKT vs DKT

**Bayesian Knowledge Tracing (BKT):**
- Models each skill as a hidden Markov model with 4 parameters: P(L₀) initial knowledge, P(T) transition/learning rate, P(G) guess, P(S) slip
- Simple, interpretable, per-skill
- Limitation: degrades as hidden concept count increases; no cross-skill transfer

**Deep Knowledge Tracing (DKT):**
- Uses LSTM/RNN to process the full interaction sequence
- 25% AUC improvement over BKT on Assistments dataset (0.86 vs 0.69)
- Models cross-skill interactions implicitly
- Limitation: black box, requires large data volumes, cold-start problem

**Hybrid BKT-LSTM (2020):**
- Combines BKT's interpretability with LSTM's sequence modeling
- Per-skill BKT parameters provide the "prior", LSTM handles temporal dynamics
- Best of both worlds for small-to-medium datasets

**Our decision:** Start with enhanced BKT (per-skill, with response-time modulation) because:
1. We have 37 well-defined skills — BKT's sweet spot
2. Cold-start: new students have zero interaction history — DKT needs hundreds of responses
3. Interpretability: parents need clear "your child knows X, is learning Y" messages
4. Upgrade path: once we have 10K+ students with full interaction logs, train DKT as a secondary predictor

*References: "Deep Knowledge Tracing" (Stanford, 2015); "BKT-LSTM: Efficient Student Modeling" (2020); "A Survey of Knowledge Tracing" (2021)*

---

### 1.3 Mastery-Based Progression

**Key finding — Zone of Proximal Development (ZPD):**
Adaptive systems that maintain students in their ZPD outperform fixed-curriculum approaches by 0.4+ standard deviations. The ZPD is operationalized as: items where P(correct) is between 0.60 and 0.85 given the student's current ability.

**Key finding — Depth Over Breadth (Singapore Math):**
Singapore Math's CPA approach (Concrete → Pictorial → Abstract) demonstrates that spending more time on fewer topics with genuine mastery produces better long-term outcomes than covering many topics superficially. Students who achieve genuine mastery (sustained accuracy ≥ 85% over multiple sessions) retain skills 3x longer.

**Key finding — My Math Academy RCT (2021):**
A cluster randomized trial showed that ~5 hours of adaptive practice produced statistically significant learning gains, with the greatest effect for students who began with moderate knowledge (i.e., those squarely in their ZPD). The system used knowledge maps of learning objectives and adaptive algorithms to determine what each child is ready to learn next.

**Key finding — Mastery Gating:**
Students should not advance to dependent skills until prerequisites are genuinely mastered. A "mastery event" requires: ≥80% accuracy across ≥5 items on a skill, sustained across ≥2 non-consecutive sessions. Single-session spikes are not mastery.

**Our alignment:** Our prerequisite graph (37 nodes with explicit dependencies) already implements mastery gating structurally. What's missing: the "sustained across sessions" check — we currently declare mastery in a single session.

*References: "Mastery Learning of Early Childhood Mathematics Through Adaptive Technologies" (2019); "Accelerating Early Math Learning with Research-Based Personalized Learning Games" (JESP, 2021)*

---

### 1.4 Spaced Repetition & Forgetting Curves

**Key finding — Optimal Review Intervals:**
The forgetting curve follows an exponential decay. Optimal review spacing targets the moment when P(recall) drops to ~90%. The FSRS algorithm (now in Anki since v23.10) models this as a prediction problem. For educational math skills, meta-analyses show spaced practice benefits of g > 0.40.

**Key finding — Spacing Schedule for Skills:**
- First review: 1 day after mastery
- Second review: 3-4 days
- Third review: 7-8 days  
- Fourth review: 14+ days
- Each successful review doubles the interval

**Key finding — Interleaving > Blocking:**
Mixing different problem types (interleaved practice) produces 43% better retention than blocking (all problems of one type together). This is because interleaving forces retrieval and discrimination between problem types.

**Our implementation:** The current `mistake_tracker` does basic spaced revision (3-day window). We need to upgrade to a proper forgetting-curve model with per-skill decay rates that adapt to the individual student.

*References: "Enhancing Human Learning via Spaced Repetition Optimization" (PNAS, 2019); "Optimizing Spaced Repetition Schedule by Capturing the Dynamics of Memory" (2023)*

---

### 1.5 Cognitive Diagnosis & Skill Deficiency Detection

**Key finding — Cognitive Diagnosis Models (CDM):**
Beyond simple ability estimation, CDMs identify exactly which sub-skills a student has mastered and which have gaps. The Q-matrix maps items to required skills, enabling precise diagnosis. For a student who fails a multi-step problem, CDM can determine whether the failure is in "reading the problem," "setting up the equation," or "executing the arithmetic."

**Key finding — Diagnostic Feedback:**
Systems that provide specific cognitive diagnosis (not just right/wrong) to learners show 25-30% better learning gains. The feedback should identify the specific misconception, not just that an error occurred.

**Our alignment:** We already have per-distractor diagnostic messages ("You added instead of subtracted — the digit in the tens place needs borrowing"). Our Q-matrix equivalent is the TAG_RULES in skill_mapper.py. What's missing: tracking *which* sub-skills within a skill node cause failures.

*Reference: "Development of a Computerized Adaptive Assessment and Learning System for Mathematical Ability Based on Cognitive Diagnosis" (PMC, 2025)*

---

## Part 2: What We're Already Doing Right

| Research Principle | Our Implementation | Status |
|---|---|---|
| 3PL IRT model | `irt_model.py` — full 3PL with EAP estimation | ✅ Complete |
| Prerequisite skill graph | `path_engine.py` — 37 nodes, 5 domains, explicit deps | ✅ Complete |
| Cross-curriculum content pool | `content_store_v2.py` — 21,330 questions from 5 curricula | ✅ Complete |
| Skill-level question mapping | `skill_mapper.py` — tag/topic/curriculum → skill | ✅ Complete |
| Mastery gating | Prerequisite check in unified planner | ✅ Complete |
| ZPD targeting | Questions picked at target difficulty ± window | ✅ Complete |
| Interleaved practice | Session mixes skills (warmup/core/stretch/review) | ✅ Complete |
| Per-distractor diagnostics | All 21,330 questions have specific error feedback | ✅ Complete |
| Basic spaced revision | `mistake_tracker.py` — 3-day review cycle | ✅ Partial |
| Parent communication | `generate_session_summary()` in unified planner | ✅ Complete |
| Adaptive difficulty | `theta_to_difficulty()` maps ability → question level | ✅ Complete |

---

## Part 3: Gaps to Fill — Research-Driven Enhancements

### Gap 1: Per-Skill Theta Tracking (Priority: CRITICAL)

**Current:** θ tracked at domain level (5 values per student)
**Needed:** θ tracked at skill level (37 values per student)
**Why:** A student may be strong in "addition_2digit" but weak in "subtraction_2digit" — same domain, different skills. Domain-level theta blurs this.

**Implementation:**
```
SkillAbility:
  skill_id: str
  theta: float           # Current ability estimate
  se: float              # Standard error
  n_responses: int       # Total responses on this skill
  n_correct: int         # Correct responses
  last_response_time: datetime
  mastery_confirmed: bool
  mastery_sessions: int  # Sessions with ≥80% on this skill
```

**Architecture:** Store in Firestore at `users/{uid}/skill_abilities/{skill_id}`. Update after every response using EAP with the skill-specific prior (initialize from domain theta).

---

### Gap 2: Response Time Integration (Priority: HIGH)

**Current:** Response time not used in ability estimation
**Needed:** Log(RT) modulates the ability update magnitude

**Model (Time-Weighted IRT):**
```
If correct AND fast (RT < median for this difficulty): θ update × 1.3
If correct AND slow (RT > 2× median): θ update × 0.7
If incorrect AND fast (< 5s): likely careless error, θ penalty × 0.5
If incorrect AND slow: genuine difficulty, full θ penalty
```

**Why this matters for kids:** Children often tap randomly when frustrated (fast + wrong = careless, not inability) or take long because they're distracted (slow + correct = still mastery). RT disambiguates these cases.

---

### Gap 3: Sustained Mastery Verification (Priority: HIGH)

**Current:** Mastery declared in single session (≥80% accuracy)
**Needed:** Mastery requires confirmation across multiple sessions

**Algorithm:**
```
mastery_confirmed = (
    accuracy >= 0.80 on this skill
    AND n_responses >= 5 on this skill
    AND successful_sessions >= 2 (non-consecutive days)
)
```

**On mastery confirmation:**
1. Mark skill as mastered
2. Schedule first review at +3 days
3. Unlock dependent skills in prerequisite graph
4. Generate parent notification: "Aarav has mastered two-digit addition!"

---

### Gap 4: Proper Forgetting Curve Model (Priority: MEDIUM)

**Current:** Fixed 3-day review window
**Needed:** Per-skill exponential decay with adaptive intervals

**FSRS-Lite Model (simplified for primary math):**
```
stability(skill) = base_stability × (1 + success_multiplier)^n_reviews
next_review_day = stability × (-log(0.9) / decay_rate)

Where:
  base_stability = 1.0 (days)
  success_multiplier = 2.0 (doubles interval each time)
  decay_rate = varies per skill type:
    - Procedural skills (addition, multiplication): 0.3 (slower decay)
    - Conceptual skills (fractions, place value): 0.5 (faster decay)
    - Spatial skills (geometry, symmetry): 0.4
```

**Integration:** The session planner checks which mastered skills have `days_since_last_practice > next_review_day` and inserts 2-3 review items per session.

---

### Gap 5: Cross-Skill Transfer Modeling (Priority: MEDIUM)

**Current:** Skills are independent — mastering "addition_basic" doesn't inform "addition_2digit"
**Needed:** Prerequisite mastery provides a prior boost to dependent skills

**Model:**
```
When skill A (prerequisite) is mastered:
  For each dependent skill B:
    θ_B_prior = max(θ_B_current, θ_A × transfer_coefficient)
    
Transfer coefficients (from prerequisite graph):
  Direct prereq: 0.6 (strong transfer)
  2-hop prereq: 0.3 (moderate transfer)
  Same-domain peer: 0.2 (weak transfer)
```

**Why:** A child who masters "fraction_concept" likely has partial knowledge of "fraction_compare" before being tested on it. Starting with a better prior means fewer warm-up questions are needed.

---

### Gap 6: Session-Level Learning Rate Detection (Priority: LOW)

**Current:** Fixed learning rate assumptions
**Needed:** Detect within-session learning curves to adjust pacing

**Signal:** If a student gets the first 2 questions wrong on a new skill but then gets the next 3 right, they're learning fast → give them harder items immediately (don't wait for next session).

**Algorithm:**
```
within_session_trend = (accuracy_last_3 - accuracy_first_3) on same skill
if within_session_trend > 0.5:
    # Fast learner on this skill — accelerate
    target_difficulty += 10
    reduce remaining items on this skill
elif within_session_trend < -0.3:
    # Struggling — scaffold
    target_difficulty -= 10
    add one more item on this skill
```

---

## Part 4: Execution Phases

### Phase 1: Per-Skill Theta + Sustained Mastery (Week 1)

**Deliverables:**
1. `skill_ability_store.py` — Firestore CRUD for per-skill theta (37 skills × N students)
2. Update `unified_session_planner.py` to use skill-level theta (not domain approximation)
3. Add mastery confirmation logic (2-session requirement)
4. Parent notification on mastery events
5. API endpoint: `GET /v2/skills/progress` — returns all 37 skill thetas for a student

**Migration:** Initialize all existing students' skill thetas from their domain theta (one-time backfill).

---

### Phase 2: Response Time Integration (Week 1-2)

**Deliverables:**
1. Add `response_time_ms` field to answer submission API
2. Build `time_weighted_updater.py` — modulates theta updates based on RT
3. Compute per-difficulty median RT from historical data (bootstrap with population medians)
4. Update Flutter to capture and submit response timestamps
5. Add RT-based careless error detection (fast + wrong → reduced penalty)

---

### Phase 3: Forgetting Curve + Smart Review (Week 2)

**Deliverables:**
1. `spaced_review_engine.py` — per-skill stability tracking with FSRS-lite
2. Replace fixed 3-day review window with adaptive scheduling
3. Different decay rates for procedural vs. conceptual vs. spatial skills
4. Session planner integrates review slots based on which skills are "due"
5. Parent weekly report includes: "Skills reviewed this week" + "Skills due for review"

---

### Phase 4: Cross-Skill Transfer + Learning Rate (Week 3)

**Deliverables:**
1. Transfer coefficient matrix (derived from prerequisite graph distances)
2. Prior boost on skill unlock (dependent skill gets warm start)
3. Within-session learning rate detection (accelerate/decelerate pacing)
4. API: `POST /v2/session/adjust` — mid-session difficulty adjustment based on real-time performance

---

### Phase 5: Parent Intelligence Layer (Week 3-4)

**Deliverables:**
1. Per-session parent message (what was practiced, how they did, what's next)
2. Weekly digest (skills mastered, skills progressing, review performance)
3. Milestone celebrations (mastery events, level-ups, streak achievements)
4. Actionable recommendations ("Aarav is close to mastering fractions — 2 more sessions!")
5. Comparative context ("On track for Grade 4 math" — without peer comparison)

---

## Part 5: Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Flutter Client                             │
│  [Start Session] → POST /v2/session/plan                     │
│  [Answer Q] → POST /v2/answer/check (includes response_time) │
│  [View Progress] → GET /v2/skills/progress                   │
└─────────────────────────────────┬───────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│                    FastAPI Backend                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐   ┌──────────────────┐                 │
│  │  Unified Session │   │  Answer Processor │                │
│  │  Planner v2      │   │  (IRT + RT update)│                │
│  └────────┬─────────┘   └────────┬─────────┘                │
│           │                       │                          │
│  ┌────────▼─────────────────────────────────┐                │
│  │         Skill Ability Store               │                │
│  │  (37 per-skill thetas per student)        │                │
│  └────────┬──────────────────────────────────┘                │
│           │                                                  │
│  ┌────────▼───────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  Skill Mapper   │  │ Spaced Review │  │ Transfer Engine │  │
│  │  (21,330 Q→skill)│  │ (FSRS-lite)  │  │ (prereq boost) │  │
│  └────────┬───────┘  └──────┬───────┘  └────────┬────────┘  │
│           │                  │                    │           │
│  ┌────────▼──────────────────▼────────────────────▼────────┐  │
│  │            Content Store v2 (ALL curricula)              │  │
│  │  Olympiad: 12,185 | NCERT: 4,373 | ICSE: 2,372         │  │
│  │  Singapore: 1,200 | USCC: 1,200 = 21,330 total         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Parent Intelligence Layer                               │  │
│  │  - Per-session summary   - Weekly digest                 │  │
│  │  - Mastery notifications - Actionable recommendations    │  │
│  └─────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│                    Firestore                                  │
│  users/{uid}/skill_abilities/{skill_id}                      │
│  users/{uid}/interaction_log/{timestamp}                     │
│  users/{uid}/review_schedule/{skill_id}                      │
│  users/{uid}/mastery_events/{skill_id}                       │
└──────────────────────────────────────────────────────────────┘
```

---

## Part 6: Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Prediction accuracy (AUC) | ~0.70 (estimated) | 0.82+ | Holdout validation on responses |
| Question-level ZPD hit rate | Unknown | 70%+ | % questions where P(correct) ∈ [0.60, 0.85] |
| Mastery retention at 30 days | Unknown | 85%+ | Review quiz accuracy 30 days post-mastery |
| Session completion rate | Unknown | 90%+ | % sessions where student finishes all 10 Qs |
| Parent message open rate | N/A (new) | 60%+ | Push notification engagement |
| Skill coverage per week | ~3 skills | 6+ skills | Unique skills practiced per student per week |
| Time to mastery (per skill) | Unknown | <15 sessions | Avg sessions from first encounter to confirmed mastery |

---

## Part 7: Research-Backed Decisions Summary

| Decision | Research Basis | Alternative Considered | Why Not |
|----------|---------------|----------------------|---------|
| BKT over DKT (for now) | BKT works with small N, interpretable | DKT (LSTM) | Cold-start, black-box, needs 10K+ students |
| Per-skill theta (37 dimensions) | MIRT literature shows precision gains | Domain-level only (5 dims) | Too coarse for mastery gating |
| Response time integration | 8-15% accuracy gain in recent studies | Ignore RT | Misses careless errors and guessing |
| FSRS-lite for review scheduling | PNAS paper + Anki real-world validation | Fixed intervals | Doesn't adapt to individual forgetting rates |
| 2-session mastery confirmation | Singapore Math research on sustained mastery | Single-session threshold | Single spikes don't indicate true learning |
| Interleaved practice sessions | 43% retention benefit over blocked practice | Topic-focused sessions | Blocks feel efficient but produce poor retention |
| ZPD targeting (P=0.60-0.85) | Meta-analyses, My Math Academy RCT | Fixed difficulty bands | One-size-fits-all fails diverse learners |
| Transfer coefficients from prereq graph | Cognitive science on skill transfer | Independent skill estimates | Ignores structural relationships between skills |

---

## Part 8: Immediate Next Steps

1. **Build `skill_ability_store.py`** — per-skill theta CRUD with Firestore persistence
2. **Update the unified session planner** — swap domain-theta calls for skill-theta
3. **Add response_time to answer API** — capture RT from Flutter, use in theta update
4. **Implement sustained mastery check** — 2-session confirmation before declaring mastery
5. **Wire parent notifications** — mastery events trigger push messages
6. **Build FSRS-lite review engine** — replace 3-day fixed window with adaptive intervals

This is the execution order. Each phase builds on the previous. The system becomes incrementally smarter with each addition.

---

*Document created: 2 May 2026*
*Based on: 15+ academic papers spanning IRT, knowledge tracing, mastery learning, spaced repetition, and cognitive diagnosis (2015-2025)*
