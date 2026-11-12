"""PawPal+ demo script: builds an owner with two pets and prints today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(scheduler: Scheduler) -> None:
    """Print the generated plan as a readable table, then skipped tasks and conflicts."""
    plan = scheduler.generate_plan()
    owner = scheduler.owner
    used = sum(task.duration_minutes for _, task, _ in plan)

    print(f"Today's Schedule for {owner.name}")
    print(f"{used} of {owner.available_minutes} minutes planned, starting at {owner.day_start}")
    print("-" * 78)
    print(f"{'Time':<7}{'Pet':<8}{'Task':<16}{'Min':>4}  {'Priority':<9}Why")
    print("-" * 78)
    for start, task, reason in plan:
        why = reason.split(", ", 1)[1] if ", " in reason else reason
        print(
            f"{start:<7}{task.pet_name:<8}{task.description:<16}"
            f"{task.duration_minutes:>4}  {task.priority:<9}{why}"
        )
    print("-" * 78)

    if scheduler.skipped:
        print("Skipped:")
        for task, reason in scheduler.skipped:
            print(f"  - {task.description} ({task.pet_name}): {reason}")

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        print("Conflicts:")
        for warning in conflicts:
            print(f"  ! {warning}")


def main() -> None:
    """Set up a sample owner, two pets, and their tasks, then print the plan."""
    owner = Owner("Jordan", available_minutes=90, day_start="07:30")

    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", 30, "high", time="08:00", category="walk"))
    mochi.add_task(Task("Breakfast", 10, "high", category="feeding"))
    mochi.add_task(Task("Puzzle toy", 25, "medium", time="09:30", category="enrichment"))
    luna.add_task(Task("Give meds", 5, "high", time="08:15", category="meds"))
    luna.add_task(Task("Litter box", 10, "medium", category="cleaning"))
    luna.add_task(Task("Brush coat", 20, "low", frequency="weekly", category="grooming"))

    print_schedule(Scheduler(owner))


if __name__ == "__main__":
    main()
