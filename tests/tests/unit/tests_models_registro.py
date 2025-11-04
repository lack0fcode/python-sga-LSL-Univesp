from django.test import TestCase
from django.utils import timezone

from core.models import CustomUser, RegistroDeAcesso


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
