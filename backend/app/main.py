# backend/main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz
import random
import statistics
import math
import threading
import time

app = FastAPI(title="Aviator Smart Predictor API")

# CORS so frontend can call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory data store (simple simulator)
rounds = []
KE_TZ = pytz.timezone("Africa/Nairobi")


def simulate_round():
    """Return a single simulated multiplier using a distribution mix."""
    r = random.random()
    if r < 0.1:
        return round(random.uniform(1.0, 2.0), 2)
    elif r < 0.4:
        return round(random.uniform(2.0, 5.0), 2)
    elif r < 0.8:
        return round(random.uniform(5.0, 10.0), 2)
    else:
        return round(random.uniform(10.0, 30.0), 2)


def auto_generate_rounds():
    """Background loop that appends a new round every 8 seconds."""
    while True:
        new_round = {
            "ts": datetime.now(KE_TZ).strftime("%Y-%m-%d %H:%M:%S"),
            "multiplier": simulate_round(),
        }
        rounds.append(new_round)
        # cap memory
        if len(rounds) > 200:
            rounds.pop(0)
        time.sleep(8)


@app.on_event("startup")
def start_background_simulator():
    thread = threading.Thread(target=auto_generate_rounds, daemon=True)
    thread.start()


# ---------- API endpoints ----------

@app.get("/")
def root():
    return {"message": "Aviator Smart Predictor Backend running", "rounds": len(rounds)}


@app.get("/rounds")
def get_rounds():
    """Return the most recent rounds (newest first)."""
    return rounds[-100:][::-1]


@app.get("/predict")
def predict(threshold: float = Query(2.0, description="Target threshold")):
    """
    Smart prediction endpoint:
    - generates a predicted_multiplier (simulated here)
    - computes volatility & confidence from recent rounds
    - suggests a cashout_point based on volatility + threshold
    """
    # 1) simulated predicted multiplier
    predicted_multiplier = simulate_round()

    # 2) compute volatility from prior rounds
    last_vals = [r["multiplier"] for r in rounds[-12:]]  # lookback
    if last_vals:
        avg = statistics.mean(last_vals)
        stdev = statistics.pstdev(last_vals) if len(last_vals) > 1 else 0.0
        volatility = stdev / avg if avg != 0 else 0.0
    else:
        avg = 5.0
        stdev = 1.0
        volatility = 0.2

    # 3) confidence (higher when volatility lower)
    confidence = round(max(0.45, 1.0 - volatility), 2)

    # 4) smart cashout logic
    if volatility > 0.35:
        # unstable: choose far safer cashout
        cashout_point = min(predicted_multiplier * 0.35, max(1.1, threshold))
    else:
        # stable: allow higher capture but cap sensibly
        cashout_point = min(predicted_multiplier * 0.75, max(threshold * 1.1, predicted_multiplier * 0.4))

    cashout_point = round(max(1.0, cashout_point), 2)

    prediction = {
        "ts": datetime.now(KE_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "predicted_multiplier": round(predicted_multiplier, 2),
        "confidence": confidence,
        "volatility": round(volatility, 3),
        "cashout_point": cashout_point,
    }

    # store prediction snapshot as part of rounds history for visibility
    rounds.append({
        "ts": prediction["ts"],
        "multiplier": prediction["predicted_multiplier"]
    })

    # keep list size reasonable
    if len(rounds) > 200:
        rounds.pop(0)

    return prediction
