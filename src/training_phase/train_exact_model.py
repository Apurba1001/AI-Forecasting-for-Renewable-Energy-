import pandas as pd
from pathlib import Path
from xgboost import XGBRegressor
import joblib
from feature_engineering import build_features_dataframe

# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "01_raw" / "generation_2024_raw.csv"

MODEL_DIR = PROJECT_ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("Looking for data at:")
print(DATA_FILE)
print("Exists?", DATA_FILE.exists())

TARGET_COL = ["Solar","Wind Onshore", "Wind Offshore"]   # change to "Wind Onshore" or "Wind Offshore"

TRAIN_END = "2024-10-31"
VAL_END = "2024-11-30"

XGB_PARAMS = dict(
    n_estimators=1500,
    max_depth=10,
    learning_rate=0.03,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    tree_method="hist",
    n_jobs=-1,
    random_state=42,
)

# ============================================================
# TRAINING
# ============================================================

def main():
    print("\n🚀 STARTING TRAINING FOR ALL ENERGY SOURCES")
    
    print("=" * 60)
    print("TRAINING HIGH-COST XGBOOST MODELS")
    print("=" * 60)
    
    print("TARGET_COLS seen by Python:", TARGET_COL)

    df = pd.read_csv(DATA_FILE)

    for target_col in TARGET_COL:
        print(f"\n➡️ Processing target_col = {target_col}")

        if target_col not in df.columns:
            print(f"⚠️ Skipping {target_col} (column not found)")
            continue

        X, y, timestamps = build_features_dataframe(
            df,
            target_col=target_col   # ✅ STRING, not list
        )

        # --- Time-based split ---
        train_mask = timestamps <= TRAIN_END
        val_mask = (timestamps > TRAIN_END) & (timestamps <= VAL_END)

        X_train, y_train = X.loc[train_mask], y.loc[train_mask]
        X_val, y_val = X.loc[val_mask], y.loc[val_mask]

        print(f"Total samples : {len(X)}")
        print(f"Train samples : {len(X_train)}")
        print(f"Val samples   : {len(X_val)}")

        if X_train.empty or X_val.empty:
            raise ValueError(f"Empty train/val split for {target_col}")

        model = XGBRegressor(**XGB_PARAMS)

        model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            verbose=100,
        )

        model_path = MODEL_DIR / f"xgb_high_cost_{target_col.replace(' ', '_')}.pkl"
        joblib.dump(model, model_path)

        print(f"✅ Saved model: {model_path.name}")

    print("\n🎉 ALL MODELS TRAINED SUCCESSFULLY")



if __name__ == "__main__":
    main()
