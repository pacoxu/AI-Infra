---
status: Active
maintainer: pacoxu
last_updated: 2026-02-25
tags: blog, kubernetes, ai-infrastructure
---

# AI-Infra Blog Posts

This directory contains blog posts and articles about AI infrastructure,
Kubernetes scheduling, and related topics.

## 2026-02-25: 贡献开源的 ROI：LF Research 2025 年调查报告解读

- [贡献开源的 ROI (Chinese)](./2026-02-25/opensource-contribution-roi_zh.md)

A Chinese blog post analyzing the Linux Foundation Research 2025 Open Source ROI
Survey, covering the business case for upstream open source contribution:

- **Hidden cost of private forks**: Organizations spending hundreds of thousands
  maintaining forks pay ongoing merge costs, delayed security patches, and
  duplicated engineering effort
- **Three core benefits of upstream contribution**: Faster security response,
  accelerated development velocity, stronger talent attraction and retention
- **Quantified ROI**: Average cost-benefit ratio of 2-5x; contributing
  organizations achieve an estimated **6x ROI** per the quantitative model
- **AI infrastructure context**: How the findings apply to Kubernetes, vLLM,
  DRA/NRI, and other fast-moving open source ecosystems
- **Practical recommendations**: Upstream-first strategy, dedicated contribution
  time, performance incentives for open source engagement

## 2026-02-14: 关注 AAIF 进展：Agentic AI Foundation 及其旗下活动预告

- [AAIF Introduction (Chinese)](./2026-02-14/aaif-introduction_zh.md)

A comprehensive introduction to the Agentic AI Foundation (AAIF) and its
upcoming flagship events:

- **AAIF Overview**: A neutral, open foundation ensuring AI Agent capabilities
  evolve transparently and collaboratively
- **AGNTCon + MCPCon 2026**: October 22-23 in San Jose, CA - The flagship
  annual conference expanding beyond MCP to the entire open agentic AI ecosystem
- **MCP Dev Summit North America 2026**: April 2-3 in New York City - Premier
  gathering for developers advancing AI agents with Model Context Protocol
- Why AAIF matters: Open standards, community collaboration, open source support
- How to participate in the AAIF community

## 2026-01-15: 推理平台实践与 AI 成本优化

- [Inference Cost Optimization (Chinese)](./2026-01-15/inference-cost-optimization_zh.md)

A comprehensive guide to cost optimization strategies for AI inference
platforms (MaaS - Model as a Service):

- Five core optimization strategies:
  - **Reduce Invalid Tokens**: Prompt template management, output length
    control, structured output constraints, Agent governance, RAG quality
    improvement
  - **Faster Computation**: Dynamic batching, parallelism, kernel optimization,
    speculative decoding, quantization
  - **Increase Utilization**: Backlog-based autoscaling, mixed deployment,
    peak-valley strategies
  - **Lower Resource Costs**: Hardware selection, deployment form optimization,
    spot instances, next-gen hardware (CXL, AI-native storage)
  - **Quality-Cost Strategies**: Intelligent routing, multi-level degradation,
    tiered SLO & budget
- Cluster scale optimization branches: Small (1-8 GPUs), Medium (8-64 GPUs),
  Large (64+ GPUs)
- Cost observability and implementation roadmap
- References to NVIDIA Inference Context Memory Storage Platform and industry
  best practices
- Links to detailed inference documentation: caching, prefill-decode
  disaggregation, model lifecycle, AIBrix platform

## 2026-01-12: KubeCon + CloudNativeCon Europe 2026 主题推荐

- [KubeCon EU 2026 Recommendations (Chinese)](./2026-01-12/kubecon-eu-2026-recommendations_zh.md)

A comprehensive guide to KubeCon + CloudNativeCon Europe 2026 with curated AI infrastructure session recommendations:

- Translation of CNCF official announcement
- Conference schedule links (main event and co-located events)
- Four recommended AI infrastructure sessions:
  - BYD's million-task scale journey with Argo Workflows (比亚迪百万任务规模实践)
  - KV-Cache Tutorial: Building AI-Aware LLM Routing on Kubernetes
  - Adaptive Routing for AI Inference Workloads
  - Redefining LLM Inference SLI/SLO (重新定义推理 SLI/SLO)
- Session details with time, location, speakers, and descriptions in Chinese
- Links to conference schedules and registration

## 2026-01-07: Ambient Global Compute — Orchestrating the Non-Elastic Cloud

- [Ambient Global Compute 中文博客](./2026-01-07/ambient-global-compute_zh.md)

