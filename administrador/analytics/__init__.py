"""Analytics package: split queries and metrics for clarity.

Public modules:
- queries: low-level DB grouping helpers
- metrics: composed KPI functions
- dashboards: frontend-oriented payload helpers
"""

from . import queries, metrics, dashboards

__all__ = ["queries", "metrics", "dashboards"]
