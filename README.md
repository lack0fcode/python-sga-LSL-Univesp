# Sistema de Gerenciamento de Atendimento (SGA) - ILSL 

Este projeto visa informatizar e otimizar o fluxo de atendimento de pacientes no Instituto Lauro de Souza Lima, em Bauru - SP tornando o processo mais eficiente e humanizado para profissionais e pacientes.

## Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Instalação](#instalação)
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

- **Cadastro de Pacientes:** Permite cadastrar novos pacientes no sistema com dados essenciais.
- **Gerenciamento de Fila de Espera:** Organização automática da ordem de atendimento, facilitando o acompanhamento em tempo real.
- **Controle de Entrada e Saída:** Registro do momento em que cada paciente entra/saí da consulta.
- **Histórico de Atendimentos:** Armazena o histórico dos atendimentos realizados para consultas futuras.
- **Relatórios:** Geração de relatórios para análise do fluxo de pacientes e desempenho do atendimento.
- **Interface Simples e Intuitiva:** Foco na facilidade de uso para toda a equipe.

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

## Como Contribuir

Contribuições são muito bem-vindas! Siga os passos abaixo:

1. Faça um fork deste repositório.
2. Crie uma branch para sua feature (`git checkout -b minha-feature`).
3. Commit suas mudanças (`git commit -m 'Minha nova feature'`).
4. Faça um push para a branch (`git push origin minha-feature`).
5. Abra um Pull Request.

Confira as issues abertas para sugestões de melhorias e funcionalidades.

---
