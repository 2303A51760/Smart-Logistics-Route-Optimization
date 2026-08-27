import math
from typing import List, Tuple, Dict, Any


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth (in km)."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Calculate the great-circle distance in integer meters."""
    return int(haversine_distance_km(lat1, lon1, lat2, lon2) * 1000)


def compute_distance_matrix_meters(locations: List[Tuple[float, float]]) -> List[List[int]]:
    """Compute distance matrix in integer meters for OR-Tools routing model."""
    matrix: List[List[int]] = []
    for i, loc1 in enumerate(locations):
        row: List[int] = []
        for j, loc2 in enumerate(locations):
            if i == j:
                row.append(0)
            else:
                dist_m = haversine_distance_meters(loc1[0], loc1[1], loc2[0], loc2[1])
                row.append(dist_m)
        matrix.append(row)
    return matrix


def compute_time_matrix_seconds(
    locations: List[Tuple[float, float]],
    speed_kmh: float = 40.0,
    service_time_seconds: int = 300,
) -> List[List[int]]:
    """Compute travel time matrix in integer seconds assuming an average urban speed.
    
    speed_kmh: average transit velocity (default: 40 km/h)
    service_time_seconds: dwell time per stop for loading/unloading (default: 5 min)
    """
    speed_mps = (speed_kmh * 1000.0) / 3600.0  # meters per second
    if speed_mps <= 0:
        speed_mps = 11.11  # fallback to 40 km/h
    
    matrix: List[List[int]] = []
    for i, loc1 in enumerate(locations):
        row: List[int] = []
        for j, loc2 in enumerate(locations):
            if i == j:
                row.append(0)
            else:
                dist_m = haversine_distance_meters(loc1[0], loc1[1], loc2[0], loc2[1])
                transit_sec = int(dist_m / speed_mps)
                # If destination is not the depot (index 0), add service time
                additional_service = service_time_seconds if j != 0 else 0
                row.append(transit_sec + additional_service)
        matrix.append(row)
    return matrix
