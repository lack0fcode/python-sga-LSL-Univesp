# core/decorators.py
from functools import wraps

from django.shortcuts import redirect


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and request.user.funcao == "administrador"
        ):
            return view_func(request, *args, **kwargs)
        else:
            return redirect(
                "pagina_inicial"
            )  # Redireciona para a página inicial ou exibe uma mensagem de erro

    return _wrapped_view


def recepcionista_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and request.user.funcao == "recepcionista"
        ):
            return view_func(request, *args, **kwargs)
        else:
            return redirect("pagina_inicial")

    return _wrapped_view


def guiche_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.funcao == "guiche":
            return view_func(request, *args, **kwargs)
        else:
            return redirect("pagina_inicial")

    return _wrapped_view


def profissional_saude_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and request.user.funcao == "profissional_saude"
        ):
            return view_func(request, *args, **kwargs)
        else:
            return redirect("pagina_inicial")

    return _wrapped_view
