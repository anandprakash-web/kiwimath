# 05 · Scripts Catalogue

The canonical, reusable scripts behind the ACAD content engine — copied into
`ACAD_OS_MANUAL/scripts/` and documented here. Per-chapter book *content*
modules (e.g. `l2_chNN_*.py`) are deliberately **not** copied: only the reusable
*frameworks* (builders + helper/figure toolkits) are.

All scripts are Python 3. Most read/write the repo at `~/Downloads/kiwimath`
and resolve their own location with `os.path.dirname(__file__)`, so they assume
they run **from their original repo path**, not from this manual's `scripts/`
folder. Where a script hard-codes an absolute path (e.g. a Drive-synced PDF
folder under `~/Downloads/...`), that is called out under **Inputs** as a path to
edit for a new environment.

---

## Table of contents

### `content_qa/` — defect scanning, clustering, repair (operate on `content-live/`)
| Script | One-line purpose |
|---|---|
| `content_qa_scan.py` | **Read-only** A–N defect scanner (the QA gate); reports flag counts + example IDs, exits non-zero if any flag. |
| `cluster_concepts.py` | Tags every served question with a `skill_id` concept cluster + adaptive-ladder fields (`skill_seq`, `skill_difficulty`); writes `skill_clusters.json`. Idempotent. |
| `fix_pattern_visuals.py` | Type H — rebuilds the missing bead/shape/size pattern SVG for "what comes next?" questions so the cycle yields the keyed answer. |
| `clear_mismatched_visuals.py` | Type I — clears decorative/mismatched template figures off self-contained L1 logic/number questions. |
| `fix_l1_decorative_logic.py` | L1 Type-I tail — restores logic stems from `original_stem` (verifying the key still holds) + clears the stray figure; removes 4 unrecoverable items. |
| `remove_l1_dups_unanswerable.py` | Removes L1 value-based true duplicates + context-stripped "which direction now?" unanswerables; backs up + writes a recovery manifest. |
| `remove_level_defects.py` | Generic per-level (`--level Ln`) within-level dedup + explicit `--ids` removal; the reusable engine for the L2…L7 QA loop. |

### `ingestion/` — source → questions
| Script | One-line purpose |
|---|---|
| `ingest_quiz.py` | Ingests Vedantu assignment PDFs into "Verified" questions as faithful cropped problem images + answer resolved from the source key (integer / MCQ-letter-by-index / fraction-decimal range). |

### `book_build/` — faithful-render + authored interactive books
| Script | One-line purpose |
|---|---|
| `build_book.py` | Builds ONE faithful-render interactive HTML book from a Vedantu pillar PDF folder (WebP page renders + designed cover + video/solution reveal tabs). |
| `build_workbook.py` | Same, for a *flat* folder of session-course PDFs (collapsible session cards, no video tab). |
| `build_all.py` | Resumable batch driver: builds all 16 pillar books via `build_book.py`, skipping any already in the 2-tab-cover format, within a time budget. |
| `render_cache.py` | Renders every slide of the 13 Number-Sense worksheet PDFs to a WebP cache (idempotent). **Run single-process.** |
| `assemble_ns.py` | Assembles the interactive "Number Sense" book from the slide cache + a hand-keyed `INTERACTIVE` config (tap-MCQ / type-and-check). |
| `build_l2book.py` + `l2_helpers.py` + `l2_figs.py` | **Authored-book framework (L2):** book template/renderer + ~25-function exact-vector SVG figure toolkit + pedagogy helpers (the per-chapter modules are content, not copied). |
| `build_l3book.py` + `l3_helpers.py` + `l3_figs.py` | Authored-book framework (L3): same as L2 plus 3 extra figures (`angle`, `ratio_bar`, `coord_grid`). |
| `vedantu_build_all.py` | *(placeholder)* — duplicate of `build_all.py` that the read-only mount could not delete; ignore it. |

### `verification/` — pre-deploy gates
| Script | One-line purpose |
|---|---|
| `pre_deploy_check.py` | Validates content (required fields, 4-choice MCQs, unique IDs, SVG refs, expected per-level bank counts) before deploy; exits non-zero on any error. |
| `tests/smoke_level_v3.py` | End-to-end `/v3` smoke: olympiad/curriculum fetch (no answer leak), economy/wallet consistency, idempotency, stats. |
| `tests/smoke_adaptive_skill.py` | Adaptive skill-ladder engine smoke: skill→next, wrong→cluster-drip, exhaust→next, re-login resume (no jump-back), no-regress, API round-trip. |
| `tests/smoke_contest_league.py` | Daily Contest + Weekly League smoke: deterministic set, score+LP, one-attempt replay, leaderboard, rollover, IDOR/auth 403s. |
| `tests/smoke_store.py` | Store MVP smoke: catalog, purchase-before-download gating, entitlements, wallet grant/spend, auth 403s. |

---

## `content_qa/`

> All seven operate on the live bank under `content-live/` (`olympiad/L*/` +
> `curriculum/*/grade*/`). They locate that bank **relative to their own file**
> (`ROOT = dirname(dirname(__file__))` = `content-live/`), so they must live at
> `content-live/qa-reports/` to run. The scanner is read-only; the six fixers
> mutate, back up first, and only ever touch the intended fields.

