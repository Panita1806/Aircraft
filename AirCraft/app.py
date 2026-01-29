# app.py
from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Aircraft Training Ops Analytics",
    page_icon="✈️",
    layout="wide"
)

# =========================
# LIGHT AIRCRAFT THEME (CSS)
# =========================
st.markdown("""
<style>
.stApp {
  background: linear-gradient(180deg, #F7FAFF 0%, #FFFFFF 50%, #F3F7FF 100%);
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #FFFFFF 0%, #F4F8FF 100%) !important;
}
[data-testid="stSidebar"] * {
  color: #0F172A !important;
}

/* KPI cards */
[data-testid="stMetric"] {
  background: #FFFFFF;
  border: 1px solid rgba(15,23,42,0.1);
  padding: 14px;
  border-radius: 12px;
}

/* DataFrames */
[data-testid="stDataFrame"] {
  border: 1px solid rgba(15,23,42,0.1);
  border-radius: 10px;
}

/* Multiselect tags */
.stMultiSelect [data-baseweb="tag"] {
  background-color: rgba(37,99,235,0.12) !important;
}
.stMultiSelect [data-baseweb="tag"] span {
  color: #1D4ED8 !important;
}

/* Spacing */
.block-container {
  padding-top: 1.2rem;
}
</style>
""", unsafe_allow_html=True)

# =========================
# TITLE
# =========================
st.title("✈️ Aircraft Training Operations Analytics")
st.caption("Aircraft usage • Weather impact • Maintenance risk • Pilot scheduling")

# =========================
# PATHS (IMPORTANT FOR DEPLOYMENT)
# =========================
APP_DIR = Path(__file__).parent
DEFAULT_FILE = APP_DIR / "aircraft_training_logs_with_pilots.csv"
AIRCRAFT_IMG = APP_DIR / "Aircraft.jpg"

