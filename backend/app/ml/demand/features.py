from datetime import date
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "day_of_week",
    "day_of_month",
    "month",
    "week_of_year",
    "is_weekend",
    "lag_1",
    "lag_7",
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_30",
]


def build_time_series_feature_matrix(
    daily_records: List[Dict[str, Any]],
) -> Tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    """
    Transforms chronological daily order time-series into feature matrix X and target y.
    Guarantees strict data leakage prevention:
    - Lag features and rolling statistics are shifted so that date T only uses information from T-1, T-2, ...
    """
    if len(daily_records) < 35:
        raise ValueError(f"Insufficient historical daily records ({len(daily_records)} found, minimum 35 required for rolling features).")

    df = pd.DataFrame(daily_records).copy()
    df["dt"] = pd.to_datetime(df["date"])
    df = df.sort_values("dt").reset_index(drop=True)

    # 1. Calendar Features
    df["day_of_week"] = df["dt"].dt.dayofweek
    df["day_of_month"] = df["dt"].dt.day
    df["month"] = df["dt"].dt.month
    df["week_of_year"] = df["dt"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    # 2. Lag Features (Shifted by 1 step to avoid target leakage)
    df["lag_1"] = df["orders_count"].shift(1)
    df["lag_7"] = df["orders_count"].shift(7)

    # 3. Rolling Window Statistics (Strictly over historical shifted windows)
    df["rolling_mean_7"] = df["orders_count"].shift(1).rolling(window=7, min_periods=3).mean()
    df["rolling_mean_14"] = df["orders_count"].shift(1).rolling(window=14, min_periods=7).mean()
    df["rolling_mean_30"] = df["orders_count"].shift(1).rolling(window=30, min_periods=14).mean()

    # Drop rows with NaN due to lag/rolling window warmup
    clean_df = df.dropna().reset_index(drop=True)

    X_df = clean_df[FEATURE_COLUMNS]
    y_arr = clean_df["orders_count"].values.astype(np.float64)

    return X_df, y_arr, clean_df


def extract_features_for_forecast_date(
    target_date: date,
    historical_series: List[float],
) -> Dict[str, Any]:
    """
    Constructs feature dictionary for future date T using the latest historical sequence.
    """
    dt = pd.to_datetime(target_date)
    series = list(historical_series)

    lag_1 = float(series[-1]) if len(series) >= 1 else 40.0
    lag_7 = float(series[-7]) if len(series) >= 7 else lag_1

    roll_7 = float(np.mean(series[-7:])) if len(series) >= 7 else float(np.mean(series))
    roll_14 = float(np.mean(series[-14:])) if len(series) >= 14 else roll_7
    roll_30 = float(np.mean(series[-30:])) if len(series) >= 30 else roll_14

    return {
        "day_of_week": int(dt.dayofweek),
        "day_of_month": int(dt.day),
        "month": int(dt.month),
        "week_of_year": int(dt.isocalendar().week),
        "is_weekend": int(dt.dayofweek in [5, 6]),
        "lag_1": lag_1,
        "lag_7": lag_7,
        "rolling_mean_7": roll_7,
        "rolling_mean_14": roll_14,
        "rolling_mean_30": roll_30,
    }
