from django.urls import path

from . import views

app_name = "profissional_saude"

urlpatterns = [
    path("selecionar_sala/", views.selecionar_sala, name="selecionar_sala"),
    path("painel/", views.painel_profissional, name="painel_profissional"),
    path(
        "acao/<int:paciente_id>/<str:acao>/",
        views.realizar_acao_profissional,
        name="realizar_acao_profissional",
    ),
    path("tv2/", views.tv2_view, name="tv2"),
    path("tv2/api/", views.tv2_api_view, name="tv2_api"),
    path("tv2/historico/api/", views.tv2_historico_api_view, name="tv2_historico_api"),
]
