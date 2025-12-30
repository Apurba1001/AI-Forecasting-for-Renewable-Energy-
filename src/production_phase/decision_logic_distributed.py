import requests
import pandas as pd
import warnings
from src.production_phase.carbon_simulator import get_current_carbon_intensity

warnings.filterwarnings("ignore")

def get_optimized_forecast(country_code, carbon_mode=None):
    # 1. Get Carbon Context (Integrated Sensor)
    carbon_data = get_current_carbon_intensity(force_mode=carbon_mode)
    
    # 2. Network URLs (Docker Service Names from docker-compose)
    XGB_URL = f"http://xgb_predict_service:8001/predict/{country_code}"
    HW_URL = f"http://hw_predict_service:8002/predict/{country_code}"
    
    selected_model = ""
    df = None

    # 3. Decision & Routing Logic
    if carbon_data["status"] == "LOW":
        try:
            print(f"🌱 Grid Clean ({carbon_data['carbon_intensity']}g). Routing to XGBoost Container...")
            response = requests.get(XGB_URL, timeout=15) # Longer timeout for heavy XGB model
            response.raise_for_status()
            df = pd.DataFrame(response.json())
            selected_model = "XGBoost (Performance Mode)"
        except Exception as e:
            print(f"⚠️ XGB Service Error: {e}. Falling back to HW...")
            # Emergency Fallback to the other container
            response = requests.get(HW_URL, timeout=10)
            df = pd.DataFrame(response.json())
            selected_model = "Holt-Winters (Auto-Fallback)"
    else:
        print(f"☁️ Grid High Carbon ({carbon_data['carbon_intensity']}g). Routing to HW Container...")
        try:
            response = requests.get(HW_URL, timeout=10)
            response.raise_for_status()
            df = pd.DataFrame(response.json())
            selected_model = "Holt-Winters (Eco Mode)"
        except Exception as e:
            return None, {"error": f"Eco-service unavailable: {str(e)}"}

    # Convert JSON response back to a proper Time-Series DataFrame
    if df is not None:
        df['datetime_utc'] = pd.to_datetime(df['datetime_utc'])
        df.set_index('datetime_utc', inplace=True)
    
    return df, {"selected_model": selected_model, "carbon_context": carbon_data}