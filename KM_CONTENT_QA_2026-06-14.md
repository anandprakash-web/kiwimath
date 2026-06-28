# Kiwimath — Content QA pass (2026-06-14)

Triggered by two real bugs spotted in the running app (question **KM-L1-NT-1164**,
"Number Hops"): a nonsense filler line in the stem, and a grey placeholder box
where no image was needed. Both were scanned for and fixed across the **entire
served bank** (`content-live/olympiad/L1–L8` + `content-live/curriculum/*`), not
just the samples.

## What was wrong

1. **Decorative filler prefixes.** Story-rewrite intros were prepended to clean
   math questions — e.g. *"A crystal on the cave wall glows near Chikoo. Skip
   count by 50s…"*. The leading sentence carries no math and only confuses.
2. **Fake placeholder images.** ~2,400 questions had a `visual_svg` that was just
   a grey rounded box containing a truncated description (`#F8F9FA` rect +
   `#6C757D` text) — not a real diagram. The app rendered it as an empty grey box
   with clipped text, on questions that need no image at all.

## What was done

| Fix | Count |
|---|---|
| Stems with decorative filler stripped (5 passes: name-wrappers, no-name scene templates, statement-style logic, colon/dash intros like "Help Vanya calculate:", old character names) | **~6,937** |
| Placeholder `visual_svg` removed (+ `visual_context`/`visual_alt` cleared) | **2,461** |
| Exact-duplicate questions removed (exposed once filler was gone) | **1,136** |
| Empty/unanswerable stems removed (". . ?") | **4** |
| Real diagrams (lines/circles/paths) **kept untouched** | **6,108** |

**Detection logic (conservative by design):**
- *Filler* — only a **leading** sentence that has no digit, no number-word, no
  "?", and contains a character name or scene word is removed, and only when the
  remaining text still holds the actual question. Real leads ("A box had 12
  cubes…", "Which is the largest number?") are never touched.
- *Placeholder* — an SVG with no real primitives (no `<line>/<circle>/<path>/…`),
  just one box + a label. Of the 2,461, only 8 even referenced a figure, and all
  8 carry their data in the text (e.g. "a smiley face = 5 students, 4 faces
  shown"), so none actually required an image.
- *Duplicates* — only **exact** matches (identical normalised stem + choices +
  answer) were removed; one copy of each kept. Near-duplicates were left alone.

## Integrity — verified, zero drift

Every kept question was hash-checked field-by-field against a pre-edit backup
(`qa-reports/backup-2026-06-14/`):

- **answers / choices / correct_value / hints / diagnostics / IRT / difficulty —
  0 mismatches.** Only `stem` and the fake `visual_svg` fields changed.
- 0 phantom IDs (nothing invented).
- Backend smoke test **17/17 PASS** (loads new banks, one economy, idempotency).
- Removed duplicates logged to `qa-reports/removed_dups_2026-06-14.json`
  (recoverable).

## New totals

| Bank | Before | After |
|---|---|---|
| Olympiad (L1–L8) | 18,099 | **16,963** (L1 8,766 · L2 5,374 · L3 2,823) |
| Curriculum (school) | 10,340 | **10,336** |
| **Total served** | 28,439 | **27,299** |

### Applied to the LIVE banks (verified, not a stale copy)
The fixes were run on `content-live/olympiad/` + `content-live/curriculum/` — the
exact banks the new app reads via `/v3`. Proof: after the pass these show **0
placeholders / 0 filler / 0 dups**, while the superseded `content-v2/` (served
only on the old `/v2`,`/v4` endpoints the new app never calls) still shows 1,598
placeholders + 7,012 filler — confirming the right copy was edited.

## "Where do images get added?" — the SVG mechanism (already in place)

Each question's image lives **inline** in its JSON `visual_svg` field (raw SVG
markup). To add or replace an image for a question you set that field; nothing
else is needed.

- Backend serves it two ways: inline in the question payload, and via
  `GET /v3/olympiad/question/{id}/visual`.
- The app renders it with `SvgPicture.string(q['visual_svg'])`.
- A question is "image-required" only if it can't be answered from text. The
  6,108 real diagrams (number lines, shapes, charts, symmetry figures) are
  genuine and were kept; the fakes were the only ones removed.

## Checked but deliberately NOT changed

- **55 "…is / …represents" stems** look truncated but are valid sentence-
  completion MCQs (e.g. "The perimeter of a square with side 15 cm is" → "60 cm").
  Left as-is.
- Minor grammar like "1 strips / 1 gummies" (singular-plural) is pre-existing and
  cosmetic — not in scope here; can be a follow-up polish.

## To go live

Content is **baked into the backend image**, not Firebase — so the cleaned bank
ships on the next deploy:
```
cd ~/Downloads/kiwimath/backend && python3 pre_deploy_check.py && ./deploy.sh
```
No app rebuild needed for this fix (the stems/images come from the API).
