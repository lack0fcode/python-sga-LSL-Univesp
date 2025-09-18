import datetime
import random

from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from core.models import RegistroDeAcesso

from .models import CustomUser


@receiver(pre_save, sender="core.Paciente")
def gerar_senha_paciente(sender, instance, **kwargs):
    from .models import Paciente

    if not instance.senha and instance.tipo_senha:
        hoje = datetime.date.today()
        contador = (
            Paciente.objects.filter(
                horario_geracao_senha__date=hoje, tipo_senha=instance.tipo_senha
            ).count()
            + 1
        )
        instance.senha = f"{instance.tipo_senha}{contador:03d}"


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    # Registra o login do usuário
    print(
        f"Usuário {user.username} (CPF: {user.cpf}) logou-se em {request.META.get('REMOTE_ADDR')}"
    )
    # Aqui você pode salvar essas informações em um modelo específico, como 'RegistroDeAcesso'
    RegistroDeAcesso.objects.create(
        usuario=user,
        tipo_de_acesso="login",
        endereco_ip=request.META.get("REMOTE_ADDR"),  # Obtém o endereço IP
        user_agent=request.META.get(
            "HTTP_USER_AGENT"
        ),  # Obtém informações do navegador
        view_name=(
            request.resolver_match.view_name
            if request.resolver_match
            else "URL não encontrada"
        ),
        data_hora=timezone.now(),
    )
