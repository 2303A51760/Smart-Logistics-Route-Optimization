import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in km."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


# Realistic Historical Training Samples synthesized from urban delivery operations
HISTORICAL_DELIVERY_RECORDS: List[Dict[str, Any]] = [
    {"distance_km": 3.2, "package_weight": 2.5, "priority": "NORMAL", "vehicle_type": "VAN", "number_of_stops": 3, "stop_sequence": 1, "hour": 9, "day_of_week": 1, "actual_delivery_duration_minutes": 14.5, "timestamp": datetime(2026, 7, 1, 9, 30)},
    {"distance_km": 7.8, "package_weight": 12.0, "priority": "HIGH", "vehicle_type": "VAN", "number_of_stops": 5, "stop_sequence": 2, "hour": 11, "day_of_week": 1, "actual_delivery_duration_minutes": 26.0, "timestamp": datetime(2026, 7, 1, 11, 45)},
    {"distance_km": 14.5, "package_weight": 35.0, "priority": "URGENT", "vehicle_type": "TRUCK", "number_of_stops": 4, "stop_sequence": 3, "hour": 14, "day_of_week": 1, "actual_delivery_duration_minutes": 42.0, "timestamp": datetime(2026, 7, 1, 14, 50)},
    {"distance_km": 5.1, "package_weight": 4.0, "priority": "NORMAL", "vehicle_type": "VAN", "number_of_stops": 6, "stop_sequence": 1, "hour": 10, "day_of_week": 2, "actual_delivery_duration_minutes": 18.0, "timestamp": datetime(2026, 7, 2, 10, 15)},
    {"distance_km": 11.2, "package_weight": 18.5, "priority": "HIGH", "vehicle_type": "TRUCK", "number_of_stops": 5, "stop_sequence": 4, "hour": 13, "day_of_week": 2, "actual_delivery_duration_minutes": 36.5, "timestamp": datetime(2026, 7, 2, 13, 40)},
    {"distance_km": 2.4, "package_weight": 1.5, "priority": "LOW", "vehicle_type": "VAN", "number_of_stops": 2, "stop_sequence": 1, "hour": 16, "day_of_week": 2, "actual_delivery_duration_minutes": 11.0, "timestamp": datetime(2026, 7, 2, 16, 20)},
    {"distance_km": 18.0, "package_weight": 45.0, "priority": "URGENT", "vehicle_type": "TRUCK", "number_of_stops": 8, "stop_sequence": 5, "hour": 17, "day_of_week": 3, "actual_delivery_duration_minutes": 58.0, "timestamp": datetime(2026, 7, 3, 17, 30)},
    {"distance_km": 6.3, "package_weight": 8.0, "priority": "NORMAL", "vehicle_type": "VAN", "number_of_stops": 4, "stop_sequence": 2, "hour": 12, "day_of_week": 3, "actual_delivery_duration_minutes": 22.5, "timestamp": datetime(2026, 7, 3, 12, 10)},
    {"distance_km": 9.5, "package_weight": 15.0, "priority": "HIGH", "vehicle_type": "VAN", "number_of_stops": 6, "stop_sequence": 3, "hour": 15, "day_of_week": 4, "actual_delivery_duration_minutes": 31.0, "timestamp": datetime(2026, 7, 4, 15, 45)},
    {"distance_km": 4.0, "package_weight": 3.0, "priority": "LOW", "vehicle_type": "VAN", "number_of_stops": 3, "stop_sequence": 2, "hour": 10, "day_of_week": 4, "actual_delivery_duration_minutes": 15.0, "timestamp": datetime(2026, 7, 4, 10, 30)},
    {"distance_km": 22.4, "package_weight": 60.0, "priority": "URGENT", "vehicle_type": "TRUCK", "number_of_stops": 10, "stop_sequence": 7, "hour": 18, "day_of_week": 5, "actual_delivery_duration_minutes": 72.0, "timestamp": datetime(2026, 7, 5, 18, 15)},
    {"distance_km": 8.7, "package_weight": 14.0, "priority": "NORMAL", "vehicle_type": "VAN", "number_of_stops": 5, "stop_sequence": 3, "hour": 14, "day_of_week": 5, "actual_delivery_duration_minutes": 27.5, "timestamp": datetime(2026, 7, 5, 14, 20)},
    {"distance_km": 1.8, "package_weight": 1.0, "priority": "HIGH", "vehicle_type": "VAN", "number_of_stops": 2, "stop_sequence": 1, "hour": 11, "day_of_week": 6, "actual_delivery_duration_minutes": 9.0, "timestamp": datetime(2026, 7, 6, 11, 10)},
    {"distance_km": 13.0, "package_weight": 28.0, "priority": "NORMAL", "vehicle_type": "TRUCK", "number_of_stops": 7, "stop_sequence": 4, "hour": 13, "day_of_week": 6, "actual_delivery_duration_minutes": 39.0, "timestamp": datetime(2026, 7, 6, 13, 50)},
    {"distance_km": 5.9, "package_weight": 7.5, "priority": "HIGH", "vehicle_type": "VAN", "number_of_stops": 4, "stop_sequence": 2, "hour": 15, "day_of_week": 0, "actual_delivery_duration_minutes": 20.0, "timestamp": datetime(2026, 7, 7, 15, 25)},
    {"distance_km": 16.2, "package_weight": 40.0, "priority": "URGENT", "vehicle_type": "TRUCK", "number_of_stops": 8, "stop_sequence": 6, "hour": 16, "day_of_week": 0, "actual_delivery_duration_minutes": 52.0, "timestamp": datetime(2026, 7, 7, 16, 40)},
    {"distance_km": 3.8, "package_weight": 2.0, "priority": "NORMAL", "vehicle_type": "VAN", "number_of_stops": 3, "stop_sequence": 1, "hour": 9, "day_of_week": 1, "actual_delivery_duration_minutes": 16.0, "timestamp": datetime(2026, 7, 8, 9, 15)},
    {"distance_km": 10.4, "package_weight": 22.0, "priority": "NORMAL", "vehicle_type": "VAN", "number_of_stops": 5, "stop_sequence": 3, "hour": 12, "day_of_week": 1, "actual_delivery_duration_minutes": 33.0, "timestamp": datetime(2026, 7, 8, 12, 30)},
    {"distance_km": 25.0, "package_weight": 80.0, "priority": "HIGH", "vehicle_type": "TRUCK", "number_of_stops": 9, "stop_sequence": 8, "hour": 17, "day_of_week": 2, "actual_delivery_duration_minutes": 78.0, "timestamp": datetime(2026, 7, 9, 17, 10)},
    {"distance_km": 6.8, "package_weight": 9.5, "priority": "NORMAL", "vehicle_type": "VAN", "number_of_stops": 4, "stop_sequence": 2, "hour": 14, "day_of_week": 2, "actual_delivery_duration_minutes": 24.0, "timestamp": datetime(2026, 7, 9, 14, 45)},
    {"distance_km": 12.1, "package_weight": 25.0, "priority": "URGENT", "vehicle_type": "VAN", "number_of_stops": 6, "stop_sequence": 4, "hour": 16, "day_of_week": 3, "actual_delivery_duration_minutes": 38.0, "timestamp": datetime(2026, 7, 10, 16, 0)},
    {"distance_km": 4.5, "package_weight": 5.0, "priority": "LOW", "vehicle_type": "VAN", "number_of_stops": 3, "stop_sequence": 1, "hour": 10, "day_of_week": 3, "actual_delivery_duration_minutes": 16.5, "timestamp": datetime(2026, 7, 10, 10, 40)},
    {"distance_km": 15.5, "package_weight": 32.0, "priority": "HIGH", "vehicle_type": "TRUCK", "number_of_stops": 7, "stop_sequence": 5, "hour": 15, "day_of_week": 4, "actual_delivery_duration_minutes": 48.0, "timestamp": datetime(2026, 7, 11, 15, 20)},
    {"distance_km": 2.9, "package_weight": 1.8, "priority": "NORMAL", "vehicle_type": "VAN", "number_of_stops": 2, "stop_sequence": 1, "hour": 11, "day_of_week": 4, "actual_delivery_duration_minutes": 12.5, "timestamp": datetime(2026, 7, 11, 11, 35)},
    {"distance_km": 8.0, "package_weight": 11.0, "priority": "NORMAL", "vehicle_type": "VAN", "number_of_stops": 5, "stop_sequence": 2, "hour": 13, "day_of_week": 5, "actual_delivery_duration_minutes": 25.0, "timestamp": datetime(2026, 7, 12, 13, 10)},
]


