# G5-6 Quality Audit Report

**Date:** 2026-04-30  
**Scope:** 7 new topic files (Topics 1, 3-8), 300 questions each (2,100 total)  
**Sample:** 20+ questions per topic across all 5 difficulty tiers (easy/medium/hard/advanced/expert)

---

## EXECUTIVE SUMMARY

The G5-6 question bank contains **several critical math errors** where the marked correct answer is demonstrably wrong, **questions that are logically unsolvable**, **hints that expose the author's own uncertainty**, and **expert-tier content far beyond the target age group**. There are also 2 questions with duplicate answer choices and widespread low-quality diagnostics.

**Critical bugs found: 10 wrong answers, 3 unsolvable questions, 2 duplicate-choice questions**

---

## 1. WRONG CORRECT ANSWERS (Critical -- Highest Priority)

These questions have a `correct_answer` that is mathematically or logically incorrect.

### T1-0976 (Medium, Counting)
- **Stem:** "How many integers from 1 to 1000 are divisible by 6 but not by 8?"
- **Marked answer:** 146 (index 3)
- **Correct answer:** 125 (index 1)
- **Proof:** floor(1000/6) = 166 multiples of 6. floor(1000/24) = 41 multiples of LCM(6,8)=24. 166 - 41 = 125.
- **Note:** The hint text itself contains the author's self-correction: *"166 - 41 = ? ... wait, let me recheck. floor(1000/6)=166, floor(1000/24)=41, so 166-41 = 125?"* -- the author caught the error in the hint but never fixed `correct_answer`.

### T1-1036 (Hard, Counting)
- **Stem:** "How many numbers from 100 to 999 have exactly one even digit?"
- **Marked answer:** 225 (index 0)
- **Correct answer:** 350 (NOT among the choices)
- **Proof (brute force verified):** Hundreds-even: 4 x 5 x 5 = 100. Tens-even: 5 x 5 x 5 = 125. Units-even: 5 x 5 x 5 = 125. Total = 350.
- **Impact:** No valid answer exists among the choices. Question is broken.

### T1-1111 (Advanced, Counting)
- **Stem:** "An ant starts at vertex A of a cube and walks along edges. After exactly 3 steps, in how many ways can it return to A?"
- **Marked answer:** 6 (index 1)
- **Correct answer:** 0 (NOT among the choices)
- **Proof:** A cube graph is bipartite. Starting from any vertex (parity 0), after an odd number of steps, the ant is always at a vertex of opposite parity (parity 1). It is impossible to return to the start in exactly 3 steps. The correct answer is 0.
- **Impact:** No valid answer exists. Question is fundamentally broken.

### T4-0991 (Medium, Logic)
- **Stem:** "I'm thinking of a number between 1 and 100. It's a perfect square. It's even. The sum of its digits is 4. What is it?"
- **Marked answer:** 40 (index 3)
- **Correct answer:** 4 (index 0)
- **Proof:** Even perfect squares 1-100: 4, 16, 36, 64, 100. Digit sums: 4, 7, 9, 10, 1. Only 4 has digit sum 4. The number 40 is NOT a perfect square.

### T4-1156 (Expert, Logic)
- **Stem:** "You have a balance and weights of 1g, 3g, 9g, and 27g. Can you measure 20g by placing weights on both pans?"
- **Marked answer:** "Yes: 27 on one side, 1+3+9 on the other with the item" (index 3)
- **Correct answer:** "Yes: 27+3 on one side, 1+9 on the other with the item" (index 2)
- **Proof:** Answer D: 27 = item + 1 + 3 + 9 = item + 13, so item = 14, NOT 20. Answer C: 27 + 3 = item + 1 + 9, so 30 = item + 10, item = 20. Correct!
- **Note:** The hint text itself works through both and arrives at answer C, then says "Wait..." -- another case of the author catching the error but not fixing `correct_answer`.

### T7-1141 (Expert, Word Problems)
- **Stem:** "A boat covers 36 km upstream in 6 hours and 36 km downstream in 4 hours. If the speed of the stream increases by 1 km/h, how long to travel 36 km upstream?"
- **Marked answer:** 9 hours (index 0)
- **Correct answer:** 7.2 hours (index 2)
- **Proof:** Upstream speed = 36/6 = 6 km/h. Downstream speed = 36/4 = 9 km/h. Boat speed = (6+9)/2 = 7.5. Stream speed = (9-6)/2 = 1.5. New stream = 2.5. New upstream speed = 7.5 - 2.5 = 5. Time = 36/5 = 7.2 hours.

