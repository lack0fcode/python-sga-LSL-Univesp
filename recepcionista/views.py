# recepcionista/views.py
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

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
            paciente = form.save()
            messages.success(
                request,
                f"Paciente {paciente.nome_completo} cadastrado com senha: {paciente.senha}!",
            )
            return redirect(reverse("recepcionista:cadastrar_paciente"))
        else:
            messages.error(
                request, "Erro ao cadastrar o paciente. Verifique os dados."
            )
    else:
        form = CadastrarPacienteForm(
            profissionais_de_saude=profissionais_de_saude
        )
    return render(
        request, "recepcionista/cadastrar_paciente.html", {"form": form}
    )