A comprehensive blog post about orchestrating the non-elastic cloud with
Kubernetes, based on Jago Macleod's KubeCon presentation:

- Infrastructure pendulum: From colocation to virtualization to elastic cloud
  to non-elastic cloud
- The golden age of cloud computing with infinite capacity
- Three drivers of change: Hardware fragmentation, regional expansion, GPU
  scarcity
- The return of CapEx and operational inversion
- Four pillars of Ambient Compute: Workload orchestration, Kueue, priority
  awareness, global dispatch
- Utilization vs latency conflict resolution
- Two practical patterns: Global batch computer and elastic platform on fixed
  hardware
- MultiKueue for global capacity scheduling
- KubeCon NA 2025 presentation reference

## 2025-12-22: OCI Is Quietly Taking Over Everything

- [OCI Taking Over Everything (English)](./2025-12-22/oci-taking-over-everything_en.md)
- [OCI 正在悄悄占领一切 (Chinese)](./2025-12-22/oci-taking-over-everything_zh.md)

A comprehensive analysis of how OCI (Open Container Initiative) is becoming
the unified distribution backbone for images, Helm charts, AI models, and WASM
in the AI era, referencing KubeCon Atlanta insights:

- OCI evolution: From container images to universal artifact distribution
- Why AI workloads amplify the need for OCI (size, governance, unification)
- Kubernetes v1.35: OCI Image Volumes enabled by default (Beta)
- ModelPack: Making AI models first-class OCI citizens
- Harbor v2.14.0: Enhanced CNAI model integration
- Docker Model Runner: Unifying inference engines (llama.cpp, vLLM) with OCI
- ORAS: Swiss Army knife for OCI artifacts
- WASM artifact registries: Next unification puzzle piece
- Industry signals: Bitnami policy changes, Docker Hardened Images (DHI)
- Performance evolution: containerd v2.2 Rebase Snapshot
- Practical adoption roadmap for enterprises

## 2025-12-22: vLLM 2025 Retrospective & 2026 Roadmap

- [vLLM 2025 Retro & 2026 RoadMap (English)](./2025-12-22/vllm-2025-retro-2026-roadmap_en.md)
- [vLLM 2025 年度回顾与 2026 年路线图 (Chinese)](./2025-12-22/vllm-2025-retro-2026-roadmap_zh.md)

A comprehensive summary of vLLM's achievements in 2025 and vision for 2026,
based on vLLM Office Hours #38:

- vLLM project overview: 65K+ stars, 800+ PRs/month, 2000+ contributors
- 2025 growth highlights: 80% Q1/Q2 growth, 30% Q3 growth
- API evolution: Agentic AI and RL support with native framework integration
- Model ecosystem: 100+ architectures, Transformers backend, SOTA vision models
- Engine revamp: V1 core architecture with hybrid allocator and KV connector
- Hardware ecosystem: TPU, Ascend, Neuron, Gaudi, OpenVINO support
- Distributed capabilities: DeepSeek 2.2k tok/s case, vLLM Router release
- 2026 focus: Stability, accuracy, performance, frontier models, hardware
  stability

## 2025-12-17: GPU Fault Detection and Self-Healing in Kubernetes

- [GPU 故障检测与自愈实践指南 (Chinese)](./2025-12-17/gpu-fault-detection_zh.md)

A practical guide for AI infrastructure engineers and SREs on detecting,
diagnosing, and automatically recovering from GPU hardware failures in
Kubernetes clusters:

- Four types of GPU failures: card dropout, link failures, memory errors, driver
  failures
- Detection approaches: DCGM Exporter, Node Problem Detector, NVIDIA Debug
  Guidelines
- Three-layer fault semantics: NodeCondition, DeviceCondition, WorkloadCondition
- Progressive remediation strategy: 6-level escalation (L0-L6)
- Fault-aware scheduling: GPU health scoring and integration with Kueue/Volcano
- Job-level attribution: DCGM HPC job mapping for fair billing
- Production deployment phases and best practices
- References from ByteDance Volcano, Microsoft AKS, and NVIDIA

## 2025-12-17: DRANET — Community-Driven Kubernetes Network Driver

- [DRANET 介绍 (Chinese)](./2025-12-17/dranet-kubernetes-network-driver_zh.md)

A comprehensive blog post about DRANET (Dynamic Resource Allocation Network),
the community-driven evolution of the Kubernetes network driver, combining
KubeCon NA 2025 keynote and research paper content:

- DRANET overview: DRA-based network driver with topology-aware resource
  management
