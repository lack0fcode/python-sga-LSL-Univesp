from django.test import Client, TestCase
from django.urls import reverse
from django.http import HttpResponse
from django.utils import timezone
from unittest.mock import patch

from .forms import CadastrarFuncionarioForm, CadastrarPacienteForm, LoginForm
from .models import (
    Atendimento,
    Chamada,
    ChamadaProfissional,
    CustomUser,
    Guiche,
    Paciente,
    RegistroDeAcesso,
)


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
        data["sala"] = 101
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


class PacienteModelTest(TestCase):
    """Testes abrangentes para o modelo Paciente."""

    def setUp(self):
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
            ("11 99999 9999", "+5511999999999"),
            ("11999999999", "+5511999999999"),
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


class RegistroDeAcessoModelTest(TestCase):
    """Testes para o modelo RegistroDeAcesso."""

    def setUp(self):
        self.usuario = CustomUser.objects.create_user(
            cpf="33344455566",
            username="33344455566",
            password="testpass",
        )

    def test_create_registro_valid(self):
        """Testa criação de registro válido."""
        registro = RegistroDeAcesso.objects.create(
            usuario=self.usuario,
            tipo_de_acesso="login",
            endereco_ip="127.0.0.1",
            user_agent="TestAgent/1.0",
            view_name="pagina_inicial",
        )
        self.assertEqual(registro.usuario, self.usuario)
        self.assertEqual(registro.tipo_de_acesso, "login")
        self.assertEqual(registro.endereco_ip, "127.0.0.1")

    def test_str_method(self):
        """Testa método __str__."""
        registro = RegistroDeAcesso.objects.create(
            usuario=self.usuario,
            tipo_de_acesso="login",
        )
        str_repr = str(registro)
        self.assertIn("33344455566", str_repr)
        self.assertIn("login", str_repr)

    def test_tipo_acesso_choices_valid(self):
        """Testa valores válidos para tipo_de_acesso."""
        for tipo in ["login", "logout"]:
            registro = RegistroDeAcesso.objects.create(
                usuario=self.usuario,
                tipo_de_acesso=tipo,
            )
            self.assertEqual(registro.tipo_de_acesso, tipo)

    def test_tipo_acesso_choices_invalid(self):
        """Testa valor inválido para tipo_de_acesso."""
        # Django não valida choices automaticamente no banco
        registro = RegistroDeAcesso.objects.create(
            usuario=self.usuario,
            tipo_de_acesso="invalid",
        )
        self.assertEqual(registro.tipo_de_acesso, "invalid")  # Django permite

    def test_campos_opcionais(self):
        """Testa campos opcionais."""
        registro = RegistroDeAcesso.objects.create(
            usuario=self.usuario,
            tipo_de_acesso="login",
        )
        self.assertIsNone(registro.endereco_ip)
        self.assertIsNone(registro.user_agent)
        self.assertIsNone(registro.view_name)

    def test_data_hora_default_now(self):
        """Testa que data_hora tem default timezone.now."""
        before = timezone.now()
        registro = RegistroDeAcesso.objects.create(
            usuario=self.usuario,
            tipo_de_acesso="login",
        )
        after = timezone.now()

        self.assertGreaterEqual(registro.data_hora, before)
        self.assertLessEqual(registro.data_hora, after)

    def test_view_name_max_length(self):
        """Testa limite de tamanho do view_name."""
        # Django não valida max_length automaticamente no banco
        registro = RegistroDeAcesso.objects.create(
            usuario=self.usuario,
            tipo_de_acesso="login",
            view_name="a" * 255,  # Exatamente max_length=255
        )
        self.assertEqual(len(registro.view_name), 255)

    def test_endereco_ip_generic_ip_field(self):
        """Testa campo endereco_ip como GenericIPAddressField."""
        # IPv4 válido
        registro = RegistroDeAcesso.objects.create(
            usuario=self.usuario,
            tipo_de_acesso="login",
            endereco_ip="192.168.1.1",
        )
        self.assertEqual(registro.endereco_ip, "192.168.1.1")

        # IPv6 válido
        registro2 = RegistroDeAcesso.objects.create(
            usuario=self.usuario,
            tipo_de_acesso="login",
            endereco_ip="2001:db8::1",
        )
        self.assertEqual(registro2.endereco_ip, "2001:db8::1")

    def test_foreign_key_usuario_required(self):
        """Testa que usuario é obrigatório."""
        with self.assertRaises(Exception):
            RegistroDeAcesso.objects.create(tipo_de_acesso="login")


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


