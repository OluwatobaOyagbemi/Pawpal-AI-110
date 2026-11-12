import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' care tasks for the day based on your time, priorities, and preferred times.")

# --- App memory -------------------------------------------------------------
# Streamlit reruns this whole script on every click. Store the Owner in
# st.session_state (a dict that survives reruns) and only create it once.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")

owner: Owner = st.session_state.owner

# --- Owner ------------------------------------------------------------------
st.subheader("Owner")
col1, col2, col3 = st.columns(3)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input("Minutes available today", min_value=0, max_value=1440,
                        value=owner.available_minutes, step=5)
    )
with col3:
    day_start = st.time_input("Day starts at", value=owner.day_start, step=900)
    owner.day_start = day_start.strftime("%H:%M")

st.divider()

# --- Pets -------------------------------------------------------------------
st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age", min_value=0, max_value=40, value=0)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Enter a pet name.")
        else:
            try:
                owner.add_pet(Pet(pet_name.strip(), species, age=int(age)))
                st.success(f"Added {pet_name.strip()}.")
            except ValueError as err:
                st.error(str(err))

if owner.pets:
    st.dataframe(
        [{"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)}
         for p in owner.pets],
        hide_index=True, width="stretch",
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Tasks ------------------------------------------------------------------
st.subheader("Tasks")
if not owner.pets:
    st.caption("Add a pet before adding tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            task_pet = st.selectbox("Pet", [p.name for p in owner.pets])
            description = st.text_input("Task", placeholder="e.g. Morning walk")
            category = st.selectbox(
                "Category", ["walk", "feeding", "meds", "enrichment", "grooming", "cleaning", "general"]
            )
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["high", "medium", "low"])
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        has_time = st.checkbox("Set a preferred time")
        preferred = st.time_input("Preferred time", value="08:00", step=900)
        if st.form_submit_button("Add task"):
            if not description.strip():
                st.error("Enter a task description.")
            else:
                try:
                    owner.get_pet(task_pet).add_task(
                        Task(
                            description.strip(),
                            int(duration),
                            priority,
                            frequency=frequency,
                            time=preferred.strftime("%H:%M") if has_time else None,
                            category=category,
                        )
                    )
                    st.success(f"Added '{description.strip()}' for {task_pet}.")
                except ValueError as err:
                    st.error(str(err))

    scheduler = Scheduler(owner)

    # --- Mark complete (recurring tasks get their next copy automatically) ---
    due_now = scheduler.sort_by_time(scheduler.collect_tasks())
    if due_now:
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        with col1:
            labels = [
                f"{t.pet_name}: {t.description} ({t.time or 'flexible'}, {t.frequency})"
                for t in due_now
            ]
            pick = st.selectbox("Mark a task complete", labels)
        with col2:
            if st.button("Complete", width="stretch"):
                done = due_now[labels.index(pick)]
                next_task = scheduler.mark_task_complete(done)
                st.session_state.flash = (
                    f"Completed '{done.description}' for {done.pet_name}. "
                    + (f"Next {done.frequency} copy is due {next_task.due_date:%a %b %d}."
                       if next_task else "One-time task, so it won't repeat.")
                )
                st.rerun()
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))

    # --- Filter and sort the task list ---
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with col2:
        status_filter = st.selectbox("Status", ["All", "Not done", "Done"])
    with col3:
        sort_by = st.selectbox("Sort by", ["Time", "Priority"])

    shown = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "Not done": False, "Done": True}[status_filter],
    )
    shown = scheduler.sort_by_time(shown) if sort_by == "Time" else scheduler.sort_by_priority(shown)

    if shown:
        st.dataframe(
            [
                {
                    "Time": t.time or "flexible",
                    "Pet": t.pet_name,
                    "Task": t.description,
                    "Min": t.duration_minutes,
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                    "Status": "done" if t.completed
                    else "due" if t.is_due_today() else f"next due {t.due_date:%a %b %d}",
                }
                for t in shown
            ],
            hide_index=True, width="stretch",
        )
    elif owner.get_all_tasks():
        st.info("No tasks match these filters.")
    else:
        st.info("No tasks yet. Add one above.")

    # --- Conflicts: shown live, in one block, with what happens and how to fix it ---
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        count = f"{len(conflicts)} time conflict" + ("s" if len(conflicts) > 1 else "")
        st.warning(
            f"**⚠️ {count}.** You can't do two things at once, so the schedule will start "
            "the later task when the earlier one ends. To keep both at their preferred "
            "times, change one task's time.\n\n"
            + "\n".join(f"- {c}" for c in conflicts)
        )

st.divider()

# --- Schedule ---------------------------------------------------------------
st.subheader("Today's Schedule")
if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    if not plan:
        st.info("Nothing to schedule. Add tasks, or check your available minutes.")
    else:
        used = sum(task.duration_minutes for _, task, _ in plan)
        moved = sum("moved" in reason for _, _, reason in plan)
        c1, c2, c3 = st.columns(3)
        c1.metric("Tasks planned", len(plan))
        c2.metric("Minutes used", f"{used} / {owner.available_minutes}")
        c3.metric("Moved for conflicts", moved)
        st.dataframe(
            [
                {"Time": start, "Pet": task.pet_name, "Task": task.description,
                 "Min": task.duration_minutes, "Priority": task.priority, "Why": reason}
                for start, task, reason in plan
            ],
            hide_index=True, width="stretch",
        )
        if not scheduler.skipped:
            st.success("Everything due today fits in your available time.")

    if scheduler.skipped:
        st.warning(
            f"**{len(scheduler.skipped)} task(s) didn't fit** in {owner.available_minutes} minutes. "
            "Add more time or lower another task's priority to fit them in.\n\n"
            + "\n".join(f"- {t.description} ({t.pet_name}): {r}" for t, r in scheduler.skipped)
        )
