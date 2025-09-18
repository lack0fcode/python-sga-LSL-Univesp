# profissional_saude/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.models import ChamadaProfissional, CustomUser, Paciente
from core.utils import enviar_whatsapp  # Importe a função de utilidade


@login_required
def painel_profissional(request):
    """
    Painel do profissional de saúde.
    """
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
@csrf_exempt
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
        # Busca a sala do profissional que fez a chamada
        sala_consulta = (
            ultima_chamada.profissional_saude.sala
        )  # Acessa a sala através do profissional
        profissional_nome = ultima_chamada.profissional_saude.first_name

        # Pega as 5 chamadas mais recentes, excluindo a última chamada
        historico_chamadas = (
            ChamadaProfissional.objects.filter(acao__in=["chamada", "reanuncio"])
            .exclude(id=ultima_chamada.id)
            .order_by("-data_hora")[:5]
        )
    except ChamadaProfissional.DoesNotExist:
        senha_chamada = None
        nome_completo = None
        sala_consulta = None
        profissional_nome = None
        historico_chamadas = []

    context = {
        "senha_chamada": senha_chamada,
        "nome_completo": nome_completo,
        "sala_consulta": sala_consulta,
        "profissional_nome": profissional_nome,
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
        # Busca a sala do profissional que fez a chamada
        sala_consulta = (
            ultima_chamada.profissional_saude.sala
        )  # Acessa a sala através do profissional
        profissional_nome = ultima_chamada.profissional_saude.first_name
        chamada_id = ultima_chamada.id

        data = {
            "senha": senha,  # Envia a senha
            "nome_completo": nome_completo,
            "sala_consulta": sala_consulta,
            "profissional_nome": profissional_nome,
            "id": chamada_id,
        }
    except ChamadaProfissional.DoesNotExist:
        data = {
            "senha": "",
            "nome_completo": "",
            "sala_consulta": "",
            "profissional_nome": "",
            "id": "",
        }

    return JsonResponse(data)
