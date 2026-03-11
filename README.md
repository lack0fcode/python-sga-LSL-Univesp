# Sistema de Gerenciamento de Atendimento (SGA) - ILSL

Este projeto visa informatizar e otimizar o fluxo de atendimento de pacientes no Instituto Lauro de Souza Lima, em Bauru - SP, tornando o processo mais eficiente, seguro e humanizado para profissionais e pacientes.

## Como Funciona

### Fluxo de Atendimento

1. **📋 Cadastro do Paciente**
   - Recepcionista cadastra paciente com dados pessoais e agendamento
   - Sistema valida CPF e dados automaticamente

2. **🎫 Chegada e Fila de Espera**
   - Paciente chega e é direcionado para o guichê
   - Recebe senha de acordo com o tipo de atendimento

3. **📢 Chamada Automática**
   - Guichê ou profissional de saúde chama próximo paciente via painel
   - Sistema envia notificação automática via SMS/WhatsApp
   - Paciente é direcionado para o guichê ou sala correta

4. **👨‍⚕️ Atendimento**
   - Profissional confirma início do atendimento
   - Sistema registra horário de entrada na consulta

5. **✅ Finalização**
   - Profissional confirma fim do atendimento
   - Sistema registra horário de saída e atualiza displays

### Displays em Tempo Real

- **TV do Guichê:** Mostra fila atual e próximos pacientes
- **TV das Salas:** Exibe paciente atual e sala de destino
- **Painel do Administrador:** Controle total do sistema

## Funcionalidades Principais

### 👥 Gestão de Usuários
- **Administrador:** Controle total, relatórios e configurações
- **Recepcionista:** Cadastro de pacientes e gerenciamento de filas
- **Profissional de Saúde:** Chamada de pacientes e controle de consultas
- **Guichê:** Atendimento inicial e distribuição de senhas

### 📊 Monitoramento em Tempo Real
- Status online/offline dos funcionários (bolinhas coloridas)
- Displays atualizados automaticamente a cada 5 segundos

### 📋 Relatórios e Analytics
- Relatório HTML detalhado de testes de integração
- Logs visuais categorizados por etapas (Recepcionista, Guichê, Profissional)
- Estatísticas de cobertura e performance dos testes

### 📱 Comunicação Integrada
- Notificações automáticas via SMS/WhatsApp para guichê e profissionais de saúde
- Relatório visual de testes com logs detalhados das notificações

## Instalação

### Pré-requisitos
- Python 3.11+
- PostgreSQL (produção) ou SQLite (desenvolvimento)
- Git

### Passos Rápidos

```bash
# 1. Clone o repositório
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

# 3. Configure o banco de dados
python manage.py migrate

# 4. Crie um superusuário
python manage.py createsuperuser

# 5. Rode o servidor
python manage.py runserver
```

Acesse http://127.0.0.1:8000/ e faça login!

## Testes e Qualidade

### Executando Testes
```bash
# Testes completos
python manage.py test --settings=sga.tests.settings_test

# Com cobertura (excluindo arquivos de análise)
coverage run --source=. --omit="bandit_Rodar.py,bandit_analisar.py,test_fluxocompleto2.py" manage.py test tests --pattern="*test*.py" --settings=sga.tests.settings_test
coverage report

# Teste de fluxo completo com relatório HTML
python test_fluxocompleto2.py
```

### Qualidade do Código
- ✅ **195 testes automatizados** cobrindo funcionalidades críticas
- ✅ **96% de cobertura** de testes automatizados
- ✅ **Análise de segurança** com Bandit e Safety
- ✅ **Linting** com Flake8 e Black
- ✅ **Type checking** com MyPy
- ✅ **CI/CD** automatizado no GitHub Actions
- ✅ **Workflow completo** com testes, linting e segurança
- ✅ **Relatórios automáticos** de cobertura e análise de segurança

## Segurança

### Proteções Implementadas
- 🔒 **Autenticação robusta** com bloqueio contra força bruta
- 🛡️ **Validação completa** de CPF e dados pessoais
- 🔐 **Controle de acesso** por funções (Admin, Recepcionista, Profissional, Guichê)
- 🚫 **Proteção contra ataques** XSS, CSRF, SQL Injection
- 📱 **Sanitização** completa de todas as entradas

## Tecnologias Utilizadas

- **Backend:** Python 3.11+ com Django 4.2
- **Banco de Dados:** PostgreSQL (produção) / SQLite (desenvolvimento)
- **Frontend:** HTML5, CSS3, JavaScript (jQuery, Bootstrap)
- **APIs:** Twilio (SMS/WhatsApp)
- **Testes:** pytest, Coverage.py, unittest.mock
- **Qualidade:** Black, Flake8, MyPy, Bandit, Safety
- **CI/CD:** GitHub Actions
- **Relatórios:** HTML dinâmico com estatísticas visuais

## Static Assets and Deployment

This repository currently includes a `staticfiles/` directory with vendored frontend libraries (jQuery, Select2, XRegExp, etc.). To keep the repository lightweight and avoid tracking large third-party files, follow this workflow:

- Do not commit `staticfiles/` to the repository. It is already listed in `.gitignore`.
- Use Django's `collectstatic` to gather static assets at build/deploy time.
- Prefer CDN-hosted or package-managed copies of third-party libraries (npm, yarn, or CDN links).

If `staticfiles/` is already tracked in the repo, remove it from the index (keeps local files but stops tracking):

```bash
# remove tracked staticfiles from git index (won't delete local files)
git rm -r --cached staticfiles staticfiles_build || true
git commit -m "chore: stop tracking vendored staticfiles; use collectstatic/CDN"
```

CI / Deployment notes:

- The GitHub Actions workflow already runs `python manage.py collectstatic --noinput` during the `django.yml` CI job. Ensure your production build or Docker image runs `collectstatic` as part of deployment.
- If you rely on CDN links, update templates to reference the CDN URLs (example: include jQuery from code.jquery.com).
- Document any required build steps (npm/yarn install, webpack, etc.) in this README or your deployment scripts.

Security note: when switching to CDN-hosted libraries, prefer using subresource integrity (SRI) attributes or a trusted CDN to avoid supply-chain risks.

## Como Contribuir

1. **Fork** o projeto
2. **Clone** sua fork: `git clone https://github.com/SEU_USERNAME/python-sga-LSL-Univesp.git`
3. **Crie uma branch** para sua feature: `git checkout -b minha-feature`
4. **Faça suas mudanças** seguindo os padrões do projeto
5. **Execute os testes:** `python manage.py test --settings=sga.tests.settings_test`
6. **Commit suas mudanças:** `git commit -m 'feat: descrição da feature'`
7. **Push para sua branch:** `git push origin minha-feature`
8. **Abra um Pull Request**

### Padrões de Commit
- `feat:` para novas funcionalidades
- `fix:` para correções de bugs
- `docs:` para documentação
- `refactor:` para refatoração de código
- `test:` para testes

## Suporte

Para dúvidas ou problemas:
- 🐛 **Issues:** [GitHub Issues](https://github.com/lack0fcode/python-sga-LSL-Univesp/issues)
- 📖 **Documentação:** Este README e comentários no código

---

**Instituto Lauro de Souza Lima - Bauru/SP**  
*Sistema desenvolvido para otimizar o atendimento médico e melhorar a experiência de pacientes e profissionais.*
