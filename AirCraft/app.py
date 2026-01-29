# app.py
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from pathlib import Path

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
  border: 1px solid rgba(15,23,42,0.10);
  padding: 14px;
  border-radius: 12px;
}

/* DataFrames */
[data-testid="stDataFrame"] {
  border: 1px solid rgba(15,23,42,0.10);
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
# PATHS (important for Streamlit Cloud)
# =========================
APP_DIR = Path(__file__).parent
DEFAULT_FILE = APP_DIR / "aircraft_training_logs_with_pilots.csv"
AIRCRAFT_IMG = APP_DIR / "Aircraft.jpg"   # <-- image file name

# =========================
# TITLE
# =========================
st.title("✈️ Aircraft Training Operations Analytics")
st.caption("Aircraft usage • Weather impact • Maintenance risk • Pilot scheduling")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "flight_date" in df.columns:
        df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    return df

st.sidebar.header("📂 Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV (optional)", type=["csv"])

df = None

# 1) Use uploaded file if present
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if "flight_date" in df.columns:
        df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    st.sidebar.success("✅ Uploaded CSV loaded")

# 2) Else try default CSV if present in repo
elif DEFAULT_FILE.exists():
    df = load_data(DEFAULT_FILE)
    st.sidebar.success(f"✅ Loaded default: {DEFAULT_FILE.name}")

# 3) Else show landing page (NO error)
else:
    st.info("📌 No data loaded yet. Please upload a CSV from the left sidebar to see analytics.")

    # show aircraft picture if available
    if AIRCRAFT_IMG.exists():
        st.image(str(AIRCRAFT_IMG), caption="Upload your CSV to start", use_container_width=True)
    else:
        st.warning("Aircraft image not found. Add `Aircraft.jpg` in the same folder as `app.py`.")

    st.markdown("""
### What you’ll get after uploading:
- ✅ Aircraft usage (total hours by aircraft)
- ✅ Training peak times (time-of-day)
- ✅ Weather impact (Fly / Delayed / No-Fly)
- ✅ Maintenance risk score (0–1)
- ✅ Pilot scheduling recommendations
    """)
    st.stop()

# =========================
# FILTERS
# =========================
st.sidebar.header("🔎 Filters")

# Date filter
if "flight_date" in df.columns and df["flight_date"].notna().any():
    min_d = df["flight_date"].min().date()
    max_d = df["flight_date"].max().date()
    date_range = st.sidebar.date_input("Flight date range", (min_d, max_d))
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        df = df[(df["flight_date"].dt.date >= start) & (df["flight_date"].dt.date <= end)]

# Aircraft filter
if "aircraft_id" in df.columns:
    aircrafts = sorted(df["aircraft_id"].dropna().unique())
    selected_aircraft = st.sidebar.multiselect("Aircraft", aircrafts, default=list(aircrafts))
    df = df[df["aircraft_id"].isin(selected_aircraft)]

# Pilot filter
if "pilot_id" in df.columns:
    pilots = sorted(df["pilot_id"].dropna().unique())
    selected_pilots = st.sidebar.multiselect("Pilot", pilots, default=list(pilots))
    df = df[df["pilot_id"].isin(selected_pilots)]

# Weather filter
if "weather_condition" in df.columns:
    weather = sorted(df["weather_condition"].dropna().unique())
    selected_weather = st.sidebar.multiselect("Weather condition", weather, default=list(weather))
    df = df[df["weather_condition"].isin(selected_weather)]

# =========================
# KPI ROW
# =========================
k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Flights", f"{len(df):,}")
k2.metric("Total Flight Hours", f"{df['flight_hours'].sum():,.2f}" if "flight_hours" in df.columns else "0.00")
k3.metric("Delayed Flights", int((df["flight_status"] == "Delayed").sum()) if "flight_status" in df.columns else 0)
k4.metric("No-Fly Flights", int((df["flight_status"] == "No-Fly").sum()) if "flight_status" in df.columns else 0)

st.divider()

# =========================
# AIRCRAFT USAGE
# =========================
st.subheader("Aircraft Usage")

if {"aircraft_id", "flight_hours"}.issubset(df.columns):
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
        fig = plt.figure(figsize=(6,4))
        plt.bar(usage_aircraft["aircraft_id"], usage_aircraft["total_flight_hours"])
        plt.title("Total Flight Hours by Aircraft")
        plt.xlabel("Aircraft")
        plt.ylabel("Hours")
        st.pyplot(fig)
else:
    st.warning("Missing columns: aircraft_id / flight_hours")

st.divider()

# =========================
# TRAINING PEAK TIMES
# =========================
st.subheader("Training Peak Times")

if {"time_of_day", "flight_hours"}.issubset(df.columns):
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
        fig = plt.figure(figsize=(6,4))
        plt.bar(usage_time["time_of_day"], usage_time["total_flight_hours"])
        plt.title("Training by Time of Day")
        plt.xlabel("Time of Day")
        plt.ylabel("Hours")
        st.pyplot(fig)
else:
    st.warning("Missing columns: time_of_day / flight_hours")

st.divider()

# =========================
# WEATHER IMPACT
# =========================
st.subheader("Weather Impact on Flights")

if {"weather_condition", "flight_status"}.issubset(df.columns):
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
        st.write("Counts")
        st.dataframe(weather_status, use_container_width=True)

    with c2:
        st.write("Percent within weather")
        st.dataframe(weather_pct, use_container_width=True)
else:
    st.warning("Missing columns: weather_condition / flight_status")

st.divider()

# =========================
# MAINTENANCE RISK
# =========================
st.subheader("Maintenance Risk Score")

risk_df = None
needed = {"aircraft_id", "flight_hours", "maintenance_flag", "downtime_days"}

if needed.issubset(df.columns):
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
        if s.max() == s.min():
            return pd.Series([0.0]*len(s), index=s.index)
        return (s - s.min()) / (s.max() - s.min())

    risk_df["risk_score"] = (
        0.5 * minmax_series(risk_df["total_flight_hours"]) +
        0.3 * minmax_series(risk_df["maintenance_events"]) +
        0.2 * minmax_series(risk_df["avg_downtime_days"])
    ).round(2)

    risk_df = risk_df.sort_values("risk_score", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        st.dataframe(risk_df, use_container_width=True)

    with c2:
        fig = plt.figure(figsize=(6,4))
        plt.bar(risk_df["aircraft_id"], risk_df["risk_score"])
        plt.title("Maintenance Risk Score")
        plt.xlabel("Aircraft")
        plt.ylabel("Risk (0–1)")
        plt.ylim(0,1)
        st.pyplot(fig)
else:
    st.warning(f"Missing columns for risk score: {needed - set(df.columns)}")

st.divider()

# =========================
# PILOT SCHEDULING
# =========================
st.subheader("Pilot Scheduling Recommendation")

sched_needed = {"pilot_id", "pilot_duty_status", "aircraft_id", "flight_status"}

if risk_df is not None and sched_needed.issubset(df.columns):
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
        cols = ["flight_date","pilot_id","aircraft_id","risk_score","weather_condition","flight_status","recommendation"]
        cols = [c for c in cols if c in schedule_df.columns]
        st.dataframe(schedule_df[cols].head(50), use_container_width=True)

    with c2:
        counts = schedule_df["recommendation"].value_counts()
        st.dataframe(counts.rename("count").reset_index().rename(columns={"index":"recommendation"}),
                     use_container_width=True)

        fig = plt.figure(figsize=(6,4))
        plt.bar(counts.index, counts.values)
        plt.xticks(rotation=20, ha="right")
        plt.title("Scheduling Decisions")
        st.pyplot(fig)
else:
    st.warning("Scheduling section needs risk score + pilot_id/pilot_duty_status/aircraft_id/flight_status columns.")

st.divider()

# =========================
# RAW DATA
# =========================
with st.expander("🔍 Raw Data Preview"):
    st.dataframe(df.head(200), use_container_width=True)
