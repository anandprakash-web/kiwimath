"""
Kiwimath Admin API — Content Management System routes.

All routes under /admin/* for question CRUD, workflow management,
QA checks, reviews, version history, and bulk operations.
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.cms_store import get_cms_store, run_qa_checks, qa_pass_count

router = APIRouter(prefix="/admin", tags=["Admin CMS"])


# ── New Pydantic Models for War Room Features ─────────────────────


# ── Pydantic Models ────────────────────────────────────────────────

class QuestionCreate(BaseModel):
    id: Optional[str] = None
    topic_id: str
    topic_name: str = ""
    topic_folder: str = ""
    stem: str
    original_stem: str = ""
    choices: list[str] = Field(min_length=4, max_length=4)
    correct_answer: int = Field(ge=0, le=3)
    difficulty_tier: str = "easy"
    difficulty_score: int = Field(ge=1, le=100, default=50)
    visual_svg: Optional[str] = None
    visual_alt: Optional[str] = None
    diagnostics: dict = {}
    hint: dict = {}
    tags: list[str] = []


class QuestionUpdate(BaseModel):
    stem: Optional[str] = None
    choices: Optional[list[str]] = None
    correct_answer: Optional[int] = None
    difficulty_tier: Optional[str] = None
    difficulty_score: Optional[int] = None
    visual_svg: Optional[str] = None
    diagnostics: Optional[dict] = None
    hint: Optional[dict] = None
    tags: Optional[list[str]] = None
    topic_id: Optional[str] = None
    topic_name: Optional[str] = None


class ReviewRequest(BaseModel):
    action: str = Field(description="approve, reject, flag, or comment")
    reviewer: str = "Anand"
    notes: str = ""


class TransitionRequest(BaseModel):
    state: str = Field(description="draft, review, approved, published, archived")
    author: str = "Anand"


class BulkImportRequest(BaseModel):
    questions: list[dict]
    author: str = "system"
    state: str = "published"


# ── Question CRUD ──────────────────────────────────────────────────

@router.post("/questions")
def create_question(q: QuestionCreate):
    """Create a new question in draft state."""
    store = get_cms_store()
    result = store.create_question(q.model_dump(), author="admin")
    return result


@router.get("/questions")
def list_questions(
    topic_id: Optional[str] = None,
    difficulty: Optional[str] = None,
    state: Optional[str] = None,
    qa_max: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List questions with filters."""
    store = get_cms_store()
    return store.list_questions(
        topic_id=topic_id, difficulty=difficulty, state=state,
        qa_max=qa_max, search=search, limit=limit, offset=offset,
    )


@router.get("/questions/{qid}")
def get_question(qid: str):
    """Get a single question with full details."""
    store = get_cms_store()
    q = store.get_question(qid)
    if not q:
        raise HTTPException(404, f"Question {qid} not found")
    return q


@router.put("/questions/{qid}")
def update_question(qid: str, data: QuestionUpdate, author: str = "admin",
                    change_note: str = ""):
    """Update a question. Auto-runs QA and saves version."""
    store = get_cms_store()
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    result = store.update_question(qid, updates, author=author, change_note=change_note)
    if not result:
        raise HTTPException(404, f"Question {qid} not found")
    return result


@router.delete("/questions/{qid}")
def delete_question(qid: str):
    """Delete a question and all its versions/reviews."""
    store = get_cms_store()
    if not store.delete_question(qid):
        raise HTTPException(404, f"Question {qid} not found")
    return {"deleted": qid}


# ── Workflow ──────────────────────────────────────────────────────

@router.post("/questions/{qid}/transition")
def transition_state(qid: str, req: TransitionRequest):
    """Move question to a new workflow state."""
    store = get_cms_store()
    try:
        result = store.transition_state(qid, req.state, req.author)
        if not result:
            raise HTTPException(404, f"Question {qid} not found")
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/questions/{qid}/publish")
def publish_question(qid: str, author: str = "Anand"):
    """Shortcut: move question directly to published (must pass QA ≥8/10)."""
    store = get_cms_store()
    try:
        result = store.transition_state(qid, "published", author)
        if not result:
            raise HTTPException(404, f"Question {qid} not found")
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Reviews ──────────────────────────────────────────────────────

