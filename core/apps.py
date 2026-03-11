# Em apps.py
from django.apps import AppConfig


class CoreConfig(AppConfig):  # Ou o nome da sua app
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"  # Ou o nome da sua app

    def ready(self):
        # Importar signals aqui para garantir que os signal handlers
        # (geração de senha e registro de login) sejam registrados
        # quando a app for carregada pelo Django.
        try:
            from . import signals  # noqa: F401
        except Exception as exc:
            # Evitar falha durante import em ambientes de teste/CI, logar para debug
            import logging

            logger = logging.getLogger(__name__)
            logger.debug("signals import failed: %s", exc)
