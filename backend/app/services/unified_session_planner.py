"""
Unified Cross-Curriculum Session Planner v2.

Replaces the old topic-based session planner with a skill-graph-driven engine
that pulls from ALL curricula (Olympiad + NCERT + ICSE + Singapore + USCC).

Key differences from the old planner:
  1. Operates at SKILL level, not topic level — each skill has a unified pool
  2. Cross-curriculum: a "fractions" session may mix NCERT + Singapore + Olympiad questions
  3. Auto-transitions: detects mastery and moves to next skill in prereq graph
  4. Continuous parent messaging: generates per-session + weekly insight summaries

Architecture:
  - SkillIndex maps every question → skill node
  - Session picks skills based on: prerequisite readiness, weakness, review needs
  - Questions picked from unified pool closest to student's target difficulty
  - After session: generates parent message about what was practiced and progress
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from app.assessment.path_engine import (
    GRADE_EXPECTATIONS,
    PREREQUISITE_GRAPH,
    PathEngine,
    SkillNode,
    Track,
)
from app.services.adaptive_engine_v2 import engine_v2, theta_to_difficulty, difficulty_to_theta
from app.services.content_store_v2 import QuestionV2, store_v2
from app.services.mistake_tracker import mistake_tracker
from app.services.skill_mapper import skill_index
from app.services.skill_ability_store import (
    skill_ability_store,
    SkillAbility,
    DEFAULT_THETA as SKILL_DEFAULT_THETA,
)
from app.services.spaced_review_engine import spaced_review_store


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SESSION_SIZE = 10
MASTERY_THRESHOLD_ACCURACY = 0.80
MASTERY_THRESHOLD_MIN_ITEMS = 5
WARMUP_SLOTS = 2          # Easy confidence-builders at session start
STRETCH_SLOTS = 2          # Challenge questions at session end
REVIEW_SLOTS = 2           # Spaced revision from past mistakes
MAX_REVIEW_PER_SESSION = 3 # Hard cap: never more than 3 reviews (strategic decision #9)
CORE_SLOTS = SESSION_SIZE - WARMUP_SLOTS - STRETCH_SLOTS - REVIEW_SLOTS  # = 4

# Welcome Back mode: if student hasn't played in ≥ WELCOME_BACK_DAYS,
# we boost warmup and reduce stretch to rebuild confidence.
WELCOME_BACK_DAYS = 3
WELCOME_BACK_WARMUP_SLOTS = 4   # Extra warmups on return
WELCOME_BACK_STRETCH_SLOTS = 1  # Fewer stretch questions
WELCOME_BACK_REVIEW_SLOTS = 2   # Same review

# How far above/below target difficulty to pull warmup/stretch questions
WARMUP_OFFSET = -15
STRETCH_OFFSET = +15


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class UnifiedPlannedQuestion:
    question_id: str
    skill_id: str
    skill_name: str
    difficulty_score: int
    slot_type: str  # "warmup" | "core" | "stretch" | "review"
    source_curriculum: str  # "olympiad" | "ncert" | "icse" | "singapore" | "uscc"


@dataclass
class UnifiedSessionPlan:
    user_id: str
    grade: int
    questions: List[UnifiedPlannedQuestion]
    focus_skills: List[str]           # Primary skills being practiced
    skill_breakdown: Dict[str, int]   # skill_id -> count
    curriculum_mix: Dict[str, int]    # curriculum -> count
    session_message: str              # Parent-facing: what this session practices
    mastery_transitions: List[str]    # Skills that just hit mastery


@dataclass
class ParentSessionSummary:
    """Generated after a session is completed."""
    session_id: str
    user_id: str
    date: str
    skills_practiced: List[str]
    accuracy: float
    questions_correct: int
    questions_total: int
    new_masteries: List[str]     # Skills mastered this session
    progress_message: str        # "Aarav got 8/10 today! Fractions are improving."
    next_focus: str              # "Next session will focus on comparing fractions."
    weekly_trend: str            # "Up 12% in arithmetic this week."


# ---------------------------------------------------------------------------
# Skill state helpers
# ---------------------------------------------------------------------------

def _get_skill_theta(user_id: str, skill_id: str) -> float:
    """Get the student's ability estimate for a specific skill.

    Uses the per-skill theta store (37 independent estimates) rather than
    the domain-level approximation. Falls back to domain theta for skills
    with no interaction history.
    """
    ability = skill_ability_store.get_skill_ability(user_id, skill_id)
    if ability.n_responses > 0:
        return ability.theta

    # Fallback: use domain-level theta for unstarted skills
    node = PREREQUISITE_GRAPH.get(skill_id)
    if not node:
        return SKILL_DEFAULT_THETA
    domain_ability = engine_v2.get_ability(user_id, node.domain)
    return domain_ability.theta


def _get_skill_difficulty_target(user_id: str, skill_id: str) -> int:
    """Target difficulty for this skill based on student's current ability."""
    ability = skill_ability_store.get_skill_ability(user_id, skill_id)
    if ability.n_responses > 0:
        return ability.difficulty_target

    # Fallback to domain
    node = PREREQUISITE_GRAPH.get(skill_id)
    if not node:
        return 50
    domain_ability = engine_v2.get_ability(user_id, node.domain)
    return theta_to_difficulty(domain_ability.theta)


