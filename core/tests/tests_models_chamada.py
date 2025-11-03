from django.test import TestCase
from django.utils import timezone

from ..models import Chamada, ChamadaProfissional, CustomUser, Guiche, Paciente


class ChamadaModelTest(TestCase):
    """Testes para o modelo Chamada."""

    def setUp(self):
        self.guiche = Guiche.objects.create(numero=1)
        self.paciente = Paciente.objects.create(
            nome_completo="Paciente Chamada",
            tipo_senha="G",
            senha="G001",
        )

    def test_create_chamada_valid(self):
        """Testa criação de chamada válida."""
        chamada = Chamada.objects.create(
            paciente=self.paciente,
            guiche=self.guiche,
            acao="chamada",
        )
        self.assertEqual(chamada.paciente, self.paciente)
        self.assertEqual(chamada.guiche, self.guiche)
        self.assertEqual(chamada.acao, "chamada")

    def test_str_method(self):
        """Testa método __str__."""
        chamada = Chamada.objects.create(
            paciente=self.paciente,
            guiche=self.guiche,
            acao="chamada",
        )
        str_repr = str(chamada)
        self.assertIn("Chamada", str_repr)
        self.assertIn("G001", str_repr)
        self.assertIn("Guichê 1", str_repr)

    def test_acao_choices_valid(self):
        """Testa valores válidos para acao."""
        for acao in ["chamada", "reanuncio", "confirmado"]:
            chamada = Chamada.objects.create(
                paciente=self.paciente,
                guiche=self.guiche,
                acao=acao,
            )
            self.assertEqual(chamada.acao, acao)

    def test_acao_choices_invalid(self):
        """Testa valor inválido para acao."""
        # Django não valida choices automaticamente no banco
        chamada = Chamada.objects.create(
            paciente=self.paciente,
            guiche=self.guiche,
            acao="acao_invalida",
        )
        self.assertEqual(chamada.acao, "acao_invalida")  # Django permite

    def test_data_hora_auto_now_add(self):
        """Testa que data_hora é auto_now_add."""
        before = timezone.now()
        chamada = Chamada.objects.create(
            paciente=self.paciente,
            guiche=self.guiche,
            acao="chamada",
        )
        after = timezone.now()

        self.assertGreaterEqual(chamada.data_hora, before)
        self.assertLessEqual(chamada.data_hora, after)

    def test_ordering_meta(self):
        """Testa ordering -data_hora."""
        from time import sleep

        chamada1 = Chamada.objects.create(
            paciente=self.paciente,
            guiche=self.guiche,
            acao="chamada",
        )
        sleep(0.01)  # Pequena pausa para garantir timestamps diferentes
        chamada2 = Chamada.objects.create(
            paciente=self.paciente,
            guiche=self.guiche,
            acao="reanuncio",
        )

        chamadas = list(Chamada.objects.all())
        self.assertEqual(chamadas[0], chamada2)  # Mais recente primeiro
        self.assertEqual(chamadas[1], chamada1)

    def test_foreign_keys_required(self):
        """Testa que ForeignKeys são obrigatórios."""
        # Sem paciente
        with self.assertRaises(Exception):
            Chamada.objects.create(guiche=self.guiche, acao="chamada")

        # Sem guiche
        with self.assertRaises(Exception):
            Chamada.objects.create(paciente=self.paciente, acao="chamada")


class ChamadaProfissionalModelTest(TestCase):
    """Testes para o modelo ChamadaProfissional."""

    def setUp(self):
        self.profissional = CustomUser.objects.create_user(
            cpf="55566677788",
            username="55566677788",
            password="testpass",
            funcao="profissional_saude",
        )
        self.paciente = Paciente.objects.create(
            nome_completo="Paciente Profissional",
            tipo_senha="G",
            senha="G001",
        )

    def test_create_chamada_profissional_valid(self):
        """Testa criação de chamada profissional válida."""
        chamada = ChamadaProfissional.objects.create(
            paciente=self.paciente,
            profissional_saude=self.profissional,
            acao="chamada",
        )
        self.assertEqual(chamada.paciente, self.paciente)
        self.assertEqual(chamada.profissional_saude, self.profissional)
        self.assertEqual(chamada.acao, "chamada")

    def test_str_method(self):
        """Testa método __str__."""
        chamada = ChamadaProfissional.objects.create(
            paciente=self.paciente,
            profissional_saude=self.profissional,
            acao="chamada",
        )
        str_repr = str(chamada)
        self.assertIn("Chamada", str_repr)
        self.assertIn("G001", str_repr)
        # O modelo usa first_name do profissional
        self.assertIn(self.profissional.first_name, str_repr)

    def test_acao_choices_valid(self):
        """Testa valores válidos para acao."""
        for acao in ["chamada", "reanuncio", "confirmado", "encaminha"]:
            chamada = ChamadaProfissional.objects.create(
                paciente=self.paciente,
                profissional_saude=self.profissional,
                acao=acao,
            )
            self.assertEqual(chamada.acao, acao)

    def test_acao_choices_invalid(self):
        """Testa valor inválido para acao."""
        # Django não valida choices automaticamente no banco
        chamada = ChamadaProfissional.objects.create(
            paciente=self.paciente,
            profissional_saude=self.profissional,
            acao="acao_invalida",
        )
        self.assertEqual(chamada.acao, "acao_invalida")  # Django permite

    def test_data_hora_auto_now_add(self):
        """Testa que data_hora é auto_now_add."""
        before = timezone.now()
        chamada = ChamadaProfissional.objects.create(
            paciente=self.paciente,
            profissional_saude=self.profissional,
            acao="chamada",
        )
        after = timezone.now()

        self.assertGreaterEqual(chamada.data_hora, before)
        self.assertLessEqual(chamada.data_hora, after)

    def test_ordering_meta(self):
        """Testa ordering -data_hora."""
        chamada1 = ChamadaProfissional.objects.create(
            paciente=self.paciente,
            profissional_saude=self.profissional,
            acao="chamada",
        )
        # Pequeno delay para garantir ordem temporal
        import time

        time.sleep(0.001)
        chamada2 = ChamadaProfissional.objects.create(
            paciente=self.paciente,
            profissional_saude=self.profissional,
            acao="reanuncio",
        )

        chamadas = list(ChamadaProfissional.objects.all())
        self.assertEqual(chamadas[0], chamada2)  # Mais recente primeiro
        self.assertEqual(chamadas[1], chamada1)

    def test_foreign_keys_required(self):
        """Testa que ForeignKeys são obrigatórios."""
        # Sem paciente
        with self.assertRaises(Exception):
            ChamadaProfissional.objects.create(
                profissional_saude=self.profissional, acao="chamada"
            )

        # Sem profissional
        with self.assertRaises(Exception):
            ChamadaProfissional.objects.create(paciente=self.paciente, acao="chamada")
