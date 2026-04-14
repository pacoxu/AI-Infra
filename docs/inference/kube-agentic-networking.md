---
status: Active
maintainer: pacoxu
last_updated: 2026-04-14
tags: inference, kubernetes, agentic, networking, governance
canonical_path: docs/inference/kube-agentic-networking.md
---

# kube-agentic-networking: Agentic Networking Governance on Kubernetes

[`kube-agentic-networking`](https://github.com/kubernetes-sigs/kube-agentic-networking)
is a Kubernetes SIG project focused on networking policies and governance for
agent workloads. In practice, it targets a common problem in agent platforms:
agents must call many tools and APIs, but platform teams still need clear
boundaries, least-privilege controls, and auditability.

## Why It Matters

Agent systems are different from traditional microservices:

- **Dynamic egress patterns**: tool calls are often decided at runtime rather
  than fixed at deploy time.
- **Cross-domain access**: one workflow may touch model endpoints, MCP tools,
  external APIs, and internal services.
- **Governance requirements**: enterprise environments require policy controls,
  traceability, and tenant isolation for agent actions.

`kube-agentic-networking` addresses these needs by bringing agent-aware
networking governance into Kubernetes-native workflows.

## Role in the AI Infra Stack

Within this repository's AI infra model, `kube-agentic-networking` sits between:

- **Agent runtimes/orchestrators** (Dify, AgentScope, LangGraph-style systems)
- **Gateway and routing layers** (AI gateway, inference routing)
- **Tool backends and external APIs** (MCP servers, internal platforms, SaaS)

It complements API gateways and agent protocols (for example MCP/A2A) by
focusing on network policy boundaries and governance posture.

## Typical Use Cases

- **Multi-tenant agent platform**: enforce namespace/team boundaries so one
  team's agent cannot reach another team's internal tools by default.
- **Controlled tool access**: allow only approved tool/API targets for specific
  agent classes.
- **Compliance and audit**: record and review network intent and access
  patterns for high-risk workflows.

## Adoption Guidance

For production rollout, a pragmatic sequence is:

1. Start with non-production agent workflows and define an explicit tool/API
   access inventory.
2. Apply least-privilege network policies for agent workloads first.
3. Add policy validation and observability before broad rollout.
4. Expand to multi-tenant and regulated workloads once policy drift and false
   positives are controlled.

## Learning Topics

- Policy design for agent-to-tool traffic
- Multi-tenant boundary modeling in Kubernetes
- Governance integration with AI gateway and protocol layers
- Operational observability for agent network access

## References

- [GitHub: kubernetes-sigs/kube-agentic-networking](https://github.com/kubernetes-sigs/kube-agentic-networking)
- [Kubernetes SIGs](https://github.com/kubernetes-sigs)
