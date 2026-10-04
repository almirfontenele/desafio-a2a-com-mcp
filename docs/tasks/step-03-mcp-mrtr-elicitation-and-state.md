# Step 03: MCP MRTR Elicitation & State Protection

> **Epic**: Reservation Processing & HMAC State Sealed Elicitation  
> **Status**: `[x] Completed`  
> **Target Validator Checks**: `PASS 13`, `PASS 14`, `PASS 15`, `PASS 16`, `PASS 17`, `PASS 18`, `PASS 19`, `PASS 20`

---

## 1. Overview & Goal

Implement the `reservar_sala` tool with full support for direct bookings, MRTR (Model Request Task State Retry) conflict elicitation, HMAC-SHA256 state token generation/validation, and client response handling (`accept` vs `decline`).

---

## 2. Technical Specification & Wire References

- **Spec Context**: Section 2.3, Section 2.5, & Section 5 of [SPEC-a2a-mcp-bridge.md](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/spec/SPEC-a2a-mcp-bridge.md)
- **Wire Examples**:
  - [02-tools-call-livre.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/02-tools-call-livre.json)
  - [03-tools-call-conflito-input-required.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/03-tools-call-conflito-input-required.json)
  - [04-tools-call-retry.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/04-tools-call-retry.json)
  - [06-erro-32021-sem-elicitation.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/06-erro-32021-sem-elicitation.json)
  - [11-tools-call-retry-recusa.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/11-tools-call-retry-recusa.json)

---

## 3. Atomic Requirements & Implementation Rules

### Rule 3.1: Elicitation Capability Pre-check
- Before handling conflict elicitation, inspect `_meta.io.modelcontextprotocol/clientCapabilities.elicitation.form`.
- If form mode capability is missing or falsy, immediately halt and return JSON-RPC error `-32021` ("Capability required") with HTTP `400 Bad Request`.

### Rule 3.2: Schedule Conflict & Alternative Room Discovery
- Check requested room availability for `[inicio, fim]`.
- If occupied, search all other rooms in `dados/salas.json` that are free for `[inicio, fim]`.
- **Zero Alternatives**: If no other room is free, return `isError: true` with exact message `Sem alternativas disponiveis no intervalo`.
- **Alternatives Found**: Sort matching alternative room IDs alphabetically (e.g. `["sala-fusca", "sala-mirante"]`).

### Rule 3.3: HMAC-SHA256 `requestState` Token Generation
- Read secret from environment variable `REQUEST_STATE_SECRET`.
- Construct state payload containing: original arguments (`sala`, `inicio`, `fim`, `responsavel`), creation timestamp, nonce.
- Sign payload using HMAC-SHA256. Token expiration MUST be between 5 and 30 minutes.

### Rule 3.4: `input_required` Payload Elicitation Response
- Return HTTP 200 JSON-RPC result with `resultType: "input_required"`.
- Provide `inputRequests` dict containing `elicitation/create` with `mode: "form"`, message string, and `requestedSchema` containing alternative room IDs in `enum`.
- Include sealed `requestState` token string.

### Rule 3.5: MRTR Retry Validation (`inputResponses` Present)
- When a retry call arrives with `inputResponses` and `requestState`:
  1. Verify HMAC-SHA256 signature using `REQUEST_STATE_SECRET`. If signature invalid or token expired, return error `-32602`.
  2. Enforce sealed parameters from `requestState` (ignore any client argument tampering).
  3. Evaluate `inputResponses`:
     - **Accept Action** (`action: "accept"`): Extract chosen room ID from `content.sala`. Reserve chosen room, record reservation, and return `resultType: "complete"` with reservation artifact schema.
     - **Decline Action** (`action: "decline"`): Complete execution without creating any reservation (`reservado: false`). Return `resultType: "complete"` with `isError` false/omitted.

---

## 4. Verification Gate

Run Step 3 checks via runner script:
```bash
python3 run_steps.py --step 3
```

Expected output:
- `PASS 13`: Occupied room returns `resultType: "input_required"`.
- `PASS 14`: Alternatives enum lists sorted room IDs.
- `PASS 15`: Missing form capability returns error `-32021` (HTTP 400).
- `PASS 16`: MRTR retry with chosen room completes reservation.
- `PASS 17`: Tampered state token is rejected with error `-32602`.
- `PASS 18`: Argument tampering on retry is overridden by sealed state.
- `PASS 19`: Retry with decline action completes with `reservado: false`.
- `PASS 20`: Conflict with no alternatives returns `isError: true` and exact message.
