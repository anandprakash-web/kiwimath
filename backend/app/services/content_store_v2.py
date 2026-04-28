"""
v2 Content Store — loads the new flat JSON/SVG content from content-v2/.

Each topic folder contains:
  - questions.json  (all 100 questions, ordered by difficulty 1-100)
  - visuals/        (SVG files referenced by question.visual_svg)

Usage:
    export KIWIMATH_V2_CONTENT_DIR=~/kiwimath/content-v2
    # Or point to the content-v2 folder at startup
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# v2 Hint Ladder model (Socratic 6-level hints)
# ---------------------------------------------------------------------------

class HintLadder(BaseModel):
    """Socratic hint ladder — 6 levels from gentle nudge to teach-and-retry."""
    level_0: str = Field(..., description="Pause prompt — gentle nudge to re-read")
    level_1: str = Field(..., description="Attention direction — where to look")
    level_2: str = Field(..., description="Thinking question — Socratic prompt")
    level_3: str = Field(..., description="Scaffolded step — break it down")
    level_4: str = Field(..., description="Guided reveal — almost there")
    level_5: str = Field(..., description="Teach + retry — explain the concept")


# ---------------------------------------------------------------------------
# v2 Question model (flat, no templates)
# ---------------------------------------------------------------------------

class QuestionV2(BaseModel):
    id: str
    stem: str
    original_stem: Optional[str] = None
    choices: List[str]
    correct_answer: int = Field(..., ge=0, le=3)
    difficulty_tier: str  # easy, medium, hard
    difficulty_score: int = Field(..., ge=1, le=100)
    visual_svg: Optional[str] = None
    visual_alt: Optional[str] = None
    diagnostics: Dict[str, str] = Field(default_factory=dict)
    topic: str
    topic_name: str
    tags: List[str] = Field(default_factory=list)
    hint: Optional[Union[str, Dict[str, str]]] = None

    @property
    def hint_ladder(self) -> Optional[HintLadder]:
        """Get structured hint ladder if available."""
        if isinstance(self.hint, dict):
            try:
                return HintLadder(**self.hint)
            except Exception:
                return None
        return None

    @property
    def hint_text(self) -> Optional[str]:
        """Get simple hint text (backward compat for old string hints)."""
        if isinstance(self.hint, str):
            return self.hint
        if isinstance(self.hint, dict):
            return self.hint.get("level_0")
        return None


class TopicV2(BaseModel):
    topic_id: str
    topic_name: str
    total_questions: int
    difficulty_distribution: Dict[str, int]


# ---------------------------------------------------------------------------
# v2 Content Store
# ---------------------------------------------------------------------------

class ContentStoreV2:
    def __init__(self) -> None:
        self._questions: Dict[str, QuestionV2] = {}          # qid -> question
        self._by_topic: Dict[str, List[QuestionV2]] = {}     # topic_id -> sorted list
        self._topics: List[TopicV2] = []                     # topic metadata
        self._svg_cache: Dict[str, str] = {}                 # svg filename -> svg content
        self._root: Optional[Path] = None

    def load_folder(self, root: Path) -> int:
        """Load all topic folders under root. Returns total questions loaded."""
        self._root = root
        count = 0

        for topic_dir in sorted(root.iterdir()):
            if not topic_dir.is_dir() or topic_dir.name.startswith("."):
                continue

            questions_path = topic_dir / "questions.json"
            if not questions_path.exists():
                continue

            try:
                data = json.loads(questions_path.read_text())
            except (json.JSONDecodeError, OSError) as e:
                print(f"[content_store_v2] skipping {topic_dir.name}: {e}")
                continue

            topic_id = data.get("topic_id", topic_dir.name)
            topic_name = data.get("topic_name", topic_id)
            questions_data = data.get("questions", [])

            topic_questions = []
            for qd in questions_data:
                try:
                    q = QuestionV2(**qd)
                    self._questions[q.id] = q
                    topic_questions.append(q)
                    count += 1
                except Exception as e:
                    print(f"[content_store_v2] skipping question: {e}")
                    continue

            # Sort by difficulty_score (should already be sorted, but ensure it)
            topic_questions.sort(key=lambda q: q.difficulty_score)
            self._by_topic[topic_id] = topic_questions

            self._topics.append(TopicV2(
                topic_id=topic_id,
                topic_name=topic_name,
                total_questions=len(topic_questions),
                difficulty_distribution=data.get("difficulty_distribution", {}),
            ))

            print(f"[content_store_v2] loaded {topic_dir.name}: {len(topic_questions)} questions")

        return count

    def get(self, qid: str) -> Optional[QuestionV2]:
        """Get a question by ID."""
        return self._questions.get(qid)

    def all_questions(self) -> List[QuestionV2]:
        """All questions, sorted by topic then difficulty."""
        return list(self._questions.values())

    def by_topic(self, topic_id: str) -> List[QuestionV2]:
        """Get all questions for a topic, sorted by difficulty (1-100)."""
        return self._by_topic.get(topic_id, [])

    def by_difficulty_range(
        self,
        topic_id: str,
        min_score: int = 1,
        max_score: int = 100,
    ) -> List[QuestionV2]:
        """Get questions within a difficulty range for a topic."""
        return [
            q for q in self.by_topic(topic_id)
            if min_score <= q.difficulty_score <= max_score
        ]

    def next_question(
        self,
        topic_id: Optional[str] = None,
        difficulty: Optional[int] = None,
        window: int = 10,
        exclude_ids: Optional[List[str]] = None,
        min_difficulty: Optional[int] = None,
        max_difficulty: Optional[int] = None,
    ) -> Optional[QuestionV2]:
        """Pick the best next question adaptively.

        Args:
            topic_id: filter to a specific topic (or None for all)
            difficulty: target difficulty score (1-100)
            window: how wide a range around difficulty to search (±window)
            exclude_ids: question IDs to skip (already answered)
            min_difficulty: floor for difficulty range (grade filter)
            max_difficulty: ceiling for difficulty range (grade filter)

        Returns the closest available question to the target difficulty.
        """
        import random

        if topic_id:
            pool = self.by_topic(topic_id)
        else:
            pool = self.all_questions()

        if not pool:
            return None

        # Apply grade-based difficulty bounds
        if min_difficulty is not None:
            pool = [q for q in pool if q.difficulty_score >= min_difficulty]
        if max_difficulty is not None:
            pool = [q for q in pool if q.difficulty_score <= max_difficulty]

        exclude = set(exclude_ids or [])
        pool = [q for q in pool if q.id not in exclude]

        if not pool:
            return None

        if difficulty is None:
            return random.choice(pool)

        # Find questions within the window
        candidates = [
            q for q in pool
            if abs(q.difficulty_score - difficulty) <= window
        ]

        if not candidates:
            # Fallback: closest question
            candidates = sorted(pool, key=lambda q: abs(q.difficulty_score - difficulty))[:5]

        return random.choice(candidates)

    def get_svg(self, topic_id: str, svg_filename: str) -> Optional[str]:
        """Load an SVG file from a topic's visuals directory."""
        cache_key = f"{topic_id}/{svg_filename}"
        if cache_key in self._svg_cache:
            return self._svg_cache[cache_key]

        if not self._root:
            return None

        # Find the topic directory
        for topic_dir in self._root.iterdir():
            if not topic_dir.is_dir():
                continue
            qpath = topic_dir / "questions.json"
            if not qpath.exists():
                continue
            try:
                data = json.loads(qpath.read_text())
                if data.get("topic_id") == topic_id:
                    svg_path = topic_dir / "visuals" / svg_filename
                    if svg_path.exists():
                        svg = svg_path.read_text()
                        self._svg_cache[cache_key] = svg
                        return svg
            except Exception:
                continue

        return None

    def topics(self) -> List[TopicV2]:
        """List all loaded topics."""
        return list(self._topics)

    def stats(self) -> Dict:
        return {
            "total_questions": len(self._questions),
            "topics": len(self._topics),
            "questions_per_topic": {
                t.topic_id: t.total_questions for t in self._topics
            },
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

store_v2 = ContentStoreV2()


def bootstrap_v2_from_env() -> None:
    """Called at app startup. Reads KIWIMATH_V2_CONTENT_DIR env var."""
    content_dir = os.environ.get("KIWIMATH_V2_CONTENT_DIR")
    if not content_dir:
        print("[content_store_v2] KIWIMATH_V2_CONTENT_DIR not set; v2 store empty.")
        return

    root = Path(content_dir).expanduser().resolve()
    if not root.exists():
        print(f"[content_store_v2] WARNING: {root} does not exist")
        return

    n = store_v2.load_folder(root)
    stats = store_v2.stats()
    print(f"[content_store_v2] loaded {n} v2 questions: {stats}")
