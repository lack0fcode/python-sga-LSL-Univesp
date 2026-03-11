from django.test import TestCase

from core.forms import CadastrarFuncionarioForm


class CadastrarFuncionarioFormTest(TestCase):
    """Testes abrangentes para CadastrarFuncionarioForm com foco em segurança."""

    def setUp(self):
        print("\033[94m🔍 Teste de unidade: Formulário Funcionário\033[0m")
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
        print("\033[92m  → Testando formulário válido com dados completos...\033[0m")
        form = CadastrarFuncionarioForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.cpf, "52998224725")
        self.assertEqual(user.username, "52998224725")  # Username definido como CPF
        self.assertTrue(user.check_password("testpass123"))
        print("\033[92m  ✅ Sucesso: Funcionário cadastrado com dados válidos!\033[0m")
        print(
            f"\033[92m     Dados: CPF={user.cpf}, Nome={user.first_name} {user.last_name}, Função={user.funcao}\033[0m"
        )

    def test_cpf_validation_valid(self):
        """Testa validação de CPF válido."""
        print("\033[92m  → Testando validação de CPFs válidos...\033[0m")
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
        print(
            "\033[92m  ✅ Sucesso: Todos os CPFs válidos passaram na validação!\033[0m"
        )
        print(f"\033[92m     CPFs testados: {', '.join(cpfs_validos)}\033[0m")

    def test_cpf_validation_invalid(self):
        """Testa validação de CPF inválido."""
        print("\033[92m  → Testando validação de CPFs inválidos...\033[0m")
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
        print("\033[92m  ✅ Sucesso: Todos os CPFs inválidos foram rejeitados!\033[0m")
        print(f"\033[92m     CPFs rejeitados: {', '.join(cpfs_invalidos)}\033[0m")

    def test_cpf_unique_constraint(self):
        """Testa constraint de unicidade do CPF."""
        print("\033[92m  → Testando unicidade do CPF...\033[0m")
        # Criar primeiro usuário
        form1 = CadastrarFuncionarioForm(data=self.valid_data)
        self.assertTrue(form1.is_valid())
        form1.save()

        # Tentar criar segundo usuário com mesmo CPF
        form2 = CadastrarFuncionarioForm(data=self.valid_data)
        self.assertFalse(form2.is_valid())
        self.assertIn("cpf", form2.errors)
        print("\033[92m  ✅ Sucesso: Unicidade do CPF corretamente aplicada!\033[0m")
        print(f"\033[92m     Erro: {form2.errors['cpf'][0]}\033[0m")

    def test_funcao_choices_valid(self):
        """Testa choices válidos para função."""
        print("\033[92m  → Testando funções válidas...\033[0m")
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
        print("\033[92m  ✅ Sucesso: Todas as funções válidas aceitas!\033[0m")
        print(f"\033[92m     Funções testadas: {', '.join(funcoes_validas)}\033[0m")

    def test_funcao_choices_invalid(self):
        """Testa choice inválido para função."""
        print("\033[92m  → Testando função inválida...\033[0m")
        data = self.valid_data.copy()
        data["funcao"] = "funcao_invalida"
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("funcao", form.errors)
        print("\033[92m  ✅ Sucesso: Função inválida corretamente rejeitada!\033[0m")
        print(f"\033[92m     Erro: {form.errors['funcao'][0]}\033[0m")

    def test_password_validation(self):
        """Testa validação de senha."""
        print("\033[92m  → Testando validação de senhas iguais...\033[0m")
        # Senhas iguais
        data = self.valid_data.copy()
        form = CadastrarFuncionarioForm(data=data)
        self.assertTrue(form.is_valid())

        print("\033[92m  → Testando senhas diferentes...\033[0m")
        # Senhas diferentes
        data["password2"] = "diferente"
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
        print(
            "\033[92m  ✅ Sucesso: Validação de senha funcionando corretamente!\033[0m"
        )
        print(
            f"\033[92m     Erro senhas diferentes: {form.errors['password2'][0]}\033[0m"
        )

    def test_password_too_short(self):
        """Testa senha muito curta."""
        print("\033[92m  → Testando senha muito curta...\033[0m")
        data = self.valid_data.copy()
        data["password1"] = "123"
        data["password2"] = "123"
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        # UserCreationForm coloca erros de validação de senha em password2
        self.assertIn("password2", form.errors)
        print("\033[92m  ✅ Sucesso: Senha curta corretamente rejeitada!\033[0m")
        print(f"\033[92m     Erro: {form.errors['password2'][0]}\033[0m")

    def test_email_validation(self):
        """Testa validação de email."""
        print("\033[92m  → Testando email válido...\033[0m")
        # Email válido
        data = self.valid_data.copy()
        form = CadastrarFuncionarioForm(data=data)
        self.assertTrue(form.is_valid())

        print("\033[92m  → Testando email inválido...\033[0m")
        # Email inválido
        data["email"] = "invalid-email"
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

        print("\033[92m  → Testando email vazio (opcional)...\033[0m")
        # Email vazio (opcional)
        data["email"] = ""
        form = CadastrarFuncionarioForm(data=data)
        self.assertTrue(form.is_valid())
        print(
            "\033[92m  ✅ Sucesso: Validação de email funcionando corretamente!\033[0m"
        )
        print(
            "\033[92m     Email válido: joao.silva@test.com | Email inválido rejeitado | Email vazio aceito\033[0m"
        )

    def test_required_fields(self):
        """Testa campos obrigatórios."""
        print("\033[92m  → Testando campos obrigatórios...\033[0m")
        # Campos obrigatórios do UserCreationForm + campos customizados
        required_fields = ["cpf", "funcao", "password1", "password2"]
        for field in required_fields:
            data = self.valid_data.copy()
            data[field] = ""
            form = CadastrarFuncionarioForm(data=data)
            self.assertFalse(form.is_valid(), f"Campo {field} deveria ser obrigatório")
            self.assertIn(field, form.errors)
        print("\033[92m  ✅ Sucesso: Todos os campos obrigatórios validados!\033[0m")
        print(
            f"\033[92m     Campos obrigatórios testados: {', '.join(required_fields)}\033[0m"
        )

    def test_username_field_hidden(self):
        """Testa que campo username é tratado corretamente."""
        print("\033[92m  → Testando que username é definido como CPF...\033[0m")
        # O username deve ser definido como CPF no save
        form = CadastrarFuncionarioForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, user.cpf)
        print("\033[92m  ✅ Sucesso: Username definido corretamente como CPF!\033[0m")
        print(f"\033[92m     Username/CPF: {user.username}\033[0m")

    def test_cpf_validation_digit2_ten_becomes_zero(self):
        """Testa CPF onde segundo dígito verificador seria 10, vira 0."""
        print("\033[92m  → Testando CPF com dígito 2 = 10 (vira 0)...\033[0m")
        # CPF 10000002810 faz digit2 = 10 -> 0, mas vamos alterar último dígito para falhar
        cpf_with_digit2_ten = "10000002811"  # Último dígito alterado para falhar
        data = self.valid_data.copy()
        data["cpf"] = cpf_with_digit2_ten
        data["username"] = cpf_with_digit2_ten
        form = CadastrarFuncionarioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("cpf", form.errors)
        print(
            "\033[92m  ✅ Sucesso: CPF com cálculo especial corretamente rejeitado!\033[0m"
        )
        print(
            f"\033[92m     CPF testado: {cpf_with_digit2_ten} | Erro: {form.errors['cpf'][0]}\033[0m"
        )

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
        print("\033[92m  → Testando CPF válido com dígito 1 = 10 (vira 0)...\033[0m")
        # CPF 10000000108: primeiro dígito calculado é 10 -> 0, segundo é 8
        cpf_valid_digit1_ten = "10000000108"
        data = self.valid_data.copy()
        data["cpf"] = cpf_valid_digit1_ten
        data["username"] = cpf_valid_digit1_ten
        form = CadastrarFuncionarioForm(data=data)
        self.assertTrue(form.is_valid())
        user = form.save()
        print("\033[92m  ✅ Sucesso: CPF válido com cálculo especial aceito!\033[0m")
        print(
            f"\033[92m     CPF válido: {cpf_valid_digit1_ten} | Usuário criado: {user.first_name} {user.last_name}\033[0m"
        )
