"""
Kiwimath question schema — Pydantic models.

v0.3 hybrid schema — extends v0.2 with:
  - Three-axis localization (locale / region / curriculum) replacing fused locale_context
  - Age tier system (Explorer K-2 / Adventurer 3-5 / Architect 6-10)
  - Mastery model with monotonic shown score + spaced repetition
  - Concept DAG for prerequisite graph (replaces linear topic ordering)

BACKWARD COMPAT: all additions are Optional with defaults.
Existing v0.1/v0.2 questions validate unchanged.

These models ARE the schema. If the schema changes, change it here and everything
downstream (validator, backend API, ingester) picks it up.

Reference spec: docs/question-schema.md
Hybrid proposal: _Schema/schema-v2-hybrid-proposal.json
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums — the tight constraints
# ---------------------------------------------------------------------------


class Topic(str, Enum):
    counting_observation = "counting_observation"
    arithmetic_missing_numbers = "arithmetic_missing_numbers"
    patterns_sequences = "patterns_sequences"
    logic_ordering = "logic_ordering"
    spatial_reasoning_3d = "spatial_reasoning_3d"
    shapes_folding_symmetry = "shapes_folding_symmetry"
    word_problems = "word_problems"
    number_puzzles_grids = "number_puzzles_grids"
    place_value = "place_value"
    time_measurement = "time_measurement"
    money_currency = "money_currency"
    comparison_ordering = "comparison_ordering"
    # v3b additional topics
    addition_subtraction = "addition_subtraction"
    multiplication_division = "multiplication_division"
    fractions_decimals = "fractions_decimals"
    estimation_mental_math = "estimation_mental_math"
    area_perimeter = "area_perimeter"
    data_probability = "data_probability"
    number_theory = "number_theory"
    exponents_roots = "exponents_roots"
    integers_negatives = "integers_negatives"
    algebra_expressions = "algebra_expressions"
    ratios_percents = "ratios_percents"
    angles_geometry = "angles_geometry"


class Tier(str, Enum):
    warmup = "warmup"
    practice = "practice"
    challenge = "challenge"


class AnswerType(str, Enum):
    """v0.1 answer types — kept for backward compat.
    Superseded by Interaction.type in v0.2 when present."""
    multiple_choice = "multiple_choice"
    numeric_input = "numeric_input"
    tap_to_select = "tap_to_select"
    drag_and_drop = "drag_and_drop"


class Status(str, Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    live = "live"


# ---------------------------------------------------------------------------
# v0.2 — Pedagogy
# ---------------------------------------------------------------------------


class Pedagogy(str, Enum):
    """Singapore CPA framework + supplementary modes."""
    cpa_concrete = "cpa_concrete"
    cpa_pictorial = "cpa_pictorial"
    cpa_abstract = "cpa_abstract"
    drill = "drill"
    exploration = "exploration"


# ---------------------------------------------------------------------------
# v0.2 — Interaction (richer replacement for answer_type)
# ---------------------------------------------------------------------------


class InteractionType(str, Enum):
    """Expanded interaction types. Frontend must have a renderer before
    content authors can use a type. fallback_type ensures graceful degradation."""
    multiple_choice = "multiple_choice"
    multiple_choice_visual = "multiple_choice_visual"
    tap_to_count = "tap_to_count"
    drag_to_order = "drag_to_order"
    numeric_keypad = "numeric_keypad"


class Interaction(BaseModel):
    """v0.2 interaction spec — describes HOW the child answers."""
    type: InteractionType
    target_formula: Optional[str] = None          # e.g. "N" for tap_to_count
    target_count: Optional[int] = None            # fixed target for non-parametric
    tap_targets: Optional[str] = None             # param key for tappable objects
    options: Optional[List[str]] = None           # for multiple_choice when overriding distractors
    options_descriptions: Optional[List[str]] = None  # for multiple_choice_visual
    correct_option_index: Optional[int] = None    # for visual MC where formula doesn't apply
    fallback_type: Optional[InteractionType] = InteractionType.multiple_choice


# ---------------------------------------------------------------------------
# v0.2 — Visual manifest (human-authored art brief)
# ---------------------------------------------------------------------------


class VisualManifest(BaseModel):
    """Human-readable visual description — coexists with svg_generator visual.
    Renderer prefers svg_generator if available, falls back to this for
    AI-generated art or static asset lookup."""
    art_brief: str = Field(..., min_length=10,
        description="Template string with {param} placeholders describing the visual")
    alt_text: str = Field(..., min_length=5)
    style: Optional[str] = "warm_cartoon"         # art style hint
    layout_hint: Optional[str] = None             # e.g. "scattered", "row", "grid", "stacked"
    visual_type: Optional[str] = None             # e.g. "illustration", "diagram", "3D_diagram"


# ---------------------------------------------------------------------------
# v0.2 — Curriculum alignment (structured replacement for loose tags)
# ---------------------------------------------------------------------------


class CurriculumAlignment(BaseModel):
    """Structured curriculum mapping — replaces loose tags for framework tracking."""
    common_core: Optional[str] = None             # e.g. "K.CC.B.4"
    cambridge_stage: Optional[int] = None         # 1-6
    cambridge_strand: Optional[str] = None        # e.g. "Thinking and Working Mathematically"
    singapore_strand: Optional[str] = None        # e.g. "Whole Numbers"
    kangaroo_level: Optional[str] = None          # e.g. "Felix", "Cadet"
    olympiad_skill: Optional[str] = None          # e.g. "Spatial Transformation / Invariants"
    reference: Optional[str] = None               # e.g. "Felix 2021 Q5"


# ---------------------------------------------------------------------------
# v0.2 — Socratic feedback (category-based, on top of misconceptions)
# ---------------------------------------------------------------------------


class SocraticFeedback(BaseModel):
    """Category-based feedback layer for responses that formula-based
    misconceptions can't predict: partial attempts, timeouts, over/under
    counting on tap interactions, and encouragement after retries."""
    on_correct: Optional[str] = None
    on_partial: Optional[str] = None              # template vars allowed: {attempt}
    on_timeout: Optional[str] = None
    on_under_count: Optional[str] = None          # tap_to_count specific
    on_over_count: Optional[str] = None           # tap_to_count specific
    generic_incorrect: Optional[str] = None       # fallback when no misconception matches
    incorrect_low: Optional[str] = None           # numeric answer too low
    incorrect_high: Optional[str] = None          # numeric answer too high
    incorrect_selection: Optional[str] = None     # wrong visual/spatial selection
    encouragement_after_retry: Optional[str] = None


# ---------------------------------------------------------------------------
# v0.3 — Age Tier system (3 tiers, not 2)
# ---------------------------------------------------------------------------


class AgeTier(str, Enum):
    """Three rendering tiers — each gets different component variants,
    illustration density, copy voice, celebration intensity, and nav model.
    Inferred from grade with optional "grown-up mode" override."""
    explorer = "explorer"        # K-2: play-first, audio-led, chunky shapes
    adventurer = "adventurer"    # 3-5: warm + character-bonded, world map
    architect = "architect"      # 6-10: confident, minimal, branching tree


def infer_tier(grade: int, grown_up_override: bool = False) -> AgeTier:
    """Resolve age tier from grade. The grown_up_override lets older struggling
    students opt into a more mature UI while practicing fundamentals."""
    if grown_up_override:
        return AgeTier.architect
    if grade <= 2:
        return AgeTier.explorer
    if grade <= 5:
        return AgeTier.adventurer
    return AgeTier.architect


# ---------------------------------------------------------------------------
# v0.3 — Three-axis localization (replacing fused locale_context)
#
# Design cofounder insight: locale, region, and curriculum are three
# INDEPENDENT axes that must not be fused:
#   - Locale (language): en-IN, es-MX, ar-SA → governs copy, RTL, plurals
#   - Region (culture): India, Mexico, Saudi → governs illustrations, names,
#     food, sport, festivals, seasons (hemisphere-aware)
#   - Curriculum (standards): CBSE, Common Core, UK NC, Singapore, IB →
#     governs concept ordering and standards codes
#
# A Spanish-speaking kid in Spain vs Mexico shares locale but not region.
# A Tamil-medium CBSE kid and English-medium ICSE kid share region but not
# locale or curriculum. Fusing these breaks in 18 months.
# ---------------------------------------------------------------------------


class NameEntry(BaseModel):
    """Name pool entry with gender tag for pronoun resolution.
    Co-dependency: name.gender_tag -> pronoun_set (resolved by template engine)."""
    value: str
    gender_tag: Literal["m", "f", "n"] = "n"


class PronounSet(BaseModel):
    """Pronoun triplet — resolved from NameEntry.gender_tag, never authored directly.
    neutral_fallback: for locales without true neuter (es, ar, hi, fr),
    specifies what gender_tag="n" resolves to. Set deliberately per locale
    rather than defaulting silently."""
    subject: str                                        # he/she/they
    object: str                                         # him/her/them
    possessive: str                                     # his/her/their
    neutral_fallback: Optional[Literal["m", "f"]] = None  # for gendered locales: what "n" maps to


class CurrencyPack(BaseModel):
    """Currency family binding — all fields resolve together, never independently.
    Co-dependency rule: currency_family."""
    currency: str                                           # "rupee", "dollar"
    symbol: str                                             # "₹", "$"
    coin_denominations: List[int] = Field(default_factory=list)   # [1, 2, 5, 10]
    bill_denominations: List[int] = Field(default_factory=list)   # [10, 20, 50, 100]


class RegionPack(BaseModel):
    """Cultural content pack — swapped per region, independent of language.
    Fills typed template slots in stem_template and visual_manifest.

    v0.4: Expanded from 10 flat fields to structured slot taxonomy (38 slots
    across 9 categories). See _Schema/slot_taxonomy_v1.yaml for full spec.

    BACKWARD COMPAT: old flat fields (names, objects, food, currency,
    currency_symbol, unit_length, unit_weight, unit_volume) are still
    accepted. New code should use the typed alternatives.
    """
    # ── Person (structured) ──
    name_pool: Optional[List[NameEntry]] = None             # names with gender tags
    pronoun_sets: Optional[Dict[str, PronounSet]] = None    # keyed by gender_tag: "m", "f", "n"
    friend_name_pool: Optional[List[NameEntry]] = None

    # ── Objects (typed categories — replaces flat `objects` + `food`) ──
    object_fruit: Optional[List[str]] = None
    object_toy: Optional[List[str]] = None
    object_animal: Optional[List[str]] = None
    object_stationery: Optional[List[str]] = None           # universal — usually same across regions
    object_vehicle: Optional[List[str]] = None
    object_prepared_food: Optional[List[str]] = None        # sensitivity: no pork/beef/alcohol
    object_coin: Optional[List[str]] = None                 # "1 rupee coin", "penny"

    # ── Currency (family binding) ──
    currency_pack: Optional[CurrencyPack] = None

    # ── Units (system-consistent: metric OR imperial, never mixed) ──
    unit_length_small: Optional[str] = None                 # cm / inch
    unit_length_large: Optional[str] = None                 # meter / foot
    unit_mass_small: Optional[str] = None                   # gram / ounce
    unit_mass_large: Optional[str] = None                   # kg / pound
    unit_volume: Optional[str] = None                       # mL / fl oz
    unit_time_short: Optional[List[str]] = None             # [second, minute]
    unit_time_long: Optional[List[str]] = None              # [hour, day, week]

    # ── Calendar ──
    week_start_day: Optional[str] = None                    # "Sunday" (US/IN), "Monday" (UK), "Saturday" (SA)
    time_format: Optional[str] = None                       # "12h" / "24h"
    season_mapping: Optional[Dict[str, str]] = None         # {"summer": "Apr-Jun"} hemisphere-aware
    number_display: Optional[str] = None                    # "western_arabic" / "arabic_indic" / "devanagari"

    # ── Shapes (real-world examples are region-specific) ──
    shape_real_world_examples: Optional[Dict[str, str]] = None  # {"circle": "bangle", "rectangle": "door"}

    # ── Illustrations ──
    illustration_protagonists: Optional[List[str]] = None   # asset IDs — diverse pool per region
    illustration_objects: Optional[Dict[str, str]] = None   # keyed by object value: {"mango": "asset_mango_in"}
    illustration_backgrounds: Optional[List[str]] = None    # scene backgrounds

    # ── Culture & Place ──
    location_commerce: Optional[List[str]] = None           # bazaar/shop/store
    location_learning: Optional[List[str]] = None           # school/library
    location_outdoor: Optional[List[str]] = None            # park/playground/maidan
    location_home: Optional[List[str]] = None               # kitchen/terrace/backyard
    sport_popular: Optional[List[str]] = None               # cricket/basketball
    sport_equipment: Optional[Dict[str, List[str]]] = None  # {"cricket": ["bat", "ball", "wickets"]}
    meal_name: Optional[List[str]] = None                   # breakfast/lunch/tiffin

    # ── Deprecated flat fields (backward compat — migrate to typed) ──
    names: Optional[List[str]] = None                       # → use name_pool
    objects: Optional[List[str]] = None                     # → use object_* categories
    food: Optional[List[str]] = None                        # → use object_fruit + object_prepared_food
    currency: Optional[str] = None                          # → use currency_pack.currency
    currency_symbol: Optional[str] = None                   # → use currency_pack.symbol
    unit_length: Optional[str] = None                       # → use unit_length_small + unit_length_large
    unit_weight: Optional[str] = None                       # → use unit_mass_small + unit_mass_large
    illustrations: Optional[Dict[str, str]] = None          # → use illustration_objects


class ContentLocalization(BaseModel):
    """Three-axis localization — replaces the fused locale_context.
    All three are independent; content API resolves template slots by
    combining the active locale + region + curriculum."""
    region_packs: Optional[Dict[str, RegionPack]] = None   # keyed by region code: "IN", "US", "MX", "UK", "SG"
    default_region: Optional[str] = "global"


# ---------------------------------------------------------------------------
# v0.3 — Mastery model (monotonic shown score + spaced repetition)
# ---------------------------------------------------------------------------


class MasteryLevel(str, Enum):
    """Khan-style vocabulary tiers — kids bond with the label, not the number.
    The label is derived from the shown_score threshold."""
    new = "new"                  # 0-24: never attempted or just started
    familiar = "familiar"        # 25-49: attempted, getting the idea
    proficient = "proficient"    # 50-79: mostly correct, some gaps
    mastered = "mastered"        # 80-100: consistent accuracy over time


def mastery_label(shown_score: float) -> MasteryLevel:
    """Derive the human-readable mastery label from the shown score."""
    if shown_score >= 80:
        return MasteryLevel.mastered
    if shown_score >= 50:
        return MasteryLevel.proficient
    if shown_score >= 25:
        return MasteryLevel.familiar
    return MasteryLevel.new


class MasteryConfig(BaseModel):
    """Per-concept mastery configuration on a question.
    The actual MasteryState (scores, timestamps) lives in the user profile
    in Firestore, not in the question JSON. This config tells the engine
    how to weight this question's contribution to concept mastery.

    Design rule: internal_elo moves both ways (for adaptivity).
    shown_score = max(score_history) over a window — NEVER drops.
    Spaced repetition decay is invisible to the kid — surfaced only as
    'time to revisit!' prompts, never as a dropping number."""
    concept_id: str = Field(..., pattern=r"^[a-z][a-z0-9_.]+$",
        description="Dot-separated concept ID, e.g. 'counting.one_to_one' or 'addition.within_10'")
    weight: float = Field(1.0, ge=0.1, le=5.0,
        description="How much this question contributes to concept mastery. Harder = higher weight.")
    review_interval_days: Optional[int] = Field(None, ge=1, le=180,
        description="Suggested spaced-repetition interval. Engine uses this as a hint.")


# ---------------------------------------------------------------------------
# v0.3 — Concept DAG (prerequisite graph, not a linear list)
#
# Design cofounder insight: math isn't linear. Algebra and geometry
# progress in parallel. A kid stuck on fractions can still learn perimeter.
# A single path means one stuck concept blocks everything.
#
# Data model: DAG of concepts with prerequisites.
# Rendering differs per age tier:
#   - Explorer (K-2): themed cartoon world with regions ("Number Island")
#   - Adventurer (3-5): branching world map with character homes
#   - Architect (6-10): Brilliant-style branching topic tree
# ---------------------------------------------------------------------------


class EdgeType(str, Enum):
    """Three prerequisite edge types — UI renders each differently.
    From DAG Review Delta 2 (design cofounder rubric Check 6).
      hard_prereq:  truly must be mastered first (UI: locked)
      soft_prereq:  typically taught before, but accessible (UI: 'try X first' nudge)
      strand_order: pedagogical ordering, freely navigable (UI: no restriction)
    """
    hard_prereq = "hard_prereq"
    soft_prereq = "soft_prereq"
    strand_order = "strand_order"


class PrerequisiteEdge(BaseModel):
    """A typed prerequisite edge in the concept DAG.
    Replaces the flat string prerequisites array for richer UI and adaptivity."""
    concept_id: str = Field(..., pattern=r"^[a-z][a-z0-9_.]+$")
    edge_type: EdgeType = EdgeType.hard_prereq


class ConceptNode(BaseModel):
    """A node in the concept prerequisite graph. Lives in a separate
    concept_graph.json file, not inside individual questions.
    Questions reference concepts via mastery_config.concept_id.

    v1.1: prerequisites upgraded from List[str] to List[PrerequisiteEdge].
    BACKWARD COMPAT: validator accepts both forms — bare strings are
    treated as hard_prereq edges."""
    concept_id: str = Field(..., pattern=r"^[a-z][a-z0-9_.]+$")
    display_name: str
    description: Optional[str] = None
    grade_range: List[int] = Field(..., min_length=2, max_length=2,
        description="[min_grade, max_grade] this concept spans")
    prerequisites: List[Union[str, PrerequisiteEdge]] = Field(default_factory=list,
        description="Typed prerequisite edges. Bare strings accepted (→ hard_prereq).")
    # Rendering hints per tier
    world_region: Optional[str] = None         # "number_island", "shape_forest" — for Explorer tier
    map_position: Optional[Dict[str, float]] = None  # {"x": 0.5, "y": 0.3} — for Adventurer tier
    topic_branch: Optional[str] = None         # "algebra", "geometry" — for Architect tier

    @field_validator("prerequisites", mode="before")
    @classmethod
    def _coerce_string_prereqs(cls, v: Any) -> Any:
        """Accept bare strings as hard_prereq edges for backward compat."""
        if not isinstance(v, list):
            return v
        out = []
        for item in v:
            if isinstance(item, str):
                out.append({"concept_id": item, "edge_type": "hard_prereq"})
            else:
                out.append(item)
        return out

    @property
    def prerequisite_ids(self) -> List[str]:
        """Flat list of prerequisite concept IDs (any edge type)."""
        return [p.concept_id if isinstance(p, PrerequisiteEdge) else p
                for p in self.prerequisites]

    @property
    def hard_prerequisites(self) -> List[str]:
        """Only hard_prereq concept IDs — these gate unlock in the UI."""
        return [p.concept_id for p in self.prerequisites
                if isinstance(p, PrerequisiteEdge) and p.edge_type == EdgeType.hard_prereq]


class ConceptGraph(BaseModel):
    """The full prerequisite DAG. Validated for no cycles.
    Loaded once at app startup, not per-question."""
    version: int = Field(..., ge=1)
    nodes: List[ConceptNode] = Field(default_factory=list)

    @model_validator(mode="after")
    def _no_duplicate_ids(self) -> "ConceptGraph":
        ids = [n.concept_id for n in self.nodes]
        if len(ids) != len(set(ids)):
            dupes = [i for i in ids if ids.count(i) > 1]
            raise ValueError(f"duplicate concept_ids: {sorted(set(dupes))}")
        return self

    @model_validator(mode="after")
    def _prerequisites_exist(self) -> "ConceptGraph":
        all_ids = {n.concept_id for n in self.nodes}
        for n in self.nodes:
            missing = set(n.prerequisite_ids) - all_ids
            if missing:
                raise ValueError(
                    f"concept '{n.concept_id}' has prerequisites {sorted(missing)} "
                    f"which don't exist in the graph"
                )
        return self

    @model_validator(mode="after")
    def _no_cycles(self) -> "ConceptGraph":
        """Topological sort to detect cycles in the prerequisite DAG."""
        adj: Dict[str, List[str]] = {n.concept_id: list(n.prerequisite_ids) for n in self.nodes}
        visited: set = set()
        in_stack: set = set()

        def dfs(node: str) -> bool:
            if node in in_stack:
                return True  # cycle
            if node in visited:
                return False
            in_stack.add(node)
            for dep in adj.get(node, []):
                if dfs(dep):
                    return True
            in_stack.remove(node)
            visited.add(node)
            return False

        for n in adj:
            if dfs(n):
                raise ValueError(f"cycle detected in concept DAG involving '{n}'")
        return self


# ---------------------------------------------------------------------------
# Param spec — either a fixed pool, a numeric range, or inherit-from-parent
# ---------------------------------------------------------------------------


class ParamPool(BaseModel):
    pool: List[Union[str, int, float]]
    constraint: Optional[str] = None  # e.g. "shape != odd_one_out"


class ParamRange(BaseModel):
    range: List[int] = Field(..., min_length=2, max_length=2)
    constraint: Optional[str] = None  # e.g. "K < N"

    @field_validator("range")
    @classmethod
    def _ordered(cls, v: List[int]) -> List[int]:
        if v[0] > v[1]:
            raise ValueError(f"range min ({v[0]}) > max ({v[1]})")
        return v


class ParamInherit(BaseModel):
    inherit_from_parent: Literal[True]


ParamSpec = Union[ParamPool, ParamRange, ParamInherit]


# ---------------------------------------------------------------------------
# Visual
# ---------------------------------------------------------------------------


class SvgGeneratorVisual(BaseModel):
    type: Literal["svg_generator"]
    generator: str
    params: Dict[str, Any] = Field(default_factory=dict)


class StaticAssetVisual(BaseModel):
    type: Literal["static_asset"]
    path: str
    alt_text: str


VisualSpec = Union[SvgGeneratorVisual, StaticAssetVisual]


# ---------------------------------------------------------------------------
# Distractors & misconceptions
# ---------------------------------------------------------------------------


class Distractor(BaseModel):
    formula: str
    label: str


class Misconception(BaseModel):
    trigger_answer: str
    diagnosis: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9_]+$",
        description="snake_case label — reused across questions, powers parent reports",
    )
    feedback_child: str = Field(..., max_length=120)
    step_down_path: List[str] = Field(..., min_length=1, max_length=5)

    @field_validator("feedback_child")
    @classmethod
    def _word_count(cls, v: str) -> str:
        wc = len(v.split())
        if wc > 20:
            raise ValueError(
                f"feedback_child is {wc} words; style rule says <15 words, hard cap 20"
            )
        return v


# ---------------------------------------------------------------------------
# Locale
# ---------------------------------------------------------------------------


class LocaleOverride(BaseModel):
    names: Optional[List[str]] = None
    objects: Optional[List[str]] = None
    currency: Optional[str] = None


class LocaleContext(BaseModel):
    IN: Optional[LocaleOverride] = None
    US: Optional[LocaleOverride] = None
    SG: Optional[LocaleOverride] = None
    global_: Optional[LocaleOverride] = Field(None, alias="global")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Main question models
# ---------------------------------------------------------------------------


# Accept both old format (G1-COUNT-001) and v3b format (G1-CH01-CO-001)
ID_RE_PARENT = re.compile(r"^G[1-8]-(?:CH\d{2}-)?[A-Za-z0-9]+-\d{3}$")
ID_RE_STEP = re.compile(r"^G[1-8]-(?:CH\d{2}-)?[A-Za-z0-9]+-\d{3}-S[1-5]$")
PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


class _QuestionBase(BaseModel):
    """Fields shared by parent questions and step-downs."""

    # --- v0.1 core (required) ---
    id: str
    grade: int = Field(..., ge=1, le=8)
    topic: Topic
    subtopic: Optional[str] = None
    subskills: List[str] = Field(..., min_length=1)
    difficulty: int = Field(..., ge=1, le=5)
    tier: Tier
    source_inspiration: Optional[str] = None

    stem_template: str = Field(..., min_length=3)
    visual: Optional[VisualSpec] = None
    answer_type: AnswerType

    params: Dict[str, ParamSpec] = Field(default_factory=dict)
    derived: Optional[Dict[str, str]] = None

    answer_formula: str
    distractors: List[Distractor] = Field(..., min_length=2, max_length=5)

    tags: List[str] = Field(default_factory=list)
    est_time_seconds: Optional[int] = Field(None, ge=5, le=300)
    version: int = Field(..., ge=1)
    author: str = Field(..., min_length=1, max_length=10)
    status: Status

    # --- v0.2 additions (all optional — backward compatible) ---
    pedagogy: Optional[Pedagogy] = None
    interaction: Optional[Interaction] = None
    visual_manifest: Optional[VisualManifest] = None
    curriculum_alignment: Optional[CurriculumAlignment] = None
    socratic_feedback: Optional[SocraticFeedback] = None

    # --- v0.3 additions (all optional — backward compatible) ---
    mastery_config: Optional[MasteryConfig] = None     # links question to concept DAG
    age_tier_override: Optional[AgeTier] = None        # force a specific tier rendering

    @field_validator("subskills")
    @classmethod
    def _snake_case_subskills(cls, v: List[str]) -> List[str]:
        for s in v:
            if not re.match(r"^[a-z][a-z0-9_]+$", s):
                raise ValueError(f"subskill '{s}' must be snake_case")
        return v

    @model_validator(mode="after")
    def _check_distractor_labels_unique(self) -> "_QuestionBase":
        labels = [d.label for d in self.distractors]
        if len(labels) != len(set(labels)):
            raise ValueError(f"duplicate distractor labels: {labels}")
        return self

    @model_validator(mode="after")
    def _check_distractor_formulas_unique(self) -> "_QuestionBase":
        """No two distractors should have the same formula — renders as
        duplicate wrong answers in MC."""
        formulas = [d.formula for d in self.distractors]
        if len(formulas) != len(set(formulas)):
            raise ValueError(f"duplicate distractor formulas: {formulas}")
        return self

    @model_validator(mode="after")
    def _answer_not_in_distractors(self) -> "_QuestionBase":
        """The correct answer must not appear as a distractor — the engine
        prepends it to the MC options automatically."""
        distractor_formulas = {d.formula for d in self.distractors}
        if self.answer_formula in distractor_formulas:
            raise ValueError(
                f"answer_formula '{self.answer_formula}' also appears as a "
                f"distractor — distractors must be wrong answers only"
            )
        return self

    @model_validator(mode="after")
    def _visual_params_reference_stem_vars(self) -> "_QuestionBase":
        """Visual param values that look like variable names must correspond
        to {placeholders} in the stem_template. Catches misaligned bindings
        that would fail at render time."""
        if not self.visual or not isinstance(self.visual, SvgGeneratorVisual):
            return self
        # Visual params may reference any declared param or derived variable,
        # not just those that appear in the stem template.
        all_vars = set(self.params.keys())
        if self.derived:
            all_vars |= set(self.derived.keys())
        all_vars |= set(PLACEHOLDER_RE.findall(self.stem_template))
        for key, val in self.visual.params.items():
            refs = []
            if isinstance(val, str):
                refs = [val]
            elif isinstance(val, list):
                refs = [v for v in val if isinstance(v, str)]
            for ref in refs:
                clean = ref.strip("{}")
                # Skip literals: numbers, hex colours, keywords
                try:
                    float(clean)
                    continue
                except ValueError:
                    pass
                if clean.startswith("#") or clean in (
                    "number_line_hops", "dots", "pattern", "true", "false",
                    "object", "shape",
                ):
                    continue
                # If it's a simple variable name, check it exists
                if clean and clean not in all_vars:
                    # It might be an expression like "A + B" or a string
                    # literal like "basic_3". Check if all word tokens are
                    # either in all_vars or are operators/keywords/literals.
                    import re as _re
                    tokens = set(_re.findall(r"[A-Za-z_]\w*", clean))
                    unknown = tokens - all_vars - {
                        "and", "or", "not", "if", "else", "true", "false",
                    }
                    # If all tokens are known variables or it contains
                    # operators (likely an expression), allow it
                    if unknown and not any(
                        op in clean for op in ("+", "-", "*", "/", "_")
                    ):
                        raise ValueError(
                            f"visual.params.{key} references '{clean}' which is "
                            f"not declared in params/derived/stem "
                            f"(have: {sorted(all_vars)})"
                        )
        return self

    @model_validator(mode="after")
    def _check_placeholders_resolve(self) -> "_QuestionBase":
        placeholders = set(PLACEHOLDER_RE.findall(self.stem_template))
        provided = set(self.params.keys())
        if self.derived:
            provided |= set(self.derived.keys())
        missing = placeholders - provided
        if missing:
            raise ValueError(
                f"stem_template uses {{{sorted(missing)}}} but no params/derived "
                f"declared for them (have: {sorted(provided)})"
            )
        return self


class Question(_QuestionBase):
    """A golden parent question. Must have misconceptions."""

    misconceptions: List[Misconception] = Field(..., min_length=2, max_length=5)
    locale_context: Optional[LocaleContext] = None       # v0.1 DEPRECATED — kept for backward compat
    content_localization: Optional[ContentLocalization] = None  # v0.3 — three-axis replacement

    @field_validator("id")
    @classmethod
    def _valid_parent_id(cls, v: str) -> str:
        if not ID_RE_PARENT.match(v):
            raise ValueError(
                f"id '{v}' must match G{{grade}}-{{TOPIC}}-{{nnn}}, e.g. G1-COUNT-001"
            )
        return v

    @model_validator(mode="after")
    def _misconceptions_link_to_distractors(self) -> "Question":
        distractor_formulas = {d.formula for d in self.distractors}
        for m in self.misconceptions:
            if m.trigger_answer not in distractor_formulas:
                raise ValueError(
                    f"misconception trigger_answer '{m.trigger_answer}' is not one of "
                    f"the distractor formulas {sorted(distractor_formulas)}"
                )
        return self

    @model_validator(mode="after")
    def _each_distractor_has_misconception(self) -> "Question":
        distractor_formulas = {d.formula for d in self.distractors}
        covered = {m.trigger_answer for m in self.misconceptions}
        uncovered = distractor_formulas - covered
        if uncovered:
            # Warn-level — allowed for v0 but flagged
            # (Authors: every distractor should have a misconception; we allow up to 1 uncovered)
            if len(uncovered) > 1:
                raise ValueError(
                    f"{len(uncovered)} distractors have no misconception "
                    f"(max allowed: 1): {sorted(uncovered)}"
                )
        return self

    @model_validator(mode="after")
    def _step_down_ids_well_formed(self) -> "Question":
        for m in self.misconceptions:
            if not m.step_down_path:
                raise ValueError(
                    f"misconception '{m.diagnosis}' has empty step_down_path — "
                    f"every parent misconception must scaffold to at least one step-down"
                )
            for sd_id in m.step_down_path:
                if not sd_id.startswith(self.id + "-S"):
                    raise ValueError(
                        f"step_down_path id '{sd_id}' should start with '{self.id}-S' "
                        f"(step-downs must belong to their parent question)"
                    )
        return self


class StepDownQuestion(_QuestionBase):
    """A scaffolding sub-question. No misconceptions — we don't recurse."""

    parent_id: str
    step_index: int = Field(..., ge=1, le=5)
    misconceptions: List[Misconception] = Field(default_factory=list, max_length=0)

    @field_validator("id")
    @classmethod
    def _valid_step_id(cls, v: str) -> str:
        if not ID_RE_STEP.match(v):
            raise ValueError(
                f"id '{v}' must match G{{grade}}-{{TOPIC}}-{{nnn}}-S{{n}}, "
                f"e.g. G1-COUNT-001-S1"
            )
        return v

    @model_validator(mode="after")
    def _parent_id_matches(self) -> "StepDownQuestion":
        expected_prefix = self.parent_id + "-S"
        if not self.id.startswith(expected_prefix):
            raise ValueError(
                f"step-down id '{self.id}' does not belong to parent '{self.parent_id}'"
            )
        return self


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def is_step_down_id(qid: str) -> bool:
    return bool(ID_RE_STEP.match(qid))


def parse_question_file(data: Dict[str, Any]) -> Union[Question, StepDownQuestion]:
    """Dispatch to the right model based on id shape."""
    qid = data.get("id", "")
    if is_step_down_id(qid):
        return StepDownQuestion.model_validate(data)
    return Question.model_validate(data)
