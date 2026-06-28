# KiwiReader → KiwiMath: Integration Handover

**To:** the team/agent building the KiwiMath app
**From:** the KiwiReader build
**What this is:** everything you need to drop the **Reader + Library + Store** module into KiwiMath as a new tab, wire it to your backend and your coin system, and ship it.

Read alongside: **`README.md`** (run instructions), **`AUDIT.md`** (what's solid, what's outstanding), **`openapi/openapi.yaml`** (sync REST contract), and the two HTML mockups (`kiwireader_library_mockup.html`, `kiwireader_store_mockup.html`).

---

## 1. TL;DR

KiwiReader is a self-contained Flutter package (`kiwi_reader`) plus a pure-Dart core (`kiwi_reader_core`). It gives KiwiMath three things:

1. **Reader** — read HTML / PDF / EPUB with highlights, underlines, notes, bookmarks, offline-first sync, and Markdown export.
2. **Library** — a grid of the student's books with per-book **offline download** (download / pause / cancel / remove, progress, restart recovery).
3. **Store** — buy a book with money **or** unlock it with **coins** (your existing coin system), then it lands in the Library.

It plugs in through **host seams** (interfaces you implement) and Riverpod provider overrides. **You write no reader logic** — you implement adapters to your content, auth, catalog, coins, and billing, and override a handful of providers. The core is 89-unit-tested and analyzer-clean; the work on your side is the adapters, the backend, and on-device QA.

---

## 2. Package layout

```
kiwireader/
├── packages/
│   ├── kiwi_reader_core/   # PURE DART (no Flutter). Models, anchoring, sync, library, commerce. 89 tests.
│   │   └── lib/io.dart      # opt-in: JsonFileStore, HttpAnnotationApi, SyncServer (dart:io)
│   └── kiwi_reader/        # FLUTTER. Widgets, Riverpod providers, device stores, host seams.
├── openapi/openapi.yaml    # /v1/sync REST contract
├── README.md  AUDIT.md  EXECUTION_PLAN.md
```

Add it to KiwiMath's `pubspec.yaml` (path or git):

```yaml
dependencies:
  kiwi_reader:
    path: ../kiwireader/packages/kiwi_reader   # re-exports kiwi_reader_core
```

