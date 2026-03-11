from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Atendimento, CustomUser, Guiche, Paciente


class AdministradorDashboardTests(TestCase):
    def setUp(self):
        # Usuário administrador
        self.admin = CustomUser.objects.create(
            cpf="00000000000",
            username="admin",
            first_name="Admin",
            last_name="User",
            funcao="administrador",
        )
        self.admin.set_password("pass")
        self.admin.save()

        # Usuário recepcionista
        self.recepcionista = CustomUser.objects.create(
            cpf="11111111111",
            username="recep",
            first_name="Recep",
            last_name="User",
            funcao="recepcionista",
        )
        self.recepcionista.set_password("pass")
        self.recepcionista.save()

        # Dados de exemplo para hoje
        now = timezone.now()
        self.p1 = Paciente.objects.create(
            nome_completo="Paciente 1", senha="0001", horario_geracao_senha=now
        )
        self.g = Guiche.objects.create(numero=1)
        self.a1 = Atendimento.objects.create(
            paciente=self.p1, funcionario=self.admin, data_hora=now
        )

    def test_listar_funcionarios_admin_access(self):
        self.client.force_login(self.admin)
        url = reverse("administrador:listar_funcionarios")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_listar_funcionarios_non_admin_redirect(self):
        self.client.force_login(self.recepcionista)
        url = reverse("administrador:listar_funcionarios")
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (302, 403))

    def test_dashboard_shows_kpis_for_admin(self):
        self.client.force_login(self.admin)
        url = reverse("administrador:dashboard_analise")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Verifica contexto básico
        self.assertIn("total_senhas_geradas_hoje", resp.context)
        self.assertIn("total_atendimentos_hoje", resp.context)
        self.assertEqual(resp.context["total_senhas_geradas_hoje"], 1)
        self.assertEqual(resp.context["total_atendimentos_hoje"], 1)
