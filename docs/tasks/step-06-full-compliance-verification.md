# Step 06: Full Compliance & End-to-End Verification

> **Epic**: Automated Compliance Suite & Non-Regression Verification  
> **Status**: `[x] Completed`  
> **Target Validator Checks**: All 36 Checks (`PASS 01` through `PASS 36`)

---

## 1. Overview & Goal

Execute the full automated test suite to ensure 100% compliance across all 36 protocol and business checks. Validate process restart resilience, tracing propagation, and zero non-determinism.

---

## 2. Technical Specification & Validation Suite

- **Validator**: [validador/validar.py](file:///home/almir/projetos/desafio-a2a-com-mcp/validador/validar.py)
- **Specification Document**: [SPEC-a2a-mcp-bridge.md](file:///home/almir/projetos/desafio-a2a-com-mcp/docs/spec/SPEC-a2a-mcp-bridge.md)
- **Context & Rules**: [GEMINI.md](file:///home/almir/projetos/desafio-a2a-com-mcp/GEMINI.md)

---

## 3. Execution Procedure & Final Checkpoints

### 3.1: Environment Variable Check
Ensure `REQUEST_STATE_SECRET` is set in the environment:
```bash
export REQUEST_STATE_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

### 3.2: Launch Services
Start MCP Server (Port `7301`) and A2A Agent (Port `7300`).

### 3.3: Run Complete Validation Suite
```bash
python3 validador/validar.py --agente http://localhost:7300 --mcp http://localhost:7301
```

### 3.4: Compliance Criteria Checklist
- [ ] **100% Test Pass**: All 36 checks pass without error (`PASS 01` to `PASS 36`).
- [ ] **Deterministic Logic**: Zero LLMs or generative AI libraries used in code execution paths.
- [ ] **Stderr Logging**: Stderr log output visible for every incoming MCP request.
- [ ] **State Opacity**: `requestState` is never exposed or decoded outside MCP Host.
- [ ] **Process Restart Resilience**: HMAC verification permits MCP server restarts during task pauses.

---

## 4. Verification Gate

Run full suite via runner script:
```bash
python3 run_steps.py --step 6
```
