"""
Kiwimath Gamification Service — v2: Meritocratic Achievement Economy

Pillars:
  1. Stability Principle — Fixed prices, moving achievement gates
  2. Hero's Formula — Reward improvement (cognitive delta), not just results
  3. Dynamic Rarity — Vault/variant system instead of price inflation
  4. Learner Personas — Steady / Power / Mastery / Comeback
  5. Invisible Central Bank — Server-side circulation tracking, child never sees it

Design principles:
  - A Kiwi Coin is always a Kiwi Coin (no inflation)
  - High-status items are trophies, not purchases
  - Effort > talent (comeback bonus > cruise bonus)
  - No dark patterns, no pay-to-win
  - Parent-friendly: IRT hidden, progress shown as Mastered/Growing/Emerging
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("kiwimath.gamification")


# ---------------------------------------------------------------------------
# Level System (unchanged — 6 tiers)
# ---------------------------------------------------------------------------

LEVELS = [
    {"level": 1, "name": "Seed",        "emoji": "\U0001f331", "xp_min": 0,    "xp_max": 99},
    {"level": 2, "name": "Sprout",      "emoji": "\U0001f33f", "xp_min": 100,  "xp_max": 299},
    {"level": 3, "name": "Kiwi Jr",     "emoji": "\U0001f95d", "xp_min": 300,  "xp_max": 699},
    {"level": 4, "name": "Kiwi",        "emoji": "\U0001f95d", "xp_min": 700,  "xp_max": 1499},
    {"level": 5, "name": "Super Kiwi",  "emoji": "\u2b50",     "xp_min": 1500, "xp_max": 2999},
    {"level": 6, "name": "Kiwi Master", "emoji": "\U0001f451", "xp_min": 3000, "xp_max": 999999},
]


def get_level(xp: int) -> Dict[str, Any]:
    for lvl in reversed(LEVELS):
        if xp >= lvl["xp_min"]:
            progress = (xp - lvl["xp_min"]) / max(1, lvl["xp_max"] - lvl["xp_min"] + 1)
            return {
                **lvl,
                "current_xp": xp,
                "progress_in_level": min(1.0, progress),
                "xp_to_next": max(0, lvl["xp_max"] + 1 - xp) if lvl["level"] < 6 else 0,
            }
    return {**LEVELS[0], "current_xp": xp, "progress_in_level": 0.0, "xp_to_next": 100}


def check_level_up(old_xp: int, new_xp: int) -> Optional[Dict[str, Any]]:
    old_level = get_level(old_xp)["level"]
    new_level = get_level(new_xp)["level"]
    if new_level > old_level:
        return get_level(new_xp)
    return None


# ---------------------------------------------------------------------------
# Micro Celebrations
# ---------------------------------------------------------------------------

MICRO_CELEBRATION_THRESHOLDS = [25, 50, 75, 100, 150, 200, 300, 500, 750, 1000,
                                 1500, 2000, 2500, 3000, 4000, 5000]


def check_micro_celebration(old_xp: int, new_xp: int) -> Optional[str]:
    for threshold in MICRO_CELEBRATION_THRESHOLDS:
        if old_xp < threshold <= new_xp:
            messages = {
                25: "Kiwi is hatching! \U0001f95a",
                50: "Kiwi is growing! \U0001f331",
                75: "Keep it up! \U0001f4aa",
                100: "100 XP! You're a star! \u2b50",
                150: "Kiwi is getting stronger! \U0001f95d",
                200: "200 XP milestone! \U0001f389",
                300: "Rising fast! \U0001f680",
                500: "Half a thousand! Amazing! \U0001f38a",
                750: "Kiwi is proud of you! \U0001f31f",
                1000: "1000 XP! Incredible! \U0001f3c6",
                1500: "Super Kiwi level! \u2b50",
                2000: "2000 XP! You're unstoppable! \U0001f525",
                2500: "Quarter master! \U0001f48e",
                3000: "KIWI MASTER! \U0001f451",
                4000: "Legend status! \U0001f308",
                5000: "5000 XP \u2014 truly extraordinary! \U0001f386",
            }
            return messages.get(threshold, f"{threshold} XP reached! \U0001f389")
    return None


# ---------------------------------------------------------------------------
# 30-Day Psychology Phases
# ---------------------------------------------------------------------------
# Maps the child's journey from first open to long-term engagement.
# Each phase has an emotional goal and a product goal — the reward
# engine adapts its behaviour based on which phase the child is in.

SESSION_PHASES = {
    "genesis_hatching":  {"days": (0, 1),  "emotional": "Wonder and immediate confidence",       "product": "Hatch pet, give first wealth, show first aspiration"},
    "safe_wins":         {"days": (2, 5),  "emotional": "I can do maths",                        "product": "Short sessions, easy wins, visible progress"},
    "habit_loop":        {"days": (6, 10), "emotional": "I come back daily",                     "product": "Streak, daily chest, comeback protection"},
    "identity_growth":   {"days": (11, 20),"emotional": "I am becoming a maths hero",            "product": "Mastery badges, pet evolution, topic celebrations"},
    "long_term_quest":   {"days": (21, 999),"emotional": "I want the Dragon",                    "product": "Reveal deeper gates, world progression, legendary rewards"},
}


def get_session_phase(days_active: int) -> str:
    """Return the current phase name for a child based on how many days active."""
    for phase_id, info in SESSION_PHASES.items():
        lo, hi = info["days"]
        if lo <= days_active <= hi:
            return phase_id
    return "long_term_quest"


def get_phase_info(days_active: int) -> Dict[str, Any]:
    """Get full phase info including emotional/product goals."""
    phase_id = get_session_phase(days_active)
    info = SESSION_PHASES[phase_id]
    return {
        "phase": phase_id,
        "emotional_goal": info["emotional"],
        "product_goal": info["product"],
    }


# ---------------------------------------------------------------------------
# Genesis Onboarding
# ---------------------------------------------------------------------------
# The first experience is magical — the child hatches their pet,
# names it, and gets a "Genesis Chest" with starter wealth.

GENESIS_INITIAL_COINS = 100
GENESIS_INITIAL_GEMS = 1
GENESIS_REWARD_MULTIPLIER = 2  # 2× rewards during genesis session


def complete_genesis(pet_name: str = "Kiwi") -> Dict[str, Any]:
    """Return the genesis rewards to apply to a new child's state.

    Called once when the child completes the hatching onboarding flow.
    """
    return {
        "coins": GENESIS_INITIAL_COINS,
        "gems": GENESIS_INITIAL_GEMS,
        "items": ["genesis_badge"],
        "pet_name": pet_name,
        "message": f"{pet_name} has hatched! Your Kiwi adventure begins! \U0001f95d",
    }


# ---------------------------------------------------------------------------
# Child State Detection
# ---------------------------------------------------------------------------
# Real-time emotional state of the child based on behavioral signals.
# This drives the Next Action Engine to keep the child in flow.

CHILD_STATES = {
    "flowing":    {"emoji": "\U0001f525", "description": "In the zone — 4+ correct in a row"},
    "struggling": {"emoji": "\U0001f622", "description": "2+ wrong in a row — needs rescue"},
    "guessing":   {"emoji": "\U0001f3b2", "description": "Answered wrong in < 3 seconds"},
    "fatigued":   {"emoji": "\U0001f634", "description": "Slow + wrong — time to end on a win"},
    "confident":  {"emoji": "\U0001f4aa", "description": "Correct, no hints — cruising"},
    "bored":      {"emoji": "\U0001f971", "description": "Fast + correct — needs harder questions"},
    "new_user":   {"emoji": "\U0001f331", "description": "Hasn't completed genesis yet"},
}

MAX_WRONG_BEFORE_RESCUE = 2
FATIGUE_TIME_SECONDS = 90  # 90s on a wrong answer = fatigued
GUESSING_TIME_SECONDS = 3  # < 3s wrong = guessing


def detect_child_state(
    consecutive_correct: int,
    consecutive_wrong: int,
    is_correct: bool,
    time_taken_seconds: float,
    hints_used: int,
    completed_genesis: bool,
) -> str:
    """Detect the child's current emotional state from behavioral signals."""
    if not completed_genesis:
        return "new_user"
    if consecutive_wrong >= MAX_WRONG_BEFORE_RESCUE:
        return "struggling"
    if not is_correct and time_taken_seconds < GUESSING_TIME_SECONDS:
        return "guessing"
    if not is_correct and time_taken_seconds > FATIGUE_TIME_SECONDS:
        return "fatigued"
    if consecutive_correct >= 4 and is_correct:
        return "flowing"
    if is_correct and hints_used == 0 and time_taken_seconds < 10:
        return "bored"  # fast + correct + no hints = might be too easy
    if is_correct and hints_used == 0:
        return "confident"
    return "confident"


