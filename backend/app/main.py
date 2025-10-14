# backend/main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz
import random
import math

app = FastAPI(title="Aviator Realtime Predictor API")

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated rounds store
rounds = []

# Kenyan timezone
KE_TZ = pytz.timezone("Africa/Nairobi")


@app.get("/")
def root():
    return {"message": "Aviator Predictor Backend Running ✅"}


@app.get("/rounds")
def get_rounds():
    # Return latest 50 rounds
    return rounds[-50:][::-1]


@app.get("/predict")
def predict(threshold: float = Query(2.0), risk: float = Query(0.3)):
    """
    Generate a random prediction for the next multiplier and suggest a cashout point.
    In production, this should use a trained ML model.
    """
    predicted_multiplier = round(random.uniform(1.0, 30.0), 2)
    confidence = round(random.uniform(0.6, 0.95), 2)

    # Compute suggested cashout point
    cashout_point = round(predicted_multiplier * math.sqrt(confidence) * risk, 2)

    # Log simulated round
    round_data = {
        "ts": datetime.now(KE_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "predicted_multiplier": predicted_multiplier,
        "confidence": confidence,
        "cashout_point": cashout_point,
    }
    rounds.append(round_data)

    return round_data


@app.get("/simulate")
def simulate():
    """
    Simulate a random new round every call.
    """
    new_round = {
        "ts": datetime.now(KE_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "multiplier": round(random.uniform(1.0, 50.0), 2),
    }
    rounds.append(new_round)
    return {"status": "ok", "new_round": new_round}
