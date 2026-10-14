# Relatório de Alterações Técnicas — Correções e Hardening (BUG-001)

> **Projeto**: A Ponte: Agente A2A com MCP por Dentro  
> **Data**: 2026-10-14  
> **Status**: Aprovado e Verificado em Produção Local  
> **Autor**: Equipe de Engenharia / Almir Fontenele  
> **Documento de Origem**: [`docs/bugs/bug_001.md`](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/bugs/bug_001.md)  
> **Suíte de Conformidade**: 36/36 Verificações Aprovadas (`validador/validar.py`)  

---

## 1. Visão Geral e Contexto

Este documento consolida as alterações de código e documentação realizadas no projeto em resposta à análise do defeito documentado em [`docs/bugs/bug_001.md`](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/bugs/bug_001.md).

O objetivo das alterações foi eliminar fragilidades na fronteira entre o **Agente A2A** (porta `7300`) e o **Servidor MCP** (porta `7301`), garantindo robustez na identificação de salas alternativas no ciclo MRTR (*Model-Resolved Tool Retry*), suporte defensivo a formatos de elicitation e tratamento resiliente de erros em conformidade com o protocolo JSON-RPC 2.0.

---

## 2. Sumário das Alterações por Arquivo

| Arquivo | Componente | Tipo de Alteração | Descrição Resumida |
| :--- | :--- | :--- | :--- |
| [`servidor-mcp/mcp_repository.py`](file:///home/almir/projetos/desafio-a2a-com-mcp/servidor-mcp/mcp_repository.py) | Servidor MCP | Bugfix / Qualidade | Substituição de checagem implícita `if not requested_room:` por `if requested_room is None:`. |
| [`agente/agent_bridge.py`](file:///home/almir/projetos/desafio-a2a-com-mcp/agente/agent_bridge.py) | Host MCP / A2A | Hardening / Protocolo | Suporte a `const` além de `enum` na extração de salas alternativas no schema de elicitation. |
| [`agente/server.py`](file:///home/almir/projetos/desafio-a2a-com-mcp/agente/server.py) | Servidor A2A | Resiliência / JSON-RPC | Envelopamento do despacho em `try...except` para retornar erro JSON-RPC `-32603` padrão. |
| [`docs/bugs/bug_001.md`](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/bugs/bug_001.md) | Documentação | Defect Report | Preenchimento completo do relatório de análise de defeito, RCA, plano de mitigação e evidências. |

---

## 3. Detalhamento Técnico das Modificações

### 3.1. Servidor MCP: Checagem Canônica de Nulidade em `mcp_repository.py`

- **Arquivo**: [`servidor-mcp/mcp_repository.py`](file:///home/almir/projetos/desafio-a2a-com-mcp/servidor-mcp/mcp_repository.py#L99-L105)
- **Método**: `RoomRepository.find_alternative_rooms`
- **Motivação**: Em Python (PEP 8), a comparação com `None` para entidades singleton/instâncias de dataclass deve ser explícita (`is None`). A verificação anterior (`if not requested_room:`) dependia de avaliação booleana implícita, propensa a ambiguidades caso métodos especiais (`__len__` ou `__bool__`) fossem implementados no modelo de domínio `Sala`.
- **Diff Aplicado**:
  ```diff
  --- a/servidor-mcp/mcp_repository.py
  +++ b/servidor-mcp/mcp_repository.py
  @@ -99,7 +99,7 @@ class RoomRepository:
   
       def find_alternative_rooms(self, requested_sala_id: str, inicio: str, fim: str) -> list[str]:
           requested_room = self.get_sala(requested_sala_id)
  -        if not requested_room:
  +        if requested_room is None:
               return []
           req_cap = requested_room.capacidade
  ```

---

### 3.2. Host MCP (Agente): Suporte a Schemas `const` e `enum` em `agent_bridge.py`

- **Arquivo**: [`agente/agent_bridge.py`](file:///home/almir/projetos/desafio-a2a-com-mcp/agente/agent_bridge.py#L75-L81)
- **Método**: `ReservationBridgeService._handle_new_booking`
- **Motivação**: Ao interceptar respostas `resultType: "input_required"`, o Host MCP extrai a lista de salas sugeridas no schema da solicitação de elicitation. Caso apenas uma sala esteja disponível, servidores de protocolo JSON Schema podem fornecer a propriedade `const` em vez de um array `enum`. A alteração previne que a lista de alternativas fique vazia nesse cenário.
- **Diff Aplicado**:
  ```diff
  --- a/agente/agent_bridge.py
  +++ b/agente/agent_bridge.py
  @@ -75,7 +75,7 @@ class ReservationBridgeService:
               schema = req_params.get("requestedSchema", {})
               properties = schema.get("properties", {})
               sala_prop = properties.get("sala", {})
  -            alternativas = sala_prop.get("enum", [])
  +            alternativas = sala_prop.get("enum") or ([sala_prop["const"]] if "const" in sala_prop else [])
   
               task.state = TaskState.INPUT_REQUIRED
               task.request_state = res.get("requestState")
  ```

---

### 3.3. Servidor A2A: Captura Global de Falhas de Despacho em `server.py`

- **Arquivo**: [`agente/server.py`](file:///home/almir/projetos/desafio-a2a-com-mcp/agente/server.py#L74-L86)
- **Método**: `A2ARequestHandler.do_POST`
- **Motivação**: A especificação JSON-RPC 2.0 exige que requisições válidas sintaticamente que sofram exceções internas retornem status HTTP 200 com payload estruturado de erro `{"code": -32603, "message": "Internal error"}`. Anteriormente, uma exceção no despacho causava falha não tratada no `BaseHTTPRequestHandler`, retornando erro genérico HTTP 500 sem envelope JSON-RPC.
- **Diff Aplicado**:
  ```diff
  --- a/agente/server.py
  +++ b/agente/server.py
  @@ -74,7 +74,16 @@ class A2ARequestHandler(BaseHTTPRequestHandler):
           method = body.get("method", "")
           params = body.get("params", {}) or {}
   
  -        result, error = self.container.dispatcher.dispatch(method, params, traceparent)
  +        try:
  +            result, error = self.container.dispatcher.dispatch(method, params, traceparent)
  +        except Exception as e:
  +            self.send_json_response(200, {
  +                "jsonrpc": "2.0",
  +                "id": req_id,
  +                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
  +            })
  +            return
  +
           if error:
               self.send_json_response(200, {
                   "jsonrpc": "2.0",
  ```

---

### 3.4. Documentação: Relatório de Análise de Defeito em `docs/bugs/bug_001.md`

- **Arquivo**: [`docs/bugs/bug_001.md`](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/bugs/bug_001.md)
- **Motivação**: Completar a documentação do defeito, eliminando placeholders e registrando de forma profissional a causa raiz, os passos de reprodução, as evidências de logs do servidor e do validador, e os critérios de validação de não-regressão.
- **Alterações Realizadas**:
  - Atualização do status do bug report de `Draft` para `Verified`;
  - Preenchimento do Sumário Executivo com o impacto e a camada afetada;
  - Marcação precisa dos subsistemas e protocolos afetados nas seções de A2A e MCP;
  - Documentação detalhada da Análise de Causa Raiz (RCA);
  - Apresentação do histórico de revisões (versão 1.1.0).

---

## 4. Verificação e Validação de Não-Regressão

### 4.1. Testes Unitários

Execução da suíte de testes unitários do repositório:
```bash
python3 -m unittest discover tests
```
**Resultado**:
```text
.........
----------------------------------------------------------------------
Ran 9 tests in 0.002s

OK
```

### 4.2. Suíte Oficial de Conformidade (`validador/validar.py`)

Execução das 36 verificações de ponta a ponta integrando Agente A2A (`http://localhost:7300`) e Servidor MCP (`http://localhost:7301`):
```bash
python3 validador/validar.py --agente http://localhost:7300 --mcp http://localhost:7301
```

**Resultado Consolidado**:
```text
PASS 01 tools/list traz as tres tools
PASS 02 toda tool tem inputSchema de objeto
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

## 5. Invariantes de Arquitetura Mantidos

- [x] **Determinismo Estrito**: Sem dependência de LLMs ou bibliotecas probabilísticas;
- [x] **Opacidade do `requestState`**: O Agente A2A preserva a integridade do token sem inspeção ou decodificação;
- [x] **Novo ID JSON-RPC em Retries**: Cada nova tentativa no ciclo MRTR gera um ID independente via `secrets.token_hex(6)`;
- [x] **Mensagem Exata de Pausa**: Mantido estritamente o formato `alternativas: <id1>, <id2>`;
- [x] **Propagação de Contexto W3C**: Propagação contínua do cabeçalho `traceparent` do cliente A2A até os metadados do MCP.
