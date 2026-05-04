"""
v2/v3 Content Store — loads flat JSON/SVG content from content-v2/ or content-v3/.

content-v3/ contains the same structure as content-v2/ but with Grand Unified
Schema fields (level, universal_skill_id, maturity_bucket, etc.) added by
migrate_to_v3.py.  The store loads whichever version is configured — all v3
fields are optional so v2 content continues to work.

Usage:
    # Preferred: point at enriched content
    export KIWIMATH_V3_CONTENT_DIR=~/kiwimath/content-v3

    # Legacy: still works, v3 fields will be None
    export KIWIMATH_V2_CONTENT_DIR=~/kiwimath/content-v2
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


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

# Accept T[1-8]-NNN topic IDs *and* curriculum IDs: NCERT-G3-001, SING-G1-001,
# USCC-G2-005, ICSE-G4-100.  The expanded pattern keeps backward compat with
# the original Grade 1-6 content while also allowing the four curriculum
# question banks (NCERT, Singapore/SING, USCC, ICSE) to be loaded into the
# same unified store.
_QUESTION_ID_RE = re.compile(
    r"^(?:"
    r"T[1-8]-\d{3,4}(?:-G\d(?:-L\d)?)?"         # Olympiad (original + grade-suffixed copies)
    r"|(?:NCERT|SING|USCC|ICSE|IGCSE)-G[1-6]-\d{3,4}(?:-G\d)?"  # Curriculum (+ grade copies)
    r"|GEN-G\d[MD]-\d{3}"                         # Generated multiplication/division
    r"|PCT-G5-\d{3}"                              # Generated percentage/ratio
    r")$"
)


class QuestionV2(BaseModel):
    model_config = ConfigDict(extra="ignore")  # v3 may add fields we don't model yet

    id: str
    stem: str
    original_stem: Optional[str] = None
    choices: List[str] = Field(default_factory=list)
    correct_answer: int = Field(default=0, ge=0, le=3)
    difficulty_tier: str  # easy, medium, hard, advanced, expert
    difficulty_score: int = Field(..., ge=1, le=500)
    visual_svg: Optional[str] = None
    visual_alt: Optional[str] = None

    @field_validator("visual_svg", mode="before")
    @classmethod
    def normalize_visual_svg(cls, v: Any) -> Any:
        """Nullify filename references (e.g. 't2-101.svg') — only keep inline SVG."""
        if isinstance(v, str) and v.strip() and not v.strip().startswith("<"):
            return None
        return v
    diagnostics: Dict[str, str] = Field(default_factory=dict)
    topic: str
    topic_name: str = ""
    chapter: Optional[str] = None  # Curriculum chapter name (e.g. "Ch1: Numbers 1 to 9")
    tags: List[str] = Field(default_factory=list)
    concept_cluster: Optional[str] = None
    hint: Optional[Union[str, Dict[str, str]]] = None
    solution_steps: List[str] = Field(default_factory=list)
    # Multi-mode interaction support
    interaction_mode: str = "mcq"  # "mcq" | "integer" | "drag_drop"
    correct_value: Optional[int] = None  # For integer mode: the correct numeric answer
    correct_order: Optional[List[int]] = None  # For drag_drop: correct ordering of items
    drag_items: Optional[List[str]] = None  # For drag_drop: the items to be arranged

    @field_validator("drag_items", mode="before")
    @classmethod
    def coerce_drag_items_to_str(cls, v: Any) -> Any:
        if isinstance(v, list):
            return [str(item) for item in v]
        return v

    # --- v3 Grand Unified Schema fields (all optional for backward compat) ---
    level: Optional[int] = None  # Kiwimath level 1-6 (replaces grade in core product)
    level_name: Optional[str] = None  # Explorer/Builder/Thinker/Solver/Strategist/Master
    universal_skill_id: Optional[str] = None  # e.g. FRAC_ADD_4
    skill_id: Optional[str] = None  # e.g. fraction_add (maps to prereq graph)
    skill_domain: Optional[str] = None  # numbers/arithmetic/fractions/geometry/measurement/data
    maturity_bucket: str = "calibrating"  # experimental/calibrating/production
    visual_requirement: Optional[str] = None  # essential/optional/none
    visual_type: Optional[str] = None  # 2d/3d_rotatable/number_line/chart/lottie/none
    visual_ai_verified: bool = False  # LLM recheck passed
    media_id: Optional[str] = None  # CDN asset reference
    media_hash: Optional[str] = None  # SHA256 integrity hash
    misconception_ids: List[str] = Field(default_factory=list)  # e.g. ["ADD_INSTEAD_SUB"]
    why_quality: Optional[str] = None  # human_authored/ai_generated/structured/minimal/none
    why_framework: Optional[str] = None  # 3R/pending
    hint_quality: Optional[Dict[str, Any]] = None  # {layers, quality, has_3_layers}
    country_context: Optional[Dict[str, Any]] = None  # localization contexts
    curriculum_source: Optional[str] = None  # ncert/icse/singapore/uscc/olympiad
    curriculum_map: Optional[Dict[str, str]] = None  # cross-curriculum references
    school_grade: Optional[int] = None  # preserved for curriculum tab only
    avg_time_to_solve_ms: Optional[int] = None  # behavioral (populated by live data)
    times_served: int = 0  # behavioral
    flag_count: int = 0  # behavioral
    schema_version: Optional[str] = None  # "3.0"

    # IRT parameters (from content generation / calibration)
    irt_params: Optional[Dict[str, float]] = None  # {a, b, c}
    irt_a: Optional[float] = None
    irt_b: Optional[float] = None
    irt_c: Optional[float] = None

    # Visual context description (for AI verification pipeline)
    visual_context: Optional[str] = None

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

    def get_chapters(self, curriculum: str, grade: int) -> List[Dict[str, Any]]:
        """Get ordered chapter list for a curriculum + grade.

        Scans all loaded questions for matching curriculum prefix and grade,
        groups by chapter field, and returns ordered chapters with question counts.

        Args:
            curriculum: "ncert", "icse", or "igcse"
            grade: 1-6

        Returns:
            List of dicts: [{id, name, question_count, topics}]
        """
        prefix_map = {
            "ncert": "NCERT",
            "icse": "ICSE",
            "igcse": "IGCSE",
            "singapore": "SING",
            "uscc": "USCC",
            "cambridge": "IGCSE",  # alias: Cambridge Primary = IGCSE prefix
        }
        prefix = prefix_map.get(curriculum.lower())
        if not prefix:
            return []

        id_prefix = f"{prefix}-G{grade}-"
        chapters: Dict[str, Dict[str, Any]] = {}

        for qid, q in self._questions.items():
            if not qid.startswith(id_prefix):
                continue
            ch = q.chapter or q.topic or "Unknown"
            if ch not in chapters:
                chapters[ch] = {
                    "id": ch,
                    "name": ch,
                    "question_count": 0,
                    "topics": set(),
                }
            chapters[ch]["question_count"] += 1
            chapters[ch]["topics"].add(q.topic)

        # Sort by chapter number if available (e.g. "Ch1: ..." < "Ch2: ...")
        def chapter_sort_key(ch_name: str) -> tuple:
            import re as _re
            m = _re.match(r"Ch(\d+)", ch_name)
            return (int(m.group(1)),) if m else (999, ch_name)

        result = []
        for ch_name in sorted(chapters.keys(), key=chapter_sort_key):
            ch = chapters[ch_name]
            ch["topics"] = sorted(ch["topics"])
            result.append(ch)

        return result

    def get_curriculum_questions(
        self, curriculum: str, grade: int, chapter: Optional[str] = None
    ) -> List[QuestionV2]:
        """Get questions for a specific curriculum, grade, and optionally chapter.

        Args:
            curriculum: "ncert", "icse", "igcse"
            grade: 1-6
            chapter: optional chapter filter (e.g. "Ch1: Numbers 1 to 9")

        Returns:
            List of QuestionV2 sorted by difficulty_score
        """
        prefix_map = {
            "ncert": "NCERT",
            "icse": "ICSE",
            "igcse": "IGCSE",
            "singapore": "SING",
            "uscc": "USCC",
            "cambridge": "IGCSE",  # alias: Cambridge Primary = IGCSE prefix
        }
        prefix = prefix_map.get(curriculum.lower())
        if not prefix:
            return []

        id_prefix = f"{prefix}-G{grade}-"
        questions = [
            q for qid, q in self._questions.items()
            if qid.startswith(id_prefix)
            and (chapter is None or q.chapter == chapter)
        ]
        questions.sort(key=lambda q: q.difficulty_score)
        return questions

    # -------------------------------------------------------------------
    # v3 Level / Skill / Maturity queries
    # -------------------------------------------------------------------

    def by_level(self, level: int) -> List[QuestionV2]:
        """Get all questions for a Kiwimath Level (1-6)."""
        return [q for q in self._questions.values() if q.level == level]

    def by_skill(self, universal_skill_id: str) -> List[QuestionV2]:
        """Get all questions for a Universal Skill ID (e.g. 'FRAC_ADD_4')."""
        return [
            q for q in self._questions.values()
            if q.universal_skill_id == universal_skill_id
        ]

    def by_skill_domain(self, domain: str) -> List[QuestionV2]:
        """Get all questions in a skill domain (numbers/arithmetic/fractions/geometry/measurement/data)."""
        return [q for q in self._questions.values() if q.skill_domain == domain]

    def by_maturity(self, bucket: str) -> List[QuestionV2]:
        """Get questions by maturity bucket (experimental/calibrating/production)."""
        return [q for q in self._questions.values() if q.maturity_bucket == bucket]

    def production_questions(self) -> List[QuestionV2]:
        """Get only production-grade questions (suitable for AH benchmarking)."""
        return self.by_maturity("production")

    def level_stats(self) -> Dict[int, int]:
        """Return level → question count mapping."""
        counts: Dict[int, int] = {}
        for q in self._questions.values():
            if q.level is not None:
                counts[q.level] = counts.get(q.level, 0) + 1
        return counts

    def skill_stats(self) -> Dict[str, int]:
        """Return universal_skill_id → question count mapping."""
        counts: Dict[str, int] = {}
        for q in self._questions.values():
            if q.universal_skill_id:
                counts[q.universal_skill_id] = counts.get(q.universal_skill_id, 0) + 1
        return counts

    def next_question_v3(
        self,
        level: int,
        skill_domain: Optional[str] = None,
        exclude_ids: Optional[List[str]] = None,
        maturity_filter: Optional[str] = None,
        difficulty: Optional[int] = None,
        window: int = 20,
    ) -> Optional[QuestionV2]:
        """Level-aware question selection (v3 schema).

        Selects from the level pool, optionally filtered by skill domain
        and maturity bucket. Falls back to the legacy next_question()
        if no v3 fields are populated.
        """
        import random

        pool = self.by_level(level)
        if skill_domain:
            pool = [q for q in pool if q.skill_domain == skill_domain]
        if maturity_filter:
            pool = [q for q in pool if q.maturity_bucket == maturity_filter]

        exclude = set(exclude_ids or [])
        pool = [q for q in pool if q.id not in exclude]

        if not pool:
            return None

        if difficulty is not None:
            candidates = [q for q in pool if abs(q.difficulty_score - difficulty) <= window]
            if candidates:
                return random.choice(candidates)

        return random.choice(pool)

    def stats(self) -> Dict:
        base = {
            "total_questions": len(self._questions),
            "topics": len(self._topics),
            "questions_per_topic": {
                t.topic_id: t.total_questions for t in self._topics
            },
        }
        # Add v3 stats if available
        ls = self.level_stats()
        if ls:
            base["levels"] = ls
            base["maturity"] = {
                bucket: len(self.by_maturity(bucket))
                for bucket in ("experimental", "calibrating", "production")
            }
        return base


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

store_v2 = ContentStoreV2()


def _load_curriculum_folder(curriculum_dir: Path, curriculum_name: str) -> int:
    """Load a curriculum folder (e.g. ncert-curriculum/) into store_v2.

    Curriculum folders have a different layout than topic folders:
        ncert-curriculum/
            grade3/ncert_g3_questions.json
            grade4/ncert_g4_questions.json
            ...

    Each JSON file has {"questions": [...], "topic_name": "...", ...}.
    Questions may lack `topic_name` on individual items, so we inject it from
    the file-level metadata or derive it from the `topic` field.
    """
    if not curriculum_dir.exists():
        return 0

    count = 0
    for grade_dir in sorted(curriculum_dir.iterdir()):
        if not grade_dir.is_dir() or grade_dir.name.startswith("."):
            continue

        for json_file in sorted(grade_dir.glob("*.json")):
            try:
                data = json.loads(json_file.read_text())
            except (json.JSONDecodeError, OSError) as e:
                print(f"[content_store_v2] skipping {json_file}: {e}")
                continue

            if isinstance(data, list):
                question_list = data
                file_topic_name = curriculum_name
            else:
                question_list = data.get("questions", [])
                file_topic_name = data.get("topic_name", curriculum_name)

            topic_id = None
            topic_questions: list[QuestionV2] = []

            for qd in question_list:
                # Inject topic_name if missing from individual question
                if "topic_name" not in qd or not qd["topic_name"]:
                    qd["topic_name"] = file_topic_name
                # Some curricula use 'chapter' instead of 'topic'
                if "topic" not in qd:
                    qd["topic"] = qd.get("chapter", f"{curriculum_name}_{grade_dir.name}")
                # Derive difficulty_tier from score if missing
                if "difficulty_tier" not in qd:
                    score = qd.get("difficulty_score", 50)
                    if score <= 20:
                        qd["difficulty_tier"] = "easy"
                    elif score <= 40:
                        qd["difficulty_tier"] = "medium"
                    elif score <= 60:
                        qd["difficulty_tier"] = "hard"
                    elif score <= 80:
                        qd["difficulty_tier"] = "advanced"
                    else:
                        qd["difficulty_tier"] = "expert"
                # Fix diagnostics: convert list values to comma-joined strings
                diag = qd.get("diagnostics")
                if isinstance(diag, dict):
                    fixed_diag: dict[str, str] = {}
                    for dk, dv in diag.items():
                        if isinstance(dv, list):
                            # Join list items; handle both strings and dicts
                            parts = []
                            for item in dv:
                                if isinstance(item, dict):
                                    parts.append(
                                        item.get("misconception", str(item))
                                    )
                                else:
                                    parts.append(str(item))
                            fixed_diag[dk] = "; ".join(parts)
                        else:
                            fixed_diag[dk] = str(dv)
                    qd["diagnostics"] = fixed_diag
                try:
                    q = QuestionV2(**qd)
                    store_v2._questions[q.id] = q
                    topic_questions.append(q)
                    count += 1
                    if topic_id is None:
                        topic_id = q.topic
                    if q.concept_cluster:
                        store_v2._cluster_index.setdefault(
                            q.concept_cluster, []
                        ).append(q.id)
                except Exception as e:
                    print(f"[content_store_v2] skipping curriculum Q: {e}")
                    continue

            if topic_questions and topic_id:
                topic_questions.sort(key=lambda q: q.difficulty_score)
                existing = store_v2._by_topic.get(topic_id, [])
                store_v2._by_topic[topic_id] = existing + topic_questions

                # Add topic metadata if not already present
                existing_ids = {t.topic_id for t in store_v2._topics}
                if topic_id not in existing_ids:
                    dist: dict[str, int] = {}
                    for q in topic_questions:
                        dist[q.difficulty_tier] = dist.get(q.difficulty_tier, 0) + 1
                    store_v2._topics.append(TopicV2(
                        topic_id=topic_id,
                        topic_name=file_topic_name,
                        total_questions=len(topic_questions),
                        difficulty_distribution=dist,
                    ))

            if topic_questions:
                print(
                    f"[content_store_v2] loaded {curriculum_name}/{grade_dir.name}: "
                    f"{len(topic_questions)} questions from {json_file.name}"
                )

    return count


def bootstrap_v2_from_env() -> None:
    """Called at app startup.

    Prefers KIWIMATH_V3_CONTENT_DIR (enriched Grand Unified Schema data).
    Falls back to KIWIMATH_V2_CONTENT_DIR for legacy content.
    """
    # Prefer v3 (Grand Unified Schema) over v2
    content_dir = os.environ.get("KIWIMATH_V3_CONTENT_DIR") or os.environ.get(
        "KIWIMATH_V2_CONTENT_DIR"
    )
    if not content_dir:
        print("[content_store_v2] No content dir set (KIWIMATH_V3_CONTENT_DIR / KIWIMATH_V2_CONTENT_DIR); store empty.")
        return

    root = Path(content_dir).expanduser().resolve()
    if not root.exists():
        print(f"[content_store_v2] WARNING: {root} does not exist")
        return

    schema_version = "v3" if "v3" in str(root) else "v2"
    print(f"[content_store_v2] loading {schema_version} content from {root}")

    # Load core topic content (T1-T8)
    n = store_v2.load_folder(root)
    print(f"[content_store_v2] loaded {n} core topic questions ({schema_version})")

    # Load all curriculum content into the same store
    curricula = {
        "ncert-curriculum": "NCERT",
        "singapore-curriculum": "Singapore Math",
        "us-common-core": "US Common Core",
        "icse-curriculum": "ICSE",
        "igcse-curriculum": "IGCSE",
    }
    curriculum_total = 0
    for folder_name, display_name in curricula.items():
        curr_dir = root / folder_name
        loaded = _load_curriculum_folder(curr_dir, display_name)
        curriculum_total += loaded
        if loaded:
            print(f"[content_store_v2] {display_name}: {loaded} questions merged into v2 store")

    stats = store_v2.stats()
    print(f"[content_store_v2] TOTAL: {n + curriculum_total} questions ({n} core + {curriculum_total} curriculum): {stats}")
