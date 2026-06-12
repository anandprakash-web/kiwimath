"""
Kiwimath Engagement Service — Leagues, Clan Wars, Rewards, Pledges.

Game theory mechanics:
    - Nash equilibrium: best-N scoring in clan wars rewards ALL members contributing
    - Loss aversion: streak system, daily calendar (skip = miss)
    - Variable ratio reinforcement: mystery box rewards are unpredictable but effort-gated
    - Social commitment: pledge system with clan visibility
    - Endowed progress: sticker album starts 10% filled (endowment effect)
    - Goal gradient: contribution bar accelerates near completion
    - Fresh start: weekly league leaderboard resets every Monday
    - Comeback mechanic: underdog boost prevents snowball dominance

Safety:
    - Mystery boxes are effort-gated (5 daily puzzles), NOT purchase-gated
    - No pay-to-win mechanics
    - ELO K-factor=32 tuned for kids (generous rating swings)
    - Soft demotion in leagues (keep 60% of points)
"""

from __future__ import annotations

import hashlib
import logging
import math
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("kiwimath.engagement")

# ---------------------------------------------------------------------------
# Constants — Leagues
# ---------------------------------------------------------------------------

LEAGUE_TIERS = [
    {"name": "bronze",    "min_points": 0,     "max_points": 499},
    {"name": "silver",    "min_points": 500,   "max_points": 1499},
    {"name": "gold",      "min_points": 1500,  "max_points": 3499},
    {"name": "platinum",  "min_points": 3500,  "max_points": 6999},
    {"name": "diamond",   "min_points": 7000,  "max_points": 14999},
    {"name": "legendary", "min_points": 15000, "max_points": 999999999},
]

SEASON_DURATION_WEEKS = 4
SOFT_DEMOTION_KEEP_RATIO = 0.60  # Keep 60% of points on season reset

# ---------------------------------------------------------------------------
# Constants — Clan Wars
# ---------------------------------------------------------------------------

ELO_DEFAULT = 1200
ELO_K_FACTOR = 32  # Generous for kids — bigger swings, faster convergence
WAR_DURATION_HOURS = 48
PUZZLES_PER_WAR = 5
COMEBACK_THRESHOLD = 0.20  # Trailing by >20% triggers boost
COMEBACK_MULTIPLIER = 1.5

# ---------------------------------------------------------------------------
# Constants — Rewards
# ---------------------------------------------------------------------------

MYSTERY_BOX_EFFORT_THRESHOLD = 5  # Must complete 5 daily puzzles

RARITY_WEIGHTS = {
    "common":    60,
    "rare":      25,
    "epic":      10,
    "legendary":  5,
}

DAILY_CALENDAR_REWARDS = [
    {"day": 1, "reward_type": "gems",          "reward_data": {"amount": 10}},
    {"day": 2, "reward_type": "sticker",       "reward_data": {"sticker": "random_common"}},
    {"day": 3, "reward_type": "gems",          "reward_data": {"amount": 25}},
    {"day": 4, "reward_type": "streak_freeze", "reward_data": {"count": 1}},
    {"day": 5, "reward_type": "gems",          "reward_data": {"amount": 50}},
    {"day": 6, "reward_type": "mystery_box",   "reward_data": {"count": 1}},
    {"day": 7, "reward_type": "gems_and_sticker", "reward_data": {"gems": 100, "sticker": "random_rare"}},
]

MYSTERY_BOX_LOOT_TABLE = {
    "common": [
        {"type": "sticker",       "data": {"rarity": "common"}},
        {"type": "bonus_xp",      "data": {"amount": 50}},
        {"type": "bonus_xp",      "data": {"amount": 100}},
    ],
    "rare": [
        {"type": "sticker",       "data": {"rarity": "rare"}},
        {"type": "avatar_item",   "data": {"category": "hat"}},
        {"type": "bonus_xp",      "data": {"amount": 250}},
    ],
    "epic": [
        {"type": "sticker",       "data": {"rarity": "epic"}},
        {"type": "avatar_item",   "data": {"category": "outfit"}},
        {"type": "streak_freeze", "data": {"count": 2}},
    ],
    "legendary": [
        {"type": "sticker",       "data": {"rarity": "legendary"}},
        {"type": "avatar_item",   "data": {"category": "legendary_outfit"}},
        {"type": "bonus_xp",      "data": {"amount": 1000}},
    ],
}


# ---------------------------------------------------------------------------
# Sticker catalog — 30 per grade, Indian themed
# ---------------------------------------------------------------------------