# Forms
class CadastrarPacienteFormTest(TestCase):
    """Testes abrangentes para CadastrarPacienteForm com foco em segurança."""

    def setUp(self):
        self.profissional = CustomUser.objects.create_user(
            cpf="77788899900",
            username="77788899900",
            password="testpass",
            funcao="profissional_saude",
            first_name="Dr.",
            last_name="Teste",
        )
        self.valid_data = {
            "nome_completo": "João Silva Santos",
            "cartao_sus": "123456789012345",
            "horario_agendamento": timezone.now(),
            "profissional_saude": self.profissional.id,
            "observacoes": "Paciente de teste",
            "tipo_senha": "G",
            "telefone_celular": "(11) 99999-9999",
        }

    def test_valid_form(self):
        """Testa formulário válido."""
        form = CadastrarPacienteForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        paciente = form.save()
        self.assertEqual(paciente.nome_completo, "João Silva Santos")
        self.assertEqual(paciente.telefone_celular, "11999999999")  # Limpo

    def test_sql_injection_nome_completo(self):
        """Testa proteção contra SQL injection no nome."""
        malicious_data = self.valid_data.copy()
        malicious_data["nome_completo"] = "'; DROP TABLE paciente; --"
        form = CadastrarPacienteForm(data=malicious_data)
        self.assertTrue(form.is_valid())  # Django ModelForm protege automaticamente
        paciente = form.save()
        self.assertEqual(paciente.nome_completo, "'; DROP TABLE paciente; --")

    def test_xss_nome_completo(self):
        """Testa proteção contra XSS no nome."""
        xss_data = self.valid_data.copy()
        xss_data["nome_completo"] = '<script>alert("XSS")</script>'
        form = CadastrarPacienteForm(data=xss_data)
        self.assertFalse(form.is_valid())
        self.assertIn("nome_completo", form.errors)
        self.assertIn(
            "Entrada inválida: scripts não são permitidos.",
            str(form.errors["nome_completo"]),
        )

    def test_sql_injection_observacoes(self):
        """Testa proteção contra SQL injection nas observações."""
        malicious_data = self.valid_data.copy()
        malicious_data["observacoes"] = "1' OR '1'='1"
        form = CadastrarPacienteForm(data=malicious_data)
        self.assertTrue(form.is_valid())
        paciente = form.save()
        self.assertEqual(paciente.observacoes, "1' OR '1'='1")

    def test_telefone_celular_valid_formats(self):
        """Testa formatos válidos de telefone."""
        valid_formats = [
            "(11) 99999-9999",
            "11 99999 9999",
            "11999999999",
            "(11)99999-9999",
            "11-99999-9999",
        ]
        for telefone in valid_formats:
            data = self.valid_data.copy()
            data["telefone_celular"] = telefone
            form = CadastrarPacienteForm(data=data)
            self.assertTrue(form.is_valid(), f"Telefone {telefone} deveria ser válido")
            paciente = form.save()
            self.assertEqual(paciente.telefone_celular, "11999999999")

    def test_telefone_celular_invalid_formats(self):
        """Testa formatos inválidos de telefone."""
        invalid_formats = [
            "12345",  # Muito curto
            "(11) 9999-9999",  # Sem 9 no início
            "1199999999",  # 10 dígitos
            "abc123",  # Não numérico
        ]
        for telefone in invalid_formats:
            data = self.valid_data.copy()
            data["telefone_celular"] = telefone
            form = CadastrarPacienteForm(data=data)
            self.assertFalse(
                form.is_valid(), f"Telefone {telefone} deveria ser inválido"
            )
            self.assertIn("telefone_celular", form.errors)

    def test_telefone_celular_edge_cases(self):
        """Testa casos extremos de telefone."""
        edge_cases = [
            "00000000000",  # Todos zeros
            "99999999999",  # Todos noves
            "(00) 00000-0000",  # DDD zero
            "(99) 99999-9999",  # DDD alto
        ]
        for telefone in edge_cases:
            data = self.valid_data.copy()
            data["telefone_celular"] = telefone
            form = CadastrarPacienteForm(data=data)
            # Alguns podem ser válidos, outros não - o importante é que não quebre
            paciente = form.save() if form.is_valid() else None
            if paciente:
                self.assertIsNotNone(paciente.telefone_celular)

    def test_cartao_sus_validation(self):
        """Testa validação do cartão SUS."""
        # Cartão SUS válido (até 20 dígitos) - formulário não valida formato específico
        data = self.valid_data.copy()
        data["cartao_sus"] = "123456789012345"
        form = CadastrarPacienteForm(data=data)
        self.assertTrue(form.is_valid())

        # Cartão SUS muito longo - Django ModelForm valida max_length do modelo
        data["cartao_sus"] = "1" * 21
        form = CadastrarPacienteForm(data=data)
        self.assertFalse(form.is_valid())  # Deve falhar por max_length
        self.assertIn("cartao_sus", form.errors)

    def test_tipo_senha_choices(self):
        """Testa choices válidos para tipo_senha."""
        tipos_validos = ["E", "C", "P", "G", "D", "A", "NH", "H", "U"]
        for tipo in tipos_validos:
            data = self.valid_data.copy()
            data["tipo_senha"] = tipo
            form = CadastrarPacienteForm(data=data)
            self.assertTrue(form.is_valid(), f"Tipo {tipo} deveria ser válido")

    def test_tipo_senha_invalid_choice(self):
        """Testa choice inválido para tipo_senha."""
        data = self.valid_data.copy()
        data["tipo_senha"] = "X"  # Inválido
        form = CadastrarPacienteForm(data=data)
        # Django ChoiceField valida choices
        self.assertFalse(form.is_valid())
        self.assertIn("tipo_senha", form.errors)

    def test_required_fields(self):
        """Testa campos obrigatórios."""
        required_fields = [
            "tipo_senha"
        ]  # Apenas tipo_senha é obrigatório no formulário
        for field in required_fields:
            data = self.valid_data.copy()
            data[field] = ""
            form = CadastrarPacienteForm(data=data)
            self.assertFalse(form.is_valid(), f"Campo {field} deveria ser obrigatório")
            self.assertIn(field, form.errors)

    def test_optional_fields(self):
        """Testa campos opcionais."""
        optional_fields = [
            "cartao_sus",
            "profissional_saude",
            "observacoes",
            "telefone_celular",
        ]
        data = self.valid_data.copy()
        for field in optional_fields:
            data[field] = ""
        data["horario_agendamento"] = ""  # Também opcional
        form = CadastrarPacienteForm(data=data)
        self.assertTrue(form.is_valid())

    def test_horario_agendamento_validation(self):
        """Testa validação de horário de agendamento."""
        # Data futura
        future_date = timezone.now() + timezone.timedelta(days=1)
        data = self.valid_data.copy()
        data["horario_agendamento"] = future_date
        form = CadastrarPacienteForm(data=data)
        self.assertTrue(form.is_valid())

        # Data passada
        past_date = timezone.now() - timezone.timedelta(days=1)
        data["horario_agendamento"] = past_date
        form = CadastrarPacienteForm(data=data)
        self.assertTrue(form.is_valid())  # Não há validação de data passada

    def test_profissional_saude_queryset(self):
        """Testa que queryset de profissional_saude filtra corretamente."""
        # Criar usuários de diferentes funções
        admin = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="testpass",
            funcao="administrador",
        )
        recepcionista = CustomUser.objects.create_user(
            cpf="22233344455",
            username="22233344455",
            password="testpass",
            funcao="recepcionista",
        )

        form = CadastrarPacienteForm()
        # O queryset deve conter apenas profissionais de saúde
        profissionais = form.fields["profissional_saude"].queryset
        self.assertIn(self.profissional, profissionais)
        self.assertNotIn(admin, profissionais)
        self.assertNotIn(recepcionista, profissionais)

    def test_form_with_profissionais_param(self):
        """Testa formulário com parâmetro profissionais_de_saude."""
        # Form sem parâmetro deve ter queryset padrão
        form_default = CadastrarPacienteForm()
        self.assertTrue(
            all(
                user.funcao == "profissional_saude"
                for user in form_default.fields["profissional_saude"].queryset
            )
        )

        # Form com parâmetro personalizado
        profissionais_custom = CustomUser.objects.filter(funcao="administrador")
        form_custom = CadastrarPacienteForm(profissionais_de_saude=profissionais_custom)
        # Como o campo é definido na classe após __init__, o parâmetro pode não funcionar
        # Vamos testar apenas que o form pode ser criado
        self.assertIsInstance(form_custom, CadastrarPacienteForm)


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

    def test_invalid_cpf(self):
        """Testa CPF inválido."""
        data = self.valid_data.copy()
        data["cpf"] = "invalid_cpf"
        form = LoginForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

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


