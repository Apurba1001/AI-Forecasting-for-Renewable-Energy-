import logging
import pathlib
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException

from src.production_phase.predict_xgboost import XGBoostForecaster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
app = FastAPI(title="XGBoost Prediction Service")
try:
    forecaster = XGBoostForecaster()
    logger.info("✅ XGBoost Forecaster initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize XGBoost Forecaster: {e}")
    forecaster = None


@app.get("/")
def home():
    return {
        "service": "XGBoost Prediction Service",
        "status": "running" if forecaster else "error",
        "model": "XGBoost (High-Performance)",
        "endpoints": ["/predict/{country_code}", "/health"],
    }


@app.get("/health")
def health():
    """Health check for Kubernetes"""
    if forecaster is None:
        raise HTTPException(status_code=503, detail="Forecaster not initialized")
    return {"status": "healthy", "model": "XGBoost"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/predict/{country_code}")
def get_prediction(country_code: str):
    """
    Generate forecast for a specific country
    Returns: Standardized format matching Holt-Winters service
    """
    if forecaster is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    logger.info(f"📊 XGBoost prediction request for: {country_code}")

    try:
        # Get prediction results
        result = forecaster.predict(country_code.upper())

        df_forecast = result["forecast_data"]
        emissions = result["emissions_kg"]

        if df_forecast.empty:
            logger.warning(f"⚠️ No data found for country: {country_code}")
            raise HTTPException(
                status_code=404,
                detail=f"No forecast data available for country: {country_code}",
            )

        logger.info(
            f"✅ Generated {len(df_forecast)} forecast records for {country_code}"
        )
        logger.info(f"🌱 Carbon footprint: {emissions:.10f} kg CO2")

        # STANDARDIZED RETURN FORMAT (matches Holt-Winters)
        return {
            "model": "XGBoost",
            "execution_carbon_kg": emissions,
            "data": df_forecast.reset_index().to_dict(orient="records"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Prediction failed for {country_code}: {e}")
        import traceback

        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
