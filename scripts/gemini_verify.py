#!/usr/bin/env python3
"""
Gemini-powered question verification and improvement.

Usage:
    python scripts/gemini_verify.py --grade 1 --mode verify --max 50
    python scripts/gemini_verify.py --grade all --mode verify
    python scripts/gemini_verify.py --grade 1 --mode improve
    python scripts/gemini_verify.py --grade all --mode both

Modes:
    verify  - solve each question, compare with stored answer
    improve - generate better hints/explanations for weak questions
    both    - do both passes
"""
import argparse
import json
import os
import sys
import time
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    print("Installing google-generativeai...")
    os.system(f"{sys.executable} -m pip install google-generativeai --break-system-packages -q")
    import google.generativeai as genai

# ── Configuration ──────────────────────────────────────────────
PROD_DIR = Path("content-production")
REPORT_DIR = Path("gemini-reports")
REPORT_DIR.mkdir(exist_ok=True)

BATCH_SIZE = 5          # Questions per Gemini call (smaller = less tokens = fewer rate limits)
MIN_SLEEP = 5.0         # Minimum seconds between requests
MAX_RETRIES = 5         # Max retries on rate limit
INITIAL_BACKOFF = 30    # Initial backoff seconds on 429


def setup_gemini(api_key: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    return model


def call_gemini_with_retry(model, prompt: str) -> str:
    """Call Gemini API with exponential backoff on rate limits."""
    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                wait = INITIAL_BACKOFF * (2 ** attempt)
                # Try to extract retry_delay from error
                delay_match = re.search(r'seconds:\s*(\d+)', err_str)
                if delay_match:
                    wait = max(wait, int(delay_match.group(1)) + 5)
                print(f"    Rate limited (attempt {attempt+1}/{MAX_RETRIES}). Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    Gemini error: {e}")
                return ""
    print(f"    Failed after {MAX_RETRIES} retries. Skipping batch.")
    return ""


# ── Verification prompts ──────────────────────────────────────

VERIFY_PROMPT = """You are a math teacher verifying answers for children's math questions (grades 1-6).

For each question below, solve it independently and tell me if the stored answer is correct.

Questions:
{questions_block}

For each question, respond in this EXACT JSON format (one object per question):
```json
[
  {{
    "id": "question_id",
    "my_answer": "your calculated answer (number or letter index)",
    "stored_correct": true/false,
    "confidence": "high/medium/low",
    "issue": "description of any problem found, or null"
  }}
]
```

Be precise with math. For MCQ, the correct_answer is the 0-based index of the right choice.
For integer questions, correct_value is the numeric answer.
"""

IMPROVE_PROMPT = """You are a friendly math tutor for children (grades 1-6).
Improve the hints and solution steps for these questions.
Make hints age-appropriate, encouraging, and Socratic (guide, don't just tell).

Questions needing improvement:
{questions_block}

For each question, provide improved content in this JSON format:
```json
[
  {{
    "id": "question_id",
    "improved_hint": {{
      "level_0": "Gentle nudge to re-read the question",
      "level_1": "Point to the key information",
      "level_2": "Socratic question to guide thinking",
      "level_3": "Break it into smaller steps",
      "level_4": "Almost give it away",
      "level_5": "Teach the concept and let them retry"
    }},
    "improved_solution_steps": ["step1", "step2", "step3"],
    "improved_diagnostics": {{
      "0": "Friendly explanation if they pick choice 0",
      "1": "Friendly explanation if they pick choice 1",
      "2": "...",
      "3": "..."
    }}
  }}
]
```
Keep language simple, warm, and encouraging. Use phrases like "Great try!", "Almost!", "Think about..."
"""


def format_question_for_gemini(q: dict) -> str:
    qid = q.get("id", q.get("question_id", "unknown"))
    stem = q.get("stem", "")
    choices = q.get("choices", [])
    correct_answer = q.get("correct_answer", None)
    correct_value = q.get("correct_value", None)
    mode = q.get("interaction_mode", "mcq")
    diff = q.get("difficulty_score", 0)

    block = f"ID: {qid}\nType: {mode}\nDifficulty: {diff}\nQuestion: {stem}\n"

    if choices:
        for i, c in enumerate(choices):
            block += f"  [{i}] {c}\n"
        block += f"Stored correct_answer (0-based index): {correct_answer}\n"

    if correct_value is not None:
        block += f"Stored correct_value: {correct_value}\n"

    return block


def parse_gemini_json(text: str) -> list:
    if not text:
        return []
    json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    bracket_match = re.search(r'\[[\s\S]*\]', text)
    if bracket_match:
        try:
            return json.loads(bracket_match.group())
        except json.JSONDecodeError:
            pass
    return []


def verify_batch(model, questions: list, grade: int) -> list:
    block = "\n---\n".join(format_question_for_gemini(q) for q in questions)
    prompt = VERIFY_PROMPT.format(questions_block=block)
    text = call_gemini_with_retry(model, prompt)
    return parse_gemini_json(text)


def improve_batch(model, questions: list, grade: int) -> list:
    block = "\n---\n".join(format_question_for_gemini(q) for q in questions)
    prompt = IMPROVE_PROMPT.format(questions_block=block)
    text = call_gemini_with_retry(model, prompt)
    return parse_gemini_json(text)


def run_verify(model, grade: int, max_questions: int = 0):
    grade_dir = PROD_DIR / f"grade{grade}"
    if not grade_dir.exists():
        print(f"  Grade {grade} not found")
        return {}

    index = json.loads((grade_dir / "topics.json").read_text())

    # Check for existing partial report to resume
    report_path = REPORT_DIR / f"verify_grade{grade}.json"
    if report_path.exists():
        report = json.loads(report_path.read_text())
        done_ids = set()
        for m in report.get("mismatches", []):
            done_ids.add(m.get("question_id"))
        print(f"  Resuming: {report['total_verified']} already done")
    else:
        report = {
            "grade": grade,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_verified": 0,
            "correct": 0,
            "mismatches": [],
            "errors": [],
        }
        done_ids = set()

    total_qs = report["total_verified"]

    for topic_info in index["topics"]:
        topic_file = grade_dir / topic_info["file"]
        data = json.loads(topic_file.read_text())
        questions = data.get("questions", [])
        topic_id = topic_info["topic_id"]

        # Skip already-verified questions
        remaining = [q for q in questions if q.get("id", q.get("question_id", "")) not in done_ids]
        if not remaining:
            continue

        print(f"  [{topic_id}] {len(remaining)} questions to verify...")

        for i in range(0, len(remaining), BATCH_SIZE):
            if max_questions and total_qs >= max_questions:
                break

            batch = remaining[i:i + BATCH_SIZE]
            results = verify_batch(model, batch, grade)

            for r in results:
                report["total_verified"] += 1
                total_qs += 1

                if r.get("stored_correct", True):
                    report["correct"] += 1
                else:
                    report["mismatches"].append({
                        "question_id": r.get("id", "?"),
                        "topic": topic_id,
                        "gemini_answer": r.get("my_answer"),
                        "confidence": r.get("confidence", "?"),
                        "issue": r.get("issue"),
                    })

            # Save progress after every batch (resumable)
            report["timestamp"] = datetime.utcnow().isoformat() + "Z"
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)

            if results:
                print(f"    ...{total_qs} verified ({report['correct']} correct, {len(report['mismatches'])} mismatches)")

            # Rate limiting
            time.sleep(MIN_SLEEP)

        if max_questions and total_qs >= max_questions:
            break

    pct = report["correct"] * 100 / max(1, report["total_verified"])
    print(f"\n  Grade {grade} verification: {report['correct']}/{report['total_verified']} correct ({pct:.1f}%)")
    print(f"  Mismatches: {len(report['mismatches'])}")
    print(f"  Report saved: {report_path}")

    return report