- New ecosystem emerges: AI/ML, HPC, and Telco driving network innovation
- DRA as common language: Unified resource allocation framework
- Convergence of ideas: From CNI Spec (2015) to Network Drivers (2025)
- Topology lottery problem: Performance bottlenecks in traditional networking
- Solution: Topology-aware scheduling with DRA + NRI
- Performance results: Up to 59.6% improvement in NCCL benchmarks
- Composable architecture for high-performance networking
- Project donated to kubernetes-sigs organization
- IEEE LCN 2025 paper and KubeCon NA 2025 keynote references

## 2025-12-15: ByteDance's Solution for Ultra-Large-Scale Kubernetes Clusters

- [ByteDance Large-Scale K8s (English)](./2025-12-15/bytedance-large-scale-k8s.md)
- [字节跳动超大规模 K8s 方案 (Chinese)](./2025-12-15/bytedance-large-scale-k8s_zh.md)

A comprehensive overview of ByteDance's solutions for ultra-large-scale
Kubernetes clusters:

- **KubeBrain**: Alternative metadata storage system supporting 20,000+ node
  clusters
- **KubeAdmiral**: Next-generation multi-cluster orchestration and scheduling
  engine
- **Gödel Scheduler**: Unified scheduling architecture for large-scale clusters
- **Katalyst**: Resource management system for improved utilization and QoS
- Multi-cluster vs single-cluster trade-offs
- KubeCon China 2025 presentations and technical blog references
- Open-source projects and GitHub repositories

## 2025-12-15: From SQL on CPUs to Inference on GPUs

- [SQL to Inference Evolution (English)](./2025-12-15/sql-to-inference.md)
- [SQL 到推理演进 (Chinese)](./2025-12-15/sql-to-inference_zh.md)

A comprehensive blog post about the transformation of AI data processing
based on PyTorchCon 2025 presentation by Robert Nishihara (Anyscale):

- New workloads: AI data processing evolution from SQL on CPUs to inference
  on GPUs
- Paradigm shift in data types: From tabular to multimodal data (images,
  video, audio, text, sensors)
- The PARK stack: PyTorch + AI + Ray + Kubernetes as the new AI infrastructure
  standard
- Co-evolution of vLLM + Ray: Why nearly every RL framework uses Ray as
  orchestrator
- Ray + Kubernetes integration: Complementary strengths for AI workloads
- RL/Post-training architecture and orchestration requirements
- Real-world adoption across research labs, tech companies, and cloud providers
- Comparison to LAMP stack defining the web era

## 2025-12-15: Multi-Tenancy Isolation in AI Infra Era

- [Multi-Tenancy Isolation (English)](./2025-12-15/multi-tenancy-isolation.md)
- [多租户隔离性方案探讨 (Chinese)](./2025-12-15/multi-tenancy-isolation_zh.md)

A comprehensive guide to multi-tenant isolation solutions in Kubernetes for the
AI infrastructure era:

- Public cloud vs private cloud considerations for training and inference
- Comparison table across dimensions: use cases, resources, cost, scheduling,
  data, SLO, security, challenges
- Container security isolation strategies: cluster isolation, node pools,
  sandboxed runtimes (gVisor, Kata)
- Agent Sandbox warm pool patterns and security strategies
- Confidential Containers for sensitive AI workloads
- Network and storage isolation best practices
- Multicluster application management with CNCF MCM Radar 2024Q3
- Multitenancy spectrum: from namespaces to dedicated clusters

## 2025-12-08: Agones — Kubernetes-Native Game Server Hosting

- [Agones Project Introduction (English)](./2025-12-08/agones.md)
- [Agones 项目介绍 (Chinese)](./2025-12-08/agones_zh.md)

A comprehensive introduction to Agones as it applies to join CNCF Sandbox,
covering the project's positioning and vision:

- What is Agones and why it exists
- Core features: GameServer CRD, Fleet management, autoscaling, client SDKs
- Architecture and design: Custom resources and lifecycle management
- Use cases: Session-based multiplayer, persistent worlds, esports
- Production adoption by major gaming companies
- Why CNCF and cloud-native integration
- Project governance and community
- Vision and roadmap for gaming infrastructure on Kubernetes

## 2025-12-08: GKE 65,000 Node Support — Benchmarking AI Workloads at Scale

- [GKE 65K Nodes (Chinese)](./2025-12-08/gke-65k-nodes_zh.md)

A comprehensive translation of Google Cloud's blog posts about GKE's
achievement of supporting 65,000 nodes for AI workloads:

