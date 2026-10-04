---
name: prd-authoring
description: >-
  Use this skill when drafting, reviewing, or refining Product Requirements Documents (PRDs)
  for software features, products, system capabilities, or user workflows.
---

# Product Requirements Document (PRD) Authoring

A Product Requirements Document (PRD) defines the *what*, *why*, and *for whom* of a feature or product before technical design begins. It acts as the single source of truth for scope, requirements, user stories, and acceptance criteria.

---

## When to Use

Activate this skill when:
- Defining a new system feature, agent capability, or protocol integration.
- Aligning product goals, success metrics, and user personas.
- Establishing functional requirements, edge cases, and out-of-scope boundaries.

---

## PRD Standard Structure & Template

Save PRD documents in `docs/prd/PRD-feature-name.md`.

```markdown
# PRD: [Feature / System Name]

- **Status**: Draft | Under Review | Approved | Deprecated
- **Target Release / Milestone**: [Version / Date]
- **Owner**: [Product Owner / Lead Engineer]
- **Document Version**: 1.0.0

---

## 1. Executive Summary & Business Goals

Provide a high-level overview of the feature. What problem does it solve, and why are we building it now?

## 2. Problem Statement & User Personas

### 2.1 Problem Statement
Describe the pain point, current limitations, or friction in the existing system.

### 2.2 Target Users / Personas
- **Persona 1**: [e.g., Enterprise Assistant Agent]
- **Persona 2**: [e.g., End-user booking a room]

## 3. Scope & Out of Scope

### In Scope
- Feature A
- Protocol binding B
- Error handling flow C

### Out of Scope
- OAuth2 authentication (deferred to Phase 2)
- Push notifications / Streaming (SSE)

## 4. User Stories & Core Workflows

### User Story 1: [Short Title]
> **As a** [user/agent],  
> **I want to** [action],  
> **So that** [benefit].

#### Workflow / Sequence:
1. User sends request.
2. System checks availability.
3. System confirms booking or returns input requirement.

## 5. Functional Requirements

| ID | Requirement | Priority (Must/Should/Could) | Acceptance Criteria |
|---|---|---|---|
| FR-01 | Must respond to `tools/list` with JSON schema | Must | Valid schema returned with HTTP 200 |
| FR-02 | Must pause task when input is required | Must | State transitions to `INPUT_REQUIRED` |

## 6. Non-Functional Requirements

- **Performance**: Response time < 200ms for availability queries.
- **Security**: HMAC signature verification on opaque state tokens.
- **Reliability & Determinism**: Zero non-deterministic behavior; identical inputs yield identical outputs.

## 7. Success Metrics & KPIs

- 100% compliance on protocol validator suite.
- Zero uncaught exceptions during invalid payload scenarios.

## 8. Dependencies & Risks

- **Dependencies**: External SDK versions, runtime environment requirements.
- **Risks & Mitigations**:
  - *Risk*: State token tampering.
  - *Mitigation*: HMAC SHA-256 signing with secret key.
```

---

## Best Practices

1. **Focus on Outcomes, Not Implementation**: Specify what the product should accomplish, leaving internal class design to technical specs (SPEC) and ADRs.
2. **Clear Acceptance Criteria**: Every requirement must be testable and verifiable.
3. **Explicit Scope Boundaries**: Clearly define what will NOT be built to avoid scope creep.
