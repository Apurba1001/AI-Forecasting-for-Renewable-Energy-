from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path
from typing import Optional

# 1. Setup Path to import your scripts from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# 2. Import the decision logic
# --- CHANGE 1: Import the Class, not the function ---
from src.production_phase.decision_logic_distributed import DistributedOrchestrator

app = FastAPI(title="Renewable Energy Forecast API")

# 3. Allow React Frontend (localhost:3000) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all connections (simplest for dev)
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CHANGE 2: Instantiate the Orchestrator once ---
# This initializes the CarbonSimulator and sets up the Docker URLs
orchestrator = DistributedOrchestrator()

@app.get("/")
def home():
    return {"status": "API is running. Use /forecast/optimized/{country_code}"}

@app.get("/forecast/optimized/{country_code}")
def get_smart_forecast(
    country_code: str, 
    # This captures the optional ?carbon_mode=HIGH/LOW parameter
    carbon_mode: Optional[str] = Query(None, description="Force HIGH or LOW carbon simulation")
):
    """
    Smart Endpoint: Checks Carbon -> Picks Model -> Returns Forecast
    """
    print(f"📡 Request: {country_code} (Carbon Override: {carbon_mode})")

    # 1. Call your Decision Logic
    try:
        df, metadata = orchestrator.get_optimized_forecast(country_code, carbon_mode=carbon_mode)
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No forecast data available")
    
    # 2. Format Data for React (Convert DataFrame to JSON-friendly list)
    df_clean = df.reset_index()
    # Convert timestamps to strings
    df_clean["datetime_utc"] = df_clean["datetime_utc"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    forecast_list = df_clean.to_dict(orient="records")
    
    # 3. Return the full package
    return {
        "metadata": metadata,  # React uses this to show the "Eco Mode" badge
        "forecast": forecast_list
    }

# To run: uvicorn src.api.main:app --reload