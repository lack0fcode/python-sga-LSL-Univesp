from django.test import TestCase
from django.utils import timezone

from core.forms import CadastrarPacienteForm, CadastrarFuncionarioForm
from core.models import CustomUser


class SecurityFormsTest(TestCase):
    """Testes de segurança para formulários: proteção contra SQL injection e XSS."""

    def setUp(self):
        print(
            "\033[95m🛡️ Teste de segurança: Proteção contra SQL injection e XSS\033[0m"
        )  # Magenta
        self.profissional = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="testpass",
            funcao="profissional_saude",
            first_name="Dr.",
            last_name="Teste",
        )
        self.valid_data_paciente = {
            "nome_completo": "João Silva Santos",
            "tipo_senha": "G",
            "cartao_sus": "123456789012345",
            "profissional_saude": self.profissional.id,
            "telefone_celular": "(11) 99999-9999",
            "observacoes": "Paciente de teste",
            "horario_agendamento": timezone.now(),
        }
        self.valid_data_funcionario = {
            "cpf": "99900011122",
            "username": "99900011122",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "funcao": "recepcionista",
            "password1": "testpass123",
            "password2": "testpass123",
        }

    def test_sql_injection_nome_completo(self):
        """Testa proteção contra SQL injection no nome."""
        print("\033[93m  → Testando proteção contra SQL injection no nome...\033[0m")
        malicious_data = self.valid_data_paciente.copy()
        malicious_data["nome_completo"] = "'; DROP TABLE paciente; --"
        form = CadastrarPacienteForm(data=malicious_data)
        self.assertTrue(form.is_valid())  # Django ModelForm protege automaticamente
        paciente = form.save()
        self.assertEqual(paciente.nome_completo, "'; DROP TABLE paciente; --")
        print(
            "\033[92m    ✅ Sucesso: SQL injection neutralizado - dados salvos como string literal!\033[0m"
        )
        print(f"\033[92m       Dados salvos: Nome='{paciente.nome_completo}'\033[0m")

    def test_xss_nome_completo(self):
        """Testa proteção contra XSS no nome."""
        print("\033[93m  → Testando proteção contra XSS no nome...\033[0m")
        xss_data = self.valid_data_paciente.copy()
        xss_data["nome_completo"] = '<script>alert("XSS")</script>'
        form = CadastrarPacienteForm(data=xss_data)
        self.assertFalse(form.is_valid())
        self.assertIn("nome_completo", form.errors)
        self.assertIn(
            "Entrada inválida: scripts não são permitidos.",
            str(form.errors["nome_completo"]),
        )
        print(
            "\033[92m    ✅ Sucesso: XSS bloqueado - formulário rejeitou entrada maliciosa!\033[0m"
        )
        print(f"\033[92m       Erro: {form.errors['nome_completo'][0]}\033[0m")

    def test_sql_injection_observacoes(self):
        """Testa proteção contra SQL injection nas observações."""
        print(
            "\033[93m  → Testando proteção contra SQL injection nas observações...\033[0m"
        )
        malicious_data = self.valid_data_paciente.copy()
        malicious_data["observacoes"] = "1' OR '1'='1"
        form = CadastrarPacienteForm(data=malicious_data)
        self.assertTrue(form.is_valid())
        paciente = form.save()
        self.assertEqual(paciente.observacoes, "1' OR '1'='1")
        print(
            "\033[92m    ✅ Sucesso: SQL injection nas observações neutralizado!\033[0m"
        )
        print(
            f"\033[92m       Dados salvos: Observações='{paciente.observacoes}'\033[0m"
        )

    def test_sql_injection_cpf_funcionario(self):
        """Testa proteção contra SQL injection no CPF."""
        print("\033[93m  → Testando proteção contra SQL injection no CPF...\033[0m")
        malicious_data = self.valid_data_funcionario.copy()
        malicious_data["cpf"] = "123'; DROP TABLE customuser; --"
        malicious_data["username"] = malicious_data["cpf"]
        form = CadastrarFuncionarioForm(data=malicious_data)
        self.assertFalse(form.is_valid())
        self.assertIn("cpf", form.errors)
        print(
            "\033[92m    ✅ Sucesso: SQL injection no CPF bloqueado por validação!\033[0m"
        )
        print(f"\033[92m       Erro: {form.errors['cpf'][0]}\033[0m")

    def test_xss_first_name_funcionario(self):
        """Testa proteção contra XSS no first_name."""
        print("\033[93m  → Testando proteção contra XSS no first_name...\033[0m")
        xss_data = self.valid_data_funcionario.copy()
        xss_data["first_name"] = '<script>alert("XSS")</script>'
        form = CadastrarFuncionarioForm(data=xss_data)
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)
        self.assertIn(
            "Entrada inválida: scripts não são permitidos.",
            str(form.errors["first_name"]),
        )
        print("\033[92m    ✅ Sucesso: XSS no first_name bloqueado!\033[0m")
        print(f"\033[92m       Erro: {form.errors['first_name'][0]}\033[0m")
