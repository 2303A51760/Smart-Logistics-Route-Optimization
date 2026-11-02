import time
from datetime import datetime
from typing import Dict, Any

_START_TIME = time.time()
_TOTAL_REQUESTS = 0
_ERROR_REQUESTS = 0


def increment_request_count():
    global _TOTAL_REQUESTS
    _TOTAL_REQUESTS += 1


def increment_error_count():
    global _ERROR_REQUESTS
    _ERROR_REQUESTS += 1


def get_metrics_data() -> Dict[str, Any]:
    uptime = time.time() - _START_TIME
    return {
        "uptime_seconds": round(uptime, 2),
        "total_requests": _TOTAL_REQUESTS,
        "error_requests": _ERROR_REQUESTS,
        "system_status": "operational",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
