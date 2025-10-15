import threading
import time
import os
import math
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz
import random
import statistics

from db import init_db, SessionLocal, Round

# ---------- config ----------
KE_TZ = pytz.timezone("Africa/Nairobi")
ROOMS = ["1", "2", "3"]
SIMULATE_ON_START = os.getenv("SIMULATE_ON_START", "1") == "1"
SIMULATE_INTERVAL = int(os.getenv("SIMULATE_INTERVAL", "8"))

app = FastAPI(title="Aviator Risk Analyzer (Rooms 1-3)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize DB
@app.on_event("startup")
def on_startup():
    init_db()
    if SIMULATE_ON_START:
        t = threading.Thread(target=simulate_background, daemon=True)
        t.start()

# ---------- DB helpers ----------
def save_round_to_db(room: str, multiplier: float, raw: str = None):
    db = SessionLocal()
    try:
        r = Round(room=str(room), multiplier=float(multiplier) if multiplier is not None else None, ts=datetime.utcnow(), raw=(raw or "sim"))
        db.add(r)
        db.commit()
    finally:
        db.close()

def query_rounds(room: str, limit: int = 500):
    db = SessionLocal()
    try:
        rows = db.query(Round).filter(Round.room == str(room)).order_by(Round.ts.desc()).limit(limit).all()
        return rows
    finally:
        db.close()

# ---------- simulator ----------
def simulate_one_round_for(room: str):
    r = random.random()
    if r < 0.1:
        m = round(random.uniform(1.0, 1.9), 2)
    elif r < 0.4:
        m = round(random.uniform(1.9, 4.9), 2)
    elif r < 0.8:
        m = round(random.uniform(5.0, 9.9), 2)
    else:
        m = round(random.uniform(10.0, 40.0), 2)
    save_round_to_db(room, m, raw="sim")
    return m

def simulate_background():
    while True:
        for room in ROOMS:
            simulate_one_round_for(room)
        time.sleep(SIMULATE_INTERVAL)

# ---------- endpoints ----------
@app.get("/")
def root():
    return {"status": "ok", "rooms": ROOMS, "message": "Aviator Risk Analyzer running (simulator on start: %s)" % SIMULATE_ON_START}

@app.get("/rounds/{room}")
def api_rounds(room: str, limit: int = Query(200, ge=1, le=5000)):
    if room not in ROOMS:
        raise HTTPException(status_code=404, detail="Invalid room id. Use 1,2,3.")
    rows = query_rounds(room, limit=limit)
    out = [{"ts": r.ts.astimezone(KE_TZ).isoformat(), "multiplier": r.multiplier} for r in rows]
    return {"room": room, "rounds": out}

@app.get("/stats/{room}")
def api_stats(room: str, lookback: int = Query(200, ge=10, le=5000)):
    if room not in ROOMS:
        raise HTTPException(status_code=404, detail="Invalid room id. Use 1,2,3.")
    rows = query_rounds(room, limit=lookback)
    mults = [r.multiplier for r in rows if r.multiplier is not None]
    if not mults:
        raise HTTPException(status_code=404, detail="No numeric rounds available yet")
    mean = statistics.mean(mults)
    median = statistics.median(mults)
    stdev = statistics.pstdev(mults) if len(mults) > 1 else 0.0
    
    def prob_ge(x): 
        return sum(1 for v in mults if v >= x) / len(mults)
    
    return {
        "room": room,
        "count": len(mults),
        "mean": round(mean, 3),
        "median": round(median, 3),
        "stdev": round(stdev, 3),
        "prob_ge": {
            "2.0": round(prob_ge(2.0), 3), 
            "5.0": round(prob_ge(5.0), 3), 
            "10.0": round(prob_ge(10.0), 3)
        }
    }

@app.get("/recommend/{room}")
def api_recommend(
    room: str,
    target_prob: float = Query(0.70, ge=0.01, le=0.99),
    lookback: int = Query(500, ge=50, le=2000)
):
    if room not in ROOMS:
        raise HTTPException(status_code=404, detail="Invalid room id. Use 1,2,3.")
    
    rows = query_rounds(room, limit=lookback)
    mults = [r.multiplier for r in rows if r.multiplier is not None]
    if not mults:
        raise HTTPException(status_code=404, detail="No numeric rounds available yet")

    n = len(mults)
    unique_sorted = sorted(set(mults))
    
    best = None
    for x in unique_sorted:
        prob = sum(1 for v in mults if v >= x) / n
        if prob >= target_prob:
            best = x
    
    if best is None:
        best = min(unique_sorted)
    
    recommended = round(max(1.0, best * 0.98), 2)
    achieved_prob = sum(1 for v in mults if v >= recommended) / n

    stdev = statistics.pstdev(mults) if len(mults) > 1 else 0.0
    mean = statistics.mean(mults)
    volatility = (stdev / mean) if mean > 0 else 0.0
    confidence_est = max(0.1, min(0.95, 1 - volatility))
    
    return {
        "room": room,
        "target_prob": round(target_prob, 3),
        "recommended_cashout": recommended,
        "achieved_prob": round(achieved_prob, 3),
        "lookback_count": n,
        "confidence_estimate": round(confidence_est, 3),
        "volatility": round(volatility, 4)
    }