def _build_sticker_catalog() -> Dict[int, List[Dict[str, Any]]]:
    """Build the full sticker catalog: 30 stickers per grade (1-6).

    Themes: animals, space, food, sports, math symbols — all with Indian flair.
    Rarity distribution per grade: 12 common, 9 rare, 6 epic, 3 legendary.
    """
    catalog: Dict[int, List[Dict[str, Any]]] = {}

    # Grade 1 — "Little Explorers" (animals + nature)
    catalog[1] = [
        # Common (12)
        {"id": "g1_s01", "name": "Rangoli Star",       "theme": "math_symbols", "rarity": "common"},
        {"id": "g1_s02", "name": "Mango Slice",        "theme": "food",         "rarity": "common"},
        {"id": "g1_s03", "name": "Baby Elephant",      "theme": "animals",      "rarity": "common"},
        {"id": "g1_s04", "name": "Cricket Bat",        "theme": "sports",       "rarity": "common"},
        {"id": "g1_s05", "name": "Coconut Tree",       "theme": "food",         "rarity": "common"},
        {"id": "g1_s06", "name": "Plus Petal",         "theme": "math_symbols", "rarity": "common"},
        {"id": "g1_s07", "name": "Parrot Friend",      "theme": "animals",      "rarity": "common"},
        {"id": "g1_s08", "name": "Kite Runner",        "theme": "sports",       "rarity": "common"},
        {"id": "g1_s09", "name": "Ladoo Treat",        "theme": "food",         "rarity": "common"},
        {"id": "g1_s10", "name": "Moon Rocket",        "theme": "space",        "rarity": "common"},
        {"id": "g1_s11", "name": "Butterfly Wings",    "theme": "animals",      "rarity": "common"},
        {"id": "g1_s12", "name": "Tulsi Leaf",         "theme": "food",         "rarity": "common"},
        # Rare (9)
        {"id": "g1_s13", "name": "Peacock Feather",    "theme": "animals",      "rarity": "rare"},
        {"id": "g1_s14", "name": "Jalebi Spiral",      "theme": "food",         "rarity": "rare"},
        {"id": "g1_s15", "name": "Rocket Launch",      "theme": "space",        "rarity": "rare"},
        {"id": "g1_s16", "name": "Tiger Cub",          "theme": "animals",      "rarity": "rare"},
        {"id": "g1_s17", "name": "Badminton Birdie",   "theme": "sports",       "rarity": "rare"},
        {"id": "g1_s18", "name": "Lotus Bloom",        "theme": "animals",      "rarity": "rare"},
        {"id": "g1_s19", "name": "Samosa Triangle",    "theme": "food",         "rarity": "rare"},
        {"id": "g1_s20", "name": "Equals Bridge",      "theme": "math_symbols", "rarity": "rare"},
        {"id": "g1_s21", "name": "Star Constellation", "theme": "space",        "rarity": "rare"},
        # Epic (6)
        {"id": "g1_s22", "name": "Dancing Peacock",    "theme": "animals",      "rarity": "epic"},
        {"id": "g1_s23", "name": "Chandrayaan Rover",  "theme": "space",        "rarity": "epic"},
        {"id": "g1_s24", "name": "Infinity Loop",      "theme": "math_symbols", "rarity": "epic"},
        {"id": "g1_s25", "name": "Diwali Sparkler",    "theme": "food",         "rarity": "epic"},
        {"id": "g1_s26", "name": "Hockey Champion",    "theme": "sports",       "rarity": "epic"},
        {"id": "g1_s27", "name": "Kingfisher Flash",   "theme": "animals",      "rarity": "epic"},
        # Legendary (3)
        {"id": "g1_s28", "name": "Golden Ashoka Wheel","theme": "math_symbols", "rarity": "legendary"},
        {"id": "g1_s29", "name": "Royal Bengal Tiger",  "theme": "animals",      "rarity": "legendary"},
        {"id": "g1_s30", "name": "ISRO Satellite",     "theme": "space",        "rarity": "legendary"},
    ]

    # Grade 2 — "Curious Minds" (nature + culture)
    catalog[2] = [
        # Common (12)
        {"id": "g2_s01", "name": "Rangoli Circle",     "theme": "math_symbols", "rarity": "common"},
        {"id": "g2_s02", "name": "Banana Bunch",       "theme": "food",         "rarity": "common"},
        {"id": "g2_s03", "name": "Monkey Swing",       "theme": "animals",      "rarity": "common"},
        {"id": "g2_s04", "name": "Kabaddi Player",     "theme": "sports",       "rarity": "common"},
        {"id": "g2_s05", "name": "Chai Cup",           "theme": "food",         "rarity": "common"},
        {"id": "g2_s06", "name": "Minus Arrow",        "theme": "math_symbols", "rarity": "common"},
        {"id": "g2_s07", "name": "Squirrel Scout",     "theme": "animals",      "rarity": "common"},
        {"id": "g2_s08", "name": "Carrom Striker",     "theme": "sports",       "rarity": "common"},
        {"id": "g2_s09", "name": "Pani Puri Pop",      "theme": "food",         "rarity": "common"},
        {"id": "g2_s10", "name": "Shooting Star",      "theme": "space",        "rarity": "common"},
        {"id": "g2_s11", "name": "Frog Splash",        "theme": "animals",      "rarity": "common"},
        {"id": "g2_s12", "name": "Sugarcane Stick",    "theme": "food",         "rarity": "common"},
        # Rare (9)
        {"id": "g2_s13", "name": "Peacock Dance",      "theme": "animals",      "rarity": "rare"},
        {"id": "g2_s14", "name": "Gulab Jamun Roll",   "theme": "food",         "rarity": "rare"},
        {"id": "g2_s15", "name": "Planet Orbit",       "theme": "space",        "rarity": "rare"},
        {"id": "g2_s16", "name": "Langur Leap",        "theme": "animals",      "rarity": "rare"},
        {"id": "g2_s17", "name": "Kho Kho Sprint",     "theme": "sports",       "rarity": "rare"},
        {"id": "g2_s18", "name": "Jasmine Garland",    "theme": "animals",      "rarity": "rare"},
        {"id": "g2_s19", "name": "Dosa Flip",          "theme": "food",         "rarity": "rare"},
        {"id": "g2_s20", "name": "Triangle Ruler",     "theme": "math_symbols", "rarity": "rare"},
        {"id": "g2_s21", "name": "Milky Way Swirl",    "theme": "space",        "rarity": "rare"},
        # Epic (6)
        {"id": "g2_s22", "name": "Flamingo Flock",     "theme": "animals",      "rarity": "epic"},
        {"id": "g2_s23", "name": "Mars Mission",       "theme": "space",        "rarity": "epic"},
        {"id": "g2_s24", "name": "Pi Spiral",          "theme": "math_symbols", "rarity": "epic"},
        {"id": "g2_s25", "name": "Holi Splash",        "theme": "food",         "rarity": "epic"},
        {"id": "g2_s26", "name": "Archery Arrow",      "theme": "sports",       "rarity": "epic"},
        {"id": "g2_s27", "name": "Hornbill Hero",      "theme": "animals",      "rarity": "epic"},
        # Legendary (3)
        {"id": "g2_s28", "name": "Golden Kolam",       "theme": "math_symbols", "rarity": "legendary"},
        {"id": "g2_s29", "name": "Snow Leopard",       "theme": "animals",      "rarity": "legendary"},
        {"id": "g2_s30", "name": "Mangalyaan Orbiter", "theme": "space",        "rarity": "legendary"},
    ]

    # Grade 3 — "Number Ninjas" (math-forward + adventure)
    catalog[3] = [
        # Common (12)
        {"id": "g3_s01", "name": "Rangoli Diamond",    "theme": "math_symbols", "rarity": "common"},
        {"id": "g3_s02", "name": "Pomegranate Burst",  "theme": "food",         "rarity": "common"},
        {"id": "g3_s03", "name": "Cobra Guard",        "theme": "animals",      "rarity": "common"},
        {"id": "g3_s04", "name": "Football Kick",      "theme": "sports",       "rarity": "common"},
        {"id": "g3_s05", "name": "Biryani Bowl",       "theme": "food",         "rarity": "common"},
        {"id": "g3_s06", "name": "Multiply Cross",     "theme": "math_symbols", "rarity": "common"},
        {"id": "g3_s07", "name": "Owl Scholar",        "theme": "animals",      "rarity": "common"},
        {"id": "g3_s08", "name": "Yoga Pose",          "theme": "sports",       "rarity": "common"},
        {"id": "g3_s09", "name": "Pav Bhaji Plate",    "theme": "food",         "rarity": "common"},
        {"id": "g3_s10", "name": "Asteroid Belt",      "theme": "space",        "rarity": "common"},
        {"id": "g3_s11", "name": "Chameleon Shift",    "theme": "animals",      "rarity": "common"},
        {"id": "g3_s12", "name": "Jackfruit Giant",    "theme": "food",         "rarity": "common"},
        # Rare (9)
        {"id": "g3_s13", "name": "Gharial Grin",       "theme": "animals",      "rarity": "rare"},
        {"id": "g3_s14", "name": "Rasmalai Cloud",     "theme": "food",         "rarity": "rare"},
        {"id": "g3_s15", "name": "Space Station",      "theme": "space",        "rarity": "rare"},
        {"id": "g3_s16", "name": "Red Panda Roll",     "theme": "animals",      "rarity": "rare"},
        {"id": "g3_s17", "name": "Chess Knight",       "theme": "sports",       "rarity": "rare"},
        {"id": "g3_s18", "name": "Marigold Crown",     "theme": "animals",      "rarity": "rare"},
        {"id": "g3_s19", "name": "Chole Bhature",      "theme": "food",         "rarity": "rare"},
        {"id": "g3_s20", "name": "Fraction Bar",       "theme": "math_symbols", "rarity": "rare"},
        {"id": "g3_s21", "name": "Black Hole Vortex",  "theme": "space",        "rarity": "rare"},
        # Epic (6)
        {"id": "g3_s22", "name": "King Cobra Hood",    "theme": "animals",      "rarity": "epic"},
        {"id": "g3_s23", "name": "Gaganyaan Capsule",  "theme": "space",        "rarity": "epic"},
        {"id": "g3_s24", "name": "Golden Ratio Shell", "theme": "math_symbols", "rarity": "epic"},
        {"id": "g3_s25", "name": "Onam Feast",         "theme": "food",         "rarity": "epic"},
        {"id": "g3_s26", "name": "Mallakhamba Pole",   "theme": "sports",       "rarity": "epic"},
        {"id": "g3_s27", "name": "Nilgiri Tahr",       "theme": "animals",      "rarity": "epic"},
        # Legendary (3)
        {"id": "g3_s28", "name": "Golden Abacus",      "theme": "math_symbols", "rarity": "legendary"},
        {"id": "g3_s29", "name": "Asiatic Lion",       "theme": "animals",      "rarity": "legendary"},
        {"id": "g3_s30", "name": "Hubble Nebula",      "theme": "space",        "rarity": "legendary"},
    ]

    # Grade 4 — "Logic Legends" (strategy + culture)
    catalog[4] = [
        # Common (12)
        {"id": "g4_s01", "name": "Rangoli Hexagon",    "theme": "math_symbols", "rarity": "common"},
        {"id": "g4_s02", "name": "Masala Dosa Roll",   "theme": "food",         "rarity": "common"},
        {"id": "g4_s03", "name": "Mongoose Dash",      "theme": "animals",      "rarity": "common"},
        {"id": "g4_s04", "name": "Table Tennis Spin",  "theme": "sports",       "rarity": "common"},
        {"id": "g4_s05", "name": "Kulfi Cone",         "theme": "food",         "rarity": "common"},
        {"id": "g4_s06", "name": "Division Shield",    "theme": "math_symbols", "rarity": "common"},
        {"id": "g4_s07", "name": "Dolphin Dive",       "theme": "animals",      "rarity": "common"},
        {"id": "g4_s08", "name": "Silambam Staff",     "theme": "sports",       "rarity": "common"},
        {"id": "g4_s09", "name": "Paneer Tikka",       "theme": "food",         "rarity": "common"},
        {"id": "g4_s10", "name": "Solar Flare",        "theme": "space",        "rarity": "common"},
        {"id": "g4_s11", "name": "Myna Chatter",       "theme": "animals",      "rarity": "common"},
        {"id": "g4_s12", "name": "Tamarind Twist",     "theme": "food",         "rarity": "common"},
        # Rare (9)
        {"id": "g4_s13", "name": "Pangolin Shield",    "theme": "animals",      "rarity": "rare"},
        {"id": "g4_s14", "name": "Rasgulla Sphere",    "theme": "food",         "rarity": "rare"},
        {"id": "g4_s15", "name": "Lunar Eclipse",      "theme": "space",        "rarity": "rare"},
        {"id": "g4_s16", "name": "Sloth Bear Hug",     "theme": "animals",      "rarity": "rare"},
        {"id": "g4_s17", "name": "Wrestling Akhada",   "theme": "sports",       "rarity": "rare"},
        {"id": "g4_s18", "name": "Hibiscus Bloom",     "theme": "animals",      "rarity": "rare"},
        {"id": "g4_s19", "name": "Vada Pav Crunch",    "theme": "food",         "rarity": "rare"},
        {"id": "g4_s20", "name": "Percentage Gem",     "theme": "math_symbols", "rarity": "rare"},
        {"id": "g4_s21", "name": "Comet Trail",        "theme": "space",        "rarity": "rare"},
        # Epic (6)
        {"id": "g4_s22", "name": "Indian Bison",       "theme": "animals",      "rarity": "epic"},
        {"id": "g4_s23", "name": "Aditya Solar Probe", "theme": "space",        "rarity": "epic"},
        {"id": "g4_s24", "name": "Tessellation Art",   "theme": "math_symbols", "rarity": "epic"},
        {"id": "g4_s25", "name": "Pongal Harvest",     "theme": "food",         "rarity": "epic"},
        {"id": "g4_s26", "name": "Polo Champion",      "theme": "sports",       "rarity": "epic"},
        {"id": "g4_s27", "name": "Malabar Civet",      "theme": "animals",      "rarity": "epic"},
        # Legendary (3)
        {"id": "g4_s28", "name": "Golden Yantra",      "theme": "math_symbols", "rarity": "legendary"},
        {"id": "g4_s29", "name": "Indian Rhinoceros",  "theme": "animals",      "rarity": "legendary"},
        {"id": "g4_s30", "name": "Chandrayaan Lander", "theme": "space",        "rarity": "legendary"},
    ]

    # Grade 5 — "Algebra Aces" (advanced + global)
    catalog[5] = [
        # Common (12)
        {"id": "g5_s01", "name": "Rangoli Mandala",    "theme": "math_symbols", "rarity": "common"},
        {"id": "g5_s02", "name": "Idli Stack",         "theme": "food",         "rarity": "common"},
        {"id": "g5_s03", "name": "Crane Glide",        "theme": "animals",      "rarity": "common"},
        {"id": "g5_s04", "name": "Boxing Glove",       "theme": "sports",       "rarity": "common"},
        {"id": "g5_s05", "name": "Lassi Glass",        "theme": "food",         "rarity": "common"},
        {"id": "g5_s06", "name": "Variable X",         "theme": "math_symbols", "rarity": "common"},
        {"id": "g5_s07", "name": "Turtle Paddle",      "theme": "animals",      "rarity": "common"},
        {"id": "g5_s08", "name": "Rowing Crew",        "theme": "sports",       "rarity": "common"},
        {"id": "g5_s09", "name": "Chaat Plate",        "theme": "food",         "rarity": "common"},
        {"id": "g5_s10", "name": "Supernova Blast",    "theme": "space",        "rarity": "common"},
        {"id": "g5_s11", "name": "Macaw Call",         "theme": "animals",      "rarity": "common"},
        {"id": "g5_s12", "name": "Litchi Bunch",       "theme": "food",         "rarity": "common"},
        # Rare (9)
        {"id": "g5_s13", "name": "Gharial Swimmer",    "theme": "animals",      "rarity": "rare"},
        {"id": "g5_s14", "name": "Mysore Pak",         "theme": "food",         "rarity": "rare"},
        {"id": "g5_s15", "name": "Neutron Star",       "theme": "space",        "rarity": "rare"},
        {"id": "g5_s16", "name": "Clouded Leopard",    "theme": "animals",      "rarity": "rare"},
        {"id": "g5_s17", "name": "Fencing Sabre",      "theme": "sports",       "rarity": "rare"},
        {"id": "g5_s18", "name": "Banyan Roots",       "theme": "animals",      "rarity": "rare"},
        {"id": "g5_s19", "name": "Thali Feast",        "theme": "food",         "rarity": "rare"},
        {"id": "g5_s20", "name": "Square Root Tree",   "theme": "math_symbols", "rarity": "rare"},
        {"id": "g5_s21", "name": "Galaxy Spiral",      "theme": "space",        "rarity": "rare"},
        # Epic (6)
        {"id": "g5_s22", "name": "Indian Elephant",    "theme": "animals",      "rarity": "epic"},
        {"id": "g5_s23", "name": "NavIC Satellite",    "theme": "space",        "rarity": "epic"},
        {"id": "g5_s24", "name": "Euler Identity",     "theme": "math_symbols", "rarity": "epic"},
        {"id": "g5_s25", "name": "Baisakhi Dance",     "theme": "food",         "rarity": "epic"},
        {"id": "g5_s26", "name": "Weightlifting Gold",  "theme": "sports",       "rarity": "epic"},
        {"id": "g5_s27", "name": "Lion Tailed Macaque", "theme": "animals",      "rarity": "epic"},
        # Legendary (3)
        {"id": "g5_s28", "name": "Golden Fibonacci",   "theme": "math_symbols", "rarity": "legendary"},
        {"id": "g5_s29", "name": "Bengal Florican",    "theme": "animals",      "rarity": "legendary"},
        {"id": "g5_s30", "name": "Voyager Probe",      "theme": "space",        "rarity": "legendary"},
    ]

    # Grade 6 — "Math Masters" (mastery + prestige)
    catalog[6] = [
        # Common (12)
        {"id": "g6_s01", "name": "Rangoli Fractal",    "theme": "math_symbols", "rarity": "common"},
        {"id": "g6_s02", "name": "Paratha Layers",     "theme": "food",         "rarity": "common"},
        {"id": "g6_s03", "name": "Eagle Soar",         "theme": "animals",      "rarity": "common"},
        {"id": "g6_s04", "name": "Javelin Throw",      "theme": "sports",       "rarity": "common"},
        {"id": "g6_s05", "name": "Rabri Swirl",        "theme": "food",         "rarity": "common"},
        {"id": "g6_s06", "name": "Sigma Sum",          "theme": "math_symbols", "rarity": "common"},
        {"id": "g6_s07", "name": "Whale Shark",        "theme": "animals",      "rarity": "common"},
        {"id": "g6_s08", "name": "Sprint Relay",       "theme": "sports",       "rarity": "common"},
        {"id": "g6_s09", "name": "Pista Barfi",        "theme": "food",         "rarity": "common"},
        {"id": "g6_s10", "name": "Pulsar Pulse",       "theme": "space",        "rarity": "common"},
        {"id": "g6_s11", "name": "Gharial Glide",      "theme": "animals",      "rarity": "common"},
        {"id": "g6_s12", "name": "Tender Coconut",     "theme": "food",         "rarity": "common"},
        # Rare (9)
        {"id": "g6_s13", "name": "Markhor Spiral",     "theme": "animals",      "rarity": "rare"},
        {"id": "g6_s14", "name": "Kaju Katli Gold",    "theme": "food",         "rarity": "rare"},
        {"id": "g6_s15", "name": "Wormhole Gate",      "theme": "space",        "rarity": "rare"},
        {"id": "g6_s16", "name": "Olive Ridley",       "theme": "animals",      "rarity": "rare"},
        {"id": "g6_s17", "name": "Kabaddi Raid",       "theme": "sports",       "rarity": "rare"},
        {"id": "g6_s18", "name": "Neem Guardian",      "theme": "animals",      "rarity": "rare"},
        {"id": "g6_s19", "name": "Filter Coffee",      "theme": "food",         "rarity": "rare"},
        {"id": "g6_s20", "name": "Coordinate Axis",    "theme": "math_symbols", "rarity": "rare"},
        {"id": "g6_s21", "name": "Quasar Beam",        "theme": "space",        "rarity": "rare"},
        # Epic (6)
        {"id": "g6_s22", "name": "Mugger Crocodile",   "theme": "animals",      "rarity": "epic"},
        {"id": "g6_s23", "name": "PSLV Rocket",        "theme": "space",        "rarity": "epic"},
        {"id": "g6_s24", "name": "Ramanujan Magic",    "theme": "math_symbols", "rarity": "epic"},
        {"id": "g6_s25", "name": "Durga Puja Lights",  "theme": "food",         "rarity": "epic"},
        {"id": "g6_s26", "name": "Long Jump Record",   "theme": "sports",       "rarity": "epic"},
        {"id": "g6_s27", "name": "Gangetic Dolphin",   "theme": "animals",      "rarity": "epic"},
        # Legendary (3)
        {"id": "g6_s28", "name": "Golden Infinity",    "theme": "math_symbols", "rarity": "legendary"},
        {"id": "g6_s29", "name": "Indian Pangolin",    "theme": "animals",      "rarity": "legendary"},
        {"id": "g6_s30", "name": "GSLV Mk III",       "theme": "space",        "rarity": "legendary"},
    ]

    return catalog


