"""
US Common Core Content Store — loads US Common Core curriculum questions and provides lookup.

Loads all questions from grade1/ through grade6/ JSON files at startup,
indexed by question ID for O(1) lookup by the assessment engine.

Usage:
    from app.services.uscc_content_store import uscc_store, init_uscc_store

    # At startup:
    init_uscc_store()

    # Per-request:
    question = uscc_store.get_question("USCC-G1-042")
    batch = uscc_store.get_questions(["USCC-G1-001", "USCC-G2-010"])
    filtered = uscc_store.get_questions_by_domain("numbers", grade=2, limit=10)
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kiwimath.uscc_content_store")

# Default path — overridable via env var USCC_CONTENT_DIR
_DEFAULT_CONTENT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "content-v2" / "us-common-core"


class USCCContentStore:
    """In-memory store for US Common Core curriculum questions."""

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

    def questions_by_grade(self) -> Dict[int, int]:
        """Return count of questions per grade."""
        return {g: len(ids) for g, ids in self._by_grade.items()}

    def questions_by_domain(self) -> Dict[str, int]:
        """Return count of questions per domain."""
        return {d: len(ids) for d, ids in self._by_domain.items()}

    def load(self) -> None:
        """Load all US Common Core questions from JSON files."""
        if not self._content_dir.exists():
            logger.warning(f"USCC content dir not found: {self._content_dir}")
            return

        for grade_num in range(1, 7):
            grade_dir = self._content_dir / f"grade{grade_num}"
            if not grade_dir.exists():
                logger.debug(f"Grade dir not found: {grade_dir}")
                continue

            json_path = grade_dir / f"uscc_g{grade_num}_questions.json"
            if not json_path.exists():
                logger.debug(f"Questions file not found: {json_path}")
                continue

            self._load_grade_file(json_path, grade_num)

        logger.info(
            f"USCC content store loaded: {self.total_questions} questions "
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

            # Extract domain from chapter
            domain = self._extract_domain(q.get("tags", []), q.get("chapter", ""))
            q["domain"] = domain

            # Build visual URL path — inline SVGs are saved as files
            if q.get("visual_svg"):
                svg_filename = f"{item_id}.svg"
                q["visual_url"] = f"/static/uscc/grade{grade}/{svg_filename}"
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

    def _extract_domain(self, tags: list, chapter: str) -> str:
        """Extract domain from chapter name (US Common Core standards).

        Mapping:
            "Operations & Algebraic Thinking" -> arithmetic
            "Number & Operations in Base Ten" -> numbers
            "Number & Operations--Fractions" -> fractions
            "Measurement & Data" -> measurement
            "Geometry" -> geometry
            "Ratios & Proportional Relationships" -> arithmetic
            "The Number System" -> numbers
            "Expressions & Equations" -> arithmetic
            "Statistics & Probability" -> measurement
        """
        chapter_map = {
            "Operations & Algebraic Thinking": "arithmetic",
            "Number & Operations in Base Ten": "numbers",
            "Number & Operations--Fractions": "fractions",
            "Measurement & Data": "measurement",
            "Geometry": "geometry",
            "Ratios & Proportional Relationships": "arithmetic",
            "The Number System": "numbers",
            "Expressions & Equations": "arithmetic",
            "Statistics & Probability": "measurement",
        }

        # Direct chapter match
        if chapter in chapter_map:
            return chapter_map[chapter]

        # Partial match on chapter
        chapter_lower = chapter.lower()
        if "algebraic" in chapter_lower or "operation" in chapter_lower and "fraction" not in chapter_lower:
            return "arithmetic"
        if "fraction" in chapter_lower:
            return "fractions"
        if "geometry" in chapter_lower:
            return "geometry"
        if "measurement" in chapter_lower or "data" in chapter_lower or "statistic" in chapter_lower:
            return "measurement"
        if "number" in chapter_lower or "base ten" in chapter_lower:
            return "numbers"
        if "ratio" in chapter_lower or "expression" in chapter_lower or "equation" in chapter_lower:
            return "arithmetic"

        # Fallback: check tags
        domain_keywords = {
            "numbers": ["counting", "numbers", "number_sense", "place_value"],
            "arithmetic": ["addition", "subtraction", "multiplication", "division", "operations", "word_problem"],
            "fractions": ["fractions", "decimals", "equivalent_fractions"],
            "geometry": ["geometry", "shapes", "symmetry", "angles"],
            "measurement": ["measurement", "length", "weight", "time", "money", "data"],
        }
        for domain, keywords in domain_keywords.items():
            if any(kw in tags for kw in keywords):
                return domain

        return "numbers"  # default

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

    def stats(self) -> Dict[str, Any]:
        """Return summary stats."""
        return {
            "total_questions": self.total_questions,
            "grades": sorted(self._by_grade.keys()),
            "domains": self.questions_by_domain(),
            "per_grade": self.questions_by_grade(),
        }


def _get_content_dir() -> Path:
    """Resolve USCC content directory from env or defaults."""
    env_dir = os.environ.get("USCC_CONTENT_DIR")
    if env_dir:
        return Path(env_dir)

    # Try relative to backend dir
    backend_dir = Path(__file__).resolve().parent.parent.parent
    candidates = [
        backend_dir.parent / "content-v2" / "us-common-core",
        backend_dir / "content-v2" / "us-common-core",
        Path("/app/content-v2/us-common-core"),  # Docker path
    ]
    for c in candidates:
        if c.exists():
            return c

    return _DEFAULT_CONTENT_DIR


# --- Module-level singleton ---
uscc_store = USCCContentStore()


def init_uscc_store() -> USCCContentStore:
    """Initialize the USCC content store (call at app startup)."""
    uscc_store.load()
    return uscc_store
