import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import pytz

st.set_page_config(page_title="Aviator Risk Analyzer", layout="wide")

# Backend URL configuration
BACKEND_URL = st.secrets.get("BACKEND_URL") or st.sidebar.text_input("Backend URL", "http://localhost:8000")
KE_TZ = pytz.timezone("Africa/Nairobi")

st.title("Aviator Risk Analyzer — Rooms 1,2,3 (Kenya time)")

# Controls
room = st.sidebar.selectbox("Select room", ["1", "2", "3"])
lookback = st.sidebar.slider("Lookback rounds (max used for stats)", 50, 2000, 500, step=50)
target_prob_pct = st.sidebar.slider("Desired empirical success probability (%)", 50, 95, 70)
target_prob = target_prob_pct / 100.0

if st.sidebar.button("Refresh now"):
    st.rerun()

# Helpers
def safe_get_json(path, params=None, timeout=10):
    try:
        r = requests.get(f"{BACKEND_URL}/{path}", params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Failed: {path} → {e}")
        return None

# Fetch rounds table
st.subheader(f"Room {room} — recent rounds (live sample)")
rounds_resp = safe_get_json(f"rounds/{room}", params={"limit": lookback})
if rounds_resp and "rounds" in rounds_resp:
    df = pd.DataFrame(rounds_resp["rounds"])
    if not df.empty:
        df["ts_local"] = pd.to_datetime(df["ts"], errors="coerce")
        st.dataframe(
            df[["ts_local", "multiplier"]]
            .rename(columns={"ts_local": "ts (EAT)"})
            .sort_values("ts (EAT)", ascending=False)
            .head(50), 
            use_container_width=True
        )
    else:
        st.info("No rounds available yet for this room.")
else:
    st.warning("No rounds data returned.")

# Stats
stats = safe_get_json(f"stats/{room}", params={"lookback": lookback})
if stats:
    st.markdown("### Statistics")
    cols = st.columns(4)
    cols[0].metric("Count", stats["count"])
    cols[1].metric("Mean", round(stats["mean"], 2))
    cols[2].metric("Median", round(stats["median"], 2))
    cols[3].metric("StdDev", round(stats["stdev"], 3))
    st.write("Empirical P(next ≥ x):", stats.get("prob_ge", {}))

# Recommendation
recommend = safe_get_json(f"recommend/{room}", params={"target_prob": target_prob, "lookback": lookback}, timeout=20)
if recommend:
    st.markdown("## Final recommended cashout (empirical)")
    st.success(f"✅ Recommended cashout for target {int(target_prob*100)}% → **{recommend['recommended_cashout']}x**")
    st.write(f"Achieved empirical prob at that cashout: {recommend['achieved_prob']*100:.1f}% (lookback {recommend['lookback_count']})")
    st.write(f"Confidence estimate: {recommend['confidence_estimate']*100:.1f}% — volatility: {recommend['volatility']}")
    st.caption("This is empirical guidance based on historical rounds. Not a guarantee. Use responsibly.")

st.caption(f"Last refreshed: {datetime.now(KE_TZ).strftime('%Y-%m-%d %H:%M:%S')} EAT")

# Auto refresh
auto = st.sidebar.checkbox("Auto refresh", value=True)
interval = st.sidebar.slider("Auto-refresh interval seconds", 5, 60, 10)
if auto:
    time.sleep(interval)
    st.rerun()
