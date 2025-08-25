# core/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),
    #path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'), #Remova essa linha
    path('login/', views.LoginView.as_view(template_name='login.html'), name='login'), #Adicione essa linha
    path('logout/', views.logout_view, name='logout'),
]