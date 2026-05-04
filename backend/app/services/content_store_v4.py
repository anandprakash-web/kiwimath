"""
v4 Content Store — loads grade-topic structured content from content-v4/.

content-v4/ structure:
    adaptive/grade{1-6}/{topic-id}.json   — IRT-sequenced questions per topic
    adaptive/grade{1-6}/index.json        — grade-level topic index
    school/{curriculum}/grade{1-6}/chapters.json — chapter references

The v4 store is topic-first and grade-aware. Questions are pre-sequenced
by IRT difficulty within each topic, enabling pure adaptive selection.

Usage:
    export KIWIMATH_V4_CONTENT_DIR=~/kiwimath/content-v4
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict

from .content_store_v2 import QuestionV2, HintLadder


class AdaptiveTopic:
    """A loaded adaptive topic with its questions."""
    __slots__ = (
        'topic_id', 'topic_name', 'topic_emoji', 'grade', 'domain',
        'skills', 'total_questions', 'difficulty_range', 'source_breakdown',
        'questions'
    )

    def __init__(self, data: dict):
        self.topic_id = data['topic_id']
        self.topic_name = data['topic_name']
        self.topic_emoji = data.get('topic_emoji', '')
        self.grade = data['grade']
        self.domain = data.get('domain', '')
        self.skills = data.get('skills', [])
        self.total_questions = data.get('total_questions', 0)
        self.difficulty_range = data.get('difficulty_range', {})
        self.source_breakdown = data.get('source_breakdown', {})
        self.questions: List[QuestionV2] = []


class SchoolChapter:
    """A curriculum chapter with question references."""
    __slots__ = (
        'chapter_name', 'total_questions', 'skill_ids',
        'adaptive_topic_ids', 'question_ids', 'difficulty_range'
    )

    def __init__(self, data: dict):
        self.chapter_name = data['chapter_name']
        self.total_questions = data.get('total_questions', 0)
        self.skill_ids = data.get('skill_ids', [])
        self.adaptive_topic_ids = data.get('adaptive_topic_ids', [])
        self.question_ids = data.get('question_ids', [])
        self.difficulty_range = data.get('difficulty_range', {})


class SchoolCurriculum:
    """A loaded school curriculum for a grade."""
    __slots__ = (
        'curriculum', 'curriculum_name', 'grade',
        'total_chapters', 'total_questions', 'chapters'
    )

    def __init__(self, data: dict):
        self.curriculum = data['curriculum']
        self.curriculum_name = data.get('curriculum_name', self.curriculum)
        self.grade = data['grade']
        self.total_chapters = data.get('total_chapters', 0)
        self.total_questions = data.get('total_questions', 0)
        self.chapters = [SchoolChapter(ch) for ch in data.get('chapters', [])]


class ContentStoreV4:
    """Grade-topic structured content store for v4 content."""

    def __init__(self) -> None:
        self._questions: Dict[str, QuestionV2] = {}
        self._topics: Dict[str, AdaptiveTopic] = {}  # topic_id -> topic
        self._by_grade: Dict[int, List[AdaptiveTopic]] = defaultdict(list)
        self._by_grade_topic: Dict[tuple, List[QuestionV2]] = {}  # (grade, topic_id) -> questions
        self._school: Dict[tuple, SchoolCurriculum] = {}  # (curriculum, grade) -> curriculum
        self._cluster_index: Dict[str, List[str]] = {}
        self._root: Optional[Path] = None

    def load(self, root: Path) -> int:
        """Load all content-v4 data. Returns total questions loaded."""
        self._root = root
        count = 0

        # Load adaptive topic files
        adaptive_dir = root / 'adaptive'
        if adaptive_dir.exists():
            for grade in range(1, 7):
                grade_dir = adaptive_dir / f'grade{grade}'
                if not grade_dir.exists():
                    continue

                for topic_file in sorted(grade_dir.glob('g*-*.json')):
                    if topic_file.name == 'index.json':
                        continue
                    try:
                        data = json.loads(topic_file.read_text())
                    except (json.JSONDecodeError, OSError) as e:
                        print(f"[content_store_v4] skipping {topic_file}: {e}")
                        continue

                    topic = AdaptiveTopic(data)
                    questions = []
                    for qd in data.get('questions', []):
                        try:
                            q = QuestionV2.model_validate(qd)
                            self._questions[q.id] = q
                            questions.append(q)
                            count += 1
                            if q.concept_cluster:
                                self._cluster_index.setdefault(
                                    q.concept_cluster, []
                                ).append(q.id)
                        except Exception as e:
                            print(f"[content_store_v4] skipping Q in {topic_file.name}: {e}")

                    topic.questions = questions
                    self._topics[topic.topic_id] = topic
                    self._by_grade[grade].append(topic)
                    self._by_grade_topic[(grade, topic.topic_id)] = questions

                    print(f"[content_store_v4] Grade {grade} {topic.topic_name}: {len(questions)} questions")

        # Load school curriculum files
        school_dir = root / 'school'
        if school_dir.exists():
            for curr_dir in sorted(school_dir.iterdir()):
                if not curr_dir.is_dir():
                    continue
                for grade_dir in sorted(curr_dir.iterdir()):
                    if not grade_dir.is_dir():
                        continue
                    chapters_file = grade_dir / 'chapters.json'
                    if not chapters_file.exists():
                        continue
                    try:
                        data = json.loads(chapters_file.read_text())
                        curriculum = SchoolCurriculum(data)
                        self._school[(curriculum.curriculum, curriculum.grade)] = curriculum
                        print(f"[content_store_v4] School: {curriculum.curriculum_name} Grade {curriculum.grade}: {curriculum.total_chapters} chapters, {curriculum.total_questions} questions")
                    except Exception as e:
                        print(f"[content_store_v4] skipping {chapters_file}: {e}")

        return count

    # --- Adaptive queries ---

    def get(self, qid: str) -> Optional[QuestionV2]:
        return self._questions.get(qid)

    def all_questions(self) -> List[QuestionV2]:
        return list(self._questions.values())

    def topics_for_grade(self, grade: int) -> List[AdaptiveTopic]:
        return self._by_grade.get(grade, [])

    def get_topic(self, topic_id: str) -> Optional[AdaptiveTopic]:
        return self._topics.get(topic_id)

    def by_topic(self, topic_id: str) -> List[QuestionV2]:
        topic = self._topics.get(topic_id)
        return topic.questions if topic else []

    def by_grade_topic(self, grade: int, topic_id: str) -> List[QuestionV2]:
        return self._by_grade_topic.get((grade, topic_id), [])

    def by_level(self, level: int) -> List[QuestionV2]:
        """Backward compat: get all questions for a grade/level."""
        questions = []
        for topic in self._by_grade.get(level, []):
            questions.extend(topic.questions)
        return questions

    def by_skill(self, skill_id: str) -> List[QuestionV2]:
        return [q for q in self._questions.values() if q.skill_id == skill_id]

    def by_skill_domain(self, domain: str) -> List[QuestionV2]:
        return [q for q in self._questions.values() if q.skill_domain == domain]

    def next_question_adaptive(
        self,
        grade: int,
        topic_id: str,
        theta: float = 0.0,
        exclude_ids: Optional[List[str]] = None,
        window: float = 0.5,
        max_per_cluster: int = 2,
        seen_clusters: Optional[Dict[str, int]] = None,
    ) -> Optional[QuestionV2]:
        """IRT-aware adaptive question selection within a grade-topic.

        Selects the question closest to the student's ability (theta)
        from unseen questions, with cluster diversity.
        """
        import random

        pool = self.by_grade_topic(grade, topic_id)
        if not pool:
            return None

        exclude = set(exclude_ids or [])
        pool = [q for q in pool if q.id not in exclude]
        if not pool:
            return None

        # Get IRT-b for each question
        def get_b(q: QuestionV2) -> float:
            if q.irt_b is not None:
                return q.irt_b
            if q.irt_params and isinstance(q.irt_params, dict):
                return q.irt_params.get('b', 0.0)
            return 0.0

        # Find questions near student's theta
        candidates = [q for q in pool if abs(get_b(q) - theta) <= window]
        if not candidates:
            # Widen: get closest 5
            candidates = sorted(pool, key=lambda q: abs(get_b(q) - theta))[:5]

        # Cluster diversity
        cluster_counts = dict(seen_clusters or {})
        preferred = []
        fallback = []
        for q in candidates:
            c = q.concept_cluster
            if c and cluster_counts.get(c, 0) >= max_per_cluster:
                fallback.append(q)
            else:
                preferred.append(q)

        active = preferred if preferred else fallback if fallback else candidates
        unseen = [q for q in active if not q.concept_cluster or cluster_counts.get(q.concept_cluster, 0) == 0]
        if unseen:
            return random.choice(unseen)
        return random.choice(active) if active else None

    # --- School queries ---

    def get_school_curriculum(self, curriculum: str, grade: int) -> Optional[SchoolCurriculum]:
        return self._school.get((curriculum, grade))

    def get_chapters(self, curriculum: str, grade: int) -> List[Dict[str, Any]]:
        """Get chapter list for school tab. Returns list of chapter dicts."""
        sc = self._school.get((curriculum, grade))
        if not sc:
            return []
        return [
            {
                'name': ch.chapter_name,
                'question_count': ch.total_questions,
                'skill_ids': ch.skill_ids,
                'adaptive_topic_ids': ch.adaptive_topic_ids,
                'question_ids': ch.question_ids,
            }
            for ch in sc.chapters
        ]

    def get_chapter_questions(
        self, curriculum: str, grade: int, chapter_name: str
    ) -> List[QuestionV2]:
        """Get questions for a specific chapter, resolved from adaptive store."""
        sc = self._school.get((curriculum, grade))
        if not sc:
            return []

        chapter = next((ch for ch in sc.chapters if ch.chapter_name == chapter_name), None)
        if not chapter:
            return []

        questions = [self._questions[qid] for qid in chapter.question_ids if qid in self._questions]
        return questions

    def available_curricula(self, grade: int) -> List[str]:
        """List curricula available for a grade."""
        return sorted(set(
            curr for (curr, g) in self._school if g == grade
        ))

    # --- Stats ---

    def stats(self) -> Dict:
        return {
            'total_questions': len(self._questions),
            'total_topics': len(self._topics),
            'grades': {
                g: {
                    'topics': len(topics),
                    'questions': sum(t.total_questions for t in topics),
                }
                for g, topics in self._by_grade.items()
            },
            'school_curricula': len(self._school),
        }


# Module-level singleton
store_v4 = ContentStoreV4()


def bootstrap_v4_from_env() -> None:
    """Called at app startup. Loads content-v4/ if available."""
    content_dir = os.environ.get('KIWIMATH_V4_CONTENT_DIR')
    if not content_dir:
        print("[content_store_v4] No KIWIMATH_V4_CONTENT_DIR set; store empty.")
        return

    root = Path(content_dir).expanduser().resolve()
    if not root.exists():
        print(f"[content_store_v4] WARNING: {root} does not exist")
        return

    print(f"[content_store_v4] loading content from {root}")
    n = store_v4.load(root)
    stats = store_v4.stats()
    print(f"[content_store_v4] TOTAL: {n} questions loaded: {stats}")
