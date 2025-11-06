---
status: Active
maintainer: pacoxu
last_updated: 2025-11-06
tags: agentic-systems, ai-agents, kubernetes, mcp, safety
canonical_path: docs/agentic/README.md
---

# Agentic Systems on Kubernetes 🤖

This guide covers the emerging landscape of AI agent systems, frameworks, and
infrastructure for building, deploying, and operating autonomous AI agents on
Kubernetes.

## Overview

Agentic systems represent the next evolution of AI applications, where AI
models can autonomously plan, execute tasks, and interact with external tools
and services. This section focuses on the infrastructure, frameworks, and
patterns for deploying agent-based AI systems at scale.

## CNCF & Kubernetes Initiatives

### CNCF Agentic System Initiative

The Cloud Native Computing Foundation (CNCF) has launched an initiative to
standardize and promote best practices for agentic AI systems in cloud-native
environments.

- <a href="https://github.com/cncf/toc/issues/1746">`CNCF TOC - Agentic
  System Initiative`</a>: Discussion and proposals for standardizing agent
  architectures, protocols, and deployment patterns
- **Key Focus Areas:**
  - Agent orchestration and lifecycle management
  - Inter-agent communication protocols
  - Security and sandboxing for autonomous agents
  - Multi-tenant agent platforms
  - Agent observability and monitoring

### Kubernetes WG AI Integration

The Kubernetes AI Integration Working Group focuses on making Kubernetes the
best platform for AI workloads, including agentic systems.

- <a href="https://github.com/kubernetes/community/blob/master/wg-ai-integration/charter.md">`WG
  AI Integration Charter`</a>
- **Scope:**
  - Integration patterns for AI models and agents
  - Resource management for agent workloads
  - API standards for AI/agent deployment
  - Best practices for running agents on Kubernetes

## Agent Frameworks & Platforms

### Cloud-Native Agent Frameworks

#### 1. KAgent - CNCF Sandbox Project

<a href="https://github.com/kagent-dev/kagent">`KAgent`</a> is a
Kubernetes-native agent framework designed for building and deploying AI
agents at scale.

- **Status:** CNCF Sandbox
- **Key Features:**
  - Native Kubernetes deployment model
  - Agent lifecycle management
  - Built-in observability
  - Multi-agent orchestration
- **Use Cases:**
  - Autonomous task execution
  - Multi-step workflows
  - Tool-calling agents

#### 2. Dapr Agents

<a href="https://github.com/dapr/dapr-agents">`Dapr Agents`</a> extends the
Distributed Application Runtime (Dapr) to support agentic workflows.

- **Key Features:**
  - Leverages Dapr's service mesh capabilities
  - State management for agent memory
  - Pub/sub for agent communication
  - Secrets management for API keys
- **Use Cases:**
  - Multi-service agent orchestration
  - Event-driven agent workflows
  - Cross-platform agent deployment

#### 3. Agent Sandbox

<a href="https://github.com/kubernetes-sigs/agent-sandbox">`Kubernetes SIG
Agent Sandbox`</a> provides secure execution environments for AI agents.

- **Status:** Kubernetes SIG project
- **Key Features:**
  - Security sandboxing for agents
  - Resource isolation
  - Policy enforcement
  - Runtime containment
- **Use Cases:**
  - Untrusted agent execution
  - Multi-tenant agent platforms
  - Production-grade agent security

#### 4. AgentScope

<a href="https://github.com/agentscope-ai/agentscope">`AgentScope`</a> is a
multi-agent platform for building complex agent applications.

- **Key Features:**
  - Multi-agent collaboration
  - Built-in message passing
  - Agent registry and discovery
  - Flexible agent architecture
- **Use Cases:**
  - Complex multi-agent systems
  - Agent swarms and teams
  - Hierarchical agent structures

### Application-Level Agent Platforms

#### Dify

<a href="https://github.com/langgenius/dify">`Dify`</a> is a comprehensive
LLM application development platform with strong agent capabilities.

- **Key Features:**
  - Visual agent workflow builder
  - Built-in RAG capabilities
  - Agent templates and marketplace
  - API management
- **Use Cases:**
  - Rapid agent prototyping
  - Business-focused agent applications
  - Multi-step agent workflows

#### Dagger

<a href="https://github.com/dagger/dagger">`Dagger`</a> is a programmable CI/CD
engine that can orchestrate agent-based workflows.

- **Key Features:**
  - Container-native execution
  - Language SDKs (Go, Python, TypeScript)
  - Pipeline orchestration
  - Caching and optimization
- **Use Cases:**
  - DevOps automation with agents
  - CI/CD agent workflows
  - Infrastructure-as-code agents

## Model Context Protocol (MCP)

### MCP Overview

