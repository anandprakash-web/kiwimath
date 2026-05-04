#!/usr/bin/env python3
"""
IRT Parameter Calibrator — Recalculate IRT parameters from real student data.

This script reads response data from Firestore (logged by response_logger.py),
fits 3PL IRT parameters per question using Maximum Likelihood Estimation,
and writes calibrated params back to the content-v2 JSON files.

The 3PL IRT model:
  P(correct | theta) = c + (1 - c) / (1 + exp(-a * (theta - b)))

Where:
  a = discrimination (how sharply the item separates ability levels)
  b = difficulty (the theta value where P(correct) = (1+c)/2)
  c = pseudo-guessing (lower asymptote — P(correct) for very low theta)

Requirements:
  - Minimum 30 responses per question for calibration (configurable)
  - Minimum 50 unique students across the dataset
  - Responses must include user_theta at time of answer

Usage:
  # Preview what would change
  python irt_calibrator.py --dry-run

  # Calibrate all questions with 30+ responses
  python irt_calibrator.py --min-responses 30

  # Calibrate a single topic
  python irt_calibrator.py --topic topic-2-arithmetic

  # Export response data to CSV for external analysis
  python irt_calibrator.py --export responses.csv
"""

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize


# ---------------------------------------------------------------------------
# 3PL IRT Model
# ---------------------------------------------------------------------------

def irt_3pl_probability(theta: float, a: float, b: float, c: float) -> float:
    """Probability of correct response under 3PL model."""
    exponent = -a * (theta - b)
    # Clamp to avoid overflow
    exponent = max(-20, min(20, exponent))
    return c + (1 - c) / (1 + math.exp(exponent))


def neg_log_likelihood(params: np.ndarray, thetas: np.ndarray,
                       responses: np.ndarray) -> float:
    """Negative log-likelihood for 3PL model (to minimize)."""
    a, b, c = params

    # Parameter constraints
    if a < 0.3 or a > 3.0 or c < 0.0 or c > 0.5 or b < -4.0 or b > 4.0:
        return 1e10  # Penalty for out-of-bounds

    total = 0.0
    for theta, correct in zip(thetas, responses):
        p = irt_3pl_probability(theta, a, b, c)
        p = max(1e-10, min(1 - 1e-10, p))  # Avoid log(0)

        if correct:
            total -= math.log(p)
        else:
            total -= math.log(1 - p)

    return total


def fit_3pl(thetas: np.ndarray, responses: np.ndarray,
            initial_guess: Tuple[float, float, float] = (1.0, 0.0, 0.2)
            ) -> Tuple[float, float, float, float]:
    """Fit 3PL IRT parameters using MLE.

    Returns (a, b, c, fit_rmse).
    """
    result = minimize(
        neg_log_likelihood,
        x0=np.array(initial_guess),
        args=(thetas, responses),
        method="Nelder-Mead",
        options={"maxiter": 1000, "xatol": 0.01, "fatol": 0.01},
    )

    a, b, c = result.x
    a = max(0.3, min(3.0, a))
    b = max(-3.5, min(3.5, b))
    c = max(0.0, min(0.45, c))

    # Calculate RMSE (fit quality)
    predicted = [irt_3pl_probability(t, a, b, c) for t in thetas]
    rmse = math.sqrt(sum((p - r) ** 2 for p, r in zip(predicted, responses)) / len(responses))

    return round(a, 3), round(b, 3), round(c, 3), round(rmse, 4)


# ---------------------------------------------------------------------------
# Item Fit Statistics
# ---------------------------------------------------------------------------

