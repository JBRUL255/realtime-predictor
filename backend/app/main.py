from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import threading
import time
from datetime import datetime

app = FastAPI(title="Aviator Live Backend")

# ---- Enable CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for simplicity (you can restrict later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Data Storage ----
ROUNDS = []  # Store rounds in memory


# ---- Models ----
class Round(BaseModel):
    ts: str
    multiplier: float


# ---- Helper: Generate Random Rounds ----
def simulate_rounds():
    """Continuously simulates random Aviator multipliers every 10 seconds."""
    while True:
        multiplier = round(random.uniform(1.0, 20.0), 2)
        ROUNDS.append({"ts": datetime.utcnow().isoformat(), "multiplier": multiplier})
        if len(ROUNDS) > 200:
            ROUNDS.pop(0)  # Keep only the latest 200
        time.sleep(10)  # every 10 seconds


# Start the background simulation thread
threading.Thread(target=simulate_rounds, daemon=True).start()


# ---- Routes ----
@app.get("/")
def root():
    return {"message": "Aviator API running", "rounds_count": len(ROUNDS)}


@app.get("/predict")
def predict(threshold: float = Query(..., description="Multiplier threshold")):
    """Simple simulated prediction."""
    probability = round(random.random(), 3)
    return {"threshold": threshold, "probability": probability}


@app.get("/rounds")
def get_rounds():
    """Fetch the latest simulated rounds."""
    return ROUNDS[-100:]


@app.post("/rounds")
def add_round(multiplier: float):
    """Manually add a round if needed."""
    ROUNDS.append({"ts": datetime.utcnow().isoformat(), "multiplier": multiplier})
    if len(ROUNDS) > 200:
        ROUNDS.pop(0)
    return {"message": "Round added", "count": len(ROUNDS)}
