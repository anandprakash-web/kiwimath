"""
NCERT Content Store — loads NCERT curriculum questions and provides lookup.

Loads all questions from grade1/ through grade6/ JSON files at startup,
indexed by question ID for O(1) lookup by the assessment engine.

Usage:
    from app.services.ncert_content_store import ncert_store, init_ncert_store

    # At startup:
    init_ncert_store()

    # Per-request:
    question = ncert_store.get_question("NCERT-G1-042")
    batch = ncert_store.get_questions(["NCERT-G1-001", "NCERT-G2-010"])
    filtered = ncert_store.get_questions_by_domain("numbers", grade=2, limit=10)
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kiwimath.ncert_content_store")

# Default path — overridable via env var NCERT_CONTENT_DIR
_DEFAULT_CONTENT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "content-v2" / "ncert-curriculum"


class NcertContentStore:
    """In-memory store for NCERT curriculum questions."""

    def __init__(self, content_dir: Optional[str | Path] = None):
        self._content_dir = Path(content_dir) if content_dir else _get_content_dir()
        # Primary index: item_id -> full question dict
        self._questions: Dict[str, Dict[str, Any]] = {}
        # Secondary indices
        self._by_domain: Dict[str, List[str]] = {}  # domain -> [item_ids]
        self._by_grade: Dict[int, List[str]] = {}   # grade -> [item_ids]
        self._by_domain_grade: Dict[str, List[str]] = {}  # "domain:grade" -> [item_ids]

    @property
    def total_questions(self) -> int:
        return len(self._questions)

    def load(self) -> None:
        """Load all NCERT questions from JSON files."""
        if not self._content_dir.exists():
            logger.warning(f"NCERT content dir not found: {self._content_dir}")
            return

        # Map of filename patterns for each grade
        grade_files = {
            1: "questions.json",
            2: "questions.json",
            3: "ncert_g3_questions.json",
            4: "ncert_g4_questions.json",
            5: "ncert_g5_questions.json",
            6: "ncert_g6_questions.json",
        }

        for grade_num in range(1, 7):
            grade_dir = self._content_dir / f"grade{grade_num}"
            if not grade_dir.exists():
                logger.debug(f"Grade dir not found: {grade_dir}")
                continue

            filename = grade_files[grade_num]
            json_path = grade_dir / filename
            if not json_path.exists():
                logger.debug(f"Questions file not found: {json_path}")
                continue

            self._load_grade_file(json_path, grade_num)

        logger.info(
            f"NCERT content store loaded: {self.total_questions} questions "
            f"across {len(self._by_grade)} grades, {len(self._by_domain)} domains"
        )

    def _load_grade_file(self, path: Path, grade: int) -> None:
        """Load a single grade's questions JSON."""
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load {path}: {e}")
            return

        questions = data.get("questions", [])
        for q in questions:
            item_id = q.get("id")
            if not item_id:
                continue

            # Enrich with grade info
            q["grade"] = grade

            # Extract domain from topic field (e.g. "ncert_g1_numbers" -> "numbers")
            domain = self._extract_domain(q.get("topic", ""), q.get("tags", []))
            q["domain"] = domain

            # Build visual URL path
            if q.get("visual_svg"):
                q["visual_url"] = f"/static/ncert/grade{grade}/visuals/{q['visual_svg']}"
            else:
                q["visual_url"] = None

            # Store in primary index
            self._questions[item_id] = q

            # Update secondary indices
            if domain not in self._by_domain:
                self._by_domain[domain] = []
            self._by_domain[domain].append(item_id)

            if grade not in self._by_grade:
                self._by_grade[grade] = []
            self._by_grade[grade].append(item_id)

            key = f"{domain}:{grade}"
            if key not in self._by_domain_grade:
                self._by_domain_grade[key] = []
            self._by_domain_grade[key].append(item_id)

    def _extract_domain(self, topic: str, tags: list) -> str:
        """Extract domain from topic string or tags.

        Topic patterns: 'ncert_g1_numbers', 'ncert_g3_geometry', etc.
        Falls back to tag-based detection.
        """
        # Try extracting from topic (last part after grade prefix)
        parts = topic.split("_")
        if len(parts) >= 3:
            domain_candidate = "_".join(parts[2:])  # e.g. "numbers", "place_value"
            return self._normalize_domain(domain_candidate)

        # Fallback: check tags
        domain_keywords = {
            "numbers": ["counting", "numbers", "number_sense", "place_value", "comparison"],
            "arithmetic": ["addition", "subtraction", "multiplication", "division", "operations"],
            "fractions": ["fractions", "decimals", "rational"],
            "geometry": ["geometry", "shapes", "symmetry", "spatial", "patterns"],
            "measurement": ["measurement", "length", "weight", "time", "money", "data"],
        }
        for domain, keywords in domain_keywords.items():
            if any(kw in tags for kw in keywords):
                return domain

        return "numbers"  # default

    def _normalize_domain(self, raw: str) -> str:
        """Normalize domain string to match assessment engine domains."""
        domain_map = {
            "numbers": "numbers",
            "number_sense": "numbers",
            "place_value": "numbers",
            "counting": "numbers",
            "arithmetic": "arithmetic",
            "addition": "arithmetic",
            "subtraction": "arithmetic",
            "multiplication": "arithmetic",
            "division": "arithmetic",
            "operations": "arithmetic",
            "fractions": "fractions",
            "decimals": "fractions",
            "geometry": "geometry",
            "shapes": "geometry",
            "symmetry": "geometry",
            "patterns": "geometry",
            "measurement": "measurement",
            "data_handling": "measurement",
            "time": "measurement",
            "money": "measurement",
            "length": "measurement",
            "weight": "measurement",
        }
        return domain_map.get(raw, "numbers")

    # --- Public API ---

    def get_question(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get full question data by ID."""
        return self._questions.get(item_id)

    def get_questions(self, item_ids: List[str]) -> List[Dict[str, Any]]:
        """Batch lookup by IDs. Returns list (preserves order, skips missing)."""
        results = []
        for item_id in item_ids:
            q = self._questions.get(item_id)
            if q:
                results.append(q)
        return results

    def get_questions_by_domain(
        self,
        domain: str,
        grade: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Filter questions by domain and optionally grade."""
        if grade is not None:
            key = f"{domain}:{grade}"
            item_ids = self._by_domain_grade.get(key, [])
        else:
            item_ids = self._by_domain.get(domain, [])

        if limit:
            item_ids = item_ids[:limit]

        return [self._questions[iid] for iid in item_ids if iid in self._questions]

    def get_question_content_for_response(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get question content formatted for API response to Flutter app."""
        q = self._questions.get(item_id)
        if not q:
            return None

        return {
            "stem": q.get("stem", ""),
            "choices": q.get("choices", []),
            "correct_answer": q.get("correct_answer"),
            "visual_svg": q.get("visual_svg"),
            "visual_url": q.get("visual_url"),
            "visual_alt": q.get("visual_alt", ""),
            "hint": q.get("hint", {}),
            "diagnostics": q.get("diagnostics", {}),
            "difficulty_tier": q.get("difficulty_tier", ""),
            "chapter": q.get("chapter", ""),
            "tags": q.get("tags", []),
        }

    def questions_by_grade(self) -> Dict[int, int]:
        """Return question count per grade."""
        return {g: len(ids) for g, ids in sorted(self._by_grade.items())}

    def questions_by_domain(self) -> Dict[str, int]:
        """Return question count per domain."""
        return {d: len(ids) for d, ids in sorted(self._by_domain.items())}

    def stats(self) -> Dict[str, Any]:
        """Return summary stats."""
        return {
            "total_questions": self.total_questions,
            "grades": sorted(self._by_grade.keys()),
            "domains": {d: len(ids) for d, ids in self._by_domain.items()},
            "per_grade": {g: len(ids) for g, ids in self._by_grade.items()},
        }


def _get_content_dir() -> Path:
    """Resolve NCERT content directory from env or defaults."""
    env_dir = os.environ.get("NCERT_CONTENT_DIR")
    if env_dir:
        return Path(env_dir)

    # Try relative to backend dir
    backend_dir = Path(__file__).resolve().parent.parent.parent
    candidates = [
        backend_dir.parent / "content-v2" / "ncert-curriculum",
        backend_dir / "content-v2" / "ncert-curriculum",
        Path("/app/content-v2/ncert-curriculum"),  # Docker path
    ]
    for c in candidates:
        if c.exists():
            return c

    return _DEFAULT_CONTENT_DIR


# --- Module-level singleton ---
ncert_store = NcertContentStore()


def init_ncert_store() -> NcertContentStore:
    """Initialize the NCERT content store (call at app startup)."""
    ncert_store.load()
    return ncert_store
