"""Automated tests for the PawPal+ system (pawpal_system.py).

Sections: task basics, sorting, filtering, recurrence, conflict detection,
plan generation, and edge cases. Every Scheduler gets a fixed `today` so the
results don't depend on the day the tests run.
"""

import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Owner, Pet, Scheduler, Task

TODAY = date(2026, 11, 11)


def make_owner(**owner_kwargs):
    """Owner with two empty pets, Mochi (dog) and Luna (cat)."""
    owner = Owner("Jordan", **owner_kwargs)
    owner.add_pet(Pet("Mochi", "dog"))
    owner.add_pet(Pet("Luna", "cat"))
    return owner


def make_scheduler():
    """Scheduler over two pets whose tasks were added out of time order."""
    owner = make_owner()
    mochi, luna = owner.get_pet("Mochi"), owner.get_pet("Luna")
    mochi.add_task(Task("Puzzle toy", 25, time="09:30"))
    luna.add_task(Task("Litter box", 10))
    mochi.add_task(Task("Morning walk", 30, time="8:00"))   # unpadded on purpose
    luna.add_task(Task("Give meds", 5, time="08:15", frequency="once"))
    return Scheduler(owner, today=TODAY)


def get_task(scheduler, description):
    """Find a task by description across all pets."""
    return next(t for t in scheduler.owner.get_all_tasks() if t.description == description)


# --- Task basics ------------------------------------------------------------

def test_mark_complete_changes_status():
    """mark_complete() sets completed to True and records the date."""
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete(TODAY)

    assert task.completed is True
    assert task.last_completed == TODAY


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet increases its task count and tags the task with the pet's name."""
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", 10, "high"))

    assert len(pet.tasks) == 1
    assert pet.tasks[0].pet_name == "Mochi"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"duration_minutes": 0},
        {"duration_minutes": -5},
        {"priority": "urgent"},
        {"frequency": "monthly"},
        {"time": "25:00"},
        {"time": "08:60"},
        {"time": "8am"},
    ],
)
def test_invalid_task_values_raise(kwargs):
    """Bad durations, priorities, frequencies, and times are rejected when the task is created."""
    args = {"description": "Walk", "duration_minutes": 30, **kwargs}
    with pytest.raises(ValueError):
        Task(**args)


def test_duplicate_pet_name_raises():
    """An owner can't have two pets with the same name."""
    owner = make_owner()
    with pytest.raises(ValueError):
        owner.add_pet(Pet("Mochi", "cat"))


# --- Sorting ----------------------------------------------------------------

def test_sort_by_time_is_chronological_with_flexible_last():
    """sort_by_time() orders by HH:MM, handles unpadded input, and puts untimed tasks last."""
    order = [t.description for t in make_scheduler().sort_by_time()]
    assert order == ["Morning walk", "Give meds", "Puzzle toy", "Litter box"]


def test_sort_by_time_keeps_insertion_order_for_ties():
    """Tasks at the same time keep the order they were added (sorted() is stable)."""
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Walk", 30, time="08:00"))
    owner.get_pet("Luna").add_task(Task("Feed", 5, time="08:00"))
    owner.get_pet("Luna").add_task(Task("Early meds", 5, time="07:00"))

    order = [t.description for t in Scheduler(owner, today=TODAY).sort_by_time()]

    assert order == ["Early meds", "Walk", "Feed"]


def test_sort_by_time_does_not_change_original_list():
    """Sorting returns a new list instead of reordering the pet's tasks."""
    scheduler = make_scheduler()
    before = [t.description for t in scheduler.owner.get_all_tasks()]
    scheduler.sort_by_time()
    assert [t.description for t in scheduler.owner.get_all_tasks()] == before


def test_sort_by_priority_high_first_then_time_then_shortest():
    """sort_by_priority() breaks priority ties by preferred time, then by duration."""
    owner = make_owner()
    pet = owner.get_pet("Mochi")
    pet.add_task(Task("Low", 5, "low", time="07:00"))
    pet.add_task(Task("High late", 10, "high", time="09:00"))
    pet.add_task(Task("High early", 10, "high", time="08:00"))
    pet.add_task(Task("High flexible long", 20, "high"))
    pet.add_task(Task("High flexible short", 5, "high"))
    scheduler = Scheduler(owner, today=TODAY)

    order = [t.description for t in scheduler.sort_by_priority(owner.get_all_tasks())]

    assert order == ["High early", "High late", "High flexible short", "High flexible long", "Low"]


