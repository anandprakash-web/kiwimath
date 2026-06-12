#!/usr/bin/env python3
"""
Kiwimath Test Bot Runner
========================

Simulates real users exercising the full API surface:
  - Practice sessions (adaptive + topic-locked)
  - Worksheets & wavebook
  - Streak tracking
  - Clan creation, joining, challenges
  - Profile updates, bookmarks
  - Parent dashboard reads
  - Daily puzzles, rewards

Usage:
    python -m tests.bots.bot_runner --base-url https://kiwimath-api-deufqab6gq-el.a.run.app
    python -m tests.bots.bot_runner --base-url http://localhost:8000 --bots 5 --rounds 20
    python -m tests.bots.bot_runner --base-url http://localhost:8000 --report-file report.json

Each bot runs as an async task, making realistic API calls with random
delays to simulate real usage patterns.
"""

import argparse
import asyncio
import json
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

# ── Bot personas ─────────────────────────────────────────────────────────────
PERSONAS = [
    {"name": "Aarav", "grade": 1},
    {"name": "Diya", "grade": 2},
    {"name": "Kabir", "grade": 3},
    {"name": "Ananya", "grade": 4},
    {"name": "Vihaan", "grade": 5},
    {"name": "Meera", "grade": 1},
    {"name": "Arjun", "grade": 3},
    {"name": "Isha", "grade": 5},
    {"name": "Rohan", "grade": 2},
    {"name": "Saanvi", "grade": 4},
]

TOPICS = [
    "counting_observation",
    "arithmetic_missing_numbers",
    "patterns_sequences",
    "logic_ordering",
    "spatial_reasoning_3d",
    "shapes_folding_symmetry",
    "word_problems_stories",
    "number_puzzles_games",
]


@dataclass
class BotReport:
    bot_id: str
    persona: dict
    started_at: str = ""
    finished_at: str = ""
    rounds_completed: int = 0
    questions_answered: int = 0
    questions_correct: int = 0
    errors: list = field(default_factory=list)
    api_latencies: list = field(default_factory=list)
    features_tested: dict = field(default_factory=dict)

    def summary(self) -> dict:
        avg_latency = (
            sum(self.api_latencies) / len(self.api_latencies)
            if self.api_latencies
            else 0
        )
        p95 = (
            sorted(self.api_latencies)[int(len(self.api_latencies) * 0.95)]
            if len(self.api_latencies) > 10
            else avg_latency
        )
        return {
            "bot_id": self.bot_id,
            "persona": self.persona,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "rounds": self.rounds_completed,
            "questions": self.questions_answered,
            "accuracy": (
                f"{self.questions_correct / self.questions_answered * 100:.0f}%"
                if self.questions_answered > 0
                else "N/A"
            ),
            "avg_latency_ms": f"{avg_latency * 1000:.0f}",
            "p95_latency_ms": f"{p95 * 1000:.0f}",
            "errors": len(self.errors),
            "error_details": self.errors[:10],  # first 10
            "features_tested": self.features_tested,
        }


