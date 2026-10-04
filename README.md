# A Ponte: Um Agente A2A com MCP por Dentro

> *Onde termina a profundidade e começa o alcance*

**Projeto:** MBA Engenharia de Software com IA (Full Cycle / Hill Valley Tech)  
**Especificações Suportadas:** A2A Protocol v1.0 & Model Context Protocol (MCP v2 - 2026-07-28)

---

## 1. Visão Geral do Projeto

O projeto **"A Ponte"** implementa a integração entre duas especificações de protocolo stateless:
1. **Servidor A2A (Agent-to-Agent Protocol v1.0)**: Exposto na porta `7300` (binding JSON-RPC 2.0 sobre HTTP), publicando o Agent Card em `GET /.well-known/agent-card.json` com a skill `reservar-sala`, e gerenciando o ciclo de vida de tarefas (`Tasks`).
2. **Servidor MCP (Model Context Protocol v2 - Revisão 2026-07-28)**: Exposto na porta `7301` (`/mcp` sobre Streamable HTTP), oferecendo ferramentas de domínio (`listar_salas`, `consultar_disponibilidade`, `reservar_sala`) e o recurso de política de uso (`politica://uso`).

O elemento central da arquitetura é a **Ponte**: a interceptação determinística da resposta `input_required` (solicitação de elicitation MRTR por conflito de agenda), a transição da `Task` A2A para `TASK_STATE_INPUT_REQUIRED` contendo as alternativas oferecidas, a retenção opaca do token assinado `requestState`, e o retry da tool MCP enviando a escolha do usuário com um **ID JSON-RPC NOVO**.

---

## 2. Instruções de Execução

### 2.1 Configuração da Variável de Ambiente

O Servidor MCP exige a variável `REQUEST_STATE_SECRET` contendo no mínimo 32 bytes aleatórios (64 caracteres hexadecimais) para a assinatura HMAC-SHA256 dos tokens de estado `requestState`.

No Linux / macOS:
```bash
export REQUEST_STATE_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

No Windows (PowerShell / CMD):
```cmd
set REQUEST_STATE_SECRET=4b9f2d1e8c7a6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a
```

---

### 2.2 Execução via Docker (Recomendado)

O repositório fornece scripts de subida automática e arquivos Docker pré-configurados.

#### Opção A: No Windows (Arquivo Batch)
Execute o script em lote a partir do Prompt de Comando ou PowerShell:
```cmd
.\run_docker.bat
```

#### Opção B: No Linux / macOS (Script Shell)
Dê permissão de execução (se necessário) e rode o script:
```bash
chmod +x run_docker.sh start.sh
./run_docker.sh
```

#### Opção C: Via Docker Compose
```bash
docker compose up --build
```

O contêiner subirá os serviços mapeando as portas:
- **Porta 7300**: Agente A2A (`http://localhost:7300`)
- **Porta 7301**: Servidor MCP (`http://localhost:7301`)

---

### 2.3 Execução Nativa / Local (Sem Docker)

Se optar por rodar os processos diretamente no host:

#### Terminal 1 — Servidor MCP (Porta 7301)
```bash
export REQUEST_STATE_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
python3 servidor-mcp/main.py
# ou para Node.js: node servidor-mcp/index.js
```

#### Terminal 2 — Agente A2A / Host MCP (Porta 7300)
```bash
python3 agente/main.py
# ou para Node.js: node agente/index.js
```

---

### 2.4 Execução do Validador Automatizado

Com os dois processos em execução (nas portas `7300` e `7301`), execute a suíte oficial de testes (36 verificações de conformidade):

```bash
python3 validador/validar.py --agente http://localhost:7300 --mcp http://localhost:7301
```

---

## 3. Onde a Ponte Acontece

A costura de protocolo entre o MCP e o A2A ocorre em dois pontos-chave do código do Agente:

1. **Da Resposta `input_required` do MCP para a Pausa `TASK_STATE_INPUT_REQUIRED` do A2A**:  
   Quando a chamada inicial `tools/call` (`reservar_sala`) retorna um resultado do tipo `resultType: "input_required"`, o Host MCP no Agente intercepta o payload, extrai o array de salas alternativas do `requestedSchema.properties.sala.enum`, coloca a `Task` A2A no estado `TASK_STATE_INPUT_REQUIRED` e armazena o token opaco `requestState` associado ao `taskId`. A mensagem enviada de volta ao cliente A2A é formatada estritamente como:
   `alternativas: <id1>, <id2>`

2. **Da Continuação A2A (`escolha=<id>`) para o Retry MCP com ID JSON-RPC Novo**:  
   Ao receber a mensagem de resposta do cliente (`escolha=sala-fusca` ou `escolha=recusar`), o Agente recupera o `requestState` guardado para aquele `taskId`, constrói a estrutura `inputResponses` com a action (`accept` ou `decline`) e executa um novo `tools/call` para o Servidor MCP. Esta nova requisição gera obrigatoriamente um **ID de requisição JSON-RPC novo** (diferente da chamada inicial), repassando o `requestState` intacto e os metadados `_meta` com a propagação do `traceparent`.

---

## 4. Decisões Técnicas de Arquitetura

1. **Proteção e Integridade do `requestState`**:  
   O estado de requisição retornado pelo Servidor MCP durante o ciclo MRTR é assinado com **HMAC-SHA256** utilizando a chave secreta de 32 bytes (`REQUEST_STATE_SECRET`). O token carrega os argumentos originais e possui tempo de expiração configurado para 15 minutos. Caso o token seja adulterado ou expirado, o Servidor MCP rejeita a requisição com o código de erro JSON-RPC `-32602`.