# --- Filtering --------------------------------------------------------------

def test_filter_tasks_by_pet_and_status():
    """filter_tasks() combines pet and completion filters."""
    scheduler = make_scheduler()
    assert {t.description for t in scheduler.filter_tasks(pet_name="Luna")} == {"Litter box", "Give meds"}

    meds = get_task(scheduler, "Give meds")
    scheduler.mark_task_complete(meds)

    assert scheduler.filter_tasks(pet_name="Luna", completed=True) == [meds]
    assert [t.description for t in scheduler.filter_tasks(pet_name="Luna", completed=False)] == ["Litter box"]


def test_filter_tasks_with_no_filters_returns_everything():
    """With no filters, filter_tasks() returns every task."""
    scheduler = make_scheduler()
    assert scheduler.filter_tasks() == scheduler.owner.get_all_tasks()


def test_filter_tasks_unknown_pet_returns_empty():
    """Filtering by a pet that doesn't exist gives an empty list, not an error."""
    assert make_scheduler().filter_tasks(pet_name="Rex") == []


# --- Recurrence -------------------------------------------------------------

def test_completing_daily_task_creates_copy_due_tomorrow():
    """A completed daily task gets a new instance due the next day, not due today."""
    scheduler = make_scheduler()
    walk = get_task(scheduler, "Morning walk")

    new = scheduler.mark_task_complete(walk)

    assert new is not None and new is not walk
    assert new.due_date == TODAY + timedelta(days=1)
    assert new.completed is False and new.pet_name == "Mochi"
    assert new.description == walk.description and new.time == walk.time
    assert new in scheduler.owner.get_pet("Mochi").tasks
    assert walk not in scheduler.collect_tasks() and new not in scheduler.collect_tasks()
    assert new.is_due_today(TODAY + timedelta(days=1))


def test_completing_weekly_task_due_in_seven_days():
    """Weekly tasks repeat seven days after completion and aren't due before then."""
    scheduler = make_scheduler()
    brush = Task("Brush coat", 20, frequency="weekly")
    scheduler.owner.get_pet("Luna").add_task(brush)

    new = scheduler.mark_task_complete(brush)

    assert new.due_date == TODAY + timedelta(days=7)
    assert not new.is_due_today(TODAY + timedelta(days=6))
    assert new.is_due_today(TODAY + timedelta(days=7))


@pytest.mark.parametrize(
    "done_on, expected",
    [
        (date(2026, 12, 31), date(2027, 1, 1)),   # year boundary
        (date(2026, 1, 31), date(2026, 2, 1)),    # month boundary
        (date(2028, 2, 28), date(2028, 2, 29)),   # leap year
    ],
)
def test_daily_recurrence_across_calendar_boundaries(done_on, expected):
    """timedelta rolls over months, years, and leap days correctly."""
    owner = make_owner()
    task = Task("Feed", 10)
    owner.get_pet("Mochi").add_task(task)

    assert Scheduler(owner, today=done_on).mark_task_complete(task).due_date == expected


def test_once_task_does_not_repeat_and_double_complete_is_ignored():
    """One-time tasks create no copy, and completing a task twice adds nothing."""
    scheduler = make_scheduler()
    meds = get_task(scheduler, "Give meds")
    count = len(scheduler.owner.get_all_tasks())

    assert scheduler.mark_task_complete(meds) is None
    assert scheduler.mark_task_complete(meds) is None
    assert len(scheduler.owner.get_all_tasks()) == count


def test_overdue_task_is_still_due():
    """A task whose due date has passed stays in today's plan instead of disappearing."""
    task = Task("Feed", 10, due_date=TODAY - timedelta(days=3))
    assert task.is_due_today(TODAY)


