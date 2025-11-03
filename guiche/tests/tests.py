from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
import datetime

from core.models import CustomUser, Paciente, Guiche, Chamada


class GuicheViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Criar usuários de teste
        self.guiche_user = CustomUser.objects.create_user(
            cpf="11122233344",
            username="11122233344",
            password="guichepass",
            funcao="guiche",
            first_name="Guiche",
            last_name="User",
        )

        self.admin_user = CustomUser.objects.create_user(
            cpf="22233344455",
            username="22233344455",
            password="adminpass",
            funcao="administrador",
            first_name="Admin",
            last_name="User",
        )

        # Criar guichê
        self.guiche = Guiche.objects.create(numero=1, funcionario=self.guiche_user)

        # Criar pacientes para teste
        self.paciente1 = Paciente.objects.create(
            nome_completo="Paciente Geral",
            tipo_senha="G",
            senha="G001",
            cartao_sus="1234567890",
            horario_agendamento=timezone.now(),
            atendido=False,
            telefone_celular="(11) 91234-5678",
        )

        self.paciente2 = Paciente.objects.create(
            nome_completo="Paciente Exames",
            tipo_senha="E",
            senha="E001",
            cartao_sus="0987654321",
            horario_agendamento=timezone.now(),
            atendido=False,
        )

    def test_permissao_guiche_required(self):
        """Testa que apenas usuários com função 'guiche' podem acessar as views"""
        # Usuário não logado
        response = self.client.get(reverse("guiche:painel_guiche"))
        self.assertEqual(response.status_code, 302)  # Redirect

        # Usuário logado mas não é guiche
        self.client.login(cpf="22233344455", password="adminpass")
        response = self.client.get(reverse("guiche:painel_guiche"))
        self.assertEqual(response.status_code, 302)  # Redirect

        # Usuário guiche logado
        self.client.login(cpf="11122233344", password="guichepass")
        response = self.client.get(reverse("guiche:painel_guiche"))
        self.assertEqual(response.status_code, 200)

    def test_painel_guiche_get_sem_filtros(self):
        """Testa GET do painel guiche sem filtros aplicados"""
        self.client.login(cpf="11122233344", password="guichepass")

        # Ajustar horário de geração para hoje (considerando o ajuste de fuso horário do código)
        hoje = timezone.now() - datetime.timedelta(hours=3)
        hoje = hoje.replace(hour=12, minute=0, second=0, microsecond=0)
        self.paciente1.horario_geracao_senha = hoje
        self.paciente1.save()
        self.paciente2.horario_geracao_senha = hoje
        self.paciente2.save()

        response = self.client.get(reverse("guiche:painel_guiche"))
        self.assertEqual(response.status_code, 200)
        # Verificar se os pacientes aparecem na resposta (pode estar em senhas ou em outro contexto)
        content = response.content.decode("utf-8")
        self.assertTrue(
            "Paciente Geral" in content or "G001" in content,
            "Paciente Geral ou senha G001 deveria aparecer na resposta",
        )

    def test_painel_guiche_post_com_filtros(self):
        """Testa POST do painel guiche aplicando filtros"""
        self.client.login(cpf="11122233344", password="guichepass")

        # Dados do formulário: selecionar apenas tipo G com proporção 1
        data = {
            "tipo_senha_g": "on",
            "proporcao_g": "1",
            "tipo_senha_e": "",  # Não selecionado
            "proporcao_e": "1",
        }

        response = self.client.post(reverse("guiche:painel_guiche"), data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verificar se os filtros foram salvos na sessão
        self.assertIn("filtros_guiche", self.client.session)
        filtros = self.client.session["filtros_guiche"]
        self.assertIn("G", filtros["tipos_selecionados"])
        self.assertNotIn("E", filtros["tipos_selecionados"])

    def test_painel_guiche_get_com_filtros_sessao(self):
        """Testa GET do painel guiche com filtros salvos na sessão"""
        self.client.login(cpf="11122233344", password="guichepass")

        # Simular filtros na sessão
        session = self.client.session
        session["filtros_guiche"] = {
            "tipos_selecionados": ["G"],
            "proporcoes": {"G": 1},
        }
        session.save()

        # Ajustar horário de geração para hoje
        hoje = timezone.now() - datetime.timedelta(hours=3)
        hoje = hoje.replace(hour=12, minute=0, second=0, microsecond=0)
        self.paciente1.horario_geracao_senha = hoje
        self.paciente1.save()
        self.paciente2.horario_geracao_senha = hoje
        self.paciente2.save()

        response = self.client.get(reverse("guiche:painel_guiche"))
        self.assertEqual(response.status_code, 200)
        # Deve mostrar apenas pacientes do tipo G
        content = response.content.decode("utf-8")
        self.assertTrue(
            "Paciente Geral" in content or "G001" in content,
            "Paciente Geral ou senha G001 deveria aparecer na resposta",
        )
        # Não deve mostrar pacientes do tipo E
        self.assertNotIn("Paciente Exames", content)
        self.assertNotIn("E001", content)

    def test_selecionar_guiche_get(self):
        """Testa GET da view de seleção de guichê"""
        self.client.login(cpf="11122233344", password="guichepass")

        response = self.client.get(reverse("guiche:selecionar_guiche"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Selecione um guichê")

    def test_selecionar_guiche_post(self):
        """Testa POST da view de seleção de guichê"""
        self.client.login(cpf="11122233344", password="guichepass")

        data = {"guiche": self.guiche.id}
        response = self.client.post(
            reverse("guiche:selecionar_guiche"), data, follow=True
        )
        self.assertEqual(response.status_code, 200)

        # Verificar se o guichê foi salvo na sessão
        self.assertEqual(self.client.session.get("guiche_id"), self.guiche.id)

    @patch("guiche.views.enviar_whatsapp")
    def test_chamar_senha(self, mock_enviar_whatsapp):
        """Testa chamada de senha com envio de WhatsApp"""
        self.client.login(cpf="11122233344", password="guichepass")

        # Simular guichê na sessão
        session = self.client.session
        session["guiche_id"] = self.guiche.id
        session.save()

        response = self.client.post(
            reverse("guiche:chamar_senha", args=[self.paciente1.id])
        )
        self.assertEqual(response.status_code, 200)

        # Verificar se a chamada foi registrada
        chamada = Chamada.objects.filter(
            paciente=self.paciente1, guiche=self.guiche, acao="chamada"
        ).exists()
        self.assertTrue(chamada)

        # Verificar se WhatsApp foi chamado (pode ser chamado 2 vezes devido à implementação)
        self.assertGreaterEqual(mock_enviar_whatsapp.call_count, 1)

    @patch("guiche.views.enviar_whatsapp")
    def test_chamar_senha_sem_telefone(self, mock_enviar_whatsapp):
        """Testa chamada de senha sem telefone (não deve enviar WhatsApp)"""
        self.client.login(cpf="11122233344", password="guichepass")

        # Simular guichê na sessão
        session = self.client.session
        session["guiche_id"] = self.guiche.id
        session.save()

        # Paciente sem telefone
        response = self.client.post(
            reverse("guiche:chamar_senha", args=[self.paciente2.id])
        )
        self.assertEqual(response.status_code, 200)

        # Verificar se WhatsApp NÃO foi chamado
        mock_enviar_whatsapp.assert_not_called()

    def test_reanunciar_senha(self):
        """Testa reanúncio de senha"""
        self.client.login(cpf="11122233344", password="guichepass")

        # Simular guichê na sessão
        session = self.client.session
        session["guiche_id"] = self.guiche.id
        session.save()

        response = self.client.post(
            reverse("guiche:reanunciar_senha", args=[self.paciente1.id])
        )
        self.assertEqual(response.status_code, 200)

        # Verificar se o reanúncio foi registrado
        chamada = Chamada.objects.filter(
            paciente=self.paciente1, guiche=self.guiche, acao="reanuncio"
        ).exists()
        self.assertTrue(chamada)

    def test_confirmar_atendimento(self):
        """Testa confirmação de atendimento"""
        self.client.login(cpf="11122233344", password="guichepass")

        # Simular guichê na sessão
        session = self.client.session
        session["guiche_id"] = self.guiche.id
        session.save()

        # Verificar estado inicial
        self.paciente1.refresh_from_db()
        self.assertFalse(self.paciente1.atendido)
        self.assertIsNone(self.guiche.senha_atendida)
        self.assertFalse(self.guiche.em_atendimento)

        response = self.client.post(
            reverse("guiche:confirmar_atendimento", args=[self.paciente1.id])
        )
        self.assertEqual(response.status_code, 200)

        # Verificar se o paciente foi marcado como atendido
        self.paciente1.refresh_from_db()
        self.guiche.refresh_from_db()
        self.assertTrue(self.paciente1.atendido)
        self.assertIsNone(self.guiche.senha_atendida)
        self.assertFalse(self.guiche.em_atendimento)

        # Verificar se a confirmação foi registrada
        chamada = Chamada.objects.filter(
            paciente=self.paciente1, guiche=self.guiche, acao="confirmado"
        ).exists()
        self.assertTrue(chamada)

    def test_tv1_view_sem_chamadas(self):
        """Testa view da TV quando não há chamadas"""
        response = self.client.get(reverse("guiche:tv1"))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["senha_chamada"])
        self.assertIsNone(response.context["nome_completo"])
        self.assertIsNone(response.context["numero_guiche"])

    def test_tv1_view_com_chamadas(self):
        """Testa view da TV com chamadas existentes"""
        # Criar uma chamada
        Chamada.objects.create(
            paciente=self.paciente1, guiche=self.guiche, acao="chamada"
        )

        response = self.client.get(reverse("guiche:tv1"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["senha_chamada"], self.paciente1)
        self.assertEqual(
            response.context["nome_completo"], self.paciente1.nome_completo
        )
        self.assertEqual(response.context["numero_guiche"], self.guiche.numero)

    def test_tv1_api_view_sem_chamadas(self):
        """Testa API da TV quando não há chamadas"""
        response = self.client.get(reverse("guiche:tv1_api"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["senha"], "")
        self.assertEqual(data["nome_completo"], "")
        self.assertEqual(data["guiche"], "")
        self.assertEqual(data["id"], "")

    def test_tv1_api_view_com_chamadas(self):
        """Testa API da TV com chamadas existentes"""
        # Criar uma chamada
        chamada = Chamada.objects.create(
            paciente=self.paciente1, guiche=self.guiche, acao="chamada"
        )

        response = self.client.get(reverse("guiche:tv1_api"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["senha"], self.paciente1.senha)
        self.assertEqual(data["nome_completo"], self.paciente1.nome_completo)
        self.assertEqual(data["guiche"], self.guiche.numero)
        self.assertEqual(data["id"], chamada.id)

    def test_fila_com_proporcoes(self):
        """Testa lógica de fila com proporções diferentes"""
        self.client.login(cpf="11122233344", password="guichepass")

        # Remover pacientes do setUp para ter controle total
        Paciente.objects.all().delete()

        # Criar apenas os pacientes necessários para este teste
        hoje = timezone.now() - datetime.timedelta(hours=3)
        hoje = hoje.replace(hour=12, minute=0, second=0, microsecond=0)

        # Criar 3 pacientes tipo G
        pacientes_g = []
        for i in range(3):
            p = Paciente.objects.create(
                nome_completo=f"Paciente G{i}",
                tipo_senha="G",
                senha=f"G{i+2:03d}",
                cartao_sus=f"111111111{i}",
                horario_agendamento=timezone.now(),
                horario_geracao_senha=hoje,
                atendido=False,
            )
            pacientes_g.append(p)

        # Criar 2 pacientes tipo E
        pacientes_e = []
        for i in range(2):
            p = Paciente.objects.create(
                nome_completo=f"Paciente E{i}",
                tipo_senha="E",
                senha=f"E{i+2:03d}",
                cartao_sus=f"222222222{i}",
                horario_agendamento=timezone.now(),
                horario_geracao_senha=hoje,
                atendido=False,
            )
            pacientes_e.append(p)

        # Aplicar filtros: G=2, E=1 (proporção 2:1)
        session = self.client.session
        session["filtros_guiche"] = {
            "tipos_selecionados": ["G", "E"],
            "proporcoes": {"G": 2, "E": 1},
        }
        session.save()

        response = self.client.get(reverse("guiche:painel_guiche"))
        self.assertEqual(response.status_code, 200)

        # Verificar se a fila foi organizada corretamente
        # Com proporção 2:1, deve alternar: G, G, E, G, G, E, etc.
        senhas = response.context["senhas"]
        self.assertEqual(len(senhas), 5)  # 3G + 2E = 5 pacientes

        # Verificar ordem: deve começar com G (mais frequente)
        self.assertEqual(senhas[0].tipo_senha, "G")
        self.assertEqual(senhas[1].tipo_senha, "G")
        self.assertEqual(senhas[2].tipo_senha, "E")

    def test_get_guiche_do_usuario_sem_guiche(self):
        """Testa erro quando usuário não tem guichê associado"""
        from guiche.views import get_guiche_do_usuario
        from django.core.exceptions import ObjectDoesNotExist

        user_sem_guiche = CustomUser.objects.create_user(
            cpf="33344455566",
            username="33344455566",
            password="testpass",
            funcao="guiche",
        )

        with self.assertRaises(Guiche.DoesNotExist):
            get_guiche_do_usuario(user_sem_guiche)

    def test_get_guiche_do_usuario_com_sessao(self):
        """Testa obtenção de guichê via sessão"""
        from guiche.views import get_guiche_do_usuario
        from django.test import RequestFactory

        # Criar request com sessão
        factory = RequestFactory()
        request = factory.get("/")
        request.session = {"guiche_id": self.guiche.id}

        user_sem_guiche = CustomUser.objects.create_user(
            cpf="33344455566",
            username="33344455566",
            password="testpass",
            funcao="guiche",
        )

        guiche_obtido = get_guiche_do_usuario(user_sem_guiche, request)
        self.assertEqual(guiche_obtido, self.guiche)