Model Context Protocol (MCP) is an emerging standard for agent-to-agent (A2A)
and agent-to-component (ACP) communication.

- **Purpose:** Standardize how agents communicate, share context, and
  coordinate actions
- **Key Concepts:**
  - Context sharing between agents
  - Tool discovery and invocation
  - State synchronization
  - Memory management

### MCP Implementations

- **MCP Servers:** Expose tools and resources to agents
- **MCP Clients:** Agents that consume MCP-compatible services
- **Transport Protocols:** HTTP, WebSocket, gRPC support
- **Schema:** JSON-based message format for interoperability

## AI Gateway for Agents

AI Gateways provide intelligent routing, load balancing, and orchestration for
agent requests to LLM backends.

### Gateway Projects

#### 1. Gateway API Inference Extension

<a href="https://github.com/kubernetes-sigs/gateway-api-inference-extension">`Gateway
API Inference Extension`</a> extends Kubernetes Gateway API for AI workloads.

- **Key Features:**
  - Model routing based on request patterns
  - Request/response transformation
  - Multi-model load balancing
  - Cost-based routing

#### 2. Envoy AI Gateway

<a href="https://github.com/envoyproxy/ai-gateway">`Envoy AI Gateway`</a>
brings Envoy's proxy capabilities to AI/agent workloads.

- **Key Features:**
  - Protocol transformation (OpenAI API → custom)
  - Rate limiting and quotas
  - Circuit breaking
  - Observability hooks

#### 3. Istio for Agent Mesh

<a href="https://github.com/istio/istio">`Istio`</a> provides service mesh
capabilities for agent-to-agent communication.

- **Use Cases:**
  - Secure agent communication (mTLS)
  - Traffic management for agents
  - Distributed tracing
  - Policy enforcement

#### 4. Specialized AI Gateways

- <a href="https://github.com/kgateway-dev/kgateway">`KGateway`</a>:
  Previously Gloo, focused on AI/ML traffic
- <a href="https://github.com/knoway-dev/knoway">`DaoCloud knoway`</a>: AI
  gateway with model management
- <a href="https://github.com/alibaba/higress">`Higress`</a>: Alibaba's
  cloud-native gateway with AI support
- <a href="https://github.com/Kong/kong">`Kong`</a>: API gateway with LLM
  plugins
- <a href="https://github.com/vllm-project/semantic-router">`Semantic
  Router`</a>: vLLM's semantic-based routing

### Gateway Features for Agents

- **Prompt Routing:** Route requests to specialized models based on content
- **Cost Optimization:** Balance between quality and cost
- **Caching:** Share responses across agents to reduce latency
- **A/B Testing:** Compare agent performance across models
- **Security:** API key management, rate limiting, DDoS protection

## Observability with OpenTelemetry (OTEL)

### OTEL for Agentic Systems

OpenTelemetry provides comprehensive observability for agent systems,
tracking the complete lifecycle of agent operations.

#### Key Metrics for Agents

- **Agent Execution:**
  - Task completion time
  - Tool invocation count
  - Success/failure rates
  - Retry patterns
- **LLM Interactions:**
  - Prompt tokens and costs
  - Response times (TTFT, TPOT)
  - Model utilization
- **Resource Usage:**
  - CPU/Memory per agent instance
  - Network bandwidth
  - Storage I/O

#### Tracing Agent Workflows

- **Distributed Traces:**
  - End-to-end agent task execution
  - Multi-agent collaboration traces
  - Tool invocation chains
  - Cross-service dependencies
- **Context Propagation:**
  - Trace IDs across agent hops
  - Baggage for agent metadata
  - Correlation across services

#### OTEL Integration Tools

- <a href="https://github.com/openlit/openlit">`OpenLit`</a>: OpenTelemetry
  for LLM applications and agents
- <a href="https://github.com/traceloop/openllmetry">`OpenLLMetry`</a>:
  Specialized for LLM tracing
- <a href="https://github.com/langfuse/langfuse">`Langfuse`</a>: LLM
  observability platform with agent support
- <a href="https://github.com/truera/trulens">`TruLens`</a>: Agent evaluation
  and observability

See [Observability Guide](../observability/README.md) for more details on
monitoring agent systems.

## Safety & Security

### Security Challenges for Agents

Autonomous agents introduce unique security risks that require specialized
mitigations:

#### 1. Code Execution Risks

- **Risk:** Agents may generate and execute malicious code
- **Mitigation:**
  - Sandboxed execution environments (gVisor, Kata Containers)
  - Code review and static analysis before execution
  - Restricted system calls and file access
  - Timeout mechanisms for runaway processes

#### 2. Prompt Injection

- **Risk:** Adversarial prompts can hijack agent behavior
- **Mitigation:**
  - Input sanitization and validation
  - Prompt templates with locked sections
  - Separate system and user contexts
  - Adversarial testing and red teaming

