# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🧩 Implementation Summary

The logic lives in `pawpal_system.py` in four classes:

- **`Task`** (dataclass): one care activity with a description, duration, priority (low/medium/high), frequency (daily/weekly/once), an optional preferred time, and completion status. `mark_complete()` records the date, and `is_due_today()` uses it to decide whether a daily or weekly task is due again.
- **`Pet`** (dataclass): a pet's details and its list of tasks. `add_task()` tags each task with the pet's name so the schedule can show who it's for.
- **`Owner`** (dataclass): the owner's daily time budget, day start time, and pets. `get_all_tasks()` returns every pet's tasks in one list.
- **`Scheduler`**: the planner. It reads tasks only through `Owner.get_all_tasks()`, so it plans across all pets at once. It keeps the tasks due today, picks the highest-priority ones that fit the time budget, places tasks with a preferred time at that time, fills gaps with flexible tasks, warns about overlapping time slots, and explains each choice.

`main.py` is a terminal demo that builds an owner with two pets, shows sorting and filtering, prints today's schedule with conflict warnings, and then completes two recurring tasks to show their next occurrences.

## 🖥️ Sample Output

Output of `python main.py` (dates depend on the day you run it):

```

All tasks, in the order they were added:
  09:30 Mochi  Puzzle toy     daily   pending
  08:00 Mochi  Morning walk   daily   pending
  flex  Mochi  Breakfast      daily   pending
  flex  Luna   Litter box     daily   pending
  08:15 Luna   Give meds      daily   pending
  flex  Luna   Brush coat     weekly  pending
  08:00 Luna   Breakfast      daily   pending

Sorted by time (flexible tasks last):
  08:00 Mochi  Morning walk   daily   pending
  08:00 Luna   Breakfast      daily   pending
  08:15 Luna   Give meds      daily   pending
  09:30 Mochi  Puzzle toy     daily   pending
  flex  Mochi  Breakfast      daily   pending
  flex  Luna   Litter box     daily   pending
  flex  Luna   Brush coat     weekly  pending

Filtered to Luna:
  flex  Luna   Litter box     daily   pending
  08:15 Luna   Give meds      daily   pending
  flex  Luna   Brush coat     weekly  pending
  08:00 Luna   Breakfast      daily   pending

Today's Schedule for Jordan
85 of 90 minutes planned, starting at 07:30
------------------------------------------------------------------------------
Time   Pet     Task             Min  Priority Why
------------------------------------------------------------------------------
07:30  Mochi   Breakfast         10  high     fits before 08:00
07:40  Luna    Litter box        10  medium   fits before 08:00
08:00  Luna    Breakfast          5  high     at preferred time 08:00
08:05  Mochi   Morning walk      30  high     preferred 08:00 but moved to avoid overlap
08:35  Luna    Give meds          5  high     preferred 08:15 but moved to avoid overlap
09:30  Mochi   Puzzle toy        25  medium   at preferred time 09:30
------------------------------------------------------------------------------
Skipped:
  - Brush coat (Luna): needs 20 min, only 5 min left
Conflicts:
  ! 'Morning walk' (Mochi) and 'Breakfast' (Luna) are both scheduled at 08:00
  ! 'Morning walk' (Mochi, 08:00, 30 min) overlaps 'Give meds' (Luna, 08:15)

Marked 'Morning walk' (daily) and 'Brush coat' (weekly) complete.

Completed tasks:
  08:00 Mochi  Morning walk   daily   done
  flex  Luna   Brush coat     weekly  done

Not yet completed (new copies are due later):
  09:30 Mochi  Puzzle toy     daily   pending
  flex  Mochi  Breakfast      daily   pending
  08:00 Mochi  Morning walk   daily   due 2026-11-12
  flex  Luna   Litter box     daily   pending
  08:15 Luna   Give meds      daily   pending
  08:00 Luna   Breakfast      daily   pending
  flex  Luna   Brush coat     weekly  due 2026-11-18
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts ==============================
collected 9 items

tests/test_pawpal.py .........                                                [100%]

============================== 9 passed in 0.01s ===============================
```

## 📐 Smarter Scheduling

These features live in `Scheduler` and `Task` in `pawpal_system.py`. `main.py` shows each one, and each has tests in `tests/test_pawpal.py`.

| Feature | Method(s) | What it does |
|---------|-----------|--------------|
| Sorting by time | `Scheduler.sort_by_time()` | Orders tasks by preferred `"HH:MM"` time, earliest first, with flexible (untimed) tasks last. |
| Sorting by priority | `Scheduler.sort_by_priority()` | Orders tasks high to low priority, then by time, then shortest first. `generate_plan()` uses it to decide what fits the time budget. |
| Filtering | `Scheduler.filter_tasks(pet_name=..., completed=...)` | Returns tasks for one pet, by completion status, or both. |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Completing a daily or weekly task adds a new copy to the same pet, due 1 or 7 days after completion. |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns when two due tasks share a start time or their time slots overlap, across all pets. |

**Sorting.** `sort_by_time()` calls `sorted()` with `key=lambda t: t.time or "99:99"`. Zero-padded `"HH:MM"` strings sort correctly as plain strings, and `Task` normalizes input such as `"8:00"` to `"08:00"` so this always holds. `"99:99"` sorts after every real time, which puts flexible tasks last.

**Filtering.** `filter_tasks()` takes an optional `pet_name` and an optional `completed` flag. A filter left as `None` is ignored, so `filter_tasks(pet_name="Luna", completed=False)` returns Luna's unfinished tasks.

**Recurring tasks.** `mark_task_complete(task)` marks the task done and calls `task.next_occurrence()`. For a recurring task, that returns a copy with `completed=False` and `due_date` set to the completion date plus `timedelta(days=1)` (daily) or `timedelta(weeks=1)` (weekly). The copy is added to the same pet. One-time tasks return `None`. Completing an already-completed task does nothing, so it can't create duplicates. `Task.is_due_today()` hides completed tasks and tasks whose due date hasn't arrived yet.

**Conflict detection.** `detect_conflicts()` sorts the due, timed tasks by start time and compares each task with the ones after it, stopping at the first one that starts after it ends. It returns warning strings and never raises. A shared start time reads "both scheduled at 08:00", and a partial overlap reads "overlaps". The checks cover all pets together, because the owner can't do two things at once. `generate_plan()` resolves conflicts by moving the later task to the next free slot. The warning tells the owner that a task won't happen at its preferred time.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
