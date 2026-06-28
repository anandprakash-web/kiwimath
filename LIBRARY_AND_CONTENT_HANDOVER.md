# Kiwimath — Library & Content Handover

**Purpose:** lets a *second cowork space* continue the **content / Library** work
(finishing the Number Sense interactive book, building more books) in parallel,
while the main space focuses on the **app**. Read this top-to-bottom once; then
live in §4 (the ongoing job) and §7 (don't-collide rules).

Last updated: 2026-06-21 · Author handoff: Number Sense 4/13 worksheets done.

---

## 1. TL;DR

The **Library** is live in the app: **6 books**, all free, with a
*purchase → download → read-offline* flow. Two content pipelines produce books,
both ending in a **single self-contained HTML file** per book that the app's
WebView reader renders:

| Pipeline | Output | Status |
|---|---|---|
| **A. Number Sense** (interactive K-2 workbook) | `content-books/number-sense/number-sense.html` | **4/13 worksheets interactive · ONGOING — this is the main job** |
| **B. IOQM pillars** (faithful + reveal) | `content-books/{geometry,algebra,combinatorics,numbertheory}-ioqm/…html` | done (4 books) |
| (older) Euclid's Garden | `content-books/euclids-garden/EuclidsGarden_Mobile.html` | done |

**A book = one HTML file in `content-books/{id}/` + a catalog row.** That's the
whole contract. Add those two things, run `./deploy.sh`, and the book appears in
the app Library. No app rebuild needed for a new book (the reader + UI are generic).

---

## 2. The Library framework (how books reach the app)

### 2.1 Backend (FastAPI) — `backend/app/`
- **`services/store_service.py`** — the catalog. Two structures you edit to add a book:
  - `_BOOK_FILES[id] = {"file": "<id>/<file>.html", "format": "html"}` — where the bytes are.
  - `_CATALOG` — append a dict: `id,title,author,subtitle,format:"html",contentVersion,byteSize,subject,levels:[…],gradeBand,"pricing":_FREE`.
  - Model: `_FREE = {"isFree": True}` → book is free but **not auto-owned**; the user must *claim* it before downloading. (Phase 2: swap `_FREE` for `{"coins":N}` to charge.)
- **`api/store.py`** — endpoints (all under `/v3`): `store/catalog`, `store/entitlements`, `store/claim`, `economy/wallet|spend|grant`, and **content** `store/content/{id}/manifest|bytes|cover`. Content is **entitlement-gated**: 403 until the user has claimed the book, 200 after → that's "purchase before download", enforced server-side.
- **`deploy.sh`** bakes `content-books/` into the image and sets `KIWIMATH_BOOKS_DIR`. So shipping a book = drop the file in `content-books/` + catalog row + `./deploy.sh`.
- **`tests/smoke_store.py`** — asserts catalog length + that content is gated. **Bump the count when you add a book.**

### 2.2 App (Flutter) — `app/lib/v3/`
- **`books_browse.dart`** — the Library UI (our own code): `BooksBrowseBody` (Store + Downloads tabs, Level/Subject filter), `BooksService` (catalog/claim/wallet), `BookDownloads` (saves bytes to `appDocs/kiwi_books/{id}.html`, offline), hand-painted `BookCoverArt` (by `subject`). Flow: **Get·Free** (claim) → **Download** → **Read**. Downloaded books appear in the **Downloads** tab and open offline.
- **`html_book_reader.dart`** — the reader for `format:"html"` books. Loads the HTML in `flutter_inappwebview` (file://, fully offline once downloaded). Gives font size, light/sepia/dark themes, scroll/paged modes, immersive chrome, scroll-resume. **Runs the book's own JS** → that's why our interactive slides work with no app changes. External links (e.g. YouTube) open in the system browser; `#anchor` links smooth-scroll in-page.
- **`book_reader.dart`** — fallback EPUB/PDF reader (epub.js). Not used by the HTML books.
- Routing: `books_browse._open()` sends `format=='html'` → `HtmlBookReader`, else `BookReaderScreen`.

### 2.3 Cover art
The app paints covers in Dart by **`subject`** (`_paletteFor` + `_CoverPainter` in `books_browse.dart`): Geometry, Algebra, Number Theory, Combinatorics, Study Skills, default. New subjects fall back to the default painter — add a case if you want a bespoke cover.

---

## 3. What the reader gives the book (so you can design HTML)
The book is just an HTML file. To look/behave right in the reader:
- Use CSS variables and a `body.night` rule for **dark mode** (the reader toggles `body.classList`), and rem/em sizing so **font scaling** works (reader scales `<html>` font-size).
- In-page nav: `<a href="#id">` + a matching `id` → the reader intercepts and smooth-scrolls (don't rely on default anchor nav; it reloads the file).
- Keep it **one self-contained file** (inline images as base64) — the reader downloads one blob. Watch total size: base64 inflates bytes ~1.33×; aim < ~30 MB so it opens fast on low-end phones.
- JS works (tap/type/check, IntersectionObserver lazy images, etc.).

---

## 4. ⭐ ONGOING JOB — Number Sense interactive workbook

**Goal (founder):** one book "Number Sense" from all **13 worksheet PDFs (784 slides)**; make **every question slide interactive** (tap the answer / type & check). Work **batch = 1 PDF**, QA each, then next.

### 4.1 Source
- Founder's upload: `VEL Wavebook PDFs.zip` → **`Number Sense and Operations/`** = 13 PDFs (594 MB). *(Re-upload this zip in the new cowork space; it's too big for the repo.)*
- Ignore the stray `Angle Sum Properties of Triangle.pdf` (not number-sense).

### 4.2 Pipeline (scripts in `content-books/_pipeline/`)
1. **`render_cache.py`** — renders all 784 slides → webp cache (1.3×). ⚠️ **RUN SINGLE-PROCESS** (duplicate/parallel runs caused memory hangs & OOM-137). ~3 min. Idempotent (skips cached). Defines the **chapter order + titles** (`CHAPTERS`).
2. **`assemble_ns.py`** — builds the book HTML from the cache + the **`INTERACTIVE` config**. Faithful slides are downscaled 0.82× + q72 (method=4) at assembly to keep the file ~26 MB. ~40 s. Copies the result into `content-books/number-sense/`.
3. ⚠️ **Edit the 3 absolute paths at the top of each script** (`SRC`, `CACHE`, `REPO`) for the new environment.

### 4.3 The `INTERACTIVE` config (the heart of the work)
`assemble_ns.py` has `INTERACTIVE = { (chapter_idx, slide_1based): {...}, … }`. Chapter index = position in `CHAPTERS` (0-based; Addition = 6, Subtraction = 7, …). Any slide **not** in the dict renders as a faithful image. Five block types:

| `t` | meaning | config keys | rendering |
|---|---|---|---|
| `mcq` | tap the right option | `crop:(x0,y0,x1,y1)`, `opts:[…]` (ints **or** strings like `"3+2=5"`), `ans:<value>`, optional `label` | cropped visual + colored tap pills; locks on correct |
| `fill` | a **+** b = c, three inputs | `crop`, `abc:(a,b,c)` | cropped visual + 3 boxes + Check |
| `fill_sub` | a **−** b = c (e.g. pattern "type missing sentence") | `abc:(a,b,c)` | **full** slide + 3 boxes + Check |
| `one` | single numeric answer | `ans:N` | **full** slide + one box + Check |
| `multi` | tap **all** correct (e.g. "all pairs that add to 9") | `crop`, `opts:[…]`, `correct:[…]` | cropped banner + pills, per-tap feedback |

**Crop tips:** `mcq`/`multi`/`fill` crop the visual to drop the printed answer area, then draw our controls. Common crops: bottom-option MCQ `(0,0,768,538)`; fill-3-box `(0,0,768,352)`; "How do you make N?" banner `(0,0,768,186)`; pick-drop result `(0,0,768,452)`. Slides are 768×576. `one`/`fill_sub` use the **whole** slide (no crop) + controls below.

### 4.4 How to key a worksheet (the method)
1. `pdftotext -f N -l N "<pdf>" -` per slide → find question slides + read **text-derivable** answers (word problems, number sentences, options).
2. For **counts / number lines / pictures**, render a montage and *look*:
   ```python
   import fitz; from PIL import Image, ImageDraw
   d=fitz.open(pdf)  # render slides at ~1.1–1.5×, paste into a grid, label each "slide N"
   ```
   Then read the answer off the image.
3. Add `(chapter_idx, slide): {...}` rows to `INTERACTIVE`.
4. **QA the PDF:** every keyed answer must be arithmetically self-consistent (e.g. `one` on "6−1=" must be 5). Then re-run `assemble_ns.py`.
5. ⚠️ **Better faithful than wrong:** if a slide can't be read reliably (drag manipulatives, ambiguous counts, "which picture" matches), LEAVE IT OUT of the config (stays a faithful image) and note it in the trailing comment. Founder spot-checks; a wrong "❌" on a correct kid answer is the worst outcome.

### 4.5 Status — done vs remaining
**DONE (4 worksheets, 83 interactive slides):**
- `c06` Addition & Forward Seq — 30 · `c07` Subtraction & Backward Seq — 30 · `c08` Challenges A&S ≤10 — 14 · `c09` Addition Facts ≤20 — 9.
- See the `INTERACTIVE` dict + its trailing `# faithful (hard): …` comments for exactly what was keyed vs deferred.

**REMAINING (9 worksheets — pick these up):**
`c00` Counting & Number Recognition · `c01` Number Comparison (1–10) · `c02` Number Comparison & Sequencing (1–20) · `c03` Skip Counting ≤20 · `c04` Group & Count (Bundling 10) · `c05` Place Value (O–T) · `c10` Add & Subtract ≤20 · `c11` Challenges Add ≤20 · `c12` Challenges Sub ≤20.
*(Tip: `c10`/`c11`/`c12` are number-sentence heavy → mostly text-derivable, fast. `c00`–`c05` have more counting/comparison → more montage-reading. Comparison worksheets likely need a new `>` / `<` / `=` tap type — add it next to `multi`.)*

### 4.6 Standalone demo
`content-books/_pipeline/addition_interactive_demo.html` — the original 6-slide proof (open in any browser). Good reference for the look/feel.

---

## 5. Content pipeline B — IOQM pillar books (`build_all.py`)
Faithful page renders (WebP 1.7×, questions never re-typed) + an interactive **shell** (contents, tap-to-reveal **Video solutions** = YouTube links, tap-to-reveal **Answers & worked solutions**). One script builds all four pillars from `Downloads/IOQM 2026/` (17 MB). Re-run to rebuild; same store-wiring contract (§2.1). Cover figures are exact SVG configs (e.g. circumcircle+incircle).

---

## 6. Deploy & QA
```
cd ~/Downloads/kiwimath/backend && ./deploy.sh        # ships content-books/ + catalog
cd ~/Downloads/kiwimath/app && flutter pub get && flutter build apk --release -t lib/main_v3.dart   # only if app code changed
```
- A **new/updated book** = backend `./deploy.sh` only (no APK needed; reader is generic).
- After editing the catalog, run `backend/tests/smoke_store.py` (set `KIWIMATH_AUTH_DISABLED=1`, `KIWIMATH_BOOKS_DIR=../content-books`, the two content dirs) — it must stay green, with the right catalog count.
- Per-worksheet QA = arithmetic self-consistency of keyed answers + founder spot-check of the counts.

---

## 7. ⚠️ Parallel-work rules (avoid collisions with the app space)

| Area | Owned by | Notes |
|---|---|---|
| `content-books/**` (book HTML, `_pipeline/`) | **Content space (you)** | Free to create/modify. |
| `store_service.py` → `_CATALOG` list + `_BOOK_FILES` dict **only** | **Content space (append rows)** | The single shared file. Only touch those two structures; **append**, don't reorder, to keep diffs clean. |
| `smoke_store.py` catalog-count assert | Content space | bump when you add a book |
| Everything else in `store_service.py`, `api/store.py`, `economy_service.py` | **App space** | store/economy logic, gating, auth |
| `books_browse.dart`, `html_book_reader.dart`, `book_reader.dart`, reader/UI | **App space** | reader & store UI |
| `deploy.sh`, app shell, main_v3 | **App space** | |

**Rule of thumb:** the content space produces **files in `content-books/` + catalog rows**; the app space owns **how books are rendered, sold, and read**. The only file both touch is `store_service.py`, and only its catalog/`_BOOK_FILES` rows — coordinate there (or, to fully decouple later, lift the catalog into a JSON the content space owns).

---

## 8. File inventory
- **Pipeline (staged in repo):** `content-books/_pipeline/{render_cache.py, assemble_ns.py, build_all.py, addition_interactive_demo.html}`
- **Books (served):** `content-books/{number-sense, geometry-ioqm, algebra-ioqm, combinatorics-ioqm, numbertheory-ioqm, euclids-garden}/…`
- **Sources (NOT in repo — re-provide):** Number Sense = `VEL Wavebook PDFs.zip` (594 MB); IOQM = `Downloads/IOQM 2026/` (17 MB).
- **Regenerable:** the 784-slide webp cache (run `render_cache.py`).
- **Store wiring:** `backend/app/services/store_service.py`, `backend/app/api/store.py`, `backend/tests/smoke_store.py`.
- **App:** `app/lib/v3/books_browse.dart`, `app/lib/v3/html_book_reader.dart`.
- Deep history of every decision: `CLAUDE.md` (search "Number Sense", "IOQM", "STORE", "READER").
