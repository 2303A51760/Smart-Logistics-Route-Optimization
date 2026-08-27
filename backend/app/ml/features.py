from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

NUMERICAL_FEATURES = [
    "distance_km",
    "package_weight",
    "number_of_stops",
    "stop_sequence",
    "hour",
    "day_of_week",
]

CATEGORICAL_FEATURES = [
    "priority",
    "vehicle_type",
]

ALL_FEATURE_COLUMNS = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


def create_feature_preprocessor() -> ColumnTransformer:
    """
    Builds a Scikit-Learn ColumnTransformer for standardizing numerical
    features and one-hot encoding categorical features.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return preprocessor


def extract_feature_dict(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts strictly pre-delivery features from a raw input or entity dict.
    Guarantees no data leakage (excludes actual durations/timestamps).
    """
    return {
        "distance_km": float(record.get("distance_km", 5.0)),
        "package_weight": float(record.get("package_weight", 1.0)),
        "number_of_stops": int(record.get("number_of_stops", 1)),
        "stop_sequence": int(record.get("stop_sequence", 1)),
        "hour": int(record.get("hour", datetime_now_hour(record))),
        "day_of_week": int(record.get("day_of_week", datetime_now_dow(record))),
        "priority": str(record.get("priority", "NORMAL")).upper(),
        "vehicle_type": str(record.get("vehicle_type", "VAN")).upper(),
    }


def datetime_now_hour(record: Dict[str, Any]) -> int:
    ts = record.get("timestamp")
    if isinstance(ts, str):
        try:
            from datetime import datetime
            return datetime.fromisoformat(ts).hour
        except Exception:
            pass
    return 12


def datetime_now_dow(record: Dict[str, Any]) -> int:
    ts = record.get("timestamp")
    if isinstance(ts, str):
        try:
            from datetime import datetime
            return datetime.fromisoformat(ts).weekday()
        except Exception:
            pass
    return 0


def records_to_feature_matrix(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], np.ndarray]:
    """
    Converts list of delivery records to feature dictionaries and target vector y.
    """
    X_dicts: List[Dict[str, Any]] = []
    y_vals: List[float] = []

    for r in records:
        X_dicts.append(extract_feature_dict(r))
        if "actual_delivery_duration_minutes" in r:
            y_vals.append(float(r["actual_delivery_duration_minutes"]))

    y_arr = np.array(y_vals, dtype=np.float64) if y_vals else np.array([])
    return X_dicts, y_arr
