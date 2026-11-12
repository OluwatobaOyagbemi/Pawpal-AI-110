"""Quick tests for PawPal+ core classes."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    """mark_complete() sets completed to True and records the date."""
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True
    assert task.last_completed is not None


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet increases its task count and tags the task with the pet's name."""
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", 10, "high"))

    assert len(pet.tasks) == 1
    assert pet.tasks[0].pet_name == "Mochi"


# --- Smarter scheduling -----------------------------------------------------

from datetime import date, timedelta

from pawpal_system import Owner, Scheduler

TODAY = date(2026, 11, 11)


def make_scheduler():
    """Owner with two pets whose tasks are added out of time order."""
    owner = Owner("Jordan")
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Puzzle toy", 25, time="09:30"))
    luna.add_task(Task("Litter box", 10))
    mochi.add_task(Task("Morning walk", 30, time="8:00"))   # unpadded on purpose
    luna.add_task(Task("Give meds", 5, time="08:15", frequency="once"))
    return Scheduler(owner, today=TODAY)


def test_sort_by_time_orders_times_and_puts_flexible_last():
    """sort_by_time() orders by HH:MM, handles unpadded input, and puts untimed tasks last."""
    order = [t.description for t in make_scheduler().sort_by_time()]
    assert order == ["Morning walk", "Give meds", "Puzzle toy", "Litter box"]


def test_filter_tasks_by_pet_and_status():
    """filter_tasks() combines pet and completion filters."""
    scheduler = make_scheduler()
    assert {t.description for t in scheduler.filter_tasks(pet_name="Luna")} == {"Litter box", "Give meds"}

    meds = scheduler.filter_tasks(pet_name="Luna")[1]
    scheduler.mark_task_complete(meds)
    assert scheduler.filter_tasks(pet_name="Luna", completed=True) == [meds]
    assert [t.description for t in scheduler.filter_tasks(pet_name="Luna", completed=False)] == ["Litter box"]


def test_completing_daily_task_creates_copy_due_tomorrow():
    """A completed daily task gets a new instance due the next day, not due today."""
    scheduler = make_scheduler()
    walk = scheduler.filter_tasks(pet_name="Mochi")[1]

    new = scheduler.mark_task_complete(walk)

    assert new is not None and new is not walk
    assert new.due_date == TODAY + timedelta(days=1)
    assert new.completed is False and new.pet_name == "Mochi"
    assert walk not in scheduler.collect_tasks() and new not in scheduler.collect_tasks()
    assert new.is_due_today(TODAY + timedelta(days=1))


def test_completing_weekly_task_due_in_seven_days():
    """Weekly tasks repeat seven days after completion."""
    scheduler = make_scheduler()
    brush = Task("Brush coat", 20, frequency="weekly")
    scheduler.owner.get_pet("Luna").add_task(brush)

    assert scheduler.mark_task_complete(brush).due_date == TODAY + timedelta(days=7)


def test_once_task_does_not_repeat_and_double_complete_is_ignored():
    """One-time tasks create no copy, and completing a task twice adds nothing."""
    scheduler = make_scheduler()
    meds = scheduler.filter_tasks(pet_name="Luna")[1]
    count = len(scheduler.owner.get_all_tasks())

    assert scheduler.mark_task_complete(meds) is None
    assert scheduler.mark_task_complete(meds) is None
    assert len(scheduler.owner.get_all_tasks()) == count


def test_detect_conflicts_flags_same_time_without_raising():
    """Two tasks at the same time produce a warning string instead of an error."""
    scheduler = make_scheduler()
    scheduler.owner.get_pet("Luna").add_task(Task("Breakfast", 5, time="09:30"))

    warnings = scheduler.detect_conflicts()

    assert any("both scheduled at 09:30" in w for w in warnings)


def test_no_conflicts_when_tasks_do_not_overlap():
    """Back-to-back tasks are not conflicts."""
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, time="08:00"))
    pet.add_task(Task("Feed", 10, time="08:30"))
    assert Scheduler(owner, today=TODAY).detect_conflicts() == []
