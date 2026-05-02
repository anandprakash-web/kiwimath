# Kiwimath Assessment Engine — Architecture Document

**Version:** 2.0  
**Date:** May 1, 2026  
**Status:** Implemented — 4 curricula, 6600 items, full CAT + Path + Spaced Rep live

---

## 1. Overview

The Kiwimath Assessment Engine is a production-grade adaptive testing system that measures student mathematical ability, generates personalized learning paths, and continuously improves its question bank through data-driven calibration.

**Core principles:**
- Psychometrically rigorous (3-Parameter IRT)
- Curriculum-aware (NCERT, Singapore, Olympiad, US Core, ICSE)
- Age-appropriate (short sessions, gamified, encouraging)
- Self-improving (items get better with every student response)

---

## 2. Item Response Theory — 3PL Model

Each question item is characterized by three parameters:

```
P(correct | θ) = c + (1 - c) / (1 + exp(-a(θ - b)))
```

| Parameter | Symbol | Meaning | Typical Range |
|-----------|--------|---------|---------------|
| Discrimination | a | How well the item differentiates ability levels | 0.5 – 2.5 |
| Difficulty | b | Ability level where P(correct) = midpoint | -3.0 – +3.0 |
| Guessing | c | Probability of getting right by chance | 0.15 – 0.25 (MCQ) |

**Why 3PL over simpler models:**
- 1PL (Rasch) assumes all items discriminate equally — unrealistic
- 2PL ignores guessing — critical for MCQ-based assessment of young children
- 3PL accounts for the reality that a Grade 1 student might guess correctly on a Grade 4 question

---

## 3. Computerized Adaptive Testing (CAT) Engine

### 3.1 Algorithm Flow

```
1. Initialize: θ₀ = 0 (or prior from historical data)
2. SELECT: Choose item with maximum Fisher Information at current θ
3. PRESENT: Show item to student
4. RESPOND: Student answers
5. UPDATE: Recalculate θ via Expected A Posteriori (EAP)
6. CHECK: Stopping rule met?
   - YES → Report final θ and SE
   - NO → Go to step 2
```

### 3.2 Item Selection Strategy

**Primary:** Maximum Fisher Information
```python
I(θ) = a² * (P - c)² / ((1 - c)² * P * (1 - P))
# Select item where I(θ_current) is maximized
```

**Constraints:**
- Exposure control: No item shown to >20% of students (Sympson-Hetter method)
- Content balancing: Ensure coverage across domains within assessment
- Recency: Don't repeat items seen in last 30 days

### 3.3 Stopping Rules

| Condition | Threshold | Rationale |
|-----------|-----------|-----------|
| Standard Error | SE < 0.30 | Reliable estimate achieved |
| Maximum items | 25 per domain | Prevent fatigue (young learners) |
| Minimum items | 8 per domain | Enough data for stability |
| Time limit | 15 minutes per session | Age-appropriate attention span |

### 3.4 Age-Appropriate Session Design

| Grade | Items per session | Sessions for full diagnostic | Total items |
|-------|-------------------|------------------------------|-------------|
| 1–2 | 10–12 | 3 | ~33 |
| 3–4 | 12–15 | 3 | ~40 |
| 5–6 | 15–20 | 2–3 | ~45 |

Sessions are gamified with streaks, stars, and encouraging animations between items to hide the "test" feeling.

---

## 4. KiwiScore — Vertical Scale

### 4.1 Design

Instead of raw θ values (-3 to +3), we report a **KiwiScore** on a familiar, growing scale (inspired by MAP Growth RIT scores):

```
KiwiScore = 200 + (θ × 30)
```

Centers Grade 3–4 at 200. Each standard deviation = 30 points.

### 4.2 Grade-Level Norms

| Grade | KiwiScore Range | Percentile Anchors (P25/P50/P75) |
|-------|----------------|-----------------------------------|
| Grade 1 | 100–140 | 110 / 120 / 130 |
| Grade 2 | 130–170 | 140 / 150 / 160 |
| Grade 3 | 160–200 | 170 / 180 / 190 |
| Grade 4 | 190–230 | 200 / 210 / 220 |
| Grade 5 | 220–260 | 230 / 240 / 250 |
| Grade 6 | 250–300 | 260 / 270 / 280 |

### 4.3 Properties

- **Vertical:** A score of 220 means the same thing whether the student is in Grade 3 or Grade 5
- **Growth-sensitive:** Parents see the number go up over months
- **Cross-curriculum:** Same scale regardless of NCERT/Singapore/Olympiad track
- **Domain-specific:** Separate KiwiScores per mathematical domain

