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
from core.forms import CadastrarFuncionarioForm
from core.models import CustomUser, RegistroDeAcesso  # Importe o modelo CustomUser


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
    usuarios_online_inativos_ids = []  # Amarelo: online mas inativo (2-10 min)
    usuarios_offline_ids = []  # Vermelho: offline (mais de 10 min)

    agora = timezone.now()
    dez_minutos_atras = agora - timezone.timedelta(minutes=10)
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

    # Usuários com atividade recente (qualquer tipo de acesso nos últimos 10 minutos)
    usuarios_com_atividade_recente = set(
        RegistroDeAcesso.objects.filter(data_hora__gte=dez_minutos_atras)
        .values_list("usuario_id", flat=True)
        .distinct()
    )

    # Combinar usuários com sessão ativa E atividade recente
    usuarios_online_potenciais = usuarios_com_sessao_ativa.union(
        usuarios_com_atividade_recente
    )

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