def _is_skill_mastered(user_id: str, skill_id: str, grade: int) -> bool:
    """Check if a skill is mastered using the sustained mastery system.

    Uses the per-skill ability store which requires ≥80% accuracy
    across ≥5 items over ≥2 non-consecutive sessions.
    """
    ability = skill_ability_store.get_skill_ability(user_id, skill_id)
    if ability.mastery_confirmed:
        return True

    # Fallback: check if theta is well above grade expectation
    node = PREREQUISITE_GRAPH.get(skill_id)
    if not node:
        return False
    theta = _get_skill_theta(user_id, skill_id)
    expected = GRADE_EXPECTATIONS.get(node.domain, {}).get(grade, 0.0)
    return theta > expected + 0.5


def _are_prereqs_ready(user_id: str, skill_id: str, grade: int) -> bool:
    """Check if all prerequisites for a skill are mastered."""
    node = PREREQUISITE_GRAPH.get(skill_id)
    if not node or not node.prerequisites:
        return True
    for prereq_id in node.prerequisites:
        if not _is_skill_mastered(user_id, prereq_id, grade):
            return False
    return True


def _identify_source(q: QuestionV2) -> str:
    """Identify which curriculum a question belongs to."""
    qid = q.id or ""
    if qid.startswith("NCERT"):
        return "ncert"
    elif qid.startswith("SING"):
        return "singapore"
    elif qid.startswith("USCC"):
        return "uscc"
    elif qid.startswith("ICSE"):
        return "icse"
    else:
        return "olympiad"


# ---------------------------------------------------------------------------
# Skill prioritisation
# ---------------------------------------------------------------------------

@dataclass
class _SkillCandidate:
    skill_id: str
    skill_name: str
    domain: str
    priority: float  # Higher = more urgent
    reason: str
    grade_gap: float  # How far behind grade expectation


def _prioritise_skills(user_id: str, grade: int) -> List[_SkillCandidate]:
    """Rank all skills by learning priority for this student.

    Priority logic:
      5.0 = prerequisite gap (foundation skill not yet mastered)
      4.0 = weak skill (below grade level, prereqs ready)
      3.0 = active learning (at grade level, still building)
      2.0 = reinforcement (near mastery, needs a few more reps)
      1.0 = stretch/acceleration (above grade, for challenge)
      0.0 = mastered, no action needed
    """
    candidates = []

    for skill_id, node in PREREQUISITE_GRAPH.items():
        # Skip skills way above the student's grade
        if node.grade_level > grade + 1.5:
            continue

        theta = _get_skill_theta(user_id, skill_id)
        expected = GRADE_EXPECTATIONS.get(node.domain, {}).get(grade, 0.0)
        gap = expected - theta  # Positive = behind, negative = ahead

        mastered = _is_skill_mastered(user_id, skill_id, grade)
        prereqs_ready = _are_prereqs_ready(user_id, skill_id, grade)

        if mastered:
            # Check if it's a stretch opportunity
            if node.grade_level > grade:
                priority = 1.0
                reason = "stretch"
            else:
                priority = 0.0
                reason = "mastered"
        elif not prereqs_ready:
            # Can't learn this yet — but flag the prereqs
            priority = 0.0
            reason = "prereqs_not_ready"
        elif gap > 1.0:
            # Major gap — this is a foundation issue
            priority = 5.0
            reason = "foundation_gap"
        elif gap > 0.5:
            # Moderate gap — active learning target
            priority = 4.0
            reason = "weak_skill"
        elif gap > 0.0:
            # Slight gap — reinforcement
            priority = 3.0
            reason = "reinforcement"
        elif gap > -0.3:
            # At level — still consolidating
            priority = 2.0
            reason = "consolidation"
        else:
            # Above level
            priority = 1.0
            reason = "stretch"

        candidates.append(_SkillCandidate(
            skill_id=skill_id,
            skill_name=node.name,
            domain=node.domain,
            priority=priority,
            reason=reason,
            grade_gap=gap,
        ))

    # Sort: highest priority first, then by gap size (biggest gap = most urgent)
    candidates.sort(key=lambda c: (-c.priority, -c.grade_gap))
    return candidates