def calculate_item_fit(thetas: np.ndarray, responses: np.ndarray,
                       a: float, b: float, c: float) -> Dict:
    """Calculate item fit statistics."""
    n = len(responses)
    if n < 10:
        return {"n": n, "fit": "insufficient_data"}

    # Point-biserial correlation
    correct_thetas = thetas[responses == 1]
    wrong_thetas = thetas[responses == 0]

    if len(correct_thetas) == 0 or len(wrong_thetas) == 0:
        point_biserial = 0.0
    else:
        mean_correct = np.mean(correct_thetas)
        mean_wrong = np.mean(wrong_thetas)
        std_total = np.std(thetas) if np.std(thetas) > 0 else 1
        p_correct = len(correct_thetas) / n
        point_biserial = (mean_correct - mean_wrong) / std_total * math.sqrt(p_correct * (1 - p_correct))

    # Observed vs expected accuracy
    expected = np.array([irt_3pl_probability(t, a, b, c) for t in thetas])
    observed_accuracy = np.mean(responses)
    expected_accuracy = np.mean(expected)

    # Chi-square-like fit (simplified)
    residuals = responses - expected
    chi_sq = float(np.sum(residuals ** 2 / (expected * (1 - expected) + 1e-10)))

    return {
        "n": n,
        "observed_accuracy": round(float(observed_accuracy), 3),
        "expected_accuracy": round(float(expected_accuracy), 3),
        "point_biserial": round(float(point_biserial), 3),
        "chi_sq": round(float(chi_sq), 2),
        "fit": "good" if abs(point_biserial) > 0.15 and chi_sq < 2 * n else "review",
    }


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_responses_from_firestore(min_responses: int = 30,
                                  topic_filter: str = "") -> Dict[str, List[Dict]]:
    """Load response data from Firestore, grouped by question_id."""
    try:
        import firebase_admin
        from firebase_admin import firestore as fs

        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        db = fs.client()

        query = db.collection("response_logs")
        if topic_filter:
            # Filter by question_id prefix (e.g., "T2-" for arithmetic)
            topic_prefix_map = {
                "topic-1-counting": "T1-",
                "topic-2-arithmetic": "T2-",
                "topic-3-patterns": "T3-",
                "topic-4-logic": "T4-",
                "topic-5-spatial": "T5-",
                "topic-6-shapes": "T6-",
                "topic-7-word-problems": "T7-",
                "topic-8-puzzles": "T8-",
            }
            prefix = topic_prefix_map.get(topic_filter, "")
            if prefix:
                query = query.where("question_id", ">=", prefix)
                query = query.where("question_id", "<", prefix[:-1] + chr(ord(prefix[-1]) + 1))

        docs = query.get()
        grouped = defaultdict(list)
        for doc in docs:
            data = doc.to_dict()
            grouped[data["question_id"]].append(data)

        # Filter to items with enough responses
        return {qid: responses for qid, responses in grouped.items()
                if len(responses) >= min_responses}

    except Exception as e:
        print(f"Firestore not available: {e}")
        print("Use --export to work with CSV data, or ensure Firestore credentials are set.")
        return {}


def load_responses_from_csv(csv_path: str) -> Dict[str, List[Dict]]:
    """Load response data from a CSV export."""
    import csv

    grouped = defaultdict(list)
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            grouped[row["question_id"]].append({
                "user_id": row["user_id"],
                "question_id": row["question_id"],
                "correct": row["correct"].lower() == "true",
                "user_theta": float(row["user_theta"]),
                "response_time_ms": int(row.get("response_time_ms", 0)),
            })

    return grouped


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

def calibrate_item(responses: List[Dict]) -> Optional[Dict]:
    """Calibrate a single item from its response data."""
    thetas = np.array([r["user_theta"] for r in responses])
    correct = np.array([1.0 if r["correct"] else 0.0 for r in responses])

    # Need sufficient theta variance
    if np.std(thetas) < 0.1:
        return None

    # Initial guess from observed data
    accuracy = np.mean(correct)
    b_guess = -np.mean(thetas[correct == 1]) if sum(correct) > 0 else 0.0
    c_guess = max(0.05, min(0.35, accuracy - 0.5)) if accuracy > 0.5 else 0.1

    a, b, c, rmse = fit_3pl(thetas, correct, initial_guess=(1.0, b_guess, c_guess))

    fit_stats = calculate_item_fit(thetas, correct, a, b, c)

    return {
        "a": a, "b": b, "c": c,
        "rmse": rmse,
        "n_responses": len(responses),
        "observed_accuracy": fit_stats["observed_accuracy"],
        "point_biserial": fit_stats["point_biserial"],
        "fit": fit_stats["fit"],
    }


