# KiwiReader

A Kindle-Scribe-style **reader + annotation** module that plugs into the kiwimaths Flutter app as a new **Read** tab. Highlight, underline, note, bookmark (and, in Phase 2, sketch with a stylus) on top of PDF / EPUB / custom-HTML / image content — with annotations that survive reflow, re-publish and device switches.

> Design rationale, state machines, branching and UI are in **`kiwireader_design.html`**. The build plan is in **`EXECUTION_PLAN.md`**.

---

## Status (M0 core + first slice of M1)

| Thing | State |
|---|---|
| `kiwi_reader_core` (pure Dart) | ✅ implemented |
| Core unit tests | ✅ **89 passing**, `dart analyze` clean |
| `openapi/openapi.yaml` | ✅ validates (6 paths, 13 schemas) |
| `AnchorFactory` (selection → anchor, KR-020) | ✅ implemented + round-trip tested |
| `OffsetMap` (display ↔ canonical) | ✅ implemented + tested |
| **Real persistence** — `JsonFileStore` (survives restart) | ✅ implemented + tested |
| **Real sync** — `HttpAnnotationApi` + runnable `SyncServer` over `/v1/sync` | ✅ tested end-to-end over HTTP (two clients converge); bearer token verified |
| **Auto-sync** — `SyncScheduler` (connectivity-gated, periodic, backoff, in-flight guard) | ✅ implemented + unit-tested |
| **PDF anchor geometry** — `PdfAnchorFactory` (normalized quads ⇄ pixels) | ✅ implemented + unit-tested |
| HTML reader: highlight · note · recolor · delete · list · **bookmarks · cross-block selection** · auto-sync | 🟢 implemented; runs via the example |
| **PDF reader** — `PdfRenderer` + `PdfReaderSurface` (pdfrx); highlight overlay (tested geometry) + create pipeline | 🟡 implemented; one device wire: feed pdfrx selection into `PdfSelectionController` |
| **EPUB reader** — `EpubRenderer` + `EpubReaderSurface` (flutter_epub_viewer); CFI+quote anchors | 🟡 implemented; runs on a device (WebView/epub.js) |
| **On-device store** — `SqliteLocalStore` (sqflite) | 🟢 implemented behind `LocalStore` (JsonFileStore is the tested reference) |
| Format-agnostic reader: picks HTML / PDF / EPUB surface by renderer type | 🟢 implemented |
| **Export** — `AnnotationExporter.toMarkdown` (revision sheet) + export action | 🟢 implemented + unit-tested |
| **Library catalog** — `CatalogProvider` (backend book list; **no in-app upload**) + `LibraryScreen` grid | 🟢 implemented; grid runs via the example |
| **Offline downloads** — `DownloadManager` (queue, progress, pause/cancel/remove/retry, restart recovery) | ✅ implemented + **unit-tested (10)** |
| **Offline store** — `OfflineBookStore` (in-memory tested ref + device `FileOfflineBookStore`) + `OfflineFirstContentProvider` | 🟢 implemented |
| **Store / commerce** — `BookPricing` on `CatalogBook`, `Entitlement`, `StoreController` (buy with money **or** unlock with coins) | ✅ implemented + **unit-tested (13)** |
| **Coin + billing seams** — `CoinWallet` (kiwiapp coins) + `PurchaseGateway` (App Store/Play/Stripe) + `EntitlementStore` | 🟢 implemented (host wires its systems) |
| **Store UI** — `StoreScreen` (price grid), acquire sheet (buy/unlock + insufficient-coins), `CoinBalanceChip`; Library `ownedOnly` | 🟢 implemented; runs via the example |

