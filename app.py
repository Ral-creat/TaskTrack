import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="TaskTrack", layout="wide")

# --- Load external CSS ---
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

# --- Sidebar: Select Profile ---
st.sidebar.header("User Profile")
user_type = st.sidebar.selectbox("Select Your Profile", ["Student", "Worker", "Teacher", "Business"])

# --- Adjust Task Types Based on Profile ---
if user_type == "Student":
    task_options = ["Assignment", "Project", "Activity"]
elif user_type == "Worker":
    task_options = ["Task", "Deadline", "Meeting"]
elif user_type == "Teacher":
    task_options = ["Lesson", "Grading", "Admin Work"]
else:  # Business
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
tab1, tab2, tab3 = st.tabs(["Dashboard", "Calendar View", "Subject Schedule"])

with tab1:
    st.header(f"{user_type} Dashboard")

    # Filter tasks for current profile
    profile_df = df[df["Profile"] == user_type]

    # Filter by status
    status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Completed"])
    if status_filter != "All":
        display_df = profile_df[profile_df["Status"] == status_filter]
    else:
        display_df = profile_df.copy()

    # Add color-coded status column for display
    def color_status(val):
        if val == "Pending":
            return 'background-color: #F4D35E'  # yellow
        elif val == "Completed":
            return 'background-color: #52B788; color:white'  # green
        else:
            return ''

    if not display_df.empty:
        # Ensure consistent date type
        if "Deadline" in display_df.columns:
            display_df["Deadline"] = pd.to_datetime(display_df["Deadline"], errors="coerce")
        display_df["Deadline"] = display_df["Deadline"].dt.strftime("%Y-%m-%d")

        # Function to display styled tables
        def show_table(df, label):
            if df.empty:
                st.caption(f"❌ No {label.lower()}s available.")
            else:
                try:
                    styled = df.style.applymap(color_status, subset=["Status"])
                    st.dataframe(styled, use_container_width=True)
                except Exception:
                    st.dataframe(df, use_container_width=True)

        # --- Separated tables with h3 headers ---
        st.subheader("📚 Task Overview by Type")

        st.markdown("### 📘 Assignments")
        show_table(display_df[display_df["Type"] == "Assignment"], "Assignment")

        st.markdown("### 📗 Projects")
        show_table(display_df[display_df["Type"] == "Project"], "Project")

        st.markdown("### 📙 Activities")
        show_table(display_df[display_df["Type"] == "Activity"], "Activity")

    else:
        st.info("No tasks to display.")

    # --- Mark as completed section ---
    st.subheader("✅ Mark Task as Completed")
    pending_tasks = profile_df[profile_df["Status"] == "Pending"]
    task_to_complete = st.selectbox("Select Task", pending_tasks["Title"] if not pending_tasks.empty else [])

    if st.button("Mark Completed") and task_to_complete:
        df.loc[df["Title"] == task_to_complete, "Status"] = "Completed"
        df.to_csv("tasks.csv", index=False)
        st.success(f"'{task_to_complete}' marked as completed!")

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
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
        st.plotly_chart(fig, use_container_width=True)

# --- Tab 3: Subject Schedule ---
with tab3:
    st.header(f"{user_type} Subject Schedule 📚")

    # Load existing schedules
    try:
        sched_df = pd.read_csv("schedules.csv")
    except FileNotFoundError:
        sched_df = pd.DataFrame(columns=["Profile", "Subject", "Day", "Time", "Instructor", "Room"])

    # --- Add Schedule Form ---
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

    # --- Display Schedules ---
    user_sched = sched_df[sched_df["Profile"] == user_type]
    if not user_sched.empty:
        st.subheader(f"{user_type}'s Weekly Class Schedule 🗓️")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        for d in days:
            day_sched = user_sched[user_sched["Day"] == d]
            with st.expander(f"📅 {d}", expanded=True):
                if not day_sched.empty:
                    st.dataframe(
                        day_sched[["Subject", "Time", "Instructor", "Room"]].reset_index(drop=True),
                        use_container_width=True
                    )
                else:
                    st.caption(f"😴 No class scheduled on {d}.")
    else:
        st.info("No schedules added yet. Add one using the form above!")

# --- Footer / Export ---
st.markdown("---")
profile_df = df[df["Profile"] == user_type]
st.download_button(
    "Download My Tasks CSV",
    data=profile_df.to_csv(index=False),
    file_name=f"{user_type}_tasks.csv"
)
