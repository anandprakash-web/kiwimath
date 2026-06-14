"""
Level/Grade Content Store — serves the consolidated remapped banks.

Reads the two canonical stores produced by the 2026-06-13 Level/Grade reorg:

    content-live/olympiad/L{1-8}/{Ln}_{PILLAR}_{topic}.json
        each file: {level, level_name, pillar, topic_key, display_name, questions:[...]}
        question ids: KM-L{n}-{PILLAR}-{serial}; legacy_id kept for back-refs.

    content-live/curriculum/{board}/grade{n}/questions.json   (board, grade, questions[])
    content-live/curriculum/{board}/grade{n}/chapters.json    (chapters[].question_ids)

The Olympiad section is LEVEL-based (L1-L8); the School section is GRADE-based
(1-6) x board x chapter. Pillars (NT/ALG/GEO/COM) are internal-only metadata —
the API exposes them for strand analytics but the app never shows them.

Questions are served from a lightweight wrapper (not the strict QuestionV2
pydantic model) because this content is already QA-verified and uses the new
KM-* id scheme that QuestionV2's legacy id validator would reject.

Env:
    KIWIMATH_OLYMPIAD_CONTENT_DIR   default: <repo>/content-live/olympiad
    KIWIMATH_CURRICULUM_CONTENT_DIR default: <repo>/content-live/curriculum
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LEVEL_NAMES = {
    "L1": "Grade 1-2", "L2": "Grade 3-4", "L3": "Grade 5-6", "L4": "Grade 7-8",
    "L5": "Grade 9-10 (IOQM)", "L6": "Olympiad (RMO)", "L7": "Olympiad (INMO)",
    "L8": "Olympiad (IMO)",
}
PILLAR_NAMES = {"NT": "Number Theory", "ALG": "Algebra", "GEO": "Geometry", "COM": "Combinatorics"}
BOARD_NAMES = {
    "ncert": "NCERT (CBSE)", "igcse": "Cambridge Primary", "icse": "ICSE",
    "singapore": "Singapore", "us-common-core": "US Common Core",
}


class LQ:
    """Lightweight, serve-ready question (the content is pre-validated)."""
    __slots__ = (
        "id", "stem", "choices", "correct_answer", "correct_value", "hint",
        "diagnostics", "visual_svg", "visual_requirement", "irt_b", "irt_params",
        "difficulty_tier", "difficulty_score", "interaction_mode", "skill_id",
        "solution_steps", "legacy_id",
    )

    def __init__(self, d: dict):
        self.id = str(d.get("id"))
        self.stem = d.get("stem", "")
        self.choices = d.get("choices") or []
        self.correct_answer = d.get("correct_answer", 0)
        self.correct_value = d.get("correct_value")
        self.hint = d.get("hint")
        self.diagnostics = d.get("diagnostics")
        self.visual_svg = d.get("visual_svg")
        self.visual_requirement = d.get("visual_requirement")
        self.irt_b = d.get("irt_b")
        self.irt_params = d.get("irt_params")
        self.difficulty_tier = d.get("difficulty_tier")
        self.difficulty_score = d.get("difficulty_score")
        self.interaction_mode = d.get("interaction_mode", "mcq")
        self.skill_id = d.get("skill_id")
        self.solution_steps = d.get("solution_steps")
        self.legacy_id = d.get("legacy_id")


def _chapter_sort_key(name: str) -> Tuple[float, str]:
    """Sort chapters numerically: 'Ch1' < 'Ch10', '1A' < '1B' < '2A'; named last."""
    m = re.match(r"^\s*(?:ch\.?|chapter)?\s*(\d+)\s*([A-Za-z])?", str(name), re.I)
    if m:
        sub = (ord(m.group(2).upper()) - 64) if m.group(2) else 0
        return (int(m.group(1)) * 100 + sub, name.lower())
    return (1e6, name.lower())


def _clean_chapter_name(name: str) -> str:
    """Strip a leading 'Ch12:' / '1A:' prefix for clean display."""
    return re.sub(r"^\s*(ch\.?|chapter)?\s*\d+[A-Za-z]?\s*[:.\-]?\s*", "", str(name), flags=re.I).strip() or name


class LevelTopic:
    __slots__ = ("level", "level_name", "pillar", "topic_key", "display_name", "questions")

    def __init__(self, data: dict):
        self.level: str = data["level"]
        self.level_name: str = data.get("level_name") or LEVEL_NAMES.get(self.level, self.level)
        self.pillar: str = data.get("pillar", "")
        self.topic_key: str = data["topic_key"]
        self.display_name: str = data.get("display_name", self.topic_key)
        self.questions: List[LQ] = []


class CurriculumGrade:
    __slots__ = ("board", "grade", "total_questions", "chapters", "_by_ref")

    def __init__(self, board: str, grade: int):
        self.board = board
        self.grade = grade
        self.total_questions = 0
        self.chapters: List[Dict[str, Any]] = []
        self._by_ref: Dict[str, LQ] = {}  # id / original_id / legacy_id -> question


class ContentStoreLevel:
    """Serves the remapped olympiad (level) + curriculum (grade) banks."""

    def __init__(self) -> None:
        self._questions: Dict[str, LQ] = {}
        self._alias: Dict[str, str] = {}                       # legacy_id -> KM id
        self._qid_meta: Dict[str, Tuple[str, str, str]] = {}   # qid -> (level, topic_key, pillar)
        self._topics: Dict[Tuple[str, str], LevelTopic] = {}   # (level, topic_key) -> topic
        self._by_level: Dict[str, List[LevelTopic]] = defaultdict(list)
        self._curriculum: Dict[Tuple[str, int], CurriculumGrade] = {}
        self._loaded = False

    # ------------------------------------------------------------------ load
    def load_olympiad(self, root: Path) -> int:
        count = 0
        for i in range(1, 9):
            level = f"L{i}"
            ldir = root / level
            if not ldir.exists():
                self._by_level.setdefault(level, [])
                continue
            for f in sorted(ldir.glob(f"{level}_*.json")):
                try:
                    data = json.loads(f.read_text())
                except Exception as e:  # noqa: BLE001
                    print(f"[content_store_level] skip {f.name}: {e}")
                    continue
                topic = LevelTopic(data)
                for qd in data.get("questions", []):
                    q = LQ(qd)
                    if not q.id:
                        continue
                    self._questions[q.id] = q
                    if q.legacy_id and q.legacy_id != q.id:
                        self._alias.setdefault(str(q.legacy_id), q.id)
                    self._qid_meta[q.id] = (topic.level, topic.topic_key, topic.pillar)
                    topic.questions.append(q)
                    count += 1
                self._topics[(topic.level, topic.topic_key)] = topic
                self._by_level[topic.level].append(topic)
        return count

    def load_curriculum(self, root: Path) -> int:
        count = 0
        if not root.exists():
            return 0
        for board_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            board = board_dir.name
            for grade in range(1, 7):
                gdir = board_dir / f"grade{grade}"
                if not gdir.is_dir():
                    continue
                cg = CurriculumGrade(board, grade)
                qfile = gdir / "questions.json"
                if qfile.exists():
                    try:
                        qdata = json.loads(qfile.read_text())
                    except Exception as e:  # noqa: BLE001
                        print(f"[content_store_level] skip {qfile}: {e}")
                        qdata = {}
                    for qd in qdata.get("questions", []):
                        q = LQ(qd)
                        if not q.id:
                            continue
                        for ref in (q.id, qd.get("original_id"), q.legacy_id):
                            if ref:
                                cg._by_ref.setdefault(str(ref), q)
                        self._questions.setdefault(q.id, q)
                        count += 1
                    cg.total_questions = qdata.get("total_questions", len(set(c.id for c in cg._by_ref.values())))
                cfile = gdir / "chapters.json"
                if cfile.exists():
                    try:
                        cdata = json.loads(cfile.read_text())
                        chs = cdata.get("chapters", cdata if isinstance(cdata, list) else [])
                        chs = chs if isinstance(chs, list) else list(chs.values())
                    except Exception:  # noqa: BLE001
                        chs = []
                    cleaned = []
                    for ch in chs:
                        cleaned.append({
                            "name": ch.get("chapter_name", "Chapter"),
                            "display_name": _clean_chapter_name(ch.get("chapter_name", "Chapter")),
                            "question_ids": ch.get("question_ids", []),
                            "total_questions": ch.get("total_questions", len(ch.get("question_ids", []))),
                        })
                    cleaned.sort(key=lambda c: _chapter_sort_key(c["name"]))
                    cg.chapters = cleaned
                self._curriculum[(board, grade)] = cg
        return count

    # ----------------------------------------------------------- olympiad api
    def levels(self) -> List[Dict[str, Any]]:
        out = []
        for i in range(1, 9):
            level = f"L{i}"
            topics = self._by_level.get(level, [])
            total = sum(len(t.questions) for t in topics)
            out.append({
                "level": level,
                "level_name": LEVEL_NAMES.get(level, level),
                "topic_count": sum(1 for t in topics if t.questions),
                "question_count": total,              # app hides this; useful internally
                "available": total > 0,
            })
        return out

    def topics(self, level: str) -> List[LevelTopic]:
        return self._by_level.get(level, [])

    def topic(self, level: str, topic_key: str) -> Optional[LevelTopic]:
        return self._topics.get((level, topic_key))

    def topic_questions(self, level: str, topic_key: str) -> List[LQ]:
        t = self._topics.get((level, topic_key))
        return t.questions if t else []

    def get(self, qid: str) -> Optional[LQ]:
        q = self._questions.get(qid)
        if q is None:
            alias = self._alias.get(qid)
            if alias:
                q = self._questions.get(alias)
        return q

    def meta(self, qid: str) -> Optional[Tuple[str, str, str]]:
        """Return (level, topic_key, pillar) for a question id."""
        if qid not in self._qid_meta:
            qid = self._alias.get(qid, qid)
        return self._qid_meta.get(qid)

    def pillar_of(self, qid: str) -> Optional[str]:
        m = self.meta(qid)
        return m[2] if m else None

    def pillar_for_topic(self, topic_key: str) -> Optional[str]:
        for (_lv, tk), t in self._topics.items():
            if tk == topic_key:
                return t.pillar
        return None

    def next_adaptive(
        self, level: str, topic_key: str, theta: float = 0.0,
        exclude_ids: Optional[List[str]] = None, window: float = 0.6,
    ) -> Optional[LQ]:
        import random
        pool = self.topic_questions(level, topic_key)
        if not pool:
            return None
        exclude = set(exclude_ids or [])
        pool = [q for q in pool if q.id not in exclude]
        if not pool:
            return None

        def b(q: LQ) -> float:
            if q.irt_b is not None:
                return q.irt_b
            if isinstance(q.irt_params, dict):
                return q.irt_params.get("b", 0.0)
            return 0.0

        near = [q for q in pool if abs(b(q) - theta) <= window]
        if not near:
            near = sorted(pool, key=lambda q: abs(b(q) - theta))[:5]
        return random.choice(near) if near else None

    # --------------------------------------------------------- curriculum api
    def boards(self) -> List[Dict[str, Any]]:
        order = ["ncert", "igcse", "icse", "singapore", "us-common-core"]
        present = {b for (b, _g) in self._curriculum}
        out = []
        for b in order + sorted(present - set(order)):
            if b in present and b not in [x["board"] for x in out]:
                total = sum(cg.total_questions for (bb, _g), cg in self._curriculum.items() if bb == b)
                out.append({"board": b, "name": BOARD_NAMES.get(b, b), "question_count": total})
        return out

    def grades(self, board: str) -> List[int]:
        return sorted(g for (b, g) in self._curriculum if b == board)

    def chapters(self, board: str, grade: int) -> List[Dict[str, Any]]:
        cg = self._curriculum.get((board, grade))
        if not cg:
            return []
        return [
            {"index": i + 1, "name": ch["name"], "display_name": ch["display_name"],
             "question_count": ch["total_questions"]}
            for i, ch in enumerate(cg.chapters)
        ]

    def chapter_questions(self, board: str, grade: int, chapter: str) -> List[LQ]:
        cg = self._curriculum.get((board, grade))
        if not cg:
            return []
        ch = next(
            (c for c in cg.chapters if c["name"] == chapter or c["display_name"] == chapter),
            None,
        )
        if not ch:
            return []
        out, seen = [], set()
        for ref in ch["question_ids"]:
            q = cg._by_ref.get(str(ref)) or self.get(str(ref))
            if q is not None and q.id not in seen:
                seen.add(q.id)
                out.append(q)
        return out

    def curriculum_total(self, board: str, grade: int) -> int:
        cg = self._curriculum.get((board, grade))
        return cg.total_questions if cg else 0

    # ----------------------------------------------------------------- stats
    def stats(self) -> Dict[str, Any]:
        levels = {
            lv: {
                "questions": sum(len(t.questions) for t in self._by_level.get(lv, [])),
                "topics": sum(1 for t in self._by_level.get(lv, []) if t.questions),
            }
            for lv in (f"L{i}" for i in range(1, 9))
        }
        oly_total = sum(v["questions"] for v in levels.values())
        cur_total = sum(cg.total_questions for cg in self._curriculum.values())
        return {
            "olympiad_total": oly_total,
            "curriculum_total": cur_total,
            "total_questions": oly_total + cur_total,
            "levels": levels,
            "curriculum_cells": len(self._curriculum),
        }


# Module-level singleton
level_store = ContentStoreLevel()


def _default(env: str, *parts: str) -> Path:
    val = os.environ.get(env)
    if val:
        return Path(val).expanduser().resolve()
    return (Path(__file__).resolve().parents[3] / Path(*parts)).resolve()


def bootstrap_level_from_env() -> None:
    """Load the remapped olympiad + curriculum banks at startup."""
    oly_root = _default("KIWIMATH_OLYMPIAD_CONTENT_DIR", "content-live", "olympiad")
    cur_root = _default("KIWIMATH_CURRICULUM_CONTENT_DIR", "content-live", "curriculum")
    n_oly = level_store.load_olympiad(oly_root) if oly_root.exists() else 0
    n_cur = level_store.load_curriculum(cur_root) if cur_root.exists() else 0
    level_store._loaded = True
    print(f"[content_store_level] olympiad={n_oly} from {oly_root} | curriculum={n_cur} from {cur_root}")
