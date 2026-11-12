"""PawPal+ logic layer.

Backend classes for planning a pet owner's daily care tasks across one or more pets.
See diagrams/uml.mmd for the class diagram.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}
FREQUENCIES = {"daily", "weekly", "once"}


def to_minutes(hhmm: str) -> int:
    """Convert "HH:MM" to minutes after midnight."""
    hours, minutes = hhmm.split(":")
    h, m = int(hours), int(minutes)
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(f"Invalid time: {hhmm!r}")
    return h * 60 + m


def to_hhmm(minutes: int) -> str:
    """Convert minutes after midnight to "HH:MM"."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Task:
    """A single pet care activity, such as a walk, feeding, or medication."""

    description: str
    duration_minutes: int
    priority: str = "medium"           # "low" | "medium" | "high"
    frequency: str = "daily"           # "daily" | "weekly" | "once"
    time: str | None = None            # preferred start "HH:MM"; None = flexible
    category: str = "general"          # e.g. "walk", "feeding", "meds", "grooming"
    completed: bool = False
    last_completed: date | None = None
    pet_name: str = ""                 # set by Pet.add_task

    def __post_init__(self) -> None:
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {sorted(PRIORITY_RANK)}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {sorted(FREQUENCIES)}")
        if self.time is not None:
            to_minutes(self.time)  # raises on bad format

    def mark_complete(self, on: date | None = None) -> None:
        """Mark this task as done and record the date it was completed."""
        self.completed = True
        self.last_completed = on or date.today()

    def priority_rank(self) -> int:
        """Return a numeric rank for sorting (higher = more important)."""
        return PRIORITY_RANK[self.priority]

    def is_due_today(self, today: date | None = None) -> bool:
        """Return True if this task should appear in today's plan."""
        today = today or date.today()
        if self.last_completed is None:
            return True
        if self.frequency == "once":
            return False
        if self.frequency == "daily":
            return self.last_completed < today
        return (today - self.last_completed).days >= 7  # weekly


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
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task with this description. Returns True if one was removed."""
        for i, task in enumerate(self.tasks):
            if task.description == description:
                del self.tasks[i]
                return True
        return False

    def get_pending_tasks(self, today: date | None = None) -> list[Task]:
        """Return tasks that are due today and not yet done."""
        return [t for t in self.tasks if t.is_due_today(today)]


@dataclass
class Owner:
    """The pet owner, their daily time budget, and their pets."""

    name: str
    available_minutes: int = 120
    day_start: str = "08:00"           # "HH:MM" when the plan begins
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner. Pet names must be unique."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"{self.name} already has a pet named {pet.name!r}")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove a pet by name. Returns True if one was removed."""
        pet = self.get_pet(pet_name)
        if pet is None:
            return False
        self.pets.remove(pet)
        return True

    def get_pet(self, pet_name: str) -> Pet | None:
        """Look up a pet by name."""
        return next((p for p in self.pets if p.name == pet_name), None)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Builds a daily plan across all of an owner's pets within their time budget."""

    def __init__(self, owner: Owner, today: date | None = None) -> None:
        self.owner = owner
        self.today = today or date.today()
        self.plan: list[tuple[str, Task, str]] = []    # (start "HH:MM", task, reason)
        self.skipped: list[tuple[Task, str]] = []      # (task, reason)

    def collect_tasks(self) -> list[Task]:
        """Gather every pet's tasks via the Owner and keep the ones due today."""
        return [t for t in self.owner.get_all_tasks() if t.is_due_today(self.today)]

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (high first), then preferred time, then shortest first."""
        return sorted(
            tasks,
            key=lambda t: (-t.priority_rank(), t.time or "99:99", t.duration_minutes),
        )

    def generate_plan(self) -> list[tuple[str, Task, str]]:
        """Pick tasks that fit the owner's time budget and assign start times.

        1. Select: go through due tasks by priority and keep each one that still fits
           in the remaining minutes; the rest are skipped.
        2. Place: tasks with a preferred time are anchored at that time (or as soon after
           as possible); flexible tasks fill the gaps in priority order.
        """
        self.plan, self.skipped = [], []

        remaining = self.owner.available_minutes
        selected: list[Task] = []
        for task in self.sort_by_priority(self.collect_tasks()):
            if task.duration_minutes <= remaining:
                selected.append(task)
                remaining -= task.duration_minutes
            else:
                self.skipped.append(
                    (task, f"needs {task.duration_minutes} min, only {remaining} min left")
                )

        timed = sorted((t for t in selected if t.time), key=lambda t: to_minutes(t.time))
        flexible = [t for t in selected if not t.time]
        cursor = to_minutes(self.owner.day_start)

        def place(task: Task, start: int, reason: str) -> int:
            self.plan.append((to_hhmm(start), task, reason))
            return start + task.duration_minutes

        for anchor in timed:
            anchor_start = to_minutes(anchor.time)
            # Fill the gap before this anchored task with flexible tasks that fit.
            for task in list(flexible):
                if cursor + task.duration_minutes <= anchor_start:
                    cursor = place(task, cursor, f"{task.priority} priority, fits before {anchor.time}")
                    flexible.remove(task)
            start = max(cursor, anchor_start)
            if start == anchor_start:
                reason = f"{anchor.priority} priority, at preferred time {anchor.time}"
            else:
                reason = f"{anchor.priority} priority, preferred {anchor.time} but moved to avoid overlap"
            cursor = place(anchor, start, reason)

        for task in flexible:
            cursor = place(task, cursor, f"{task.priority} priority, next open slot")

        return self.plan

    def detect_conflicts(self) -> list[str]:
        """Return warnings for due tasks whose preferred time slots overlap (across all pets)."""
        timed = sorted(
            (t for t in self.collect_tasks() if t.time), key=lambda t: to_minutes(t.time)
        )
        warnings = []
        for i, a in enumerate(timed):
            a_end = to_minutes(a.time) + a.duration_minutes
            for b in timed[i + 1:]:
                if to_minutes(b.time) >= a_end:
                    break
                warnings.append(
                    f"'{a.description}' ({a.pet_name}, {a.time}, {a.duration_minutes} min) "
                    f"overlaps '{b.description}' ({b.pet_name}, {b.time})"
                )
        return warnings

    def explain_plan(self) -> str:
        """Return a human-readable explanation of what was scheduled and why."""
        if not self.plan and not self.skipped:
            self.generate_plan()

        used = sum(t.duration_minutes for _, t, _ in self.plan)
        lines = [
            f"Daily plan for {self.owner.name} "
            f"({used} of {self.owner.available_minutes} min used):"
        ]
        if not self.plan:
            lines.append("  Nothing scheduled.")
        for start, task, reason in self.plan:
            lines.append(
                f"  {start} - {task.description} for {task.pet_name} "
                f"({task.duration_minutes} min) - {reason}"
            )
        if self.skipped:
            lines.append("Skipped:")
            for task, reason in self.skipped:
                lines.append(f"  {task.description} for {task.pet_name} - {reason}")
        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("Conflicts:")
            lines.extend(f"  {c}" for c in conflicts)
        return "\n".join(lines)