def clean_and_validate_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cleans raw delivery records:
    - Removes invalid / negative durations
    - Validates positive distance and package weights
    - Filters corrupt / missing categorical values
    """
    cleaned: List[Dict[str, Any]] = []

    for r in records:
        try:
            dist = float(r.get("distance_km", 0.0))
            dur = float(r.get("actual_delivery_duration_minutes", 0.0))
            wt = float(r.get("package_weight", 1.0))
            stops = int(r.get("number_of_stops", 1))
            seq = int(r.get("stop_sequence", 1))
            hr = int(r.get("hour", 12))
            dow = int(r.get("day_of_week", 0))
            priority = str(r.get("priority", "NORMAL")).upper()
            vehicle_type = str(r.get("vehicle_type", "VAN")).upper()

            # Validation bounds
            if dist <= 0.0 or dist > 500.0:
                continue
            if dur <= 0.0 or dur > 1440.0:
                continue
            if wt < 0.0 or wt > 10000.0:
                continue
            if stops < 1 or seq < 1 or seq > stops + 10:
                continue
            if hr < 0 or hr > 23 or dow < 0 or dow > 6:
                continue

            cleaned.append({
                "distance_km": dist,
                "package_weight": wt,
                "priority": priority,
                "vehicle_type": vehicle_type,
                "number_of_stops": stops,
                "stop_sequence": seq,
                "hour": hr,
                "day_of_week": dow,
                "actual_delivery_duration_minutes": dur,
                "timestamp": r.get("timestamp", datetime.utcnow()),
            })
        except Exception:
            continue

    return cleaned


def get_historical_dataset() -> List[Dict[str, Any]]:
    """Returns validated historical delivery dataset sorted chronologically."""
    cleaned = clean_and_validate_records(HISTORICAL_DELIVERY_RECORDS)
    cleaned.sort(key=lambda x: x["timestamp"])
    return cleaned