# ---------------------------------------------------------------------------
# Question selection from unified pool
# ---------------------------------------------------------------------------

def _pick_question(
    skill_id: str,
    target_difficulty: int,
    grade: int,
    used_ids: Set[str],
    prefer_curriculum: Optional[str] = None,
) -> Optional[Tuple[QuestionV2, str]]:
    """Pick the best question for a skill from the unified cross-curriculum pool.

    Uses weighted random sampling based on difficulty proximity instead of
    top-5 selection, giving much better variety across sessions.

    Returns (question, source_curriculum) or None.
    """
    # Get grade-appropriate difficulty window
    window = 40  # ±40 difficulty points from target (was ±30)
    min_d = max(1, target_difficulty - window)
    max_d = target_difficulty + window

    pool = skill_index.get_questions_for_skill(
        skill_id, min_difficulty=min_d, max_difficulty=max_d, exclude_ids=used_ids
    )

    if not pool:
        # Widen the window
        pool = skill_index.get_questions_for_skill(
            skill_id, min_difficulty=1, max_difficulty=300, exclude_ids=used_ids
        )

    if not pool:
        return None

    # Prefer diversity: try to pick from a different curriculum than recent ones
    if prefer_curriculum:
        preferred = [q for q in pool if _identify_source(q) == prefer_curriculum]
        if preferred and len(preferred) >= 3:
            pool = preferred

    # Weighted random sampling by difficulty proximity
    # Closer to target = higher weight, but all candidates have a chance
    weights = []
    for q in pool:
        dist = abs(q.difficulty_score - target_difficulty)
        # Inverse-distance weight with a floor so far questions still have a chance
        weight = 1.0 / (1.0 + dist * 0.05)
        weights.append(weight)

    # Normalize weights
    total_w = sum(weights)
    if total_w > 0:
        weights = [w / total_w for w in weights]
        chosen = random.choices(pool, weights=weights, k=1)[0]
    else:
        chosen = random.choice(pool)

    return chosen, _identify_source(chosen)


# ---------------------------------------------------------------------------
# Main session planning
# ---------------------------------------------------------------------------

