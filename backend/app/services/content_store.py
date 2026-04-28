"""
In-memory content store.

For v0 this just loads JSON files from a directory on disk at startup and
keeps them in memory. When we move to Postgres + an ingester in Week 3, this
interface stays the same — only the implementation changes.

v3b support: tries the v3 adapter first when loading JSON files, falling back
to the original parse_question_file if the adapter fails or returns None.
Supports loading from any grade directory (Grade1, Grade2, ... Grade5+).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from app.models.question import (
    Question,
    StepDownQuestion,
    parse_question_file,
)
from app.services.v3_adapter import adapt_v3b


class ContentStore:
    def __init__(self) -> None:
        self._parents: Dict[str, Question] = {}
        self._step_downs: Dict[str, StepDownQuestion] = {}

    def _try_load_json(self, data: Dict) -> Optional[Union[Question, StepDownQuestion]]:
        """Try loading a JSON dict as a question, using v3 adapter then fallback.

        Strategy:
          1. Try v3b adapter -> parse_question_file on adapted data
          2. Fall back to direct parse_question_file on raw data
        """
        # Strategy 1: v3b adapter
        try:
            adapted = adapt_v3b(data)
            if adapted:
                return parse_question_file(adapted)
        except Exception:
            pass

        # Strategy 2: direct parse (original format)
        try:
            return parse_question_file(data)
        except Exception:
            pass

        return None

    def load_folder(self, root: Path) -> int:
        """Load all *.json question files under root. Returns count loaded.

        Supports any grade directory structure — recursively walks all
        subdirectories (Grade1/, Grade2/, Ch01_COUN/, etc.).
        """
        count = 0
        for path in sorted(root.rglob("*.json")):
            if any(part.startswith(".") for part in path.parts):
                continue
            # Skip known non-question files
            if path.name in ("content_index.json", "package.json"):
                continue
            try:
                data = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError) as e:
                print(f"[content_store] skipping {path.name}: cannot read JSON: {e}")
                continue

            obj = self._try_load_json(data)
            if obj is None:
                print(f"[content_store] skipping {path.name}: failed both v3b adapter and direct parse")
                continue

            if isinstance(obj, Question):
                self._parents[obj.id] = obj
            elif isinstance(obj, StepDownQuestion):
                self._step_downs[obj.id] = obj
            count += 1
        return count

    def get(self, qid: str) -> Optional[Union[Question, StepDownQuestion]]:
        return self._parents.get(qid) or self._step_downs.get(qid)

    def parents(self) -> List[Question]:
        return list(self._parents.values())

    def by_topic(self, topic: str) -> List[Question]:
        return [q for q in self._parents.values() if q.topic.value == topic]

    def by_grade(self, grade: int) -> List[Question]:
        """Return all parent questions for a given grade (1-5)."""
        prefix = f"G{grade}-"
        return [q for q in self._parents.values() if q.id.startswith(prefix)]

    def stats(self) -> Dict[str, int]:
        return {
            "parents": len(self._parents),
            "step_downs": len(self._step_downs),
        }

    def stats_by_grade(self) -> Dict[str, Dict[str, int]]:
        """Return parent/step-down counts grouped by grade."""
        grade_stats: Dict[str, Dict[str, int]] = {}
        for qid in self._parents:
            g = qid.split("-")[0]  # e.g. "G1"
            grade_stats.setdefault(g, {"parents": 0, "step_downs": 0})
            grade_stats[g]["parents"] += 1
        for qid in self._step_downs:
            g = qid.split("-")[0]
            grade_stats.setdefault(g, {"parents": 0, "step_downs": 0})
            grade_stats[g]["step_downs"] += 1
        return grade_stats


# Module-level singleton. Populated by app startup.
store = ContentStore()


def bootstrap_from_env() -> None:
    """Called at app startup. Reads KIWIMATH_CONTENT_DIR env var.

    Supports pointing to:
      - A single grade folder (e.g., Grade1/)
      - A parent folder containing multiple grade folders (e.g., Kiwimath_Content_v3b/)
    """
    content_dir = os.environ.get("KIWIMATH_CONTENT_DIR")
    if not content_dir:
        print(
            "[content_store] KIWIMATH_CONTENT_DIR not set; using empty store. "
            "Set it to your content folder to load questions."
        )
        return
    root = Path(content_dir).expanduser().resolve()
    n = store.load_folder(root)
    stats = store.stats()
    print(
        f"[content_store] loaded {n} file(s) from {root} "
        f"({stats['parents']} parents, {stats['step_downs']} step-downs)"
    )
