# Kiwimath Store + Reader Integration Plan (KiwiReader)

*How we add a **Store + Library + Reader** to the Kiwimath app by dropping in the `kiwi_reader` package from the other cowork space, wiring it to our backend + coin economy, and shipping it. Grounded in the actual KiwiReader code (`HANDOVER_KIWIMATH.md`, `AUDIT.md`, the `commerce/` seams) and our own `KIWIMATH_ECONOMY_STORE_CONTRACT.md`.*

**Last updated:** 2026-06-19.

---

## 0. The good news (what we do *not* have to build)
KiwiReader is a self-contained Flutter package (`kiwi_reader` + a pure-Dart `kiwi_reader_core`, 89 unit tests, analyzer-clean) that already gives us:
- **Reader** — HTML / PDF / EPUB, highlights, notes, bookmarks, offline-first sync, Markdown export.
- **Library** — a grid of owned books with per-book offline download (pause/cancel/resume).
- **Store** — buy a book with **money** or unlock it with **coins**, then it lands in the Library. The whole **purchase saga is already written and tested** (`StoreController`: ownership checks, insufficient-coins, declined payments, no double-charge, idempotent grant, in-memory-first durability).

We write **no reader logic**. Our job is exactly three things: implement **6 adapters**, stand up the **backend endpoints**, and close the **4 launch must-dos**. That's it.

---

## 1. How it plugs in (mechanics)
1. Add the package to `app/pubspec.yaml`:
   ```yaml
   dependencies:
     kiwi_reader:
       path: ../kiwireader/packages/kiwi_reader
   ```
2. **Riverpod.** KiwiReader's state lives in a `ProviderScope`; our v3 app (`kiwi_v3.dart`) currently uses plain `setState`. **Action:** add `flutter_riverpod` and wrap the root `MaterialApp` in `main_v3.dart` with a `ProviderScope`. The existing `setState` screens are unaffected (they just live inside the scope); only the Library/Store/Reader subtree reads the providers. Low cost, no rewrite.
3. Drop in the screens (a new **"Library/Store" tab** or a section under the Compete/Profile area):
   - `LibraryScreen(ownedOnly: true, onOpenBook: …)` — owned books.
   - `StoreScreen(onOpenBook: …)` — browse + buy/unlock.
   - Open a book → `Navigator.push(KiwiReader(bookId: …, config: ReaderConfig(theme: …)))`.
4. Override the **provider seams** in the `ProviderScope` with our adapters (§2).

---

## 2. The 6 adapters we implement (the integration surface)
These are the only Dart we write on the app side. Signatures are fixed by KiwiReader.

| # | Seam | What we implement | Backs onto |
|---|------|-------------------|------------|
| 1 | **`CoinWallet`** | `balance()` + `spend({amount, reason, bookId})` → `CoinSpendResult` | **our economy wallet** — `GET /v1/economy/wallet` + `POST /v1/economy/spend` (the bridge; §3) |
| 2 | **`CatalogProvider`** | `books()` → `List<CatalogBook>` (with `BookPricing`) | `GET /v3/store/catalog` |
| 3 | **`ContentProvider`** | `manifest()`, `bytes()` (streamed), `coverImage()` | `GET /v3/store/content/{id}/…` (authed, from GCS/CDN) |
| 4 | **`AuthProvider`** | `accessToken()`, `userId`, `onSignOut` | wrap our existing **Firebase auth** + an app sign-out stream |
| 5 | **`PurchaseGateway`** | `purchase(book)`, `restore()` | **IAP** (`in_app_purchase`) + our receipt-validation endpoint |
| 6 | **`EntitlementStore`** | already provided: `FileEntitlementStore` (device) | reconciled from `GET /v3/store/entitlements` on launch |

KiwiReader ships device implementations for the storage seams (`SqliteLocalStore`, `FileOfflineBookStore`, `FileEntitlementStore`) — we just open them and pass paths. So adapters 2–5 plus the `CoinWallet` are the real work, and they're thin.

