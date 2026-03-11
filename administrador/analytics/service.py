"""Convenience service module re-exporting analytics helpers.

This mirrors the old `administrador.analysis.service` API so internal
callsites can switch imports to `administrador.analytics.service` with
minimal changes. Keep this module small and explicit.
"""

from .queries import (
    throughput_by_day,
    entries_by_hour,
    entries_by_day_hour,
    peak_hours,
    total_senhas_generated,
)
from .metrics import (
    average_wait_time,
    current_queue_length,
    guiche_utilization,
    reanuncio_rate,
    queue_stats,
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