### `content_qa_scan.py`
- **Original location:** `content-live/qa-reports/content_qa_scan.py`
- **Purpose:** The QA gate. Runs 14 conservative detectors (defect types A–N from the Mistakes Repository) over the whole served bank and reports counts + example IDs. **Read-only — never edits.**
- **Inputs:** No args. Globs `content-live/olympiad/L*/L*_*.json` + `content-live/curriculum/*/grade*/questions.json` (files >1 KB). No env vars, no absolute paths.
- **Detectors:** A unsubstituted `{placeholders}`/LaTeX accents · B wrong ratio-angle key (larger/smaller) + remainder-theorem sanity · C semicircle/sector drawn as a full circle · D promises a figure that isn't shown · E Venn/tree spoiler figure (regions/leaves = answer) · F geometry figure labels the asked quantity · G acute-angle label on a right-angle vertex · H "comes next" pattern with empty visual · I decorative figure on a logic/number question · J empty / one-word / absent-referent stem · K answer leaks in an early hint · L true duplicate (stem + option **set** + resolved answer **value** + visual hash) · M fake grey-box placeholder SVG · N context-stripped "which direction now?" unanswerable.
- **Outputs:** Prints to stdout only; writes nothing. **Exit code `0` = clean, `1` = at least one flag** (so it gates CI / a fix loop).
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/content-live && python3 qa-reports/content_qa_scan.py
  ```
- **Guardrails / gotchas:** Read-only and idempotent. Detectors favour **precision** (e.g. detector L keys on the *resolved choice value*, not the raw MCQ index, so shuffled-choice items aren't falsely merged; detector K requires a giving-away context and skips short/common words). The standing convention is **fix every flag, re-run until TOTAL = 0**; when a new defect class appears, add a detector here *first*.
- **Reuse for a new exam app:** The *harness shape* is fully reusable (one detector per mistake type, precision-first, exit-non-zero-on-flag, "scan → fix → re-scan to zero" loop). The **individual detectors are math-content-specific** (geometry figures, ratio angles, number patterns, compass directions) and must be re-authored per the new subject's defect catalogue. It also assumes this exact JSON question schema (`stem`, `choices`, `correct_answer` as index, `correct_value`, `visual_svg`/`visual_png`, `hint` dict, `irt_b`).

### `cluster_concepts.py`
- **Original location:** `content-live/qa-reports/cluster_concepts.py`
- **Purpose:** Tags every served question with the **skill cluster** (one concept = number-varied + wording-varied copies collapsed) it belongs to, and lays the adaptive difficulty ladder. The precursor + ongoing maintainer of the adaptive layer.
- **Inputs:** No args. Globs the same olympiad + curriculum files (>800 B). Tunable constant `TH = 0.70` (leader-clustering Jaccard threshold; lower = coarser concepts). Builds a character-name lexicon from the data so "Help X figure out:" wrappers and character names don't fragment clusters.
- **Outputs:** **Mutates every question file in place** (additive fields only: `skill_id`, `skill_size`, `skill_rank`, `is_skill_original`, `skill_seq`, `skill_difficulty`) and writes the index `content-live/skill_clusters.json`. Prints `tagged N questions into M concepts | integrity_bad=K`.
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/content-live && python3 qa-reports/cluster_concepts.py
  ```
- **Guardrails / gotchas:** **Idempotent** — it strips its own `SK` fields before re-tagging, then verifies a per-question `corehash` (everything *except* the skill fields) is byte-identical before/after; `integrity_bad` must be `0` (proves it changed no existing field). **Always re-run after any import/dedup** so clusters + ladder stay current. Uses **leader clustering** (not single-linkage union-find, which chained unrelated families into one blob). Operators are normalized so arithmetic facts (3×4 vs 3+4) don't merge.
- **Reuse for a new exam app:** **Method is subject-agnostic** (stem → normalized signature → leader-cluster by Jaccard → emit skill_id + difficulty ladder). The normalization lexicon (character names, "Help …" prefixes, the ×/÷/− operator map) is tuned for this content and would be re-tuned per subject, but the algorithm and the additive-tag + corehash-integrity pattern transfer directly.

