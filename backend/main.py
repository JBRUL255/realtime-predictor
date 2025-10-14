# backend/main.py
from fastapi import FastAPI
from backend.db import init_db
from backend.scraper import scrape_page

app = FastAPI(title="Backend API", version="1.0.0")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {"message": "Backend is running successfully!"}

@app.get("/scrape")
def scrape(url: str):
    result = scrape_page(url)
    return result
