# 04 · Every Mistake & Learning

**Read this before any content work.** This is the superset of everything that went wrong and what it taught us — content defects, engineering bugs, AI-process mistakes, and product reversals. The content-defect detail lives in the canonical `qa-reports/MISTAKES_REPOSITORY.md` (23 types, with detectors); this file summarizes those **and** adds the engineering / process / product mistakes that aren't in that doc.

The meta-lesson, stated once: **every mistake class became a re-runnable detector or a fixed habit, so it can never silently return.** That is the whole point of cataloguing them.

---

## A. Content defects (the 23-type catalogue)

These are the question-bank defects found across passes. Full detail (symptom, detector signal, examples, fix) is in `MISTAKES_REPOSITORY.md`; this is the index so you know what to look for.

| # | Class | What it looks like | Count fixed |
|---|-------|--------------------|-------------|
| 1 | Decorative filler prefix | story sentence glued before the real question ("A crystal glows near Chikoo. What is 7×8?") | ~6,937 |
| 2 | Empty / truncated stem | blank, or ends mid-word | 4 + 262 |
| 3 | Unanswerable (missing info) | asks for a value the text/figure doesn't determine | 209 |
| 4 (A) | Unsubstituted placeholder | a literal `{b}`, `{rem}` renders in the question | 20 |
| 5 (D) | Confusing formation | references a figure/"dots" picture that isn't shown | 5 |
| 6 | **Wrong key — arithmetic** | keyed to a distractor (3 cats × 4 legs keyed "7"=3+4) | 11 |
| 7 | Wrong key — percent | "sold 35%, how many left" keyed to the sold amount | 1 |
| 8 (B) | Wrong key — ratio larger/smaller | ratio 7:2 "larger angle" keyed to the smaller term | 1 |
| 9 | Answer-leaking hint | the hint states the final answer | 7,978 + 1,393 |
| 10 | Wrong / mismatched-formula hint | hint quotes the wrong number, or an area formula on a circumference question | 299 + 17 |
| 11 | Generic template solution | boilerplate that never uses this question's numbers | ~3,340 |
| 12 | Mismatched diagnostics | per-choice "why wrong" uses the wrong formula | (in #11) |
| 13 | Fake placeholder SVG | a grey box + label, no real figure | 2,461 |
| 14 | Mismatched template image | a clock drawn on a "square rotated 90°" question | 52 + 148 |
| 15 | Missing-but-required image | essential-visual flag, no figure | 14 |
| 16 (C) | Wrong figure (semicircle as full circle) | "semicircle r=14" drawn as a full circle | 2 + 13 |
| 17 (E) | **Figure reveals the solution** | Venn showing the derived regions / tree showing all leaves | 29 |
| 18 | Duplicates & skeleton overload | identical or near-identical questions flooding a file | thousands |
| 19 (F) | Figure labels the answer | right-triangle figure labelling the hypotenuse "5" + tiny font | 17 |
| 20 (G) | Angle label on wrong vertex | "30°" drawn on the right-angle corner | 4 |
| 21 (H) | Pattern visual missing | "what colour comes next?" with no image | 69 |
| 22 (I) | Decorative figure on a logic question | a reused mirror template on "which doesn't belong: 28,21,26,20?" | 316 + 24 |
| 23 (N) | Context-stripped "which direction now?" | rotation series flattened → no setup, answer underivable | 139 |

**The two most instructive families:**

- **Wrong answer keys (#6–8) — the most dangerous defect of all.** The child does the math right and is told they're wrong; that destroys trust instantly. Root cause: early QA treated `correct_answer` as *locked* and never math-checked it. The fix is a *philosophy*: **every computable answer-key family gets its own validator.** Still un-validated (open work): fractions/decimals, multi-step, combinatorics, probability.

- **The figure is the answer (#17, #19) — the subtle defect.** A Venn diagram that already shows the region decomposition, or a triangle that labels its own hypotenuse, lets the child *read* the answer instead of *computing* it — trivializing the very concept being taught. Golden rule: **a figure is an aid, never the answer; show givens, not the worked decomposition.**

---

## B. The answer-key validation lesson (its own section because it matters most)

The live bug that started it: *"Raju has 7 watermelons, gets 5 more"* keyed to **2** (a distractor), not 12. Prior QA had passed it because it never checked the math.

The learnings:
1. **`correct_answer` is not sacred.** Build a validator that recomputes and flags `recompute ≠ key`.
2. **Validators must be family-scoped and guarded.** "tri**angle**" contains "angle"; "in all / altogether" appears in *both* addition and multiplication ("8 groups of 22, how many in all" is 8×22, not 8+22) — prioritize the multiplication phrasing; composite/multi-step figures break single-formula validators (exclude them).
3. **`correct_answer` is a 0-based CHOICE INDEX for MCQ**, not the value. Comparing a computed truth to the index gives garbage. Resolve `choices[correct_answer]` or use `correct_value`.
4. For non-math subjects (JEE/NEET) **no validator is possible** — which is exactly why those answers must come from authoritative sources and human experts, never the AI (the central rule of the `HANDOVER_MINIAPP/` pack).

---

## C. Engineering bugs (and their fixes)

| Bug | What happened | Fix / lesson |
|-----|---------------|--------------|
| **MCQ option mangling** | PDF text of an option `1046½` extracted as `1·1046·2`; a numeric grab returned "1" → silently wrong grading | Keep MCQ as real **letter-choice** graded by the key's letter index; never convert option text to a number |
| **Dedup keyed on the index** | the duplicate detector keyed on the raw `correct_answer` index, so two "Which direction now?" items with the same index but **shuffled choices** were wrongly merged (and same-value reorders missed) | Key dedup on the **resolved value** `choices[correct_answer]` + the visual hash |
| **IDOR on per-user routes** | `/next` (and others) didn't check the caller owned the user → cross-user data access | `assert_user_match` → 403; applied to every per-user route |
| **Double-award / double-debit** | replay/double-tap on answer-check / spend could award or debit twice | idempotency keys on answer-check, contest submit, economy spend |
| **Spend currency not pinned** | a 300-coin book could be paid with 300 gems | unlock requires the correct currency |
| **Adaptive state regressed** | under concurrent writes the ladder could jump a learner backward on re-login | monotonic re-read guard (no-regress) |
| **Reader engine limits** | EPUB/epub.js: paging manager enum exposed only the wrong mode → pages wouldn't flip; `onRelocated` setState storms → flicker | Own HTML WebView reader; cache the widget; progress via `ValueNotifier` not setState; stage big files to `file://` |
| **Clustering blob** | single-linkage union-find chained unrelated sequences into one 656-item "concept" | leader clustering at Jaccard ≥ 0.70 |
| **Empty-topic stubs showed** | empty L4–L8 scaffold topics appeared in the UI | empty-topic filter (`if t.questions`) |
| **Progress score didn't change with grade** | `/me/progress` derived the score from *global* accuracy, so every grade showed the same number | scope accuracy/mastery to the requested level |

**Accepted-but-flagged:** the coin debit + idempotency isn't yet a single Firestore transaction (cross-instance double-tap risk). Fine now; **must become a transaction before real money.**

---

## D. AI-process mistakes (how *the assistant* got it wrong — read these, they're easy to repeat)

These are mistakes the AI itself made during the work. A new cowork will be tempted into the same ones.

1. **Misreading dense figures.** During a geometry QA, the AI rendered figures in a dense montage and misread them (read `tan α = 1/7` as `1/2`, mismatched tile labels) — and nearly "fixed" content that was actually correct. **Lesson: render figures one-per-row at full size and look carefully; never trust a dense montage; never edit content on a shaky read.**
2. **Trusting extracted PDF text for math.** Led to the mangling bugs in `01`/`C`. **Lesson: faithful-image or brute-force-validate; never trust the text stream for notation.**
3. **Wrong CLI invocation.** `rclone copyid` (errored "unknown command") — the right form is `rclone backend copyid REMOTE id dir/`. **Lesson: verify a tool's actual interface before scripting around it.**
4. **Over-eager "verification" that corrupts.** The instinct to "double-check this answer by re-solving it" is *dangerous* for non-trivial math and *impossible* for science — it introduces errors. **Lesson: the only safe automated check is mechanical (did it get an answer? is it hidden pre-submit? duplicates?) or a brute-force on a strictly computable family.**
5. **Sandbox surprises.** The mount forbids `rm` (copy-only); bare `#` comments break some commands; cairosvg over-saturates 8-hex-alpha colors and can't render some unicode (shows tofu boxes) though browsers are fine. **Lesson: know the environment's quirks; render-verify in the real target (browser), not just the converter.**

---

## E. Product reversals (things we built, then undid — and why)

Reversals aren't failures; they're learning made visible. Each one sharpened the product.

1. **Image-based practice questions → books only.** 1,172 faithful-image Vedantu questions were ingested into the served bank, then **pulled** — on-device they looked unfinished outside a book. Kept only in the Library; a backlog tracks slow conversion to clean typed HTML. **Lesson: a faithful image is great *inside a book*, weak as a *standalone practice question*. Match the format to the surface.**
2. **KiwiReader / EPUB → our own HTML reader.** Two reader engines were adopted and abandoned before settling on a WebView we fully own (see `02` §5). **Lesson: for a study reader, control beats convenience; don't inherit an engine's limits.**
3. **Grade-based → Level-based olympiad, then grade-aligned re-tiering.** The olympiad section was re-tagged from grades to L1–L8; later the Vedantu books were re-tiered when the founder corrected the grade mapping (their "Level N" was offset). **Lesson: pin the level/grade mapping *early and explicitly* — a wrong mapping silently mis-places everything.**
4. **4 pillars → 7 → 9 strands.** The taxonomy grew as real content arrived (added Trig, Basic Maths, Arithmetic; then Geometry + Combinatorial-Geometry + Algebra-NT). **Lesson: let the taxonomy follow the content, but make it first-class in the backend when it does.**
5. **Verified-quiz pool: badge → backend-only.** Started to badge "verified" content in the UI; the founder chose to make it a silent backend preference instead. **Lesson: not every internal quality signal needs to be a user-facing label.**

---

## F. The false-positive guards (hard-won — any new detector must respect these)

These tripped earlier scans. They're the difference between a detector that helps and one that deletes good content:

- **Set notation is not a placeholder.** `{Tiger, Lion}` in "A ∩ B = ?" is a correct set; placeholder tokens are lowercase + short (`{b}`, `{rem}`). Strip `$…$` first, require `[a-z][a-z0-9_]{0,5}`.
- **`correct_answer` is a choice INDEX for MCQ** (not the value) — resolve `choices[correct_answer]`.
- **`\cdots`/`\ldots` contain the substring "dots"** — strip LaTeX before any "dots" match.
- **"dots" is a counting noun in lower grades** ("8 dots and gets 2 more") — require explicit *figure/diagram* words for the absent-figure detector.
- **"tri*angle*" contains "angle"** — use a word boundary in the ratio-angle validator.
- **"clock*wise*" contains "clock"** — negative lookahead in the image classifier.
- **A full circle is correct for inscribed/central-angle and paper-folding** — exclude from the semicircle-as-circle check.
- **Intentional cross-level duplicates** (same question calibrated at a different tier) are NOT dups — the dedup detector ignores same-question/different-difficulty pairs in separate files.

---

## G. The golden rules (the distilled list)

1. A figure is an *aid*, never the *answer*. Show givens, not the worked decomposition.
2. Never reference a picture you don't show.
3. Math-check every answer key in a computable family — `correct_answer` is not sacred.
4. Visuals only where genuinely required; default to none.
5. Plain language beats clever framing; the wording must never be harder than the math.
6. Substitute or strip every template token — no `{b}`/`{rem}`/raw LaTeX accents ever reach a learner.
7. Fix one field, touch one field — back up, diff, assert the change-set.
8. Render before you ship a figure — look at the image, not the markup.
9. Detect, don't eyeball — every defect class becomes a re-runnable detector.
10. Batch then QA; slow and certain; keep green. A missing item costs nothing, a wrong item costs a user.

---

## H. Open items (the honest backlog for the next cowork)

- **Validate the un-validated answer-key families:** fractions/decimals, multi-step word problems, combinatorics, probability.
- **Deep-audit L4–L7 solutions** (the IOQM/RMO/INMO/Grade7-8 imports) as L1–L3 + curriculum were done.
- **Run the A–N scanner loop on L3–L7 + curriculum** (L1 and L2 are at 0; the rest still carry flags).
- **Convert the image-question backlog** (`CONVERSION_BACKLOG.json`) to clean typed HTML/LaTeX — slowly, only when 100% certain.
- **Make the coin spend a Firestore transaction** before any real-money/IAP.
- **Finish the Number Sense interactive book** (9 of 13 worksheets remaining).
