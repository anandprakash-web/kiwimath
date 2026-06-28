# Kiwimath — Economy & Store Integration Contract

*The shared agreement between the **Economy/Leaderboard** build (this space — owns the wallet) and the **Bookstore + Reader** build (the other cowork space — owns the catalog, entitlements, reader). Build against this so the two never drift.*

**Status:** v1 draft for alignment. **Last updated:** 2026-06-18.

---

## 0. The one rule
There is **exactly one wallet per user**, owned by the Economy service, mutated **only** through a server-authoritative, idempotent API. No other service (including the bookstore) ever writes a balance directly or trusts a client-supplied balance. Everything else here follows from that.

---

## 1. Ownership split (who owns what)

| Domain | Owner | Holds |
|---|---|---|
| **Wallet** (Coins, Gems balances + transaction ledger) | **Economy service** (this space) | `wallets/{userId}`, `wallet_txns/{txnId}` |
| **Earning** (practice, contests, leagues, streaks, milestones) | Economy service | calls `grant()` internally |
| **Catalog** (books, metadata, prices) | **Bookstore** (other space) | `catalog/{sku}` |
| **Entitlements** (which books a user owns) | **Bookstore** | `entitlements/{userId}/books/{sku}` |
| **Reader** (reading the book) | **Bookstore** | — |
| **The purchase** (spend currency → grant book) | **Bookstore orchestrates**, Economy executes the spend | the saga in §5 |

Clean boundary: **money lives with the Economy service; books live with the Bookstore.** A purchase is the one cross-boundary transaction — §5 makes it safe.

---

## 2. The currency model (final)

