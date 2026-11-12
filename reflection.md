# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

**Core user actions.** After reading the scenario, I picked three things a user has to be able to do:

1. **Add a pet and owner info.** The user enters their name, how much time they have today, and their pet's basic details (name, species, age).
2. **Add and manage care tasks.** The user adds tasks for a pet, such as a walk, feeding, meds or grooming. Each task has a duration and a priority, and can have a preferred time and a frequency (daily or weekly). Tasks can be marked complete or removed.
3. **Generate and view today's plan.** The user asks for a daily schedule. The app picks the tasks that fit in the available time, puts them in order with start times, and explains why each task was included or left out.

**UML design.** The diagram (`diagrams/uml.mmd`) has four classes. An Owner has many Pets, each Pet has many Tasks, and a Scheduler takes an Owner and builds the plan from every task returned by `Owner.get_all_tasks()`.

- **Task** (dataclass) holds one care activity: `description`, `duration_minutes`, `priority`, `frequency` (daily, weekly or once), an optional `time` ("HH:MM"), `category`, `completed`, `last_completed`, and `pet_name`. It can mark itself complete, turn its priority into a number for sorting, and say whether it's due today.
- **Pet** (dataclass) holds the pet's `name`, `species`, `age`, `notes` and its list of `tasks`. When it adds a task, it stamps the task with its `pet_name`. It can also remove a task by description and return the tasks still pending today.
- **Owner** (dataclass) holds the owner's `name`, `available_minutes`, `day_start`, `preferences` and `pets`. It can add, remove or find pets, and `get_all_tasks()` returns every pet's tasks together.
- **Scheduler** holds the scheduling logic. It gets tasks only through `Owner.get_all_tasks()`, so it works across all pets. It keeps the ones due today, sorts them by priority, fits them into the owner's time budget with start times, flags overlapping time slots, and explains the plan. I kept this logic out of Owner and Pet so the data classes stay simple and the scheduling rules live in one place I can test.

**b. Design changes**

- Yes. When I asked my AI assistant to review the skeleton, it pointed out that `Task.is_due_today()` couldn't work for weekly tasks: a task only stored `completed: bool`, so there was no way to know *when* it was last done. I added a `last_completed: date` field to `Task`, and `mark_complete()` will record today's date. That gives the scheduler what it needs to decide whether a weekly task is due again.
- The review also noted that a `Task` didn't know which pet it belonged to, so my skeleton had the Scheduler passing `(Pet, Task)` pairs around. During implementation I changed this: `Pet.add_task()` now sets a `pet_name` field on the task. Now the Scheduler can get everything through one call, `Owner.get_all_tasks()`, and still show which pet each task is for. This makes the Scheduler work across all pets instead of one at a time.
- I renamed `title` to `description` and `preferred_time` to `time` to match the project spec's wording for a Task.
- One thing I left as it is: `remove_task(description)` removes only the first match, so tasks with the same description are still ambiguous.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- The scheduler works with five constraints. The owner's available minutes are a hard limit, and a task that doesn't fit is skipped. Priority decides which tasks get the minutes first. A preferred time places a task at that time if possible. The day start is where flexible tasks begin. The due date leaves out tasks that are done or not due until later. Because one owner does every task, tasks for different pets also can't overlap.
- I put priority first because missing a pet's meds is worse than missing a brushing, and a schedule that's full but skips the meds is a bad schedule. The time budget comes next because the owner can't make more time. Preferred times matter least, so the scheduler moves a task to the next free slot instead of dropping it, and tells the owner it moved. `Owner` also has a `preferences` list, but the scheduler doesn't use it yet.

**b. Tradeoffs**

- **Greedy, priority-first selection.** The scheduler goes through tasks from highest to lowest priority and keeps each one that still fits in the remaining minutes. It never looks for the combination of tasks that fills the most time. For example, with 30 minutes left and a 25-minute medium task ahead of two 15-minute low tasks, it takes the 25-minute task and skips both low ones, even though the two low tasks would use the full 30 minutes. This is reasonable for pet care because priority matters more than a full schedule. A high-priority task like meds should never lose its spot to two small low-priority ones, and the owner can predict the result without understanding a packing algorithm.
- **Readability over cleverness in conflict detection.** When I asked my AI assistant how to simplify `detect_conflicts()`, it suggested `itertools.combinations(timed, 2)` with no nested loop. That version is shorter, but it compares every pair of tasks. My version sorts by start time and stops the inner loop at the first task that starts after the current one ends. I kept my version because the early `break` makes the overlap rule visible ("sorted, so nothing later can overlap"). With only a few tasks a day, speed isn't the reason.

---

## 3. AI Collaboration

**a. How you used AI**

- I used Claude Code in VS Code for the whole project. In the early phases it drafted the Mermaid UML and the class skeleton, reviewed the skeleton, and then wrote the implementation, the `main.py` demo and the first tests. In the later phases it added sorting, filtering, recurrence and conflict warnings, grew the test suite from 2 tests to 42, connected everything to the Streamlit UI, and helped write this file and the README.
- The most useful feature was that the agent could change several files in one step and then run the code itself. Recurrence touched `pawpal_system.py`, `main.py`, the tests, the app and the README at once. After each change it ran `main.py` and `python -m pytest`, and it also ran the Streamlit app headless to click through marking a task complete. That's how it caught its own mistake when a test it wrote failed on the first run.
- The other useful habit was asking review questions about my own code instead of just asking for code, like "does this skeleton have missing relationships?" and "how could this algorithm be simplified?" Those found real gaps, such as weekly tasks having no completion date.
- On separate chat sessions: I started this session by asking what I'd done in my last one, and the assistant rebuilt it from the git history. After that, Phases 3, 4 and 5 ran in the same chat. What kept things organized was committing at the end of each phase with a clear message (`feat: implement sorting, filtering, and conflict detection`, `test: add automated test suite for PawPal+ system`), so each phase has a clean boundary in git even without a new chat. A fresh chat per phase would have kept the context smaller and stopped earlier decisions from carrying over without me noticing, so for the next project I'd start a new chat at each phase.

