---
status: Active
maintainer: pacoxu
last_updated: 2026-07-09
tags: ai-agents, agentic-workflow, kubernetes, mcp, agent-platforms
canonical_path: agent-infra/README.md
---

# AI Agent Platforms and Frameworks

This document provides a comprehensive overview of AI Agent platforms,
frameworks, and infrastructure projects in the cloud-native ecosystem. AI
Agents are autonomous software systems that can perceive their environment,
make decisions, and take actions to achieve specific goals, often using Large
Language Models (LLMs) as their core reasoning engine.

## Table of Contents

- [Overview](#overview)
- [Production Agent Infra: 9 Layers + 4 Cross-Cutting Capabilities](#production-agent-infra-9-layers--4-cross-cutting-capabilities)
- [Native AI Agent Kits](#native-ai-agent-kits)
- [Kubernetes-Native Agent Platforms](#kubernetes-native-agent-platforms)
- [Agent Infra Ecosystem Snapshot (2026)](#agent-infra-ecosystem-snapshot-2026)
- [Agent Development Frameworks](#agent-development-frameworks)
- [Agent Sandbox Infrastructure](#agent-sandbox-infrastructure)
- [Agent Infrastructure Components](#agent-infrastructure-components)
- [CNCF and Ecosystem Initiatives](#cncf-and-ecosystem-initiatives)
- [Learning Topics](#learning-topics)
- [RoadMap](#roadmap)
- [References](#references)

## Overview

AI Agents represent the next evolution in AI infrastructure, moving beyond
simple model inference to autonomous systems that can:

- Execute complex multi-step workflows
- Use tools and APIs to interact with external systems
- Maintain memory and context across conversations
- Make decisions based on goals and constraints
- Learn and adapt from feedback

### Four-Stage Evolution of AI Agents

According to **Professor Yang Qiang** (Hong Kong University of Science and
Technology), AI Agents (智能体) are expected to evolve through four distinct
stages in 2026 and beyond:

1. **Stage 1: Human-Defined Goals and Planning**
   - Both objectives and execution plans are defined by humans
   - Agents follow predetermined workflows
   - Current most common implementation stage

2. **Stage 2: AI-Assisted Planning**
   - Goals are defined by humans
   - Planning and execution strategies are assisted by AI
   - AI helps optimize workflows but humans maintain control

3. **Stage 3: AI-Learned Planning from Process Data**
   - AI observes human workflows and process data
   - Automatically learns and generates planning strategies
   - Reduces human intervention in routine tasks

4. **Stage 4: Fully Autonomous Agents**
   - Ultimate stage: Both goals and planning are defined internally by LLMs
   - Agents operate with true autonomy
   - Self-directed decision-making and execution

**Current State**: Most AI Agents today operate at Stages 1 and 2.

**Economic Value Insight**: According to industry observations, the bottleneck
for agents creating real economic value is not in the model capabilities
themselves, but in:

- **Environment**: Deploying models into diverse enterprise environments
- **Education**: Training organizations to effectively use agent systems

Even without further model improvements, significant economic benefits can be
realized by deploying existing models across various enterprise scenarios. The
focus should be on integration, deployment infrastructure, and organizational
readiness.

Reference: [Agent Evolution Theory - WeChat Article](https://mp.weixin.qq.com/s/NUx4n5j0ftxzZ0Sz29RjOQ)
(accessed 2026)

### Agent Landscape Categories

The AI Agent landscape includes:

1. **Native Agent Kits**: Cloud provider-specific platforms (e.g., VolcEngine)
2. **Kubernetes-Native Solutions**: Projects designed for K8s environments
   (e.g., KAgent, AgentCube)
3. **Development Frameworks**: Libraries and SDKs for building agents
   (e.g., AgentScope, LangChain)
4. **Infrastructure Components**: Sandboxes, gateways, MCP servers

## Production Agent Infra: 9 Layers + 4 Cross-Cutting Capabilities

For a production-oriented architecture view, see
[AI Infra 全景图：Agent Framework、调度、编排、沙箱、记忆管理、Tracing 分层拆解](./ai-agent-infra-9-layers-zh.md).

This companion document maps the runtime path from **L0 基础资源层** to
**L8 可观测与运营层**, and explains how **security governance**,
**CI/CD and release governance**, **FinOps**, and **developer experience**
cut across every layer. It is a useful complement to this index-style
ecosystem guide because it focuses on how production Agent systems are
assembled, debugged, evaluated, governed, and operated end to end.

## Native AI Agent Kits

### VolcEngine Native AI Agent Kit (ByteDance)

<a href="https://www.volcengine.com/">VolcEngine</a> provides a comprehensive
Native AI Agent Kit with the following architecture:

**Architecture Components:**

- **API Gateway (API网关)**: Entry point for traffic (流量接入)
- **AI Agent Core**: Central orchestration with three key capabilities:
  - 丰富的应用模版 (Rich application templates)
  - 极致弹性 按需付费 (Extreme elasticity, pay-as-you-go)
  - AI 应用全链路可观测 (Full-chain observability for AI applications)

**Core Capabilities (核心能力):**

1. **Extreme Elasticity (极致弹性)**:
   - Helps split-level vCPU elasticity
   - Meets agent resource demands
   - Scales from zero to thousands of instances

2. **MCP Support (支持 MCP)**:
   - Supports Model Context Protocol
   - Agents can use MCP to integrate with ecosystems
   - Connect to data sources and existing tools

3. **Memory Management (记忆管理)**:
   - Provides instant RAG functionality
   - Supports private domain knowledge
   - Long-term memory recall

4. **Full-chain Observability (全链路观测)**:
   - End-to-end agent monitoring
   - Tracks developer call chains, token consumption, and framework overhead
   - Transparent to developers without affecting business service performance

**Three-Layer Architecture:**

1. **模型 (Models)**:
   - 火山方舟模型 (Volcano Ark models)
   - 自建模型 (Self-built models)

2. **Tools**:
   - MCP Hub
   - OS Agent
   - Sandbox

3. **Memory**:
   - 知识平台 (Knowledge platform)
   - 长期记忆 (Long-term memory)

Reference: VolcEngine AI Agent Platform showcases the industry trend of
providing integrated agent infrastructure with elasticity, protocol support
(MCP), memory management, and comprehensive observability.

## Kubernetes-Native Agent Platforms

### KAgent

<a href="https://github.com/kagent-dev/kagent">`KAgent`</a>: **CNCF Sandbox
Project**

KAgent is a Kubernetes-native platform for building and deploying AI agents.
It provides a declarative approach to agent management using Kubernetes
Custom Resources.

**Key Features:**

- Kubernetes-native agent orchestration
- Declarative agent configuration
- Built-in agent lifecycle management
- Integration with Kubernetes RBAC and security policies

**Status**: CNCF Sandbox (2024)

**Use Cases:**

- Multi-tenant agent deployment
- Enterprise agent orchestration
- Cloud-native agent workflows

### Volcano AgentCube

<a href="https://github.com/volcano-sh/agentcube">`AgentCube`</a>

AgentCube is part of the Volcano ecosystem, providing agent orchestration
capabilities on Kubernetes with a focus on batch workloads and resource
management.

**Key Features:**

- Integration with Volcano scheduling
- Batch agent execution
- GPU-aware agent scheduling
- Queue-based agent management

**Maintained by**: Volcano community (CNCF Graduated project)

### Volcano Kthena

<a href="https://github.com/volcano-sh/kthena">`Kthena`</a>

Kthena is a Volcano ecosystem project for Kubernetes-native LLM inference
orchestration and management. While primarily focused on inference workloads,
Kthena provides advanced scheduling capabilities relevant to agentic systems
that require LLM backends.

**Key Features:**

- LeaderWorkerSet integration for distributed inference topologies
- Network topology-aware scheduling (Volcano v1.14+)
- Role-level gang scheduling for distributed workloads
- ModelServing lifecycle management with revision control
- Router observability and debugging capabilities

**Maintained by**: Volcano community (CNCF Graduated project)

### Kubernetes SIG Agent Sandbox

<a href="https://github.com/kubernetes-sigs/agent-sandbox">`agent-sandbox`</a>

Official Kubernetes SIG project providing secure sandbox environments for
running AI agents with strong isolation guarantees.

**Key Features:**

- Secure execution environments for agent code
- Strong isolation between agents and host systems
- Integration with Kubernetes security policies
- Support for code interpreters and tool execution

**Status**: Kubernetes SIG project (official)

See also: [Agent Sandbox Documentation](../docs/kubernetes/isolation.md#6-agent-sandbox-kubernetes-sig-project)

### Agent Substrate

<a href="https://github.com/agent-substrate/substrate">`agent-substrate/substrate`</a>

Agent Substrate is a Kubernetes-based runtime and control plane for
agent-like workloads. Instead of keeping one Pod bound to one long-lived
session, it maps a larger set of stateful "actors" onto a smaller pool of
ready workers and keeps the Kubernetes control plane out of the hot path.

**Key Features:**

- Actor/worker multiplexing for higher density
- Suspend/resume lifecycle for stateful sessions
- Real-time assignment and traffic routing to active workers
- gVisor-based OCI container execution with framework-agnostic compatibility

**Status**: Very early development; not production-ready yet

**Use Cases:**

- Large fleets of mostly-idle coding or tool-using agents
- Stateful agent sessions that need sub-second reactivation
- Platforms that want Kubernetes primitives underneath but lower latency than
  Pod-per-session orchestration

See also: [CNCF: Why sandboxing your agent is not enough](https://www.cncf.io/blog/2026/07/07/why-sandboxing-your-agent-is-not-enough/)

### Agent Infra Sandbox

<a href="https://github.com/agent-infra/sandbox">`agent-infra/sandbox`</a>

Community project providing sandbox infrastructure for AI agents with focus
on security and isolation.

**Key Features:**

- Lightweight sandbox runtime
- Multiple isolation backends
- Integration with agent frameworks
- Resource limiting and monitoring

### OpenKruise Agents

<a href="https://github.com/openkruise/agents">`openkruise/agents`</a>

OpenKruise extension providing agent capabilities for application lifecycle
management in Kubernetes.

**Key Features:**

- Application-aware agent operations
- Integration with OpenKruise workload controllers
- Advanced deployment strategies for agent workloads
- In-place update support for agents

### ArgoCD Agent

<a href="https://github.com/argoproj-labs/argocd-agent">`argocd-agent`</a>

ArgoCD Agent provides agent-based deployment capabilities for GitOps workflows,
enabling secure and scalable application delivery across multiple clusters.

**Key Features:**

- Agent-based cluster registration
- Secure pull-based deployment model
- Multi-cluster GitOps management
- Integration with ArgoCD ecosystem
- Reduced control plane overhead

**Status**: ArgoProj Labs (experimental)

**Use Cases:**

- Multi-cluster GitOps deployments
- Edge cluster management
- Secure deployments in restricted environments
- Large-scale cluster fleet management

### Agent Infra Ecosystem Snapshot (2026)

Based on the "Agent Infra 生态图谱" conference summary (KCD Beijing / vLLM
community), the current sandbox/runtime ecosystem can be summarized as:

- **K8s standard layer — `kubernetes-sigs/agent-sandbox`**: SIG Apps official
  project with `Sandbox` CRD, `SandboxWarmPool`, and deep GKE integration.
- **Agent runtime substrate — `agent-substrate/substrate`**: Core runtime
  system for invocation-based agent wake-up, suspend/resume, and shared
  worker pools on Kubernetes.
- **Alibaba `OpenSandbox`**: Four sandbox types (`Coding`, `GUI`, `Exec`,
  `RL`) plus a three-tier isolation design for heterogeneous agent workloads.
- **OpenKruise AIO Sandbox**: Lifecycle management, E2B protocol compatibility,
  and an all-in-one container design to simplify framework integration.
- **ByteDance `DeerFlow 2.0`**: Sub-agent orchestration with independent
  sandbox mode for fine-grained isolation and parallel scheduling.
- **Tencent Cloud Agent Runtime**: Optimized for production throughput with
  ~100 ms cold start and 100K-level concurrency claims.

These projects indicate a convergence path: **standardized CRD control plane +
durable actor/session runtime + pluggable sandbox runtime backends + warm pool
or snapshot-based latency control**.

#### Kubernetes Dynamic Containers Watch (2026-06-18)

[kubernetes/enhancements#6169](https://github.com/kubernetes/enhancements/pull/6169)
adds the first KEP draft for
[KEP-5972: Dynamic Containers](https://github.com/kubernetes/enhancements/issues/5972).
As of this snapshot, the PR is still open, labeled `do-not-merge/hold`, and
under active API / SIG-Auth review, so it should be tracked as an upstream
design signal rather than a consumable Kubernetes API.

The important AI infra signal is that Kubernetes core is discussing whether a
running Pod can become a mutable execution envelope for agentic and
high-churn workloads:

- **Warm pools for agents**: pre-create Pods that have already paid scheduling,
  sandbox, CNI, volume, and device setup cost, then add short-lived main
  containers later for low-latency tool execution.
- **Hierarchical scheduling**: let Kubernetes allocate the coarse Pod resource
  budget while Ray, Slurm, or agent runtimes perform fine-grained local
  container placement inside that envelope.
- **Restore / migration fast path**: schedule a shell Pod first, then restore
  or migrate workload state into it.
- **In-place sidecar or daemon changes**: swap supporting containers with less
  disruption than full Pod replacement.

The latest design update moved new Pod mutability behind a dedicated
`pods/dynamic` subresource instead of broadening default Pod update rules. That
subresource is not intended to be granted by the default `edit` ClusterRole.
The draft also adds a read-only `pods/allocated` view for the kubelet-allocated
Pod spec and gates the feature through `DynamicContainers` on
`kube-apiserver` and `kubelet`.

The active review concern is admission and policy compatibility. After the
SIG-Auth discussion, the proposed direction is:

- provide a static cluster-level opt-out, likely as an API server flag;
- treat the new subresource as the future extension point for broader Pod
  mutability, while still limiting the first alpha scope;
- require admission webhooks and policies that cover Pod create or update to
  also cover `pods/dynamic`; otherwise requests through the new subresource
  should be rejected instead of bypassing legacy policy.

For this repository, the practical takeaway is to keep agent sandbox
architecture decoupled from this KEP for now: design warm pools and sandbox
APIs around existing CRDs/runtime backends, but watch `pods/dynamic` because it
could eventually collapse some custom fast-start paths back into core
Kubernetes.

#### Agent Sandbox Selection Update (2026-07-09)

Recent agent sandbox projects should be compared by layer, not as direct
one-for-one replacements. A practical platform usually combines an
agent-facing API, a Kubernetes lifecycle controller, and one or more isolation
runtimes:

| Layer | Candidate Projects | Primary Role | Selection Notes |
| ----- | ------------------ | ------------ | --------------- |
| Agent-facing sandbox platform | [OpenSandbox](https://github.com/alibaba/OpenSandbox), [CubeSandbox](https://github.com/TencentCloud/CubeSandbox), [E2B](https://github.com/e2b-dev/e2b), [Daytona](https://github.com/daytonaio/daytona), [Sandbox0](https://github.com/sandbox0-ai/sandbox0) | SDK/API, sandbox lifecycle, command/file/browser execution, templates | Use OpenSandbox as the broad self-hosted default; evaluate CubeSandbox for high-density E2B-compatible microVM pools; check Daytona's AGPLv3 impact before embedding. |
| Kubernetes lifecycle API | [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox), [agent-sandbox/agent-sandbox](https://github.com/agent-sandbox/agent-sandbox), [volcano-sh/agentcube](https://github.com/volcano-sh/agentcube) | CRD/controller, warm pools, stable sandbox identity, scheduling hooks | `kubernetes-sigs/agent-sandbox` is the neutral K8s API layer; `agent-sandbox/agent-sandbox` adds REST/MCP and E2B compatibility; AgentCube is still proposal/early design. |
| Agent runtime substrate | [agent-substrate/substrate](https://github.com/agent-substrate/substrate) | Invocation routing, worker pools, agent actor lifecycle, suspend/resume | Use when agent fleets are mostly idle and dedicated pods would waste resources; pair it with Agent Sandbox or runtime sandboxing for the isolation boundary. |
| Isolation runtime | [gVisor](https://github.com/google/gvisor), [Kata Containers](https://github.com/kata-containers/kata-containers), [containerd/nerdbox](https://github.com/containerd/nerdbox), [Firecracker](https://github.com/firecracker-microvm/firecracker), [Kuasar](https://github.com/kuasar-io/kuasar) | Runtime boundary for untrusted code | Start with gVisor for density and operational simplicity; use Kata for VM-level tenant boundaries and GPU paths; treat Firecracker as a low-level primitive unless the team owns the control plane. |
| Local coding-agent sandbox | [Cleanroom](https://github.com/buildkite/cleanroom), [Brood Box](https://github.com/stacklok/brood-box), [microsandbox](https://github.com/superradcompany/microsandbox), [BoxLite](https://github.com/boxlite-ai/boxlite), [Matchlock](https://github.com/jingkaihe/matchlock), [Shuru](https://github.com/superhq-ai/shuru), [sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime) | Developer-machine isolation, repo policy, credential proxy, diff review | Prefer Cleanroom/Brood Box when the threat model is coding-agent access to a repo; use microsandbox/BoxLite for embeddable local microVM APIs; use sandbox-runtime for OS policy guardrails without VM isolation. |
| Watch / avoid for now | [BinSquare/ERA](https://github.com/BinSquare/ERA), [autohandai/sandbox-core](https://github.com/autohandai/sandbox-core), [SmolVM](https://github.com/CelestoAI/SmolVM), [Gondolin](https://github.com/earendil-works/gondolin), [Pyro](https://github.com/danievanzyl/pyro), `opencapsule/opencapsule` | Early-stage or unclear availability | ERA is archived/deprecated; `opencapsule/opencapsule` was not publicly resolvable on GitHub when checked; the remaining projects are useful to track or borrow ideas from but need deeper maturity validation. |

`agent-substrate/substrate` is closest to a **durable agent-session runtime**
layer rather than a generic agent framework or sandbox SDK.

- Closest architectural neighbor: `agent-sandbox/agent-sandbox` if you want a
  Kubernetes-native runtime with persistent sessions, but its center of gravity
  is REST/MCP sandbox lifecycle management and E2B compatibility.
- Closest agent-facing API alternatives: `Sandbox0` and `E2B` if you want
  session/sandbox APIs, persistent volumes, warm pools, and credential or
  network controls exposed directly to application code.
- Higher-level alternative: `kagent` if you want to define and operate agents
  as Kubernetes resources, rather than optimize actor multiplexing and
  suspend/resume latency in the runtime layer.

Default stack recommendation:

1. **Agent API**: OpenSandbox as the broad self-hosted API/SDK surface.
2. **Kubernetes lifecycle**: `kubernetes-sigs/agent-sandbox` for `Sandbox`,
   `SandboxTemplate`, `SandboxClaim`, and `SandboxWarmPool`.
3. **Runtime substrate**: `agent-substrate/substrate` when idle-agent density,
   invocation-based wake-up, and suspend/resume matter.
4. **Default runtime**: gVisor for CPU-only untrusted code with high density.
5. **High-risk runtime**: Kata or CubeSandbox for stronger microVM boundaries.
6. **Local development**: Cleanroom or Brood Box for repo-scoped egress,
   host-side credentials, and post-run change review.

## Agent Development Frameworks

### LangChain DeepAgents

<a href="https://github.com/langchain-ai/deepagents">`deepagents`</a>

DeepAgents is LangChain's framework for building sophisticated multi-agent
systems with enhanced reasoning capabilities through deeper chain-of-thought
processing and planning.

**Key Features:**

- Enhanced reasoning with deeper chain-of-thought processing
- Advanced planning and task decomposition
- Integration with LangChain ecosystem
- Multi-agent coordination patterns
- Advanced memory and state management
- Support for complex agent workflows

**Maintained by**: LangChain AI

**Status**: Active development

### AgentScope

<a href="https://github.com/agentscope-ai/agentscope">`AgentScope`</a>

AgentScope is a flexible and comprehensive agent development framework
supporting multi-agent systems.

**Key Features:**

- Multi-agent orchestration
- Built-in communication protocols
- Support for various LLM backends
- Python-based development experience

**Maintained by**: AgentScope AI community

### Dapr Agents

<a href="https://github.com/dapr/dapr-agents">`dapr-agents`</a>

Integration of agent capabilities with Dapr (Distributed Application Runtime),
providing cloud-native agent primitives.

**Key Features:**

- Dapr building blocks for agents
- Service-to-service agent invocation
- State management for agent memory
- Pub/sub patterns for agent communication

**Status**: Part of the Dapr ecosystem

### Coze Studio

<a href="https://github.com/coze-dev/coze-studio">`Coze Studio`</a>

Development environment for building conversational AI agents with visual
tooling.

**Key Features:**

- Visual agent design interface
- Pre-built agent templates
- Integration with popular LLM providers
- Testing and debugging tools

### Open-AutoGLM

<a href="https://github.com/zai-org/Open-AutoGLM">`Open-AutoGLM`</a>

Open-source autonomous agent framework based on GLM (General Language Model).

**Key Features:**

- Autonomous task execution
- Tool usage and API calling
- Chinese language optimization
- Integration with Zhipu AI models

### Spring AI Alibaba

<a href="https://github.com/alibaba/spring-ai-alibaba">`spring-ai-alibaba`</a>

Spring ecosystem integration for building AI agents with Alibaba Cloud
services.

**Key Features:**

- Spring Boot integration for agents
- Alibaba Cloud service connectors
- Java/Kotlin agent development
- Enterprise-grade reliability patterns

### Google ADK-Go

<a href="https://github.com/google/adk-go">`adk-go`</a>

Google's Agent Development Kit for Go, providing Go-native agent development
capabilities.

**Key Features:**

- Go-native agent framework
- Google Cloud integration
- High-performance agent runtime
- Structured agent patterns

## Agent Sandbox Infrastructure

Agent sandboxes provide secure, isolated execution environments for AI agents
that run untrusted code — LLM-generated Python, shell commands, file
operations, and browser automation. Designing a scalable sandbox requires
choosing the right architecture pattern and underlying technology.

### Two Architecture Patterns

<a href="https://browser-use.com/posts/two-ways-to-sandbox-agents">Browser
Use</a> describes two fundamental patterns for keeping agent code isolated
from infrastructure secrets:

**Pattern 1: Isolate the Tool** — The agent loop runs on your backend;
only dangerous operations (code execution, terminal) run in a separate
sandbox reached via HTTP. Simple to adopt but the agent still shares resources
with the API backend.

**Pattern 2: Isolate the Agent** — The entire agent runs in a sandbox
with zero secrets. A stateless **control plane** holds all credentials and
proxies every sensitive operation:

- **LLM calls**: Control plane owns the full conversation history and proxies
  to the LLM provider; sandbox only sends new messages
- **File sync**: Sandbox requests presigned upload/download URLs; never
  holds cloud credentials
- **Billing and cost caps**: Enforced at the control plane boundary

Pattern 2 makes the agent fully disposable and scales each layer
independently. Key insight: *"Your agent should have nothing worth stealing
and nothing worth preserving."*

### OpenClaw-Centric Cloud-Native Deployment

[OpenClaw](https://openclawai.github.io/) is an open-source agent framework
that already includes sandbox abstractions and backend plugins. In practice,
it maps well to Kubernetes-style control-plane/data-plane separation:

- **Agent control plane** (API, session state, policy, auth) runs as regular
  Deployments/Services in Kubernetes.
- **Execution sandbox plane** (tool calls, shell/code execution, browser/file
  access) runs in isolated workers selected by a sandbox backend.

OpenClaw's current sandbox backend options include
`DockerSandboxBackend`, `SSHSandboxBackend`, and `OpenShellSandboxBackend`,
with `mirror` and `remote` execution modes in its backend configuration.
This model is compatible with `agent-sandbox` CRDs or any internal sandbox
operator that allocates one isolated runtime per agent session.

#### Minimal Cloud-Native Shape

1. **Ingress/API Layer**: Agent gateway (`Deployment` + `Service` +
   `HorizontalPodAutoscaler`)
2. **Scheduler/Queue Layer**: Route tasks to a sandbox pool (Kubernetes Queue,
   internal queue, or workflow engine)
3. **Sandbox Runtime Layer**: One sandbox per session/task with strict quotas,
   network policy, and filesystem boundaries
4. **Observability Layer**: Trace `agent_step`, `tool_call`, and `sandbox_id`
   together for debugging and cost attribution

### Pod or VM for Agent Runtime?

Short answer: run the **control plane in Pods**, and choose Pod-runtime vs
VM-runtime for **sandbox workers** by risk level.

| Runtime choice | Best fit | Isolation strength | Startup/cost profile | GPU path |
| -------------- | -------- | ------------------ | -------------------- | -------- |
| Pod (`runc`) | Trusted internal tools, low risk | Low | Fastest, cheapest | Native |
| Pod + `gVisor` RuntimeClass | Untrusted code with moderate compatibility needs | Medium | Fast, low overhead | Limited/depends on stack |
| Pod + Kata RuntimeClass (microVM isolation) | Multi-tenant untrusted workloads | High | Slower, higher overhead | Good with passthrough setups |
| Dedicated VM per agent/tenant | Strongest boundary, compliance-heavy scenarios | Very high | Slowest, most expensive | Full VM control |

#### Practical Recommendation

1. Start with **Kubernetes Pods for control plane** and **sandbox workers on
   RuntimeClass** (`gVisor` for CPU-heavy untrusted tasks, `Kata` for stricter
   isolation).
2. Use **VM pools** only for high-risk tenants, regulated data, or when kernel
   isolation/compliance requires hard VM boundaries.
3. Keep the agent runtime **ephemeral** (warm pool + TTL cleanup) and persist
   only explicit artifacts (logs, outputs, checkpoints).

Example `Sandbox` runtime selection:

```yaml
apiVersion: agents.x-k8s.io/v1alpha1
kind: Sandbox
metadata:
  name: openclaw-session-123
spec:
  podTemplate:
    spec:
      runtimeClassName: kata-qemu
      containers:
      - name: openclaw-worker
        image: ghcr.io/example/openclaw-worker:latest
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
```

### Sandbox Technology Landscape

| Technology | Cold Start | Isolation | Python | Image Build |
| ---------- | --------- | --------- | ------ | ----------- |
| Container (Docker) | ~50ms | Shared kernel | Full | Dockerfile |
| Firecracker microVM | ~125ms (+snapshot <1s) | Separate kernel | Full | ext4 rootfs |
| Kata Containers | ~125ms | Separate kernel | Full | OCI/Docker |
| WASM (monty) | 0.06ms | WASI | Limited | Custom |
| Unikernel (Unikraft) | <100ms | Minimal kernel | Improving | Custom |

The core tradeoffs analyzed by 高策 (gaocegege) in
<a href="https://gaocegege.com/Blog/genai/unikernel-agent">Agent sandbox
可能的选型以及 unikernel 的机会</a> (2026):

- **e2b** (<a href="https://github.com/e2b-dev/e2b">GitHub</a>): Uses
  Firecracker microVMs. Templates are full VM snapshots that resume in under
  1 second (Intel <8ms, AMD <3ms). Image building converts Dockerfiles to
  ext4 rootfs. Uses a lightweight best-of-k scheduler rather than Kubernetes.
- **k7** (<a href="https://github.com/Katakate/k7">GitHub</a>): Uses Kata
  Containers with Firecracker VMM. Works directly with OCI/Docker images —
  no ext4 conversion. Integrates with Kubernetes/k3s. Kata's abstraction
  prevents direct use of Firecracker snapshots.
- **monty** (<a href="https://github.com/pydantic/monty">GitHub</a>): A
  WASM-based Python-subset interpreter achieving 0.06ms cold starts, but
  supports only a limited subset of Python (no `class`, limited stdlib).
- **Unikraft** (<a href="https://unikraft.org/">website</a>): Unikernel
  framework that compiles application + minimal kernel into a single image.
  Very small attack surface and fast startup. Added limited multi-process
  support in v0.19 (May 2025). Browser Use uses Unikraft microVMs in
  production for zero-secret agent isolation.

### Image Distribution Optimization

For large images, pulling is often the dominant latency source — not
container/VM startup itself. Modal's approach of **FUSE-based lazy loading**
serves files on-demand from a priority cache chain (memory → local SSD →
zone cache → CDN → object storage), dramatically cutting startup time.
Similar techniques: <a href="https://github.com/containerd/stargz-snapshotter">
estargz</a>, <a href="https://github.com/dragonflydb/dragonfly">Dragonfly</a>.

### Selection Guidance

For production AI-Infra platforms, avoid selecting a single "sandbox project"
without first deciding the layer boundary:

1. **Platform API**: choose OpenSandbox, CubeSandbox, E2B, Daytona, or
   Sandbox0 based on self-hosting, protocol compatibility, and licensing.
2. **Kubernetes API**: use `kubernetes-sigs/agent-sandbox` when the platform
   needs declarative lifecycle, warm pools, and stable sandbox identity.
3. **Runtime substrate**: use `agent-substrate/substrate` when many agents
   should exist dormantly and wake on invocation without one pod per agent.
4. **Runtime boundary**: map risk level to `RuntimeClass` or VM pools:
   gVisor for density, Kata for VM isolation, and dedicated VM/microVM pools
   for regulated tenants.
5. **Developer workstation**: evaluate Cleanroom or Brood Box separately from
   cluster sandboxes because local coding agents need repo diff review,
   credential forwarding, and deny-by-default egress policy.

The useful decision rule is: **OpenSandbox or CubeSandbox is a platform
choice; Agent Sandbox is a Kubernetes lifecycle choice; Agent Substrate is a
runtime-density choice; gVisor, Kata, nerdbox, and Firecracker are runtime
boundary choices**.

### References

- <a href="https://browser-use.com/posts/two-ways-to-sandbox-agents">Browser
  Use: Building Secure, Scalable Agent Sandbox Infrastructure</a>
- <a href="https://gaocegege.com/Blog/genai/unikernel-agent">高策: Agent
  sandbox 可能的选型以及 unikernel 的机会</a>
- <a href="https://github.com/e2b-dev/e2b">e2b (Firecracker sandbox)</a>
- <a href="https://github.com/alibaba/OpenSandbox">OpenSandbox</a>
- <a href="https://github.com/TencentCloud/CubeSandbox">CubeSandbox</a>
- <a href="https://github.com/containerd/nerdbox">containerd/nerdbox</a>
- <a href="https://github.com/buildkite/cleanroom">Cleanroom</a>
- <a href="https://github.com/stacklok/brood-box">Brood Box</a>
- <a href="https://github.com/superradcompany/microsandbox">microsandbox</a>
- <a href="https://github.com/Katakate/k7">k7 (Kata sandbox)</a>
- <a href="https://unikraft.org/">Unikraft</a>
- <a href="../docs/kubernetes/isolation.md#6-agent-sandbox">Detailed implementation
  guide: Agent Sandbox in Kubernetes Isolation doc</a>

---

## Agent Infrastructure Components

### Model Context Protocol (MCP)

**Status**: Adopted (CNCF Tech Radar 2025)

Model Context Protocol (MCP) is an emerging standard for agent-to-agent
communication and context sharing. According to CNCF Tech Radar 2025, MCP and
Llama Stack are in the "Adopt" position.

**Key Concepts:**

- Standardized protocol for sharing context between agents
- Server-client architecture for context management
- Integration with existing data sources and tools
- Support for agent ecosystems

**Projects using MCP:**

- VolcEngine Native AI Agent Kit (MCP Hub, MCP Server)
- Various agent frameworks adopting MCP for interoperability

### Agent-to-Agent (A2A) / Agent Communication Protocol (ACP)

Next-generation protocols for agent collaboration:

- **A2A**: Direct agent-to-agent communication patterns
- **ACP**: Standardized communication protocol for multi-agent systems

**Status**: Emerging standards, being evaluated in various projects

### Kube-Agentic-Networking

<a href="https://github.com/kubernetes-sigs/kube-agentic-networking">`kube-agentic-networking`</a>

Kubernetes SIG project for defining networking policies and governance for
agents and tools in Kubernetes.

**Key Features:**

- Network policies for agent communication
- Tool access control and governance
- Agent-to-tool security boundaries
- Integration with Kubernetes NetworkPolicy API

## CNCF and Ecosystem Initiatives

### CNCF Agentic System Initiative

<a href="https://github.com/cncf/toc/issues/1746">CNCF TOC Issue #1746</a>

The CNCF Technical Oversight Committee is exploring an Agentic System
Initiative to coordinate efforts across the cloud-native ecosystem.

**Focus Areas:**

- Standardization of agent interfaces
- Security and isolation for agents
- Multi-agent orchestration patterns
- Integration with CNCF projects

**Status**: Under discussion (2024-2025)

### WG AI Integration

<a href="https://github.com/kubernetes/community/blob/master/wg-ai-integration/charter.md">
Kubernetes WG AI Integration Charter</a>

Working group focused on integrating AI capabilities into Kubernetes,
including agent workloads.

**Scope:**

- AI workload patterns in Kubernetes
- Agent lifecycle management
- Integration with Kubernetes APIs
- Best practices for AI agents on K8s

### KubeEdge Sedna

<a href="https://github.com/kubeedge/sedna">`Sedna`</a>

Sedna is a KubeEdge subproject providing edge-cloud collaborative AI
capabilities, including federated learning, incremental learning, and edge
inference with agent-like coordination.

**Key Features:**

- Edge-cloud synergy for AI workloads
- Federated learning across edge nodes
- Incremental learning and model updates
- Joint inference between edge and cloud
- Lifelong learning capabilities

**Status**: CNCF Incubating (KubeEdge project)

**Use Cases:**

- Edge AI agent deployment
- Distributed learning across edge devices
- Model inference at the edge with cloud coordination
- IoT and edge computing scenarios

**Architecture:**

- GlobalManager: Cloud-side control plane
- LocalController: Edge-side agent components
- Workers: Execute AI tasks (training, inference, evaluation)
- Dataset/Model management across edge-cloud

### CNCF Tech Radar 2025 - Agentic AI Platforms

According to **CNCF Tech Radar 2025 (Q3)**, the Agentic AI landscape is
categorized as follows:

**Adopt:**

- **Model Context Protocol (MCP)**: Reliable choice for most use cases
- **Llama Stack**: Proven technology for agent platforms

**Trial:**

- **Agent2Agent (A2A)**: Worth exploring to meet specific needs
- **agentgateway**: Experimental but promising
- **Haystack**: Multi-modal agent framework
- **autogen**: Microsoft's agent framework

**Assess:**

- **kagent**: CNCF project requiring careful evaluation
- **kgateway**: Agent gateway under assessment

**Hold:**

- **LangChain**: Mature but less suitable for Kubernetes-native use cases
- **crewAI**: Popular but complex for cloud-native deployments

Reference: CNCF Tech Radar provides developer perception on technology
maturity and adoption recommendations.

### Related Video Resources

- **YouTube**: <a href="https://www.youtube.com/watch?v=WvpDBJVjIbI">
  Kubernetes and AI Agents</a>
- **Blog**: <a href="https://jimmysong.io/blog/kubernetes-ai-oss-solo/">
  Kubernetes AI OSS Solo</a> by Jimmy Song

### DeepSeek AI Agent Strategy

Major AI model providers are making agents central to their platforms:

- <a href="https://x.com/deepseek_ai/status/1995452641430651132">DeepSeek
  Agent Announcement</a>
- Models increasingly designed with agent capabilities as first-class citizens
- Shift from pure inference to agentic reasoning patterns

## Learning Topics

### Core Concepts

1. **Agent Architecture**:
   - Perception: How agents understand their environment
   - Reasoning: Decision-making with LLMs
   - Action: Tool use and API calls
   - Memory: Short-term and long-term context

2. **Agent Orchestration**:
   - Single-agent vs. multi-agent systems
   - Agent collaboration patterns
   - Task decomposition and planning
   - Error handling and recovery

3. **Agent Security**:
   - Sandbox environments (Pattern 1: isolate-tool vs Pattern 2: isolate-agent)
   - Technology selection: Firecracker, Kata Containers, Unikernel, WASM
   - Resource limits and quotas
   - Tool access control
   - Audit logging
   - See [Agent Sandbox Infrastructure](#agent-sandbox-infrastructure) and
     [Isolation Guide](../docs/kubernetes/isolation.md#6-agent-sandbox)
   - Runtime benchmark: [runc vs gVisor vs Kata vs VM](./runtime-benchmark.md)

### Infrastructure Patterns

1. **Deployment Models**:
   - Serverless agents (scale-to-zero)
   - Long-running agent services
   - Batch agent execution
   - Event-driven agent invocation

2. **Resource Management**:
   - CPU/Memory allocation for agents
   - GPU scheduling for agent workloads
   - Elastic scaling strategies
   - Cost optimization

3. **Observability**:
   - Agent performance metrics
   - Token consumption tracking
   - Tool invocation tracing
   - Decision path visualization

### Protocol and Standards

1. **Model Context Protocol (MCP)**:
   - Server implementation
   - Client integration
   - Context sharing patterns
   - Tool registration

2. **Agent Communication**:
   - A2A protocol patterns
   - Message formats and schemas
   - State synchronization
   - Error handling

## RoadMap

### Short-term (2026 Q1-Q2)

- [ ] Expand documentation for each major agent platform
- [ ] Create practical guides for deploying agents on Kubernetes
- [ ] Document MCP implementation patterns
- [x] Add agent security best practices and sandbox infrastructure guide

### Medium-term (2026 Q3-Q4)

- [ ] Multi-agent system patterns and architectures
- [ ] Agent observability and monitoring guide
- [ ] Integration patterns with AI Gateway solutions
- [ ] Cost optimization strategies for agent workloads

### Long-term (2027+)

- [ ] Agent-native Kubernetes extensions
- [ ] Advanced multi-agent orchestration
- [ ] Agent marketplace and ecosystem
- [ ] Standardization efforts and protocol evolution

## References

### Official Documentation

- [KAgent Documentation](https://github.com/kagent-dev/kagent)
- [Volcano AgentCube](https://github.com/volcano-sh/agentcube)
- [Volcano Kthena](https://github.com/volcano-sh/kthena)
- [OpenClaw](https://openclawai.github.io/)
- [OpenClaw Sandboxing](https://openclawai.github.io/docs/deploying/sandboxing/)
- [Kubernetes SIG Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox)
- [Agent Substrate](https://github.com/agent-substrate/substrate)
- [Agent Infra Sandbox](https://github.com/agent-infra/sandbox)
- [Kube-Agentic-Networking](https://github.com/kubernetes-sigs/kube-agentic-networking)
- [LangChain DeepAgents](https://github.com/langchain-ai/deepagents)
- [ArgoCD Agent](https://github.com/argoproj-labs/argocd-agent)
- [KubeEdge Sedna](https://github.com/kubeedge/sedna)
- [NVIDIA NeMo Agent Toolkit (Code Sandbox)](https://docs.nvidia.com/nemo/agent-toolkit/latest/reference/sandbox.html)

### Community Resources

- [CNCF Agentic System Initiative](https://github.com/cncf/toc/issues/1746)
- [WG AI Integration Charter](https://github.com/kubernetes/community/blob/master/wg-ai-integration/charter.md)
- [CNCF Tech Radar 2025](https://radar.cncf.io/)
- [Agent Evolution Theory - WeChat Article](https://mp.weixin.qq.com/s/NUx4n5j0ftxzZ0Sz29RjOQ)
- [CNCF: Why sandboxing your agent is not enough](https://www.cncf.io/blog/2026/07/07/why-sandboxing-your-agent-is-not-enough/)
- [Browser Use: Building Secure, Scalable Agent Sandbox Infrastructure](https://browser-use.com/posts/two-ways-to-sandbox-agents)
- [高策: Agent sandbox 可能的选型以及 unikernel 的机会](https://gaocegege.com/Blog/genai/unikernel-agent)

### Related Documentation

- [AI Gateway & Agentic Workflow](../README.md#-3-ai-gateway--agentic-workflow)
- [Agent Sandbox and Isolation](../docs/kubernetes/isolation.md#6-agent-sandbox)
- [Runtime Benchmark: runc vs gVisor vs Kata vs VM](./runtime-benchmark.md)
- [Production Agent Infra: 9 Layers + 4 Cross-Cutting Capabilities](./ai-agent-infra-9-layers-zh.md)
- [Memory and Context Management](../docs/inference/memory-context-db.md)
- [LLM Inference Platforms](../docs/inference/README.md) - For model deployment
  platforms like Kaito, AIBrix, and OME that provide the inference backend
  for agent systems

---

**Note**: This is a rapidly evolving space. Many projects are in early stages
or experimental. Always verify project maturity and production-readiness
before adoption. Some content was generated with AI assistance - verify
details before using in production environments.