STICKER_CATALOG = _build_sticker_catalog()
STICKERS_PER_GRADE = 30
ENDOWMENT_RATIO = 0.10  # Start album 10% filled


# ---------------------------------------------------------------------------
# League helpers
# ---------------------------------------------------------------------------

def get_league_tier(points: int) -> Dict[str, Any]:
    """Determine league tier from league points."""
    for tier in reversed(LEAGUE_TIERS):
        if points >= tier["min_points"]:
            return {
                "league": tier["name"],
                "promotion_threshold": tier["max_points"] + 1 if tier["name"] != "legendary" else None,
                "demotion_threshold": tier["min_points"] if tier["name"] != "bronze" else None,
            }
    return {
        "league": "bronze",
        "promotion_threshold": 500,
        "demotion_threshold": None,
    }


def get_season_info() -> Dict[str, Any]:
    """Get current season number and end time.

    Seasons are 4-week windows anchored to a fixed epoch (2026-01-05, a Monday).
    """
    epoch = datetime(2026, 1, 5, 0, 0, 0, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days_since = (now - epoch).days
    season_number = (days_since // (SEASON_DURATION_WEEKS * 7)) + 1
    season_start = epoch + timedelta(days=(season_number - 1) * SEASON_DURATION_WEEKS * 7)
    season_end = season_start + timedelta(weeks=SEASON_DURATION_WEEKS)
    return {
        "season_number": season_number,
        "season_ends_at": season_end.isoformat(),
        "season_start": season_start.isoformat(),
    }


def apply_season_reset(league_points: int) -> int:
    """Soft demotion: keep 60% of points on season reset."""
    return int(league_points * SOFT_DEMOTION_KEEP_RATIO)


def rank_players_in_league(
    players: List[Dict[str, Any]],
    league_name: str,
) -> List[Dict[str, Any]]:
    """Rank all players in a specific league tier by points descending."""
    league_players = [
        p for p in players
        if get_league_tier(p.get("league_points", 0))["league"] == league_name
    ]
    league_players.sort(key=lambda p: p.get("league_points", 0), reverse=True)
    for i, p in enumerate(league_players):
        p["rank_in_league"] = i + 1
    return league_players


# ---------------------------------------------------------------------------
# ELO rating
# ---------------------------------------------------------------------------

def compute_expected_score(rating_a: float, rating_b: float) -> float:
    """Expected win probability for player A."""
    return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400.0))


