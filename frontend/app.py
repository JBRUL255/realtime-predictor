import streamlit as st
import requests
import pandas as pd
import os

# ---- Page Setup ----
st.set_page_config(page_title="✈️ Aviator Live", layout="wide")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ---- UI Header ----
st.title("✈️ Aviator Live (Collector + Predictor)")
st.sidebar.header("Controls")

# ---- Sidebar Controls ----
threshold = st.sidebar.slider("Threshold", 1.0, 10.0, 2.0, 0.1)
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 3, 30, 5)

# ---- Auto Refresh ----
if auto_refresh:
    st.sidebar.info(f"🔁 Refreshing every {refresh_interval} seconds")
    # This automatically refreshes the app
    st_autorefresh = st.experimental_data_editor if False else None  # no-op placeholder
    st_autorefresh = st.autorefresh  # for compatibility
    st_autorefresh(interval=refresh_interval * 1000, key="aviator_refresh")

# ---- Prediction ----
if st.sidebar.button("Predict"):
    try:
        r = requests.get(f"{BACKEND_URL}/predict", params={"threshold": threshold}, timeout=15)
        r.raise_for_status()
        pred = r.json()
        if "probability" in pred:
            st.metric(f"P(next ≥ {pred['threshold']})", f"{pred['probability']:.2%}")
        else:
            st.error(f"Invalid response: {pred}")
    except Exception as e:
        st.error(f"Predict error: {e}")

# ---- Latest Rounds ----
st.subheader("Latest Rounds")
try:
    r = requests.get(f"{BACKEND_URL}/rounds", timeout=10)
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list) and data:
            df = pd.DataFrame(data)
            if "ts" in df.columns:
                df["ts"] = pd.to_datetime(df["ts"])
            st.dataframe(df.tail(50).sort_values(by="ts", ascending=False), use_container_width=True)
        else:
            st.info("No rounds yet.")
    else:
        st.warning(f"Server returned: {r.status_code}")
except Exception as e:
    st.error(f"Cannot fetch rounds: {e}")

