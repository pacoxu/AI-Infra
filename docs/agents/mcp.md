---
status: Active
maintainer: pacoxu
last_updated: 2026-03-24
tags: mcp, model-context-protocol, agent-tools, agent-gateway, kubernetes
canonical_path: docs/agents/mcp.md
---

# Model Context Protocol (MCP)

Model Context Protocol (MCP) is an open standard for connecting AI agents and
LLMs to external tools, data sources, and services. It defines a
**host/client/server** architecture that separates the agent runtime (host +
client) from the tool providers (servers), enabling a rich ecosystem of
reusable, composable integrations.

**Status**: Adopted — CNCF Tech Radar 2025

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Projects](#key-projects)
  - [ToolHive](#toolhive)
  - [KMCP](#kmcp)
  - [AgentGateway](#agentgateway)
  - [MCP for Beginners](#mcp-for-beginners)
- [MCP Authorization (Spec Issue #1442)](#mcp-authorization-spec-issue-1442)
- [Learning Topics](#learning-topics)
- [RoadMap](#roadmap)
- [References](#references)

---

## Overview

MCP was introduced by Anthropic and quickly gained broad industry adoption
(OpenAI, Google DeepMind, Microsoft, and many others). The protocol solves a
key integration problem: every AI agent previously required custom, one-off
connectors for each tool or data source. MCP defines a universal "plug" that
any compliant server exposes and any compliant client can consume.

**Core capabilities:**

- **Tools**: Functions the LLM can invoke (e.g., web search, code execution,
  database queries)
- **Resources**: Data the LLM can read (e.g., files, database records, API
  responses)
- **Prompts**: Reusable prompt templates managed server-side
- **Sampling**: Allow servers to request LLM completions through the client

**Transport options:**

- `stdio` — local subprocess (simple, no network)
- `Streamable HTTP` (formerly SSE) — remote servers over HTTP with
  server-sent events

## Architecture

```text
┌─────────────────────────────────────┐
│            MCP Host                 │  (e.g., Claude Desktop, custom app)
│  ┌────────────┐  ┌────────────┐     │
│  │ MCP Client │  │ MCP Client │ ... │
│  └─────┬──────┘  └─────┬──────┘     │
└────────│───────────────│────────────┘
         │ MCP Protocol  │
    ┌────▼───┐      ┌────▼──────────┐
    │ MCP    │      │  MCP Server   │   MCP Server ...
    │ Server │      │  (remote/HTTP)│
    └────────┘      └───────────────┘
```

- **Host**: The application that owns the user interaction (e.g., an IDE
  plugin, a chat UI).
- **Client**: Embedded in the host; maintains a 1:1 connection to one MCP
  server.
- **Server**: Exposes tools/resources/prompts for a specific domain (GitHub,
  databases, Kubernetes, etc.).

## Key Projects

### ToolHive

<a href="https://github.com/stacklok/toolhive">`stacklok/toolhive`</a>

ToolHive is a lightweight, security-focused tool for running and managing MCP
servers as containerized workloads. It acts as an MCP proxy/manager — you
describe which MCP servers you need, and ToolHive fetches, isolates, and
exposes them through a unified local endpoint.

**Key Features:**

- **Containerized MCP servers**: Each MCP server runs in its own isolated
  container (OCI image), preventing one malicious tool from affecting others
  or the host system.
- **Registry and discovery**: Built-in registry of well-known MCP server
  images; `thv install <name>` pulls and wires up a server automatically.
- **Transparent proxy**: Exposes all managed servers through a single SSE
  endpoint, so the agent host sees one consolidated MCP interface.
- **Kubernetes-native deployment**: `thv deploy` can target a local container
  runtime or a Kubernetes cluster via the `--target k8s` flag.
- **Secret injection**: Secrets (API keys, tokens) are injected at runtime via
  environment variables; they never touch the registry or image layers.

**Maintained by**: Stacklok

**Use Cases:**

- Local developer workflows: run GitHub, Slack, and Postgres MCP servers
  side-by-side with one command
- Enterprise deployments: centralized, auditable MCP server fleet on
  Kubernetes
- Security-conscious teams: each tool server is sandboxed in its own container

### KMCP

<a href="https://github.com/kagent-dev/kmcp">`kagent-dev/kmcp`</a>

KMCP (Kubernetes MCP) is a Kubernetes-native implementation of the Model
Context Protocol developed by the KAgent team. It exposes Kubernetes cluster
capabilities (namespaces, pods, deployments, logs, events, custom resources)
as MCP tools and resources, allowing AI agents to interact with Kubernetes
clusters using standard MCP clients.

**Key Features:**

- **Kubernetes as an MCP server**: Any MCP-compatible agent or host can
  interact with Kubernetes workloads without custom connectors.
- **Fine-grained RBAC**: Uses Kubernetes ServiceAccount and RBAC to scope
  which resources an agent can read or mutate.
- **CRD-aware**: Automatically discovers installed CustomResourceDefinitions
  and exposes them as addressable resources.
- **Audit logging**: Every tool call is logged as a Kubernetes event for
  traceability.
- **Integration with KAgent**: Works out-of-the-box with
  [KAgent](https://github.com/kagent-dev/kagent) for declarative agent
  deployments.

**Maintained by**: KAgent community (CNCF Sandbox)

**Use Cases:**

- AI-driven cluster operations (e.g., "find all pods in CrashLoopBackOff and
  show their logs")
- GitOps agents that read Kubernetes state and propose pull requests
- Autonomous incident response agents

### AgentGateway

<a href="https://github.com/agentgateway/agentgateway">`agentgateway/agentgateway`</a>

AgentGateway is a proxy and routing layer designed specifically for agentic
workloads. It sits between agent clients and multiple MCP servers (or A2A
agents), providing traffic management, security, and observability at the
agent-communication layer.

**Status**: Trial — CNCF Tech Radar 2025

**Key Features:**

- **MCP proxy**: Aggregates and proxies multiple upstream MCP servers behind a
  single endpoint; agents configure one gateway instead of N individual
  servers.
- **A2A support**: In addition to MCP, AgentGateway supports the
  [Agent-to-Agent (A2A)](./a2a.md) protocol for agent-to-agent calls.
- **Policy enforcement**: Rate limiting, authentication (API keys, mTLS), and
  authorization rules applied at the gateway layer.
- **Observability**: Native OpenTelemetry tracing for every tool call and
  agent interaction, compatible with standard CNCF observability stacks
  (Jaeger, Prometheus).
- **Multi-protocol**: Supports both MCP `stdio` and `Streamable HTTP`
  transports.

**Maintained by**: AgentGateway community

**Architecture:**

```text
AI Agent (MCP Client)
        │
        ▼
 ┌─────────────┐          ┌──────────────────┐
 │ AgentGateway│──────────▶  MCP Server A    │
 │  (proxy)    │          │  MCP Server B    │
 │             │──────────▶  A2A Agent C     │
 └─────────────┘          └──────────────────┘
```

**Use Cases:**

- Central ingress for all MCP servers in an enterprise environment
- Unified policy enforcement across heterogeneous tool providers
- Bridging MCP and A2A ecosystems from a single control point

### MCP for Beginners

<a href="https://github.com/microsoft/mcp-for-beginners">`microsoft/mcp-for-beginners`</a>

An official Microsoft learning resource that provides a structured,
hands-on curriculum for understanding and implementing MCP. It covers the
protocol specification, building MCP servers in multiple languages, and
integrating them with popular agent hosts.

**Curriculum Highlights:**

- Introduction to MCP concepts (host, client, server, tools, resources,
  prompts)
- Building your first MCP server in Python, TypeScript, and C#
- Connecting MCP servers to Claude Desktop and VS Code (GitHub Copilot)
- Advanced patterns: multi-server aggregation, authentication, streaming
- Deployment considerations for production MCP servers

**Maintained by**: Microsoft

**Why it matters**: This is the most comprehensive beginner-friendly resource
for learning MCP from the ground up, maintained by one of the major adopters
of the protocol.

---

## MCP Authorization (Spec Issue #1442)

<a href="https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1442">
modelcontextprotocol/issues/1442</a>

This GitHub issue tracks the official MCP authorization specification —
defining how MCP clients authenticate to MCP servers and how servers enforce
access control. This is one of the most actively discussed areas of the MCP
specification.

**Key Discussion Points:**

- **OAuth 2.1 / PKCE flow**: The spec proposes OAuth 2.1 with PKCE as the
  primary auth mechanism for remote MCP servers, allowing servers to issue
  scoped access tokens to clients.
- **Per-server credentials**: Each MCP server can independently require
  authentication; the host is responsible for managing credentials per
  server connection.
- **Scope mapping to tools**: Authorization scopes can be mapped to specific
  tools or resource types, enabling fine-grained access control.
- **Local vs. remote distinction**: `stdio` servers (local processes) may
  inherit OS-level trust; only remote servers require explicit auth flows.
- **Enterprise SSO integration**: Discussion around integrating with SAML/OIDC
  identity providers for enterprise deployments.

**Status**: Active specification work; implementations in ToolHive and
AgentGateway are tracking this issue to align with the final spec.

**Why this matters for platform engineers:**

Understanding the authorization model is critical before deploying MCP servers
in production. Without proper auth, any agent with network access to an MCP
server can invoke all its tools, potentially leading to privilege escalation or
data leakage.

---

## Learning Topics

### Core Protocol

1. **MCP Specification**:
   - Host/Client/Server roles and responsibilities
   - Tool, Resource, and Prompt primitives
   - Transport selection: `stdio` vs. `Streamable HTTP`
   - Lifecycle management (initialization, capability negotiation, shutdown)

2. **Building MCP Servers**:
   - Implementing tools with input schemas (JSON Schema)
   - Implementing resources with URI templates
   - Handling streaming responses
   - Language SDKs: Python (`mcp`), TypeScript (`@modelcontextprotocol/sdk`),
     Go, Rust, C#

3. **Security**:
   - Container isolation for MCP servers (ToolHive pattern)
   - OAuth 2.1 authorization (spec issue #1442)
   - Secret injection without image layer exposure
   - Audit logging and traceability

### Kubernetes Integration

1. **Deploying MCP Servers on Kubernetes**:
   - Packaging MCP servers as OCI images
   - Using ToolHive `--target k8s` for automated deployment
   - Service exposure (ClusterIP for internal agents, Ingress for external)
   - Horizontal scaling considerations (stateless vs. stateful servers)

2. **KMCP for Cluster Operations**:
   - Configuring RBAC for agent service accounts
   - Exposing specific resource types as MCP resources
   - Integrating with KAgent for declarative agent definitions

3. **AgentGateway for Production**:
   - Setting up a centralized MCP proxy
   - Configuring authentication and rate limiting
   - Connecting OpenTelemetry for distributed tracing

---

## RoadMap

- [ ] MCP authorization spec finalization (tracking issue #1442)
- [ ] ToolHive Kubernetes operator for declarative MCP server management
- [ ] KMCP multi-cluster support
- [ ] AgentGateway CNCF project application
- [ ] MCP registry standardization (discoverability of MCP servers)

---

## References

- [MCP Official Site](https://modelcontextprotocol.io/)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Authorization Issue #1442](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1442)
- [ToolHive](https://github.com/stacklok/toolhive)
- [KMCP](https://github.com/kagent-dev/kmcp)
- [AgentGateway](https://github.com/agentgateway/agentgateway)
- [MCP for Beginners (Microsoft)](https://github.com/microsoft/mcp-for-beginners)
- [CNCF Tech Radar 2025](https://radar.cncf.io/)
- [AI Agent Platforms Guide](./README.md)
- [A2A Protocol Guide](./a2a.md)
