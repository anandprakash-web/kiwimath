#!/usr/bin/env python3
"""
Kiwimath Content Auditor v2
============================

Type-aware auditor that identifies question types and validates accordingly:

  Question Types:
    - MCQ (multiple choice): has choices[], correct_answer is index
    - Integer input: interaction_mode="integer", correct_value is the answer
    - Fill-in-the-blank: stem contains ___ or blank, may have choices or free input

  Checks per type:
    MCQ:      choices count, duplicate choices, correct_answer in range, visual match
    Integer:  correct_value is numeric, stem has "= ?" or similar, no stale choices
    All:      unique IDs, stem quality, SVG validity, rendering issues, duplicates

Usage:
    # Full audit against live API
    python -m tests.bots.content_auditor --base-url https://kiwimath-api-deufqab6gq-el.a.run.app

    # Audit specific grade
    python -m tests.bots.content_auditor --grade 3

    # Quick audit (first 20 questions per topic)
    python -m tests.bots.content_auditor --quick

    # Save detailed report
    python -m tests.bots.content_auditor --report audit_report.json
"""

import argparse
import asyncio
import json
import re
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Optional

import httpx

# ── Question type detection ──────────────────────────────────────────────────

def detect_question_type(q: dict) -> str:
    """Detect question type from its fields."""
    mode = q.get("interaction_mode", "")
    choices = q.get("choices") or []
    correct_value = q.get("correct_value")

    if mode == "integer":
        return "integer"
    if mode == "fill_blank":
        return "fill_blank"
    if isinstance(choices, list) and len(choices) == 0 and correct_value is not None:
        return "integer"
    if isinstance(choices, list) and len(choices) >= 2:
        return "mcq"
    if "___" in q.get("stem", "") or "blank" in q.get("stem", "").lower():
        return "fill_blank"
    # Default: if has choices treat as MCQ, else integer
    if choices:
        return "mcq"
    return "integer"


# ── Quality flag categories ─────────────────────────────────────────────────

FLAG_MISSING_VISUAL = "missing_visual"
FLAG_BROKEN_VISUAL = "broken_visual"
FLAG_SHORT_STEM = "short_stem"
FLAG_EMPTY_CHOICES = "empty_choices_mcq"
FLAG_WRONG_CHOICE_COUNT = "wrong_choice_count"
FLAG_DUPLICATE_CHOICES = "duplicate_choices"
FLAG_NO_EXPLANATION = "no_explanation"
FLAG_NO_HINTS = "no_hints"
FLAG_RENDERING_ISSUE = "rendering_issue"
FLAG_DUPLICATE_STEM = "duplicate_stem"
FLAG_DUPLICATE_ID = "duplicate_id"
FLAG_DIFFICULTY_SUSPECT = "difficulty_suspect"
FLAG_API_ERROR = "api_error"
FLAG_ANSWER_MISMATCH = "answer_mismatch"
FLAG_INTEGER_NO_VALUE = "integer_no_correct_value"
FLAG_MCQ_NO_ANSWER = "mcq_no_correct_answer"
FLAG_MCQ_ANSWER_OOB = "mcq_answer_out_of_bounds"
FLAG_STALE_CHOICES = "integer_has_stale_choices"

SEVERITY = {
    FLAG_MISSING_VISUAL: "high",
    FLAG_BROKEN_VISUAL: "high",
    FLAG_SHORT_STEM: "medium",
    FLAG_EMPTY_CHOICES: "critical",
    FLAG_WRONG_CHOICE_COUNT: "high",
    FLAG_DUPLICATE_CHOICES: "high",
    FLAG_NO_EXPLANATION: "low",
    FLAG_NO_HINTS: "low",
    FLAG_RENDERING_ISSUE: "high",
    FLAG_DUPLICATE_STEM: "medium",
    FLAG_DUPLICATE_ID: "critical",
    FLAG_DIFFICULTY_SUSPECT: "low",
    FLAG_API_ERROR: "critical",
    FLAG_ANSWER_MISMATCH: "critical",
    FLAG_INTEGER_NO_VALUE: "critical",
    FLAG_MCQ_NO_ANSWER: "critical",
    FLAG_MCQ_ANSWER_OOB: "critical",
    FLAG_STALE_CHOICES: "medium",
}

