# 02 · The Library System

The Library is the second content surface: a shelf of **books** the learner buys (free for now), downloads, and reads offline in an in-app reader. This file covers the three kinds of book, how each is built, the store/economy flow, and the reader — plus the hard lessons that shaped the reader.

---

## 1. The book contract (the whole interface)

> **A book = one self-contained HTML file in `content-books/{id}/` + one catalog row. That's it.** Add those two things, run `./deploy.sh`, and the book appears in the app Library. No app rebuild needed — the reader and store UI are generic.

- **The file:** `content-books/{id}/{id}.html` — fully self-contained (images inline as base64, JS inline). The reader downloads one blob and runs it.
- **The catalog row:** in `store_service.py`, append to `_BOOK_FILES` (where the bytes are) + `_CATALOG` (id, title, author, subject, levels, gradeBand, byteSize, pricing). Bump the count assertion in `smoke_store.py`.

That decoupling — books are data, the reader is generic code — is why ~43 books exist on one reader. Why HTML and not EPUB/PDF: see §5.

---

## 2. Three kinds of book (pick by source + goal)

| Kind | When to use | Build | Math notation & figures |
|------|-------------|-------|-------------------------|
| **Faithful-render** | You have a source PDF (past papers, assignments) and must NOT alter the questions | Render each PDF page → WebP image → wrap in an interactive HTML shell | Pixel-perfect (it's the real page) — sidesteps all text-mangling |
| **Authored** | You want an original *teaching* book written from scratch | Python builder generates HTML + exact vector SVG figures | Authored cleanly; figures drawn as exact vectors |
| **Interactive** | You want the learner to *answer inside* the book (tap / type & check) | Faithful slide image + replace the answer area with real HTML controls | Faithful visual kept; controls added |

### 2a. Faithful-render books (the workhorse)
Script: `scripts/book_build/build_book.py` (and `build_all.py` to batch). For each topic PDF: PyMuPDF renders pages → WebP (≈1.7–2.0×, base64) → a self-contained HTML shell with a branded cover, a tappable contents nav, the problem pages, and `<details>` reveals for **video solutions** (YouTube links extracted from the PDF) and **answers & worked solutions**. Night mode, lazy-loaded images.

**Why render instead of re-type:** the source math (exponents, √, geometry figures) survives perfectly because it's the real page. Re-typing would corrupt it (the text-mangling problem from `01` §4). This is the safe default for any notation-heavy or figure-heavy source.

Built this way: the upper-tier pillar books (IOQM/RMO/INMO × 7 strands), the G3-4 and G5-6 grade workbooks, the IOQM "Four Pillars" books. `build_workbook.py` is the flat-folder variant for session courses (no video tab).

### 2b. Authored books (the premium teaching layer)
The L2 book *"Kiwi's Grand Math Adventure"* (Grades 3-4) and L3 *"Kiwi's Math Expedition"* (Grades 5-6) — written from scratch like a maths expert would, Socratic + Bloom's-taxonomy pedagogy, exact vector figures, our own taxonomy names, bridging the sharp level-to-level jump, with Kangaroo-style problems and (L3) Vedic-maths speed tricks.

**The build framework** (reusable — in `scripts/book_build/`):
- `build_lNbook.py` — the Euclid-style template: title page → tappable index grouped by Part → flowing `<section>` chapters with prev/next + "↑ Contents" + A−/A+ font sizing + night mode. **Pure-anchor navigation (works without JS).**
- `lN_helpers.py` — prose helpers (H, P, kiwi mascot, big-question hook, figure, example, steps, try-it, Bloom's-ladder practice, challenge, ⚠️ mistake-trap box) + the smart-escape `_safe()` (preserves real HTML entities) + `fit_svgs()` (build-time pass that grows each SVG viewBox to contain its labels — fixes clipping universally).
- `lN_figs.py` — a ~25-function exact-vector SVG toolkit (number lines, place-value, fraction bars/circles, polygons, 3D solids, symmetry, Venn, charts, clocks, angles, ratio bars, coordinate grids…).
- One module per chapter, `lN_chNN_*.py`, exposing `build(chapter)`.

**How they were written:** chapter 1 by hand as the gold standard, chapters 2–23 by **parallel subagents** — each one brute-force-verifies every answer in Python (~150 checks/agent, 0 wrong) and render-tests its figures via cairosvg — with one central QA pass. This fan-out-then-verify pattern is the way to author at volume safely (see `06`).

### 2c. Interactive books (answer-inside)
The Number Sense book (K-2, 13 worksheets, 784 slides). Pipeline in `content-books/_pipeline/`: `render_cache.py` (renders all slides to a WebP cache — **run single-process or it OOMs**) + `assemble_ns.py` (config-driven: an `INTERACTIVE` dict keys each slide as `mcq` / `fill` / `one` / `multi`, crops the faithful visual to drop the printed answer, and draws real tap/type/check controls). **The interactivity runs in the reader's WebView with no app change** — the book's own JS does it. This book is ONGOING (4/13 worksheets keyed); full method in `LIBRARY_AND_CONTENT_HANDOVER.md`.

**Interactive-book rule:** *better faithful than wrong.* If a slide can't be keyed with certainty (drag manipulatives, ambiguous counts), leave it as a faithful image rather than risk telling a correct kid they're wrong.

---

## 3. The store + economy flow (purchase → download → read)

All under `/v3`, server-enforced:

```
catalog  →  claim (purchase)  →  download bytes (entitlement-gated)  →  read offline
```
- `api/store.py`: `store/catalog`, `store/entitlements`, `store/claim`, and `store/content/{id}/manifest|bytes|cover`. **Content is entitlement-gated: 403 until claimed, 200 after** — that's "purchase before download," enforced server-side.
- `economy_service.py`: one wallet (coins/gems/XP/streak), idempotent `spend`/`grant`. Books priced `_FREE` (claimable but not auto-owned) for now; swap to `{"coins": N}` to charge. The earn-or-buy dual path is already built.
- `deploy.sh` bakes `content-books/` into the image and sets `KIWIMATH_BOOKS_DIR`.

**Economy principle:** one shared ledger across practice, quiz, contest, and store — "no disjoint" (wallet, progress, profile always agree). And **money never buys rank** — coins/gems unlock content and cosmetics, never leaderboard position.

---

## 4. The reader (app side)

- `app/lib/v3/books_browse.dart` — the Library UI (our own code): Store + Downloads tabs, Level/Subject filter, hand-painted `BookCoverArt` (per-subject vector motif, zero network/asset dependency), the Get→Download→Read flow, offline download to `appDocs/kiwi_books/{id}.html`.
- `app/lib/v3/html_book_reader.dart` — the reader for `format:html` books: loads the HTML in `flutter_inappwebview` (file://, fully offline once downloaded), runs the book's own JS (so interactive slides work), gives font size / light-sepia-dark themes / scroll-or-paged modes / immersive chrome / scroll-resume. External links open in the system browser; `#anchor` links smooth-scroll in-page.
- `book_reader.dart` — a fallback EPUB/PDF reader (epub.js). Not used by the HTML books.

**What a book's HTML must do to behave in the reader:** CSS variables + a `body.night` rule (dark mode), rem/em sizing (font scaling), `<a href="#id">` + matching `id` for in-page nav (the reader intercepts and smooth-scrolls), one self-contained file with inline base64 images (aim < ~30 MB; base64 inflates ~1.33×).

---

## 5. Why the reader is our own HTML WebView (the saga, so you don't repeat it)

The reader went through several iterations — this is the compressed lesson:

1. Started by integrating **KiwiReader** (a third-party Flutter reader package) — worked, but every reader UX change meant fighting an external API.
2. Tried **EPUB** (flutter_epub_viewer / epub.js). Hit a hard engine limit: its paging manager enum only exposed the *wrong* mode for paginated layout, so pages wouldn't flip smoothly; scroll mode janked; `onRelocated` setState storms caused flicker. These were *engine* limits, not our bugs.
3. Concluded: **render the book's own self-contained HTML in a WebView we fully control.** Native-smooth scroll, our chrome, the book's JS runs (enabling interactivity), and we own every pixel.

**The transferable lesson:** for a *study* reader (textbook, figures, non-linear, interactive) — not a novel reader — owning a WebView on self-contained HTML beats adopting a general EPUB engine. You trade "free" pagination for total control and zero engine surprises. Also learned: stage big files to a temp file and load `file://` (don't push a 12 MB book through the platform channel as one string); cache the WebView widget and drive progress via a `ValueNotifier` (not setState) to kill flicker.

---

## 6. Doing a Library task (the checklist)

1. **Pick the book kind** (§2) by your source and goal.
2. **Build** with the matching script in `scripts/book_build/` (faithful = `build_book.py`; authored = the `build_lNbook.py` framework; interactive = the `_pipeline/` scripts). Edit the hard-coded source/output paths at the top for your environment.
3. **Render-check** the output HTML in a browser (figures, math, nav, dark mode).
4. **Wire the store:** one row in `_BOOK_FILES` + `_CATALOG`, bump `smoke_store.py`'s count.
5. **Verify** `smoke_store.py` green.
6. **Deploy** `./deploy.sh` (no app rebuild for a new book).
7. **Rights check:** only ship books you can legally distribute — third-party reference texts usually aren't redistributable; your own + licensed material is. (This is a real constraint, not a formality.)
