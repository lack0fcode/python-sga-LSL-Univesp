# administrador/urls.py
from django.urls import path
from . import views

app_name = 'administrador'

urlpatterns = [
    path('cadastrar_funcionario/', views.cadastrar_funcionario, name='cadastrar_funcionario'),
    path('listar_funcionarios/', views.listar_funcionarios, name='listar_funcionarios'),
    path('editar_funcionario/<int:pk>/', views.editar_funcionario, name='editar_funcionario'),
    path('excluir_funcionario/<int:pk>/', views.excluir_funcionario, name='excluir_funcionario'),
]