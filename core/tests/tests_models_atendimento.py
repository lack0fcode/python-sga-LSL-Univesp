from django.test import TestCase
from django.utils import timezone

from ..models import Atendimento, CustomUser, Paciente


class AtendimentoModelTest(TestCase):
    """Testes para o modelo Atendimento."""

    def setUp(self):
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
        atendimento = Atendimento.objects.create(
            paciente=self.paciente,
            funcionario=self.profissional,
        )
        self.assertEqual(atendimento.paciente, self.paciente)
        self.assertEqual(atendimento.funcionario, self.profissional)
        self.assertIsNotNone(atendimento.data_hora)

    def test_str_method(self):
        """Testa método __str__."""
        atendimento = Atendimento.objects.create(
            paciente=self.paciente,
            funcionario=self.profissional,
        )
        str_repr = str(atendimento)
        self.assertIn("Paciente Teste", str_repr)
        self.assertIn("22233344455", str_repr)

    def test_data_hora_auto_now_add(self):
        """Testa que data_hora é auto_now_add."""
        before = timezone.now()
        atendimento = Atendimento.objects.create(
            paciente=self.paciente,
            funcionario=self.profissional,
        )
        after = timezone.now()

        self.assertGreaterEqual(atendimento.data_hora, before)
        self.assertLessEqual(atendimento.data_hora, after)

    def test_foreign_keys_required(self):
        """Testa que ForeignKeys são obrigatórios."""
        # Sem paciente
        with self.assertRaises(Exception):
            Atendimento.objects.create(funcionario=self.profissional)

        # Sem funcionário
        with self.assertRaises(Exception):
            Atendimento.objects.create(paciente=self.paciente)
