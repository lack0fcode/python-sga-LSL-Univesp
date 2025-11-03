from django.test import TestCase

from ..forms import CadastrarFuncionarioForm
from ..models import CustomUser


class CadastrarFuncionarioFormTest(TestCase):
    """Testes abrangentes para CadastrarFuncionarioForm com foco em segurança."""

    def setUp(self):
        self.valid_data = {
            "cpf": "52998224725",  # CPF válido
            "username": "52998224725",
            "first_name": "João",
            "last_name": "Silva",
            "email": "joao.silva@test.com",
            "funcao": "administrador",
            "password1": "testpass123",
            "password2": "testpass123",
        }

    def test_valid_form(self):
        """Testa formulário válido."""
        form = CadastrarFuncionarioForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.cpf, "52998224725")
        self.assertEqual(user.username, "52998224725")  # Username definido como CPF
        self.assertTrue(user.check_password("testpass123"))

    def test_cpf_validation_valid(self):
        """Testa validação de CPF válido."""
        cpfs_validos = [
            "12345678909",  # CPF válido calculado
            "52998224725",  # CPF válido
            "11144477735",  # CPF válido
        ]
        for cpf in cpfs_validos:
            data = self.valid_data.copy()
            data["cpf"] = cpf
            data["username"] = cpf
            form = CadastrarFuncionarioForm(data=data)
            self.assertTrue(form.is_valid(), f"CPF {cpf} deveria ser válido")

    def test_cpf_validation_invalid(self):
        """Testa validação de CPF inválido."""
        cpfs_invalidos = [
            "123",  # Muito curto
            "123456789012",  # Muito longo
            "abc123def45",  # Não numérico
            "",  # Vazio
            "1234567890",  # 10 dígitos
            "1234567890123",  # 13 dígitos
        ]
        for cpf in cpfs_invalidos:
            data = self.valid_data.copy()
            data["cpf"] = cpf
            data["username"] = cpf
            form = CadastrarFuncionarioForm(data=data)
            self.assertFalse(form.is_valid(), f"CPF {cpf} deveria ser inválido")
            self.assertIn("cpf", form.errors)

    def test_cpf_unique_constraint(self):
        """Testa constraint de unicidade do CPF."""
        # Criar primeiro usuário
        form1 = CadastrarFuncionarioForm(data=self.valid_data)
        self.assertTrue(form1.is_valid())
        form1.save()

        # Tentar criar segundo usuário com mesmo CPF
        form2 = CadastrarFuncionarioForm(data=self.valid_data)
        self.assertFalse(form2.is_valid())
        self.assertIn("cpf", form2.errors)

    def test_sql_injection_cpf(self):
        """Testa proteção contra SQL injection no CPF."""
        malicious_data = self.valid_data.copy()
        malicious_data["cpf"] = "123'; DROP TABLE customuser; --"
        malicious_data["username"] = malicious_data["cpf"]
        form = CadastrarFuncionarioForm(data=malicious_data)
        self.assertFalse(form.is_valid())
        self.assertIn("cpf", form.errors)

    def test_xss_first_name(self):
        """Testa proteção contra XSS no first_name."""
        xss_data = self.valid_data.copy()
        xss_data["first_name"] = '<script>alert("XSS")</script>'
        form = CadastrarFuncionarioForm(data=xss_data)
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)
        self.assertIn(
            "Entrada inválida: scripts não são permitidos.",
            str(form.errors["first_name"]),
        )

    def test_funcao_choices_valid(self):
        """Testa choices válidos para função."""
        funcoes_validas = [
            "administrador",
            "recepcionista",
            "guiche",
            "profissional_saude",
        ]
        for funcao in funcoes_validas:
            data = self.valid_data.copy()
            data["funcao"] = funcao
            form = CadastrarFuncionarioForm(data=data)
            self.assertTrue(form.is_valid(), f"Função {funcao} deveria ser válida")

    def test_funcao_choices_invalid(self):
        """Testa choice inválido para função."""
        data = self.valid_data.copy()
        data["funcao"] = "funcao_invalida"
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("funcao", form.errors)

    def test_password_validation(self):
        """Testa validação de senha."""
        # Senhas iguais
        data = self.valid_data.copy()
        form = CadastrarFuncionarioForm(data=data)
        self.assertTrue(form.is_valid())

        # Senhas diferentes
        data["password2"] = "diferente"
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_password_too_short(self):
        """Testa senha muito curta."""
        data = self.valid_data.copy()
        data["password1"] = "123"
        data["password2"] = "123"
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        # UserCreationForm coloca erros de validação de senha em password2
        self.assertIn("password2", form.errors)

    def test_email_validation(self):
        """Testa validação de email."""
        # Email válido
        data = self.valid_data.copy()
        form = CadastrarFuncionarioForm(data=data)
        self.assertTrue(form.is_valid())

        # Email inválido
        data["email"] = "invalid-email"
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

        # Email vazio (opcional)
        data["email"] = ""
        form = CadastrarFuncionarioForm(data=data)
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        """Testa campos obrigatórios."""
        # Campos obrigatórios do UserCreationForm + campos customizados
        required_fields = ["cpf", "funcao", "password1", "password2"]
        for field in required_fields:
            data = self.valid_data.copy()
            data[field] = ""
            form = CadastrarFuncionarioForm(data=data)
            self.assertFalse(form.is_valid(), f"Campo {field} deveria ser obrigatório")
            self.assertIn(field, form.errors)

    def test_username_field_hidden(self):
        """Testa que campo username é tratado corretamente."""
        # O username deve ser definido como CPF no save
        form = CadastrarFuncionarioForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, user.cpf)

    def test_cpf_validation_digit2_ten_becomes_zero(self):
        """Testa CPF onde segundo dígito verificador seria 10, vira 0."""
        # CPF 10000002810 faz digit2 = 10 -> 0, mas vamos alterar último dígito para falhar
        cpf_with_digit2_ten = "10000002811"  # Último dígito alterado para falhar
        data = self.valid_data.copy()
        data["cpf"] = cpf_with_digit2_ten
        data["username"] = cpf_with_digit2_ten
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("cpf", form.errors)

    def test_cpf_validation_second_digit_check_fails(self):
        """Testa CPF que passa primeira verificação mas falha na segunda."""
        # CPF válido 52998224725, alterando último dígito
        cpf_second_digit_wrong = "52998224726"
        data = self.valid_data.copy()
        data["cpf"] = cpf_second_digit_wrong
        data["username"] = cpf_second_digit_wrong
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("cpf", form.errors)

    def test_cpf_validation_digit1_ten_becomes_zero(self):
        """Testa CPF onde primeiro dígito verificador seria 10, vira 0."""
        # CPF 10000000108 faz digit1 = 10 -> 0, mas vamos alterar penúltimo dígito para falhar
        cpf_with_digit1_ten = "10000000118"  # Penúltimo dígito alterado
        data = self.valid_data.copy()
        data["cpf"] = cpf_with_digit1_ten
        data["username"] = cpf_with_digit1_ten
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("cpf", form.errors)

    def test_cpf_validation_digit1_ten_valid_cpf(self):
        """Testa CPF válido onde primeiro dígito verificador é 10 (vira 0)."""
        # CPF 10000000108: primeiro dígito calculado é 10 -> 0, segundo é 8
        cpf_valid_digit1_ten = "10000000108"
        data = self.valid_data.copy()
        data["cpf"] = cpf_valid_digit1_ten
        data["username"] = cpf_valid_digit1_ten
        form = CadastrarFuncionarioForm(data=data)
        self.assertTrue(form.is_valid())
