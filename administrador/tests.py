from django.test import TestCase, Client
from django.urls import reverse
from core.models import CustomUser


class AdministradorViewsTest(TestCase):

    def test_cadastrar_funcionario_cpf_duplicado(self):
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:cadastrar_funcionario")
        data = {
            "cpf": self.func.cpf,  # CPF já existente
            "username": self.func.username,
            "first_name": "Novo",
            "last_name": "Funcionario",
            "email": "novo@func.com",
            "funcao": "recepcionista",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Erro")
        # Só deve existir um usuário com esse CPF
        self.assertEqual(CustomUser.objects.filter(cpf=self.func.cpf).count(), 1)

    def test_permissao_views_sem_login(self):
        # Todas as views devem redirecionar se não estiver logado
        urls = [
            reverse("administrador:cadastrar_funcionario"),
            reverse("administrador:listar_funcionarios"),
            reverse("administrador:excluir_funcionario", args=[self.func.pk]),
        ]
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            resp_post = self.client.post(url)
            self.assertEqual(resp_post.status_code, 302)

    def test_permissao_views_nao_admin(self):
        # Logado como não-admin
        self.client.login(cpf="22233344455", password="funcpass")
        urls = [
            reverse("administrador:cadastrar_funcionario"),
            reverse("administrador:listar_funcionarios"),
            reverse("administrador:excluir_funcionario", args=[self.admin.pk]),
        ]
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            resp_post = self.client.post(url)
            self.assertEqual(resp_post.status_code, 302)

    def test_integridade_exclusao(self):
        self.client.login(cpf="11122233344", password="adminpass")
        # Excluir funcionário
        url = reverse("administrador:excluir_funcionario", args=[self.func.pk])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Não deve mais aparecer na listagem
        list_url = reverse("administrador:listar_funcionarios")
        resp2 = self.client.get(list_url)
        self.assertNotContains(resp2, self.func.cpf)
        # Não deve mais existir no banco
        self.assertFalse(CustomUser.objects.filter(pk=self.func.pk).exists())

    def test_integridade_cpf_unico(self):
        # Não deve ser possível cadastrar dois usuários com o mesmo CPF
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:cadastrar_funcionario")
        data = {
            "cpf": self.admin.cpf,
            "username": self.admin.username,
            "first_name": "Outro",
            "last_name": "Admin",
            "email": "outro@admin.com",
            "funcao": "administrador",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Erro")
        self.assertEqual(CustomUser.objects.filter(cpf=self.admin.cpf).count(), 1)

    def setUp(self):
        self.client = Client()
        self.admin = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="adminpass",
            funcao="administrador",
            first_name="Admin",
            last_name="User",
        )
        self.func = CustomUser.objects.create_user(
            cpf="22233344455",
            username="22233344455",
            password="funcpass",
            funcao="recepcionista",
            first_name="Func",
            last_name="User",
        )

    def test_cadastrar_funcionario_get(self):
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:cadastrar_funcionario")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "form")

    def test_cadastrar_funcionario_post(self):
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:cadastrar_funcionario")
        data = {
            "cpf": "33344455566",
            "username": "33344455566",
            "first_name": "Novo",
            "last_name": "Funcionario",
            "email": "novo@func.com",
            "funcao": "recepcionista",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(CustomUser.objects.filter(cpf="33344455566").exists())

    def test_listar_funcionarios(self):
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:listar_funcionarios")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Admin")
        self.assertContains(resp, "Func")

    def test_excluir_funcionario(self):
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:excluir_funcionario", args=[self.func.pk])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(pk=self.func.pk).exists())

    def test_permissao_apenas_admin(self):
        # Não logado
        url = reverse("administrador:listar_funcionarios")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        # Logado como não-admin
        self.client.login(cpf="22233344455", password="funcpass")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