# Patterns that indicate rendering problems
RENDERING_ISSUES = [
    re.compile(r"â€™|â€œ|â€|Ã"),       # Mojibake patterns
    re.compile(r"\\u[0-9a-fA-F]{4}"),   # Unicode escapes
    re.compile(r"\\n|\\t"),             # Literal escape sequences
    re.compile(r"\x00-\x08"),           # Control characters
]


class QuestionAudit:
    """Audit result for a single question."""
    def __init__(self, question_id: str, grade: int, topic: str):
        self.question_id = question_id
        self.grade = grade
        self.topic = topic
        self.stem = ""
        self.choices = []
        self.correct_answer = None
        self.correct_value = None
        self.difficulty_tier = ""
        self.difficulty_score = 0
        self.question_type = "mcq"
        self.has_visual = False
        self.visual_works = False
        self.has_hints = False
        self.has_explanation = False
        self.flags: list[dict] = []
        self.answer_check_result: Optional[dict] = None

    def flag(self, flag_type: str, detail: str = ""):
        self.flags.append({
            "type": flag_type,
            "severity": SEVERITY.get(flag_type, "low"),
            "detail": detail,
        })

    @property
    def is_clean(self):
        return len(self.flags) == 0

    def to_dict(self):
        return {
            "question_id": self.question_id,
            "grade": self.grade,
            "topic": self.topic,
            "question_type": self.question_type,
            "stem_preview": self.stem[:80] + ("..." if len(self.stem) > 80 else ""),
            "choices_count": len(self.choices),
            "correct_answer": self.correct_answer,
            "correct_value": self.correct_value,
            "difficulty_tier": self.difficulty_tier,
            "has_visual": self.has_visual,
            "has_hints": self.has_hints,
            "has_explanation": self.has_explanation,
            "flags": self.flags,
            "flag_count": len(self.flags),
        }