- 65K nodes cluster architecture and design
- Scheduler optimization for large-scale clusters
- Mixed workload support: 50K training pods + 15K inference pods
- Workload isolation with preemption mechanism
- Fault recovery capabilities and StatefulSet guarantees
- Performance benchmarks: Pod startup time and API server performance
- Control plane optimization for ultra-large scale
- Network optimization with VPC-native networking
- AI training and inference use cases
- KubeCon NA keynote reference: "Kubernetes in the Second Decade"
- Community contributions and upstream improvements

## 2025-12-05: How the Kubernetes Community Operates — Entry Points in the AI Era

- [Kubernetes Community Operations (English)](./2025-12-05/kubernetes-community-operations.md)
- [Kubernetes 社区运作方式 (Chinese)](./2025-12-05/kubernetes-community-operations_zh.md)

A comprehensive guide to understanding how the Kubernetes community is
structured and where to find entry points in the AI era:

- Community structure: CNCF, Steering Committee, SIGs/WGs, Subprojects
- The contributor ladder: From non-member to SIG Chair
- Current SIGs, WGs, and Committees as of late 2024
- AI/ML working groups: Batch, Serving, Device Management, AI Gateway, AI
  Integration
- New contributor orientation resources
- AI/ML-specific entry points and opportunities
- Community statistics: 97.8k contributors, 4.63M contributions, 8.6k reviewers

## 2025-12-03: Ant Group Large-Scale Cluster — 50% Memory Reduction at 20K Nodes

- [Ant Group Large-Scale K8s (English)](./2025-12-03/ant-group-large-scale-k8s.md)
- [蚂蚁大规模集群经验 (Chinese)](./2025-12-03/ant-group-large-scale-k8s_zh.md)

A comprehensive overview of Ant Group's large-scale Kubernetes cluster
experiences at 20,000+ nodes:

- Etcd splitting practice (2022): Reducing operational time from 1-2 hours
  to 10 minutes
- Large-scale Kubernetes service breakthroughs in the digital intelligence era
- API Server memory optimization: 50% memory reduction with zero-intrusion
  architecture
- KoM (Kubernetes on Mesh) gateway for unified traffic management
- Resource grouping strategy: Pod, Config, Event, Default groups
- Performance improvements: CPU -30%, ETCD storage -20%, throughput +40%
- Container delivery optimizations: 95% faster application startup
- E2E diagnostics and self-healing with 80%+ L1 interception rate

## 2025-12-02: KCD Hangzhou — Observability Optimization at Scale

- [KCD Hangzhou Observability (English)](./2025-12-02/kcd-hangzhou-observability.md)
- [KCD 杭州可观测性优化 (Chinese)](./2025-12-02/kcd-hangzhou-observability_zh.md)

A blog post covering the hottest observability topics from KCD Hangzhou +
OpenInfra Days China 2025 and KubeCon NA 2025:

- Xiaohongshu (RED) large-scale metrics monitoring optimization
- 10x query speedup and tens of thousands of CPU cores saved
- Collection layer restructuring based on vmagent
- High availability improvements and cross-cloud multi-active deployment
- Computation push-down and pre-aggregation for query acceleration
- OpenAI's Fluent Bit optimization: 30,000 CPU cores freed with one line of code
- Profiling insights using Linux Perf

## 2025-12-01: Kubernetes Safe Upgrade and Rollback

- [Safe Upgrade and Rollback (English)](./2025-12-01/safe-upgrade-rollback.md)
- [安全升级与回滚 (Chinese)](./2025-12-01/safe-upgrade-rollback_zh.md)

A comprehensive guide to Kubernetes safe upgrade and rollback capabilities
based on the Google Cloud blog and KubeCon NA 2025 keynote:

- Emulation Version (`--emulation-version`) available in Kubernetes 1.31+
- Minimum Compatibility Version (`--min-compatibility-version`) in 1.35+
- KEP-4330: Compatibility Versions
- GKE reliability: 99.98% upgrade success rate
- Three stages of upgrade readiness
- Best practices for safe upgrades and rollback procedures

## 2025-12-01: Inference Orchestration Solutions

- [Inference Orchestration (English)](./2025-12-01/inference-orchestration.md)
- [推理编排 (Chinese)](./2025-12-01/inference-orchestration_zh.md)

An overview of current open-source inference orchestration solutions and
convergence trends:

- Workload solutions: dual LWS (llm-d), Serving Group (Kthena), StormService
  (AIBrix), Dynamo Grove/LWS, RBG
