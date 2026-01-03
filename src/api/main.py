from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import traceback
import logging
import os

# ------------------------------------------------------------------
# Path + import hygiene
# ------------------------------------------------------------------

if 'src.production_phase.decision_logic_distributed' in sys.modules:
    del sys.modules['src.production_phase.decision_logic_distributed']

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.production_phase import decision_logic_distributed
logger.error("🔥 USING FILE: %s", decision_logic_distributed.__file__)

from src.production_phase.decision_logic_distributed import DistributedOrchestrator

# ------------------------------------------------------------------
# FastAPI setup
# ------------------------------------------------------------------

app = FastAPI(
    title="Renewable Energy Forecast API",
    description="API for optimized renewable energy forecasting using distributed models.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Orchestrator initialization (FAIL FAST)
# ------------------------------------------------------------------

orchestrator = DistributedOrchestrator()

if not hasattr(orchestrator, "get_optimized_forecast"):
    raise RuntimeError("Invalid DistributedOrchestrator loaded")

logger.info("✅ DistributedOrchestrator initialized successfully")

# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.get("/")
def home():
    return {"status": "API is running. Use /forecast/optimized/{country_code}"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "orchestrator": "running",
            "xgb_service": orchestrator.XGB_URL,
            "hw_service": orchestrator.HW_URL
        }
    }

@app.get("/forecast/optimized/{country_code}")
def get_smart_forecast(
    country_code: str,
    carbon_mode: Optional[str] = Query(
        None,
        description="Force carbon mode: 'HIGH' or 'LOW'"
    )
):
    logger.info(f"📡 Forecast request: country={country_code}, carbon_mode={carbon_mode}")

    # ------------------------------------------------------------------
    # Runtime execution (CHAOS SAFE)
    # ------------------------------------------------------------------

    try:
        df, metadata = orchestrator.get_optimized_forecast(
            country_code,
            carbon_mode=carbon_mode
        )

    # 🔁 Runtime dependency failure → graceful degradation
    except ConnectionError as e:
        logger.warning("🔁 Runtime dependency failure detected")
        return emergency_fallback(country_code, str(e))

    # ❌ Programmer / logic error → crash loudly (NO fallback)
    except Exception as e:
        logger.critical("🔥 INTERNAL API ERROR")
        logger.critical(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")

    # ------------------------------------------------------------------
    # Validate orchestrator response
    # ------------------------------------------------------------------

    #if metadata.get("error"):
        #return emergency_fallback(country_code, metadata["error"])
        
    df, metadata = orchestrator.get_optimized_forecast(
    country_code,
    carbon_mode=carbon_mode
)

    if df is None:
        return emergency_fallback(
            country_code,
            metadata.get("error", "Unknown failure")
        )

    if df is None or df.empty:
        return emergency_fallback(country_code, "Empty forecast from orchestrator")

    # ------------------------------------------------------------------
    # Success path
    # ------------------------------------------------------------------

    df_clean = df.reset_index()

    if "datetime_utc" in df_clean.columns:
        df_clean["datetime_utc"] = df_clean["datetime_utc"].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    forecast_list = df_clean.to_dict(orient="records")

    response_metadata = {
        "selected_model": metadata.get("selected_model", "Unknown"),
        "carbon_intensity": metadata.get("carbon_context", {}).get("carbon_intensity", 0),
        "carbon_status": metadata.get("carbon_context", {}).get("status", "UNKNOWN"),
        "execution_carbon_kg": metadata.get("execution_carbon_footprint_kg", 0.0),
        "forecast_records": len(forecast_list),
        "country_code": country_code.upper(),
        "timestamp": datetime.now().isoformat()
    }

    return {
        "metadata": response_metadata,
        "forecast": forecast_list
    }

# ------------------------------------------------------------------
# Emergency fallback (ONLY when both models are down)
# ------------------------------------------------------------------

def emergency_fallback(country_code: str, error_msg: str):
    logger.warning(f"🛡️ EMERGENCY FALLBACK for {country_code}: {error_msg}")

    # 🚫 Disable fallback entirely during chaos demo if desired
    if os.getenv("CHAOS_DEMO_MODE") == "true":
        raise HTTPException(
            status_code=503,
            detail="All forecast services unavailable"
        )

    base_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    static_forecast = []

    import math
    for i in range(24):
        t = base_time + timedelta(hours=i)
        solar = max(0, 100 * (1 - abs(12 - i) / 12)) if 6 <= i <= 18 else 0
        wind_on = 80 + 30 * math.sin(i * math.pi / 12)
        wind_off = 60 + 20 * math.sin((i + 6) * math.pi / 12)

        static_forecast.append({
            "datetime_utc": t.strftime("%Y-%m-%d %H:%M:%S"),
            "Solar": round(solar, 2),
            "Wind_Onshore": round(wind_on, 2),
            "Wind_Offshore": round(wind_off, 2),
            "Total_Generation": round(solar + wind_on + wind_off, 2),
        })

    return {
        "metadata": {
            "selected_model": "Emergency Static Fallback",
            "status": "degraded",
            "error": error_msg,
            "forecast_records": 24,
            "country_code": country_code.upper(),
            "timestamp": datetime.now().isoformat(),
        },
        "forecast": static_forecast,
    }

# ------------------------------------------------------------------
# POST endpoint
# ------------------------------------------------------------------

class ForecastRequest(BaseModel):
    country_code: str
    carbon_mode: Optional[str] = None

@app.post("/forecast")
def forecast_post(req: ForecastRequest):
    return get_smart_forecast(req.country_code, req.carbon_mode)

# ------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