### T7-1156 (Expert, Word Problems)
- **Stem:** "A and B start a business with $5,000 and $7,000. After 4 months, C joins with $9,000. At the end of the year, the profit is $4,600. What is C's share?"
- **Marked answer:** $1,800 (index 3)
- **Correct answer:** ~$1,533 (NOT among the choices)
- **Proof:** A: 5000x12 = 60,000. B: 7000x12 = 84,000. C: 9000x8 = 72,000. Total = 216,000. C's share = (72,000/216,000) x 4,600 = 1/3 x 4,600 = $1,533.33.
- **Impact:** No valid answer exists among the choices.

### T8-0946 (Easy, Puzzles)
- **Stem:** "Mirror code: A<->Z, B<->Y, C<->X, ... Decode 'KFMM'."
- **Marked answer:** PULL (index 0)
- **Correct answer:** PUNN (NOT among the choices)
- **Proof:** Using n -> 27-n mapping: K(11)->P(16), F(6)->U(21), M(13)->N(14), M(13)->N(14). Result: PUNN.
- **Note:** The hint text shows the author discovering this error: *"K=11->27-11=16=P, F=6->27-6=21=U, M=13->27-13=14=N... Hmm, that gives PUNN."*
- **Impact:** No valid answer exists.

### T8-1021 (Hard, Puzzles)
- **Stem:** "In a 4x4 magic square using 1-16, the sum of all corner numbers is always: 34"
- **Issue:** The claim that corner sum is "always" 34 is false for general 4x4 magic squares. This is only true for pandiagonal/most-perfect magic squares. The word "always" makes this statement incorrect.

### T6-1081 (Advanced, Shapes)
- **Stem:** "A square has side 20 cm. Quarter-circles of radius 10 cm are drawn from each corner. What is the area of the leaf-shaped region in the center?"
- **Marked answer:** 114 sq cm (index 1)
- **Issue:** With side 20 and radius 10, adjacent corner circles are exactly 20 apart (= r1 + r2 = 10 + 10). The quarter-circles from adjacent corners just barely touch at the midpoint of each side -- they do NOT overlap. No "leaf-shaped region" exists in the center. The question is geometrically invalid.

---

## 2. UNSOLVABLE / AMBIGUOUS QUESTIONS (Critical)

### T4-0976 (Medium, Logic)
- **Stem:** "Three packages weigh different amounts. A+B > C, B+C > A, A > B. Rank them heaviest to lightest."
- **Marked answer:** C, A, B (C > A > B)
- **Issue:** The ranking is NOT uniquely determined. Example 1: A=5, B=3, C=4 satisfies all constraints but gives A > C > B. Example 2: A=5, B=3, C=6 gives C > A > B. Both are valid. The question has no unique answer.
- **Note:** The hint text reveals the author struggling with this: *"Is C > A or A > C?... Let me recheck..."*

### T7-1186 (Expert, Word Problems)
- **Stem:** "The ratio of incomes of A and B is 5:3. The ratio of expenditures is 4:3. Each saves $1000. What is A's income?"
- **Marked answer:** $5,000
- **Issue:** Setting up equations: 5x - 4y = 1000 and 3x - 3y = 1000. Solving: 3y = -2000, giving y = -666.67 (negative expenditure). The problem has no valid solution.

### T1-0903 (Easy, Counting)
- **Stem:** "How many triangles are in a shape made of 3 small triangles arranged in a row?"
- **Marked answer:** 5
- **Issue:** The answer depends entirely on HOW the triangles are arranged (equilateral? right? sharing edges? pointing same direction?). Without a visual, this is ambiguous. Different valid arrangements yield 3, 4, or 5 triangles.

---

## 3. DUPLICATE ANSWER CHOICES (High Priority)

### T1-1061
- **Choices:** ['186', '120', '186', '246'] -- "186" appears twice

### T3-0999
- **Choices:** ['3', '1', '1', '4'] -- "1" appears twice

---

## 4. HINT QUALITY ISSUES (High Priority)

### 4a. Hints Exposing Author Uncertainty

Over **80 hints** contain phrases like "wait", "let me recheck", "hmm", "actually" -- showing the author's real-time problem-solving process rather than providing clean Socratic guidance. This is deeply unprofessional for a student-facing product. Students seeing these hints would lose trust in the app.

**Worst offenders by topic:**
- Topic 4 (Logic): 40+ hints with author self-talk
- Topic 8 (Puzzles): 25+ hints with author self-talk
- Topic 1 (Counting): 10+ hints
- Topic 5 (Spatial): 8+ hints
- Topic 6 (Shapes): 5+ hints

**Examples:**
- T4-0976 level_2: *"We know A > B. Is C > A or A > C?... Let me recheck..."* (400+ characters of rambling)
- T8-0946 level_2: *"K=11->27-11=16=P... Hmm, that gives PUNN. Let me recheck..."*
- T1-0976 level_2: *"166 - 41 = ? ... wait, let me recheck..."*
- T4-1081 level_2: *"The circle is D-B-A-C-E... Hmm... Let me try..."* (500+ characters of working)

