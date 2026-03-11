# administrador/views.py
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.http import require_POST

from django.contrib.auth.forms import SetPasswordForm

from core.decorators import admin_required
from core.forms import CadastrarFuncionarioForm, EditarFuncionarioForm
from core.models import (
    Atendimento,  # Importe os modelos necessários
    Chamada,
    CustomUser,
    Guiche,
    Paciente,
    RegistroDeAcesso,
)

from administrador.analytics.service import (
    average_wait_time,
    peak_hours,
    entries_by_hour,
    entries_by_day_hour,
    reanuncio_rate,
    throughput_by_day,
    queue_stats,
)
from administrador.analytics.dashboards import dashboard_overview

logger = logging.getLogger(__name__)


@admin_required
def cadastrar_funcionario(request):
    if request.method == "POST":
        form = CadastrarFuncionarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Funcionário cadastrado com sucesso!")
            return redirect(
                reverse("administrador:listar_funcionarios")
            )  # Redireciona para a lista de funcionários
        else:
            messages.error(
                request, "Erro ao cadastrar o funcionário. Verifique os dados."
            )
    else:
        form = CadastrarFuncionarioForm()
    return render(request, "administrador/cadastrar_funcionario.html", {"form": form})


@login_required
@require_POST
def registrar_atividade(request):
    """View para registrar atividade do usuário em tempo real.

    Protected by CSRF (default) and requires POST. Clients must include the
    CSRF token when sending the request.
    """
    # Registrar atividade no banco de dados
    RegistroDeAcesso.objects.create(
        usuario=request.user,
        tipo_de_acesso="atividade",
        data_hora=timezone.now(),
    )
    return JsonResponse({"status": "ok"})


@admin_required
def listar_funcionarios(request):
    # Obter parâmetro de filtro da função
    funcao_filtro = request.GET.get("funcao", "")

    # Filtrar funcionários baseado na função selecionada
    if funcao_filtro:
        funcionarios = CustomUser.objects.filter(funcao=funcao_filtro)
    else:
        funcionarios = CustomUser.objects.all()  # Obtém todos os usuários

    # Calcular estatísticas
    total_funcionarios = funcionarios.count()
    funcionarios_ativos = funcionarios.filter(is_active=True).count()

    # Calcular status dos funcionários com três categorias
    usuarios_online_ativos_ids = []  # Verde: online e ativo (últimos 2 min)
    usuarios_online_inativos_ids = []  # Amarelo: online mas inativo (2-5 min)
    usuarios_offline_ids = []  # Vermelho: offline (mais de 5 min)

    agora = timezone.now()
    cinco_minutos_atras = agora - timezone.timedelta(minutes=5)
    dois_minutos_atras = agora - timezone.timedelta(minutes=2)

    # Obter sessões ativas (não expiradas)
    sessoes_ativas = Session.objects.filter(expire_date__gt=agora)
    usuarios_com_sessao_ativa = set()

    for sessao in sessoes_ativas:
        try:
            dados_sessao = sessao.get_decoded()
            user_id = dados_sessao.get("_auth_user_id")
            if user_id:
                usuarios_com_sessao_ativa.add(int(user_id))
        except Exception as e:
            logger.exception("Erro decodificando sessão: %s", e)
            continue

    # Usuários com atividade recente (nos últimos 5 minutos)
    usuarios_com_atividade_recente = set(
        RegistroDeAcesso.objects.filter(data_hora__gte=cinco_minutos_atras)
        .values_list("usuario_id", flat=True)
        .distinct()
    )

    # Usuários realmente online: apenas aqueles com atividade nos últimos 10 minutos
    # (removendo a dependência de sessões ativas que podem durar semanas)
    usuarios_online_potenciais = usuarios_com_atividade_recente

    # Para cada funcionário, determinar seu status
    for usuario in funcionarios:
        if usuario.id in usuarios_online_potenciais:
            # Verificar se teve atividade muito recente (nos últimos 2 minutos)
            atividade_muito_recente = RegistroDeAcesso.objects.filter(
                usuario=usuario, data_hora__gte=dois_minutos_atras
            ).exists()

            if atividade_muito_recente:
                usuarios_online_ativos_ids.append(usuario.id)
            else:
                usuarios_online_inativos_ids.append(usuario.id)
        else:
            usuarios_offline_ids.append(usuario.id)

    # Manter compatibilidade com código existente
    usuarios_online_ids = usuarios_online_ativos_ids + usuarios_online_inativos_ids
    # Atualizar estatísticas
    funcionarios_online_ativos = len(usuarios_online_ativos_ids)
    funcionarios_online_inativos = len(usuarios_online_inativos_ids)
    funcionarios_offline = len(usuarios_offline_ids)

    # Manter compatibilidade - total online = ativos + inativos
    funcionarios_online = funcionarios_online_ativos + funcionarios_online_inativos

    funcoes_distintas = funcionarios.values("funcao").distinct().count()

    # Obter todas as funções disponíveis para o filtro
    funcoes_disponiveis = CustomUser.FUNCAO_CHOICES

    return render(
        request,
        "administrador/listar_funcionarios.html",
        {
            "funcionarios": funcionarios,
            "total_funcionarios": total_funcionarios,
            "funcionarios_ativos": funcionarios_ativos,
            "funcionarios_online": funcionarios_online,
            "funcionarios_online_ativos": funcionarios_online_ativos,
            "funcionarios_online_inativos": funcionarios_online_inativos,
            "funcionarios_offline": funcionarios_offline,
            "usuarios_online_ids": usuarios_online_ids,
            "usuarios_online_ativos_ids": usuarios_online_ativos_ids,
            "usuarios_online_inativos_ids": usuarios_online_inativos_ids,
            "usuarios_offline_ids": usuarios_offline_ids,
            "funcoes_distintas": funcoes_distintas,
            "funcoes_disponiveis": funcoes_disponiveis,
            "funcao_filtro": funcao_filtro,
        },
    )


