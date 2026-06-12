# Content Quality Gate — Kiwimath

> "The adaptive engine only adapts bad content faster."
> The moat is content quality + explanation quality + parent trust + child delight.

---

## The 7-Gate Framework

Every question in Kiwimath must pass ALL 7 gates before reaching production.
A single failure blocks the question until fixed.

---

### Gate 1: Mathematical Correctness

| Check | Pass criteria | Fail example |
|-------|--------------|--------------|
| Correct answer is actually correct | Verified by 2+ methods | "What is 7×8?" answer marked as 54 |
| All distractors are wrong | None match correct answer | Duplicate of correct in options |
| No ambiguous stems | One clear interpretation | "Take away 3" (from what?) |
| Units consistent | Same units in stem + options | Stem asks cm, options in mm |
| Number ranges age-appropriate | Within grade capability | Grade 1 question uses 3-digit numbers |

**Automated checks:**
- `answer_validator.py` — recomputes correct answer from stem
- Option deduplication scan
- Number range vs grade level matrix

---

### Gate 2: Pedagogical Validity

| Check | Pass criteria | Fail example |
|-------|--------------|--------------|
| Concept matches grade | Aligned to curriculum scope | Fractions in Grade 1 |
| Prerequisite skills present | Student should know prereqs | Order of ops before multiplication |
| Cognitive load appropriate | One concept per question | Multi-step + carry + word problem |
| Stem language age-matched | Words a 6-year-old knows (G1) | "Determine the quotient" for Grade 1 |
| No trick questions | Tests understanding, not trickery | Deliberately misleading wording |

**Automated checks:**
- Grade-concept alignment matrix validation
- Reading level analysis (Flesch-Kincaid)
- Prerequisite graph verification

---

### Gate 3: Hint Quality (3-Layer Scaffolding with Option Elimination)

Hints follow the 3-Layer protocol and interact with the UI:

| Layer | Content type | UI effect | Check | Fail example |
|-------|-------------|-----------|-------|--------------|
| **Layer 1: Cognitive Nudge** | Remind them of the "Goal" — what concept applies | No change to options | Must activate correct schema | Generic: "Think carefully" |
| **Layer 2: Strategic Bridge** | "How-to" without the numbers | One wrong option fades out | Must guide without giving answer | "The answer is between 50 and 60" |
| **Layer 3: Visual Scaffolding** | Show a visual model or worked example | Options reduce to 50/50 | Must leave final step to child | Hint 3 IS the answer |

| Additional checks | Pass criteria | Fail example |
|-------|--------------|--------------|
| Never gives the answer | Guides thinking, doesn't tell | "The answer is 12" |
| Progressive revelation | Each layer closer but not there | All 3 hints say the same thing differently |
| Final hint leaves ONE step | Child does last step themselves | Hint 3 is just "add 4+4+4" when answer IS 12 |
| Language matches level | Same vocabulary constraints | "Decompose the addend" for Level 1-2 |

**Quality rubric (score 1-5):**
- 5: Perfect Socratic ladder, child discovers answer; UI fades are pedagogically chosen
- 4: Good scaffolding, slightly too directive
- 3: Adequate but generic ("count on your fingers")
- 2: Nearly gives answer or too vague
- 1: Wrong, spoils answer, or completely unhelpful

**Minimum: Score ≥ 3 for all 3 layers. Score ≥ 4 average across all hints.**

**"Why?" Explanation (post-answer) must follow the 3-R Framework:**
1. Re-Contextualize — state the error neutrally
2. Redirect — offer a mental model
3. Reinforce — micro-question before moving on

---

### Gate 4: Visual Requirement

| Grade | Visual expectation | Minimum visual coverage |
|-------|-------------------|------------------------|
| Grade 1-2 | Almost every question | ≥80% have visuals |
| Grade 3-4 | Most questions | ≥60% have visuals |
| Grade 5-6 | When concept demands it | ≥40% have visuals |

| Check | Pass criteria | Fail example |
|-------|--------------|--------------|
| Visual matches stem | Shows what question asks | Stem says "triangles," visual shows squares |
| Visual is necessary | Adds understanding, not decoration | Random clipart that doesn't help |
| Visual is clear | Distinguishable at phone resolution | Tiny labels, overlapping shapes |
| No visual when not needed | Pure arithmetic can be text-only | Useless "2+3" with a picture of cats |
| Alt text present | Accessible description | No alt text = fails Gate 4 |

**Automated checks:**
- Visual-stem keyword matching
- Resolution/clarity validation (SVG viewBox check)
- Alt text presence

---

### Gate 5: Distractor Quality (Misconception-Based)

| Check | Pass criteria | Fail example |
|-------|--------------|--------------|
| Each distractor tests a misconception | Mapped to specific error | Random wrong numbers |
| Distractors are plausible | A student WOULD make that error | Option "999" for "5+3" |
| Diagnostic feedback is specific | Tells what went wrong for THAT choice | "Try again!" |
| No duplicate distractors | All options distinct | Two options both say "15" |
| Distractor difficulty gradient | Some near-misses, some further | All equally wrong |

**Misconception mapping template:**
```
Question: What is 43 - 17?
Correct: 26
Distractor 36 → Misconception: subtracted smaller from larger in each column
Distractor 24 → Misconception: arithmetic slip in borrowing
Distractor 34 → Misconception: no borrowing applied
```

**Minimum: Every distractor must have a named misconception in the JSON.**

---

### Gate 6: Interaction Fit

