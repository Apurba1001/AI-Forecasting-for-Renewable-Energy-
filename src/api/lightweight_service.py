from fastapi import FastAPI, HTTPException
from src.production_phase.predict_lightweight import HoltWintersForecaster
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Holt Winters Prediction Service")

# Initialize forecaster once at startup
try:
    forecaster = HoltWintersForecaster()
    logger.info("✅ Holt-Winters Forecaster initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Holt-Winters Forecaster: {e}")
    forecaster = None

@app.get("/health")
def health():
    """Health check for Kubernetes"""
    if forecaster is None:
        raise HTTPException(status_code=503, detail="Forecaster not initialized")
    return {"status": "healthy", "model": "Holt-Winters"}

@app.get("/predict/{country_code}")
def get_prediction(country_code: str):
    """
    Generate forecast for a specific country
    Returns: Standardized format matching XGBoost service
    """
    if forecaster is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    logger.info(f"🌱 Holt-Winters prediction request for: {country_code}")
    
    try:
        # Get prediction results
        result = forecaster.predict(country_code.upper())
        
        df_forecast = result["forecast_data"]
        emissions = result["emissions_kg"]
        
        if df_forecast.empty:
            logger.warning(f"⚠️ No data found for country: {country_code}")
            raise HTTPException(
                status_code=404, 
                detail=f"No forecast data available for country: {country_code}"
            )
        
        logger.info(f"✅ Generated {len(df_forecast)} forecast records for {country_code}")
        logger.info(f"🌱 Carbon footprint: {emissions:.10f} kg CO2")
        
        # STANDARDIZED RETURN FORMAT (matches XGBoost)
        return {
            "model": "Holt-Winters",
            "execution_carbon_kg": emissions,
            "data": df_forecast.reset_index().to_dict(orient="records")
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
    uvicorn.run(app, host="0.0.0.0", port=8002)