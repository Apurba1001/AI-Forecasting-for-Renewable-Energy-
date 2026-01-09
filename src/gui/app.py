"""
Renewable Energy Forecast System - Production GUI
Integrates with existing trained models and prediction modules
MINIMAL CHANGES VERSION - Only fixes API integration
"""

import json
import os
import sys
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# Configure paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
FORECASTS_DIR = DATA_DIR / "03_forecasts"
METRICS_DIR = DATA_DIR / "04_metrics"
CARBON_DIR = DATA_DIR / "05_carbon"

# Page configuration
st.set_page_config(
    page_title="Renewable Energy Forecast System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Custom CSS - Modern, Professional Design (UNCHANGED)
st.markdown(
    """
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Main App Background */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
    }
    
    /* Header Styling */
    h1 {
        color: #1e293b;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: #334155;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-left: 4px solid #3b82f6;
        padding-left: 1rem;
    }
    
    h3 {
        color: #475569;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    .subtitle {
        color: #64748b;
        font-size: 15px;
        margin-top: -8px;
        margin-bottom: 32px;
        font-weight: 400;
    }
    
        /* ============================
    LIVE SYSTEM MONITOR (SIDEBAR)
    ============================ */

    [data-testid="stSidebar"] .live-monitor-container {
        background: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 14px !important;
        margin-bottom: 1rem !important;
    }

    [data-testid="stSidebar"] .intensity-card {
        border-radius: 10px !important;
        padding: 12px !important;
        color: white !important;
        margin-bottom: 12px !important;
    }

    [data-testid="stSidebar"] .intensity-label {
        font-size: 0.75rem !important;
        opacity: 0.85 !important;
        margin-bottom: 4px !important;
    }

    [data-testid="stSidebar"] .intensity-value {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
    }

    [data-testid="stSidebar"] .status-grid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 8px !important;
    }

    [data-testid="stSidebar"] .status-box {
        background: #020617 !important;
        border-radius: 8px !important;
        padding: 6px !important;
        text-align: center !important;
    }

    [data-testid="stSidebar"] .status-tag {
        margin-top: 4px !important;
        padding: 3px 6px !important;
        border-radius: 999px !important;
        font-size: 0.7rem !important;
        font-weight: 700 !important;
        color: white !important;
    }
    
    /* Metric Cards Enhancement */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748b;
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    div[data-testid="stMetric"] {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 
                    0 2px 4px -1px rgba(0, 0, 0, 0.03);
        min-height: 140px;
        border: 1px solid rgba(226, 232, 240, 0.8);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 
                    0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: #3b82f6;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
        border-right: 1px solid #374151;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #e5e7eb;
        font-size: 1.25rem;
        font-weight: 700;
        padding: 0.5rem 0;
        border-left: none;
    }
    
    /* Sidebar Label Styling */
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stDateInput label,
    [data-testid="stSidebar"] .stTimeInput label {
        color: #cbd5f5;
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    /* Sidebar Subheader Emoji Fix */
    [data-testid="stSidebar"] h3 {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Model Cards */
    .model-card {
        padding: 1.25rem;
        border-radius: 10px;
        margin: 0.75rem 0;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        position: relative;
        overflow: hidden;
    }
    
    .model-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, transparent, currentColor, transparent);
        opacity: 0.5;
    }
    
    .eco-model {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-color: #10b981;
        color: #065f46;
    }
    
    .eco-model::before {
        color: #10b981;
    }
    
    .eco-model:hover {
        box-shadow: 0 10px 20px rgba(16, 185, 129, 0.2);
        transform: scale(1.02);
    }
    
    .performance-model {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-color: #ef4444;
        color: #7f1d1d;
    }
    
    .performance-model::before {
        color: #ef4444;
    }
    
    .performance-model:hover {
        box-shadow: 0 10px 20px rgba(239, 68, 68, 0.2);
        transform: scale(1.02);
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.625rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
        text-transform: none;
        letter-spacing: 0.3px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Download Button Special Styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.4);
    }
    
    /* Input Fields */
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
        background-color: #1f2937;
        color: white;
        font-weight: 500;
    }
    
    .stSelectbox > div > div:hover,
    .stTextInput > div > div > input:hover,
    .stDateInput > div > div > input:hover,
    .stTimeInput > div > div > input:hover {
        border-color: #3b82f6;
    }
    
    .stSelectbox > div > div:focus-within,
    .stTextInput > div > div > input:focus,
    .stDateInput > div > div > input:focus,
    .stTimeInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Date and Time input labels */
    .stDateInput label,
    .stTimeInput label {
        color: #cbd5f5;
        font-weight: 500;
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
    }
    
    /* Radio Buttons */
    .stRadio > div {
        gap: 0.75rem;
    }
    
    .stRadio > div > label {
        display: flex !important;
        align-items: center;
        background-color: #1f2937;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        transition: all 0.3s ease;
        cursor: pointer;
        margin-bottom: 0.5rem;
    }
    
    .stRadio > div > label:hover {
        border-color: #3b82f6;
        background-color: #1f2937;
    }
    
    .stRadio > div > label[data-baseweb="radio"] > div:first-child {
        margin-right: 0.75rem;
    }
    
    /* Selected radio button */
    .stRadio > div > label > div[data-testid="stMarkdownContainer"] {
        color: #334155;
        font-weight: 500;
    }
    
    /* Make radio text visible */
    .stRadio label {
        color: #cbd5f5!important;
    }
    
    /* Radio button circle styling */
    .stRadio > div > label > div:first-child {
        background-color: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    }
    
    /* Dataframe Styling */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    [data-testid="stDataFrame"] table {
        font-size: 0.9rem;
    }
    
    [data-testid="stDataFrame"] thead tr th {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
        color: white !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
        padding: 1rem !important;
    }
    
    [data-testid="stDataFrame"] tbody tr:hover {
        background-color: #f8fafc !important;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #cbd5e1, transparent);
    }
    
    /* Info/Warning/Success Boxes */
    .stAlert {
        border-radius: 10px;
        border-left-width: 4px;
        padding: 1rem 1.25rem;
        font-size: 0.95rem;
    }
    
    [data-baseweb="notification"] {
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Info Box */
    .stAlert[data-baseweb="notification"][kind="info"] {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-left-color: #3b82f6;
    }
    
    /* Success Box */
    .stAlert[data-baseweb="notification"][kind="success"] {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left-color: #10b981;
    }
    
    /* Warning Box */
    .stAlert[data-baseweb="notification"][kind="warning"] {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left-color: #f59e0b;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        font-weight: 600;
        color: #334155;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #f8fafc;
        border-color: #3b82f6;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #3b82f6 !important;
    }
    
    /* Plotly Chart Container */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
    }
    
    /* Footer */
    .css-footer {
        color: #94a3b8;
        font-size: 0.875rem;
        text-align: center;
        padding: 1rem 0;
        border-top: 1px solid #e2e8f0;
        margin-top: 2rem;
    }
    
    /* Tooltips */
    [data-testid="stTooltipIcon"] {
        color: #64748b;
        transition: color 0.3s ease;
    }
    
    [data-testid="stTooltipIcon"]:hover {
        color: #3b82f6;
    }
    
    /* Loading State */
    .stProgress > div > div {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #3b82f6);
        background-size: 200% 100%;
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    /* Card Hover Effects */
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    /* Smooth Transitions */
    * {
        transition: background-color 0.3s ease, border-color 0.3s ease;
    }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        h1 {
            font-size: 1.75rem;
        }
        
        div[data-testid="stMetric"] {
            padding: 1rem;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
    }
    
    </style>
    """,
    unsafe_allow_html=True,
)


# Cache functions for performance
@st.cache_data
def load_countries():
    """Load available countries from data"""
    try:
        # Try to load from processed data
        processed_dir = DATA_DIR / "02_processed"
        if processed_dir.exists():
            files = list(processed_dir.glob("*.csv"))
            if files:
                df = pd.read_csv(files[0], nrows=1)
                if "country" in df.columns:
                    countries = pd.read_csv(files[0])["country"].unique().tolist()
                    return sorted(countries)
    except Exception as e:
        st.sidebar.error(f"Error loading countries: {e}")

    # Default fallback
    return [
        "Germany",
        "France",
        "Spain",
        "Italy",
        "Poland",
        "Netherlands",
        "Belgium",
        "Austria",
        "Denmark",
        "Sweden",
        "Bulgaria",
        "Switzerland",
        "Czech Republic",
        "Estonia",
        "Finland",
        "Greece",
        "Croatia",
        "Hungary",
        "Ireland",
        "Lithuania",
        "Luxembourg",
        "Latvia",
        "Norway",
        "Portugal",
        "Romania",
        "Slovenia",
        "Slovakia",
        "United Kingdom",
    ]


@st.cache_data
def load_energy_types():
    """Load available energy types - Only Solar, Wind Onshore, Wind Offshore"""
    return ["Wind Onshore", "Wind Offshore", "Solar"]


@st.cache_data
def load_metrics():
    """Load model performance metrics"""
    try:
        metric_files = list(METRICS_DIR.glob("*.csv"))
        if metric_files:
            latest_metrics = max(metric_files, key=lambda x: x.stat().st_mtime)
            return pd.read_csv(latest_metrics)

        # Also try JSON format
        json_files = list(METRICS_DIR.glob("*.json"))
        if json_files:
            latest_json = max(json_files, key=lambda x: x.stat().st_mtime)
            with open(latest_json, "r") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading metrics: {e}")

    return None


API_URL = os.getenv("API_URL", "http://localhost:8000")


def get_system_status(carbon_mode=None):
    status = {"ORCH": "DOWN", "XGB": "DOWN", "HW": "DOWN", "intensity": 0.0}

    ORCH_URL = "http://orchestrator:8000"
    XGB_URL = os.getenv("XGB_SERVICE_URL", "http://xgb_service:8001")
    HW_URL = os.getenv("HW_SERVICE_URL", "http://hw_service:8002")

    # ---- Carbon live (independent) ----
    try:
        params = {"carbon_mode": carbon_mode} if carbon_mode else {}
        carbon_resp = requests.get(f"{ORCH_URL}/carbon-live", params=params, timeout=0.5).json()
        status["intensity"] = carbon_resp.get("carbon_intensity", 0.0)
        status["status"] = carbon_resp.get("status")
    except Exception as e:
        print("Carbon live error:", e)

    # ---- Orchestrator health ----
    try:
        orch_health = requests.get(f"{ORCH_URL}/health", timeout=3).json()
        if orch_health.get("status") == "healthy":
            status["ORCH"] = "UP"
    except Exception as e:
        print("Orchestrator health error:", e)

    # ---- XGB health ----
    try:
        xgb_health = requests.get(f"{XGB_URL}/health", timeout=5).json()
        if xgb_health.get("status") == "healthy":
            status["XGB"] = "UP"
    except Exception as e:
        print("XGB health error:", e)

    # ---- HW health ----
    try:
        hw_health = requests.get(f"{HW_URL}/health", timeout=3).json()
        if hw_health.get("status") == "healthy":
            status["HW"] = "UP"
    except Exception as e:
        print("HW health error:", e)

    return status


def draw_live_monitor():
    # A. Get user intent from the sidebar radio key
    user_choice = st.session_state.get("sim_selector", "Automatic")
    
    # B. Map UI text to backend-friendly strings
    api_mode = None
    if "LOW" in user_choice: api_mode = "LOW"
    elif "HIGH" in user_choice: api_mode = "HIGH"

    # C. Fetch the data using the shared mode
    sys_status = get_system_status(carbon_mode=api_mode)

    # Determine Status Color & Label
    intensity = sys_status["intensity"]
    status_label = sys_status.get("status", "Unknown")
    
    # Dynamic Gradient based on Carbon Status
    if status_label == "HIGH":
        bg_gradient = "linear-gradient(135deg, #991b1b 0%, #dc2626 100%)" # Red
        text_color = "#fecaca"
    elif status_label == "LOW":
        bg_gradient = "linear-gradient(135deg, #065f46 0%, #10b981 100%)" # Green
        text_color = "#d1fae5"
    else:
        bg_gradient = "linear-gradient(135deg, #374151 0%, #1f2937 100%)" # Gray
        text_color = "#9ca3af"

    def get_tag_style(state):
        bg = "#059669" if state == "UP" else "#dc2626"
        return f"background: {bg}; color: white; margin-top: 4px; padding: 2px 8px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; display: inline-block;"

    # E. Render the HTML
    st.html(f"""
    <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid #334155; border-radius: 12px; padding: 14px; margin-bottom: 1rem; font-family: sans-serif;">
        <div style="display: flex; align-items: center; margin-bottom: 12px; color: white;">
            <strong style="font-size: 1rem;">📡 Live System Monitor</strong>
        </div>

        <div style="background: {bg_gradient}; border-radius: 10px; padding: 15px; color: white; margin-bottom: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.9;">Grid Carbon Intensity</div>
            <div style="font-size: 1.8rem; font-weight: 800; margin: 4px 0;">
                {intensity:.1f} <span style="font-size: 1rem; font-weight: 400;">g/kWh</span>
            </div>
            <div style="font-weight: 700; font-size: 0.8rem; display: flex; align-items: center; gap: 5px;">
                <span style="width: 8px; height: 8px; background: white; border-radius: 50%; display: inline-block;"></span>
                STATUS: {status_label}
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
            <div style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 8px; text-align: center;">
                <div style="font-size: 0.65rem; color: #94a3b8; font-weight: 600;">ORCH</div>
                <div style="{get_tag_style(sys_status['ORCH'])}">{sys_status['ORCH']}</div>
            </div>
            <div style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 8px; text-align: center;">
                <div style="font-size: 0.65rem; color: #94a3b8; font-weight: 600;">XGB</div>
                <div style="{get_tag_style(sys_status['XGB'])}">{sys_status['XGB']}</div>
            </div>
            <div style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 8px; text-align: center;">
                <div style="font-size: 0.65rem; color: #94a3b8; font-weight: 600;">HW</div>
                <div style="{get_tag_style(sys_status['HW'])}">{sys_status['HW']}</div>
            </div>
        </div>
    </div>
    """)


def generate_forecast(
    country, energy_source, model_type, forecast_date, forecast_time, interval_hours
):
    """
    ✅ FIXED: Generates forecast by calling FastAPI backend
    Now properly handles standardized response format and carbon emissions
    """
    from datetime import datetime, timedelta

    import pandas as pd
    import requests

    country_code_map = {
        "Austria": "AT",
        "Belgium": "BE",
        "Bulgaria": "BG",
        "Croatia": "HR",
        "Czech Republic": "CZ",
        "Denmark": "DK",
        "Estonia": "EE",
        "Finland": "FI",
        "France": "FR",
        "Germany": "DE",
        "Greece": "GR",
        "Hungary": "HU",
        "Ireland": "IE",
        "Italy": "IT",
        "Latvia": "LV",
        "Lithuania": "LT",
        "Luxembourg": "LU",
        "Netherlands": "NL",
        "Norway": "NO",
        "Poland": "PL",
        "Portugal": "PT",
        "Romania": "RO",
        "Slovakia": "SK",
        "Slovenia": "SI",
        "Spain": "ES",
        "Sweden": "SE",
        "Switzerland": "CH",
        "United Kingdom": "UK",
    }

    country_code = country_code_map.get(country, "DE")

    # Map GUI selection to API carbon mode

    params = {}
    if model_type == "LOW":
        params["carbon_mode"] = "LOW"
    elif model_type == "HIGH":
        params["carbon_mode"] = "HIGH"

    # ✅ FIXED: Better error handling
    try:
        response = requests.get(
            f"{API_URL}/forecast/optimized/{country_code}", params=params, timeout=60
        )
        #response.raise_for_status()
        payload = response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Orchestrator Offline: Unable to reach the forecasting service.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API Error: {e}")
        return None

    # ✅ FIXED: Extract metadata and forecast data from standardized response
    metadata = payload.get("metadata", {})
    forecast_data = payload.get("forecast", [])

    # ✅ NEW: Check what model was actually used
    selected_model = metadata.get("selected_model", "Unknown")
            
    
    if not forecast_data or "Emergency" in selected_model:
        # We return a dummy structure so the app doesn't crash, 
        # but our error messages above will have already triggered.
        return {
            "times": [datetime.now()],
            "predicted": [0.0],
            "upper_bound": [0.0],
            "lower_bound": [0.0],
            "model_type": model_type,
            "selected_model": "Emergency",
            "carbon_emissions_kg": 0.0,
            "full_forecast_df": pd.DataFrame()
        }

    # ✅ FIXED: Build DataFrame from forecast
    df = pd.DataFrame(forecast_data)
    # Check for common column names for the timestamp
    potential_date_cols = ["datetime_utc", "index", "timestamp"]
    actual_date_col = next((c for c in potential_date_cols if c in df.columns), None)
    if actual_date_col:
        df[actual_date_col] = pd.to_datetime(df[actual_date_col])
        if actual_date_col != "datetime_utc":
            df.drop(columns=[actual_date_col], inplace=True, errors="ignore")
    else:
        try:
            df.index = pd.to_datetime(df.index)
            df["datetime_utc"] = df.index
        except:
            raise KeyError(f"Could not find time column. Available columns: {df.columns.tolist()}")
        
    df.set_index("datetime_utc", inplace=True)
    df.sort_index(inplace=True)

    # ✅ FIXED: Get carbon emissions from metadata
    carbon_emissions_kg = metadata.get("execution_carbon_kg", 0.0)

    # Log for debugging
    print(f"📊 Received forecast: {len(df)} records")
    print(f"🌱 Carbon emissions: {carbon_emissions_kg} kg")
    print(f"🤖 Model used: {selected_model}")
    print(f"📋 Columns: {df.columns.tolist()}")

    # --- Select values safely ---
    energy_col_map = {
        "Wind Onshore": "Wind_Onshore",
        "Wind Offshore": "Wind_Offshore",
        "Solar": "Solar",
    }

    col = energy_col_map.get(energy_source)

    if col and col in df.columns:
        values = df[col].astype(float).values
    elif "predicted_generation_mw" in df.columns:
        values = df["predicted_generation_mw"].astype(float).values
    elif "Total_Generation" in df.columns:
        values = df["Total_Generation"].astype(float).values
    else:
        raise ValueError(
            f"No usable forecast column found. Available: {df.columns.tolist()}"
        )

    # --- DEFINE predicted EXACTLY ONCE ---
    start_dt = datetime.combine(forecast_date, forecast_time)

    if interval_hours == 24:
        times = [start_dt]
        predicted = [float(values.mean())]
    else:
        step = interval_hours
        indices = range(0, len(values), step)
        times = [start_dt + timedelta(hours=i) for i in indices]
        predicted = [float(values[i]) for i in indices]

    # --- Confidence bounds (SAFE) ---
    margin = 0.15 if model_type == "Low Cost" else 0.10
    upper_bound = [p * (1 + margin) for p in predicted]
    lower_bound = [p * (1 - margin) for p in predicted]

    # ✅ FIXED: Return carbon emissions and metadata
    return {
        "times": times,
        "predicted": predicted,
        "upper_bound": upper_bound,
        "lower_bound": lower_bound,
        "confidence": ["High"] * len(times),
        "full_forecast_df": df,
        "model_type": model_type,
        "carbon_emissions_kg": carbon_emissions_kg,  # ✅ NEW
        "selected_model": selected_model,  # ✅ NEW
        "metadata": metadata,  # ✅ NEW
    }


# Title and subtitle
st.title("⚡ Renewable Energy Forecast System")
st.markdown(
    '<p class="subtitle">Multi-source forecasting for 28 European countries</p>',
    unsafe_allow_html=True,
)

# Sidebar configuration
with st.sidebar:
    @st.fragment(run_every=15)
    def auto_refresh_monitor():
        # This function pulls from st.session_state.sim_selector automatically
        draw_live_monitor()
    
    auto_refresh_monitor()
    st.header("🔧 Forecast Configuration")

    # Load available options
    countries = load_countries()

    # Section 1: Location & Energy Source
    st.subheader("📍 Location & Source")

    # Country selection
    country = st.selectbox(
        "Country",
        countries,
        index=0 if "Germany" in countries else 0,
        help="Select the country for energy forecast",
    )

    st.divider()


    # Energy source selection - Only Solar, Wind Onshore, Wind Offshore
    energy_source = st.selectbox(
        "Energy Source",
        ["Wind Onshore", "Wind Offshore", "Solar"],
        index=0,
        help="Select the renewable energy source type",
    )

    st.divider()

    # Section 2: Date & Time
    st.subheader("📅 Date & Time")

    # Date selection
    forecast_date = st.date_input(
        "Forecast Date",
        value=datetime.now().date(),
        min_value=date(2025, 12, 30),
        max_value=date(2026, 12, 31),
        help="Select the date for forecast",
    )

    # Time selection
    forecast_time = st.time_input(
        "Forecast Time",
        value=datetime.now().replace(minute=0, second=0, microsecond=0).time(),
        step=3600,  # 3600 seconds = 1 hour
        help="Select the starting time for forecast",
    )

    st.divider()

    # Section 3: Forecast Interval
    st.subheader("⏱️ Forecast Interval")

    # Interval selection with better styling
    interval_options = {
        "1h": "1 Hour",
        "3h": "3 Hours",
        "6h": "6 Hours",
        "12h": "12 Hours",
        "24h": "24 Hours (Full Day)",
    }

    forecast_interval = st.radio(
        "Select Time Interval",
        options=list(interval_options.keys()),
        format_func=lambda x: interval_options[x],
        index=4,  # Default to 24h
        help="Choose how often you want forecast data points",
    )

    # Convert interval to hours
    interval_hours = int(forecast_interval.replace("h", ""))

    st.divider()

    # Section 4: Model Selection
    st.subheader("⚡ Grid Carbon Intensity")

    # Model type selection with better labels
    model_options = {
        "Automatic": "🤖 Automatic (Real-time)",
        "Low Cost": "🌱 Low  (Eco-Friendly)",
        "High Cost": "⚡ High  (Dirty Grid)",
    }

    model_type_selection = st.radio(
        "Carbon Mode",
        options=list(model_options.keys()),
        format_func=lambda x: model_options[x],
        index=0,
        key="sim_selector",
        help="Automatic: System decides based on live grid carbon intensity\nLow: Grid is clean \nHigh: Grid is dirty",
    )
        
        
    # ✅ FIX: Check actual_model instead of model_type
    if model_type_selection == "Low Cost":
        api_param = "LOW"
    elif model_type_selection == "High Cost":
        api_param = "HIGH"
    else:
        api_param = None

    st.divider()

    # Action buttons
    st.subheader("🚀 Actions")

    run_forecast = st.button(
        "🔄 Run Forecast", use_container_width=True, type="primary"
    )

    st.divider()

    # Summary of selected parameters
    with st.expander("📋 Selected Parameters", expanded=False):
        st.write(f"**Country:** {country}")
        st.write(f"**Energy Source:** {energy_source}")
        st.write(f"**Date:** {forecast_date.strftime('%Y-%m-%d')}")
        st.write(f"**Time:** {forecast_time.strftime('%H:%M')}")
        st.write(f"**Interval:** {forecast_interval}")
        # Optional: show the actual model if forecast has run
        if "forecast_data" in st.session_state:
            actual = st.session_state["forecast_data"].get("selected_model")
            st.write(f"**Actual Model Used:** {actual}")

# Main content
if run_forecast:
    with st.spinner(f"Running forecast for {country} - {energy_source}..."):
        # Generate forecast using YOUR existing prediction modules
        forecast_data = generate_forecast(
            country=country,
            energy_source=energy_source,
            model_type=api_param,
            forecast_date=forecast_date,
            forecast_time=forecast_time,
            interval_hours=interval_hours,
        )

        if forecast_data:
            # This 'model_type' is used by Col5 and your chart logic
            st.session_state["model_type"] = forecast_data["model_type"]
            # This is used for the Metric Label in Col3
            st.session_state["actual_model_used"] = forecast_data["selected_model"]
            st.session_state["forecast_data"] = forecast_data
            st.session_state["current_country"] = country
            st.session_state["current_energy"] = energy_source
            st.session_state["forecast_date"] = forecast_date
            st.session_state["forecast_time"] = forecast_time
            st.session_state["interval"] = forecast_interval
            st.success("✅ Forecast completed successfully!")

# Display forecast if available
if "forecast_data" in st.session_state:
    forecast_data = st.session_state["forecast_data"]

    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        full_df = forecast_data.get("full_forecast_df")
        energy_col_map = {
            "Wind Onshore": "Wind_Onshore",
            "Wind Offshore": "Wind_Offshore",
            "Solar": "Solar",
        }
        
        target_col = energy_col_map.get(st.session_state.get("current_energy"))
        selected_hour = st.session_state.get("forecast_time").hour

        # ---- SAFE series selection (NO KeyErrors) ----
        if full_df is not None and target_col in full_df.columns:
            series = full_df[target_col].astype(float).values
        elif full_df is not None and "predicted_generation_mw" in full_df.columns:
            series = full_df["predicted_generation_mw"].astype(float).values
        else:
            series = forecast_data["predicted"]

        # ✅ FIX: Bounds checking for selected_hour
        if selected_hour < len(series):
            current_output = series[selected_hour]
        else:
            # Fallback: use first available value or mean
            current_output = series[0] if len(series) > 0 else np.mean(forecast_data["predicted"])

        # ---- Delta calculation (safe) ----
        if selected_hour + 1 < len(series):
            delta_value = current_output - series[selected_hour - 1]
            delta_str = f"{delta_value:.0f} MW"
        else:
            delta_str = None

        st.metric(
            label=f"Output at {st.session_state.get('forecast_time').strftime('%H:%M')}",
            value=f"{current_output:.0f} MW",
            delta=delta_str,
        )
       

    with col2:
        peak_forecast = max(forecast_data["predicted"])
        peak_index = forecast_data["predicted"].index(peak_forecast)
        peak_time = forecast_data["times"][peak_index]
        interval = st.session_state.get("interval", "24h")
        st.metric(
            label=f"Peak Forecast ({interval})",
            value=f"{peak_forecast:.0f} MW",
            delta=f"at {peak_time.strftime('%H:%M') if hasattr(peak_time, 'strftime') else 'N/A'}",
        )
        
    with col3:
        # Get the actual model that was used from metadata
        selected_model = forecast_data.get("selected_model", "Unknown")
        
        # --- FIX 1: Remove "High Accuracy" text ---
        if "XGBoost" in selected_model:
            model_name, icon, m_desc = "XGBoost", "⚡", "Performance"
            delta_color = "inverse"
        elif "Holt-Winters" in selected_model:
            model_name, icon, m_desc = "Holt-Winters", "🌱", "Eco-Friendly"
            delta_color = "normal"
        else:
            model_name, icon, m_desc = "Emergency", "🚨", "Offline"
            delta_color = "off"
        
        # --- FIX 3: Fix the Emergency Label Logic ---
        if "Fallback" in selected_model:
            m_desc = "⚠️ Fallback"
            delta_color = "off"
        elif "Emergency" in selected_model:
            m_desc = "🔴 Emergency"
            delta_color = "inverse"
        # If neither Fallback nor Emergency, it keeps the 'm_desc' from above
        
        st.metric(
            label="🤖 Model Used",
            value=f"{icon} {model_name}",
            delta=m_desc,
            delta_color=delta_color
        )
        
    with col4:
        avg_output = np.mean(forecast_data["predicted"])
        st.metric(
            label="Average Output",
            value=f"{avg_output:.0f} MW",
            delta=f"{(avg_output - current_output):.0f} MW",
        )
        
    with col5:
        # ✅ FIXED: Carbon Emissions Display - Always in kg CO₂eq
        carbon_emissions = forecast_data.get("carbon_emissions_kg", 0.0)

        # Color based on model type
        if st.session_state.get("model_type") == "LOW":
            delta_color = "normal"  # Green
            comparison = "Eco Mode"
        else:
            delta_color = "inverse"  # Red
            comparison = "Performance Mode"

        st.metric(
            label="🌍 Carbon Footprint",
            value=f"{carbon_emissions:.6f} kg CO₂eq",
            delta=comparison,
            delta_color=delta_color,
            help=f"Total emissions from model inference"
        )

    st.divider()

    # Forecast chart
    st.subheader("📊 Forecast Visualization")

    # Add forecast details
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Country:** {st.session_state.get('current_country', 'N/A')}")
    with col2:
        st.info(f"**Energy Source:** {st.session_state.get('current_energy', 'N/A')}")
    with col3:
        st.info(f"**Interval:** {st.session_state.get('interval', 'N/A')}")

    # Get data
    times = forecast_data["times"]
    predicted = forecast_data["predicted"]
    upper_bound = forecast_data["upper_bound"]
    lower_bound = forecast_data["lower_bound"]
    interval = st.session_state.get("interval", "24h")
    interval_hours = int(interval.replace("h", ""))

    # Get full forecast for proper windowing
    full_forecast_df = forecast_data.get("full_forecast_df")
    start_hour = st.session_state.get("forecast_time").hour
    start_datetime = datetime.combine(
        st.session_state.get("forecast_date"), st.session_state.get("forecast_time")
    )

    # Prepare data based on interval
    start_hour = st.session_state.get("forecast_time").hour
    start_datetime = datetime.combine(
        st.session_state.get("forecast_date"), st.session_state.get("forecast_time")
    )

    # Get full forecast for proper data
    full_forecast_df = forecast_data.get("full_forecast_df")

    if full_forecast_df is not None:
        energy_col_map = {
            "Wind Onshore": "Wind_Onshore",
            "Wind Offshore": "Wind_Offshore",
            "Solar": "Solar",
        }
        target_col = energy_col_map.get(st.session_state.get("current_energy"))

        if target_col and target_col in full_forecast_df.columns:
            full_predicted = full_forecast_df[target_col].values
            confidence_margin = (
                0.15 if st.session_state.get("model_type") == "Low Cost" else 0.10
            )

            if interval_hours == 24:
                # Show full 24 hours
                display_times = [
                    start_datetime - timedelta(hours=start_hour) + timedelta(hours=i)
                    for i in range(24)
                ]
                display_predicted = full_predicted[:24].tolist()
                display_upper = [v * (1 + confidence_margin) for v in display_predicted]
                display_lower = [v * (1 - confidence_margin) for v in display_predicted]
                selected_time = start_datetime
                selected_value = full_predicted[start_hour]
            else:
                # For 1h, 3h, 6h, 12h intervals - show window around selected hour
                window_config = {
                    1: 3,  # 1h: show 3 hours total
                    3: 3,  # 3h: show 9 hours total
                    6: 6,  # 6h: show 18 hours total
                    12: 12,  # 12h: show 24 hours
                }

                total_hours = window_config.get(interval_hours, 3)
                hours_before = total_hours // 2

                start_idx = max(0, start_hour - hours_before)
                end_idx = min(23, start_idx + total_hours - 1)

                if end_idx - start_idx < total_hours - 1:
                    start_idx = max(0, end_idx - total_hours + 1)

                all_indices = list(range(start_idx, end_idx + 1))

                display_times = [
                    start_datetime + timedelta(hours=(i - start_hour))
                    for i in all_indices
                ]
                display_predicted = [full_predicted[i] for i in all_indices]
                display_upper = [v * (1 + confidence_margin) for v in display_predicted]
                display_lower = [v * (1 - confidence_margin) for v in display_predicted]

                selected_hour_index_in_display = all_indices.index(start_hour)
                selected_time = display_times[selected_hour_index_in_display]
                selected_value = display_predicted[selected_hour_index_in_display]
        else:
            # Fallback
            display_times = times
            display_predicted = predicted
            display_upper = upper_bound
            display_lower = lower_bound
            selected_time = None
            selected_value = None
    else:
        display_times = times
        display_predicted = predicted
        display_upper = upper_bound
        display_lower = lower_bound
        selected_time = None
        selected_value = None

    # Create clean Plotly figure
    fig = go.Figure()

    # Confidence band (shaded area)
    fig.add_trace(
        go.Scatter(
            x=display_times + display_times[::-1],
            y=display_upper + display_lower[::-1],
            fill="toself",
            fillcolor="rgba(59, 130, 246, 0.1)",
            line=dict(width=0),
            showlegend=True,
            name="Confidence Range",
            hoverinfo="skip",
        )
    )

    # Main prediction line
    fig.add_trace(
        go.Scatter(
            x=display_times,
            y=display_predicted,
            mode="lines",
            line=dict(color="#3b82f6", width=3),
            name="Forecast",
            hovertemplate="<b>%{x|%H:%M}</b><br>%{y:.1f} MW<extra></extra>",
        )
    )

    # Highlight selected hour (if not 24h view)
    if selected_time is not None and selected_value is not None:
        fig.add_trace(
            go.Scatter(
                x=[selected_time],
                y=[selected_value],
                mode="markers",
                marker=dict(
                    size=14, color="#ef4444", line=dict(color="white", width=3)
                ),
                name="Selected Hour",
                hovertemplate="<b>Selected: %{x|%H:%M}</b><br>%{y:.1f} MW<extra></extra>",
            )
        )

    # Clean layout
    fig.update_layout(
        xaxis=dict(
            title="Time",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=False,
            tickformat="%H:%M",
            tickfont=dict(size=11, color="#64748b"),
        ),
        yaxis=dict(
            title="Power Output (MW)",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=True,
            zerolinecolor="rgba(0,0,0,0.1)",
            tickfont=dict(size=11, color="#64748b"),
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        height=500,
        margin=dict(l=60, r=30, t=40, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#475569"),
        ),
        font=dict(family="Inter, sans-serif"),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Detailed forecast table
    st.subheader("📋 Detailed Forecast")

    # Create DataFrame for display
    display_df = pd.DataFrame(
        {
            "Time": [
                t.strftime("%Y-%m-%d %H:%M") if hasattr(t, "strftime") else str(t)
                for t in times
            ],
            "Forecast (MW)": [f"{p:.0f}" for p in predicted],
            "Lower Bound (MW)": [f"{l:.0f}" for l in lower_bound],
            "Upper Bound (MW)": [f"{u:.0f}" for u in upper_bound],
            "Confidence": forecast_data.get("confidence", ["High"] * len(times)),
        }
    )

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Export options
    st.divider()
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("💾 Export Options")

    with col2:
        csv = display_df.to_csv(index=False)
        filename = f"forecast_{st.session_state.get('current_country', 'unknown')}_{st.session_state.get('current_energy', 'unknown').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=filename,
            mime="text/csv",
            use_container_width=True,
        )

else:
    # Landing page
    st.info("👈 Configure settings in the sidebar and click 'Run Forecast' to begin.")

# Footer