def update_elo(
    rating: int,
    expected: float,
    actual: float,
    k: int = ELO_K_FACTOR,
) -> int:
    """Update ELO rating. actual: 1.0=win, 0.5=draw, 0.0=loss."""
    return max(100, round(rating + k * (actual - expected)))


# ---------------------------------------------------------------------------
# Clan war matchmaking
# ---------------------------------------------------------------------------

ELO_MATCH_WINDOW = 200  # Match clans within +-200 ELO

def find_war_opponent(
    clan_id: str,
    clan_elo: int,
    clan_grade: int,
    all_clans: Dict[str, Dict[str, Any]],
) -> Optional[str]:
    """Find a suitable opponent: same grade, within ELO_MATCH_WINDOW.

    Returns opponent clan_id or None if no match found.
    """
    candidates = []
    for cid, clan in all_clans.items():
        if cid == clan_id:
            continue
        if clan.get("grade") != clan_grade:
            continue
        if clan.get("status") != "active":
            continue
        their_elo = clan.get("war_elo", ELO_DEFAULT)
        if abs(their_elo - clan_elo) <= ELO_MATCH_WINDOW:
            candidates.append((cid, abs(their_elo - clan_elo)))

    if not candidates:
        return None

    # Pick closest ELO match, break ties randomly
    candidates.sort(key=lambda x: (x[1], random.random()))
    return candidates[0][0]


