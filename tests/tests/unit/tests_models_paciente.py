from django.test import TestCase
from django.utils import timezone

from core.models import CustomUser, Paciente


class PacienteModelTest(TestCase):
    """Testes abrangentes para o modelo Paciente."""

    def setUp(self):
        print("\033[94m🔍 Teste de unidade: Modelo Paciente\033[0m")
        self.profissional = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="testpass",
            funcao="profissional_saude",
            first_name="Dr.",
            last_name="Teste",
        )
        self.paciente_data = {
            "nome_completo": "Maria Oliveira Santos",
            "tipo_senha": "G",
            "senha": "G001",
            "cartao_sus": "123456789012345",
            "profissional_saude": self.profissional,
            "telefone_celular": "(11) 99999-9999",
            "observacoes": "Paciente de teste",
        }

    def test_create_paciente_valid(self):
        """Testa criação de paciente válido."""
        paciente = Paciente.objects.create(**self.paciente_data)
        self.assertEqual(paciente.nome_completo, "Maria Oliveira Santos")
        self.assertEqual(paciente.tipo_senha, "G")
        self.assertEqual(paciente.senha, "G001")
        self.assertFalse(paciente.atendido)  # default False

    def test_str_method(self):
        """Testa método __str__."""
        paciente = Paciente.objects.create(**self.paciente_data)
        str_repr = str(paciente)
        self.assertIn("Maria Oliveira Santos", str_repr)
        self.assertIn("G001", str_repr)

    def test_campos_opcionais(self):
        """Testa campos opcionais."""
        data_minima = {
            "nome_completo": "João Silva",
        }
        paciente = Paciente.objects.create(**data_minima)
        self.assertIsNone(paciente.tipo_senha)
        self.assertIsNone(paciente.senha)
        self.assertIsNone(paciente.cartao_sus)
        self.assertIsNone(paciente.profissional_saude)
        self.assertIsNone(paciente.telefone_celular)
        self.assertIsNone(paciente.observacoes)
        self.assertFalse(paciente.atendido)

    def test_tipo_senha_choices_valid(self):
        """Testa valores válidos para tipo_senha."""
        tipos_validos = ["E", "C", "P", "G", "D", "A", "NH", "H", "U"]
        for tipo in tipos_validos:
            data = self.paciente_data.copy()
            data["tipo_senha"] = tipo
            data["senha"] = f"{tipo}001"
            paciente = Paciente.objects.create(**data)
            self.assertEqual(paciente.tipo_senha, tipo)

    def test_tipo_senha_choices_invalid(self):
        """Testa valor inválido para tipo_senha."""
        # Django não valida choices automaticamente no banco
        data = self.paciente_data.copy()
        data["tipo_senha"] = "X"  # Inválido
        paciente = Paciente.objects.create(**data)
        self.assertEqual(paciente.tipo_senha, "X")  # Django permite

    def test_senha_max_length(self):
        """Testa limite de tamanho da senha."""
        # Django não valida max_length automaticamente no banco
        data = self.paciente_data.copy()
        data["senha"] = "A" * 6  # Exatamente max_length=6
        paciente = Paciente.objects.create(**data)
        self.assertEqual(len(paciente.senha), 6)

    def test_cartao_sus_max_length(self):
        """Testa limite de tamanho do cartão SUS."""
        # Django não valida max_length automaticamente no banco
        data = self.paciente_data.copy()
        data["cartao_sus"] = "1" * 20  # Exatamente max_length=20
        paciente = Paciente.objects.create(**data)
        self.assertEqual(len(paciente.cartao_sus), 20)

    def test_nome_completo_max_length(self):
        """Testa limite de tamanho do nome completo."""
        # Django não valida max_length automaticamente no banco
        data = self.paciente_data.copy()
        data["nome_completo"] = "A" * 255  # Exatamente max_length=255
        paciente = Paciente.objects.create(**data)
        self.assertEqual(len(paciente.nome_completo), 255)

    def test_observacoes_max_length(self):
        """Testa limite de tamanho das observações."""
        # Django não valida max_length automaticamente no banco
        data = self.paciente_data.copy()
        data["observacoes"] = "A" * 255  # Exatamente max_length=255
        paciente = Paciente.objects.create(**data)
        self.assertEqual(len(paciente.observacoes), 255)

    def test_telefone_celular_max_length(self):
        """Testa limite de tamanho do telefone."""
        # Django não valida max_length automaticamente no banco
        data = self.paciente_data.copy()
        data["telefone_celular"] = "1" * 20  # Exatamente max_length=20
        paciente = Paciente.objects.create(**data)
        self.assertEqual(len(paciente.telefone_celular), 20)

    def test_telefone_e164_valid_formats(self):
        """Testa método telefone_e164 com formatos válidos."""
        test_cases = [
            ("(11) 99999-9999", "+5511999999999"),
            ("5511999999999", "+5511999999999"),
        ]
        for telefone_input, expected in test_cases:
            data = self.paciente_data.copy()
            data["telefone_celular"] = telefone_input
            paciente = Paciente.objects.create(**data)
            self.assertEqual(paciente.telefone_e164(), expected)

    def test_telefone_e164_invalid_formats(self):
        """Testa método telefone_e164 com formatos inválidos."""
        invalid_cases = [
            "(11) 9999-9999",  # Sem 9 no início
            "1199999999",  # 10 dígitos
            "119999999999",  # 12 dígitos
            "551199999999",  # 12 dígitos com 55
            "abc123",  # Não numérico
            "",  # Vazio
        ]
        for telefone_input in invalid_cases:
            data = self.paciente_data.copy()
            data["telefone_celular"] = telefone_input
            paciente = Paciente.objects.create(**data)
            self.assertIsNone(paciente.telefone_e164())

    def test_telefone_e164_none_when_empty(self):
        """Testa telefone_e164 retorna None quando telefone é vazio."""
        data = self.paciente_data.copy()
        data["telefone_celular"] = None
        paciente = Paciente.objects.create(**data)
        self.assertIsNone(paciente.telefone_e164())

        paciente.telefone_celular = ""
        paciente.save()
        self.assertIsNone(paciente.telefone_e164())

    def test_horario_agendamento_auto_now_add(self):
        """Testa que horario_geracao_senha é auto_now_add."""
        before = timezone.now()
        paciente = Paciente.objects.create(**self.paciente_data)
        after = timezone.now()

        self.assertIsNotNone(paciente.horario_geracao_senha)
        self.assertGreaterEqual(paciente.horario_geracao_senha, before)
        self.assertLessEqual(paciente.horario_geracao_senha, after)

    def test_atendido_default_false(self):
        """Testa que atendido tem default False."""
        paciente = Paciente.objects.create(**self.paciente_data)
        self.assertFalse(paciente.atendido)

    def test_foreign_key_profissional_saude(self):
        """Testa relacionamento ForeignKey com profissional_saude."""
        paciente = Paciente.objects.create(**self.paciente_data)
        self.assertEqual(paciente.profissional_saude, self.profissional)

    def test_foreign_key_profissional_saude_null(self):
        """Testa ForeignKey profissional_saude pode ser null."""
        data = self.paciente_data.copy()
        data.pop("profissional_saude")
        paciente = Paciente.objects.create(**data)
        self.assertIsNone(paciente.profissional_saude)

    def test_recadastro_com_mesmo_cartao_sus_reutiliza_registro(self):
        """Cadastra um paciente com cartao_sus e cadastra novamente; não deve criar duplicata."""
        from django.urls import reverse

        # Criar usuário recepcionista e autenticar
        recep = CustomUser.objects.create_user(
            cpf="22233344455",
            username="22233344455",
            password="testpass",
            funcao="recepcionista",
            first_name="Recep",
            last_name="Usuario",
        )
        self.client.force_login(recep)

        url = reverse("recepcionista:cadastrar_paciente")

        post_data = {
            "nome_completo": "Paciente Repetido",
            "tipo_senha": "G",
            "cartao_sus": "999888777666555",
            "telefone_celular": "(11) 99999-9999",
            "observacoes": "Primeiro cadastro",
        }

        # Primeiro cadastro cria o registro
        resp1 = self.client.post(url, post_data, follow=True)
        self.assertEqual(
            Paciente.objects.filter(cartao_sus="999888777666555").count(), 1
        )
        primeiro = Paciente.objects.get(cartao_sus="999888777666555")

        # Modifica o nome e cadastra novamente com mesmo cartao_sus
        post_data2 = post_data.copy()
        post_data2["nome_completo"] = "Paciente Repetido Atualizado"
        post_data2["observacoes"] = "Segundo cadastro - retorno"

        resp2 = self.client.post(url, post_data2, follow=True)

        # Deve continuar existindo apenas um registro com o mesmo cartao_sus
        self.assertEqual(
            Paciente.objects.filter(cartao_sus="999888777666555").count(), 1
        )
        atualizado = Paciente.objects.get(cartao_sus="999888777666555")

        # Verifica que o mesmo id foi atualizado
        self.assertEqual(primeiro.id, atualizado.id)
        self.assertIn("retorno", (atualizado.observacoes or "").lower())

    def test_recadastro_gera_nova_senha_quando_reutiliza_registro(self):
        """Ao recadastrar com mesmo cartao_sus, deve ser gerada nova senha (diferente da anterior)."""
        from django.urls import reverse

        recep = CustomUser.objects.create_user(
            cpf="33344455566",
            username="33344455566",
            password="testpass",
            funcao="recepcionista",
            first_name="Recep2",
            last_name="Usuario",
        )
        self.client.force_login(recep)

        url = reverse("recepcionista:cadastrar_paciente")

        post_data = {
            "nome_completo": "Paciente Senha1",
            "tipo_senha": "G",
            "cartao_sus": "555666777888999",
            "telefone_celular": "(11) 99999-9999",
            "observacoes": "Primeiro cadastro",
        }

        resp1 = self.client.post(url, post_data, follow=True)
        p1 = Paciente.objects.get(cartao_sus="555666777888999")
        senha1 = p1.senha
        self.assertIsNotNone(senha1)

        # Recadastrar com outro tipo de senha
        post_data2 = post_data.copy()
        post_data2["tipo_senha"] = "E"
        resp2 = self.client.post(url, post_data2, follow=True)
        p2 = Paciente.objects.get(cartao_sus="555666777888999")
        senha2 = p2.senha

        self.assertIsNotNone(senha2)
        self.assertNotEqual(senha1, senha2)
        # E a nova senha deve começar com o novo tipo solicitado
        self.assertTrue(senha2.startswith("E"))
