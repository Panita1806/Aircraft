# =========================
# LOAD DATA (STRICT CONTROL)
# =========================
APP_DIR = Path(__file__).parent
DEFAULT_FILE = APP_DIR / "aircraft_training_logs_with_pilots.csv"
AIRCRAFT_IMG = APP_DIR / "Aircraft.jpg"

st.sidebar.header("📂 Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

df = None

# -------------------------
# CASE 1: Uploaded file
# -------------------------
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if "flight_date" in df.columns:
        df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")

# -------------------------
# CASE 2: Default CSV exists
# -------------------------
elif DEFAULT_FILE.exists():
    df = pd.read_csv(DEFAULT_FILE)
    if "flight_date" in df.columns:
        df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")

# -------------------------
# CASE 3: NO DATA → LANDING PAGE
# -------------------------
else:
    st.markdown("## ✈️ Aircraft Training Operations Analytics")

    if AIRCRAFT_IMG.exists():
        st.image(
            str(AIRCRAFT_IMG),
            use_container_width=True
        )

    st.markdown("""
### 📌 Upload your training CSV to begin

Once uploaded, you will get:
- ✅ Aircraft usage analytics
- ✅ Weather impact on flights
- ✅ Maintenance risk scoring
- ✅ Pilot scheduling recommendations

⬅️ **Use the sidebar to upload your CSV**
    """)

    st.stop()   # ⛔ THIS IS THE KEY LINE
