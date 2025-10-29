import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="TaskTrack", layout="wide")

# --- Load CSS ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

local_css("style.css")

# --- Load tasks ---
try:
    df = pd.read_csv("tasks.csv", parse_dates=["Deadline"])
except FileNotFoundError:
    df = pd.DataFrame(columns=["Profile", "Type", "Title", "Subject/Project", "Deadline", "Notes", "Status"])

# --- Load completed tasks ---
try:
    completed_df = pd.read_csv("completed_tasks.csv", parse_dates=["Deadline"])
except FileNotFoundError:
    completed_df = pd.DataFrame(columns=["Profile", "Type", "Title", "Subject/Project", "Deadline", "Notes", "Status"])

# --- Sidebar: Profile ---
st.sidebar.header("User Profile")
user_type = st.sidebar.selectbox("Select Your Profile", ["Student", "Worker", "Teacher", "Business"])

# --- Adjust Task Types Based on Profile ---
if user_type == "Student":
    task_options = ["Assignment", "Project", "Activity"]
elif user_type == "Worker":
    task_options = ["Task", "Deadline", "Meeting"]
elif user_type == "Teacher":
    task_options = ["Lesson", "Grading", "Admin Work"]
else:
    task_options = ["Order", "Deliverable", "Appointment"]

# --- Sidebar: Add Task ---
st.sidebar.header("Add New Task")
with st.sidebar.form("task_form", clear_on_submit=True):
    task_type = st.selectbox("Task Type", task_options)
    title = st.text_input("Title")
    subject_project = st.text_input("Subject/Project")
    deadline = st.date_input("Deadline", min_value=datetime.today())
    notes = st.text_area("Notes (optional)")
    submitted = st.form_submit_button("Add Task")

    if submitted:
        new_task = {
            "Profile": user_type,
            "Type": task_type,
            "Title": title,
            "Subject/Project": subject_project,
            "Deadline": deadline,
            "Notes": notes,
            "Status": "Pending"
        }
        df = pd.concat([df, pd.DataFrame([new_task])], ignore_index=True)
        df.to_csv("tasks.csv", index=False)
        st.success(f"{task_type} '{title}' added under {user_type} profile!")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Calendar View", "Subject Schedule", "Task History"])

# --- Dashboard Tabs ---
st.title("📋 Task Tracker Dashboard")

tab1, tab2 = st.tabs(["🏠 Active Tasks", "📜 Completed History"])

with tab1:
    st.subheader("📌 Active Tasks")
    active_df = df[df["Status"] != "Completed"]

    if not active_df.empty:
        st.dataframe(active_df, use_container_width=True)
    else:
        st.info("No active tasks right now. Chill time 😎")

    # --- Mark as completed section ---
    st.markdown("### ✅ Mark Task as Completed")
    pending_tasks = active_df[active_df["Status"] == "Pending"]

    task_to_complete = st.selectbox(
        "Select Task to Complete",
        pending_tasks["Title"] if not pending_tasks.empty else [],
        key="complete_task_select"
    )

    if st.button("Mark Completed"):
        if task_to_complete:
            # Move task to completed history
            completed_row = df[df["Title"] == task_to_complete].copy()
            completed_row["Status"] = "Completed"

            # Append to completed.csv
            try:
                completed_df = pd.read_csv("completed_tasks.csv")
                completed_df = pd.concat([completed_df, completed_row], ignore_index=True)
            except FileNotFoundError:
                completed_df = completed_row

            completed_df.to_csv("completed_tasks.csv", index=False)

            # Remove from active list
            df = df[df["Title"] != task_to_complete]
            df.to_csv("tasks.csv", index=False)

            st.success(f"'{task_to_complete}' marked completed and moved to history! 🎉")
            st.rerun()
        else:
            st.warning("Please select a task to complete.")

with tab2:
    st.subheader("📜 Completed Task History")

    try:
        completed_df = pd.read_csv("completed_tasks.csv")
        if not completed_df.empty:
            st.dataframe(completed_df, use_container_width=True)
        else:
            st.info("No completed tasks yet. Keep grinding 💪")
    except FileNotFoundError:
        st.info("No completed tasks yet. Keep grinding 💪")

# --- Tab 2: Calendar View ---
with tab2:
    st.header(f"{user_type} Calendar View")
    profile_df = df[df["Profile"] == user_type]
    if profile_df.empty:
        st.info("No tasks yet.")
    else:
        profile_df["Deadline"] = pd.to_datetime(profile_df["Deadline"], errors="coerce")
        profile_df["Deadline_str"] = profile_df["Deadline"].dt.strftime("%Y-%m-%d")

        fig = px.scatter(
            profile_df,
            x="Deadline",
            y="Title",
            color="Type",
            hover_data=["Subject/Project", "Notes", "Status"],
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
        st.plotly_chart(fig, use_container_width=True)

# --- Tab 3: Subject Schedule ---
with tab3:
    st.header(f"{user_type} Subject Schedule 📚")

    try:
        sched_df = pd.read_csv("schedules.csv")
    except FileNotFoundError:
        sched_df = pd.DataFrame(columns=["Profile", "Subject", "Day", "Time", "Instructor", "Room"])

    with st.form("schedule_form", clear_on_submit=True):
        st.subheader("Add New Class Schedule 📝")
        subject = st.text_input("Subject Name")
        day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
        time = st.text_input("Time (e.g., 8:00 AM - 9:30 AM)")
        instructor = st.text_input("Instructor Name")
        room = st.text_input("Room / Location")
        add_sched = st.form_submit_button("Add Schedule")

        if add_sched:
            new_sched = {
                "Profile": user_type,
                "Subject": subject,
                "Day": day,
                "Time": time,
                "Instructor": instructor,
                "Room": room
            }
            sched_df = pd.concat([sched_df, pd.DataFrame([new_sched])], ignore_index=True)
            sched_df.to_csv("schedules.csv", index=False)
            st.success(f"✅ Added {subject} on {day}!")

    user_sched = sched_df[sched_df["Profile"] == user_type]
    if not user_sched.empty:
        st.subheader(f"{user_type}'s Weekly Class Schedule 🗓️")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        for d in days:
            day_sched = user_sched[user_sched["Day"] == d]
            with st.expander(f"📅 {d}", expanded=True):
                if not day_sched.empty:
                    st.dataframe(day_sched[["Subject", "Time", "Instructor", "Room"]], use_container_width=True)
                else:
                    st.caption(f"😴 No class scheduled on {d}.")
    else:
        st.info("No schedules added yet. Add one using the form above!")

# --- Tab 4: Task History ---
with tab4:
    st.header(f"🕓 {user_type} Task History")
    user_history = completed_df[completed_df["Profile"] == user_type]

    if not user_history.empty:
        user_history["Deadline"] = pd.to_datetime(user_history["Deadline"], errors="coerce")
        user_history["Deadline"] = user_history["Deadline"].dt.strftime("%Y-%m-%d")
        st.dataframe(user_history, use_container_width=True)
    else:
        st.info("No completed tasks yet.")

# --- Footer ---
st.markdown("---")
profile_df = df[df["Profile"] == user_type]
st.download_button(
    "Download My Tasks CSV",
    data=profile_df.to_csv(index=False),
    file_name=f"{user_type}_tasks.csv"
)
