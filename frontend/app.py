import streamlit as st
import requests
import time
from datetime import datetime
import pytz
import plotly.graph_objects as go

st.set_page_config(page_title="Aviator Flight Dashboard ✈️", layout="centered")

# Backend URL
BACKEND_URL = "https://realtime-predictor.onrender.com"

# Title
st.title("🛫 Aviator Flight Dashboard — Live Prediction")

# Select Room
room = st.selectbox("Select Aviator Room", ["1", "2", "3"])
st.markdown("---")

placeholder = st.empty()

def get_kenya_time():
    tz = pytz.timezone("Africa/Nairobi")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def fetch_data(endpoint):
    try:
        res = requests.get(f"{BACKEND_URL}/{endpoint}", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        return None
    return None

# Automatically retry and switch rooms if one fails
def smart_fetch(endpoint):
    result = fetch_data(endpoint)
    if result is None or ("detail" in result if isinstance(result, dict) else False):
        # Switch to next available room
        current = int(room)
        alt_room = str((current % 3) + 1)
        st.warning(f"Room {room} unavailable — switching to Room {alt_room}")
        time.sleep(1)
        return fetch_data(endpoint.replace(f"/{room}", f"/{alt_room}"))
    return result

while True:
    rounds_data = smart_fetch(f"rounds/{room}")
    pred_data = smart_fetch(f"predict/{room}")

    with placeholder.container():
        st.subheader(f"📡 Room {room} — Live Updates")

        if pred_data:
            st.metric("🎯 Predicted Multiplier", f"{pred_data['predicted_multiplier']}x")
            st.metric("💰 Suggested Cashout Point", f"{pred_data['cashout_point']}x")
            st.metric("📈 Confidence", f"{pred_data['confidence']}%")
            st.caption(f"🕒 Updated at: {pred_data['timestamp']} (Kenyan Time)")
        else:
            st.error("Prediction fetch failed for all rooms.")

        if rounds_data:
            multipliers = [r["multiplier"] for r in rounds_data["rounds"]]
            timestamps = [r["timestamp"] for r in rounds_data["rounds"]]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=timestamps, y=multipliers, mode="lines+markers", name="Multiplier"))
            fig.update_layout(title=f"📊 Room {room} — Last 20 Rounds", xaxis_title="Time", yaxis_title="Multiplier (x)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No round data available in any room.")

        st.markdown("---")
        st.caption(f"Last refresh: {get_kenya_time()}")

    time.sleep(10)
