import os
import time
import pandas as pd
from entsoe import EntsoePandasClient
from entsoe.exceptions import NoMatchingDataError
from dotenv import load_dotenv

# 1. Setup Environment
load_dotenv()  # Load API key from .env file
API_KEY = os.getenv("ENTSOE_API_KEY")
client = EntsoePandasClient(api_key=API_KEY)

if not API_KEY:
    raise ValueError("❌ API Key missing! Please set ENTSOE_API_KEY in your .env file.")

# 2. Configuration
START_DATE = pd.Timestamp("2024-01-01", tz="UTC")
END_DATE = pd.Timestamp("2024-01-02", tz="UTC")
OUTPUT_DIR = "data/01_raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "generation_2024_raw.csv")

# List of common European country codes (ISO-3166-1 alpha-2 / ENTSOE codes)
# Note: Some small regions are excluded to keep it robust.
# COUNTRIES = [
#     "AT", "BE", "BG", "CH", "CZ", "DE", "DK", "EE", "ES", "FI", 
#     "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "NL", 
#     "NO", "PL", "PT", "RO", "SE", "SI", "SK", "UK"
# ]
COUNTRIES = ["AT", "BE"]    #short list for testing

# We only want these specific generation types
TARGET_RENEWABLES = [
    'Solar',
    'Wind Onshore',
    'Wind Offshore'
]

all_data = []

def load_data():
    """
    Loops through country codes and loads data from entsoe for each of the listed country,
    concentenates into one single csv, and filter for wind/solar
    """
    print(f"Starting data ingestion from ENSTOE ({START_DATE} to {END_DATE})")
    for country in COUNTRIES:

        df = client.query_generation(country_code=country, start=START_DATE, end=END_DATE, psr_type=None)
        df.columns = df.columns.droplevel(1)
        all_data.append(df)
        time.sleep(5)
    
    final_df = pd.concat(all_data)
    final_df.to_csv("./data/01_raw/data_download_test.csv")
    print(final_df.head())
    return

if __name__=="__main__":
    load_data()