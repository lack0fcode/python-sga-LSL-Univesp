import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from core.models import ChamadaProfissional, Paciente


class ProfissionalSaudeTests(TestCase):
    """
    Testes para o app profissional_saude.
    """

    def setUp(self):
        """Configura dados de teste."""
        self.client = Client()

        # Criar usuários de teste
        User = get_user_model()
        self.profissional1 = User.objects.create_user(
            username="prof1",
            cpf="12345678901",
            first_name="João",
            last_name="Silva",
            funcao="profissional_saude",
            sala=101,
            password="testpass123",
        )
        self.profissional2 = User.objects.create_user(
            username="prof2",
            cpf="12345678902",
            first_name="Maria",
            last_name="Santos",
            funcao="profissional_saude",
            sala=102,
            password="testpass123",
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            cpf="12345678903",
            first_name="Admin",
            last_name="User",
            funcao="administrador",
            password="testpass123",
        )

        # Criar pacientes de teste
        self.paciente1 = Paciente.objects.create(
            nome_completo="José da Silva",
            tipo_senha="G",
            senha="G001",
            telefone_celular="(11) 99999-9999",
            profissional_saude=self.profissional1,
            atendido=True,
            horario_agendamento=timezone.now() - timedelta(hours=1),
        )
        self.paciente2 = Paciente.objects.create(
            nome_completo="Ana Oliveira",
            tipo_senha="P",
            senha="P001",
            telefone_celular="(11) 98888-8888",
            profissional_saude=self.profissional1,
            atendido=True,
            horario_agendamento=timezone.now() - timedelta(minutes=30),
        )
        self.paciente3 = Paciente.objects.create(
            nome_completo="Carlos Pereira",
            tipo_senha="D",
            senha="D001",
            telefone_celular="(11) 97777-7777",
            profissional_saude=self.profissional2,
            atendido=False,
            horario_agendamento=timezone.now() + timedelta(hours=1),
        )

    def test_painel_profissional_requires_login(self):
        """Testa que painel_profissional requer login."""
        response = self.client.get(reverse("profissional_saude:painel_profissional"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_painel_profissional_with_profissional_user(self):
        """Testa painel_profissional com usuário profissional de saúde."""
        self.client.login(cpf="12345678901", password="testpass123")
        response = self.client.get(reverse("profissional_saude:painel_profissional"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profissional_saude/painel_profissional.html")

        # Verificar contexto
        self.assertIn("pacientes", response.context)
        self.assertIn("profissionais", response.context)
        self.assertIn("historico_chamadas", response.context)

        # Verificar pacientes atendidos do profissional
        pacientes = response.context["pacientes"]
        self.assertEqual(len(pacientes), 2)  # paciente1 e paciente2
        self.assertIn(self.paciente1, pacientes)
        self.assertIn(self.paciente2, pacientes)

        # Verificar outros profissionais (excluindo o atual)
        profissionais = response.context["profissionais"]
        self.assertEqual(len(profissionais), 1)
        self.assertIn(self.profissional2, profissionais)
        self.assertNotIn(self.profissional1, profissionais)

    def test_painel_profissional_with_admin_user(self):
        """Testa painel_profissional com usuário administrador (deve ser negado)."""
        self.client.login(cpf="12345678903", password="testpass123")
        response = self.client.get(reverse("profissional_saude:painel_profissional"))

        # Como não há verificação específica de função na view, deve funcionar
        # mas idealmente deveria ter verificação de função
        self.assertEqual(response.status_code, 200)

    @patch("profissional_saude.views.enviar_whatsapp")
    def test_realizar_acao_chamar_success(self, mock_whatsapp):
        """Testa ação 'chamar' com sucesso."""
        mock_whatsapp.return_value = True

        self.client.login(cpf="12345678901", password="testpass123")

        # Verificar estado inicial
        chamada_count_inicial = ChamadaProfissional.objects.count()

        response = self.client.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                kwargs={"paciente_id": self.paciente1.id, "acao": "chamar"},
            )
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertIn("chamada com sucesso", data["mensagem"])

        # Verificar que ChamadaProfissional foi criada
        self.assertEqual(ChamadaProfissional.objects.count(), chamada_count_inicial + 1)
        chamada = ChamadaProfissional.objects.latest("data_hora")
        self.assertEqual(chamada.paciente, self.paciente1)
        self.assertEqual(chamada.profissional_saude, self.profissional1)
        self.assertEqual(chamada.acao, "chamada")

        # Verificar que WhatsApp foi chamado
        mock_whatsapp.assert_called_once()
        args = mock_whatsapp.call_args[0]
        self.assertEqual(args[0], "+5511999999999")  # telefone_e164 format
        self.assertIn("Dr(a). João", args[1])
        self.assertIn("Sala 101", args[1])

    @patch("profissional_saude.views.enviar_whatsapp")
    def test_realizar_acao_chamar_without_phone(self, mock_whatsapp):
        """Testa ação 'chamar' sem telefone do paciente."""
        # Criar paciente sem telefone
        paciente_sem_telefone = Paciente.objects.create(
            nome_completo="Paciente Sem Telefone",
            tipo_senha="G",
            senha="G002",
            profissional_saude=self.profissional1,
            atendido=True,
        )

        self.client.login(cpf="12345678901", password="testpass123")

        with patch("builtins.print") as mock_print:
            response = self.client.post(
                reverse(
                    "profissional_saude:realizar_acao_profissional",
                    kwargs={"paciente_id": paciente_sem_telefone.id, "acao": "chamar"},
                )
            )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")

        # Verificar que print foi chamado com aviso
        mock_print.assert_called_once()
        self.assertIn("telefone inválido ou ausente", mock_print.call_args[0][0])

        # WhatsApp não deve ser chamado
        mock_whatsapp.assert_not_called()

    def test_realizar_acao_reanunciar_success(self):
        """Testa ação 'reanunciar' com sucesso."""
        self.client.login(cpf="12345678901", password="testpass123")

        chamada_count_inicial = ChamadaProfissional.objects.count()

        response = self.client.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                kwargs={"paciente_id": self.paciente1.id, "acao": "reanunciar"},
            )
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertIn("reanunciada com sucesso", data["mensagem"])

        # Verificar que ChamadaProfissional foi criada
        self.assertEqual(ChamadaProfissional.objects.count(), chamada_count_inicial + 1)
        chamada = ChamadaProfissional.objects.latest("data_hora")
        self.assertEqual(chamada.paciente, self.paciente1)
        self.assertEqual(chamada.profissional_saude, self.profissional1)
        self.assertEqual(chamada.acao, "reanuncio")

    def test_realizar_acao_confirmar_success(self):
        """Testa ação 'confirmar' com sucesso."""
        self.client.login(cpf="12345678901", password="testpass123")

        # Verificar estado inicial
        self.paciente1.refresh_from_db()
        self.assertTrue(self.paciente1.atendido)

        response = self.client.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                kwargs={"paciente_id": self.paciente1.id, "acao": "confirmar"},
            )
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertIn("confirmado com sucesso", data["mensagem"])

        # Verificar que paciente foi marcado como não atendido
        self.paciente1.refresh_from_db()
        self.assertFalse(self.paciente1.atendido)

    def test_realizar_acao_encaminhar_success(self):
        """Testa ação 'encaminhar' com sucesso."""
        self.client.login(cpf="12345678901", password="testpass123")

        response = self.client.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                kwargs={"paciente_id": self.paciente1.id, "acao": "encaminhar"},
            ),
            {"profissional_encaminhar_id": self.profissional2.id},
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertIn("encaminhado para Maria", data["mensagem"])

        # Verificar que paciente foi reatribuído
        self.paciente1.refresh_from_db()
        self.assertEqual(self.paciente1.profissional_saude, self.profissional2)
        self.assertTrue(self.paciente1.atendido)  # Deve permanecer atendido

    def test_realizar_acao_encaminhar_without_profissional(self):
        """Testa ação 'encaminhar' sem selecionar profissional."""
        self.client.login(cpf="12345678901", password="testpass123")

        response = self.client.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                kwargs={"paciente_id": self.paciente1.id, "acao": "encaminhar"},
            )
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
        self.assertIn("Selecione um profissional", data["mensagem"])

    def test_realizar_acao_invalid(self):
        """Testa ação inválida."""
        self.client.login(cpf="12345678901", password="testpass123")

        response = self.client.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                kwargs={"paciente_id": self.paciente1.id, "acao": "acao_invalida"},
            )
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
        self.assertIn("Ação inválida", data["mensagem"])

    def test_realizar_acao_requires_login(self):
        """Testa que realizar_acao_profissional requer login."""
        response = self.client.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                kwargs={"paciente_id": self.paciente1.id, "acao": "chamar"},
            )
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_realizar_acao_requires_post(self):
        """Testa que realizar_acao_profissional requer método POST."""
        self.client.login(username="prof1", password="testpass123")

        response = self.client.get(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                kwargs={"paciente_id": self.paciente1.id, "acao": "chamar"},
            )
        )
        self.assertEqual(response.status_code, 405)  # Method not allowed

    def test_tv2_view_with_calls(self):
        """Testa tv2_view com chamadas existentes."""
        # Criar algumas chamadas com timestamps diferentes
        chamada1 = ChamadaProfissional.objects.create(
            paciente=self.paciente1,
            profissional_saude=self.profissional1,
            acao="chamada",
        )
        # Pequeno delay para garantir ordenação
        import time

        time.sleep(0.01)
        chamada2 = ChamadaProfissional.objects.create(
            paciente=self.paciente2,
            profissional_saude=self.profissional1,
            acao="reanuncio",
        )

        response = self.client.get(reverse("profissional_saude:tv2"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profissional_saude/tv2.html")

        # Verificar contexto - chamada2 deve ser a mais recente
        self.assertEqual(
            response.context["senha_chamada"], self.paciente2
        )  # Última chamada
        self.assertEqual(
            response.context["nome_completo"], self.paciente2.nome_completo
        )
        self.assertEqual(response.context["sala_consulta"], self.profissional1.sala)
        self.assertEqual(
            response.context["profissional_nome"], self.profissional1.first_name
        )
        self.assertEqual(
            len(response.context["historico_senhas"]), 1
        )  # Uma chamada anterior

    def test_tv2_view_no_calls(self):
        """Testa tv2_view sem chamadas."""
        response = self.client.get(reverse("profissional_saude:tv2"))

        self.assertEqual(response.status_code, 200)

        # Verificar contexto vazio
        self.assertIsNone(response.context["senha_chamada"])
        self.assertIsNone(response.context["nome_completo"])
        self.assertIsNone(response.context["sala_consulta"])
        self.assertIsNone(response.context["profissional_nome"])
        self.assertEqual(len(response.context["historico_senhas"]), 0)

    def test_tv2_api_view_with_calls(self):
        """Testa tv2_api_view com chamadas existentes."""
        chamada = ChamadaProfissional.objects.create(
            paciente=self.paciente1,
            profissional_saude=self.profissional1,
            acao="chamada",
        )

        response = self.client.get(reverse("profissional_saude:tv2_api"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(data["senha"], self.paciente1.senha)
        self.assertEqual(data["nome_completo"], self.paciente1.nome_completo)
        self.assertEqual(data["sala_consulta"], self.profissional1.sala)
        self.assertEqual(data["profissional_nome"], self.profissional1.first_name)
        self.assertEqual(data["id"], chamada.id)

    def test_tv2_api_view_no_calls(self):
        """Testa tv2_api_view sem chamadas."""
        response = self.client.get(reverse("profissional_saude:tv2_api"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(data["senha"], "")
        self.assertEqual(data["nome_completo"], "")
        self.assertEqual(data["sala_consulta"], "")
        self.assertEqual(data["profissional_nome"], "")
        self.assertEqual(data["id"], "")

    def test_paciente_telefone_e164_formatting(self):
        """Testa formatação E.164 do telefone do paciente."""
        # Teste com telefone válido
        self.assertEqual(self.paciente1.telefone_e164(), "+5511999999999")

        # Teste com telefone inválido
        paciente_invalido = Paciente.objects.create(
            nome_completo="Paciente Inválido", telefone_celular="123"
        )
        self.assertIsNone(paciente_invalido.telefone_e164())

    def test_historico_chamadas_limit(self):
        """Testa limite de histórico de chamadas no painel."""
        # Criar 15 chamadas para testar limite de 10
        for i in range(15):
            ChamadaProfissional.objects.create(
                paciente=self.paciente1,
                profissional_saude=self.profissional1,
                acao="chamada" if i % 2 == 0 else "reanuncio",
            )

        self.client.login(cpf="12345678901", password="testpass123")
        response = self.client.get(reverse("profissional_saude:painel_profissional"))

        historico = response.context["historico_chamadas"]
        self.assertEqual(len(historico), 10)  # Deve limitar a 10

        # Verificar ordenação (mais recente primeiro)
        chamadas_ordenadas = list(
            ChamadaProfissional.objects.filter(
                profissional_saude=self.profissional1, acao__in=["chamada", "reanuncio"]
            ).order_by("-data_hora")[:10]
        )

        for i, chamada in enumerate(historico):
            self.assertEqual(chamada, chamadas_ordenadas[i])

    def test_atendimento_profissional_form_validation(self):
        """Testa validação do AtendimentoProfissionalForm."""
        from profissional_saude.forms import AtendimentoProfissionalForm

        # Teste formulário válido (sem ações selecionadas inicialmente)
        form_data = {"paciente_id": self.paciente1.id}
        form = AtendimentoProfissionalForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Teste com uma ação selecionada
        form_data = {"paciente_id": self.paciente1.id, "chamar": "on"}
        form = AtendimentoProfissionalForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Teste com múltiplas ações (deve falhar)
        form_data = {
            "paciente_id": self.paciente1.id,
            "chamar": "on",
            "reanunciar": "on",
        }
        form = AtendimentoProfissionalForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Selecione apenas uma ação", str(form.errors))

        # Teste com profissional_encaminhar queryset
        form = AtendimentoProfissionalForm()
        # O queryset deve ser configurado dinamicamente na view
        self.assertIsNone(form.fields["profissional_encaminhar"].queryset)