---

## 5. Domain-Level Diagnostic

### 5.1 Domains

Each student gets a separate ability estimate (θ) per domain:

| Domain | Items in Diagnostic | Skills Measured |
|--------|-------------------|-----------------|
| Numbers & Place Value | 8–12 | Counting, place value, comparison, number sense |
| Arithmetic Operations | 8–12 | Addition, subtraction, multiplication, division fluency |
| Fractions & Decimals | 6–10 | Fraction concepts, operations, decimal conversion |
| Geometry & Spatial | 6–10 | Shapes, symmetry, spatial reasoning, coordinate basics |
| Measurement & Data | 6–10 | Length, weight, time, money, data interpretation |

### 5.2 Output

```json
{
  "student_id": "abc123",
  "assessment_date": "2026-05-01",
  "overall_kiwiscore": 185,
  "domain_scores": {
    "numbers": { "theta": 0.3, "kiwiscore": 209, "se": 0.28, "grade_equiv": 4.2 },
    "arithmetic": { "theta": -0.5, "kiwiscore": 185, "se": 0.25, "grade_equiv": 3.4 },
    "fractions": { "theta": -1.2, "kiwiscore": 164, "se": 0.31, "grade_equiv": 2.8 },
    "geometry": { "theta": 0.1, "kiwiscore": 203, "se": 0.29, "grade_equiv": 3.9 },
    "measurement": { "theta": -0.3, "kiwiscore": 191, "se": 0.27, "grade_equiv": 3.5 }
  },
  "recommended_track": "school_focus",
  "priority_domains": ["fractions", "arithmetic"]
}
```

---

## 6. Path Recommendation Engine

### 6.1 Prerequisite Graph

```
counting → addition → multiplication → division → fractions
place_value → addition → subtraction → decimals
shapes_2d → symmetry → area → perimeter
addition → word_problems_add → multi_step_problems
multiplication → factors → lcm_hcf → fractions_operations
```

### 6.2 Recommendation Algorithm

```python
def generate_path(student_profile, curriculum, grade):
    gaps = []
    
    for domain, score in student_profile.domain_scores.items():
        expected = grade_level_expectation(grade, domain, curriculum)
        if score.theta < expected:
            # Find which prerequisite skills are weak
            weak_skills = find_weak_prerequisites(domain, score, curriculum)
            gaps.extend(weak_skills)
    
    # Topological sort by prerequisite order
    ordered_gaps = topological_sort(gaps, prerequisite_graph)
    
    # Assign to tracks
    path = {
        "foundation": [g for g in ordered_gaps if g.grade_level < grade - 1],
        "school": [g for g in ordered_gaps if grade - 1 <= g.grade_level <= grade],
        "accelerate": get_above_grade_topics(student_profile, curriculum)
    }
    
    return path
```

### 6.3 Track Definitions

| Track | Target Students | Content | Shown to Parents As |
|-------|----------------|---------|---------------------|
| 🔧 Foundation | >1 grade behind in any domain | Fill prerequisite gaps from earlier grades | "Building strong basics" |
| 🏫 School | At or slightly below grade level | Curriculum-aligned grade-level content | "Keeping pace with school" |
| 🚀 Accelerate | At or above grade level | Singapore Math, Olympiad prep, next grade | "Going beyond" |

### 6.4 Path Updates

- Re-assessed every 2 weeks (mini-CAT of 8 items on focus domains)
- Path adjusts dynamically based on practice performance
- Students can "graduate" from Foundation → School → Accelerate

---

## 7. Spaced Repetition Layer (HLR-Inspired)

### 7.1 Model

Based on Duolingo's Half-Life Regression:

```
P(recall) = 2^(-Δt / h)

where:
  Δt = time since last practice (hours)
  h = half-life of memory for this skill
  h = 2^(θ_strength) × base_decay
```

### 7.2 Scheduling Logic

```python
def get_review_priority(skill, current_time):
    delta_t = current_time - skill.last_practiced
    half_life = 2 ** skill.strength * BASE_DECAY_HOURS
    p_recall = 2 ** (-delta_t / half_life)
    
    if p_recall < 0.7:  # Below threshold → schedule review
        return 1.0 - p_recall  # Higher priority for more decayed skills
    return 0  # No review needed yet

def update_strength(skill, correct):
    if correct:
        skill.strength += 0.4  # Strengthen memory
        skill.consecutive_correct += 1
    else:
        skill.strength = max(0, skill.strength - 0.8)  # Decay faster on errors
        skill.consecutive_correct = 0
```

