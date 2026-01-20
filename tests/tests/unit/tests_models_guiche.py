from django.test import TestCase

from core.models import CustomUser, Guiche, Paciente


class GuicheModelTest(TestCase):
    """Testes para o modelo Guiche."""

    def setUp(self):
        self.funcionario = CustomUser.objects.create_user(
            cpf="44455566677",
            username="44455566677",
            password="testpass",
            funcao="guiche",
        )
        self.paciente = Paciente.objects.create(
            nome_completo="Paciente Guiche",
            tipo_senha="G",
            senha="G001",
        )

    def test_create_guiche_valid(self):
        """Testa criação de guichê válido."""
        guiche = Guiche.objects.create(
            numero=1,
            funcionario=self.funcionario,
        )
        self.assertEqual(guiche.numero, 1)
        self.assertEqual(guiche.funcionario, self.funcionario)
        self.assertFalse(guiche.em_atendimento)

    def test_str_method_with_funcionario(self):
        """Testa método __str__ com funcionário."""
        guiche = Guiche.objects.create(
            numero=1,
            funcionario=self.funcionario,
        )
        str_repr = str(guiche)
        self.assertIn("Guichê 1", str_repr)
        # O modelo usa first_name, então vamos verificar isso
        self.assertIn(self.funcionario.first_name, str_repr)

    def test_str_method_without_funcionario(self):
        """Testa método __str__ sem funcionário."""
        guiche = Guiche.objects.create(numero=2)
        str_repr = str(guiche)
        self.assertIn("Guichê 2", str_repr)
        self.assertIn("Livre", str_repr)

    def test_numero_unique(self):
        """Testa constraint de unicidade do numero."""
        Guiche.objects.create(numero=1)
        with self.assertRaises(Exception):
            Guiche.objects.create(numero=1)

    def test_campos_opcionais(self):
        """Testa campos opcionais."""
        guiche = Guiche.objects.create(numero=3)
        self.assertIsNone(guiche.funcionario)
        self.assertIsNone(guiche.senha_atendida)
        self.assertIsNone(guiche.user)
        self.assertFalse(guiche.em_atendimento)

    def test_em_atendimento_default_false(self):
        """Testa que em_atendimento tem default False."""
        guiche = Guiche.objects.create(numero=4)
        self.assertFalse(guiche.em_atendimento)

    def test_one_to_one_user(self):
        """Testa relacionamento OneToOne com user."""
        guiche = Guiche.objects.create(
            numero=5,
            user=self.funcionario,
        )
        self.assertEqual(guiche.user, self.funcionario)

    def test_foreign_key_senha_atendida(self):
        """Testa ForeignKey senha_atendida."""
        guiche = Guiche.objects.create(
            numero=6,
            senha_atendida=self.paciente,
        )
        self.assertEqual(guiche.senha_atendida, self.paciente)
