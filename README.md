# Sistema de Gerenciamento de Atendimento (SGA) - ILSL 

Este projeto visa informatizar e otimizar o fluxo de atendimento de pacientes no Instituto Lauro de Souza Lima, em Bauru - SP, tornando o processo mais eficiente, seguro e humanizado para profissionais e pacientes.

## Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Instalação](#instalação)
- [Testes](#testes)
- [Como Contribuir](#como-contribuir)
- [Próximos Passos e Melhorias Futuras](#próximos-passos-e-melhorias-futuras)
- [Licença](#licença)

---

## Visão Geral

O SGA foi desenvolvido em Python (Django), com o objetivo de gerenciar de forma integrada o fluxo de pacientes, organização de filas, agendamento e comunicação entre equipe médica e pacientes. Ele tem como foco principal:

- Gerenciamento eletrônico da fila de espera.
- Redução de atrasos e aumento da organização interna.
- Melhoria da comunicação com os pacientes.

---

## Funcionalidades

### Implementadas

- **Cadastro de Pacientes:** Permite cadastrar novos pacientes no sistema com validação completa de dados
- **Gerenciamento de Fila de Espera:** Organização automática da ordem de atendimento com prioridade
- **Controle de Entrada e Saída:** Registro preciso do momento em que cada paciente entra/saí da consulta
- **Histórico de Atendimentos:** Armazena o histórico completo dos atendimentos para consultas futuras
- **Sistema de Chamadas:** Integração WhatsApp para chamada automática de pacientes
- **Displays TV:** Painéis de acompanhamento em tempo real para pacientes e profissionais
- **Relatórios Avançados:** Geração de relatórios detalhados para análise de desempenho
- **Controle de Acesso:** Sistema robusto de permissões por função (administrador, recepcionista, profissional, guichê)
- **Segurança Avançada:** 
  - Proteções CSRF, validação de CPF completa
  - Proteção contra XSS (Cross-Site Scripting)
  - Proteção contra SQL Injection
  - Bloqueio automático contra força bruta
  - Sanitização completa de entrada
- **Interface Responsiva:** Design moderno e intuitivo para desktop e dispositivos móveis
- **Integração Contínua:** CI/CD com GitHub Actions, testes automatizados com PostgreSQL
- **Cobertura de Testes Completa:** 193 testes incluindo segurança e API Twilio

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/lack0fcode/python-sga-LSL-Univesp.git
cd python-sga-LSL-Univesp
```

### 2. Crie o arquivo .env

```bash
DATABASE_URL_EXAMPLE="postgresql://<username>:<password>@<host>:<porta>/<database>?sslmode=require"
```

### 3. Crie e ative um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Rode o servidor localmente

```bash
python manage.py runserver
```

O sistema estará disponível em http://127.0.0.1:8000/

---

## Testes

O projeto possui **188 testes automatizados** que cobrem as funcionalidades principais do sistema, incluindo testes de segurança abrangentes e validações completas.

### Executando os Testes

Para executar os testes, use o comando:

```bash
python manage.py test --settings=sga.settings_test
```

**Nota:** Os testes utilizam SQLite em memória para desenvolvimento local (rápido e isolado), mas PostgreSQL no GitHub Actions (igual ao ambiente de produção).

### Cobertura dos Testes

- ✅ Testes de autenticação e autorização
- ✅ Testes de cadastro e gerenciamento de pacientes
- ✅ Testes de fila de atendimento no guichê
- ✅ Testes de painel e ações do profissional de saúde
- ✅ Testes de integração WhatsApp para chamadas de pacientes
- ✅ Testes de displays TV para acompanhamento em tempo real
- ✅ Testes de relatórios e histórico de chamadas
- ✅ Testes de validação de formulários e segurança
- ✅ Testes de API endpoints
- ✅ Testes de controle de acesso e permissões
- ✅ **Testes de Segurança Avançada:**
  - Proteção contra XSS (Cross-Site Scripting)
  - Proteção contra SQL Injection
  - Proteção contra força bruta (bloqueio de conta)
  - Validações de entrada sanitizadas

### Integração Contínua (CI/CD)

O projeto utiliza GitHub Actions para integração contínua:

- **Testes Automatizados:** Executados em PostgreSQL (ambiente idêntico à produção)
- **Análise de Segurança:** Verificação com Bandit e Safety
- **Linting:** Validação de código com Flake8 e Black
- **Cobertura:** Relatórios detalhados de cobertura de testes

### Arquitetura de Testes

O sistema de testes foi projetado para máxima eficiência e confiabilidade:

- **Desenvolvimento Local:** SQLite in-memory (rápido, ~6 segundos para 188 testes)
- **CI/CD:** PostgreSQL (igual à produção, captura diferenças de comportamento)
- **APIs Externas:** Mocks completos (Twilio) para evitar custos e dependências
- **Segurança:** Testes ativos de vulnerabilidades (XSS, SQL injection, força bruta)
- **Cobertura:** 100% das funcionalidades críticas testadas

---

## Segurança

O sistema implementa **múltiplas camadas de segurança** com validações ativas:

### 🛡️ **Proteções Implementadas:**

- **Proteção CSRF:** Todas as views estão protegidas contra ataques CSRF
- **Validação de CPF:** Validação completa com cálculo de dígitos verificadores
- **Controle de Acesso:** Sistema de permissões baseado em funções (administrador, recepcionista, profissional de saúde, guichê)
- **Proteção XSS:** Validação ativa contra scripts maliciosos em formulários
- **Proteção SQL Injection:** Django ORM com prepared statements (proteção nativa)
- **Bloqueio de Força Bruta:** Contas bloqueadas após 4 tentativas de login falhidas
- **Sanitização de Entrada:** Validação rigorosa de todos os dados de entrada
- **Configurações de Produção:** Headers de segurança, SSL/TLS obrigatório, configurações controladas por variáveis de ambiente

---

Contribuições são muito bem-vindas! Siga os passos abaixo:

1. Faça um fork deste repositório.
2. Crie uma branch para sua feature (`git checkout -b minha-feature`).
3. Commit suas mudanças (`git commit -m 'Minha nova feature'`).
4. Faça um push para a branch (`git push origin minha-feature`).
5. Abra um Pull Request.

---

## Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
