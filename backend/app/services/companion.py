"""
Kiwimath Companion System v1
============================
Data models, summon resolver, asset pipeline, and telemetry for the
5-character companion cast. v1 ships Kiwi only; other 4 are gated by
ship_in_version and fall back to chosen_primary.

Architecture: client-side resolver (pure function) with server-side
config delivery + telemetry ingestion. This module is the source of
truth — Flutter mirrors these models in Dart.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enums ─────────────────────────────────────────────────────────────

class CompanionId(str, Enum):
    KIWI = "kiwi"
    MAU = "mau"
    LUMI = "lumi"
    PICO = "pico"
    HEDGE = "hedge"


class Emotion(str, Enum):
    NEUTRAL = "neutral"
    THINKING = "thinking"
    HAPPY = "happy"
    ENCOURAGING = "encouraging"
    CELEBRATING = "celebrating"
    WAVING = "waving"
    READING = "reading"


class Surface(str, Enum):
    ONBOARDING_STEP1 = "onboarding_wizard_step1"
    ONBOARDING_STEP2 = "onboarding_wizard_step2_picker"
    HOME_NODE_PEEK = "home_recommended_node_peek"
    HOME_ADVENTURE = "home_today_adventure_card"
    LESSON_FRAMING = "lesson_problem_framing"
    LESSON_HINT1 = "lesson_hint_first"
    LESSON_HINT2 = "lesson_hint_second"
    LESSON_WRONG = "lesson_wrong_answer"
    LESSON_RETRY = "lesson_second_attempt"
    LESSON_MULTI = "lesson_multi_step"
    LESSON_MASTERY = "lesson_mastery_moment"
    HABITAT = "habitat_tab"
    REGION_CEREMONY = "region_completion_ceremony"
    GRADE_CEREMONY = "grade_promotion_ceremony"
    IDLE_INACTIVE = "idle_inactive"


class AgeTier(str, Enum):
    K2 = "k2"
    MIDDLE = "middle"
    SENIOR = "senior"


class DismissReason(str, Enum):
    AUTO_FADE = "auto_fade"
    KID_DISMISSED = "kid_dismissed"
    SURFACE_CHANGED = "surface_changed"
    DEEP_THINK_RETREAT = "deep_think_retreat"


# ── Cast definitions ──────────────────────────────────────────────────

@dataclass(frozen=True)
class Companion:
    id: CompanionId
    name: str
    region: str
    role: str
    habitat_region_id: Optional[str]
    signature_color: str          # hex
    signature_color_soft: str
    signature_color_text: str
    is_default: bool
    is_visitor: bool
    ship_in_version: int

CAST: Dict[CompanionId, Companion] = {
    CompanionId.KIWI: Companion(
        id=CompanionId.KIWI, name="Kiwi", region="pacific_oceania",
        role="curious_explorer", habitat_region_id="number_island",
        signature_color="#16A34A", signature_color_soft="#D1FAE5",
        signature_color_text="#065F46", is_default=True, is_visitor=False,
        ship_in_version=1,
    ),
    CompanionId.MAU: Companion(
        id=CompanionId.MAU, name="Mau", region="east_africa",
        role="careful_checker", habitat_region_id="measure_mountain",
        signature_color="#D97706", signature_color_soft="#FEF3C7",
        signature_color_text="#92400E", is_default=False, is_visitor=False,
        ship_in_version=2,
    ),
    CompanionId.LUMI: Companion(
        id=CompanionId.LUMI, name="Lumi", region="himalayas_asia",
        role="quiet_thinker", habitat_region_id="pattern_cave",
        signature_color="#7C3AED", signature_color_soft="#EDE9FE",
        signature_color_text="#5B21B6", is_default=False, is_visitor=False,
        ship_in_version=2,
    ),
    CompanionId.PICO: Companion(
        id=CompanionId.PICO, name="Pico", region="andes_americas",
        role="spark", habitat_region_id=None,
        signature_color="#0891B2", signature_color_soft="#CFFAFE",
        signature_color_text="#155E75", is_default=False, is_visitor=True,
        ship_in_version=2,
    ),
    CompanionId.HEDGE: Companion(
        id=CompanionId.HEDGE, name="Hedge", region="europe",
        role="organiser", habitat_region_id="shape_forest",
        signature_color="#EA580C", signature_color_soft="#FFF7ED",
        signature_color_text="#9A3412", is_default=False, is_visitor=False,
        ship_in_version=2,
    ),
}


# ── User state ────────────────────────────────────────────────────────

@dataclass
class UserCompanionState:
    chosen_primary: CompanionId = CompanionId.KIWI
    chosen_at: float = 0.0
    age_tier: AgeTier = AgeTier.K2
    audio_enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "chosen_primary_companion_id": self.chosen_primary.value,
            "chosen_at": self.chosen_at,
            "age_tier": self.age_tier.value,
            "audio_enabled": self.audio_enabled,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "UserCompanionState":
        return cls(
            chosen_primary=CompanionId(d.get("chosen_primary_companion_id", "kiwi")),
            chosen_at=d.get("chosen_at", 0.0),
            age_tier=AgeTier(d.get("age_tier", "k2")),
            audio_enabled=d.get("audio_enabled", True),
        )


# ── Summon request / response ────────────────────────────────────────

@dataclass
class SummonRequest:
    surface: Surface
    user_state: UserCompanionState
    lesson_id: Optional[str] = None
    problem_steps_required: int = 1
    pico_appearances_in_lesson: int = 0
    last_kid_action_ms_ago: int = 0
    kid_typing: bool = False
    current_app_version: int = 1


@dataclass
class SummonResponse:
    primary_id: CompanionId
    primary_emotion: Emotion
    secondary_id: Optional[CompanionId] = None
    secondary_emotion: Optional[Emotion] = None
    asset_paths: Dict[str, str] = field(default_factory=dict)
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    show_all_five: bool = False

    def to_dict(self) -> dict:
        d = {
            "primary_companion_id": self.primary_id.value,
            "primary_emotion": self.primary_emotion.value,
            "asset_paths": self.asset_paths,
            "fallback_used": self.fallback_used,
            "show_all_five": self.show_all_five,
        }
        if self.secondary_id:
            d["secondary_companion_id"] = self.secondary_id.value
            d["secondary_emotion"] = self.secondary_emotion.value if self.secondary_emotion else None
        if self.fallback_reason:
            d["fallback_reason"] = self.fallback_reason
        return d


# ── Default emotions per surface ──────────────────────────────────────

SURFACE_EMOTIONS: Dict[Surface, Emotion] = {
    Surface.ONBOARDING_STEP1: Emotion.WAVING,
    Surface.ONBOARDING_STEP2: Emotion.WAVING,
    Surface.HOME_NODE_PEEK: Emotion.NEUTRAL,
    Surface.HOME_ADVENTURE: Emotion.HAPPY,
    Surface.LESSON_FRAMING: Emotion.READING,
    Surface.LESSON_HINT1: Emotion.THINKING,
    Surface.LESSON_HINT2: Emotion.THINKING,
    Surface.LESSON_WRONG: Emotion.ENCOURAGING,
    Surface.LESSON_RETRY: Emotion.ENCOURAGING,
    Surface.LESSON_MULTI: Emotion.THINKING,
    Surface.LESSON_MASTERY: Emotion.CELEBRATING,
    Surface.HABITAT: Emotion.NEUTRAL,
    Surface.REGION_CEREMONY: Emotion.CELEBRATING,
    Surface.GRADE_CEREMONY: Emotion.CELEBRATING,
    Surface.IDLE_INACTIVE: Emotion.NEUTRAL,
}


# ── Asset path builder ────────────────────────────────────────────────

CDN_BASE = "/assets/companions"

def build_asset_paths(companion_id: CompanionId, age_tier: AgeTier,
                      emotion: Emotion) -> Dict[str, str]:
    cid = companion_id.value
    tier = age_tier.value
    return {
        "pose_svg": f"{CDN_BASE}/{cid}/{tier}/{emotion.value}.svg",
        "silhouette_svg": f"{CDN_BASE}/{cid}/silhouette.svg",
        "idle_blink": f"{CDN_BASE}/{cid}/{tier}/animations/idle/blink.riv",
        "idle_breath": f"{CDN_BASE}/{cid}/{tier}/animations/idle/breath.riv",
    }


def build_prefetch_manifest(companion_id: CompanionId,
                            age_tier: AgeTier) -> List[str]:
    """All assets to prefetch on session start for the chosen primary."""
    cid = companion_id.value
    tier = age_tier.value
    paths = []
    # All 7 emotion poses
    for emo in Emotion:
        paths.append(f"{CDN_BASE}/{cid}/{tier}/{emo.value}.svg")
    # Silhouette fallback
    paths.append(f"{CDN_BASE}/{cid}/silhouette.svg")
    # Idle animations
    for behavior in ["blink", "breath", "look_around", "character_tic"]:
        paths.append(f"{CDN_BASE}/{cid}/{tier}/animations/idle/{behavior}.riv")
    # Reactive animations
    for anim in ["happy_bounce", "soft_lean_in", "pull_out_object"]:
        paths.append(f"{CDN_BASE}/{cid}/{tier}/animations/reactive/{anim}.riv")
    # Habitat scene (if companion has one)
    companion = CAST[companion_id]
    if companion.habitat_region_id:
        for layer in ["sky", "mid", "foreground", "interactables"]:
            paths.append(f"/assets/habitats/{companion.habitat_region_id}/{layer}.svg")
    return paths


# ── Constraint checks ────────────────────────────────────────────────

def _is_shipped(companion_id: CompanionId, app_version: int) -> bool:
    return CAST[companion_id].ship_in_version <= app_version


def _pico_capped(req: SummonRequest) -> bool:
    return req.pico_appearances_in_lesson >= 1


def _hedge_blocked(req: SummonRequest) -> bool:
    return req.problem_steps_required <= 1


def _deep_think_active(req: SummonRequest) -> bool:
    return req.kid_typing and req.last_kid_action_ms_ago < 3000


# ── Summon resolver — the core state machine ─────────────────────────

def resolve_companion(req: SummonRequest) -> SummonResponse:
    """
    Pure function: (surface, user_state, context) → companion + emotion.
    Runs client-side for <1ms latency; server delivers rules via config.
    """
    surface = req.surface
    primary = req.user_state.chosen_primary
    age_tier = req.user_state.age_tier
    version = req.current_app_version
    fallback_used = False
    fallback_reason = None
    secondary_id = None
    secondary_emotion = None
    show_all = False

    # ── Rule lookup ──────────────────────────────────────────────
    if surface == Surface.ONBOARDING_STEP1:
        candidate = CompanionId.KIWI  # always Kiwi

    elif surface == Surface.ONBOARDING_STEP2:
        # All 5 shown in picker
        show_all = True
        candidate = primary

    elif surface == Surface.LESSON_HINT2:
        # Lumi overrides for second hints
        candidate = CompanionId.LUMI

    elif surface == Surface.LESSON_RETRY:
        # Mau overrides for review attempts
        candidate = CompanionId.MAU

    elif surface == Surface.LESSON_MULTI:
        # Hedge for multi-step, but only if problem qualifies
        if req.problem_steps_required > 1:
            candidate = CompanionId.HEDGE
        else:
            candidate = primary

    elif surface == Surface.LESSON_MASTERY:
        # Pico flies in + chosen_primary stays
        candidate = CompanionId.PICO
        secondary_id = primary
        secondary_emotion = Emotion.CELEBRATING

    elif surface in (Surface.REGION_CEREMONY, Surface.GRADE_CEREMONY):
        show_all = True
        candidate = primary

    else:
        # Default: chosen_primary
        candidate = primary

    # ── Constraint: Pico cap ─────────────────────────────────────
    if candidate == CompanionId.PICO and _pico_capped(req):
        candidate = primary
        secondary_id = None
        secondary_emotion = None
        fallback_used = True
        fallback_reason = "pico_max_1_per_lesson"

    # ── Constraint: Hedge only multi-step ────────────────────────
    if candidate == CompanionId.HEDGE and _hedge_blocked(req):
        candidate = primary
        fallback_used = True
        fallback_reason = "hedge_single_step_blocked"

    # ── Constraint: Mau blacklist on mastery ─────────────────────
    if surface == Surface.LESSON_MASTERY and candidate == CompanionId.MAU:
        # Mau's role is verification, not celebration
        # But if Mau IS chosen_primary, use Mau with celebrating emotion
        pass  # Mau stays as primary with celebrating emotion — spec says OK

    # ── Ship version gate ────────────────────────────────────────
    if not _is_shipped(candidate, version):
        fallback_used = True
        fallback_reason = "unshipped_companion"
        candidate = primary
        # If primary is also unshipped (shouldn't happen), fall to Kiwi
        if not _is_shipped(candidate, version):
            candidate = CompanionId.KIWI

    if secondary_id and not _is_shipped(secondary_id, version):
        secondary_id = None
        secondary_emotion = None

    # ── Resolve emotion ──────────────────────────────────────────
    emotion = SURFACE_EMOTIONS.get(surface, Emotion.NEUTRAL)

    # Special case: Lumi on second hint stays thinking; if kid's
    # chosen_primary IS Lumi, use encouraging instead to differentiate
    if surface == Surface.LESSON_HINT2 and candidate == CompanionId.LUMI:
        if primary == CompanionId.LUMI:
            emotion = Emotion.ENCOURAGING
        else:
            emotion = Emotion.THINKING

    # ── Deep-think retreat ───────────────────────────────────────
    # Client handles the fade animation; resolver signals it
    deep_think = _deep_think_active(req)

    # ── Build asset paths ────────────────────────────────────────
    asset_paths = build_asset_paths(candidate, age_tier, emotion)
    if secondary_id:
        sec_paths = build_asset_paths(secondary_id, age_tier,
                                       secondary_emotion or Emotion.CELEBRATING)
        asset_paths["secondary_pose_svg"] = sec_paths["pose_svg"]
        asset_paths["secondary_silhouette_svg"] = sec_paths["silhouette_svg"]

    return SummonResponse(
        primary_id=candidate,
        primary_emotion=emotion,
        secondary_id=secondary_id,
        secondary_emotion=secondary_emotion,
        asset_paths=asset_paths,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        show_all_five=show_all,
    )


# ── Telemetry event builders ─────────────────────────────────────────

def companion_summoned_event(response: SummonResponse, req: SummonRequest) -> dict:
    return {
        "event": "companion_summoned",
        "companion_id": response.primary_id.value,
        "surface": req.surface.value,
        "chosen_primary_id": req.user_state.chosen_primary.value,
        "lesson_id": req.lesson_id,
        "fallback_used": response.fallback_used,
        "fallback_reason": response.fallback_reason,
        "timestamp": time.time(),
    }


def companion_dismissed_event(companion_id: str, surface: str,
                               reason: str, time_visible_ms: int,
                               kid_acted: bool) -> dict:
    return {
        "event": "companion_dismissed",
        "companion_id": companion_id,
        "surface": surface,
        "dismiss_reason": reason,
        "time_visible_ms": time_visible_ms,
        "kid_acted_during_visit": kid_acted,
        "timestamp": time.time(),
    }


# ── Config bundle (served to client at session start) ─────────────────

def get_companion_config(user_state: UserCompanionState,
                         app_version: int = 1) -> dict:
    """
    Returns the full companion config bundle for the client.
    Called once per session; client caches and resolves locally.
    """
    primary = user_state.chosen_primary
    cast_list = []
    for cid, comp in CAST.items():
        cast_list.append({
            "id": comp.id.value,
            "name": comp.name,
            "region": comp.region,
            "role": comp.role,
            "signature_color": comp.signature_color,
            "signature_color_soft": comp.signature_color_soft,
            "signature_color_text": comp.signature_color_text,
            "is_default": comp.is_default,
            "shipped": comp.ship_in_version <= app_version,
        })

    return {
        "cast": cast_list,
        "chosen_primary": primary.value,
        "age_tier": user_state.age_tier.value,
        "audio_enabled": user_state.audio_enabled,
        "emotions": [e.value for e in Emotion],
        "surfaces": [s.value for s in Surface],
        "prefetch_manifest": build_prefetch_manifest(primary, user_state.age_tier),
        "performance_budgets": {
            "per_session_total_assets_mb": 2.0,
            "per_screen_simultaneous_animations": 1,
            "mastery_exception_max": 2,
            "fps_target": 60,
            "fps_minimum": 45,
            "memory_per_companion_mb": 0.5,
            "cache_ttl_hours": 24,
        },
        "idle_behaviors": {
            "blink": {"interval_min_ms": 4000, "interval_max_ms": 7000, "duration_ms": 200},
            "breath": {"interval_ms": 4000, "duration_ms": 4000, "scale_amplitude": 0.02},
            "look_around": {"interval_min_ms": 15000, "interval_max_ms": 22000, "duration_ms": 800},
        },
        "constraints": {
            "pico_max_per_lesson": 1,
            "lumi_auto_fade_ms": 5000,
            "deep_think_retreat_typing_ms": 3000,
            "deep_think_retreat_no_submit_ms": 10000,
            "idle_fade_start_ms": 30000,
            "idle_fade_to_opacity": 0.3,
        },
    }