### `fix_pattern_visuals.py`
- **Original location:** `content-live/qa-reports/fix_pattern_visuals.py`
- **Purpose:** **Type H** repair. A content pass shortened some "What colour/shape/size comes next?" stems to bare prompts but stripped the `visual_svg`, leaving them unanswerable. This rebuilds a valid pattern SVG whose cycle yields the keyed `correct_answer`.
- **Inputs:** `--kind color|shape|size` (default `color`), `--apply` (omit for dry-run). Reads all `content-live/olympiad/**/*.json` + `curriculum/**/*.json` (skips `qa-reports`). Recovers the sequence from each question's `original_stem` when present (and verifies `next == answer`), else infers a 2-item `[answer, other]` cycle from the diagnostics / a distractor (so `next` is always the answer).
- **Outputs:** Writes **only** `visual_svg` + `visual_alt` on fixed questions; answer/choices/hint untouched. Backs up each changed file once to `content-live/qa-reports/backup-pattern-visuals-<date>/` before overwriting. Prints fixed/skipped counts + the skip list (unrecoverable items are *flagged, not fabricated*).
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/content-live/qa-reports
  python3 fix_pattern_visuals.py --kind color          # dry run
  python3 fix_pattern_visuals.py --kind color --apply  # then shape, then size
  ```
- **Guardrails / gotchas:** Mutating but **backs up before write** and **only touches visual fields**. Refuses to fabricate: if the answer isn't a known colour/shape/size or no "other" can be derived, it **skips and logs** rather than inventing a pattern. Generates clean SVGs (beads on a string / outlined shapes / size-graded circles, each ending in a dashed "?").
- **Reuse for a new exam app:** **Math-specific.** The defect *idea* (a stripped visual leaves a question unanswerable; rebuild it from `original_stem` and verify the key) transfers, but the SVG generators (beads/shapes/sizes) and the recovery heuristics are bespoke to visual pattern questions.

### `clear_mismatched_visuals.py`
- **Original location:** `content-live/qa-reports/clear_mismatched_visuals.py`
- **Purpose:** **Type I** repair. A reused generic-template SVG (e.g. a "mirror" figure) was auto-attached to self-contained number-logic questions ("Which doesn't belong: 28,21,26,20?") that need no figure. Clears the figure on the safe, unambiguous subset.
- **Inputs:** `--apply` (omit for dry-run). Operates on `content-live/olympiad/L1/L1_*.json` only. Targets logic/sorting/odd-one-out/missing-number topics where the stem makes no figure reference, choices are plain values, there are no undefined variables (`A+B`), and ≥2 digits are present.
- **Outputs:** Sets `visual_svg=None`, `visual_alt=""`, `visual_requirement="none"` on cleared questions (answers intact). Backs up to `content-live/qa-reports/backup-mismatch-visuals-<date>/`. Prints `cleared=… flagged(not touched)=…` and lists the flagged-for-manual-review items.
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/content-live/qa-reports
  python3 clear_mismatched_visuals.py          # dry run
  python3 clear_mismatched_visuals.py --apply
  ```
- **Guardrails / gotchas:** Mutating, **backs up first**, **only clears visual fields**. Conservative: anything with an undefined variable, a figure reference, or figure-style choices is **flagged, not cleared**. Hard-wired to L1.
- **Reuse for a new exam app:** **Math-specific** (the topic tags + "self-contained" heuristic are content rules). The *principle* — detect a decorative figure on a question answerable from text alone and strip only the visual fields — is reusable.

### `fix_l1_decorative_logic.py`
- **Original location:** `content-live/qa-reports/fix_l1_decorative_logic.py`
- **Purpose:** The **L1 Type-I tail**: items flagged by detector I that `clear_mismatched_visuals.py` would *not* auto-clear because the served stem had an undefined variable (`A+B`), a dropped name, or a narrative prefix. Restores the canonical stem from `original_stem` and clears the stray figure; removes the few that are unrecoverable.
- **Inputs:** `--apply` (omit for dry-run). Operates on `content-live/olympiad/L1/L1_*.json`. Two hard-coded sets: `RESTORE` (the ~22 recoverable IDs) and `REMOVE` (4 unrecoverable IDs). Pulls the stem back via regex anchors from `original_stem`.
- **Outputs:** On the restore set, writes `stem` + clears `visual_svg`/`visual_alt`/`visual_requirement`; the remove set deletes whole items. Backs up to `backup-l1-decorative-<date>/`. **Aborts before writing if any verify fails.**
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/content-live/qa-reports
  python3 fix_l1_decorative_logic.py          # dry run (prints verify results)
  python3 fix_l1_decorative_logic.py --apply
  ```
- **Guardrails / gotchas:** Mutating, **backs up first**, **fail-closed**: each restored stem is arithmetic-/comparison-verified to still yield the keyed answer (A+B+A == key, most/fewest-coin == key, listed-token present); any failure aborts the whole apply. No fabrication — stems come only from `original_stem`.
- **Reuse for a new exam app:** **Math-specific** (hard-coded ID lists, arithmetic verifiers). The *pattern* — recover from a preserved `original_stem`, re-verify the answer key still follows, abort-on-any-failure — is a strong reusable safety discipline.

### `remove_l1_dups_unanswerable.py`
- **Original location:** `content-live/qa-reports/remove_l1_dups_unanswerable.py`
- **Purpose:** Removes two confirmed L1 defect classes: **value-based true duplicates** (detector L) and **context-stripped directional unanswerables** (detector N, "Which direction now?" with no setup recoverable).
- **Inputs:** `--apply` (omit for dry-run). Operates on `content-live/olympiad/L1/L1_*.json`. Duplicate key = stem + sorted choice set + **resolved answer value** (`choices[correct_answer]`) + visual hash; keeps the first occurrence.
- **Outputs:** Rewrites files with the offending items removed. Backs up changed files to `backup-dedup-l1-<date>/` and writes a recovery manifest `removed_l1_<date>.json` (every removed id + reason + surviving twin) — fully reversible. Prints removal counts by reason.
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/content-live/qa-reports
  python3 remove_l1_dups_unanswerable.py          # dry run
  python3 remove_l1_dups_unanswerable.py --apply
  ```