# ---------------------------------------------------------------------------
# Next Action Engine
# ---------------------------------------------------------------------------
# Decides what the product should do next based on child state + phase.

NEXT_ACTIONS = {
    "show_easier_question":        "Let's try a power-up question and win this together.",
    "show_slightly_harder":        "You're on fire. A stronger challenge is ready.",
    "show_visual_hint":            "Slow down, Math Miner. Your pet has a clue for you.",
    "show_confidence_boost":       "Your brain energy is waking up your pet!",
    "show_challenge_mode":         "Challenge mode unlocked!",
    "show_revision":               "Let's revisit what we've learned.",
    "show_reward_chest":           "You've earned a surprise chest!",
    "end_on_win":                  "One final win and your pet can rest proudly.",
    "continue_normal":             "Great work. Keep growing your brain energy.",
}


def decide_next_action(child_state: str, phase: str) -> Dict[str, str]:
    """Decide next product action based on child state and session phase."""
    if phase == "genesis_hatching":
        return {
            "action": "show_confidence_boost",
            "message": NEXT_ACTIONS["show_confidence_boost"],
        }

    action_map = {
        "struggling":  "show_easier_question",
        "guessing":    "show_visual_hint",
        "flowing":     "show_slightly_harder",
        "fatigued":    "end_on_win",
        "bored":       "show_challenge_mode",
        "confident":   "continue_normal",
        "new_user":    "show_confidence_boost",
    }

    action = action_map.get(child_state, "continue_normal")
    return {
        "action": action,
        "message": NEXT_ACTIONS.get(action, "Keep going!"),
    }


# ---------------------------------------------------------------------------
# Pillar 2: Hero's Formula — Reward Cognitive Delta
# ---------------------------------------------------------------------------
# Per-question rewards with full granularity.

# Base: 5 coins per attempt (even wrong answers earn effort coins)
COIN_PER_ATTEMPT = 5

# Correct answer bonus: +10 coins
CORRECT_BONUS_COINS = 10

# No-hint confidence bonus: +5 coins (correct without any hints)
NO_HINT_BONUS_COINS = 5

# Answer streak bonus: +3 coins per consecutive correct (capped at 5)
ANSWER_STREAK_BONUS = 3
ANSWER_STREAK_CAP = 5

# Hard question courage bonus: +8 coins (difficulty >= 70 out of 100)
HARD_QUESTION_BONUS = 8
HARD_DIFFICULTY_THRESHOLD = 70

# Comeback Bonus: +20 coins if child returned after struggling yesterday
# Session-level coin constants (used in compute_session_coins)
COIN_PER_CORRECT = 5           # Base coins per correct answer in session tally
STREAK_COIN_BONUS = 2          # Extra coins per correct if streak >= 3 days
HARD_COIN_BONUS = 3            # Extra coins per correct on hard-tier questions

COMEBACK_BONUS = 20

# Improvement Bonus: +30 coins if mastery rose significantly
IMPROVEMENT_BONUS = 30

# Perfect session: +25 coins + 2 mastery gems
PERFECT_SESSION_COINS = 25
PERFECT_SESSION_GEMS = 2


def compute_question_reward(
    is_correct: bool,
    difficulty: int,
    hints_used: int,
    consecutive_correct: int,
    is_genesis_session: bool = False,
) -> Dict[str, Any]:
    """Compute per-question Kiwi Coin + XP reward with full breakdown.

    This is the granular per-question formula from the Kiwi Brain engine.
    The session-level bonuses (comeback, improvement) are applied separately.
    """
    breakdown: Dict[str, int] = {}

    # Base: every attempt earns coins (effort > talent)
    coins = COIN_PER_ATTEMPT
    xp = 5
    breakdown["base_effort"] = COIN_PER_ATTEMPT

    if is_correct:
        coins += CORRECT_BONUS_COINS
        xp += 10
        breakdown["correct_bonus"] = CORRECT_BONUS_COINS

        # No-hint confidence bonus
        if hints_used == 0:
            coins += NO_HINT_BONUS_COINS
            breakdown["no_hint_bonus"] = NO_HINT_BONUS_COINS

        # Answer streak bonus (capped)
        if consecutive_correct >= 2:
            streak_bonus = ANSWER_STREAK_BONUS * min(consecutive_correct, ANSWER_STREAK_CAP)
            coins += streak_bonus
            breakdown["answer_streak"] = streak_bonus

        # Hard question courage bonus
        if difficulty >= HARD_DIFFICULTY_THRESHOLD:
            coins += HARD_QUESTION_BONUS
            xp += 10
            breakdown["hard_courage"] = HARD_QUESTION_BONUS

    # Genesis 2× multiplier
    if is_genesis_session:
        coins *= GENESIS_REWARD_MULTIPLIER
        xp *= GENESIS_REWARD_MULTIPLIER
        breakdown["genesis_multiplier"] = coins  # show total after multiplier

    return {
        "coins": coins,
        "xp": xp,
        "breakdown": breakdown,
    }


def compute_session_coins(
    correct: int,
    total: int,
    streak_days: int,
    is_hard_tier: bool = False,
    is_comeback: bool = False,
    mastery_improved: bool = False,
) -> Dict[str, Any]:
    """Compute Kiwi Coins earned from a session using the Hero's Formula.

    Daily_Tokens = sum(Base + Bonus_Logic)

    Returns breakdown dict so the child can see WHY they earned each coin.
    """
    breakdown: Dict[str, int] = {}

    # Base: 5 coins per correct answer
    base = correct * COIN_PER_CORRECT
    breakdown["base"] = base

    # Streak bonus: +2 per correct if streak >= 3 days
    streak_bonus = 0
    if streak_days >= 3:
        streak_bonus = correct * STREAK_COIN_BONUS
        breakdown["streak_bonus"] = streak_bonus

    # Hard tier bonus: +3 per correct
    hard_bonus = 0
    if is_hard_tier:
        hard_bonus = correct * HARD_COIN_BONUS
        breakdown["hard_bonus"] = hard_bonus

    # Comeback Bonus: +20 if child returned after a struggle
    comeback = 0
    if is_comeback:
        comeback = COMEBACK_BONUS
        breakdown["comeback_bonus"] = comeback

    # Improvement Bonus: +30 if mastery rose significantly
    improvement = 0
    if mastery_improved:
        improvement = IMPROVEMENT_BONUS
        breakdown["improvement_bonus"] = improvement

    # Perfect session
    perfect = 0
    if correct == total and total >= 5:
        perfect = PERFECT_SESSION_COINS
        breakdown["perfect_bonus"] = perfect

    total_coins = base + streak_bonus + hard_bonus + comeback + improvement + perfect

    return {
        "coins_earned": total_coins,
        "breakdown": breakdown,
    }


def compute_mastery_gems(
    correct: int,
    total: int,
    accuracy_percent: float,
    topics_mastered_count: int,
) -> Dict[str, Any]:
    """Compute Mastery Gems — the "Skill" currency.

    Mastery gems are harder to earn than coins. They represent genuine skill.
    1 gem per 3 correct answers, +2 for perfect, +1 per newly mastered topic.
    """
    gems = correct // 3

    # Perfect session bonus
    perfect_gems = 0
    if correct == total and total >= 5:
        perfect_gems = PERFECT_SESSION_GEMS
        gems += perfect_gems

    return {
        "gems_earned": gems,
        "perfect_gems": perfect_gems,
    }


# ---------------------------------------------------------------------------
# Mastery Score Formula (from Kiwi Brain reference)
# ---------------------------------------------------------------------------
# Weighted composite: 55% accuracy + 25% attempt confidence + 20% ability
# This is used for topic mastery evaluation and gate checks.

MASTERY_THRESHOLD = 80  # 80+ = "Mastered"


def calculate_mastery_score(
    accuracy: float,
    attempts: int,
    ability_score: float = 300.0,
) -> int:
    """Calculate mastery score (0-100) using weighted formula.

    Components:
    - Accuracy (55%): raw correct/attempts ratio
    - Attempt confidence (25%): min(attempts/20, 1.0) — ramps to 1.0 at 20 attempts
    - Ability component (20%): ability_score/800 clamped to [0,1]
    """
    if attempts == 0:
        return 0
    accuracy_component = accuracy / 100.0  # normalize to 0-1
    attempt_confidence = min(attempts / 20.0, 1.0)
    ability_component = max(0.0, min(ability_score / 800.0, 1.0))
    score = 100 * (0.55 * accuracy_component + 0.25 * attempt_confidence + 0.20 * ability_component)
    return round(max(0, min(100, score)))


def topic_crossed_mastery(mastery_before: int, mastery_after: int) -> bool:
    """Check if a topic just crossed the mastery threshold."""
    return mastery_before < MASTERY_THRESHOLD <= mastery_after


