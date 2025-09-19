from django.test import TestCase, Client
from django.urls import reverse
from core.models import CustomUser, Paciente
from django.utils import timezone


class RecepcionistaViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.recep = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="receppass",
            funcao="recepcionista",
            first_name="Recep",
            last_name="User",
        )
        self.prof = CustomUser.objects.create_user(
            cpf="22233344455",
            username="22233344455",
            password="profpass",
            funcao="profissional_saude",
            first_name="Prof",
            last_name="User",
        )

    def test_cadastrar_paciente_get(self):
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "form")

    def test_cadastrar_paciente_post(self):
        self.client.login(cpf="11122233344", password="receppass")
        url = reverse("recepcionista:cadastrar_paciente")
        data = {
            "nome_completo": "Paciente Teste",
            "cartao_sus": "1234567890",
            "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "profissional_saude": self.prof.id,
            "observacoes": "Obs",
            "tipo_senha": "G",
            "telefone_celular": "(11) 91234-5678",
        }
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Paciente.objects.filter(nome_completo="Paciente Teste").exists()
        )

    def test_permissao_apenas_recepcionista(self):
        url = reverse("recepcionista:cadastrar_paciente")
        # Não logado
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        # Logado como profissional de saúde
        self.client.login(cpf="22233344455", password="profpass")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