@router.post("/questions/{qid}/review")
def review_question(qid: str, req: ReviewRequest):
    """Submit a review action (approve/reject/flag/comment)."""
    store = get_cms_store()
    if not store.get_question(qid):
        raise HTTPException(404, f"Question {qid} not found")
    return store.add_review(qid, req.action, req.reviewer, req.notes)


@router.get("/questions/{qid}/reviews")
def get_reviews(qid: str):
    """Get review history for a question."""
    store = get_cms_store()
    return store.get_reviews(qid)


# ── Version History ──────────────────────────────────────────────

@router.get("/questions/{qid}/versions")
def get_versions(qid: str):
    """Get version history for a question."""
    store = get_cms_store()
    return store.get_versions(qid)


@router.get("/questions/{qid}/versions/{version}")
def get_version_snapshot(qid: str, version: int):
    """Get the full snapshot of a specific version."""
    store = get_cms_store()
    snapshot = store.get_version_snapshot(qid, version)
    if not snapshot:
        raise HTTPException(404, f"Version {version} not found for {qid}")
    return snapshot


# ── QA ──────────────────────────────────────────────────────────

@router.post("/questions/{qid}/qa-check")
def qa_check(qid: str):
    """Run 10-point QA check on a question."""
    store = get_cms_store()
    q = store.get_question(qid)
    if not q:
        raise HTTPException(404, f"Question {qid} not found")

    results = run_qa_checks(q)
    passed, total = qa_pass_count(results)
    return {
        "question_id": qid,
        "score": f"{passed}/{total}",
        "passed": passed,
        "total": total,
        "checks": results,
    }


@router.post("/qa/batch")
def qa_batch(topic_id: Optional[str] = None, state: Optional[str] = None):
    """Run QA on all questions matching filters. Returns summary."""
    store = get_cms_store()
    result = store.list_questions(topic_id=topic_id, state=state, limit=10000)
    questions = result["questions"]

    issues = []
    for q in questions:
        qa = run_qa_checks(q)
        failures = [c for c in qa if not c["passed"]]
        if failures:
            issues.append({
                "id": q["id"],
                "topic": q["topic_name"],
                "score": f"{len(qa) - len(failures)}/{len(qa)}",
                "failures": [f["check"] for f in failures],
            })

    return {
        "total_checked": len(questions),
        "issues_found": len(issues),
        "clean": len(questions) - len(issues),
        "pass_rate": round((len(questions) - len(issues)) / max(len(questions), 1) * 100, 1),
        "issues": issues,
    }


# ── Bulk Import/Export ───────────────────────────────────────────

@router.post("/import")
def import_questions(req: BulkImportRequest):
    """Bulk import questions from JSON array."""
    store = get_cms_store()
    return store.import_questions(req.questions, author=req.author, state=req.state)


@router.post("/import-from-content")
def import_from_content_dir():
    """Import all questions from the content-v2/ directory."""
    # Find content dir
    content_dir = os.environ.get("KIWIMATH_V2_CONTENT_DIR")
    if not content_dir:
        # Try relative paths
        for candidate in [
            Path(__file__).parent.parent.parent.parent / "content-v2",
            Path(__file__).parent.parent.parent / "content-v2",
            Path.home() / "Downloads" / "kiwimath" / "content-v2",
        ]:
            if candidate.exists():
                content_dir = str(candidate)
                break

    if not content_dir or not Path(content_dir).exists():
        raise HTTPException(400, "content-v2/ directory not found. Set KIWIMATH_V2_CONTENT_DIR env var.")

    manifest_path = Path(content_dir) / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(400, "manifest.json not found in content directory")

    manifest = json.loads(manifest_path.read_text())
    all_questions = []

    for topic in manifest.get("topics", []):
        qfile = Path(content_dir) / topic["folder"] / "questions.json"
        if qfile.exists():
            data = json.loads(qfile.read_text())
            for q in data.get("questions", []):
                q["_topic_folder"] = topic["folder"]
                q["_topic_display"] = topic["topic_name"]
                q["topic_id"] = topic.get("topic_id", q.get("topic", ""))
                q["topic_name"] = topic["topic_name"]
                q["topic_folder"] = topic["folder"]
            all_questions.extend(data.get("questions", []))

    store = get_cms_store()
    return store.import_questions(all_questions, author="system", state="published")


