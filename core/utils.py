# core/utils.py
import logging
import os
from twilio.rest import Client
from django.conf import settings

logger = logging.getLogger(__name__)


def enviar_whatsapp(
    numero_destino: str,
    mensagem: str = None,
    content_sid: str = None,
    content_variables: dict = None,
):
    """
    Envia uma mensagem via WhatsApp usando a API do Twilio.
    Pode usar texto simples ou template aprovado.

    Args:
        numero_destino: Número do destinatário em formato E.164
        mensagem: Texto da mensagem (para mensagens simples)
        content_sid: SID do template aprovado (para templates)
        content_variables: Variáveis do template (opcional)

    Retorna um dicionário com status e detalhes.
    """
    if (
        not settings.TWILIO_ACCOUNT_SID
        or not settings.TWILIO_AUTH_TOKEN
        or not settings.TWILIO_WHATSAPP_NUMBER
    ):
        error_msg = (
            "Credenciais Twilio não configuradas. Verifique as variáveis de ambiente."
        )
        logger.error(f"Erro: {error_msg}")
        return {"status": "error", "error": error_msg}

    # Validar parâmetros
    if not mensagem and not content_sid:
        return {"status": "error", "error": "Deve fornecer 'mensagem' ou 'content_sid'"}

    if content_sid and mensagem:
        return {
            "status": "error",
            "error": "Use 'mensagem' OU 'content_sid', não ambos",
        }

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Preparar parâmetros da mensagem
        message_params = {
            "from_": f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
            "to": f"whatsapp:{numero_destino}",
        }

        if mensagem:
            # Mensagem de texto simples
            message_params["body"] = mensagem
        elif content_sid:
            # Template aprovado
            message_params["content_sid"] = content_sid
            if content_variables:
                import json

                message_params["content_variables"] = json.dumps(content_variables)

        message = client.messages.create(**message_params)
        logger.info(f"Mensagem enviada com SID: {message.sid}")
        return {
            "status": "success",
            "sid": message.sid,
            "to": numero_destino,
            "message_status": message.status,
            "date_created": (
                message.date_created.isoformat() if message.date_created else None
            ),
            "direction": message.direction,
            "price": message.price,
            "error_message": message.error_message,
            "message_type": "template" if content_sid else "text",
        }
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem via WhatsApp: {e}")
        return {"status": "error", "error": str(e)}


def enviar_sms_ou_whatsapp(
    numero_destino: str,
    mensagem: str,
    content_sid: str = None,
    content_variables: dict = None,
):
    """
    Tenta enviar SMS primeiro, se falhar usa WhatsApp como fallback.

    Args:
        numero_destino: Número do destinatário em formato E.164
        mensagem: Texto da mensagem
        content_sid: SID do template aprovado (opcional, apenas para WhatsApp)
        content_variables: Variáveis do template (opcional, apenas para WhatsApp)

    Retorna um dicionário com status e detalhes.
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        error_msg = (
            "Credenciais Twilio não configuradas. Verifique as variáveis de ambiente."
        )
        logger.error(f"Erro: {error_msg}")
        return {"status": "error", "error": error_msg}

    # Primeiro tentar SMS
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Usar o número SMS do Twilio (não WhatsApp)
        sms_number = os.environ.get(
            "TWILIO_SMS_NUMBER", "TWILIO_WHATSAPP_NUMBER"
        )  # Número verificado para SMS

        message = client.messages.create(
            from_=sms_number, body=mensagem, to=numero_destino
        )

        logger.info(f"SMS enviado com sucesso. SID: {message.sid}")
        return {
            "status": "success",
            "sid": message.sid,
            "to": numero_destino,
            "message_status": message.status,
            "date_created": (
                message.date_created.isoformat() if message.date_created else None
            ),
            "direction": message.direction,
            "price": message.price,
            "error_message": message.error_message,
            "message_type": "sms",
        }

    except Exception as sms_error:
        logger.warning(
            f"Falha ao enviar SMS: {sms_error}. Tentando WhatsApp como fallback..."
        )

        # Se SMS falhar, tentar WhatsApp
        try:
            whatsapp_result = enviar_whatsapp(
                numero_destino, mensagem, content_sid, content_variables
            )

            if whatsapp_result["status"] == "success":
                logger.info("WhatsApp enviado com sucesso como fallback")
                whatsapp_result["fallback_used"] = True
                whatsapp_result["original_error"] = str(sms_error)
                return whatsapp_result
            else:
                logger.error(
                    f"WhatsApp também falhou: {whatsapp_result.get('error', 'Erro desconhecido')}"
                )
                return {
                    "status": "error",
                    "error": f"SMS e WhatsApp falharam. SMS: {str(sms_error)}, WhatsApp: {whatsapp_result.get('error', 'Erro desconhecido')}",
                    "sms_error": str(sms_error),
                    "whatsapp_error": whatsapp_result.get("error"),
                }

        except Exception as whatsapp_error:
            logger.error(f"Erro crítico no fallback WhatsApp: {whatsapp_error}")
            return {
                "status": "error",
                "error": f"SMS e WhatsApp falharam. SMS: {str(sms_error)}, WhatsApp: {str(whatsapp_error)}",
                "sms_error": str(sms_error),
                "whatsapp_error": str(whatsapp_error),
            }
