# frontend/app.py
import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
import pytz
import time

st.set_page_config(page_title="Aviator Live Predictor", layout="wide")

# Backend URL (Render service or localhost)
BACKEND_URL = os.getenv("BACKEND_URL", "https://your-backend-service.onrender.com")

# Kenyan timezone
KE_TZ = pytz.timezone("Africa/Nairobi")

st.title("✈️ Aviator Live Predictor Dashboard")

st.sidebar.header("🎛 Controls")
threshold = st.sidebar.slider("Prediction Threshold", 1.0, 10.0, 2.0, 0.1)
risk = st.sidebar.slider("Risk Factor (Higher = Riskier)", 0.1, 1.0, 0.3, 0.05)

if st.sidebar.button("🔮 Predict Next Round"):
    try:
        r = requests.get(f"{BACKEND_URL}/predict", params={"threshold": threshold, "risk": risk}, timeout=15)
        r.raise_for_status()
        pred = r.json()

        st.subheader("🎯 Current Prediction")
        st.metric("Predicted Multiplier", f"{pred['predicted_multiplier']}x")
        st.metric("Confidence", f"{pred['confidence'] * 100:.0f}%")
        st.markdown(f"💰 **Suggested Cashout Point:** `{pred['cashout_point']}x`")

    except Exception as e:
        st.error(f"Prediction failed: {e}")

st.divider()
st.subheader("📊 Latest Game Rounds")

# Auto-refresh every 5 seconds
while True:
    try:
        r = requests.get(f"{BACKEND_URL}/rounds", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if len(data) == 0:
                st.info("No round data available yet. Waiting for updates...")
            else:
                df = pd.DataFrame(data)
                if "ts" in df.columns:
                    df["ts"] = pd.to_datetime(df["ts"])
                df = df.sort_values(by="ts", ascending=False)
                st.dataframe(df.head(20), use_container_width=True)
        else:
            st.warning(f"Failed to fetch rounds (status {r.status_code})")
    except Exception as e:
        st.error(f"Failed to fetch rounds: {e}")

    # Kenyan time at bottom
    st.caption(f"🕒 Updated at: {datetime.now(KE_TZ).strftime('%Y-%m-%d %H:%M:%S')} EAT")

    # Wait before refreshing
    time.sleep(5)
    st.experimental_rerun()