def plan_unified_session(
    user_id: str,
    grade: int,
    session_size: int = SESSION_SIZE,
    last_session_date: Optional[datetime] = None,
    previously_seen_ids: Optional[Set[str]] = None,
) -> UnifiedSessionPlan:
    """Build a cross-curriculum adaptive session.

    Session structure (normal):
      [2 warmup] → [4 core skill practice] → [2 stretch] → [2 review]

    Welcome Back mode (≥3 days away):
      [4 warmup] → [3 core] → [1 stretch] → [2 review]
      Boosts warmup for confidence after a gap. Parent message explains.

    Review cap: never more than MAX_REVIEW_PER_SESSION (3) review slots,
    even if FSRS has many due items. Prevents all-review sessions.

    previously_seen_ids: Question IDs the student has recently answered
    (loaded from Firestore). These are excluded from selection to prevent
    repetition across sessions.
    """
    if not skill_index.is_built:
        skill_index.build()

    # Detect Welcome Back mode
    welcome_back = False
    days_away = 0
    if last_session_date:
        days_away = (datetime.now(timezone.utc) - last_session_date).days
        welcome_back = days_away >= WELCOME_BACK_DAYS

    # 1. Prioritise skills for this student
    candidates = _prioritise_skills(user_id, grade)
    active_skills = [c for c in candidates if c.priority > 0]

    # Identify focus skills (top 2-3 for this session)
    focus_skills = [c for c in active_skills if c.priority >= 3.0][:3]
    if not focus_skills:
        focus_skills = active_skills[:3]

    # Mastered skills for warmup
    mastered_skills = [c for c in candidates if c.reason == "mastered"]
    # Stretch skills
    stretch_skills = [c for c in candidates if c.reason == "stretch"]

    # Slot allocation — adjusted for Welcome Back mode
    if welcome_back:
        n_warmup = WELCOME_BACK_WARMUP_SLOTS
        n_stretch = WELCOME_BACK_STRETCH_SLOTS
        n_review = min(WELCOME_BACK_REVIEW_SLOTS, MAX_REVIEW_PER_SESSION)
    else:
        n_warmup = WARMUP_SLOTS
        n_stretch = STRETCH_SLOTS
        n_review = min(REVIEW_SLOTS, MAX_REVIEW_PER_SESSION)
    n_core = session_size - n_warmup - n_stretch - n_review

    planned: List[UnifiedPlannedQuestion] = []
    # Seed with previously seen questions to prevent cross-session repetition
    used_ids: Set[str] = set(previously_seen_ids) if previously_seen_ids else set()
    skill_counts: Dict[str, int] = defaultdict(int)
    curriculum_counts: Dict[str, int] = defaultdict(int)
    recent_curricula: List[str] = []

    def _add_question(skill_id: str, skill_name: str, slot_type: str, target_d: int) -> bool:
        # Prefer a curriculum we haven't used recently
        prefer = None
        curricula_available = ["olympiad", "ncert", "singapore", "icse", "uscc"]
        least_used = min(curricula_available, key=lambda c: curriculum_counts.get(c, 0))
        if curriculum_counts.get(least_used, 0) < 2:
            prefer = least_used

        result = _pick_question(skill_id, target_d, grade, used_ids, prefer)
        if result is None:
            return False

        q, source = result
        planned.append(UnifiedPlannedQuestion(
            question_id=q.id,
            skill_id=skill_id,
            skill_name=skill_name,
            difficulty_score=q.difficulty_score,
            slot_type=slot_type,
            source_curriculum=source,
        ))
        used_ids.add(q.id)
        skill_counts[skill_id] += 1
        curriculum_counts[source] += 1
        recent_curricula.append(source)
        return True

    # --- WARMUP: confidence builders (boosted in Welcome Back mode) ---
    warmup_added = 0
    warmup_offset = WARMUP_OFFSET - 10 if welcome_back else WARMUP_OFFSET  # Even easier on return
    random.shuffle(mastered_skills)
    for skill in mastered_skills:
        if warmup_added >= n_warmup:
            break
        target = _get_skill_difficulty_target(user_id, skill.skill_id)
        target = max(1, target + warmup_offset)
        if _add_question(skill.skill_id, skill.skill_name, "warmup", target):
            warmup_added += 1

    # If not enough mastered skills, use easiest focus skill questions
    if warmup_added < n_warmup and focus_skills:
        for skill in focus_skills:
            if warmup_added >= n_warmup:
                break
            target = _get_skill_difficulty_target(user_id, skill.skill_id)
            target = max(1, target - 20)
            if _add_question(skill.skill_id, skill.skill_name, "warmup", target):
                warmup_added += 1

    # --- CORE: focus skill practice ---
    core_added = 0
    focus_cycle = list(focus_skills)
    focus_idx = 0
    attempts = 0
    while core_added < n_core and attempts < 20:
        if not focus_cycle:
            break
        skill = focus_cycle[focus_idx % len(focus_cycle)]
        target = _get_skill_difficulty_target(user_id, skill.skill_id)
        if _add_question(skill.skill_id, skill.skill_name, "core", target):
            core_added += 1
        focus_idx += 1
        attempts += 1

    # --- STRETCH: slightly above level ---
    stretch_added = 0
    stretch_candidates = stretch_skills if stretch_skills else focus_skills
    random.shuffle(stretch_candidates)
    for skill in stretch_candidates:
        if stretch_added >= n_stretch:
            break
        target = _get_skill_difficulty_target(user_id, skill.skill_id)
        target = min(300, target + STRETCH_OFFSET)
        if _add_question(skill.skill_id, skill.skill_name, "stretch", target):
            stretch_added += 1

    # --- REVIEW: capped at MAX_REVIEW_PER_SESSION (never all-review) ---
    review_added = 0

    # Priority 1: FSRS-scheduled reviews (skills due per forgetting curve)
    due_reviews = spaced_review_store.get_due_reviews(user_id, max_items=n_review)
    for schedule in due_reviews:
        if review_added >= n_review:
            break
        skill_id = schedule.skill_id
        target = _get_skill_difficulty_target(user_id, skill_id)
        node = PREREQUISITE_GRAPH.get(skill_id)
        skill_name = node.name if node else skill_id
        if _add_question(skill_id, skill_name, "review", target):
            review_added += 1

    # Priority 2: Fall back to mistake tracker if FSRS doesn't fill slots
    if review_added < n_review:
        revision_candidates = mistake_tracker.get_revision_question_ids(
            student_id=user_id, max_items=(n_review - review_added) * 2,
        )
        for rc in revision_candidates:
            if review_added >= n_review:
                break
            qid = rc["question_id"]
            if qid in used_ids:
                continue
            q = store_v2.get(qid)
            if q is None:
                continue
            skill_id = skill_index.get_skill(qid)
            node = PREREQUISITE_GRAPH.get(skill_id)
            skill_name = node.name if node else skill_id

            planned.append(UnifiedPlannedQuestion(
                question_id=qid,
                skill_id=skill_id,
                skill_name=skill_name,
                difficulty_score=q.difficulty_score,
                slot_type="review",
                source_curriculum=_identify_source(q),
            ))
            used_ids.add(qid)
            skill_counts[skill_id] += 1
            curriculum_counts[_identify_source(q)] += 1
            review_added += 1

    # --- Fill remaining slots if session is short ---
    while len(planned) < session_size and active_skills:
        skill = random.choice(active_skills[:5])
        target = _get_skill_difficulty_target(user_id, skill.skill_id)
        if not _add_question(skill.skill_id, skill.skill_name, "core", target):
            break

    # --- Order: warmup → core (shuffled) → stretch → review ---
    warmups = [q for q in planned if q.slot_type == "warmup"]
    cores = [q for q in planned if q.slot_type == "core"]
    stretches = [q for q in planned if q.slot_type == "stretch"]
    reviews = [q for q in planned if q.slot_type == "review"]
    random.shuffle(cores)
    ordered = warmups + cores + stretches + reviews

    # --- Generate session message for parent ---
    focus_names = [s.skill_name for s in focus_skills[:2]]
    if welcome_back:
        msg = f"Welcome back! It's been {days_away} days — starting with some warm-up problems to rebuild confidence."
        if focus_names:
            msg += f" Then we'll practice {' and '.join(focus_names)}."
    elif focus_names:
        msg = f"Today's session focuses on {' and '.join(focus_names)}."
    else:
        msg = "Today's session covers a mix of skills for balanced practice."

    curricula_used = [k for k, v in curriculum_counts.items() if v > 0]
    if len(curricula_used) > 1:
        msg += f" Questions drawn from {len(curricula_used)} different approaches for deeper understanding."

    # --- Detect mastery transitions ---
    mastery_transitions = []
    for skill in focus_skills:
        if _is_skill_mastered(user_id, skill.skill_id, grade):
            mastery_transitions.append(skill.skill_name)

    return UnifiedSessionPlan(
        user_id=user_id,
        grade=grade,
        questions=ordered,
        focus_skills=[s.skill_id for s in focus_skills],
        skill_breakdown=dict(skill_counts),
        curriculum_mix=dict(curriculum_counts),
        session_message=msg,
        mastery_transitions=mastery_transitions,
    )