| Concept type | Best interaction | Wrong interaction |
|-------------|-----------------|-------------------|
| "Which shape has 4 sides?" | MCQ with visuals | Integer input |
| "Put these in order: 3, 1, 5, 2" | Drag-drop | MCQ |
| "What is 7 × 8?" | Integer input | MCQ (too easy to guess) |
| "Is 15 > 12? Yes/No" | MCQ (2 options) | Integer input |
| "Count the dots" | Integer input | MCQ (limits learning) |

| Check | Pass criteria | Fail example |
|-------|--------------|--------------|
| Interaction matches cognitive demand | See table above | Ordering questions as MCQ |
| MCQ has 4 options (not 2-3) | Unless Yes/No type | 3 options = 33% guess rate |
| Integer input has reasonable range | Child can type answer | Answer is 1,247 for Grade 1 |
| Drag-drop has 3-6 items | Manageable on phone | 10 items to reorder |

---

### Gate 7: Duplicate & Repetition Detection

| Check | Pass criteria | Fail example |
|-------|--------------|--------------|
| No exact stem duplicates | Unique stem text | "What is 5+3?" appears 4 times |
| No template duplicates | Same pattern, different numbers only | 50 questions all "What is A+B?" |
| Concept coverage diverse | Multiple angles per skill | All addition questions are "X+Y=?" |
| Number patterns varied | Different number combinations | Always uses 5, 3, 7 |
| Word problem variety | Different contexts | All word problems about "apples" |

**Automated checks:**
- Fuzzy string matching (Levenshtein < 0.3 = duplicate)
- Template fingerprinting (strip numbers, compare structure)
- Number frequency analysis per topic
- Context word cloud per topic

**Maximum template repetition: ≤15% of any topic can share the same template.**

---

## Quality Gate Pipeline

```
┌──────────────┐
│ New Question  │ (AI-generated or human-written)
└──────┬───────┘
       ▼
┌──────────────┐
│ Gate 1: Math │ → Auto-verify answer + options
└──────┬───────┘
       ▼
┌──────────────┐
│ Gate 2: Peda │ → Grade alignment + language level
└──────┬───────┘
       ▼
┌──────────────┐
│ Gate 3: Hints│ → Socratic rubric scoring
└──────┬───────┘
       ▼
┌──────────────┐
│ Gate 4: Visual│ → Coverage check + match verification
└──────┬───────┘
       ▼
┌──────────────────┐
│ Gate 5: Distract │ → Misconception mapping present?
└──────┬───────────┘
       ▼
┌────────────────────┐
│ Gate 6: Interaction│ → Concept-type fit check
└──────┬─────────────┘
       ▼
┌────────────────────┐
│ Gate 7: Duplicates │ → Template + number fingerprint
└──────┬─────────────┘
       ▼
┌──────────────┐
│ ✅ APPROVED  │ → Production content pool
└──────────────┘
```

**If ANY gate fails:**
- Question goes to "Needs Fix" queue in CMS
- Tagged with which gate(s) failed
- Cannot enter production pool until all 7 gates pass
- Batch failure report sent weekly

---

## Current State Audit (Honest Assessment)

| Gate | Current status | Gap |
|------|---------------|-----|
| Gate 1: Math correctness | ⚠️ Mostly OK | Some edge cases in generated content |
| Gate 2: Pedagogy | ⚠️ Partial | Language level not systematically checked |
| Gate 3: Hints | ❌ Weak | Many generic ("think carefully"), some spoilers |
| Gate 4: Visuals | ❌ Major gap | Grade 1-2 has <50% visual coverage |
| Gate 5: Distractors | ⚠️ Partial | Many lack named misconceptions |
| Gate 6: Interaction | ⚠️ Partial | Most are MCQ even when drag-drop is better |
| Gate 7: Duplicates | ⚠️ Fixed once | Template diversity improved but needs monitoring |

**Priority order for remediation:**
1. Gate 3 (Hints) — directly impacts learning; parent sees "Why?" quality
2. Gate 4 (Visuals) — Grade 1-3 kids NEED pictures to understand
3. Gate 5 (Distractors) — "Why?" explanation quality depends on this
4. Gate 6 (Interaction) — makes app feel intelligent vs generic quiz
5. Gate 7 (Duplicates) — continuous monitoring needed
6. Gate 2 (Pedagogy) — language audit pass
7. Gate 1 (Math) — mostly OK, needs edge case sweep

---

## Metrics

| Metric | Target | How measured |
|--------|--------|-------------|
| Gate pass rate (new content) | ≥90% on first submission | CMS pipeline tracking |
| User-flagged questions | <0.5% of served questions | In-app flagging system |
| Hint helpfulness | ≥70% correct after hint used | Analytics: hint_used → correct_after |
| Visual coverage (G1-2) | ≥80% | Automated scan |
| Distractor mapping coverage | 100% | JSON schema validation |
| Template diversity | ≤15% same template per topic | Fingerprint analysis |

---

## Who Owns This

| Role | Responsibility |
|------|---------------|
| Anand (Product) | Sets quality bar, reviews flagged content |
| AI pipeline | Runs automated gates (1, 4, 6, 7) |
| Human QA | Reviews gates 2, 3, 5 (requires judgment) |
| CMS | Surfaces failures, tracks remediation |
| Analytics | Measures in-production quality via user signals |

---

*This gate is the immune system of Kiwimath.
Without it, the adaptive engine is a precision delivery system for mediocre content.*
