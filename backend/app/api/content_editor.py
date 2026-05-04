"""
Simple content editor API — reads/writes content-v2 JSON files directly.

No CMS/SQLite dependency. Works immediately after deploy.
Designed for non-technical content team to browse, edit, and fix questions.
"""

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/content-editor", tags=["Content Editor"])


def _content_root() -> Path:
    """Find content-v2 directory."""
    env = os.environ.get("KIWIMATH_V2_CONTENT_DIR")
    if env and Path(env).exists():
        return Path(env)
    for candidate in [
        Path(__file__).resolve().parent.parent.parent / "content-v2",
        Path.home() / "Downloads" / "kiwimath" / "content-v2",
    ]:
        if candidate.exists():
            return candidate
    raise HTTPException(500, "content-v2 directory not found")


def _load_all_questions() -> list[dict]:
    """Load all questions from topic JSON files in content-v2."""
    root = _content_root()
    all_qs = []

    # Only load from topic-* directories (skip _workspace, curriculum dirs, scripts, etc.)
    for topic_dir in sorted(root.iterdir()):
        if not topic_dir.is_dir() or not topic_dir.name.startswith("topic-"):
            continue
        for jf in sorted(topic_dir.glob("*.json")):
            if jf.name.startswith("."):
                continue
            try:
                data = json.loads(jf.read_text())
                questions = data if isinstance(data, list) else data.get("questions", [])
                for q in questions:
                    q["_source_file"] = str(jf.relative_to(root))
                    q["_topic_folder"] = topic_dir.name
                    if "topic_name" not in q:
                        q["topic_name"] = data.get("topic_name", topic_dir.name) if isinstance(data, dict) else topic_dir.name
                all_qs.extend(questions)
            except Exception:
                continue

    return all_qs


@router.get("/questions")
def list_questions(
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    mode: Optional[str] = None,
    flagged_only: bool = False,
    limit: int = Query(default=30, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List questions from content-v2 JSON with filters."""
    all_qs = _load_all_questions()

    # Filter
    filtered = all_qs
    if topic:
        filtered = [q for q in filtered if q.get("topic", "") == topic or q.get("_topic_folder", "") == topic]
    if difficulty:
        filtered = [q for q in filtered if q.get("difficulty_tier", "") == difficulty]
    if mode:
        filtered = [q for q in filtered if q.get("interaction_mode", "mcq") == mode]
    if search:
        s = search.lower()
        filtered = [q for q in filtered if s in q.get("stem", "").lower() or s in q.get("id", "").lower()]

    total = len(filtered)
    page = filtered[offset:offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "questions": page,
    }


@router.get("/questions/{qid}")
def get_question(qid: str):
    """Get a single question by ID."""
    all_qs = _load_all_questions()
    for q in all_qs:
        if q.get("id") == qid:
            return q
    raise HTTPException(404, f"Question {qid} not found")


@router.get("/topics")
def list_topics():
    """List all topics with question counts."""
    all_qs = _load_all_questions()
    topics = {}
    for q in all_qs:
        folder = q.get("_topic_folder", "unknown")
        name = q.get("topic_name", folder)
        if folder not in topics:
            topics[folder] = {"topic_id": q.get("topic", folder), "topic_name": name, "total": 0}
        topics[folder]["total"] += 1
    return {"topics": sorted(topics.values(), key=lambda t: t["topic_id"])}


class QuestionEdit(BaseModel):
    stem: Optional[str] = None
    choices: Optional[list[str]] = None
    correct_answer: Optional[int] = None
    difficulty_tier: Optional[str] = None
    difficulty_score: Optional[int] = None
    interaction_mode: Optional[str] = None
    tags: Optional[list[str]] = None
    hint: Optional[dict] = None
    diagnostics: Optional[dict] = None


@router.put("/questions/{qid}")
def update_question(qid: str, edit: QuestionEdit):
    """Update a question in its source JSON file."""
    root = _content_root()
    all_qs = _load_all_questions()

    # Find the question and its source file
    target = None
    for q in all_qs:
        if q.get("id") == qid:
            target = q
            break

    if not target:
        raise HTTPException(404, f"Question {qid} not found")

    source_file = root / target["_source_file"]
    if not source_file.exists():
        raise HTTPException(500, f"Source file not found: {target['_source_file']}")

    # Load the file
    data = json.loads(source_file.read_text())
    questions = data if isinstance(data, list) else data.get("questions", [])

    # Find and update the question
    updated = False
    for q in questions:
        if q.get("id") == qid:
            changes = edit.model_dump(exclude_none=True)
            for key, value in changes.items():
                q[key] = value
            updated = True
            break

    if not updated:
        raise HTTPException(404, f"Question {qid} not found in source file")

    # Write back
    source_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    return {"status": "saved", "question_id": qid, "file": target["_source_file"]}


@router.get("/stats")
def content_stats():
    """Quick stats about all content."""
    all_qs = _load_all_questions()

    by_topic = {}
    by_difficulty = {}
    by_mode = {}
    no_choices = 0
    no_hint = 0

    for q in all_qs:
        topic = q.get("_topic_folder", "unknown")
        by_topic[topic] = by_topic.get(topic, 0) + 1

        tier = q.get("difficulty_tier", "unknown")
        by_difficulty[tier] = by_difficulty.get(tier, 0) + 1

        mode = q.get("interaction_mode", "mcq")
        by_mode[mode] = by_mode.get(mode, 0) + 1

        if not q.get("choices"):
            no_choices += 1
        if not q.get("hint"):
            no_hint += 1

    return {
        "total_questions": len(all_qs),
        "by_topic": by_topic,
        "by_difficulty": by_difficulty,
        "by_mode": by_mode,
        "issues": {
            "no_choices": no_choices,
            "no_hint": no_hint,
        },
    }