@admin_required
def dashboard_analise(request):
    """Página de análise de dados — acesso restrito a administradores."""
    # default range: last 14 days
    hoje = timezone.localdate()
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=14)
    overview = dashboard_overview(start_dt, end_dt)
    # keep compatibility with existing templates/tests expecting daily quick KPIs
    total_senhas_geradas_hoje = Paciente.objects.filter(
        horario_geracao_senha__date=hoje
    ).count()
    total_atendimentos_hoje = Atendimento.objects.filter(data_hora__date=hoje).count()

    context = {
        "overview": overview,
        "range_start": start_dt,
        "range_end": end_dt,
        "total_senhas_geradas_hoje": total_senhas_geradas_hoje,
        "total_atendimentos_hoje": total_atendimentos_hoje,
    }
    return render(request, "administrador/dashboard_modern.html", context)


@admin_required
def dashboard_analise_api(request):
    """Retorna métricas básicas em JSON para alimentar o frontend do dashboard."""
    # allow client to pass start/end ISO params; default last 14 days
    start_dt, end_dt = _parse_date_range(request, default_days=14)
    overview = dashboard_overview(start_dt, end_dt)
    # ensure date objects are serialized to ISO strings within throughput
    if overview.get("throughput"):
        for d in overview["throughput"]:
            if isinstance(d.get("day"), (datetime,)):
                d["day"] = d["day"].isoformat()
    return JsonResponse(overview)