- Convergence trends in the ecosystem
- When PD disaggregation truly provides value
- AIConfigurator for configuration optimization
- Recommendations for new and existing deployments

## 2025-12-01: AWS 10K Node EKS Ultra Scale Clusters

- [AWS 10K Node Clusters (English)](./2025-12-01/aws-10k-node-clusters.md)
- [AWS 万节点集群 (Chinese)](./2025-12-01/aws-10k-node-clusters_zh.md)

A follow-up to Google's 130K node cluster, covering AWS EKS ultra-scale
optimizations:

- Community improvements: Kubernetes v1.33 read/list cache, Karpenter
- AWS-specific: QLDB journal for etcd, BoltDB on tmpfs
- Image acceleration: SOCI Snapshotter for lazy loading
- AI workloads: LWS + vLLM, CoreDNS autoscaling
- Performance SLOs: 1s for gets/writes, 30s for lists, 500 pods/second

## 2025-11-28: Agent Sandbox — Secure AI Agents on Kubernetes

- [Agent Sandbox (English)](./2025-11-28/agent-sandbox.md)
- [Agent Sandbox (Chinese)](./2025-11-28/agent-sandbox_zh.md)

A comprehensive guide to Agent Sandbox, a Kubernetes SIG Apps project for
secure AI agent execution, covering:

- Project introduction and Sandbox CRD
- gVisor (GKE) integration status
- Kata Containers integration status
- SandboxWarmPool for sub-second startup latency
- Use cases for AI agents, development environments, and notebooks
- Industry trends and future directions

## 2025-11-26: JobSet In-Place Restart — 92% Faster Recovery

- [JobSet In-Place Restart (English)](./2025-11-26/jobset-in-place-restart.md)
- [JobSet In-Place Restart (Chinese)](./2025-11-26/jobset-in-place-restart_zh.md)

A blog post about JobSet leveraging Kubernetes In-Place Container Restart
(Co-Evolving theme), covering:

- Co-Evolving concept: Kubernetes features empowering the ecosystem
- In-Place Container Restart capability (KEP-5307 in 1.34, KEP-5532 in 1.35)
- Real-world results: Restart time from 2m10s to 10s (92% faster) on 5000 nodes
- Benefits for distributed training, job dependencies, and resource efficiency
- Integration considerations and future roadmap

## 2025-11-26: cgroup v2 Migration Guide

- [cgroup v2 Migration Guide (English)](./2025-11-26/cgroup-v2.md)
- [cgroup v2 Migration Guide (Chinese)](./2025-11-26/cgroup-v2_zh.md)

A comprehensive guide to cgroup v2 migration for Kubernetes users, covering:

- Kubernetes 1.31 maintenance mode and 1.35 deprecation announcement
- cgroup v1 vs v2 differences and technical improvements
- Historical timeline and kernel/controller evolution
- cgroup v2 hierarchy and controller details (CPU, memory, IO, PSI)
- Migration guidance with runc (1.3.2+) and crun (1.23+) recommendations
- kubeadm upgrade warnings for cgroup v1 environments

## 2025-11-25: Topology-Aware Scheduling

- [Topology-Aware Scheduling (English)](./2025-11-25/topology-aware-scheduling.md)
- [Topology-Aware Scheduling (Chinese)](./2025-11-25/topology-aware-scheduling_zh.md)

A comprehensive guide to topology-aware scheduling for AI workloads, covering:

- Background on current topology scheduling (Device Plugin, Kueue, Volcano)
- DRA topology management with GPU + NIC coordination
- DRAConsumableCapacity feature in Kubernetes 1.34
- Migration challenges from Device Plugin to DRA
- KubeCon NA 2025 insights and resources

## 2025-11-25: Gang Scheduling

- [Gang Scheduling Blog (English)](./2025-11-25/gang-scheduling.md)
- [Gang Scheduling Blog (Chinese)](./2025-11-25/gang-scheduling_zh.md)

A comprehensive overview of gang scheduling and workload-aware scheduling
coming to Kubernetes v1.35, covering:

- Workload API (Alpha)
- Gang Scheduling (Alpha)
- Opportunistic Batching (Beta)
- Kubernetes 1.36 roadmap
- Real-world use cases for AI/ML workloads

## Contributing

To add a new blog post:

1. Create a new directory with the date: `YYYY-MM-DD/`
2. Add your blog post as `topic-name.md` (English)
3. Optionally add a Chinese translation as `topic-name_zh.md`
4. Follow the metadata format used in existing posts
5. Ensure all markdown passes `markdownlint` validation
6. Update this README with a link to your post