# ---------------------------------------------------------------------------
# Comeback / underdog boost
# ---------------------------------------------------------------------------

def compute_comeback_boost(our_score: int, their_score: int) -> float:
    """Compute comeback multiplier.

    If trailing by >20%, apply 1.5x boost. Otherwise 1.0x.
    Prevents snowball dominance — game theory comeback mechanic.
    """
    if their_score == 0:
        return 1.0
    deficit_ratio = (their_score - our_score) / max(1, their_score)
    if deficit_ratio > COMEBACK_THRESHOLD:
        return COMEBACK_MULTIPLIER
    return 1.0


# ---------------------------------------------------------------------------
# War scoring
# ---------------------------------------------------------------------------

def compute_war_score(
    member_scores: List[int],
    member_count: int,
) -> int:
    """Best-N scoring: only top N scores count.

    N = min(member_count, 10). Nash equilibrium: optimal strategy
    requires ALL members to contribute since you don't know who
    will have the top scores.
    """
    n = min(member_count, 10)
    sorted_scores = sorted(member_scores, reverse=True)
    return sum(sorted_scores[:n])


def compute_puzzle_points(
    correct: bool,
    time_taken: int,
    comeback_boost: float,
) -> int:
    """Score a single puzzle submission in a clan war.

    Base: 100 points for correct answer.
    Speed bonus: up to 50 extra points for fast answers (< 30s).
    Comeback multiplier applied on top.
    """
    if not correct:
        return 0
    base = 100
    speed_bonus = max(0, 50 - (time_taken // 6))  # 0-50 bonus for under 5min
    raw = base + speed_bonus
    return int(raw * comeback_boost)


# ---------------------------------------------------------------------------
# Reward generation — variable ratio reinforcement
# ---------------------------------------------------------------------------

def roll_rarity() -> str:
    """Roll a rarity using weighted random (variable ratio reinforcement).

    60% common, 25% rare, 10% epic, 5% legendary.
    Effort-gated, NOT purchase-gated — ethical engagement.
    """
    roll = random.randint(1, 100)
    if roll <= 5:
        return "legendary"
    elif roll <= 15:
        return "epic"
    elif roll <= 40:
        return "rare"
    else:
        return "common"


def generate_mystery_box_reward(grade: int) -> Dict[str, Any]:
    """Open a mystery box and generate a reward.

    Uses variable ratio reinforcement — unpredictable but effort-gated.
    """
    rarity = roll_rarity()
    loot_options = MYSTERY_BOX_LOOT_TABLE[rarity]
    chosen = random.choice(loot_options)

    reward: Dict[str, Any] = {
        "reward_type": chosen["type"],
        "reward_data": dict(chosen["data"]),
        "rarity": rarity,
    }

    # If sticker, pick a specific one from the grade catalog
    if chosen["type"] == "sticker":
        sticker = pick_random_sticker(grade, rarity)
        if sticker:
            reward["reward_data"]["sticker_id"] = sticker["id"]
            reward["reward_data"]["sticker_name"] = sticker["name"]

    return reward


def pick_random_sticker(grade: int, rarity: str) -> Optional[Dict[str, Any]]:
    """Pick a random sticker of given rarity from the grade catalog."""
    grade_stickers = STICKER_CATALOG.get(grade, [])
    matching = [s for s in grade_stickers if s["rarity"] == rarity]
    if not matching:
        return None
    return random.choice(matching)


# ---------------------------------------------------------------------------
# Sticker album — endowed progress effect
# ---------------------------------------------------------------------------

def create_starter_album(grade: int) -> List[str]:
    """Create a starter album with 10% pre-filled (endowment effect).

    Kids feel invested immediately when they see progress.
    """
    grade_stickers = STICKER_CATALOG.get(grade, [])
    if not grade_stickers:
        return []

    starter_count = max(1, int(len(grade_stickers) * ENDOWMENT_RATIO))
    # Give common stickers as starters
    commons = [s for s in grade_stickers if s["rarity"] == "common"]
    starters = random.sample(commons, min(starter_count, len(commons)))
    return [s["id"] for s in starters]


# ---------------------------------------------------------------------------
# Daily calendar
# ---------------------------------------------------------------------------

def get_daily_calendar_reward(day_number: int) -> Dict[str, Any]:
    """Get the reward for a specific day in the 7-day cycle.

    Loss aversion: missing a day skips that slot — no backfill.
    """
    idx = (day_number - 1) % 7
    return DAILY_CALENDAR_REWARDS[idx]


def get_daily_calendar_grid(
    claimed_days: List[int],
    current_cycle_start: int,
) -> List[Dict[str, Any]]:
    """Build a 7-day calendar grid showing claimed/unclaimed rewards."""
    grid = []
    for day in range(1, 8):
        reward = DAILY_CALENDAR_REWARDS[day - 1]
        absolute_day = current_cycle_start + day
        grid.append({
            "day": day,
            "reward_type": reward["reward_type"],
            "reward_preview": reward["reward_data"],
            "claimed": absolute_day in claimed_days,
            "available": day == len([d for d in claimed_days if d >= current_cycle_start]) + 1,
        })
    return grid


# ---------------------------------------------------------------------------
# Goal gradient — contribution bar acceleration
# ---------------------------------------------------------------------------

def compute_contribution_display(
    current: int,
    target: int,
) -> Dict[str, Any]:
    """Compute contribution bar with goal gradient acceleration.

    Near completion, the visual bar "stretches" to feel faster —
    psychological momentum effect.
    """
    if target <= 0:
        return {"raw_progress": 1.0, "display_progress": 1.0, "remaining": 0}

    raw = min(1.0, current / target)
    # Goal gradient: accelerate visual progress in final 30%
    if raw >= 0.7:
        overshoot = (raw - 0.7) / 0.3  # 0.0 to 1.0 in the last 30%
        display = 0.7 + (overshoot ** 0.7) * 0.3  # Faster visual curve
    else:
        display = raw

    return {
        "raw_progress": round(raw, 4),
        "display_progress": round(display, 4),
        "remaining": max(0, target - current),
    }


# ---------------------------------------------------------------------------
# Pledge tracking
# ---------------------------------------------------------------------------

def create_pledge(
    uid: str,
    target_puzzles: int,
    duration_days: int,
) -> Dict[str, Any]:
    """Create a commitment pledge visible to clanmates.

    Social commitment device — public pledges increase follow-through.
    """
    now = datetime.now(timezone.utc)
    return {
        "uid": uid,
        "target_puzzles_per_day": min(5, max(1, target_puzzles)),
        "duration_days": duration_days,
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=duration_days)).isoformat(),
        "days_completed": 0,
        "current_streak": 0,
        "active": True,
        "created_at": now.isoformat(),
    }


def check_pledge_progress(
    pledge: Dict[str, Any],
    puzzles_today: int,
) -> Dict[str, Any]:
    """Check if today's pledge target is met."""
    target = pledge.get("target_puzzles_per_day", 1)
    met = puzzles_today >= target
    return {
        "target": target,
        "current": puzzles_today,
        "met_today": met,
        "streak": pledge.get("current_streak", 0) + (1 if met else 0),
    }


# ---------------------------------------------------------------------------
# Age-tiered reward filtering
# ---------------------------------------------------------------------------

def get_age_tier(grade: int) -> str:
    """Determine age tier for reward filtering.

    G1-2: stickers (visual, collectible)
    G3-4: mystery boxes (surprise element)
    G5-6: badges (achievement-oriented)
    """
    if grade <= 2:
        return "stickers"
    elif grade <= 4:
        return "mystery_boxes"
    else:
        return "badges"


logger.info(
    "Engagement service loaded — %d league tiers, %d sticker grades, ELO K=%d",
    len(LEAGUE_TIERS),
    len(STICKER_CATALOG),
    ELO_K_FACTOR,
)