# =========================
# LOAD DATA (UPLOAD FIRST; ELSE DEFAULT; ELSE LANDING)
# =========================
st.sidebar.header("📂 Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

df = None

if uploaded_file is not None:
    # Use uploaded data
    df = pd.read_csv(uploaded_file)
    st.sidebar.success("Using uploaded CSV ✅")

elif DEFAULT_FILE.exists():
    # Use default data included in repo
    df = pd.read_csv(DEFAULT_FILE)
    st.sidebar.success(f"Loaded default: {DEFAULT_FILE.name} ✅")

else:
    # LANDING PAGE (no data available)
    st.markdown("## Welcome 👋")
    if AIRCRAFT_IMG.exists():
        st.image(str(AIRCRAFT_IMG), use_container_width=True)

    st.markdown("""
### 📌 Upload your CSV to begin

Once uploaded, you will get:
- ✅ Aircraft usage analytics
- ✅ Weather impact on flight status
- ✅ Maintenance risk scoring
- ✅ Pilot scheduling recommendations

⬅️ Use the sidebar to upload your CSV.
""")
    st.stop()  # ⛔ stops here, dashboard won't run

# Ensure date format
if "flight_date" in df.columns:
    df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")

# =========================
# VALIDATE REQUIRED COLUMNS (nice errors)
# =========================
required_cols = [
    "flight_date", "aircraft_id", "pilot_id",
    "weather_condition", "flight_status",
    "flight_hours", "maintenance_flag", "downtime_days",
    "pilot_duty_status", "time_of_day"
]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing columns in CSV: {missing}")
    st.stop()

# =========================
# FILTERS
# =========================
st.sidebar.header("🔎 Filters")

# Date filter
if df["flight_date"].notna().any():
    min_d = df["flight_date"].min().date()
    max_d = df["flight_date"].max().date()
    date_range = st.sidebar.date_input("Flight date range", (min_d, max_d))
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        df = df[(df["flight_date"].dt.date >= start) & (df["flight_date"].dt.date <= end)]

# Aircraft filter
aircrafts = sorted(df["aircraft_id"].dropna().unique())
selected_aircraft = st.sidebar.multiselect("Aircraft", aircrafts, default=aircrafts)
df = df[df["aircraft_id"].isin(selected_aircraft)]

# Pilot filter
pilots = sorted(df["pilot_id"].dropna().unique())
selected_pilots = st.sidebar.multiselect("Pilot", pilots, default=pilots)
df = df[df["pilot_id"].isin(selected_pilots)]

# Weather filter
weather = sorted(df["weather_condition"].dropna().unique())
selected_weather = st.sidebar.multiselect("Weather condition", weather, default=weather)
df = df[df["weather_condition"].isin(selected_weather)]

# =========================
# KPI ROW
# =========================
k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Flights", f"{len(df):,}")
k2.metric("Total Flight Hours", f"{df['flight_hours'].sum():,.2f}")
k3.metric("Delayed Flights", f"{int((df['flight_status'] == 'Delayed').sum()):,}")
k4.metric("No-Fly Flights", f"{int((df['flight_status'] == 'No-Fly').sum()):,}")

st.divider()

# =========================
# AIRCRAFT USAGE
# =========================
st.subheader("Aircraft Usage")

usage_aircraft = (
    df.groupby("aircraft_id")["flight_hours"]
    .sum()
    .reset_index(name="total_flight_hours")
    .sort_values("total_flight_hours", ascending=False)
)

c1, c2 = st.columns(2)

with c1:
    st.dataframe(usage_aircraft, use_container_width=True)

with c2:
    fig = plt.figure(figsize=(6, 4))
    plt.bar(usage_aircraft["aircraft_id"], usage_aircraft["total_flight_hours"])
    plt.title("Total Flight Hours by Aircraft")
    plt.xlabel("Aircraft")
    plt.ylabel("Hours")
    st.pyplot(fig)

st.divider()

# =========================
# TRAINING PEAK TIMES
# =========================
st.subheader("Training Peak Times")

usage_time = (
    df.groupby("time_of_day")["flight_hours"]
    .sum()
    .reset_index(name="total_flight_hours")
    .sort_values("total_flight_hours", ascending=False)
)

c1, c2 = st.columns(2)

with c1:
    st.dataframe(usage_time, use_container_width=True)

with c2:
    fig = plt.figure(figsize=(6, 4))
    plt.bar(usage_time["time_of_day"], usage_time["total_flight_hours"])
    plt.title("Training by Time of Day")
    plt.xlabel("Time of Day")
    plt.ylabel("Hours")
    st.pyplot(fig)

st.divider()

# =========================
# WEATHER IMPACT
# =========================
st.subheader("Weather Impact on Flights")

weather_status = (
    df.groupby(["weather_condition", "flight_status"])
    .size()
    .reset_index(name="count")
)

weather_pct = weather_status.copy()
weather_pct["percent"] = (
    weather_pct["count"] /
    weather_pct.groupby("weather_condition")["count"].transform("sum") * 100
).round(1)

c1, c2 = st.columns(2)

with c1:
    st.write("Counts (weather × status)")
    st.dataframe(weather_status, use_container_width=True)

with c2:
    st.write("Percent within each weather condition")
    st.dataframe(weather_pct, use_container_width=True)

st.divider()

# =========================
# MAINTENANCE RISK
# =========================
st.subheader("Maintenance Risk Score")

risk_df = (
    df.groupby("aircraft_id")
    .agg(
        total_flight_hours=("flight_hours", "sum"),
        maintenance_events=("maintenance_flag", "sum"),
        avg_downtime_days=("downtime_days", "mean")
    )
    .reset_index()
)

def minmax_series(s: pd.Series) -> pd.Series:
    mn, mx = float(s.min()), float(s.max())
    if mx == mn:
        return pd.Series([0.0] * len(s), index=s.index)
    return (s - mn) / (mx - mn)

risk_df["hours_n"] = minmax_series(risk_df["total_flight_hours"])
risk_df["maint_n"] = minmax_series(risk_df["maintenance_events"])
risk_df["down_n"]  = minmax_series(risk_df["avg_downtime_days"])

# weights (you can tweak)
w_hours, w_maint, w_down = 0.5, 0.3, 0.2

risk_df["risk_score"] = (
    w_hours * risk_df["hours_n"] +
    w_maint * risk_df["maint_n"] +
    w_down  * risk_df["down_n"]
).round(2)

risk_df = risk_df.sort_values("risk_score", ascending=False)

c1, c2 = st.columns(2)

with c1:
    st.dataframe(
        risk_df[["aircraft_id", "total_flight_hours", "maintenance_events", "avg_downtime_days", "risk_score"]],
        use_container_width=True
    )
    st.caption("Risk score is a simple combined indicator (0–1). Higher = more operational attention.")

with c2:
    fig = plt.figure(figsize=(6, 4))
    plt.bar(risk_df["aircraft_id"], risk_df["risk_score"])
    plt.title("Maintenance Risk Score by Aircraft")
    plt.xlabel("Aircraft")
    plt.ylabel("Risk (0–1)")
    plt.ylim(0, 1)
    st.pyplot(fig)

st.divider()

# =========================
# PILOT SCHEDULING
# =========================
st.subheader("Pilot Scheduling Recommendation")

schedule_df = df.merge(
    risk_df[["aircraft_id", "risk_score"]],
    on="aircraft_id",
    how="left"
)

def decision(row):
    if row["pilot_duty_status"] != "Available":
        return "Do Not Assign"
    if row["flight_status"] != "Fly":
        return "Do Not Assign"
    if row["risk_score"] >= 0.7:
        return "Avoid (High Risk)"
    elif row["risk_score"] >= 0.4:
        return "Assign with Caution"
    else:
        return "Assign"

schedule_df["recommendation"] = schedule_df.apply(decision, axis=1)

c1, c2 = st.columns(2)

with c1:
    st.dataframe(
        schedule_df[
            ["flight_date", "pilot_id", "pilot_duty_status", "aircraft_id",
             "risk_score", "weather_condition", "flight_status", "recommendation"]
        ].head(50),
        use_container_width=True
    )

with c2:
    counts = schedule_df["recommendation"].value_counts()
    st.write("Recommendation counts")
    st.dataframe(counts.rename("count").reset_index().rename(columns={"index": "recommendation"}))

    fig = plt.figure(figsize=(6, 4))
    plt.bar(counts.index.astype(str), counts.values)
    plt.xticks(rotation=20, ha="right")
    plt.title("Scheduling Decisions")
    st.pyplot(fig)

st.divider()

# =========================
# RAW DATA
# =========================
with st.expander("🔍 Raw Data Preview"):
    st.dataframe(df.head(200), use_container_width=True)
