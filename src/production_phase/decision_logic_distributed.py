import os
import requests
import pandas as pd
from src.production_phase.carbon_simulator import CarbonSimulator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DistributedOrchestrator:
    def __init__(self):
        # 1. Initialize the Virtual Sensor Component
        self.sensor = CarbonSimulator()
        
        # 2. Service Discovery (Docker Network Names)
        # ✅ FIXED: Default to localhost for local development
        self.XGB_URL = os.getenv("XGB_SERVICE_URL", "http://xgb-service:8001")
        self.HW_URL  = os.getenv("HW_SERVICE_URL",  "http://hw-service:8002")

        
        logger.info(f"🔧 Orchestrator initialized")
        logger.info(f"   XGBoost Service: {self.XGB_URL}")
        logger.info(f"   Holt-Winters Service: {self.HW_URL}")

    def _call_service(self, base_url, country_code, timeout=10):
        """
        Internal helper to handle network requests cleanly.
        Returns: (DataFrame, emissions_kg)
        """
        try:
            url = f"{base_url}/predict/{country_code}"
            logger.info(f"📡 Calling service: {url}")
            
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            
            logger.info(f"✅ Service responded successfully")
            
            # Handle standardized response format
            if isinstance(payload, dict) and "data" in payload:
                # New standardized format
                data_rows = payload["data"]
                emissions = payload.get("execution_carbon_kg", 0.0)
                model_name = payload.get("model", "Unknown")
                logger.info(f"   Model: {model_name}")
                logger.info(f"   Emissions: {emissions:.10f} kg CO2")
            elif isinstance(payload, list):
                # Old format (raw list)
                data_rows = payload
                emissions = 0.0
                logger.warning("   ⚠️ Service returned old format (no emissions data)")
            else:
                raise ValueError(f"Unexpected response format: {type(payload)}")
            
            # Create DataFrame from data rows
            df = pd.DataFrame(data_rows)
            logger.info(f"   Created DataFrame: {df.shape}")
            
            if df.empty:
                logger.warning("   ⚠️ Empty DataFrame received from service")
                return None, 0.0
            
            # Handle datetime index
            if 'datetime_utc' in df.columns:
                df['datetime_utc'] = pd.to_datetime(df['datetime_utc'])
                df.set_index('datetime_utc', inplace=True)
                logger.info(f"   Set datetime index: {df.index.min()} to {df.index.max()}")
            else:
                logger.warning("   ⚠️ No datetime_utc column found")
                df.index = pd.to_datetime(df.index)
            
            logger.info(f"   DataFrame columns: {df.columns.tolist()}")
            
            return df, emissions
            
        except requests.exceptions.Timeout as e:
            logger.error(f"❌ Service timeout: {base_url}")
            raise ConnectionError(f"Service timeout at {base_url}: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Cannot connect to service: {base_url}")
            raise ConnectionError(f"Service unreachable at {base_url}: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP error from service: {e.response.status_code}")
            raise ConnectionError(f"Service error at {base_url}: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error calling service: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    # ✅ FIXED: This is the method your main.py is calling!
    def get_optimized_forecast(self, country_code, carbon_mode=None):
        """
        Main Orchestrator Logic:
        1. Check Carbon Sensor
        2. Route traffic to the correct Microservice
        3. Return forecast data with metadata
        
        Returns: (DataFrame, metadata_dict)
        """
        logger.info(f"🎯 Starting optimized forecast for {country_code}")
        logger.info(f"   Carbon mode override: {carbon_mode}")
        
        # Step 1: Read the Sensor
        carbon_data = self.sensor.get_current_carbon_intensity(force_mode=carbon_mode)
        intensity_status = carbon_data["status"]
        
        logger.info(f"🌍 Carbon intensity: {carbon_data['carbon_intensity']}g CO2/kWh")
        logger.info(f"   Status: {intensity_status}")
        
        selected_model = ""
        df = None
        execution_carbon = 0.0

        # Step 2: Route Traffic Based on Carbon Intensity
        if intensity_status == "LOW":
            logger.info("🌱 Grid is clean → Routing to XGBoost (High-Performance)")
            try:
                df, execution_carbon = self._call_service(self.XGB_URL, country_code, timeout=15)
                selected_model = "XGBoost (Performance Mode)"

            except Exception as xgb_err:
                logger.warning(f"⚠️ XGBoost failed: {xgb_err}")
                logger.info("🔄 Falling back to Holt-Winters...")

                try:
                    df, execution_carbon = self._call_service(self.HW_URL, country_code)
                    selected_model = "Holt-Winters (Auto-Fallback from XGBoost)"

                except Exception as hw_err:
                    logger.error("❌ Both services failed!")
                    return None, {
                        "error": "All services failed",
                        "xgb_error": str(xgb_err),
                        "hw_error": str(hw_err),
                        "carbon_context": carbon_data,
                    }

        else:  # HIGH carbon intensity
            logger.info("☁️ Grid has high carbon → Routing to Holt-Winters (Eco Mode)")
            try:
                df, execution_carbon = self._call_service(self.HW_URL, country_code)
                selected_model = "Holt-Winters (Eco Mode)"

            except Exception as hw_err:
                logger.warning(f"⚠️ Holt-Winters failed: {hw_err}")
                logger.info("🔄 Falling back to XGBoost...")

                try:
                    df, execution_carbon = self._call_service(self.XGB_URL, country_code, timeout=15)
                    selected_model = "XGBoost (Auto-Fallback from Holt-Winters)"

                except Exception as xgb_err:
                    logger.error("❌ Both services failed!")
                    return None, {
                        "error": "All services failed",
                        "hw_error": str(hw_err),
                        "xgb_error": str(xgb_err),
                        "carbon_context": carbon_data,
                    }
            
        # Step 3: Validate and Return
        if df is None or df.empty:
            logger.error("❌ Received empty forecast data")
            return None, {
                "error": "Empty forecast data",
                "selected_model": selected_model,
                "carbon_context": carbon_data
            }
        
        logger.info(f"✅ Forecast complete!")
        logger.info(f"   Model: {selected_model}")
        logger.info(f"   Records: {len(df)}")
        logger.info(f"   Execution carbon: {execution_carbon:.10f} kg CO2")
        
        metadata = {
            "selected_model": selected_model,
            "carbon_context": carbon_data,
            "execution_carbon_footprint_kg": execution_carbon,
            "forecast_records": len(df),
            "country_code": country_code
        }
        
        return df, metadata

# --- Example Usage ---
if __name__ == "__main__":
    orchestrator = DistributedOrchestrator()
    
    print("\n" + "="*60)
    print("Testing Orchestrator")
    print("="*60)
    
    # Test with LOW carbon mode (should use XGBoost)
    print("\n🧪 Test 1: LOW carbon mode (Germany)")
    df, metadata = orchestrator.get_optimized_forecast("DE", carbon_mode="LOW")
    
    if df is not None:
        print(f"\n✅ Success!")
        print(f"   Model: {metadata['selected_model']}")
        print(f"   Carbon footprint: {metadata['execution_carbon_footprint_kg']} kg")
        print(f"   Data shape: {df.shape}")
        print(f"\n📊 Sample data:")
        print(df.head())
    else:
        print(f"\n❌ Failed: {metadata.get('error', 'Unknown error')}")
    
    # Test with HIGH carbon mode (should use Holt-Winters)
    print("\n🧪 Test 2: HIGH carbon mode (Germany)")
    df, metadata = orchestrator.get_optimized_forecast("DE", carbon_mode="HIGH")
    
    if df is not None:
        print(f"\n✅ Success!")
        print(f"   Model: {metadata['selected_model']}")
        print(f"   Carbon footprint: {metadata['execution_carbon_footprint_kg']} kg")
        print(f"   Data shape: {df.shape}")
    else:
        print(f"\n❌ Failed: {metadata.get('error', 'Unknown error')}")