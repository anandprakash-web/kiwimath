# Quarantine

Content moved out of the live content tree because it is not safe to serve.

## benjamin-olympiad/ (moved 2026-06-12, from content-v2/benjamin-olympiad/)

**Why quarantined:**

- **Originals (379 questions, `grade6/benjamin_g6_questions.json`):** 283/379 (75%) have
  `correct_answer = 0`, i.e. keyed to the *first choice as a placeholder* during PDF
  extraction. Manual inspection confirmed placeholder keys (e.g. BEN-2009-Q06: "How many
  faces has the object shown? (Prism with a hole)" keyed to "3" — a prism with a hole has
  8+ faces, and there is no visual attached). Serving these would mark children wrong on
  correct answers ~75% of the time.
- **Variants (430 questions, `grade6/benjamin_variants.json`):** ALL are unverified.
  Choices were inherited from parent questions without recomputation
  (`needs_answer_recalc` / missing `answer_verified`). Several are provably broken
  (BEN-2010-Q06-SU2, BEN-2013-Q07-SD2, BEN-2019-Q13-SIM1, BEN-2017-Q12-SU2 — internally
  inconsistent premises after numeric substitution).
- **OCR damage:** dozens of stems (esp. 2015 papers) contain OCR-doubled letters
  ("duckks", "thaat", "wwith", "minimuum"), and ~175 questions reference visuals that
  were never extracted from the PDFs.

**Safety check performed:** `backend/app/services/content_store_v2.py` iterates
directories under the content root (`load_folder` → `root.iterdir()`) and loads
curriculum folders only via `_load_curriculum_folder`, which returns 0 when the folder
does not exist. `benjamin-olympiad` is not referenced by name anywhere in the loader,
so its absence cannot crash the backend — it simply won't be loaded.
The QA scanner (`qa-reports/v2_qa.py`) was updated to skip the Benjamin files when the
directory is absent.

**What re-enabling requires (per question):**

1. **Answer keys:** re-extract the official answer keys from the 17 Benjamin PDFs
   (2009–2025) — answer tables are usually on the last page of each paper — OR solve
   each question by hand and re-key. `correct_answer = 0` must never be trusted.
2. **Variants:** recompute choices AND keys from each variant's actual numbers
   (do not inherit from the parent). Delete the 4 provably-broken variants listed above
   or regenerate them.
3. **OCR cleanup:** fix doubled-letter stems against the source PDFs.
4. **Visuals:** generate SVGs for the ~175 visual-dependent questions, or exclude them.
5. Re-run `python3 qa-reports/v2_qa.py` with the folder restored and confirm 0 criticals
   before moving the folder back into `content-v2/`.
