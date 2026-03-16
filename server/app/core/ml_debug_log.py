"""
In-memory debug log store for ML operations.

Keeps only the latest 100 events so logs remain lightweight.
"""

from collections import deque
from datetime import datetime, timezone
from itertools import count
from typing import Any, Dict, List, Optional

MAX_ML_DEBUG_LOGS = 100

_ml_debug_logs: deque[Dict[str, Any]] = deque(maxlen=MAX_ML_DEBUG_LOGS)
_ml_log_counter = count(1)


def add_ml_debug_log(
    component: str,
    operation: str,
    message: str,
    level: str = "INFO",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Append a log entry to the in-memory ML debug buffer (newest first)."""
    entry = {
        "id": next(_ml_log_counter),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "operation": operation,
        "level": level.upper(),
        "message": message,
        "details": details or {},
    }
    _ml_debug_logs.appendleft(entry)
    return entry


def get_ml_debug_logs(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return latest ML debug logs, newest first."""
    logs = list(_ml_debug_logs)
    if limit is None:
        return logs
    safe_limit = max(1, min(int(limit), MAX_ML_DEBUG_LOGS))
    return logs[:safe_limit]


def clear_ml_debug_logs() -> None:
    """Clear all in-memory ML debug logs."""
    _ml_debug_logs.clear()


def get_ml_debug_log_count() -> int:
    """Return current number of retained ML debug logs."""
    return len(_ml_debug_logs)
