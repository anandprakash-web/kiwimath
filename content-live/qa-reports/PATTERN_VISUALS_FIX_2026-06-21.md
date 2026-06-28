# Pattern questions with missing visuals — root cause & fix (2026-06-21)

## The bug (founder screenshot: "Pattern Play → What colour bead comes next?")
A pattern MCQ rendered with **no image** and four colour options, so it was
**unanswerable** — nothing shows the pattern.

## Why (root cause)
The served `stem` had been **shortened to a bare prompt** ("What colour bead
comes next?") by an earlier content pass, on the assumption the pattern would
live in a visual. But `visual_svg` was `None`/empty — the placeholder SVG had
been stripped (or never inlined). So the pattern data was simply **gone**.

Evidence: `original_stem` on the same question still read
*"…beads: Red, Blue, Red, Blue, Red, Blue, ___. What colour bead comes next?"* —
the pattern was in the original text and got dropped from both stem and visual.

## The fix
Rebuild a **valid pattern visual** (or restore the sequence) so the cycle yields
the keyed `correct_answer`. Source of the pattern, in priority order:
1. **exact sequence from `original_stem`** when present (and its cycle's next == answer);
2. else **inferred 2‑item repeat `[answer, other]`**, where `other` comes from the
   diagnostics (e.g. *"which colour follows Yellow"*) or a distractor — the
   sequence ends on `other`, so the next item is always the keyed answer.

Generated SVGs: coloured **beads on a string**, outlined **shapes**, or
size‑graded **circles**, each ending in a dashed "**?**" bead/box.

Script (reusable, idempotent, backs up before writing):
`qa-reports/fix_pattern_visuals.py --kind {color|shape|size} [--apply]`

## Result — 69 questions repaired, 100% answer‑consistent
| kind | fixed | how |
|---|---|---|
| colour beads | 22 | bead SVG (7 from original_stem incl. AABB patterns, 15 inferred) |
| shapes | 37 | shape SVG (circle/square/triangle/star/heart/diamond/rectangle/…) |
| size | 9 | size‑graded circles |
| number (stem restore) | 1 | `KM-L3-ALG-0587` → "2,2,4,6,10,… → 16" |

- Verified: for every fixed item the pattern's **next element == `correct_answer`** (69/69).
- Integrity vs backup: **only `visual_svg` / `visual_alt` / `stem` changed** — answers, choices, hints, IRT, tags untouched.
- All SVGs valid (`<svg…`); JSON valid; files re‑indented to repo style; content QA scanner = **0 flags**.
- Backup: `qa-reports/backup-pattern-visuals-2026-06-21/`.

## Flagged — 14 NOT auto‑fixed (data unrecoverable; would require fabrication)
Left as‑is on purpose (better faithful than a guessed pattern). Need the original
patterns from source, or a decision to delete/replace:
- **number, no recoverable sequence (2):** `KM-L3-ALG-0499` (ans 28), `KM-L1-COM-0711` (ans 11) — `original_stem` is empty or pure filler.
- **mixed‑attribute choices (10):** `A1-PAT-0557/0576/0577/0578/0580/0581/0583/0590/0591/0594` — options jumble shape/colour/direction/size, so even the *pattern type* is ambiguous.
- **symbol choices (2):** `KM-L1-GEO-0136` (△☆□○), `A2-PAT-0337` (🟢🔴🔵🟡) — cleanly fixable later by adding a unicode/emoji→name map to the script.

## Prevention
Added detector **`H · pattern needs a visual but visual_svg empty`** to
`qa-reports/content_qa_scan.py` so any future stripped‑pattern question is caught.
