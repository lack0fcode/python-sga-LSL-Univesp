# Roteiro para Vídeo de Apresentação do Projeto (PI2) — UNIVESP

**Duração total sugerida:** 10:00

> Observação: substitua o placeholder do link do PI1 pelo URL real do vídeo do PI1.

---

## 00:00 – 00:10 — Abertura (vinheta)
- Visual: Logotipo do projeto / UNIVESP + música curta (2–3s) e fade.
- Texto na tela: "Apresentação do Projeto — PI2 | UNIVESP"
- Narração (voz off opcional): "Apresentação do projeto desenvolvido para o PI2 — UNIVESP."

---

## 00:10 – 01:40 — INTRODUÇÃO (1:30) — Gustavo e Amanda
Objetivo: contextualizar o projeto, relação com PI1, requisitos do PI2, menção a JavaScript e acessibilidade.

- Cena: Gustavo e Amanda em plano médio (ou tela dividida), ambiente de trabalho.
- Texto na tela: "Introdução — Gustavo & Amanda"

Falas sugeridas (cada trecho ~20–30s, total 1:30):
- Gustavo (0:10–0:50):
  - "Olá, somos a equipe do projeto SGA (ou nome do projeto). Este vídeo apresenta o trabalho desenvolvido para o PI2 da UNIVESP."
  - "O PI2 dá continuidade ao que foi iniciado no PI1; no PI1 entregamos a base do sistema, incluindo cadastro de pacientes, fluxo de atendimento e painéis de visualização."
  - "Você pode ver o vídeo do PI1 aqui:" — (mostrar link/thumbnail) `[Vídeo PI1](LINK_DO_VIDEO_PI1)` (pausar 2–3s para leitura).
- Amanda (0:50–1:40):
  - "Para o PI2 recebemos novos requisitos (listar brevemente): integração com nuvem/deploy, uso de APIs externas/internas, controle de versão com repositório, e testes automatizados."
  - "É importante dizer que no PI1 já havíamos começado a aplicar JavaScript para melhorar a interface e também algumas práticas de acessibilidade, mesmo quando isso ainda não era requisito formal — por isso tivemos vantagem ao evoluir o projeto."
  - "No resto do vídeo vamos mostrar as escolhas técnicas e as telas, além de explicar como implementamos cada ponto."

Cenas/Visual:
- Mostrar rapidamente screenshots das telas principais do sistema (painel, TV2, guichê, cadastro).
- Inserir legendas com os requisitos do PI2 enquanto Amanda fala.

---

## 01:40 – 03:40 — NUVEM (2:00) — Gustavo
Objetivo: explicar o conceito de nuvem, onde o projeto está hospedado e demonstrar telas de deploy/console.

- Cena: Gustavo em locução + gravação de tela (screen capture) mostrando painel do provedor (ex.: Vercel, Heroku, DigitalOcean, AWS — adaptar conforme usado).
- Texto na tela: "Nuvem — Deploy e Infraestrutura"

Falas sugeridas (~2:00):
- "Nuvem é a entrega de recursos de computação via internet. Para nosso projeto, utilizamos o Vercel para hospedar a aplicação, o que nos trouxe deploy contínuo, escalabilidade e facilidade de rollback."
- "Aqui vocês podem ver o processo de deploy: cada push para a branch principal dispara um build automático; mostramos logs e deploys bem-sucedidos."
- "Também configuramos variáveis de ambiente para credenciais e usamos storage para arquivos estáticos/media."

Cenas/Visual:
- Mostrar a dashboard do provedor, histórico de deploys, logs de build, e a URL pública do serviço.
- Inserir callouts: "CI/CD ativo", "Variáveis de ambiente", "Storage para assets".
- Mostrar brevemente como atualizar o backend/frontend e o deploy automatizado.

Dica técnica: mencionar como o projeto usa settings separados para produção/testes (ex.: `sga.settings_test` ou equivalente).

---

## 03:40 – 05:40 — USO DE API (2:00) — Amanda
Objetivo: explicar o conceito de API, justificar escolha e demonstrar integração no projeto.

- Cena: Amanda em locução + gravação de tela mostrando endpoints e chamadas (Postman ou console do navegador).
- Texto na tela: "APIs — Integração e Escolhas"

Falas sugeridas (~2:00):
- "API (Application Programming Interface) é a interface que permite que sistemas conversem entre si. No nosso projeto usamos APIs para comunicação interna entre frontend e backend, integração com serviços externos (ex.: envio de WhatsApp/Twilio) e APIs internas para a TV2."
- "Escolhemos arquitetura REST/JSON por ser simples e compatível com o frontend em JavaScript. Para chamadas externas, usamos [nome da API externa, ex.: Twilio — se aplicável] com tratamento de erros e fallback (mock) durante testes."
- "Mostramos aqui um exemplo: quando uma senha é chamada, o backend registra a chamada e a API da TV2 retorna o JSON consumido pelo display."

Cenas/Visual:
- Apresentar uma chamada real via browser/Postman: resposta JSON com campos (senha, nome_completo, profissional_nome, sala).
- Mostrar trecho do código (curto) onde a API é implementada (por exemplo, `tv2_api_view`), destacando segurança (autenticação / validação).
- Mostrar mocks usados nos testes para evitar chamadas externas.

