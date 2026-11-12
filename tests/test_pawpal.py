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
