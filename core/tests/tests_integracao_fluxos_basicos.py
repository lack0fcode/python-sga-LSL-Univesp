"""
Testes de integração para fluxos básicos do sistema SGA-ILSL.
Testa os fluxos fundamentais de usuários: administrador, recepcionista, guichê e profissional de saúde.
"""

from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import patch

from ..models import Paciente, CustomUser

User = get_user_model()


class FluxosBasicosIntegracaoTest(TransactionTestCase):
    """
    Testes de integração que simulam os fluxos básicos do sistema SGA-ILSL.
    Cada teste cria usuários dinamicamente e testa suas funcionalidades específicas.
    """

    def setUp(self):
        """Configura dados iniciais para os testes."""
        # Mock WhatsApp to avoid real API calls
        self.mock_whatsapp = patch("core.utils.enviar_whatsapp").start()
        self.mock_whatsapp.return_value = True

        self.admin_user = User.objects.create_user(
            cpf="00000000000",
            username="00000000000",
            password="admin123",
            first_name="Admin",
            last_name="Sistema",
            funcao="administrador",
        )

        # Dados para criação dinâmica de usuários
        self.user_data = {
            "recepcionista": {
                "cpf": "11111111111",
                "password": "recep123",
                "first_name": "Maria",
                "last_name": "Recepção",
                "funcao": "recepcionista",
            },
            "guiche": {
                "cpf": "22222222222",
                "password": "guiche123",
                "first_name": "João",
                "last_name": "Guichê",
                "funcao": "guiche",
            },
            "profissional_saude": {
                "cpf": "33333333333",
                "password": "prof123",
                "first_name": "Dr.",
                "last_name": "Silva",
                "funcao": "profissional_saude",
            },
        }

    def tearDown(self):
        """Limpa mocks após os testes."""
        self.mock_whatsapp.stop()

    def criar_usuario_direto(self, user_type, cpf=None):
        """Método auxiliar para criar usuário diretamente no banco."""
        data = self.user_data[user_type].copy()
        if cpf:
            data["cpf"] = cpf

        # Atribuir sala para profissionais de saúde
        sala = None
        if user_type == "profissional_saude":
            sala = 101  # Sala padrão para testes

        return User.objects.create_user(
            cpf=data["cpf"],
            username=data["cpf"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            funcao=data["funcao"],
            sala=sala,
        )

    def test_fluxo_administrador_cria_usuarios(self):
        """Testa se administrador consegue criar todos os tipos de usuário."""
        # Cria usuários de cada tipo diretamente
        for user_type in ["recepcionista", "guiche", "profissional_saude"]:
            usuario = self.criar_usuario_direto(user_type)
            self.assertEqual(usuario.funcao, user_type)
            self.assertTrue(
                usuario.check_password(self.user_data[user_type]["password"])
            )

        # Verifica total de usuários criados
        total_users = User.objects.filter(
            cpf__in=[data["cpf"] for data in self.user_data.values()]
        ).count()
        self.assertEqual(total_users, 3)

    def test_fluxo_recepcionista_cadastra_paciente(self):
        """Testa fluxo completo: recepcionista cadastra paciente."""
        # Admin cria recepcionista e profissional de saúde
        recepcionista = self.criar_usuario_direto("recepcionista")
        profissional = self.criar_usuario_direto("profissional_saude")

        # Recepcionista faz login
        client = Client()
        login_success = client.login(cpf=recepcionista.cpf, password="recep123")
        self.assertTrue(login_success)

        # Recepcionista acessa página de cadastro de paciente
        response = client.get(reverse("recepcionista:cadastrar_paciente"))
        self.assertEqual(response.status_code, 200)

        # Cadastra paciente com profissional de saúde correto
        paciente_data = {
            "nome_completo": "Paciente Teste Dinâmico",
            "cartao_sus": "123456789012345",
            "telefone_celular": "11999999999",
            "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "profissional_saude": profissional.id,  # Usar ID do profissional
            "tipo_senha": "G",
        }

        response = client.post(
            reverse("recepcionista:cadastrar_paciente"), data=paciente_data, follow=True
        )
        self.assertEqual(response.status_code, 200)

        # Verifica se paciente foi criado
        paciente = Paciente.objects.get(cartao_sus="123456789012345")
        self.assertEqual(paciente.nome_completo, "Paciente Teste Dinâmico")
        self.assertEqual(paciente.tipo_senha, "G")
        self.assertIsNotNone(paciente.senha)  # Senha deve ter sido gerada

    def test_fluxo_guiche_acessa_painel(self):
        """Testa fluxo: guichê acessa painel."""
        # Admin cria guichê diretamente
        guiche_user = self.criar_usuario_direto("guiche")

        # Guichê faz login
        client = Client()
        login_success = client.login(cpf=guiche_user.cpf, password="guiche123")
        self.assertTrue(login_success)

        # Guichê acessa painel
        response = client.get(reverse("guiche:painel_guiche"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "guiche/painel_guiche.html")

    def test_fluxo_profissional_saude_acessa_painel(self):
        """Testa fluxo: profissional da saúde acessa painel."""
        # Admin cria profissional diretamente
        profissional = self.criar_usuario_direto("profissional_saude")

        # Profissional faz login
        client = Client()
        login_success = client.login(cpf=profissional.cpf, password="prof123")
        self.assertTrue(login_success)

        # Profissional acessa painel
        response = client.get(reverse("profissional_saude:painel_profissional"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profissional_saude/painel_profissional.html")