---

## 3. The coin bridge (this is the half we've already designed)
`CoinWallet.spend(amount, reason: 'unlock_book', bookId)` is *exactly* the `spend` in our **Economy & Store Integration Contract**. We implement the adapter against two endpoints we add to the Kiwimath backend:

- **`GET /v1/economy/wallet/{userId}`** → `{coins, gems}` (we already expose coins via `/v3/me/wallet`; add a stable economy wallet read).
- **`POST /v1/economy/spend`** → `{userId, currency:'coins', amount, sku:bookId, reason:'unlock_book', idempotencyKey}`. Server-authoritative deduct; returns `ok:false` (no deduction) on insufficient/҂error. **Idempotent on `(userId, bookId, reason)`** so a crash-retry re-confirms instead of double-charging (KiwiReader requires this; AUDIT F3/O1).
- **`POST /v1/economy/grant`** → credit coins/gems **or** grant a book entitlement directly — used by the **leaderboard** for milestone book gifts ("win Gold league → free book"). This is the *earn* path.

We already hardened this idempotency pattern (`get/record_idempotent_response`) and the `assert_user_match` auth on the leaderboard MVP — we reuse both.

---

## 4. Backend we build (the catalog/content/entitlement/sync side)
| Endpoint | Purpose | Notes |
|---|---|---|
| `GET /v3/store/catalog` | the student's `CatalogBook` list + pricing | JSON = `CatalogBook.toJson()`; books **ingested on backend**, never from the app |
| `GET /v3/store/entitlements` | **source-of-truth owned-book ids** | app reconciles on launch (closes O1's "reconcile on launch") |
| `GET /v3/store/content/{id}/manifest` · `…/bytes` · `…/cover` | authed book content | stream bytes (ranged) from GCS; covers from CDN |
| `POST /v1/sync` | annotations sync | mirror KiwiReader's `SyncServer` reference + `openapi/openapi.yaml`; **opaque monotonic cursor, not timestamps** |
| `POST /v1/billing/validate` | IAP receipt validation | marks the entitlement owned on capture |
| (admin) book **ingestion** | upload EPUB/PDF/HTML → GCS + a catalog row with pricing | start with a handful of books by hand |

Ownership is written **server-side at the moment coins are debited / payment captured** (AUDIT O1) so it always reconciles, even if the device write is lost.

---

## 5. Coins vs Gems vs money — how our economy maps
KiwiReader's pricing is **coins + money** only (no gems). We map:
- **Common books → Coins** (the `CoinWallet`, free-to-play kids can earn them).
- **Money path → IAP** (`PurchaseGateway`) for parents who'd rather pay.
- **Gems / achievements / league wins → the *grant* path.** A milestone or a Gem-gated title is delivered by the backend **granting the book entitlement directly** ("unlocked at Master", "free book for winning your league") — no KiwiReader change, and it keeps the powerful *competing-earns-books* loop.
- To also **sell** books for Gems inside the Store later, ask the KiwiReader team to add a `gems` field to `BookPricing` (a tiny, additive change). Not needed for MVP.
- Do the **one-Gems consolidation** from the contract first, so the wallet has a single hard currency.

Crucially, **money never buys rank or rating** — books are content, not competitive power — so selling them is fair and doesn't touch the leaderboard.

---

## 6. The four launch must-dos (host responsibilities, from the audit)
| # | Must-do | Our plan |
|---|---------|----------|
| **O1** | end-to-end purchase durability | backend owns-at-debit + idempotent `spend` on `(user,book,reason)` + **reconcile `/store/entitlements` on launch** |
| **O2** | encrypt paid content at rest | `ContentProvider` hands DRM'd/encrypted bytes (or add an encryption hook in the offline store) |
| **O3** | purge on sign-out | wire `AuthProvider.onSignOut` → clear offline books + entitlements + annotations; namespace device storage per `userId` |
| **IAP** | store compliance | sell digital books (and, if ever, coins-for-money) through App Store / Play IAP; earning coins via quizzes/streaks and spending them is fine |

Plus two small device wires KiwiReader left for the host: feed pdfrx / epub.js text-selection events into `PdfSelectionController` / `EpubSelectionController` (HTML reader is already fully wired); and add widget/golden tests for the Library/Store screens.

---

## 7. The flywheel this closes
```
  Leaderboard / practice ──earn──▶ Coins & Gems ──spend/grant──▶ Books (KiwiReader store)
            ▲                                                          │
            └──────────────────── more learning ◀──────read───────────┘
```
The store is the **sink that finally gives coins a purpose**, and "win your league → free book" is the strongest motivator we can offer. Pricing guardrails from the contract: common book ≈ ~2 weeks of coins; don't inflate coins before the store exists; track minted-vs-spent.

---

## 8. Phased rollout
- **Phase 0 — Spike (a few days).** Add the package + a root `ProviderScope` + **dev wiring** (in-memory adapters + one sample book bundled). Library/Store/Reader run with **no backend**. Proves the drop-in compiles and reads on-device.
- **Phase 1 — Coins end-to-end.** Build `GET/POST /v1/economy/wallet|spend`, `GET /v3/store/catalog`, `GET /v3/store/entitlements`, `…/content/*`; implement the 6 production adapters; ingest ~5 books to GCS. **Buy-with-coins + claim-free working end-to-end**, owned book opens in the reader, downloads offline.
- **Phase 2 — Money + durability.** `PurchaseGateway` via `in_app_purchase` + receipt validation; close **O1** (owns-at-debit + idempotent spend + launch reconcile). Sync API (`POST /v1/sync`) for annotations.
- **Phase 3 — Security + QA.** Close **O2** (encrypt-at-rest) and **O3** (purge-on-sign-out); the two PDF/EPUB selection wires; widget/golden tests; on-device QA of **buy → download → read offline**.
- **Phase 4 — Tie to the economy.** Milestone **book gifts** wired to the leaderboard `grant`; Gem pricing in the Store (if we extend `BookPricing`); seasonal book rewards.

---

## 9. Their open questions — answered from our side
1. **Coin API?** It's the economy wallet we built for the leaderboard. We'll expose `GET /v1/economy/wallet` (balance) + `POST /v1/economy/spend` (idempotent on `(user,book,reason)`, server-authoritative) + live balance via the existing wallet refresh. → drives the `CoinWallet` adapter.
2. **Currency & catalog / per-user ownership?** Coins (virtual) + money (INR, minor units). Ownership stored **per-user on the backend** (`/store/entitlements`) — we'll build it as the source of truth.
3. **Money: IAP or web?** Mobile-first → **IAP** (`in_app_purchase`) with server receipt validation; web later.
4. **DRM?** Not encrypted yet → we add **at-rest encryption** here (O2) and have `ContentProvider` hand protected bytes.
5. **Coins-for-money?** Not in MVP. If ever, they're subject to IAP rules — flag at that time.

## 10. Questions back to the KiwiReader team
1. Add a `gems` field to `BookPricing` for a second store currency (additive) — or keep Gems on the grant/gift path only?
2. Confirm the `BookManifest`/`ContentProvider` bytes shape for PDF + EPUB so we build the content endpoint to match.
3. The `/v1/sync` cursor + payload: we'll mirror your `SyncServer` reference — anything beyond `openapi.yaml` we should know?

---

## 11. Bottom line / sequencing
The reader, library, and store **logic are done and tested**. Our critical path is: **(a)** package + ProviderScope + dev wiring (proves it runs), **(b)** the economy `spend/wallet` + catalog + entitlements backend (the coin bridge we already designed), **(c)** IAP + the O1 durability, **(d)** O2/O3 + on-device QA. Phases 0–1 alone deliver "earn coins → unlock a book → read it," which is the whole point — and it rides on the economy and auth patterns we've already built and hardened.
