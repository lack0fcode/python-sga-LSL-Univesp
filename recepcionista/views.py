# recepcionista/views.py
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from zoneinfo import ZoneInfo

from core.decorators import recepcionista_required
from core.forms import CadastrarPacienteForm
from core.models import CustomUser, Paciente  # Importe os modelos necessários


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

            # Normalizar cartão SUS (remover espaços) para buscas e para salvar
            paciente.cartao_sus = (paciente.cartao_sus or "").strip()

            # Preparar texto de observações (agendamento ou hora de entrada)
            horario_atendimento = paciente.horario_agendamento
            observacoes_existentes = paciente.observacoes or ""

            if horario_atendimento:
                try:
                    formatted = horario_atendimento.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    formatted = str(horario_atendimento)
                novo_texto = f"Horário do atendimento: {formatted}"
            else:
                br_tz = ZoneInfo("America/Sao_Paulo")
                hora_entrada = timezone.localtime(timezone.now(), br_tz).strftime(
                    "%H:%M"
                )
                novo_texto = f"Hora de entrada: {hora_entrada}"

            # Não persistir ainda; concatena nas observações do objeto candidato
            if observacoes_existentes.strip():
                paciente.observacoes = f"{observacoes_existentes}\n{novo_texto}"
            else:
                paciente.observacoes = novo_texto

            # Lookup por cartão SUS primeiro (quando informado), depois por telefone
            paciente_usado = None
            cartao = (paciente.cartao_sus or "").strip()
            if cartao:
                qs = Paciente.objects.filter(cartao_sus__iexact=cartao).order_by(
                    "-horario_agendamento", "-id"
                )
                if qs.exists():
                    existente = qs.first()
                    if paciente.nome_completo:
                        existente.nome_completo = paciente.nome_completo
                    existente.tipo_senha = paciente.tipo_senha or existente.tipo_senha
                    existente.profissional_saude = (
                        paciente.profissional_saude or existente.profissional_saude
                    )
                    # Substitui observações antigas: usa as observações submetidas agora
                    # seguidas do texto gerado (agendamento/hora de entrada).
                    if paciente.observacoes and paciente.observacoes.strip():
                        new_obs = f"{paciente.observacoes.strip()}\n{novo_texto}"
                    else:
                        new_obs = novo_texto
                    existente.observacoes = new_obs[:255]
                    if paciente.telefone_celular:
                        existente.telefone_celular = paciente.telefone_celular
                    existente.horario_agendamento = (
                        paciente.horario_agendamento or existente.horario_agendamento
                    )
                    # Forçar nova geração de senha: limpa a senha atual e atualiza horario_geracao_senha
                    from django.utils import timezone as _tz

                    existente.senha = None
                    existente.horario_geracao_senha = _tz.now()
                    # Garantir que paciente reapareça na fila ao recadastrar
                    existente.atendido = False
                    existente.save()
                    paciente_usado = existente

            if not paciente_usado:
                tel = (paciente.telefone_celular or "").strip()
                if tel:
                    qs = Paciente.objects.filter(telefone_celular=tel).order_by(
                        "-horario_agendamento", "-id"
                    )
                    if qs.exists():
                        existente = qs.first()
                        if paciente.nome_completo:
                            existente.nome_completo = paciente.nome_completo
                        existente.tipo_senha = (
                            paciente.tipo_senha or existente.tipo_senha
                        )
                        existente.profissional_saude = (
                            paciente.profissional_saude or existente.profissional_saude
                        )
                        if paciente.observacoes and paciente.observacoes.strip():
                            new_obs = f"{paciente.observacoes.strip()}\n{novo_texto}"
                        else:
                            new_obs = novo_texto
                        existente.observacoes = new_obs[:255]
                        existente.horario_agendamento = (
                            paciente.horario_agendamento
                            or existente.horario_agendamento
                        )
                        # Forçar nova geração de senha ao re-cadastrar
                        from django.utils import timezone as _tz

                        existente.senha = None
                        existente.horario_geracao_senha = _tz.now()
                        # Garantir que paciente reapareça na fila ao recadastrar
                        existente.atendido = False
                        existente.save()
                        paciente_usado = existente

            # Se não encontrou nenhum existente, cria novo registro
            if not paciente_usado:
                paciente.save()
                paciente_usado = paciente

            messages.success(
                request,
                f"Paciente {paciente_usado.nome_completo} cadastrado com senha: {paciente_usado.senha}!",
            )
            return redirect(reverse("recepcionista:cadastrar_paciente"))
        else:
            messages.error(request, "Erro ao cadastrar o paciente. Verifique os dados.")
    else:
        form = CadastrarPacienteForm(profissionais_de_saude=profissionais_de_saude)
    return render(request, "recepcionista/cadastrar_paciente.html", {"form": form})
