"""
Script para executar teste de fluxo completo e gerar relatório HTML dedicado com dados fictícios.
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Tuple
from unittest.mock import patch

# Configurar Django primeiro
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sga.tests.settings_test")
import django

django.setup()


# Aplicar mock ANTES de importar as views
_current_test_instance = None
_sms_real_enviado = False  # Flag para controlar envio de SMS real apenas uma vez


def mock_enviar_whatsapp(
    numero_destino: str,
    mensagem: str = None,
    content_sid: str = None,
    content_variables: dict = None,
) -> Dict[str, Any]:
    """Mock que registra as chamadas e ENVIA SMS REAL apenas na primeira chamada do guichê."""
    global _sms_real_enviado

    # Se já enviou SMS real, retorna mock simulado
    if _sms_real_enviado:
        resultado_mock = {
            "status": "success",
            "sid": "SM_mock_" + str(hash(f"{numero_destino}_{mensagem}"))[:10],
            "to": numero_destino,
            "message_status": "sent",
            "date_created": datetime.now().isoformat(),
            "direction": "outbound-api",
            "price": None,
            "error_message": None,
            "message_type": "sms",
        }

        # Adicionar log como mock
        if _current_test_instance is not None:
            _current_test_instance.log(
                "whatsapp",
                f"📱 SMS MOCK (simulado) para {numero_destino}: {mensagem} | SID: {resultado_mock['sid']}",
            )

        print(f"[SMS MOCK] 📱 SMS simulado enviado para {numero_destino}: {mensagem}")
        return resultado_mock

    # Primeira chamada: enviar SMS real
    from twilio.rest import Client
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print(f"[SMS REAL] 📱 Enviando SMS REAL para {numero_destino}: {mensagem}")

    # Marcar que SMS real foi enviado ANTES de tentar
    _sms_real_enviado = True

    try:
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

        # Usar o número Twilio válido para SMS
        from_number = "+14178554802"  # Número verificado da conta

        # Se for template, usar mensagem padrão
        if content_sid:
            body = f"📱 SMS TESTE - Template WhatsApp: Seu atendimento foi agendado para {content_variables.get('1', 'hoje')} às {content_variables.get('2', 'agora')}."
        else:
            body = f"📱 SMS TESTE - {mensagem}"

        message = client.messages.create(
            from_=from_number, body=body, to=numero_destino
        )

        resultado = {
            "status": "success",
            "sid": message.sid,
            "to": numero_destino,
            "message_status": message.status,
            "date_created": (
                message.date_created.isoformat() if message.date_created else None
            ),
            "direction": message.direction,
            "price": message.price,
            "error_message": message.error_message,
            "message_type": "sms",
        }

        # Adicionar log diretamente à instância atual do teste
        if _current_test_instance is not None:
            _current_test_instance.log(
                "whatsapp",
                f"📱 SMS REAL enviado para {numero_destino}: {body} | SID: {message.sid} | Status: {message.status}",
            )

        print(
            f"[SMS REAL] ✅ SMS REAL enviado! SID: {message.sid}, Status: {message.status}"
        )
        return resultado

    except Exception as e:
        error_msg = f"❌ Erro ao enviar SMS: {str(e)}"
        print(f"[SMS REAL] {error_msg}")

        if _current_test_instance is not None:
            _current_test_instance.log("whatsapp", error_msg)

        return {"status": "error", "error": str(e)}


mock_patch = patch(
    "core.utils.enviar_sms_ou_whatsapp", side_effect=mock_enviar_whatsapp
)
mock_patch.start()

from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import Paciente, CustomUser, Guiche, Chamada, ChamadaProfissional

User = get_user_model()


class TestFluxoCompletoComRelatorio(TransactionTestCase):
    """Teste de fluxo completo que gera relatório HTML com dados ficticios."""

    def setUp(self):
        """Configura dados iniciais para os testes."""
        # Definir esta instância como a atual para o mock
        global _current_test_instance, _sms_real_enviado
        _current_test_instance = self
        _sms_real_enviado = (
            False  # Reset flag para permitir SMS real na primeira chamada
        )

        # Inicializar lista para logs
        self.logs: List[Dict[str, Any]] = []

        # Criar usuários diretamente
        self.recepcionista = User.objects.create_user(
            cpf="06685907002",
            username="06685907002",
            password="recepcionista123",
            first_name="Maria",
            last_name="Recepção",
            funcao="recepcionista",
        )

        self.profissional = User.objects.create_user(
            cpf="49115029085",
            username="49115029085",
            password="profissional123",
            first_name="Dr.",
            last_name="Silva",
            funcao="profissional_saude",
            sala=101,
        )

        self.guiche_user = User.objects.create_user(
            cpf="31411943007",
            username="31411943007",
            password="guiche123",
            first_name="João",
            last_name="Guichê",
            funcao="guiche",
        )

        # Criar guichê
        self.guiche = Guiche.objects.create(
            numero=1, funcionario=self.guiche_user, user=self.guiche_user
        )

    def tearDown(self):
        """Limpa dados após os testes."""
        pass

    def log(self, tipo: str, mensagem: str):
        """Adiciona log à lista."""
        self.logs.append({"tipo": tipo, "mensagem": mensagem})
        print(f"[{tipo.upper()}] {mensagem}")

    def test_fluxo_completo_com_relatorio(self):
        """Testa o fluxo completo e gera relatório HTML."""
        print("\n" + "=" * 80)
        print("🧪 TESTE DE FLUXO COMPLETO COM RELATÓRIO - SGA-ILSL")
        print("=" * 80)

        # Etapa 1: Recepcionista cadastra paciente
        self.log("info", "Etapa 1: Recepcionista cadastra paciente")

        self.log(
            "info",
            f"Recepcionista criado: ID={self.recepcionista.id}, CPF={self.recepcionista.cpf}, Nome={self.recepcionista.first_name} {self.recepcionista.last_name}, Função={self.recepcionista.funcao}",
        )
        self.log(
            "info",
            f"Profissional criado: ID={self.profissional.id}, CPF={self.profissional.cpf}, Nome={self.profissional.first_name} {self.profissional.last_name}, Função={self.profissional.funcao}, Sala={self.profissional.sala}",
        )
        self.log("success", "✅ Usuários criados com sucesso!")

        client1 = Client()
        self.log(
            "info",
            f"Fazendo login com recepcionista: CPF={self.recepcionista.cpf}, Senha=*****",
        )
        login_success = client1.login(
            cpf=self.recepcionista.cpf, password="recepcionista123"
        )
        self.assertTrue(login_success)
        self.log(
            "info",
            f"Sessão criada para usuário ID={self.recepcionista.id} ({self.recepcionista.first_name} {self.recepcionista.last_name})",
        )
        self.log("success", "✅ Recepcionista logado!")

        # Cadastrar paciente
        paciente_data = {
            "nome_completo": "Kauã Fernandes Azevedo",
            "cartao_sus": "123456789012346",
            "telefone_celular": "(51) 99591-9117",
            "horario_agendamento": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "profissional_saude": self.profissional.id,
            "tipo_senha": "G",
        }
        self.log(
            "info",
            f"Cadastrando paciente: Nome={paciente_data['nome_completo']}, Cartão SUS={paciente_data['cartao_sus']}, Tipo Senha={paciente_data['tipo_senha']}, Profissional ID={paciente_data['profissional_saude']}",
        )
        response = client1.post(
            reverse("recepcionista:cadastrar_paciente"), data=paciente_data, follow=True
        )
        self.assertEqual(response.status_code, 200)

        paciente = Paciente.objects.get(nome_completo="Kauã Fernandes Azevedo")
        telefone_e164 = paciente.telefone_e164()
        self.log(
            "success",
            f"✅ Paciente cadastrado: ID={paciente.id}, Nome={paciente.nome_completo}, Senha={paciente.senha}, Tipo={paciente.tipo_senha}, Atendido={paciente.atendido}, Telefone={paciente.telefone_celular}, E164={telefone_e164}",
        )

        # Logout recepcionista
        self.log(
            "info",
            f"Recepcionista ID={self.recepcionista.id} ({self.recepcionista.first_name} {self.recepcionista.last_name}) fazendo logout...",
        )
        response = client1.get(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.log("success", "✅ Recepcionista deslogado!")

        # Etapa 2: Guichê chama paciente
        self.log("info", "Etapa 2: Guichê chama paciente")

        self.log(
            "info",
            f"Guichê criado: ID={self.guiche.id}, Número={self.guiche.numero}, Funcionário ID={self.guiche_user.id} ({self.guiche_user.first_name} {self.guiche_user.last_name})",
        )

        client2 = Client()
        self.log(
            "info",
            f"Guichê fazendo login: CPF={self.guiche_user.cpf}, Senha=*****, Função={self.guiche_user.funcao}",
        )
        login_success = client2.login(cpf=self.guiche_user.cpf, password="guiche123")
        self.assertTrue(login_success)
        self.log(
            "info",
            f"Sessão criada para guichê ID={self.guiche.id} (Funcionário: {self.guiche_user.first_name} {self.guiche_user.last_name})",
        )
        self.log("success", "✅ Guichê logado!")

        # Guichê chama paciente
        self.log(
            "info",
            f"Guichê {self.guiche.numero} chamando paciente ID={paciente.id} ({paciente.nome_completo})...",
        )
        response = client2.post(reverse("guiche:chamar_senha", args=[paciente.id]))
        self.assertEqual(response.status_code, 200)
        chamada = Chamada.objects.filter(paciente=paciente, acao="chamada").latest(
            "data_hora"
        )
        self.log(
            "success",
            f"✅ Paciente chamado: Chamada ID={chamada.id}, Paciente={chamada.paciente.nome_completo}, Guichê={chamada.guiche.numero}, Ação={chamada.acao}",
        )

        # Verificar TV1
        self.log("info", f"Verificando TV1 para paciente {paciente.nome_completo}...")
        response = client2.get(reverse("guiche:tv1"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, paciente.nome_completo)
        self.log(
            "tv",
            f"✅ TV1 (Status: {response.status_code}) mostra paciente: '{paciente.nome_completo}' - Guichê {self.guiche.numero} - Senha {paciente.senha}",
        )

        # Guichê reanuncia
        self.log(
            "info",
            f"Guichê {self.guiche.numero} reanunciando paciente ID={paciente.id} ({paciente.nome_completo})...",
        )
        response = client2.post(reverse("guiche:reanunciar_senha", args=[paciente.id]))
        self.assertEqual(response.status_code, 200)
        reanuncio = Chamada.objects.filter(paciente=paciente, acao="reanuncio").latest(
            "data_hora"
        )
        self.log(
            "success",
            f"✅ Paciente reanunciado: Reanúncio ID={reanuncio.id}, Paciente={reanuncio.paciente.nome_completo}, Guichê={reanuncio.guiche.numero}, Ação={reanuncio.acao}",
        )

        # Guichê confirma atendimento
        self.log(
            "info",
            f"Guichê {self.guiche.numero} confirmando atendimento do paciente ID={paciente.id} ({paciente.nome_completo})...",
        )
        response = client2.post(
            reverse("guiche:confirmar_atendimento", args=[paciente.id])
        )
        self.assertEqual(response.status_code, 200)
        confirmacao = Chamada.objects.filter(
            paciente=paciente, acao="confirmado"
        ).latest("data_hora")
        paciente.refresh_from_db()
        self.log(
            "success",
            f"✅ Atendimento confirmado: Confirmação ID={confirmacao.id}, Paciente={confirmacao.paciente.nome_completo}, Guichê={confirmacao.guiche.numero}, Ação={confirmacao.acao}, Paciente.atendido={paciente.atendido}",
        )

        # Verificar histórico TV1
        self.log(
            "info",
            f"Verificando histórico TV1 para paciente confirmado {paciente.nome_completo}...",
        )
        response = client2.get(reverse("guiche:tv1"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, paciente.nome_completo)
        self.log(
            "tv",
            f"✅ Histórico TV1 contém paciente confirmado: {paciente.nome_completo}",
        )

        # Logout guichê
        self.log(
            "info",
            f"Guichê ID={self.guiche.id} (Funcionário: {self.guiche_user.first_name} {self.guiche_user.last_name}) fazendo logout...",
        )
        response = client2.get(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.log("success", "✅ Guichê deslogado!")

        # Etapa 3: Profissional chama paciente
        self.log("info", "Etapa 3: Profissional chama paciente")

        client3 = Client()
        self.log(
            "info",
            f"Profissional fazendo login: CPF={self.profissional.cpf}, Senha=*****, Função={self.profissional.funcao}, Sala={self.profissional.sala}",
        )
        login_success = client3.login(
            cpf=self.profissional.cpf, password="profissional123"
        )
        self.assertTrue(login_success)
        self.log(
            "info",
            f"Sessão criada para profissional ID={self.profissional.id} ({self.profissional.first_name} {self.profissional.last_name})",
        )
        self.log("success", "✅ Profissional logado!")

        # Profissional chama paciente
        self.log(
            "info",
            f"Profissional {self.profissional.first_name} {self.profissional.last_name} (Sala {self.profissional.sala}) chamando paciente ID={paciente.id} ({paciente.nome_completo})...",
        )
        response = client3.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                args=[paciente.id, "chamar"],
            )
        )
        self.assertEqual(response.status_code, 200)
        chamada_prof = ChamadaProfissional.objects.filter(
            paciente=paciente, acao="chamada"
        ).latest("data_hora")
        self.log(
            "success",
            f"✅ Paciente chamado pelo profissional: Chamada ID={chamada_prof.id}, Paciente={chamada_prof.paciente.nome_completo}, Profissional={chamada_prof.profissional_saude.first_name} {chamada_prof.profissional_saude.last_name}, Ação={chamada_prof.acao}",
        )

        # Verificar TV2
        self.log("info", f"Verificando TV2 para paciente {paciente.nome_completo}...")
        response = client3.get(reverse("profissional_saude:tv2"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, paciente.nome_completo)
        self.log(
            "tv",
            f"✅ TV2 (Status: {response.status_code}) mostra paciente: '{paciente.nome_completo}' - Profissional {self.profissional.first_name} {self.profissional.last_name} - Senha {paciente.senha}",
        )

        # Profissional reanuncia
        self.log(
            "info",
            f"Profissional {self.profissional.first_name} {self.profissional.last_name} reanunciando paciente ID={paciente.id} ({paciente.nome_completo})...",
        )
        response = client3.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                args=[paciente.id, "reanunciar"],
            )
        )
        self.assertEqual(response.status_code, 200)
        reanuncio_prof = ChamadaProfissional.objects.filter(
            paciente=paciente, acao="reanuncio"
        ).latest("data_hora")
        self.log(
            "success",
            f"✅ Paciente reanunciado pelo profissional: Reanúncio ID={reanuncio_prof.id}, Paciente={reanuncio_prof.paciente.nome_completo}, Profissional={reanuncio_prof.profissional_saude.first_name} {reanuncio_prof.profissional_saude.last_name}, Ação={reanuncio_prof.acao}",
        )

        # Profissional confirma atendimento
        self.log(
            "info",
            f"Profissional {self.profissional.first_name} {self.profissional.last_name} confirmando atendimento do paciente ID={paciente.id} ({paciente.nome_completo})...",
        )
        response = client3.post(
            reverse(
                "profissional_saude:realizar_acao_profissional",
                args=[paciente.id, "confirmar"],
            )
        )
        self.assertEqual(response.status_code, 200)
        confirmacao_prof = ChamadaProfissional.objects.filter(
            paciente=paciente, acao="confirmado"
        ).latest("data_hora")
        paciente.refresh_from_db()
        self.log(
            "success",
            f"✅ Atendimento confirmado pelo profissional: Confirmação ID={confirmacao_prof.id}, Paciente={confirmacao_prof.paciente.nome_completo}, Profissional={confirmacao_prof.profissional_saude.first_name} {confirmacao_prof.profissional_saude.last_name}, Ação={confirmacao_prof.acao}, Paciente.atendido={paciente.atendido}",
        )

        # Verificar histórico TV2
        self.log(
            "info",
            f"Verificando histórico TV2 para paciente confirmado {paciente.nome_completo}...",
        )
        response = client3.get(reverse("profissional_saude:tv2"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, paciente.nome_completo)
        self.log(
            "tv",
            f"✅ Histórico TV2 contém paciente confirmado: {paciente.nome_completo}",
        )

        # Logout profissional
        self.log(
            "info",
            f"Profissional ID={self.profissional.id} ({self.profissional.first_name} {self.profissional.last_name}) fazendo logout...",
        )
        response = client3.get(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.log("success", "✅ Profissional deslogado!")

        # Gerar relatório HTML
        self.gerar_relatorio_html()

        print("\n" + "=" * 80)
        print("🎉 FLUXO COMPLETO FINALIZADO COM SUCESSO!")
        print("📄 Relatório HTML gerado: relatorio_teste_real.html")
        print("=" * 80)

    def gerar_relatorio_html(self):
        """Gera relatório HTML com dados ficticios do teste."""

        # Organizar logs por etapas
        etapas: Dict[str, List[Tuple[str, str]]] = {
            "Etapa 1: Recepcionista cadastra paciente": [],
            "Etapa 2: Guichê chama paciente": [],
            "Etapa 3: Profissional chama paciente": [],
        }

        etapa_atual = None
        for log in self.logs:
            if log["mensagem"].startswith("Etapa"):
                etapa_atual = log["mensagem"]
            elif etapa_atual:
                etapas[etapa_atual].append((log["tipo"], log["mensagem"]))

        # Template HTML
        html_template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Teste Real - SGA-ILSL</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .test-title {{
            color: #1e3c72;
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 30px;
            text-align: center;
            border-bottom: 3px solid #1e3c72;
            padding-bottom: 15px;
        }}

        .step {{
            margin-bottom: 30px;
            border-left: 4px solid #3498db;
            padding-left: 20px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}

        .step-title {{
            color: #2c3e50;
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}

        .step-title::before {{
            content: "→";
            color: #3498db;
            font-size: 1.2em;
            margin-right: 10px;
        }}

        .log-entry {{
            margin: 8px 0;
            padding: 8px 12px;
            border-radius: 6px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            line-height: 1.4;
        }}

        .log-info {{
            background: #e3f2fd;
            border-left: 3px solid #2196f3;
            color: #1565c0;
        }}

        .log-success {{
            background: #e8f5e8;
            border-left: 3px solid #4caf50;
            color: #2e7d32;
            font-weight: bold;
        }}

        .log-title {{
            background: #fff3e0;
            border-left: 3px solid #ff9800;
            color: #e65100;
            font-weight: bold;
            font-size: 16px;
        }}

        .tv-verification {{
            background: #f3e5f5;
            border-left: 3px solid #9c27b0;
            color: #7b1fa2;
            font-weight: bold;
            margin: 10px 0;
        }}

        .log-whatsapp {{
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            border-left: 3px solid #d32f2f;
            color: white;
            font-weight: bold;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.02); }}
            100% {{ transform: scale(1); }}
        }}

        .final-success {{
            background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
            color: white;
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            font-size: 1.2em;
            font-weight: bold;
            margin-top: 30px;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }}

        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
        }}

        .stat {{
            background: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #28a745;
        }}

        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2em;
            }}

            .content {{
                padding: 20px;
            }}

            .stats {{
                flex-direction: column;
                gap: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Relatório de Teste Real</h1>
            <p>Sistema de Gerenciamento de Atendimento - ILSL</p>
        </div>

        <div class="content">
            <div class="test-title">🔗 Teste de Integração: Fluxo Completo de Atendimento (Dados Fictícios)</div>

            <div class="stats">
                <div class="stat">
                    <div class="stat-number">3</div>
                    <div class="stat-label">Etapas Executadas</div>
                </div>
                <div class="stat">
                    <div class="stat-number">15</div>
                    <div class="stat-label">Ações Validadas</div>
                </div>
                <div class="stat">
                    <div class="stat-number">2</div>
                    <div class="stat-label">TVs Verificadas</div>
                </div>
            </div>
"""

        # Adicionar etapas
        for titulo_etapa, logs_etapa in etapas.items():
            html_template += f"""
            <div class="step">
                <div class="step-title">{titulo_etapa}</div>"""

            for tipo_log, mensagem in logs_etapa:
                classe_css = f"log-{tipo_log}"
                if tipo_log == "tv":
                    classe_css = "log-success tv-verification"
                elif tipo_log == "whatsapp":
                    classe_css = "log-whatsapp"
                html_template += f"""
                <div class="log-entry {classe_css}">{mensagem}</div>"""

            html_template += """
            </div>"""

        # Finalizar HTML
        html_template += """

            <div class="final-success">
                🎉 Fluxo completo de atendimento finalizado com sucesso!
            </div>
        </div>

        <div class="footer">
            <p>Relatório gerado em {data_geracao}</p>
            <p>Sistema SGA-ILSL - Testes de Integração com Dados Fictícios</p>
        </div>
    </div>
</body>
</html>"""

        # Formatar o template com os dados
        html_final = html_template.format(
            data_geracao=datetime.now().strftime("%d de %B de %Y"),
        )

        # Salvar o arquivo
        with open("relatorio_teste_real.html", "w", encoding="utf-8") as f:
            f.write(html_final)

        print("✅ Relatório HTML com dados fictícios gerado com sucesso!")
        print("📄 Arquivo: relatorio_teste_real.html")


if __name__ == "__main__":
    # Executar o teste
    import django
    from django.conf import settings
    from django.test.utils import get_runner

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sga.tests.settings_test")
    django.setup()

    TestCase = get_runner(settings)
    test_runner = TestCase()
    failures = test_runner.run_tests(["__main__"])

    if failures == 0:
        print("\n✅ Todos os testes passaram!")
    else:
        print(f"\n❌ {failures} teste(s) falharam.")
