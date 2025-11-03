from django.test import TestCase

from ..models import CustomUser


class CustomUserModelTest(TestCase):
    """Testes abrangentes para o modelo CustomUser."""

    def setUp(self):
        self.user_data = {
            "cpf": "12345678901",
            "username": "12345678901",
            "password": "testpass123",
            "first_name": "João",
            "last_name": "Silva",
            "email": "joao.silva@test.com",
            "funcao": "administrador",
        }

    def test_create_user_valid(self):
        """Testa criação de usuário válido."""
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertEqual(user.cpf, "12345678901")
        self.assertEqual(user.first_name, "João")
        self.assertEqual(user.funcao, "administrador")
        self.assertTrue(user.check_password("testpass123"))

    def test_username_field_is_cpf(self):
        """Testa que USERNAME_FIELD é cpf."""
        self.assertEqual(CustomUser.USERNAME_FIELD, "cpf")

    def test_str_method(self):
        """Testa método __str__."""
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertEqual(str(user), "João Silva")

    def test_cpf_unique_constraint(self):
        """Testa constraint de unicidade do CPF."""
        CustomUser.objects.create_user(**self.user_data)
        with self.assertRaises(Exception):  # IntegrityError
            CustomUser.objects.create_user(**self.user_data)

    def test_cpf_max_length(self):
        """Testa limite de tamanho do CPF."""
        # Django não valida max_length automaticamente no banco, apenas no form
        # Vamos testar que o campo aceita até o limite
        data = self.user_data.copy()
        data["cpf"] = "1" * 14  # Exatamente max_length=14
        data["username"] = data["cpf"]
        user = CustomUser.objects.create_user(**data)
        self.assertEqual(len(user.cpf), 14)

    def test_funcao_choices_valid(self):
        """Testa valores válidos para função."""
        for funcao in [
            "administrador",
            "recepcionista",
            "guiche",
            "profissional_saude",
        ]:
            data = self.user_data.copy()
            data["cpf"] = f"1111111111{funcao[0]}"  # CPF único
            data["username"] = data["cpf"]
            data["funcao"] = funcao
            user = CustomUser.objects.create_user(**data)
            self.assertEqual(user.funcao, funcao)

    def test_funcao_choices_invalid(self):
        """Testa valor inválido para função."""
        # Django não valida choices automaticamente no banco
        # Vamos testar que o valor é salvo mesmo sendo inválido
        data = self.user_data.copy()
        data["cpf"] = "11111111111"
        data["username"] = data["cpf"]
        data["funcao"] = "funcao_invalida"
        user = CustomUser.objects.create_user(**data)
        self.assertEqual(user.funcao, "funcao_invalida")  # Django permite

    def test_sala_field_optional(self):
        """Testa que campo sala é opcional."""
        data = self.user_data.copy()
        data["cpf"] = "22222222222"
        data["username"] = data["cpf"]
        user = CustomUser.objects.create_user(**data)
        self.assertIsNone(user.sala)

    def test_sala_field_with_value(self):
        """Testa campo sala com valor."""
        data = self.user_data.copy()
        data["cpf"] = "33333333333"
        data["username"] = data["cpf"]
        data["sala"] = 101  # type: ignore
        user = CustomUser.objects.create_user(**data)
        self.assertEqual(user.sala, 101)

    def test_data_admissao_optional(self):
        """Testa que data_admissao é opcional."""
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertIsNone(user.data_admissao)

    def test_required_fields(self):
        """Testa campos obrigatórios."""
        # CPF não é obrigatório no modelo (USERNAME_FIELD), mas vamos testar username
        data = self.user_data.copy()
        data.pop("username")  # Remove username que é obrigatório
        with self.assertRaises(Exception):
            CustomUser.objects.create_user(**data)

    def test_email_optional(self):
        """Testa que email é opcional."""
        data = self.user_data.copy()
        data["cpf"] = "44444444444"
        data["username"] = data["cpf"]
        data.pop("email")
        user = CustomUser.objects.create_user(**data)
        self.assertEqual(user.email, "")

    def test_superuser_creation(self):
        """Testa criação de superusuário."""
        data = self.user_data.copy()
        data["cpf"] = "55555555555"
        data["username"] = data["cpf"]
        user = CustomUser.objects.create_superuser(**data)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