# ---------------------------------------------------------------------------
# Pillar 4: Learner Personas
# ---------------------------------------------------------------------------

LEARNER_PERSONAS = {
    "steady_learner": {
        "name": "Guardian of the Streak",
        "emoji": "\U0001f6e1\ufe0f",
        "description": "Consistent, 10 min/day",
        "hook": "The Guardian of the Streak",
    },
    "power_learner": {
        "name": "The Math Miner",
        "emoji": "\u26cf\ufe0f",
        "description": "High volume, fast solver",
        "hook": "The Math Miner",
    },
    "mastery_learner": {
        "name": "The Sovereign Genius",
        "emoji": "\U0001f9e0",
        "description": "Tackles the hardest problems",
        "hook": "The Sovereign Genius",
    },
    "comeback_learner": {
        "name": "The Resilient Hero",
        "emoji": "\U0001f9b8",
        "description": "Returns after a struggle",
        "hook": "The Resilient Hero",
    },
    "explorer_learner": {
        "name": "The Curious Explorer",
        "emoji": "\U0001f9ed",
        "description": "Tries every topic, loves variety",
        "hook": "The Curious Explorer",
    },
}


def classify_learner(
    streak_days: int,
    sessions_completed: int,
    hard_correct: int,
    hard_attempted: int,
    comeback_count: int,
    accuracy_percent: float,
    topics_practised: int = 0,
    topics_mastered: int = 0,
) -> str:
    """Classify child into a learner persona based on behavioral signals.

    Priority order (most aspirational identity first):
    1. Comeback Learner — if they've come back from struggles (highest merit)
    2. Mastery Learner — if they tackle hard questions with high accuracy
    3. Explorer Learner — tries many topics but hasn't mastered them yet
    4. Power Learner — if they do high volume sessions
    5. Steady Learner — default, consistent practice (always positive)
    """
    # Comeback: 2+ comebacks after struggle
    if comeback_count >= 2:
        return "comeback_learner"

    # Mastery: attempted 10+ hard questions with 60%+ accuracy on them
    if hard_attempted >= 10 and hard_correct / max(1, hard_attempted) >= 0.6:
        return "mastery_learner"

    # Explorer: tried 5+ topics but mastered fewer than 3
    if topics_practised >= 5 and topics_mastered < 3:
        return "explorer_learner"

    # Power: 20+ sessions completed
    if sessions_completed >= 20:
        return "power_learner"

    # Default: steady learner
    return "steady_learner"


# ---------------------------------------------------------------------------
# Pillar 1: Stability Principle — Fixed Prices, Achievement Gates
# ---------------------------------------------------------------------------

# Shop items use KIWI COINS (not gems) for regular items.
# Legendary items use Achievement Gates (coins + gems + level + mastery).

SHOP_ITEMS = {
    "hats": [
        {"id": "hat_pirate",      "name": "Pirate Hat",     "emoji": "\U0001f3f4\u200d\u2620\ufe0f", "coin_price": 60,  "tier": "common"},
        {"id": "hat_astronaut",   "name": "Space Helmet",   "emoji": "\U0001f680",  "coin_price": 100, "tier": "uncommon"},
        {"id": "hat_crown",       "name": "Royal Crown",    "emoji": "\U0001f451",  "coin_price": 200, "tier": "rare"},
        {"id": "hat_wizard",      "name": "Wizard Hat",     "emoji": "\U0001f9d9",  "coin_price": 80,  "tier": "common"},
        {"id": "hat_chef",        "name": "Chef's Hat",     "emoji": "\U0001f468\u200d\U0001f373", "coin_price": 50,  "tier": "common"},
        {"id": "hat_detective",   "name": "Detective Cap",  "emoji": "\U0001f575\ufe0f",  "coin_price": 70,  "tier": "common"},
    ],
    "glasses": [
        {"id": "glasses_star",    "name": "Star Glasses",   "emoji": "\u2b50",  "coin_price": 40,  "tier": "common"},
        {"id": "glasses_heart",   "name": "Heart Glasses",  "emoji": "\u2764\ufe0f",  "coin_price": 40,  "tier": "common"},
        {"id": "glasses_cool",    "name": "Cool Shades",    "emoji": "\U0001f60e",  "coin_price": 50,  "tier": "common"},
        {"id": "glasses_nerd",    "name": "Nerd Specs",     "emoji": "\U0001f913",  "coin_price": 30,  "tier": "common"},
    ],
    "outfits": [
        {"id": "outfit_cape",     "name": "Super Cape",     "emoji": "\U0001f9b8",  "coin_price": 80,  "tier": "uncommon"},
        {"id": "outfit_tux",      "name": "Fancy Tuxedo",   "emoji": "\U0001f935",  "coin_price": 100, "tier": "uncommon"},
        {"id": "outfit_ninja",    "name": "Ninja Suit",     "emoji": "\U0001f977",  "coin_price": 90,  "tier": "uncommon"},
        {"id": "outfit_sport",    "name": "Sports Jersey",  "emoji": "\u26bd",  "coin_price": 60,  "tier": "common"},
    ],
    "colors": [
        {"id": "color_gold",      "name": "Golden Kiwi",    "emoji": "\U0001f7e1",  "coin_price": 70,  "tier": "uncommon"},
        {"id": "color_blue",      "name": "Ocean Kiwi",     "emoji": "\U0001f535",  "coin_price": 60,  "tier": "common"},
        {"id": "color_pink",      "name": "Berry Kiwi",     "emoji": "\U0001fa77",  "coin_price": 60,  "tier": "common"},
        {"id": "color_purple",    "name": "Galaxy Kiwi",    "emoji": "\U0001f7e3",  "coin_price": 80,  "tier": "uncommon"},
    ],
    "effects": [
        {"id": "fx_fireworks",    "name": "Fireworks",      "emoji": "\U0001f386",  "coin_price": 50,  "tier": "common"},
        {"id": "fx_rainbow",      "name": "Rainbow Burst",  "emoji": "\U0001f308",  "coin_price": 60,  "tier": "common"},
        {"id": "fx_stars",        "name": "Star Shower",    "emoji": "\u2728",  "coin_price": 40,  "tier": "common"},
    ],
}

# ---------------------------------------------------------------------------
# Pillar 1 + 3: Achievement Gates for Legendary Items
# ---------------------------------------------------------------------------
# "Fixed Prices, Moving Gates" — the child sees the same price forever.
# Scarcity is managed by GATES, not price increases.

LEGENDARY_ITEMS = {
    "dragon_golden": {
        "name": "Golden Dragon",
        "emoji": "\U0001f409",
        "category": "legendary",
        "slot": "celebration_fx",
        "coin_price": 500,       # The visible, stable price
        "gem_price": 10,         # Mastery Gems required
        "generation": 1,         # Current generation (for vault rotation)
        "is_vaulted": False,     # Set True when retired
        "gate": {
            "kiwi_coins": 500,
            "mastery_gems": 10,
            "min_level": 5,            # Super Kiwi or above
            "topics_mastered": 3,      # Breadth: 3+ topics at 70%+ accuracy
            "weekly_streak": 5,        # Consistency: 5+ day streak
        },
    },
    "dragon_frost": {
        "name": "Frost Dragon",
        "emoji": "\U0001f409",
        "category": "legendary",
        "slot": "celebration_fx",
        "coin_price": 500,
        "gem_price": 10,
        "generation": 2,
        "is_vaulted": True,      # Not yet released — waiting for Golden saturation
        "gate": {
            "kiwi_coins": 500,
            "mastery_gems": 10,
            "min_level": 5,
            "topics_mastered": 4,
            "weekly_streak": 7,
        },
    },
    "dragon_shadow": {
        "name": "Shadow Dragon",
        "emoji": "\U0001f432",
        "category": "legendary",
        "slot": "celebration_fx",
        "coin_price": 500,
        "gem_price": 12,
        "generation": 3,
        "is_vaulted": True,
        "gate": {
            "kiwi_coins": 500,
            "mastery_gems": 12,
            "min_level": 6,
            "topics_mastered": 5,
            "weekly_streak": 7,
        },
    },
    "unicorn_rainbow": {
        "name": "Rainbow Unicorn",
        "emoji": "\U0001f984",
        "category": "legendary",
        "slot": "hat",
        "coin_price": 400,
        "gem_price": 8,
        "generation": 1,
        "is_vaulted": False,
        "gate": {
            "kiwi_coins": 400,
            "mastery_gems": 8,
            "min_level": 4,
            "topics_mastered": 2,
            "weekly_streak": 3,
        },
    },
    "phoenix_crown": {
        "name": "Phoenix Crown",
        "emoji": "\U0001f525",
        "category": "legendary",
        "slot": "hat",
        "coin_price": 600,
        "gem_price": 15,
        "generation": 1,
        "is_vaulted": False,
        "gate": {
            "kiwi_coins": 600,
            "mastery_gems": 15,
            "min_level": 6,
            "topics_mastered": 6,
            "weekly_streak": 10,
        },
    },
}