@admin_required
def kpi_metrics_fragment(request):
    """Retorna um fragmento HTML com os KPIs básicos (usado por HTMX)."""
    # Default to "since UP" unless the UI provides a start param
    start_dt, end_dt = _parse_date_range(request, default_days=None)
    stats = queue_stats(start_dt, end_dt)
    # today's quick KPIs for default fallbacks in the fragment template
    hoje = timezone.localdate()
    total_senhas_geradas_hoje = Paciente.objects.filter(
        horario_geracao_senha__date=hoje
    ).count()
    total_atendimentos_hoje = Atendimento.objects.filter(data_hora__date=hoje).count()
    chamadas_hoje = Chamada.objects.filter(data_hora__date=hoje)
    reanuncios_hoje = chamadas_hoje.filter(acao="reanuncio").count()
    avg_wait_seconds = stats.get("avg_wait_seconds")
    avg_wait_minutes = None
    if avg_wait_seconds is not None:
        try:
            avg_wait_minutes = float(avg_wait_seconds) / 60.0
        except Exception:
            avg_wait_minutes = None

    guiche_util = stats.get("guiche_utilization")
    guiche_util_percent = None
    if guiche_util is not None:
        try:
            guiche_util_percent = float(guiche_util) * 100.0
        except Exception:
            guiche_util_percent = None

    context = {
        "total_senhas_geradas": stats.get("total_senhas_generated"),
        "total_senhas_geradas_hoje": total_senhas_geradas_hoje,
        "total_atendimentos": stats.get("total_atendimentos"),
        "total_atendimentos_hoje": total_atendimentos_hoje,
        "avg_wait_seconds": avg_wait_seconds,
        "avg_wait_minutes": avg_wait_minutes,
        "throughput": stats.get("throughput"),
        "peak_hours": stats.get("peak_hours"),
        "reanuncios": stats.get("reanuncio_rate"),
        "guiches_em_atendimento": Guiche.objects.filter(em_atendimento=True).count(),
        "guiches_total": Guiche.objects.count(),
        "guiche_utilization": guiche_util,
        "guiche_util_percent": guiche_util_percent,
        "current_queue_length": stats.get("current_queue_length"),
        "range_start": start_dt,
        "range_end": end_dt,
        "total_chamadas_hoje": chamadas_hoje.count(),
        "reanuncios_hoje": reanuncios_hoje,
    }

    return render(request, "administrador/_kpi_metrics.html", context)


def _parse_date_range(
    request, default_days: int | None = 7
) -> tuple[datetime | None, datetime]:
    """Parseia parâmetros GET `start` e `end` em ISO ou retorna range padrão."""
    end = request.GET.get("end")
    start = request.GET.get("start")
    start_dt: datetime | None = None
    if end:
        try:
            end_dt = datetime.fromisoformat(end)
        except Exception:
            end_dt = datetime.now()
    else:
        end_dt = datetime.now()

    if start:
        try:
            start_dt = datetime.fromisoformat(start)
        except Exception:
            start_dt = (
                None if default_days is None else end_dt - timedelta(days=default_days)
            )
    else:
        start_dt = (
            None if default_days is None else end_dt - timedelta(days=default_days)
        )

    return start_dt, end_dt


@admin_required
def kpi_throughput(request):
    start_dt, end_dt = _parse_date_range(request, default_days=14)
    qs = throughput_by_day(start_dt, end_dt)
    data = [{"day": obj["day"].isoformat(), "count": obj["count"]} for obj in qs]
    return JsonResponse({"throughput": data})


@admin_required
def kpi_avg_wait(request):
    start_dt, end_dt = _parse_date_range(request, default_days=7)
    avg = average_wait_time(start_dt, end_dt)
    # avg may be timedelta or None
    avg_seconds = None
    if avg is not None:
        avg_seconds = avg.total_seconds()
    return JsonResponse({"avg_wait_seconds": avg_seconds})


@admin_required
def kpi_peak_hours(request):
    start_dt, end_dt = _parse_date_range(request, default_days=7)
    qs = peak_hours(start_dt, end_dt)
    data = [{"hour": obj["hour"], "count": obj["count"]} for obj in qs]
    return JsonResponse({"peak_hours": data})


@admin_required
def kpi_entries_by_hour(request):
    """Return hourly time-series counts for the given range (used for temporal charts)."""
    start_dt, end_dt = _parse_date_range(request, default_days=7)
    qs = entries_by_hour(start_dt, end_dt)
    data = [{"hour": obj["hour"], "count": obj["count"]} for obj in qs]
    return JsonResponse({"entries_by_hour": data})


