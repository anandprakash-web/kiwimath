# Archive Index (created 2026-06-12)

Everything in this folder is NOT served and NOT part of active QA. The single canonical question source is **`content-live/`** at the repo root (content-v2 = olympiad/curriculum bank, content-v4 = adaptive bank; zero ID overlap; ~29,143 unique questions). Do all question QA/corrections there only.

| Item | What it is | Why archived |
|---|---|---|
| `content/content-production/` | 29,460-question "schema 5.0" merged set (May 17) | Was never wired to the backend; overlaps content-live by ~97%. Kept as the candidate for a future single-bank migration. QA'd + fixed 2026-06-12. |
| `content/benjamin-olympiad-QUARANTINED/` | 809 Benjamin olympiad questions (379 originals + 430 variants) | **Answer keys are placeholders (75% keyed to first choice). Must be re-keyed before any use.** See WHY_QUARANTINED.md. |
| `root-files/` | Stray working JSONs (new_arithmetic/new_counting question drafts, old audit outputs) | One-shot artifacts; the ~184 unique draft questions not in content-live can be merged later if wanted. |
| `docs/` | Old planning docs, spreadsheets, summaries (April–May) | Superseded by CLAUDE.md + the three 2026-06-12 reports at root. |
| `tools/` | One-shot generator/audit scripts, old review tool HTML | Already executed; kept for reference. `tools/old-scripts/` were the v4 content generators. |
| `_Schema/` | Schema v2 design + sample question JSONs | Design history. |
| `gemini-reports/` | Old Gemini audit output | Superseded by qa-reports/. |
| `puzzle-svgs/` | Puzzle SVG drafts | Live puzzles are served from backend/static/puzzles/. |

Note: the old `_archive/` and `archived_duplicates/` folders (pre-June) were deleted from disk on 2026-06-12 but remain recoverable from git history.
