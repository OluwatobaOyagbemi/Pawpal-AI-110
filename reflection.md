# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

**Core user actions.** After reading the scenario, I picked three things a user has to be able to do:

1. **Add a pet and owner info.** The user enters their name, how much time they have today, and their pet's basic details (name, species, age).
2. **Add and manage care tasks.** The user adds tasks for a pet, such as a walk, feeding, meds or grooming. Each task has a duration and a priority, and can have a preferred time and a frequency (daily or weekly). Tasks can be marked complete or removed.
3. **Generate and view today's plan.** The user asks for a daily schedule. The app picks the tasks that fit in the available time, puts them in order with start times, and explains why each task was included or left out.

**UML design.** The diagram (`diagrams/uml.mmd`) has four classes. An Owner has many Pets, each Pet has many Tasks, and a Scheduler takes an Owner and builds the plan from all of that owner's pets' tasks.

- **Task** (dataclass) holds one care activity: title, category, duration, priority, frequency, optional preferred time, and whether it's done. It can mark itself complete, turn its priority into a number for sorting, and say whether it's due today.
- **Pet** (dataclass) holds the pet's details and its list of tasks. It can add or remove tasks and return the ones still pending.
- **Owner** (dataclass) holds the owner's name, daily time budget, day start time, preferences and pets. It can add, remove or find pets, and collect every task across all of them.
- **Scheduler** holds the scheduling logic. It gathers due tasks, sorts them by priority, fits them into the owner's time budget with start times, flags overlapping time slots, and explains the plan. I kept this logic out of Owner and Pet so the data classes stay simple and the scheduling rules live in one place I can test.

**b. Design changes**

- Yes. When I asked my AI assistant to review the skeleton, it pointed out that `Task.is_due_today()` couldn't work for weekly tasks: a task only stored `completed: bool`, so there was no way to know *when* it was last done. I added a `last_completed: date` field to `Task`, and `mark_complete()` will record today's date. That gives the scheduler what it needs to decide whether a weekly task is due again.
- The review also noted that a `Task` didn't know which pet it belonged to, so my skeleton had the Scheduler passing `(Pet, Task)` pairs around. During implementation I changed this: `Pet.add_task()` now sets a `pet_name` field on the task. Now the Scheduler can get everything through one call, `Owner.get_all_tasks()`, and still show which pet each task is for. This makes the Scheduler work across all pets instead of one at a time.
- I renamed `title` to `description` and `preferred_time` to `time` to match the project spec's wording for a Task.
- One thing I left as it is: `remove_task(description)` removes only the first match, so tasks with the same description are still ambiguous.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