KiwiMath must already use **`flutter_riverpod`** and wrap its app in a `ProviderScope` (KiwiReader's state lives there).

---

## 3. The integration contract — host seams you implement

These are the only things you must write. Signatures are exact.

### 3.1 `ContentProvider` — where book content lives _(required)_
```dart
abstract class ContentProvider {
  Future<BookManifest> manifest(String bookId);          // format + sections + contentVersion
  Future<ByteStream> bytes(String bookId, {ByteRange? range}); // Stream<List<int>>
  Future<Uri?> coverImage(String bookId);
}
```
Stream bytes from your CDN/encrypted blob. `contentVersion` drives re-anchoring: bump it when a book is re-published and annotations re-resolve automatically.

### 3.2 `AuthProvider` — token + sign-out _(required)_
```dart
abstract class AuthProvider {
  Future<String> accessToken();   // bearer token for the sync backend
  String get userId;
  Stream<void> get onSignOut;     // see §6: wire this to purge local data
}
```

### 3.3 `CatalogProvider` — the backend book list _(required for Library/Store)_
```dart
abstract class CatalogProvider {
  Future<List<CatalogBook>> books();   // the books for this student (no in-app upload)
}
```
Books are **ingested on your backend**; the app only lists/downloads/buys. Each `CatalogBook`:
```dart
CatalogBook(
  id: 'organic-chem', title: 'Essential Organic Chemistry', author: 'P. Y. Bruice',
  format: BookFormat.pdf, contentVersion: 'v1', coverUrl: 'https://…', byteSize: 14200000,
  pricing: BookPricing(coins: 300, amountMinor: 14900, currency: 'INR'), // see §3.4
);
```

### 3.4 Pricing (data, not code)
Set `pricing` per book from your backend:
- `null` → school-issued / not for sale (treated as owned; never shown in Store).
- `BookPricing.free` → free to claim.
- `BookPricing(coins: 300)` → coins only.
- `BookPricing(amountMinor: 14900, currency: 'INR')` → money only (₹149; **minor units**).
- both fields → student chooses at checkout.

### 3.5 `CoinWallet` — your coin system _(required only if you sell with coins)_
```dart
abstract class CoinWallet {
  Future<int> balance();
  Future<CoinSpendResult> spend({required int amount, required String reason, String? bookId});
  Stream<int> get balanceChanges; // optional; push live balance if you have it
}
// CoinSpendResult.success(newBalance) | CoinSpendResult.failure(currentBalance, 'reason')
```
**This is the bridge to the coin system you built in the other KiwiMath cowork.** Implement it against that wallet's API. Critical requirements (see AUDIT O1):
- `spend` must **deduct on the server authoritatively** and return `ok:false` (without deducting) on insufficient balance or error.
- `spend` should be **idempotent on `(bookId, reason)`** so a retry after a crash re-confirms rather than double-charges.
- Your backend should mark the book **owned at the moment of debit**, so ownership reconciles on next launch even if the local write was lost.

### 3.6 `PurchaseGateway` — real-money billing _(required only if you sell for money)_
```dart
abstract class PurchaseGateway {
  Future<PurchaseResult> purchase(CatalogBook book); // success | cancelled | failed
  Future<List<String>> restore();                    // owned book ids
}
```
On iOS/Android this **must** wrap App Store / Play in-app purchase (`in_app_purchase`) with server-side receipt validation. KiwiReader records the entitlement; it never touches card data. (See §6 compliance.)

---

## 4. Wiring (ProviderScope overrides)

KiwiReader exposes provider "holes" that throw until you override them. Two tiers: **dev** (in-memory, no backend) and **production**.

### 4.1 Dev wiring (runs with no backend — good for first integration)
```dart
ProviderScope(
  overrides: [
    deviceIdProvider.overrideWithValue(myDeviceId),
    localStoreProvider.overrideWithValue(InMemoryLocalStore()),
    annotationApiProvider.overrideWithValue(InMemoryAnnotationApi()),
    contentProviderRef.overrideWithValue(MyContentProvider()),
    catalogProviderRef.overrideWithValue(MyCatalogProvider()),
    contentRendererProvider.overrideWithValue(HtmlRenderer.fromBook(sample)),
    // Store (optional in dev):
    coinWalletProvider.overrideWithValue(MyCoinWallet()),
    purchaseGatewayProvider.overrideWithValue(MyIapGateway()),
  ],
  child: const KiwiMathApp(),
);
```

### 4.2 Production wiring
```dart
// On device, persistent stores + offline-first content + auto-sync:
final dir = (await getApplicationSupportDirectory()).path;
final offlineStore = await FileOfflineBookStore.open('$dir/kiwi_books');

ProviderScope(
  overrides: [
    deviceIdProvider.overrideWithValue(myDeviceId),
    authProviderRef.overrideWithValue(MyAuthProvider()),

    // Annotations: SQLite + real HTTP sync (import 'package:kiwi_reader_core/io.dart')
    localStoreProvider.overrideWithValue(await SqliteLocalStore.open('$dir/kiwi.db')),
    annotationApiProvider.overrideWithValue(HttpAnnotationApi(Uri.parse('https://api.kiwimath…'))),
    connectivityProvider.overrideWithValue(ConnectivityPlusSource()),

    // Library + offline reading (NOTE: one shared offlineStore instance — see AUDIT F5):
    catalogProviderRef.overrideWithValue(MyCatalogProvider()),
    offlineBookStoreProvider.overrideWithValue(offlineStore),
    contentProviderRef.overrideWith((ref) =>
        OfflineFirstContentProvider(MyContentProvider(), ref.watch(offlineBookStoreProvider))),

    // Store:
    coinWalletProvider.overrideWithValue(MyCoinWallet()),
    purchaseGatewayProvider.overrideWithValue(MyIapGateway()),
    entitlementStoreProvider.overrideWithValue(await FileEntitlementStore.open('$dir/kiwi_ent.json')),
  ],
  child: const KiwiMathApp(),
);
```

### 4.3 Drop in the tabs/screens
```dart
// Library tab (owned books; with a Store, set ownedOnly: true):
LibraryScreen(ownedOnly: true, onOpenBook: (ctx, book) => _openReader(ctx, book.id));

// Store tab:
StoreScreen(onOpenBook: (ctx, book) => _openReader(ctx, book.id));

// Opening a book = push the reader:
void _openReader(BuildContext ctx, String bookId) => Navigator.of(ctx).push(
  MaterialPageRoute(builder: (_) => KiwiReader(
    bookId: bookId,
    config: const ReaderConfig(theme: ReaderTheme.sepia),
    onEvent: (e) => analytics.log(e),   // optional
  )),
);
```
The reader picks the HTML/PDF/EPUB surface automatically from the renderer/format.

---

## 5. Backend contract (what KiwiMath's server must provide)

1. **Sync API** — implement `POST /v1/sync` per `openapi/openapi.yaml`. Key rule: the sync delta uses an **opaque monotonic cursor** (`sinceCursor`/`cursor`), not timestamps. The `SyncServer` reference in `io.dart` is a correct, runnable spec to mirror.
2. **Catalog** — an endpoint returning the student's `CatalogBook` list (the JSON shape is `CatalogBook.toJson()`), including `pricing`.
3. **Content** — authenticated book bytes + covers (your `ContentProvider` calls these).
4. **Coins** — an authoritative **spend** endpoint your `CoinWallet` calls; idempotent on `(bookId, reason)`; marks the book owned on debit (AUDIT O1).
5. **Entitlements** — the **source of truth for ownership**. Expose owned-book ids so the app reconciles on launch/sign-in (don't rely only on `PurchaseGateway.restore()`, which is money-only).
6. **Billing** — receipt validation for IAP purchases.

---

## 6. Must-do before a paid launch (from the audit)

These are **host responsibilities** and are currently NOT done:

- **IAP compliance.** Sell digital books (and sell coins for money) through App Store / Play in-app purchase via `PurchaseGateway`. Earning coins via quizzes/streaks and spending them is fine.
- **Encrypt downloaded content at rest (AUDIT O2).** `FileOfflineBookStore` writes raw bytes; for paid content, have `ContentProvider` hand DRM'd/encrypted bytes (or add an encryption hook).
- **Purge on sign-out (AUDIT O3).** Wire `AuthProvider.onSignOut` to clear the offline books, entitlements, and annotations, and namespace storage per `userId` — otherwise data leaks across accounts on a shared device.
- **End-to-end purchase durability (AUDIT O1).** Backend-authoritative ownership + idempotent coin spend + launch reconciliation, so a crash mid-purchase never strands a payment.

---

## 7. Run it

```bash
# Core: real tests (needs Dart ≥ 3.4)
cd packages/kiwi_reader_core && dart pub get && dart analyze && dart test   # 89 pass

# The full module on a device/emulator (needs Flutter ≥ 3.22)
cd packages/kiwi_reader/example && flutter pub get && flutter run
# Demo: Store tab (500 coins, demo gateway) + Library tab (owned-only). Buy/unlock, then download & read.
```

---

## 8. Remaining work owned by KiwiMath (backlog)

1. Implement the six adapters (§3) and the backend (§5).
2. Close the four launch must-dos (§6).
3. **Two device-only wires:** feed pdfrx and epub.js text-selection events into `PdfSelectionController` / `EpubSelectionController` (anchor-creation pipeline behind them is done; `TODO(KR-012-sel)`). HTML reader is fully wired.
4. **Tests/QA the core can't cover here:** widget/golden tests for `LibraryScreen`/`StoreScreen`/acquire sheet; on-device PDF/EPUB QA; an integration test of buy → download → read offline.
5. Hardening from the audit: controller ready-state (M1), outbox single-pass drain (M2), production HTTP client (M4), streaming offline reads (L1), `select`-based rebuilds (L2).

---

## 9. Open questions for the KiwiMath team

1. **Coins:** what is the exact API of the coin system from the other cowork (balance read, spend/debit with idempotency key, live balance events)? That determines the `CoinWallet` adapter.
2. **Currency & catalog:** what currencies/price points, and is ownership stored per-user on the backend today?
3. **Money:** IAP only, or also web checkout? (Affects `PurchaseGateway`.)
4. **DRM:** is content already encrypted/licensed, or do we add at-rest encryption here (O2)?
5. **Coins-for-money:** will coins ever be *purchased* with money? If so they're subject to IAP rules too.

---

## 10. Pointers

- API surface & dev wiring: `README.md`
- Risk register & what's outstanding: `AUDIT.md`
- Sync REST contract: `openapi/openapi.yaml`
- Sprint/ticket history: `EXECUTION_PLAN.md`
- Visual reference: `kiwireader_library_mockup.html`, `kiwireader_store_mockup.html`, `kiwireader_qa_and_mockups.html`, `kiwireader_design.html`

**Bottom line:** the reader, library, and store logic are built and tested. Your path to ship is: implement the adapters, stand up the backend endpoints, close the four launch must-dos, finish the two selection wires, and QA on-device.
