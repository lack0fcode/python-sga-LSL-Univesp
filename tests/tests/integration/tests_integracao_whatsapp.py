"""
Testes de integração para funcionalidades WhatsApp do sistema SGA-ILSL.
Testa os fluxos que envolvem notificações via WhatsApp.
"""

from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import patch

from core.models import Paciente, CustomUser

User = get_user_model()


class WhatsAppIntegracaoTest(TransactionTestCase):
    """
    Testes de integração que simulam fluxos envolvendo notificações WhatsApp.
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

    def test_fluxo_completo_com_whatsapp(self):
        """Testa fluxo completo incluindo notificação WhatsApp com dados válidos."""

        # 1. Admin cria recepcionista e profissional de saúde
        recepcionista = self.criar_usuario_direto("recepcionista")
        profissional = self.criar_usuario_direto("profissional_saude")

        # 2. Recepcionista cadastra paciente
        client_recep = Client()
        client_recep.login(cpf=recepcionista.cpf, password="recep123")

        paciente_data = {
            "nome_completo": "Paciente WhatsApp",
            "cartao_sus": "777777777777777",
            "telefone_celular": "(11) 98888-8888",  # Formato correto esperado pela validação
            "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "profissional_saude": profissional.id,  # Usar ID do profissional
            "tipo_senha": "G",
        }

        response = client_recep.post(
            reverse("recepcionista:cadastrar_paciente"), data=paciente_data
        )

        # Verifica se o POST foi bem-sucedido
        try:
            paciente = Paciente.objects.get(cartao_sus="777777777777777")
            self.assertEqual(paciente.nome_completo, "Paciente WhatsApp")
            self.assertIsNotNone(paciente.senha)  # Senha deve ter sido gerada
        except Paciente.DoesNotExist:
            # Se paciente não foi criado, verifica se há mensagens de erro na resposta
            self.fail(
                f"Paciente não foi criado. Status: {response.status_code}. Content: {response.content.decode()}"
            )

    def test_fluxo_completo_com_whatsapp_falha(self):
        """Testa fluxo com WhatsApp quando cadastro falha para cobrir bloco except."""
        # 1. Admin cria recepcionista e profissional de saúde
        recepcionista = self.criar_usuario_direto("recepcionista", "88888888888")
        profissional = self.criar_usuario_direto("profissional_saude", "99999999999")

        # 2. Recepcionista tenta cadastrar paciente com dados que causam erro
        client_recep = Client()
        client_recep.login(cpf=recepcionista.cpf, password="recep123")

        # Primeiro cadastra um paciente válido
        paciente_data_valido = {
            "nome_completo": "Paciente Original",
            "cartao_sus": "888888888888888",
            "telefone_celular": "(11) 97777-7777",
            "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "profissional_saude": profissional.id,
            "tipo_senha": "G",
        }

        client_recep.post(
            reverse("recepcionista:cadastrar_paciente"), data=paciente_data_valido
        )

        # Agora tenta cadastrar com mesmo cartão SUS (deve falhar)
        paciente_data_invalido = {
            "nome_completo": "Paciente Duplicado",
            "cartao_sus": "888888888888888",  # Mesmo cartão SUS
            "telefone_celular": "(11) 96666-6666",
            "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "profissional_saude": profissional.id,
            "tipo_senha": "P",
        }

        response = client_recep.post(
            reverse("recepcionista:cadastrar_paciente"), data=paciente_data_invalido
        )

        # Verifica se o POST falhou
        try:
            paciente = Paciente.objects.get(
                cartao_sus="888888888888888", nome_completo="Paciente Duplicado"
            )
            self.fail("Paciente duplicado não deveria ter sido criado")
        except Paciente.DoesNotExist:
            # Se paciente não foi criado, verifica se há mensagens de erro na resposta
            self.assertContains(
                response, "Já existe"
            )  # Deve conter mensagem de erro de duplicata
