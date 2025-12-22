import pandas as pd
import joblib
from pathlib import Path
import warnings
from config import TARGET_COUNTRY, TARGET_COLS, MODEL_DIR, OUTPUT_DIR

# Suppress warnings
warnings.filterwarnings("ignore")

def load_model(country, target):
    # 1. FIX: Convert "Wind Onshore" -> "Wind_Onshore" for filename lookup
    clean_target = target.replace(' ', '_')
    
    filename = f"hw_{country}_{clean_target}.pkl"
    model_path = MODEL_DIR / filename
    
    if not model_path.exists():
        # Debug print to help you verify path is correct
        # print(f"Checking for model at: {model_path} -> Not Found")
        return None
    try:
        return joblib.load(model_path)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
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
    
    for target in TARGET_COLS:
        # Load model using the helper (which now handles spaces correctly)
        model = load_model(country_code, target)
        
        if model is None:
            continue
            
        # 2. FIX: Create clean name for Output CSV Header
        clean_target = target.replace(' ', '_')
            
        try:
            # Get the model's raw 24-hour pattern
            raw_values = model.forecast(24).values
            
            # Physics Check (No negative energy)
            raw_values[raw_values < 0] = 0
            
            # Map directly to 00:00 - 23:00
            forecast_series = pd.Series(data=raw_values, index=future_index)
            
            # Store using the clean name (e.g., "Wind_Onshore")
            forecasts[clean_target] = forecast_series
            
            print(f"   ✅ {clean_target:<15} | Peak: {forecast_series.max():,.0f} MW")
            
        except Exception as e:
            print(f"   ❌ Failed to predict {target}: {e}")

    # Save
    if forecasts:
        result_df = pd.DataFrame(forecasts)
        
        # Add Total Generation (Standard for your dashboard)
        result_df["Total_Generation"] = result_df.sum(axis=1)
        
        result_df.index.name = "datetime_utc"
        
        output_file = OUTPUT_DIR / f"forecast_{country_code}.csv"
        result_df.to_csv(output_file)
        print(f"   📄 Saved to: {output_file.name}")
    else:
        print(f"   ⚠️ No models found for {country_code}. Check 'models/lightweight' folder.")

if __name__ == "__main__":
    generate_forecast(TARGET_COUNTRY)