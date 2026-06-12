"""
Growth Journey Service — aggregates engagement and proficiency data for the
Growth tab in the Flutter app.

Provides:
  - Mountain journey view (current level, baseline, engagement stats)
  - Per-topic heatmap (current vs diagnostic baseline)
  - Timeline / sparkline data (theta snapshots over time)
  - Milestones timeline (level-ups, badges, streaks, breakthroughs)
  - Diagnostic baseline persistence

Firestore paths used:
  users/{uid}/growth/baseline          — diagnostic baseline snapshot
  users/{uid}/rewards                  — gems, stickers, badges
  users/{uid}/streaks                  — streak data
  users/{uid}/engagement/stats         — aggregate engagement stats
  users/{uid}/proficiency/growth       — theta snapshots over time
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.adaptive_engine_v2 import engine_v2
from app.services.content_store_v2 import store_v2
from app.services.proficiency_levels import (
    get_proficiency_level,
    proficiency_store,
    theta_to_scale_score,
)

logger = logging.getLogger("kiwimath.growth")

# The 8 core Kangaroo / Olympiad topics
_CORE_TOPICS = [
    "counting_observation",
    "arithmetic_missing_numbers",
    "patterns_sequences",
    "logic_ordering",
    "spatial_reasoning_3d",
    "shapes_folding_symmetry",
    "word_problems_stories",
    "number_puzzles_games",
]

# Milestone thresholds
_STREAK_MILESTONES = [7, 30, 100]
_GEM_MILESTONES = [100, 500, 1000, 5000]
_WORKSHEET_MILESTONES = [10, 50, 100, 500]


# ---------------------------------------------------------------------------
# Firestore helpers (graceful fallback)
# ---------------------------------------------------------------------------

def _get_db():
    """Return Firestore client or None."""
    try:
        from app.services.firestore_service import _get_db as fs_get_db
        return fs_get_db()
    except Exception:
        return None


def _read_doc(path: str) -> Optional[Dict[str, Any]]:
    """Read a single Firestore document. Returns None on failure."""
    db = _get_db()
    if not db:
        return None
    try:
        doc = db.document(path).get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        logger.warning(f"Firestore read failed for {path}: {e}")
    return None


def _write_doc(path: str, data: Dict[str, Any], merge: bool = True) -> bool:
    """Write to a Firestore document. Returns True on success."""
    db = _get_db()
    if not db:
        return False
    try:
        db.document(path).set(data, merge=merge)
        return True
    except Exception as e:
        logger.warning(f"Firestore write failed for {path}: {e}")
        return False


# ---------------------------------------------------------------------------
# GrowthService
# ---------------------------------------------------------------------------

class GrowthService:
    """Aggregates growth and engagement data for the Growth tab."""

    # ------------------------------------------------------------------
    # Journey (mountain view)
    # ------------------------------------------------------------------

    def get_journey(self, user_id: str, grade: int) -> Dict[str, Any]:
        """Mountain journey data: current level, baseline, path, milestones,
        engagement stats.
        """
        # --- Current overall theta (weighted average across practiced topics) ---
        current_theta, total_attempts, total_correct = self._compute_overall_theta(user_id)
        current_level = get_proficiency_level(current_theta)
        current_scale = theta_to_scale_score(current_theta)

        # --- Diagnostic baseline ---
        baseline = _read_doc(f"users/{user_id}/growth/baseline")
        baseline_data: Dict[str, Any] = {}
        delta_levels = 0
        delta_scale = 0
        days_since_diagnostic = 0
        suggested_retake = False

        if baseline:
            baseline_data = {
                "level": baseline.get("baseline_level", 1),
                "name": baseline.get("baseline_level_name", "Explorer"),
                "theta": baseline.get("baseline_theta", -3.0),
                "scale_score": baseline.get("baseline_scale", 200),
                "taken_at": baseline.get("taken_at", ""),
            }
            delta_levels = current_level.level - baseline.get("baseline_level", 1)
            delta_scale = current_scale - baseline.get("baseline_scale", 200)

            taken_at = baseline.get("taken_at", "")
            if taken_at:
                try:
                    taken_dt = datetime.fromisoformat(taken_at)
                    now = datetime.now(timezone.utc)
                    days_since_diagnostic = (now - taken_dt).days
                    suggested_retake = days_since_diagnostic > 30
                except Exception:
                    pass

        # --- Engagement stats ---
        engagement = self._aggregate_engagement(user_id)

        # --- Milestones count ---
        milestones = self.get_milestones(user_id, grade)
        milestones_count = len(milestones.get("milestones", []))

        return {
            "current": {
                "level": current_level.level,
                "name": current_level.name,
                "theta": round(current_theta, 3),
                "scale_score": current_scale,
            },
            "baseline": baseline_data,
            "delta_levels": delta_levels,
            "delta_scale": delta_scale,
            "engagement": engagement,
            "milestones_count": milestones_count,
            "days_since_diagnostic": days_since_diagnostic,
            "suggested_retake": suggested_retake,
        }

    # ------------------------------------------------------------------
    # Topic heatmap
    # ------------------------------------------------------------------

    def get_topic_heatmap(self, user_id: str, grade: int) -> Dict[str, Any]:
        """Per-topic growth data: current level vs diagnostic baseline."""
        baseline = _read_doc(f"users/{user_id}/growth/baseline")
        per_topic_baseline: Dict[str, float] = {}
        if baseline:
            per_topic_baseline = baseline.get("per_topic_theta", {})

        all_topics = store_v2.topics()
        # Filter to only the 8 core topics
        core_ids = set(_CORE_TOPICS)
        topics_list = [t for t in all_topics if t.topic_id in core_ids]

        result: List[Dict[str, Any]] = []
        for t in topics_list:
            ability = engine_v2.get_ability(user_id, t.topic_id)
            current_theta = ability.theta
            current_level = get_proficiency_level(current_theta)

            baseline_theta = per_topic_baseline.get(t.topic_id, current_theta)
            baseline_level = get_proficiency_level(baseline_theta)

            delta = round(current_theta - baseline_theta, 3)

            # Determine trend
            if delta > 0.1:
                trend = "up"
            elif delta < -0.1:
                trend = "down"
            else:
                trend = "flat"

            accuracy = ability.correct / max(1, ability.attempts) * 100

            # A topic is a "superpower" if it's the student's highest level
            # (computed after the loop below)
            result.append({
                "topic_id": t.topic_id,
                "name": t.topic_name,
                "current_level": current_level.level,
                "current_theta": round(current_theta, 3),
                "baseline_level": baseline_level.level,
                "baseline_theta": round(baseline_theta, 3),
                "delta": delta,
                "trend": trend,
                "questions_since": ability.attempts,
                "accuracy": round(accuracy, 1),
                "is_superpower": False,
                "needs_levelup": current_level.level < 3 and ability.attempts >= 10,
            })

        # Mark the highest-level topic as superpower
        if result:
            best = max(result, key=lambda x: (x["current_level"], x["current_theta"]))
            best["is_superpower"] = True

        return {"topics": result}

    # ------------------------------------------------------------------
    # Timeline / sparkline
    # ------------------------------------------------------------------

    def get_timeline(self, user_id: str) -> Dict[str, Any]:
        """Sparkline chart data: theta snapshots over time with milestones."""
        growth_data = proficiency_store.get_growth_data(user_id)

        snapshots: List[Dict[str, Any]] = []
        if growth_data.get("has_growth_data"):
            # Pull raw snapshots from Firestore
            raw = _read_doc(f"users/{user_id}/proficiency/growth")
            if raw:
                snapshots = raw.get("snapshots", [])

        # Build engagement milestones for overlay
        engagement_milestones = self._get_engagement_milestones(user_id)

        return {
            "snapshots": snapshots,
            "growth_summary": growth_data,
            "engagement_milestones": engagement_milestones,
        }

    # ------------------------------------------------------------------
    # Milestones
    # ------------------------------------------------------------------

    def get_milestones(self, user_id: str, grade: int) -> Dict[str, Any]:
        """Achievement timeline: level-ups, breakthroughs, engagement milestones."""
        milestones: List[Dict[str, Any]] = []

        # --- Diagnostic milestone ---
        baseline = _read_doc(f"users/{user_id}/growth/baseline")
        if baseline:
            bl_level = baseline.get("baseline_level", 1)
            bl_name = baseline.get("baseline_level_name", "Explorer")
            milestones.append({
                "type": "diagnostic",
                "description": f"Started at Level {bl_level} {bl_name}",
                "date": baseline.get("taken_at", ""),
                "icon": "flag",
            })

        # --- Level-up milestones from growth snapshots ---
        raw_growth = _read_doc(f"users/{user_id}/proficiency/growth")
        if raw_growth:
            snapshots = raw_growth.get("snapshots", [])
            prev_level = None
            for snap in snapshots:
                level = snap.get("level", 1)
                if prev_level is not None and level > prev_level:
                    milestones.append({
                        "type": "level_up",
                        "description": f"Reached Level {level} {snap.get('level_name', '')}",
                        "date": snap.get("timestamp", ""),
                        "icon": "arrow_up",
                        "from_level": prev_level,
                        "to_level": level,
                    })
                prev_level = level

        # --- Topic breakthroughs ---
        all_topics = store_v2.topics()
        core_ids = set(_CORE_TOPICS)
        for t in all_topics:
            if t.topic_id not in core_ids:
                continue
            ability = engine_v2.get_ability(user_id, t.topic_id)
            level = get_proficiency_level(ability.theta)
            if level.level >= 4 and ability.attempts >= 10:
                milestones.append({
                    "type": "topic_breakthrough",
                    "description": f"{t.topic_name} mastered!",
                    "date": ability.updated_at or "",
                    "topic_id": t.topic_id,
                    "icon": "star",
                })

        # --- Engagement milestones ---
        engagement = self._aggregate_engagement(user_id)

        # Streak milestones
        longest = engagement.get("longest_streak", 0)
        for threshold in _STREAK_MILESTONES:
            if longest >= threshold:
                milestones.append({
                    "type": "streak",
                    "description": f"{threshold}-day streak achieved!",
                    "date": "",
                    "icon": "fire",
                    "value": threshold,
                })

        # Gem milestones
        total_gems = engagement.get("total_gems", 0)
        for threshold in _GEM_MILESTONES:
            if total_gems >= threshold:
                milestones.append({
                    "type": "gems",
                    "description": f"Earned {threshold} gems!",
                    "date": "",
                    "icon": "gem",
                    "value": threshold,
                })

        # Badge milestones
        rewards = _read_doc(f"users/{user_id}/rewards")
        if rewards:
            for badge in rewards.get("badges", []):
                milestones.append({
                    "type": "badge",
                    "description": f"Unlocked '{badge.get('name', 'Badge')}'",
                    "date": badge.get("earned_at", ""),
                    "icon": "badge",
                })

        # Worksheet milestones
        worksheets = engagement.get("worksheets_completed", 0)
        for threshold in _WORKSHEET_MILESTONES:
            if worksheets >= threshold:
                milestones.append({
                    "type": "worksheet",
                    "description": f"Completed {threshold} worksheets!",
                    "date": "",
                    "icon": "worksheet",
                    "value": threshold,
                })

        # Clan war milestones
        wars_won = engagement.get("clan_wars_won", 0)
        if wars_won >= 1:
            milestones.append({
                "type": "clan_war",
                "description": "Won first Clan War!" if wars_won == 1 else f"Won {wars_won} Clan Wars!",
                "date": "",
                "icon": "sword",
                "value": wars_won,
            })

        # Sort by date (most recent first), undated items go to the end
        milestones.sort(key=lambda m: m.get("date", "") or "0000", reverse=True)

        return {"milestones": milestones}

    # ------------------------------------------------------------------
    # Diagnostic baseline
    # ------------------------------------------------------------------

    def save_diagnostic_baseline(
        self,
        user_id: str,
        grade: int,
        benchmark_id: str,
        theta: float,
        per_topic_theta: Dict[str, float],
    ) -> Dict[str, Any]:
        """Store diagnostic test result as the baseline for growth tracking."""
        level = get_proficiency_level(theta)
        scale = theta_to_scale_score(theta)
        now = datetime.now(timezone.utc).isoformat()

        # Capture current engagement snapshot at time of diagnostic
        engagement = self._aggregate_engagement(user_id)

        data = {
            "baseline_theta": round(theta, 4),
            "baseline_level": level.level,
            "baseline_level_name": level.name,
            "baseline_scale": scale,
            "per_topic_theta": {k: round(v, 4) for k, v in per_topic_theta.items()},
            "taken_at": now,
            "benchmark_id": benchmark_id,
            "grade": grade,
            "engagement_snapshot": {
                "total_gems": engagement.get("total_gems", 0),
                "current_streak": engagement.get("current_streak", 0),
                "badges_count": engagement.get("badges_earned", 0),
            },
        }

        saved = _write_doc(f"users/{user_id}/growth/baseline", data, merge=False)

        return {
            "status": "saved" if saved else "saved_locally",
            "baseline": data,
        }

    # ------------------------------------------------------------------
    # Has diagnostic check
    # ------------------------------------------------------------------

    def has_diagnostic(self, user_id: str) -> bool:
        """Check if user has taken a diagnostic test."""
        baseline = _read_doc(f"users/{user_id}/growth/baseline")
        return baseline is not None and "baseline_theta" in (baseline or {})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_overall_theta(self, user_id: str):
        """Compute weighted average theta across all practiced topics.

        Returns (avg_theta, total_attempts, total_correct).
        """
        all_topics = store_v2.topics()
        total_attempts = 0
        total_correct = 0
        weighted_theta = 0.0

        for topic in all_topics:
            ability = engine_v2.get_ability(user_id, topic.topic_id)
            if ability.attempts > 0:
                weighted_theta += ability.theta * ability.attempts
                total_attempts += ability.attempts
                total_correct += ability.correct

        if total_attempts == 0:
            return -3.0, 0, 0

        avg_theta = weighted_theta / total_attempts
        return avg_theta, total_attempts, total_correct

    def _aggregate_engagement(self, user_id: str) -> Dict[str, Any]:
        """Pull and aggregate engagement stats from Firestore.

        Falls back to defaults if Firestore is unavailable.
        """
        defaults = {
            "total_gems": 0,
            "total_xp": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "badges_earned": 0,
            "stickers_collected": 0,
            "sticker_album_pct": 0.0,
            "worksheets_completed": 0,
            "daily_puzzles_solved": 0,
            "clan_wars_won": 0,
            "practice_sessions": 0,
            "total_questions_answered": 0,
            "days_active": 0,
        }

        # Read from multiple Firestore paths
        rewards = _read_doc(f"users/{user_id}/rewards")
        streaks = _read_doc(f"users/{user_id}/streaks")
        stats = _read_doc(f"users/{user_id}/engagement/stats")

        if rewards:
            defaults["total_gems"] = rewards.get("total_gems", 0)
            defaults["total_xp"] = rewards.get("total_xp", 0)
            defaults["badges_earned"] = len(rewards.get("badges", []))
            stickers = rewards.get("stickers_collected", [])
            defaults["stickers_collected"] = len(stickers) if isinstance(stickers, list) else stickers
            total_stickers = 60  # default catalog size
            defaults["sticker_album_pct"] = round(
                defaults["stickers_collected"] / max(1, total_stickers) * 100, 1
            )

        if streaks:
            defaults["current_streak"] = streaks.get("current", streaks.get("streak_current", 0))
            defaults["longest_streak"] = streaks.get("longest", streaks.get("streak_longest", 0))

        if stats:
            defaults["worksheets_completed"] = stats.get("worksheets_completed", 0)
            defaults["daily_puzzles_solved"] = stats.get("daily_puzzles_solved", 0)
            defaults["clan_wars_won"] = stats.get("clan_wars_won", 0)
            defaults["practice_sessions"] = stats.get("practice_sessions", 0)
            defaults["total_questions_answered"] = stats.get("total_questions_answered", 0)
            defaults["days_active"] = stats.get("days_active", 0)

        # If no Firestore stats, compute total_questions_answered from adaptive engine
        if defaults["total_questions_answered"] == 0:
            _, total_attempts, _ = self._compute_overall_theta(user_id)
            defaults["total_questions_answered"] = total_attempts

        return defaults

    def _get_engagement_milestones(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve notable engagement milestones for timeline overlay."""
        milestones: List[Dict[str, Any]] = []

        rewards = _read_doc(f"users/{user_id}/rewards")
        if rewards:
            # First badge
            badges = rewards.get("badges", [])
            if badges:
                first_badge = badges[0]
                milestones.append({
                    "type": "badge",
                    "label": f"Badge: {first_badge.get('name', '')}",
                    "date": first_badge.get("earned_at", ""),
                })

        streaks = _read_doc(f"users/{user_id}/streaks")
        if streaks:
            longest = streaks.get("longest", streaks.get("streak_longest", 0))
            if longest >= 7:
                milestones.append({
                    "type": "streak_record",
                    "label": f"Streak record: {longest} days",
                    "date": streaks.get("longest_date", ""),
                })

        return milestones


# Singleton
growth_service = GrowthService()
