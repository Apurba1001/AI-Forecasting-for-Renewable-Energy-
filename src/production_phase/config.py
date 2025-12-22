# config.py

import os
from pathlib import Path

# --- GLOBAL SETTINGS ---
TARGET_COUNTRY = "AT"
TARGET_COLS = ["Solar", "Wind Onshore", "Wind Offshore"]

# --- PATHS ---
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "01_raw" / "generation_2024_raw.csv"

# --- 🔴 FIX IS HERE 🔴 ---
# Point to the specific subfolder where the .pkl files are.
# If your folder is named "holt_winters", change "lightweight" to "holt_winters".
MODEL_DIR = PROJECT_ROOT / "models" / "lightweight" 
MODEL_DIR_XGB = PROJECT_ROOT / "models"

OUTPUT_DIR = PROJECT_ROOT / "data" / "03_forecasts"

# Ensure directories exist
MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)