@router.post("/purge-and-reimport")
def purge_and_reimport():
    """Delete ALL existing questions from CMS and reimport only from content-v2/.
    Use this to clean out V1 questions and load only V2 content."""
    store = get_cms_store()

    # 1. Purge all questions
    cur = store.conn.cursor()
    old_count = cur.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    cur.executescript("""
        DELETE FROM question_analytics;
        DELETE FROM versions;
        DELETE FROM reviews;
        DELETE FROM ai_calibration;
        DELETE FROM student_reactions;
        DELETE FROM parent_flags;
        DELETE FROM ab_results;
        DELETE FROM ab_tests;
        DELETE FROM templates;
        DELETE FROM question_assets;
        DELETE FROM questions;
    """)
    store.conn.commit()

    # 2. Find content-v2 directory
    content_dir = os.environ.get("KIWIMATH_V2_CONTENT_DIR")
    if not content_dir:
        for candidate in [
            Path(__file__).parent.parent.parent.parent / "content-v2",
            Path(__file__).parent.parent.parent / "content-v2",
            Path.home() / "Downloads" / "kiwimath" / "content-v2",
        ]:
            if candidate.exists():
                content_dir = str(candidate)
                break

    if not content_dir or not Path(content_dir).exists():
        raise HTTPException(400, "content-v2/ directory not found")

    # 3. Load manifest and import all topics
    manifest_path = Path(content_dir) / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(400, "manifest.json not found")

    manifest = json.loads(manifest_path.read_text())
    all_questions = []

    for topic in manifest.get("topics", []):
        qfile = Path(content_dir) / topic["folder"] / "questions.json"
        if qfile.exists():
            data = json.loads(qfile.read_text())
            for q in data.get("questions", []):
                q["topic_id"] = topic.get("topic_id", q.get("topic", ""))
                q["topic_name"] = topic["topic_name"]
                q["topic_folder"] = topic["folder"]
            all_questions.extend(data.get("questions", []))

    result = store.import_questions(all_questions, author="system", state="published")
    result["purged"] = old_count
    return result


@router.post("/visual-review/{qid}/remove-visual")
def remove_visual(qid: str):
    """Mark a question as not needing a visual — removes visual_svg reference."""
    store = get_cms_store()
    q = store.get_question(qid)
    if not q:
        raise HTTPException(404, f"Question {qid} not found")

    cur = store.conn.cursor()
    cur.execute(
        "UPDATE questions SET visual_svg=NULL, visual_alt=NULL, updated_at=? WHERE id=?",
        (time.time(), qid),
    )
    store.conn.commit()

    # Also update the content-v2 JSON file
    _sync_visual_removal_to_content(qid)

    return {"status": "ok", "id": qid, "message": "Visual removed"}


