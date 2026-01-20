from django.test import TestCase, Client
from django.urls import reverse
from core.models import CustomUser


class AdministradorViewsTest(TestCase):

    def setUp(self):
        print("\033[95m🎯 Teste funcional: Views Administrador\033[0m")
        self.client = Client()

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
            "cpf": "52998224725",
            "username": "52998224725",
            "first_name": "Novo",
            "last_name": "Funcionario",
            "email": "novo@func.com",
            "funcao": "recepcionista",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(CustomUser.objects.filter(cpf="52998224725").exists())

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

    # ===== TESTES DE SEGURANÇA =====

    def test_large_input_handling(self):
        """Testa tratamento de inputs grandes."""
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:cadastrar_funcionario")

        # Nome muito longo
        data = {
            "cpf": "11144477735",
            "username": "11144477735",
            "first_name": "A" * 100,  # Longo mas aceitável
            "last_name": "Grande",
            "email": "grande@teste.com",
            "funcao": "recepcionista",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        user = CustomUser.objects.filter(cpf="11144477735")
        self.assertTrue(user.exists())

    def test_special_characters_names(self):
        """Testa caracteres especiais em nomes."""
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:cadastrar_funcionario")

        special_names = [
            "José da Silva",
            "João Paulo",
            "María José",
            "André-François",
            "Müller",
            "O'Connor",
        ]

        valid_cpfs = [
            "99828848325",
            "91917883587",
            "13957166179",
            "04490859457",
            "50863958605",
            "77787970200",
        ]
        for i, name in enumerate(special_names):
            first_name, last_name = (
                name.split(" ", 1) if " " in name else (name, "Teste")
            )
            cpf = valid_cpfs[i]
            data = {
                "cpf": cpf,
                "username": cpf,
                "first_name": first_name,
                "last_name": last_name,
                "email": f"teste{i}@teste.com",
                "funcao": "recepcionista",
                "password1": "testpass123",
                "password2": "testpass123",
            }
            resp = self.client.post(url, data, follow=True)
            self.assertEqual(resp.status_code, 200)
            user = CustomUser.objects.filter(cpf=cpf)
            self.assertTrue(user.exists())

    def test_password_validation(self):
        """Testa validação de senha."""
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:cadastrar_funcionario")

        # Senhas não coincidem
        data = {
            "cpf": "00011122233",
            "username": "00011122233",
            "first_name": "Teste",
            "last_name": "Senha",
            "email": "senha@teste.com",
            "funcao": "recepcionista",
            "password1": "senha123",
            "password2": "senha456",  # Diferente
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        # Verificar que não foi criado
        user = CustomUser.objects.filter(cpf="00011122233")
        self.assertFalse(user.exists())

    def test_funcao_choices_validation(self):
        """Testa validação de choices para função."""
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:cadastrar_funcionario")

        # Função inválida
        data = {
            "cpf": "11223344556",  # CPF diferente
            "username": "11223344556",
            "first_name": "Teste",
            "last_name": "Funcao",
            "email": "funcao@teste.com",
            "funcao": "cargo_invalido",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        # Verificar que não foi criado
        user = CustomUser.objects.filter(cpf="11223344556")
        self.assertFalse(user.exists())

    def test_permission_bypass_attempts(self):
        """Testa tentativas de bypass de permissões."""
        # Tentar cadastrar admin como recepcionista
        self.client.login(
            cpf="22233344455", password="funcpass"
        )  # Logado como recepcionista
        url = reverse("administrador:cadastrar_funcionario")
        data = {
            "cpf": "22233344455",
            "username": "22233344455",
            "first_name": "Bypass",
            "last_name": "Test",
            "email": "bypass@teste.com",
            "funcao": "administrador",  # Tentando criar admin
            "password1": "testpass123",
            "password2": "testpass123",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)  # Deve redirecionar (sem permissão)

    def test_data_integrity_multiple_registrations(self):
        """Testa integridade de dados em múltiplos cadastros."""
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:cadastrar_funcionario")

        # Cadastrar múltiplos usuários
        valid_cpfs = ["12345678909", "52998224725", "11144477735"]
        for i in range(3):
            cpf = valid_cpfs[i]
            data = {
                "cpf": cpf,
                "username": cpf,
                "first_name": f"Usuario{i}",
                "last_name": "Teste",
                "email": f"usuario{i}@teste.com",
                "funcao": "recepcionista",
                "password1": "testpass123",
                "password2": "testpass123",
            }
            resp = self.client.post(url, data, follow=True)
            self.assertEqual(resp.status_code, 200)
            user = CustomUser.objects.filter(cpf=cpf)
            self.assertTrue(user.exists())

        # Verificar que todos foram criados
        self.assertEqual(CustomUser.objects.filter(last_name="Teste").count(), 3)

    def test_editar_funcionario(self):
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:editar_funcionario", args=[self.func.pk])
        data = {
            "cpf": "12345678909",
            "username": "12345678909",
            "first_name": "Edited",
            "last_name": "Funcionario",
            "email": "edited@func.com",
            "funcao": "guiche",
            "password1": "newpass123",
            "password2": "newpass123",
        }
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Funcionário atualizado com sucesso")
        self.func.refresh_from_db()
        self.assertEqual(self.func.first_name, "Edited")
        self.assertEqual(self.func.funcao, "guiche")

    def test_editar_funcionario_invalido(self):
        self.client.login(cpf="11122233344", password="adminpass")
        url = reverse("administrador:editar_funcionario", args=[self.func.pk])
        data = {
            "cpf": "12345678909",
            "username": "12345678909",
            "first_name": "Edited",
            "last_name": "Funcionario",
            "email": "edited@func.com",
            "funcao": "guiche",
            "password1": "newpass123",
            "password2": "differentpass",  # Senhas diferentes
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Erro ao atualizar o funcionário")
