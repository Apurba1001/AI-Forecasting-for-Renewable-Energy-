# API wrapper for lightweight Holt-Winters prediction service
from fastapi import FastAPI
from src.production_phase.predict_lightweight import generate_forecast

app = FastAPI(title="Holt-Winters Service")

@app.get("/predict/{country_code}")
def predict(country_code: str):
    df = generate_forecast(country_code)
    # Convert to JSON-friendly format
    return df.reset_index().to_dict(orient="records")