- **Guardrails / gotchas:** Mutating (deletes items) but **backs up + manifests every removal**, and **asserts every removed duplicate has a surviving twin** before writing. After running, **re-cluster** (`cluster_concepts.py`) and update `counts_report.json` + the smoke/pre-deploy expected counts — removals cascade into those.
- **Reuse for a new exam app:** **Mostly subject-agnostic** for the dedup half (the value-based-key idea is general and important — never key on a raw MCQ index). The directional-unanswerable half is math/spatial-specific. The backup + manifest + surviving-twin assertion discipline is reusable as-is.

### `remove_level_defects.py`
- **Original location:** `content-live/qa-reports/remove_level_defects.py`
- **Purpose:** The **generic, reusable per-level defect remover** — the engine for the L2…L7 QA loop. Within a single level, removes value-based true duplicates plus an explicit list of unanswerable IDs.
- **Inputs (argparse):** `--level Ln` (required, e.g. `L2`), `--ids KM-L2-…,KM-L2-…` (optional explicit removals), `--apply`. Operates on `content-live/olympiad/Ln/Ln_*.json`.
- **Outputs:** Rewrites files minus the removed items; backs up to `backup-Ln-defects-<date>/` and writes `removed_Ln_<date>.json`. Prints per-reason counts. **Does not touch cross-level pairs** (the same question intentionally calibrated for two tiers in separate files — a student never sees both).
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/content-live/qa-reports
  python3 remove_level_defects.py --level L2 --ids KM-L2-ALG-0232,KM-L2-NT-0430          # dry run
  python3 remove_level_defects.py --level L2 --ids KM-L2-ALG-0232,KM-L2-NT-0430 --apply
  ```
- **Guardrails / gotchas:** Mutating but **backs up + manifests**, asserts no removed duplicate's twin is itself removed, and scopes strictly within one level. Re-cluster + update counts after applying.
- **Reuse for a new exam app:** **Largely subject-agnostic** — within-level value-based dedup + explicit-ID removal with backup/manifest is generic. Only the `Ln` level taxonomy and the JSON schema are app-specific.

---

## `ingestion/`

### `ingest_quiz.py`
- **Original location:** `outputs/vedantu_build/ingest_quiz.py`
- **Purpose:** Ingests Vedantu assignment PDFs into gradeable "Verified" daily-quiz questions. Keeps each problem as a **faithful cropped page image** (so exact math notation + figures survive — sidesteps the exponent/fraction text-mangling that plagues OCR) plus its answer resolved from the source Answer Key.
- **Inputs (positional):** `<Vedantu_Content_root>` `<content-live/olympiad root>`. Iterates source folders `L5/L6/L7` (the sheet's levels) and grade-maps them **down one tier** (`SRC_TO_OUR = {L5→L4, L6→L5, L7→L6}`). Requires `PyMuPDF (fitz)` + `Pillow`. The source folder is whatever path you pass (in practice `~/Downloads/Vedantu_Content`) — **edit the path you pass** for a new environment.
- **Answer resolution:** integer key → typed-integer (exact); fraction/decimal → typed answer with an accepted `[answer_min, answer_max]` ±1% range; MCQ letter (a–e) → a **real letter-choice MCQ graded by index** (it never converts option *text* to a number — PDF text mangles fractions/√/exponents in options). If options aren't a clean contiguous a,b,c set in the crop, it **skips** rather than risk a wrong key.
- **Outputs:** Writes `content-live/olympiad/Ln/Ln_<PILLAR>_<topic>.json` (new IDs `KM-Ln-<PILLAR>-NNNN`, `legacy_id`, `source`, `verified:true`, `visual_png` base64 crop). Re-runnable: **skips any topic file already written** and protects the two hand-validated NT topics (`gcd_lcm`, `cyclicity`). Prints a per-topic table + total ingested.
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/outputs/vedantu_build
  python3 ingest_quiz.py ~/Downloads/Vedantu_Content ~/Downloads/kiwimath/content-live/olympiad
  ```
- **Guardrails / gotchas:** Mutating (creates new bank files) but **idempotent** (skips existing) and **protects** the hand-validated topics. The **golden rule** baked in: never trust mangled option text — keep MCQs as letter-by-index, grade typed answers only for direct-numeric keys. After ingesting, run the scanner → re-cluster → update counts → smoke/pre-deploy.
- **Reuse for a new exam app:** **Method is highly reusable** (faithful-crop the problem image, resolve the key by mode, MCQ-by-letter-index, range-grade non-integers, idempotent skip). The level/pillar mapping, the grade offset, and the ID scheme are app-specific. Any subject with PDF source banks benefits from the "image the question, don't re-type the math" discipline.

---

## `book_build/`

> The faithful-render builders read PDFs from a Drive-synced folder under
> `~/Downloads/` (`SRC = ~/Downloads/Vedantu_Content` or
> `~/Downloads/VEL Wavebook PDFs/...`) and write HTML books into
> `content-books/<id>/`. **Those `SRC` paths are hard-coded near the top of each
> builder and must be edited for a new machine.** All require `PyMuPDF (fitz)` +
> `Pillow`.