def check_achievement_gate(
    item_id: str,
    kiwi_coins: int,
    mastery_gems: int,
    level: int,
    topics_mastered: int,
    weekly_streak: int,
) -> Dict[str, Any]:
    """Check if a child meets all requirements for a legendary item.

    Returns gate status with per-requirement pass/fail so the UI can show
    progress toward each gate criterion (the child sees a checklist, not a price tag).
    """
    item = LEGENDARY_ITEMS.get(item_id)
    if not item:
        return {"unlockable": False, "error": "Item not found"}

    if item.get("is_vaulted", False):
        return {"unlockable": False, "error": "Item is in the vault", "vaulted": True}

    gate = item["gate"]
    checks = {
        "kiwi_coins": {
            "required": gate["kiwi_coins"],
            "current": kiwi_coins,
            "passed": kiwi_coins >= gate["kiwi_coins"],
            "label": f"{gate['kiwi_coins']} Kiwi Coins",
        },
        "mastery_gems": {
            "required": gate["mastery_gems"],
            "current": mastery_gems,
            "passed": mastery_gems >= gate["mastery_gems"],
            "label": f"{gate['mastery_gems']} Mastery Gems",
        },
        "min_level": {
            "required": gate["min_level"],
            "current": level,
            "passed": level >= gate["min_level"],
            "label": f"Level {gate['min_level']}+",
        },
        "topics_mastered": {
            "required": gate["topics_mastered"],
            "current": topics_mastered,
            "passed": topics_mastered >= gate["topics_mastered"],
            "label": f"{gate['topics_mastered']} topics mastered",
        },
        "weekly_streak": {
            "required": gate["weekly_streak"],
            "current": weekly_streak,
            "passed": weekly_streak >= gate["weekly_streak"],
            "label": f"{gate['weekly_streak']}-day streak",
        },
    }

    all_passed = all(c["passed"] for c in checks.values())

    return {
        "unlockable": all_passed,
        "item": {
            "id": item_id,
            "name": item["name"],
            "emoji": item["emoji"],
            "slot": item["slot"],
        },
        "gates": checks,
        "gates_passed": sum(1 for c in checks.values() if c["passed"]),
        "gates_total": len(checks),
    }


# ---------------------------------------------------------------------------
# Pillar 3: Dynamic Rarity — Vault System
# ---------------------------------------------------------------------------
# When 5% of users have the Golden Dragon, the Central Bank vaults it
# and releases the Frost Dragon. Early adopters keep their "Legacy Item."

VAULT_SATURATION_THRESHOLD = 0.05  # 5% of active users


def get_active_legendaries() -> List[Dict[str, Any]]:
    """Return legendaries currently available (not vaulted)."""
    active = []
    for item_id, item in LEGENDARY_ITEMS.items():
        if not item.get("is_vaulted", False):
            active.append({
                "id": item_id,
                "name": item["name"],
                "emoji": item["emoji"],
                "slot": item["slot"],
                "coin_price": item["coin_price"],
                "gem_price": item["gem_price"],
                "generation": item["generation"],
                "gate": item["gate"],
            })
    return active


def get_vaulted_legendaries() -> List[Dict[str, Any]]:
    """Return legendaries in the vault (retired or not yet released)."""
    vaulted = []
    for item_id, item in LEGENDARY_ITEMS.items():
        if item.get("is_vaulted", False):
            vaulted.append({
                "id": item_id,
                "name": item["name"],
                "emoji": item["emoji"],
                "generation": item["generation"],
            })
    return vaulted


# ---------------------------------------------------------------------------
# Badge System — 12 Starter Badges, 3 Tiers Each (unchanged)
# ---------------------------------------------------------------------------

BADGE_DEFINITIONS = {
    # === EFFORT BADGES ===
    "first_try_hero": {
        "name": "First Try Hero",
        "emoji": "\U0001f9b8",
        "category": "effort",
        "description": "Answer your first question!",
        "tiers": {
            "bronze": {"requirement": "Answer 1 question", "threshold": 1},
            "silver": {"requirement": "Answer 50 questions", "threshold": 50},
            "gold":   {"requirement": "Answer 200 questions", "threshold": 200},
        },
        "metric": "total_attempts",
    },
    "never_give_up": {
        "name": "Never Give Up",
        "emoji": "\U0001f4aa",
        "category": "effort",
        "description": "Keep trying even when it's hard!",
        "tiers": {
            "bronze": {"requirement": "Retry 3 wrong answers", "threshold": 3},
            "silver": {"requirement": "Retry 15 wrong answers", "threshold": 15},
            "gold":   {"requirement": "Retry 50 wrong answers", "threshold": 50},
        },
        "metric": "retries_after_wrong",
    },
    "daily_learner": {
        "name": "Daily Learner",
        "emoji": "\U0001f4c5",
        "category": "effort",
        "description": "Practice every day!",
        "tiers": {
            "bronze": {"requirement": "3-day streak", "threshold": 3},
            "silver": {"requirement": "7-day streak", "threshold": 7},
            "gold":   {"requirement": "30-day streak", "threshold": 30},
        },
        "metric": "streak_longest",
    },
    "welcome_back_hero": {
        "name": "Welcome Back Hero",
        "emoji": "\U0001f423",
        "category": "effort",
        "description": "Come back after a break \u2014 that takes courage!",
        "tiers": {
            "bronze": {"requirement": "Return after 1 day break", "threshold": 1},
            "silver": {"requirement": "Return after 3 day break", "threshold": 3},
            "gold":   {"requirement": "Return after 7 day break", "threshold": 7},
        },
        "metric": "comeback_count",
    },

    # === SKILL BADGES ===
    "number_ninja": {
        "name": "Number Ninja",
        "emoji": "\U0001f522",
        "category": "skill",
        "description": "Master counting and arithmetic!",
        "tiers": {
            "bronze": {"requirement": "Answer 10 counting/arithmetic correct", "threshold": 10},
            "silver": {"requirement": "Answer 30 correct with 70%+ accuracy", "threshold": 30},
            "gold":   {"requirement": "Answer 60 correct with 85%+ accuracy", "threshold": 60},
        },
        "metric": "topic_correct",
        "topics": ["counting_observation", "arithmetic_missing_numbers"],
    },
    "shape_wizard": {
        "name": "Shape Wizard",
        "emoji": "\U0001f53a",
        "category": "skill",
        "description": "See shapes everywhere!",
        "tiers": {
            "bronze": {"requirement": "Answer 10 shape questions correct", "threshold": 10},
            "silver": {"requirement": "Answer 30 correct with 70%+ accuracy", "threshold": 30},
            "gold":   {"requirement": "Answer 60 correct with 85%+ accuracy", "threshold": 60},
        },
        "metric": "topic_correct",
        "topics": ["shapes_folding_symmetry", "spatial_reasoning"],
    },
    "logic_detective": {
        "name": "Logic Detective",
        "emoji": "\U0001f575\ufe0f",
        "category": "skill",
        "description": "Crack every logic puzzle!",
        "tiers": {
            "bronze": {"requirement": "Answer 10 logic questions correct", "threshold": 10},
            "silver": {"requirement": "Answer 30 correct with 70%+ accuracy", "threshold": 30},
            "gold":   {"requirement": "Answer 60 correct with 85%+ accuracy", "threshold": 60},
        },
        "metric": "topic_correct",
        "topics": ["logic_ordering"],
    },
    "puzzle_dragon": {
        "name": "Puzzle Dragon Slayer",
        "emoji": "\U0001f409",
        "category": "skill",
        "description": "Defeat the trickiest puzzles!",
        "tiers": {
            "bronze": {"requirement": "Answer 10 puzzle questions correct", "threshold": 10},
            "silver": {"requirement": "Answer 30 correct with 70%+ accuracy", "threshold": 30},
            "gold":   {"requirement": "Answer 60 correct with 85%+ accuracy", "threshold": 60},
        },
        "metric": "topic_correct",
        "topics": ["number_puzzles", "patterns_sequences"],
    },

    # === MASTERY BADGES ===
    "sharpshooter": {
        "name": "Sharpshooter",
        "emoji": "\U0001f3af",
        "category": "mastery",
        "description": "Hit the bullseye with amazing accuracy!",
        "tiers": {
            "bronze": {"requirement": "70% accuracy over 20 questions", "threshold": 70},
            "silver": {"requirement": "80% accuracy over 50 questions", "threshold": 80},
            "gold":   {"requirement": "90% accuracy over 100 questions", "threshold": 90},
        },
        "metric": "accuracy_percent",
    },
    "hard_climber": {
        "name": "Hard Climber",
        "emoji": "\U0001f3d4\ufe0f",
        "category": "mastery",
        "description": "Conquer the hardest questions!",
        "tiers": {
            "bronze": {"requirement": "Answer 3 hard questions correctly", "threshold": 3},
            "silver": {"requirement": "Answer 10 hard questions correctly", "threshold": 10},
            "gold":   {"requirement": "Answer 25 hard questions correctly", "threshold": 25},
        },
        "metric": "hard_correct",
    },
    "all_topics": {
        "name": "Rainbow Explorer",
        "emoji": "\U0001f308",
        "category": "mastery",
        "description": "Try every topic!",
        "tiers": {
            "bronze": {"requirement": "Practice 3 different topics", "threshold": 3},
            "silver": {"requirement": "Practice 5 different topics", "threshold": 5},
            "gold":   {"requirement": "Practice all 8 topics", "threshold": 8},
        },
        "metric": "topics_practised",
    },
    "kiwi_champion": {
        "name": "Kiwi Champion",
        "emoji": "\U0001f3c6",
        "category": "mastery",
        "description": "The ultimate Kiwimath achiever!",
        "tiers": {
            "bronze": {"requirement": "Earn 5 other badges", "threshold": 5},
            "silver": {"requirement": "Earn 8 other badges (any tier)", "threshold": 8},
            "gold":   {"requirement": "Earn all 11 other badges at silver+", "threshold": 11},
        },
        "metric": "total_badges",
    },
}