#### 3. Data Access & Privacy

- **Risk:** Agents may access or leak sensitive data
- **Mitigation:**
  - Role-based access control (RBAC)
  - Data masking and anonymization
  - Audit logging of all data access
  - Principle of least privilege

#### 4. Unauthorized Actions

- **Risk:** Agents may perform unintended or harmful actions
- **Mitigation:**
  - Human-in-the-loop (HITL) for critical operations
  - Action allowlists and blocklists
  - Rate limiting and quotas
  - Rollback mechanisms

#### 5. Multi-Tenant Isolation

- **Risk:** Agents in shared environments may interfere or leak data
- **Mitigation:**
  - Namespace isolation in Kubernetes
  - Network policies
  - Resource quotas
  - Separate secrets management

### Safety Best Practices

#### Design Patterns

- **Guardrails:** Pre-defined boundaries for agent behavior
- **Verification Loops:** Validate agent outputs before execution
- **Escalation Policies:** Route risky actions to humans
- **Rollback Plans:** Undo mechanisms for agent actions
- **Monitoring Alerts:** Detect anomalous agent behavior

#### Security Tools

- **Policy Engines:**
  - <a href="https://github.com/open-policy-agent/opa">`Open Policy
    Agent`</a>: Policy enforcement for agent actions
  - <a href="https://github.com/kyverno/kyverno">`Kyverno`</a>: Kubernetes
    policy management
- **Secrets Management:**
  - <a href="https://github.com/external-secrets/external-secrets">`External
    Secrets Operator`</a>
  - <a href="https://github.com/hashicorp/vault">`HashiCorp Vault`</a>
- **Runtime Security:**
  - <a href="https://github.com/falcosecurity/falco">`Falco`</a>: Runtime
    security monitoring
  - <a href="https://github.com/aquasecurity/tracee">`Tracee`</a>: Runtime
    security and forensics

#### Compliance & Governance

- **Audit Trails:** Complete logging of agent decisions and actions
- **Explainability:** Understand why agents made specific choices
- **Testing:** Comprehensive test suites including adversarial scenarios
- **Documentation:** Clear policies and runbooks for agent operations
- **Incident Response:** Procedures for handling agent misbehavior

## Serverless for Agents

### Knative for Agent Workloads

<a href="https://github.com/knative/serving">`Knative`</a> provides serverless
infrastructure ideal for event-driven agent workloads.

- **Key Benefits:**
  - Scale-to-zero for idle agents
  - Auto-scaling based on request load
  - Event-driven activation
  - Cost optimization
- **Use Cases:**
  - Periodic agent tasks
  - Event-triggered agents
  - On-demand agent execution
- **Example:** <a href="https://github.com/knative/docs/blob/main/docs/blog/articles/ai_functions_llama_stack.md">`Llama
  Stack on Knative`</a>

## Learning Resources

### Recommended Videos

- <a href="https://www.youtube.com/watch?v=WvpDBJVjIbI">`Building Agentic
  Systems`</a>: Comprehensive overview of agent architecture patterns
- <a href="https://jimmysong.io/blog/kubernetes-ai-oss-solo/">`Kubernetes for
  AI OSS`</a>: Jimmy Song's analysis of AI on Kubernetes

### Key Papers & Specs

- **Model Context Protocol Specification:** Standards for agent communication
- **Agent Security Whitepaper:** CNCF security considerations for agents
- **Multi-Agent Patterns:** Design patterns for agent collaboration

### Community & Working Groups

- **CNCF TAG Workloads Foundation:** Agent workload patterns
- **Kubernetes WG AI Integration:** Integration standards
- **OpenTelemetry SIG:** Observability for agents

## RoadMap

### Emerging Topics

- **Agent Mesh:** Service mesh specifically for agent-to-agent communication
- **Agent Marketplaces:** Discover and deploy pre-built agents
- **Fine-Tuning for Agents:** Specialized model training for agent tasks
- **Multi-Modal Agents:** Agents with vision, audio, and code capabilities
- **Swarm Intelligence:** Large-scale coordination of agent populations

### Standards in Development

- **Agent API Specification:** Common APIs for agent interaction
- **Security Profiles:** Standard security configurations for agents
- **Observability Schema:** Unified metrics and traces for agents
- **Deployment Manifests:** Kubernetes CRDs for agent workloads

## Related Sections

- [Inference Guide](../inference/README.md): LLM backends for agent reasoning
- [Observability Guide](../observability/README.md): Monitoring agent systems
- [Training Guide](../training/README.md): Training agent models
- [Kubernetes Guide](../kubernetes/README.md): Kubernetes fundamentals

---

*Note: This landscape is rapidly evolving. Contributions and updates are
welcome as new projects and patterns emerge.*
