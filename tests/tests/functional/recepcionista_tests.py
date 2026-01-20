from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import CustomUser, Paciente
from core.forms import CadastrarPacienteForm


class RecepcionistaViewsTest(TestCase):
    """Testes abrangentes para recepcionista com foco em segurança."""

    @staticmethod
    def get_unique_cartao_sus(base="123456789012"):
        """Gera um cartão SUS único baseado em um timestamp."""
        import time

        return f"{base}{int(time.time()*1000000) % 100000}"

    def setUp(self):
        self.client = Client()
        self.recep = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="receppass",
            funcao="recepcionista",
            first_name="Recep",
            last_name="User",
        )
        self.prof = CustomUser.objects.create_user(
            cpf="22233344455",
            username="22233344455",
            password="profpass",
            funcao="profissional_saude",
            first_name="Prof",
            last_name="User",
        )
        self.admin = CustomUser.objects.create_user(
            cpf="99988877766",
            username="99988877766",
            password="adminpass",
            funcao="administrador",
            first_name="Admin",
            last_name="User",
        )
        self.valid_data = {
            "nome_completo": "Paciente Teste",
            "cartao_sus": self.get_unique_cartao_sus(),
            "horario_agendamento": timezone.now(),
            "profissional_saude": self.prof.id,
            "observacoes": "Observações de teste",
            "tipo_senha": "G",
            "telefone_celular": "(11) 91234-5678",
        }

    def test_cadastrar_paciente_get(self):
        """Testa acesso GET ao formulário."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "form")

    def test_cadastrar_paciente_post_valid(self):
        """Testa cadastro válido de paciente."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")
        resp = self.client.post(url, self.valid_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Paciente.objects.filter(nome_completo="Paciente Teste").exists()
        )

    def test_permissao_apenas_recepcionista(self):
        """Testa permissões de acesso."""
        url = reverse("recepcionista:cadastrar_paciente")

        # Não logado
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        # Logado como profissional de saúde
        self.client.login(cpf="22233344455", password="profpass")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        # Logado como administrador
        self.client.login(cpf="99988877766", password="adminpass")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        # Logado como recepcionista (deve funcionar)
        self.client.login(cpf="11122233344", password="receppass")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_post_permissao_apenas_recepcionista(self):
        """Testa permissões de POST."""
        url = reverse("recepcionista:cadastrar_paciente")

        # Não logado
        resp = self.client.post(url, self.valid_data)
        self.assertEqual(resp.status_code, 302)

        # Logado como profissional de saúde
        self.client.login(cpf="22233344455", password="profpass")
        resp = self.client.post(url, self.valid_data)
        self.assertEqual(resp.status_code, 302)

        # Logado como recepcionista (deve funcionar)
        self.client.login(cpf="11122233344", password="receppass")
        resp = self.client.post(url, self.valid_data, follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_data_integrity_multiple_submissions(self):
        """Testa integridade de dados em múltiplas submissões."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        # Submeter mesmo dados múltiplas vezes
        for i in range(3):
            data = self.valid_data.copy()
            data["nome_completo"] = f"Paciente {i}"
            data["cartao_sus"] = self.get_unique_cartao_sus()
            resp = self.client.post(url, data, follow=True)
            self.assertEqual(resp.status_code, 200)
            paciente = Paciente.objects.filter(nome_completo=f"Paciente {i}")
            self.assertTrue(paciente.exists())

        # Verificar que todos foram criados
        self.assertEqual(
            Paciente.objects.filter(nome_completo__startswith="Paciente ").count(), 3
        )

    def test_large_input_handling(self):
        """Testa tratamento de inputs grandes."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        # Nome muito longo
        data = self.valid_data.copy()
        data["nome_completo"] = "A" * 300  # Maior que max_length
        data["cartao_sus"] = self.get_unique_cartao_sus()
        data["observacoes"] = "B" * 1000  # Campo sem limite específico
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        # Verificar se foi criado (Django pode truncar ou rejeitar)
        paciente = Paciente.objects.filter(nome_completo__startswith="A" * 255)
        if paciente.exists():
            self.assertTrue(True)  # Aceitou truncado
        else:
            # Verificar se erro foi mostrado
            self.assertContains(resp, "erro")

    def test_special_characters(self):
        """Testa caracteres especiais."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        special_names = [
            "José da Silva",
            "João & Maria",
            "Ana-Maria",
            "José María",
            "João Paulo",
        ]

        for name in special_names:
            data = self.valid_data.copy()
            data["nome_completo"] = name
            data["cartao_sus"] = self.get_unique_cartao_sus()
            resp = self.client.post(url, data, follow=True)
            self.assertEqual(resp.status_code, 200)
            paciente = Paciente.objects.filter(nome_completo=name)
            self.assertTrue(paciente.exists())

    def test_form_validation_errors_display(self):
        """Testa exibição de erros de validação."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        # Dados inválidos
        invalid_data = {
            "nome_completo": "",  # Obrigatório vazio
            "tipo_senha": "X",  # Inválido
            "telefone_celular": "123",  # Inválido
        }

        resp = self.client.post(url, invalid_data)
        self.assertEqual(resp.status_code, 200)
        # Verificar que erros são mostrados
        self.assertContains(
            resp, "Erro ao cadastrar o paciente"
        )  # Mensagem de erro genérica
