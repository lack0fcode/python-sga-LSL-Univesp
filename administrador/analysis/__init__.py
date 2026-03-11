"""Compatibility shim: re-export analytics functions from the new
`administrador.analytics` package so existing imports keep working.
"""

from administrador.analytics.metrics import (
    average_wait_time,
    current_queue_length,
    guiche_utilization,
    reanuncio_rate,
    queue_stats,
)
from administrador.analytics.queries import (
    peak_hours,
    entries_by_hour,
    entries_by_day_hour,
    throughput_by_day,
    total_senhas_generated,
)

__all__ = [
    "total_senhas_generated",
    "throughput_by_day",
    "average_wait_time",
    "current_queue_length",
    "peak_hours",
    "entries_by_hour",
    "entries_by_day_hour",
    "guiche_utilization",
    "reanuncio_rate",
    "queue_stats",
]
