# Step 07: Unit Testing & Component Isolation Suite

> **Epic**: Component Unit Tests & Automated Test Coverage  
> **Status**: `[x] Completed`  
> **Target Framework**: Python Standard `unittest` / `pytest`

---

## 1. Overview & Goal

Establish an isolated unit testing suite in the `tests/` directory to verify core component logic (business rule constraints, HMAC state token cryptography, A2A Task state machine transitions, message parsers) without requiring running HTTP network servers.

---

## 2. Technical Specification & Test Coverage

- **Specification Context**: [SPEC-a2a-mcp-bridge.md](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/spec/SPEC-a2a-mcp-bridge.md)
- **Rules Context**: [GEMINI.md](file:///home/almir/projetos/desafio-a2a-com-mcp/GEMINI.md)

---

## 3. Atomic Requirements & Test Modules

### Rule 7.1: MCP Server Core Unit Tests (`tests/test_mcp_server.py`)
- **Metadata & Header Validation**:
  - Test missing `_meta` returns error `-32602`.
  - Test missing `protocolVersion` or `clientCapabilities` returns error `-32602`.
  - Test header mismatch (`MCP-Protocol-Version`, `Mcp-Method`) returns error `-32020`.
- **Business Rule Constraints**:
  - Test invalid room ID returns error message `Sala inexistente: <id>`.
  - Test booking outside 08:00–20:00 returns operating hours error.
  - Test duration > 2 hours returns max duration error.
  - Test inverted time interval (`fim <= inicio`) returns invalid window error.
- **HMAC Cryptography & State Sealed Tokens**:
  - Test `requestState` HMAC token creation with `REQUEST_STATE_SECRET`.
  - Test HMAC token validation with valid secret.
  - Test tampered token payload signature rejection.
  - Test token expiration rejection (> 30 min or < 5 min).
- **MRTR Elicitation & Elicitation Schema**:
  - Test occupied room generates sorted alternative room enum.
  - Test missing form capability returns error `-32021`.

### Rule 7.2: A2A Agent Core Unit Tests (`tests/test_a2a_agent.py`)
- **Agent Card v1.0 Schema**:
  - Test Agent Card fields (`name`, `version`, `supportedInterfaces`, `skills`).
- **Task State Machine**:
  - Test transition from `SUBMITTED` -> `WORKING`.
  - Test pause transition to `TASK_STATE_INPUT_REQUIRED` with exact format `alternativas: <id1>, <id2>`.
  - Test resumption with valid room choice (`escolha=<id>`) -> `TASK_STATE_WORKING` -> `TASK_STATE_COMPLETED`.
  - Test cancellation with decline choice (`escolha=recusar`) -> `TASK_STATE_CANCELED`.
  - Test terminal state error enforcement when sending message to finished task.
- **Message Parsing & Traceparent**:
  - Test parsing text arguments (`sala`, `inicio`, `fim`, `responsavel`).
  - Test extraction and forwarding of W3C `traceparent` context header.

---

## 4. Verification Gate

Run unit tests via `unittest` runner:
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Or run via runner script:
```bash
python3 run_steps.py --step 7
```
