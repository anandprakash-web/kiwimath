"""
Proof Grader — uses Gemini API to grade subjective math proofs (L4-L5).

Rubric-based grading:
  - Correctness (0–40): Is the proof logically valid?
  - Completeness (0–30): Are all cases covered?
  - Clarity (0–20): Is the proof clearly written?
  - Elegance (0–10): Creative or efficient approach?

Total: 0–100. Pass threshold: 60.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("kiwimath.proof_grader")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")


async def grade_proof(
    question_stem: str,
    student_proof: str,
    rubric: Optional[str] = None,
    model_solution: Optional[str] = None,
) -> dict:
    """
    Grade a student's proof using Gemini.

    Returns:
        {
            "score": 0–100,
            "passed": bool,
            "breakdown": {"correctness": int, "completeness": int, "clarity": int, "elegance": int},
            "feedback": str,
            "suggestions": [str],
        }
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — returning mock grade")
        return _mock_grade()

    prompt = _build_prompt(question_stem, student_proof, rubric, model_solution)

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        result = json.loads(response.text)
        # Validate and clamp scores
        breakdown = result.get("breakdown", {})
        correctness = max(0, min(40, breakdown.get("correctness", 0)))
        completeness = max(0, min(30, breakdown.get("completeness", 0)))
        clarity = max(0, min(20, breakdown.get("clarity", 0)))
        elegance = max(0, min(10, breakdown.get("elegance", 0)))
        total = correctness + completeness + clarity + elegance

        return {
            "score": total,
            "passed": total >= 60,
            "breakdown": {
                "correctness": correctness,
                "completeness": completeness,
                "clarity": clarity,
                "elegance": elegance,
            },
            "feedback": result.get("feedback", ""),
            "suggestions": result.get("suggestions", []),
        }

    except Exception as e:
        logger.error(f"Gemini grading error: {e}")
        return {
            "score": 0,
            "passed": False,
            "breakdown": {"correctness": 0, "completeness": 0, "clarity": 0, "elegance": 0},
            "feedback": f"Grading temporarily unavailable: {str(e)}",
            "suggestions": ["Please try again in a moment."],
            "error": True,
        }


def _build_prompt(
    question_stem: str,
    student_proof: str,
    rubric: Optional[str],
    model_solution: Optional[str],
) -> str:
    parts = [
        "You are a math olympiad proof grader. Grade the student's proof on these criteria:",
        "",
        "RUBRIC:",
        "- Correctness (0-40): Is the proof logically valid? Are all steps justified?",
        "- Completeness (0-30): Are all cases handled? No gaps in logic?",
        "- Clarity (0-20): Is the proof well-written and easy to follow?",
        "- Elegance (0-10): Is the approach creative or efficient?",
        "",
        f"QUESTION:\n{question_stem}",
        "",
    ]

    if rubric:
        parts.append(f"ADDITIONAL RUBRIC NOTES:\n{rubric}\n")

    if model_solution:
        parts.append(f"MODEL SOLUTION (for reference only):\n{model_solution}\n")

    parts.extend([
        f"STUDENT'S PROOF:\n{student_proof}",
        "",
        "Respond in JSON with exactly these fields:",
        '{"breakdown": {"correctness": N, "completeness": N, "clarity": N, "elegance": N}, '
        '"feedback": "2-3 sentence summary", '
        '"suggestions": ["improvement 1", "improvement 2"]}',
    ])

    return "\n".join(parts)


def _mock_grade() -> dict:
    """Return a mock grade when Gemini is unavailable."""
    return {
        "score": 50,
        "passed": False,
        "breakdown": {"correctness": 20, "completeness": 15, "clarity": 10, "elegance": 5},
        "feedback": "Proof grading requires Gemini API. Please set GEMINI_API_KEY.",
        "suggestions": ["Configure GEMINI_API_KEY environment variable."],
        "mock": True,
    }