### 7.3 Integration with Practice Sessions

- After initial assessment, daily practice sessions mix:
  - 40% new content (from learning path)
  - 30% spaced review (decaying skills)
  - 30% adaptive practice (at current θ boundary)

---

## 8. Item Quality & Continuous Improvement

### 8.1 Item Lifecycle

```
DRAFT → REVIEW → FIELD_TEST → ACTIVE → MONITOR → RETIRED
```

| State | Description | Data Required |
|-------|-------------|---------------|
| DRAFT | Expert-authored, initial parameter estimates | None |
| REVIEW | Editorial + pedagogical review passed | None |
| FIELD_TEST | Live but unscored (doesn't affect KiwiScore) | 0–199 responses |
| ACTIVE | Fully calibrated, used in scored assessments | 200+ responses |
| MONITOR | Under review due to flagged metrics | Ongoing |
| RETIRED | Removed from active bank | N/A |

### 8.2 Item Health Metrics

Every item is continuously monitored:

| Metric | Healthy Range | Flag Threshold | Action |
|--------|---------------|----------------|--------|
| Discrimination (a) | 0.5 – 2.5 | < 0.3 or > 3.0 | Review wording |
| Fit residual | < 2.0 | > 3.0 | Investigate misfit |
| Exposure rate | < 15% | > 20% | Reduce selection probability |
| Avg response time | 15–90 sec | < 5 sec or > 180 sec | Check clarity |
| Distractor effectiveness | All options chosen by >5% | Any option < 3% | Revise distractors |
| Differential Item Functioning | Near zero | |d| > 0.5 | Check for curriculum bias |

### 8.3 Empirical Calibration Pipeline

```python
# Weekly batch job
def recalibrate_items():
    responses = load_responses(last_7_days)
    
    for item in active_items:
        item_responses = responses.filter(item_id=item.id)
        if len(item_responses) >= 50:  # Enough new data
            # Marginal Maximum Likelihood estimation
            new_params = estimate_3pl_params(item_responses)
            
            # Check for significant drift
            if param_drift(item.params, new_params) > DRIFT_THRESHOLD:
                flag_for_review(item, reason="parameter_drift")
            else:
                item.params = weighted_average(item.params, new_params, weight=0.3)
                item.last_calibrated = now()
    
    # Report item bank health
    generate_health_report()
```

### 8.4 The Flywheel Effect

```
More students using the app
  → More response data per item
    → More precise item calibration
      → More accurate ability estimates
        → Better item selection (fewer items needed)
          → Shorter, less fatiguing tests
            → Better student experience & retention
              → More students using the app
```

**Scale milestones:**

| Students | Data Volume | Capability Unlocked |
|----------|-------------|---------------------|
| 100 | ~5K responses/week | Basic field testing |
| 1,000 | ~50K responses/week | Full empirical calibration |
| 10,000 | ~500K responses/week | DIF analysis, norm tables |
| 100,000 | ~5M responses/week | AI item generation, micro-norms |

### 8.5 AI-Assisted Item Generation (Phase 3)

Once we have 50K+ calibrated responses:

```python
# Train difficulty predictor from item features
features = extract_features(item_text)
# - number magnitude, operation count, step count
# - vocabulary complexity, context familiarity
# - visual component (yes/no), distractor similarity

model = train_difficulty_predictor(features, empirical_b_values)

# Generate new items targeting specific difficulty
target_b = 0.5  # Slightly above average difficulty
prompt = generate_item_prompt(domain="fractions", target_b=target_b, grade=4)
candidate = llm_generate(prompt)
predicted_params = model.predict(extract_features(candidate))

# Field test if prediction matches target
if abs(predicted_params.b - target_b) < 0.3:
    queue_for_field_test(candidate)
```

---

## 9. Multi-Curriculum Support

### 9.1 Item Tagging

Each item is tagged with:

```json
{
  "item_id": "ARITH_MUL_042",
  "curriculum_tags": ["NCERT_4_7", "SING_3B_5", "USCC_4_OA_1"],
  "domain": "arithmetic",
  "subdomain": "multiplication",
  "cognitive_level": "apply",
  "grade_range": [3, 5],
  "params": { "a": 1.2, "b": 0.4, "c": 0.22 },
  "context": "indian"  // or "international", "singapore", "american"
}
```

### 9.2 Curriculum-Specific Assessment

The CAT engine filters items by curriculum when assessing:
- NCERT assessment → only NCERT-tagged items
- Singapore assessment → only Singapore-tagged items
- Cross-curriculum diagnostic → uses all items, reports per-curriculum readiness

### 9.3 Curriculum Gap Detection

After diagnostic, the system identifies:
- "You're at Singapore Grade 4 level but NCERT Grade 3 level in fractions" → suggests NCERT fraction practice
- "Ready for Olympiad Number Theory but need Geometry foundation" → prioritizes Geometry in Olympiad track

---

## 10. Technical Implementation

### 10.1 Backend Architecture

```
kiwimath-backend/
├── assessment/
│   ├── cat_engine.py          # CAT loop, item selection, θ estimation
│   ├── item_bank.py           # Item CRUD, parameter storage
│   ├── scoring.py             # θ → KiwiScore, grade equivalents
│   ├── path_engine.py         # Prerequisite graph, track assignment
│   ├── spaced_rep.py          # HLR scheduling
│   └── calibration.py         # Batch recalibration job
├── models/
│   ├── item.py                # Item schema (params, tags, health)
│   ├── student_ability.py     # Per-domain θ history
│   ├── response.py            # Response log (item, correct, time, θ)
│   └── learning_path.py       # Assigned path + progress
├── api/
│   ├── assess.py              # /assess/start, /assess/respond, /assess/result
│   ├── practice.py            # /practice/next-session, /practice/submit
│   └── reports.py             # /reports/kiwiscore, /reports/growth
└── jobs/
    ├── calibrate.py           # Weekly item recalibration
    ├── health_check.py        # Daily item health monitoring
    └── norm_update.py         # Monthly norm table refresh
```

### 10.2 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/assess/start` | POST | Begin diagnostic assessment for a domain |
| `/assess/next-item` | GET | Get next adaptive item |
| `/assess/respond` | POST | Submit response, get updated θ |
| `/assess/result` | GET | Final scores + path recommendation |
| `/practice/session` | GET | Get next practice session (new + review mix) |
| `/practice/submit` | POST | Submit practice responses, update HLR |
| `/reports/kiwiscore` | GET | Current scores + history |
| `/reports/growth` | GET | Growth over time for parent dashboard |
| `/reports/path` | GET | Current learning path + progress |

### 10.3 Technology Stack

| Component | Technology | Reason |
|-----------|-----------|--------|
| IRT/CAT Engine | `catsim` (Python) | Battle-tested, MIT license, full 3PL |
| API Server | FastAPI | Async, fast, auto-docs |
| Database | Firestore | Already in stack, real-time sync to Flutter |
| Response Log | BigQuery | Analytics, batch calibration at scale |
| Hosting | Cloud Run | Auto-scaling, pay-per-use |
| Scheduled Jobs | Cloud Scheduler | Weekly calibration triggers |
| Item Bank Cache | Redis | Fast item lookup during CAT |

### 10.4 Data Schema (Firestore)

```
items/{item_id}
  ├── text: string
  ├── options: array
  ├── correct_answer: int
  ├── domain: string
  ├── subdomain: string
  ├── curriculum_tags: array
  ├── params: { a: float, b: float, c: float }
  ├── health: { discrimination: float, fit: float, exposure: int }
  ├── state: "field_test" | "active" | "retired"
  └── created_at, last_calibrated: timestamp

students/{uid}/ability/{domain}
  ├── theta: float
  ├── se: float
  ├── kiwiscore: int
  ├── last_assessed: timestamp
  └── history: array[{ date, theta, se }]

responses/{response_id}
  ├── student_id: string
  ├── item_id: string
  ├── correct: boolean
  ├── response_time_ms: int
  ├── theta_before: float
  ├── theta_after: float
  ├── session_id: string
  └── timestamp: timestamp

paths/{uid}
  ├── track: "foundation" | "school" | "accelerate"
  ├── curriculum: string
  ├── focus_domains: array
  ├── skills_queue: array[{ skill, priority, status }]
  └── last_updated: timestamp
```

---

## 11. Parent Dashboard

### 11.1 Visualizations

- **KiwiScore trend line** — monthly growth with grade-level bands
- **Domain radar chart** — 5-axis showing relative strengths
- **Track progress** — percentage through current learning path
- **Comparison to grade norms** — percentile rank (optional, parent chooses to see or hide)

### 11.2 Actionable Insights

```
"Riya's KiwiScore grew from 165 to 192 this month (+27 points).
She's now performing at mid-Grade 3 level overall.

Strongest area: Geometry (Grade 4.1 equivalent)
Focus area: Fractions (Grade 2.8 equivalent — below grade level)

Recommended: 10 minutes daily on fraction practice will close this gap in ~3 weeks."
```

---

## 12. Implementation Phases

### Phase 1: Foundation ✅ COMPLETE
- [x] Custom 3PL IRT engine (no catsim dependency)
- [x] CAT engine with Maximum Fisher Information item selection
- [x] KiwiScore vertical scale (200 + θ×30)
- [x] 6,600 calibrated items across 4 curricula
- [x] 9 REST endpoints (/assess/start, /next-item, /respond, /result, /full-diagnostic, /report, /end, /spaced-review, /item-bank/stats)
- [x] Path recommendation with prerequisite graph (40+ skill nodes)

### Phase 2: Practice Engine ✅ COMPLETE
- [x] Half-Life Regression spaced repetition
- [x] Session mixer (40% new, 30% review, 30% adaptive)
- [x] Spaced review endpoint with recall probability + priority queue
- [x] Flutter assessment flow connected

### Phase 3: Calibration Pipeline ✅ COMPLETE
- [x] Item calibration engine (JMLE + MML)
- [x] Infit/outfit mean-square fit statistics
- [x] Item drift detection (threshold: 0.3)
- [x] DIF analysis for curriculum fairness (NCERT vs Singapore)
- [x] Blended parameter updates (30% weight for stability)

### Phase 4: Multi-Curriculum Content ✅ COMPLETE
- [x] NCERT: 3,000 questions (Grades 1-6, 500/grade)
- [x] Singapore Math: 1,200 questions (Grades 1-6, 200/grade)
- [x] US Common Core: 1,200 questions (Grades 1-6, 200/grade)
- [x] ICSE: 1,200 questions (Grades 1-6, 200/grade)
- [x] Per-curriculum content stores with Flutter-ready payloads
- [x] Static SVG serving for all visual assets
- [x] Assessment bank: 6,600 items with IRT parameters

### Phase 5: Intelligence Layer (In Progress)
- [x] Prerequisite graph with topological sorting
- [x] Dynamic path generation (Foundation/School/Accelerate tracks)
- [x] Grade norm tables for percentile reporting
- [x] Parent dashboard with growth reports + summary generation
- [ ] AI item generation pipeline
- [ ] Population-based norm recalibration from live data

---

## 13. Key References

| Resource | Use |
|----------|-----|
| catsim (Python) | Core IRT/CAT implementation |
| NWEA MAP Growth Technical Report 2024–2025 | Vertical scale design, norm tables methodology |
| Duolingo Half-Life Regression (Settles & Meeder, 2016) | Spaced repetition model |
| IRT Parameter Estimation (de Ayala, 2009) | Theoretical foundation for calibration |
| adaptivetesting (Python) | Alternative CAT library (backup) |
| EduCAT (Python) | Reference for exposure control |

---

## 14. Success Metrics

| Metric | Target (6 months) | Target (12 months) |
|--------|-------------------|---------------------|
| Assessment reliability (Cronbach's α) | > 0.85 | > 0.90 |
| Average items to converge | < 20 | < 15 |
| Item bank size (active) | 6,600 ✅ | 10,000+ |
| Calibrated items (200+ responses) | 200 | 1,500 |
| Path recommendation accuracy | 70% follow-through | 85% follow-through |
| KiwiScore test-retest correlation | > 0.88 | > 0.92 |
| Student engagement (complete assessment) | 80% | 90% |

---

---

## 15. Content Inventory (Current)

| Curriculum | Grades | Questions | SVG Visuals | IRT Calibrated |
|------------|--------|-----------|-------------|----------------|
| NCERT | 1-6 | 3,000 | ~1,914 | ✅ All |
| Singapore Math | 1-6 | 1,200 | ~797 | ✅ All |
| US Common Core | 1-6 | 1,200 | ~540 | ✅ All |
| ICSE | 1-6 | 1,200 | ~555 | ✅ All |
| **TOTAL** | | **6,600** | **~3,806** | **6,600** |

### Domain Distribution (Assessment Bank)

| Domain | Items | Percentage |
|--------|-------|-----------|
| Arithmetic | 1,800 | 27.3% |
| Measurement | 1,528 | 23.2% |
| Numbers | 1,448 | 21.9% |
| Fractions | 1,001 | 15.2% |
| Geometry | 823 | 12.5% |

---

*Document maintained by Kiwimath Engineering. Last updated: May 1, 2026.*
