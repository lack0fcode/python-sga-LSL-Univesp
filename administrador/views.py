# administrador/views.py
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from core.decorators import admin_required
from core.forms import CadastrarFuncionarioForm, EditarFuncionarioForm
from core.models import CustomUser,Paciente, Chamada, ChamadaProfissional, RegistroDeAcesso  # Importe o modelo CustomUser
from django.contrib.auth.forms import SetPasswordForm

from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncHour
from datetime import timedelta
import json
 
@admin_required
def cadastrar_funcionario(request):
    if request.method == "POST":
        form = CadastrarFuncionarioForm(request.POST)
        if form.is_valid():
            user = form.save()
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
@csrf_exempt
def registrar_atividade(request):
    """View para registrar atividade do usuário em tempo real"""
    if request.method == "POST":
        # Registrar atividade no banco de dados
        RegistroDeAcesso.objects.create(
            usuario=request.user, tipo_de_acesso="atividade", data_hora=timezone.now()
        )
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)


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
        except:
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


@admin_required
def dashboard(request):
    hoje = timezone.now().date()
    ultimos_7_dias = timezone.now() - timedelta(days=7)
    ultimos_30_dias = timezone.now() - timedelta(days=30)
 
    # ── BLOCO 1: VISÃO GERAL DO DIA ──────────────────────────────────────────
    pacientes_hoje = Paciente.objects.filter(horario_geracao_senha__date=hoje)
    total_pacientes_hoje = pacientes_hoje.count()
    total_atendidos_hoje = pacientes_hoje.filter(atendido=True).count()
    total_aguardando = pacientes_hoje.filter(atendido=False).count()
    taxa_atendimento_hoje = (
        round((total_atendidos_hoje / total_pacientes_hoje) * 100, 1)
        if total_pacientes_hoje > 0 else 0
    )
 
    # ── BLOCO 2: TEMPO MÉDIO DE ESPERA ───────────────────────────────────────
    # horario_geracao_senha -> primeira chamada no guiche
    chamadas_recentes = (
        Chamada.objects
        .filter(acao="chamada", data_hora__gte=ultimos_30_dias)
        .select_related("paciente")
        .order_by("paciente_id", "data_hora")
    )
    visto = set()
    tempos_espera = []
    tempos_espera_hoje = []
    for c in chamadas_recentes:
        if c.paciente_id in visto:
            continue
        visto.add(c.paciente_id)
        if c.paciente.horario_geracao_senha:
            minutos = (c.data_hora - c.paciente.horario_geracao_senha).total_seconds() / 60
            if 0 < minutos < 480:
                tempos_espera.append(minutos)
                if c.data_hora.date() == hoje:
                    tempos_espera_hoje.append(minutos)
 
    tempo_medio_espera = round(sum(tempos_espera) / len(tempos_espera), 1) if tempos_espera else 0
    tempo_medio_espera_hoje = round(sum(tempos_espera_hoje) / len(tempos_espera_hoje), 1) if tempos_espera_hoje else 0
 
    # ── BLOCO 3: TEMPO MÉDIO DE ATENDIMENTO NO GUICHE ────────────────────────
    # chamada -> confirmado no guiche
    tempos_guiche = []
    for conf in Chamada.objects.filter(acao="confirmado", data_hora__gte=ultimos_30_dias).select_related("paciente"):
        chamada_ini = (
            Chamada.objects
            .filter(paciente=conf.paciente, acao="chamada", data_hora__lt=conf.data_hora)
            .order_by("data_hora").first()
        )
        if chamada_ini:
            minutos = (conf.data_hora - chamada_ini.data_hora).total_seconds() / 60
            if 0 < minutos < 240:
                tempos_guiche.append(minutos)
 
    tempo_medio_guiche = round(sum(tempos_guiche) / len(tempos_guiche), 1) if tempos_guiche else 0
 
    # ── BLOCO 4: TEMPO MÉDIO DE CONSULTA COM PROFISSIONAL ────────────────────
    tempos_consulta = []
    for conf in ChamadaProfissional.objects.filter(acao="confirmado", data_hora__gte=ultimos_30_dias).select_related("paciente"):
        chamada_ini = (
            ChamadaProfissional.objects
            .filter(paciente=conf.paciente, acao="chamada", data_hora__lt=conf.data_hora)
            .order_by("data_hora").first()
        )
        if chamada_ini:
            minutos = (conf.data_hora - chamada_ini.data_hora).total_seconds() / 60
            if 0 < minutos < 480:
                tempos_consulta.append(minutos)
 
    tempo_medio_consulta = round(sum(tempos_consulta) / len(tempos_consulta), 1) if tempos_consulta else 0
 
    # ── BLOCO 5: VOLUME POR TIPO DE SERVICO ──────────────────────────────────
    volume_por_tipo = (
        Paciente.objects.filter(horario_geracao_senha__gte=ultimos_30_dias)
        .values("tipo_senha").annotate(total=Count("id")).order_by("-total")
    )
    tipo_display = dict(Paciente.SENHA_CHOICES)
    tipo_labels = [tipo_display.get(i["tipo_senha"], i["tipo_senha"] or "Sem tipo") for i in volume_por_tipo]
    tipo_data = [i["total"] for i in volume_por_tipo]
 
    # ── BLOCO 6: ATENDIMENTOS POR PROFISSIONAL ───────────────────────────────
    por_prof = (
        ChamadaProfissional.objects
        .filter(acao="confirmado", data_hora__gte=ultimos_30_dias)
        .values("profissional_saude__first_name", "profissional_saude__last_name")
        .annotate(total=Count("id")).order_by("-total")
    )
    prof_labels = [
        f"{i['profissional_saude__first_name']} {i['profissional_saude__last_name']}".strip()
        for i in por_prof
    ]
    prof_data = [i["total"] for i in por_prof]
 
    # ── BLOCO 7: TENDENCIA 14 DIAS ───────────────────────────────────────────
    tendencia = (
        Paciente.objects.filter(horario_geracao_senha__gte=timezone.now() - timedelta(days=14))
        .annotate(dia=TruncDate("horario_geracao_senha"))
        .values("dia")
        .annotate(total=Count("id"), atendidos=Count("id", filter=Q(atendido=True)))
        .order_by("dia")
    )
    tendencia_labels = [i["dia"].strftime("%d/%m") for i in tendencia]
    tendencia_total = [i["total"] for i in tendencia]
    tendencia_atendidos = [i["atendidos"] for i in tendencia]
 
    # ── BLOCO 8: PICO DE DEMANDA POR HORA ────────────────────────────────────
    por_hora_qs = (
        Paciente.objects.filter(horario_geracao_senha__gte=ultimos_7_dias)
        .annotate(hora=TruncHour("horario_geracao_senha"))
        .values("hora").annotate(total=Count("id"))
    )
    hora_data_raw = {}
    for item in por_hora_qs:
        h = timezone.localtime(item["hora"]).strftime("%Hh")
        hora_data_raw[h] = hora_data_raw.get(h, 0) + item["total"]
 
    hora_labels = [f"{h:02d}h" for h in range(6, 21)]
    hora_data = [hora_data_raw.get(k, 0) for k in hora_labels]
 
    # ── BLOCO 9: INDICADORES DE QUALIDADE ────────────────────────────────────
    total_chamadas = Chamada.objects.filter(data_hora__gte=ultimos_30_dias).count()
    total_reanuncios = Chamada.objects.filter(acao="reanuncio", data_hora__gte=ultimos_30_dias).count()
    taxa_reanuncio = round((total_reanuncios / total_chamadas) * 100, 1) if total_chamadas > 0 else 0
 
    total_encaminhamentos = ChamadaProfissional.objects.filter(acao="encaminha", data_hora__gte=ultimos_30_dias).count()
    total_conf_prof = ChamadaProfissional.objects.filter(acao="confirmado", data_hora__gte=ultimos_30_dias).count()
    base_enc = total_conf_prof + total_encaminhamentos
    taxa_encaminhamento = round((total_encaminhamentos / base_enc) * 100, 1) if base_enc > 0 else 0
 
    # ── BLOCO 10: EQUIPE ATIVA HOJE ──────────────────────────────────────────
    profissionais_ativos = (
        RegistroDeAcesso.objects
        .filter(data_hora__date=hoje, tipo_de_acesso="login", usuario__funcao="profissional_saude")
        .values("usuario_id").distinct().count()
    )
    guichistas_ativos = (
        RegistroDeAcesso.objects
        .filter(data_hora__date=hoje, tipo_de_acesso="login", usuario__funcao="guiche")
        .values("usuario_id").distinct().count()
    )
 
    # ── BLOCO 11: TOP 5 REANUNCIOS HOJE ──────────────────────────────────────
    top_reanuncios = (
        Chamada.objects.filter(acao="reanuncio", data_hora__date=hoje)
        .values("paciente__nome_completo", "paciente__senha", "paciente__tipo_senha")
        .annotate(total=Count("id")).order_by("-total")[:5]
    )
 
    context = {
        "total_pacientes_hoje": total_pacientes_hoje,
        "total_atendidos_hoje": total_atendidos_hoje,
        "total_aguardando": total_aguardando,
        "taxa_atendimento_hoje": taxa_atendimento_hoje,
        "profissionais_ativos": profissionais_ativos,
        "guichistas_ativos": guichistas_ativos,
        "tempo_medio_espera": tempo_medio_espera,
        "tempo_medio_espera_hoje": tempo_medio_espera_hoje,
        "tempo_medio_guiche": tempo_medio_guiche,
        "tempo_medio_consulta": tempo_medio_consulta,
        "taxa_reanuncio": taxa_reanuncio,
        "taxa_encaminhamento": taxa_encaminhamento,
        "tipo_labels": json.dumps(tipo_labels, ensure_ascii=False),
        "tipo_data": json.dumps(tipo_data),
        "prof_labels": json.dumps(prof_labels, ensure_ascii=False),
        "prof_data": json.dumps(prof_data),
        "tendencia_labels": json.dumps(tendencia_labels),
        "tendencia_total": json.dumps(tendencia_total),
        "tendencia_atendidos": json.dumps(tendencia_atendidos),
        "hora_labels": json.dumps(hora_labels),
        "hora_data": json.dumps(hora_data),
        "top_reanuncios": top_reanuncios,
        "data_hoje": hoje,
    }
 
    return render(request, "administrador/dashboard.html", context)