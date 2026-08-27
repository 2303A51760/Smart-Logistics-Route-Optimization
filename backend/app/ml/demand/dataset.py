import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Continuous 90-day historical daily logistics order demand volume
# Reflects realistic urban logistics patterns (weekday peaks, weekend drops, periodic holiday surges)
_BASE_START_DATE = date(2026, 5, 1)
_HISTORICAL_DAILY_COUNTS = [
    42, 45, 48, 52, 55, 30, 25,  # Week 1
    44, 47, 50, 53, 58, 32, 28,  # Week 2
    46, 49, 52, 56, 61, 35, 29,  # Week 3
    45, 48, 51, 54, 59, 31, 26,  # Week 4
    48, 52, 55, 60, 64, 38, 30,  # Week 5
    49, 53, 56, 59, 63, 36, 31,  # Week 6
    50, 54, 58, 62, 67, 40, 32,  # Week 7
    52, 55, 59, 63, 68, 39, 33,  # Week 8
    51, 54, 57, 61, 66, 37, 30,  # Week 9
    53, 57, 61, 65, 70, 42, 34,  # Week 10
    54, 58, 62, 66, 72, 43, 35,  # Week 11
    55, 59, 63, 68, 74, 45, 36,  # Week 12
    56, 60, 64, 69, 75, 46, 37,  # Week 13
]

SYNTHETIC_HISTORICAL_ORDERS_SERIES: List[Dict[str, Any]] = [
    {
        "date": (_BASE_START_DATE + timedelta(days=i)).isoformat(),
        "orders_count": count,
        "warehouse_id": "wh-001" if i % 3 != 2 else ("wh-002" if i % 3 == 1 else "wh-003"),
    }
    for i, count in enumerate(_HISTORICAL_DAILY_COUNTS)
]


def fill_missing_dates(
    daily_records: List[Dict[str, Any]],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Ensures complete chronological time-series with zero-demand days preserved.
    Prevents missing dates from corrupting lag and rolling window features.
    """
    if not daily_records:
        return []

    # Map existing records by date string
    record_map: Dict[str, int] = {}
    for r in daily_records:
        d_str = r["date"] if isinstance(r["date"], str) else r["date"].isoformat()
        record_map[d_str] = record_map.get(d_str, 0) + int(r.get("orders_count", 1))

    all_dates = [datetime.fromisoformat(d).date() for d in record_map.keys()]
    min_d = start_date or min(all_dates)
    max_d = end_date or max(all_dates)

    filled: List[Dict[str, Any]] = []
    curr_d = min_d
    while curr_d <= max_d:
        d_str = curr_d.isoformat()
        orders = record_map.get(d_str, 0)
        filled.append({
            "date": d_str,
            "orders_count": orders,
        })
        curr_d += timedelta(days=1)

    return filled


def aggregate_orders_by_period(
    raw_orders: List[Dict[str, Any]],
    period: str = "daily",
    warehouse_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Aggregates order events into daily or weekly time-series buckets.
    """
    filtered = raw_orders
    if warehouse_id:
        filtered = [o for o in raw_orders if o.get("warehouse_id") == warehouse_id]

    if not filtered:
        return []

    # Group by date
    daily_counts: Dict[str, int] = {}
    for o in filtered:
        ts = o.get("created_at") or o.get("date")
        if isinstance(ts, str):
            d_str = ts.split("T")[0]
        elif isinstance(ts, (datetime, date)):
            d_str = ts.strftime("%Y-%m-%d")
        else:
            continue

        daily_counts[d_str] = daily_counts.get(d_str, 0) + 1

    daily_list = [{"date": d, "orders_count": count} for d, count in sorted(daily_counts.items())]
    filled_daily = fill_missing_dates(daily_list)

    if period.lower() == "weekly":
        # Group by Monday-based week
        df = pd.DataFrame(filled_daily)
        df["dt"] = pd.to_datetime(df["date"])
        df["week"] = df["dt"].dt.to_period("W-SUN").apply(lambda r: r.start_time.strftime("%Y-%m-%d"))
        weekly_df = df.groupby("week")["orders_count"].sum().reset_index()
        return [{"date": row["week"], "orders_count": int(row["orders_count"])} for _, row in weekly_df.iterrows()]

    return filled_daily


def get_historical_demand_dataset(warehouse_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns validated continuous daily historical demand time-series dataset.
    """
    if warehouse_id:
        filtered = [r for r in SYNTHETIC_HISTORICAL_ORDERS_SERIES if r.get("warehouse_id") == warehouse_id]
        if len(filtered) < 14:
            # Scale down base counts for specific warehouse
            wh_factor = 0.55 if warehouse_id == "wh-001" else 0.35
            return [
                {
                    "date": r["date"],
                    "orders_count": max(1, int(r["orders_count"] * wh_factor)),
                }
                for r in SYNTHETIC_HISTORICAL_ORDERS_SERIES
            ]
        return fill_missing_dates(filtered)

    return fill_missing_dates(SYNTHETIC_HISTORICAL_ORDERS_SERIES)
