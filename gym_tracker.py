import streamlit as st
import pandas as pd
import os
import datetime
import hashlib
import json
import calendar
# -------------------- Authentication --------------------
# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
# Load user credentials
USER_CREDENTIALS_FILE = "users.json"
if not os.path.exists(USER_CREDENTIALS_FILE):
    with open(USER_CREDENTIALS_FILE, "w") as f:
        json.dump({"admin": hash_password("admin")}, f)  # Default user
with open(USER_CREDENTIALS_FILE, "r") as f:
    users = json.load(f)
# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
# Streamlit login
st.sidebar.title(":lock: Login / Register")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
login_button = st.sidebar.button("Login")
register_button = st.sidebar.button("Register")
# Authentication check
if login_button:
    if username in users and users[username] == hash_password(password):
        st.session_state.authenticated = True
        st.session_state.username = username
        st.sidebar.success("Login successful!")
    else:
        st.sidebar.error("Invalid username or password")
# Registration logic
if register_button:
    if username in users:
        st.sidebar.error("Username already exists. Please choose a different username.")
    else:
        users[username] = hash_password(password)
        with open(USER_CREDENTIALS_FILE, "w") as f:
            json.dump(users, f)
        st.sidebar.success("Registration successful! Please log in.")
# Check if user is authenticated
if not st.session_state.authenticated:
    st.warning("Please log in to access the app.")
    st.stop()
# -------------------- Data Handling --------------------
DATA_FILE = f"{st.session_state.username}_gym_weights.csv"
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["Date", "Exercise", "Weight (kg)", "Reps", "Estimated 1RM (kg)"])
# Fixed calculate_1rm function
def calculate_1rm(weight, reps):
    return round(weight * (1 + reps / 30), 1)  # Removed the extra comma
# -------------------- UI --------------------
st.markdown("<h1 style='text-align: center;'>:man-lifting-weights: Gym Tracker</h1>", unsafe_allow_html=True)
st.write(f"Welcome, **{st.session_state.username}**! Track your workouts, estimate your 1RM, and visualize progress.")
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.subheader(":inbox_tray: Log Your Workout")
    with st.form("log_form"):
        date = st.date_input("Date")
        exercise = st.text_input("Exercise Name", placeholder="e.g., Bench Press")
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)
        reps = st.number_input("Reps", min_value=1, step=1)
        submitted = st.form_submit_button("Log Entry")
        if submitted:
            one_rm = calculate_1rm(weight, reps)
            new_entry = pd.DataFrame([[date, exercise, weight, reps, one_rm]], columns=df.columns)
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"Entry added! Estimated 1RM: **{one_rm} kg**")
with col2:
    st.subheader(":bar_chart: Quick Stats")
    if not df.empty:
        latest_workout = df.iloc[-1]
        st.metric("Latest Exercise", latest_workout["Exercise"])
        st.metric("Latest Weight", f"{latest_workout['Weight (kg)']} kg")
        st.metric("Estimated 1RM", f"{latest_workout['Estimated 1RM (kg)']} kg")
    else:
        st.info("No workouts logged yet!")
st.markdown("---")
tab1, tab2, tab3 = st.tabs([":clipboard: Workout Log", ":chart_with_upwards_trend: Progress Graph", ":date: Calendar View"])
with tab1:
    st.subheader("Workout History")
    if not df.empty:
        st.dataframe(df.style.apply(lambda x: ["background-color: green" if v == df["Estimated 1RM (kg)"].max() else "" for v in x["Estimated 1RM (kg)"]], axis=1))
    else:
        st.warning("No data recorded yet.")
with tab2:
    st.subheader("1RM Progress Over Time")
    if not df.empty:
        selected_exercise = st.selectbox("Select an exercise:", df["Exercise"].unique())
        filtered_df = df[df["Exercise"] == selected_exercise]
        if not filtered_df.empty:
            filtered_df["Date"] = pd.to_datetime(filtered_df["Date"])
            filtered_df = filtered_df.sort_values("Date")
            st.line_chart(filtered_df.set_index("Date")[["Estimated 1RM (kg)"]])
        else:
            st.info("No data for the selected exercise.")
    else:
        st.warning("Log some workouts to see progress!")
with tab3:
    st.subheader(":date: Workout Calendar View")
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
        workout_days = df["Date"].dt.day.value_counts().sort_index()
        month = st.selectbox("Select Month", range(1, 13), index=datetime.datetime.now().month - 1)
        year = st.selectbox("Select Year", range(2023, 2030), index=0)
        cal = calendar.TextCalendar()
        st.text(cal.formatmonth(year, month))
        st.write(":large_green_circle: **Days with logged workouts:**")
        for day in sorted(workout_days.index):
            st.write(f"- {day}/{month}/{year}: {workout_days[day]} workouts")
    else:
        st.warning("No workouts logged yet.")
# Logout button
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.experimental_rerun()
st.sidebar.text(":unlock: Logged in as: " + st.session_state.username)
# Run with: streamlit run gym_tracker_with_registration.py
