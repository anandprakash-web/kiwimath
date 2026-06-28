"""
Store catalog + per-user entitlements (ownership = the source of truth).

The catalog JSON shape matches KiwiReader's `CatalogBook.toJson()` so the app's
`CatalogProvider` can deserialize it directly. Entitlements are persisted per
user in `FirestoreBackedStore` and exposed as owned-ids so the app reconciles
ownership on launch (closes AUDIT O1's "reconcile on launch").

MVP: the catalog is a seeded list (same 5 books as the app's dev spike). Later
this comes from an ingestion pipeline (upload EPUB/PDF/HTML → GCS + a row here).
A book with **no pricing** is school-issued → treated as owned by everyone.
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.state_store import FirestoreBackedStore

_ent = FirestoreBackedStore("store_entitlements")  # user -> {bookId: {via, at}}

# Where real book files live (baked into the image by deploy.sh, or local).
def _books_dir() -> Path:
    env = os.environ.get("KIWIMATH_BOOKS_DIR")
    if env:
        return Path(env)
    return (Path(__file__).resolve().parents[3] / "content-books")

# bookId -> on-disk file + format + cover (served by /v3/store/content/*).
_BOOK_FILES: Dict[str, Dict[str, str]] = {
    "euclids-garden": {"file": "euclids-garden/EuclidsGarden_Mobile.html", "format": "html",
                       "cover": "euclids-garden/cover.png"},
    # IOQM 2026 four pillars — faithful page renders (questions unchanged) +
    # interactive shell (contents, tap-to-reveal video & solutions).
    "geometry-ioqm": {"file": "geometry-ioqm/EuclidGeometry_IOQM.html", "format": "html"},
    "algebra-ioqm": {"file": "algebra-ioqm/algebra-ioqm.html", "format": "html"},
    "combinatorics-ioqm": {"file": "combinatorics-ioqm/combinatorics-ioqm.html", "format": "html"},
    "numbertheory-ioqm": {"file": "numbertheory-ioqm/numbertheory-ioqm.html", "format": "html"},
    # K-2 interactive workbook — 13 worksheets, faithful slides + tap/type-to-check.
    "number-sense": {"file": "number-sense/number-sense.html", "format": "html"},
    # Vedantu grade-course workbooks — faithful session-assignment renders + solutions.
    "g34-workbook": {"file": "g34-workbook/g34-workbook.html", "format": "html"},
    "g56-workbook": {"file": "g56-workbook/g56-workbook.html", "format": "html"},
    # Original authored teaching books (Socratic, Bloom's, SVG figures, Kangaroo + Vedic).
    "l2-mathbook": {"file": "l2-mathbook/l2-mathbook.html", "format": "html"},
    "l3-mathbook": {"file": "l3-mathbook/l3-mathbook.html", "format": "html"},
    # Vedantu academic library — grade-aligned (L4 Grade7-8 / L5 IOQM / L6 RMO).
    "l4-algebra": {"file": "l4-algebra/l4-algebra.html", "format": "html"},
    "l4-arithmetic": {"file": "l4-arithmetic/l4-arithmetic.html", "format": "html"},
    "l4-combinatorics": {"file": "l4-combinatorics/l4-combinatorics.html", "format": "html"},
    "l4-geometry": {"file": "l4-geometry/l4-geometry.html", "format": "html"},
    "l4-numbertheory": {"file": "l4-numbertheory/l4-numbertheory.html", "format": "html"},
    "l5-algebra": {"file": "l5-algebra/l5-algebra.html", "format": "html"},
    "l5-basicmaths": {"file": "l5-basicmaths/l5-basicmaths.html", "format": "html"},
    "l5-combinatorics": {"file": "l5-combinatorics/l5-combinatorics.html", "format": "html"},
    "l5-geometry": {"file": "l5-geometry/l5-geometry.html", "format": "html"},
    "l5-numbertheory": {"file": "l5-numbertheory/l5-numbertheory.html", "format": "html"},
    "l5-trigonometry": {"file": "l5-trigonometry/l5-trigonometry.html", "format": "html"},
    "l6-algebra": {"file": "l6-algebra/l6-algebra.html", "format": "html"},
    "l6-basicmaths": {"file": "l6-basicmaths/l6-basicmaths.html", "format": "html"},
    "l6-combinatorics": {"file": "l6-combinatorics/l6-combinatorics.html", "format": "html"},
    "l6-geometry": {"file": "l6-geometry/l6-geometry.html", "format": "html"},
    "l6-numbertheory": {"file": "l6-numbertheory/l6-numbertheory.html", "format": "html"},
}

# MVP store model: every book is FREE ({isFree:true}) but must be *purchased*
# (claimed) before it can be downloaded — nothing is auto-owned. Real prices
# come in phase 2 by swapping isFree for coins/amountMinor.
_FREE = {"isFree": True}
_CATALOG: List[Dict[str, Any]] = [
    {"id": "euclids-garden", "title": "Euclid's Garden", "author": "Anand Prakash",
     "subtitle": "A Journey Through Geometry", "format": "html",
     "contentVersion": "v1", "byteSize": 1926329,
     "subject": "Geometry", "levels": [3, 4, 5, 6, 7], "gradeBand": "6–10",
     "pricing": _FREE},
    {"id": "geometry-ioqm", "title": "IOQM 2026 · Geometry", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 12567315,
     "subject": "Geometry", "levels": [5, 6, 7], "gradeBand": "8–10",
     "pricing": _FREE},
    {"id": "algebra-ioqm", "title": "IOQM 2026 · Algebra", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 8884125,
     "subject": "Algebra", "levels": [5, 6, 7], "gradeBand": "8–10",
     "pricing": _FREE},
    {"id": "combinatorics-ioqm", "title": "IOQM 2026 · Combinatorics", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 6551394,
     "subject": "Combinatorics", "levels": [5, 6, 7], "gradeBand": "8–10",
     "pricing": _FREE},
    {"id": "numbertheory-ioqm", "title": "IOQM 2026 · Number Theory", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 6135455,
     "subject": "Number Theory", "levels": [5, 6, 7], "gradeBand": "8–10",
     "pricing": _FREE},
    {"id": "number-sense", "title": "Number Sense & Operations", "author": "Vedantu",
     "subtitle": "Count, compare, add & subtract — interactive", "format": "html",
     "contentVersion": "v1", "byteSize": 25745637,
     "subject": "Number Sense", "levels": [1], "gradeBand": "K–2",
     "pricing": _FREE},
    {"id": "l2-mathbook", "title": "Kiwi's Grand Math Adventure", "author": "VOS",
     "subtitle": "Learn it all — Grades 3–4, with a Kangaroo Corner", "format": "html",
     "contentVersion": "v1", "byteSize": 552987,
     "subject": "Math Book", "levels": [2], "gradeBand": "3–4",
     "pricing": _FREE},
    {"id": "l3-mathbook", "title": "Kiwi's Math Expedition", "author": "VOS",
     "subtitle": "Grades 5–6 — integers to Olympiad, with Vedic speed tricks & a Kangaroo Corner", "format": "html",
     "contentVersion": "v1", "byteSize": 733941,
     "subject": "Math Book", "levels": [3], "gradeBand": "5–6",
     "pricing": _FREE},
    {"id": "g34-workbook", "title": "Grade 3–4 Olympiad Workbook", "author": "Vedantu",
     "subtitle": "Full course — assignments & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 12532200,
     "subject": "Olympiad Workbook", "levels": [2], "gradeBand": "3–4",
     "pricing": _FREE},
    {"id": "g56-workbook", "title": "Grade 5–6 Olympiad Workbook", "author": "Vedantu",
     "subtitle": "Full course — assignments & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 14169791,
     "subject": "Olympiad Workbook", "levels": [3], "gradeBand": "5–6",
     "pricing": _FREE},
    {"id": "l4-algebra", "title": "Grade 7–8 · Algebra", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 7937620,
     "subject": "Algebra", "levels": [4], "gradeBand": "7–8",
     "pricing": _FREE},
    {"id": "l4-arithmetic", "title": "Grade 7–8 · Arithmetic", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 1450698,
     "subject": "Arithmetic", "levels": [4], "gradeBand": "7–8",
     "pricing": _FREE},
    {"id": "l4-combinatorics", "title": "Grade 7–8 · Combinatorics", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 1671091,
     "subject": "Combinatorics", "levels": [4], "gradeBand": "7–8",
     "pricing": _FREE},
    {"id": "l4-geometry", "title": "Grade 7–8 · Geometry", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 7657866,
     "subject": "Geometry", "levels": [4], "gradeBand": "7–8",
     "pricing": _FREE},
    {"id": "l4-numbertheory", "title": "Grade 7–8 · Number Theory", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 6429676,
     "subject": "Number Theory", "levels": [4], "gradeBand": "7–8",
     "pricing": _FREE},
    {"id": "l5-algebra", "title": "IOQM · Algebra", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 5422122,
     "subject": "Algebra", "levels": [5], "gradeBand": "9–10",
     "pricing": _FREE},
    {"id": "l5-basicmaths", "title": "IOQM · Basic Mathematics", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 1531759,
     "subject": "Basic Mathematics", "levels": [5], "gradeBand": "9–10",
     "pricing": _FREE},
    {"id": "l5-combinatorics", "title": "IOQM · Combinatorics", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 3492951,
     "subject": "Combinatorics", "levels": [5], "gradeBand": "9–10",
     "pricing": _FREE},
    {"id": "l5-geometry", "title": "IOQM · Geometry", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 9979228,
     "subject": "Geometry", "levels": [5], "gradeBand": "9–10",
     "pricing": _FREE},
    {"id": "l5-numbertheory", "title": "IOQM · Number Theory", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 5064256,
     "subject": "Number Theory", "levels": [5], "gradeBand": "9–10",
     "pricing": _FREE},
    {"id": "l5-trigonometry", "title": "IOQM · Trigonometry", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 3148140,
     "subject": "Trigonometry", "levels": [5], "gradeBand": "9–10",
     "pricing": _FREE},
    {"id": "l6-algebra", "title": "RMO · Algebra", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 12490851,
     "subject": "Algebra", "levels": [6], "gradeBand": "9–11",
     "pricing": _FREE},
    {"id": "l6-basicmaths", "title": "RMO · Basic Mathematics", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 2025731,
     "subject": "Basic Mathematics", "levels": [6], "gradeBand": "9–11",
     "pricing": _FREE},
    {"id": "l6-combinatorics", "title": "RMO · Combinatorics", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 11352476,
     "subject": "Combinatorics", "levels": [6], "gradeBand": "9–11",
     "pricing": _FREE},
    {"id": "l6-geometry", "title": "RMO · Geometry", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 20130044,
     "subject": "Geometry", "levels": [6], "gradeBand": "9–11",
     "pricing": _FREE},
    {"id": "l6-numbertheory", "title": "RMO · Number Theory", "author": "Vedantu",
     "subtitle": "Assignments, video & worked solutions", "format": "html",
     "contentVersion": "v1", "byteSize": 9415918,
     "subject": "Number Theory", "levels": [6], "gradeBand": "9–11",
     "pricing": _FREE},
]
_BY_ID = {b["id"]: b for b in _CATALOG}
# Books with no pricing are school-issued → auto-owned by everyone (but a
# coming-soon title has no content, so it is never auto-owned/ownable).
_AUTO_OWNED = [b["id"] for b in _CATALOG
               if "pricing" not in b and not b.get("comingSoon")]


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class StoreService:
    def catalog(self) -> List[Dict[str, Any]]:
        return _CATALOG

    def book(self, book_id: str) -> Optional[Dict[str, Any]]:
        return _BY_ID.get(book_id)

    def pricing(self, book_id: str) -> Dict[str, Any]:
        return (_BY_ID.get(book_id) or {}).get("pricing") or {}

    def coin_price(self, book_id: str) -> Optional[int]:
        return self.pricing(book_id).get("coins")

    def is_coming_soon(self, book_id: str) -> bool:
        return bool((_BY_ID.get(book_id) or {}).get("comingSoon"))

    def is_free(self, book_id: str) -> bool:
        b = _BY_ID.get(book_id)
        if b is None or b.get("comingSoon"):
            return False  # a coming-soon title has no content → never free/ownable
        return ("pricing" not in b) or bool(self.pricing(book_id).get("isFree"))

    # ---- entitlements ----
    def owned_ids(self, user_id: str) -> List[str]:
        doc = _ent.get(user_id) or {}
        return sorted(set(list(doc.keys()) + _AUTO_OWNED))

    def is_owned(self, user_id: str, book_id: str) -> bool:
        return book_id in self.owned_ids(user_id)

    def own(self, user_id: str, book_id: str, via: str) -> bool:
        """Record ownership. Idempotent — never overwrites an existing record
        (so via/acquiredAt are stable). Returns True if newly granted."""
        if book_id in _AUTO_OWNED or self.is_coming_soon(book_id):
            return False  # coming-soon titles can't be owned (no content yet)
        doc = _ent.get(user_id) or {}
        if book_id in doc:
            return False
        doc[book_id] = {"via": via, "at": _now()}
        _ent.set(user_id, doc)
        return True

    # ---- real book files (served by /v3/store/content/*) ----
    def has_file(self, book_id: str) -> bool:
        return book_id in _BOOK_FILES

    def file_format(self, book_id: str) -> Optional[str]:
        rec = _BOOK_FILES.get(book_id)
        return rec.get("format") if rec else None

    def file_path(self, book_id: str) -> Optional[Path]:
        rec = _BOOK_FILES.get(book_id)
        if not rec:
            return None
        p = _books_dir() / rec["file"]
        return p if p.exists() else None

    def cover_path(self, book_id: str) -> Optional[Path]:
        rec = _BOOK_FILES.get(book_id)
        if not rec or "cover" not in rec:
            return None
        p = _books_dir() / rec["cover"]
        return p if p.exists() else None


store = StoreService()