@router.post("/visual-review/{qid}/run-qa")
def run_visual_qa(qid: str):
    """Run QA checks on a single question and return detailed results."""
    store = get_cms_store()
    q = store.get_question(qid)
    if not q:
        raise HTTPException(404, f"Question {qid} not found")

    from ..services.cms_store import run_qa_checks
    qa_results = run_qa_checks(q)

    # Additional visual-specific QA
    visual_checks = []
    svg_file = q.get("visual_svg")
    if svg_file:
        # Check SVG exists on disk
        content_dir = _find_content_dir()
        if content_dir:
            topic_folder = q.get("topic_folder", "")
            svg_path = Path(content_dir) / topic_folder / "visuals" / svg_file
            svg_found = svg_path.exists()
            visual_checks.append({
                "check": "svg_file_exists",
                "passed": svg_found,
                "detail": f"SVG file {svg_file} {'found' if svg_found else 'NOT FOUND'} on disk",
            })
            if svg_found:
                content = svg_path.read_text()
                visual_checks.append({
                    "check": "svg_valid",
                    "passed": "<svg" in content and len(content) > 50,
                    "detail": f"SVG content valid ({len(content)} bytes)",
                })
                # Check stem-visual alignment (basic keyword matching)
                stem_lower = q.get("stem", "").lower()
                stem_nums = re.findall(r'\b(\d+)\b', stem_lower)
                svg_nums = re.findall(r'\b(\d+)\b', content)
                overlap = set(stem_nums) & set(svg_nums)
                visual_checks.append({
                    "check": "stem_visual_alignment",
                    "passed": len(overlap) > 0 or not stem_nums,
                    "detail": f"Stem numbers: {stem_nums[:5]}, SVG numbers: {svg_nums[:5]}, overlap: {list(overlap)[:5]}",
                })

    # Answer correctness check
    stem = q.get("stem", "")
    choices = q.get("choices", [])
    correct_idx = q.get("correct_answer", -1)
    correct_val = str(choices[correct_idx]) if 0 <= correct_idx < len(choices) else "?"

    # Try to verify answer for arithmetic/counting questions
    answer_check = {"check": "answer_plausible", "passed": True, "detail": f"Correct answer: {correct_val}"}
    nums = [int(n) for n in re.findall(r'\b(\d+)\b', stem)]
    if "+" in stem and len(nums) >= 2:
        expected = sum(nums[:2])
        if str(expected) in [str(c) for c in choices]:
            answer_check["detail"] += f" (sum of {nums[0]}+{nums[1]}={expected})"
            answer_check["passed"] = str(expected) == correct_val

    # Hint quality check
    hint = q.get("hint", {})
    hint_check = {
        "check": "hint_quality",
        "passed": isinstance(hint, dict) and len(hint) >= 5,
        "detail": f"Hint has {len(hint) if isinstance(hint, dict) else 0} levels",
    }

    all_results = qa_results + visual_checks + [answer_check, hint_check]
    passed = sum(1 for r in all_results if r["passed"])
    total = len(all_results)

    # Update QA score in DB
    cur = store.conn.cursor()
    cur.execute(
        "UPDATE questions SET qa_score=?, qa_results=?, updated_at=? WHERE id=?",
        (passed, json.dumps(all_results), time.time(), qid),
    )
    store.conn.commit()

    return {
        "id": qid,
        "qa_score": f"{passed}/{total}",
        "passed": passed,
        "total": total,
        "results": all_results,
    }


def _find_content_dir():
    """Find the content-v2 directory."""
    content_dir = os.environ.get("KIWIMATH_V2_CONTENT_DIR")
    if content_dir:
        return content_dir
    for candidate in [
        Path(__file__).parent.parent.parent.parent / "content-v2",
        Path(__file__).parent.parent.parent / "content-v2",
        Path.home() / "Downloads" / "kiwimath" / "content-v2",
    ]:
        if candidate.exists():
            return str(candidate)
    return None


def _sync_visual_removal_to_content(qid: str):
    """When visual is removed in CMS, also update the content-v2 JSON."""
    content_dir = _find_content_dir()
    if not content_dir:
        return
    # Determine topic from question ID prefix
    prefix_map = {
        "T1": "topic-1-counting", "T2": "topic-2-arithmetic",
        "T3": "topic-3-patterns", "T4": "topic-4-logic",
        "T5": "topic-5-spatial", "T6": "topic-6-shapes",
        "T7": "topic-7-word-problems", "T8": "topic-8-puzzles",
    }
    prefix = qid.split("-")[0]
    folder = prefix_map.get(prefix)
    if not folder:
        return
    qfile = Path(content_dir) / folder / "questions.json"
    if not qfile.exists():
        return
    data = json.loads(qfile.read_text())
    for q in data.get("questions", []):
        if q["id"] == qid:
            q["visual_svg"] = None
            q["visual_alt"] = None
            break
    qfile.write_text(json.dumps(data, indent=2))


@router.get("/export")
def export_published():
    """Export all published questions in content-v2/ format."""
    store = get_cms_store()
    return store.export_published()


