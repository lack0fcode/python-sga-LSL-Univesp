from typing import Optional, List, Dict
from datetime import datetime, timedelta
import statistics
import logging

from django.db.models import (
    Avg,
    DurationField,
    ExpressionWrapper,
    F,
    Count,
)

from core.models import Atendimento, Chamada, Guiche, Paciente
from .queries import _normalize_range, throughput_by_day

logger = logging.getLogger(__name__)


def average_wait_time(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
):
    s, e = _normalize_range(start, end)
    f_left = F("data_hora")
    f_right = F("paciente__horario_geracao_senha")
    expr = f_left - f_right
    qs = (
        Atendimento.objects.filter(data_hora__range=(s, e))
        .annotate(
            wait=ExpressionWrapper(
                expr,
                output_field=DurationField(),
            )
        )
        .aggregate(avg_wait=Avg("wait"))
    )
    return qs.get("avg_wait")


def current_queue_length() -> int:
    return int(Paciente.objects.filter(atendido=False).count())


def guiche_utilization(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Optional[float]:
    total = Guiche.objects.count()
    if total == 0:
        return 0.0
    busy = Guiche.objects.filter(em_atendimento=True).count()
    return float(busy) / float(total)


def reanuncio_rate(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Optional[float]:
    s, e = _normalize_range(start, end)
    chamadas = Chamada.objects.filter(data_hora__range=(s, e))
    total = chamadas.count()
    if total == 0:
        return None
    reanuncios = chamadas.filter(acao="reanuncio").count()
    return float(reanuncios) / float(total)


def _wait_durations_seconds(
    start: Optional[datetime], end: Optional[datetime]
) -> List[float]:
    s, e = _normalize_range(start, end)
    qs = (
        Atendimento.objects.filter(data_hora__range=(s, e))
        .annotate(
            wait=ExpressionWrapper(
                F("data_hora") - F("paciente__horario_geracao_senha"),
                output_field=DurationField(),
            )
        )
        .values_list("wait", flat=True)
    )
    durations = []
    for td in qs:
        if td is None:
            continue
        try:
            durations.append(float(td.total_seconds()))
        except Exception as exc:  # log and continue on unexpected values
            logger.debug("skipping duration value: %r (%s)", td, exc)
            continue
    return durations


def median_wait_time(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> Optional[float]:
    secs = _wait_durations_seconds(start, end)
    if not secs:
        return None
    return float(statistics.median(secs))


def p95_wait_time(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> Optional[float]:
    secs = _wait_durations_seconds(start, end)
    if not secs:
        return None
    # approximate p95 using statistics.quantiles if available
    try:
        q = statistics.quantiles(secs, n=100)
        return float(q[94])
    except Exception:
        # fallback: sort and pick
        secs_sorted = sorted(secs)
        idx = int(0.95 * len(secs_sorted)) - 1
        idx = max(0, min(idx, len(secs_sorted) - 1))
        return float(secs_sorted[idx])


def average_service_time(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> Optional[float]:
    s, e = _normalize_range(start, end)
    atendimentos = Atendimento.objects.filter(data_hora__range=(s, e)).select_related(
        "paciente"
    )
    service_secs = []
    for at in atendimentos:
        last_call = (
            Chamada.objects.filter(
                paciente=at.paciente, acao="chamada", data_hora__lte=at.data_hora
            )
            .order_by("-data_hora")
            .first()
        )
        if last_call is None:
            continue
        delta = at.data_hora - last_call.data_hora
        if delta is None:
            continue
        service_secs.append(float(delta.total_seconds()))
    if not service_secs:
        return None
    return float(sum(service_secs) / len(service_secs))


def abandonment_rate(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> Optional[float]:
    s, e = _normalize_range(start, end)
    total_generated = Paciente.objects.filter(
        horario_geracao_senha__range=(s, e)
    ).count()
    if total_generated == 0:
        return None
    attended = Atendimento.objects.filter(data_hora__range=(s, e)).count()
    abandoned = max(0, total_generated - attended)
    return float(abandoned) / float(total_generated)


def scheduled_vs_walkin(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> Dict[str, int]:
    s, e = _normalize_range(start, end)
    qs = Paciente.objects.filter(horario_geracao_senha__range=(s, e))
    scheduled = qs.filter(horario_agendamento__isnull=False).count()
    walkin = qs.filter(horario_agendamento__isnull=True).count()
    total = scheduled + walkin
    return {"scheduled": scheduled, "walkin": walkin, "total": total}


def no_show_rate(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> Optional[float]:
    s, e = _normalize_range(start, end)
    scheduled_qs = Paciente.objects.filter(
        horario_geracao_senha__range=(s, e), horario_agendamento__isnull=False
    )
    scheduled = scheduled_qs.count()
    if scheduled == 0:
        return None
    # scheduled patients attended within window
    scheduled_attended = Atendimento.objects.filter(
        data_hora__range=(s, e), paciente__in=scheduled_qs
    ).count()
    no_show = max(0, scheduled - scheduled_attended)
    return float(no_show) / float(scheduled)


def sla_breach_count(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    sla_seconds: int = 1800,
) -> int:
    # Count atendimentos in range whose wait exceeded sla_seconds
    s, e = _normalize_range(start, end)
    qs = (
        Atendimento.objects.filter(data_hora__range=(s, e))
        .annotate(
            wait=ExpressionWrapper(
                F("data_hora") - F("paciente__horario_geracao_senha"),
                output_field=DurationField(),
            )
        )
        .values_list("wait", flat=True)
    )
    cnt = 0
    for td in qs:
        if td is None:
            continue
        try:
            if float(td.total_seconds()) > float(sla_seconds):
                cnt += 1
        except Exception as exc:
            logger.debug("skipping wait value in sla_breach_count: %r (%s)", td, exc)
            continue
    return cnt


def queue_breakdown_by_type() -> Dict[str, int]:
    # Simple breakdown: 'priority' == tipo_senha == 'A', others 'normal'
    qs = Paciente.objects.filter(atendido=False)
    priority = qs.filter(tipo_senha="A").count()
    normal = qs.exclude(tipo_senha="A").count()
    return {"priority": priority, "normal": normal}


def queue_stats(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> dict:
    s, e = _normalize_range(start, end)
    total_senhas = Paciente.objects.filter(horario_geracao_senha__range=(s, e)).count()
    total_atendimentos = Atendimento.objects.filter(data_hora__range=(s, e)).count()
    avg_td = average_wait_time(s, e)
    avg_seconds = None
    if avg_td is not None:
        avg_seconds = avg_td.total_seconds()

    throughput = []
    for x in throughput_by_day(s, e):
        throughput.append(
            {
                "day": x["day"].isoformat(),
                "count": x["count"],
            }
        )
    peaks: List[dict] = []
    # entries_by_day_hour left as optional detailed payload for dashboards
    rean_rate = reanuncio_rate(s, e)
    guiche_util = guiche_utilization(s, e)
    queue_len = current_queue_length()

    return {
        "total_senhas_generated": total_senhas,
        "total_atendimentos": total_atendimentos,
        "avg_wait_seconds": avg_seconds,
        "throughput": throughput,
        "peak_hours": peaks,
        "reanuncio_rate": rean_rate,
        "guiche_utilization": guiche_util,
        "current_queue_length": queue_len,
    }