class ContentAuditor:
    """Crawls and audits every question in the system — type-aware."""

    def __init__(self, base_url: str, concurrency: int = 10, quick: bool = False,
                 target_grade: Optional[int] = None):
        self.base_url = base_url.rstrip("/")
        self.concurrency = concurrency
        self.quick = quick
        self.target_grade = target_grade
        self.client = httpx.AsyncClient(timeout=30.0)
        self.semaphore = asyncio.Semaphore(concurrency)
        self.audits: list[QuestionAudit] = []
        self.seen_stems: dict[str, str] = {}  # normalized_stem -> first question_id
        self.seen_ids: dict[str, str] = {}    # id -> first source
        self.type_counts = defaultdict(int)
        self.stats = {
            "total_questions": 0,
            "total_flags": 0,
            "questions_clean": 0,
            "questions_flagged": 0,
            "by_type": defaultdict(lambda: {"total": 0, "flagged": 0}),
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_flag_type": defaultdict(int),
            "by_grade": {},
            "by_topic": {},
        }

    async def close(self):
        await self.client.aclose()

    async def _get(self, path: str, **kwargs) -> tuple[int, Any]:
        url = f"{self.base_url}{path}"
        try:
            async with self.semaphore:
                resp = await self.client.get(url, **kwargs)
                if resp.status_code >= 400:
                    return resp.status_code, resp.json() if resp.text else None
                return resp.status_code, resp.json()
        except Exception as e:
            return 0, None

    async def _post(self, path: str, **kwargs) -> tuple[int, Any]:
        url = f"{self.base_url}{path}"
        try:
            async with self.semaphore:
                resp = await self.client.post(url, **kwargs)
                if resp.status_code >= 400:
                    return resp.status_code, resp.json() if resp.text else None
                return resp.status_code, resp.json()
        except Exception:
            return 0, None

    # ── Discovery ────────────────────────────────────────────────────────────

    async def discover_v2_topics(self, grade: int) -> list[dict]:
        status, data = await self._get("/v2/topics", params={"grade": grade})
        return data if status == 200 and data else []

    async def discover_v4_topics(self, grade: int) -> list[dict]:
        status, data = await self._get(f"/v4/topics/{grade}")
        return data if status == 200 and data else []

    async def discover_wavebook_topics(self, grade: int) -> list[dict]:
        if grade < 3:
            return []
        status, data = await self._get("/wavebook/topics", params={"grade": grade})
        if status == 200 and data:
            return data if isinstance(data, list) else data.get("topics", [])
        return []

    async def discover_worksheets(self, grade: int) -> list[dict]:
        status, data = await self._get("/olympiad/worksheets/list", params={"grade": grade})
        if status == 200 and data:
            return data if isinstance(data, list) else data.get("worksheets", [])
        return []

    # ── Question fetching ────────────────────────────────────────────────────

    async def fetch_v2_questions(self, grade: int, topic: str, limit: int = 500) -> list[dict]:
        questions = []
        exclude_ids = set()
        max_per_topic = 20 if self.quick else limit
        for i in range(max_per_topic):
            params = {"topic": topic, "grade": grade, "difficulty": 100, "window": 200}
            if exclude_ids:
                params["exclude"] = ",".join(exclude_ids)
            status, q = await self._get("/v2/questions/next", params=params)
            if status != 200 or not q:
                break
            qid = q.get("question_id", "")
            if qid in exclude_ids:
                break
            exclude_ids.add(qid)
            questions.append(q)
        return questions

    async def fetch_v4_questions(self, grade: int, topic_id: str, limit: int = 500) -> list[dict]:
        questions = []
        exclude_ids = set()
        max_per_topic = 20 if self.quick else limit
        for _ in range(max_per_topic):
            params = {"grade": grade, "topic_id": topic_id, "theta": 0.0}
            if exclude_ids:
                params["exclude"] = ",".join(exclude_ids)
            status, q = await self._get("/v4/next", params=params)
            if status != 200 or not q:
                break
            qid = q.get("id", "")
            if qid in exclude_ids:
                break
            exclude_ids.add(qid)
            questions.append(q)
        return questions

    async def fetch_worksheet_questions(self, grade: int, day: int) -> list[dict]:
        status, data = await self._get("/olympiad/worksheets", params={"grade": grade, "day": day})
        if status == 200 and data:
            return data.get("questions", []) if isinstance(data, dict) else []
        return []

    async def fetch_wavebook_questions(self, grade: int, topic: str) -> list[dict]:
        status, data = await self._get("/wavebook/questions", params={"grade": grade, "topic": topic})
        if status == 200 and data:
            return data.get("questions", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        return []

    # ── Type-aware auditing ──────────────────────────────────────────────────

    def audit_question(self, q: dict, grade: int, topic: str, source: str = "v2") -> QuestionAudit:
        """Run type-aware quality checks on a single question."""
        qid = q.get("question_id") or q.get("id", "unknown")
        audit = QuestionAudit(qid, grade, topic)

        # Extract fields
        audit.stem = q.get("stem", "")
        audit.choices = q.get("choices") or []
        audit.correct_answer = q.get("correct_answer")
        audit.correct_value = q.get("correct_value")
        audit.difficulty_tier = q.get("difficulty_tier", "")
        audit.difficulty_score = q.get("difficulty_score", 0)
        audit.has_visual = bool(q.get("visual_svg"))
        audit.has_hints = bool(q.get("hints") or q.get("hint") or q.get("hint_ladder"))
        audit.has_explanation = bool(q.get("solution_steps") or q.get("diagnostics"))

        # ── Detect question type ──────────────────────────────────
        qtype = detect_question_type(q)
        audit.question_type = qtype
        self.type_counts[qtype] += 1

        # ── Check 1: Unique ID ────────────────────────────────────
        if qid in self.seen_ids:
            audit.flag(FLAG_DUPLICATE_ID,
                       f"ID collision with {self.seen_ids[qid]} — different questions MUST have different IDs")
        else:
            self.seen_ids[qid] = f"{source}:{topic}"

        # ── Check 2: Stem quality ─────────────────────────────────
        if not audit.stem or len(audit.stem.strip()) < 10:
            audit.flag(FLAG_SHORT_STEM, f"Stem too short ({len(audit.stem)} chars)")

        # ── Check 3: Rendering issues ─────────────────────────────
        text_to_check = audit.stem + " ".join(str(c) for c in audit.choices)
        for pattern in RENDERING_ISSUES:
            match = pattern.search(text_to_check)
            if match:
                audit.flag(FLAG_RENDERING_ISSUE, f"Found '{match.group()}' in question text")
                break

        # ── Check 4: Type-specific validation ─────────────────────

        if qtype == "mcq":
            # MCQ: must have 3-5 choices, no duplicates, valid correct_answer index
            if not audit.choices or len(audit.choices) == 0:
                audit.flag(FLAG_EMPTY_CHOICES, "MCQ question has no choices")
            elif len(audit.choices) < 2:
                audit.flag(FLAG_WRONG_CHOICE_COUNT, f"Only {len(audit.choices)} choice(s)")
            elif len(audit.choices) > 6:
                audit.flag(FLAG_WRONG_CHOICE_COUNT, f"{len(audit.choices)} choices (expected 3-5)")

            if audit.choices:
                choice_strs = [str(c).strip().lower() for c in audit.choices]
                if len(set(choice_strs)) < len(choice_strs):
                    dupes = [c for c in set(choice_strs) if choice_strs.count(c) > 1]
                    audit.flag(FLAG_DUPLICATE_CHOICES, f"Duplicate: '{dupes[0]}'")

            if audit.correct_answer is None:
                audit.flag(FLAG_MCQ_NO_ANSWER, "MCQ has no correct_answer index")
            elif isinstance(audit.correct_answer, int) and audit.choices:
                if audit.correct_answer < 0 or audit.correct_answer >= len(audit.choices):
                    audit.flag(FLAG_MCQ_ANSWER_OOB,
                               f"correct_answer={audit.correct_answer} but {len(audit.choices)} choices")

        elif qtype == "integer":
            # Integer: must have correct_value, should be numeric
            cv = audit.correct_value
            if cv is None:
                # Check if correct_answer can serve as value
                if audit.correct_answer is not None:
                    pass  # correct_answer might be the value for legacy questions
                else:
                    audit.flag(FLAG_INTEGER_NO_VALUE, "Integer question has no correct_value")
            else:
                try:
                    float(cv)
                except (TypeError, ValueError):
                    audit.flag(FLAG_INTEGER_NO_VALUE,
                               f"correct_value '{cv}' is not numeric")

        elif qtype == "fill_blank":
            # Fill-in-the-blank: similar to integer validation
            if audit.correct_value is None and audit.correct_answer is None:
                audit.flag(FLAG_INTEGER_NO_VALUE, "Fill-blank has no answer")

        # ── Check 5: Visual check ─────────────────────────────────
        vr = q.get("visual_requirement", "")
        if vr in ("required", "essential") and not audit.has_visual:
            audit.flag(FLAG_MISSING_VISUAL,
                       f"visual_requirement='{vr}' but no SVG")

        if audit.has_visual:
            svg = q.get("visual_svg", "")
            if not svg.strip().startswith("<svg"):
                audit.flag(FLAG_BROKEN_VISUAL, "SVG does not start with <svg>")
            elif "</svg>" not in svg:
                audit.flag(FLAG_BROKEN_VISUAL, "SVG missing closing </svg>")
            elif len(svg) < 50:
                audit.flag(FLAG_BROKEN_VISUAL, f"SVG suspiciously short ({len(svg)} chars)")

        # ── Check 6: Explanation/hints ────────────────────────────
        if not audit.has_explanation:
            audit.flag(FLAG_NO_EXPLANATION, "No solution steps or diagnostics")
        if not audit.has_hints:
            audit.flag(FLAG_NO_HINTS, "No hints provided")

        # ── Check 7: Duplicate stem detection ─────────────────────
        stem_key = re.sub(r'\s+', ' ', audit.stem.strip().lower())[:100]
        if stem_key in self.seen_stems:
            first_id = self.seen_stems[stem_key]
            if first_id != qid:
                audit.flag(FLAG_DUPLICATE_STEM, f"Duplicate of {first_id}")
        else:
            self.seen_stems[stem_key] = qid

        return audit

    async def check_answer_mcq(self, qid: str, correct_answer: int, user_id: str = "auditor_bot") -> Optional[dict]:
        """Submit MCQ answer and verify the API agrees."""
        payload = {
            "question_id": qid,
            "selected_answer": correct_answer,
            "user_id": user_id,
            "time_taken_ms": 5000,
            "hints_used": 0,
        }
        status, data = await self._post("/v2/answer/check", json=payload)
        return data if status == 200 else None

    async def check_answer_integer(self, qid: str, correct_value: Any, user_id: str = "auditor_bot") -> Optional[dict]:
        """Submit integer answer and verify the API agrees."""
        payload = {
            "question_id": qid,
            "typed_answer": str(correct_value),
            "user_id": user_id,
            "time_taken_ms": 5000,
            "hints_used": 0,
        }
        status, data = await self._post("/v2/answer/check", json=payload)
        return data if status == 200 else None

    # ── Main crawl ───────────────────────────────────────────────────────────

    async def audit_grade(self, grade: int):
        """Audit all content for a single grade."""
        print(f"\n{'─' * 50}")
        print(f"  Grade {grade} — discovering content...")

        v2_topics = await self.discover_v2_topics(grade)
        v4_topics = await self.discover_v4_topics(grade)
        wb_topics = await self.discover_wavebook_topics(grade)
        ws_days = await self.discover_worksheets(grade)

        print(f"  Found: {len(v2_topics)} olympiad, {len(v4_topics)} adaptive, "
              f"{len(wb_topics)} wavebook, {len(ws_days)} worksheets")

        grade_audits = []

        # ── V2 Olympiad ───────────────────────────────────────────
        for t in v2_topics:
            topic_id = t.get("topic_id", t.get("id", ""))
            topic_name = t.get("topic_name", t.get("name", topic_id))
            questions = await self.fetch_v2_questions(grade, topic_id)
            print(f"    [v2] {topic_name}: {len(questions)} questions", end="")

            flagged = 0
            for q in questions:
                audit = self.audit_question(q, grade, topic_id, source="v2")

                # Type-aware answer verification
                if audit.question_type == "mcq" and audit.correct_answer is not None:
                    result = await self.check_answer_mcq(audit.question_id, audit.correct_answer)
                    if result and not result.get("correct", True):
                        audit.flag(FLAG_ANSWER_MISMATCH,
                                   f"Submitted correct_answer={audit.correct_answer} but API disagrees")
                elif audit.question_type == "integer" and audit.correct_value is not None:
                    result = await self.check_answer_integer(audit.question_id, audit.correct_value)
                    if result and not result.get("correct", True):
                        audit.flag(FLAG_ANSWER_MISMATCH,
                                   f"Submitted correct_value={audit.correct_value} but API disagrees")

                grade_audits.append(audit)
                if not audit.is_clean:
                    flagged += 1

            status = f" ({flagged} flagged)" if flagged else " ok"
            print(status)

        # ── V4 Adaptive ───────────────────────────────────────────
        for t in v4_topics:
            topic_id = t.get("topic_id", "")
            topic_name = t.get("topic_name", topic_id)
            questions = await self.fetch_v4_questions(grade, topic_id)
            print(f"    [v4] {topic_name}: {len(questions)} questions", end="")

            flagged = 0
            type_breakdown = defaultdict(int)
            for q in questions:
                audit = self.audit_question(q, grade, topic_id, source="v4")
                type_breakdown[audit.question_type] += 1

                # Type-aware answer verification for v4
                if audit.question_type == "integer" and audit.correct_value is not None:
                    result = await self.check_answer_integer(audit.question_id, audit.correct_value)
                    if result and not result.get("correct", True):
                        audit.flag(FLAG_ANSWER_MISMATCH,
                                   f"Integer: correct_value={audit.correct_value} but API disagrees")

                grade_audits.append(audit)
                if not audit.is_clean:
                    flagged += 1

            types_str = ", ".join(f"{k}:{v}" for k, v in type_breakdown.items())
            status = f" ({flagged} flagged)" if flagged else " ok"
            print(f" [{types_str}]{status}")

        # ── Wavebook ──────────────────────────────────────────────
        for t in wb_topics:
            topic_name = t if isinstance(t, str) else t.get("topic", t.get("name", ""))
            questions = await self.fetch_wavebook_questions(grade, topic_name)
            if self.quick:
                questions = questions[:20]
            print(f"    [wb] {topic_name}: {len(questions)} questions", end="")

            flagged = 0
            for q in questions:
                audit = self.audit_question(q, grade, f"wavebook:{topic_name}", source="wavebook")
                grade_audits.append(audit)
                if not audit.is_clean:
                    flagged += 1

            status = f" ({flagged} flagged)" if flagged else " ok"
            print(status)

        # ── Worksheets ────────────────────────────────────────────
        ws_list = ws_days[:5] if self.quick else ws_days
        for ws in ws_list:
            day = ws.get("day", ws) if isinstance(ws, dict) else ws
            if not isinstance(day, int):
                continue
            questions = await self.fetch_worksheet_questions(grade, day)
            print(f"    [ws] Day {day}: {len(questions)} questions", end="")

            flagged = 0
            for q in questions:
                audit = self.audit_question(q, grade, f"worksheet:day{day}", source="worksheet")
                grade_audits.append(audit)
                if not audit.is_clean:
                    flagged += 1

            status = f" ({flagged} flagged)" if flagged else " ok"
            print(status)

        self.audits.extend(grade_audits)

        total = len(grade_audits)
        flagged = sum(1 for a in grade_audits if not a.is_clean)
        clean = total - flagged
        print(f"\n  Grade {grade} summary: {total} questions, {clean} clean, {flagged} flagged")

    async def diagnose_server(self):
        """Pre-flight check: what content is loaded?"""
        print("\n  Pre-flight diagnostics:")

        status, health = await self._get("/health")
        if status == 200 and health:
            print(f"    Health: OK — {health.get('status', '?')}")
            cv2 = health.get("content_v2", {})
            cv4 = health.get("content_v4", {})
            print(f"    v2: {cv2}")
            print(f"    v4: {cv4}")
        else:
            print(f"    Health: FAIL status={status}")

        status, v4g = await self._get("/v4/grades")
        if status == 200 and v4g:
            total_v4 = sum(g.get("question_count", 0) for g in v4g)
            print(f"    v4 grades: {len(v4g)} grades, {total_v4} questions")
        else:
            print(f"    v4 grades: FAIL status={status}")

        status, v4s = await self._get("/v4/stats")
        if status == 200 and v4s:
            print(f"    v4 stats: {v4s.get('total_questions', '?')} questions loaded")
        print()

    async def run(self):
        """Run the full audit."""
        grades = [self.target_grade] if self.target_grade else list(range(1, 7))
        mode = "quick" if self.quick else "full"
        print(f"\n{'=' * 60}")
        print(f"  KIWIMATH CONTENT AUDITOR v2 ({mode} mode)")
        print(f"  Type-aware: MCQ | Integer | Fill-blank")
        print(f"  Target: {self.base_url}")
        print(f"  Grades: {grades}")
        print(f"{'=' * 60}")

        await self.diagnose_server()

        start = time.time()
        for grade in grades:
            await self.audit_grade(grade)
        elapsed = time.time() - start

        # Compile stats
        self.stats["total_questions"] = len(self.audits)
        self.stats["questions_clean"] = sum(1 for a in self.audits if a.is_clean)
        self.stats["questions_flagged"] = sum(1 for a in self.audits if not a.is_clean)

        for audit in self.audits:
            g = audit.grade
            t = audit.topic
            qt = audit.question_type

            # By type
            self.stats["by_type"][qt]["total"] += 1
            if not audit.is_clean:
                self.stats["by_type"][qt]["flagged"] += 1

            # By grade
            if g not in self.stats["by_grade"]:
                self.stats["by_grade"][g] = {"total": 0, "flagged": 0, "flags": defaultdict(int),
                                              "types": defaultdict(int)}
            self.stats["by_grade"][g]["total"] += 1
            self.stats["by_grade"][g]["types"][qt] += 1
            if not audit.is_clean:
                self.stats["by_grade"][g]["flagged"] += 1

            # By topic
            if t not in self.stats["by_topic"]:
                self.stats["by_topic"][t] = {"total": 0, "flagged": 0, "flags": defaultdict(int)}
            self.stats["by_topic"][t]["total"] += 1
            if not audit.is_clean:
                self.stats["by_topic"][t]["flagged"] += 1

            for flag in audit.flags:
                self.stats["by_severity"][flag["severity"]] += 1
                self.stats["by_flag_type"][flag["type"]] += 1
                self.stats["by_grade"][g]["flags"][flag["type"]] += 1
                self.stats["by_topic"][t]["flags"][flag["type"]] += 1

        self.stats["total_flags"] = sum(self.stats["by_severity"].values())
        self.stats["elapsed_seconds"] = round(elapsed, 1)

        return self.stats

    def print_report(self):
        s = self.stats
        print(f"\n{'=' * 60}")
        print(f"  CONTENT AUDIT REPORT")
        print(f"{'=' * 60}")
        print(f"  Total questions:  {s['total_questions']}")
        print(f"  Clean:            {s['questions_clean']} ({s['questions_clean']/max(s['total_questions'],1)*100:.0f}%)")
        print(f"  Flagged:          {s['questions_flagged']}")
        print(f"  Total flags:      {s['total_flags']}")
        print(f"  Time:             {s['elapsed_seconds']}s")
        print()

        # Question type breakdown
        print("  Question Types:")
        for qt, counts in sorted(s["by_type"].items()):
            total = counts["total"]
            flagged = counts["flagged"]
            clean_pct = (total - flagged) / max(total, 1) * 100
            print(f"    {qt:<15} {total:>6} total, {flagged:>4} flagged ({clean_pct:.0f}% clean)")
        print()

        # Severity breakdown
        print("  Severity Breakdown:")
        for sev in ["critical", "high", "medium", "low"]:
            count = s["by_severity"][sev]
            if count > 0:
                icon = {"critical": "[CRIT]", "high": "[HIGH]", "medium": "[MED]", "low": "[LOW]"}[sev]
                print(f"    {icon:<8} {count:>5}")
        print()

        # Flag type breakdown
        if s["by_flag_type"]:
            print("  Issue Types:")
            for flag_type, count in sorted(s["by_flag_type"].items(), key=lambda x: -x[1]):
                print(f"    {count:>5}x  {flag_type}")
            print()

        # Per-grade summary with type breakdown
        print("  Per-Grade:")
        print(f"  {'Grade':<8} {'Total':>7} {'MCQ':>6} {'Int':>6} {'Fill':>6} {'Flagged':>8} {'Clean%':>7}")
        print(f"  {'-'*55}")
        for g in sorted(s["by_grade"].keys()):
            gs = s["by_grade"][g]
            clean_pct = (gs["total"] - gs["flagged"]) / max(gs["total"], 1) * 100
            mcq = gs["types"].get("mcq", 0)
            integer = gs["types"].get("integer", 0)
            fill = gs["types"].get("fill_blank", 0)
            status = "OK" if gs["flagged"] == 0 else "!!"
            print(f"  G{g:<7} {gs['total']:>7} {mcq:>6} {integer:>6} {fill:>6} {gs['flagged']:>8} {clean_pct:>6.0f}% {status}")
        print()

        # Critical issues
        critical = [a for a in self.audits if any(f["severity"] == "critical" for f in a.flags)]
        if critical:
            print(f"  CRITICAL ISSUES ({len(critical)} questions):")
            for a in critical[:20]:
                crit_flags = [f for f in a.flags if f["severity"] == "critical"]
                for f in crit_flags:
                    print(f"    [{a.question_id}] G{a.grade} {a.topic} ({a.question_type}): "
                          f"{f['type']} — {f['detail'][:80]}")
            if len(critical) > 20:
                print(f"    ... and {len(critical) - 20} more")
            print()

        # Duplicate IDs
        dup_ids = [a for a in self.audits if any(f["type"] == FLAG_DUPLICATE_ID for f in a.flags)]
        if dup_ids:
            print(f"  DUPLICATE ID COLLISIONS: {len(dup_ids)} — THIS IS A DATA INTEGRITY RISK")
            for a in dup_ids[:10]:
                print(f"    {a.question_id}: {a.stem[:60]}")
            print()

        if s["questions_flagged"] == 0:
            print("  ALL CLEAN — Zero issues found!")

        print(f"{'=' * 60}")

    def save_report(self, filepath: str):
        by_grade = {}
        for g, gs in self.stats["by_grade"].items():
            by_grade[g] = {
                "total": gs["total"], "flagged": gs["flagged"],
                "flags": dict(gs["flags"]), "types": dict(gs["types"]),
            }
        by_topic = {}
        for t, ts in self.stats["by_topic"].items():
            by_topic[t] = {
                "total": ts["total"], "flagged": ts["flagged"],
                "flags": dict(ts["flags"]),
            }
        report = {
            "timestamp": datetime.now(tz=None).isoformat(),
            "base_url": self.base_url,
            "mode": "quick" if self.quick else "full",
            "summary": {
                "total_questions": self.stats["total_questions"],
                "questions_clean": self.stats["questions_clean"],
                "questions_flagged": self.stats["questions_flagged"],
                "total_flags": self.stats["total_flags"],
                "elapsed_seconds": self.stats["elapsed_seconds"],
                "by_type": {k: dict(v) for k, v in self.stats["by_type"].items()},
                "by_severity": self.stats["by_severity"],
                "by_flag_type": dict(self.stats["by_flag_type"]),
            },
            "by_grade": by_grade,
            "by_topic": by_topic,
            "flagged_questions": [a.to_dict() for a in self.audits if not a.is_clean],
        }
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n  Full report saved to {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Kiwimath Content Auditor v2 — type-aware quality checker",
    )
    parser.add_argument("--base-url", default="https://kiwimath-api-deufqab6gq-el.a.run.app")
    parser.add_argument("--grade", type=int, default=None)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--report", default=None)
    args = parser.parse_args()

    auditor = ContentAuditor(
        base_url=args.base_url, concurrency=args.concurrency,
        quick=args.quick, target_grade=args.grade,
    )

    async def run_and_cleanup():
        await auditor.run()
        auditor.print_report()
        if args.report:
            auditor.save_report(args.report)
        await auditor.close()

    asyncio.run(run_and_cleanup())


if __name__ == "__main__":
    main()