# ---------------------------------------------------------------------------
# Parent messaging — generated AFTER session completion
# ---------------------------------------------------------------------------

def generate_session_summary(
    user_id: str,
    grade: int,
    session_plan: UnifiedSessionPlan,
    results: List[Dict],  # [{question_id, correct, time_ms}, ...]
) -> ParentSessionSummary:
    """Generate a parent-facing summary after session completion.

    Called by the answer-check endpoint after the last question is answered.
    """
    total = len(results)
    correct = sum(1 for r in results if r.get("correct"))
    accuracy = correct / max(total, 1)

    # Identify which skills improved
    skills_practiced = list(set(q.skill_name for q in session_plan.questions))

    # --- Record per-skill responses and check mastery ---
    session_id = f"sess_{user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
    skill_session_results: Dict[str, List[bool]] = defaultdict(list)

    for r in results:
        qid = r.get("question_id", "")
        skill_id = skill_index.get_skill(qid)
        is_correct = r.get("correct", False)
        rt_ms = r.get("time_ms", 0)
        q = store_v2.get(qid)
        diff = q.difficulty_score if q else 100

        # Update per-skill theta
        skill_ability_store.record_response(
            user_id=user_id,
            skill_id=skill_id,
            correct=is_correct,
            difficulty_score=diff,
            response_time_ms=rt_ms,
            session_id=session_id,
        )
        skill_session_results[skill_id].append(is_correct)

    # Check mastery for each practiced skill
    new_masteries = []
    for skill_id, outcomes in skill_session_results.items():
        session_acc = sum(outcomes) / max(1, len(outcomes))
        newly_mastered = skill_ability_store.check_and_confirm_mastery(
            user_id=user_id,
            skill_id=skill_id,
            session_id=session_id,
            session_accuracy=session_acc,
        )
        if newly_mastered:
            node = PREREQUISITE_GRAPH.get(skill_id)
            if node:
                new_masteries.append(node.name)
            # Schedule FSRS review for newly mastered skill
            spaced_review_store.schedule_mastered_skill(user_id, skill_id)

    # Record FSRS review results for review-slot questions
    for r in results:
        qid = r.get("question_id", "")
        # Check if this was a review question
        review_qs = [q for q in session_plan.questions if q.slot_type == "review"]
        for rq in review_qs:
            if rq.question_id == qid:
                spaced_review_store.record_review(
                    user_id=user_id,
                    skill_id=rq.skill_id,
                    success=r.get("correct", False),
                )

    # --- Progress message ---
    if accuracy >= 0.9:
        tone = "Excellent work!"
    elif accuracy >= 0.7:
        tone = "Good progress!"
    elif accuracy >= 0.5:
        tone = "Keep practicing!"
    else:
        tone = "Building foundations —"

    skill_str = " and ".join(skills_practiced[:2])
    progress_msg = f"{tone} Got {correct}/{total} correct practicing {skill_str}."

    if new_masteries:
        progress_msg += f" Mastered: {', '.join(new_masteries)}!"

    # --- Next focus ---
    # Re-prioritise to see what's next
    candidates = _prioritise_skills(user_id, grade)
    next_skills = [c for c in candidates if c.priority >= 3.0][:2]
    if next_skills:
        next_names = " and ".join(s.skill_name for s in next_skills)
        next_focus = f"Next session will focus on {next_names}."
    else:
        next_focus = "Next session will reinforce and extend current skills."

    # --- Weekly trend (simplified — would normally query history) ---
    if accuracy >= 0.8:
        weekly_trend = "Accuracy trending up this week — great consistency!"
    elif accuracy >= 0.6:
        weekly_trend = "Steady progress this week — keep the daily practice going."
    else:
        weekly_trend = "Still building confidence — shorter, more frequent sessions help most."

    return ParentSessionSummary(
        session_id=f"sess_{user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
        user_id=user_id,
        date=datetime.now(timezone.utc).isoformat(),
        skills_practiced=skills_practiced,
        accuracy=round(accuracy * 100, 1),
        questions_correct=correct,
        questions_total=total,
        new_masteries=new_masteries,
        progress_message=progress_msg,
        next_focus=next_focus,
        weekly_trend=weekly_trend,
    )


