from django.test import Client, TestCase
from django.urls import reverse

from core.models import CustomUser


class CoreViewsTest(TestCase):
    def setUp(self):
        print(
            "\033[95m🎯 Teste funcional: Acesso admin e login requerido\033[0m"
        )  # Magenta
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            cpf="00011122233",
            username="00011122233",
            password="testpass",
        )

    def test_admin_access_registro_acesso(self):
        """Testa acesso à página admin de RegistroDeAcesso para cobrir configuração."""
        print(
            "\033[91m  → Testando acesso à página admin de RegistroDeAcesso...\033[0m"
        )  # Vermelho
        _admin_user = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="adminpass",
            funcao="administrador",
            is_staff=True,
            is_superuser=True,
        )
        self.client.login(cpf="11122233344", password="adminpass")
        response = self.client.get("/admin/core/registrodeacesso/")
        self.assertEqual(response.status_code, 200)

    def test_pagina_inicial_requires_login(self):
        print("\033[91m  → Verificando se página inicial requer login...\033[0m")
        response = self.client.get(reverse("pagina_inicial"))
        self.assertEqual(response.status_code, 302)  # Redirect to login
