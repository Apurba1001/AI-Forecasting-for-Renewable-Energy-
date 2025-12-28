# config.py

import os
from pathlib import Path

# --- PATHS ---
# Since this file is now in the ROOT, the parent is the root itself.
PROJECT_ROOT = Path(__file__).resolve().parent

# --- GLOBAL SETTINGS ---
TARGET_COUNTRY = "AT"
TARGET_COLS = ["Solar", "Wind Onshore", "Wind Offshore"]

DATA_FILE = PROJECT_ROOT / "data" / "01_raw" / "generation_2024_raw.csv"

# --- 🔴 FIX IS HERE 🔴 ---
# Point to the specific subfolder where the .pkl files are.
# If your folder is named "holt_winters", change "lightweight" to "holt_winters".
MODEL_DIR = PROJECT_ROOT / "models" / "lightweight" 
MODEL_DIR_XGB = PROJECT_ROOT / "models"
CARBON_DIR = PROJECT_ROOT / "data" / "05_carbon"
OUTPUT_DIR = PROJECT_ROOT / "data" / "03_forecasts"

# Ensure directories exist
MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CARBON_DIR.mkdir(parents=True, exist_ok=True)