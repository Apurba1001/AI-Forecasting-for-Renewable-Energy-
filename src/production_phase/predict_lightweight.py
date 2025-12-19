import pandas as pd
import joblib
from pathlib import Path
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "models" / "lightweight"
OUTPUT_DIR = PROJECT_ROOT / "data" / "03_forecasts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------
# 🛠️ CHANGE THIS CODE TO PREDICT A DIFFERENT COUNTRY
TARGET_COUNTRY = "BE" 
# -----------------------------------------

AVAILABLE_TARGETS = ["Solar", "Wind_Onshore", "Wind_Offshore"]

def load_model(country, target):
    filename = f"hw_{country}_{target}.pkl"
    model_path = MODEL_DIR / filename
    if not model_path.exists():
        return None
    try:
        return joblib.load(model_path)
    except Exception as e:
        return None

def generate_forecast(country_code):
    """
    Generates a standard 24h profile (Midnight to Midnight) for the current date.
    """
    print(f"\n🔮 Generating Daily Forecast for {country_code}...")
    
    # Define "Today" from 00:00 to 23:00 UTC
    today_midnight = pd.Timestamp.now(tz="UTC").normalize()
    future_index = pd.date_range(start=today_midnight, periods=24, freq="h")
    
    forecasts = {}
    
    for target in AVAILABLE_TARGETS:
        model = load_model(country_code, target)
        if model is None:
            continue
            
        try:
            # Get the model's raw 24-hour pattern
            raw_values = model.forecast(24).values
            
            # Physics Check (No negative energy)
            raw_values[raw_values < 0] = 0
            
            # Map directly to 00:00 - 23:00
            forecast_series = pd.Series(data=raw_values, index=future_index)
            forecasts[target] = forecast_series
            
            print(f"   ✅ {target:<15} | Peak: {forecast_series.max():,.0f} MW")
            
        except Exception as e:
            print(f"   ❌ Failed to predict {target}: {e}")

    # Save
    if forecasts:
        result_df = pd.DataFrame(forecasts)
        result_df["Total_Generation"] = result_df.sum(axis=1)
        result_df.index.name = "datetime_utc"
        
        output_file = OUTPUT_DIR / f"forecast_{country_code}.csv"
        result_df.to_csv(output_file)
        print(f"   📄 Saved to: {output_file.name}")
    else:
        print(f"   ⚠️ No models found for {country_code}.")

if __name__ == "__main__":
    generate_forecast(TARGET_COUNTRY)