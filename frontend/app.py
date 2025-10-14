# frontend/app.py
import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Aviator Live", layout="wide")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("✈️ Aviator Live (Collector + Predictor)")

st.sidebar.header("Controls")
threshold = st.sidebar.slider("Threshold", 1.0, 10.0, 2.0, 0.1)
if st.sidebar.button("Predict"):
    try:
        r = requests.get(f"{BACKEND_URL}/predict", params={"threshold": threshold}, timeout=15)
        r.raise_for_status()
        pred = r.json()
        st.metric(f"P(next ≥ {pred['threshold']})", f"{pred['probability']:.2%}")
    except Exception as e:
        st.error(f"Predict error: {e}")

st.subheader("Latest Rounds")
try:
    r = requests.get(f"{BACKEND_URL}/rounds", timeout=10)
    if r.status_code == 200:
        data = r.json()
        df = pd.DataFrame(data)
        if "ts" in df.columns:
            df["ts"] = pd.to_datetime(df["ts"])
        st.dataframe(df.head(100))
    else:
        st.info("No rounds yet or server returned: " + str(r.status_code))
except Exception as e:
    st.error(f"Cannot fetch rounds: {e}")