# ---------------------------------------------------------------------------
# Within-session learning rate detection
# ---------------------------------------------------------------------------

def detect_learning_rate(
    session_results: List[Dict],
    skill_id: str,
) -> Dict[str, Any]:
    """Detect within-session learning rate for a specific skill.

    Compares performance on early vs. late items for the same skill.
    If accuracy improves significantly → fast learner → accelerate.
    If accuracy drops → struggling → scaffold more.

    Returns:
        {
            "trend": "accelerating" | "stable" | "struggling",
            "difficulty_adjustment": int (-15 to +15),
            "confidence": float (0-1),
        }
    """
    # Filter results for this skill
    skill_results = [r for r in session_results if r.get("skill_id") == skill_id]

    if len(skill_results) < 3:
        return {"trend": "stable", "difficulty_adjustment": 0, "confidence": 0.0}

    # Split into first half and second half
    mid = len(skill_results) // 2
    first_half = skill_results[:mid]
    second_half = skill_results[mid:]

    first_acc = sum(1 for r in first_half if r.get("correct")) / max(1, len(first_half))
    second_acc = sum(1 for r in second_half if r.get("correct")) / max(1, len(second_half))

    trend_delta = second_acc - first_acc
    confidence = min(1.0, len(skill_results) / 5.0)

    if trend_delta > 0.4:
        # Strong improvement — fast learner on this skill
        return {
            "trend": "accelerating",
            "difficulty_adjustment": +12,
            "confidence": confidence,
        }
    elif trend_delta > 0.2:
        # Moderate improvement
        return {
            "trend": "accelerating",
            "difficulty_adjustment": +7,
            "confidence": confidence,
        }
    elif trend_delta < -0.3:
        # Getting worse — struggling
        return {
            "trend": "struggling",
            "difficulty_adjustment": -12,
            "confidence": confidence,
        }
    elif trend_delta < -0.15:
        # Slight decline
        return {
            "trend": "struggling",
            "difficulty_adjustment": -7,
            "confidence": confidence,
        }

    return {"trend": "stable", "difficulty_adjustment": 0, "confidence": confidence}


