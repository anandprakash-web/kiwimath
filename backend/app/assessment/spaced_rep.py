"""
Spaced Repetition Engine — Half-Life Regression (HLR) inspired.

Based on Duolingo's approach (Settles & Meeder, 2016):
    P(recall) = 2^(-Δt / h)
    h = 2^(strength) × base_decay

Manages memory decay per skill, scheduling reviews when recall
probability drops below threshold, and updating strength on practice.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Optional


# Configuration
RECALL_THRESHOLD = 0.70  # Schedule review when P(recall) drops below this
BASE_DECAY_HOURS = 24.0  # Base half-life in hours (decays to 50% in 1 day at strength=0)
STRENGTH_GAIN_CORRECT = 0.4
STRENGTH_LOSS_INCORRECT = 0.8
MAX_STRENGTH = 6.0  # Cap: half-life = 2^6 * 24 = 1536 hours ≈ 64 days
MIN_STRENGTH = 0.0


@dataclass
class SkillMemory:
    """Memory state for a single skill."""
    skill_id: str
    student_id: str
    strength: float = 0.0  # Higher = longer half-life
    last_practiced: float = 0.0  # Unix timestamp
    consecutive_correct: int = 0
    total_attempts: int = 0
    total_correct: int = 0

    @property
    def half_life_hours(self) -> float:
        """Current half-life in hours."""
        return (2 ** self.strength) * BASE_DECAY_HOURS

    def recall_probability(self, current_time: Optional[float] = None) -> float:
        """P(recall) at the given time."""
        if self.last_practiced == 0:
            return 0.0  # Never practiced
        now = current_time or time.time()
        delta_hours = (now - self.last_practiced) / 3600.0
        if delta_hours <= 0:
            return 1.0
        h = self.half_life_hours
        return 2 ** (-delta_hours / h)

    def needs_review(self, current_time: Optional[float] = None) -> bool:
        """Whether this skill should be reviewed."""
        if self.last_practiced == 0:
            return True
        return self.recall_probability(current_time) < RECALL_THRESHOLD

    def review_priority(self, current_time: Optional[float] = None) -> float:
        """Priority score for scheduling. Higher = more urgent."""
        p = self.recall_probability(current_time)
        if p >= RECALL_THRESHOLD:
            return 0.0
        return 1.0 - p  # More decayed = higher priority

    def time_until_review(self, current_time: Optional[float] = None) -> float:
        """Hours until P(recall) drops below threshold."""
        now = current_time or time.time()
        if self.last_practiced == 0:
            return 0.0
        h = self.half_life_hours
        # Solve: 2^(-t/h) = RECALL_THRESHOLD
        # -t/h = log2(RECALL_THRESHOLD)
        # t = -h * log2(RECALL_THRESHOLD)
        t_hours = -h * math.log2(RECALL_THRESHOLD)
        elapsed = (now - self.last_practiced) / 3600.0
        remaining = t_hours - elapsed
        return max(0.0, remaining)


class SpacedRepEngine:
    """Manages spaced repetition scheduling for all students."""

    def __init__(self):
        self._memories: dict[str, dict[str, SkillMemory]] = {}
        # student_id -> {skill_id -> SkillMemory}

    def get_memory(self, student_id: str, skill_id: str) -> SkillMemory:
        """Get or create memory state for a student-skill pair."""
        if student_id not in self._memories:
            self._memories[student_id] = {}
        if skill_id not in self._memories[student_id]:
            self._memories[student_id][skill_id] = SkillMemory(
                skill_id=skill_id, student_id=student_id
            )
        return self._memories[student_id][skill_id]

    def record_practice(
        self,
        student_id: str,
        skill_id: str,
        correct: bool,
        current_time: Optional[float] = None,
    ) -> SkillMemory:
        """Record a practice attempt and update memory strength."""
        now = current_time or time.time()
        memory = self.get_memory(student_id, skill_id)

        memory.total_attempts += 1

        if correct:
            memory.total_correct += 1
            memory.consecutive_correct += 1
            # Bonus for consecutive correct answers
            bonus = min(0.2, memory.consecutive_correct * 0.05)
            memory.strength = min(
                MAX_STRENGTH,
                memory.strength + STRENGTH_GAIN_CORRECT + bonus,
            )
        else:
            memory.consecutive_correct = 0
            memory.strength = max(
                MIN_STRENGTH,
                memory.strength - STRENGTH_LOSS_INCORRECT,
            )

        memory.last_practiced = now
        return memory

    def get_review_queue(
        self,
        student_id: str,
        max_items: int = 10,
        current_time: Optional[float] = None,
    ) -> list[SkillMemory]:
        """Get skills that need review, sorted by priority."""
        if student_id not in self._memories:
            return []

        now = current_time or time.time()
        needs_review = [
            mem for mem in self._memories[student_id].values()
            if mem.needs_review(now)
        ]

        # Sort by priority (most decayed first)
        needs_review.sort(key=lambda m: -m.review_priority(now))
        return needs_review[:max_items]

    def get_all_skills(self, student_id: str) -> list[SkillMemory]:
        """Get all skill memories for a student."""
        if student_id not in self._memories:
            return []
        return list(self._memories[student_id].values())

    def get_skill_health(self, student_id: str) -> dict:
        """Summary of student's memory health across all skills."""
        skills = self.get_all_skills(student_id)
        if not skills:
            return {"total_skills": 0, "mastered": 0, "decaying": 0, "new": 0}

        now = time.time()
        mastered = sum(1 for s in skills if s.recall_probability(now) > 0.9)
        decaying = sum(1 for s in skills if s.needs_review(now))
        fresh = sum(
            1 for s in skills
            if 0.7 <= s.recall_probability(now) <= 0.9
        )

        return {
            "total_skills": len(skills),
            "mastered": mastered,
            "fresh": fresh,
            "decaying": decaying,
            "avg_strength": round(
                sum(s.strength for s in skills) / len(skills), 2
            ),
        }

    def build_session_mix(
        self,
        student_id: str,
        new_skills: list[str],
        total_items: int = 10,
        current_time: Optional[float] = None,
    ) -> dict[str, list[str]]:
        """Build a practice session mixing new content, review, and adaptive practice.

        Returns:
            {"new": [...skill_ids], "review": [...skill_ids], "adaptive": [...skill_ids]}

        Mix ratio: 40% new, 30% review, 30% adaptive (at ability boundary)
        """
        n_new = max(1, int(total_items * 0.4))
        n_review = max(1, int(total_items * 0.3))
        n_adaptive = total_items - n_new - n_review

        # Get review items
        review_queue = self.get_review_queue(student_id, max_items=n_review, current_time=current_time)
        review_ids = [m.skill_id for m in review_queue]

        # New items from the learning path
        new_ids = new_skills[:n_new]

        # Adaptive: skills near the boundary (P(recall) between 0.5 and 0.8)
        now = current_time or time.time()
        all_skills = self.get_all_skills(student_id)
        boundary_skills = [
            s for s in all_skills
            if 0.5 <= s.recall_probability(now) <= 0.8
            and s.skill_id not in review_ids
        ]
        boundary_skills.sort(key=lambda s: abs(s.recall_probability(now) - 0.65))
        adaptive_ids = [s.skill_id for s in boundary_skills[:n_adaptive]]

        return {
            "new": new_ids,
            "review": review_ids,
            "adaptive": adaptive_ids,
        }

    def export_state(self, student_id: str) -> list[dict]:
        """Export student's memory state for persistence."""
        skills = self.get_all_skills(student_id)
        return [
            {
                "skill_id": s.skill_id,
                "strength": s.strength,
                "last_practiced": s.last_practiced,
                "consecutive_correct": s.consecutive_correct,
                "total_attempts": s.total_attempts,
                "total_correct": s.total_correct,
            }
            for s in skills
        ]

    def import_state(self, student_id: str, state: list[dict]) -> None:
        """Import student's memory state from persistence."""
        if student_id not in self._memories:
            self._memories[student_id] = {}
        for s in state:
            memory = SkillMemory(
                skill_id=s["skill_id"],
                student_id=student_id,
                strength=s.get("strength", 0.0),
                last_practiced=s.get("last_practiced", 0.0),
                consecutive_correct=s.get("consecutive_correct", 0),
                total_attempts=s.get("total_attempts", 0),
                total_correct=s.get("total_correct", 0),
            )
            self._memories[student_id][s["skill_id"]] = memory
