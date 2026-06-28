# Store integration — Phase 1 build (2026-06-19)

Coins end-to-end: a real backend behind KiwiReader's seams + the production app adapters. **earn coins → unlock a real book → it's owned (server-side) → reconciled on launch.** 18/18 new tests; existing 17/17 + 18/18 + 23/23 + pre-deploy all green.

## Backend (built + tested)
- **`app/services/gamification.py`** — added authoritative `spend(user, currency, amount) → (ok, new_balance, err)` and `grant(user, currency, amount)`; debits/credits the one ledger (`kiwi_coins` / `gems`), persists.
- **`app/services/economy_service.py`** — `wallet` · `spend` (idempotent on key; **`reason='unlock_book'` records the book entitlement at debit** = AUDIT **O1 owns-at-debit**; writes a txn ledger) · `grant` (currency and/or book gift) · `claim_free` (validated).
- **`app/services/store_service.py`** — seeded catalog (5 books, `CatalogBook.toJson()` shape, with pricing) + per-user **entitlements** (`FirestoreBackedStore`, source of truth); no-pricing books auto-owned (school-issued).
- **`app/api/store.py`** (wired in `main.py`):
  - `GET  /v3/store/catalog`
  - `GET  /v3/store/entitlements?user_id=`   (owned ids → reconcile on launch)
  - `GET  /v3/economy/wallet?user_id=`
  - `POST /v3/economy/spend`   (assert_user_match; **server enforces the catalog price** so the client can't underpay)
  - `POST /v3/store/claim`     (free books only — validated)
  - `POST /v3/economy/grant`   (admin / internal cron only — leaderboard book gifts + coin payouts)

**Tested — `tests/smoke_store.py` 18/18:** catalog + pricing · wallet · **spend debits + records entitlement** · **idempotent (no double-charge)** · **price enforced (underpay 400)** · insufficient → no deduction · free-claim (paid book rejected) · admin book-gift · **IDOR closed** (cross-user wallet/library/spend → 403; a normal user can't grant).

## App (built — production adapters, structurally verified)
`app/lib/v3/books_integration.dart` now also has the **production adapters** (they read the signed-in Firebase user at call time, so they work under the root `ProviderScope`):
- `_BackendCatalog` → `GET /v3/store/catalog`
- `_BackendWallet` → `balance` = `GET /v3/economy/wallet`; `spend` = `POST /v3/economy/spend` with a **stable idempotency key** `uid:bookId:reason`
- `_BackendEntitlements` → `load` = `GET /v3/store/entitlements` (reconcile on launch); `save` pushes a **free** claim to `/v3/store/claim` (coin/purchase ownership is already server-recorded at debit)
- `backendBooksOverrides()` wires these; `main_v3.dart` now uses it (swap back to `booksOverrides()` for the no-backend demo).

## Stubbed for now (next phases, by design)
- **Content** = the HTML sample renderer for every book (real bytes/covers need **ingestion** → GCS; Phase 1.5).
- **Money** = the dev gateway (real **IAP** + receipt validation = Phase 2).
- **Annotations sync** = in-memory (`POST /v1/sync` backend = Phase 2).
- **Encrypt-at-rest (O2)** + **purge-on-sign-out (O3)** = Phase 3.
- Leaderboard **book gifts** call `POST /v3/economy/grant {sku}` — endpoint ready, wiring to league wins = Phase 4.

## Ship
1. **Backend:** `cd ~/Downloads/kiwimath/backend && ./deploy.sh` (adds the store/economy routes; no content change).
2. **App:** `cd ~/Downloads/kiwimath/app && flutter pub get && flutter analyze 2>&1 | grep "error •" && flutter build apk --release -t lib/main_v3.dart` (paste me any `error •`).
   - To seed yourself coins for testing: `POST /v3/economy/grant` with the internal key, or earn them in-app.
3. **What you'll see:** Olympiad tab → **Library** banner → the **real catalog** from the backend, your **real coin balance**; unlock a coins book → coins debit server-side, the book moves to **My books**, and it **stays owned across reinstalls** (server is the source of truth). Opening it renders the sample chapter (content ingestion is next).

This makes the core flywheel real: **earn coins → unlock a book → read it**, with server-authoritative, idempotent, price-enforced purchases.
