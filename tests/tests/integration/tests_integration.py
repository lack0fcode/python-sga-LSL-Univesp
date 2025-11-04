from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import CustomUser, Paciente


# Teste de integração: fluxo completo de cadastro, login, acesso e logout
class IntegracaoFluxoCompletoTest(TestCase):
    def setUp(self):
        print(
            "\033[93m🔗 Teste de integração: Fluxo completo cadastro/login/logout\033[0m"
        )  # Amarelo
        self.client = Client()
        self.funcionario = CustomUser.objects.create_user(
            cpf="12312312399",
            username="12312312399",
            password="funcpass",
            first_name="Func",
            last_name="Test",
            funcao="administrador",
        )

    def test_fluxo_completo(self):
        print("\033[96m  → Etapa 1: Cadastrando paciente via modelo...\033[0m")  # Ciano
        print("\033[94m     Criando objeto Paciente no banco de dados...\033[0m")
        # Cadastro de paciente via model (simulando formulário)
        paciente = Paciente.objects.create(
            nome_completo="Paciente Integração",
            cartao_sus="99988877766",
            horario_agendamento=timezone.now(),
            profissional_saude=self.funcionario,
            tipo_senha="G",
        )
        print(f"\033[94m     Paciente criado com ID: {paciente.id}\033[0m")
        self.assertIsNotNone(paciente.id)
        print("\033[92m    ✅ Paciente cadastrado com sucesso!\033[0m")
        print(
            f"\033[92m       Dados: ID={paciente.id}, Nome={paciente.nome_completo}, Cartão SUS={paciente.cartao_sus}, Tipo Senha={paciente.tipo_senha}\033[0m"
        )

        print("\033[96m  → Etapa 2: Fazendo login com usuário administrador...\033[0m")
        print("\033[94m     Enviando credenciais para autenticação...\033[0m")
        print(f"\033[94m     CPF: {self.funcionario.cpf}, Senha: funcpass\033[0m")
        # Login
        login = self.client.login(cpf="12312312399", password="funcpass")
        self.assertTrue(login)
        print("\033[94m     Sessão criada com sucesso\033[0m")
        print("\033[92m    ✅ Login realizado com sucesso!\033[0m")
        print(
            f"\033[92m       Usuário: {self.funcionario.first_name} {self.funcionario.last_name} (CPF: {self.funcionario.cpf}, Função: {self.funcionario.funcao})\033[0m"
        )

        print("\033[96m  → Etapa 3: Acessando página inicial protegida...\033[0m")
        print("\033[94m     Fazendo requisição GET para página inicial...\033[0m")
        print(f"\033[94m     URL: {reverse('pagina_inicial')}\033[0m")
        # Acesso à página inicial (protegida)
        response = self.client.get(reverse("pagina_inicial"))
        print(f"\033[94m     Resposta recebida: Status {response.status_code}\033[0m")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)
        print("\033[94m     Verificando autenticação do usuário na sessão...\033[0m")
        print("\033[92m    ✅ Página inicial acessada com autenticação!\033[0m")
        print(
            f"\033[92m       Status: {response.status_code}, Usuário autenticado: {response.context['user'].is_authenticated}, Usuário: {response.context['user'].get_full_name()}\033[0m"
        )

        print("\033[96m  → Etapa 4: Fazendo logout...\033[0m")
        print("\033[94m     Fazendo requisição GET para logout...\033[0m")
        print(f"\033[94m     URL: {reverse('logout')}\033[0m")
        # Logout
        response = self.client.get(reverse("logout"), follow=True)
        print(f"\033[94m     Logout processado: Status {response.status_code}\033[0m")
        self.assertEqual(response.status_code, 200)
        print("\033[94m     Verificando se usuário foi deslogado...\033[0m")
        # Após logout, usuário não está autenticado
        response2 = self.client.get(reverse("pagina_inicial"))
        print(
            f"\033[94m     Tentativa de acesso após logout: Status {response2.status_code}\033[0m"
        )
        self.assertEqual(response2.status_code, 302)
        print("\033[94m     Redirecionamento para login confirmado\033[0m")
        print("\033[92m    ✅ Logout realizado com sucesso!\033[0m")
        print(
            f"\033[92m       Após logout: Status {response2.status_code} (redirecionamento para login), Usuário autenticado: False\033[0m"
        )
