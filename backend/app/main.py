from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz
import random

app = FastAPI(title="Aviator Realtime Predictor API")

# ✅ Allow frontend calls from any domain (including Render frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Kenyan timezone
ke_tz = pytz.timezone("Africa/Nairobi")

# ✅ In-memory simulation of rooms (1, 2, 3)
rooms_data = {"1": [], "2": [], "3": []}

def generate_round(room_id: str):
    """Simulate a round for a given room."""
    now = datetime.now(ke_tz)
    multiplier = round(random.uniform(1.0, 20.0), 2)
    round_data = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "multiplier": multiplier
    }
    rooms_data[room_id].append(round_data)
    if len(rooms_data[room_id]) > 25:
        rooms_data[room_id].pop(0)
    return round_data


@app.get("/")
def root():
    return {"message": "Aviator Realtime Predictor API is live 🚀"}


@app.get("/rounds/{room_id}")
def get_rounds(room_id: str):
    if room_id not in rooms_data:
        return {"error": "Invalid room ID. Use 1, 2, or 3."}
    generate_round(room_id)
    return {
        "room": room_id,
        "rounds": rooms_data[room_id]
    }


@app.get("/predict/{room_id}")
def predict(room_id: str):
    if room_id not in rooms_data:
        return {"error": "Invalid room ID. Use 1, 2, or 3."}

    predicted_multiplier = round(random.uniform(1.5, 20.0), 2)
    confidence = round(random.uniform(65, 95), 1)
    cashout_point = round(predicted_multiplier * random.uniform(0.55, 0.85), 2)

    return {
        "room": room_id,
        "predicted_multiplier": predicted_multiplier,
        "confidence": confidence,
        "cashout_point": cashout_point,
        "timestamp": datetime.now(ke_tz).strftime("%Y-%m-%d %H:%M:%S")
    }
