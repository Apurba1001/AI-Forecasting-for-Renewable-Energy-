import os
import requests
import pandas as pd
from src.production_phase.carbon_simulator import CarbonSimulator

class DistributedOrchestrator:
    def __init__(self):
        # 1. Initialize the Virtual Sensor Component
        self.sensor = CarbonSimulator()
        
        # 2. Service Discovery (Docker Network Names)

        # self.XGB_URL = "http://xgb_predict_service:8001/predict/"
        # self.HW_URL = "http://hw_predict_service:8002/predict/"
        
        # USE ENVIRONMENT VARIABLES (Best Practice)
        # If running locally, default to your Docker Compose names
        # If running in K8s, we will inject the K8s names
        self.XGB_URL = os.getenv("XGB_SERVICE_URL", "http://xgb_predict_service:8001/predict/")
        self.HW_URL = os.getenv("HW_SERVICE_URL", "http://hw_predict_service:8002/predict/")

    def _call_service(self, base_url, country_code, timeout=10):
        """Internal helper to handle network requests cleanly."""
        try:
            url = f"{base_url}{country_code}"
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Convert JSON back to DataFrame
            df = pd.DataFrame(response.json())
            if not df.empty:
                df['datetime_utc'] = pd.to_datetime(df['datetime_utc'])
                df.set_index('datetime_utc', inplace=True)
            return df
            
        except requests.exceptions.RequestException as e:
            # Re-raise to let the main logic decide on fallback
            raise ConnectionError(f"Service unreachable at {base_url}: {e}")

    def get_optimized_forecast(self, country_code, carbon_mode=None):
        """
        Main Orchestrator Logic:
        1. Check Carbon Sensor.
        2. Route traffic to the correct Microservice.
        """
        # Step 1: Read the Sensor
        carbon_data = self.sensor.get_current_carbon_intensity(force_mode=carbon_mode)
        intensity_status = carbon_data["status"]
        
        selected_model = ""
        df = None

        # Step 2: Route Traffic
        if intensity_status == "LOW":
            print(f"🌱 Grid Clean ({carbon_data['carbon_intensity']}g). Routing to XGBoost Container...")
            try:
                # Primary Choice: Heavy Model
                df = self._call_service(self.XGB_URL, country_code, timeout=15)
                selected_model = "XGBoost (Performance Mode)"
                
            except Exception as e:
                print(f"⚠️ XGB Service Error: {e}. Falling back to HW...")
                # Fallback Choice
                try:
                    df = self._call_service(self.HW_URL, country_code)
                    selected_model = "Holt-Winters (Auto-Fallback)"
                except Exception as fallback_err:
                    return None, {"error": f"ALL services failed: {fallback_err}"}

        else:
            print(f"☁️ Grid High Carbon ({carbon_data['carbon_intensity']}g). Routing to HW Container...")
            try:
                # Primary Choice: Eco Model
                df = self._call_service(self.HW_URL, country_code)
                selected_model = "Holt-Winters (Eco Mode)"
            except Exception as e:
                return None, {"error": f"Eco-service unavailable: {e}"}

        return df, {"selected_model": selected_model, "carbon_context": carbon_data}

# --- Example Usage (If running locally for test) ---
if __name__ == "__main__":
    orchestrator = DistributedOrchestrator()
    df, metadata = orchestrator.get_optimized_forecast("DE", carbon_mode="LOW")
    if df is not None:
        print(f"Success! Model used: {metadata['selected_model']}")