class KiwimathBot:
    """Simulates a single student user."""

    def __init__(self, base_url: str, persona: dict, rounds: int = 10):
        self.base_url = base_url.rstrip("/")
        self.persona = persona
        self.rounds = rounds
        self.user_id = f"bot_{uuid.uuid4().hex[:12]}"
        self.report = BotReport(
            bot_id=self.user_id,
            persona=persona,
        )
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    # ── API helpers ──────────────────────────────────────────────────────────

    async def _request(
        self, method: str, path: str, **kwargs
    ) -> tuple[int, Any]:
        url = f"{self.base_url}{path}"
        t0 = time.monotonic()
        try:
            resp = await self.client.request(method, url, **kwargs)
            elapsed = time.monotonic() - t0
            self.report.api_latencies.append(elapsed)

            if resp.status_code >= 400:
                err = f"{method} {path} → {resp.status_code}: {resp.text[:200]}"
                self.report.errors.append(err)
                return resp.status_code, None

            try:
                data = resp.json()
            except Exception:
                data = resp.text
            return resp.status_code, data

        except Exception as e:
            elapsed = time.monotonic() - t0
            self.report.api_latencies.append(elapsed)
            err = f"{method} {path} → EXCEPTION: {e}"
            self.report.errors.append(err)
            return 0, None

    async def get(self, path: str, **kwargs):
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs):
        return await self._request("POST", path, **kwargs)

    # ── Feature flows ────────────────────────────────────────────────────────

    async def flow_onboard(self):
        """Create/update profile via POST /user/profile."""
        status, data = await self.post(
            "/user/profile",
            json={
                "user_id": self.user_id,
                "display_name": self.persona["name"],
                "child_name": self.persona["name"],
                "daily_goal": 5,
                "curriculum": "olympiad",
            },
        )
        self._track("onboarding", status == 200)
        return status == 200

    async def flow_get_profile(self):
        """Read back profile via GET /user/profile."""
        status, data = await self.get(
            "/user/profile", params={"user_id": self.user_id}
        )
        ok = status == 200 and data is not None
        self._track("profile_read", ok)
        return ok

    def _detect_question_type(self, q: dict) -> str:
        """Detect question type: mcq, integer, or fill_blank."""
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
        if choices:
            return "mcq"
        return "integer"

    async def _answer_question(self, q: dict, qid: str, topic: str, grade: int, difficulty: int):
        """Type-aware answer submission."""
        qtype = self._detect_question_type(q)
        choices = q.get("choices") or []
        correct_answer = q.get("correct_answer", 0)
        correct_value = q.get("correct_value")

        # Simulate thinking time
        await asyncio.sleep(random.uniform(0.5, 2.0))

        if qtype == "mcq" and len(choices) >= 2:
            # MCQ: pick from choices
            n_choices = len(choices)
            if random.random() < 0.7:
                picked = correct_answer if isinstance(correct_answer, int) and 0 <= correct_answer < n_choices else 0
            else:
                picked = random.randint(0, n_choices - 1)

            check_status, result = await self.post(
                "/v2/answer/check",
                json={
                    "question_id": qid,
                    "selected_index": picked,
                    "user_id": self.user_id,
                    "topic": topic,
                    "difficulty": difficulty,
                    "grade": grade,
                },
            )

        elif qtype == "integer":
            # Integer: type in the answer
            if random.random() < 0.7 and correct_value is not None:
                typed = str(correct_value)
            else:
                # Wrong answer: offset the correct value
                try:
                    typed = str(int(correct_value or 0) + random.randint(1, 10))
                except (ValueError, TypeError):
                    typed = "42"

            check_status, result = await self.post(
                "/v2/answer/check",
                json={
                    "question_id": qid,
                    "typed_answer": typed,
                    "user_id": self.user_id,
                    "topic": topic,
                    "difficulty": difficulty,
                    "grade": grade,
                },
            )

        elif qtype == "fill_blank":
            # Fill-blank: type the answer
            answer = str(correct_value or correct_answer or "")
            if random.random() > 0.7:
                answer = "wrong_answer"

            check_status, result = await self.post(
                "/v2/answer/check",
                json={
                    "question_id": qid,
                    "typed_answer": answer,
                    "user_id": self.user_id,
                    "topic": topic,
                    "difficulty": difficulty,
                    "grade": grade,
                },
            )
        else:
            return

        self.report.questions_answered += 1
        if check_status == 200 and result:
            if result.get("correct"):
                self.report.questions_correct += 1

        # Track by type
        type_key = f"answer_{qtype}"
        self._track(type_key, check_status == 200)

    async def flow_practice_session(self):
        """Answer 5-10 questions in a topic-locked session — type-aware."""
        topic = random.choice(TOPICS)
        grade = self.persona["grade"]
        n_questions = random.randint(5, 10)
        exclude = []

        for _ in range(n_questions):
            params = {
                "topic": topic,
                "difficulty": random.randint(1, 3),
                "window": 10,
                "user_id": self.user_id,
                "grade": grade,
            }
            if exclude:
                params["exclude"] = ",".join(exclude)

            status, q = await self.get("/v2/questions/next", params=params)
            if status != 200 or q is None:
                self._track("question_fetch", False)
                break

            qid = q.get("question_id", "")
            exclude.append(qid)

            # Type-aware answering
            await self._answer_question(q, qid, topic, grade, params["difficulty"])

        self._track("practice_session", True)

    async def flow_smart_session(self):
        """Try starting a smart (5-phase) unified session."""
        grade = self.persona["grade"]
        status, data = await self.get(
            "/v2/session/unified",
            params={"user_id": self.user_id, "grade": grade},
        )
        ok = status == 200 and data is not None
        self._track("smart_session", ok)

        if ok and isinstance(data.get("questions"), list):
            # Answer first 3 questions from the plan — type-aware
            for q_item in data["questions"][:3]:
                qid = q_item.get("question_id", "")
                if not qid:
                    continue
                q_status, q_data = await self.get(f"/v2/questions/{qid}")
                if q_status != 200 or q_data is None:
                    continue

                await self._answer_question(
                    q_data, qid, q_item.get("topic", ""), grade, 2
                )
                await asyncio.sleep(random.uniform(0.3, 1.0))

    async def flow_worksheets(self):
        """Browse worksheets for the bot's grade."""
        grade = self.persona["grade"]
        day = random.randint(1, 10)
        status, data = await self.get(
            "/olympiad/worksheets", params={"grade": grade, "day": day}
        )
        ok = status == 200 and data is not None
        self._track("worksheets_list", ok)

    async def flow_wavebook(self):
        """Browse wavebook topics."""
        grade = self.persona["grade"]
        # Wavebook is for grades 3-6; skip for younger kids
        if grade < 3:
            self._track("wavebook_list", True)
            return
        status, data = await self.get(
            "/wavebook/topics", params={"grade": grade}
        )
        ok = status == 200
        self._track("wavebook_list", ok)

    async def flow_streak(self):
        """Check user profile for streak data."""
        status, data = await self.get(
            "/user/profile", params={"user_id": self.user_id}
        )
        ok = status == 200 and data is not None
        if ok:
            ok = "streak_current" in (data or {})
        self._track("streak_read", ok)

    async def flow_bookmarks(self):
        """Save and retrieve a bookmark."""
        # First get a question to bookmark
        params = {
            "topic": random.choice(TOPICS),
            "difficulty": 1,
            "window": 5,
            "grade": self.persona["grade"],
        }
        status, q = await self.get("/v2/questions/next", params=params)
        if status != 200 or q is None:
            self._track("bookmark_save", False)
            return

        qid = q.get("question_id", "")
        # Toggle bookmark on
        save_status, _ = await self.post(
            "/v2/bookmarks/toggle",
            json={
                "user_id": self.user_id,
                "question_id": qid,
                "topic": params["topic"],
                "grade": self.persona["grade"],
            },
        )
        self._track("bookmark_save", save_status == 200)

        # List bookmarks
        list_status, _ = await self.get(
            "/v2/bookmarks/list",
            params={
                "user_id": self.user_id,
                "grade": self.persona["grade"],
            },
        )
        self._track("bookmark_list", list_status == 200)

    async def flow_parent_dashboard(self):
        """Read parent dashboard analytics."""
        status, data = await self.get(
            "/v2/parent/dashboard",
            params={
                "user_id": self.user_id,
                "grade": self.persona["grade"],
            },
        )
        ok = status == 200
        self._track("parent_dashboard", ok)

    async def flow_growth(self):
        """Check growth journey."""
        status, data = await self.get(
            "/growth/journey",
            params={
                "user_id": self.user_id,
                "grade": self.persona["grade"],
            },
        )
        # 404 is OK if no data yet
        ok = status in (200, 404)
        self._track("growth_read", ok)

    async def flow_clan(self):
        """Create a clan, check status."""
        # Name must be letters, numbers, spaces only (no underscores)
        tag = self.user_id.replace("bot_", "")[:6]
        clan_name = f"Team {self.persona['name']} {tag}"
        status, data = await self.post(
            "/v4/clans",
            json={
                "name": clan_name,
                "grade": self.persona["grade"],
                "leader_uid": self.user_id,
                "parent_uid": self.user_id,
                "crest_shape": "shield",
                "crest_color": "#FF6D00",
            },
        )
        ok = status == 200 and data is not None
        self._track("clan_create", ok)

        if ok:
            clan_id = data.get("clan_id", "")
            # Read clan
            read_status, _ = await self.get(f"/v4/clans/{clan_id}")
            self._track("clan_read", read_status == 200)

    async def flow_daily_puzzle(self):
        """Fetch daily puzzle."""
        status, _ = await self.get(
            "/v4/daily-puzzle",
            params={"grade": self.persona["grade"]},
        )
        ok = status in (200, 404)  # 404 if none configured for today
        self._track("daily_puzzle", ok)

    async def flow_rewards(self):
        """Check reward balance (404 is expected for new users)."""
        status, _ = await self.get(f"/v4/rewards/{self.user_id}")
        if status == 404:
            # Expected for fresh bots — remove the error that _request logged
            self.report.errors = [
                e for e in self.report.errors
                if f"/v4/rewards/{self.user_id}" not in e
            ]
        ok = status in (200, 404)
        self._track("rewards_balance", ok)

    # ── Main run loop ────────────────────────────────────────────────────────

    async def run(self):
        """Execute the full bot simulation."""
        self.report.started_at = datetime.utcnow().isoformat()
        name = self.persona["name"]
        grade = self.persona["grade"]
        print(f"  [{self.user_id}] {name} (G{grade}) starting...")

        # Onboard
        ok = await self.flow_onboard()
        if not ok:
            print(f"  [{self.user_id}] Failed to onboard — aborting")
            self.report.finished_at = datetime.utcnow().isoformat()
            return

        await self.flow_get_profile()

        # Run rounds of mixed activities
        all_flows = [
            self.flow_practice_session,
            self.flow_smart_session,
            self.flow_worksheets,
            self.flow_wavebook,
            self.flow_streak,
            self.flow_bookmarks,
            self.flow_parent_dashboard,
            self.flow_growth,
            self.flow_daily_puzzle,
            self.flow_rewards,
        ]

        for round_num in range(self.rounds):
            # Pick 2-4 random flows per round
            n_flows = random.randint(2, 4)
            flows = random.sample(all_flows, min(n_flows, len(all_flows)))

            for flow in flows:
                try:
                    await flow()
                except Exception as e:
                    self.report.errors.append(f"{flow.__name__}: {e}")

                # Think time between activities
                await asyncio.sleep(random.uniform(0.2, 1.0))

            self.report.rounds_completed = round_num + 1

        # Try clan once at the end
        try:
            await self.flow_clan()
        except Exception as e:
            self.report.errors.append(f"clan: {e}")

        self.report.finished_at = datetime.utcnow().isoformat()
        errors = len(self.report.errors)
        qs = self.report.questions_answered
        print(
            f"  [{self.user_id}] {name} done — {qs} questions, {errors} errors"
        )

    def _track(self, feature: str, success: bool):
        if feature not in self.report.features_tested:
            self.report.features_tested[feature] = {"pass": 0, "fail": 0}
        key = "pass" if success else "fail"
        self.report.features_tested[feature][key] += 1