@router.post("/export-to-files")
def export_to_files():
    """Export published questions to content-v2/ directory as JSON files."""
    store = get_cms_store()
    topics = store.export_published()

    content_dir = os.environ.get("KIWIMATH_V2_CONTENT_DIR")
    if not content_dir:
        for candidate in [
            Path(__file__).parent.parent.parent.parent / "content-v2",
            Path(__file__).parent.parent.parent / "content-v2",
            Path.home() / "Downloads" / "kiwimath" / "content-v2",
        ]:
            if candidate.exists():
                content_dir = str(candidate)
                break

    if not content_dir:
        raise HTTPException(400, "content-v2/ directory not found")

    written = []
    for tid, topic_data in topics.items():
        # Find matching folder
        folder_name = None
        for q in topic_data["questions"]:
            if q.get("topic_folder") or q.get("_topic_folder"):
                folder_name = q.get("topic_folder") or q.get("_topic_folder")
                break

        if not folder_name:
            folder_name = f"topic-{tid}"

        out_dir = Path(content_dir) / folder_name
        out_dir.mkdir(exist_ok=True)
        out_file = out_dir / "questions.json"

        # Clean export (remove CMS-only fields)
        export_data = {
            "topic_id": topic_data["topic_id"],
            "topic_name": topic_data["topic_name"],
            "version": "2.0",
            "total_questions": topic_data["total_questions"],
            "difficulty_distribution": topic_data["difficulty_distribution"],
            "questions": topic_data["questions"],
        }

        out_file.write_text(json.dumps(export_data, indent=2, ensure_ascii=False))
        written.append(str(out_file))

    return {"exported_files": written, "total_topics": len(topics)}


# ── Dashboard ────────────────────────────────────────────────────

@router.get("/dashboard")
def dashboard():
    """Get CMS dashboard with pipeline stats, topic coverage, QA health, War Room summary."""
    store = get_cms_store()
    return store.dashboard()


# ── War Room ─────────────────────────────────────────────────────

@router.get("/war-room")
def war_room(limit: int = Query(default=50, le=200)):
    """The 'Problem Child' queue — top underperforming questions sorted by urgency.
    urgency = 0.35*error_rate + 0.25*abandon_rate + 0.20*hint_reliance + 0.20*latency_index
    Red flag: error_rate > 20% OR avg_latency > 60s OR abandon > 15%"""
    store = get_cms_store()
    return store.war_room(limit=limit)


@router.post("/questions/{qid}/record-attempt")
def record_attempt(qid: str, correct: bool, latency_sec: float,
                   hints_used: int = 0, abandoned: bool = False,
                   first_try: bool = True):
    """Record a student attempt — updates War Room analytics."""
    store = get_cms_store()
    return store.update_analytics(qid, correct, latency_sec, hints_used, abandoned, first_try)


@router.post("/questions/{qid}/frustration-signal")
def frustration_signal(qid: str):
    """Record a student 'I'm stuck' tap."""
    store = get_cms_store()
    store.record_frustration(qid)
    return {"recorded": True, "question_id": qid}


# ── A/B Testing ──────────────────────────────────────────────────

class ABTestCreate(BaseModel):
    hypothesis: str = ""
    author: str = "Anand"


@router.post("/questions/{qid}/ab-test")
def create_ab_test(qid: str, req: ABTestCreate):
    """Create an A/B test — duplicates question as variant B for editing."""
    store = get_cms_store()
    try:
        return store.create_ab_test(qid, req.hypothesis, req.author)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/ab-tests")
def list_ab_tests(status: Optional[str] = None):
    """List all A/B tests with per-variant result stats."""
    store = get_cms_store()
    return store.list_ab_tests(status)


class ABResultRecord(BaseModel):
    variant: str
    student_id: str = ""
    correct: bool = False
    latency_sec: float = 0.0
    hints_used: int = 0
    emoji: Optional[str] = None


@router.post("/ab-tests/{test_id}/result")
def record_ab_result(test_id: str, req: ABResultRecord):
    """Record a student result for an A/B test variant."""
    store = get_cms_store()
    store.record_ab_result(test_id, req.variant, req.student_id,
                           req.correct, req.latency_sec, req.hints_used, req.emoji)
    return {"recorded": True}


# ── Variable Templates ───────────────────────────────────────────

class TemplateCreate(BaseModel):
    variable_ranges: dict = Field(description='e.g. {"val1": [1, 9], "val2": [1, 9]}')


@router.post("/questions/{qid}/template")
def create_template(qid: str, req: TemplateCreate):
    """Create a parametric template from a question with variable ranges."""
    store = get_cms_store()
    try:
        return store.create_template(qid, req.variable_ranges)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/templates/{template_id}/generate")