def test_mark_task_complete_for_task_without_pet_raises():
    """A task that was never added to one of the owner's pets can't be completed via the Scheduler."""
    scheduler = make_scheduler()
    with pytest.raises(ValueError):
        scheduler.mark_task_complete(Task("Stray task", 10))


# --- Conflict detection -----------------------------------------------------

def test_detect_conflicts_flags_duplicate_times_across_pets():
    """Two tasks for different pets at the same time produce a warning string, not an error."""
    scheduler = make_scheduler()
    scheduler.owner.get_pet("Luna").add_task(Task("Breakfast", 5, time="09:30"))

    warnings = scheduler.detect_conflicts()

    assert any("both scheduled at 09:30" in w for w in warnings)


def test_detect_conflicts_flags_duplicate_times_for_same_pet():
    """Two tasks for the same pet at the same time are also flagged."""
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Walk", 30, time="08:00"))
    owner.get_pet("Mochi").add_task(Task("Feed", 10, time="08:00"))

    warnings = Scheduler(owner, today=TODAY).detect_conflicts()

    assert warnings == ["'Walk' (Mochi) and 'Feed' (Mochi) are both scheduled at 08:00"]


def test_detect_conflicts_flags_partial_overlap():
    """A task that starts while another is still running is flagged as an overlap."""
    warnings = make_scheduler().detect_conflicts()   # walk 08:00-08:30, meds 08:15
    assert len(warnings) == 1
    assert "'Morning walk'" in warnings[0] and "overlaps 'Give meds'" in warnings[0]


def test_three_tasks_at_same_time_give_every_pair():
    """Three tasks at one time produce three pairwise warnings."""
    owner = make_owner()
    for name in ("A", "B", "C"):
        owner.get_pet("Mochi").add_task(Task(name, 10, time="08:00"))

    assert len(Scheduler(owner, today=TODAY).detect_conflicts()) == 3


def test_no_conflicts_when_tasks_are_back_to_back():
    """A task that starts exactly when another ends is not a conflict."""
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Walk", 30, time="08:00"))
    owner.get_pet("Mochi").add_task(Task("Feed", 10, time="08:30"))
    assert Scheduler(owner, today=TODAY).detect_conflicts() == []


def test_completed_tasks_are_not_conflicts():
    """Once one of two clashing tasks is done, the warning goes away."""
    owner = make_owner()
    walk = Task("Walk", 30, time="08:00")
    owner.get_pet("Mochi").add_task(walk)
    owner.get_pet("Luna").add_task(Task("Feed", 5, time="08:00"))
    scheduler = Scheduler(owner, today=TODAY)

    scheduler.mark_task_complete(walk)

    assert scheduler.detect_conflicts() == []


# --- Plan generation --------------------------------------------------------

def test_plan_anchors_timed_tasks_and_fills_gaps_with_flexible_ones():
    """Flexible tasks fill time before a timed task, which stays at its preferred time."""
    owner = make_owner(day_start="07:30")
    owner.get_pet("Mochi").add_task(Task("Walk", 30, "high", time="08:00"))
    owner.get_pet("Luna").add_task(Task("Litter box", 10))
    owner.get_pet("Luna").add_task(Task("Brush", 15, "low"))

    plan = Scheduler(owner, today=TODAY).generate_plan()

    assert [(start, t.description) for start, t, _ in plan] == [
        ("07:30", "Litter box"),
        ("07:40", "Brush"),
        ("08:00", "Walk"),
    ]


def test_plan_moves_overlapping_task_to_next_free_slot():
    """When two preferred times overlap, the later task starts when the earlier one ends."""
    plan = make_scheduler().generate_plan()
    starts = {t.description: start for start, t, _ in plan}

    assert starts["Morning walk"] == "08:00"
    assert starts["Give meds"] == "08:30"
    assert "moved to avoid overlap" in next(r for _, t, r in plan if t.description == "Give meds")


def test_plan_has_no_overlapping_slots():
    """However tasks are set up, no two planned tasks run at the same time."""
    scheduler = make_scheduler()
    scheduler.owner.get_pet("Luna").add_task(Task("Breakfast", 5, time="08:00"))
    plan = scheduler.generate_plan()

    def minutes(hhmm):
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    slots = sorted((minutes(s), minutes(s) + t.duration_minutes) for s, t, _ in plan)
    for (_, end), (next_start, _) in zip(slots, slots[1:]):
        assert next_start >= end


