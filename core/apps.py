# Em apps.py
from django.apps import AppConfig


class CoreConfig(AppConfig):  # Ou o nome da sua app
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"  # Ou o nome da sua app

    def ready(self):
        import core.signals  # Importe o arquivo signals.py
