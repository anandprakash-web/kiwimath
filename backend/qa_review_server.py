#!/usr/bin/env python3
"""
Kiwimath QA Review & Practice Server
Standalone HTTP server serving a mobile-first question review app.
Loads questions from ../content-v2/ relative to this script.
Run: python3 qa_review_server.py
Access: http://localhost:8899
"""

import http.server
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path
from datetime import datetime

PORT = 8899
SCRIPT_DIR = Path(__file__).resolve().parent
CONTENT_DIR = SCRIPT_DIR.parent / "content-v2"
REVIEW_DATA_FILE = SCRIPT_DIR / "qa_review_data.json"

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

ALL_QUESTIONS = {}  # id -> question dict
KANGAROO_G12 = []   # sorted by difficulty_score
KANGAROO_G34 = []
KANGAROO_G56 = []
BENJAMIN_G6 = []    # Benjamin Olympiad questions for Grade 6
CURRICULUM_DATA = {}  # (curriculum, grade) -> {chapter -> [questions]}
TOPIC_NAMES = {
    "1": "Counting", "2": "Arithmetic", "3": "Patterns", "4": "Logic",
    "5": "Spatial", "6": "Shapes", "7": "Word Problems", "8": "Puzzles",
}


def extract_questions_from_file(filepath):
    """Extract question list from a JSON file, handling both list and dict formats."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
        return []

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "questions" in data and isinstance(data["questions"], list):
            return data["questions"]
    return []


def should_skip_file(filepath):
    s = str(filepath).lower()
    return any(k in s for k in ("_workspace", "visual_registry", "manifest"))


def load_all_questions():
    global KANGAROO_G12, KANGAROO_G34, KANGAROO_G56

    kangaroo_g12 = []
    kangaroo_g34 = []
    kangaroo_g56 = []

    # --- Load Kangaroo / adaptive topic questions ---
    for topic_num in range(1, 9):
        topic_dirs = list(CONTENT_DIR.glob(f"topic-{topic_num}-*"))
        if not topic_dirs:
            continue
        topic_dir = topic_dirs[0]
        topic_name = TOPIC_NAMES.get(str(topic_num), f"Topic {topic_num}")

        for json_file in sorted(topic_dir.glob("*.json")):
            if should_skip_file(json_file):
                continue
            fname = json_file.name.lower()
            questions = extract_questions_from_file(json_file)

            for q in questions:
                if not isinstance(q, dict) or "id" not in q:
                    continue
                q.setdefault("difficulty_score", 50)
                q.setdefault("topic", topic_name)
                q["_topic_num"] = str(topic_num)
                q["_topic_name"] = topic_name
                q["_source_file"] = fname
                ALL_QUESTIONS[q["id"]] = q

                # Classify into grade bands based on filename
                if q["id"].startswith("T"):
                    if "g56" in fname:
                        kangaroo_g56.append(q)
                    elif "grade34" in fname or "variety" in fname:
                        kangaroo_g34.append(q)
                    elif fname == "questions.json":
                        kangaroo_g12.append(q)
                    else:
                        # data_handling, geometry_measurement, measurement_units
                        ds = q.get("difficulty_score", 50)
                        if ds <= 100:
                            kangaroo_g12.append(q)
                        elif ds <= 200:
                            kangaroo_g34.append(q)
                        else:
                            kangaroo_g56.append(q)

    # Sort by difficulty
    kangaroo_g12.sort(key=lambda q: (q.get("difficulty_score", 50), q["id"]))
    kangaroo_g34.sort(key=lambda q: (q.get("difficulty_score", 50), q["id"]))
    kangaroo_g56.sort(key=lambda q: (q.get("difficulty_score", 50), q["id"]))

    KANGAROO_G12 = kangaroo_g12
    KANGAROO_G34 = kangaroo_g34
    KANGAROO_G56 = kangaroo_g56

    # --- Load Benjamin / Olympiad questions for Grade 6 ---
    global BENJAMIN_G6
    benjamin_g6 = []
    benjamin_dir = CONTENT_DIR / "benjamin-olympiad" / "grade6"
    if benjamin_dir.exists():
        for json_file in sorted(benjamin_dir.glob("*.json")):
            if should_skip_file(json_file):
                continue
            questions = extract_questions_from_file(json_file)
            for q in questions:
                if not isinstance(q, dict) or "id" not in q:
                    continue
                q.setdefault("difficulty_score", 201)
                q.setdefault("topic", "Benjamin Olympiad")
                q["_topic_num"] = "benjamin"
                q["_topic_name"] = q.get("topic_name", "Benjamin Olympiad")
                q["_source_file"] = json_file.name
                ALL_QUESTIONS[q["id"]] = q
                benjamin_g6.append(q)
        # Deduplicate by ID (topic files overlap with main file)
        seen = set()
        deduped = []
        for q in benjamin_g6:
            if q["id"] not in seen:
                seen.add(q["id"])
                deduped.append(q)
        benjamin_g6 = deduped
    benjamin_g6.sort(key=lambda q: (q.get("difficulty_score", 201), q["id"]))
    BENJAMIN_G6 = benjamin_g6

    # --- Load curriculum questions ---
    curriculum_dirs = {
        "NCERT": CONTENT_DIR / "ncert-curriculum",
        "ICSE": CONTENT_DIR / "icse-curriculum",
        "IGCSE": CONTENT_DIR / "igcse-curriculum",
        "Singapore": CONTENT_DIR / "singapore-curriculum",
        "USCC": CONTENT_DIR / "us-common-core",
    }

    for curr_name, curr_dir in curriculum_dirs.items():
        if not curr_dir.exists():
            continue
        for grade_num in range(1, 7):
            grade_dir = curr_dir / f"grade{grade_num}"
            if not grade_dir.exists():
                continue
            chapter_map = {}
            for json_file in sorted(grade_dir.glob("*.json")):
                if should_skip_file(json_file):
                    continue
                questions = extract_questions_from_file(json_file)
                for q in questions:
                    if not isinstance(q, dict) or "id" not in q:
                        continue
                    q.setdefault("difficulty_score", 50)
                    q.setdefault("chapter", "Uncategorized")
                    ALL_QUESTIONS[q["id"]] = q
                    ch = q.get("chapter", "Uncategorized")
                    chapter_map.setdefault(ch, []).append(q)

            # Sort within each chapter by difficulty
            for ch in chapter_map:
                chapter_map[ch].sort(key=lambda q: (q.get("difficulty_score", 50), q["id"]))

            if chapter_map:
                CURRICULUM_DATA[(curr_name, grade_num)] = chapter_map

    total = len(ALL_QUESTIONS)
    print(f"Loaded {total} questions total.")
    print(f"  Kangaroo G1-2: {len(KANGAROO_G12)}")
    print(f"  Kangaroo G3-4: {len(KANGAROO_G34)}")
    print(f"  Kangaroo G5-6: {len(KANGAROO_G56)}")
    print(f"  Benjamin G6: {len(BENJAMIN_G6)}")
    curricula_loaded = set(k[0] for k in CURRICULUM_DATA.keys())
    print(f"  Curricula: {', '.join(sorted(curricula_loaded))}")


# ---------------------------------------------------------------------------
# Review data persistence
# ---------------------------------------------------------------------------

def load_review_data():
    if REVIEW_DATA_FILE.exists():
        try:
            with open(REVIEW_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"flags": {}, "comments": {}}


def save_review_data(data):
    with open(REVIEW_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def get_kangaroo_pool(grade):
    if grade in (1, 2):
        return KANGAROO_G12
    if grade in (3, 4):
        return KANGAROO_G34
    if grade == 5:
        return KANGAROO_G56
    if grade == 6:
        return BENJAMIN_G6
    return []


def question_to_api(q, include_review=False):
    """Convert question dict to API response, including review data if requested."""
    irt = q.get("irt_params", {})
    out = {
        "id": q.get("id"),
        "stem": q.get("stem", ""),
        "choices": q.get("choices", []),
        "correct_answer": q.get("correct_answer", 0),
        "difficulty_score": q.get("difficulty_score", 0),
        "competency_level": q.get("competency_level", ""),
        "topic": q.get("topic", ""),
        "chapter": q.get("chapter", ""),
        "irt_a": q.get("irt_a", irt.get("a", 0)),
        "irt_b": q.get("irt_b", irt.get("b", 0)),
        "irt_c": q.get("irt_c", irt.get("c", 0)),
        "visual_svg": q.get("visual_svg"),
        "visual_context": q.get("visual_context", q.get("visual_alt", "")),
        "hints": q.get("hint", q.get("hints", {})),
        "why": q.get("diagnostics", q.get("why", {})),
        "interaction_mode": q.get("interaction_mode", "mcq"),
        "skill_id": q.get("skill_id", ""),
        "skill_domain": q.get("skill_domain", ""),
        "tags": q.get("tags", []),
        "_topic_num": q.get("_topic_num", ""),
        "_topic_name": q.get("_topic_name", ""),
    }
    if include_review:
        rd = load_review_data()
        qid = q.get("id", "")
        out["flag"] = rd.get("flags", {}).get(qid, "")
        out["comments"] = rd.get("comments", {}).get(qid, [])
    return out


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

HTML_PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Kiwimath QA</title>
<style>
:root {
  --orange: #FF6D00;
  --orange-dark: #E65100;
  --orange-light: #FFF3E0;
  --green: #2E7D32;
  --green-light: #E8F5E9;
  --red: #C62828;
  --red-light: #FFEBEE;
  --yellow: #F9A825;
  --yellow-light: #FFFDE7;
  --blue: #1565C0;
  --blue-light: #E3F2FD;
  --gray: #757575;
  --gray-light: #F5F5F5;
  --gray-border: #E0E0E0;
  --white: #FFFFFF;
  --text: #212121;
  --text-secondary: #616161;
  --shadow: 0 2px 8px rgba(0,0,0,0.12);
  --radius: 12px;
  --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { height: 100%; overflow: hidden; }
body {
  font-family: var(--font);
  background: var(--gray-light);
  color: var(--text);
  display: flex; flex-direction: column;
  -webkit-tap-highlight-color: transparent;
}

/* TOP BAR */
.topbar {
  background: var(--orange);
  color: white;
  padding: 10px 16px;
  display: flex; align-items: center; gap: 10px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.15);
  z-index: 100;
  flex-shrink: 0;
}
.topbar-title { font-size: 18px; font-weight: 700; flex: 1; }
.topbar-btn {
  background: rgba(255,255,255,0.2);
  border: none; color: white;
  padding: 6px 10px; border-radius: 8px;
  font-size: 14px; cursor: pointer;
  font-family: var(--font);
}
.topbar-btn:hover { background: rgba(255,255,255,0.3); }
.topbar-btn.active { background: rgba(255,255,255,0.4); }

/* GRADE SELECTOR */
.grade-bar {
  background: var(--orange-dark);
  padding: 6px 16px;
  display: flex; gap: 6px;
  overflow-x: auto;
  flex-shrink: 0;
}
.grade-btn {
  background: rgba(255,255,255,0.15);
  border: none; color: white;
  padding: 5px 14px; border-radius: 20px;
  font-size: 13px; font-weight: 600;
  cursor: pointer; white-space: nowrap;
  font-family: var(--font);
}
.grade-btn.active { background: white; color: var(--orange-dark); }

/* TAB BAR */
.tab-bar {
  display: flex; background: white;
  border-bottom: 2px solid var(--gray-border);
  flex-shrink: 0;
}
.tab-btn {
  flex: 1; padding: 10px;
  border: none; background: none;
  font-size: 14px; font-weight: 600;
  color: var(--gray);
  cursor: pointer; position: relative;
  font-family: var(--font);
}
.tab-btn.active { color: var(--orange); }
.tab-btn.active::after {
  content: ''; position: absolute;
  bottom: -2px; left: 10%; width: 80%; height: 3px;
  background: var(--orange); border-radius: 3px 3px 0 0;
}

/* CONTENT AREA */
.content {
  flex: 1; overflow-y: auto;
  padding: 12px;
  -webkit-overflow-scrolling: touch;
}

/* QUESTION CARD */
.q-card {
  background: white; border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 16px;
  margin-bottom: 12px;
}
.q-header {
  display: flex; justify-content: space-between;
  align-items: center; margin-bottom: 10px;
  flex-wrap: wrap; gap: 4px;
}
.q-number {
  font-size: 12px; font-weight: 700;
  color: var(--orange); text-transform: uppercase;
}
.q-id {
  font-size: 11px; color: var(--gray);
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
}
.q-diff {
  font-size: 11px; color: var(--text-secondary);
  background: var(--gray-light); padding: 2px 8px;
  border-radius: 10px;
}
.q-meta-row {
  display: flex; gap: 6px; align-items: center; flex-wrap: wrap;
}
.q-stem {
  font-size: 17px; line-height: 1.5;
  margin-bottom: 14px; color: var(--text);
  white-space: pre-wrap;
}
.q-visual {
  margin-bottom: 14px; text-align: center;
  overflow: auto; max-height: 300px;
}
.q-visual svg { max-width: 100%; height: auto; }
.q-choices { display: flex; flex-direction: column; gap: 8px; }
.choice-btn {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 14px; border: 2px solid var(--gray-border);
  border-radius: 10px; background: white;
  font-size: 15px; cursor: pointer;
  transition: all 0.15s;
  text-align: left;
  font-family: var(--font);
  width: 100%;
}
.choice-btn:hover:not(.disabled) { border-color: var(--orange); background: var(--orange-light); }
.choice-btn .choice-letter {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--gray-light); display: flex;
  align-items: center; justify-content: center;
  font-weight: 700; font-size: 13px;
  color: var(--text-secondary); flex-shrink: 0;
}
.choice-btn .choice-text { flex: 1; line-height: 1.4; }
.choice-btn.correct {
  border-color: var(--green); background: var(--green-light);
}
.choice-btn.correct .choice-letter {
  background: var(--green); color: white;
}
.choice-btn.wrong {
  border-color: var(--red); background: var(--red-light);
}
.choice-btn.wrong .choice-letter {
  background: var(--red); color: white;
}
.choice-btn.disabled { pointer-events: none; opacity: 0.7; }
.choice-btn.disabled.correct, .choice-btn.disabled.wrong { opacity: 1; }

/* FEEDBACK */
.feedback {
  margin-top: 12px; padding: 10px 14px;
  border-radius: 8px; font-size: 14px; font-weight: 600;
}
.feedback.correct-fb { background: var(--green-light); color: var(--green); }
.feedback.wrong-fb { background: var(--red-light); color: var(--red); }
.feedback .flag-link {
  display: inline-block; margin-left: 10px;
  color: var(--blue); text-decoration: underline;
  cursor: pointer; font-weight: 400; font-size: 13px;
}

/* HINTS */
.hints-toggle {
  margin-top: 10px; color: var(--blue);
  font-size: 13px; cursor: pointer;
  text-decoration: underline;
  background: none; border: none;
  font-family: var(--font);
}
.hints-box {
  margin-top: 8px; padding: 10px;
  background: var(--blue-light); border-radius: 8px;
  font-size: 13px; line-height: 1.5;
  display: none;
}
.hints-box.show { display: block; }
.hint-item { margin-bottom: 6px; }
.hint-label { font-weight: 600; color: var(--blue); }

/* WHY / DIAGNOSTICS */
.why-box {
  margin-top: 8px; padding: 10px;
  background: var(--yellow-light); border-radius: 8px;
  font-size: 13px; line-height: 1.5;
  display: none;
}
.why-box.show { display: block; }

/* ADMIN FLAGS */
.admin-panel {
  margin-top: 14px; padding: 14px;
  background: var(--gray-light); border-radius: 10px;
  border: 1px solid var(--gray-border);
}
.admin-panel-title {
  font-size: 12px; font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.flag-buttons { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.flag-btn {
  padding: 6px 12px; border-radius: 8px;
  border: 2px solid var(--gray-border);
  background: white; font-size: 12px;
  cursor: pointer; font-family: var(--font);
  font-weight: 600;
}
.flag-btn:hover { opacity: 0.8; }
.flag-btn.eliminate { border-color: var(--red); color: var(--red); }
.flag-btn.eliminate.active { background: var(--red); color: white; }
.flag-btn.repeated { border-color: var(--yellow); color: #F57F17; }
.flag-btn.repeated.active { background: var(--yellow); color: white; }
.flag-btn.needs-fix { border-color: var(--blue); color: var(--blue); }
.flag-btn.needs-fix.active { background: var(--blue); color: white; }
.flag-btn.approved { border-color: var(--green); color: var(--green); }
.flag-btn.approved.active { background: var(--green); color: white; }
.flag-btn.clear-flag { border-color: var(--gray); color: var(--gray); }

.comment-area { margin-top: 10px; }
.comment-input {
  width: 100%; padding: 8px; border: 1px solid var(--gray-border);
  border-radius: 8px; font-size: 13px; resize: vertical;
  min-height: 40px; font-family: var(--font);
}
.comment-post {
  margin-top: 6px; padding: 6px 16px;
  background: var(--orange); color: white;
  border: none; border-radius: 8px;
  font-size: 13px; font-weight: 600;
  cursor: pointer; font-family: var(--font);
}
.comment-list { margin-top: 8px; }
.comment-item {
  padding: 8px; background: white;
  border-radius: 8px; margin-bottom: 6px;
  font-size: 13px; position: relative;
}
.comment-meta { font-size: 11px; color: var(--gray); margin-bottom: 4px; }
.comment-delete {
  position: absolute; top: 6px; right: 8px;
  background: none; border: none; color: var(--red);
  cursor: pointer; font-size: 16px; line-height: 1;
}

/* NAV BUTTONS */
.nav-bar {
  display: flex; gap: 10px; margin-top: 14px;
}
.nav-btn {
  flex: 1; padding: 12px; border: none;
  border-radius: 10px; font-size: 15px;
  font-weight: 700; cursor: pointer;
  font-family: var(--font);
}
.nav-btn.prev { background: var(--gray-light); color: var(--text); }
.nav-btn.next { background: var(--orange); color: white; }
.nav-btn:disabled { opacity: 0.4; cursor: default; }

/* BOTTOM STATS */
.bottom-bar {
  background: white;
  border-top: 1px solid var(--gray-border);
  padding: 8px 16px;
  display: flex; justify-content: space-around;
  font-size: 12px; font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.stat-item { text-align: center; }
.stat-value { font-size: 16px; color: var(--text); }
.stat-value.correct-val { color: var(--green); }
.stat-value.wrong-val { color: var(--red); }
.stat-value.acc-val { color: var(--orange); }

/* CURRICULUM PICKER */
.picker-section {
  margin-bottom: 16px;
}
.picker-title {
  font-size: 13px; font-weight: 700; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.picker-grid {
  display: flex; flex-wrap: wrap; gap: 8px;
}
.picker-btn {
  padding: 10px 16px; border: 2px solid var(--gray-border);
  border-radius: 10px; background: white;
  font-size: 14px; font-weight: 600;
  cursor: pointer; font-family: var(--font);
  transition: all 0.15s;
}
.picker-btn:hover { border-color: var(--orange); }
.picker-btn.active { background: var(--orange); color: white; border-color: var(--orange); }

/* CHAPTER LIST */
.chapter-list { display: flex; flex-direction: column; gap: 8px; }
.chapter-item {
  background: white; border-radius: 10px;
  padding: 14px; box-shadow: var(--shadow);
  cursor: pointer; display: flex;
  justify-content: space-between; align-items: center;
  transition: all 0.15s;
  border-left: 4px solid transparent;
}
.chapter-item:hover { border-left-color: var(--orange); }
.chapter-name { font-size: 14px; font-weight: 600; flex: 1; }
.chapter-count {
  font-size: 12px; color: var(--gray);
  background: var(--gray-light); padding: 3px 10px;
  border-radius: 12px; white-space: nowrap;
}

/* TOPIC FILTER */
.topic-filter {
  display: flex; gap: 6px; overflow-x: auto;
  padding: 8px 0; margin-bottom: 8px;
}
.topic-chip {
  padding: 5px 12px; border-radius: 16px;
  border: 1px solid var(--gray-border);
  background: white; font-size: 12px;
  cursor: pointer; white-space: nowrap;
  font-family: var(--font); font-weight: 500;
}
.topic-chip.active { background: var(--orange); color: white; border-color: var(--orange); }

/* INFO MESSAGE */
.info-msg {
  padding: 24px; text-align: center;
  color: var(--text-secondary); font-size: 15px;
  line-height: 1.6;
}
.info-msg .emoji { font-size: 40px; margin-bottom: 10px; display: block; }

/* ADMIN LOGIN MODAL */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  display: none; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal-overlay.show { display: flex; }
.modal-box {
  background: white; border-radius: 16px;
  padding: 24px; width: 300px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.modal-title { font-size: 18px; font-weight: 700; margin-bottom: 16px; }
.modal-input {
  width: 100%; padding: 10px; border: 2px solid var(--gray-border);
  border-radius: 10px; font-size: 15px; margin-bottom: 12px;
  font-family: var(--font);
}
.modal-input:focus { border-color: var(--orange); outline: none; }
.modal-buttons { display: flex; gap: 8px; }
.modal-btn {
  flex: 1; padding: 10px; border: none;
  border-radius: 10px; font-size: 14px;
  font-weight: 600; cursor: pointer;
  font-family: var(--font);
}
.modal-btn.cancel { background: var(--gray-light); color: var(--text); }
.modal-btn.submit { background: var(--orange); color: white; }
.modal-error { color: var(--red); font-size: 13px; margin-bottom: 8px; display: none; }

/* FLAG INDICATOR */
.flag-indicator {
  display: inline-block; padding: 2px 8px;
  border-radius: 6px; font-size: 11px;
  font-weight: 700; text-transform: uppercase;
}
.flag-indicator.eliminate { background: var(--red-light); color: var(--red); }
.flag-indicator.repeated { background: var(--yellow-light); color: #F57F17; }
.flag-indicator.needs-fix { background: var(--blue-light); color: var(--blue); }
.flag-indicator.approved { background: var(--green-light); color: var(--green); }

/* EXPORT BAR */
.export-bar {
  padding: 4px 16px; text-align: right;
  flex-shrink: 0; display: none;
  background: var(--orange-light);
}
.export-btn {
  padding: 5px 14px; background: var(--blue);
  color: white; border: none; border-radius: 8px;
  font-size: 12px; font-weight: 600; cursor: pointer;
  font-family: var(--font);
}

/* RESET STATS BTN */
.reset-stats {
  margin-top: 4px; background: none; border: none;
  color: var(--gray); font-size: 11px; cursor: pointer;
  text-decoration: underline; font-family: var(--font);
}

/* Scrollbar */
.content::-webkit-scrollbar { width: 4px; }
.content::-webkit-scrollbar-track { background: transparent; }
.content::-webkit-scrollbar-thumb { background: var(--gray-border); border-radius: 4px; }

/* Loading */
.loading { text-align: center; padding: 40px; color: var(--gray); }
</style>
</head>
<body>

<!-- TOP BAR -->
<div class="topbar">
  <div class="topbar-title">Kiwimath QA</div>
  <button class="topbar-btn" id="adminToggle" onclick="toggleAdmin()">&#128274;</button>
</div>

<!-- GRADE BAR -->
<div class="grade-bar" id="gradeBar">
  <button class="grade-btn active" data-grade="1" onclick="selectGrade(1)">G1</button>
  <button class="grade-btn" data-grade="2" onclick="selectGrade(2)">G2</button>
  <button class="grade-btn" data-grade="3" onclick="selectGrade(3)">G3</button>
  <button class="grade-btn" data-grade="4" onclick="selectGrade(4)">G4</button>
  <button class="grade-btn" data-grade="5" onclick="selectGrade(5)">G5</button>
  <button class="grade-btn" data-grade="6" onclick="selectGrade(6)">G6</button>
</div>

<!-- TAB BAR -->
<div class="tab-bar">
  <button class="tab-btn active" id="tabSmart" onclick="switchTab('smart')">Smart Practice</button>
  <button class="tab-btn" id="tabCurr" onclick="switchTab('curriculum')">Curriculum</button>
</div>

<!-- EXPORT BAR -->
<div class="export-bar" id="exportBar">
  <button class="export-btn" onclick="exportFlags()">Export Flags JSON</button>
</div>

<!-- CONTENT -->
<div class="content" id="content">
  <div class="loading">Loading questions...</div>
</div>

<!-- BOTTOM STATS -->
<div class="bottom-bar">
  <div class="stat-item"><div class="stat-value" id="statAttempted">0</div>Attempted</div>
  <div class="stat-item"><div class="stat-value correct-val" id="statCorrect">0</div>Correct</div>
  <div class="stat-item"><div class="stat-value wrong-val" id="statWrong">0</div>Wrong</div>
  <div class="stat-item">
    <div class="stat-value acc-val" id="statAccuracy">0%</div>Accuracy
    <br><button class="reset-stats" onclick="resetStats()">reset</button>
  </div>
</div>

<!-- ADMIN LOGIN MODAL -->
<div class="modal-overlay" id="adminModal">
  <div class="modal-box">
    <div class="modal-title">Admin Login</div>
    <div class="modal-error" id="adminError">Wrong password</div>
    <input type="password" class="modal-input" id="adminPassword" placeholder="Enter password" onkeydown="if(event.key==='Enter')submitAdmin()">
    <div class="modal-buttons">
      <button class="modal-btn cancel" onclick="closeAdminModal()">Cancel</button>
      <button class="modal-btn submit" onclick="submitAdmin()">Login</button>
    </div>
  </div>
</div>

<script>
// =========================================================================
// STATE
// =========================================================================
var S = {
  tab: 'smart',
  grade: 1,
  isAdmin: false,
  reviewerName: 'Reviewer',

  // Smart Practice
  smartQuestions: [],
  smartIndex: 0,
  smartTopic: '',
  smartTotal: 0,

  // Curriculum
  curriculumName: '',
  currChapters: [],
  currChapter: '',
  currQuestions: [],
  currIndex: 0,
  currView: 'pick',

  // Session stats
  attempted: 0,
  correct: 0,
  wrong: 0,

  // Per-grade progress saved to localStorage
  _smartProgress: {},
};

var CURRICULUM_DISPLAY = {
  'NCERT': 'NCERT',
  'ICSE': 'ICSE',
  'IGCSE': 'Cambridge',
  'Singapore': 'Singapore',
  'USCC': 'US Common Core'
};
var CURRICULUM_KEYS = ['NCERT', 'ICSE', 'IGCSE', 'Singapore', 'USCC'];
var TOPIC_NAMES = {1:'Counting',2:'Arithmetic',3:'Patterns',4:'Logic',5:'Spatial',6:'Shapes',7:'Word Problems',8:'Puzzles'};
var LETTERS = ['A', 'B', 'C', 'D'];

// =========================================================================
// INIT
// =========================================================================
function init() {
  loadSessionStats();
  loadProgress();
  updateStatsUI();
  if (S.tab === 'curriculum') {
    switchTab('curriculum');
  } else {
    loadSmartQuestions();
  }
}

function loadSessionStats() {
  try {
    var d = JSON.parse(localStorage.getItem('kiwi_session') || '{}');
    S.attempted = d.a || 0;
    S.correct = d.c || 0;
    S.wrong = d.w || 0;
  } catch(e) {}
}

function saveSessionStats() {
  localStorage.setItem('kiwi_session', JSON.stringify({a: S.attempted, c: S.correct, w: S.wrong}));
}

function resetStats() {
  S.attempted = 0; S.correct = 0; S.wrong = 0;
  saveSessionStats();
  updateStatsUI();
}

function loadProgress() {
  try {
    var d = JSON.parse(localStorage.getItem('kiwi_progress') || '{}');
    if (d.grade) S.grade = d.grade;
    if (d.tab) S.tab = d.tab;
    S._smartProgress = d.sp || {};
    // Sync grade buttons
    document.querySelectorAll('.grade-btn').forEach(function(btn) {
      btn.classList.toggle('active', parseInt(btn.getAttribute('data-grade')) === S.grade);
    });
    // Sync tab buttons
    document.getElementById('tabSmart').classList.toggle('active', S.tab === 'smart');
    document.getElementById('tabCurr').classList.toggle('active', S.tab === 'curriculum');
  } catch(e) {}
}

function saveProgress() {
  localStorage.setItem('kiwi_progress', JSON.stringify({
    grade: S.grade, tab: S.tab, sp: S._smartProgress
  }));
}

function smartKey() {
  return 'g' + S.grade + '_t' + (S.smartTopic || 'all');
}

function getSavedIdx() {
  return S._smartProgress[smartKey()] || 0;
}

function setSavedIdx(i) {
  S._smartProgress[smartKey()] = i;
  saveProgress();
}

// =========================================================================
// GRADE & TAB
// =========================================================================
function selectGrade(g) {
  S.grade = g;
  document.querySelectorAll('.grade-btn').forEach(function(btn) {
    btn.classList.toggle('active', parseInt(btn.getAttribute('data-grade')) === g);
  });
  saveProgress();
  if (S.tab === 'smart') {
    loadSmartQuestions();
  } else {
    S.currView = 'pick';
    S.curriculumName = '';
    renderCurriculum();
  }
}

function switchTab(tab) {
  S.tab = tab;
  document.getElementById('tabSmart').classList.toggle('active', tab === 'smart');
  document.getElementById('tabCurr').classList.toggle('active', tab === 'curriculum');
  saveProgress();
  if (tab === 'smart') {
    loadSmartQuestions();
  } else {
    S.currView = 'pick';
    renderCurriculum();
  }
}

// =========================================================================
// ADMIN
// =========================================================================
function toggleAdmin() {
  if (S.isAdmin) {
    S.isAdmin = false;
    document.getElementById('adminToggle').innerHTML = '&#128274;';
    document.getElementById('adminToggle').classList.remove('active');
    document.getElementById('exportBar').style.display = 'none';
    refreshCurrentQuestion();
    return;
  }
  document.getElementById('adminModal').classList.add('show');
  document.getElementById('adminPassword').value = '';
  document.getElementById('adminError').style.display = 'none';
  setTimeout(function() { document.getElementById('adminPassword').focus(); }, 100);
}

function closeAdminModal() {
  document.getElementById('adminModal').classList.remove('show');
}

function submitAdmin() {
  var pw = document.getElementById('adminPassword').value;
  if (pw === 'kiwiadmin') {
    S.isAdmin = true;
    document.getElementById('adminToggle').innerHTML = '&#128275;';
    document.getElementById('adminToggle').classList.add('active');
    document.getElementById('exportBar').style.display = 'block';
    closeAdminModal();
    var name = prompt('Reviewer name:', S.reviewerName);
    if (name && name.trim()) S.reviewerName = name.trim();
    refreshCurrentQuestion();
  } else {
    document.getElementById('adminError').style.display = 'block';
  }
}

function refreshCurrentQuestion() {
  if (S.tab === 'smart' && S.smartQuestions.length > 0) {
    var q = S.smartQuestions[S.smartIndex];
    if (q && q.id) fetchAndRender(q.id, 'smart');
    else renderSmartQuestion();
  } else if (S.tab === 'curriculum' && S.currView === 'questions' && S.currQuestions.length > 0) {
    var q2 = S.currQuestions[S.currIndex];
    if (q2 && q2.id) fetchAndRender(q2.id, 'curr');
    else renderCurrQuestion();
  }
}

// =========================================================================
// SMART PRACTICE
// =========================================================================
function loadSmartQuestions() {
  if (false) { /* G6 Benjamin questions now available */
    rc('<div class="info-msg"><span class="emoji">&#128218;</span>Grade 6 doesn\'t have adaptive questions yet.<br>Use the <strong>Curriculum</strong> tab instead.</div>');
    return;
  }
  var url = '/api/smart-practice?grade=' + S.grade + '&start=0&count=99999';
  if (S.smartTopic) url += '&topic=' + encodeURIComponent(S.smartTopic);
  fetch(url).then(function(r) { return r.json(); }).then(function(data) {
    S.smartQuestions = data.questions || [];
    S.smartTotal = data.total || S.smartQuestions.length;
    S.smartIndex = getSavedIdx();
    if (S.smartIndex >= S.smartQuestions.length) S.smartIndex = 0;
    renderSmartView();
  }).catch(function() {
    rc('<div class="info-msg">Error loading questions.</div>');
  });
}

function renderSmartView() {
  if (S.smartQuestions.length === 0) {
    rc('<div class="info-msg"><span class="emoji">&#128528;</span>No questions found for this selection.</div>');
    return;
  }
  renderSmartQuestion();
}

function renderSmartQuestion() {
  var q = S.smartQuestions[S.smartIndex];
  if (!q) {
    rc('<div class="info-msg">No more questions!</div>');
    return;
  }
  var html = buildTopicFilter();
  html += buildQCard(q, S.smartIndex, S.smartQuestions.length, 'smart');
  rc(html);
}

function buildTopicFilter() {
  var h = '<div class="topic-filter">';
  h += '<button class="topic-chip ' + (!S.smartTopic ? 'active' : '') + '" onclick="filterTopic(\'\')">All</button>';
  for (var t = 1; t <= 8; t++) {
    var active = S.smartTopic === String(t) ? 'active' : '';
    h += '<button class="topic-chip ' + active + '" onclick="filterTopic(\'' + t + '\')">' + TOPIC_NAMES[t] + '</button>';
  }
  h += '</div>';
  return h;
}

function filterTopic(t) {
  S.smartTopic = t;
  loadSmartQuestions();
}

// =========================================================================
// CURRICULUM
// =========================================================================
function renderCurriculum() {
  if (S.currView === 'pick') renderCurrPicker();
  else if (S.currView === 'chapters') loadCurrChapters();
  else if (S.currView === 'questions') renderCurrQuestion();
}

function renderCurrPicker() {
  var h = '<div class="picker-section"><div class="picker-title">Select Curriculum</div><div class="picker-grid">';
  CURRICULUM_KEYS.forEach(function(k) {
    var active = S.curriculumName === k ? 'active' : '';
    h += '<button class="picker-btn ' + active + '" onclick="pickCurr(\'' + k + '\')">' + CURRICULUM_DISPLAY[k] + '</button>';
  });
  h += '</div></div>';
  if (S.curriculumName) {
    h += '<div class="picker-section"><div class="picker-title">Select Grade</div><div class="picker-grid">';
    for (var g = 1; g <= 6; g++) {
      h += '<button class="picker-btn" onclick="pickCurrGrade(' + g + ')">Grade ' + g + '</button>';
    }
    h += '</div></div>';
  }
  rc(h);
}

function pickCurr(c) {
  S.curriculumName = c;
  renderCurrPicker();
}

function pickCurrGrade(g) {
  S.grade = g;
  document.querySelectorAll('.grade-btn').forEach(function(btn) {
    btn.classList.toggle('active', parseInt(btn.getAttribute('data-grade')) === g);
  });
  S.currView = 'chapters';
  loadCurrChapters();
}

function loadCurrChapters() {
  var url = '/api/curriculum/chapters?curriculum=' + encodeURIComponent(S.curriculumName) + '&grade=' + S.grade;
  fetch(url).then(function(r) { return r.json(); }).then(function(data) {
    S.currChapters = data.chapters || [];
    renderChapterList();
  });
}

function renderChapterList() {
  if (S.currChapters.length === 0) {
    rc('<div class="info-msg"><span class="emoji">&#128528;</span>No chapters found for ' + esc(CURRICULUM_DISPLAY[S.curriculumName] || S.curriculumName) + ' Grade ' + S.grade + '.</div>' +
      '<div style="text-align:center;margin-top:12px"><button class="picker-btn" onclick="backToPicker()">Back</button></div>');
    return;
  }
  var h = '<div style="margin-bottom:10px;display:flex;align-items:center;gap:8px">' +
    '<button class="picker-btn" onclick="backToPicker()" style="padding:6px 12px;font-size:13px">&larr; Back</button>' +
    '<span style="font-weight:700;font-size:14px">' + esc(CURRICULUM_DISPLAY[S.curriculumName] || S.curriculumName) + ' &mdash; Grade ' + S.grade + '</span></div>';
  h += '<div class="chapter-list">';
  S.currChapters.forEach(function(ch) {
    h += '<div class="chapter-item" onclick="pickChapter(' + escJ(ch.name) + ')">' +
      '<div class="chapter-name">' + esc(ch.name) + '</div>' +
      '<div class="chapter-count">' + ch.count + ' Q</div></div>';
  });
  h += '</div>';
  rc(h);
}

function backToPicker() {
  S.currView = 'pick';
  renderCurrPicker();
}

function pickChapter(ch) {
  S.currChapter = ch;
  S.currView = 'questions';
  S.currIndex = 0;
  loadCurrQuestions();
}

function loadCurrQuestions() {
  var url = '/api/curriculum/questions?curriculum=' + encodeURIComponent(S.curriculumName) +
    '&grade=' + S.grade + '&chapter=' + encodeURIComponent(S.currChapter) +
    '&start=0&count=99999';
  fetch(url).then(function(r) { return r.json(); }).then(function(data) {
    S.currQuestions = data.questions || [];
    renderCurrQuestion();
  });
}

function renderCurrQuestion() {
  if (S.currQuestions.length === 0) {
    rc('<div class="info-msg">No questions in this chapter.</div>' +
      '<div style="text-align:center;margin-top:12px"><button class="picker-btn" onclick="backToChapters()">Back to Chapters</button></div>');
    return;
  }
  var q = S.currQuestions[S.currIndex];
  if (!q) {
    rc('<div class="info-msg">End of chapter!</div>' +
      '<div style="text-align:center;margin-top:12px"><button class="picker-btn" onclick="backToChapters()">Back to Chapters</button></div>');
    return;
  }
  var backBtn = '<div style="margin-bottom:8px"><button class="picker-btn" onclick="backToChapters()" style="padding:5px 10px;font-size:12px">&larr; ' + esc(S.currChapter) + '</button></div>';
  var html = backBtn + buildQCard(q, S.currIndex, S.currQuestions.length, 'curr');
  rc(html);
}

function backToChapters() {
  S.currView = 'chapters';
  loadCurrChapters();
}

// =========================================================================
// QUESTION CARD BUILDER
// =========================================================================
function buildQCard(q, index, total, mode) {
  var aKey = mode + '_' + q.id;
  var wasAnswered = sessionStorage.getItem(aKey);
  var selIdx = wasAnswered !== null ? parseInt(sessionStorage.getItem(aKey + '_s')) : null;
  var answered = wasAnswered === '1';

  var h = '<div class="q-card">';

  // Header
  h += '<div class="q-header">';
  h += '<div class="q-meta-row">';
  h += '<span class="q-number">Q' + (index + 1) + ' / ' + total + '</span>';
  h += '<span class="q-id">' + esc(q.id) + '</span>';
  if (q.flag) {
    h += ' <span class="flag-indicator ' + esc(q.flag) + '">' + esc(q.flag.replace(/-/g, ' ')) + '</span>';
  }
  h += '</div>';
  h += '<span class="q-diff">D:' + (q.difficulty_score != null ? q.difficulty_score : '?') + '</span>';
  h += '</div>';

  // Stem
  h += '<div class="q-stem">' + esc(q.stem) + '</div>';

  // SVG visual
  if (q.visual_svg) {
    h += '<div class="q-visual">' + q.visual_svg + '</div>';
  }

  // Choices
  h += '<div class="q-choices">';
  var choices = q.choices || [];
  for (var i = 0; i < choices.length; i++) {
    var cls = 'choice-btn';
    if (answered) {
      cls += ' disabled';
      if (i === q.correct_answer) cls += ' correct';
      else if (i === selIdx) cls += ' wrong';
    }
    h += '<button class="' + cls + '" onclick="doAnswer(\'' + mode + '\',' + i + ',' + q.correct_answer + ',' + escJ(q.id) + ')">';
    h += '<span class="choice-letter">' + LETTERS[i] + '</span>';
    h += '<span class="choice-text">' + esc(String(choices[i])) + '</span>';
    h += '</button>';
  }
  h += '</div>';

  // Feedback
  if (answered) {
    var isCorr = selIdx === q.correct_answer;
    var fbCls = isCorr ? 'correct-fb' : 'wrong-fb';
    var cLetter = LETTERS[q.correct_answer] || '?';
    var fbText = isCorr ? 'Correct!' : 'Wrong &mdash; answer is ' + cLetter;
    h += '<div class="feedback ' + fbCls + '">' + fbText;
    if (!isCorr) {
      h += ' <span class="flag-link" onclick="quickFlag(' + escJ(q.id) + ')">Flag this question</span>';
    }
    h += '</div>';

    // Hints
    var hints = q.hints;
    if (hints && typeof hints === 'object' && Object.keys(hints).length > 0) {
      var hintId = 'hints_' + index;
      h += '<button class="hints-toggle" onclick="togBox(\'' + hintId + '\',this,\'Hints\')">Show Hints</button>';
      h += '<div class="hints-box" id="' + hintId + '">';
      for (var hk in hints) {
        if (hints.hasOwnProperty(hk)) {
          h += '<div class="hint-item"><span class="hint-label">' + esc(hk) + ':</span> ' + esc(String(hints[hk])) + '</div>';
        }
      }
      h += '</div>';
    }

    // Diagnostics / Why
    var why = q.why;
    if (why && typeof why === 'object' && Object.keys(why).length > 0) {
      var whyId = 'why_' + index;
      h += '<button class="hints-toggle" onclick="togBox(\'' + whyId + '\',this,\'Explanation\')">Show Explanation</button>';
      h += '<div class="why-box" id="' + whyId + '">';
      for (var wk in why) {
        if (why.hasOwnProperty(wk)) {
          h += '<div class="hint-item"><span class="hint-label">' + esc(wk) + ':</span> ' + esc(String(why[wk])) + '</div>';
        }
      }
      h += '</div>';
    }

    // Admin panel
    if (S.isAdmin) {
      h += buildAdminPanel(q);
    }
  }

  h += '</div>'; // end q-card

  // Nav
  h += '<div class="nav-bar">';
  h += '<button class="nav-btn prev" onclick="nav(\'' + mode + '\',-1)"' + (index <= 0 ? ' disabled' : '') + '>&larr; Prev</button>';
  h += '<button class="nav-btn next" onclick="nav(\'' + mode + '\',1)"' + (index >= total - 1 ? ' disabled' : '') + '>Next &rarr;</button>';
  h += '</div>';

  return h;
}

function buildAdminPanel(q) {
  var flags = [
    {key: 'eliminate', label: '&#128465; Eliminate', cls: 'eliminate'},
    {key: 'repeated', label: '&#128260; Repeated', cls: 'repeated'},
    {key: 'needs-fix', label: '&#128295; Needs Fix', cls: 'needs-fix'},
    {key: 'approved', label: '&#9989; Approved', cls: 'approved'}
  ];
  var h = '<div class="admin-panel">';
  h += '<div class="admin-panel-title">Admin Review</div>';
  h += '<div class="flag-buttons">';
  flags.forEach(function(f) {
    var active = q.flag === f.key ? 'active' : '';
    h += '<button class="flag-btn ' + f.cls + ' ' + active + '" onclick="setFlag(' + escJ(q.id) + ',\'' + f.key + '\')">' + f.label + '</button>';
  });
  h += '<button class="flag-btn clear-flag" onclick="setFlag(' + escJ(q.id) + ',\'\')">&times; Clear</button>';
  h += '</div>';

  // Comments
  h += '<div class="comment-area">';
  h += '<textarea class="comment-input" id="commentInput" placeholder="Add a comment..."></textarea>';
  h += '<button class="comment-post" onclick="postComment(' + escJ(q.id) + ')">Post Comment</button>';
  h += '<div class="comment-list">';
  if (q.comments && q.comments.length > 0) {
    q.comments.forEach(function(c, i) {
      h += '<div class="comment-item">';
      h += '<div class="comment-meta">' + esc(c.reviewer || 'Unknown') + ' &mdash; ' + esc(c.timestamp || '') + '</div>';
      h += '<div>' + esc(c.text || '') + '</div>';
      h += '<button class="comment-delete" onclick="delComment(' + escJ(q.id) + ',' + i + ')">&times;</button>';
      h += '</div>';
    });
  }
  h += '</div></div></div>';
  return h;
}

// =========================================================================
// ACTIONS
// =========================================================================
function doAnswer(mode, selected, correct, qid) {
  var aKey = mode + '_' + qid;
  if (sessionStorage.getItem(aKey) === '1') return;
  sessionStorage.setItem(aKey, '1');
  sessionStorage.setItem(aKey + '_s', String(selected));
  S.attempted++;
  if (selected === correct) S.correct++;
  else S.wrong++;
  saveSessionStats();
  updateStatsUI();
  fetchAndRender(qid, mode);
}

function fetchAndRender(qid, mode) {
  fetch('/api/question?id=' + encodeURIComponent(qid)).then(function(r) { return r.json(); }).then(function(q) {
    if (mode === 'smart') {
      S.smartQuestions[S.smartIndex] = q;
      renderSmartQuestion();
    } else {
      S.currQuestions[S.currIndex] = q;
      renderCurrQuestion();
    }
  });
}

function nav(mode, dir) {
  if (mode === 'smart') {
    S.smartIndex = Math.max(0, Math.min(S.smartQuestions.length - 1, S.smartIndex + dir));
    setSavedIdx(S.smartIndex);
    var q = S.smartQuestions[S.smartIndex];
    if (q && q.id) {
      fetch('/api/question?id=' + encodeURIComponent(q.id)).then(function(r) { return r.json(); }).then(function(fq) {
        S.smartQuestions[S.smartIndex] = fq;
        renderSmartQuestion();
      }).catch(function() { renderSmartQuestion(); });
    } else {
      renderSmartQuestion();
    }
  } else {
    S.currIndex = Math.max(0, Math.min(S.currQuestions.length - 1, S.currIndex + dir));
    var q2 = S.currQuestions[S.currIndex];
    if (q2 && q2.id) {
      fetch('/api/question?id=' + encodeURIComponent(q2.id)).then(function(r) { return r.json(); }).then(function(fq) {
        S.currQuestions[S.currIndex] = fq;
        renderCurrQuestion();
      }).catch(function() { renderCurrQuestion(); });
    } else {
      renderCurrQuestion();
    }
  }
  document.getElementById('content').scrollTop = 0;
}

function quickFlag(qid) {
  if (S.isAdmin) {
    setFlag(qid, 'needs-fix');
  } else {
    alert('Enable admin mode (lock icon) to flag questions.');
  }
}

function setFlag(qid, flag) {
  fetch('/api/flag', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question_id: qid, flag: flag, reviewer: S.reviewerName})
  }).then(function(r) { return r.json(); }).then(function() {
    var mode = S.tab === 'smart' ? 'smart' : 'curr';
    fetchAndRender(qid, mode);
  });
}

function postComment(qid) {
  var el = document.getElementById('commentInput');
  var text = el ? el.value.trim() : '';
  if (!text) return;
  fetch('/api/comment', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question_id: qid, text: text, reviewer: S.reviewerName})
  }).then(function(r) { return r.json(); }).then(function() {
    var mode = S.tab === 'smart' ? 'smart' : 'curr';
    fetchAndRender(qid, mode);
  });
}

function delComment(qid, index) {
  if (!confirm('Delete this comment?')) return;
  fetch('/api/comment/delete', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question_id: qid, index: index})
  }).then(function(r) { return r.json(); }).then(function() {
    var mode = S.tab === 'smart' ? 'smart' : 'curr';
    fetchAndRender(qid, mode);
  });
}

function exportFlags() {
  window.open('/api/export', '_blank');
}

function togBox(id, btn, label) {
  var box = document.getElementById(id);
  if (box) {
    var vis = box.classList.toggle('show');
    btn.textContent = (vis ? 'Hide ' : 'Show ') + label;
  }
}

// =========================================================================
// RENDER HELPERS
// =========================================================================
function rc(html) {
  document.getElementById('content').innerHTML = html;
}

function updateStatsUI() {
  document.getElementById('statAttempted').textContent = S.attempted;
  document.getElementById('statCorrect').textContent = S.correct;
  document.getElementById('statWrong').textContent = S.wrong;
  var acc = S.attempted > 0 ? Math.round(S.correct / S.attempted * 100) : 0;
  document.getElementById('statAccuracy').textContent = acc + '%';
}

function esc(s) {
  if (s == null) return '';
  var d = document.createElement('div');
  d.appendChild(document.createTextNode(String(s)));
  return d.innerHTML;
}

function escJ(s) {
  // Return a JS string literal for use in onclick attrs
  return "'" + String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'";
}

// =========================================================================
// KEYBOARD SHORTCUTS
// =========================================================================
document.addEventListener('keydown', function(e) {
  // Skip if typing in a textarea/input
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

  var mode = S.tab === 'smart' ? 'smart' : 'curr';
  var questions = mode === 'smart' ? S.smartQuestions : S.currQuestions;
  var index = mode === 'smart' ? S.smartIndex : S.currIndex;
  var q = questions[index];
  if (!q) return;

  var key = e.key.toLowerCase();
  var answerMap = {a:0, b:1, c:2, d:3, '1':0, '2':1, '3':2, '4':3};
  if (key in answerMap) {
    var aKey = mode + '_' + q.id;
    if (sessionStorage.getItem(aKey) !== '1') {
      doAnswer(mode, answerMap[key], q.correct_answer, q.id);
      e.preventDefault();
    }
  }
  if (key === 'arrowright' || key === 'n') { nav(mode, 1); e.preventDefault(); }
  if (key === 'arrowleft' || key === 'p') { nav(mode, -1); e.preventDefault(); }
});

// =========================================================================
// START
// =========================================================================
init();
</script>
</body>
</html>'''


# ---------------------------------------------------------------------------
# HTTP Server
# ---------------------------------------------------------------------------

class QAHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Quieter logging: only log errors
        if args and "404" in str(args[0]):
            super().log_message(fmt, *args)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def parse_qs(self):
        parsed = urllib.parse.urlparse(self.path)
        return urllib.parse.parse_qs(parsed.query), parsed.path

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        qs, path = self.parse_qs()

        if path == "/":
            self.send_html(HTML_PAGE)
            return

        if path == "/api/stats":
            self.handle_stats()
            return

        if path == "/api/smart-practice":
            self.handle_smart_practice(qs)
            return

        if path == "/api/curriculum/chapters":
            self.handle_curriculum_chapters(qs)
            return

        if path == "/api/curriculum/questions":
            self.handle_curriculum_questions(qs)
            return

        if path == "/api/question":
            self.handle_question(qs)
            return

        if path == "/api/export":
            self.handle_export()
            return

        self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        qs, path = self.parse_qs()
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}

        if path == "/api/flag":
            self.handle_flag(data)
            return

        if path == "/api/comment":
            self.handle_comment(data)
            return

        if path == "/api/comment/delete":
            self.handle_comment_delete(data)
            return

        self.send_json({"error": "Not found"}, 404)

    # --- API handlers ---

    def handle_stats(self):
        stats = {
            "kangaroo_g12": len(KANGAROO_G12),
            "kangaroo_g34": len(KANGAROO_G34),
            "kangaroo_g56": len(KANGAROO_G56),
            "total": len(ALL_QUESTIONS),
            "curricula": {},
        }
        for (curr, grade), chapters in CURRICULUM_DATA.items():
            if curr not in stats["curricula"]:
                stats["curricula"][curr] = {}
            total_q = sum(len(qs) for qs in chapters.values())
            stats["curricula"][curr][f"grade{grade}"] = {
                "chapters": len(chapters),
                "questions": total_q,
            }
        rd = load_review_data()
        flag_counts = {}
        for qid, flag in rd.get("flags", {}).items():
            if flag:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
        stats["flags"] = flag_counts
        stats["comments_count"] = sum(len(c) for c in rd.get("comments", {}).values())
        self.send_json(stats)

    def handle_smart_practice(self, qs):
        grade = int(qs.get("grade", [1])[0])
        start = int(qs.get("start", [0])[0])
        count = int(qs.get("count", [20])[0])
        topic = qs.get("topic", [""])[0]

        pool = get_kangaroo_pool(grade)
        if topic:
            pool = [q for q in pool if q.get("_topic_num") == topic]

        total = len(pool)
        subset = pool[start:start + count]

        rd = load_review_data()
        questions_out = []
        for q in subset:
            qo = question_to_api(q)
            qid = q.get("id", "")
            qo["flag"] = rd.get("flags", {}).get(qid, "")
            qo["comments"] = rd.get("comments", {}).get(qid, [])
            questions_out.append(qo)

        self.send_json({
            "grade": grade,
            "total": total,
            "start": start,
            "count": len(questions_out),
            "questions": questions_out,
        })

    def handle_curriculum_chapters(self, qs):
        curriculum = qs.get("curriculum", [""])[0]
        grade = int(qs.get("grade", [1])[0])

        chapters_data = CURRICULUM_DATA.get((curriculum, grade), {})
        chapters = []
        # Sort chapters naturally by leading number
        def ch_sort_key(name):
            m = re.search(r"(\d+)", name)
            return (int(m.group(1)) if m else 999, name)

        for ch_name in sorted(chapters_data.keys(), key=ch_sort_key):
            chapters.append({
                "name": ch_name,
                "count": len(chapters_data[ch_name]),
            })

        self.send_json({
            "curriculum": curriculum,
            "grade": grade,
            "chapters": chapters,
        })

    def handle_curriculum_questions(self, qs):
        curriculum = qs.get("curriculum", [""])[0]
        grade = int(qs.get("grade", [1])[0])
        chapter = qs.get("chapter", [""])[0]
        start = int(qs.get("start", [0])[0])
        count = int(qs.get("count", [20])[0])

        chapters_data = CURRICULUM_DATA.get((curriculum, grade), {})
        pool = chapters_data.get(chapter, [])
        total = len(pool)
        subset = pool[start:start + count]

        rd = load_review_data()
        questions_out = []
        for q in subset:
            qo = question_to_api(q)
            qid = q.get("id", "")
            qo["flag"] = rd.get("flags", {}).get(qid, "")
            qo["comments"] = rd.get("comments", {}).get(qid, [])
            questions_out.append(qo)

        self.send_json({
            "curriculum": curriculum,
            "grade": grade,
            "chapter": chapter,
            "total": total,
            "start": start,
            "count": len(questions_out),
            "questions": questions_out,
        })

    def handle_question(self, qs):
        qid = qs.get("id", [""])[0]
        q = ALL_QUESTIONS.get(qid)
        if not q:
            self.send_json({"error": "Question not found"}, 404)
            return
        self.send_json(question_to_api(q, include_review=True))

    def handle_flag(self, data):
        qid = data.get("question_id", "")
        flag = data.get("flag", "")
        if not qid:
            self.send_json({"error": "Missing question_id"}, 400)
            return
        rd = load_review_data()
        if flag:
            rd.setdefault("flags", {})[qid] = flag
        else:
            rd.setdefault("flags", {}).pop(qid, None)
        save_review_data(rd)
        self.send_json({"ok": True, "question_id": qid, "flag": flag})

    def handle_comment(self, data):
        qid = data.get("question_id", "")
        text = data.get("text", "").strip()
        reviewer = data.get("reviewer", "Unknown")
        if not qid or not text:
            self.send_json({"error": "Missing question_id or text"}, 400)
            return
        rd = load_review_data()
        rd.setdefault("comments", {}).setdefault(qid, []).append({
            "text": text,
            "reviewer": reviewer,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        save_review_data(rd)
        self.send_json({"ok": True, "question_id": qid})

    def handle_comment_delete(self, data):
        qid = data.get("question_id", "")
        index = data.get("index", -1)
        if not qid:
            self.send_json({"error": "Missing question_id"}, 400)
            return
        rd = load_review_data()
        comments = rd.get("comments", {}).get(qid, [])
        if 0 <= index < len(comments):
            comments.pop(index)
            if not comments:
                rd["comments"].pop(qid, None)
            save_review_data(rd)
            self.send_json({"ok": True})
        else:
            self.send_json({"error": "Invalid comment index"}, 400)

    def handle_export(self):
        rd = load_review_data()
        body = json.dumps(rd, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Disposition", "attachment; filename=qa_review_export.json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Loading questions from {CONTENT_DIR} ...")
    load_all_questions()
    print(f"\nStarting Kiwimath QA server on http://0.0.0.0:{PORT}")
    print(f"  Open in browser: http://localhost:{PORT}")
    server = http.server.HTTPServer(("0.0.0.0", PORT), QAHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