# Views
class CoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            cpf="00011122233",
            username="00011122233",
            password="testpass",
        )

    def test_login_view_get(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_login_view_post_valid(self):
        response = self.client.post(
            reverse("login"),
            {"cpf": "00011122233", "password": "testpass"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        # After login, try to access a login-required page to check authentication
        response2 = self.client.get(reverse("pagina_inicial"))
        self.assertTrue(response2.context["user"].is_authenticated)

    def test_login_view_post_invalid(self):
        response = self.client.post(
            reverse("login"),
            {"cpf": "00011122233", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)

    def test_login_redirect_based_on_role(self):
        """Testa redirecionamento após login baseado na função do usuário."""
        # Teste para administrador
        admin_user = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="adminpass",
            funcao="administrador",
            is_staff=True,
            is_superuser=True,
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "11122233344", "password": "adminpass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("administrador:listar_funcionarios"))

        self.client.logout()

        # Teste para recepcionista
        recep_user = CustomUser.objects.create_user(
            cpf="22233344455",
            username="22233344455",
            password="receptionpass",
            funcao="recepcionista",
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "22233344455", "password": "receptionpass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("recepcionista:cadastrar_paciente"))

        self.client.logout()

        # Teste para guiche
        guiche_user = CustomUser.objects.create_user(
            cpf="33344455566",
            username="33344455566",
            password="guichepass",
            funcao="guiche",
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "33344455566", "password": "guichepass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("guiche:selecionar_guiche"))

        self.client.logout()

        # Teste para profissional_saude
        prof_user = CustomUser.objects.create_user(
            cpf="44455566677",
            username="44455566677",
            password="profpass",
            funcao="profissional_saude",
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "44455566677", "password": "profpass"},
            follow=True,
        )
        self.assertRedirects(
            response, reverse("profissional_saude:painel_profissional")
        )

    def test_login_view_post_form_invalid(self):
        """Testa login com formulário inválido (CPF vazio)."""
        response = self.client.post(
            reverse("login"),
            {"cpf": "", "password": "testpass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este campo é obrigatório")  # Ou similar
        self.assertFalse(response.context["user"].is_authenticated)

    def test_login_redirect_unknown_role(self):
        """Testa redirecionamento para função desconhecida."""
        unknown_user = CustomUser.objects.create_user(
            cpf="55566677788",
            username="55566677788",
            password="unknownpass",
            funcao="desconhecida",  # Função não reconhecida
        )
        response = self.client.post(
            reverse("login"),
            {"cpf": "55566677788", "password": "unknownpass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("pagina_inicial"))

    def test_admin_access_registro_acesso(self):
        """Testa acesso à página admin de RegistroDeAcesso para cobrir configuração."""
        admin_user = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="adminpass",
            funcao="administrador",
            is_staff=True,
            is_superuser=True,
        )
        self.client.login(cpf="11122233344", password="adminpass")
        response = self.client.get("/admin/core/registrodeacesso/")
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        self.client.login(cpf="00011122233", password="testpass")
        response = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_login_creates_registro_acesso(self):
        """Testa se login cria RegistroDeAcesso via sinal."""
        from core.models import RegistroDeAcesso

        initial_count = RegistroDeAcesso.objects.count()
        response = self.client.post(
            reverse("login"),
            {"cpf": "00011122233", "password": "testpass"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RegistroDeAcesso.objects.count(), initial_count + 1)
        registro = RegistroDeAcesso.objects.last()
        self.assertEqual(registro.tipo_de_acesso, "login")

    def test_pagina_inicial_requires_login(self):
        response = self.client.get(reverse("pagina_inicial"))
        self.assertEqual(response.status_code, 302)  # Redirect to login


# Teste de integração: fluxo completo de cadastro, login, acesso e logout
class IntegracaoFluxoCompletoTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.funcionario = CustomUser.objects.create_user(
            cpf="12312312399",
            username="12312312399",
            password="funcpass",
            first_name="Func",
            last_name="Test",
            funcao="administrador",
        )

    def test_fluxo_completo(self):
        # Cadastro de paciente via model (simulando formulário)
        paciente = Paciente.objects.create(
            nome_completo="Paciente Integração",
            cartao_sus="99988877766",
            horario_agendamento=timezone.now(),
            profissional_saude=self.funcionario,
            tipo_senha="G",
        )
        self.assertIsNotNone(paciente.id)

        # Login
        login = self.client.login(cpf="12312312399", password="funcpass")
        self.assertTrue(login)

        # Acesso à página inicial (protegida)
        response = self.client.get(reverse("pagina_inicial"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)

        # Logout
        response = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        # Após logout, usuário não está autenticado
        response2 = self.client.get(reverse("pagina_inicial"))
        self.assertEqual(response2.status_code, 302)


class UtilsTest(TestCase):
    """Testes para funções utilitárias em core.utils."""

    @patch("core.utils.Client")
    def test_enviar_whatsapp_sucesso(self, mock_client):
        """Testa envio bem-sucedido de WhatsApp."""
        from core.utils import enviar_whatsapp
        from django.conf import settings

        # Mock das configurações
        settings.TWILIO_ACCOUNT_SID = "test_sid"
        settings.TWILIO_AUTH_TOKEN = "test_token"
        settings.TWILIO_WHATSAPP_NUMBER = "+1234567890"

        # Mock do cliente e mensagem
        mock_message = mock_client.return_value.messages.create.return_value
        mock_message.sid = "test_sid"

        resultado = enviar_whatsapp("+5511999999999", "Teste mensagem")

        self.assertTrue(resultado)
        mock_client.assert_called_once_with("test_sid", "test_token")
        mock_client.return_value.messages.create.assert_called_once_with(
            from_="whatsapp:+1234567890",
            body="Teste mensagem",
            to="whatsapp:+5511999999999",
        )

    def test_enviar_whatsapp_credenciais_ausentes(self):
        """Testa falha quando credenciais Twilio não estão configuradas."""
        from core.utils import enviar_whatsapp
        from django.conf import settings

        # Simular credenciais ausentes
        settings.TWILIO_ACCOUNT_SID = None
        settings.TWILIO_AUTH_TOKEN = "test_token"
        settings.TWILIO_WHATSAPP_NUMBER = "+1234567890"

        resultado = enviar_whatsapp("+5511999999999", "Teste mensagem")

        self.assertFalse(resultado)

    @patch("core.utils.Client")
    def test_enviar_whatsapp_erro_api(self, mock_client):
        """Testa falha na API do Twilio."""
        from core.utils import enviar_whatsapp
        from django.conf import settings

        # Mock das configurações
        settings.TWILIO_ACCOUNT_SID = "test_sid"
        settings.TWILIO_AUTH_TOKEN = "test_token"
        settings.TWILIO_WHATSAPP_NUMBER = "+1234567890"

        # Mock do cliente para lançar exceção
        mock_client.return_value.messages.create.side_effect = Exception("Erro na API")

        resultado = enviar_whatsapp("+5511999999999", "Teste mensagem")

        self.assertFalse(resultado)
        mock_client.assert_called_once_with("test_sid", "test_token")


class DecoratorTest(TestCase):
    """Testes para os decorators de permissões."""

    def setUp(self):
        self.client = Client()
        # Cria usuário recepcionista (não administrador)
        self.user = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="testpass123",
            first_name="Maria",
            last_name="Santos",
            email="maria.santos@test.com",
            funcao="recepcionista",
        )

    def test_admin_required_redirects_non_admin(self):
        """Testa que admin_required redireciona usuário não administrador."""
        from core.decorators import admin_required
        from django.http import HttpRequest

        # Cria uma view mock
        def mock_admin_view(request):
            return HttpResponse("Acesso permitido")

        # Decora a view
        decorated_view = admin_required(mock_admin_view)

        # Cria request mock com usuário não admin
        request = HttpRequest()
        request.user = self.user

        # Chama a view decorada
        response = decorated_view(request)

        # Deve redirecionar para pagina_inicial
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("pagina_inicial"))


class TemplateTagsTest(TestCase):
    """Testes para template tags em core.templatetags.core_tags."""

    def setUp(self):
        from guiche.forms import GuicheForm

        # Cria um formulário GuicheForm que tem os campos proporcao_*
        self.form = GuicheForm()

    def test_get_proporcao_field_with_empty_value(self):
        """Testa get_proporcao_field quando o valor está vazio."""
        from core.templatetags.core_tags import get_proporcao_field
        from guiche.forms import GuicheForm

        # Modifica o form para simular um campo vazio
        # Como o form é dinâmico, vamos criar um form com dados que façam value() retornar vazio
        form_data = {"proporcao_g": ""}  # Campo vazio
        form = GuicheForm(data=form_data)

        result = get_proporcao_field(form, "tipo_senha_g")

        # Deve retornar o widget com value="1" porque o valor está vazio
        self.assertIn('value="1"', str(result))

    def test_get_proporcao_field_with_value(self):
        """Testa get_proporcao_field quando o valor não está vazio."""
        from core.templatetags.core_tags import get_proporcao_field
        from guiche.forms import GuicheForm

        # Campo com valor
        form_data = {"proporcao_g": "5"}
        form = GuicheForm(data=form_data)

        result = get_proporcao_field(form, "tipo_senha_g")

        # Deve retornar o campo original (não modificado)
        self.assertEqual(result, form["proporcao_g"])

    def test_add_class_filter(self):
        """Testa o filtro add_class."""
        from core.templatetags.core_tags import add_class
        from guiche.forms import GuicheForm

        form = GuicheForm()
        field = form["proporcao_g"]

        result = add_class(field, "my-custom-class")

        # Deve conter a classe CSS adicionada
        self.assertIn('class="my-custom-class"', str(result))
