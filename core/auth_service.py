from django.contrib.auth import authenticate
from django.utils import timezone

from .models import CustomUser


def authenticate_and_update(
    cpf: str, password: str, max_attempts: int = 4, lock_minutes: int = 5
):
    """Tenta autenticar o usuário por CPF e atualiza contadores/lockout.

    Retorna (user_auth, None) em sucesso ou (None, erro_msg) em falha.
    """
    try:
        user = CustomUser.objects.get(cpf=cpf)
    except CustomUser.DoesNotExist:
        # Não revelar existência do usuário
        return None, "CPF ou senha incorretos."

    # Verificar lockout
    if user.lockout_until and timezone.now() < user.lockout_until:
        remaining = (user.lockout_until - timezone.now()).total_seconds() / 60
        return (
            None,
            f"Conta bloqueada. Tente novamente em {int(remaining)} minutos.",
        )

    user_auth = authenticate(username=cpf, password=password)
    if user_auth and user_auth.is_active:
        user.failed_login_attempts = 0
        user.lockout_until = None
        user.save(update_fields=["failed_login_attempts", "lockout_until"])
        return user_auth, None

    # Falha de autenticação — incrementar contador
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= max_attempts:
        user.lockout_until = timezone.now() + timezone.timedelta(minutes=lock_minutes)
        user.save(update_fields=["failed_login_attempts", "lockout_until"])
        return (
            None,
            f"Conta bloqueada por tentativas excessivas. Tente novamente em {lock_minutes} minutos.",
        )

    user.save(update_fields=["failed_login_attempts"])
    return None, "CPF ou senha incorretos."
