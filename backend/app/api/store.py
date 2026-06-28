"""
v3 Store + Economy API — the backend behind KiwiReader's host seams.

    GET  /v3/store/catalog                      → CatalogBook list (+ pricing)
    GET  /v3/store/entitlements?user_id=        → owned book ids (source of truth)
    GET  /v3/economy/wallet?user_id=            → { coins, gems }
    POST /v3/economy/spend                      → server-authoritative, idempotent
                                                   (reason=unlock_book → records the entitlement)
    POST /v3/store/claim                        → claim a FREE book (validated)
    POST /v3/economy/grant                      → credit / book gift (admin / internal cron)

Auth: router is under the shared verify_token; user_id endpoints add
assert_user_match (a student only touches their own wallet / library).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.auth import assert_user_match, is_admin, verify_token
from app.services.economy_service import economy
from app.services.store_service import store

router = APIRouter(prefix="/v3", tags=["v3-store"])

_MEDIA = {"epub": "application/epub+zip", "pdf": "application/pdf", "html": "text/html"}


def _uid(decoded: Dict[str, Any]) -> str:
    return decoded.get("uid") or decoded.get("user_id") or ""


@router.get("/store/catalog")
def store_catalog(decoded: Dict[str, Any] = Depends(verify_token)):
    return {"books": store.catalog()}


@router.get("/store/entitlements")
def store_entitlements(user_id: str = Query(...), decoded: Dict[str, Any] = Depends(verify_token)):
    assert_user_match(decoded, user_id)
    return {"userId": user_id, "owned": store.owned_ids(user_id)}


@router.get("/economy/wallet")
def economy_wallet(user_id: str = Query(...), decoded: Dict[str, Any] = Depends(verify_token)):
    assert_user_match(decoded, user_id)
    return economy.wallet(user_id)


class SpendBody(BaseModel):
    user_id: str
    currency: str = "coins"
    amount: int
    sku: Optional[str] = None
    reason: str = "spend"
    idempotency_key: Optional[str] = None


@router.post("/economy/spend")
def economy_spend(body: SpendBody, decoded: Dict[str, Any] = Depends(verify_token)):
    assert_user_match(decoded, body.user_id)
    # If unlocking a book, enforce currency + the catalog's coin price (don't
    # trust the client — otherwise a 300-coin book could be paid with 300 gems).
    if body.reason == "unlock_book" and body.sku:
        if body.currency != "coins":
            raise HTTPException(400, "Books are unlocked with coins.")
        price = store.coin_price(body.sku)
        if price is None:
            raise HTTPException(400, "This book can't be unlocked with coins.")
        if int(body.amount) != int(price):
            raise HTTPException(400, "Price mismatch.")
    return economy.spend(body.user_id, body.currency, int(body.amount),
                         sku=body.sku, reason=body.reason, idempotency_key=body.idempotency_key)


class ClaimBody(BaseModel):
    user_id: str
    book_id: str


@router.post("/store/claim")
def store_claim(body: ClaimBody, decoded: Dict[str, Any] = Depends(verify_token)):
    assert_user_match(decoded, body.user_id)
    res = economy.claim_free(body.user_id, body.book_id)
    if not res.get("ok"):
        raise HTTPException(400, res.get("error", "cannot_claim"))
    return res


class GrantBody(BaseModel):
    user_id: str
    currency: Optional[str] = None
    amount: int = 0
    sku: Optional[str] = None
    reason: str = "grant"
    idempotency_key: Optional[str] = None


@router.post("/economy/grant")
def economy_grant(body: GrantBody, decoded: Dict[str, Any] = Depends(verify_token)):
    # Credits coins/gems or gifts a book — only the cron / admin / dev may call it,
    # never a normal user (they can't grant themselves currency or books).
    if not (decoded.get("internal") or decoded.get("dev_mode") or is_admin(decoded)):
        raise HTTPException(403, "Forbidden: admin or internal only")
    return economy.grant(body.user_id, currency=body.currency, amount=int(body.amount),
                         sku=body.sku, reason=body.reason, idempotency_key=body.idempotency_key)


# ---- real book content (KiwiReader's ContentProvider seam) ------------------
# manifest + bytes are entitlement-gated (only an owner can read a book); the
# cover is open to any signed-in user so it can show in the Store before buying.

@router.get("/store/content/{book_id}/manifest")
def content_manifest(book_id: str, decoded: Dict[str, Any] = Depends(verify_token)):
    book = store.book(book_id)
    if book is None or not store.has_file(book_id):
        raise HTTPException(404, "No such book content.")
    if not store.is_owned(_uid(decoded), book_id):
        raise HTTPException(403, "You don't own this book.")
    return {
        "id": book_id,
        "format": store.file_format(book_id),
        "contentVersion": book.get("contentVersion", "v1"),
        "sections": [],                       # EPUB/PDF carry their own spine/pages
        "title": book.get("title"),
    }


@router.get("/store/content/{book_id}/bytes")
def content_bytes(book_id: str, decoded: Dict[str, Any] = Depends(verify_token)):
    if not store.has_file(book_id):
        raise HTTPException(404, "No such book content.")
    if not store.is_owned(_uid(decoded), book_id):
        raise HTTPException(403, "You don't own this book.")
    path = store.file_path(book_id)
    if path is None:
        raise HTTPException(404, "Book file missing.")
    media = _MEDIA.get(store.file_format(book_id) or "", "application/octet-stream")
    return FileResponse(str(path), media_type=media, filename=path.name)  # supports Range


@router.get("/store/content/{book_id}/cover")
def content_cover(book_id: str, decoded: Dict[str, Any] = Depends(verify_token)):
    path = store.cover_path(book_id)
    if path is None:
        raise HTTPException(404, "No cover.")
    return FileResponse(str(path), media_type="image/png", filename=path.name)
