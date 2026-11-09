"""PawPal+ logic layer.

Class skeletons generated from diagrams/uml.mmd. Method bodies are stubs;
scheduling logic is implemented in a later phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}


@dataclass
class Task:
    """A single pet care activity, such as a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    priority: str = "medium"          # "low" | "medium" | "high"
    category: str = "general"         # e.g. "walk", "feeding", "meds", "grooming"
    frequency: str = "daily"          # "daily" | "weekly" | "once"
    preferred_time: str | None = None  # "HH:MM", optional
    completed: bool = False
    last_completed: date | None = None  # needed so is_due_today() can handle weekly tasks

    def mark_complete(self) -> None:
        """Mark this task as done and record today's date."""
        pass

    def priority_rank(self) -> int:
        """Return a numeric rank for sorting (higher = more important)."""
        pass

    def is_due_today(self) -> bool:
        """Return True if this task should appear in today's plan."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove a task by its title."""
        pass

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        pass


@dataclass
class Owner:
    """The pet owner, their daily time budget, and their pets."""

    name: str
    available_minutes: int = 120
    day_start: str = "08:00"          # "HH:MM" when the plan begins
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        pass

    def get_pet(self, pet_name: str) -> Pet | None:
        """Look up a pet by name."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        pass


class Scheduler:
    """Builds a daily plan for an owner's pets within their time budget."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.plan: list[tuple[str, Pet, Task]] = []  # (start "HH:MM", pet, task)
        self.skipped: list[Task] = []

    def collect_tasks(self) -> list[tuple[Pet, Task]]:
        """Gather pending, due-today tasks paired with the pet they belong to."""
        pass

    def sort_by_priority(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order tasks by priority, then by preferred time / duration."""
        pass

    def generate_plan(self) -> list[tuple[str, Pet, Task]]:
        """Fit tasks into the owner's available time and assign start times."""
        pass

    def detect_conflicts(self) -> list[str]:
        """Return warnings for tasks whose time slots overlap."""
        pass

    def explain_plan(self) -> str:
        """Return a human-readable explanation of what was scheduled and why."""
        pass