**b. Judgment and verification**

- **A suggestion I modified:** In the skeleton, the Scheduler passed `(Pet, Task)` pairs around so it could tell which pet each task belonged to. The assignment says the Scheduler reads from `Owner.get_all_tasks()`, which returns plain tasks, so I changed the design. `Pet.add_task()` stamps each task with a `pet_name`, and the Scheduler reads only from `get_all_tasks()`.
- **A suggestion I rejected:** When I asked how to simplify `detect_conflicts()`, the AI suggested `itertools.combinations`. It's shorter and more "Pythonic", but it hides the early `break` that makes the overlap rule clear, so I kept my loop (see 2b).
- **What I accepted:** I kept the AI's two-step scheduling approach, which first picks tasks by priority within the time budget and then places them by time. I also kept its rename of `title` to `description` to match the spec.
- **What I left for later:** `remove_task()` removes only the first task with a matching description, so duplicate descriptions are ambiguous. It doesn't affect scheduling, so I left it.
- **Where the AI got it wrong:** One of its tests expected the wrong task to be skipped. It also committed the `.coverage` data file by accident, and its first attempt to ignore that file broke `.gitignore` by gluing two entries onto one line. All three were caught by checking the output (the failing test, `git status` and `git check-ignore`) rather than trusting the summary.
- **How I verified it:** All 42 tests pass and cover every line of `pawpal_system.py`. I also traced the README's example workflow through the real classes to confirm each start time it claims, and ran the app myself in the browser.

---

## 4. Testing and Verification

**a. What you tested**

- The suite in `tests/test_pawpal.py` has 42 tests, grouped by feature. For sorting, I checked that `sort_by_time()` returns tasks in time order, reads `"8:00"` as 08:00, puts flexible tasks last, and keeps the original order when two tasks share a time. For recurrence, completing a daily task adds a copy due the next day and a weekly one is due seven days later. The dates also roll over correctly at the end of a month, the end of a year, and on a leap day. One-time tasks don't repeat, and completing the same task twice doesn't make two copies. For conflicts, two tasks at the same time get flagged whether they belong to one pet or two, partial overlaps get flagged, and back-to-back tasks don't.
- I also tested the plan itself. Timed tasks keep their preferred time, flexible tasks fill the gaps, nothing in the final plan overlaps, and low-priority tasks get skipped when time runs out. Then I covered the empty cases, like an owner with no pets, a pet with no tasks, and zero minutes available.
- These are the parts a pet owner would notice going wrong. A daily meds task that never comes back, or that shows up twice, is the kind of mistake that would make someone stop trusting the app. Date math at month and year ends is easy to get wrong, so I tested `timedelta` on real boundary dates. Every Scheduler in the tests gets a fixed date, so the results are the same whatever day I run them.
- One test failed on the first run, and the mistake was in the test. I expected the Puzzle toy to be skipped, but all four tasks were medium priority, so the scheduler chose the timed tasks first and skipped the flexible Litter box instead. I fixed the expected result and wrote the reason in the test's docstring.

**b. Confidence**

- I'd give it 4 out of 5. All 42 tests pass, and together they run every line of `pawpal_system.py`. I'm holding back one star because the Streamlit app isn't in the automated tests (I checked it by hand in the browser), and because of a gap I already know about: a task that runs past midnight, like 23:50 for 30 minutes, gets a start time of `24:20`.
- With more time I'd test tasks that cross midnight, a preferred time earlier than the owner's day start, and two tasks for the same pet with the same description, since `remove_task()` only removes the first match. I'd also add tests for the Streamlit app using Streamlit's `AppTest`, so marking a task complete and filtering get checked automatically.

---

## 5. Reflection

**a. What went well**

- I'm most satisfied that the schedule explains itself. Every task has a reason next to it, like "preferred 08:15 but moved to avoid overlap", and conflicts show up as warnings that say what will happen and how to fix it instead of crashing. Keeping all the logic in `pawpal_system.py` also paid off: the app, the terminal demo and the tests all use the same methods, so testing the logic once covers all three.

**b. What you would improve**

- I'd fix tasks that run past midnight, which currently get start times like `24:20`. I'd also try a selection step that fills the available time better while still putting high priority first.
- The app can add pets and tasks but can't edit or delete them, and everything resets when the page reloads, so I'd add editing and save the data to a file.
- I'd use the owner's `preferences` list, which exists but does nothing yet, and give tasks unique IDs so `remove_task()` isn't ambiguous.

**c. Key takeaway**

- Being the lead architect meant deciding the rules and checking the results while the AI did most of the typing. The AI was fast, and it was just as confident when it was wrong, as with the failing test and the broken `.gitignore`. The parts that made this project mine were the constraints I set (the Scheduler only reads through `get_all_tasks()`), the tradeoffs I chose (priority over a full schedule, a readable loop over a shorter one), and the habit of running the code before accepting a change.
