# Store Phase 1.5 — Real book ingestion ("Euclid's Garden")

**Date:** 2026-06-19. Phase 1.5 from the store plan: serve a **real** book end-to-end
so opening it shows the actual book instead of the sample. First book in:
**Euclid's Garden — A Journey Through Geometry** (Anand Prakash), 30 chapters,
81 embedded figures, served as **EPUB** (KiwiReader-native, reflows on phone).

---

## What shipped

### The book file
- Placed at `content-books/euclids-garden/` — `EuclidsGarden.epub` (648 KB, valid
  EPUB 3: `application/epub+zip`, 37-doc spine, 81 SVG figures), `EuclidsGarden_Book.pdf`
  (954 KB, kept as a fallback format), and a generated `cover.png`.
- **Why EPUB, not the `reader/` HTML folder:** the book's README ships a standalone
  multi-file HTML reader, but KiwiReader's HTML path renders its own structured
  `HtmlBook` JSON, not raw HTML pages. The EPUB carries the *same* lessons + figures +
  math, reflows to any screen, and KiwiReader renders it natively (`EpubRenderer`).
  PDF is baked too, so switching is a one-line catalog change if needed on-device.

### Backend (`/v3/store/content/*`)
- `store_service.py` — added the `euclids-garden` catalog row (format `epub`,
  school-issued = no pricing → **owned + readable immediately**) and a `_BOOK_FILES`
  map → on-disk file + format + cover, resolved under `KIWIMATH_BOOKS_DIR`
  (falls back to repo `content-books/`).
- `api/store.py` — three new endpoints behind the shared auth:
  - `GET /v3/store/content/{id}/manifest` → `{id, format, contentVersion, sections, title}` — **entitlement-gated**.
  - `GET /v3/store/content/{id}/bytes` → streams the file (`FileResponse`, supports HTTP Range) — **entitlement-gated** (only an owner reads a book).
  - `GET /v3/store/content/{id}/cover` → the cover PNG (any signed-in user, so it shows in the Store).
- `deploy.sh` — bakes `content-books/` into the image (`COPY content-books/ /content-books/`)
  and sets `KIWIMATH_BOOKS_DIR=/content-books`.

### App (`books_integration.dart`)
- `_BackendContent` — real `ContentProvider`: `manifest` + `bytes` from the new
  endpoints (auth via `authed_http`), so the renderer gets the actual file.
- `_openBook` now resolves the renderer **per book format** — `EpubRenderer.open` /
  `PdfRenderer.open` / `HtmlRenderer` (sample) — using the active `ContentProvider`,
  shows a loading spinner while the file downloads, then pushes `KiwiReader` inside a
  `ProviderScope` that overrides `contentRendererProvider` for that book (KiwiReader
  reads that provider; it does not auto-resolve from format).
- `backendBooksOverrides()` now uses `_BackendContent` (was the synthetic `_DevContent`).

---

## Verification (all green)
| Check | Result |
|---|---|
| `smoke_store` (+5 new content assertions) | ✅ **24/24** |
| └ owned book manifest → 200 (epub) | ✅ |
| └ owned book bytes → 200, `application/epub+zip`, 648,542 bytes, `PK` magic | ✅ |
| └ cover → 200 png; un-ingested book content → 404 | ✅ |
| `smoke_level_v3` / `smoke_adaptive_skill` / `smoke_contest_league` | ✅ 17 / 18 / 23 |
| App import — total routes | ✅ **279** (+3 content), no dup paths |
| `pre_deploy_check` | ✅ PASSED |
| `content_qa_scan` (8 detectors) | ✅ 0 flags |
| `books_integration.dart` | ✅ delimiter-balanced; switch covers all 4 `BookFormat` |

EPUB content confirmed complete: 30 chapters (Points & Definitions → Inscribed Angle →
Power of a Point → Angle Chasing → Trigonometry in Geometry → …), 81 figures.

---

## KiwiReader package fixes (first real compile of its Flutter layer)
Wiring the real EPUB renderer made the app actually **compile** KiwiReader's Flutter
presentation layer for the first time (the prior APK predated the store work and never
pulled it in). That surfaced latent bugs in the package itself (`kiwireader/`), which its
pure-Dart core tests (89, core-only) never exercised. Found + fixed:
- **`kiwi_reader_widget.dart`** — the PDF & EPUB surfaces called `_createExternal(...)`, a
  method that doesn't exist (4 call sites). The real method is `_createPdf(Anchor, {token, noteText})`
  — renamed the calls. (Would fail to compile for *any* book, even HTML.)
- **`epub_reader_surface.dart`** — used `EpubSource.fromBytes(...)`, which doesn't exist in
  `flutter_epub_viewer 1.2.8` (it loads from url/file/asset). Now stages the EPUB bytes to a
  temp file once (`dart:io`) and uses `EpubSource.fromFile(...)`.

Then an **exhaustive verification pass** over the whole never-compiled layer:
- Scripted scan for the same "called-but-undefined private method" bug class across all 28
  package files → **0** (the 13 hits were all same-file private classes).
- External-API calls checked against the **actually-resolved** versions: `pdfrx 1.3.5`
  (`PdfViewer.data`, `PdfViewerParams.enableTextSelection`/`pagePaintCallbacks`,
  `PdfViewerPagePaintCallback(Canvas,Rect,PdfPage)`, `PdfDocument.openData`) — all confirmed
  against dartdoc; `sqflite 2.4.2`, `connectivity_plus 6.1.5` (`List<ConnectivityResult>` API),
  `uuid` — all match.
- Independent subagent cross-checked every constructor call / `@override` / enum switch /
  type reference in all 28 files against `kiwi_reader_core` → **no additional compile errors**.
- Android/Gradle/NDK config is fine — the failed build reached the Dart compile step (NDK 27
  installed, Gradle ran), so only the Dart errors above blocked it.

**Fast iterate loop:** app-dir `flutter analyze` does NOT descend into the path-package's own
files, so verify the package directly:
`cd ~/Downloads/kiwimath/kiwireader/packages/kiwi_reader && flutter pub get && flutter analyze`
(8 s, authoritative) — then the full APK build. Paste any residual error.

## Ship
- **Backend:** `cd ~/Downloads/kiwimath/backend && ./deploy.sh` — bakes the book + serves `/v3/store/content/*`.
- **APK:** `cd ~/Downloads/kiwimath/app && flutter pub get && flutter analyze && flutter build apk --release -t lib/main_v3.dart` — opens the real EPUB in the reader.
- After deploy, the book appears in **Library → My books** (auto-owned) → tap → reads in KiwiReader.

## Notes / next
- EPUB & PDF rendering is device-only (epub.js WebView / PDFium) — can't render here;
  **on-device QA**: open the book, check figures + math + reflow. If EPUB looks off,
  flip the catalog row to `format: "pdf"` (PDF already baked) — no code change.
- Cover is served but not yet wired as `coverUrl` (auth-on-image); cards show the
  generated placeholder until covers move to a public URL/GCS. Cosmetic only.
- To sell this book instead of giving it: add a `pricing` block to the catalog row
  (coins and/or money) — the unlock→own→read flow is already tested for paid books.
- At scale, move book files from baked-in to GCS (the `file_path` resolver is the seam).
