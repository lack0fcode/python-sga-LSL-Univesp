# core/admin.py
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Atendimento, CustomUser, Guiche, Paciente, RegistroDeAcesso


class RegistroDeAcessoAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "tipo_de_acesso",
        "endereco_ip",
        "user_agent",
        "data_hora_local",
    )

    def data_hora_local(self, obj):
        return timezone.localtime(obj.data_hora).strftime("%d/%m/%Y %H:%M:%S")

    data_hora_local.admin_order_field = "data_hora"  # type: ignore
    data_hora_local.short_description = "Data e Hora (São Paulo)"  # type: ignore


admin.site.register(CustomUser)
admin.site.register(Paciente)
admin.site.register(Atendimento)
admin.site.register(RegistroDeAcesso, RegistroDeAcessoAdmin)
admin.site.register(Guiche)
