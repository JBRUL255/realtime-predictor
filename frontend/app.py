import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import time

# --- CONFIG ---
st.set_page_config(
    page_title="✈️ Aviator Live (Collector + Predictor)",
    layout="wide",
    page_icon="✈️"
)

API_BASE = "https://realtime-predictor.onrender.com"
REFRESH_INTERVAL = 10  # seconds
TIMEZONE = pytz.timezone("Africa/Nairobi")

# --- PAGE HEADER ---
st.title("✈️ Aviator Live (Collector + Predictor)")
st.caption("Real-time rounds and predicted multipliers — synced to Kenyan Time 🇰🇪")

# --- REFRESH CONTROL ---
st.sidebar.header("⚙️ Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
st.sidebar.write(f"Refresh every {REFRESH_INTERVAL} seconds when enabled.")

# --- FETCH DATA ---
def fetch_latest_rounds():
    try:
        res = requests.get(f"{API_BASE}/latest-rounds", timeout=10)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
        else:
            st.error(f"Failed to fetch rounds (status {res.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Cannot fetch rounds: {e}")
        return pd.DataFrame()

def fetch_prediction():
    try:
        res = requests.get(f"{API_BASE}/predict", timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            return {"error": f"Prediction failed ({res.status_code})"}
    except Exception as e:
        return {"error": str(e)}

# --- DISPLAY LATEST ROUNDS ---
st.subheader("🕒 Latest Rounds")

df = fetch_latest_rounds()
if not df.empty:
    # Convert timestamps to Kenyan time
    df['ts'] = pd.to_datetime(df['ts']).dt.tz_localize("UTC").dt.tz_convert(TIMEZONE)
    df = df.sort_values(by="ts", ascending=False).reset_index(drop=True)
    st.dataframe(df, use_container_width=True)
else:
    st.warning("No round data available yet. Waiting for updates...")

# --- PREDICTION SECTION ---
st.subheader("🎯 Current Prediction")
prediction = fetch_prediction()

if "error" in prediction:
    st.error(prediction["error"])
else:
    multiplier = prediction.get("predicted_multiplier", "N/A")
    conf = prediction.get("confidence", "N/A")
    st.metric(label="Predicted Multiplier", value=f"{multiplier}")
    st.caption(f"Confidence: {conf}")

# --- AUTO REFRESH LOOP ---
if auto_refresh:
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

