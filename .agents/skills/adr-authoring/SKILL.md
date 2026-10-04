---
name: adr-authoring
description: >-
  Use this skill when creating, reviewing, or updating Architecture Decision Records (ADR / ARD)
  for software architecture, technology choices, protocols, state management, or system design trade-offs.
---

# Architecture Decision Record (ADR / ARD) Authoring

Architecture Decision Records (ADRs/ARDs) document critical architectural choices, their rationale, context, and consequences. They serve as a historical record for the engineering team.

---

## When to Use

Activate this skill when:
- Deciding on system boundaries, protocol choices (e.g., A2A vs MCP, REST vs gRPC).
- Choosing state management strategies (stateless retry vs session storage, HMAC signature vs JWT).
- Standardizing software patterns or library choices.
- Documenting trade-offs or architectural compromises.

---

## ADR Document Lifecycle States

- **Proposed**: Under review, open for discussion.
- **Accepted**: Agreed upon and ready for implementation.
- **Rejected**: Decision evaluated and declined.
- **Deprecated**: Previously accepted decision no longer recommended.
- **Superseded**: Replaced by a newer ADR (must link to the replacing ADR).

---

## ADR Standard Structure & Template

Save ADR documents in `docs/adr/YYYY-MM-DD-short-title.md` or `docs/adr/ADR-00X-title.md`.

```markdown
# ADR-000: [Short Title of Architectural Decision]

- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Date**: YYYY-MM-DD
- **Authors**: [Author Names / Team]
- **Deciders**: [Decision Makers]
- **Technical Story**: [Issue / Task / Requirement reference]

## 1. Context and Problem Statement

Describe the technical or business problem, environmental constraints, architectural goals, and why a decision is necessary.

## 2. Decision Drivers

- Driver 1 (e.g., protocol requirement, performance, statelessness)
- Driver 2 (e.g., security, HMAC state verification)
- Driver 3 (e.g., developer velocity, determinism)

## 3. Considered Options

### Option 1: [Name of Option 1]
- **Description**: Short description.
- **Pros**: Benefits.
- **Cons**: Trade-offs / Drawbacks.

### Option 2: [Name of Option 2]
- **Description**: Short description.
- **Pros**: Benefits.
- **Cons**: Trade-offs / Drawbacks.

## 4. Decision Outcome

**Chosen Option**: Option X because [rationale].

### Positive Consequences
- Benefit 1
- Benefit 2

### Negative Consequences / Trade-offs
- Risk 1 (and mitigation)
- Risk 2

## 5. Pros and Cons of the Options

Summarize comparative evaluation if necessary.

## 6. Validation & Compliance

How will this decision be verified during CI/CD, testing, or code reviews?
```

---

## Best Practices

1. **Be Explicit About Trade-offs**: Never present a decision as cost-free. Detail what is sacrificed (e.g., memory vs CPU, simplicity vs flexibility).
2. **Immutable History**: Once accepted, do not rewrite past ADRs to reflect changes; create a new ADR that supersedes the old one.
3. **Keep Context Neutral**: Focus on facts, technical trade-offs, and protocol requirements rather than personal preferences.