def generate_instances(template_id: str, count: int = Query(default=10, le=100)):
    """Generate N unique question instances from a template."""
    store = get_cms_store()
    try:
        return store.generate_instances(template_id, count)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/templates")
def list_templates():
    """List all variable templates."""
    store = get_cms_store()
    return store.list_templates()


# ── AI Difficulty Calibration ────────────────────────────────────

@router.post("/qa/ai-calibrate")
def ai_calibrate():
    """AI scan: flag questions with inconsistent difficulty, grade mismatches, and outliers."""
    store = get_cms_store()
    return store.ai_calibrate()


@router.get("/qa/calibration-flags")
def get_calibration_flags(question_id: Optional[str] = None):
    """Get unresolved AI calibration flags."""
    store = get_cms_store()
    return store.get_calibration_flags(question_id)


# ── Student/Parent Feedback ──────────────────────────────────────

class EmojiReaction(BaseModel):
    student_id: str = ""
    emoji: str = Field(description="happy, bored, or frustrated")


@router.post("/questions/{qid}/emoji-reaction")
def emoji_reaction(qid: str, req: EmojiReaction):
    """Record student emoji reaction after a question."""
    if req.emoji not in ("happy", "bored", "frustrated"):
        raise HTTPException(400, "Emoji must be: happy, bored, or frustrated")
    store = get_cms_store()
    store.record_emoji_reaction(qid, req.student_id, req.emoji)
    return {"recorded": True}


class ParentFlagCreate(BaseModel):
    parent_id: str = ""
    parent_name: str = ""
    comment: str


@router.post("/questions/{qid}/parent-flag")
def add_parent_flag(qid: str, req: ParentFlagCreate):
    """Pin a parent comment to a specific question."""
    store = get_cms_store()
    return store.add_parent_flag(qid, req.parent_id, req.parent_name, req.comment)


@router.post("/parent-flags/{flag_id}/resolve")
def resolve_parent_flag(flag_id: int, resolved_by: str = "Anand"):
    """Mark a parent flag as resolved."""
    store = get_cms_store()
    store.resolve_parent_flag(flag_id, resolved_by)
    return {"resolved": True}


@router.get("/questions/{qid}/feedback")
def get_feedback(qid: str):
    """Get all feedback for a question — emoji reactions + parent flags + frustration signals."""
    store = get_cms_store()
    return store.get_feedback(qid)


# ── Rollback ─────────────────────────────────────────────────────

@router.post("/questions/{qid}/rollback/{version}")
def rollback_question(qid: str, version: int, author: str = "Anand"):
    """One-click rollback: restore question to a specific version."""
    store = get_cms_store()
    try:
        result = store.rollback(qid, version, author)
        if not result:
            raise HTTPException(404, f"Question {qid} not found")
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


# ══════════════════════════════════════════════════════════════════
# GLOBAL ASSET LIBRARY
# ══════════════════════════════════════════════════════════════════


class AssetCreate(BaseModel):
    name: str
    asset_type: str = "svg"
    svg_data: Optional[str] = None
    file_ref: Optional[str] = None
    alt_text: str = ""
    functional_tags: list[str] = []
    scaling_tags: list[str] = []
    theme: str = ""
    mood: str = ""
    curriculum_path: str = ""
    cognitive_skill: str = ""
    visual_aid_type: str = ""
    grade_range: str = ""
    width: int = 0
    height: int = 0


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    svg_data: Optional[str] = None
    file_ref: Optional[str] = None
    alt_text: Optional[str] = None
    functional_tags: Optional[list[str]] = None
    scaling_tags: Optional[list[str]] = None
    theme: Optional[str] = None
    mood: Optional[str] = None
    curriculum_path: Optional[str] = None
    cognitive_skill: Optional[str] = None
    visual_aid_type: Optional[str] = None
    grade_range: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class AssetLinkRequest(BaseModel):
    question_id: str
    asset_id: str
    role: str = "primary_visual"


class BulkReplaceRequest(BaseModel):
    old_asset_id: str
    new_asset_id: str


# ── Asset CRUD ────────────────────────────────────────────────────