def update_content_files(calibrations: Dict[str, Dict], content_dir: Path,
                         dry_run: bool = False) -> int:
    """Write calibrated IRT params back to content-v2 JSON files."""
    updated = 0

    for topic_dir in sorted(content_dir.iterdir()):
        if not topic_dir.is_dir() or not topic_dir.name.startswith("topic-"):
            continue

        for json_file in sorted(topic_dir.glob("*.json")):
            data = json.loads(json_file.read_text())
            questions = data.get("questions", data) if isinstance(data, dict) else data
            file_updated = False

            for q in questions:
                qid = q.get("id", "")
                if qid in calibrations:
                    cal = calibrations[qid]
                    old = f"a={q.get('irt_a')}, b={q.get('irt_b')}, c={q.get('irt_c')}"
                    new = f"a={cal['a']}, b={cal['b']}, c={cal['c']}"

                    if dry_run:
                        print(f"  {qid}: {old} → {new} (n={cal['n_responses']}, fit={cal['fit']})")
                    else:
                        q["irt_params"] = {"a": cal["a"], "b": cal["b"], "c": cal["c"]}
                        q["irt_a"] = cal["a"]
                        q["irt_b"] = cal["b"]
                        q["irt_c"] = cal["c"]
                        q["irt_calibrated"] = True
                        q["irt_n_responses"] = cal["n_responses"]
                        q["irt_fit"] = cal["fit"]

                    file_updated = True
                    updated += 1

            if file_updated and not dry_run:
                if isinstance(data, dict):
                    data["questions"] = questions
                json_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    return updated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="IRT Parameter Calibrator")
    parser.add_argument("--content-dir", type=Path,
                        default=Path(__file__).resolve().parent.parent.parent / "content-v2")
    parser.add_argument("--min-responses", type=int, default=30,
                        help="Minimum responses needed to calibrate an item")
    parser.add_argument("--topic", type=str, help="Calibrate single topic only")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--csv", type=str, help="Load responses from CSV instead of Firestore")
    parser.add_argument("--export", type=str, help="Export Firestore responses to CSV")
    args = parser.parse_args()

    # Load response data
    if args.csv:
        grouped = load_responses_from_csv(args.csv)
    else:
        grouped = load_responses_from_firestore(args.min_responses, args.topic or "")

    if not grouped:
        print("No response data found. Responses are collected automatically as students")
        print("use the app. Once you have 30+ responses per question, run this script again.")
        print(f"\nTo check response count: python -c \"from app.services.response_logger import response_logger; print(response_logger.get_response_count())\"")
        return

    print(f"Found response data for {len(grouped)} questions")

    # Export if requested
    if args.export:
        import csv
        with open(args.export, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "question_id", "user_id", "correct", "user_theta",
                "response_time_ms", "skill_id", "timestamp"
            ])
            writer.writeheader()
            for qid, responses in grouped.items():
                for r in responses:
                    writer.writerow({
                        "question_id": r.get("question_id"),
                        "user_id": r.get("user_id"),
                        "correct": r.get("correct"),
                        "user_theta": r.get("user_theta"),
                        "response_time_ms": r.get("response_time_ms"),
                        "skill_id": r.get("skill_id"),
                        "timestamp": r.get("timestamp"),
                    })
        print(f"Exported to {args.export}")
        return

    # Calibrate
    calibrations = {}
    good_fit = 0
    review_fit = 0

    for qid, responses in sorted(grouped.items()):
        result = calibrate_item(responses)
        if result:
            calibrations[qid] = result
            if result["fit"] == "good":
                good_fit += 1
            else:
                review_fit += 1

    print(f"\nCalibrated: {len(calibrations)} questions")
    print(f"  Good fit: {good_fit}")
    print(f"  Needs review: {review_fit}")
    print(f"  Skipped (insufficient variance): {len(grouped) - len(calibrations)}")

    if calibrations:
        # Show summary statistics
        a_vals = [c["a"] for c in calibrations.values()]
        b_vals = [c["b"] for c in calibrations.values()]
        c_vals = [c["c"] for c in calibrations.values()]
        print(f"\nParameter distributions:")
        print(f"  a: mean={sum(a_vals)/len(a_vals):.2f}, range=[{min(a_vals):.2f}, {max(a_vals):.2f}]")
        print(f"  b: mean={sum(b_vals)/len(b_vals):.2f}, range=[{min(b_vals):.2f}, {max(b_vals):.2f}]")
        print(f"  c: mean={sum(c_vals)/len(c_vals):.2f}, range=[{min(c_vals):.2f}, {max(c_vals):.2f}]")

        # Update content files
        updated = update_content_files(calibrations, args.content_dir, dry_run=args.dry_run)
        print(f"\n{'Would update' if args.dry_run else 'Updated'}: {updated} questions in content files")


if __name__ == "__main__":
    main()