**Recommendation:** All hints containing "wait", "hmm", "let me", "actually" must be rewritten to provide clean, progressive Socratic guidance.

### 4b. Hints That Give Away the Answer Too Early

Some level_0 hints are too revealing:
- T4-1052 level_0: *"If X always lies, then X's statement 'at least one of us lies' is actually true."* -- This solves the problem entirely.

---

## 5. DIAGNOSTIC QUALITY ISSUES (Medium Priority)

### 5a. Truncated / Placeholder Diagnostics

Three questions have diagnostics that are clearly broken:
- **T7-1141** diag[3]: `"Didn't."` (truncated)
- **T7-1156** diag[0]: `"Didn't."` (truncated)
- **T7-1182** diag[0]: `"Didn't."` (truncated)

### 5b. Non-Specific Diagnostics

Over **200 diagnostics** across Topics 3 and 7 are too terse to help students understand their errors. Examples:
- "Adds 3", "Off by 2", "Miscounts", "Used n=4"

These tell the student WHAT went wrong in the vaguest terms but not WHY or HOW to fix their thinking. Effective diagnostics should identify the conceptual error (e.g., "You added the common difference twice instead of once" rather than "Off by 2").

### 5c. Reused Boilerplate Diagnostics (Topic 4)

Many Topic 4 logic questions reuse identical diagnostic text from balance-scale questions for completely unrelated question types:
- T4-1036 (water jug puzzle) has diagnostics: *"The balance equation doesn't support this equivalence"* -- irrelevant to a water jug problem.
- T4-1051 (round-robin tournament) has diagnostics: *"The ordering or ranking constraints make this impossible"* -- while technically applicable, clearly copy-pasted from a different template.

---

## 6. AGE-APPROPRIATENESS ISSUES (High Priority)

Several expert-tier questions are far beyond Grade 5-6 level, even for competition math:

### Grossly Inappropriate (university/graduate level):
| ID | Topic | Content |
|---|---|---|
| T8-1156 | Puzzles | VCG mechanism design (graduate economics/CS) |
| T8-1186 | Puzzles | Elliptic curve cryptography (university cryptography) |
| T8-1036 | Puzzles | Sprague-Grundy theorem (university combinatorial game theory) |
| T8-1096 | Puzzles | Sprague-Grundy naming conventions |
| T6-1171 | Shapes | Euler line (advanced high school geometry) |
| T6-1186 | Shapes | Point-to-line distance formula (Grade 9-10 coordinate geometry) |
| T6-1151 | Shapes | Nephroid perimeter (university-level curve geometry, hint even confused) |

### Borderline but Acceptable for Competition:
| ID | Topic | Content |
|---|---|---|
| T3-1051 | Patterns | FOIL expansion (typically grade 7-8, OK for competition G5-6) |
| T3-1171 | Patterns | Difference of squares factoring |
| T4-1141 | Logic | Blue-eyed islanders (classic but very advanced) |
| T1-1141 | Counting | Pairing formula 10!/(2^5 x 5!) |

---

## 7. DIFFICULTY TIER MISMATCHES (Medium Priority)

### Questions Too Easy for Their Tier:
- **T5-0905** (Easy, score 202): "If one face of a cube is painted red, how many faces are NOT painted?" -- This is trivial subtraction (6-1=5), below G5-6 easy level.
- **T7-0901** (Easy, score 201): "24 - 8 = ?" -- Pure single-digit subtraction, more appropriate for G2-3.
- **T7-0905** (Easy, score 201): "12 + 8 = ?" -- Addition of two numbers, more appropriate for G2-3.

### Questions Too Hard for Their Tier:
- **T4-1141** (Expert, score 281): Blue-eyed islanders common knowledge puzzle -- while labeled expert, this is a famous puzzle that stumps many adults. Questionable even for expert G5-6.
- **T1-0905** (Easy, score 205): Inclusion-exclusion principle -- while the specific instance is solvable, the concept is typically medium difficulty.

---

## 8. STEM CLARITY ISSUES (Medium Priority)

### Questions Requiring Visuals to Be Unambiguous:

Several questions describe geometric or spatial arrangements that are ambiguous without a visual. See Section 10 for the full list of questions needing SVG visuals.

### Ambiguous Stems:
- **T1-0903**: "3 small triangles arranged in a row" -- what type of triangles? How are they connected?
- **T5-1021**: Complex cube net description -- very hard to parse from text alone
- **T5-0903**: "Cross-shaped net" -- multiple valid cross configurations exist
- **T5-0902**: "L-shape of 6 squares" -- many possible L arrangements

---

## 9. STRUCTURAL / DATA ISSUES

### Missing Visual Context
All 2,100 questions have `visual_svg: null`. While many text-only questions work fine, geometry and spatial reasoning questions suffer significantly (see Section 10).

