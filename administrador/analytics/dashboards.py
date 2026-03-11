"""Dashboard-oriented helpers that prepare payloads for frontend views.

This module composes query and metric functions to return JSON-serializable
structures tailored for charts and fragments.
"""

from typing import Optional, List
from datetime import datetime

from .queries import (
    entries_by_day_hour,
    entries_by_hour,
    throughput_by_day,
)
from .metrics import queue_stats
from .metrics import (
    median_wait_time,
    p95_wait_time,
    average_service_time,
    abandonment_rate,
    scheduled_vs_walkin,
    no_show_rate,
    sla_breach_count,
    queue_breakdown_by_type,
)


def dashboard_overview(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> dict:
    stats = queue_stats(start, end)
    # enrich with additional KPIs
    stats.update(
        {
            "median_wait_seconds": median_wait_time(start, end),
            "p95_wait_seconds": p95_wait_time(start, end),
            "avg_service_seconds": average_service_time(start, end),
            "abandonment_rate": abandonment_rate(start, end),
            "scheduled_vs_walkin": scheduled_vs_walkin(start, end),
            "no_show_rate": no_show_rate(start, end),
            "sla_breach_count": sla_breach_count(start, end),
            "queue_breakdown": queue_breakdown_by_type(),
        }
    )
    return stats


def dashboard_throughput(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> List[dict]:
    return throughput_by_day(start, end)


def dashboard_entries_hour(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> List[dict]:
    return entries_by_hour(start, end)


def dashboard_entries_day_hour(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> List[dict]:
    return entries_by_day_hour(start, end)
