# GEMINI.md - Contexto do Projeto "A Ponte: Agente A2A com MCP"

> **Visão Geral:** Este arquivo fornece o contexto técnico, diretrizes de desenvolvimento, arquitetura de integração e comandos essenciais para assistentes de IA (Gemini / Antigravity) trabalhando no repositório.

---

## 1. Visão Geral do Projeto

O projeto **"A Ponte: um agente A2A com MCP por dentro"** é o desafio prático do MBA em Engenharia de Software com IA. O objetivo é integrar duas especificações de protocolo stateless:

1. **A2A (Agent-to-Agent Protocol v1.0)**: O agente atua como servidor A2A exposto na porta `7300` (binding JSON-RPC 2.0 sobre HTTP), expondo Agent Card, gerenciando Tasks e transitando por estados de workflow (`SUBMITTED`, `WORKING`, `INPUT_REQUIRED`, `COMPLETED`, `CANCELED`, `FAILED`).
2. **MCP (Model Context Protocol v2 - Revisão 2026-07-28)**: O agente atua internamente como host MCP consumindo um servidor MCP exposto na porta `7301` (Streamable HTTP `/mcp`) que provê ferramentas de domínio (`listar_salas`, `consultar_disponibilidade`, `reservar_sala`) e recursos (`politica://uso`).

### O Conceito da "Ponte"
Como o transporte HTTP é totalmente stateless e sem callbacks síncronos:
- Quando o servidor MCP identifica conflito de horário na reserva, ele responde com `resultType: "input_required"` (elicitation em *form mode*) e um `requestState` selado e assinado via HMAC.
- O agente A2A intercepta a resposta, transita a `Task` para `TASK_STATE_INPUT_REQUIRED`, devolve a lista de alternativas ao cliente A2A e armazena o `requestState` associado à `Task`.
- Ao receber a escolha do cliente (`escolha=<id>`), o agente reenvia o `tools/call` para o servidor MCP utilizando um **ID JSON-RPC NOVO**, enviando os `inputResponses` e o `requestState` intacto.

---

## 2. Estrutura do Repositório

```
.
├── GEMINI.md                            # Este arquivo de contexto para agentes de IA
├── README.md                            # Documentação principal da entrega e execução
├── dados/                               # [NÃO ALTERAR] Dados fixos do domínio
│   ├── salas.json                       # Cadastro fixo das 5 salas de reunião
│   ├── reservas.json                    # Reservas iniciais preexistentes
│   └── politica-de-uso.md               # Regras de uso (recurso politica://uso)
├── validador/                           # [NÃO ALTERAR] Suíte automatizada de validação
│   └── validar.py                       # Cliente de testes (36 verificações de conformidade)
├── exemplos/                            # [NÃO ALTERAR] Exemplos de payload JSON-RPC
│   └── wire/                            # Arquivos .json com requests e responses reais
├── docs/                                # Documentação técnica e arquitetural
│   ├── desafio.md                       # Especificação completa do desafio
│   └── ADR-001-arquitetura-ponte-a2a-mcp.md # Registro de decisão de arquitetura
├── servidor-mcp/                        # [CÓDIGO A DESENVOLVER] Servidor MCP (Porta 7301)
└── agente/                              # [CÓDIGO A DESENVOLVER] Agente A2A / Host MCP (Porta 7300)
```

> [!CAUTION]
> **Aviso Importante:** Os diretórios `dados/`, `validador/` e `exemplos/` são estritamente **read-only** e não devem ser modificados sob hipótese alguma.

---

## 3. Especificações Técnicas e Contratos

### 3.1. Servidor MCP (Porta `7301`, Endpoint `/mcp`)
- **Transporte:** Streamable HTTP.
- **Capabilities:** Deve declarar `tools` e `resources`.
- **Tools Expóstatas:**
  1. `listar_salas`: Retorna lista de salas com `structuredContent` e bloco de texto.
  2. `consultar_disponibilidade`: Recebe `sala`, `inicio`, `fim`. Retorna disponibilidade ou conflito.
  3. `reservar_sala`: Recebe `sala`, `inicio`, `fim`, `responsavel`. Processa a reserva ou dispara o ciclo MRTR (`input_required`).
