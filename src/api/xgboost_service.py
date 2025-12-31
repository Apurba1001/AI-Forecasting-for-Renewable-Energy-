from fastapi import FastAPI, HTTPException
from src.production_phase.predict_xgboost import XGBoostForecaster

app = FastAPI(title="XGBoost Prediction Service")
forecaster = XGBoostForecaster()

@app.get("/predict/{country_code}")
def get_prediction(country_code: str):
    # The API layer is now extremely 'thin' (Good Architecture)
    result = forecaster.predict(country_code.upper())
    
    if result.empty:
        raise HTTPException(status_code=404, detail="Data not found for this country")
        
    return result.reset_index().to_dict(orient="records")