### `build_book.py`
- **Original location:** `outputs/vedantu_build/build_book.py`
- **Purpose:** Builds ONE faithful-render interactive HTML book from a Vedantu pillar PDF folder, with a designed per-pillar gold-line-art cover.
- **Inputs (positional):** `<LEVEL> <PILLAR_FOLDER> "<Display Pillar>" <Tier> <out_id>` (e.g. `L5 NumberTheory "Number Theory" IOQM ioqm-numbertheory`). Reads `~/Downloads/Vedantu_Content/<LEVEL>/<PILLAR_FOLDER>/*.pdf` (**hard-coded `SRC`**). Per-pillar palettes + SVG motifs (prime lattice, parabola, circumcircle, K5, unit circle, (a+b)² square, ratio bars) are built in.
- **Outputs:** Writes `content-books/<out_id>/<out_id>.html` (WebP page renders base64-embedded; problem pages, then `<details>` reveal tabs for "▶ Video solutions" and "Answers & worked solutions"; night-mode toggle; smooth-scroll contents). Prints path + size + topic count. Overwrites in place.
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/outputs/vedantu_build
  python3 build_book.py L5 NumberTheory "Number Theory" IOQM ioqm-numbertheory
  ```
- **Guardrails / gotchas:** Splits problem vs solution pages by page text ("Answers Key"/"Solutions"); extracts `youtu.be`/`youtube.com` links for the video tab. Pages render at SCALE 2.0 / WebP q72. The output carries an `<!-- fmt:2tab-cov -->` marker that `build_all.py` uses to decide whether a rebuild is needed.
- **Reuse for a new exam app:** **Subject-agnostic pipeline** (render PDF pages → WebP → wrap in an interactive shell; questions are never re-typed so notation/figures are exact). Only the cover palette/motif map and the "Answers Key/Solutions" split heuristic are content-flavoured.

### `build_workbook.py`
- **Original location:** `outputs/vedantu_build/build_workbook.py`
- **Purpose:** Same faithful-render approach for a **flat folder** of session-course PDFs (Grade 3-4 / 5-6 workbooks): mixed topics, session-ordered, collapsible session cards, worked-solution reveal, **no video tab** (these PDFs have none). General magic-square cover motif.
- **Inputs (positional):** `<SRC_SUBFOLDER> "<Display>" "<Tier>" <out_id> <base_hex> <gold_hex>`. Reads `~/Downloads/Vedantu_Content/<SRC_SUBFOLDER>/*.pdf` (**hard-coded `SRC`**), ordered by a leading number in each filename.
- **Outputs:** Writes `content-books/<out_id>/<out_id>.html` (each session a native `<details>` card; problem pages then an "Answers & worked solutions" reveal; sticky top bar; back-to-contents FAB). `<!-- fmt:wb2 -->` marker. Prints path + size + session count.
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/outputs/vedantu_build
  python3 build_workbook.py L3 "Grade 3–4 Workbook" "Grade 3–4" g34-workbook "#0E3B2E" "#EBC95C"
  ```
- **Guardrails / gotchas:** No-JS contents (native `<details>`). Same page-split heuristic as `build_book.py` but no video extraction.
- **Reuse for a new exam app:** **Subject-agnostic** (same render-and-wrap pipeline; the only content assumption is the answers/solutions split text).

### `build_all.py`
- **Original location:** `outputs/vedantu_build/build_all.py`
- **Purpose:** Resumable, time-budgeted batch driver that builds all 16 pillar books by shelling out to `build_book.py`.
- **Inputs:** optional positional `BUDGET` seconds (default 33). Hard-coded list `M` of the 16 `(level, folder, display, tier, out_id)` tuples (L5/L6/L7 × pillars).
- **Outputs:** Calls `build_book.py` per book (which writes `content-books/<id>/`); prints what it built this run + how many of 16 are done + what remains.
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/outputs/vedantu_build && python3 build_all.py 120
  ```
- **Guardrails / gotchas:** **Resumable** — skips any book whose HTML already exists *and* contains the `fmt:2tab-cov` marker (so only stale-format books rebuild); stops cleanly when the time budget is hit (rerun to continue). Direct in-place overwrite (the sandbox mount forbids `rm`).
- **Reuse for a new exam app:** **Subject-agnostic driver pattern** (resumable, format-marker-gated, time-budgeted batch). Re-point the `M` list + `build_book.py` call at the new content.

### `render_cache.py`
- **Original location:** `content-books/_pipeline/render_cache.py`
- **Purpose:** Renders every slide of the 13 Number-Sense worksheet PDFs to a WebP cache so the assembler can build the book without re-rendering.
- **Inputs:** No args. Reads `~/Downloads/VEL Wavebook PDFs/Number Sense and Operations/` (**hard-coded `SRC`**) using a fixed `CHAPTERS` filename→title list. Renders at SCALE 1.3 / WebP q78.
- **Outputs:** Writes `outputs/nsbuild/cache/cNN/pNNN.webp` per slide + `cache/manifest.json`. Idempotent (skips a slide whose cache file already exists and is non-empty). Prints per-chapter page counts + total MB.
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/content-books/_pipeline && python3 render_cache.py
  ```
- **Guardrails / gotchas:** **RUN SINGLE-PROCESS** — duplicate concurrent render processes caused memory hangs / OOM (exit 137). Idempotent, so a killed run resumes safely.
- **Reuse for a new exam app:** **Subject-agnostic** PDF→WebP slide-cache step. Only the `SRC` path + `CHAPTERS` list are content-specific.

### `assemble_ns.py`
- **Original location:** `content-books/_pipeline/assemble_ns.py`
- **Purpose:** Assembles the single interactive "Number Sense" HTML book from the slide cache + a hand-keyed answer config — faithful slides stay images, but configured slides become **tap-the-answer (MCQ / multi-select)** or **type-and-check (a+b=c, a−b=c, single answer)** interactions.
- **Inputs:** No args. Reads `outputs/nsbuild/cache/` (manifest + slides) and re-crops a few interactive slides from the source PDFs at `~/Downloads/VEL Wavebook PDFs/...` (**hard-coded `SRC`**). The answer key is the in-file `INTERACTIVE` dict keyed by `(chapter_idx, slide_1based)`.
- **Outputs:** Writes `outputs/nsbuild/number-sense.html` and copies it to `content-books/number-sense/number-sense.html`. Prints size + chapter/interactive/total-slide counts.
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/content-books/_pipeline && python3 assemble_ns.py   # after render_cache.py
  ```
- **Guardrails / gotchas:** Re-run after extending `INTERACTIVE` (idempotent overwrite). Faithful slides are downscaled 0.82× / WebP q72 at assembly to keep the single file light enough for low-end phones (base64 inflates WebP ~1.33×). Slides that can't be auto-keyed safely (drag-manipulatives, ambiguous counts) are **left faithful + commented**, not guessed.
- **Reuse for a new exam app:** **Pattern is reusable** (faithful visual + replace the printed answer area with real tap/type controls + JS check). The `INTERACTIVE` answer key is hand-authored per worksheet — i.e. **transcription is manual and subject-specific**, only the rendering/interaction scaffolding is generic.

### Authored-book framework — `build_l2book.py` / `l2_helpers.py` / `l2_figs.py` and the L3 trio
- **Original locations:** `outputs/l2book/build_l2book.py`, `outputs/l2book/l2_helpers.py`, `outputs/l2book/l2_figs.py`; `outputs/l3book/build_l3book.py`, `outputs/l3book/l3_helpers.py`, `outputs/l3book/l3_figs.py`. *(The per-chapter `l2_chNN_*.py` / `l3_chNN_*.py` modules are book **content** and were intentionally not copied.)*
- **Purpose:** The reusable **template + toolkit** for an *authored* (hand-written, not faithful-render) interactive math book: a book-style reader shell + an exact-vector SVG figure toolkit + pedagogy helpers. L3 = L2 plus three extra figures.
- **Inputs:** None (no args). `build_lNbook.py` dynamically imports the per-chapter modules (`importlib`, tolerant — a broken chapter is skipped with a printed warning), assembles them against a fixed `OUTLINE`/`TRACK`, and renders. The chapter modules each expose `build(chapter)` and call the helpers/figures; they are where the actual teaching content lives.
- **What each file provides:**
  - `build_lNbook.py` — the HTML template (title page → tappable grouped index → open flowing chapters with prev/next + "↑ Contents", A−/A+ font sizing, night mode, Core/Stretch/Olympiad track badges) and the `render()` driver. Writes `content-books/lN-mathbook/lN-mathbook.html`.
  - `lN_helpers.py` — `esc`/`_safe`, **`fit_svgs`** (grows each SVG's viewBox so no text label clips — only ever enlarges), prose-block builders (`H`, `P`, `kiwi`, `big_q`, `figure`, `example`, `steps`, `tryit`, `practice`, `challenge`, `trap`), plus a few inline figures (`number_line`, `pv_table`, `base_ten`, `place_arrows`).
  - `lN_figs.py` — ~25-function exact-vector SVG figure toolkit: `compare`, `array_dots`, `factor_tree`, `fraction_bar`, `fraction_circle`, `decimal_grid`, `frac_on_line`, `rect_fig`, `area_grid`, `polygon`, `solid`, `cube_net`, `symmetry_fig`, `venn2`, `bar_chart`, `pictograph`, `pie`, `magic_square`, `clock`, `spinner`, `balance`, `pattern_seq` (L3 adds `angle`, `ratio_bar`, `coord_grid`).
- **Outputs:** `content-books/l2-mathbook/l2-mathbook.html` (and L3 equivalent). Prints path + size + chapters-built/total.
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/outputs/l2book && python3 build_l2book.py
  cd ~/Downloads/kiwimath/outputs/l3book && python3 build_l3book.py
  ```
  (each builder imports its sibling `lN_chNN_*.py` modules from the same dir, so run it from there.)
- **Guardrails / gotchas:** Pure standard library (no PDF deps) — figures are generated SVG. The **framework** is reusable; the value is in the toolkit + template + pedagogy scaffold. Authored content must still be brute-force-verified question-by-question (the original chapters each had ~150 Python answer checks) — the framework does not validate math for you.
- **Reuse for a new exam app:** **Template + reader shell + pedagogy helpers (`fit_svgs`, the block builders, the index/nav/night/font shell) are subject-agnostic** and reuse as-is. The **figure toolkit is math-specific** (fraction bars, factor trees, magic squares) — a new subject reuses the SVG-builder *style* but authors its own figure functions. The per-chapter content is, by definition, written fresh for each subject/level.

### `vedantu_build_all.py` *(placeholder, ignore)*
- A leftover copy of `build_all.py` that the read-only mount could not delete; its contents were neutralized to a one-line note. Use `build_all.py`.

---

## `verification/`

> The pre-deploy gate + four smoke suites. **Path caveat:** `pre_deploy_check.py`
> and `smoke_level_v3.py` resolve content relative to the **repo root**
> (`content-live/...`), so run them from `~/Downloads/kiwimath/`; the other three
> smoke tests default to `../content-live/...`, so run them from
> `~/Downloads/kiwimath/backend/`. All four smoke tests build an in-process
> FastAPI `TestClient` with `KIWIMATH_AUTH_DISABLED=1` and exit non-zero on any
> failed assertion.

### `pre_deploy_check.py`
- **Original location:** `backend/pre_deploy_check.py`
- **Purpose:** The content pre-flight gate. Run **before `deploy.sh`** to confirm content is structurally correct.
- **Inputs:** No args. Reads `content-live/content-v2/topic-*/` (the legacy v2 bank) plus the `/v3` banks `content-live/olympiad/L*/` and `content-live/curriculum/*/grade*/questions.json`. Paths are resolved relative to the script (`../content-live`), so run from repo root.
- **Checks:** required fields (`id`, `stem`, `choices`, `correct_answer`, `difficulty_tier`, `difficulty_score`); exactly 4 choices; `correct_answer ∈ {0,1,2,3}`; unique IDs; difficulty within range; SVG references resolve (inline SVG accepted, file refs checked case-insensitively); per-level olympiad/curriculum **bank counts vs expected thresholds** (warns if olympiad < 16,000 or curriculum < 9,000 — update these when counts change).
- **Outputs:** Prints a report (per-topic counts, `/v3` bank totals, visuals). **Exit `1` on any error, `0` (with warnings allowed) otherwise.**
- **How to run:**
  ```bash
  cd ~/Downloads/kiwimath/backend && python3 pre_deploy_check.py
  ```
- **Guardrails / gotchas:** Read-only. The **expected-count thresholds are baked in** and must be bumped after any dedup/import (CLAUDE.md tracks the current totals, e.g. olympiad ~19,642 / curriculum 10,336). It validates the legacy `content-v2` 8-topic structure *and* the `/v3` banks.
- **Reuse for a new exam app:** **Structure/shape checks are subject-agnostic** (required fields, choice count, unique IDs, visual refs resolve, bank-count thresholds). The expected topic list, file names, and count thresholds are app-specific config to re-author.

### `tests/smoke_level_v3.py`
- **Original location:** `backend/tests/smoke_level_v3.py`
- **Purpose:** End-to-end smoke of the `/v3` content API + economy.
- **Inputs / run:** From `~/Downloads/kiwimath/` (defaults `content-live/olympiad` + `content-live/curriculum`); sets `KIWIMATH_AUTH_DISABLED=1`, `sys.path.insert(0,"backend")`.
  ```bash
  cd ~/Downloads/kiwimath && python3 backend/tests/smoke_level_v3.py
  ```
- **Asserts:** 8 olympiad levels (L1 available, L8/IMO not); topics list; **next question served WITHOUT answer leak**; get-question + visual endpoints; empty-level scaffold hidden; 5 curriculum boards; chapters sequenced ascending; **answer/check grades correctly + drives ONE wallet (no disjoint between answer-check wallet, `/me/wallet`, and `/me/progress`)**; idempotency (duplicate POST replays, no double-award); `/v3/stats` matches the bank counts.
- **Gotchas:** The final stats assertion hard-codes the expected totals (`olympiad_total==19642`, `curriculum_total==10336`) — **update after any content change**. Read-only against content (uses in-memory economy state).
- **Reuse:** The *suite shape* (in-process TestClient, no-leak check, single-ledger consistency, idempotency) is fully reusable; the specific endpoints, level taxonomy, and hard-coded counts are app-specific.

### `tests/smoke_adaptive_skill.py`
- **Original location:** `backend/tests/smoke_adaptive_skill.py`
- **Purpose:** Smoke of the adaptive skill-ladder engine (`adaptive_skill.AdaptiveSkillEngine`) + its `/v3` endpoints.
- **Inputs / run:** From `~/Downloads/kiwimath/backend/` (defaults `../content-live/...`).
  ```bash
  cd ~/Downloads/kiwimath/backend && python3 tests/smoke_adaptive_skill.py
  ```
- **Asserts:** ladder built from cluster tags; **skill-question correct → next skill (cluster skipped)**; **skill wrong → drip its cluster questions**; multi-drip then a cluster-correct → next skill; cluster exhausted → next skill anyway; **a fresh engine instance (re-login) resumes the same question — never jumps back**; **no-regress** (re-answering a cleared earlier skill doesn't move position back); full API round-trip (`/next` → `/answer/check` → `/next` + `/adaptive-status`) with no answer leak.
- **Gotchas:** It **searches** `L4` topics for a rich ladder (>5 skills, clusters on skills 0 and 1, a 3+ cluster) rather than assuming the first topic — this was hardened because new single-skill Vedantu topics can sort ahead. Depends on `cluster_concepts.py` having tagged the bank (`skill_seq`/`skill_difficulty`).
- **Reuse:** The adaptive-ladder *behaviour spec* (right→advance, wrong→drip, exhaust→advance, persistence, no-regress) is reusable design; the cluster-tag dependency and level taxonomy are app-specific.

### `tests/smoke_contest_league.py`
- **Original location:** `backend/tests/smoke_contest_league.py`
- **Purpose:** Smoke of the Daily Contest + Weekly League MVP (`contest_service`, `league_service`, `/v3/contest/*` + `/v3/league/*`).
- **Inputs / run:** From `~/Downloads/kiwimath/backend/`; sets `KIWIMATH_CONTEST_ALWAYS_OPEN=1` so the 6 PM IST gate doesn't block the test.
  ```bash
  cd ~/Downloads/kiwimath/backend && python3 tests/smoke_contest_league.py
  ```
- **Asserts:** deterministic 8-question set per (date, level), differs by level, ordered by increasing difficulty; today serves live with **no answer leak**; submit-all-correct → score + LP + economy award; **one attempt** (re-submit replays, no double-award); board ranks by score; league cohort/tier/zones/promote target; practice LP nudges the league; rollover promotes top 7 / relegates bottom 7; result persists across a fresh service instance; **IDOR/auth — a non-dev token gets 403 on another user's contest/league/submit**; the internal rollover endpoint is dev/admin-only (normal user 403).
- **Gotchas:** Requires `KIWIMATH_CONTEST_ALWAYS_OPEN=1` to run off-hours. Uses in-memory league/contest stores.
- **Reuse:** The competitive-integrity assertion set (deterministic set, no leak, one-attempt, rank-by-score, rollover, IDOR-closed) is reusable design; the scoring formula, tiers, and level taxonomy are app-specific.

### `tests/smoke_store.py`
- **Original location:** `backend/tests/smoke_store.py`
- **Purpose:** Smoke of the Store MVP (`store_service`, `api/store`, `economy_service`).
- **Inputs / run:** From `~/Downloads/kiwimath/backend/`; also sets `KIWIMATH_BOOKS_DIR=../content-books` so real book bytes are served.
  ```bash
  cd ~/Downloads/kiwimath/backend && python3 tests/smoke_store.py
  ```
- **Asserts:** catalog (26 books — Euclid's Garden + 16 pillar + 2 workbooks + L2/L3 math books + Number Sense; all free; no coming-soon; the 4 IOQM pillars are `html`); **nothing auto-owned**; **purchase-before-download** (content 403 before claim, 200 after); manifest/bytes for a real >5 MB HTML book carrying the interactive shell; all 4 pillars purchasable + downloadable (>1 MB each); wallet grant + insufficient-spend rejection; unknown book → 404; **auth — a non-dev user can't read another's wallet/library or grant (403)**.
- **Gotchas:** The catalog-count assertion hard-codes `== 26` — **update when books are added/removed**. Needs `KIWIMATH_BOOKS_DIR` pointing at `content-books/` so the byte-size assertions pass.
- **Reuse:** The store-integrity assertion set (no auto-own, purchase-gates-content, entitlement-checked bytes, auth-isolated wallet) is reusable design; the catalog contents/counts are app-specific.

---

## How these fit the workflow

These scripts implement one repeatable loop, run whenever content is added or
defects are found:

**ingest → cluster → scan (A–N) → fix → re-scan → pre_deploy + smoke → deploy**

1. **Ingest** new source material into the bank with `ingestion/ingest_quiz.py`
   (faithful image + key-resolved answer; idempotent), or author it with the
   `book_build/` builders / authored-book framework.
2. **Cluster** with `content_qa/cluster_concepts.py` so every question carries a
   `skill_id` + adaptive-ladder tags (idempotent; `integrity_bad` must be 0).
3. **Scan** the whole bank with `content_qa/content_qa_scan.py` (read-only, A–N).
4. **Fix** every flagged class with the matching `content_qa/` fixer
   (`fix_pattern_visuals` H, `clear_mismatched_visuals` / `fix_l1_decorative_logic` I,
   `remove_l1_dups_unanswerable` L+N, `remove_level_defects` for the per-level
   dedup loop) — each backs up + manifests + touches only the intended fields.
   When a brand-new defect appears, **add a detector to the scanner first**.
5. **Re-scan** and repeat 3–5 until `content_qa_scan.py` reports **TOTAL = 0**.
   (Removals cascade — re-run `cluster_concepts.py` and update the expected
   counts in `counts_report.json` + the pre-deploy/smoke thresholds.)
6. **Verify** with `verification/pre_deploy_check.py` (green) + the four smoke
   suites (`smoke_level_v3`, `smoke_adaptive_skill`, `smoke_contest_league`,
   `smoke_store`).
7. **Deploy** with `backend/deploy.sh` (content + books are baked into the image;
   most content-only changes ship without an APK rebuild).