def test_plan_skips_low_priority_when_time_runs_out():
    """Higher-priority tasks are chosen first; tasks that don't fit are skipped with a reason."""
    owner = make_owner(available_minutes=40)
    owner.get_pet("Mochi").add_task(Task("Grooming", 30, "low"))
    owner.get_pet("Mochi").add_task(Task("Walk", 30, "high"))
    owner.get_pet("Luna").add_task(Task("Meds", 10, "high"))
    scheduler = Scheduler(owner, today=TODAY)

    plan = scheduler.generate_plan()

    assert {t.description for _, t, _ in plan} == {"Walk", "Meds"}
    assert [(t.description, reason) for t, reason in scheduler.skipped] == [
        ("Grooming", "needs 30 min, only 0 min left")
    ]


def test_task_exactly_filling_the_budget_is_scheduled():
    """A task whose duration equals the remaining minutes still fits."""
    owner = make_owner(available_minutes=30)
    owner.get_pet("Mochi").add_task(Task("Walk", 30))
    scheduler = Scheduler(owner, today=TODAY)

    assert len(scheduler.generate_plan()) == 1
    assert scheduler.skipped == []


def test_plan_leaves_out_completed_and_future_tasks():
    """Done tasks and recurring copies due tomorrow are not in today's plan."""
    scheduler = make_scheduler()
    scheduler.mark_task_complete(get_task(scheduler, "Morning walk"))

    planned = [t.description for _, t, _ in scheduler.generate_plan()]

    assert "Morning walk" not in planned
    assert sorted(planned) == ["Give meds", "Litter box", "Puzzle toy"]


def test_explain_plan_lists_schedule_skips_and_conflicts():
    """explain_plan() gives a readable summary including skipped tasks and conflicts.

    All four tasks are medium priority, so ties go to timed tasks first: the walk,
    meds, and puzzle (60 min) fill the budget and the flexible litter box is skipped.
    """
    scheduler = make_scheduler()
    scheduler.owner.available_minutes = 60

    text = scheduler.explain_plan()

    assert text.startswith("Daily plan for Jordan (60 of 60 min used):")
    assert "Skipped:" in text and "Litter box" in text.split("Skipped:")[1]
    assert "Conflicts:" in text


# --- Edge cases: empty owners and pets --------------------------------------

def test_owner_with_no_pets_gets_empty_plan():
    """An owner with no pets has no tasks, no plan, and no conflicts."""
    scheduler = Scheduler(Owner("Jordan"), today=TODAY)

    assert scheduler.generate_plan() == []
    assert scheduler.sort_by_time() == []
    assert scheduler.filter_tasks() == []
    assert scheduler.detect_conflicts() == []
    assert "Nothing scheduled." in scheduler.explain_plan()


def test_pet_with_no_tasks_is_handled():
    """A pet with no tasks has nothing pending and doesn't break planning for other pets."""
    scheduler = make_scheduler()
    scheduler.owner.add_pet(Pet("Rex", "dog"))

    assert scheduler.owner.get_pet("Rex").get_pending_tasks(TODAY) == []
    assert scheduler.filter_tasks(pet_name="Rex") == []
    assert len(scheduler.generate_plan()) == 4


def test_zero_available_minutes_skips_everything():
    """With no time available, every task is skipped and the plan is empty."""
    scheduler = make_scheduler()
    scheduler.owner.available_minutes = 0

    assert scheduler.generate_plan() == []
    assert len(scheduler.skipped) == 4


def test_remove_task_and_remove_pet():
    """Removing returns True when something was removed and False otherwise."""
    owner = make_owner()
    owner.get_pet("Mochi").add_task(Task("Walk", 30))

    assert owner.get_pet("Mochi").remove_task("Walk") is True
    assert owner.get_pet("Mochi").remove_task("Walk") is False
    assert owner.remove_pet("Luna") is True
    assert owner.remove_pet("Luna") is False
    assert [p.name for p in owner.pets] == ["Mochi"]
