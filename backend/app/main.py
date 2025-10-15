from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz
import random

app = FastAPI(title="Aviator Realtime Predictor API 🚀")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory round store
aviator_data = {"1": [], "2": [], "3": []}

def generate_round(room_id: str):
    """Simulate round data for the room."""
    multiplier = round(random.uniform(1.0, 50.0), 2)
    ke_time = datetime.now(pytz.timezone("Africa/Nairobi")).strftime("%Y-%m-%d %H:%M:%S")
    aviator_data[room_id].append({"timestamp": ke_time, "multiplier": multiplier})
    aviator_data[room_id] = aviator_data[room_id][-20:]  # keep latest 20 only

@app.get("/")
def root():
    return {"message": "Aviator Realtime Predictor API active 🇰🇪"}

@app.get("/rounds/{room_id}")
def get_rounds(room_id: str):
    if room_id not in aviator_data:
        raise HTTPException(status_code=404, detail="Room not found")
    generate_round(room_id)
    return {"room": room_id, "rounds": aviator_data[room_id]}

@app.get("/predict/{room_id}")
def predict(room_id: str):
    if room_id not in aviator_data:
        raise HTTPException(status_code=404, detail="Room not found")

    recent_rounds = aviator_data[room_id][-5:]
    if not recent_rounds:
        generate_round(room_id)
        recent_rounds = aviator_data[room_id][-5:]

    multipliers = [r["multiplier"] for r in recent_rounds]
    avg = sum(multipliers) / len(multipliers)
    confidence = random.randint(70, 95)
    predicted_multiplier = round(avg * random.uniform(1.05, 1.35), 2)
    cashout_point = round(predicted_multiplier / random.uniform(3, 5), 2)

    ke_time = datetime.now(pytz.timezone("Africa/Nairobi")).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "room": room_id,
        "predicted_multiplier": predicted_multiplier,
        "confidence": confidence,
        "cashout_point": cashout_point,
        "timestamp": ke_time
    }
