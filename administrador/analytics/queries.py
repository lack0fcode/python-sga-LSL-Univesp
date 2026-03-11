from datetime import datetime
from typing import List, Optional
from collections import Counter as _Counter
import logging

from django.db.models import Min
from django.utils import timezone

from core.models import Atendimento, Paciente

logger = logging.getLogger(__name__)


def _normalize_range(
    start: Optional[datetime],
    end: Optional[datetime],
) -> tuple:
    if end is None:
        end_dt = timezone.now()
    else:
        end_dt = end

    if start is None:
        p_min = Paciente.objects.aggregate(min_p=Min("horario_geracao_senha"))
        a_min = Atendimento.objects.aggregate(min_a=Min("data_hora"))
        candidates = [
            p_min.get("min_p"),
            a_min.get("min_a"),
        ]
        earliest = None
        for c in candidates:
            if c is None:
                continue
            if earliest is None or c < earliest:
                earliest = c
        if earliest is None:
            tzinfo_val = timezone.utc
            earliest = datetime(
                1970,
                1,
                1,
                tzinfo=tzinfo_val,
            )
        start_dt = earliest
    else:
        start_dt = start

    return start_dt, end_dt


def total_senhas_generated(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> int:
    s, e = _normalize_range(start, end)
    qs = Paciente.objects.filter(horario_geracao_senha__range=(s, e))
    return int(qs.count())


def throughput_by_day(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[dict]:
    s, e = _normalize_range(start, end)
    from collections import Counter
    from datetime import timedelta as _td

    days: _Counter = _Counter()
    for dt in Paciente.objects.filter(horario_geracao_senha__range=(s, e)).values_list(
        "horario_geracao_senha",
        flat=True,
    ):
        if not dt:
            continue
        try:
            key = dt.date()
        except Exception as exc:
            logger.debug(
                "skipping invalid datetime in throughput_by_day: %r (%s)", dt, exc
            )
            continue
        days[key] += 1

    start_date = s.date()
    end_date = e.date()
    result = []
    cur = start_date
    while cur <= end_date:
        # return actual date objects here so callers that expect date keys
        # (unit tests) receive them directly
        result.append({"day": cur, "count": int(days.get(cur, 0))})
        cur = cur + _td(days=1)

    return result


def peak_hours(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[dict]:
    s, e = _normalize_range(start, end)
    from collections import Counter

    hours: _Counter = _Counter()
    for dt in Paciente.objects.filter(horario_geracao_senha__range=(s, e)).values_list(
        "horario_geracao_senha",
        flat=True,
    ):
        if not dt:
            continue
        try:
            h = int(dt.hour)
        except Exception as exc:
            logger.debug("skipping invalid datetime in peak_hours: %r (%s)", dt, exc)
            continue
        hours[h] += 1

    result = []
    for k, v in sorted(hours.items()):
        result.append({"hour": k, "count": v})
    return result


def entries_by_hour(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[dict]:
    s, e = _normalize_range(start, end)
    from collections import Counter

    hours: _Counter = _Counter()
    for dt in Paciente.objects.filter(horario_geracao_senha__range=(s, e)).values_list(
        "horario_geracao_senha",
        flat=True,
    ):
        if not dt:
            continue
        try:
            truncated = dt.replace(minute=0, second=0, microsecond=0)
        except Exception as exc:
            logger.debug(
                "skipping invalid datetime in entries_by_hour: %r (%s)", dt, exc
            )
            continue
        hours[truncated] += 1

    result = []
    for k, v in sorted(hours.items()):
        result.append({"hour": k.isoformat(), "count": v})
    return result


def entries_by_day_hour(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[dict]:
    s, e = _normalize_range(start, end)
    from collections import Counter
    from datetime import timedelta as _td

    counts: _Counter = _Counter()
    for dt in Paciente.objects.filter(horario_geracao_senha__range=(s, e)).values_list(
        "horario_geracao_senha",
        flat=True,
    ):
        if not dt:
            continue
        try:
            day = dt.date().isoformat()
            hour = int(dt.hour)
        except Exception as exc:
            logger.debug(
                "skipping invalid datetime in entries_by_day_hour: %r (%s)", dt, exc
            )
            continue
        counts[(day, hour)] += 1

    start_date = s.date()
    end_date = e.date()
    result = []
    cur = start_date
    while cur <= end_date:
        day_str = cur.isoformat()
        for hour in range(0, 24):
            result.append(
                {
                    "day": day_str,
                    "hour": hour,
                    "count": int(counts.get((day_str, hour), 0)),
                }
            )
        cur = cur + _td(days=1)

    result.sort(key=lambda x: (x["day"], x["hour"]))
    return result
