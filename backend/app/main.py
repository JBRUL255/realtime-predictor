from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import random
import threading
import time

app = FastAPI(title="Aviator Predictor API", version="3.0")

# ------------------------------------------------------------
# CORS SETTINGS (allow frontend Render app to call API)
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# GLOBAL DATA STORE
# ------------------------------------------------------------
rounds = []  # in-memory list for storing simulated rounds

def generate_rounds():
    """Simulate Aviator game rounds every 10 seconds."""
    while True:
        multiplier = round(random.uniform(1.0, 20.0), 2)
        rounds.append({
            "ts": datetime.utcnow().isoformat(timespec="seconds"),  # UTC for frontend to convert
            "multiplier": multiplier
        })
        # keep only last 500 rounds
        if len(rounds) > 500:
            rounds.pop(0)
        time.sleep(10)

# start simulation thread
threading.Thread(target=generate_rounds, daemon=True).start()

# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------

@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "running", "message": "Aviator Predictor Backend Active 🚀"}

@app.get("/latest-rounds")
def get_latest_rounds():
    """Return latest 100 Aviator rounds."""
    return rounds[-100:][::-1]  # newest first

@app.get("/predict")
def predict():
    """Simulate prediction of the next multiplier."""
    # calculate fake prediction using last rounds
    if not rounds:
        predicted_multiplier = round(random.uniform(1.0, 10.0), 2)
    else:
        last_10 = [r["multiplier"] for r in rounds[-10:]]
        avg_recent = sum(last_10) / len(last_10)
        predicted_multiplier = round(random.uniform(1.0, 1.5) * avg_recent, 2)
        predicted_multiplier = min(predicted_multiplier, 20.0)

    confidence = round(random.uniform(0.70, 0.99), 2)

    return {
        "predicted_multiplier": predicted_multiplier,
        "confidence": f"{confidence:.0%}",
        "timestamp": datetime.utcnow().isoformat(timespec="seconds")
    }
