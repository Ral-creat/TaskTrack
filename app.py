import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="TaskTrack", layout="wide")

# --- Load external CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# --- Load tasks ---
try:
    df = pd.read_csv("tasks.csv", parse_dates=["Deadline"])
except FileNotFoundError:
    df = pd.DataFrame(columns=["Profile","Type", "Title", "Subject/Project", "Deadline", "Notes", "Status"])

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
tab1, tab2 = st.tabs(["Dashboard", "Calendar View"])

# --- Tab 1: Dashboard ---
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
    # Ensure consistent date type for safety
    if "Deadline" in display_df.columns:
        display_df["Deadline"] = pd.to_datetime(display_df["Deadline"], errors="coerce")

    # Convert to clean date strings
    display_df["Deadline"] = display_df["Deadline"].dt.strftime("%Y-%m-%d")

    # Apply color styling safely
    try:
        styled_df = display_df.style.applymap(color_status, subset=["Status"])
        st.dataframe(styled_df, use_container_width=True)
    except Exception:
        st.dataframe(display_df, use_container_width=True)
else:
    st.info("No tasks to display.")

    # Mark as completed
    st.subheader("Mark Task as Completed")
    pending_tasks = profile_df[profile_df["Status"]=="Pending"]
    task_to_complete = st.selectbox("Select Task", pending_tasks["Title"] if not pending_tasks.empty else [])
    
    if st.button("Mark Completed") and task_to_complete:
        df.loc[df["Title"]==task_to_complete, "Status"] = "Completed"
        df.to_csv("tasks.csv", index=False)
        st.success(f"'{task_to_complete}' marked as completed!")

# --- Tab 2: Calendar View ---
with tab2:
    st.header(f"{user_type} Calendar View")
    
    profile_df = df[df["Profile"] == user_type]
    
    if profile_df.empty:
        st.info("No tasks yet.")
    else:
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

# --- Footer / Export ---
st.markdown("---")
profile_df = df[df["Profile"] == user_type]
st.download_button(
    "Download My Tasks CSV",
    data=profile_df.to_csv(index=False),
    file_name=f"{user_type}_tasks.csv"
)
