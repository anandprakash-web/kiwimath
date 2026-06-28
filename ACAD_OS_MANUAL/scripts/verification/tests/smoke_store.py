"""Smoke test — Store MVP: free books, PURCHASE-before-download, entitlements, auth.

Model: every book is free but must be *claimed* (purchased) before its content
can be downloaded; nothing is auto-owned. The content endpoints enforce that
server-side, so a trial user only downloads what they've added to their library.
"""
import os
os.environ["KIWIMATH_AUTH_DISABLED"] = "1"
os.environ.setdefault("KIWIMATH_OLYMPIAD_CONTENT_DIR", os.path.abspath("../content-live/olympiad"))
os.environ.setdefault("KIWIMATH_CURRICULUM_CONTENT_DIR", os.path.abspath("../content-live/curriculum"))
os.environ.setdefault("KIWIMATH_BOOKS_DIR", os.path.abspath("../content-books"))

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.core.auth import verify_token
from app.core import auth
from app.api.store import router as store_router

app = FastAPI(); app.include_router(store_router, dependencies=[Depends(verify_token)])
c = TestClient(app)
fails = []
def P(ok, msg):
    print(("[PASS] " if ok else "[FAIL] ") + msg)
    if not ok: fails.append(msg)

U = "dev-local"  # uid the disabled-auth dev identity returns (so content gating aligns)
PILLARS = ["geometry-ioqm", "algebra-ioqm", "combinatorics-ioqm", "numbertheory-ioqm"]
def wallet(): return c.get(f"/v3/economy/wallet?user_id={U}").json()
def owned(): return set(c.get(f"/v3/store/entitlements?user_id={U}").json()["owned"])

# 1) catalog — exactly 5 real books, all free, no dummies / coming-soon
cat = c.get("/v3/store/catalog").json()["books"]
ids = {b["id"] for b in cat}
P(len(cat) == 26, f"catalog lists {len(cat)} books (6 + 16 pillar + 2 workbooks + L2/L3 math books)")
P(all(p in ids for p in PILLARS) and "euclids-garden" in ids and "number-sense" in ids,
  "catalog = Euclid's Garden + 4 IOQM pillars + Number Sense")
P({"l5-numbertheory", "l4-algebra", "l6-geometry", "l5-trigonometry"} <= ids,
  "catalog includes the 16 grade-aligned Vedantu books (L4/L5/L6)")
P(all((b.get("pricing") or {}).get("isFree") for b in cat), "every book is free (isFree=true)")
P(not any(b.get("comingSoon") for b in cat), "no coming-soon placeholders")
P(all(b["format"] == "html" for b in cat if b["id"] in PILLARS), "the 4 pillars are html")

# 2) nothing is auto-owned — a fresh user owns nothing until they purchase
P(owned() == set(), "fresh user owns nothing (no auto-owned books)")

# 3) PURCHASE-BEFORE-DOWNLOAD — content is blocked until the book is claimed
pre = c.get("/v3/store/content/geometry-ioqm/bytes")
P(pre.status_code == 403, "content blocked before purchase (403)")
cl = c.post("/v3/store/claim", json={"user_id": U, "book_id": "geometry-ioqm"}).json()
P(cl.get("ok") and "geometry-ioqm" in owned(), "purchase (free claim) -> owned")
man = c.get("/v3/store/content/geometry-ioqm/manifest")
P(man.status_code == 200 and man.json()["format"] == "html", "after purchase: manifest 200 (html)")
by = c.get("/v3/store/content/geometry-ioqm/bytes")
P(by.status_code == 200 and by.headers["content-type"].startswith("text/html") and len(by.content) > 5_000_000,
  f"after purchase: bytes 200 html ({len(by.content)} B)")
P(b"Video solutions" in by.content and b"youtu" in by.content and b"scrollIntoView" in by.content,
  "book carries interactive shell (video links + working contents nav)")

# 4) all 4 pillars purchasable + downloadable
for p in PILLARS:
    c.post("/v3/store/claim", json={"user_id": U, "book_id": p})
P(all(p in owned() for p in PILLARS), "all 4 pillars purchasable")
ok_all = True
for p in PILLARS:
    r = c.get(f"/v3/store/content/{p}/bytes")
    if r.status_code != 200 or len(r.content) < 1_000_000:
        ok_all = False
P(ok_all, "all 4 pillar books download (>1MB each)")

# 5) wallet still works (grant + balance); insufficient spend rejected
c.post("/v3/economy/grant", json={"user_id": U, "currency": "coins", "amount": 500,
       "reason": "test_seed", "idempotency_key": "seed1"})
P(wallet()["coins"] == 500, "wallet grant works")
ins = c.post("/v3/economy/spend", json={"user_id": U, "currency": "coins", "amount": 99999,
             "reason": "spend", "idempotency_key": "k_ins"}).json()
P(ins["ok"] is False and wallet()["coins"] == 500, "insufficient spend -> rejected, no deduction")

# 6) unknown book content -> 404
P(c.get("/v3/store/content/no-such-book/bytes").status_code == 404, "unknown book content -> 404")

# 7) AUTH — a normal (non-dev) user can't touch another's wallet/library, nor grant
app2 = FastAPI(); app2.include_router(store_router)
app2.dependency_overrides[auth.verify_token] = lambda: {"uid": "userA"}
c2 = TestClient(app2)
P(c2.get("/v3/economy/wallet?user_id=userA").status_code == 200, "auth: own wallet -> 200")
P(c2.get("/v3/economy/wallet?user_id=userB").status_code == 403, "auth: other's wallet -> 403")
P(c2.get("/v3/store/entitlements?user_id=userB").status_code == 403, "auth: other's library -> 403")
P(c2.post("/v3/economy/grant", json={"user_id": "userA", "currency": "coins", "amount": 999}).status_code == 403, "auth: normal user can't grant -> 403")

print("\nDONE" if not fails else f"\nFAILURES ({len(fails)}): {fails}")
import sys; sys.exit(1 if fails else 0)
