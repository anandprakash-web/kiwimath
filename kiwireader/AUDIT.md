# KiwiReader — Technical Audit

_Independent engineering review of the KiwiReader module (reader + annotation + library + store)._
**Date:** 2026-06-19 · **Reviewer:** Cowork (acting as senior Flutter/Dart engineer) · **Method:** static review of every source file, full `dart analyze`, full unit-test run (89 tests), and a second independent pass by a separate reviewer agent. Fixes were applied and re-tested during the audit.

---

## 1. Verdict

**The pure-Dart core is production-grade: cleanly separated, defensively designed, and well-tested (89 passing unit tests, `dart analyze` clean).** The architecture — a format-agnostic anchoring layer, an offline-first sync engine, and two injectable state machines for downloads and purchases — is genuinely solid, and the riskiest logic is the most thoroughly tested.

**It is not yet shippable end-to-end**, for reasons that are by design rather than defects: the Flutter UI layer cannot be compiled in this environment (no Flutter SDK) and has no widget/integration tests yet; the backend (sync server, catalog, coin ledger, billing) exists only as reference/mocks behind host seams; and three production concerns — **at-rest encryption of paid content, sign-out data purge, and end-to-end purchase idempotency** — are host responsibilities that must be implemented before a paid catalog goes live.

Readiness by layer:

| Layer | State | Confidence |
|---|---|---|
| Core domain (anchoring, sync merge, download, commerce) | Implemented + unit-tested | **High** |
| Core I/O reference (JSON store, HTTP client, sync server) | Implemented + tested; reference-grade | Medium |
| Flutter UI / providers / device stores | Implemented, **syntax-validated only** (not compiled, no widget tests) | Medium-low |
| Backend (sync, catalog, coins, billing) | **Seams only** — host must implement | n/a (external) |

---

## 2. What was audited

Scope: `packages/kiwi_reader_core` (41 lib files) and `packages/kiwi_reader` (28 lib files), 89 unit tests (~1.6k test LOC over ~7k lib LOC), the OpenAPI contract, and the example app.

Method: read all source; ran `dart analyze` (clean) and `dart test` (89/89). The Flutter package was reviewed by reading only — it depends on Flutter/pdfrx/epub.js/sqflite, none of which compile here — and validated for syntax with `dart format`. A second reviewer agent independently re-derived the findings below.

---

## 3. Strengths (verified)

- **Separation of concerns.** All risky logic lives in pure Dart with zero Flutter imports, so it is testable and portable. The Flutter layer is a thin adapter over documented seams (`ContentProvider`, `AuthProvider`, `CatalogProvider`, `CoinWallet`, `PurchaseGateway`, `LocalStore`, `OfflineBookStore`, `EntitlementStore`).
- **Anchoring is robust.** The W3C-style 3-layer anchor (structural + quote + position) and the `AnchorResolver` decision tree (`resolved → repaired → approx → orphaned`, "never silently misplaced") are tested across reflow, edits, repeated phrases, and typos.
- **Sync is skew-proof.** The audit confirmed the earlier fix: sync uses an **opaque monotonic server cursor**, not wall-clock time. Merge covers LWW, tombstone-wins, note keep-both, and deterministic tiebreaks; two-client convergence is tested over real HTTP.
- **The new state machines are defensive.** `DownloadManager` and `StoreController` validate inputs, surface explicit states, and were hardened during this audit (below).

---

## 4. Findings & resolutions

Severities: **Critical** (money/data loss), **High** (correctness/security), **Medium**, **Low/Nit**. "Fixed" items were changed and re-tested in this pass; "Outstanding" items are tracked with an owner.

### Fixed during the audit (core, with new tests)

