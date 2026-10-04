# Step 05: A2A-MCP Bridge & Task Lifecycle Management

> **Epic**: MRTR Intercept Bridge & Task State Machine Execution  
> **Status**: `[x] Completed`  
> **Target Validator Checks**: `PASS 24` through `PASS 36`

---

## 1. Overview & Goal

Implement the core bridge logic ("A Ponte") in the A2A Agent. Orchestrate state transitions (`SUBMITTED`, `WORKING`, `INPUT_REQUIRED`, `COMPLETED`, `CANCELED`, `FAILED`), intercept MCP `input_required` elicitation, bind opaque HMAC `requestState` tokens, and retry MCP calls with **new JSON-RPC request IDs**.

---

## 2. Technical Specification & Wire References

- **Spec Context**: Section 1, Section 3, Section 4, & Section 6 of [SPEC-a2a-mcp-bridge.md](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/spec/SPEC-a2a-mcp-bridge.md)
- **Wire Examples**:
  - [08-a2a-send-message.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/08-a2a-send-message.json)
  - [09-a2a-get-task-input-required.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/09-a2a-get-task-input-required.json)
  - [10-a2a-send-message-continuacao.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/10-a2a-send-message-continuacao.json)

---

## 3. Atomic Requirements & Implementation Rules

### Rule 5.1: Task Creation & Direct Booking Flow
- When `SendMessage` is received without a `taskId`:
  1. Instantiate a new `Task` record in state `TASK_STATE_SUBMITTED`, then immediately move to `TASK_STATE_WORKING`.
  2. Parse booking text arguments (`sala`, `inicio`, `fim`, `responsavel`).
  3. Extract W3C `traceparent` header from incoming A2A HTTP request and propagate it inside `params._meta.traceparent` to the MCP host call.
  4. Issue MCP `tools/call` for `reservar_sala` with mandatory `_meta` (`protocolVersion: "2026-07-28"` and `clientCapabilities: { elicitation: { form: {} } }`).
  5. If MCP returns direct completion:
     - Create task artifact `name: "reserva"` with text content containing reservation details and policy version (`politica: "2026-11-01"`).
     - Transition Task to `TASK_STATE_COMPLETED`.

### Rule 5.2: MCP Elicitation Intercept & Task Pausing
- When MCP returns `resultType: "input_required"`:
  1. Transition Task state to `TASK_STATE_INPUT_REQUIRED`.
  2. Format pause message text EXACTLY as: `alternativas: <id1>, <id2>` (sorted enum IDs separated by comma-space, with no extra prefixes, greetings, or punctuation).
  3. Store `requestState` string in-memory associated with `taskId`. Treat `requestState` as completely opaque (never decode, parse, or leak in A2A responses).

### Rule 5.3: Task Resumption & MCP Retry
- When `SendMessage` is received referencing an existing `taskId` in `TASK_STATE_INPUT_REQUIRED`:
  1. Parse message text for `escolha=<value>`.
  2. **Invalid Choice Handling**: If `<value>` is not in the stored alternative enum list, keep Task in `TASK_STATE_INPUT_REQUIRED` and re-emit exact alternatives string (`alternativas: <id1>, <id2>`).
  3. **Valid Room Choice**:
     - Transition Task state to `TASK_STATE_WORKING`.
     - Dispatch MCP `tools/call` retry with a **NEW JSON-RPC request ID** (different from the initial call ID).
     - Include `inputResponses` with `action: "accept"`, `content: { sala: "<value>" }`, and unchanged opaque `requestState`.
     - On MCP success, produce `reserva` artifact and transition Task state to `TASK_STATE_COMPLETED`.

### Rule 5.4: Decline Flow & Task Cancellation
- If continuation message specifies `escolha=recusar`:
  1. Dispatch MCP `tools/call` retry with **NEW JSON-RPC ID**, `inputResponses` containing `action: "decline"`, and unchanged `requestState`.
  2. Transition Task state to `TASK_STATE_CANCELED`.

### Rule 5.5: Task Inspection & Terminal Enforcement
- `GetTask` handler returns Task ID, `contextId`, status state, message, and artifacts.
- Sending `SendMessage` targeting a Task in a terminal state (`COMPLETED`, `CANCELED`, `FAILED`) MUST be rejected with a JSON-RPC error.

### Rule 5.6: Tool Execution Error Mapping
- If MCP returns `isError: true` (e.g. invalid room ID, inverted window), transition Task state to `TASK_STATE_FAILED` with the exact error message from the tool.

### Rule 5.7: Task Isolation & Token Opacity
- Multiple concurrent paused tasks MUST maintain isolated state mappings without cross-contaminating `requestState`.
- `requestState` MUST NEVER be exposed in any A2A message, card, or task payload.

---

## 4. Verification Gate

Run Step 5 checks via runner script:
```bash
python3 run_steps.py --step 5
```

Expected output:
- `PASS 24` through `PASS 36` all pass clean.
