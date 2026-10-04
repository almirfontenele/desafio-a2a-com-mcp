---
name: implementation-planner
description: >-
  Use this skill when designing step-by-step Implementation Plans (IMPLEMENTAÇÃO),
  execution strategies, refactoring sequences, or phase-by-phase development roadmaps.
---

# Implementation Plan (IMPLEMENTAÇÃO) Strategy & Planning

An Implementation Plan translates technical specifications (SPECs) and architectural decisions (ADRs) into an ordered, phased execution strategy. It breaks complex software builds into safe, incrementally testable steps.

---

## When to Use

Activate this skill when:
- Planning the build out of a new service, module, or protocol layer.
- Structuring multi-phase refactoring or protocol integration.
- Defining dependencies, prerequisites, and milestone verification gates.

---

## Implementation Plan Structure & Template

Save Implementation Plans in `docs/implementation/PLAN-feature-name.md`.

```markdown
# Implementation Plan: [Feature / System Name]

- **Status**: Draft | In Progress | Completed
- **Based on SPEC**: [Link to SPEC]
- **Target Branch**: `main`

---

## 1. Overview & Strategy

Summarize the implementation strategy. How will the software be built incrementally without breaking existing functionality?

## 2. Prerequisites & Environment Setup

- [ ] Environment variables configured (`REQUEST_STATE_SECRET`, `PORT`).
- [ ] Dependencies installed and version-locked in `pyproject.toml` / `package.json`.
- [ ] Static domain data verified (`dados/salas.json`, `dados/reservas.json`).

## 3. Phase Breakdown & Step-by-Step Execution

### Phase 1: Core Foundation & Static Endpoints
- **Goal**: Implement server initialization, logging, and basic schema definitions.
- **Tasks**:
  1. [ ] Setup MCP Streamable HTTP server on port 7301.
  2. [ ] Implement `stderr` logger capturing method, id, and `traceparent`.
  3. [ ] Expose `politica://uso` resource with contents from `dados/politica-de-uso.md`.
- **Verification Gate**:
  Run unit test or curl command:
  ```bash
  curl http://localhost:7301/mcp
  ```

### Phase 2: Domain Tools & Business Rules
- **Goal**: Implement `listar_salas`, `consultar_disponibilidade`, and happy-path `reservar_sala`.
- **Tasks**:
  1. [ ] Load domain JSON files safely into memory.
  2. [ ] Implement validation rules (time windows 08:00-20:00, max 2h, inverted dates).
  3. [ ] Return exact business error strings on constraint violations.
- **Verification Gate**:
  Run initial validator checks for MCP tools.

### Phase 3: State & MRTR (Elicitation Cycle)
- **Goal**: Support `input_required` response on conflict and secure `requestState` handling.
- **Tasks**:
  1. [ ] Implement alternative room algorithm (capacity filter, sorting).
  2. [ ] Build HMAC-SHA256 signer/verifier for `requestState`.
  3. [ ] Implement capability negotiation check (`io.modelcontextprotocol/clientCapabilities`).
- **Verification Gate**:
  Verify tampering detection and process restart resistance.

### Phase 4: A2A Agent & Bridge Protocol Integration
- **Goal**: Implement A2A agent card, JSON-RPC endpoint `/a2a`, and task state machine.
- **Tasks**:
  1. [ ] Implement `GET /.well-known/agent-card.json`.
  2. [ ] Implement `SendMessage` and `GetTask` handlers.
  3. [ ] Wire MCP client call and bridge `input_required` to `TASK_STATE_INPUT_REQUIRED`.
- **Verification Gate**:
  Run full 36-step compliance validator.

## 4. Rollback & Contingency Plan

- What to do if a phase fails verification?
- Key isolation points to avoid partial corruption.
```

---

## Best Practices

1. **Incremental Verification Gates**: Every phase MUST have a concrete, executable verification command before proceeding to the next phase.
2. **Strict Phase Boundaries**: Keep phases independent and cohesive.
3. **No Blind Jumps**: Ensure prerequisites are explicit before starting code edits.
