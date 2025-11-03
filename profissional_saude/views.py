# profissional_saude/views.py
from typing import Any, Dict, List
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from core.decorators import profissional_saude_required
from core.models import ChamadaProfissional, CustomUser, Paciente
from core.utils import enviar_whatsapp  # Importe a função de utilidade

from .forms import SelecionarSalaForm


@login_required
@profissional_saude_required
def painel_profissional(request):
    """
    Painel do profissional de saúde.
    """
    # Verificar se o profissional tem sala atribuída
    if not request.user.sala:
        return redirect("profissional_saude:selecionar_sala")

    pacientes = Paciente.objects.filter(
        profissional_saude=request.user, atendido=True
    ).order_by("horario_agendamento")
    profissionais = CustomUser.objects.filter(funcao="profissional_saude").exclude(
        id=request.user.id
    )

    historico_chamadas = ChamadaProfissional.objects.filter(
        profissional_saude=request.user, acao__in=["chamada", "reanuncio"]
    ).order_by("-data_hora")[
        :10
    ]  # Últimas 10 chamadas

    context = {
        "pacientes": pacientes,
        "profissionais": profissionais,
        "historico_chamadas": historico_chamadas,
    }
    return render(request, "profissional_saude/painel_profissional.html", context)


@require_POST
@login_required
def realizar_acao_profissional(request, paciente_id, acao):
    """
    View para lidar com as ações do profissional de saúde:
    chamar, reanunciar, encaminhar e confirmar.
    """
    paciente = get_object_or_404(Paciente, id=paciente_id)
    profissional_saude = request.user

    if acao == "chamar":
        ChamadaProfissional.objects.create(
            paciente=paciente, profissional_saude=profissional_saude, acao="chamada"
        )

        # Tenta enviar mensagem via WhatsApp
        numero_celular_paciente = paciente.telefone_e164()
        if numero_celular_paciente:
            mensagem = (
                f"Olá {paciente.nome_completo.split()[0]}! "
                f"Seu atendimento com o(a) Dr(a). {profissional_saude.first_name} "
                f"na Sala {profissional_saude.sala} foi iniciado. Por favor, aguarde."
            )
            enviar_whatsapp(numero_celular_paciente, mensagem)
        else:
            print(
                f"Aviso: Não foi possível enviar WhatsApp para o paciente {paciente.nome_completo} (ID: {paciente_id}) - telefone inválido ou ausente."
            )

        return JsonResponse(
            {"status": "success", "mensagem": "Senha chamada com sucesso."}
        )
    elif acao == "reanunciar":
        ChamadaProfissional.objects.create(
            paciente=paciente, profissional_saude=profissional_saude, acao="reanuncio"
        )
        # Opcional: Reenviar o WhatsApp também no reanuncio?
        # numero_celular_paciente = paciente.telefone_e164()
        # if numero_celular_paciente:
        #     mensagem = (
        #         f"Olá {paciente.nome_completo.split()[0]}! "
        #         f"O(A) Dr(a). {profissional_saude.first_name} está chamando novamente. "
        #         f"Por favor, dirija-se à Sala {profissional_saude.sala}."
        #     )
        #     enviar_whatsapp(numero_celular_paciente, mensagem)
        # else:
        #     print(f"Aviso: Não foi possível enviar WhatsApp no reanuncio para o paciente {paciente.nome_completo} (ID: {paciente_id}) - telefone inválido ou ausente.")

        return JsonResponse(
            {"status": "success", "mensagem": "Senha reanunciada com sucesso."}
        )
    elif acao == "confirmar":
        paciente.atendido = False  # Marcar como não atendido para sair da lista
        paciente.save()
        return JsonResponse(
            {"status": "success", "mensagem": "Atendimento confirmado com sucesso."}
        )
    elif acao == "encaminhar":
        profissional_encaminhar_id = request.POST.get("profissional_encaminhar_id")
        if profissional_encaminhar_id:
            profissional_encaminhar = get_object_or_404(
                CustomUser, id=profissional_encaminhar_id
            )
            paciente.profissional_saude = profissional_encaminhar
            paciente.atendido = True  # Para aparecer na lista do outro profissional
            paciente.save()
            return JsonResponse(
                {
                    "status": "success",
                    "mensagem": f"Paciente encaminhado para {profissional_encaminhar.first_name} com sucesso.",
                }
            )
        else:
            return JsonResponse(
                {
                    "status": "error",
                    "mensagem": "Selecione um profissional para encaminhar.",
                },
                status=400,
            )
    else:
        return JsonResponse(
            {"status": "error", "mensagem": "Ação inválida."}, status=400
        )


