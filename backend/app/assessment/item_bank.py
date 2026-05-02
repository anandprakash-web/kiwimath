"""
Item Bank — manages the pool of calibrated assessment items.

Handles:
- Loading items with IRT parameters
- Filtering by domain, curriculum, grade, state
- Exposure tracking and control
- Item health monitoring
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from .irt_model import ItemParameters


@dataclass
class ItemHealth:
    """Health metrics for monitoring item quality."""
    item_id: str
    total_responses: int = 0
    correct_count: int = 0
    avg_response_time_sec: float = 0.0
    empirical_difficulty: float = 0.0  # observed p-value
    fit_residual: float = 0.0
    exposure_rate: float = 0.0
    last_calibrated: Optional[str] = None  # ISO timestamp

    @property
    def p_value(self) -> float:
        if self.total_responses == 0:
            return 0.5
        return self.correct_count / self.total_responses

    @property
    def needs_review(self) -> bool:
        """Flag items that need human review."""
        if self.total_responses < 50:
            return False
        return (
            self.fit_residual > 3.0
            or self.exposure_rate > 0.20
            or self.avg_response_time_sec < 5.0
            or self.avg_response_time_sec > 180.0
        )


class ItemBank:
    """In-memory item bank with filtering and selection support."""

    def __init__(self):
        self._items: dict[str, ItemParameters] = {}
        self._health: dict[str, ItemHealth] = {}
        self._recently_seen: dict[str, set[str]] = {}
        # student_id -> set of item_ids seen in last 30 days

    def add_item(self, item: ItemParameters) -> None:
        self._items[item.item_id] = item
        if item.item_id not in self._health:
            self._health[item.item_id] = ItemHealth(item_id=item.item_id)

    def add_items(self, items: list[ItemParameters]) -> None:
        for item in items:
            self.add_item(item)

    def get_item(self, item_id: str) -> Optional[ItemParameters]:
        return self._items.get(item_id)

    @property
    def size(self) -> int:
        return len(self._items)

    def get_eligible_items(
        self,
        domain: Optional[str] = None,
        curriculum: Optional[str] = None,
        grade: Optional[int] = None,
        exclude_ids: Optional[set[str]] = None,
        student_id: Optional[str] = None,
        state: str = "active",
    ) -> list[ItemParameters]:
        """Get items matching all filter criteria."""
        exclude = exclude_ids or set()
        seen = self._recently_seen.get(student_id, set()) if student_id else set()

        results = []
        for item in self._items.values():
            if item.state != state:
                continue
            if item.item_id in exclude:
                continue
            if item.item_id in seen:
                continue
            if domain and item.domain != domain:
                continue
            if curriculum and curriculum not in item.curriculum_tags:
                continue
            if grade and not (item.grade_range[0] <= grade <= item.grade_range[1]):
                continue
            results.append(item)

        return results

    def get_field_test_items(
        self,
        domain: Optional[str] = None,
        n: int = 2,
    ) -> list[ItemParameters]:
        """Get unscored field test items to seed into sessions."""
        candidates = self.get_eligible_items(domain=domain, state="field_test")
        if len(candidates) <= n:
            return candidates
        return random.sample(candidates, n)

    def record_exposure(self, item_id: str, student_id: str) -> None:
        """Track that a student saw this item."""
        if student_id not in self._recently_seen:
            self._recently_seen[student_id] = set()
        self._recently_seen[student_id].add(item_id)

        if item_id in self._items:
            self._items[item_id].exposure_count += 1

    def record_response(
        self,
        item_id: str,
        correct: bool,
        response_time_sec: float,
    ) -> None:
        """Update item health metrics with a new response."""
        health = self._health.get(item_id)
        if not health:
            health = ItemHealth(item_id=item_id)
            self._health[item_id] = health

        n = health.total_responses
        health.total_responses += 1
        if correct:
            health.correct_count += 1
        # Running average of response time
        health.avg_response_time_sec = (
            (health.avg_response_time_sec * n + response_time_sec) / (n + 1)
        )

    def get_health(self, item_id: str) -> Optional[ItemHealth]:
        return self._health.get(item_id)

    def get_items_needing_review(self) -> list[ItemHealth]:
        """Return all items flagged for review."""
        return [h for h in self._health.values() if h.needs_review]

    def get_domain_stats(self) -> dict[str, dict]:
        """Summary stats per domain."""
        stats: dict[str, dict] = {}
        for item in self._items.values():
            if item.domain not in stats:
                stats[item.domain] = {
                    "total": 0, "active": 0, "field_test": 0, "retired": 0,
                    "avg_difficulty": 0.0, "difficulties": [],
                }
            s = stats[item.domain]
            s["total"] += 1
            s[item.state] = s.get(item.state, 0) + 1
            s["difficulties"].append(item.b)

        for domain, s in stats.items():
            if s["difficulties"]:
                s["avg_difficulty"] = sum(s["difficulties"]) / len(s["difficulties"])
            del s["difficulties"]

        return stats

    def to_dict_list(self) -> list[dict]:
        """Export all items as dicts (for persistence)."""
        return [
            {
                "item_id": item.item_id,
                "a": item.a, "b": item.b, "c": item.c,
                "domain": item.domain,
                "subdomain": item.subdomain,
                "curriculum_tags": item.curriculum_tags,
                "grade_range": list(item.grade_range),
                "exposure_count": item.exposure_count,
                "state": item.state,
            }
            for item in self._items.values()
        ]

    @classmethod
    def from_dict_list(cls, items: list[dict]) -> "ItemBank":
        """Load item bank from serialized dicts."""
        bank = cls()
        for d in items:
            item = ItemParameters(
                item_id=d["item_id"],
                a=d["a"], b=d["b"], c=d["c"],
                domain=d.get("domain", ""),
                subdomain=d.get("subdomain", ""),
                curriculum_tags=d.get("curriculum_tags", []),
                grade_range=tuple(d.get("grade_range", [1, 6])),
                exposure_count=d.get("exposure_count", 0),
                state=d.get("state", "active"),
            )
            bank.add_item(item)
        return bank
