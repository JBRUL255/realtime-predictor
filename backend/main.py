# backend/main.py
import os, logging, threading
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from datetime import datetime

from .db import init_db, SessionLocal, Round
from .scraper import start_playwright_collector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aviator-backend")

app = FastAPI(title="Aviator Predictor (scraper)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    logger.info("Initializing DB...")
    init_db()
    # start scraper thread if url provided
    from .scraper import AVIATOR_PAGE_URL
    if AVIATOR_PAGE_URL:
        logger.info("Starting collector thread...")
        t = threading.Thread(target=start_playwright_collector, args=(AVIATOR_PAGE_URL,), daemon=True)
        t.start()
    else:
        logger.warning("AVIATOR_PAGE_URL not set, scraper disabled.")

class RoundOut(BaseModel):
    id: int
    round_id: str = None
    ts: datetime
    multiplier: float = None
    raw: str = None
    class Config:
        orm_mode = True

class PredictionOut(BaseModel):
    threshold: float
    probability: float

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/rounds", response_model=List[RoundOut])
def get_rounds(limit: int = Query(100, ge=1, le=2000)):
    db = SessionLocal()
    try:
        rows = db.query(Round).order_by(Round.ts.desc()).limit(limit).all()
        if not rows:
            raise HTTPException(status_code=404, detail="No rounds yet")
        return rows
    finally:
        db.close()

@app.get("/predict", response_model=PredictionOut)
def predict(threshold: float = Query(2.0, ge=1.0)):
    # placeholder model: return a simulated probability; replace with real model later
    import random
    p = round(random.uniform(0.05, 0.95), 3)
    return {"threshold": threshold, "probability": p}