- **Resource Expóstato:** `politica://uso` (conteúdo de `dados/politica-de-uso.md`, `mimeType: text/markdown`).
- **Segurança de `requestState`:** Protegido via HMAC-SHA256 usando a variável `REQUEST_STATE_SECRET` (mínimo 32 bytes hex). Deve expirar entre 5 e 30 minutos e suportar reinicialização do servidor MCP.
- **Stderr Logging:** Todo request recebido deve registrar no `stderr` no mínimo: método, ID e `traceparent` (se presente em `_meta`).

### 3.2. Agente A2A (Porta `7300`)
- **Endpoints:**
  - `GET /.well-known/agent-card.json`: Retorna Agent Card v1.0 declarando a skill `reservar-sala`.
  - `POST /a2a`: Endpoint JSON-RPC 2.0 aceitando `SendMessage` e `GetTask`.
- **Metadados Obrigatorios no Host MCP:** Todo request MCP gerado pelo agente deve incluir em `_meta`:
  - `io.modelcontextprotocol/protocolVersion`: `"2026-07-28"`
  - `io.modelcontextprotocol/clientCapabilities`: `{"elicitation": {"form": {}}}`
  - `traceparent`: Propagado do header `traceparent` do cliente A2A.

### 3.3. Tabela de Erros e Semântica

| Categoria | Condição | Código / Tipo | Mensagem Exata / Retorno |
| :--- | :--- | :--- | :--- |
| **Erro de Execução (Tool)** | Sala inexistente | `isError: true` | `Sala inexistente: <id>` |
| **Erro de Execução (Tool)** | Fora de 08:00 às 20:00 | `isError: true` | `Fora da janela de uso: a politica permite reservas entre 08:00 e 20:00` |
| **Erro de Execução (Tool)** | Duração > 2 horas | `isError: true` | `Duracao acima do limite: a politica permite no maximo 2 horas` |
| **Erro de Execução (Tool)** | Fim <= Início | `isError: true` | `Intervalo invalido: fim deve ser posterior a inicio` |
| **Erro de Execução (Tool)** | Sem salas alternativas | `isError: true` | `Sem alternativas disponiveis no intervalo` |
| **Erro de Protocolo (MCP)** | Ausência de `_meta` | `-32602` (HTTP 400) | Invalid params |
| **Erro de Protocolo (MCP)** | Capability elicitation ausente | `-32021` (HTTP 400) | `requiredCapabilities` em data |
| **Erro de Protocolo (MCP)** | `requestState` inválido/adulterado | `-32602` | Erro de verificação de assinatura |

---

## 4. Comandos e Execução

### Variáveis de Ambiente Necessárias
```bash
export REQUEST_STATE_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

### Validação da Solução
A suíte oficial do projeto avalia 36 verificações automatizadas de ponta a ponta:

```bash
python3 validador/validar.py --agente http://localhost:7300 --mcp http://localhost:7301
```

---

## 5. Diretrizes para Agentes de IA

Ao atuar neste repositório, siga estritamente as regras abaixo:

1. **Determinismo:** Não utilize LLMs nem bibliotecas de IA generativa no caminho de execução do agente ou servidor MCP. Toda a lógica deve ser baseada em regras estritas.
2. **Separação de Responsabilidades:** O agente A2A não deve conter regras de negócio de reserva de salas; ele apenas traduz protocolos entre A2A e MCP. O servidor MCP é o único responsável pelo domínio e validações.
3. **Opacidade do `requestState`:** O agente A2A trata o `requestState` como um valor opaco (nunca inspeciona, altera ou decodifica).
4. **Novo ID no Retry MRTR:** Certifique-se de que a requisição de retry enviada ao servidor MCP utilize um **ID de requisição JSON-RPC diferente** do ID inicial.
5. **Formato Exato de Pausa A2A:** Quando a Task pausar, a mensagem enviada pelo agente deve ser exatamente:
   `alternativas: <id1>, <id2>` (sem prefixos, saudações ou formatação adicional).
6. **Verificação Automatizada:** Após realizar qualquer alteração no código, execute `python3 validador/validar.py` para garantir 100% de aprovação nas 36 verificações.
