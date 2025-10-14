from fastapi import FastAPI
from app.db import init_db, save_prediction, fetch_all_predictions
from app.scraper import scrape_data

app = FastAPI(title="Aviator Predictor Backend", version="1.0")

# Initialize the database when app starts
@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def home():
    return {"message": "✅ Aviator Predictor Backend is running"}

@app.get("/predict")
def predict():
    prediction = scrape_data()
    save_prediction(prediction["predicted_multiplier"])
    return {"status": "success", "data": prediction}

@app.get("/history")
def history():
    records = fetch_all_predictions()
    return {"count": len(records), "predictions": records}
