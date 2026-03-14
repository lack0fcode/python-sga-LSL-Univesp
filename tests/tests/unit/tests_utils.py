from django.test import TestCase
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from unittest.mock import patch
from core.models import CustomUser


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

        self.assertEqual(resultado["status"], "error")
        self.assertIn("Credenciais Twilio não configuradas", resultado["error"])

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

        self.assertEqual(resultado["status"], "error")
        self.assertEqual(resultado["error"], "Erro na API")
        mock_client.assert_called_once_with("test_sid", "test_token")


class DecoratorTest(TestCase):
    """Testes para os decorators de permissões."""

    def setUp(self):
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
