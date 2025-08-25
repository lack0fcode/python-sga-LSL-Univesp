from django.urls import path
from . import views

app_name = 'guiche'

urlpatterns = [
    path('painel_guiche/', views.painel_guiche, name='painel_guiche'),
    path('chamar/<int:paciente_id>/', views.chamar_senha, name='chamar_senha'),
    path('reanunciar/<int:paciente_id>/', views.reanunciar_senha, name='reanunciar_senha'),
    path('confirmar/<int:paciente_id>/', views.confirmar_atendimento, name='confirmar_atendimento'),
    path('tv1/', views.tv1_view, name='tv1'),
    path('tv1/api/', views.tv1_api_view, name='tv1_api'),  # Sem guiche_numero
]