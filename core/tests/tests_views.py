from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from ..models import CustomUser, RegistroDeAcesso


class CoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            cpf="00011122233",
            username="00011122233",
            password="testpass",
        )

    def test_login_view_get(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_login_view_post_valid(self):
        response = self.client.post(
            reverse("login"),
            {"cpf": "00011122233", "password": "testpass"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        # After login, try to access a login-required page to check authentication
        response2 = self.client.get(reverse("pagina_inicial"))
        self.assertTrue(response2.context["user"].is_authenticated)

    def test_login_view_post_invalid(self):
        response = self.client.post(
            reverse("login"),
            {"cpf": "00011122233", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)

    def test_login_redirect_based_on_role(self):
        """Testa redirecionamento após login baseado na função do usuário."""
        # Teste para administrador
        admin_user = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="adminpass",
            funcao="administrador",
            is_staff=True,
            is_superuser=True,
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "11122233344", "password": "adminpass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("administrador:listar_funcionarios"))

        self.client.logout()

        # Teste para recepcionista
        recep_user = CustomUser.objects.create_user(
            cpf="22233344455",
            username="22233344455",
            password="receptionpass",
            funcao="recepcionista",
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "22233344455", "password": "receptionpass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("recepcionista:cadastrar_paciente"))

        self.client.logout()

        # Teste para guiche
        guiche_user = CustomUser.objects.create_user(
            cpf="33344455566",
            username="33344455566",
            password="guichepass",
            funcao="guiche",
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "33344455566", "password": "guichepass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("guiche:selecionar_guiche"))

        self.client.logout()

        # Teste para profissional_saude
        prof_user = CustomUser.objects.create_user(
            cpf="44455566677",
            username="44455566677",
            password="profpass",
            funcao="profissional_saude",
            sala=101,  # Atribuir sala para evitar redirecionamento
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "44455566677", "password": "profpass"},
            follow=True,
        )
        self.assertRedirects(
            response, reverse("profissional_saude:painel_profissional")
        )

    def test_login_view_post_form_invalid(self):
        """Testa login com formulário inválido (CPF vazio)."""
        response = self.client.post(
            reverse("login"),
            {"cpf": "", "password": "testpass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este campo é obrigatório")  # Ou similar
        self.assertFalse(response.context["user"].is_authenticated)

    def test_login_redirect_unknown_role(self):
        """Testa redirecionamento para função desconhecida."""
        unknown_user = CustomUser.objects.create_user(
            cpf="55566677788",
            username="55566677788",
            password="unknownpass",
            funcao="desconhecida",  # Função não reconhecida
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "55566677788", "password": "unknownpass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("pagina_inicial"))

    def test_admin_access_registro_acesso(self):
        """Testa acesso à página admin de RegistroDeAcesso para cobrir configuração."""
        admin_user = CustomUser.objects.create_user(
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

    def test_logout_view(self):
        self.client.login(cpf="00011122233", password="testpass")
        response = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_login_creates_registro_acesso(self):
        """Testa se login cria RegistroDeAcesso via sinal."""
        from ..models import RegistroDeAcesso

        initial_count = RegistroDeAcesso.objects.count()
        response = self.client.post(
            reverse("login"),
            {"cpf": "00011122233", "password": "testpass"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RegistroDeAcesso.objects.count(), initial_count + 1)
        registro = RegistroDeAcesso.objects.last()
        self.assertEqual(registro.tipo_de_acesso, "login")

    def test_pagina_inicial_requires_login(self):
        response = self.client.get(reverse("pagina_inicial"))
        self.assertEqual(response.status_code, 302)  # Redirect to login
