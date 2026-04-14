"""
In-memory content store.

For v0 this just loads JSON files from a directory on disk at startup and
keeps them in memory. When we move to Postgres + an ingester in Week 3, this
interface stays the same — only the implementation changes.
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


class ContentStore:
    def __init__(self) -> None:
        self._parents: Dict[str, Question] = {}
        self._step_downs: Dict[str, StepDownQuestion] = {}

    def load_folder(self, root: Path) -> int:
        """Load all *.json question files under root. Returns count loaded."""
        count = 0
        for path in sorted(root.rglob("*.json")):
            if any(part.startswith(".") for part in path.parts):
                continue
            try:
                data = json.loads(path.read_text())
                obj = parse_question_file(data)
            except Exception as e:
                print(f"[content_store] skipping {path.name}: {e}")
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

    def stats(self) -> Dict[str, int]:
        return {
            "parents": len(self._parents),
            "step_downs": len(self._step_downs),
        }


# Module-level singleton. Populated by app startup.
store = ContentStore()


def bootstrap_from_env() -> None:
    """Called at app startup. Reads KIWIMATH_CONTENT_DIR env var."""
    content_dir = os.environ.get("KIWIMATH_CONTENT_DIR")
    if not content_dir:
        print(
            "[content_store] KIWIMATH_CONTENT_DIR not set; using empty store. "
            "Set it to your Grade1/ folder to load questions."
        )
        return
    root = Path(content_dir).expanduser().resolve()
    n = store.load_folder(root)
    stats = store.stats()
    print(
        f"[content_store] loaded {n} file(s) from {root} "
        f"({stats['parents']} parents, {stats['step_downs']} step-downs)"
    )
