# recepcionista/views.py
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from core.decorators import recepcionista_required
from core.forms import CadastrarPacienteForm
from core.models import CustomUser  # Importe o modelo CustomUser


@recepcionista_required
def cadastrar_paciente(request):
    profissionais_de_saude = CustomUser.objects.filter(
        funcao="profissional_saude"
    )  # Filtrando o select com o tipo do usuário
    if request.method == "POST":
        form = CadastrarPacienteForm(
            request.POST, profissionais_de_saude=profissionais_de_saude
        )
        if form.is_valid():
            paciente = form.save(commit=False)

            # Usar o horário de agendamento (escolhido pelo recepcionista)
            # nas observações; se não existir, cair para hora de entrada.
            horario_atendimento = paciente.horario_agendamento
            observacoes_existentes = paciente.observacoes or ""

            # Se já existe paciente cadastrado com o mesmo Cartão SUS,
            # assumimos que é um retorno e registramos apenas a hora de entrada.
            from core.models import Paciente as _Paciente

            is_returning = False
            if paciente.cartao_sus:
                is_returning = _Paciente.objects.filter(
                    cartao_sus=paciente.cartao_sus
                ).exists()

            # Calcular hora de entrada sempre (usado tanto para retorno quanto
            # para registrar o horário local do cadastro)
            br_tz = ZoneInfo("America/Sao_Paulo")
            hora_entrada = timezone.localtime(timezone.now(), br_tz).strftime("%H:%M")

            if horario_atendimento and not is_returning:
                # Formata data e hora do agendamento e também inclui a hora de
                # entrada para compatibilidade com os relatórios.
                try:
                    formatted = horario_atendimento.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    # Caso venha em outro formato, usa str()
                    formatted = str(horario_atendimento)
                novo_texto = f"Horário do atendimento: {formatted}\nHora de entrada: {hora_entrada}"
            else:
                novo_texto = f"Hora de entrada: {hora_entrada}"

            if observacoes_existentes.strip():
                paciente.observacoes = f"{observacoes_existentes}\n{novo_texto}"
            else:
                paciente.observacoes = novo_texto

            paciente.save()

            messages.success(
                request,
                f"Paciente {paciente.nome_completo} cadastrado com senha: {paciente.senha}!",
            )
            return redirect(reverse("recepcionista:cadastrar_paciente"))
        else:
            messages.error(request, "Erro ao cadastrar o paciente. Verifique os dados.")
    else:
        form = CadastrarPacienteForm(profissionais_de_saude=profissionais_de_saude)
    return render(request, "recepcionista/cadastrar_paciente.html", {"form": form})