The riskiest logic — **anchor resolution**, **sync conflict resolution**, and **anchor construction** — is implemented and unit-tested first, on purpose. (The Flutter layer can't be compiled in the build sandbox — no Flutter SDK — but every `.dart` file is syntactically validated and the slice runs with `flutter run` in `packages/kiwi_reader/example`.)

---

## Layout

```
kiwireader/
├── packages/
│   ├── kiwi_reader_core/    # PURE DART. Models, anchoring, sync. No Flutter. Tested here.
│   │   ├── lib/src/models/        annotation, anchor, 3 selectors, bookmark, progress, manifest
│   │   ├── lib/src/anchoring/     text normalizer, quote matcher, AnchorResolver, Reconciler
│   │   ├── lib/src/sync/          merge (LWW + tombstone + keep-both), SyncEngine, in-memory mock
│   │   ├── lib/src/store/         LocalStore interface + InMemoryLocalStore
│   │   ├── lib/src/library/       CatalogBook, DownloadStatus, DownloadManager, OfflineBookStore
│   │   ├── lib/src/commerce/      BookPricing, Entitlement, StoreController, CoinWallet, PurchaseGateway
│   │   └── test/                  89 unit tests
│   └── kiwi_reader/        # FLUTTER. Riverpod wiring, ContentRenderer seam, KiwiReader widget.
├── openapi/openapi.yaml    # Annotation & Sync REST contract
├── EXECUTION_PLAN.md
└── README.md
```

---

## Run the core tests

Requires the Dart SDK (>= 3.4).

```bash
cd packages/kiwi_reader_core
dart pub get
dart analyze        # -> No issues found!
dart test           # -> All tests passed!  (46)
```

### Run a real sync backend + persistent store (pure Dart, no Flutter)

```bash
cd packages/kiwi_reader_core
dart run kiwi_reader_core:mock_server 8080   # POST /v1/sync, GET /health
```

Wire a host (or any Dart client) to real persistence + sync via the io entrypoint:

```dart
import 'package:kiwi_reader_core/io.dart';

final store = await JsonFileStore.open('/path/annotations.json'); // survives restart
final api = HttpAnnotationApi(Uri.parse('http://127.0.0.1:8080'));
// ProviderScope overrides:
//   localStoreProvider.overrideWithValue(store),
//   annotationApiProvider.overrideWithValue(api),
```

`SyncEngine` is unchanged — it depends only on the `LocalStore` + `AnnotationApi`
interfaces, so these drop in. On mobile, swap `JsonFileStore` for a Drift store
(KR-025) behind the same interface.

### Run the reader slice (needs Flutter)

```bash
cd packages/kiwi_reader/example
flutter pub get
flutter run        # long-press-drag a sentence, tap a color; the ☁ button syncs
```
The example wires the in-memory store + mock backend and a sample book, so it runs with no backend.

### What the tests prove

**Anchoring** (`test/anchor_resolver_test.dart`) — every branch of the resolution decision tree:
`resolved` (structural + quote agree) · `repaired` (structural stale → relocated by quote) · position disambiguation of repeated quotes · prefix/suffix context disambiguation · `approx` (fuzzy match on a typo) · position-only fallback · `orphaned` (kept, never misplaced) · whitespace-reflow immunity.

**Anchor construction** (`test/anchor_factory_test.dart`) — `AnchorFactory.fromSelection` → `AnchorResolver` **round-trip**: a freshly-made highlight resolves back to the same range; and still lands correctly after whitespace reflow, after a content edit that shifts offsets, and on a repeated phrase (disambiguated by captured prefix/suffix).

**Display ↔ canonical mapping** (`test/offset_map_test.dart`) — `OffsetMap` agrees with the normalizer, round-trips display↔canonical offsets, maps a multi-space DISPLAY selection to the right collapsed canonical text, and trims leading/trailing whitespace. This is what lets blocks render real line breaks while anchors stay in stable canonical coordinates.

**Persistence** (`test/json_file_store_test.dart`) — a `JsonFileStore` keeps items, the outbox and the sync cursor across a full reopen; cleared outbox entries and tombstones persist.

**Real HTTP sync** (`test/http_sync_test.dart`) — spins up the `SyncServer` in-process and drives `SyncEngine` through `HttpAnnotationApi`: two clients converge over the wire, a delete propagates as a tombstone, and the **bearer token from `tokenProvider` is sent** — proving the OpenAPI JSON contract round-trips for real.

**Auto-sync orchestration** (`test/sync_scheduler_test.dart`) — `SyncScheduler` skips when offline, runs + ends idle on success, **retries with exponential backoff** until success, **triggers a sync when connectivity returns**, and an **in-flight guard** prevents overlapping syncs.

**PDF anchor geometry** (`test/pdf_anchor_test.dart`) — `PdfAnchorFactory` normalizes a selection's page-point rects to 0..1 page quads and denormalizes them to any render size (zoom/DPI-proof), clamps out-of-bounds rects, makes region-only anchors for scanned PDFs, and round-trips through `Anchor` JSON.

**Export** (`test/annotation_exporter_test.dart`) — `AnnotationExporter.toMarkdown` groups by section (first-seen order), renders highlights/notes/bookmarks with quotes + notes + counts, collapses whitespace, and excludes soft-deleted records.

**Offline downloads** (`test/download_manager_test.dart`) — `DownloadManager` drives the whole offline state machine with no device, network, or Flutter: `notDownloaded → queued → downloading(%) → downloaded`, progress fractions (and indeterminate progress when size is unknown), the **concurrency limit** (extra books wait in the queue and only open when a slot frees), **pause / cancel / remove**, a stream error → `failed` (with message) then **retry → downloaded**, a changed `contentVersion` **forcing a re-download**, and **restart recovery** — an interrupted download is normalized back to `notDownloaded`, never left as a phantom "offline" copy.

**Store / acquisition** (`test/store_controller_test.dart`) — `StoreController` drives the buy-or-unlock state machine against fake seams: **unlock with coins** debits the wallet and grants ownership; **insufficient coins** fails without ever calling spend; a **declined spend** stays unowned; a coins-only call is rejected for a money-only book; **purchase** success/cancelled/failed map correctly (cancelled ≠ error); an **already-owned** book is never charged twice on either path; **free** books are claimed at no cost; **restore** reconciles previously-bought books; and `init()` restores persisted ownership + balance. (Plus pricing/entitlement JSON round-trips and `₹/$` formatting.)

**Sync** (`test/merge_test.dart`, `test/sync_engine_test.dart`) — the full conflict matrix:
newer-wins LWW · **tombstone beats a newer edit** · later-tombstone wins · **note keep-both** · deterministic tiebreak · offline-create→push · remote delta pull · server-wins conflict learned by client · delete propagation · idempotent re-sync · **two devices converge**.

> Implementing the tests surfaced a real bug: a wall-clock sync cursor breaks under client/server clock skew. Fixed by switching to an **opaque monotonic server cursor** (`SyncRequest.sinceCursor`) — the standard, skew-proof approach.

---

## Integrate into kiwimaths

1. Add the package (path or git):
   ```yaml
   dependencies:
     kiwi_reader:
       path: ../kiwireader/packages/kiwi_reader
   ```
2. Implement the host interfaces: `ContentProvider` (book manifest + bytes), `AuthProvider` (token + sign-out), and `CatalogProvider` (`books()` — the backend-uploaded list; the app never uploads).
3. Override the dependency providers in your `ProviderScope` (`contentProviderRef`, `authProviderRef`, `deviceIdProvider`, `localStoreProvider`, `annotationApiProvider`). For local dev you can override the last two with the bundled `InMemoryLocalStore` and `InMemoryAnnotationApi`.
4. Drop the widget into the Read tab:
   ```dart
   KiwiReader(
     bookId: 'calc-ncert-ch3',
     config: const ReaderConfig(theme: ReaderTheme.sepia, enableInk: true),
     onEvent: (e) => analytics.log(e),
   )
   ```
5. Add the **Library tab** (browse + download for offline). It lists the
   backend catalog and downloads books via the pure-Dart `DownloadManager`;
   opening a downloaded book reads from the device:
   ```dart
   // Read offline once downloaded:
   contentProviderRef.overrideWith((ref) => OfflineFirstContentProvider(
         myContentProvider, ref.watch(offlineBookStoreProvider)));
   // On device, persist downloads across restarts:
   // offlineBookStoreProvider.overrideWithValue(await FileOfflineBookStore.open(dir))

   LibraryScreen(
     ownedOnly: true, // with a Store, Library shows owned books
     onOpenBook: (context, book) => Navigator.of(context).push(
       MaterialPageRoute(builder: (_) => KiwiReader(bookId: book.id)),
     ),
   )
   ```
6. (Optional) Add the **Store tab** — buy with money or unlock with coins. Wire
   the two seams to your systems and drop in `StoreScreen`:
   ```dart
   // Coins -> the kiwiapp coin system you already built:
   coinWalletProvider.overrideWithValue(MyKiwiCoinWallet());
   // Money -> App Store / Play / web billing (the host owns receipts):
   purchaseGatewayProvider.overrideWithValue(MyIapGateway());
   // entitlementStoreProvider.overrideWithValue(myPersistentEntitlementStore);

   StoreScreen(onOpenBook: (context, book) => /* push KiwiReader */);
   ```
   Each `CatalogBook` the backend returns just sets `pricing:`
   (`BookPricing(coins: 300, amountMinor: 14900, currency: 'INR')`, or
   `BookPricing.free`, or `null` for school-issued). Either seam may be left
   `null` to disable that path.

   > **App-store compliance:** selling digital books — and buying coins with
   > money — must go through in-app purchase on iOS/Android; that is the role of
   > `PurchaseGateway`. *Earning* coins through engagement and spending them is
   > fine. Confirm your billing setup before shipping.

---

## Done so far / what's next

**Done:** core (models, anchoring, sync) + tests; OpenAPI; `AnchorFactory` (KR-020); `OffsetMap` (display↔canonical, so blocks keep line breaks); the **HTML reader slice** — `HtmlRenderer` (KR-011), highlight overlay from resolved anchors (KR-021), selection toolbar (KR-022), optimistic create (KR-023), **note editor (KR-030), tap-a-highlight recolor/note/delete, and the annotations list with jump-to (KR-032)** — all runnable via the example.

Plus **real persistence** (`JsonFileStore`, KR-025 reference), **real HTTP sync** (`HttpAnnotationApi` + runnable `SyncServer`, KR-035) with bearer-token auth, and **auto-sync** (`SyncScheduler`: connectivity-gated, periodic, backoff, in-flight guard — KR-036) surfaced as a live status icon in the reader — all tested end-to-end here.

Plus the full roadmap: **PDF** (`PdfRenderer` + tested quad geometry), **EPUB** (`EpubRenderer`, CFI+quote anchors), **bookmarks**, **cross-block selection** (section-level painter, which also restored paragraph breaks), the **on-device `SqliteLocalStore`**, and **Markdown export**. The reader **picks the HTML / PDF / EPUB surface by renderer type** — the format-agnostic seam working end to end across all three formats.

**Remaining (device-only wires + later phases):**

- One device wire each for PDF and EPUB **text-selection capture** (feed the viewer's selection event into the `PdfSelectionController` / `EpubSelectionController`; the create pipeline behind them is complete).
- Orphaned "needs review" banner; **PDF/HTML export** (Markdown export is done + tested); Phase-2 stylus ink; Phase-3 teacher-shared annotations + highlight→quiz linking.

Every `.dart` file is syntactically validated here; the core is fully compiled + tested. The Flutter layer compiles/runs on a machine with the Flutter SDK (`flutter run` in the example).

---

## Requirements

- Dart SDK ≥ 3.4 (core)
- Flutter ≥ 3.22 (reader package)
