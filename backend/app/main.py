from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import random
import threading
import time

app = FastAPI(title="Aviator Predictor API", version="2.0")

# ------------------------------------------------------------
# CORS SETTINGS (Allow frontend to call this API)
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# SIMULATED GAME DATA
# ------------------------------------------------------------
rounds = []  # store game rounds

def generate_rounds():
    """Simulate Aviator rounds every 10 seconds."""
    while True:
        # simulate random multiplier values
        multiplier = round(random.uniform(1.0, 20.0), 2)
        # add new round with Kenyan time
        rounds.append({
            "ts": (datetime.utcnow() + timedelta(hours=3)).isoformat(timespec="seconds"),
            "multiplier": multiplier
        })
        # keep only the last 500 rounds to avoid memory bloat
        if len(rounds) > 500:
            rounds.pop(0)
        time.sleep(10)

# Start background thread when server boots
threading.Thread(target=generate_rounds, daemon=True).start()

# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------

@app.get("/")
def root():
    """Simple health check endpoint."""
    return {"status": "running", "message": "Aviator Predictor Backend Active 🚀"}

@app.get("/rounds")
def get_rounds():
    """Return latest Aviator rounds."""
    return rounds[-100:][::-1]  # last 100, newest first

@app.get("/predict")
def predict(threshold: float = Query(2.0, description="Prediction threshold")):
    """Return mock probability that next round ≥ threshold."""
    # basic fake probability model
    probability = max(0.0, 1.0 - (threshold / 20.0) + random.uniform(-0.1, 0.1))
    probability = round(probability, 2)
    return {
        "threshold": threshold,
        "probability": probability,
        "timestamp": (datetime.utcnow() + timedelta(hours=3)).isoformat(timespec="seconds")
    }
