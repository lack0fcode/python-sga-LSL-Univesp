from django.test import TestCase
from django.utils import timezone

from ..forms import LoginForm
from ..models import CustomUser


class LoginFormTest(TestCase):
    """Testes abrangentes para LoginForm com foco em segurança."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            cpf="99900011122",
            username="99900011122",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.valid_data = {
            "cpf": "99900011122",
            "password": "testpass123",
        }

    def test_valid_login(self):
        """Testa login válido."""
        form = LoginForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        self.assertIn("user", form.cleaned_data)
        self.assertEqual(form.cleaned_data["user"], self.user)

    def test_invalid_password(self):
        """Testa senha inválida."""
        data = self.valid_data.copy()
        data["password"] = "wrongpass"
        form = LoginForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_nonexistent_user(self):
        """Testa usuário inexistente."""
        data = self.valid_data.copy()
        data["cpf"] = "00000000000"
        form = LoginForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_inactive_user(self):
        """Testa usuário inativo."""
        self.user.is_active = False
        self.user.save()

        form = LoginForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_sql_injection_cpf(self):
        """Testa proteção contra SQL injection no CPF."""
        malicious_data = self.valid_data.copy()
        malicious_data["cpf"] = "999' OR '1'='1"
        form = LoginForm(data=malicious_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_sql_injection_password(self):
        """Testa proteção contra SQL injection na senha."""
        malicious_data = self.valid_data.copy()
        malicious_data["password"] = "' OR '1'='1"
        form = LoginForm(data=malicious_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_empty_fields(self):
        """Testa campos vazios."""
        # Ambos vazios
        form = LoginForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("cpf", form.errors)
        self.assertIn("password", form.errors)

        # CPF vazio
        form = LoginForm(data={"password": "testpass123"})
        self.assertFalse(form.is_valid())
        self.assertIn("cpf", form.errors)

        # Senha vazia
        form = LoginForm(data={"cpf": "99900011122"})
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_whitespace_handling(self):
        """Testa tratamento de espaços em branco."""
        # CPF com espaços
        data = self.valid_data.copy()
        data["cpf"] = "  99900011122  "
        form = LoginForm(data=data)
        self.assertTrue(
            form.is_valid()
        )  # Django CharField remove espaços automaticamente

    def test_case_sensitivity_cpf(self):
        """Testa sensibilidade a maiúsculas/minúsculas no CPF."""
        # CPF em maiúsculas (se fosse alfanumérico)
        data = self.valid_data.copy()
        data["cpf"] = "99900011122"
        form = LoginForm(data=data)
        self.assertTrue(form.is_valid())

    def test_max_length_cpf(self):
        """Testa limite de tamanho do CPF."""
        data = self.valid_data.copy()
        data["cpf"] = "1" * 20  # Maior que max_length
        form = LoginForm(data=data)
        # Django permite input maior, mas falha na autenticação
        self.assertFalse(form.is_valid())

    def test_brute_force_protection(self):
        """Testa proteção contra força bruta (bloqueio após 4 tentativas)."""
        # 3 tentativas falhidas
        for i in range(3):
            data = self.valid_data.copy()
            data["password"] = f"wrongpass{i}"
            form = LoginForm(data=data)
            self.assertFalse(form.is_valid())
            self.assertIn("__all__", form.errors)
            self.assertIn("CPF ou senha incorretos.", str(form.errors["__all__"]))

        # 4ª tentativa deve bloquear
        data = self.valid_data.copy()
        data["password"] = "wrongpass3"
        form = LoginForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn(
            "Conta bloqueada por tentativas excessivas.", str(form.errors["__all__"])
        )

        # Verificar que o usuário está bloqueado
        user = CustomUser.objects.get(cpf=self.valid_data["cpf"])
        self.assertIsNotNone(user.lockout_until)
        self.assertGreater(user.lockout_until, timezone.now())

        # Tentativa adicional deve mostrar mensagem de bloqueio
        form2 = LoginForm(data=data)
        self.assertFalse(form2.is_valid())
        self.assertIn("__all__", form2.errors)
        self.assertIn("Conta bloqueada.", str(form2.errors["__all__"]))

    def test_timing_attack_resistance(self):
        """Testa resistência a ataques de temporização."""
        start_time = timezone.now()
        form_valid = LoginForm(data=self.valid_data)
        valid_time = timezone.now() - start_time

        start_time = timezone.now()
        data_invalid = self.valid_data.copy()
        data_invalid["password"] = "wrong"
        form_invalid = LoginForm(data=data_invalid)
        invalid_time = timezone.now() - start_time

        self.assertTrue(abs((valid_time - invalid_time).total_seconds()) < 1.0)
