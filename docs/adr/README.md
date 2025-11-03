# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records (ADRs) for the Ticket System project.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## ADR Format

Each ADR follows this structure:

- **Title**: Short noun phrase
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Context**: What is the issue we're addressing?
- **Decision**: What is the change we're making?
- **Consequences**: What becomes easier or harder with this decision?

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [001](./001-dual-mode-architecture.md) | Dual-Mode Architecture (Monolith + Microservices) | Accepted | 2025-11-02 |
| [002](./002-kubernetes-autoscaling.md) | Kubernetes HPA for Automatic Scaling | Accepted | 2025-11-02 |
| [003](./003-local-registry-deployment.md) | Local Registry for Development | Accepted | 2025-11-02 |
| [004](./004-http-connection-pooling.md) | HTTP Connection Pooling | Accepted | 2025-11-02 |
| [005](./005-asyncio-lock-for-stock.md) | Asyncio Lock for Stock Management | Accepted | 2025-11-02 |

## Creating a New ADR

1. Copy the template: `cp template.md 00X-title.md`
2. Fill in the sections
3. Update this index
4. Submit for review

---

Last updated: 2025-11-02
