# AI Forecasting for Renewable Energy Output (Wind & Solar)

**Team Members:**  
- Andreas Zisch  
- Apurba Bhushan Parajuli  

**GitHub Repository:**  
https://github.com/Apurba1001/AI-Forecasting-for-Renewable-Energy-.git  

---

## 1. Project Definition

Forecast 24-hour renewable generation using time-series models.

* **Architecture:** Data Ingest → Feature Engineering → Forecasting Engine → REST API.  
* **ADRs:** Rolling window selection; model selection (XGBoost or Holt \- Winters Exponential Smoothing).  
* **CI/CD:** Automated dataset validation, forecast accuracy tests, container builds.  
* **Sustainability:** Report carbon cost per forecast window or per batch job.  
* **Carbon-aware behavior:**  
  * High intensity: Use XGBoost the high cost model   
  * Low intensity: Use Holt-Winters as the low cost simple model

Summary:

This project implements a lightweight, cloud-based AI system that forecasts 24-hour renewable energy output (wind and solar) using standard time-series models. The architecture is kept simple while still demonstrating cloud-native principles. A small **Data Ingest service** periodically downloads historical generation data (e.g., from Open Power System Data) and stores it in cloud object storage. A **Feature Engineering component** prepares rolling-window features, and a **Forecasting Engine** runs one of two models: a full-precision ARIMA/Prophet model or a simplified low-power baseline. A single **REST API** (built with FastAPI) exposes both the forecasts and system status to a minimal dashboard.

---

## 2. Use Cases

### Scheduled Data Ingestion and Validation
![Data Ingest Pipeline](https://github.com/Apurba1001/AI-Forecasting-for-Renewable-Energy-/blob/Apurba/data_Ingest.png)
   **Primary Actors:** Data Ingest Service, CI/CD Pipeline  
   **Description:**  
    At regular intervals, the Data Ingest Service downloads renewable energy generation data from external sources (ENTSOE)  and validates schema, freshness, and completeness before saving them for feature engineering. Failed validations block downstream processing and trigger alerts in the CI/CD pipeline.  
    **Architectural Significance:**  
   This use case drives decisions around data contracts, storage abstraction, fault isolation, and automated quality gates in the pipeline

### Rolling-Window Feature Engineering
![Feature Engineering](https://github.com/Apurba1001/AI-Forecasting-for-Renewable-Energy-/blob/Apurba/features.png)
    **Primary Actors:** Forecasting Engine, Carbon Intensity Monitor  
    **Description:**  
    When a forecast request or scheduled job is triggered, the system evaluates the current carbon-intensity signal. If carbon intensity is low, the Forecasting Engine executes a full-precision forecasting model ; if carbon intensity is high, it switches to a low-power baseline model to reduce emissions.  
    **Architectural Significance:**  
    This use case directly influences model selection logic, runtime adaptability, sustainability goals, and the separation of concerns between monitoring and forecasting components.

### Carbon-Aware Forecast Execution
![Carbon-Aware Forecasting](https://github.com/Apurba1001/AI-Forecasting-for-Renewable-Energy-/blob/Apurba/carbon.png)
    **Primary Actors:** Forecasting Engine, Carbon Intensity Monitor  
    **Description:**  
    When a forecast request or scheduled job is triggered, the system evaluates the current carbon-intensity signal. If carbon intensity is low, the Forecasting Engine executes a full-precision forecasting model; if carbon intensity is high, it switches to a low-power baseline or quantized model to reduce emissions.  
    **Architectural Significance:**  
    This use case directly influences model selection logic, runtime adaptability, sustainability goals, and the separation of concerns between monitoring and forecasting components.

---

## 3. Component Diagram
![Component Diagram](https://github.com/Apurba1001/AI-Forecasting-for-Renewable-Energy-/blob/Apurba/component.png)

### **1\. Training Phase (Offline)**

* Data is ingested, cleaned, and transformed into features.  
* Two models are trained in parallel:  
  * **Heavy model** (high accuracy, high compute/emissions)  
  * **Light model** (lower accuracy, low compute/emissions)  
* Emissions and accuracy metrics are tracked.  
* Trained models and metrics are stored as shared artifacts.

### **2\. Production Phase (Live Inference)**

* A **FastAPI inference server** receives prediction requests.  
* A **carbon-aware switch** selects:  
  * the **heavy model** when carbon intensity is low, or  
  * the **light model** when carbon intensity is high.  
* Predictions are aggregated and returned to the user/dashboard  
---

## Application Scaffolding

```
## Application Scaffolding:

AI-Forecasting-for-Renewable-Energy-/
├── data/
│   ├── 01\_raw/          \# Raw CSVs from ENTSOE
│   ├── 02\_intermediate/ \# Cleaned/Imputed data
│   └── 03\_model\_input/  \# Data with features (lags, rolling windows) 
│
├── models/              \# Where the final .joblib/.pkl files live
│
├── src/
│   ├── production\_phase/  
│   ├── training\_phase/
│   │   ├── 1\_load\_data.py
│   │   ├── 2\_preprocessing.py
│   │   ├── 3\_feature\_engineering.py
│   │   ├── 4\_train\_exact\_model.py
│   │	├── 5\_train\_lightweight\_model.py
│   │   └── 6\_evaluate.py
│   │
│   └── api/            
│       └── main.py
├── requirements.txt
```
