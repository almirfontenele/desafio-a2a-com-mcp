# Step 02: MCP Domain Tools & Resource Exposure

> **Epic**: Domain Tools & Policy Resource Implementation  
> **Status**: `[x] Completed`  
> **Target Validator Checks**: `PASS 02`, `PASS 03`, `PASS 06`, `PASS 07`, `PASS 08`, `PASS 09`, `PASS 10`, `PASS 11`, `PASS 12`

---

## 1. Overview & Goal

Implement the MCP tools `listar_salas` and `consultar_disponibilidade`, along with the resource `politica://uso`. Enforce exact business validation rules and error message strings.

---

## 2. Technical Specification & Wire References

- **Spec Context**: Section 2.3 & Section 2.4 of [SPEC-a2a-mcp-bridge.md](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/spec/SPEC-a2a-mcp-bridge.md)
- **Wire Examples**:
  - [01-tools-list.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/01-tools-list.json)
  - [05-resources-read-politica.json](file:///home/almir/projetos/desafio-a2a-com-mcp/exemplos/wire/05-resources-read-politica.json)
- **Domain Files**:
  - [dados/salas.json](file:///home/almir/projetos/desafio-a2a-com-mcp/dados/salas.json)
  - [dados/reservas.json](file:///home/almir/projetos/desafio-a2a-com-mcp/dados/reservas.json)
  - [dados/politica-de-uso.md](file:///home/almir/projetos/desafio-a2a-com-mcp/dados/politica-de-uso.md)

---

## 3. Atomic Requirements & Implementation Rules

### Rule 2.1: Tool Discovery (`tools/list`)
- Expose all 3 domain tools: `listar_salas`, `consultar_disponibilidade`, `reservar_sala`.
- Each tool definition MUST include a valid `inputSchema` detailing expected properties and required arguments.

### Rule 2.2: `listar_salas` Tool
- Load rooms from `dados/salas.json`.
- Return `structuredContent` matching array schema: `[{ id, nome, capacidade, recursos }]`.
- Return a `content` text block containing identical formatted JSON text representation.

### Rule 2.3: `consultar_disponibilidade` Tool & Business Rules
- Receive `arguments: { sala, inicio, fim }`.
- Evaluate business constraints in exact sequence:
  1. **Room Existence**: If `sala` is not in `dados/salas.json`, return `isError: true` with message `Sala inexistente: <id>`.
  2. **Operating Hours**: Start and End times must fall between `08:00` and `20:00` (-03:00 timezone). If violated, return `isError: true` with message `Fora da janela de uso: a politica permite reservas entre 08:00 e 20:00`.
  3. **Maximum Duration**: Duration (`fim - inicio`) must not exceed `2 hours` (7200 seconds). If violated, return `isError: true` with message `Duracao acima do limite: a politica permite no maximo 2 horas`.
  4. **Window Validity**: `fim` must be strictly greater than `inicio`. If `fim <= inicio`, return `isError: true` with message `Intervalo invalido: fim deve ser posterior a inicio`.
- **Availability Check**: If all constraints pass, check overlap against `dados/reservas.json` for that room.
  - Return `structuredContent: { disponivel: true/false, sala, inicio, fim }`.

### Rule 2.4: `politica://uso` Resource (`resources/read`)
- Endpoint handles `method: "resources/read"` with `params: { uri: "politica://uso" }`.
- Load static markdown from `dados/politica-de-uso.md`.
- Return `contents: [{ uri: "politica://uso", mimeType: "text/markdown", text: "<md_content>" }]`.
- **Unknown URIs**: If `params.uri` is not `politica://uso`, MUST return JSON-RPC error code `-32602` ("Resource not found"). Returning empty `contents: []` is prohibited.

### Rule 2.5: Unknown Tool Handling
- Any `tools/call` for an unrecognized tool name MUST return JSON-RPC error `-32602` or `isError: true`.

---

## 4. Verification Gate

Run Step 2 checks via runner script:
```bash
python3 run_steps.py --step 2
```

Expected output:
- `PASS 02`: Tool input schemas are valid.
- `PASS 03`: `listar_salas` returns structured and text content.
- `PASS 06`: Unknown tool call handled gracefully.
- `PASS 07`: `politica://uso` returns markdown text.
- `PASS 08`: Unknown URI returns error `-32602`.
- `PASS 09`: Invalid room ID returns exact `Sala inexistente: <id>` message.
- `PASS 10`: Out-of-hours booking returns exact window error message.
- `PASS 11`: Duration > 2 hours returns exact max duration message.
- `PASS 12`: Inverted interval returns exact invalid interval message.
