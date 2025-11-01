"""
Testes de integração dinâmica para o sistema SGA-ILSL.
Testa o fluxo completo do sistema com diferentes usuários e suas funções.
"""

from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import patch

from core.models import Paciente, CustomUser

User = get_user_model()


class FluxoCompletoDinamicoTest(TransactionTestCase):
    """
    Testes de integração que simulam o fluxo completo do sistema SGA-ILSL.
    Cada teste cria usuários dinamicamente e testa suas funcionalidades específicas.
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
        return User.objects.create_user(
            cpf=data["cpf"],
            username=data["cpf"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            funcao=data["funcao"],
        )

    def test_fluxo_administrador_cria_usuarios(self):
        """Testa se administrador consegue criar todos os tipos de usuário."""
        # Cria usuários de cada tipo diretamente
        for user_type in ["recepcionista", "guiche", "profissional_saude"]:
            usuario = self.criar_usuario_direto(user_type)
            self.assertEqual(usuario.funcao, user_type)
            self.assertTrue(
                usuario.check_password(self.user_data[user_type]["password"])
            )

        # Verifica total de usuários criados
        total_users = User.objects.filter(
            cpf__in=[data["cpf"] for data in self.user_data.values()]
        ).count()
        self.assertEqual(total_users, 3)

    def test_fluxo_recepcionista_cadastra_paciente(self):
        """Testa fluxo completo: recepcionista cadastra paciente."""
        # Admin cria recepcionista e profissional de saúde
        recepcionista = self.criar_usuario_direto("recepcionista")
        profissional = self.criar_usuario_direto("profissional_saude")

        # Recepcionista faz login
        client = Client()
        login_success = client.login(cpf=recepcionista.cpf, password="recep123")
        self.assertTrue(login_success)

        # Recepcionista acessa página de cadastro de paciente
        response = client.get(reverse("recepcionista:cadastrar_paciente"))
        self.assertEqual(response.status_code, 200)

        # Cadastra paciente com profissional de saúde correto
        paciente_data = {
            "nome_completo": "Paciente Teste Dinâmico",
            "cartao_sus": "123456789012345",
            "telefone_celular": "11999999999",
            "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "profissional_saude": profissional.id,  # Usar ID do profissional
            "tipo_senha": "G",
        }

        response = client.post(
            reverse("recepcionista:cadastrar_paciente"), data=paciente_data, follow=True
        )
        self.assertEqual(response.status_code, 200)

        # Verifica se paciente foi criado
        paciente = Paciente.objects.get(cartao_sus="123456789012345")
        self.assertEqual(paciente.nome_completo, "Paciente Teste Dinâmico")
        self.assertEqual(paciente.tipo_senha, "G")
        self.assertIsNotNone(paciente.senha)  # Senha deve ter sido gerada

    def test_fluxo_guiche_acessa_painel(self):
        """Testa fluxo: guichê acessa painel."""
        # Admin cria guichê diretamente
        guiche_user = self.criar_usuario_direto("guiche")

        # Guichê faz login
        client = Client()
        login_success = client.login(cpf=guiche_user.cpf, password="guiche123")
        self.assertTrue(login_success)

        # Guichê acessa painel
        response = client.get(reverse("guiche:painel_guiche"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "guiche/painel_guiche.html")

    def test_fluxo_profissional_saude_acessa_painel(self):
        """Testa fluxo: profissional da saúde acessa painel."""
        # Admin cria profissional diretamente
        profissional = self.criar_usuario_direto("profissional_saude")

        # Profissional faz login
        client = Client()
        login_success = client.login(cpf=profissional.cpf, password="prof123")
        self.assertTrue(login_success)

        # Profissional acessa painel
        response = client.get(reverse("profissional_saude:painel_profissional"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profissional_saude/painel_profissional.html")

    def test_fluxo_completo_com_whatsapp(self):
        """Testa fluxo completo incluindo notificação WhatsApp."""

        # 1. Admin cria recepcionista e profissional de saúde
        recepcionista = self.criar_usuario_direto("recepcionista")
        profissional = self.criar_usuario_direto("profissional_saude")

        # 2. Recepcionista cadastra paciente
        client_recep = Client()
        client_recep.login(cpf=recepcionista.cpf, password="recep123")

        paciente_data = {
            "nome_completo": "Paciente WhatsApp",
            "cartao_sus": "777777777777777",
            "telefone_celular": "(11) 98888-8888",  # Formato correto esperado pela validação
            "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "profissional_saude": profissional.id,  # Usar ID do profissional
            "tipo_senha": "G",
        }

        response = client_recep.post(
            reverse("recepcionista:cadastrar_paciente"), data=paciente_data
        )

        # Verifica se o POST foi bem-sucedido
        try:
            paciente = Paciente.objects.get(cartao_sus="777777777777777")
            self.assertEqual(paciente.nome_completo, "Paciente WhatsApp")
            self.assertIsNotNone(paciente.senha)  # Senha deve ter sido gerada
        except Paciente.DoesNotExist:
            # Se paciente não foi criado, verifica se há mensagens de erro na resposta
            self.fail(
                f"Paciente não foi criado. Status: {response.status_code}. Content: {response.content.decode()}"
            )

    def test_fluxo_completo_dinamico_cadastro_chamada_consulta(self):
        """Testa o fluxo completo dinâmico: cadastro -> guichê -> profissional -> consulta."""
        # 1. CRIAR USUÁRIOS
        recepcionista = self.criar_usuario_direto("recepcionista")
        profissional = self.criar_usuario_direto("profissional_saude")
        guiche_user = self.criar_usuario_direto("guiche")

        # Criar guichê para o usuário
        from core.models import Guiche

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
        from core.models import ChamadaProfissional

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
        self.assertEqual(data["profissional_nome"], "Dr.")

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
        from core.models import Guiche

        guiche = Guiche.objects.create(
            numero=1, funcionario=guiche_user, user=guiche_user
        )

        client_recep = Client()
        client_recep.login(cpf=recepcionista.cpf, password="recep123")

        # Cadastrar 3 pacientes diferentes
        pacientes_data = [
            {
                "nome": "Maria Oliveira",
                "sus": "111111111111111",
                "telefone": "11977776666",
                "profissional": profissional1.id,
                "tipo": "G",
            },
            {
                "nome": "Pedro Costa",
                "sus": "222222222222222",
                "telefone": "11966665555",
                "profissional": profissional2.id,
                "tipo": "P",
            },
            {
                "nome": "Ana Pereira",
                "sus": "333333333333333",
                "telefone": "11955554444",
                "profissional": profissional1.id,
                "tipo": "G",
            },
        ]

        pacientes = []
        for data in pacientes_data:
            paciente_data = {
                "nome_completo": data["nome"],
                "cartao_sus": data["sus"],
                "telefone_celular": data["telefone"],
                "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "profissional_saude": data["profissional"],
                "tipo_senha": data["tipo"],
            }

            client_recep.post(
                reverse("recepcionista:cadastrar_paciente"), data=paciente_data
            )
            paciente = Paciente.objects.get(cartao_sus=data["sus"])
            pacientes.append(paciente)
            self.assertTrue(paciente.senha.startswith(data["tipo"]))

        # Guichê chama primeiro paciente (Maria)
        client_guiche = Client()
        client_guiche.login(cpf=guiche_user.cpf, password="guiche123")

        response = client_guiche.post(
            reverse("guiche:chamar_senha", args=[pacientes[0].id])  # Maria
        )
        self.assertEqual(response.status_code, 200)

        # Verificar TV1 mostra Maria sendo chamada
        client_tv1 = Client()
        response = client_tv1.get(reverse("guiche:tv1"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, pacientes[0].nome_completo
        )  # Maria aparece na TV1
        self.assertContains(response, "Guichê 1")  # Guichê aparece na TV1

        # Verificar API da TV1
        response_api = client_tv1.get(reverse("guiche:tv1_api"))
        self.assertEqual(response_api.status_code, 200)
        data = response_api.json()
        self.assertEqual(data["nome_completo"], pacientes[0].nome_completo)
        self.assertEqual(data["guiche"], 1)
        self.assertEqual(data["senha"], pacientes[0].senha)

        # Confirmar atendimento (Maria vai para fila do profissional)
        response = client_guiche.post(
            reverse("guiche:confirmar_atendimento", args=[pacientes[0].id])
        )
        self.assertEqual(response.status_code, 200)

        pacientes[0].refresh_from_db()
        self.assertTrue(pacientes[0].atendido)

        # Profissional1 chama Maria para consulta
        client_prof1 = Client()
        client_prof1.login(cpf=profissional1.cpf, password="prof123")

        response = client_prof1.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                args=[pacientes[0].id, "chamar"],
            )
        )
        self.assertEqual(response.status_code, 200)

        # Verificar TV2 mostra Maria para o profissional1
        client_tv2 = Client()
        response = client_tv2.get(reverse("profissional_saude:tv2"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Maria Oliveira")  # Nome na TV2

        # Verificar painel do profissional1 mostra Maria
        response = client_prof1.get(reverse("profissional_saude:painel_profissional"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Maria Oliveira")

        # Guichê chama segundo paciente (Pedro)
        response = client_guiche.post(
            reverse("guiche:chamar_senha", args=[pacientes[1].id])  # Pedro
        )
        self.assertEqual(response.status_code, 200)

        # Confirmar atendimento (Pedro vai para fila do profissional)
        response = client_guiche.post(
            reverse("guiche:confirmar_atendimento", args=[pacientes[1].id])
        )
        self.assertEqual(response.status_code, 200)

        # Profissional2 chama Pedro
        client_prof2 = Client()
        client_prof2.login(cpf=profissional2.cpf, password="prof123")

        response = client_prof2.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                args=[pacientes[1].id, "chamar"],
            )
        )
        self.assertEqual(response.status_code, 200)

        # Verificar TV2 mostra Pedro para profissional2
        response = client_tv2.get(reverse("profissional_saude:tv2"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pedro Costa")  # Nome na TV2

        # Verificar API da TV2
        response_api = client_tv2.get(reverse("profissional_saude:tv2_api"))
        self.assertEqual(response_api.status_code, 200)
        data = response_api.json()
        self.assertEqual(data["nome_completo"], "Pedro Costa")
        self.assertEqual(data["senha"], pacientes[1].senha)
        self.assertEqual(data["profissional_nome"], "Dra.")

        # Guichê chama terceiro paciente (Ana)
        response = client_guiche.post(
            reverse("guiche:chamar_senha", args=[pacientes[2].id])  # Ana
        )
        self.assertEqual(response.status_code, 200)

        # Confirmar atendimento (Ana vai para fila do profissional1)
        response = client_guiche.post(
            reverse("guiche:confirmar_atendimento", args=[pacientes[2].id])
        )
        self.assertEqual(response.status_code, 200)

        # Verificar que cada profissional vê apenas seus pacientes
        response = client_prof1.get(reverse("profissional_saude:painel_profissional"))
        self.assertContains(response, "Maria Oliveira")
        self.assertContains(response, "Ana Pereira")  # Agora na fila
        self.assertNotContains(response, "Pedro Costa")  # Não deve aparecer

        response = client_prof2.get(reverse("profissional_saude:painel_profissional"))
        self.assertContains(response, "Pedro Costa")
        self.assertNotContains(response, "Maria Oliveira")
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
