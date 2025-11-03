"""
Testes de integração para autorização e validação do sistema SGA-ILSL.
Testa fluxos complexos, autorização de acesso e validação de dados.
"""

from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import patch

from ..models import Paciente, CustomUser

User = get_user_model()


class AutorizacaoValidacaoIntegracaoTest(TransactionTestCase):
    """
    Testes de integração que simulam fluxos complexos, autorização e validação.
    """

    def setUp(self):
        """Configura dados iniciais para os testes."""
        # Mock WhatsApp to avoid real API calls
        self.mock_whatsapp = patch("core.utils.enviar_whatsapp").start()
        self.mock_whatsapp.return_value = True

        self.admin_user = User.objects.create_user(
            cpf="00000000000",
            username="00000000000",
            password="admin123",
            first_name="Admin",
            last_name="Sistema",
            funcao="administrador",
        )

        # Dados para criação dinâmica de usuários
        self.user_data = {
            "recepcionista": {
                "cpf": "11111111111",
                "password": "recep123",
                "first_name": "Maria",
                "last_name": "Recepção",
                "funcao": "recepcionista",
            },
            "guiche": {
                "cpf": "22222222222",
                "password": "guiche123",
                "first_name": "João",
                "last_name": "Guichê",
                "funcao": "guiche",
            },
            "profissional_saude": {
                "cpf": "33333333333",
                "password": "prof123",
                "first_name": "Dr.",
                "last_name": "Silva",
                "funcao": "profissional_saude",
            },
        }

    def tearDown(self):
        """Limpa mocks após os testes."""
        self.mock_whatsapp.stop()

    def criar_usuario_direto(self, user_type, cpf=None):
        """Método auxiliar para criar usuário diretamente no banco."""
        data = self.user_data[user_type].copy()
        if cpf:
            data["cpf"] = cpf

        # Atribuir sala para profissionais de saúde
        sala = None
        if user_type == "profissional_saude":
            sala = 101  # Sala padrão para testes

        return User.objects.create_user(
            cpf=data["cpf"],
            username=data["cpf"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            funcao=data["funcao"],
            sala=sala,
        )

    def test_fluxo_completo_dinamico_cadastro_chamada_consulta(self):
        """Testa o fluxo completo dinâmico: cadastro -> guichê -> profissional -> consulta."""
        # 1. CRIAR USUÁRIOS
        recepcionista = self.criar_usuario_direto("recepcionista")
        profissional = self.criar_usuario_direto("profissional_saude")
        guiche_user = self.criar_usuario_direto("guiche")

        # Criar guichê para o usuário
        from ..models import Guiche

        guiche = Guiche.objects.create(
            numero=1, funcionario=guiche_user, user=guiche_user
        )

        # 2. RECEPCIONISTA CADASTRA PACIENTE
        client_recep = Client()
        client_recep.login(cpf=recepcionista.cpf, password="recep123")

        paciente_data = {
            "nome_completo": "João Silva Teste Dinâmico",
            "cartao_sus": "999999999999999",
            "telefone_celular": "11988887777",
            "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "profissional_saude": profissional.id,
            "tipo_senha": "G",
        }

        response = client_recep.post(
            reverse("recepcionista:cadastrar_paciente"), data=paciente_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect após sucesso

        # Verificar paciente criado
        paciente = Paciente.objects.get(cartao_sus="999999999999999")
        self.assertEqual(paciente.nome_completo, "João Silva Teste Dinâmico")
        self.assertEqual(paciente.tipo_senha, "G")
        self.assertTrue(paciente.senha.startswith("G"))  # Senha começa com tipo

        # 3. VERIFICAR PACIENTE NA TV1 (GUICHÊ) - ANTES de chamar
        client_tv1 = Client()
        response = client_tv1.get(reverse("guiche:tv1"))
        self.assertEqual(response.status_code, 200)
        # Paciente deve estar na lista de senhas, mas não chamado ainda
        self.assertContains(response, "Nenhuma senha chamada no momento")

        # 4. GUICHÊ CHAMA O PACIENTE
        client_guiche = Client()
        client_guiche.login(cpf=guiche_user.cpf, password="guiche123")

        # Chamar paciente (não marca como atendido ainda)
        response = client_guiche.post(
            reverse("guiche:chamar_senha", args=[paciente.id])
        )
        self.assertEqual(response.status_code, 200)  # Retorna JSON

        # Paciente ainda não está atendido
        paciente.refresh_from_db()
        self.assertFalse(paciente.atendido)

        # 5. GUICHÊ CONFIRMA ATENDIMENTO (agora paciente vai para fila do profissional)
        response = client_guiche.post(
            reverse("guiche:confirmar_atendimento", args=[paciente.id])
        )
        self.assertEqual(response.status_code, 200)  # Retorna JSON

        # Agora paciente está atendido e vai para fila do profissional
        paciente.refresh_from_db()
        self.assertTrue(paciente.atendido)

        # 5. VERIFICAR PACIENTE NA TV1 (GUICHÊ) - DEPOIS de chamar
        response = client_tv1.get(reverse("guiche:tv1"))
        self.assertEqual(response.status_code, 200)
        # Agora deve aparecer na TV1 como chamado
        self.assertContains(response, "João Silva Teste Dinâmico")  # Nome aparece na TV
        self.assertContains(response, "Guichê 1")  # Guichê aparece na TV

        # 5.1. VERIFICAR API DA TV1
        response_api = client_tv1.get(reverse("guiche:tv1_api"))
        self.assertEqual(response_api.status_code, 200)
        data = response_api.json()
        self.assertEqual(data["nome_completo"], "João Silva Teste Dinâmico")
        self.assertEqual(data["guiche"], 1)
        self.assertEqual(data["senha"], paciente.senha)

        # 6. PROFISSIONAL CHAMA PARA CONSULTA
        client_prof = Client()
        client_prof.login(cpf=profissional.cpf, password="prof123")

        # Chamar paciente para consulta
        response = client_prof.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                args=[paciente.id, "chamar"],
            )
        )
        self.assertEqual(response.status_code, 200)  # Retorna JSON

        # Verificar chamada registrada
        from ..models import ChamadaProfissional

        chamada = ChamadaProfissional.objects.filter(
            paciente=paciente, profissional_saude=profissional, acao="chamada"
        ).first()
        self.assertIsNotNone(chamada)

        # 7. VERIFICAR PACIENTE NA TV2 (PROFISSIONAL) - DEPOIS de chamar
        client_tv2 = Client()
        response = client_tv2.get(reverse("profissional_saude:tv2"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "João Silva Teste Dinâmico")  # Nome na TV2

        # 7.1. VERIFICAR API DA TV2
        response_api = client_tv2.get(reverse("profissional_saude:tv2_api"))
        self.assertEqual(response_api.status_code, 200)
        data = response_api.json()
        self.assertEqual(data["nome_completo"], "João Silva Teste Dinâmico")
        self.assertEqual(data["senha"], paciente.senha)
        self.assertEqual(data["profissional_nome"], "Dr. Silva")

        # 8. VERIFICAR PAINEL DO PROFISSIONAL
        response = client_prof.get(reverse("profissional_saude:painel_profissional"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "João Silva Teste Dinâmico")  # Aparece no painel

    def test_fluxo_dinamico_multiplos_pacientes_filas(self):
        """Testa fluxo dinâmico com múltiplos pacientes e filas simultâneas."""
        # Criar usuários
        recepcionista = self.criar_usuario_direto("recepcionista", "44444444444")
        profissional1 = self.criar_usuario_direto("profissional_saude", "55555555555")
        profissional2 = self.criar_usuario_direto("profissional_saude", "66666666666")
        profissional2.first_name = "Dra."
        profissional2.last_name = "Santos"
        profissional2.save()

        guiche_user = self.criar_usuario_direto("guiche", "77777777777")

        # Criar guichê
        from ..models import Guiche

        guiche = Guiche.objects.create(
            numero=1, funcionario=guiche_user, user=guiche_user
        )

        client_recep = Client()
        client_recep.login(cpf=recepcionista.cpf, password="recep123")

        # Cadastrar múltiplos pacientes
        pacientes_data = [
            {
                "nome_completo": "Ana Pereira",
                "cartao_sus": "111111111111111",
                "telefone_celular": "11911111111",
                "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "profissional_saude": profissional1.id,
                "tipo_senha": "G",
            },
            {
                "nome_completo": "Carlos Oliveira",
                "cartao_sus": "222222222222222",
                "telefone_celular": "11922222222",
                "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "profissional_saude": profissional2.id,
                "tipo_senha": "P",
            },
            {
                "nome_completo": "Maria Santos",
                "cartao_sus": "333333333333333",
                "telefone_celular": "11933333333",
                "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "profissional_saude": profissional1.id,
                "tipo_senha": "G",
            },
        ]

        pacientes = []
        for data in pacientes_data:
            response = client_recep.post(
                reverse("recepcionista:cadastrar_paciente"), data=data
            )
            self.assertEqual(response.status_code, 302)

            paciente = Paciente.objects.get(cartao_sus=data["cartao_sus"])
            pacientes.append(paciente)
            self.assertEqual(paciente.nome_completo, data["nome_completo"])

        # Verificar que pacientes foram criados mas NÃO aparecem na TV1 ainda (antes de serem chamados)
        client_tv1 = Client()
        response = client_tv1.get(reverse("guiche:tv1"))
        self.assertEqual(response.status_code, 200)
        # Pacientes não devem aparecer na TV1 até serem chamados
        self.assertContains(response, "Nenhuma senha chamada no momento")
        self.assertNotContains(response, "Ana Pereira")
        self.assertNotContains(response, "Carlos Oliveira")
        self.assertNotContains(response, "Maria Santos")

        # Guichê chama primeiro paciente (Ana Pereira)
        client_guiche = Client()
        client_guiche.login(cpf=guiche_user.cpf, password="guiche123")

        response = client_guiche.post(
            reverse("guiche:chamar_senha", args=[pacientes[0].id])
        )
        self.assertEqual(response.status_code, 200)

        # Confirmar atendimento do primeiro paciente
        response = client_guiche.post(
            reverse("guiche:confirmar_atendimento", args=[pacientes[0].id])
        )
        self.assertEqual(response.status_code, 200)

        # Verificar TV1 após chamada
        response = client_tv1.get(reverse("guiche:tv1"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ana Pereira")  # Aparece como chamada
        self.assertContains(response, "Guichê 1")  # Guichê aparece na TV
        # Outros pacientes não aparecem na TV1 até serem chamados
        self.assertNotContains(response, "Carlos Oliveira")
        self.assertNotContains(response, "Maria Santos")

        # Profissional 1 chama Ana Pereira para consulta
        client_prof1 = Client()
        client_prof1.login(cpf=profissional1.cpf, password="prof123")

        response = client_prof1.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                args=[pacientes[0].id, "chamar"],
            )
        )
        self.assertEqual(response.status_code, 200)

        # Verificar TV2 do profissional 1
        client_tv2 = Client()
        response = client_tv2.get(reverse("profissional_saude:tv2"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ana Pereira")  # Aparece na TV2 do prof1
        # Maria Santos não aparece ainda pois não foi chamada
        self.assertNotContains(response, "Maria Santos")
        # Carlos Oliveira não deve aparecer na TV2 do prof1 (pertence ao prof2)
        self.assertNotContains(response, "Carlos Oliveira")

        # Profissional 2 chama Carlos Oliveira para consulta
        client_prof2 = Client()
        client_prof2.login(cpf=profissional2.cpf, password="prof123")

        response = client_prof2.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                args=[pacientes[1].id, "chamar"],
            )
        )
        self.assertEqual(response.status_code, 200)

        # Verificar que Ana Pereira não aparece na TV2 do profissional 2
        response = client_tv2.get(reverse("profissional_saude:tv2"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Ana Pereira")

    def test_autorizacao_acesso_por_funcao(self):
        """Testa que usuários só acessam páginas permitidas para sua função."""
        # Criar usuários de cada tipo diretamente
        users = {}
        for user_type in ["recepcionista", "guiche", "profissional_saude"]:
            users[user_type] = self.criar_usuario_direto(user_type)

        # Testar acessos permitidos e negados
        permissoes = {
            "recepcionista": {
                "permitido": [reverse("recepcionista:cadastrar_paciente")],
                "negado": [
                    reverse("guiche:painel_guiche"),
                    reverse("profissional_saude:painel_profissional"),
                ],
            },
            "guiche": {
                "permitido": [reverse("guiche:painel_guiche")],
                "negado": [
                    reverse("recepcionista:cadastrar_paciente"),
                    reverse("profissional_saude:painel_profissional"),
                ],
            },
            "profissional_saude": {
                "permitido": [reverse("profissional_saude:painel_profissional")],
                "negado": [
                    reverse("recepcionista:cadastrar_paciente"),
                    reverse("guiche:painel_guiche"),
                ],
            },
        }

        for user_type, user in users.items():
            client = Client()
            client.login(cpf=user.cpf, password=self.user_data[user_type]["password"])

            # Testa acessos permitidos
            for url in permissoes[user_type]["permitido"]:
                response = client.get(url)
                self.assertEqual(
                    response.status_code, 200, f"{user_type} deveria acessar {url}"
                )

            # Testa acessos negados (redirect ou 403)
            for url in permissoes[user_type]["negado"]:
                response = client.get(url)
                self.assertIn(
                    response.status_code,
                    [302, 403],
                    f"{user_type} não deveria acessar {url}",
                )

    def test_cadastro_paciente_com_dados_invalidos(self):
        """Testa tentativa de cadastro de paciente com dados inválidos para cobrir bloco de erro."""
        # Criar recepcionista
        recepcionista = self.criar_usuario_direto("recepcionista")
        profissional = self.criar_usuario_direto("profissional_saude")

        # Recepcionista faz login
        client = Client()
        client.login(cpf=recepcionista.cpf, password="recep123")

        # Tentar cadastrar paciente com dados inválidos (telefone inválido)
        paciente_data_invalido = {
            "nome_completo": "Paciente Inválido",
            "cartao_sus": "123456789012345",
            "telefone_celular": "1199999999",  # Inválido - 10 dígitos
            "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "profissional_saude": profissional.id,
            "tipo_senha": "G",
        }

        response = client.post(
            reverse("recepcionista:cadastrar_paciente"), data=paciente_data_invalido
        )

        # Verifica se o POST retornou erro (status 200 com form inválido)
        self.assertEqual(response.status_code, 200)

        # Verifica se paciente NÃO foi criado devido aos dados inválidos
        try:
            paciente = Paciente.objects.get(cartao_sus="123456789012345")
            self.fail("Paciente não deveria ter sido criado com dados inválidos")
        except Paciente.DoesNotExist:
            # Se paciente não foi criado, verifica se há mensagens de erro na resposta
            self.assertContains(
                response, "celular válido"
            )  # Deve conter mensagem de erro