@never_cache
def tv2_view(request):
    """
    View para exibir informações na TV2.
    """
    try:
        ultima_chamada = ChamadaProfissional.objects.filter(
            acao__in=["chamada", "reanuncio"]
        ).latest("data_hora")
        senha_chamada = ultima_chamada.paciente
        nome_completo = ultima_chamada.paciente.nome_completo
        # Busca o número da sala do profissional que fez a chamada
        sala_profissional = ultima_chamada.profissional_saude.sala

        # Pega as 5 confirmações mais recentes
        historico_chamadas = ChamadaProfissional.objects.filter(
            acao="confirmado"
        ).order_by("-data_hora")[:5]
    except ChamadaProfissional.DoesNotExist:
        senha_chamada = None
        nome_completo = None
        sala_profissional = None
        historico_chamadas = []

    context = {
        "senha_chamada": senha_chamada,
        "nome_completo": nome_completo,
        "sala_profissional": sala_profissional,
        "historico_senhas": historico_chamadas,
        "ultima_chamada": (
            ultima_chamada if senha_chamada else None
        ),  # Passa a última chamada para o template
    }
    return render(request, "profissional_saude/tv2.html", context)


def tv2_api_view(request):
    """
    API para fornecer dados atualizados para a TV2.
    """
    try:
        # Obtenha a última chamada feita por um profissional de saúde
        ultima_chamada = ChamadaProfissional.objects.filter(
            acao__in=["chamada", "reanuncio"]
        ).latest("data_hora")
        senha = ultima_chamada.paciente.senha  # Pega a senha
        nome_completo = ultima_chamada.paciente.nome_completo
        # Busca o número da sala do profissional que fez a chamada
        sala_profissional = ultima_chamada.profissional_saude.sala
        profissional_nome = (
            ultima_chamada.profissional_saude.get_full_name()
            or ultima_chamada.profissional_saude.username
        )
        chamada_id = ultima_chamada.id

        data = {
            "senha": senha,  # Envia a senha
            "nome_completo": nome_completo,
            "sala_profissional": sala_profissional,
            "profissional_nome": profissional_nome,
            "id": chamada_id,
        }
    except ChamadaProfissional.DoesNotExist:
        data = {
            "senha": "",
            "nome_completo": "",
            "sala_profissional": "",
            "profissional_nome": "",
            "id": "",
        }

    return JsonResponse(data)


def tv2_historico_api_view(request) -> JsonResponse:
    """API para obter apenas o histórico de confirmações da TV2"""
    try:
        # Obtém as últimas 5 confirmações
        historico_chamadas = (
            ChamadaProfissional.objects.filter(acao="confirmado")
            .select_related("paciente", "profissional_saude")
            .order_by("-data_hora")[:5]
        )

        historico_data: List[Dict[str, Any]] = []
        for chamada in historico_chamadas:
            historico_data.append(
                {
                    "id": chamada.id,
                    "paciente_nome": chamada.paciente.nome_completo,
                    "paciente_senha": chamada.paciente.senha,
                    "sala_profissional": chamada.profissional_saude.sala,
                    "data_hora": chamada.data_hora.strftime("%H:%M:%S"),
                }
            )

        data: Dict[str, Any] = {"historico": historico_data}
    except Exception as e:
        data = {"historico": [], "error": str(e)}

    return JsonResponse(data)


@login_required
@profissional_saude_required
def selecionar_sala(request):
    """
    View para o profissional de saúde selecionar sua sala.
    """
    if request.method == "POST":
        form = SelecionarSalaForm(request.POST)
        if form.is_valid():
            sala_numero = int(form.cleaned_data["sala"])

            # Verificar se outro profissional já está usando esta sala
            outro_profissional = (
                CustomUser.objects.filter(funcao="profissional_saude", sala=sala_numero)
                .exclude(id=request.user.id)
                .first()
            )

            if outro_profissional:
                # Sala já ocupada - mostrar erro
                from django.contrib import messages

                messages.error(
                    request,
                    f"A sala {sala_numero} já está sendo usada pelo profissional {outro_profissional.first_name} {outro_profissional.last_name}.",
                )
            else:
                # Sala disponível - salvar
                request.user.sala = sala_numero
                request.user.save()
                from django.contrib import messages

                messages.success(
                    request, f"Sala {sala_numero} selecionada com sucesso!"
                )
                return redirect("profissional_saude:painel_profissional")
    else:
        # Inicializar form com sala atual se existir
        initial = {}
        if request.user.sala:
            initial["sala"] = str(request.user.sala)
        form = SelecionarSalaForm(initial=initial)

    return render(request, "profissional_saude/selecionar_sala.html", {"form": form})
