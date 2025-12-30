# API wrapper for performance XG Boost prediction service
from fastapi import FastAPI
from src.production_phase.predict_xgboost import generate_forecast

app = FastAPI(title="XGBoost Service")

@app.get("/predict/{country_code}")
def predict(country_code: str):
    df = generate_forecast(country_code)
    return df.reset_index().to_dict(orient="records")