@dataclass
class BadgeState:
    badge_id: str
    current_tier: Optional[str] = None
    progress: int = 0
    unlocked_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "badge_id": self.badge_id,
            "current_tier": self.current_tier,
            "progress": self.progress,
            "unlocked_at": self.unlocked_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BadgeState":
        return cls(
            badge_id=data.get("badge_id", ""),
            current_tier=data.get("current_tier"),
            progress=data.get("progress", 0),
            unlocked_at=data.get("unlocked_at"),
        )


def evaluate_badges(
    stats: Dict[str, Any],
    current_badges: Dict[str, BadgeState],
) -> Tuple[Dict[str, BadgeState], List[Dict[str, Any]]]:
    new_unlocks = []
    updated = dict(current_badges)

    for badge_id, defn in BADGE_DEFINITIONS.items():
        if badge_id not in updated:
            updated[badge_id] = BadgeState(badge_id=badge_id)

        state = updated[badge_id]
        metric_key = defn["metric"]

        if metric_key == "topic_correct":
            topic_correct = stats.get("topic_correct", {})
            relevant_topics = defn.get("topics", [])
            value = sum(topic_correct.get(t, 0) for t in relevant_topics)
        elif metric_key == "total_badges":
            value = sum(
                1 for bid, bs in updated.items()
                if bid != badge_id and bs.current_tier is not None
            )
        else:
            value = stats.get(metric_key, 0)

        state.progress = value

        tiers_order = ["bronze", "silver", "gold"]
        current_tier_idx = tiers_order.index(state.current_tier) if state.current_tier else -1

        for tier_idx, tier_name in enumerate(tiers_order):
            if tier_idx <= current_tier_idx:
                continue
            threshold = defn["tiers"][tier_name]["threshold"]

            if metric_key == "accuracy_percent":
                min_questions = {70: 20, 80: 50, 90: 100}.get(threshold, 20)
                if stats.get("total_attempts", 0) < min_questions:
                    break
                if value < threshold:
                    break
            elif value < threshold:
                break

            state.current_tier = tier_name
            state.unlocked_at = datetime.now(timezone.utc).isoformat()

            # Badge rewards: coins + gems (meritocratic economy)
            coin_reward = {"bronze": 20, "silver": 50, "gold": 100}[tier_name]
            gem_reward = {"bronze": 3, "silver": 5, "gold": 10}[tier_name]
            new_unlocks.append({
                "badge_id": badge_id,
                "badge_name": defn["name"],
                "emoji": defn["emoji"],
                "tier": tier_name,
                "coins_awarded": coin_reward,
                "gems_awarded": gem_reward,
                "description": defn["tiers"][tier_name]["requirement"],
            })

    return updated, new_unlocks


# ---------------------------------------------------------------------------
# Identity Titles (updated with learner persona hooks)
# ---------------------------------------------------------------------------

TITLES = [
    {"id": "curious_thinker",  "name": "Curious Thinker",  "emoji": "\U0001f914", "requirement": "Ask for 5 hints",        "metric": "hints_used",       "threshold": 5},
    {"id": "brave_solver",     "name": "Brave Solver",     "emoji": "\U0001f4a1", "requirement": "Attempt 10 hard questions","metric": "hard_attempted",   "threshold": 10},
    {"id": "pattern_finder",   "name": "Pattern Finder",   "emoji": "\U0001f50d", "requirement": "Master patterns topic",   "metric": "pattern_mastery",  "threshold": 70},
    {"id": "logic_hero",       "name": "Logic Hero",       "emoji": "\U0001f9e0", "requirement": "Master logic topic",      "metric": "logic_mastery",    "threshold": 70},
    {"id": "math_explorer",    "name": "Math Explorer",    "emoji": "\U0001f31f", "requirement": "Try all 8 topics",        "metric": "topics_practised", "threshold": 8},
    # Persona-based titles (earned through behavioral classification)
    {"id": "streak_guardian",  "name": "Streak Guardian",  "emoji": "\U0001f6e1\ufe0f", "requirement": "7-day streak as Steady Learner", "metric": "streak_longest", "threshold": 7},
    {"id": "resilient_hero",   "name": "Resilient Hero",   "emoji": "\U0001f9b8", "requirement": "3+ comebacks",            "metric": "comeback_count",   "threshold": 3},
]


