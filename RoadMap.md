---
status: Active
maintainer: pacoxu
last_updated: 2025-12-01
tags: roadmap, planning, future-work, ai-native
---

# AI-Infra RoadMap 🗺️

This document outlines upcoming features, topics under consideration, and items
that may be out of scope for the AI-Infra repository. The roadmap helps guide
the evolution of this learning resource and sets expectations about future
content.

## 🌅 AI Native Era: The Second Half of Cloud Native (2025–2035)

The Cloud Native journey can be divided into two phases:

- **First Half (2015–2025)**: Focused on containers, microservices, and
  application delivery
- **Second Half (2025–2035)**: Focused on AI Native platform engineering,
  where models, agents, and inference workloads become first-class citizens

idea from https://mp.weixin.qq.com/s/di2HEsjLoCO4NB2Act6Qmg

### Key Paradigm Shifts

| Dimension | First Half (2015–2025) | Second Half (2025–2035, AI Native) |
| --- | --- | --- |
| Core Objects | Containers, Pods, Microservices | Models, Inference Tasks, Agents, Data Pipelines |
| Platform Goal | Stable application delivery | Continuous, efficient AI workload & Agent orchestration |
| Abstraction Layer | Deployment / Service / Ingress / Job | Model / Endpoint / Graph / Policy / Agent |
| Resource Scheduling | CPU / Memory / Node | GPU / TPU / ASIC / KV Cache / Bandwidth / Power |
| Engineering Focus | DevOps / GitOps / Platform Engineering 1.0 | AI Native Platform Engineering / AI SRE |
| Security & Compliance | Image security, CVE, Supply chain SBOM | Model security, Data security, AI supply chain & "hallucination dependencies" |
| Runtime Forms | Container + VM + Serverless | Container + WASM + Nix + Agent Runtime |

### AI Native Focus Areas

This repository is evolving to address the key challenges of the AI Native era:

| Direction | Technical Focus | Essential Difference from First Half |
| --- | --- | --- |
| **AI Native Platform** | Model/Agent as first-class citizens, unified abstraction & governance | Objects shift from services to models and inference |
| **Resource Scheduling** | DRA, heterogeneous computing, topology awareness, power & cost optimization | From static quotas to dynamic, policy-driven allocation |
| **Runtime** | Container + WASM + Nix + Agent Runtime | From "process containerization" to "execution graph containerization" |
| **Platform Engineering** | IDP + AI SRE + Security + Cost + Compliance | From tool assembly to "autonomous platforms" |
| **Security & Supply Chain** | Full-chain governance of LLM dependencies, model weights, datasets, vector DBs | Protected assets expand from images to "all AI engineering assets" |
| **Open Source & Ecosystem** | Upstream collaboration in AI Infra / Model Runtime / Agent Runtime | Not just "using open source" but "building the future in open source" |

## 🚀 Coming Soon

The following topics are planned for future addition to the repository,
organized by AI Native focus areas:

### AI Native Platform

- **Model/Agent Abstraction Patterns**: How to treat models and agents as
  first-class Kubernetes citizens, including CRD design patterns
- **Unified Model Governance**: Best practices for model versioning, rollout
  strategies, and multi-model orchestration

### Resource Scheduling

- **DRA updates**: New Dynamic Resource Allocation implementations like
  [dranet](https://github.com/google/dranet)
- **Heterogeneous Computing**: Multi-accelerator scheduling across GPU, TPU,
  NPU, and custom ASICs
- **Topology-Aware Scheduling**: GPU/network topology optimization for
  distributed training and inference
- **Power & Cost Optimization**: Energy-aware scheduling and cost models for
  AI workloads

### Runtime Evolution

- **Agent Runtime Environments**: Sandboxing and isolation patterns for AI
  agents (Agent Sandbox)
- **WASM for AI**: WebAssembly use cases in AI inference and edge deployments
- **Execution Graph Containerization**: Moving beyond process containerization
  to full inference DAG management

### Platform Engineering 2.0

- 🎓 **Weekly learning challenges & case studies**: Interactive learning
  materials to help engineers practice AI infrastructure concepts
- **Agentic Workflow development**: Deep dive into platforms like Dify, KAgent,
  or Dagger - [Issue #30](https://github.com/pacoxu/AI-Infra/issues/30)
- **AI SRE Practices**: Site reliability engineering adapted for AI workloads
- **Autonomous Platform Patterns**: Self-healing, auto-scaling, and
  self-optimizing AI infrastructure

### Hardware & Infrastructure

- **SuperNode architectures**: Coverage of large-scale AI hardware systems:
  - Huawei CloudMatrix 384 (UnifiedBus)
  - NVIDIA GB200 NVL72 (36 Grace CPUs + 72 Blackwell GPUs in rack-scale,
    liquid-cooled design)
  - 沐曦耀龙S8000 G2超节点 (Moffett YaoLong S8000 G2 SuperNode)

### Observability

- **Observability**: Advanced monitoring and metrics for AI workloads
  - eBPF for LLM (Deepflow)
  - AutoScaling Metrics and Strategies: TTFT, TPOT, ITL, etc.
  - [Issue #78](https://github.com/pacoxu/AI-Infra/issues/78)

### Model Optimization

- **Model Quantization**: Techniques for reducing model size and improving
  inference performance
- **A general/basic guide about LLM**: Covering LLM fundamentals, MoE
  architectures, Ollama, and related tools

### Security & Supply Chain

- **LLM Security & Compliance/Policy**: Security best practices and policy
  enforcement for LLM deployments
- **AI Supply Chain Security**: Model weight provenance, dataset governance,
  and "hallucination dependency" management
- **Vector Database Security**: Security patterns for embedding stores and
  retrieval systems

### Agent Communication

- **MCP and A2A**: Model Context Protocol and Agent-to-Agent communication -
  [Issue #32](https://github.com/pacoxu/AI-Infra/issues/32)

## 🚫 Out of Scope

The following topics are currently considered out of scope for this repository.
They may be valuable but are either too broad, covered extensively elsewhere,
or don't align closely with the repository's focus on Kubernetes-based AI
infrastructure:

- **General Observability Projects**: Tools like Prometheus, Grafana,
  OpenTelemetry, etc. (These are well-documented elsewhere and not
  AI-specific)
- **RAG**: Retrieval-Augmented Generation architectures and implementations

## 💬 Discussion & Contributions

For some topics, we may open dedicated issues for discussion before deciding
whether to include them. If you have suggestions for new topics or want to
contribute learning materials, please:

- Open an issue to discuss the topic
- Check existing issues for ongoing discussions
- Submit a pull request with new content that aligns with the repository's
  focus

## 📅 Update Schedule

**This roadmap is reviewed and updated every quarter** to ensure it remains
current with the rapidly evolving AI infrastructure landscape. The next
scheduled review is planned for Q1 2026.

If you notice that items on this roadmap have become outdated or if you'd like
to propose new topics, please open an issue or submit a pull request.

---

Last updated: 2025-12-01
