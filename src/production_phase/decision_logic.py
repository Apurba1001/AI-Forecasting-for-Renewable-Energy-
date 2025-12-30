import sys
from pathlib import Path

# Setup path to import from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# --- IMPORTS ---
from src.production_phase.carbon_simulator import get_current_carbon_intensity

# Import both prediction engines with clear aliases
from src.production_phase.predict_lightweight import generate_forecast as forecast_lightweight
from src.production_phase.predict_xgboost import generate_forecast as forecast_xgboost

def get_optimized_forecast(country_code, carbon_mode=None):
    """
    Decides which model to use based on Grid Carbon Intensity.
    
    Args:
        country_code (str): The ISO country code (e.g., "DE").
        carbon_mode (str, optional): Force "HIGH" or "LOW" for demo purposes.
        
    Returns:
        tuple: (DataFrame of forecast, Dictionary of decision metadata)
    """
    
    # 1. Check the Carbon "Weather"
    # (Passes the force_mode to the simulator to handle overrides)
    carbon_data = get_current_carbon_intensity(force_mode=carbon_mode)
    intensity_status = carbon_data['status']
    
    # Prepare metadata to explain the decision to the frontend
    decision_metadata = {
        "carbon_context": carbon_data,
        "selected_model": "",
        "reasoning": ""
    }

    # 2. The Decision Logic
    if intensity_status == "HIGH":
        print(f"\n⚠️  DECISION: High Carbon Grid detected ({carbon_data['carbon_intensity']} g).")
        print(f"    👉 Switching to ECO Model (Holt-Winters) to save compute.")
        
        # EXECUTE LIGHTWEIGHT MODEL
        try:
            forecast_df = forecast_lightweight(country_code)
            
            decision_metadata["selected_model"] = "Eco Model (Holt-Winters)"
            decision_metadata["reasoning"] = "Grid carbon is HIGH. Using low-energy model."
            
        except Exception as e:
            print(f"❌ Eco Model Failed: {e}")
            forecast_df = None

    else:
        print(f"\n✅ DECISION: Low Carbon Grid detected ({carbon_data['carbon_intensity']} g).")
        print(f"    👉 Switching to PERFORMANCE Model (XGBoost) for max accuracy.")
        
        # EXECUTE XGBOOST MODEL
        try:
            forecast_df = forecast_xgboost(country_code)
            
            decision_metadata["selected_model"] = "Performance Model (XGBoost)"
            decision_metadata["reasoning"] = "Grid carbon is LOW. Using high-accuracy model."
            
        except Exception as e:
            print(f"❌ Performance Model Failed: {e}")
            # Fallback to lightweight if XGBoost crashes
            print("    ⚠️ Fallback: Attempting Eco Model...")
            forecast_df = forecast_lightweight(country_code)
            decision_metadata["selected_model"] = "Eco Model (Fallback)"

    return forecast_df, decision_metadata

if __name__ == "__main__":
    # --- TEST RUN ---
    country_code = 'ES'
    print("--- TESTING DECISION LOGIC ---")
    
    # Test 1: Force High Carbon
    print("\n[TEST 1] Forcing HIGH Carbon:")
    df, meta = get_optimized_forecast(country_code, carbon_mode="HIGH")
    if df is not None:
        print(f"Result: Generated {len(df)} rows.")
        print(f"Metadata: {meta['selected_model']}")
        
    # Test 2: Force Low Carbon
    print("\n[TEST 2] Forcing LOW Carbon:")
    df, meta = get_optimized_forecast(country_code, carbon_mode="LOW")
    if df is not None:
        print(f"Result: Generated {len(df)} rows.")
        print(f"Metadata: {meta['selected_model']}")