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

`main.py` is a terminal demo that builds an owner with two pets and prints today's schedule.

## 🖥️ Sample Output

Output of `python main.py`:

```
Today's Schedule for Jordan
80 of 90 minutes planned, starting at 07:30
------------------------------------------------------------------------------
Time   Pet     Task             Min  Priority Why
------------------------------------------------------------------------------
07:30  Mochi   Breakfast         10  high     fits before 08:00
07:40  Luna    Litter box        10  medium   fits before 08:00
08:00  Mochi   Morning walk      30  high     at preferred time 08:00
08:30  Luna    Give meds          5  high     preferred 08:15 but moved to avoid overlap
09:30  Mochi   Puzzle toy        25  medium   at preferred time 09:30
------------------------------------------------------------------------------
Skipped:
  - Brush coat (Luna): needs 20 min, only 10 min left
Conflicts:
  ! 'Morning walk' (Mochi, 08:00, 30 min) overlaps 'Give meds' (Luna, 08:15)
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
collected 2 items

tests/test_pawpal.py ..                                                  [100%]

============================== 2 passed in 0.00s ===============================
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
