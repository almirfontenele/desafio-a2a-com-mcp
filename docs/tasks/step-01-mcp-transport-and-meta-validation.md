# Step 01: MCP Server Foundation & Transport Layer

> **Epic**: MCP Protocol Server Setup (Port `7301`, Endpoint `/mcp`)  
> **Status**: `[x] Completed`  
> **Target Validator Checks**: `PASS 01`, `PASS 04`, `PASS 05`

---

## 1. Overview & Goal

Establish the HTTP Streamable server on port `7301` listening at `/mcp`. Ensure strict handling of protocol headers, mandatory `_meta` fields, client capability checks, and `stderr` logging.

---

## 2. Technical Specification & Wire References

- **Spec Context**: Section 2.1 & Section 2.2 of [SPEC-a2a-mcp-bridge.md](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/spec/SPEC-a2a-mcp-bridge.md)
- **Wire Example**: [01-tools-list.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/01-tools-list.json), [06-erro-32021-sem-elicitation.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/06-erro-32021-sem-elicitation.json)

---

## 3. Atomic Requirements & Implementation Rules

### Rule 1.1: Transport & Port Binding
- Expose Streamable HTTP endpoint on `http://127.0.0.1:7301/mcp` (accepting `POST` requests).
- Accept headers `Content-Type: application/json` and `Accept: application/json, text/event-stream`.

### Rule 1.2: Mandatory Metadata (`_meta`) Validation
- Inspect `params._meta` for every JSON-RPC request.
- **Protocol Version**: Ensure `_meta.io.modelcontextprotocol/protocolVersion` is present and equals `"2026-07-28"`.
- **Client Capabilities**: Ensure `_meta.io.modelcontextprotocol/clientCapabilities` is present.
- **Error Response**: If `_meta` or any of these mandatory fields are missing/invalid, return JSON-RPC error code `-32602` ("Invalid params") with HTTP `400 Bad Request`.

### Rule 1.3: Protocol Header Mirroring Validation
- Validate matching HTTP headers:
  - `MCP-Protocol-Version`: `"2026-07-28"`
  - `Mcp-Method`: Must match the JSON-RPC `method` in the body (e.g., `"tools/call"`, `"tools/list"`, `"resources/read"`).
  - `Mcp-Name`: Must match tool or resource name when applicable (e.g., `"reservar_sala"`).
- If header validation fails, return JSON-RPC error code `-32020` ("Header mismatch").

### Rule 1.4: Stderr Request Logging
- For EVERY received request, log a single line to `stderr` formatted as:
  `[MCP-SERVER] <HTTP_METHOD> <JSONRPC_METHOD> id=<ID> traceparent=<TRACEPARENT>`
- Extract `traceparent` from `_meta.traceparent` if present; fallback to `none` if omitted.

---

## 4. Verification Gate

Run Step 1 checks via runner script or validator:
```bash
python3 run_steps.py --step 1
```

Expected output:
- `PASS 01`: MCP `tools/list` succeeds.
- `PASS 04`: Missing `_meta.protocolVersion` returns HTTP 400 / error `-32602`.
- `PASS 05`: Missing `_meta.clientCapabilities` returns HTTP 400 / error `-32602`.
