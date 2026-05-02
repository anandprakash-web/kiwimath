"""
Smart Session Planner — builds adaptive 10-question sessions across all topics.

Replaces the old "pick a topic, get random questions" flow. The plan is computed
once when the student taps "Play" and the Flutter client walks through questions
one by one, calling /v2/answer/check for each.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from app.services.cluster_mastery_store import (
    ClusterMastery,
    get_cluster_mastery,
    get_mastered_clusters,
)
from app.services.content_store_v2 import QuestionV2, store_v2
from app.services.adaptive_engine_v2 import engine_v2, theta_to_difficulty
from app.services.mistake_tracker import mistake_tracker

GRADE_DIFFICULTY = {
    1: (1, 50),
    2: (51, 100),
    3: (101, 150),
    4: (151, 200),
    5: (201, 250),
    6: (251, 300),
}

SPACED_REVIEW_DAYS = 3
MIN_TOPIC_SPREAD = 4
MAX_PER_CLUSTER = 2


@dataclass
class PlannedQuestion:
    question_id: str
    topic_id: str
    topic_name: str
    concept_cluster: str
    difficulty_score: int
    priority_reason: str


@dataclass
class SessionPlan:
    user_id: str
    grade: int
    questions: List[PlannedQuestion]
    cluster_breakdown: Dict[str, int]
    topic_breakdown: Dict[str, int]
    total_mastered: int
    total_clusters: int


@dataclass
class _ClusterEntry:
    cluster_name: str
    topic_id: str
    topic_name: str
    questions: List[QuestionV2]
    priority: float
    reason: str


def _days_since(iso_str: str) -> float:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).total_seconds() / 86400
    except (ValueError, AttributeError):
        return 999.0


def _classify_cluster(
    cluster_name: str,
    mastery: Optional[ClusterMastery],
    mastered_set: Set[str],
) -> Tuple[float, str]:
    if mastery is None:
        return 4.0, "new_skill"

    if mastery.attempts > 0 and mastery.accuracy < 0.5:
        return 5.0, "weak_skill"

    if cluster_name in mastered_set:
        days = _days_since(mastery.last_seen)
        if days > SPACED_REVIEW_DAYS:
            return 1.0, "spaced_review"
        return 0.0, "recently_mastered"

    if mastery.accuracy < 0.8:
        return 3.0, "reinforcement"

    return 0.0, "recently_mastered"


def _pick_best_question(
    questions: List[QuestionV2],
    target_difficulty: int,
    used_ids: Set[str],
) -> Optional[QuestionV2]:
    available = [q for q in questions if q.id not in used_ids]
    if not available:
        return None
    available.sort(key=lambda q: abs(q.difficulty_score - target_difficulty))
    return available[0]


def _order_questions(questions: List[PlannedQuestion]) -> List[PlannedQuestion]:
    if len(questions) <= 3:
        return questions

    by_diff = sorted(questions, key=lambda q: q.difficulty_score)

    easy = by_diff[:3]
    hard = by_diff[3:-1] if len(by_diff) > 4 else by_diff[3:]
    closer = [by_diff[-1]] if len(by_diff) > 4 else []

    random.shuffle(hard)

    mid_idx = len(hard) // 2
    medium_candidates = sorted(hard, key=lambda q: q.difficulty_score)
    if medium_candidates:
        closer_q = medium_candidates[mid_idx]
        hard = [q for q in hard if q.question_id != closer_q.question_id]
        closer = [closer_q]

    return easy + hard + closer


def plan_session(
    user_id: str,
    grade: int,
    session_size: int = 10,
) -> SessionPlan:
    mastery_map = get_cluster_mastery(user_id)
    mastered_set = get_mastered_clusters(user_id)

    diff_range = GRADE_DIFFICULTY.get(grade, (1, 50))
    min_d, max_d = diff_range

    cluster_questions: Dict[str, List[QuestionV2]] = defaultdict(list)
    cluster_topic: Dict[str, Tuple[str, str]] = {}
    all_clusters: Set[str] = set()

    for topic_meta in store_v2.topics():
        topic_id = topic_meta.topic_id
        questions = store_v2.by_difficulty_range(topic_id, min_d, max_d)
        for q in questions:
            cluster = q.concept_cluster or f"{topic_id}/_default"
            cluster_questions[cluster].append(q)
            cluster_topic[cluster] = (topic_id, q.topic_name)
            all_clusters.add(cluster)

    entries: List[_ClusterEntry] = []
    for cluster, qs in cluster_questions.items():
        mastery = mastery_map.get(cluster)
        priority, reason = _classify_cluster(cluster, mastery, mastered_set)
        tid, tname = cluster_topic[cluster]
        entries.append(_ClusterEntry(
            cluster_name=cluster,
            topic_id=tid,
            topic_name=tname,
            questions=qs,
            priority=priority,
            reason=reason,
        ))

    entries.sort(key=lambda e: (e.priority, random.random()), reverse=True)

    planned: List[PlannedQuestion] = []
    used_ids: Set[str] = set()
    cluster_counts: Dict[str, int] = defaultdict(int)
    topic_counts: Dict[str, int] = defaultdict(int)

    ability_cache: Dict[str, int] = {}

    def _target_difficulty(topic_id: str) -> int:
        if topic_id not in ability_cache:
            ability = engine_v2.get_ability(user_id, topic_id)
            ability_cache[topic_id] = theta_to_difficulty(ability.theta)
        return ability_cache[topic_id]

    def _try_add_from_cluster(entry: _ClusterEntry, max_q: int) -> int:
        added = 0
        target = _target_difficulty(entry.topic_id)
        for _ in range(max_q):
            if len(planned) >= session_size:
                break
            q = _pick_best_question(entry.questions, target, used_ids)
            if q is None:
                break
            planned.append(PlannedQuestion(
                question_id=q.id,
                topic_id=entry.topic_id,
                topic_name=entry.topic_name,
                concept_cluster=entry.cluster_name,
                difficulty_score=q.difficulty_score,
                priority_reason=entry.reason,
            ))
            used_ids.add(q.id)
            cluster_counts[entry.cluster_name] += 1
            topic_counts[entry.topic_id] += 1
            added += 1
        return added

    for entry in entries:
        if len(planned) >= session_size:
            break
        if entry.priority <= 0 and len(planned) >= session_size // 2:
            continue
        if cluster_counts[entry.cluster_name] >= MAX_PER_CLUSTER:
            continue

        slots = MAX_PER_CLUSTER - cluster_counts[entry.cluster_name]

        unique_topics = len(topic_counts)
        if unique_topics < MIN_TOPIC_SPREAD and topic_counts.get(entry.topic_id, 0) >= 2:
            if any(
                e.topic_id not in topic_counts and e.priority > 0
                for e in entries
                if cluster_counts[e.cluster_name] < MAX_PER_CLUSTER
            ):
                slots = min(slots, 1)

        _try_add_from_cluster(entry, slots)

    if len(planned) < session_size:
        for entry in entries:
            if len(planned) >= session_size:
                break
            remaining = MAX_PER_CLUSTER - cluster_counts[entry.cluster_name]
            if remaining > 0:
                _try_add_from_cluster(entry, remaining)

    # ------------------------------------------------------------------
    # Mix in revision questions from the mistake tracker
    # Target: 2-3 revision questions per 10-question session
    # ------------------------------------------------------------------
    revision_target = max(1, session_size * 3 // 10)  # ~30% revision slots
    revision_candidates = mistake_tracker.get_revision_question_ids(
        student_id=user_id,
        max_items=revision_target,
    )

    revision_added = 0
    for rc in revision_candidates:
        qid = rc["question_id"]
        if qid in used_ids:
            continue
        # Verify the question still exists in the content store
        q = store_v2.get(qid)
        if q is None:
            continue
        # Check if it's within the grade difficulty range
        if not (min_d <= q.difficulty_score <= max_d):
            continue

        # If we're at capacity, replace the last non-revision question
        if len(planned) >= session_size:
            # Find a non-revision question to replace (from the end)
            replaced = False
            for idx in range(len(planned) - 1, -1, -1):
                if planned[idx].priority_reason != "revision":
                    planned.pop(idx)
                    replaced = True
                    break
            if not replaced:
                break  # All slots are already revision — stop

        planned.append(PlannedQuestion(
            question_id=qid,
            topic_id=rc["topic_id"],
            topic_name=q.topic_name,
            concept_cluster=rc["concept_cluster"],
            difficulty_score=q.difficulty_score,
            priority_reason="revision",
        ))
        used_ids.add(qid)
        cluster_counts[rc["concept_cluster"]] = cluster_counts.get(rc["concept_cluster"], 0) + 1
        topic_counts[rc["topic_id"]] = topic_counts.get(rc["topic_id"], 0) + 1
        revision_added += 1

    planned = _order_questions(planned)

    return SessionPlan(
        user_id=user_id,
        grade=grade,
        questions=planned,
        cluster_breakdown=dict(cluster_counts),
        topic_breakdown=dict(topic_counts),
        total_mastered=len(mastered_set),
        total_clusters=len(all_clusters),
    )
