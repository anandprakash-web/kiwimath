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
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


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

# Allow 3- or 4-digit numeric IDs so Grade 3-4 content (T1-601 onwards) can
# coexist with the original Grade 1-2 set (T1-001 to T1-600).
_QUESTION_ID_RE = re.compile(r"^T[1-8]-\d{3,4}$")


class QuestionV2(BaseModel):
    id: str
    stem: str
    original_stem: Optional[str] = None
    choices: List[str]
    correct_answer: int = Field(..., ge=0, le=3)
    difficulty_tier: str  # easy, medium, hard, advanced, expert
    difficulty_score: int = Field(..., ge=1, le=500)
    visual_svg: Optional[str] = None
    visual_alt: Optional[str] = None
    diagnostics: Dict[str, str] = Field(default_factory=dict)
    topic: str
    topic_name: str
    tags: List[str] = Field(default_factory=list)
    concept_cluster: Optional[str] = None
    hint: Optional[Union[str, Dict[str, str]]] = None

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not _QUESTION_ID_RE.match(v):
            raise ValueError(
                f"Question ID '{v}' does not match required format T[1-8]-NNN "
                f"(e.g. T1-001, T8-600)"
            )
        return v

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
        self._cluster_index: Dict[str, List[str]] = {}       # cluster -> list of qids
        self._root: Optional[Path] = None

    def load_folder(self, root: Path) -> int:
        """Load all topic folders under root. Returns total questions loaded.

        Each topic folder is expected to contain `questions.json` (Grade 1-2,
        difficulty 1-100). Optional secondary files like `grade34_questions.json`
        (Grade 3-4, difficulty 101-200) are loaded automatically and merged
        into the same topic — see Task #191.
        """
        self._root = root
        count = 0

        # Files we look for inside each topic folder, in load order.
        # Adding files here is the explicit way to opt new content packs into
        # the loader (e.g. variety augmentations). The order here also
        # determines tie-breaking — earlier wins on question_id collisions.
        question_files = [
            "questions.json",
            "grade34_questions.json",
            "grade34_variety_questions.json",
            "g56_questions.json",
            "data_handling.json",
            "geometry_measurement.json",
            "measurement_units.json",
        ]

        for topic_dir in sorted(root.iterdir()):
            if not topic_dir.is_dir() or topic_dir.name.startswith("."):
                continue

            topic_id: Optional[str] = None
            topic_name: Optional[str] = None
            topic_questions: List[QuestionV2] = []
            combined_distribution: Dict[str, int] = {}
            loaded_files: List[str] = []

            for fname in question_files:
                p = topic_dir / fname
                if not p.exists():
                    continue
                try:
                    data = json.loads(p.read_text())
                except (json.JSONDecodeError, OSError) as e:
                    print(f"[content_store_v2] skipping {p}: {e}")
                    continue

                # Handle both formats: {"questions": [...]} and flat [...]
                if isinstance(data, list):
                    question_list = data
                    if topic_id is None:
                        topic_id = topic_dir.name
                        topic_name = topic_id
                else:
                    question_list = data.get("questions", [])
                    if topic_id is None:
                        topic_id = data.get("topic_id", topic_dir.name)
                        topic_name = data.get("topic_name", topic_id)

                for qd in question_list:
                    try:
                        q = QuestionV2(**qd)
                        self._questions[q.id] = q
                        topic_questions.append(q)
                        count += 1
                        # Build cluster index
                        if q.concept_cluster:
                            self._cluster_index.setdefault(q.concept_cluster, []).append(q.id)
                    except Exception as e:
                        print(f"[content_store_v2] skipping question: {e}")
                        continue

                dist = data.get("difficulty_distribution") if isinstance(data, dict) else None
                for tier, n in (dist or {}).items():
                    combined_distribution[tier] = combined_distribution.get(tier, 0) + int(n)

                loaded_files.append(fname)

            if not topic_questions:
                continue

            # Sort by difficulty_score (should already be sorted, but ensure it)
            topic_questions.sort(key=lambda q: q.difficulty_score)
            self._by_topic[topic_id] = topic_questions

            self._topics.append(TopicV2(
                topic_id=topic_id,
                topic_name=topic_name,
                total_questions=len(topic_questions),
                difficulty_distribution=combined_distribution,
            ))

            print(
                f"[content_store_v2] loaded {topic_dir.name}: "
                f"{len(topic_questions)} questions from {loaded_files}"
            )

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
        max_score: int = 500,
    ) -> List[QuestionV2]:
        """Get questions within a difficulty range for a topic (1-200)."""
        return [
            q for q in self.by_topic(topic_id)
            if min_score <= q.difficulty_score <= max_score
        ]

    def get_cluster_qids(self, cluster: str) -> List[str]:
        """Get all question IDs belonging to a concept cluster."""
        return self._cluster_index.get(cluster, [])

    def cluster_stats(self) -> Dict[str, int]:
        """Return cluster → count mapping for diagnostics."""
        return {k: len(v) for k, v in self._cluster_index.items()}

    def next_question(
        self,
        topic_id: Optional[str] = None,
        difficulty: Optional[int] = None,
        window: int = 10,
        exclude_ids: Optional[List[str]] = None,
        min_difficulty: Optional[int] = None,
        max_difficulty: Optional[int] = None,
        exclude_clusters: Optional[List[str]] = None,
        max_per_cluster: int = 2,
        seen_clusters: Optional[Dict[str, int]] = None,
    ) -> Optional[QuestionV2]:
        """Pick the best next question adaptively with cluster deduplication.

        Args:
            topic_id: filter to a specific topic (or None for all)
            difficulty: target difficulty score (1-100)
            window: how wide a range around difficulty to search (±window)
            exclude_ids: question IDs to skip (already answered)
            min_difficulty: floor for difficulty range (grade filter)
            max_difficulty: ceiling for difficulty range (grade filter)
            exclude_clusters: clusters to fully skip (mastered patterns)
            max_per_cluster: max questions from same cluster in a session (default 2)
            seen_clusters: dict of cluster -> times_seen for soft limiting

        Returns the closest available question to the target difficulty,
        preferring questions from unseen concept clusters.
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

        # --- Cluster-aware filtering ---
        excluded_clusters = set(exclude_clusters or [])
        cluster_counts = dict(seen_clusters or {})

        # Partition into preferred (unseen/under-limit clusters) and fallback
        preferred = []
        fallback = []
        for q in pool:
            cluster = q.concept_cluster
            if cluster and cluster in excluded_clusters:
                fallback.append(q)
                continue
            if cluster and cluster_counts.get(cluster, 0) >= max_per_cluster:
                fallback.append(q)
                continue
            preferred.append(q)

        # Use preferred pool if non-empty, otherwise fall back to all
        active_pool = preferred if preferred else fallback if fallback else pool

        if difficulty is None:
            return random.choice(active_pool)

        # Find questions within the window
        candidates = [
            q for q in active_pool
            if abs(q.difficulty_score - difficulty) <= window
        ]

        if not candidates:
            # Widen: try from full active pool
            candidates = sorted(active_pool, key=lambda q: abs(q.difficulty_score - difficulty))[:5]

        if not candidates:
            return random.choice(active_pool) if active_pool else None

        # Diversity bonus: prefer questions from clusters not yet seen
        unseen = [q for q in candidates if not q.concept_cluster or cluster_counts.get(q.concept_cluster, 0) == 0]
        if unseen:
            return random.choice(unseen)

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
