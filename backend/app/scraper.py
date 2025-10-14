import random

# Example mock scraper that simulates a "prediction" model.
# Replace this logic with your real ML or UI-based predictor later.
def scrape_data():
    # Simulate prediction result between 1.0 - 2.0
    result = round(random.uniform(1.0, 2.0), 2)
    return {"predicted_multiplier": result}
