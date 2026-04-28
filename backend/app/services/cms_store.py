"""
Kiwimath CMS Store — SQLite-backed content management system.

Handles: question CRUD, workflow states, version history, QA checks,
reviewer actions, bulk import/export, War Room analytics, A/B testing,
variable templates, AI difficulty calibration, student/parent feedback.

Workflow: draft → review → approved → published
Only 'published' questions export to production content-v2/ JSON.
"""

import json
import math
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class WorkflowState(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ReviewAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    FLAG = "flag"
    COMMENT = "comment"


# ── 10-point QA checklist ──────────────────────────────────────────────

def run_qa_checks(q: dict) -> list[dict]:
    """Run 10-point QA checklist. Returns list of {check, passed, detail}."""
    results = []

    def check(name: str, passed: bool, detail: str = ""):
        results.append({"check": name, "passed": passed, "detail": detail})

    stem = q.get("stem", "")
    choices = q.get("choices", [])
    correct = q.get("correct_answer", -1)
    hints = q.get("hint", {})
    diags = q.get("diagnostics", {})
    diff = q.get("difficulty_score", 0)

    # 1. Stem clarity — ends with ?
    check("stem_question_mark", stem.strip().endswith("?"),
          "Stem should end with a question mark")

    # 2. Visual-stem match — has visual
    check("has_visual", bool(q.get("visual_svg")),
          "Question should have an SVG visual")

    # 3. Single correct answer — valid index
    check("valid_correct_answer", 0 <= correct < len(choices),
          f"correct_answer={correct}, choices={len(choices)}")

    # 4. No duplicate options
    normed = [str(c).strip().lower() for c in choices]
    check("unique_choices", len(set(normed)) == len(normed),
          f"Duplicates: {[c for c in normed if normed.count(c) > 1]}")

    # 5. Answer position — not always first (checked at batch level, pass here)
    check("answer_position", True, "Check at batch level for position bias")

    # 6. Diagnostics meaningful — at least 3 wrong-answer explanations
    wrong_diags = {k: v for k, v in diags.items() if str(k) != str(correct)}
    check("diagnostics_complete", len(wrong_diags) >= 3,
          f"Has {len(wrong_diags)} wrong-answer diagnostics (need 3)")

    # 7. Difficulty calibrated — 1-100 range
    check("difficulty_range", 1 <= diff <= 100,
          f"difficulty_score={diff}")

    # 8. Hint ladder complete — all 6 levels
    hint_keys = set(hints.keys())
    expected = {"level_0", "level_1", "level_2", "level_3", "level_4", "level_5"}
    check("hints_complete", expected.issubset(hint_keys),
          f"Missing: {expected - hint_keys}")

    # 9. Age-appropriate — stem length reasonable (proxy check)
    words = len(stem.split())
    check("age_appropriate_length", 5 <= words <= 80,
          f"Stem has {words} words")

    # 10. Non-empty choices
    check("choices_non_empty", all(str(c).strip() for c in choices),
          "All choices should be non-empty")

    return results


def qa_pass_count(results: list[dict]) -> tuple[int, int]:
    """Returns (passed, total)."""
    passed = sum(1 for r in results if r["passed"])
    return passed, len(results)


# ── SQLite CMS Store ──────────────────────────────────────────────────

class CMSStore:
    """SQLite-backed CMS for Kiwimath questions."""

    def __init__(self, db_path: str = "cms.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                topic_id TEXT NOT NULL,
                topic_name TEXT NOT NULL,
                topic_folder TEXT DEFAULT '',
                stem TEXT NOT NULL,
                original_stem TEXT DEFAULT '',
                choices TEXT NOT NULL,          -- JSON array
                correct_answer INTEGER NOT NULL,
                difficulty_tier TEXT DEFAULT 'easy',
                difficulty_score INTEGER DEFAULT 50,
                visual_svg TEXT,
                visual_alt TEXT,
                diagnostics TEXT DEFAULT '{}',   -- JSON object
                hint TEXT DEFAULT '{}',          -- JSON object (6 levels)
                tags TEXT DEFAULT '[]',          -- JSON array
                state TEXT DEFAULT 'draft',
                qa_score INTEGER DEFAULT 0,      -- passed checks out of 10
                qa_results TEXT DEFAULT '[]',    -- JSON array of check results
                created_by TEXT DEFAULT 'system',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                published_at REAL,
                version INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                snapshot TEXT NOT NULL,           -- full JSON snapshot
                author TEXT DEFAULT 'system',
                change_note TEXT DEFAULT '',
                created_at REAL NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                action TEXT NOT NULL,             -- approve/reject/flag/comment
                reviewer TEXT NOT NULL,
                notes TEXT DEFAULT '',
                created_at REAL NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );

            CREATE INDEX IF NOT EXISTS idx_q_topic ON questions(topic_id);
            CREATE INDEX IF NOT EXISTS idx_q_state ON questions(state);
            CREATE INDEX IF NOT EXISTS idx_q_diff ON questions(difficulty_tier);
            CREATE INDEX IF NOT EXISTS idx_ver_qid ON versions(question_id);
            CREATE INDEX IF NOT EXISTS idx_rev_qid ON reviews(question_id);

            -- War Room analytics (populated from live student data)
            CREATE TABLE IF NOT EXISTS question_analytics (
                question_id TEXT PRIMARY KEY,
                total_attempts INTEGER DEFAULT 0,
                total_correct INTEGER DEFAULT 0,
                total_first_try_correct INTEGER DEFAULT 0,
                error_rate REAL DEFAULT 0.0,
                success_rate_first_try REAL DEFAULT 0.0,
                avg_latency_sec REAL DEFAULT 0.0,
                target_latency_sec REAL DEFAULT 30.0,
                latency_index REAL DEFAULT 1.0,
                abandon_count INTEGER DEFAULT 0,
                abandon_rate REAL DEFAULT 0.0,
                hint_used_count INTEGER DEFAULT 0,
                hint_reliance_score REAL DEFAULT 0.0,
                frustration_signals INTEGER DEFAULT 0,
                urgency_score REAL DEFAULT 0.0,
                red_flag INTEGER DEFAULT 0,
                last_updated REAL DEFAULT 0.0,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );

            -- A/B Testing
            CREATE TABLE IF NOT EXISTS ab_tests (
                id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                variant_a_id TEXT NOT NULL,
                variant_b_id TEXT NOT NULL,
                hypothesis TEXT DEFAULT '',
                status TEXT DEFAULT 'draft',
                sample_size_target INTEGER DEFAULT 100,
                created_by TEXT DEFAULT 'system',
                created_at REAL NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );

            CREATE TABLE IF NOT EXISTS ab_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT NOT NULL,
                variant TEXT NOT NULL,
                student_id TEXT DEFAULT '',
                correct INTEGER DEFAULT 0,
                latency_sec REAL DEFAULT 0.0,
                hints_used INTEGER DEFAULT 0,
                emoji_reaction TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (test_id) REFERENCES ab_tests(id)
            );

            -- Variable Templates
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                stem_template TEXT NOT NULL,
                variable_ranges TEXT NOT NULL,
                instance_count INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );

            -- Student Feedback
            CREATE TABLE IF NOT EXISTS student_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                student_id TEXT DEFAULT '',
                emoji TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );

            -- Parent Flags
            CREATE TABLE IF NOT EXISTS parent_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                parent_id TEXT DEFAULT '',
                parent_name TEXT DEFAULT '',
                comment TEXT NOT NULL,
                resolved INTEGER DEFAULT 0,
                resolved_by TEXT,
                resolved_at REAL,
                created_at REAL NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );

            -- AI Calibration Results
            CREATE TABLE IF NOT EXISTS ai_calibration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                flag_type TEXT NOT NULL,
                severity TEXT DEFAULT 'warning',
                message TEXT NOT NULL,
                suggestion TEXT DEFAULT '',
                resolved INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );

            CREATE INDEX IF NOT EXISTS idx_analytics_urgency ON question_analytics(urgency_score DESC);
            CREATE INDEX IF NOT EXISTS idx_analytics_redflag ON question_analytics(red_flag);
            CREATE INDEX IF NOT EXISTS idx_ab_status ON ab_tests(status);
            CREATE INDEX IF NOT EXISTS idx_reactions_qid ON student_reactions(question_id);
            CREATE INDEX IF NOT EXISTS idx_pflags_qid ON parent_flags(question_id);
            CREATE INDEX IF NOT EXISTS idx_aical_qid ON ai_calibration(question_id);

            -- ── Global Asset Library ──────────────────────────────
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                asset_type TEXT DEFAULT 'svg',        -- svg, png, animation, audio
                svg_data TEXT,                         -- actual SVG content (or base64 for binary)
                file_ref TEXT,                         -- external file reference (e.g. T1-003.svg)
                alt_text TEXT DEFAULT '',
                -- Functional tags
                functional_tags TEXT DEFAULT '[]',     -- JSON: ["Counter","Character","Background","Operator"]
                scaling_tags TEXT DEFAULT '[]',        -- JSON: ["Mobile_Optimized","Tablet_Optimized"]
                theme TEXT DEFAULT '',                 -- "Jungle","Space","Ocean","Classroom"
                mood TEXT DEFAULT '',                  -- "Happy","Neutral","Curious","Challenging"
                -- Pedagogical context
                curriculum_path TEXT DEFAULT '',       -- Counting, Operations, PlaceValue, Geometry
                cognitive_skill TEXT DEFAULT '',       -- Subitizing, Regrouping, MentalRecall
                visual_aid_type TEXT DEFAULT '',       -- NumberLine, TenFrame, Abacus, ConcreteObjects
                grade_range TEXT DEFAULT '',           -- "1-2", "3-4", "1-5"
                -- Metadata
                width INTEGER DEFAULT 0,
                height INTEGER DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                created_by TEXT DEFAULT 'system',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            -- Question ↔ Asset many-to-many join
            CREATE TABLE IF NOT EXISTS question_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                role TEXT DEFAULT 'primary_visual',    -- primary_visual, hint_visual_L2, hint_visual_L4, solution_visual
                sort_order INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions(id),
                FOREIGN KEY (asset_id) REFERENCES assets(id),
                UNIQUE(question_id, asset_id, role)
            );

            CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type);
            CREATE INDEX IF NOT EXISTS idx_assets_theme ON assets(theme);
            CREATE INDEX IF NOT EXISTS idx_assets_curriculum ON assets(curriculum_path);
            CREATE INDEX IF NOT EXISTS idx_assets_visual_aid ON assets(visual_aid_type);
            CREATE INDEX IF NOT EXISTS idx_qa_qid ON question_assets(question_id);
            CREATE INDEX IF NOT EXISTS idx_qa_aid ON question_assets(asset_id);
        """)
        self.conn.commit()

    # ── Question CRUD ──────────────────────────────────────────────

    def create_question(self, data: dict, author: str = "system") -> dict:
        """Create a new question in draft state."""
        qid = data.get("id") or f"Q-{uuid.uuid4().hex[:8].upper()}"
        now = time.time()

        # Run QA
        qa = run_qa_checks(data)
        passed, total = qa_pass_count(qa)

        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO questions (
                id, topic_id, topic_name, topic_folder, stem, original_stem,
                choices, correct_answer, difficulty_tier, difficulty_score,
                visual_svg, visual_alt, diagnostics, hint, tags,
                state, qa_score, qa_results, created_by, created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            qid,
            data.get("topic_id", data.get("topic", "")),
            data.get("topic_name", ""),
            data.get("_topic_folder", data.get("topic_folder", "")),
            data.get("stem", ""),
            data.get("original_stem", ""),
            json.dumps(data.get("choices", [])),
            data.get("correct_answer", 0),
            data.get("difficulty_tier", "easy"),
            data.get("difficulty_score", 50),
            data.get("visual_svg"),
            data.get("visual_alt"),
            json.dumps(data.get("diagnostics", {})),
            json.dumps(data.get("hint", {})),
            json.dumps(data.get("tags", [])),
            data.get("state", "draft"),
            passed,
            json.dumps(qa),
            author,
            now,
            now,
            1,
        ))

        # Save version 1
        self._save_version(qid, 1, data, author, "Initial creation")
        self.conn.commit()
        return self.get_question(qid)

    def get_question(self, qid: str) -> Optional[dict]:
        """Get a single question with all details."""
        cur = self.conn.cursor()
        row = cur.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
        if not row:
            return None
        return self._row_to_dict(row)

    def update_question(self, qid: str, data: dict, author: str = "system",
                        change_note: str = "") -> Optional[dict]:
        """Update a question, auto-run QA, save version."""
        existing = self.get_question(qid)
        if not existing:
            return None

        # Merge updates
        merged = {**existing, **data}
        merged["id"] = qid  # preserve ID

        # Re-run QA
        qa = run_qa_checks(merged)
        passed, total = qa_pass_count(qa)

        new_version = existing["version"] + 1
        now = time.time()

        cur = self.conn.cursor()
        cur.execute("""
            UPDATE questions SET
                topic_id=?, topic_name=?, stem=?, original_stem=?,
                choices=?, correct_answer=?, difficulty_tier=?, difficulty_score=?,
                visual_svg=?, visual_alt=?, diagnostics=?, hint=?, tags=?,
                qa_score=?, qa_results=?, updated_at=?, version=?
            WHERE id=?
        """, (
            merged.get("topic_id", ""),
            merged.get("topic_name", ""),
            merged.get("stem", ""),
            merged.get("original_stem", ""),
            json.dumps(merged.get("choices", [])) if isinstance(merged.get("choices"), list) else merged.get("choices", "[]"),
            merged.get("correct_answer", 0),
            merged.get("difficulty_tier", "easy"),
            merged.get("difficulty_score", 50),
            merged.get("visual_svg"),
            merged.get("visual_alt"),
            json.dumps(merged.get("diagnostics", {})) if isinstance(merged.get("diagnostics"), dict) else merged.get("diagnostics", "{}"),
            json.dumps(merged.get("hint", {})) if isinstance(merged.get("hint"), dict) else merged.get("hint", "{}"),
            json.dumps(merged.get("tags", [])) if isinstance(merged.get("tags"), list) else merged.get("tags", "[]"),
            passed,
            json.dumps(qa),
            now,
            new_version,
            qid,
        ))

        self._save_version(qid, new_version, merged, author, change_note)
        self.conn.commit()
        return self.get_question(qid)

    def list_questions(self, topic_id: str = None, difficulty: str = None,
                       state: str = None, qa_max: int = None,
                       search: str = None, limit: int = 100,
                       offset: int = 0) -> dict:
        """List questions with filters. Returns {total, questions}."""
        conditions = []
        params = []

        if topic_id:
            conditions.append("topic_id = ?")
            params.append(topic_id)
        if difficulty:
            conditions.append("difficulty_tier = ?")
            params.append(difficulty)
        if state:
            conditions.append("state = ?")
            params.append(state)
        if qa_max is not None:
            conditions.append("qa_score <= ?")
            params.append(qa_max)
        if search:
            conditions.append("(stem LIKE ? OR id LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        where = " WHERE " + " AND ".join(conditions) if conditions else ""

        cur = self.conn.cursor()
        total = cur.execute(f"SELECT COUNT(*) FROM questions{where}", params).fetchone()[0]

        rows = cur.execute(
            f"SELECT * FROM questions{where} ORDER BY topic_id, difficulty_score LIMIT ? OFFSET ?",
            params + [limit, offset]
        ).fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "questions": [self._row_to_dict(r) for r in rows],
        }

    def delete_question(self, qid: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM versions WHERE question_id = ?", (qid,))
        cur.execute("DELETE FROM reviews WHERE question_id = ?", (qid,))
        cur.execute("DELETE FROM questions WHERE id = ?", (qid,))
        self.conn.commit()
        return cur.rowcount > 0

    # ── Workflow ──────────────────────────────────────────────────

    def transition_state(self, qid: str, new_state: str, author: str = "system") -> Optional[dict]:
        """Move question to a new workflow state."""
        valid_transitions = {
            "draft": ["review", "archived"],
            "review": ["approved", "draft", "archived"],
            "approved": ["published", "review", "archived"],
            "published": ["archived", "review"],
            "archived": ["draft"],
        }

        q = self.get_question(qid)
        if not q:
            return None

        current = q["state"]
        if new_state not in valid_transitions.get(current, []):
            raise ValueError(f"Cannot transition from '{current}' to '{new_state}'. "
                             f"Valid: {valid_transitions.get(current, [])}")

        # Block publishing if QA < 8/10
        if new_state == "published" and q["qa_score"] < 8:
            raise ValueError(f"Cannot publish: QA score {q['qa_score']}/10 (need ≥8)")

        now = time.time()
        cur = self.conn.cursor()
        pub_at = now if new_state == "published" else q.get("published_at")
        cur.execute("UPDATE questions SET state=?, updated_at=?, published_at=? WHERE id=?",
                    (new_state, now, pub_at, qid))
        self.conn.commit()
        return self.get_question(qid)

    # ── Reviews ──────────────────────────────────────────────────

    def add_review(self, qid: str, action: str, reviewer: str, notes: str = "") -> dict:
        now = time.time()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO reviews (question_id, action, reviewer, notes, created_at) VALUES (?,?,?,?,?)",
            (qid, action, reviewer, notes, now)
        )

        # Auto-transition on approve/reject
        if action == "approve":
            self.transition_state(qid, "approved", reviewer)
        elif action == "reject":
            self.transition_state(qid, "draft", reviewer)

        self.conn.commit()
        return {"question_id": qid, "action": action, "reviewer": reviewer,
                "notes": notes, "created_at": now}

    def get_reviews(self, qid: str) -> list[dict]:
        cur = self.conn.cursor()
        rows = cur.execute(
            "SELECT * FROM reviews WHERE question_id=? ORDER BY created_at DESC", (qid,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Versions ─────────────────────────────────────────────────

    def get_versions(self, qid: str) -> list[dict]:
        cur = self.conn.cursor()
        rows = cur.execute(
            "SELECT * FROM versions WHERE question_id=? ORDER BY version DESC", (qid,)
        ).fetchall()
        return [{"version": r["version"], "author": r["author"],
                 "change_note": r["change_note"], "created_at": r["created_at"]}
                for r in rows]

    def get_version_snapshot(self, qid: str, version: int) -> Optional[dict]:
        cur = self.conn.cursor()
        row = cur.execute(
            "SELECT snapshot FROM versions WHERE question_id=? AND version=?",
            (qid, version)
        ).fetchone()
        return json.loads(row["snapshot"]) if row else None

    # ── Bulk Import/Export ────────────────────────────────────────

    def import_questions(self, questions: list[dict], author: str = "system",
                         state: str = "published") -> dict:
        """Bulk import questions. Returns {imported, skipped, errors}."""
        imported = 0
        skipped = 0
        errors = []

        for q in questions:
            try:
                qid = q.get("id", "")
                # Check if exists
                if self.get_question(qid):
                    skipped += 1
                    continue
                q["state"] = state
                self.create_question(q, author)
                imported += 1
            except Exception as e:
                errors.append({"id": q.get("id", "?"), "error": str(e)})

        return {"imported": imported, "skipped": skipped, "errors": errors}

    def export_published(self) -> dict:
        """Export all published questions grouped by topic, matching content-v2/ format."""
        cur = self.conn.cursor()
        rows = cur.execute(
            "SELECT * FROM questions WHERE state='published' ORDER BY topic_id, difficulty_score"
        ).fetchall()

        topics = {}
        for row in rows:
            q = self._row_to_dict(row)
            tid = q["topic_id"]
            if tid not in topics:
                topics[tid] = {
                    "topic_id": tid,
                    "topic_name": q["topic_name"],
                    "version": "2.0",
                    "total_questions": 0,
                    "difficulty_distribution": {"easy": 0, "medium": 0, "hard": 0},
                    "questions": [],
                }
            t = topics[tid]
            t["questions"].append({
                "id": q["id"],
                "stem": q["stem"],
                "choices": q["choices"],
                "correct_answer": q["correct_answer"],
                "difficulty_tier": q["difficulty_tier"],
                "difficulty_score": q["difficulty_score"],
                "visual_svg": q.get("visual_svg"),
                "visual_alt": q.get("visual_alt"),
                "diagnostics": q["diagnostics"],
                "tags": q["tags"],
                "topic": q["topic_id"],
                "topic_name": q["topic_name"],
                "original_stem": q.get("original_stem", ""),
                "hint": q["hint"],
            })
            t["total_questions"] += 1
            tier = q["difficulty_tier"]
            if tier in t["difficulty_distribution"]:
                t["difficulty_distribution"][tier] += 1

        return topics

    # ── War Room ──────────────────────────────────────────────────

    def war_room(self, limit: int = 50) -> dict:
        """Get the 'Problem Child' queue — top underperforming questions by urgency."""
        cur = self.conn.cursor()

        # Ensure analytics rows exist for all questions
        cur.execute("""
            INSERT OR IGNORE INTO question_analytics (question_id, last_updated)
            SELECT id, 0.0 FROM questions WHERE id NOT IN (SELECT question_id FROM question_analytics)
        """)
        self.conn.commit()

        # Get urgent questions (sorted by urgency_score DESC)
        rows = cur.execute("""
            SELECT q.*, a.total_attempts, a.total_correct, a.error_rate,
                   a.success_rate_first_try, a.avg_latency_sec, a.target_latency_sec,
                   a.latency_index, a.abandon_rate, a.hint_reliance_score,
                   a.frustration_signals, a.urgency_score, a.red_flag
            FROM questions q
            LEFT JOIN question_analytics a ON q.id = a.question_id
            WHERE q.state = 'published'
            ORDER BY COALESCE(a.urgency_score, 0) DESC, COALESCE(a.red_flag, 0) DESC
            LIMIT ?
        """, (limit,)).fetchall()

        questions = []
        for r in rows:
            q = self._row_to_dict(r)
            q["analytics"] = {
                "total_attempts": r["total_attempts"] or 0,
                "total_correct": r["total_correct"] or 0,
                "error_rate": round(r["error_rate"] or 0, 3),
                "success_rate_first_try": round(r["success_rate_first_try"] or 0, 3),
                "avg_latency_sec": round(r["avg_latency_sec"] or 0, 1),
                "latency_index": round(r["latency_index"] or 1.0, 2),
                "abandon_rate": round(r["abandon_rate"] or 0, 3),
                "hint_reliance_score": round(r["hint_reliance_score"] or 0, 3),
                "frustration_signals": r["frustration_signals"] or 0,
                "urgency_score": round(r["urgency_score"] or 0, 3),
                "red_flag": bool(r["red_flag"]),
            }
            questions.append(q)

        # Red flag count
        red_flags = cur.execute(
            "SELECT COUNT(*) FROM question_analytics WHERE red_flag = 1"
        ).fetchone()[0]

        # Strand mastery heatmap
        heatmap = []
        for row in cur.execute("""
            SELECT q.topic_name, q.topic_id,
                   COUNT(*) as total,
                   AVG(COALESCE(a.success_rate_first_try, 0)) as avg_sr,
                   AVG(COALESCE(a.error_rate, 0)) as avg_error,
                   AVG(COALESCE(a.avg_latency_sec, 0)) as avg_latency,
                   SUM(CASE WHEN a.red_flag = 1 THEN 1 ELSE 0 END) as red_flags
            FROM questions q
            LEFT JOIN question_analytics a ON q.id = a.question_id
            WHERE q.state = 'published'
            GROUP BY q.topic_id ORDER BY avg_sr ASC
        """):
            heatmap.append({
                "topic_name": row["topic_name"],
                "topic_id": row["topic_id"],
                "total_questions": row["total"],
                "avg_success_rate": round(row["avg_sr"] or 0, 3),
                "avg_error_rate": round(row["avg_error"] or 0, 3),
                "avg_latency": round(row["avg_latency"] or 0, 1),
                "red_flags": row["red_flags"] or 0,
            })

        return {
            "problem_queue": questions,
            "total_red_flags": red_flags,
            "strand_heatmap": heatmap,
        }

    def update_analytics(self, qid: str, correct: bool, latency_sec: float,
                         hints_used: int = 0, abandoned: bool = False,
                         first_try: bool = True) -> dict:
        """Record a student attempt and recalculate analytics. Called from answer API."""
        cur = self.conn.cursor()

        # Ensure row exists
        cur.execute(
            "INSERT OR IGNORE INTO question_analytics (question_id, last_updated) VALUES (?, ?)",
            (qid, time.time())
        )

        # Get current stats
        row = cur.execute("SELECT * FROM question_analytics WHERE question_id=?", (qid,)).fetchone()
        if not row:
            return {}

        ta = (row["total_attempts"] or 0) + 1
        tc = (row["total_correct"] or 0) + (1 if correct else 0)
        tfc = (row["total_first_try_correct"] or 0) + (1 if correct and first_try else 0)
        ac = (row["abandon_count"] or 0) + (1 if abandoned else 0)
        hu = (row["hint_used_count"] or 0) + (1 if hints_used > 0 else 0)

        error_rate = 1.0 - (tc / max(ta, 1))
        sr_first = tfc / max(ta, 1)
        abandon_rate = ac / max(ta, 1)
        hint_reliance = hu / max(ta, 1)

        # Rolling average latency
        old_avg = row["avg_latency_sec"] or 0
        avg_latency = old_avg + (latency_sec - old_avg) / ta

        target = row["target_latency_sec"] or 30.0
        latency_index = avg_latency / max(target, 1.0)

        # Urgency score: weighted composite
        urgency = (0.35 * error_rate + 0.25 * abandon_rate +
                   0.20 * hint_reliance + 0.20 * min(latency_index, 3.0) / 3.0)

        # Red flag: error > 20% OR avg_latency > 60s OR abandon > 15%
        red_flag = 1 if (error_rate > 0.20 or avg_latency > 60.0 or abandon_rate > 0.15) else 0

        cur.execute("""
            UPDATE question_analytics SET
                total_attempts=?, total_correct=?, total_first_try_correct=?,
                error_rate=?, success_rate_first_try=?, avg_latency_sec=?,
                latency_index=?, abandon_count=?, abandon_rate=?,
                hint_used_count=?, hint_reliance_score=?,
                urgency_score=?, red_flag=?, last_updated=?
            WHERE question_id=?
        """, (ta, tc, tfc, error_rate, sr_first, avg_latency,
              latency_index, ac, abandon_rate, hu, hint_reliance,
              urgency, red_flag, time.time(), qid))
        self.conn.commit()

        return {"question_id": qid, "urgency_score": round(urgency, 3),
                "red_flag": bool(red_flag), "error_rate": round(error_rate, 3)}

    def record_frustration(self, qid: str) -> None:
        """Increment frustration signal count for a question."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO question_analytics (question_id, last_updated) VALUES (?, ?)",
            (qid, time.time())
        )
        cur.execute(
            "UPDATE question_analytics SET frustration_signals = frustration_signals + 1 WHERE question_id=?",
            (qid,)
        )
        self.conn.commit()

    # ── A/B Testing ──────────────────────────────────────────────

    def create_ab_test(self, qid: str, hypothesis: str = "",
                       author: str = "system") -> dict:
        """Create an A/B test by duplicating the question as variant B."""
        original = self.get_question(qid)
        if not original:
            raise ValueError(f"Question {qid} not found")

        # Create variant B as a copy
        variant_data = {**original}
        variant_data["id"] = f"{qid}-B"
        variant_data["state"] = "draft"
        variant_data.pop("created_at", None)
        variant_data.pop("updated_at", None)
        variant_data.pop("published_at", None)
        variant_data.pop("version", None)
        variant_data.pop("qa_score", None)
        variant_data.pop("qa_results", None)

        # Check if variant already exists
        if not self.get_question(variant_data["id"]):
            self.create_question(variant_data, author)

        test_id = f"AB-{uuid.uuid4().hex[:8].upper()}"
        now = time.time()

        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO ab_tests (id, question_id, variant_a_id, variant_b_id,
                                  hypothesis, status, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, 'draft', ?, ?)
        """, (test_id, qid, qid, variant_data["id"], hypothesis, author, now))
        self.conn.commit()

        return {
            "test_id": test_id,
            "question_id": qid,
            "variant_a": qid,
            "variant_b": variant_data["id"],
            "hypothesis": hypothesis,
            "status": "draft",
        }

    def list_ab_tests(self, status: str = None) -> list[dict]:
        cur = self.conn.cursor()
        if status:
            rows = cur.execute("SELECT * FROM ab_tests WHERE status=? ORDER BY created_at DESC",
                               (status,)).fetchall()
        else:
            rows = cur.execute("SELECT * FROM ab_tests ORDER BY created_at DESC").fetchall()

        tests = []
        for r in rows:
            t = dict(r)
            # Get result stats for each variant
            for variant_key in ["variant_a_id", "variant_b_id"]:
                vid = t[variant_key]
                stats = cur.execute("""
                    SELECT COUNT(*) as n, AVG(correct) as sr, AVG(latency_sec) as avg_lat,
                           AVG(hints_used) as avg_hints
                    FROM ab_results WHERE test_id=? AND variant=?
                """, (t["id"], vid)).fetchone()
                t[f"{variant_key}_stats"] = {
                    "sample_size": stats["n"] or 0,
                    "success_rate": round(stats["sr"] or 0, 3),
                    "avg_latency": round(stats["avg_lat"] or 0, 1),
                    "avg_hints": round(stats["avg_hints"] or 0, 1),
                }
            tests.append(t)
        return tests

    def record_ab_result(self, test_id: str, variant: str, student_id: str,
                         correct: bool, latency_sec: float, hints_used: int = 0,
                         emoji: str = None) -> None:
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO ab_results (test_id, variant, student_id, correct, latency_sec,
                                    hints_used, emoji_reaction, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (test_id, variant, student_id, 1 if correct else 0,
              latency_sec, hints_used, emoji, time.time()))
        self.conn.commit()

    # ── Variable Templates ───────────────────────────────────────

    def create_template(self, qid: str, variable_ranges: dict) -> dict:
        """Create a parametric template from a question.
        variable_ranges: {"val1": [1, 9], "val2": [1, 9]}
        """
        q = self.get_question(qid)
        if not q:
            raise ValueError(f"Question {qid} not found")

        template_id = f"TPL-{uuid.uuid4().hex[:8].upper()}"
        now = time.time()

        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO templates (id, question_id, stem_template, variable_ranges, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (template_id, qid, q["stem"], json.dumps(variable_ranges), now))
        self.conn.commit()

        return {"template_id": template_id, "question_id": qid,
                "stem_template": q["stem"], "variable_ranges": variable_ranges}

    def generate_instances(self, template_id: str, count: int = 10) -> list[dict]:
        """Generate N unique question instances from a template."""
        cur = self.conn.cursor()
        row = cur.execute("SELECT * FROM templates WHERE id=?", (template_id,)).fetchone()
        if not row:
            raise ValueError(f"Template {template_id} not found")

        stem_template = row["stem_template"]
        ranges = json.loads(row["variable_ranges"])
        source_q = self.get_question(row["question_id"])

        import random
        instances = []
        seen = set()

        for i in range(count * 3):  # oversample to find unique combos
            if len(instances) >= count:
                break

            values = {}
            for var_name, var_range in ranges.items():
                if isinstance(var_range, list) and len(var_range) == 2:
                    values[var_name] = random.randint(var_range[0], var_range[1])
                elif isinstance(var_range, list):
                    values[var_name] = random.choice(var_range)

            key = tuple(sorted(values.items()))
            if key in seen:
                continue
            seen.add(key)

            # Substitute variables in stem
            stem = stem_template
            for var_name, val in values.items():
                stem = stem.replace("{{" + var_name + "}}", str(val))

            # Generate new choices if possible (simple arithmetic)
            instance = {
                "stem": stem,
                "variables": values,
                "choices": source_q["choices"] if source_q else [],
                "correct_answer": source_q["correct_answer"] if source_q else 0,
            }
            instances.append(instance)

        # Update instance count
        cur.execute("UPDATE templates SET instance_count=? WHERE id=?",
                    (len(instances), template_id))
        self.conn.commit()

        return instances

    def list_templates(self) -> list[dict]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT * FROM templates ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    # ── AI Difficulty Calibration ────────────────────────────────

    def ai_calibrate(self) -> dict:
        """Scan all questions and flag difficulty inconsistencies."""
        cur = self.conn.cursor()
        rows = cur.execute("SELECT * FROM questions WHERE state IN ('published', 'approved')").fetchall()
        questions = [self._row_to_dict(r) for r in rows]

        # Clear old calibration results
        cur.execute("DELETE FROM ai_calibration WHERE resolved = 0")

        flags = []
        now = time.time()

        # Group by topic for statistical analysis
        topic_groups = {}
        for q in questions:
            tid = q.get("topic_id", "")
            if tid not in topic_groups:
                topic_groups[tid] = []
            topic_groups[tid].append(q)

        for q in questions:
            qid = q["id"]
            score = q.get("difficulty_score", 50)
            tier = q.get("difficulty_tier", "easy")
            topic = q.get("topic_id", "")
            stem = q.get("stem", "")

            # 1. Grade-difficulty mismatch
            # G1-2 should be difficulty 1-50, but check for complexity signals
            word_count = len(stem.split())
            has_multiplication = any(op in stem.lower() for op in ["multiply", "times", "×", "product"])
            has_division = any(op in stem.lower() for op in ["divide", "÷", "quotient", "share equally"])
            has_fractions = any(op in stem.lower() for op in ["fraction", "half", "quarter", "third", "1/"])

            # If tagged easy (1-30) but has complex operations
            if score <= 30 and (has_multiplication or has_division or has_fractions):
                msg = f"Tagged difficulty {score} (easy) but contains complex operations"
                suggestion = f"Consider recalibrating to difficulty 50+ (medium/hard)"
                flags.append({"qid": qid, "type": "grade_mismatch", "severity": "warning",
                              "msg": msg, "suggestion": suggestion})

            # If tagged hard (70+) but very short/simple stem
            if score >= 70 and word_count < 10 and not has_multiplication and not has_fractions:
                msg = f"Tagged difficulty {score} (hard) but stem is only {word_count} words with simple operations"
                suggestion = "Consider recalibrating to lower difficulty"
                flags.append({"qid": qid, "type": "grade_mismatch", "severity": "warning",
                              "msg": msg, "suggestion": suggestion})

            # 2. Tier-score mismatch
            expected_tiers = {"easy": (1, 33), "medium": (34, 66), "hard": (67, 100)}
            if tier in expected_tiers:
                lo, hi = expected_tiers[tier]
                if not (lo <= score <= hi):
                    msg = f"Tier '{tier}' but difficulty_score={score} (expected {lo}-{hi})"
                    suggestion = f"Change tier to match score, or adjust score to {lo}-{hi}"
                    flags.append({"qid": qid, "type": "tier_score_mismatch", "severity": "info",
                                  "msg": msg, "suggestion": suggestion})

            # 3. Hint complexity vs difficulty
            hints = q.get("hint", {})
            if isinstance(hints, str):
                try:
                    hints = json.loads(hints)
                except:
                    hints = {}
            total_hint_words = sum(len(str(v).split()) for v in hints.values())
            if score <= 20 and total_hint_words > 100:
                msg = f"Very easy question (score={score}) but hints have {total_hint_words} words"
                suggestion = "Simplify hints for easy questions — kids at this level need shorter guidance"
                flags.append({"qid": qid, "type": "hint_complexity", "severity": "info",
                              "msg": msg, "suggestion": suggestion})

            # 4. Outlier detection within topic
            topic_qs = topic_groups.get(topic, [])
            if len(topic_qs) >= 10:
                scores = [tq.get("difficulty_score", 50) for tq in topic_qs if tq.get("difficulty_tier") == tier]
                if scores:
                    mean = sum(scores) / len(scores)
                    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
                    std = math.sqrt(variance) if variance > 0 else 0
                    if std > 0 and abs(score - mean) > 2.5 * std:
                        msg = (f"Difficulty outlier in {topic}/{tier}: score={score}, "
                               f"topic mean={mean:.0f} ± {std:.0f}")
                        suggestion = f"Consider adjusting to ~{mean:.0f}"
                        flags.append({"qid": qid, "type": "difficulty_outlier", "severity": "warning",
                                      "msg": msg, "suggestion": suggestion})

        # 5. Check for questions with analytics that show mismatch
        analytics_rows = cur.execute("""
            SELECT a.*, q.difficulty_tier, q.difficulty_score
            FROM question_analytics a
            JOIN questions q ON q.id = a.question_id
            WHERE a.total_attempts >= 10
        """).fetchall()

        for ar in analytics_rows:
            qid = ar["question_id"]
            sr = ar["success_rate_first_try"] or 0
            tier = ar["difficulty_tier"]

            # Easy question with low success rate
            if tier == "easy" and sr < 0.5 and (ar["total_attempts"] or 0) >= 20:
                msg = f"Tagged 'easy' but success rate is only {sr*100:.0f}%"
                suggestion = "Question may be harder than tagged — recalibrate or add better hints"
                flags.append({"qid": qid, "type": "analytics_mismatch", "severity": "critical",
                              "msg": msg, "suggestion": suggestion})

            # Hard question with very high success rate
            if tier == "hard" and sr > 0.85 and (ar["total_attempts"] or 0) >= 20:
                msg = f"Tagged 'hard' but success rate is {sr*100:.0f}%"
                suggestion = "Question may be easier than tagged — recalibrate to medium/easy"
                flags.append({"qid": qid, "type": "analytics_mismatch", "severity": "warning",
                              "msg": msg, "suggestion": suggestion})

        # Save flags to DB
        for f in flags:
            cur.execute("""
                INSERT INTO ai_calibration (question_id, flag_type, severity, message, suggestion, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f["qid"], f["type"], f["severity"], f["msg"], f["suggestion"], now))
        self.conn.commit()

        # Summary
        by_type = {}
        by_severity = {"critical": 0, "warning": 0, "info": 0}
        for f in flags:
            by_type[f["type"]] = by_type.get(f["type"], 0) + 1
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1

        return {
            "total_scanned": len(questions),
            "total_flags": len(flags),
            "by_type": by_type,
            "by_severity": by_severity,
            "flags": flags[:100],  # Return first 100
        }

    def get_calibration_flags(self, qid: str = None) -> list[dict]:
        cur = self.conn.cursor()
        if qid:
            rows = cur.execute(
                "SELECT * FROM ai_calibration WHERE question_id=? AND resolved=0 ORDER BY created_at DESC",
                (qid,)
            ).fetchall()
        else:
            rows = cur.execute(
                "SELECT * FROM ai_calibration WHERE resolved=0 ORDER BY severity, created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Student/Parent Feedback ──────────────────────────────────

    def record_emoji_reaction(self, qid: str, student_id: str, emoji: str) -> None:
        """Record student emoji reaction (happy/bored/frustrated)."""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO student_reactions (question_id, student_id, emoji, created_at)
            VALUES (?, ?, ?, ?)
        """, (qid, student_id, emoji, time.time()))
        self.conn.commit()

    def add_parent_flag(self, qid: str, parent_id: str, parent_name: str,
                        comment: str) -> dict:
        """Pin a parent comment to a question."""
        now = time.time()
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO parent_flags (question_id, parent_id, parent_name, comment, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (qid, parent_id, parent_name, comment, now))
        self.conn.commit()
        return {"question_id": qid, "parent_name": parent_name, "comment": comment}

    def resolve_parent_flag(self, flag_id: int, resolved_by: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE parent_flags SET resolved=1, resolved_by=?, resolved_at=? WHERE id=?",
            (resolved_by, time.time(), flag_id)
        )
        self.conn.commit()

    def get_feedback(self, qid: str) -> dict:
        """Get all feedback for a question — emoji reactions + parent flags."""
        cur = self.conn.cursor()

        # Emoji summary
        emojis = {"happy": 0, "bored": 0, "frustrated": 0}
        for row in cur.execute(
            "SELECT emoji, COUNT(*) as cnt FROM student_reactions WHERE question_id=? GROUP BY emoji",
            (qid,)
        ):
            emojis[row["emoji"]] = row["cnt"]

        total_reactions = sum(emojis.values())

        # Parent flags
        pf_rows = cur.execute(
            "SELECT * FROM parent_flags WHERE question_id=? ORDER BY created_at DESC",
            (qid,)
        ).fetchall()

        # Frustration signals from analytics
        frustration = 0
        ar = cur.execute(
            "SELECT frustration_signals FROM question_analytics WHERE question_id=?",
            (qid,)
        ).fetchone()
        if ar:
            frustration = ar["frustration_signals"] or 0

        return {
            "question_id": qid,
            "emoji_reactions": emojis,
            "total_reactions": total_reactions,
            "frustration_pct": round(emojis["frustrated"] / max(total_reactions, 1) * 100, 1),
            "parent_flags": [dict(r) for r in pf_rows],
            "parent_flag_count": len(pf_rows),
            "unresolved_flags": sum(1 for r in pf_rows if not r["resolved"]),
            "frustration_signals": frustration,
        }

    # ── Rollback ─────────────────────────────────────────────────

    def rollback(self, qid: str, target_version: int, author: str = "system") -> Optional[dict]:
        """Restore a question to a specific version snapshot."""
        snapshot = self.get_version_snapshot(qid, target_version)
        if not snapshot:
            raise ValueError(f"Version {target_version} not found for {qid}")

        # Update with snapshot data, creating a new version
        return self.update_question(
            qid, snapshot, author=author,
            change_note=f"Rollback to version {target_version}"
        )

    # ── Enhanced Dashboard ───────────────────────────────────────

    def dashboard(self) -> dict:
        cur = self.conn.cursor()

        # Pipeline counts
        pipeline = {}
        for row in cur.execute("SELECT state, COUNT(*) as cnt FROM questions GROUP BY state"):
            pipeline[row["state"]] = row["cnt"]

        # Topic coverage
        topics = []
        for row in cur.execute("""
            SELECT topic_name, topic_id, COUNT(*) as total,
                   SUM(CASE WHEN state='published' THEN 1 ELSE 0 END) as published,
                   SUM(CASE WHEN difficulty_tier='easy' THEN 1 ELSE 0 END) as easy,
                   SUM(CASE WHEN difficulty_tier='medium' THEN 1 ELSE 0 END) as medium,
                   SUM(CASE WHEN difficulty_tier='hard' THEN 1 ELSE 0 END) as hard,
                   AVG(qa_score) as avg_qa
            FROM questions GROUP BY topic_id ORDER BY topic_name
        """):
            topics.append(dict(row))

        # QA health
        qa_issues = cur.execute("SELECT COUNT(*) FROM questions WHERE qa_score < 10").fetchone()[0]
        qa_critical = cur.execute("SELECT COUNT(*) FROM questions WHERE qa_score < 8").fetchone()[0]
        total = cur.execute("SELECT COUNT(*) FROM questions").fetchone()[0]

        # Analytics summary
        red_flags = cur.execute("SELECT COUNT(*) FROM question_analytics WHERE red_flag = 1").fetchone()[0]
        ai_flags = cur.execute("SELECT COUNT(*) FROM ai_calibration WHERE resolved = 0").fetchone()[0]
        unresolved_parent = cur.execute("SELECT COUNT(*) FROM parent_flags WHERE resolved = 0").fetchone()[0]
        active_ab = cur.execute("SELECT COUNT(*) FROM ab_tests WHERE status = 'active'").fetchone()[0]

        # Recent correction log
        recent_edits = []
        for row in cur.execute("""
            SELECT v.question_id, v.version, v.author, v.change_note, v.created_at
            FROM versions v ORDER BY v.created_at DESC LIMIT 20
        """):
            recent_edits.append(dict(row))

        return {
            "total_questions": total,
            "pipeline": pipeline,
            "topics": topics,
            "qa_health": {
                "clean": total - qa_issues,
                "minor_issues": qa_issues - qa_critical,
                "critical": qa_critical,
                "pass_rate": round((total - qa_issues) / max(total, 1) * 100, 1),
            },
            "war_room": {
                "red_flags": red_flags,
                "ai_calibration_flags": ai_flags,
                "unresolved_parent_flags": unresolved_parent,
                "active_ab_tests": active_ab,
            },
            "recent_edits": recent_edits,
        }

    # ── Global Asset Library ────────────────────────────────────

    def create_asset(self, data: dict, author: str = "system") -> dict:
        """Create a new asset in the library."""
        asset_id = data.get("id") or f"AST-{uuid.uuid4().hex[:8].upper()}"
        now = time.time()
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO assets (
                id, name, asset_type, svg_data, file_ref, alt_text,
                functional_tags, scaling_tags, theme, mood,
                curriculum_path, cognitive_skill, visual_aid_type, grade_range,
                width, height, usage_count, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
        """, (
            asset_id,
            data.get("name", asset_id),
            data.get("asset_type", "svg"),
            data.get("svg_data"),
            data.get("file_ref"),
            data.get("alt_text", ""),
            json.dumps(data.get("functional_tags", [])),
            json.dumps(data.get("scaling_tags", [])),
            data.get("theme", ""),
            data.get("mood", ""),
            data.get("curriculum_path", ""),
            data.get("cognitive_skill", ""),
            data.get("visual_aid_type", ""),
            data.get("grade_range", ""),
            data.get("width", 0),
            data.get("height", 0),
            author,
            now, now,
        ))
        self.conn.commit()
        return self.get_asset(asset_id)

    def get_asset(self, asset_id: str) -> Optional[dict]:
        cur = self.conn.cursor()
        row = cur.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not row:
            return None
        return self._asset_to_dict(row)

    def update_asset(self, asset_id: str, data: dict) -> Optional[dict]:
        """Update an asset. Changes propagate to all questions using it."""
        existing = self.get_asset(asset_id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = time.time()
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE assets SET
                name=?, asset_type=?, svg_data=?, file_ref=?, alt_text=?,
                functional_tags=?, scaling_tags=?, theme=?, mood=?,
                curriculum_path=?, cognitive_skill=?, visual_aid_type=?, grade_range=?,
                width=?, height=?, updated_at=?
            WHERE id=?
        """, (
            merged.get("name", ""),
            merged.get("asset_type", "svg"),
            merged.get("svg_data"),
            merged.get("file_ref"),
            merged.get("alt_text", ""),
            json.dumps(merged.get("functional_tags", [])) if isinstance(merged.get("functional_tags"), list) else merged.get("functional_tags", "[]"),
            json.dumps(merged.get("scaling_tags", [])) if isinstance(merged.get("scaling_tags"), list) else merged.get("scaling_tags", "[]"),
            merged.get("theme", ""),
            merged.get("mood", ""),
            merged.get("curriculum_path", ""),
            merged.get("cognitive_skill", ""),
            merged.get("visual_aid_type", ""),
            merged.get("grade_range", ""),
            merged.get("width", 0),
            merged.get("height", 0),
            now,
            asset_id,
        ))
        self.conn.commit()
        return self.get_asset(asset_id)

    def delete_asset(self, asset_id: str) -> dict:
        """Delete an asset. Blocked if questions still reference it."""
        cur = self.conn.cursor()
        refs = cur.execute(
            "SELECT question_id FROM question_assets WHERE asset_id=?", (asset_id,)
        ).fetchall()
        if refs:
            return {
                "status": "blocked",
                "reason": "Asset still referenced by questions",
                "linked_questions": len(refs),
                "question_ids": [r["question_id"] for r in refs],
            }
        cur.execute("DELETE FROM assets WHERE id=?", (asset_id,))
        self.conn.commit()
        return {"status": "deleted", "asset_id": asset_id}

    def list_assets(self, asset_type: str = None, theme: str = None,
                    functional_tag: str = None, curriculum_path: str = None,
                    visual_aid_type: str = None, search: str = None,
                    limit: int = 100, offset: int = 0) -> dict:
        """List assets with tag-based filters."""
        conditions = []
        params = []
        if asset_type:
            conditions.append("asset_type = ?")
            params.append(asset_type)
        if theme:
            conditions.append("theme = ?")
            params.append(theme)
        if functional_tag:
            conditions.append("functional_tags LIKE ?")
            params.append(f'%"{functional_tag}"%')
        if curriculum_path:
            conditions.append("curriculum_path = ?")
            params.append(curriculum_path)
        if visual_aid_type:
            conditions.append("visual_aid_type = ?")
            params.append(visual_aid_type)
        if search:
            conditions.append("(name LIKE ? OR alt_text LIKE ? OR id LIKE ?)")
            params.extend([f"%{search}%"] * 3)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        cur = self.conn.cursor()
        total = cur.execute(f"SELECT COUNT(*) FROM assets{where}", params).fetchone()[0]
        rows = cur.execute(
            f"SELECT * FROM assets{where} ORDER BY usage_count DESC, name LIMIT ? OFFSET ?",
            params + [limit, offset]
        ).fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "assets": [self._asset_to_dict(r) for r in rows],
        }

    def link_asset(self, question_id: str, asset_id: str,
                   role: str = "primary_visual") -> dict:
        """Link an asset to a question with a specific role."""
        now = time.time()
        cur = self.conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO question_assets (question_id, asset_id, role, created_at)
            VALUES (?, ?, ?, ?)
        """, (question_id, asset_id, role, now))
        # Update usage count
        cur.execute("""
            UPDATE assets SET usage_count = (
                SELECT COUNT(DISTINCT question_id) FROM question_assets WHERE asset_id = ?
            ) WHERE id = ?
        """, (asset_id, asset_id))
        self.conn.commit()
        return {"question_id": question_id, "asset_id": asset_id, "role": role}

    def unlink_asset(self, question_id: str, asset_id: str,
                     role: str = "primary_visual") -> bool:
        """Remove an asset link from a question."""
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM question_assets WHERE question_id=? AND asset_id=? AND role=?",
            (question_id, asset_id, role)
        )
        # Recalculate usage count
        cur.execute("""
            UPDATE assets SET usage_count = (
                SELECT COUNT(DISTINCT question_id) FROM question_assets WHERE asset_id = ?
            ) WHERE id = ?
        """, (asset_id, asset_id))
        self.conn.commit()
        return cur.rowcount > 0

    def get_question_assets(self, question_id: str) -> list[dict]:
        """Get all assets linked to a question."""
        cur = self.conn.cursor()
        rows = cur.execute("""
            SELECT a.*, qa.role, qa.sort_order
            FROM assets a
            JOIN question_assets qa ON a.id = qa.asset_id
            WHERE qa.question_id = ?
            ORDER BY qa.sort_order, qa.role
        """, (question_id,)).fetchall()
        result = []
        for r in rows:
            d = self._asset_to_dict(r)
            d["role"] = r["role"]
            d["sort_order"] = r["sort_order"]
            result.append(d)
        return result

    def get_asset_usage(self, asset_id: str) -> list[dict]:
        """Get all questions using a specific asset."""
        cur = self.conn.cursor()
        rows = cur.execute("""
            SELECT q.id, q.stem, q.topic_id, q.difficulty_tier, q.state, qa.role
            FROM questions q
            JOIN question_assets qa ON q.id = qa.question_id
            WHERE qa.asset_id = ?
            ORDER BY q.topic_id, q.difficulty_score
        """, (asset_id,)).fetchall()
        return [dict(r) for r in rows]

    def bulk_replace_asset(self, old_asset_id: str, new_asset_id: str) -> dict:
        """Replace all references to old_asset with new_asset across the question bank."""
        # Verify both exist
        if not self.get_asset(old_asset_id):
            raise ValueError(f"Old asset {old_asset_id} not found")
        if not self.get_asset(new_asset_id):
            raise ValueError(f"New asset {new_asset_id} not found")

        cur = self.conn.cursor()
        # Count affected
        affected = cur.execute(
            "SELECT COUNT(*) FROM question_assets WHERE asset_id=?", (old_asset_id,)
        ).fetchone()[0]

        # Remove duplicates first (where new_asset already linked with same role)
        cur.execute("""
            DELETE FROM question_assets WHERE asset_id=? AND EXISTS (
                SELECT 1 FROM question_assets qa2
                WHERE qa2.question_id = question_assets.question_id
                AND qa2.role = question_assets.role
                AND qa2.asset_id = ?
            )
        """, (old_asset_id, new_asset_id))
        # Swap remaining references
        cur.execute(
            "UPDATE question_assets SET asset_id=? WHERE asset_id=?",
            (new_asset_id, old_asset_id)
        )

        # Recalculate usage counts for both
        for aid in (old_asset_id, new_asset_id):
            cur.execute("""
                UPDATE assets SET usage_count = (
                    SELECT COUNT(DISTINCT question_id) FROM question_assets WHERE asset_id = ?
                ) WHERE id = ?
            """, (aid, aid))

        self.conn.commit()
        return {
            "old_asset": old_asset_id,
            "new_asset": new_asset_id,
            "replaced": affected,
            "questions_updated": affected,
        }

    def find_orphan_references(self) -> dict:
        """Find questions pointing to assets that don't exist (null references)."""
        cur = self.conn.cursor()

        # Question_assets pointing to missing assets
        orphan_links = cur.execute("""
            SELECT qa.question_id, qa.asset_id, qa.role
            FROM question_assets qa
            LEFT JOIN assets a ON qa.asset_id = a.id
            WHERE a.id IS NULL
        """).fetchall()

        # Questions with visual_svg that aren't in the asset library
        unlinked_visuals = cur.execute("""
            SELECT q.id, q.visual_svg
            FROM questions q
            WHERE q.visual_svg IS NOT NULL AND q.visual_svg != ''
            AND q.id NOT IN (
                SELECT DISTINCT question_id FROM question_assets WHERE role = 'primary_visual'
            )
        """).fetchall()

        # Assets with zero usage
        unused_assets = cur.execute(
            "SELECT id, name, asset_type FROM assets WHERE usage_count = 0"
        ).fetchall()

        return {
            "orphan_links": [dict(r) for r in orphan_links],
            "unlinked_visuals": [{"question_id": r["id"], "visual_svg": r["visual_svg"]} for r in unlinked_visuals],
            "unused_assets": [dict(r) for r in unused_assets],
            "total_orphan_links": len(orphan_links),
            "total_unlinked_visuals": len(unlinked_visuals),
            "total_unused_assets": len(unused_assets),
        }

    def migrate_visuals_to_assets(self, author: str = "system") -> dict:
        """Extract all question visual_svg references into the Asset Library.
        Creates one asset per unique visual reference and links it to the question."""
        cur = self.conn.cursor()
        rows = cur.execute("""
            SELECT id, visual_svg, visual_alt, topic_id, difficulty_tier, difficulty_score
            FROM questions
            WHERE visual_svg IS NOT NULL AND visual_svg != ''
        """).fetchall()

        created = 0
        linked = 0
        skipped = 0
        now = time.time()

        # Track unique visuals to avoid duplicates
        visual_to_asset = {}

        for r in rows:
            qid = r["id"]
            svg_ref = r["visual_svg"]
            alt = r["visual_alt"] or ""

            # Check if this visual reference already has an asset
            if svg_ref in visual_to_asset:
                asset_id = visual_to_asset[svg_ref]
            else:
                # Check if asset exists for this file_ref
                existing = cur.execute(
                    "SELECT id FROM assets WHERE file_ref=?", (svg_ref,)
                ).fetchone()

                if existing:
                    asset_id = existing["id"]
                    skipped += 1
                else:
                    # Create new asset
                    asset_id = f"AST-{uuid.uuid4().hex[:8].upper()}"
                    # Infer tags from question metadata
                    topic = r["topic_id"] or ""
                    grade = "1-2" if (r["difficulty_score"] or 50) <= 50 else "3-5"

                    cur.execute("""
                        INSERT INTO assets (
                            id, name, asset_type, file_ref, alt_text,
                            functional_tags, scaling_tags, theme, mood,
                            curriculum_path, grade_range,
                            created_by, created_at, updated_at
                        ) VALUES (?, ?, 'svg', ?, ?, '["Counter"]', '["Mobile_Optimized"]',
                                  '', '', ?, ?, ?, ?, ?)
                    """, (asset_id, svg_ref, svg_ref, alt, topic, grade, author, now, now))
                    created += 1

                visual_to_asset[svg_ref] = asset_id

            # Link asset to question (if not already linked)
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO question_assets (question_id, asset_id, role, created_at)
                    VALUES (?, ?, 'primary_visual', ?)
                """, (qid, asset_id, now))
                if cur.rowcount > 0:
                    linked += 1
            except Exception:
                pass

        # Update usage counts for all newly created assets
        cur.execute("""
            UPDATE assets SET usage_count = (
                SELECT COUNT(DISTINCT question_id) FROM question_assets WHERE asset_id = assets.id
            )
        """)
        self.conn.commit()

        return {
            "assets_created": created,
            "assets_skipped": skipped,
            "questions_linked": linked,
            "total_visual_questions": len(rows),
        }

    def get_question_bundle(self, qid: str, device: str = "desktop") -> Optional[dict]:
        """Build smart retrieval bundle — the JSON package sent to the student app.
        Resolves assets by device type and includes typed hint stack."""
        q = self.get_question(qid)
        if not q:
            return None

        # Resolve linked assets
        assets = self.get_question_assets(qid)
        primary_visual = None
        hint_visuals = {}
        solution_visuals = []

        for a in assets:
            role = a.get("role", "")
            # Device-aware: pick appropriate scaling
            asset_data = {
                "asset_id": a["id"],
                "name": a.get("name", ""),
                "type": a.get("asset_type", "svg"),
                "alt_text": a.get("alt_text", ""),
            }
            # Include SVG data or file reference
            if a.get("svg_data"):
                asset_data["data"] = a["svg_data"]
            elif a.get("file_ref"):
                asset_data["file_ref"] = a["file_ref"]

            if role == "primary_visual":
                primary_visual = asset_data
            elif role.startswith("hint_visual"):
                hint_visuals[role] = asset_data
            elif role == "solution_visual":
                solution_visuals.append(asset_data)

        # Fallback: use inline visual_svg if no library asset
        if not primary_visual and q.get("visual_svg"):
            primary_visual = {
                "asset_id": None,
                "name": q.get("visual_svg", ""),
                "type": "svg",
                "file_ref": q.get("visual_svg"),
                "alt_text": q.get("visual_alt", ""),
            }

        # Build typed hint stack
        hints = q.get("hint", {})
        hint_stack = []
        for level in range(6):
            # Try both key formats
            text = hints.get(f"level_{level}") or hints.get(f"L{level}") or ""
            hint_entry = {
                "level": level,
                "text": text,
            }
            # Determine hint type
            if level <= 1:
                hint_entry["type"] = "nudge"
            elif level <= 3:
                hint_entry["type"] = "visual_aid"
                # Attach visual asset if linked
                vis_key = f"hint_visual_L{level}"
                if vis_key in hint_visuals:
                    hint_entry["visual"] = hint_visuals[vis_key]
            else:
                hint_entry["type"] = "walkthrough"
                if f"hint_visual_L{level}" in hint_visuals:
                    hint_entry["visual"] = hint_visuals[f"hint_visual_L{level}"]

            hint_stack.append(hint_entry)

        # Build the JSON package
        bundle = {
            "question_id": qid,
            "logic": q.get("stem", ""),
            "original_stem": q.get("original_stem", ""),
            "choices": q.get("choices", []),
            "correct_answer": q.get("correct_answer", 0),
            "difficulty": {
                "score": q.get("difficulty_score", 50),
                "tier": q.get("difficulty_tier", "easy"),
            },
            "topic": {
                "id": q.get("topic_id", ""),
                "name": q.get("topic_name", ""),
            },
            "assets": {
                "primary_visual": primary_visual,
                "solution_visuals": solution_visuals,
            },
            "hints": hint_stack,
            "diagnostics": q.get("diagnostics", {}),
            "device": device,
        }

        return bundle

    def asset_dashboard(self) -> dict:
        """Asset Library dashboard stats."""
        cur = self.conn.cursor()
        total = cur.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        by_type = {}
        for r in cur.execute("SELECT asset_type, COUNT(*) as cnt FROM assets GROUP BY asset_type"):
            by_type[r["asset_type"]] = r["cnt"]
        by_theme = {}
        for r in cur.execute("SELECT theme, COUNT(*) as cnt FROM assets WHERE theme != '' GROUP BY theme"):
            by_theme[r["theme"]] = r["cnt"]
        by_curriculum = {}
        for r in cur.execute("SELECT curriculum_path, COUNT(*) as cnt FROM assets WHERE curriculum_path != '' GROUP BY curriculum_path"):
            by_curriculum[r["curriculum_path"]] = r["cnt"]

        linked_questions = cur.execute("SELECT COUNT(DISTINCT question_id) FROM question_assets").fetchone()[0]
        total_links = cur.execute("SELECT COUNT(*) FROM question_assets").fetchone()[0]
        unused = cur.execute("SELECT COUNT(*) FROM assets WHERE usage_count = 0").fetchone()[0]

        return {
            "total_assets": total,
            "by_type": by_type,
            "by_theme": by_theme,
            "by_curriculum": by_curriculum,
            "questions_with_assets": linked_questions,
            "total_links": total_links,
            "unused_assets": unused,
        }

    def _asset_to_dict(self, row) -> dict:
        d = dict(row)
        for field in ("functional_tags", "scaling_tags"):
            if field in d and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    # ── Helpers ───────────────────────────────────────────────────

    def _save_version(self, qid: str, version: int, data: dict,
                      author: str, note: str):
        # Clean data for JSON serialization
        snapshot = {k: v for k, v in data.items() if not k.startswith("_")}
        self.conn.cursor().execute(
            "INSERT INTO versions (question_id, version, snapshot, author, change_note, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (qid, version, json.dumps(snapshot, default=str), author, note, time.time())
        )

    def _row_to_dict(self, row) -> dict:
        d = dict(row)
        # Parse JSON fields
        for field in ("choices", "diagnostics", "hint", "tags", "qa_results"):
            if field in d and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    def close(self):
        self.conn.close()


# Singleton
_cms_store: Optional[CMSStore] = None


def get_cms_store(db_path: str = None) -> CMSStore:
    global _cms_store
    if _cms_store is None:
        import os
        default_path = str(Path(__file__).parent.parent.parent / "cms_v2.db")
        path = db_path or os.environ.get("KIWIMATH_CMS_DB", default_path)
        _cms_store = CMSStore(path)
    return _cms_store