def evaluate_titles(stats: Dict[str, Any], current_titles: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    all_titles = list(current_titles)
    newly_earned = []

    for title_def in TITLES:
        if title_def["id"] in all_titles:
            continue

        value = stats.get(title_def["metric"], 0)
        if value >= title_def["threshold"]:
            all_titles.append(title_def["id"])
            newly_earned.append({
                "id": title_def["id"],
                "name": title_def["name"],
                "emoji": title_def["emoji"],
            })

    return all_titles, newly_earned


# ---------------------------------------------------------------------------
# Surprise Chests (rewards in COINS now, not just gems)
# ---------------------------------------------------------------------------

CHEST_INTERVAL = 3

CHEST_REWARDS = [
    {"coins": 30, "gems": 2, "message": "Kiwi found a hidden treasure! \U0001f48e"},
    {"coins": 25, "gems": 1, "message": "A chest full of sparkles! \u2728"},
    {"coins": 35, "gems": 2, "message": "Kiwi dug up something special! \U0001f31f"},
    {"coins": 40, "gems": 3, "message": "A golden chest! Amazing! \U0001f3c6"},
    {"coins": 30, "gems": 2, "message": "Surprise coins from Captain Kiwi! \U0001f95d"},
    {"coins": 25, "gems": 1, "message": "The math fairy left you a gift! \U0001f9da"},
]


def check_chest(sessions_completed: int) -> Optional[Dict[str, Any]]:
    if sessions_completed <= 0:
        return None

    if sessions_completed % CHEST_INTERVAL == 0:
        chest_idx = (sessions_completed // CHEST_INTERVAL - 1) % len(CHEST_REWARDS)
        reward = CHEST_REWARDS[chest_idx]
        return {
            "chest_number": sessions_completed // CHEST_INTERVAL,
            "coins": reward["coins"],
            "gems": reward["gems"],
            "message": reward["message"],
        }
    return None


# ---------------------------------------------------------------------------
# Kiwi Avatar
# ---------------------------------------------------------------------------

DEFAULT_AVATAR = {
    "base_color": "green",
    "hat": None,
    "glasses": None,
    "outfit": None,
    "celebration_fx": "confetti",
}


def get_shop_catalog() -> Dict[str, List[Dict[str, Any]]]:
    return SHOP_ITEMS


def can_purchase_with_coins(coins: int, item_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Check if a regular (non-legendary) item can be purchased with coins."""
    for category, items in SHOP_ITEMS.items():
        for item in items:
            if item["id"] == item_id:
                return coins >= item["coin_price"], item
    return False, None


# ---------------------------------------------------------------------------
# Parent Dashboard Helper
# ---------------------------------------------------------------------------

def mastery_label(accuracy: float) -> str:
    if accuracy >= 80:
        return "Mastered"
    elif accuracy >= 50:
        return "Growing"
    elif accuracy >= 20:
        return "Emerging"
    else:
        return "Starting"


def mastery_color(label: str) -> str:
    return {
        "Mastered": "#4CAF50",
        "Growing": "#2196F3",
        "Emerging": "#FF9800",
        "Starting": "#9E9E9E",
    }.get(label, "#9E9E9E")


def parent_topic_summary(topic_name: str, accuracy: float, attempts: int) -> Dict[str, Any]:
    label = mastery_label(accuracy)
    return {
        "topic": topic_name,
        "status": label,
        "color": mastery_color(label),
        "accuracy": round(accuracy, 1),
        "questions_practised": attempts,
        "suggestion": _parent_suggestion(label, topic_name),
    }


def _parent_suggestion(label: str, topic: str) -> str:
    if label == "Mastered":
        return f"Great progress in {topic}! Try harder questions to keep growing."
    elif label == "Growing":
        return f"{topic} is improving! A few more practice sessions will help."
    elif label == "Emerging":
        return f"{topic} needs more practice. Try the easy questions first."
    else:
        return f"Let's start exploring {topic} together!"


# ---------------------------------------------------------------------------
# Gamification State Manager (v2 — dual currency)
# ---------------------------------------------------------------------------

@dataclass
class GamificationState:
    """Complete gamification state for a student — v2 with dual currency."""
    user_id: str
    xp_total: int = 0
    kiwi_coins: int = 0          # Effort currency (the "Labor" economy)
    gems: int = 5                # Mastery Gems (the "Skill" economy, starter = 5)
    streak_current: int = 0
    streak_longest: int = 0
    sessions_completed: int = 0
    total_attempts: int = 0
    total_correct: int = 0
    hard_correct: int = 0
    hard_attempted: int = 0
    retries_after_wrong: int = 0
    comeback_count: int = 0
    hints_used: int = 0
    topics_practised: List[str] = field(default_factory=list)
    topic_correct: Dict[str, int] = field(default_factory=dict)
    topic_attempts: Dict[str, int] = field(default_factory=dict)
    badges: Dict[str, BadgeState] = field(default_factory=dict)
    titles: List[str] = field(default_factory=list)
    avatar: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_AVATAR))
    owned_items: List[str] = field(default_factory=list)
    # v2 fields
    learner_persona: str = "steady_learner"
    last_session_accuracy: float = 0.0     # For improvement detection
    last_session_struggled: bool = False   # For comeback bonus
    topics_mastered_count: int = 0         # Topics at 70%+ accuracy with 10+ attempts
    lifetime_coins_earned: int = 0         # Central Bank tracking
    lifetime_gems_earned: int = 0          # Central Bank tracking
    # v3 fields — child state / genesis / phase tracking
    consecutive_correct: int = 0           # Running count for child state detection
    consecutive_wrong: int = 0             # Running count for child state detection
    completed_genesis: bool = False        # Whether genesis onboarding is done
    pet_name: str = "Kiwi"                 # Genesis pet name
    days_active: int = 0                   # Total days the child has been active
    # v4 fields — per-question telemetry
    question_history: List[Dict[str, Any]] = field(default_factory=list)  # [{qid, topic, correct, difficulty, ts}]

    @property
    def accuracy_percent(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return (self.total_correct / self.total_attempts) * 100

    def count_mastered_topics(self) -> int:
        """Count topics with 70%+ accuracy and 10+ attempts."""
        count = 0
        for topic_id in self.topics_practised:
            attempts = self.topic_attempts.get(topic_id, 0)
            correct = self.topic_correct.get(topic_id, 0)
            if attempts >= 10 and (correct / attempts) >= 0.70:
                count += 1
        self.topics_mastered_count = count
        return count

    def stats_dict(self) -> Dict[str, Any]:
        return {
            "total_attempts": self.total_attempts,
            "total_correct": self.total_correct,
            "retries_after_wrong": self.retries_after_wrong,
            "streak_longest": self.streak_longest,
            "comeback_count": self.comeback_count,
            "hints_used": self.hints_used,
            "topic_correct": dict(self.topic_correct),
            "topic_attempts": dict(self.topic_attempts),
            "accuracy_percent": self.accuracy_percent,
            "hard_correct": self.hard_correct,
            "hard_attempted": self.hard_attempted,
            "topics_practised": len(self.topics_practised),
            "total_badges": sum(1 for b in self.badges.values() if b.current_tier),
            "pattern_mastery": self._topic_accuracy("patterns_sequences"),
            "logic_mastery": self._topic_accuracy("logic_ordering"),
        }

    def _topic_accuracy(self, topic_id: str) -> float:
        attempts = self.topic_attempts.get(topic_id, 0)
        if attempts < 10:
            return 0.0
        correct = self.topic_correct.get(topic_id, 0)
        return (correct / attempts) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "xp_total": self.xp_total,
            "kiwi_coins": self.kiwi_coins,
            "gems": self.gems,
            "streak_current": self.streak_current,
            "streak_longest": self.streak_longest,
            "sessions_completed": self.sessions_completed,
            "total_attempts": self.total_attempts,
            "total_correct": self.total_correct,
            "hard_correct": self.hard_correct,
            "hard_attempted": self.hard_attempted,
            "retries_after_wrong": self.retries_after_wrong,
            "comeback_count": self.comeback_count,
            "hints_used": self.hints_used,
            "topics_practised": self.topics_practised,
            "topic_correct": self.topic_correct,
            "topic_attempts": self.topic_attempts,
            "badges": {bid: b.to_dict() for bid, b in self.badges.items()},
            "titles": self.titles,
            "avatar": self.avatar,
            "owned_items": self.owned_items,
            "learner_persona": self.learner_persona,
            "last_session_accuracy": self.last_session_accuracy,
            "last_session_struggled": self.last_session_struggled,
            "topics_mastered_count": self.topics_mastered_count,
            "lifetime_coins_earned": self.lifetime_coins_earned,
            "lifetime_gems_earned": self.lifetime_gems_earned,
            "consecutive_correct": self.consecutive_correct,
            "consecutive_wrong": self.consecutive_wrong,
            "completed_genesis": self.completed_genesis,
            "pet_name": self.pet_name,
            "days_active": self.days_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GamificationState":
        badges = {}
        for bid, bdata in data.get("badges", {}).items():
            badges[bid] = BadgeState.from_dict(bdata)
        return cls(
            user_id=data.get("user_id", ""),
            xp_total=data.get("xp_total", 0),
            kiwi_coins=data.get("kiwi_coins", 0),
            gems=data.get("gems", 5),
            streak_current=data.get("streak_current", 0),
            streak_longest=data.get("streak_longest", 0),
            sessions_completed=data.get("sessions_completed", 0),
            total_attempts=data.get("total_attempts", 0),
            total_correct=data.get("total_correct", 0),
            hard_correct=data.get("hard_correct", 0),
            hard_attempted=data.get("hard_attempted", 0),
            retries_after_wrong=data.get("retries_after_wrong", 0),
            comeback_count=data.get("comeback_count", 0),
            hints_used=data.get("hints_used", 0),
            topics_practised=data.get("topics_practised", []),
            topic_correct=data.get("topic_correct", {}),
            topic_attempts=data.get("topic_attempts", {}),
            badges=badges,
            titles=data.get("titles", []),
            avatar=data.get("avatar", dict(DEFAULT_AVATAR)),
            owned_items=data.get("owned_items", []),
            learner_persona=data.get("learner_persona", "steady_learner"),
            last_session_accuracy=data.get("last_session_accuracy", 0.0),
            last_session_struggled=data.get("last_session_struggled", False),
            topics_mastered_count=data.get("topics_mastered_count", 0),
            lifetime_coins_earned=data.get("lifetime_coins_earned", 0),
            lifetime_gems_earned=data.get("lifetime_gems_earned", 0),
            consecutive_correct=data.get("consecutive_correct", 0),
            consecutive_wrong=data.get("consecutive_wrong", 0),
            completed_genesis=data.get("completed_genesis", False),
            pet_name=data.get("pet_name", "Kiwi"),
            days_active=data.get("days_active", 0),
        )


class GamificationManager:
    """Manages gamification state with Firestore persistence — v2 economy."""

    def __init__(self):
        self._cache: Dict[str, GamificationState] = {}

    def get_state(self, user_id: str) -> GamificationState:
        if user_id in self._cache:
            return self._cache[user_id]

        state = self._load_from_firestore(user_id)
        if state is None:
            state = GamificationState(user_id=user_id)

        self._cache[user_id] = state
        return state

    def record_answer(
        self,
        user_id: str,
        topic_id: str,
        is_correct: bool,
        is_hard: bool = False,
        is_retry: bool = False,
        difficulty: int = 0,
        hints_used: int = 0,
        time_taken_seconds: float = 0.0,
        question_id: str = "",
    ) -> Dict[str, Any]:
        """Record a single answer and return any events triggered.

        Returns dict with possible keys:
            - xp_earned, coins_earned, gems_earned, reward_breakdown
            - level_up, micro_celebration
            - badge_unlocks, title_unlocks
            - persona (current learner persona)
            - child_state, next_action (from Kiwi Brain engine)
        """
        state = self.get_state(user_id)
        events: Dict[str, Any] = {}

        old_xp = state.xp_total

        # Per-question telemetry
        if question_id:
            state.question_history.append({
                "qid": question_id,
                "topic": topic_id,
                "correct": is_correct,
                "difficulty": difficulty,
                "hints": hints_used,
                "time_s": round(time_taken_seconds, 1),
                "ts": datetime.now(timezone.utc).isoformat(),
            })

        # Update stats
        state.total_attempts += 1
        if hints_used > 0:
            state.hints_used += hints_used

        # Track topic
        if topic_id not in state.topics_practised:
            state.topics_practised.append(topic_id)
        state.topic_attempts[topic_id] = state.topic_attempts.get(topic_id, 0) + 1

        # Update consecutive correct/wrong streaks
        if is_correct:
            state.consecutive_correct += 1
            state.consecutive_wrong = 0
            state.total_correct += 1
            state.topic_correct[topic_id] = state.topic_correct.get(topic_id, 0) + 1
            if is_hard:
                state.hard_correct += 1
        else:
            state.consecutive_wrong += 1
            state.consecutive_correct = 0
            if is_retry:
                state.retries_after_wrong += 1

        if is_hard:
            state.hard_attempted += 1

        # --- Per-question rewards via compute_question_reward() ---
        reward = compute_question_reward(
            is_correct=is_correct,
            difficulty=difficulty,
            hints_used=hints_used,
            consecutive_correct=state.consecutive_correct,
            is_genesis_session=not state.completed_genesis,
        )

        coin_gain = reward["coins"]
        xp_gain = reward["xp"]

        state.kiwi_coins += coin_gain
        state.lifetime_coins_earned += coin_gain
        state.xp_total += xp_gain
        events["coins_earned"] = coin_gain
        events["xp_earned"] = xp_gain
        events["reward_breakdown"] = reward["breakdown"]

        # Mastery Gems (1 per 3 correct)
        if is_correct:
            gem_gain = 1 if state.total_correct % 3 == 0 else 0
            if gem_gain > 0:
                state.gems += gem_gain
                state.lifetime_gems_earned += gem_gain
                events["gems_earned"] = gem_gain

        # --- Child state detection (Kiwi Brain) ---
        child_state = detect_child_state(
            consecutive_correct=state.consecutive_correct,
            consecutive_wrong=state.consecutive_wrong,
            is_correct=is_correct,
            time_taken_seconds=time_taken_seconds,
            hints_used=hints_used,
            completed_genesis=state.completed_genesis,
        )
        events["child_state"] = child_state

        # --- Next action engine ---
        phase = get_session_phase(state.days_active)
        next_action = decide_next_action(child_state, phase)
        events["next_action"] = next_action

        # Update mastered topics count
        state.count_mastered_topics()

        # Check level up
        level_up = check_level_up(old_xp, state.xp_total)
        if level_up:
            events["level_up"] = level_up

        # Check micro celebration
        celebration = check_micro_celebration(old_xp, state.xp_total)
        if celebration:
            events["micro_celebration"] = celebration

        # Evaluate badges
        stats = state.stats_dict()
        updated_badges, new_unlocks = evaluate_badges(stats, state.badges)
        state.badges = updated_badges
        if new_unlocks:
            events["badge_unlocks"] = new_unlocks
            for unlock in new_unlocks:
                state.kiwi_coins += unlock["coins_awarded"]
                state.gems += unlock["gems_awarded"]
                state.lifetime_coins_earned += unlock["coins_awarded"]
                state.lifetime_gems_earned += unlock["gems_awarded"]

        # Evaluate titles
        all_titles, new_titles = evaluate_titles(stats, state.titles)
        state.titles = all_titles
        if new_titles:
            events["title_unlocks"] = new_titles

        # Update learner persona
        state.learner_persona = classify_learner(
            streak_days=state.streak_current,
            sessions_completed=state.sessions_completed,
            hard_correct=state.hard_correct,
            hard_attempted=state.hard_attempted,
            comeback_count=state.comeback_count,
            accuracy_percent=state.accuracy_percent,
            topics_practised=len(state.topics_practised),
            topics_mastered=state.topics_mastered_count,
        )
        events["persona"] = state.learner_persona

        # Persist
        self._save_to_firestore(user_id, state)

        return events

    def complete_session(
        self,
        user_id: str,
        correct: int,
        total: int,
    ) -> Dict[str, Any]:
        """Record session completion with Hero's Formula bonuses.

        Returns events including coin/gem breakdown, comeback/improvement bonuses.
        """
        state = self.get_state(user_id)
        events: Dict[str, Any] = {}

        state.sessions_completed += 1
        session_accuracy = (correct / max(1, total)) * 100

        # --- Hero's Formula: Detect bonuses ---

        # Comeback Bonus: child struggled last session and came back
        is_comeback = state.last_session_struggled
        if is_comeback:
            state.comeback_count += 1

        # Improvement Bonus: accuracy improved by 10%+ from last session
        mastery_improved = (
            state.last_session_accuracy > 0
            and session_accuracy >= state.last_session_accuracy + 10
        )

        # Compute session coins with full Hero's Formula
        coin_result = compute_session_coins(
            correct=correct,
            total=total,
            streak_days=state.streak_current,
            is_hard_tier=False,  # session-level, not question-level
            is_comeback=is_comeback,
            mastery_improved=mastery_improved,
        )

        session_coins = coin_result["coins_earned"]
        state.kiwi_coins += session_coins
        state.lifetime_coins_earned += session_coins
        events["session_coins"] = coin_result

        # Compute mastery gems
        gem_result = compute_mastery_gems(
            correct=correct,
            total=total,
            accuracy_percent=session_accuracy,
            topics_mastered_count=state.topics_mastered_count,
        )

        session_gems = gem_result["gems_earned"]
        state.gems += session_gems
        state.lifetime_gems_earned += session_gems
        events["session_gems"] = gem_result

        # Perfect session XP bonus (on top of per-question XP)
        if correct == total and total >= 5:
            state.xp_total += 25
            events["perfect_bonus"] = {"xp": 25}

        # Check surprise chest
        chest = check_chest(state.sessions_completed)
        if chest:
            state.kiwi_coins += chest["coins"]
            state.gems += chest["gems"]
            state.lifetime_coins_earned += chest["coins"]
            state.lifetime_gems_earned += chest["gems"]
            events["chest"] = chest

        # Record session state for next session's Hero's Formula
        state.last_session_accuracy = session_accuracy
        state.last_session_struggled = session_accuracy < 50

        # Update mastered topics
        state.count_mastered_topics()

        # Reset consecutive streaks at session boundary
        state.consecutive_correct = 0
        state.consecutive_wrong = 0

        # Update persona
        state.learner_persona = classify_learner(
            streak_days=state.streak_current,
            sessions_completed=state.sessions_completed,
            hard_correct=state.hard_correct,
            hard_attempted=state.hard_attempted,
            comeback_count=state.comeback_count,
            accuracy_percent=state.accuracy_percent,
            topics_practised=len(state.topics_practised),
            topics_mastered=state.topics_mastered_count,
        )
        events["persona"] = state.learner_persona
        events["persona_info"] = LEARNER_PERSONAS.get(state.learner_persona, {})

        self._save_to_firestore(user_id, state)
        return events

    def purchase_item(self, user_id: str, item_id: str) -> Dict[str, Any]:
        """Purchase a regular shop item with Kiwi Coins."""
        state = self.get_state(user_id)

        if item_id in state.owned_items:
            return {"success": False, "error": "Already owned"}

        can_buy, item = can_purchase_with_coins(state.kiwi_coins, item_id)
        if not can_buy:
            return {"success": False, "error": "Not enough Kiwi Coins"}
        if item is None:
            return {"success": False, "error": "Item not found"}

        state.kiwi_coins -= item["coin_price"]
        state.owned_items.append(item_id)
        self._save_to_firestore(user_id, state)

        return {"success": True, "item": item, "coins_remaining": state.kiwi_coins}

    def unlock_legendary(self, user_id: str, item_id: str) -> Dict[str, Any]:
        """Attempt to unlock a legendary item through the Achievement Gate.

        This is NOT a purchase — it's an achievement unlock. The child
        must meet ALL gate requirements simultaneously.
        """
        state = self.get_state(user_id)

        if item_id in state.owned_items:
            return {"success": False, "error": "Already owned"}

        level = get_level(state.xp_total)["level"]
        state.count_mastered_topics()

        gate_result = check_achievement_gate(
            item_id=item_id,
            kiwi_coins=state.kiwi_coins,
            mastery_gems=state.gems,
            level=level,
            topics_mastered=state.topics_mastered_count,
            weekly_streak=state.streak_current,
        )

        if not gate_result["unlockable"]:
            return {
                "success": False,
                "error": "Achievement gate not met",
                "gate_status": gate_result,
            }

        # Deduct currencies
        legendary = LEGENDARY_ITEMS[item_id]
        state.kiwi_coins -= legendary["coin_price"]
        state.gems -= legendary["gem_price"]
        state.owned_items.append(item_id)
        self._save_to_firestore(user_id, state)

        return {
            "success": True,
            "item": gate_result["item"],
            "message": f"You've earned the {legendary['name']}! You are a true Kiwi Sovereign!",
            "coins_remaining": state.kiwi_coins,
            "gems_remaining": state.gems,
        }

    def get_legendary_status(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all legendary items with gate progress for the child."""
        state = self.get_state(user_id)
        level = get_level(state.xp_total)["level"]
        state.count_mastered_topics()

        result = []
        for item_id in LEGENDARY_ITEMS:
            gate_result = check_achievement_gate(
                item_id=item_id,
                kiwi_coins=state.kiwi_coins,
                mastery_gems=state.gems,
                level=level,
                topics_mastered=state.topics_mastered_count,
                weekly_streak=state.streak_current,
            )
            gate_result["owned"] = item_id in state.owned_items
            result.append(gate_result)

        return result

    def equip_item(self, user_id: str, slot: str, item_id: Optional[str]) -> Dict[str, Any]:
        state = self.get_state(user_id)

        if slot not in ("hat", "glasses", "outfit", "base_color", "celebration_fx"):
            return {"success": False, "error": "Invalid slot"}

        if item_id and item_id not in state.owned_items:
            if not item_id.startswith("color_") and item_id != "green":
                return {"success": False, "error": "Item not owned"}

        state.avatar[slot] = item_id
        self._save_to_firestore(user_id, state)
        return {"success": True, "avatar": state.avatar}

    def get_profile_summary(self, user_id: str) -> Dict[str, Any]:
        state = self.get_state(user_id)
        level = get_level(state.xp_total)

        earned_badges = []
        for bid, bstate in state.badges.items():
            if bstate.current_tier:
                defn = BADGE_DEFINITIONS.get(bid, {})
                earned_badges.append({
                    "badge_id": bid,
                    "name": defn.get("name", bid),
                    "emoji": defn.get("emoji", "\U0001f3c5"),
                    "tier": bstate.current_tier,
                    "progress": bstate.progress,
                })

        earned_titles = []
        for title_id in state.titles:
            for t in TITLES:
                if t["id"] == title_id:
                    earned_titles.append(t)
                    break

        persona_info = LEARNER_PERSONAS.get(state.learner_persona, {})

        return {
            "user_id": user_id,
            "level": level,
            "xp_total": state.xp_total,
            "kiwi_coins": state.kiwi_coins,
            "gems": state.gems,
            "streak_current": state.streak_current,
            "streak_longest": state.streak_longest,
            "accuracy": round(state.accuracy_percent, 1),
            "total_questions": state.total_attempts,
            "sessions_completed": state.sessions_completed,
            "badges": earned_badges,
            "badges_total": len(earned_badges),
            "titles": earned_titles,
            "avatar": state.avatar,
            "topics_practised": len(state.topics_practised),
            "topics_mastered": state.topics_mastered_count,
            "learner_persona": state.learner_persona,
            "persona_info": persona_info,
        }

    def get_parent_dashboard(self, user_id: str) -> Dict[str, Any]:
        state = self.get_state(user_id)
        level = get_level(state.xp_total)

        topic_summaries = []
        for topic_id in state.topics_practised:
            attempts = state.topic_attempts.get(topic_id, 0)
            correct = state.topic_correct.get(topic_id, 0)
            accuracy = (correct / max(1, attempts)) * 100
            topic_name = topic_id.replace("_", " ").title()
            topic_summaries.append(parent_topic_summary(topic_name, accuracy, attempts))

        topic_summaries.sort(key=lambda x: x["accuracy"], reverse=True)

        strengths = [t["topic"] for t in topic_summaries if t["status"] == "Mastered"]
        needs_practice = [t["topic"] for t in topic_summaries if t["status"] in ("Emerging", "Starting")]

        persona_info = LEARNER_PERSONAS.get(state.learner_persona, {})

        return {
            "child_name": "Your child",
            "level": level,
            "total_questions": state.total_attempts,
            "overall_accuracy": round(state.accuracy_percent, 1),
            "streak": state.streak_current,
            "sessions_completed": state.sessions_completed,
            "topics": topic_summaries,
            "strengths": strengths,
            "needs_practice": needs_practice,
            "badges_earned": sum(1 for b in state.badges.values() if b.current_tier),
            "learner_persona": state.learner_persona,
            "persona_name": persona_info.get("name", "Learner"),
            "kiwi_coins": state.kiwi_coins,
            "mastery_gems": state.gems,
        }

    # -----------------------------------------------------------------------
    # Pillar 5: Invisible Central Bank — Circulation Tracking
    # -----------------------------------------------------------------------

    def get_economy_stats(self) -> Dict[str, Any]:
        """Server-side only: aggregate economy stats for the Central Bank.

        This data is NEVER shown to children. It's used by the admin to
        decide when to vault/release legendary items.
        """
        total_coins_in_circulation = 0
        total_gems_in_circulation = 0
        legendary_owners: Dict[str, int] = {lid: 0 for lid in LEGENDARY_ITEMS}
        total_users = len(self._cache)

        for uid, state in self._cache.items():
            total_coins_in_circulation += state.kiwi_coins
            total_gems_in_circulation += state.gems
            for lid in LEGENDARY_ITEMS:
                if lid in state.owned_items:
                    legendary_owners[lid] += 1

        saturation = {}
        for lid, count in legendary_owners.items():
            saturation[lid] = {
                "owners": count,
                "saturation_pct": (count / max(1, total_users)) * 100,
                "should_vault": count / max(1, total_users) >= VAULT_SATURATION_THRESHOLD,
            }

        return {
            "total_users_cached": total_users,
            "coins_in_circulation": total_coins_in_circulation,
            "gems_in_circulation": total_gems_in_circulation,
            "avg_coins_per_user": total_coins_in_circulation / max(1, total_users),
            "avg_gems_per_user": total_gems_in_circulation / max(1, total_users),
            "legendary_saturation": saturation,
        }

    # -----------------------------------------------------------------------
    # Genesis Onboarding
    # -----------------------------------------------------------------------

    def start_genesis(self, user_id: str, pet_name: str = "Kiwi") -> Dict[str, Any]:
        """Run the genesis onboarding flow for a new child.

        Awards initial wealth, sets genesis badge, and returns the
        genesis event data for the Flutter UI to show the hatching animation.
        """
        state = self.get_state(user_id)

        if state.completed_genesis:
            return {"success": False, "error": "Genesis already completed"}

        genesis = complete_genesis(pet_name)

        state.kiwi_coins += genesis["coins"]
        state.gems += genesis["gems"]
        state.lifetime_coins_earned += genesis["coins"]
        state.lifetime_gems_earned += genesis["gems"]
        state.pet_name = pet_name
        state.completed_genesis = True

        self._save_to_firestore(user_id, state)

        return {
            "success": True,
            "pet_name": pet_name,
            "initial_coins": genesis["coins"],
            "initial_gems": genesis["gems"],
            "genesis_badge": genesis["items"][0] if genesis["items"] else "genesis_badge",
            "reward_multiplier": GENESIS_REWARD_MULTIPLIER,
            "message": genesis["message"],
        }

    # -----------------------------------------------------------------------
    # Firestore persistence
    # -----------------------------------------------------------------------

    def _load_from_firestore(self, user_id: str) -> Optional[GamificationState]:
        try:
            from app.services.firestore_service import _get_db, is_firestore_available
            if not is_firestore_available():
                return None
            db = _get_db()
            if not db:
                return None
            doc = db.collection("users").document(user_id).collection("gamification").document("state").get()
            if doc.exists:
                return GamificationState.from_dict(doc.to_dict())
            return None
        except Exception as e:
            logger.warning(f"Failed to load gamification for {user_id}: {e}")
            return None

    def _save_to_firestore(self, user_id: str, state: GamificationState) -> None:
        try:
            from app.services.firestore_service import _get_db, is_firestore_available
            if not is_firestore_available():
                return
            db = _get_db()
            if not db:
                return
            (db.collection("users").document(user_id)
             .collection("gamification").document("state")
             .set(state.to_dict(), merge=True))
        except Exception as e:
            logger.warning(f"Failed to save gamification for {user_id}: {e}")


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

gamification = GamificationManager()
