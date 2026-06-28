# Kiwimath Content Mistakes Repository

**Purpose.** A living catalogue of every *content* defect found in the Kiwimath question banks, with how to spot each one and how it was fixed. It exists so that (a) we never re-introduce a class of mistake we've already solved, and (b) this work can be **handed over to another coworker** without losing the institutional knowledge.

**Scope.** Served banks only: `content-live/olympiad/L{1-8}/` (olympiad ladder) and `content-live/curriculum/{board}/grade{n}/` (school). Superseded `content-v2/`, `content-v4/`, and everything under `archive/` are out of scope.

**Last updated:** 2026-06-17.

---

## How to use this document

Each mistake has the same schema:

- **What it looks like** — the symptom a tester sees.
- **Why it's wrong** — the impact on the child / parent trust.
- **How to detect** — the programmatic signal (so it's re-runnable, not eyeball-only).
- **Examples** — real question IDs + file.
- **Fix** — exactly what we change, and (critically) what we must NOT change.
- **Status** — count fixed + the QA pass/date.

Two rules that apply to **every** fix:

1. **Locked fields.** When fixing one thing, never silently alter another. `correct_answer`, `correct_value`, `choices`, `hint`, `irt_b`, `difficulty_*` are *locked* unless the mistake is specifically about them. Every pass diffs the edited file against a backup and asserts **only the intended fields changed**.
2. **Backup first.** Copy the file to `qa-reports/backup-<pass>-<date>/` before editing, so the diff is always possible.

---

## Quick index

| # | Category | Mistake | Detector signal | Fixed | First found |
|---|----------|---------|-----------------|-------|-------------|
| 1 | Stem | Decorative filler prefix | name-wrapper / scene templates | ~6,937 | 2026-06-14 |
| 2 | Stem | Empty / truncated stem | `stem` blank or ends mid-word | 4 + 262 | 2026-06-12/14 |
| 3 | Stem | Unanswerable (missing essential info) | asks for a value not derivable from text/figure | 209 | 2026-06-12 |
| 4 | Stem | **Unsubstituted placeholder** `{b}`,`{j}`,`{rem}` | `{token}` outside `$…$`/SVG | 20 | 2026-06-17 (Type A) |
| 5 | Stem | **Confusing formation** (refers to absent figure) | promises a visual, no `visual_svg`/`visual_png` | 5 | 2026-06-17 (Type D) |
| 6 | Answer key | Wrong key — arithmetic (keyed to distractor) | recompute single-step word problem ≠ key | 11 | 2026-06-14 |
| 7 | Answer key | Wrong key — percent (sold vs left) | recompute ≠ key | 1 | 2026-06-14 |
| 8 | Answer key | **Wrong key — ratio larger/smaller** | max/min ratio term × k ≠ key | 1 | 2026-06-17 (Type B) |
| 9 | Hint | Answer-leaking hint | hint string contains the answer value | 1,393+ | 2026-06-13 |
| 10 | Hint | Wrong / mismatched-formula hint value | hint number ≠ recomputed value | 299 + 17 | 2026-06-14 |
| 11 | Solution | Generic template solution (doesn't solve *this* q) | solution lacks the stem's numbers/method | ~3,340 | 2026-06-14 |
| 12 | Solution | Mismatched diagnostics (wrong formula) | e.g. area formula on a circumference q | (in #11 pass) | 2026-06-14 |
| 13 | Image | Fake placeholder SVG (grey box) | `#F8F9FA` rect + label, no real figure | 2,461 | 2026-06-14 |
| 14 | Image | Mismatched template image (wrong figure) | figure-type classifier ≠ stem domain | 52 + 148 | 2026-06-14 |
| 15 | Image | Missing-but-required image | essential-visual flag, no figure | 14 | 2026-06-14 |
| 16 | Image | **Wrong figure** (semicircle drawn as full circle) | curved-shape stem + full-`<circle>` svg, no arc | 2 + 13 | 2026-06-17 (Type C) |
| 17 | Image | **Figure reveals the solution** (spoiler) | Venn region-sum / tree leaf-count = answer | 29 | 2026-06-17 (Type E) |
| 18 | Structure | Exact / near duplicates, skeleton overload | stem+choices hash collision | 1,136+342+1,147+1,790 | 2026-06-04/14 |
| 19 | Image | **Figure labels the answer** (geometry) + tiny font | answer value drawn as a figure label, not given in stem | 17 | 2026-06-18 (Type F) |
| 20 | Image | **Angle label on the wrong vertex** + tiny font | acute-angle label sits on the right-angle (90°) corner | 4 | 2026-06-18 (Type G) |
| 21 | Image | **Pattern visual missing** (stripped) | "what X comes next?" + empty `visual_svg`, no pattern in stem | 69 | 2026-06-21 (Type H) |
| 22 | Image | **Mismatched/decorative figure on a logic question** | reused template SVG on a sorting/odd-one-out/missing-number stem that needs no figure | 316 + 24 tail | 2026-06-21 (Type I) |
| 23 | Stem | **Context-stripped "which direction now?"** (unanswerable) | rotation series flattened → no setup/figure, keyed dir underivable | 139 | 2026-06-21 (Type N) |

---

## A. Stem / language mistakes

### 1. Decorative filler prefix
- **What it looks like:** A story sentence glued in front of the real question — "A crystal on the cave wall glows near Chikoo. What is 7 × 8?" The filler has no bearing on the math.
- **Why it's wrong:** Adds reading load for young children, buries the actual task, and looks unprofessional to parents.
- **How to detect:** name-wrapper templates ("\<Character\> …"), scene templates ("With tools and parts."), statement-logic intros ("The machine needs Kiwi to solve a puzzle. Negate: …"), colon/dash lead-ins ("Help Vanya calculate:"). **Guard:** never cross a sentence that contains a digit, operator, `:`, quote, or math object — that protects flag-reflection, paper-folding, magic-square, age-comparison content.
- **Examples:** broad across L1/L2 olympiad.
- **Fix:** strip the prefix sentence; keep the math sentence verbatim.
- **Status:** ~6,937 stems (Content QA #2, 2026-06-14), preceded by ~6,650 in the 2026-06-13 pass.

### 2. Empty / truncated stem
- **What it looks like:** blank stem, or one that ends mid-word (`KM-L3-NT-0574`).
- **Detect:** `stem` empty after trim, or no terminal punctuation + dangling token.
- **Fix:** reconstruct from `original_stem`/tags/choices; if irrecoverable, delete.
- **Status:** 4 empty removed + 262 reconstructed + 1 truncated fixed.

### 3. Unanswerable (missing essential info)
- **What it looks like:** asks for a value that the text (and any figure) does not determine.
- **Detect:** manual + "essential-visual with no figure" overlap.
- **Fix:** delete (recoverable from `qa-reports/`).
- **Status:** 209 deleted (2026-06-12).

### 4. Unsubstituted template placeholder — **Type A**
- **What it looks like:** a literal `{b}k`, `{j}`, `{rem}` shows in the rendered question/figure (e.g. the second angle of a ratio diagram reads `{b}k`).
- **Why it's wrong:** obviously broken; signals auto-generation slipped through.
- **How to detect:** `(?<![\\_^]){[A-Za-z][A-Za-z0-9_]*}` **after stripping `$…$` math** (so valid LaTeX like `\dfrac{abc}{4K}`, `Σ_{k}`, `x^{2k}` is NOT flagged), and treat *any* brace inside `visual_svg` as real (SVG has no LaTeX).
- **Examples:** `KM-L4-GEO-0012/13/14/15` (`{b}` in SVG), `KM-L5-COM-0181-84` (`{j}` hint), `KM-L5-GEO-0229/30` (`{n}` hint), `KM-L7-ALG-0021-24` (`{rem}` solution). Plus `Erd\H{o}s`→Erdős (LaTeX accent rendering raw in prose) ×6.
- **Fix:** substitute the value from the stem/solution; only the affected field changes.
- **Status:** 20 (2026-06-17).

### 5. Confusing question formation — **Type D**
- **What it looks like:** "In the pattern 1, 3, 5, 7, … which **figure number** has exactly 21 **dots**?" — invokes a dot/figure picture that **isn't shown**, forcing the child to imagine an absent diagram. It is really just "what position is 21 in the sequence?"
- **Why it's wrong:** the wording is harder than the math; the child stalls on phrasing, not on the concept.
- **How to detect (principled):** stem promises a concrete visual — `shown | the figure | the diagram | figure number | dots | shaded` — but `visual_svg` AND `visual_png` are both empty.
- **Examples:** `KM-L4-ALG-0198/0199/0200` (figure/dots, no figure); `KM-L2-GEO-1022` ("The figure given consists of two squares…" — no figure, and the perimeter *depends* on the unseen arrangement); `KM-L2-GEO-1014` ("area of shaded region" — no figure, though the parenthetical gave the count).
- **Counter-examples (left alone):** `KM-L4-ALG-0188-0194` say "figure shown" and **do** have a labelled dot-figure (Fig 1–4 = 1/3/5/7); `KM-L5-GEO-0151-60` use "figure" in the ordinary geometric sense ("L-shaped figure"); and bare "dots" as a counting noun ("Aarohi has 8 dots and gets 2 more") is **not** a figure reference.
- **Fix:** reword to plain self-contained language, **answer preserved**, only `stem` changes (e.g. "…what is the position of 21? (1 is the 1st, 3 is the 2nd, …)"; "Two squares of sides 8 cm and 6 cm are joined so the smaller sits flat against one side of the larger…" → perimeter 44).
- **Status:** 5 (2026-06-17): 3 in L4-ALG + 2 in L2-GEO.

---

## B. Answer-key mistakes

> The most dangerous class: a child does the math right and is told they're wrong. Prior QA treated `correct_answer` as locked and never math-checked it — that is exactly how these slipped through. **Every computable family needs its own validator.**

### 6. Wrong key — arithmetic (keyed to a distractor)
- **What it looks like:** "Raju has 7 watermelons, gets 5 more" keyed to 2 (or to the *add-result of a multiplication*, e.g. 3 cats × 4 legs keyed "7" = 3+4).
- **Detect:** validator for single-step integer add/sub/mul/div word problems + explicit "what is A op B"; flag when recompute ≠ key. **Watch the "in all / altogether" trap** — it appears in *both* addition and multiplication ("8 groups of 22, how many in all" is 8×22, not 8+22); prioritise the multiplication phrasing.
- **Examples:** `A1-ADD-0315`, `KM-L1-NT-0039/0140/0429/0432`, `KM-L1-ALG-0314/0447`, `KM-L1-COM-0721/0771/0804`.
- **Status:** 11 fixed (2026-06-14).

### 7. Wrong key — percent (sold vs left)
- **Example:** `KM-L3-ALG-0326` "sold 35% of 200, how many left" keyed 70 (=sold) → fixed to 130 (=left).
- **Status:** 1 fixed.

### 8. Wrong key — ratio larger/smaller angle — **Type B**
- **What it looks like:** "Two angles on a straight line are in the ratio 7:2. Find the **larger** angle." keyed **40** (= 2·20, the *smaller*) instead of **140** (= 7·20).
- **Root cause:** the generator always took the **second** ratio term as "larger" — correct for 4:5 but wrong whenever the first term is bigger.
- **How to detect:** parse the N-part ratio (use a real word-boundary on "angle" so "tri**angle**" doesn't match), pick `max`/`min` term × k for "larger"/"smaller", compare to key.
- **Example:** `KM-L4-GEO-0015` (only one in L4–L7).
- **Re-validated CORRECT (false alarms):** 3-part triangle ratios (1:2:3…) and the L5 similar-triangle family `KM-L5-GEO-0161-76`.
- **Status:** 1 fixed (2026-06-17). Also re-confirmed the remainder-theorem family `KM-L7-ALG-0021-24` keys are correct (only their `{rem}` text was broken — see #4).

> **Still not validated** (could hold wrong keys, future passes): fraction/decimal arithmetic, multi-step word problems, combinatorics counts, probability.

---

## C. Hint mistakes

### 9. Answer-leaking hint
- **What it looks like:** the hint states the final answer instead of nudging.
- **Detect:** hint text contains the `correct_value` (or the answer choice string).
- **Fix:** mask/reword to a method nudge.
- **Status:** 7,978 (early) + 1,393 masked + 545 missing generated → **0 leaks**.

### 10. Wrong / mismatched-formula hint value
- **What it looks like:** circumference question, but `hint.level_2` quotes "24 cm" when the answer is 50.24; or an **area** formula in the hint of a **circumference** question.
- **Detect:** recompute the hinted intermediate; compare to the number in the hint. Flag formula keywords that don't match the stem's quantity (area vs perimeter vs circumference).
- **Status:** 299 wrong values + 17 mismatched-formula hints (2026-06-14, L1–L3 + curriculum).

---

## D. Solution / diagnostics mistakes

### 11. Generic template solution (doesn't solve *this* question)
- **What it looks like:** a boilerplate "Analysis: … Answer: …" that never uses the stem's actual numbers or method.
- **Detect:** solution lacks the stem's operands/operation; or identical solution text shared across many different stems.
- **Fix:** regenerate a real, math-aware solution (geometry/sequence/arithmetic/volume/shape-facts generators) — only generate when the computed value matches the stored answer.
- **Status:** ~3,340 real solutions generated + 13,878 answer-appended (L1–L3 + curriculum). **L4–L7 solutions not yet deep-audited** (new content).

### 12. Mismatched diagnostics
- **What it looks like:** per-choice "why this is wrong" text that uses the wrong formula (e.g. `Area = πr²` reasoning on a circumference item).
- **Status:** fixed within the #11 pass.

---

## E. Image / figure mistakes

### 13. Fake placeholder SVG (grey box)
- **Detect:** SVG is a `#F8F9FA` rectangle + `#6C757D` label, no real geometry.
- **Fix:** remove (questions were text-answerable).
- **Status:** 2,461 removed (kept 6,108 real diagrams).

### 14. Mismatched template image (wrong figure)
- **What it looks like:** a clock drawn on a "square rotated 90°" question; a rectangle on a circular-paper/sector question — figures are reused generic templates that got mis-assigned.
- **Detect:** figure-type classifier (clock = 12 texts + clock-nums; coin = `#FFD700` gold; triangle = 3-pt polygon; rect; grid ≥8 rects; angle = `°` + rays) vs the stem's domain. **Match by DOMAIN, not raw shape** (most "circle" SVGs are gold coins on money questions, or ray diagrams — a blunt shape rule deletes good art). Mind substring traps: "**clock**wise" matched the clock keyword (fix with negative lookahead).
- **Status:** 52 (geometry pass) + 148 (full 6,013-image audit) removed.

### 15. Missing-but-required image
- **Detect:** essential-visual and no figure.
- **Fix:** generate the accurate figure (e.g. "divided into N parts, M shaded" → N-segment bar with M shaded).
- **Status:** 14 recreated.

### 16. Wrong figure — semicircle drawn as full circle — **Type C**
- **What it looks like:** "A semicircle has radius 14 cm…" with a **full circle** SVG.
- **Detect:** stem has `semicircle|sector|quarter circle|half circle|arc of`, the SVG has a big `<circle>` (r≥15) and **no** `<path … A …>` arc.
- **Fix:** redraw the correct figure (flat diameter + arc on top) and **render-verify with cairosvg** before committing.
- **Examples:** `KM-L4-GEO-0151` (r=7), `KM-L4-GEO-0152` (r=14). **L1–L3 extension (2026-06-17):** the scanner found 13 more — 12 semicircle "what is the radius/area" items in `L1_GEO_shapes_2d_3d.json` + `L3_GEO_area_perimeter_volume.json`, and 1 quarter-circle (`KM-L3-GEO-0220`) — all drawn as full circles. Redrawn (semicircle / quarter-circle generators, label preserved, render-verified). The earlier full image audit missed these because it looked for cross-*domain* swaps (clock-on-rotation), not shape-fidelity *within* geometry.
- **False positives (left alone):** `KM-L3-GEO-0072` "inscribed angle subtends an arc of 130°" and "central angle" items genuinely use a full circle; `KM-L1-GEO-0456` shows the circle *before* it is folded.
- **Status:** 2 (L4) + 13 (L1–L3) = 15 (2026-06-17).

### 17. Figure reveals the solution (spoiler) — **Type E**
- **What it looks like:** the figure has already done the work.
  - **Venn:** "20 like F, 16 like C, 9 both, how many like at least one?" with circles showing **11 | 9 | 7** — 11 and 7 are *derived* (20−9, 16−9), so the child just reads 11+9+7.
  - **Tree:** "3 shirts and 4 trousers, how many ways?" with all **12 leaf-dots** drawn — the child counts instead of computing 3×4.
- **Why it's wrong:** trivialises the concept being taught (inclusion–exclusion, multiplication principle); the child never does the reasoning.
- **How to detect:**
  - Venn: ≥2 large overlapping `<circle>` + region numbers whose sum (or a labelled region) equals `correct_value`, on a set-overlap word problem, with at least one figure-number **not present in the stem** (i.e. derived).
  - Tree: ≥6 `<line>` + leaf `<circle>` count ≈ `correct_value` on a "how many ways/outcomes" stem.
- **False-positive guard:** "answer literally appears as a label" is **not** sufficient — for MCQ items `correct_answer` is a *choice index* (0–3) that trivially collides with small numbers in legitimate "givens" figures (`KM-L1-ALG-2259` shows the sequence 1,2,3,4,5,?; `KM-L3-ALG-0936` shows the coin totals). Those were inspected and **left alone**.
- **Fix:** remove the spoiler figure (all are text-answerable); if the stem instructed "Using a tree diagram," drop that clause. Locked fields untouched.
- **Examples:** Venn `KM-L4-COM-0147-0162` (16), tree `KM-L4-COM-0001/0003/0129/0133-0145` (13).
- **Status:** 29 figures removed + 5 stems reworded (2026-06-17). Only family found was L4 combinatorics (L5–L7 are proof-based, no such figures).

### 19. Figure labels the answer (geometry) + tiny font — **Type F**
- **What it looks like:** "A right triangle has legs 3 and 4. Find the hypotenuse." with the figure drawing the triangle **and labelling the hypotenuse "5"** — the child just reads the answer off the picture instead of computing 3-4-5. The leg labels were also tiny (font-size 13, unreadable on a phone).
- **Why it's wrong:** trivialises the Pythagorean step (same spirit as Type E, but the spoiler is a *side label* rather than a region/leaf count); and the small font is a readability defect.
- **How to detect:** geometry figure (`<polygon>`) whose **integer answer value appears as a `>N<` text label** AND that value is **not** a number given in the stem. **Guard:** exclude clock / number-line / graph figures — their scale numerals (a clock always has 1-12; a number line has its ticks) collide with small answers and are *not* spoilers. Detector `scan_answer_in_figure` (`content_qa_scan.py`, section "F").
- **Examples:** `KM-L4-GEO-0059-0063` (5) and `KM-L5-GEO-0033-0044` (12) — the right-triangle "find the hypotenuse" family.
- **Counter-examples (left alone):** "find the area / find the *other* leg" variants where the answer isn't labelled; and the number-line "Compute (−5)+(8)−(3)" / fraction figures (the `<polygon>` is an arrowhead and the number is a scale tick, not a side label).
- **Fix:** redraw the triangle showing **only the givens** (the two legs), with a **larger readable font (20)**, a clear right-angle mark, and **no hypotenuse label** — render-verified with cairosvg. Only `visual_svg` changes; answer/choices/hint/solution/skill-tags untouched.
- **Status:** 17 (2026-06-18).

### 20. Angle label on the wrong vertex (geometry) + tiny font — **Type G**
- **What it looks like:** "A right triangle has one acute angle 30°. Find the other acute angle." with the **"30°" drawn at the right-angle corner** — the very vertex carrying the square 90° mark. So the figure says the 90° angle is 30°, which contradicts the picture. The labels were also tiny (font-size 16).
- **Why it's wrong:** the figure is geometrically self-contradictory and confuses the child about which angle is which.
- **How to detect:** the right-angle mark is a 3-point `<polyline>` whose **middle point is the 90° vertex**; flag when a degree-label `<text>` containing a number (e.g. "30°") sits within ~28px of that vertex. Detector `scan_angle_on_right_angle` (`content_qa_scan.py`, section "G").
- **Examples:** `KM-L4-GEO-0049-0052` (the "find the other acute angle" family — given 30°/55°/18°/62°).
- **Fix:** redraw with the **right-angle square at the 90° vertex**, the **given acute angle at an acute vertex** (the apex), and **`?` at the other acute vertex**, with a larger readable font (19). Only `visual_svg` changes.
- **Status:** 4 (2026-06-18).

### 21. Pattern visual missing (stripped) — **Type H**
- **What it looks like:** "What colour bead comes next?" with **no image** and four colour options — unanswerable. A content pass shortened the `stem` to a bare prompt expecting a visual, but `visual_svg` is empty (placeholder stripped); the pattern survived only in `original_stem`.
- **How to detect:** stem contains "comes next" + `visual_svg` empty + **no pattern in the stem** (no digits / shape words / comma list). Detector `scan_pattern_no_visual` (`content_qa_scan.py`, section "H").
- **Fix:** rebuild a valid pattern visual whose cycle lands on the keyed answer — exact sequence from `original_stem` (verify next==answer) else inferred `[answer, other]` (other from the "which colour follows X" diagnostic). Bead / shape / size SVGs. Generators in `qa-reports/fix_pattern_visuals.py` (`--kind color|shape|size`).
- **Status:** 69 fixed (colour 22, shape 37, size 9, +1 number stem-restore), 2026-06-21. 9 flagged unrecoverable (no original pattern + ambiguous choices).

### 22. Mismatched / decorative figure on a logic question — **Type I**
- **What it looks like:** "Which one does not belong: 28, 21, 26, 20?" showing an irrelevant **mirror** figure (`visual_alt: "topic-8-puzzles visual"`). A reused generic-template SVG got auto-attached to a number/logic question that needs no figure.
- **How to detect:** logic / sorting / odd-one-out / missing-number topic + a `<svg>` + the stem never references a figure. Detector `scan_decorative_figure_on_logic` (`content_qa_scan.py`, section "I"). The defect lives in **28 templates reused ≥8× across unrelated topics**.
- **Fix:** clear `visual_svg`/`visual_alt` + set `visual_requirement="none"` on the **self-contained** subset (numbers all in the stem, no undefined variables, plain choices) — `qa-reports/clear_mismatched_visuals.py`. Flag the rest (variables / not self-contained).
- **Status:** 316 cleared in L1 (only visual fields changed), 2026-06-21. The 24 flagged-for-review were then resolved (2026-06-21): 22 **restored** from `original_stem` (A+B+A with `If A=x and B=y…`, coin-comparison with the dropped name, which-doesn't-belong) via anchor extraction + verify-the-key-still-follows, figure cleared — `qa-reports/fix_l1_decorative_logic.py`; 2 unrecoverable removed.

### 23. Context-stripped "which direction now?" (unanswerable) — **Type N**
- **What it looks like:** `"Which direction now?"` / `"Which direction is Arjun facing now?"` with **no figure, no starting compass dir, no turn, no number** — the keyed direction (e.g. North) is underivable. Setup was lost when a multi-step rotation series got flattened; `original_stem` empty and the hint is off-topic ("Let's think about shapes!").
- **How to detect:** empty `visual_svg` + stem matches `which direction … (now?|facing)` + **no** setup token (`turn|left|right|clockwise|step|move|goes|north|south|east|west|up|down|\d`) + nothing recoverable in `original_stem`. Detector `scan_directional_unanswerable` (`content_qa_scan.py`, section "N"). **Guard:** self-contained variants ("Meera faces West and turns right. Which direction now?" → North) and "He goes up 3 steps. Which direction?" contain a setup token and are correctly kept.
- **Fix:** **remove** (unrecoverable, corrupted hint, would be fabrication to rebuild). Backed-up + logged.
- **Status:** 139 removed in L1, 2026-06-21 (`remove_l1_dups_unanswerable.py`).

---

## F. Structural mistakes

### 18. Duplicates & skeleton overload
- **What it looks like:** identical stem+choices+answer; or many near-identical questions from the same template flooding one file.
- **Detect:** `scan_duplicates` (`content_qa_scan.py`, section "L"). Key = (normalised stem, sorted choice **set**, **resolved answer VALUE**, visual-hash). **CRITICAL:** `correct_answer` is a 0-based **index**, so key on `choices[correct_answer]`, NOT the raw index — else shuffled-choice items with different real answers get wrongly merged (and same-value reorders get missed). Fixed 2026-06-21 (was keying on the index → false dedup of distinct "Which direction now?" items).
- **Fix:** keep first occurrence per key; remove the rest. `qa-reports/remove_l1_dups_unanswerable.py` (L1).
- **Status:** 1,136 + 342 exact + 1,147 near + 1,790 skeleton-trimmed across passes; 704 hidden dups exposed after filler-stripping; **L1 2026-06-21: 134 value-based dups + 11 newly-exposed-after-restore removed**.

---

## Detection toolkit (re-runnable)

A consolidated scanner lives at **`qa-reports/content_qa_scan.py`** — run it from `content-live/` to get current counts for the programmatic detectors (placeholders, ratio-angle keys, remainder keys, absent-figure, semicircle-as-circle, Venn/tree spoilers). It is read-only (reports, never edits). Re-run it after any new import to catch regressions.

```
cd ~/Downloads/kiwimath/content-live && python3 qa-reports/content_qa_scan.py
```

**Current state:** the scanner now runs **14 detectors A–N** (added H pattern-missing, I decorative-figure, J empty-stem, K hint-leak, L value-based-duplicate, M fake-svg, N directional-unanswerable). As of **2026-06-21, L1 = 0 and L2 = 0** flags across all A–N (per-level loops complete; olympiad 20,013→19,615; smoke 17/17, pre_deploy green). Two detectors were hardened during the L2 pass: **J** now flags only empty / one-word / absent-referent stems (was over-flagging sentence-completion MCQs, conversions, inline patterns, concrete prompts); **L** ignores intentional cross-level pairs (same question, different tier difficulty, separate files) and flags only same-level dups or same-difficulty cross-level misfiles. Later levels still carry flags pending their own loop: **L3 J≈9** (absent-referent pattern qs) + dups, plus L4–L7 + curriculum — process L3 next with the same A–N lens.

Verification harness used by every fix pass:
- `backend/pre_deploy_check.py` — counts + required-field + SVG-ref check (must end "ALL CHECKS PASSED").
- `backend/tests/smoke_level_v3.py` — 17 assertions (no answer-leak at fetch, economy consistency, idempotency). Must stay **17/17**.

### False positives the detectors must avoid (hard-won)

These tripped earlier scans — the detectors now guard against them, and any new detector should too:

- **Set notation is not a placeholder.** `{Elephant}`, `{Tiger, Lion}` (in "A ∩ B = ?") are correct sets. Placeholder tokens are *lowercase and short* (`{b}`, `{rem}`); the regex requires `[a-z][a-z0-9_]{0,5}` and strips `$…$` first.
- **`correct_answer` is a CHOICE INDEX for MCQ.** It is 0–3, not the answer value — comparing a computed truth to it gives garbage. Resolve the real value from `choices[correct_answer]` (or use `correct_value` for integer mode).
- **`\cdots`/`\ldots` contain the substring "dots"** — strip LaTeX commands before any "dots" match.
- **"dots" is a counting noun in lower grades** ("8 dots and gets 2 more") — the absent-figure detector requires explicit *figure/diagram* words, not bare "dots".
- **"tri*angle*" contains "angle"** — the ratio-angle validator uses a word boundary so similar-triangle side/area problems aren't mis-validated as angle-sum.
- **"clock*wise*" contains "clock"** — the image classifier used a negative lookahead so rotation questions weren't matched to clock figures.
- **A full circle is correct for inscribed/central-angle and paper-folding** — exclude those from the semicircle-as-circle check.
- **Multi-step / composite figures** ("divided/attached/inscribed") break naive single-formula validators — exclude them from answer-key validation.

---

## Golden rules (so we don't repeat these)

1. **A figure is an *aid*, never the *answer*.** If summing/counting the figure's marks gives the answer, the figure is wrong. Show *givens*, not the worked decomposition.
2. **Never reference a picture you don't show.** If the stem says "shown / the figure / dots / shaded," a real figure must exist — otherwise reword to pure text.
3. **Math-check every answer key in a computable family.** `correct_answer` is not sacred; build a validator per family.
4. **Visuals only where genuinely required.** Default to no figure for word problems; geometry is the main place figures earn their place.
5. **Plain language beats clever framing for K-8.** The wording should never be harder than the math.
6. **Substitute or strip every template token.** No `{b}`, `{n}`, `{rem}` may ever reach a child; no raw LaTeX accents in prose.
7. **Fix one field, touch one field.** Diff against backup; assert the change-set.
8. **Render before you ship a figure.** Generate the PNG and look at it (cairosvg) — don't trust the markup.

---

## Backups, changelogs, reports

- Per-pass backups: `content-live/olympiad/qa-reports/backup-*-<date>/`, `qa-reports/backup-<date>/`.
- This session's changelog: `content-live/olympiad/qa-reports/3types_changelog_2026-06-17.json` (Types A–E, 70 edits).
- Narrative reports: `qa-reports/3TYPES_QA_2026-06-17.md`, `QA_FULL_REPORT_2026-06-12.md`, `KM_CONTENT_QA_2026-06-14.md`, `KM_OLYMPIAD_QA_REPORT_2026-06-13.md`.
- Master memory: `CLAUDE.md` (every pass is logged there with counts).

---

## Open items for the next coworker

- **Validate the un-validated answer-key families:** fractions/decimals, multi-step word problems, combinatorics, probability (see #8).
- **Deep-audit L4–L7 solutions** (the IOQM/RMO/INMO/Grade7-8 imports) the way L1–L3 + curriculum were done (#11).
- **L5–L7 LaTeX-in-prose:** some `Σ_{k=1}^{L}`, `x^{2k}` are written outside `$…$` and render imperfectly — cosmetic, not yet swept.
- **L8 (IMO)** is intentionally empty (coming-soon, hidden by the empty-topic filter).
