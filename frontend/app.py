import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 🌍 CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Aviator Live", layout="wide")
BACKEND_URL = os.getenv("BACKEND_URL", "https://realtime-predictor-backend.onrender.com")  # <-- replace with your backend URL

# ---------------------------------------------------------
# 🛫 HEADER
# ---------------------------------------------------------
st.title("✈️ Aviator Live (Collector + Predictor)")

# ---------------------------------------------------------
# 🔁 AUTO REFRESH (every 5 seconds)
# ---------------------------------------------------------
# Streamlit built-in auto-refresh
st_autorefresh = getattr(st, "autorefresh", None)
if st_autorefresh:
    st_autorefresh(interval=5000, limit=None, key="data_refresh")
else:
    # fallback if Streamlit <1.26
    st.experimental_rerun()

# ---------------------------------------------------------
# ⚙️ CONTROLS
# ---------------------------------------------------------
st.sidebar.header("Controls")
threshold = st.sidebar.slider("Threshold", 1.0, 10.0, 2.0, 0.1)

if st.sidebar.button("Predict"):
    try:
        r = requests.get(f"{BACKEND_URL}/predict", params={"threshold": threshold}, timeout=10)
        r.raise_for_status()
        pred = r.json()
        st.metric(f"P(next ≥ {pred['threshold']})", f"{pred['probability']:.2%}")
    except Exception as e:
        st.error(f"Predict error: {e}")

# ---------------------------------------------------------
# 📊 LATEST ROUNDS TABLE
# ---------------------------------------------------------
st.subheader("Latest Rounds")

try:
    r = requests.get(f"{BACKEND_URL}/rounds", timeout=10)
    if r.status_code == 200:
        data = r.json()
        df = pd.DataFrame(data)

        # ✅ Convert timestamp to Kenya time
        if "ts" in df.columns:
            df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
            df["ts"] = df["ts"] + timedelta(hours=3)  # convert UTC → EAT (Kenya)
            df = df.sort_values("ts", ascending=False)

        st.dataframe(df.head(100), use_container_width=True)
    else:
        st.info(f"No rounds yet or server returned: {r.status_code}")
except Exception as e:
    st.error(f"Cannot fetch rounds: {e}")

# ---------------------------------------------------------
# 📝 FOOTER
# ---------------------------------------------------------
st.markdown(
    "<small>🕒 Data auto-refreshes every 5 seconds | Timezone: EAT (UTC+3)</small>",
    unsafe_allow_html=True,
)