@admin_required
def kpi_entries_by_day_hour(request):
    """Return day/hour counts for heatmap display."""
    start_dt, end_dt = _parse_date_range(request, default_days=14)
    qs = entries_by_day_hour(start_dt, end_dt)
    return JsonResponse({"entries_by_day_hour": qs})


@admin_required
def kpi_queue_length(request):
    start_dt, end_dt = _parse_date_range(request, default_days=None)
    stats = queue_stats(start_dt, end_dt)
    return JsonResponse({"queue_length": stats.get("current_queue_length")})


@admin_required
def kpi_guiche_utilization(request):
    start_dt, end_dt = _parse_date_range(request, default_days=None)
    stats = queue_stats(start_dt, end_dt)
    return JsonResponse({"guiche_utilization": stats.get("guiche_utilization")})


@admin_required
def kpi_queue_fragment(request):
    """Fragmento HTML com o tamanho atual da fila."""
    start_dt, end_dt = _parse_date_range(request, default_days=None)
    stats = queue_stats(start_dt, end_dt)
    return render(
        request,
        "administrador/_queue_length.html",
        {
            "queue_length": stats.get("current_queue_length"),
            "range_start": start_dt,
            "range_end": end_dt,
        },
    )


@admin_required
def kpi_guiche_fragment(request):
    """Fragmento HTML com a utilização dos guichês."""
    start_dt, end_dt = _parse_date_range(request, default_days=None)
    stats = queue_stats(start_dt, end_dt)
    return render(
        request,
        "administrador/_guiche_util.html",
        {
            "guiche_utilization": stats.get("guiche_utilization"),
            "range_start": start_dt,
            "range_end": end_dt,
        },
    )


@admin_required
def kpi_reanuncio_rate(request):
    start_dt, end_dt = _parse_date_range(request, default_days=7)
    rate = reanuncio_rate(start_dt, end_dt)
    return JsonResponse({"reanuncio_rate": rate})


@admin_required
def editar_funcionario(request, pk):
    funcionario = get_object_or_404(CustomUser, pk=pk)
    if request.method == "POST":
        form = CadastrarFuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            messages.success(request, "Funcionário atualizado com sucesso!")
            return redirect(reverse("administrador:listar_funcionarios"))
        else:
            messages.error(
                request, "Erro ao atualizar o funcionário. Verifique os dados."
            )
    else:
        form = CadastrarFuncionarioForm(instance=funcionario)
    return render(request, "administrador/cadastrar_funcionario.html", {"form": form})


@admin_required
def excluir_funcionario(request, pk):
    funcionario = get_object_or_404(CustomUser, pk=pk)
    funcionario.delete()
    messages.success(request, "Funcionário excluído com sucesso!")
    return redirect(reverse("administrador:listar_funcionarios"))


@admin_required
def alterar_senha_funcionario(request, pk):
    funcionario = get_object_or_404(CustomUser, pk=pk)
    if request.method == "POST":
        form = SetPasswordForm(funcionario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Senha alterada com sucesso para o funcionário.")
            return redirect(reverse("administrador:listar_funcionarios"))
        else:
            messages.error(request, "Erro ao alterar a senha. Verifique os dados.")
    else:
        form = SetPasswordForm(funcionario)

    return render(
        request,
        "administrador/alterar_senha_funcionario.html",
        {"form": form, "funcionario": funcionario},
    )


@admin_required
def editar_dados_funcionario(request, pk):
    funcionario = get_object_or_404(CustomUser, pk=pk)
    if request.method == "POST":
        form = EditarFuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            messages.success(request, "Dados do funcionário atualizados com sucesso!")
            return redirect(reverse("administrador:listar_funcionarios"))
        else:
            messages.error(request, "Erro ao atualizar os dados. Verifique os campos.")
    else:
        form = EditarFuncionarioForm(instance=funcionario)

    return render(
        request,
        "administrador/editar_dados_funcionario.html",
        {"form": form, "funcionario": funcionario},
    )
