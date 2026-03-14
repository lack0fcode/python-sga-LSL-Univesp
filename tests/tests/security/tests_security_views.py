from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import CustomUser, RegistroDeAcesso


class SecurityViewsTest(TestCase):
    """Testes funcionais de segurança: autenticação, autorização e logout."""

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

        # Teste para recepcionista
        self.client.logout()
        recepcionista_user = CustomUser.objects.create_user(
            cpf="22233344455",
            username="22233344455",
            password="recepcionistapass",
            funcao="recepcionista",
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "22233344455", "password": "recepcionistapass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("recepcionista:cadastrar_paciente"))

        # Teste para profissional de saúde
        self.client.logout()
        profissional_user = CustomUser.objects.create_user(
            cpf="33344455566",
            username="33344455566",
            password="profissionalpass",
            funcao="profissional_saude",
            sala=101,  # Atribuir sala para evitar redirecionamento
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "33344455566", "password": "profissionalpass"},
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
        self.assertFalse(response.context["user"].is_authenticated)

    def test_login_redirect_unknown_role(self):
        """Testa redirecionamento para função desconhecida."""
        unknown_user = CustomUser.objects.create_user(
            cpf="44455566677",
            username="44455566677",
            password="unknownpass",
            funcao="unknown",
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "44455566677", "password": "unknownpass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("pagina_inicial"))

    def test_logout_view(self):
        """Testa logout."""
        self.client.login(cpf="00011122233", password="testpass")
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("login"))

    def test_login_creates_registro_acesso(self):
        """Testa se login cria registro de acesso."""
        initial_count = RegistroDeAcesso.objects.count()
        self.client.post(
            reverse("login"),
            {"cpf": "00011122233", "password": "testpass"},
        )
        self.assertEqual(RegistroDeAcesso.objects.count(), initial_count + 1)
        registro = RegistroDeAcesso.objects.last()
        self.assertEqual(registro.tipo_de_acesso, "login")
        self.assertEqual(registro.usuario, self.user)
