---
status: Active
maintainer: pacoxu
last_updated: 2026-03-24
tags: a2a, agent-to-agent, agent-interoperability, multi-agent, protocol
canonical_path: docs/agents/a2a.md
---

# Agent-to-Agent (A2A) Protocol

Agent-to-Agent (A2A) is an open protocol specification for enabling direct
communication and interoperability between AI agents built on different
frameworks and platforms. Where MCP standardizes how an agent connects to
*tools and data sources*, A2A standardizes how *agents communicate with each
other* — discovering capabilities, delegating tasks, and exchanging results.

**Status**: Trial — CNCF Tech Radar 2025

## Table of Contents

- [Overview](#overview)
- [A2A vs. MCP](#a2a-vs-mcp)
- [The A2A Project](#the-a2a-project)
- [Core Concepts](#core-concepts)
- [AgentGateway and A2A](#agentgateway-and-a2a)
- [Learning Topics](#learning-topics)
- [RoadMap](#roadmap)
- [References](#references)

---

## Overview

As multi-agent systems grow more complex — with specialized agents for
research, coding, data analysis, and orchestration — a common interoperability
layer becomes essential. A2A addresses this by defining:

- **How agents advertise their capabilities** (Agent Cards / capability
  manifests)
- **How agents invoke each other** (task delegation, structured messaging)
- **How agents exchange context and results** (standardized message formats)
- **How trust is established** between agents (authentication and
  authorization)

A2A is complementary to MCP: a typical agentic system might use MCP to connect
to tools (databases, APIs, Kubernetes) and A2A to coordinate between
specialized sub-agents.

**Key use cases:**

- Orchestrator agent delegates research to a specialized research agent
- Code generation agent hands off security scanning to a security agent
- Human-in-the-loop workflows where one agent pauses for approval from
  another
- Cross-organization agent collaboration (agents in different enterprises
  interoperating via A2A)

---

## A2A vs. MCP

| Dimension | MCP | A2A |
| --- | --- | --- |
| **Primary purpose** | Agent ↔ Tool/Data Source | Agent ↔ Agent |
| **Participants** | LLM client + Tool server | Agent + Agent (peers) |
| **Interaction model** | Request/response (tools), stream (resources) | Task delegation, async messaging |
| **Discovery** | Manual configuration | Agent Card (capability manifest) |
| **Auth** | OAuth 2.1 / API keys (evolving, issue #1442) | Per-spec, OIDC/mTLS |
| **Status (CNCF TR 2025)** | Adopt | Trial |
| **Best for** | Tool integration, data access | Multi-agent coordination |

**Complementary usage**: In practice, many agentic systems use *both* protocols
simultaneously — A2A for agent orchestration and MCP for tool access within
each agent.

---

## The A2A Project

<a href="https://github.com/a2aproject/A2A">`a2aproject/A2A`</a>

The A2A project is the reference specification and implementation repository
for the Agent-to-Agent protocol, originally developed by Google and open-sourced
for broad industry collaboration.

**What the repository contains:**

- **Protocol specification**: Formal definition of message formats, transport
  requirements, and capability negotiation
- **Agent Card schema**: JSON Schema for agents to declare their capabilities,
  endpoints, and authentication requirements
- **Reference implementations**: SDKs in Python and TypeScript for building
  A2A-compliant agents
- **Sample agents**: Working examples of orchestrator and sub-agents using the
  protocol
- **Conformance tests**: Test suites for validating A2A compliance

**Key Protocol Elements:**

1. **Agent Card** (`/.well-known/agent.json`): A standardized JSON document
   that an agent publishes to advertise its capabilities, skills, input/output
   schemas, and authentication requirements — similar to OpenAPI for agents.

2. **Task**: The fundamental unit of A2A interaction. An orchestrator creates
   a task, sends it to a sub-agent, and the sub-agent returns a result.
   Tasks support streaming for long-running operations.

3. **Message**: Structured payload exchanged within a task. Messages can
   contain text, structured data (JSON), files, or references to external
   resources.

4. **Push Notifications**: Agents can register a webhook to receive async
   task updates, enabling fire-and-forget patterns for long-running tasks.

5. **Authentication**: A2A uses industry-standard mechanisms (OIDC, API keys,
   mTLS) declared in the Agent Card so clients know how to authenticate before
   sending any task.

**Industry Adoption:**

The A2A protocol has attracted broad support across the AI ecosystem:

- Google (originator), backing multi-framework support
- LangChain, CrewAI, AutoGen — major agent frameworks adding A2A support
- Enterprise platforms building A2A bridges for internal agent fleets
- CNCF Tech Radar 2025 inclusion in "Trial" position

**Getting Started:**

```bash
# Install the Python SDK
pip install a2a-sdk

# Run the sample orchestrator
git clone https://github.com/a2aproject/A2A
cd A2A/samples/python
python orchestrator.py
```

---

## Core Concepts

### Agent Card

The Agent Card is the cornerstone of A2A discoverability. An A2A-compliant
agent serves a JSON document at `/.well-known/agent.json` (by convention)
that describes:

```json
{
  "name": "Code Review Agent",
  "description": "Reviews code for security issues and style violations",
  "url": "https://code-review-agent.example.com",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  },
  "skills": [
    {
      "id": "review_code",
      "name": "Review Code",
      "description": "Analyzes code for security and quality issues",
      "inputModes": ["text"],
      "outputModes": ["text", "data"]
    }
  ],
  "authentication": {
    "schemes": ["Bearer"]
  }
}
```

### Task Lifecycle

```text
Orchestrator                    Sub-Agent
    │                               │
    │── tasks/send ────────────────▶│  (create task with message)
    │                               │  [working...]
    │◀─ streaming updates ──────────│  (optional: stream partial results)
    │                               │  [completed]
    │── tasks/get ─────────────────▶│  (poll for result)
    │◀─ task result ────────────────│
```

Task states: `submitted` → `working` → `input-required` (optional, for
human-in-the-loop) → `completed` / `failed` / `canceled`

### Multi-Agent Topology

A2A supports flexible topologies:

- **Hierarchical**: One orchestrator delegates to multiple specialized
  sub-agents (most common)
- **Peer-to-peer**: Agents at the same level collaborate on shared goals
- **Pipeline**: Agent A's output becomes Agent B's input in a chain
- **Fan-out/Fan-in**: Orchestrator fans out tasks to parallel agents, then
  aggregates results

---

## AgentGateway and A2A

<a href="https://github.com/agentgateway/agentgateway">`agentgateway/agentgateway`</a>

AgentGateway provides infrastructure-level support for both MCP and A2A in a
single proxy layer, making it a natural integration point for production
agentic systems.

**A2A capabilities in AgentGateway:**

- **Agent discovery proxy**: Fetches and caches Agent Cards from registered
  sub-agents; orchestrators query AgentGateway for capability discovery
  instead of reaching every agent directly.
- **Task routing**: Routes A2A tasks to the correct sub-agent based on
  capability matching, load balancing, or explicit routing rules.
- **Auth delegation**: Manages credentials for downstream agents; orchestrators
  authenticate to AgentGateway once, and AgentGateway handles per-agent auth.
- **Observability**: Traces A2A task flows end-to-end with OpenTelemetry, so
  you can see the full task delegation chain across multiple agents.
- **MCP + A2A bridge**: An agent can receive requests via MCP tools and
  forward them as A2A tasks to specialized agents — AgentGateway handles
  the protocol translation.

For more on AgentGateway's MCP capabilities, see the
[MCP documentation](./mcp.md#agentgateway).

---

## Learning Topics

### Protocol Fundamentals

1. **A2A Specification**:
   - Agent Card schema and publishing (`/.well-known/agent.json`)
   - Task creation, streaming, and completion lifecycle
   - Message types (text, data, files, references)
   - Push notification patterns for async tasks

2. **Building A2A Agents**:
   - Implementing an A2A server (sub-agent)
   - Implementing an A2A client (orchestrator)
   - Using the Python and TypeScript SDKs
   - Capability declaration and negotiation

3. **Security and Trust**:
   - Authentication schemes in Agent Cards (Bearer, mTLS, OIDC)
   - Authorization for task delegation
   - Preventing prompt injection via A2A messages
   - Audit trails for inter-agent communication

### Multi-Agent System Design

1. **Orchestration Patterns**:
   - When to use hierarchical vs. peer-to-peer topologies
   - Task decomposition strategies for complex goals
   - Handling partial failures in multi-agent pipelines
   - Human-in-the-loop integration via `input-required` state

2. **Interoperability**:
   - Bridging agents built on different frameworks
     (LangChain, AutoGen, KAgent, custom)
   - Using AgentGateway as a cross-framework hub
   - Versioning and backward compatibility in Agent Cards

3. **MCP + A2A Together**:
   - Typical architecture: A2A for agent coordination, MCP for tool access
   - Protocol boundary decisions: when does a "tool" become an "agent"?
   - Avoiding double-proxying (agent calling agent via MCP vs. A2A directly)

### Kubernetes Deployment

1. **Deploying A2A Agents on Kubernetes**:
   - Each agent as a Kubernetes `Deployment` + `Service`
   - Agent Card serving via `Ingress` or `Gateway API`
   - Service mesh (Istio/Linkerd) for mTLS between agents
   - Health checks for A2A endpoints

2. **AgentGateway on Kubernetes**:
   - Central A2A proxy as a `Deployment` behind an `Ingress`
   - ConfigMap-based agent registry
   - Integration with Kubernetes NetworkPolicy for agent isolation

---

## RoadMap

- [ ] A2A conformance test suite completion
- [ ] CNCF project application for A2A
- [ ] KAgent A2A integration (agents discoverable via A2A from KAgent CRDs)
- [ ] AgentGateway A2A routing policies (capability-based routing)
- [ ] A2A + MCP unified authorization model alignment
- [ ] Multi-cluster A2A federation for cross-cluster agent collaboration

---

## References

- [A2A Protocol Repository](https://github.com/a2aproject/A2A)
- [A2A Specification (latest)](https://github.com/a2aproject/A2A/blob/main/spec.md)
- [AgentGateway](https://github.com/agentgateway/agentgateway)
- [MCP Protocol Guide](./mcp.md)
- [CNCF Tech Radar 2025](https://radar.cncf.io/)
- [AI Agent Platforms Guide](./README.md)
- [Kube-Agentic-Networking](https://github.com/kubernetes-sigs/kube-agentic-networking)
