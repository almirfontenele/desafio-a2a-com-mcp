---
name: task-breakdown
description: >-
  Use this skill when decomposing specifications, PRDs, or implementation plans into atomic,
  actionable development tasks (TASKS), checklists, and trackable work items.
---

# Task Breakdown & Checklist (TASKS) Authoring

Task Breakdown turns high-level feature specifications or implementation plans into granular, bite-sized engineering tasks with concrete acceptance criteria and status tracking.

---

## When to Use

Activate this skill when:
- Converting SPECs or Implementation Plans into actionable developer checklists.
- Creating a progress log or task matrix for a project milestone.
- Tracking completion of technical requirements and test pass gates.

---

## Standard Task Checklist Structure & Template

Save Task Checklists in `docs/tasks/TASKS-milestone-name.md` or directly in project progress logs.

```markdown
# Task Checklist: [Milestone / Feature Name]

> **Overall Progress**: `[██████░░░░] 60%` (6 / 10 Tasks Completed)

---

## Epic 1: MCP Server Implementation

- [x] **TSK-01**: MCP Streamable HTTP Transport
  - **Description**: Configure HTTP server listening on port 7301 with `/mcp` endpoint.
  - **Acceptance Criteria**: Responds to valid Streamable HTTP headers; returns HTTP 400 on missing meta.
  - **Verification**: `python3 validador/validar.py` (Checks 1-4)

- [x] **TSK-02**: Stderr Request Logging
  - **Description**: Log method, JSON-RPC id, and `traceparent` header to `stderr`.
  - **Acceptance Criteria**: Log output visible in console for every incoming request.
  - **Verification**: Manual review of stderr stream.

- [ ] **TSK-03**: `politica://uso` Resource Handler
  - **Description**: Expose `dados/politica-de-uso.md` content via `resources/read`.
  - **Acceptance Criteria**: Returns Markdown content with mimeType `text/markdown`; returns `-32602` for non-existent URIs.
  - **Verification**: `python3 validador/validar.py` (Check 6)

---

## Epic 2: MRTR & State Protection

- [ ] **TSK-04**: HMAC-SHA256 `requestState` Signing
  - **Description**: Cryptographically sign state payload using secret from `REQUEST_STATE_SECRET`.
  - **Acceptance Criteria**: Tampered tokens rejected with error code `-32602`.
  - **Verification**: Validator test case 11 (tampered token check).

- [ ] **TSK-05**: Elicitation Capability Negotiation
  - **Description**: Inspect `_meta.io.modelcontextprotocol/clientCapabilities.elicitation.form`.
  - **Acceptance Criteria**: Return error `-32021` with HTTP 400 if client lacks form mode capability.
  - **Verification**: Validator test case 13.

---

## Epic 3: A2A Agent & Bridge Protocol

- [ ] **TSK-06**: Agent Card Publishing
  - **Description**: Serve A2A Agent Card v1.0 on `GET /.well-known/agent-card.json`.
  - **Acceptance Criteria**: Valid JSON matching `exemplos/wire/07-a2a-agent-card.json`.
  - **Verification**: `curl http://localhost:7300/.well-known/agent-card.json`

- [ ] **TSK-07**: Bridge Input Required State Pausing
  - **Description**: Map MCP `input_required` to A2A `TASK_STATE_INPUT_REQUIRED`.
  - **Acceptance Criteria**: Message text equals `alternativas: <ids>`; `requestState` saved internally per Task.
  - **Verification**: `python3 validador/validar.py` (Bridge checks)
```

---

## Best Practices

1. **Atomic Tasks**: Every task should address a single responsibility and be completion-verifiable in isolation.
2. **Explicit Verification Command**: Associate each task with a test script, curl command, or validator check.
3. **No Hidden Assumptions**: Explicitly list dependent task IDs (`Depends on TSK-01`).