@router.post("/assets")
def create_asset(data: AssetCreate, author: str = "admin"):
    """Create a new asset in the Global Asset Library."""
    store = get_cms_store()
    return store.create_asset(data.model_dump(), author=author)


@router.get("/assets")
def list_assets(
    asset_type: Optional[str] = None,
    theme: Optional[str] = None,
    functional_tag: Optional[str] = None,
    curriculum_path: Optional[str] = None,
    visual_aid_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List assets with tag-based filters."""
    store = get_cms_store()
    return store.list_assets(
        asset_type=asset_type, theme=theme, functional_tag=functional_tag,
        curriculum_path=curriculum_path, visual_aid_type=visual_aid_type,
        search=search, limit=limit, offset=offset,
    )


@router.get("/assets/dashboard")
def asset_dashboard():
    """Asset Library dashboard — stats, counts by type/theme/curriculum."""
    store = get_cms_store()
    return store.asset_dashboard()


@router.get("/assets/orphans")
def find_orphan_references():
    """Detect orphan asset references, unlinked visuals, and unused assets."""
    store = get_cms_store()
    return store.find_orphan_references()


@router.get("/assets/{asset_id}")
def get_asset(asset_id: str):
    """Get a single asset with all metadata."""
    store = get_cms_store()
    asset = store.get_asset(asset_id)
    if not asset:
        raise HTTPException(404, f"Asset {asset_id} not found")
    return asset


@router.put("/assets/{asset_id}")
def update_asset(asset_id: str, data: AssetUpdate):
    """Update asset metadata. Changes propagate to all linked questions."""
    store = get_cms_store()
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    result = store.update_asset(asset_id, updates)
    if not result:
        raise HTTPException(404, f"Asset {asset_id} not found")
    return result


@router.delete("/assets/{asset_id}")
def delete_asset(asset_id: str):
    """Delete an asset. Blocked if questions still reference it."""
    store = get_cms_store()
    result = store.delete_asset(asset_id)
    if result.get("status") == "blocked":
        raise HTTPException(409, result)
    return result


@router.get("/assets/{asset_id}/usage")
def get_asset_usage(asset_id: str):
    """Get all questions that use this asset."""
    store = get_cms_store()
    if not store.get_asset(asset_id):
        raise HTTPException(404, f"Asset {asset_id} not found")
    return {"asset_id": asset_id, "questions": store.get_asset_usage(asset_id)}


# ── Asset Linking ─────────────────────────────────────────────────

@router.post("/assets/link")
def link_asset(req: AssetLinkRequest):
    """Link an asset to a question with a specific role."""
    store = get_cms_store()
    return store.link_asset(req.question_id, req.asset_id, role=req.role)


@router.post("/assets/unlink")
def unlink_asset(req: AssetLinkRequest):
    """Remove an asset link from a question."""
    store = get_cms_store()
    result = store.unlink_asset(req.question_id, req.asset_id, role=req.role)
    return {"unlinked": result, "question_id": req.question_id, "asset_id": req.asset_id}


@router.get("/questions/{qid}/assets")
def get_question_assets(qid: str):
    """Get all assets linked to a question."""
    store = get_cms_store()
    q = store.get_question(qid)
    if not q:
        raise HTTPException(404, f"Question {qid} not found")
    return {"question_id": qid, "assets": store.get_question_assets(qid)}


# ── Bulk Operations ───────────────────────────────────────────────

@router.post("/assets/bulk-replace")
def bulk_replace_asset(req: BulkReplaceRequest):
    """Replace all references to old_asset with new_asset across the question bank."""
    store = get_cms_store()
    try:
        return store.bulk_replace_asset(req.old_asset_id, req.new_asset_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/assets/migrate")
def migrate_visuals_to_assets(author: str = "system"):
    """Migrate visual_svg filename references into the Asset Library."""
    store = get_cms_store()
    return store.migrate_visuals_to_assets(author=author)


# ══════════════════════════════════════════════════════════════════
# ADAPTIVE RETRIEVAL API
# ══════════════════════════════════════════════════════════════════

@router.get("/bundle/{qid}")
def get_question_bundle(qid: str, device: str = "desktop"):
    """Adaptive Retrieval: smart JSON package with resolved assets, typed hint stack, device context."""
    store = get_cms_store()
    bundle = store.get_question_bundle(qid, device=device)
    if not bundle:
        raise HTTPException(404, f"Question {qid} not found")
    return bundle


# ══════════════════════════════════════════════════════════════════
# VISUAL REVIEW API
# ══════════════════════════════════════════════════════════════════

@router.get("/visual-review")
def visual_review(
    topic_id: Optional[str] = None,
    has_visual: Optional[str] = Query(None, description="all, yes, no"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get questions with resolved SVG content for visual review.
    Returns each question with its inline SVG rendered from Asset Library or content store."""
    store = get_cms_store()
    from app.services.content_store_v2 import store_v2
    from pathlib import Path
    import os

    # Build a topic_id → visuals directory mapping for direct filesystem fallback
    content_root = store_v2._root if store_v2._root else None
    if not content_root:
        env_path = os.environ.get("KIWIMATH_V2_CONTENT_DIR", "")
        if env_path and Path(env_path).is_dir():
            content_root = Path(env_path)

    _topic_dirs = {}
    if content_root and content_root.is_dir():
        import json as _json
        for td in content_root.iterdir():
            if not td.is_dir():
                continue
            qp = td / "questions.json"
            if qp.exists():
                try:
                    d = _json.loads(qp.read_text())
                    tid = d.get("topic_id", "")
                    if tid:
                        _topic_dirs[tid] = td / "visuals"
                except Exception:
                    pass

    def _resolve_svg(topic_id: str, filename: str) -> Optional[str]:
        """Try content store first, then direct filesystem."""
        result = store_v2.get_svg(topic_id, filename)
        if result:
            return result
        # Direct filesystem fallback
        vis_dir = _topic_dirs.get(topic_id)
        if vis_dir and vis_dir.is_dir():
            fpath = vis_dir / filename
            if fpath.exists():
                return fpath.read_text()
        return None

    # Fetch questions with filters
    conditions = []
    params = []
    if topic_id:
        conditions.append("topic_id = ?")
        params.append(topic_id)
    if has_visual == "yes":
        conditions.append("(visual_svg IS NOT NULL AND visual_svg != '')")
    elif has_visual == "no":
        conditions.append("(visual_svg IS NULL OR visual_svg = '')")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    cur = store.conn.cursor()
    total = cur.execute(f"SELECT COUNT(*) FROM questions {where}", params).fetchone()[0]
    rows = cur.execute(
        f"SELECT * FROM questions {where} ORDER BY topic_id, difficulty_score LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()

    results = []
    for row in rows:
        q = store._row_to_dict(row)
        svg_content = None
        svg_source = None

        # 1. Try Asset Library first
        assets = store.get_question_assets(q["id"])
        for a in assets:
            if a.get("role") == "primary_visual" and a.get("svg_data"):
                svg_content = a["svg_data"]
                svg_source = "asset_library"
                break

        # 2. Fallback: resolve visual_svg filename from content store
        if not svg_content and q.get("visual_svg"):
            ref = q["visual_svg"]
            # If it looks like inline SVG already
            if ref.strip().startswith("<svg") or ref.strip().startswith("<SVG"):
                svg_content = ref
                svg_source = "inline"
            else:
                # Try loading from content-v2 filesystem
                resolved = _resolve_svg(q.get("topic_id", ""), ref)
                if resolved:
                    svg_content = resolved
                    svg_source = "content_v2"
                else:
                    svg_source = "missing"

        results.append({
            "id": q["id"],
            "stem": q["stem"],
            "choices": q.get("choices", []),
            "correct_answer": q.get("correct_answer", 0),
            "difficulty_tier": q.get("difficulty_tier", ""),
            "difficulty_score": q.get("difficulty_score", 0),
            "topic_id": q.get("topic_id", ""),
            "topic_name": q.get("topic_name", ""),
            "visual_ref": q.get("visual_svg", ""),
            "visual_alt": q.get("visual_alt", ""),
            "svg_content": svg_content,
            "svg_source": svg_source,
            "state": q.get("state", ""),
            "qa_score": q.get("qa_score", 0),
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "questions": results,
    }
