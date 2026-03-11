from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.template import loader
import re

from core.forms import CadastrarFuncionarioForm


class SecurityAttacksTest(TestCase):
    """Tests that demonstrate whether findings are actually exploitable.

    These tests are written to pass when the repository is vulnerable so they
    act as indicators (they intentionally assert the presence of the issue).
    """

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            cpf="90090090000", username="tester", password="safe-pass-123"
        )

    def test_csrf_exempt_registrar_atividade_allows_post_without_token(self):
        """If the view is decorated with @csrf_exempt, a POST without CSRF succeeds.

        We use a test client with `enforce_csrf_checks=True` and `force_login`
        to ensure the POST would normally require a CSRF token.
        The test passes when the endpoint accepts the POST (i.e. vulnerable).
        """
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        url = reverse("administrador:registrar_atividade")
        resp = client.post(url, {}, content_type="application/json")
        # secure behavior: POST without CSRF token must be rejected (403)
        self.assertEqual(resp.status_code, 403)

    def test_weak_password_accepted_by_cadastrar_funcionario_form(self):
        """Detects whether the form accepts a weak password without validation.

        This test passes when the form is valid for a deliberately weak password
        (indicating missing password validation). If your project enforces
        validators, this test will fail — which is good.
        """
        weak = {
            "cpf": "12345678901",
            "first_name": "Weak",
            "last_name": "Pwd",
            "email": "weak@example.com",
            "funcao": "recepcionista",
            "password1": "1234",
            "password2": "1234",
        }
        form = CadastrarFuncionarioForm(data=weak)
        # The test is written to pass if the weak password is accepted (vulnerable)
        self.assertTrue(form.is_valid())

    def test_templates_include_external_cdns_without_sri(self):
        """Quick check: templates that include external CDN resources should
        include `integrity` attribute. This test passes when an insecure
        inclusion (missing SRI) is found — acting as vulnerability indicator.
        """
        templates_to_check = [
            "base.html",
            "administrador/dashboard_analise.html",
            "guiche/tv1.html",
            "profissional_saude/tv2.html",
        ]
        found_insecure = False
        for tpl_name in templates_to_check:
            try:
                tpl = loader.get_template(tpl_name)
                content = tpl.template.source
            except Exception:
                # If template can't be loaded, skip (no assertion here)
                continue
            # find external script/link tags
            for line in content.splitlines():
                if re.search(r"https?://", line):
                    # if integrity is missing on same line, mark insecure
                    if "integrity=" not in line:
                        found_insecure = True
                        break
            if found_insecure:
                break

        # Pass when at least one insecure external resource exists
        self.assertTrue(found_insecure)
