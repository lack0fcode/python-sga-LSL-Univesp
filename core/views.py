# core/views.py
import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from core.models import RegistroDeAcesso

from .forms import LoginForm

logger = logging.getLogger(__name__)


def login_view(request):
    logger.info("A view de login foi chamada.")
    if request.method == "POST":
        form = LoginForm(request.POST)
        logger.debug("Form valid: %s", form.is_valid())
        logger.debug("Form errors: %s", form.errors)
        logger.debug("Form data: %s", form.data)
        logger.info("Formulário POST recebido.")
        if form.is_valid():
            cpf = form.cleaned_data["cpf"]
            password = form.cleaned_data["password"]
            logger.info(f"CPF: {cpf}, Tentando autenticar...")
            user = authenticate(request, username=cpf, password=password)
            if user is not None:
                logger.info(
                    f"Autenticação bem-sucedida para o usuário: {user.username}"
                )
                login(request, user)
                # Forçar redirecionamento baseado na função do usuário (mesmo para superusers)
                next_url = None
                if user.funcao == "administrador":
                    next_url = "administrador:listar_funcionarios"
                elif user.funcao == "recepcionista":
                    next_url = "recepcionista:cadastrar_paciente"
                elif user.funcao == "guiche":
                    next_url = "guiche:selecionar_guiche"
                elif user.funcao == "profissional_saude":
                    if user.sala:
                        next_url = "profissional_saude:painel_profissional"
                    else:
                        next_url = "profissional_saude:selecionar_sala"
                else:
                    next_url = "pagina_inicial"

                if next_url:
                    return redirect(next_url)
                else:
                    return redirect("pagina_inicial")
            else:
                logger.warning("Autenticação falhou para CPF: %s", cpf)
                form.add_error(None, "CPF ou senha incorretos.")
        else:
            logger.debug("Form inválido: %s", form.errors)
            form.add_error(None, "Dados inválidos. Verifique o CPF.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


@login_required
def pagina_inicial(request):
    return render(request, "pagina_inicial.html")


@login_required
def logout_view(request):
    # Liberar guichê se o usuário for do tipo guiche
    if hasattr(request.user, "funcao") and request.user.funcao == "guiche":
        guiche_id = request.session.get("guiche_id")
        if guiche_id:
            try:
                from core.models import Guiche

                guiche = Guiche.objects.get(id=guiche_id)
                guiche.funcionario = None
                guiche.save()
            except Guiche.DoesNotExist:
                pass
    RegistroDeAcesso.objects.create(
        usuario=request.user,
        tipo_de_acesso="logout",
        endereco_ip=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT"),
        view_name=(
            request.resolver_match.view_name
            if request.resolver_match
            else "URL não encontrada"
        ),
        data_hora=timezone.now(),
    )
    logout(request)
    return redirect("login")  # Redireciona para a página de login
