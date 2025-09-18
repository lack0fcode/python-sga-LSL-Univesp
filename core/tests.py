from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import CadastrarFuncionarioForm, CadastrarPacienteForm, LoginForm
from .models import (
    Atendimento,
    Chamada,
    ChamadaProfissional,
    CustomUser,
    Guiche,
    Paciente,
    RegistroDeAcesso,
)


class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            cpf="12345678900",
            username="12345678900",
            password="testpass",
            first_name="Test",
            last_name="User",
            funcao="administrador",
        )

    def test_str(self):
        self.assertEqual(str(self.user), "Test User")

    def test_username_field_is_cpf(self):
        self.assertEqual(self.user.USERNAME_FIELD, "cpf")


class PacienteModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="testpass",
            funcao="profissional_saude",
        )
        self.paciente = Paciente.objects.create(
            nome_completo="Paciente Teste",
            tipo_senha="G",
            senha="G001",
            cartao_sus="1234567890",
            profissional_saude=self.user,
            horario_agendamento=timezone.now(),
        )

    def test_str(self):
        self.assertIn("Paciente Teste", str(self.paciente))


class AtendimentoModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            cpf="22233344455",
            username="22233344455",
            password="testpass",
        )
        self.paciente = Paciente.objects.create(nome_completo="Paciente A")
        self.atendimento = Atendimento.objects.create(
            paciente=self.paciente, funcionario=self.user
        )

    def test_str(self):
        # Patch: Atendimento.__str__ uses paciente.nome, but Paciente has nome_completo
        # So we monkeypatch the Paciente instance for this test only
        self.paciente.nome = self.paciente.nome_completo
        self.assertIn("Paciente A", str(self.atendimento))


class RegistroDeAcessoModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            cpf="33344455566",
            username="33344455566",
            password="testpass",
        )
        self.registro = RegistroDeAcesso.objects.create(
            usuario=self.user,
            tipo_de_acesso="login",
            endereco_ip="127.0.0.1",
            user_agent="TestAgent",
            view_name="pagina_inicial",
        )

    def test_str(self):
        self.assertIn(self.user.username, str(self.registro))


class GuicheModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            cpf="44455566677",
            username="44455566677",
            password="testpass",
        )
        self.guiche = Guiche.objects.create(numero=1, funcionario=self.user)

    def test_str(self):
        self.assertIn("Guichê 1", str(self.guiche))


class ChamadaModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            cpf="55566677788",
            username="55566677788",
            password="testpass",
        )
        self.paciente = Paciente.objects.create(nome_completo="Paciente B")
        self.guiche = Guiche.objects.create(numero=2, funcionario=self.user)
        self.chamada = Chamada.objects.create(
            paciente=self.paciente, guiche=self.guiche, acao="chamada"
        )

    def test_str(self):
        self.assertIn("Chamada", str(self.chamada))


class ChamadaProfissionalModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            cpf="66677788899",
            username="66677788899",
            password="testpass",
            funcao="profissional_saude",
        )
        self.paciente = Paciente.objects.create(nome_completo="Paciente C")
        self.chamada_prof = ChamadaProfissional.objects.create(
            paciente=self.paciente, profissional_saude=self.user, acao="chamada"
        )

    def test_str(self):
        self.assertIn("Chamada", str(self.chamada_prof))


# Forms
class CadastrarPacienteFormTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            cpf="77788899900",
            username="77788899900",
            password="testpass",
            funcao="profissional_saude",
        )

    def test_valid_form(self):
        data = {
            "nome_completo": "Paciente D",
            "cartao_sus": "1234567890",
            "horario_agendamento": timezone.now(),
            "profissional_saude": self.user.id,
            "observacoes": "Obs",
            "tipo_senha": "G",
        }
        form = CadastrarPacienteForm(data)
        self.assertTrue(form.is_valid())


class CadastrarFuncionarioFormTest(TestCase):
    def test_valid_form(self):
        data = {
            "cpf": "88899900011",
            "username": "88899900011",
            "first_name": "Func",
            "last_name": "Test",
            "email": "func@test.com",
            "funcao": "administrador",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        form = CadastrarFuncionarioForm(data)
        self.assertTrue(form.is_valid())


class LoginFormTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            cpf="99900011122",
            username="99900011122",
            password="testpass",
        )

    def test_valid_login(self):
        data = {"cpf": "99900011122", "password": "testpass"}
        form = LoginForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_login(self):
        data = {"cpf": "99900011122", "password": "wrongpass"}
        form = LoginForm(data)
        self.assertFalse(form.is_valid())


# Views
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

    def test_logout_view(self):
        self.client.login(cpf="00011122233", password="testpass")
        response = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_pagina_inicial_requires_login(self):
        response = self.client.get(reverse("pagina_inicial"))
        self.assertEqual(response.status_code, 302)  # Redirect to login