def distribute_personas(n_bots: int) -> list[dict]:
    """Even grade distribution: cycles through grades 1-5, assigns Indian names."""
    names_by_grade = {
        1: ["Aarav", "Meera", "Riya", "Krish", "Advait", "Aanya", "Vivaan", "Pari", "Reyansh", "Navya"],
        2: ["Diya", "Rohan", "Anvi", "Aditya", "Ishaan", "Saira", "Dhruv", "Trisha", "Aryan", "Kiara"],
        3: ["Kabir", "Arjun", "Zara", "Atharv", "Pihu", "Shaurya", "Anika", "Rudra", "Myra", "Ayaan"],
        4: ["Ananya", "Saanvi", "Veer", "Siya", "Arnav", "Kavya", "Laksh", "Nisha", "Parth", "Rashi"],
        5: ["Vihaan", "Isha", "Neil", "Tara", "Om", "Prisha", "Ritvik", "Aisha", "Yash", "Mahi"],
    }
    personas = []
    for i in range(n_bots):
        grade = (i % 5) + 1  # cycles 1,2,3,4,5,1,2,...
        names = names_by_grade[grade]
        name = names[i // 5 % len(names)]
        personas.append({"name": name, "grade": grade})
    return personas


async def run_bots(
    base_url: str, n_bots: int, rounds: int, concurrency: int = 20
) -> list[dict]:
    """Spin up N bots with concurrency limit to avoid overwhelming the server."""
    personas = distribute_personas(n_bots)
    semaphore = asyncio.Semaphore(concurrency)

    print(f"\nStarting {n_bots} bot(s) against {base_url}...")
    print(f"Each bot will run {rounds} rounds of mixed activities.")
    print(f"Concurrency limit: {concurrency} simultaneous bots.\n")

    async def run_with_limit(bot):
        async with semaphore:
            await bot.run()

    bots = [KiwimathBot(base_url, p, rounds) for p in personas]
    await asyncio.gather(*[run_with_limit(b) for b in bots])

    reports = [b.report.summary() for b in bots]
    for b in bots:
        await b.close()

    return reports


def print_report(reports: list[dict]):
    """Pretty-print the aggregate report."""
    total_qs = sum(int(r.get("questions", 0)) for r in reports)
    total_errors = sum(int(r.get("errors", 0)) for r in reports)
    bots_ok = sum(1 for r in reports if int(r.get("errors", 0)) == 0)
    all_latencies = []
    for r in reports:
        all_latencies.append(float(r.get("avg_latency_ms", 0)))

    print("\n" + "=" * 60)
    print("  KIWIMATH BOT TEST REPORT")
    print("=" * 60)
    print(f"  Bots:            {len(reports)} ({bots_ok} clean, {len(reports) - bots_ok} with errors)")
    print(f"  Total questions:  {total_qs}")
    print(f"  Total errors:     {total_errors}")
    if all_latencies:
        avg = sum(all_latencies) / len(all_latencies)
        p95 = sorted(all_latencies)[int(len(all_latencies) * 0.95)] if len(all_latencies) > 1 else avg
        print(f"  Avg latency:      {avg:.0f}ms  |  P95: {p95:.0f}ms")
    print()

    # ── Per-grade summary ──────────────────────────────────────
    grade_stats: dict[int, dict] = {}
    for r in reports:
        g = r["persona"]["grade"]
        if g not in grade_stats:
            grade_stats[g] = {"bots": 0, "qs": 0, "errors": 0}
        grade_stats[g]["bots"] += 1
        grade_stats[g]["qs"] += int(r.get("questions", 0))
        grade_stats[g]["errors"] += int(r.get("errors", 0))

    print("  Grade Distribution:")
    print(f"  {'Grade':<8} {'Bots':>6} {'Questions':>10} {'Errors':>8}")
    print("  " + "-" * 36)
    for g in sorted(grade_stats.keys()):
        s = grade_stats[g]
        status = "✅" if s["errors"] == 0 else "❌"
        print(f"  G{g:<7} {s['bots']:>6} {s['qs']:>10} {s['errors']:>7} {status}")
    print()

    # ── Feature matrix ─────────────────────────────────────────
    feature_agg: dict[str, dict[str, int]] = {}
    for r in reports:
        for feat, counts in r.get("features_tested", {}).items():
            if feat not in feature_agg:
                feature_agg[feat] = {"pass": 0, "fail": 0}
            feature_agg[feat]["pass"] += counts.get("pass", 0)
            feature_agg[feat]["fail"] += counts.get("fail", 0)

    print("  Feature Health:")
    print(f"  {'Feature':<25} {'Pass':>6} {'Fail':>6} {'Rate':>8}")
    print("  " + "-" * 50)
    for feat in sorted(feature_agg.keys()):
        p = feature_agg[feat]["pass"]
        f = feature_agg[feat]["fail"]
        rate = f"{p / (p + f) * 100:.0f}%" if (p + f) > 0 else "N/A"
        status = "✅" if f == 0 else "❌"
        print(f"  {feat:<25} {p:>6} {f:>6} {rate:>7} {status}")

    print()

    # ── Error breakdown (deduplicated) ─────────────────────────
    if total_errors > 0:
        error_counts: dict[str, int] = {}
        for r in reports:
            for err in r.get("error_details", []):
                # Normalize: strip bot IDs to group same errors
                key = err[:80].split("→")[0].strip() + " → " + err.split("→")[-1].strip()[:60] if "→" in err else err[:100]
                error_counts[key] = error_counts.get(key, 0) + 1
        print("  Error Summary (deduplicated):")
        for err, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            print(f"    {count:>3}x  {err[:110]}")
        print()

    # ── Pass/fail verdict ──────────────────────────────────────
    failed_features = [f for f, c in feature_agg.items() if c["fail"] > 0]
    if not failed_features:
        print("  ✅ ALL FEATURES PASSING — system healthy")
    else:
        print(f"  ❌ FAILING: {', '.join(failed_features)}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Kiwimath Test Bot Runner — simulates real users for QA & monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick smoke test (5 bots, 3 rounds)
  python -m tests.bots.bot_runner --base-url https://kiwimath-api-deufqab6gq-el.a.run.app

  # Full stress test (100 bots, 5 rounds each)
  python -m tests.bots.bot_runner --bots 100 --rounds 5 --base-url https://kiwimath-api-deufqab6gq-el.a.run.app

  # Monitoring mode: run every 6 hours, 10 bots per cycle
  python -m tests.bots.bot_runner --monitor --interval 21600 --bots 10 --base-url https://kiwimath-api-deufqab6gq-el.a.run.app
""",
    )
    parser.add_argument(
        "--base-url",
        default="https://kiwimath-api-deufqab6gq-el.a.run.app",
        help="Backend API base URL (default: Cloud Run production)",
    )
    parser.add_argument(
        "--bots", type=int, default=5, help="Number of bots per run"
    )
    parser.add_argument(
        "--rounds", type=int, default=3, help="Rounds of mixed activity per bot",
    )
    parser.add_argument(
        "--concurrency", type=int, default=20,
        help="Max simultaneous bots (default: 20, prevents server overload)",
    )
    parser.add_argument(
        "--report-file", default=None, help="Save JSON report to file"
    )
    parser.add_argument(
        "--monitor", action="store_true",
        help="Continuous monitoring mode — runs bots in a loop",
    )
    parser.add_argument(
        "--interval", type=int, default=21600,
        help="Seconds between monitoring runs (default: 21600 = 6 hours)",
    )
    args = parser.parse_args()

    if args.monitor:
        print(f"🔄 Monitoring mode: {args.bots} bots every {args.interval}s ({args.interval // 3600}h)")
        print(f"   Target: {args.base_url}\n")
        run_count = 0
        while True:
            run_count += 1
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            print(f"\n{'─' * 60}")
            print(f"  Monitor run #{run_count} at {ts}")
            print(f"{'─' * 60}")
            reports = asyncio.run(
                run_bots(args.base_url, args.bots, args.rounds, args.concurrency)
            )
            print_report(reports)

            # Save timestamped report
            report_path = f"bot_monitor_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, "w") as f:
                json.dump(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "monitor_run": run_count,
                        "base_url": args.base_url,
                        "n_bots": args.bots,
                        "rounds": args.rounds,
                        "reports": reports,
                    },
                    f,
                    indent=2,
                )
            # Check for critical failures
            total_errors = sum(int(r.get("errors", 0)) for r in reports)
            onboard_fails = sum(
                r.get("features_tested", {}).get("onboarding", {}).get("fail", 0)
                for r in reports
            )
            if onboard_fails > 0:
                print(f"\n  🚨 CRITICAL: {onboard_fails} bots failed to onboard!")
            elif total_errors > 0:
                print(f"\n  ⚠️  {total_errors} non-critical errors detected")
            else:
                print(f"\n  ✅ All clear — next run in {args.interval // 60} minutes")

            try:
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n\nMonitoring stopped.")
                break
    else:
        reports = asyncio.run(
            run_bots(args.base_url, args.bots, args.rounds, args.concurrency)
        )
        print_report(reports)

        if args.report_file:
            with open(args.report_file, "w") as f:
                json.dump(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "base_url": args.base_url,
                        "n_bots": args.bots,
                        "rounds": args.rounds,
                        "reports": reports,
                    },
                    f,
                    indent=2,
                )
            print(f"\n  Report saved to {args.report_file}")


if __name__ == "__main__":
    main()
