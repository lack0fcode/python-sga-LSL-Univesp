# core/utils.py
import logging
import os
from twilio.rest import Client
from django.conf import settings

logger = logging.getLogger(__name__)


def enviar_whatsapp(numero_destino: str, mensagem: str):
    """
    Envia uma mensagem via WhatsApp usando a API do Twilio.
    """
    if (
        not settings.TWILIO_ACCOUNT_SID
        or not settings.TWILIO_AUTH_TOKEN
        or not settings.TWILIO_WHATSAPP_NUMBER
    ):
        logger.error(
            "Erro: Credenciais Twilio não configuradas. Verifique as variáveis de ambiente."
        )
        return False

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        message = client.messages.create(
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",  # Seu número Twilio
            body=mensagem,
            to=f"whatsapp:{numero_destino}",  # Número do paciente
        )
        logger.info(f"Mensagem enviada com SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem via WhatsApp: {e}")
        return False
