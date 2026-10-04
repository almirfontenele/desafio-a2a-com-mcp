# Step 04: A2A Agent Card & Server Endpoints

> **Epic**: A2A Server Infrastructure Setup (Port `7300`)  
> **Status**: `[x] Completed`  
> **Target Validator Checks**: `PASS 21`, `PASS 22`, `PASS 23`

---

## 1. Overview & Goal

Set up the A2A server on port `7300`. Expose the discovery Agent Card at `GET /.well-known/agent-card.json` and initialize the JSON-RPC 2.0 HTTP endpoint at `POST /a2a`.

---

## 2. Technical Specification & Wire References

- **Spec Context**: Section 2.1 & Section 2.5 of [SPEC-a2a-mcp-bridge.md](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/spec/SPEC-a2a-mcp-bridge.md)
- **Wire Example**: [07-a2a-agent-card.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/07-a2a-agent-card.json)

---

## 3. Atomic Requirements & Implementation Rules

### Rule 4.1: Agent Card Publishing (`GET /.well-known/agent-card.json`)
- Serve HTTP `200 OK` with `Content-Type: application/json`.
- Response body MUST contain:
  - `name`: `"Central de Salas"`
  - `description`: `"Reserva salas de reuniao da Hill Valley Tech."`
  - `version`: `"1.0.0"`
  - `supportedInterfaces`: Array containing interface with `url: "http://127.0.0.1:7300/a2a"`, `protocolBinding: "JSONRPC"`, `protocolVersion: "1.0"`.
  - `skills`: Array containing skill object with `id: "reservar-sala"`.

### Rule 4.2: A2A Endpoint Dispatcher (`POST /a2a`)
- HTTP `POST` handler at path `/a2a` expecting JSON-RPC 2.0 request payloads.
- Accept methods `SendMessage` and `GetTask`. Return appropriate JSON-RPC 2.0 response objects.

---

## 4. Verification Gate

Run Step 4 checks via runner script:
```bash
python3 run_steps.py --step 4
```

Expected output:
- `PASS 21`: Agent Card endpoint returns HTTP 200 and valid JSON.
- `PASS 22`: Agent Card declares JSON-RPC protocol interface details.
- `PASS 23`: Agent Card declares skill `id: "reservar-sala"`.