| Currency | Type | Earned from | Spendable? | Buys | Resets |
|---|---|---|---|---|---|
| **XP** | progression | every question | no | — (drives account Level) | no |
| **Kiwi Coins** | **soft / spendable** | practice + reward payouts + daily login | **yes** | cosmetics, **common books** | no |
| **Gems** | **hard / prestige** | achievements, contest wins, milestones | **yes** | premium cosmetics, **premium / gated books** | no |
| **League Points (LP)** | score | contest + effort + streak | no (it's a rank) | — | weekly |
| **Kiwi Rating** | status | contests only | no (it's a status) | — | persistent |
| **Streak** | consistency | daily activity | no | — (drives multipliers) | on miss |

**Consolidate the two "gems".** Today there are two gem-like meters (Mastery Gems + the engagement-calendar `totalGems`). The store needs **one Gems**. Migration: sum existing balances into a single `gems` field; the daily calendar henceforth grants Coins (+ occasional Gems) into the same ledger.

**Only Coins and Gems are spendable.** The store transacts in those two only. LP and Rating are never spent — but *performing well on them pays out Coins/Gems* (§6), which is how competition funds the store without ever letting anyone *buy* rank.

---

## 3. Single source of truth — the wallet ledger

- `wallets/{userId}` holds `{coins, gems, version, updatedAt}`.
- Every mutation appends a row to `wallet_txns/{txnId}` `{userId, currency, delta, reason, sku?, idempotencyKey, balanceAfter, ts}` — a full audit trail (essential once real money + real value are involved).
- All writes are **server-authoritative** and **idempotent** (§4.4). Mutations use a transaction (read-modify-write under a version check) so concurrent spends/grants can't double-apply — the same compare-and-set discipline used for the adaptive ladder.

---

## 4. The API contract

Base: `/v1/economy`. Auth on every call: a valid user token **and** `assert_user_match(token, userId)` (the pattern already hardened in this codebase) — a user can only touch their own wallet. Server-to-server calls (bookstore → economy) use a service token with an `actingFor: userId` claim.

### 4.1 `GET /v1/economy/wallet/{userId}` → balances (read)
```json
200 → { "userId":"u_123", "coins": 1840, "gems": 7, "xp": 21030, "level": 12,
        "rating": 1660, "streak": 23, "version": 88 }
```
For display only. Never used as the source of truth for a spend (the spend re-reads server-side).

### 4.2 `POST /v1/economy/spend` → deduct (write, idempotent)
```json
REQUEST  { "userId":"u_123", "currency":"coins", "amount":1500,
           "sku":"book_fractions_lvl4", "reason":"store_purchase",
           "idempotencyKey":"buy_u123_bookFr_9f2c" }
200      { "ok":true, "txnId":"t_55", "currency":"coins",
           "newBalance":340, "replayed":false }
409      { "ok":false, "error":"INSUFFICIENT_FUNDS", "balance":900, "needed":1500 }
```
Server re-reads the balance, checks `balance >= amount`, deducts atomically, writes the txn. `amount` must be a positive integer.

### 4.3 `POST /v1/economy/grant` → credit (write, idempotent)
```json
REQUEST  { "userId":"u_123", "currency":"gems", "amount":3,
           "reason":"league_win_gold_wk24", "idempotencyKey":"grant_u123_wk24_gold" }
200      { "ok":true, "txnId":"t_56", "currency":"gems", "newBalance":10, "replayed":false }
```
Used by the leaderboard (league/season/rating rewards), daily login, streak milestones, and **book milestone gifts** (which grant a *book*, not currency — see §6).

### 4.4 Idempotency (mandatory on every write)
Every `spend`/`grant` carries a caller-generated `idempotencyKey`. The economy stores processed keys (`idempotency/{key}` → the original result) and **replays the identical response** on a repeat — so a network retry, double-tap, or saga re-run can never double-charge or double-grant. (This is the exact `get/record_idempotent_response` pattern already in the backend.) Keys are unique per logical action (e.g. one per purchase attempt, one per league-week reward).

### 4.5 Errors (stable codes)
`INSUFFICIENT_FUNDS` · `INVALID_AMOUNT` · `UNKNOWN_CURRENCY` · `USER_MISMATCH` (403) · `RATE_LIMITED` · `WALLET_LOCKED`. All 4xx are safe to surface; 5xx → caller retries with the **same** idempotency key.

---

## 5. Purchase flow (buy a book with currency) — the saga

Because money and books live in different services, a purchase is a 2-step saga the **bookstore orchestrates**, made safe by idempotency:

```
1. User taps "Get book" (price: 1500 coins).
2. Bookstore → POST /economy/spend  {idempotencyKey: K, ...}
     ├─ 200 ok        → go to 3
     └─ 409 INSUFFICIENT_FUNDS → show "earn 600 more coins" (no entitlement). DONE.
3. Bookstore writes entitlement  entitlements/{userId}/books/{sku}
     ├─ success       → unlock the book in the reader. DONE.
     └─ write fails   → COMPENSATE: POST /economy/grant {refund, idempotencyKey: K+"_refund"}
                        → book not granted, coins returned. DONE.
4. Reconciliation sweep (daily, bookstore): for any spend with reason=store_purchase
   that has no matching entitlement and no refund → refund or grant the book. Closes
   any gap from a crash between steps 2 and 3.
```

This gives **clean ownership** (bookstore fully owns entitlements) with **no "money taken, no book"** outcome. Idempotency keys make every step safe to retry.

*(Simpler alternative if both teams prefer it: an atomic `POST /economy/redeem {userId, sku, currency, amount}` in the economy service that deducts **and** records the entitlement in one transaction. Correct and simpler, but couples the economy service to entitlements. Recommended only if the bookstore can't own a reconciliation job. **Default recommendation: the saga above.**)*

---

## 6. Reward flow (competition → currency → books)

The leaderboard pays out **spendable currency**, which funds the store — the loop that makes competing feel materially rewarding:

- League promotion / weekly top-3 → `grant(coins)` + sometimes `grant(gems)`.
- Season champion → `grant(gems)` + a cosmetic.
- Rating milestone (e.g. reach Master) → `grant(gems)`.
- **Milestone book gift** ("win Gold league → free book"): the leaderboard tells the bookstore to grant a *specific book entitlement* (not currency) via a `POST /store/gift {userId, sku, reason, idempotencyKey}` the bookstore exposes. The book lands in the library for free.

Rule preserved throughout: **you can earn the currency that buys books by competing, but you can never buy rank or rating.** Books are content, not power.

---

## 7. Pricing & economy balance (decide the ratios *now*)

A currency is only motivating if it's scarce enough to matter. Lock the earn↔price ratio early, before coins flood in.

**Earn-rate baseline (target, tune with telemetry):**
- Solid daily session ≈ 100–200 coins · daily contest ≈ 50–300 · daily login/streak ≈ 20–60.
- A committed kid earns ≈ **1,000–1,500 coins/week** and **1–3 gems/week** (gems only from achievements/wins).

**Price the store against that:**

| Item | Currency | Price (target) | So it feels like… |
|---|---|---|---|
| Cosmetic (common) | Coins | 200–600 | a few days |
| **Common book** | **Coins** | **1,500–3,000** | ~1–2 weeks of real effort |
| **Premium / gated book** | **Gems** | **5–10 gems** | a month of strong play *(a trophy)* |
| Premium book (alt path) | **Money** | ₹ direct | parents who'd rather buy |
| Achievement-locked book | Gems + a milestone | "unlock at Master" | prestige |

**Guardrails:**
- **No hyperinflation.** Earn rates conservative *now*; a common book ≈ ~2 weeks of effort. If you flood coins first, books become trivial or you nerf later (which feels awful to kids).
- **Sink ≥ source over time.** Track coins *minted* vs *spent* on an economy dashboard from day one; if minting outruns sinks, raise prices or add sinks, don't inflate.
- **No pay-to-win.** Money may buy books and cosmetics (and optionally Gems, since Gems only buy content/cosmetics) — **never LP, Rating, or any competitive advantage.**
- **Prefer pricing + good sinks over coin decay.** Decay/expiry feels punitive to children; the bookstore *is* the sink that keeps coins valuable.
- **Refunds & gifting** go through the same idempotent `grant`/`gift`, never a manual balance edit.

---

## 8. Data model (Firestore)

```
wallets/{userId}                 { coins, gems, version, updatedAt }
wallet_txns/{txnId}              { userId, currency, delta, reason, sku?, idempotencyKey, balanceAfter, ts }
idempotency/{key}                { result, ts }                         (economy)
catalog/{sku}                    { title, tier, priceCoins?, priceGems?, priceMoney?, ageBand, ... }  (bookstore)
entitlements/{userId}/books/{sku}{ grantedAt, via: "coins|gems|money|gift", txnId? }                  (bookstore)
```

Economy owns the first three; bookstore owns the last two. The only shared key is `userId` (+ `sku` referenced by a spend's `reason`/`sku` for audit).

---

## 9. Security & anti-abuse
- **Server-authoritative** balances — the client display is never trusted for a spend; the server re-reads.
- **Idempotent** writes — no double-charge / double-grant under retries or double-taps.
- **`assert_user_match`** on user calls; **service token** (`actingFor`) on bookstore→economy calls.
- **Rate-limit** spend/grant per user; flag anomalies (impossible earn velocity) for review.
- **Full ledger** (`wallet_txns`) — every coin is traceable; required once real money + real value exist.
- **No client-minted currency.** All `grant`s originate server-side from a known `reason`.

---

## 10. The flywheel (why this matters)
```
   Leaderboard / Contests ──earn──▶ Coins & Gems ──spend──▶ Books (the store)
            ▲                                                      │
            └──────────────── more learning ◀────read──────────────┘
```
Engagement funds the economy; the economy buys real educational content; content drives more learning and more engagement. The store is the **sink that gives every coin a purpose** — without it, the currencies are points with nowhere to go.

---

## 11. Integration checklist (for the bookstore/reader space)
- [ ] Build against `GET /wallet`, `POST /spend`, `POST /grant` (§4) — never write balances directly.
- [ ] Generate a unique `idempotencyKey` per purchase attempt; reuse it on retry.
- [ ] Implement the purchase **saga** (§5) — spend → entitlement → compensating refund on failure.
- [ ] Run the daily **reconciliation** sweep (spend-without-entitlement → refund or grant).
- [ ] Expose `POST /store/gift {userId, sku, reason, idempotencyKey}` for milestone book gifts (§6).
- [ ] Own `catalog` + `entitlements`; reference `sku` in spend `reason` for audit.
- [ ] Agree the **price ratios** (§7) jointly before launch; instrument minted-vs-spent.

## 12. Open questions to align on (both spaces)
1. Real-money rail (App Store / Play billing vs a payments provider) — who owns it, and does money ever top up Gems, or only buy books/cosmetics directly?
2. Family/multi-child wallets — one wallet per child, or a parent purse that gifts down?
3. Gifting/sharing books between clanmates — in scope?
4. Refund policy for money purchases (store-credit in Gems vs money back).
5. Offline reading entitlement checks (the reader must verify ownership offline).
