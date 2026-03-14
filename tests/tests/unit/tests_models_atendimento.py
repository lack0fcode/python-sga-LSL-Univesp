from django.test import TestCase
from django.utils import timezone

from core.models import Atendimento, CustomUser, Paciente


class AtendimentoModelTest(TestCase):
    """Testes para o modelo Atendimento."""

    def setUp(self):
        print("\033[94m🔍 Teste de unidade: Modelo Atendimento\033[0m")  # Azul
        self.profissional = CustomUser.objects.create_user(
            cpf="22233344455",
            username="22233344455",
            password="testpass",
            funcao="profissional_saude",
        )
        self.paciente = Paciente.objects.create(
            nome_completo="Paciente Teste",
            tipo_senha="G",
            senha="G001",
        )

    def test_create_atendimento_valid(self):
        """Testa criação de atendimento válido."""
        print(
            "\033[92m  → Criando atendimento válido com paciente e funcionário...\033[0m"
        )  # Verde
        atendimento = Atendimento.objects.create(
            paciente=self.paciente,
            funcionario=self.profissional,
        )
        self.assertEqual(atendimento.paciente, self.paciente)
        self.assertEqual(atendimento.funcionario, self.profissional)
        self.assertIsNotNone(atendimento.data_hora)
        print("\033[92m  ✅ Sucesso: Atendimento criado com dados válidos!\033[0m")
        print(
            f"\033[92m     Dados: Paciente={atendimento.paciente.nome_completo}, Funcionário={atendimento.funcionario.cpf}, Data/Hora={atendimento.data_hora}\033[0m"
        )

    def test_str_method(self):
        """Testa método __str__."""
        print("\033[92m  → Testando representação string do atendimento...\033[0m")
        atendimento = Atendimento.objects.create(
            paciente=self.paciente,
            funcionario=self.profissional,
        )
        str_repr = str(atendimento)
        self.assertIn("Paciente Teste", str_repr)
        self.assertIn("22233344455", str_repr)
        print(
            "\033[92m  ✅ Sucesso: Representação string contém nome do paciente e CPF do funcionário!\033[0m"
        )
        print(f"\033[92m     String: {str_repr}\033[0m")

    def test_data_hora_auto_now_add(self):
        """Testa que data_hora é auto_now_add."""
        print(
            "\033[92m  → Verificando se data/hora é definida automaticamente...\033[0m"
        )
        before = timezone.now()
        atendimento = Atendimento.objects.create(
            paciente=self.paciente,
            funcionario=self.profissional,
        )
        after = timezone.now()

        self.assertGreaterEqual(atendimento.data_hora, before)
        self.assertLessEqual(atendimento.data_hora, after)
        print(
            "\033[92m  ✅ Sucesso: Data/hora definida automaticamente no momento da criação!\033[0m"
        )
        print(f"\033[92m     Data/Hora: {atendimento.data_hora}\033[0m")

    def test_foreign_keys_required(self):
        """Testa que ForeignKeys são obrigatórios."""
        print("\033[92m  → Testando que chaves estrangeiras são obrigatórias...\033[0m")
        # Sem paciente
        with self.assertRaises(Exception):
            Atendimento.objects.create(funcionario=self.profissional)

        # Sem funcionário
        with self.assertRaises(Exception):
            Atendimento.objects.create(paciente=self.paciente)
        print(
            "\033[92m  ✅ Sucesso: Chaves estrangeiras corretamente obrigatórias!\033[0m"
        )