2. **Opacidade do Estado para o Agente A2A**:  
   O Agente trata o `requestState` como uma string estritamente opaca: ele não decodifica, inspeciona, nem altera seus dados. O token nunca é exposto nas mensagens A2A nem no Agent Card.

3. **Gerenciamento de Estado de Tasks**:  
   As tarefas A2A e a associação entre `taskId` e `requestState` são gerenciadas em memória no Agente. O Servidor MCP permanece 100% stateless entre requisições; mesmo se o processo do Servidor MCP for reiniciado entre o `input_required` e o retry, a reserva é concluída com sucesso pois todo o contexto viaja assinado no `requestState`.

4. **Especificações Técnicas Detalhadas**:  
   - Especificação Técnica Completa: [SPEC-a2a-mcp-bridge.md](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/spec/SPEC-a2a-mcp-bridge.md)
   - Product Requirements Document: [PRD-agente-a2a-mcp-ponte.md](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/prd/PRD-agente-a2a-mcp-ponte.md)
   - Architectural Decision Record: [ADR-001-arquitetura-ponte-a2a-mcp.md](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/ADR-001-arquitetura-ponte-a2a-mcp.md)

---

## 5. Saída Demonstrativa do Validador

Abaixo a saída da suíte automatizada de testes `validador/validar.py`:

```text
trace-id desta execucao: 4bf92f3577b34da6a3ce929d0e0e4736
procure esse valor no stderr do servidor MCP para conferir a propagacao do traceparent.

PASS 01 tools/list traz as tres tools
PASS 02 toda tool tem inputSchema que e objeto JSON Schema valido
PASS 03 listar_salas devolve structuredContent e o mesmo JSON em texto
PASS 04 _meta sem protocolVersion devolve -32602 e HTTP 400
PASS 05 _meta sem clientCapabilities devolve -32602 e HTTP 400
PASS 06 tool inexistente e recusada, por -32602 ou por isError
PASS 07 resources/read de politica://uso devolve a politica
PASS 08 resources/read de URI inexistente devolve -32602
PASS 09 sala inexistente devolve isError com a mensagem exata
PASS 10 fora da janela devolve isError com a mensagem exata
PASS 11 duracao acima de 2h devolve isError com a mensagem exata
PASS 12 intervalo invertido devolve isError com a mensagem exata
PASS 13 conflito devolve input_required com inputRequests e requestState
PASS 14 a elicitation e form mode e oferece as alternativas na ordem certa
PASS 15 conflito sem a capability elicitation devolve -32021 e HTTP 400
PASS 16 retry com inputResponses e requestState conclui a reserva
PASS 17 requestState adulterado e rejeitado com -32602
PASS 18 argumentos adulterados no retry nao tomam efeito
PASS 19 recusa conclui sem reservar e sem isError
PASS 20 conflito sem alternativa possivel devolve isError com a mensagem exata
PASS 21 agent card responde 200 no well-known com JSON
PASS 22 o card declara a interface JSON-RPC com url e versao 1.0
PASS 23 o card declara a skill reservar-sala
PASS 24 SendMessage com sala livre conclui a Task
PASS 25 o artifact chama reserva e traz a versao da politica
PASS 26 GetTask devolve id, contextId e estado corrente
PASS 27 SendMessage com sala ocupada pausa a Task
PASS 28 a Task pausada lista as alternativas na ordem certa
PASS 29 escolha fora do enum mantem a Task pausada
PASS 30 a continuacao conclui a Task na sala escolhida
PASS 31 SendMessage em Task terminal e recusado
PASS 32 a recusa termina a Task em CANCELED
PASS 33 duas Tasks pausadas ao mesmo tempo concluem cada uma com a sua reserva
PASS 34 nenhuma resposta A2A carrega o requestState
PASS 35 sala inexistente termina a Task em FAILED com a mensagem da tool
PASS 36 o agente e deterministico: o mesmo pedido produz a mesma pausa

resumo: 36 passaram, 0 falharam, de 36 verificacoes
```

---

## 6. Estrutura do Repositório

```text
.
├── README.md                            # Documentação principal e instruções de execução
├── Dockerfile                           # Configuração da imagem Docker (Python 3.11 + Node.js 20)
├── docker-compose.yml                   # Orquestrador Docker Compose
├── run_docker.bat                       # Script de execução automatizada em lote no Windows
├── run_docker.sh                        # Script de execução automatizada em Shell no Linux/macOS
├── start.sh                             # Ponto de entrada do contêiner Docker
├── dados/                               # [READ-ONLY] Dados fixos (salas.json, reservas.json, politica-de-uso.md)
├── validador/                           # [READ-ONLY] Suíte automatizada de testes (validar.py)
├── exemplos/                            # [READ-ONLY] Payloads JSON-RPC de referência em wire/
├── docs/                                # Documentação técnica e arquitetural
│   ├── desafio.md                       # Especificação original do desafio
│   ├── ADR-001-arquitetura-ponte-a2a-mcp.md # Registro de decisões de arquitetura
│   ├── prd/                             # Product Requirements Document (PRD)
│   └── spec/                            # Especificação Técnica (SPEC em inglês)
├── servidor-mcp/                        # Código do Servidor MCP (Porta 7301)
└── agente/                              # Código do Agente A2A / Host MCP (Porta 7300)
```
