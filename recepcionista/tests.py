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

    def test_sql_injection_nome_completo(self):
        """Testa proteção contra SQL injection no nome."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")
        malicious_data = self.valid_data.copy()
        malicious_data["nome_completo"] = "'; DROP TABLE paciente; --"
        malicious_data["cartao_sus"] = self.get_unique_cartao_sus()
        resp = self.client.post(url, malicious_data, follow=True)
        self.assertEqual(resp.status_code, 200)  # Formulário processado e redirecionado
        # Verificar que paciente foi criado (Django protege automaticamente)
        paciente = Paciente.objects.filter(nome_completo="'; DROP TABLE paciente; --")
        self.assertTrue(paciente.exists())

    def test_xss_nome_completo(self):
        """Testa proteção contra XSS no nome."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")
        xss_data = self.valid_data.copy()
        xss_data["nome_completo"] = '<script>alert("xss")</script>'
        xss_data["cartao_sus"] = self.get_unique_cartao_sus()
        resp = self.client.post(url, xss_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Verificar que o formulário é inválido devido à validação XSS
        self.assertContains(resp, "Entrada inválida: scripts não são permitidos.")
        paciente = Paciente.objects.filter(
            nome_completo='<script>alert("XSS")</script>'
        )
        self.assertFalse(paciente.exists())

    def test_sql_injection_observacoes(self):
        """Testa proteção contra SQL injection nas observações."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")
        malicious_data = self.valid_data.copy()
        malicious_data["observacoes"] = "1' OR '1'='1"
        malicious_data["cartao_sus"] = self.get_unique_cartao_sus()
        resp = self.client.post(url, malicious_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        paciente = Paciente.objects.filter(observacoes="1' OR '1'='1")
        self.assertTrue(paciente.exists())

    def test_telefone_celular_formats(self):
        """Testa diferentes formatos de telefone."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        valid_formats = [
            "(11) 91234-5678",
            "11 91234 5678",
            "11912345678",
            "(11)91234-5678",
        ]

        for telefone in valid_formats:
            data = self.valid_data.copy()
            data["nome_completo"] = f"Paciente {telefone}"
            data["telefone_celular"] = telefone
            data["cartao_sus"] = self.get_unique_cartao_sus()
            resp = self.client.post(url, data, follow=True)
            self.assertEqual(resp.status_code, 200)
            paciente = Paciente.objects.filter(nome_completo=f"Paciente {telefone}")
            self.assertTrue(paciente.exists())

    def test_telefone_celular_invalid_formats(self):
        """Testa formatos inválidos de telefone."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        invalid_formats = [
            "12345",  # Muito curto
            "(11) 9123-4567",  # Sem 9 no início
            "1191234567",  # 10 dígitos
            "abc123",  # Não numérico
        ]

        for telefone in invalid_formats:
            data = self.valid_data.copy()
            data["nome_completo"] = f"Paciente Inválido {telefone}"
            data["telefone_celular"] = telefone
            data["cartao_sus"] = self.get_unique_cartao_sus()
            resp = self.client.post(url, data)
            self.assertEqual(resp.status_code, 200)
            # Paciente não deve ser criado devido ao telefone inválido
            paciente = Paciente.objects.filter(
                nome_completo=f"Paciente Inválido {telefone}"
            )
            self.assertFalse(paciente.exists())

    def test_cartao_sus_validation(self):
        """Testa validação do cartão SUS."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        # Cartão SUS muito longo (deve falhar)
        data = self.valid_data.copy()
        data["cartao_sus"] = "1" * 21
        data["nome_completo"] = "Paciente Cartão Longo"
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        # Verificar que não foi criado
        paciente = Paciente.objects.filter(cartao_sus="1" * 21)
        self.assertFalse(paciente.exists())
        paciente = Paciente.objects.filter(nome_completo="Paciente Cartão Longo")
        self.assertFalse(paciente.exists())  # Não deve ser criado

    def test_tipo_senha_choices(self):
        """Testa choices válidos para tipo_senha."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        tipos_validos = ["E", "C", "P", "G", "D", "A", "NH", "H", "U"]
        for tipo in tipos_validos:
            data = self.valid_data.copy()
            data["nome_completo"] = f"Paciente {tipo}"
            data["tipo_senha"] = tipo
            data["cartao_sus"] = self.get_unique_cartao_sus()
            resp = self.client.post(url, data, follow=True)
            self.assertEqual(resp.status_code, 200)
            paciente = Paciente.objects.filter(nome_completo=f"Paciente {tipo}")
            self.assertTrue(paciente.exists())

    def test_tipo_senha_invalid_choice(self):
        """Testa choice inválido para tipo_senha."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        data = self.valid_data.copy()
        data["nome_completo"] = "Paciente Tipo Inválido"
        data["tipo_senha"] = "X"  # Inválido
        data["cartao_sus"] = self.get_unique_cartao_sus()
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        paciente = Paciente.objects.filter(nome_completo="Paciente Tipo Inválido")
        self.assertFalse(paciente.exists())

    def test_required_fields(self):
        """Testa que alguns campos podem ser vazios."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        # Campos opcionais vazios, mas campos obrigatórios preenchidos
        data = {
            "nome_completo": "Paciente Teste",
            "tipo_senha": "G",  # Obrigatório
            "telefone_celular": "",
            "cartao_sus": "",
            "horario_agendamento": "",
            "profissional_saude": "",
            "observacoes": "",
        }
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Deve criar paciente
        paciente = Paciente.objects.filter(nome_completo="Paciente Teste")
        self.assertTrue(paciente.exists())

    def test_optional_fields(self):
        """Testa campos opcionais."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        data = {
            "nome_completo": "Paciente Mínimo",
            "tipo_senha": "G",
            # Outros campos opcionais omitidos
        }
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        paciente = Paciente.objects.filter(nome_completo="Paciente Mínimo")
        self.assertTrue(paciente.exists())

    def test_profissional_saude_optional(self):
        """Testa que profissional_saude é opcional."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        data = self.valid_data.copy()
        data["nome_completo"] = "Paciente Sem Profissional"
        data["profissional_saude"] = ""  # Vazio
        data["cartao_sus"] = self.get_unique_cartao_sus()
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        paciente = Paciente.objects.filter(nome_completo="Paciente Sem Profissional")
        self.assertTrue(paciente.exists())
        self.assertIsNone(paciente.first().profissional_saude)

    def test_horario_agendamento_validation(self):
        """Testa validação de horário de agendamento."""
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")

        # Data futura
        future_date = timezone.now() + timezone.timedelta(days=1)
        data = self.valid_data.copy()
        data["nome_completo"] = "Paciente Futuro"
        data["horario_agendamento"] = future_date
        data["cartao_sus"] = self.get_unique_cartao_sus()
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        paciente = Paciente.objects.filter(nome_completo="Paciente Futuro")
        self.assertTrue(paciente.exists())

        # Data passada (deve ser aceita)
        past_date = timezone.now() - timezone.timedelta(days=1)
        data["nome_completo"] = "Paciente Passado"
        data["horario_agendamento"] = past_date
        data["cartao_sus"] = self.get_unique_cartao_sus()
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        paciente = Paciente.objects.filter(nome_completo="Paciente Passado")
        self.assertTrue(paciente.exists())

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
