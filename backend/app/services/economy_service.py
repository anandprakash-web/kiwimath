"""
Economy — the coin/gem bridge the Store spends through.

Server-authoritative, idempotent wallet operations on top of `gamification`
(which owns the balances). This is exactly the `spend`/`grant`/`getBalance` of
KIWIMATH_ECONOMY_STORE_CONTRACT.md and the backing of KiwiReader's `CoinWallet`
seam.

  - `spend(reason='unlock_book', sku=bookId)` debits **and atomically records the
    book entitlement** (AUDIT O1: owns-at-debit), so ownership reconciles on
    launch even if the device write is lost.
  - every write is idempotent on `idempotencyKey` (replays the same response) and
    appended to a txn ledger for audit.
"""

from __future__ import annotations

import datetime
import threading
import uuid
from collections import defaultdict
from typing import Any, Dict, Optional

from app.services.state_store import FirestoreBackedStore
from app.services.gamification import gamification
from app.services.store_service import store

_idem = FirestoreBackedStore("economy_idem")   # idempotencyKey -> result
_txn = FirestoreBackedStore("economy_txn")      # txnId -> ledger row
# Per-user in-instance serialization of spends. Narrows the double-charge window
# to the cross-instance case; full safety needs a Firestore transaction on the
# debit (tracked: real-money hardening, Phase 2). The currency is virtual.
_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class EconomyService:
    def wallet(self, user_id: str) -> Dict[str, Any]:
        st = gamification.get_state(user_id)
        return {"userId": user_id, "coins": int(st.kiwi_coins), "gems": int(st.gems)}

    def spend(self, user_id: str, currency: str, amount: int,
              sku: Optional[str] = None, reason: str = "spend",
              idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        with _locks[user_id]:
            if idempotency_key:
                cached = _idem.get(idempotency_key)
                if cached is not None:
                    return {**cached, "replayed": True}

            ok, bal, err = gamification.spend(user_id, currency, int(amount))
            resp: Dict[str, Any] = {"ok": ok, "currency": currency,
                                    "newBalance": bal, "replayed": False}
            if not ok:
                resp["error"] = err            # insufficient / invalid_amount — NOT cached,
                return resp                     # so a later retry (after earning) can succeed.

            # O1 — record ownership at the moment of debit. Only for a real,
            # coin-priced catalog book (no arbitrary/non-catalog ownership writes).
            if reason == "unlock_book" and sku and store.book(sku):
                store.own(user_id, sku, "coins")
                resp["bookOwned"] = sku
            txn_id = "t_" + uuid.uuid4().hex[:12]
            _txn.set(txn_id, {"userId": user_id, "currency": currency, "delta": -int(amount),
                              "reason": reason, "sku": sku, "balanceAfter": bal, "ts": _now()})
            resp["txnId"] = txn_id

            if idempotency_key:
                _idem.set(idempotency_key, resp)
            return resp

    def grant(self, user_id: str, currency: Optional[str] = None, amount: int = 0,
              sku: Optional[str] = None, reason: str = "grant",
              idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """Credit currency and/or grant a book entitlement (leaderboard milestone
        gifts, refunds, promos). Idempotent."""
        if idempotency_key:
            cached = _idem.get(idempotency_key)
            if cached is not None:
                return {**cached, "replayed": True}

        resp: Dict[str, Any] = {"ok": True, "replayed": False}
        if currency and amount and int(amount) > 0:
            resp["currency"] = currency
            resp["newBalance"] = gamification.grant(user_id, currency, int(amount))
        if sku:
            resp["bookGranted"] = sku if store.own(user_id, sku, "granted") else None
        txn_id = "t_" + uuid.uuid4().hex[:12]
        _txn.set(txn_id, {"userId": user_id, "currency": currency, "delta": int(amount or 0),
                          "reason": reason, "sku": sku, "ts": _now()})
        resp["txnId"] = txn_id

        if idempotency_key:
            _idem.set(idempotency_key, resp)
        return resp

    def claim_free(self, user_id: str, book_id: str) -> Dict[str, Any]:
        """Record ownership of a FREE / school-issued book (user-allowed; the
        backend validates the book is actually free, so a paid book can't be
        claimed without paying)."""
        if not store.is_free(book_id):
            return {"ok": False, "error": "not_free"}
        granted = store.own(user_id, book_id, "free")
        return {"ok": True, "bookOwned": book_id, "newlyGranted": granted}


economy = EconomyService()
