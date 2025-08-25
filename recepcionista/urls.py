# recepcionista/urls.py
from django.urls import path
from . import views

app_name = 'recepcionista'

urlpatterns = [
    path('cadastrar_paciente/', views.cadastrar_paciente, name='cadastrar_paciente'),
]