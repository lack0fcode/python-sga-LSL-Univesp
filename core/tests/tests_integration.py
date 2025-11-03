from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import CustomUser, Paciente


# Teste de integração: fluxo completo de cadastro, login, acesso e logout
class IntegracaoFluxoCompletoTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.funcionario = CustomUser.objects.create_user(
            cpf="12312312399",
            username="12312312399",
            password="funcpass",
            first_name="Func",
            last_name="Test",
            funcao="administrador",
        )

    def test_fluxo_completo(self):
        # Cadastro de paciente via model (simulando formulário)
        paciente = Paciente.objects.create(
            nome_completo="Paciente Integração",
            cartao_sus="99988877766",
            horario_agendamento=timezone.now(),
            profissional_saude=self.funcionario,
            tipo_senha="G",
        )
        self.assertIsNotNone(paciente.id)

        # Login
        login = self.client.login(cpf="12312312399", password="funcpass")
        self.assertTrue(login)

        # Acesso à página inicial (protegida)
        response = self.client.get(reverse("pagina_inicial"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)

        # Logout
        response = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        # Após logout, usuário não está autenticado
        response2 = self.client.get(reverse("pagina_inicial"))
        self.assertEqual(response2.status_code, 302)
