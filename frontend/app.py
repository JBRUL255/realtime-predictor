import streamlit as st
import requests
import pandas as pd
import time
import plotly.graph_objects as go

st.set_page_config(page_title="Aviator Flight Dashboard", layout="wide")

BACKEND_URL = "https://your-backend-url.onrender.com"  # Replace with your backend URL

st.title("🛫 Betika Aviator Flight Dashboard (Rooms 1–3)")

room = st.sidebar.selectbox("Select Room", ["1", "2", "3"])
refresh_rate = st.sidebar.slider("Refresh interval (seconds)", 3, 30, 8)

st.markdown(f"### 🎮 Current Room: **{room}**")

rounds_container = st.empty()
prediction_container = st.empty()


def fetch_rounds(room_id):
    try:
        res = requests.get(f"{BACKEND_URL}/rounds/{room_id}", timeout=10)
        if res.status_code == 200:
            return res.json()["rounds"]
        else:
            st.warning(f"Failed to fetch rounds (status {res.status_code})")
            return []
    except Exception as e:
        st.error(f"Cannot fetch rounds: {e}")
        return []


def fetch_prediction(room_id):
    try:
        res = requests.get(f"{BACKEND_URL}/predict/{room_id}", timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            st.warning("Prediction fetch failed.")
            return None
    except Exception as e:
        st.error(f"Cannot fetch prediction: {e}")
        return None


# Main loop for real-time refresh
while True:
    rounds = fetch_rounds(room)
    prediction = fetch_prediction(room)

    if rounds:
        df = pd.DataFrame(rounds)
        rounds_container.subheader("📊 Recent Rounds (Kenyan Time)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["timestamp"],
            y=df["multiplier"],
            mode="lines+markers",
            line=dict(shape="spline"),
            name=f"Room {room}"
        ))
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Multiplier (x)",
            height=400
        )
        rounds_container.plotly_chart(fig, use_container_width=True)

    if prediction:
        prediction_container.markdown(f"""
        ### 🎯 Prediction — Room {prediction['room']}
        - **Predicted Multiplier:** {prediction['predicted_multiplier']}x  
        - **Confidence:** {prediction['confidence']}%  
        - 💰 **Suggested Cashout:** {prediction['cashout_point']}x  
        - 🕒 **Updated:** {prediction['timestamp']}  
        """)

    time.sleep(refresh_rate)
    st.rerun()
