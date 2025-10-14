# frontend/app.py
import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
import pytz
import time
import plotly.graph_objects as go

st.set_page_config(page_title="✈️ Aviator Flight Dashboard", layout="wide", page_icon="✈️")

# ---------- CONFIG ----------
BACKEND_URL = os.getenv("BACKEND_URL", "https://your-backend-service.onrender.com")
KE_TZ = pytz.timezone("Africa/Nairobi")
REFRESH_SECONDS = 5

# ---------- STYLING ----------
st.markdown(
    """
<style>
body {background-color:#071130; color:#E6F0FF;}
.big {font-size:44px; font-weight:700;}
.small {font-size:14px; color:#bcd;}
.panel {background:#0b1224; padding:12px; border-radius:8px;}
.live-dot {height:12px;width:12px;border-radius:50%;display:inline-block;margin-right:8px;}
</style>
""",
    unsafe_allow_html=True,
)

st.title("🛫 Aviator Flight Dashboard — Live")
st.caption("Realtime predictions • smart cashout • flight-style instruments • Kenyan time (EAT)")

# ---------- LAYOUT ----------
col_left, col_center, col_right = st.columns([1.5, 2.5, 1.2])

with col_left:
    st.markdown("### 🎛 Controls", unsafe_allow_html=True)
    threshold = st.slider("Target Threshold (x)", 1.0, 20.0, 2.0, 0.1)
    risk_mode = st.selectbox("Risk mode", ["Conservative", "Balanced", "Aggressive"])
    predict_btn = st.button("🔮 Predict Next")

with col_center:
    live_placeholder = st.empty()
    gauge_area = st.empty()

with col_right:
    info_area = st.empty()
    st.markdown("### 🕒 Status")
    status_box = st.empty()

# ---------- helper functions ----------
def fetch_prediction(threshold_val):
    try:
        r = requests.get(f"{BACKEND_URL}/predict", params={"threshold": threshold_val}, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def fetch_rounds():
    try:
        r = requests.get(f"{BACKEND_URL}/rounds", timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def gauge_figure(value, title, max_val=20, color="lime"):
    # Plotly radial gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 14}},
        gauge={
            'axis': {'range': [None, max_val]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, max_val*0.3], 'color': "#06324a"},
                {'range': [max_val*0.3, max_val*0.6], 'color': "#0b5a8a"},
                {'range': [max_val*0.6, max_val], 'color': "#0f9bd1"},
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(height=240, margin=dict(t=30, b=10, l=10, r=10), paper_bgcolor="#071130", font_color="#E6F0FF")
    return fig

# ---------- ACTION: manual predict ----------
if predict_btn:
    pred = fetch_prediction(threshold)
    if pred.get("error"):
        st.error("Prediction error: " + pred["error"])
    else:
        # choose color by volatility/confidence
        vol = pred.get("volatility", 0)
        conf = pred.get("confidence", 0)
        stable = vol < 0.35 and conf > 0.6
        live_color = "lime" if stable else "orange"

        live_placeholder.markdown(
            f"<div style='padding:10px;background:#081327;border-radius:8px'>"
            f"<span class='live-dot' style='background:{live_color}'></span>"
            f"<strong>LIVE</strong>   •   <small>{pred.get('ts')} EAT</small></div>",
            unsafe_allow_html=True
        )

        # Gauges: predicted multiplier (altitude) and volatility (speed/instability)
        predicted = pred.get("predicted_multiplier", 0)
        volatility = pred.get("volatility", 0)
        cashout = pred.get("cashout_point", 1.0)
        conf_pct = int(pred.get("confidence", 0) * 100)

        g1 = gauge_figure(predicted, "Predicted Multiplier (Altitude)", max_val=max(20, predicted * 1.2), color="lime")
        g2 = gauge_figure(volatility * 100, "Volatility (Lower is Stable)", max_val=100, color="orange")

        gauge_area.plotly_chart(g1, use_container_width=True)
        gauge_area.plotly_chart(g2, use_container_width=True)

        info_area.markdown(f"**Predicted:** {predicted}x  \n**Confidence:** {conf_pct}%  \n**Suggested cashout:** **{cashout}x**")

# ---------- LIVE TABLE + AUTO-UPDATE ----------
st.markdown("---")
st.subheader("📡 Live Flight Data")

table_placeholder = st.empty()

# auto-refresh loop
while True:
    rounds_data = fetch_rounds()
    if isinstance(rounds_data, dict) and rounds_data.get("error"):
        table_placeholder.error("Failed to fetch rounds: " + rounds_data["error"])
    else:
        df = pd.DataFrame(rounds_data)
        if not df.empty:
            df["ts"] = pd.to_datetime(df["ts"])
            df = df.sort_values("ts", ascending=False).reset_index(drop=True)
            # show simplified table with time and multiplier/value
            table_placeholder.dataframe(df.head(30), use_container_width=True)
        else:
            table_placeholder.info("Waiting for rounds...")

    # status light (uses last volatility if available)
    try:
        latest = df.iloc[0] if not df.empty else None
        status_color = "lime" if latest is not None and latest.get("multiplier", 0) > 3 else "orange"
    except Exception:
        status_color = "orange"

    status_box.markdown(f"<div style='padding:8px;background:#081327;border-radius:6px'>"
                       f"<span class='live-dot' style='background:{status_color}'></span>"
                       f"<b>STATUS:</b> LIVE • {datetime.now(KE_TZ).strftime('%Y-%m-%d %H:%M:%S')} EAT</div>",
                       unsafe_allow_html=True)

    time.sleep(REFRESH_SECONDS)
    st.rerun()
