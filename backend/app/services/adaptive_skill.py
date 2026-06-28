"""
Adaptive skill-ladder engine (concept-cluster based).

Each (level, topic) has an ordered **ladder of skills**. A *skill* is one concept
cluster: the canonical **skill question** (the cluster parent, `is_skill_original`)
followed by its **cluster questions** (number/wording variants), ordered by
difficulty. Skills themselves are ordered along the ladder by `skill_seq`
(the parent question's difficulty).

Rule (exactly as specified):
  - Show the **skill question** (cluster parent).
  - If answered **correct** → advance to the **next skill**; its cluster
    questions are skipped.
  - If answered **wrong** → show the next **cluster question**; keep showing
    them one by one until one is answered correct (→ next skill) or the cluster
    is **exhausted** (→ next skill anyway).

Per-user position — `(skill_index, cursor)` per (user, level, topic) — is
persisted in Firestore (in-memory fallback for local/tests) so a student who
logs out mid-topic **resumes exactly where they left off and never jumps back**
to questions already cleared.

The ladder is built from the content tags written by
`content-live/qa-reports/cluster_concepts.py`:
  skill_id · skill_rank (order within a cluster, 0 = parent) · is_skill_original
  · skill_seq (skill's position in the topic ladder).
"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from app.services.content_store_level import level_store
from app.services.state_store import FirestoreBackedStore

# Durable per-user position store (one Firestore doc per user; merges per topic).
_state = FirestoreBackedStore("adaptive_skill_state")


class AdaptiveSkillEngine:
    def __init__(self) -> None:
        # (level, topic) -> (ladder, qindex)
        #   ladder  : List[(skill_id, [qid, ...])]  parent first, then cluster qs
        #   qindex  : qid -> (skill_index, within_skill_index)
        self._cache: Dict[Tuple[str, str], Tuple[List[Tuple[str, List[str]]], Dict[str, Tuple[int, int]]]] = {}
        self._lock = threading.Lock()

    # --------------------------------------------------------------- ladder
    def _build(self, level: str, topic: str):
        qs = level_store.topic_questions(level, topic)
        groups: Dict[str, list] = defaultdict(list)
        for q in qs:
            sid = getattr(q, "skill_id", None) or q.id
            groups[sid].append(q)

        skills = []
        for sid, members in groups.items():
            # within a skill: parent first (skill_rank 0), then cluster qs by difficulty
            members.sort(key=lambda q: (
                q.skill_rank if getattr(q, "skill_rank", None) is not None else 0,
                q.id,
            ))
            seq = next((m.skill_seq for m in members if getattr(m, "skill_seq", None) is not None), 0)
            skills.append((seq, sid, [m.id for m in members]))

        # ladder order = difficulty (skill_seq), tie-break by skill_id for stability
        skills.sort(key=lambda t: (t[0], t[1]))
        ladder = [(sid, qids) for (_seq, sid, qids) in skills]
        qindex: Dict[str, Tuple[int, int]] = {}
        for si, (_sid, qids) in enumerate(ladder):
            for qi, qid in enumerate(qids):
                qindex[qid] = (si, qi)
        return ladder, qindex

    def _ladder(self, level: str, topic: str):
        key = (level, topic)
        cached = self._cache.get(key)
        if cached is None:
            with self._lock:
                cached = self._cache.get(key)
                if cached is None:
                    cached = self._build(level, topic)
                    self._cache[key] = cached
        return cached

    # ---------------------------------------------------------------- state
    @staticmethod
    def _cell_key(level: str, topic: str) -> str:
        return f"{level}|{topic}"

    @staticmethod
    def _as_int(v) -> int:
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    def _get_pos(self, user_id: str, level: str, topic: str) -> Tuple[int, int]:
        doc = _state.get(user_id) or {}
        cell = doc.get(self._cell_key(level, topic)) or {}
        return self._as_int(cell.get("pos", 0)), self._as_int(cell.get("cursor", 0))

    def _set_pos(self, user_id: str, level: str, topic: str, pos: int, cursor: int) -> None:
        _state.update(user_id, {self._cell_key(level, topic): {"pos": pos, "cursor": cursor}})

    # ----------------------------------------------------------- public api
    def next_qid(self, user_id: str, level: str, topic: str) -> Optional[str]:
        """The question the student should see right now (pure read — does NOT
        advance). None when the topic's ladder is finished."""
        ladder, _ = self._ladder(level, topic)
        if not ladder:
            return None
        pos, cursor = self._get_pos(user_id, level, topic)
        if pos >= len(ladder):
            return None
        _sid, qids = ladder[pos]
        if cursor >= len(qids):
            return None
        return qids[cursor]

    def record(self, user_id: str, level: str, topic: str, qid: str, correct: bool) -> None:
        """Advance the ladder per the rule. Monotonic — never regresses, so a
        re-answered earlier question can't drag the student backwards."""
        ladder, qindex = self._ladder(level, topic)
        if not ladder:
            return
        loc = qindex.get(qid)
        if loc is None:
            return
        si, qi = loc
        pos, cursor = self._get_pos(user_id, level, topic)
        # Only act on the question that is (or is ahead of) the live pointer.
        if si < pos:
            return  # already cleared this skill — ignore, don't jump back
        if correct:
            new_pos, new_cursor = si + 1, 0                 # clear skill → next skill
        else:
            nxt = qi + 1
            if nxt >= len(ladder[si][1]):
                new_pos, new_cursor = si + 1, 0             # cluster exhausted → next skill
            else:
                new_pos, new_cursor = si, nxt               # show next cluster question
        # Monotonic write: re-read immediately before persisting and never move
        # the saved position backwards. This protects "never jump back" against
        # out-of-order / concurrent answer writes (FirestoreBackedStore is not
        # transactional — a sub-millisecond TOCTOU window remains and is
        # accepted; the app also serialises answers, so this is belt-and-braces).
        cur_pos, cur_cursor = self._get_pos(user_id, level, topic)
        if (new_pos, new_cursor) < (cur_pos, cur_cursor):
            return
        self._set_pos(user_id, level, topic, new_pos, new_cursor)

    def status(self, user_id: str, level: str, topic: str) -> Dict:
        ladder, _ = self._ladder(level, topic)
        pos, cursor = self._get_pos(user_id, level, topic)
        cur_skill = ladder[pos][0] if 0 <= pos < len(ladder) else None
        return {
            "level": level, "topic": topic,
            "skills_total": len(ladder),
            "skill_index": pos,
            "on_cluster_question": cursor,          # 0 = on the skill question itself
            "current_skill_id": cur_skill,
            "completed": pos >= len(ladder),
        }

    def reset(self, user_id: str, level: str, topic: str) -> None:
        self._set_pos(user_id, level, topic, 0, 0)


engine_skill = AdaptiveSkillEngine()