| # | Sev | Finding | Resolution |
|---|---|---|---|
| F1 | High | **Download completion raced pause/cancel/remove** — a `downloaded` status (or committed bytes) could land after the user cancelled (`DownloadManager._complete` cleaned up and wrote after an `await` with no re-check). | Added a per-book **generation token**; `onData/onDone/onError` and the post-`putBytes` commit now no-op if the generation changed; cancel/pause/remove/dispose bump it. Bytes written during a cancel are removed. New test: _cancel during download; a late completion is ignored_. |
| F2 | High | **Double-tap could double-spend / double-charge** — `unlockWithCoins`/`purchase` only guarded on `isOwned`, which isn't set until after the async spend. | Added an **in-flight guard** (`state == processing → return`). New test: _concurrent double-tap unlocks once (1 spend)_. |
| F3 | Critical (partial) | **A paid book could be lost** if the local entitlement write failed/crashed after a successful spend. | `_grant` now (a) is **idempotent** (never overwrites an existing entitlement, so `restore()` can't downgrade `via`/`acquiredAt`), and (b) **owns in-memory first and tolerates a cache-write failure**, so the book is never lost in-session. New tests: _restore doesn't overwrite_; _failed cache write still grants_. Residual durability is a host responsibility — see O1. |
| F4 | Bug (found while fixing F1) | `dispose()` could throw _concurrent modification_ when a completion finished mid-cancel. | Snapshot + clear `_subs` before awaiting cancels; invalidate all generations. |
| F5 | Doc/High | The `OfflineFirstContentProvider` correctness depends on sharing **one** `OfflineBookStore` instance with the `DownloadManager`. | Made the invariant explicit in dartdoc; `CoinWallet.spend` idempotency requirement documented. |

### Outstanding — must address before a paid launch (host/backend)

- **O1 — End-to-end purchase/coin idempotency & reconciliation _(Critical, host+backend)_.** The client mitigations (F3) are not sufficient alone: the **backend must mark a book owned at the moment coins are debited / payment is captured**, `CoinWallet.spend` must be **idempotent on `(bookId, reason)`**, and the app must **reconcile ownership from the backend on launch / sign-in** (not just `PurchaseGateway.restore()`, which today only covers money). Without this, a crash between debit and grant can still strand a purchase server-side.
- **O2 — Encrypt downloaded content at rest _(High, host)_.** `FileOfflineBookStore` writes raw book bytes to disk. For paid/licensed content this is trivially copyable. The host's `ContentProvider` should hand already-DRM'd/encrypted bytes, or an encryption hook should be added to the offline store. (`BookManifest.license` is a placeholder, not enforced.)
- **O3 — Wire `AuthProvider.onSignOut` to purge local data _(High, host)_.** Nothing currently clears the offline books, entitlements, or annotations on sign-out / account switch, so one student's downloads and ownership can leak into the next account on a shared device. Namespace storage per `userId` and purge on sign-out.

### Outstanding — recommended (medium)

- **M1 — Surface controller init state.** `downloadManagerProvider`/`storeControllerProvider` call `init()` fire-and-forget; the UI can briefly show "nothing owned/downloaded" and a corrupt cache load is swallowed. Expose a ready/`AsyncValue` signal and surface load errors.
- **M2 — Sync drains the outbox in one pass.** When `applyRemote` re-enqueues a merged record (note keep-both / locally-newer), it ships on the _next_ trigger, not immediately. Re-run a sync pass while the outbox is non-empty so merges are durable promptly.
- **M3 — Note keep-both can grow unbounded.** Repeated cross-device note edits keep appending "— also —" fragments. Move to structured authored segments or de-dupe/cap.
- **M4 — Production HTTP client.** The reference `HttpAnnotationApi` has no timeout and treats 4xx like 5xx (so the scheduler back-offs forever on a permanent error) and attaches the bearer token regardless of scheme. The host should use a real client (Dio) with timeouts, 4xx/5xx distinction, and an https-only token path. (The reference exists to prove the contract, not to ship.)

### Low / nits

- **L1 — Streaming reads.** `OfflineFirstContentProvider` returns the whole file as one chunk and `bytesOf` reads it fully into memory; large PDFs are buffered in RAM despite the streaming `ByteStream` design. Use `File.openRead()` for the offline path.
- **L2 — Rebuild granularity.** `storeChangesProvider`/`downloadStatusesProvider` tick all consumers on every progress chunk; use `select`/per-book deltas to avoid rebuilding every card during a download.
- **L3 — `restore()` records `via: purchase` for all restored ids** even if originally a coin unlock (fidelity only; ownership is correct). `DownloadStatus.copyWith` can't clear `version`. Parse timestamps as UTC on read.

---

## 5. Security & compliance

- **App-store billing (blocking for paid launch).** On iOS/Android, selling digital books — and buying coins with real money — must go through **in-app purchase**. That is exactly the role of the `PurchaseGateway` seam; the host must implement it with `in_app_purchase` and server-side receipt validation. *Earning* coins through engagement and spending them is permitted.
- **At-rest encryption & data lifecycle.** See O2/O3. Treat downloaded paid content as licensed material.
- **Token handling.** Tokens flow through `AuthProvider`; the reference HTTP client should be replaced with an https-only, timeout-bounded production client (M4).
- **PII.** Annotations may contain student-authored notes; they sync to the host backend and cache locally. Ensure the backend and local purge honor the host's data-retention/right-to-delete policy.

---

## 6. Known limitations (by design, not defects)

- The **Flutter layer is not compiled or widget-tested here** (no Flutter SDK in the build sandbox); it is syntax-validated and must get on-device QA + widget/golden tests.
- **Two device-only wires remain**: feeding pdfrx and epub.js text-selection events into `PdfSelectionController` / `EpubSelectionController` (the anchor-creation pipeline behind them is complete and tested; marked `TODO(KR-012-sel)`).
- The **sync server, catalog, coin ledger, and billing are reference/mocks**; production implementations live in the host/backend.

---

## 7. Recommendations (prioritized)

1. **Before any paid catalog:** implement O1 (backend-authoritative ownership + idempotent spend + launch reconciliation), O2 (encrypt-at-rest), O3 (sign-out purge), and the IAP `PurchaseGateway`.
2. **Before GA of the reader:** complete the two selection wires; add widget/integration tests for `LibraryScreen`, `StoreScreen`, and the acquire sheet; on-device QA of PDF/EPUB.
3. **Hardening:** M1 (init/ready state), M2 (outbox drain), M4 (production HTTP client).
4. **Polish:** M3 (note merge), L1/L2 (streaming reads, rebuild granularity).

## 8. Sign-off

The core is trustworthy and well-tested, and the highest-severity issues found in this audit were fixed and re-verified (89/89 tests green, analyzer clean). The remaining work is concentrated at the **host/backend boundary** (commerce durability, encryption, sign-out) and in **Flutter-layer QA** — all tracked above and reflected in the handover. With those closed, KiwiReader is ready to integrate into KiwiMath.