def adjust_remaining_session(
    plan: UnifiedSessionPlan,
    results_so_far: List[Dict],
    current_index: int,
) -> UnifiedSessionPlan:
    """Mid-session adjustment: if student is learning fast, swap remaining
    questions for harder ones. If struggling, swap for easier ones.

    Called after each answer to potentially adjust upcoming questions.
    Only adjusts if confidence is high enough (≥3 results on same skill).
    """
    if current_index >= len(plan.questions) - 1:
        return plan  # No remaining questions to adjust

    # Check learning rate for each focus skill
    for skill_id in plan.focus_skills:
        rate_info = detect_learning_rate(results_so_far, skill_id)

        if rate_info["confidence"] < 0.6:
            continue  # Not enough data yet

        adjustment = rate_info["difficulty_adjustment"]
        if adjustment == 0:
            continue

        # Adjust remaining questions for this skill
        for i in range(current_index + 1, len(plan.questions)):
            q = plan.questions[i]
            if q.skill_id == skill_id:
                q.difficulty_score = max(1, min(300, q.difficulty_score + adjustment))

    return plan


def generate_weekly_report(
    user_id: str,
    grade: int,
    child_name: str = "Your child",
) -> str:
    """Generate a weekly parent report (called by scheduled task).

    Returns a multi-paragraph summary suitable for push notification or email.
    """
    candidates = _prioritise_skills(user_id, grade)

    mastered = [c for c in candidates if c.reason == "mastered"]
    weak = [c for c in candidates if c.priority >= 4.0]
    active = [c for c in candidates if c.priority == 3.0]

    # Build report
    lines = []

    # Opening
    lines.append(f"Weekly Math Report for {child_name} (Grade {grade})")
    lines.append("")

    # Strengths
    if mastered:
        strength_names = ", ".join(s.skill_name for s in mastered[:4])
        lines.append(f"Mastered skills: {strength_names}")

    # Active learning
    if active:
        active_names = ", ".join(s.skill_name for s in active[:3])
        lines.append(f"Currently building: {active_names}")

    # Areas needing attention
    if weak:
        weak_names = ", ".join(s.skill_name for s in weak[:3])
        lines.append(f"Needs more practice: {weak_names}")

    # Review status from FSRS
    review_summary = spaced_review_store.get_review_summary(user_id)
    if review_summary["due_for_review"] > 0:
        lines.append(
            f"Review needed: {review_summary['due_for_review']} mastered skills "
            f"are due for a refresh to keep them sharp."
        )

    # Recommendation
    lines.append("")
    if weak:
        lines.append(
            f"Recommendation: 15 minutes daily on {weak[0].skill_name} will "
            f"make the biggest difference this week."
        )
    elif active:
        lines.append(
            f"Recommendation: Keep up the daily practice! {child_name} is "
            f"building {active[0].skill_name} nicely."
        )
    else:
        lines.append(
            f"Amazing! {child_name} has mastered all grade-level skills. "
            f"We're serving challenge problems to keep them growing."
        )

    # Overall progress
    progress = skill_ability_store.get_skill_progress(user_id, grade)
    lines.append("")
    lines.append(
        f"Overall: {progress['mastered_skills']}/{progress['total_skills']} "
        f"skills mastered ({progress['mastery_percentage']}%)"
    )

    return "\n".join(lines)
