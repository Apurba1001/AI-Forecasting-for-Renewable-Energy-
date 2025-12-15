import pandas as pd


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df["hour"] = df["datetime_utc"].dt.hour
    df["dayofweek"] = df["datetime_utc"].dt.dayofweek
    df["month"] = df["datetime_utc"].dt.month
    df["dayofyear"] = df["datetime_utc"].dt.dayofyear
    df["weekofyear"] = df["datetime_utc"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    return df


def build_features_dataframe(df: pd.DataFrame, target_col: str):
    """
    Build GLOBAL (all countries) feature matrix for high-cost XGBoost
    """

    # --- Validation ---
    target_col = target_col.strip()
    if target_col not in df.columns:
        raise ValueError(
            f"Target column '{target_col}' not found. "
            f"Available columns: {list(df.columns)}"
        )

    # --- Prep ---
    df = df.copy()
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True)
    df = df.sort_values(["Country", "datetime_utc"])

    # --- Time features ---
    df = add_time_features(df)

    # --- Lag features (PER COUNTRY) ---
    lags = [1, 3, 6, 12, 24, 48, 168]
    for lag in lags:
        df[f"{target_col}_lag_{lag}"] = (
            df.groupby("Country")[target_col].shift(lag)
        )

    # --- Rolling statistics (PER COUNTRY) ---
    for window in [24, 168]:
        df[f"{target_col}_roll_mean_{window}"] = (
            df.groupby("Country")[target_col]
              .rolling(window)
              .mean()
              .reset_index(level=0, drop=True)
        )
        df[f"{target_col}_roll_std_{window}"] = (
            df.groupby("Country")[target_col]
              .rolling(window)
              .std()
              .reset_index(level=0, drop=True)
        )

    # --- Country one-hot encoding ---
    country_dummies = pd.get_dummies(df["Country"], prefix="country")
    df = pd.concat([df, country_dummies], axis=1)

    # --- Drop rows with insufficient history ---
    df = df.dropna()

    if df.empty:
        raise ValueError("No rows left after feature engineering. Check data coverage.")

    # --- Split X / y ---
    X = df.drop(columns=["datetime_utc", "Country", target_col])
    y = df[target_col]
    timestamps = df["datetime_utc"]

    return X.astype(float), y.astype(float), timestamps