Observação: mencionar que, para desenvolvimento, a equipe isolou integrações externas com mocks (evita custos/instabilidade).

---

## 05:40 – 07:40 — CONTROLE DE VERSÃO (2:00) — Gustavo
Objetivo: explicar versionamento, branch strategy, e mostrar telas do repositório.

- Cena: Gustavo + gravação de tela do GitHub/GitLab (repositório).
- Texto na tela: "Controle de Versão — Git & Repositório"

Falas sugeridas (~2:00):
- "Controle de versão é o registro de alterações no código. Usamos Git hospedado em [GitHub/GitLab]."
- "Nossa estratégia: branch `main` para produção, branches de feature para desenvolvimento, PRs (pull requests) para revisão de código e merges somente após aprovação."
- "Também usamos tags/semantic versioning para releases e integridade do projeto."
- "Aqui mostramos o fluxo: criar branch, desenvolver, abrir PR, rodar testes, revisar e mesclar."

Cenas/Visual:
- Mostrar o repositório, histórico de commits, exemplo de PR com comentários e aprovação.
- Mostrar CI status (se houver) e como um merge dispara deploy automático.
- Inserir callout com boas práticas: mensagens de commit claras, revisões, e uso de issues para rastrear requisitos.

---

## 07:40 – 09:40 — TESTES (2:00) — Caue Tragante
Objetivo: apresentar estratégia de testes, tipos de testes e demonstrar execução (unidade/integracao/coverage).

- Cena: Caue em locução + gravação de terminal executando testes (pytest/manage.py test) e mostrando relatório de coverage.
- Texto na tela: "Testes — Estratégia e Resultados"

Falas sugeridas (~2:00):
- "Fui responsável pela parte de testes. Realizamos testes unitários e de integração usando o framework de testes do Django e `pytest` onde aplicável."
- "Cobertura: monitoramos com `coverage.py` para garantir que as áreas críticas estejam testadas; ajustamos dados de teste para refletir regras de negócio (ex.: seleção de sala para profissionais)."
- "Também mockamos serviços externos (ex.: envio de WhatsApp/Twilio) para evitar efeitos colaterais durante execução dos testes."
- "Aqui mostramos a execução: (mostrar terminal) — todos os testes passaram e o coverage final ficou em torno de 94% (substituir pelo valor atual, se necessário)."

Cenas/Visual:
- Mostrar comandos no terminal e resultados: numeração de testes, OK/FAIL, e trecho do relatório da coverage com percentuais.
- Mostrar exemplos de testes importantes (pequenos trechos): criação de usuário, fluxo de chamada para TV2, APIs.
- Nota rápida: mencionar que testes são executados em CI em cada PR.

---

## 09:40 – 10:00 — ENCERRAMENTO (0:30) — Gustavo e Amanda
Objetivo: agradecimentos, próximos passos e chamada para ação.

- Cena: Gustavo e Amanda em plano médio, tom amigável.
- Texto na tela: "Obrigado! Próximos passos e contato"

Falas sugeridas (~0:30):
- Gustavo: "Obrigado por assistir. Esperamos que tenha ficado claro como evoluímos o sistema do PI1 para o PI2 e as escolhas técnicas que tomamos."
- Amanda: "Se quiser ver o código ou contribuir, o repositório está público em [LINK_DO_REPOSITORIO] — e o vídeo do PI1 está aqui: [Vídeo PI1](LINK_DO_VIDEO_PI1)."
- Ambos (final): "Perguntas e contribuições são bem-vindas — até mais!"

Cenas/Visual:
- Mostrar link do repositório, contatos dos integrantes (opcional), e créditos rápidos (nomes: Gustavo, Amanda, Caue Tragante).
- Fade out com logotipo e música curta.

---

## Anotações de Produção
- Formato: 16:9, resolução 1080p.
- Tom: claro e didático; evitar demasiada tecnicidade sem contexto.
- Duração alvo: ~10 minutos (conforme tempos acima).
- Arquivos / assets a ter à mão:
  - Link do vídeo PI1 (substituir placeholder).
  - URL do repositório.
  - Capturas de tela: dashboards de nuvem, GitHub PRs, Postman/console, resultados de testes/coverage.
  - Trechos de código curtos (máx. 10–15s cada) com destaque em sintaxe.
- Legendas: gerar legendas (importante para acessibilidade).
- Acessibilidade: usar contraste alto no texto em tela, fonte legível, e descrever imagens importantes ao falar (para deficientes visuais).

---

**Próximos passos sugeridos**:
- Substituir os placeholders (`LINK_DO_VIDEO_PI1`, `LINK_DO_REPOSITORIO`, `NOME_DO_PROVEDOR`) pelos links reais.
- Gerar `ROTEIRO_PI2.md` em formato final (este arquivo) e distribuí-lo para a equipe.
- Opcional: adaptar o roteiro para versão curta (2–3 min) ou técnica (para banca).

---

> Créditos: Gustavo, Amanda, Caue Tragante