def run_improve(model, grade: int, max_questions: int = 0):
    grade_dir = PROD_DIR / f"grade{grade}"
    if not grade_dir.exists():
        return

    index = json.loads((grade_dir / "topics.json").read_text())
    improved_count = 0

    for topic_info in index["topics"]:
        topic_file = grade_dir / topic_info["file"]
        data = json.loads(topic_file.read_text())
        questions = data.get("questions", [])
        topic_id = topic_info["topic_id"]

        weak = [q for q in questions if not q.get("hint") and not q.get("hint_ladder")]
        if not weak:
            continue

        print(f"  [{topic_id}] {len(weak)} questions need hints...")

        for i in range(0, len(weak), BATCH_SIZE):
            if max_questions and improved_count >= max_questions:
                break

            batch = weak[i:i + BATCH_SIZE]
            results = improve_batch(model, batch, grade)

            improvements_map = {r["id"]: r for r in results if "id" in r}

            for q in questions:
                qid = q.get("id", q.get("question_id", ""))
                if qid in improvements_map:
                    imp = improvements_map[qid]
                    if "improved_hint" in imp:
                        q["hint"] = imp["improved_hint"]
                    if "improved_solution_steps" in imp:
                        q["solution_steps"] = imp["improved_solution_steps"]
                    if "improved_diagnostics" in imp:
                        q["diagnostics"] = imp["improved_diagnostics"]
                    improved_count += 1

            time.sleep(MIN_SLEEP)

        data["questions"] = questions
        with open(topic_file, "w") as f:
            json.dump(data, f, indent=2)

    print(f"\n  Grade {grade}: improved {improved_count} questions")
    return improved_count


def main():
    parser = argparse.ArgumentParser(description="Gemini verification & improvement")
    parser.add_argument("--grade", default="1", help="Grade (1-6 or 'all')")
    parser.add_argument("--mode", default="verify", choices=["verify", "improve", "both"])
    parser.add_argument("--max", type=int, default=0, help="Max questions to process (0 = all)")
    parser.add_argument("--key", default="", help="Gemini API key (or set GEMINI_API_KEY env)")
    args = parser.parse_args()

    # Auto-load .env file from project root
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    api_key = args.key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key or api_key == "PASTE_YOUR_KEY_HERE":
        print("ERROR: Set your Gemini API key in .env file or pass --key")
        print(f"  .env location: {env_path}")
        sys.exit(1)

    model = setup_gemini(api_key)

    # Quick connectivity test
    print("Testing Gemini API connection...")
    try:
        test = model.generate_content("What is 2+2? Reply with just the number.")
        print(f"  API OK: {test.text.strip()}")
    except Exception as e:
        print(f"  API ERROR: {e}")
        print("\nCheck your API key and ensure the Gemini API is enabled in Google AI Studio.")
        sys.exit(1)

    grades = list(range(1, 7)) if args.grade == "all" else [int(args.grade)]

    for g in grades:
        print(f"\n{'=' * 50}")
        print(f"  Grade {g}")
        print(f"{'=' * 50}")

        if args.mode in ("verify", "both"):
            run_verify(model, g, max_questions=args.max)

        if args.mode in ("improve", "both"):
            run_improve(model, g, max_questions=args.max)

    print("\nDone! Reports saved to gemini-reports/")


if __name__ == "__main__":
    main()
