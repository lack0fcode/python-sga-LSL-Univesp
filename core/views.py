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
                return redirect("pagina_inicial")
            else:
                logger.warning("Credenciais incorretas.")
                form.add_error(None, "CPF ou senha incorretos.")
        else:
            logger.warning("Formulário inválido.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


@login_required
def pagina_inicial(request):
    return render(request, "pagina_inicial.html")


@login_required
def logout_view(request):
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