### Inconsistent Difficulty Scores
Within each tier, difficulty scores should roughly correlate with actual difficulty. Some easy questions have higher difficulty scores than medium questions in the same topic.

---

## 10. QUESTIONS NEEDING SVG VISUALS (High Priority)

The following questions would greatly benefit from or require visual illustrations:

### Topic 1 - Counting
- **T1-0903**: Triangles in a row (arrangement unclear without visual)
- **T1-0906**: 2x2 grid squares
- **T1-0961**: 3x3 grid squares
- **T1-1021**: Grid paths (0,0) to (4,3)
- **T1-1066**: Ant on cube edges
- **T1-1081**: Grid paths avoiding (2,2)
- **T1-1111**: Ant on cube walk

### Topic 5 - Spatial Reasoning
- **T5-0901**: Cube net
- **T5-0902**: Four different net shapes (cross, L, line, T) -- critical, must show all 4
- **T5-0903**: Cross-shaped cube net with opposite faces
- **T5-0904**: Cube net perimeter
- **T5-0906**: Valid vs invalid cube nets
- **T5-0961**: Net with 4 squares in a row
- **T5-0976**: Paper rotation with dot tracking
- **T5-1021**: Specific cube net configuration with star
- **T5-1036**: Clock reflection
- **T5-1051**: Robot grid movement
- **T5-1081**: Numbered cube net folding
- **T5-1111**: Robot path with displacement
- **T5-1126**: Cube cross-section
- **T5-1141**: Die rolling sequence
- **T5-1186**: Cylinder diagonal cross-section

### Topic 6 - Shapes & Geometry
- **T6-0901**: Rectangle with square removed
- **T6-0903**: L-shaped figure
- **T6-0904**: Square with triangle attached
- **T6-0906**: Path around rectangular pool
- **T6-1021**: Room with semicircular alcove
- **T6-1081**: Square with quarter-circles (also geometrically invalid, see Section 1)
- **T6-1096**: Intersecting chords in circle
- **T6-1141**: Semicircles in square forming petals

### Topic 8 - Puzzles
- **T8-0901 to T8-0906**: Magic square questions (show the grid)
- **T8-0931**: River crossing (show the scenario)
- **T8-0961**: Odd-number magic square
- **T8-1021**: 4x4 magic square

---

## 11. SUMMARY OF ISSUES BY SEVERITY

### BLOCKING (must fix before release):
| Count | Issue |
|---|---|
| 8 | Wrong correct answers (T1-0976, T1-1036, T1-1111, T4-0991, T4-1156, T7-1141, T7-1156, T8-0946) |
| 2 | Geometrically/logically invalid questions (T6-1081, T7-1186) |
| 1 | Ambiguous stem with no unique answer (T4-0976) |
| 2 | Duplicate answer choices (T1-1061, T3-0999) |
| 1 | Misleading claim stated as universal truth (T8-1021) |

### HIGH PRIORITY (fix before release):
| Count | Issue |
|---|---|
| 80+ | Hints containing author self-talk ("wait", "hmm", "let me recheck") |
| 7 | Expert questions grossly inappropriate for G5-6 age group |
| 3 | Truncated/placeholder diagnostics ("Didn't.") |
| 40+ | Questions needing SVG visuals for clarity |

### MEDIUM PRIORITY (fix in next iteration):
| Count | Issue |
|---|---|
| 200+ | Non-specific/terse diagnostics that don't help learning |
| 20+ | Reused boilerplate diagnostics from wrong question types |
| 5+ | Easy-tier questions too trivial for G5-6 |
| 3+ | Ambiguous stems requiring visual context |

---

## 12. RECOMMENDATIONS

1. **Immediate:** Fix all 8 wrong answers and 3 unsolvable questions. These are the most damaging bugs possible in an education app.

2. **Immediate:** Deduplicate answer choices in T1-1061 and T3-0999.

3. **Before release:** Run an automated script to find all hints containing "wait", "hmm", "let me", "actually" and rewrite them as clean Socratic guidance.

4. **Before release:** Replace all truncated diagnostics ("Didn't.") with meaningful explanations.

5. **Before release:** Remove or replace expert questions on VCG mechanisms, elliptic curve cryptography, and other university-level topics. Replace with challenging but age-appropriate competition math.

6. **Before release:** Add SVG visuals to at least the 15 most critical spatial/geometry questions (all of Topic 5 cube net questions, key Topic 6 composite shape questions).

7. **Next iteration:** Improve all terse diagnostics (especially in Topics 3 and 7) to explain the conceptual error, not just state "Off by 2".

8. **Next iteration:** Review difficulty tier assignments, especially easy-tier questions that are too trivial for G5-6.

9. **Systemic:** Implement an automated answer-verification pipeline that brute-force checks numerical answers before committing questions.

10. **Systemic:** Implement a hint-quality linter that flags author self-talk patterns.
