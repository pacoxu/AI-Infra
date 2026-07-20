---
status: Active
maintainer: pacoxu
last_updated: 2026-07-13
tags: blog, kubernetes, ai-infrastructure
---

# AI-Infra Blog Posts

Older posts have been archived to [docs/archive-blog](../archive-blog/README.md).

This directory contains blog posts and articles about AI infrastructure,
Kubernetes scheduling, and related topics.

## 2026-06-15: KEP-766 DisaggregatedSet 深入解读：为何对 AI 工作负载重要

- [KEP-766 DisaggregatedSet 深入解读：为何对 AI 工作负载重要 (Chinese)](./2026-06-15/2026-06-15-kep-766-disaggregatedset-ai-workloads_zh.md)

A Chinese architecture-focused analysis of `KEP-766 DisaggregatedSet`, updated
with the post-issue upstream reality that LWS `v0.9.0` already includes the
proposal, implementation, controller, and Helm integration work:

- **Problem definition**: explains why manually coordinating multiple
  `LeaderWorkerSet` resources becomes fragile for prefill/decode and other
  multi-role inference services.
- **API and rollout model**: breaks down `spec.roles`,
  `LeaderWorkerSetTemplateSpec`, role/revision labels, and the N-dimensional
  rolling update algorithm.
- **AI workload impact**: connects coordinated revision management,
  per-revision headless Services, and role-level resource differences back to
  production inference operations.
- **Scope boundaries**: separates `DisaggregatedSet` from higher-level
  platforms such as `KServe + llm-d`, `AIBrix`, `Kthena`, `Dynamo/Grove`, and
  broader role APIs such as `RBG`.

## 2026-05-21: Kubernetes Scheduler 演进主线：从 Predicates/Priorities 到 Scheduling Framework，再到 Workload-Aware Scheduling

- [Kubernetes Scheduler 演进主线：从 Predicates/Priorities 到 Scheduling Framework，再到 Workload-Aware Scheduling (Chinese)](./2026-05-21/2026-05-21-kubernetes-scheduler-framework-evolution_zh.md)

A Chinese architecture-focused retrospective on how `kube-scheduler` evolved
from built-in predicates/priorities into a plugin framework and then toward
workload-level scheduling:

- **Three-stage arc**: frames scheduler history as `Predicates/Priorities +
  Extenders` -> `Scheduling Framework` -> `Workload-Aware Scheduling`.
- **Framework-centered narrative**: uses `KEP-624` and the classic extension
  points diagram as the core explanatory device, instead of turning the piece
  into release-note enumeration.
- **Why `v1.16-v1.20` matters**: explains why that period works as a practical
  "framework formation phase" for writing, while still distinguishing that from
  the official `v1.19` stable milestone.
- **Why this still matters**: connects `profiles`, queue behavior, and
  `v1.35/v1.36` workload-aware scheduling back to the original framework
  design.

## 2026-05-18: Cache Offload 深入：Run:ai Model Streamer、Dynamo ModelExpress 与大模型加载加速

- [Cache Offload 深入：Run:ai Model Streamer、Dynamo ModelExpress 与大模型加载加速 (Chinese)](./2026-05-18/2026-05-18-model-streamer-modelexpress-model-loading-zh.md)

A Chinese production-oriented analysis of the model-weight loading path behind
LLM cold starts:

- **Separates weights from KV cache**: clarifies why model loading and runtime
  KV-cache offload have different lifecycle and failure semantics.
- **Three-path comparison**: compares prefetch/hierarchical caching, Run:ai
  Model Streamer, and Dynamo ModelExpress by data path and operating boundary.
- **First replica plus fleet scale-out**: positions Model Streamer for
  object-storage-to-GPU loading and ModelExpress for NIXL/RDMA reuse from an
  existing worker.
- **vLLM and Dynamo examples**: includes current `runai_streamer`, sharded
  loading, and unified `mx` configuration paths.
- **Production guardrails**: covers readiness, identity, immutable model
  versions, compatibility, fallback paths, and cold/warm/scale-out benchmarks.

## 2026-05-13: 推理编排方案如何选择？AIBrix、Kthena、Dynamo、llm-d、KServe、vLLM Production Stack 与 SGLang/RBG

- [推理编排方案如何选择？AIBrix、Kthena、Dynamo、llm-d、KServe、vLLM Production Stack 与 SGLang/RBG (Chinese)](./2026-05-13/2026-05-13-how-to-choose-inference-orchestration-stacks_zh.md)
- [How to choose an inference orchestration stack: AIBrix, Kthena, Dynamo, llm-d, KServe, vLLM Production Stack, and SGLang/RBG](./2026-05-13/2026-05-13-how-to-choose-inference-orchestration-stacks.md)

A bilingual update of the earlier inference orchestration theme, reframed
around stack layers rather than project names:

- **Do not compare unlike layers**: separates runtime, serving stack, control
  plane, and workload primitive before comparing projects.
- **Latest public progress**: updates `KServe + llm-d`, `AIBrix`, `Kthena`,
  `Dynamo/Grove`, `vLLM Production Stack`, and `SGLang/RBG` to reflect their
  current public positioning as of 2026-05-13.
- **Infrastructure-first decision guide**: gives a practical selection path for
  Volcano, KServe, vLLM, NVIDIA, vanilla Kubernetes, and SGLang users.
- **PD is still conditional**: keeps the warning that prefill/decode
  disaggregation is a systems tradeoff, not an automatic win.

## 2026-05-11: NVIDIA 推理编排主线拆解：Dynamo、Grove、KAI Scheduler 与 GPU DRA Driver

- [NVIDIA 推理编排主线拆解：Dynamo、Grove、KAI Scheduler 与 GPU DRA Driver (Chinese)](./2026-05-11/2026-05-11-dynamo-grove-kai-dra-ecosystem-zh.md)

A Chinese ecosystem analysis that zooms in from the broader NVIDIA open source
landscape to the orchestration path around Dynamo:

- **Not four competing projects**: frames `Dynamo -> Grove -> KAI Scheduler -> GPU DRA Driver`
  as one vertical architecture from serving intent to hardware topology.
- **Why Grove matters**: explains Grove as the workload abstraction layer for
  multi-role disaggregated inference, not just another controller.
- **Why KAI matters**: highlights topology-aware scheduling, hierarchical
  PodGroups, DRA support, and fairshare as the execution layer for AI clusters.
- **Why DRA matters now**: connects upstream DRA progress in Kubernetes 1.35/1.36
  to NVIDIA's `ComputeDomain` and future GPU-sharing semantics.
- **Where NIXL, NCCL, and AICR fit**: positions `NIXL/NCCL` as the data movement
  and GPU communication layer, and `AICR/GPU Operator` as cluster baseline and
  operations support rather than the orchestration core itself.
- **Where LWS and vLLM fit**: positions `LWS + Volcano` as the official
  community-native path, and notes `Koordinator` can play a similar scheduling
  role when teams already standardize on it; `vLLM` remains engine/data-plane
  rather than the same layer as Grove/KAI/DRA.

## 2026-05-04: 大规模 GPU 调度：拓扑、队列、公平性的系统化实践

- [大规模 GPU 调度：拓扑、队列、公平性的系统化实践 (Chinese)](./2026-05-04/2026-05-04-large-scale-gpu-scheduling-topology-queue-fairness_zh.md)

A Chinese platform-oriented draft that connects topology-aware GPU placement
with queue admission, quota, fair sharing, preemption, DRA, HAMi, and
fault-aware scheduling:

- **Workload-first framing**: explains why large-scale GPU scheduling should
  start from workload admission and queue fairness rather than single-Pod
  placement.
- **Single-cluster baseline**: recommends `Kueue + kube-scheduler + DRA/HAMi`
  before introducing a replacement scheduler or deeper scheduler customization.
- **Project role split**: compares Kueue, DRA, HAMi, Volcano, KAI Scheduler,
  and Koordinator by scheduling responsibility and operating boundary.
- **Decision matrix**: gives platform signals for when to stay simple and when
  topology, fairshare, gang, preemption, or colocation pressure justifies a
  more complex scheduling path.

## 2026-04-28: 如何理解 Hugging Face、私有 Hugging Face、MatrixHub、Harbor + Dragonfly + ModelPack 与 ModelExpress

- [如何理解 Hugging Face、私有 Hugging Face、MatrixHub、Harbor + Dragonfly + ModelPack 与 ModelExpress (Chinese)](./2026-04-28/2026-04-28-understanding-model-distribution-stack_zh.md)

A Chinese architecture-oriented article that places public model hubs, private
model hubs, OCI-first artifact stacks, node-level P2P distribution, and
runtime weight transfer into a single model distribution view:

- **Layered framing**: separates public model sources, enterprise governance,
  node distribution, and runtime acceleration.
- **Scenario-driven comparison**: explains when to prefer MatrixHub, when to
  prefer Harbor + ModelPack + Dragonfly, and when ModelExpress becomes the
  right answer.
- **One-stack diagram**: provides a Mermaid overview covering Hugging Face,
  ModelScope, MatrixHub, Harbor, Dragonfly, ModelPack, and ModelExpress.

## 2026-04-23: Kubernetes v1.36 DRA 整体设计

- [Kubernetes v1.36 DRA 的整体设计：从请求入口到调度、状态与拓扑 (Chinese)](./2026-04-23/2026-04-23-kubernetes-v1.36-dra-ai-infra_zh.md)

A Chinese architecture analysis based on the Kubernetes v1.36 DRA KEP map:

- **Architecture map**: organizes DRA by request entry points, resource
  modeling, scheduling and binding, status, observability, and admin
  boundaries.
- **Official DRA blog follow-up**: now also folds in the upstream 2026-05-07
  DRA blog and links the recent v1.33 -> v1.34 -> v1.36 progression into the
  same article.
- **Topology focus**: highlights why GPU/NIC, NUMA, PCIe, fabric, and
  supernode placement reshape the scheduler problem.
- **Maturity and next steps**: adds a v1.37 follow-up watchlist plus KEP and
  open-issue limitation tables, separating practical v1.36 capabilities from
  DRA+WAS and other still-open design directions.

## 2026-04-15: Kubernetes v1.34 PSI Metrics Beta（AI-Infra 落地）

- [Kubernetes v1.34 PSI Metrics Beta：AI-Infra 该如何落地 (Chinese)](./2026-04-15/2026-04-15-kubernetes-v1.34-psi-metrics-beta-ai-infra_zh.md)

A Chinese practical guide focused on operationalizing PSI metrics in AI
clusters after KEP-4205 moved to Beta:

- **From kernel to platform signal**: maps Linux PSI into kubelet Summary API
  and `/metrics/cadvisor` collection paths.
- **Actionable observability**: highlights the six PSI Prometheus metrics and
  proposes node/workload alert starting points.
- **AI-oriented closed loop**: links PSI pressure to scheduling and scaling
  decisions instead of keeping it dashboard-only.

## 2026-04-15: VolumeGroupSnapshot + CBT for AI Checkpoints

- [用 VolumeGroupSnapshot + CBT 改善 AI Checkpoint 备份与恢复 (Chinese)](./2026-04-15/2026-04-15-volume-group-snapshot-and-cbt-for-ai-checkpoints_zh.md)

A Chinese implementation note that combines KEP-3476 and KEP-3314 for AI
training backup and recovery:

- **Consistent multi-volume recovery point**: uses VolumeGroupSnapshot for
  crash-consistent checkpoints across PVC groups.
- **Incremental backup path**: introduces changed-block tracking (CBT) to avoid
  repeated full-volume transfers.
- **Production rollout framing**: includes driver capability checks, phased
  adoption, and restore-first validation guidance.

## 2026-04-13: AI 训练作业管理：JobSet、Kueue、Ray 与 Gang Scheduling

- [AI 训练作业管理：JobSet、Kueue、Ray 与 Gang Scheduling (Chinese)](./2026-04-13/2026-04-13-ai-training-job-management-jobset-kueue-ray-gang_zh.md)

A Chinese architecture note that separates training job orchestration into
workload topology, queue admission, runtime execution, and gang scheduling:

- **Boundary-first comparison**: explains why `JobSet`, `Kueue`, `KubeRay`, and
  `Gang Scheduling` are complementary layers rather than direct alternatives.
- **Reference architecture**: shows how a multi-team platform can submit
  `JobSet`, `RayJob`, or other training CRDs through Kueue before Pod creation.
- **Practical guidance**: recommends `JobSet + Kueue` for static distributed
  training and `KubeRay + Kueue` for Ray Train/Tune/RL workloads.
- **Fact check**: records current release versions and KEP-4671 stage/milestone
  information as of 2026-07-11.

## 2026-04-06: GPU Pod 冷启动优化：AI 工作负载的性能突破

- [GPU Pod 冷启动优化：AI 工作负载的性能突破 (Chinese)](./2026-04-06/2026-04-06-gpu-pod-cold-start-optimization_zh.md)

A Chinese practical deep dive that extends the AI startup critical-path model
from PR #281 into production scenarios:

- **Critical-path + economics**: combines startup decomposition with tenant-level
  warm-pool cost modeling.
- **Model loading first**: prioritizes Run:ai Model Streamer and cache
  orchestration (Fluid) before micro-level scheduler tuning.
- **Capacity-aware scaling**: links large-cluster scheduling patterns with
  cold-start budget control under multi-tenant AI workloads.
- **Not only acceleration**: introduces workaround paths (VPA and in-place Pod
  container restarts in v1.35) to reduce unnecessary full cold starts.

## 2026-04-01: Kubernetes Swap Status in 2026

- [Kubernetes Swap Status in 2026: kubelet behavior, memory pressure, and what is next](./2026-04-01/2026-04-01-kubernetes-swap-status-kubelet-and-memory-pressure.md)
- [Kubernetes Swap 现状（2026）：kubelet 行为、内存压力与场景化落地 (Chinese)](./2026-04-01/2026-04-01-kubernetes-swap-status-kubelet-memory-pressure_zh.md)

An up-to-date status summary of Kubernetes swap support with a practical
operations lens:

- **Current status**: KEP-2400 is implemented and closed; NodeSwap is GA in 1.34
- **kubelet behavior today**: `NoSwap` vs `LimitedSwap`, Linux + cgroup v2 path
- **Operational focus**: observability endpoints, `kubectl top --show-swap`,
  and memory-pressure tuning boundaries
- **Roadmap gap**: workload-controlled swap, swap-aware scheduling, and
  swap-aware evictions tracked in #5359/#5424/#5433
- **Scenario-oriented guidance**: converts conference materials into concrete
  rollout scenarios (cost density, memory spikes, control-plane protection,
  and fine-grained policy exploration)

## 2026-03-24: Maintenance Scan (Outdated Resources + Safe Upgrades)

Implemented in this cleanup:

- Standardized blog filenames to `YYYY-MM-DD-topic-name(_lang).md` to reduce
  ambiguity in cross-references and search indexing.
- Removed duplicate long-form blog listings from top-level READMEs and kept the
  full archive in this file as the canonical index.
- Removed Agones posts and all corresponding index references.

Safe upgrade proposals for follow-up:

- Add a lightweight markdown link checker in CI for `docs/blog/**`.
- Run a quarterly metadata refresh (`last_updated`, canonical links, and stale
  external references).

## 2026-03-24: vLLM v0.18.0 发布解读：AI-Infra 视角的重点变化

- [vLLM v0.18.0 发布解读：AI-Infra 团队值得重点关注什么？ (Chinese)](./2026-03-24/2026-03-24-vllm-v0.18.0-ai-infra-highlights_zh.md)

A Chinese analysis of vLLM v0.18.0 release notes from an AI infrastructure
operations perspective:

- **Serving interface expansion**: New `--grpc` serving mode and
  `vllm launch render` for GPU-less preprocessing
- **Memory hierarchy upgrades**: Smarter KV offloading, FlexKV backend, and
  multi-KV-group offloading support
- **Large-scale MoE serving**: Elastic EP Milestone 2 with NIXL-EP and faster
  expert loading path
- **Operational risk gating**: Known Qwen3.5 + FP8 KV cache accuracy issue on
  B200, plus dependency/default behavior changes
- **Rollout checklist**: Concrete canary and upgrade checks for platform teams

## 2026-03-13: NVIDIA AICR：把 GPU 集群安装经验固化成可复现 Recipe

- [NVIDIA AICR 中文介绍](./2026-03-13/2026-03-13-nvidia-aicr-introduction_zh.md)

A Chinese introduction to NVIDIA AI Cluster Runtime (AICR), based on the
project's official repository and the recently merged AI-Infra PR:

- **What AICR is**: A recipe-driven tool for optimized, validated, and
  reproducible GPU-accelerated Kubernetes cluster setups
- **Why it matters**: Turns fragile platform runbooks into version-locked,
  auditable deployment artifacts for Helm and GitOps workflows
- **Core workflow**: `snapshot` captures live state, `recipe` defines the
  target, `validate` checks drift, and `bundle` renders deployable outputs
- **How to position it**: AICR sits above GPU Operator and complements DRA,
  focusing on cluster baseline management rather than device allocation
- **Current scope**: Early-stage but promising support for EKS, GKE, Kind,
  H100/GB200, Ubuntu, Kubeflow, and Dynamo

## 2026-03-13: 【2020】拜耳作物科学以 15,000 节点的 GKE 集群为未来播种

- [Bayer Crop Science and a 15K-Node GKE Cluster (Chinese)](./2026-03-13/2026-03-13-bayer-gke-15000-nodes_zh.md)

A Chinese translation and retrospective on Google Cloud's November 17, 2020
case study about Bayer Crop Science scaling GKE to 15,000 worker nodes:

- **Why 1K nodes was not enough**: Route-based networking and VPC route scale
  became the practical ceiling for older cluster designs
- **Key product change**: VPC-native GKE with Alias IP removed per-node route
  dependence and unlocked larger clusters
- **Regional cluster improvement**: Custom subnet mode enabled more precise
  per-zone IP planning for large regional deployments
- **Outcome**: Single-cluster scale up to **15,000 worker nodes** and
  **50,000 Pods**
- **Still relevant in 2026**: A useful reminder that network and IP planning
  often become the first true scale bottleneck

## 2026-02-25: 贡献开源的 ROI：LF Research 2025 年调查报告解读

- [贡献开源的 ROI (Chinese)](../archive-blog/2026-02-25/2026-02-25-opensource-contribution-roi_zh.md)

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

- [AAIF Introduction (Chinese)](../archive-blog/2026-02-14/2026-02-14-aaif-introduction_zh.md)

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

- [Inference Cost Optimization (Chinese)](../archive-blog/2026-01-15/2026-01-15-inference-cost-optimization_zh.md)

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

- [KubeCon EU 2026 Recommendations (Chinese)](../archive-blog/2026-01-12/2026-01-12-kubecon-eu-2026-recommendations_zh.md)

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

- [Ambient Global Compute 中文博客](../archive-blog/2026-01-07/2026-01-07-ambient-global-compute_zh.md)

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

- [OCI Taking Over Everything (English)](../archive-blog/2025-12-22/2025-12-22-oci-taking-over-everything_en.md)
- [OCI 正在悄悄占领一切 (Chinese)](../archive-blog/2025-12-22/2025-12-22-oci-taking-over-everything_zh.md)

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

- [vLLM 2025 Retro & 2026 RoadMap (English)](../archive-blog/2025-12-22/2025-12-22-vllm-2025-retro-2026-roadmap_en.md)
- [vLLM 2025 年度回顾与 2026 年路线图 (Chinese)](../archive-blog/2025-12-22/2025-12-22-vllm-2025-retro-2026-roadmap_zh.md)

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

- [GPU 故障检测与自愈实践指南 (Chinese)](../archive-blog/2025-12-17/2025-12-17-gpu-fault-detection_zh.md)

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

- [DRANET 介绍 (Chinese)](../archive-blog/2025-12-17/2025-12-17-dranet-kubernetes-network-driver_zh.md)

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

- [ByteDance Large-Scale K8s (English)](../archive-blog/2025-12-15/2025-12-15-bytedance-large-scale-k8s.md)
- [字节跳动超大规模 K8s 方案 (Chinese)](../archive-blog/2025-12-15/2025-12-15-bytedance-large-scale-k8s_zh.md)

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

- [SQL to Inference Evolution (English)](../archive-blog/2025-12-15/2025-12-15-sql-to-inference.md)
- [SQL 到推理演进 (Chinese)](../archive-blog/2025-12-15/2025-12-15-sql-to-inference_zh.md)

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

- [Multi-Tenancy Isolation (English)](../archive-blog/2025-12-15/2025-12-15-multi-tenancy-isolation.md)
- [多租户隔离性方案探讨 (Chinese)](../archive-blog/2025-12-15/2025-12-15-multi-tenancy-isolation_zh.md)

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

## 2025-12-08: GKE 65,000 Node Support — Benchmarking AI Workloads at Scale

- [GKE 65K Nodes (Chinese)](../archive-blog/2025-12-08/2025-12-08-gke-65k-nodes_zh.md)

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

- [Kubernetes Community Operations (English)](../archive-blog/2025-12-05/2025-12-05-kubernetes-community-operations.md)
- [Kubernetes 社区运作方式 (Chinese)](../archive-blog/2025-12-05/2025-12-05-kubernetes-community-operations_zh.md)

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

- [Ant Group Large-Scale K8s (English)](../archive-blog/2025-12-03/2025-12-03-ant-group-large-scale-k8s.md)
- [蚂蚁大规模集群经验 (Chinese)](../archive-blog/2025-12-03/2025-12-03-ant-group-large-scale-k8s_zh.md)

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

- [KCD Hangzhou Observability (English)](../archive-blog/2025-12-02/2025-12-02-kcd-hangzhou-observability.md)
- [KCD 杭州可观测性优化 (Chinese)](../archive-blog/2025-12-02/2025-12-02-kcd-hangzhou-observability_zh.md)

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

- [Safe Upgrade and Rollback (English)](../archive-blog/2025-12-01/2025-12-01-safe-upgrade-rollback.md)
- [安全升级与回滚 (Chinese)](../archive-blog/2025-12-01/2025-12-01-safe-upgrade-rollback_zh.md)

A comprehensive guide to Kubernetes safe upgrade and rollback capabilities
based on the Google Cloud blog and KubeCon NA 2025 keynote:

- Emulation Version (`--emulation-version`) available in Kubernetes 1.31+
- Minimum Compatibility Version (`--min-compatibility-version`) in 1.35+
- KEP-4330: Compatibility Versions
- GKE reliability: 99.98% upgrade success rate
- Three stages of upgrade readiness
- Best practices for safe upgrades and rollback procedures

## 2025-12-01: Inference Orchestration Solutions

- [Inference Orchestration (English)](../archive-blog/2025-12-01/2025-12-01-inference-orchestration.md)
- [推理编排 (Chinese)](../archive-blog/2025-12-01/2025-12-01-inference-orchestration_zh.md)

An overview of current open-source inference orchestration solutions and
convergence trends:

- Workload solutions: dual LWS (llm-d), Serving Group (Kthena), StormService
  (AIBrix), Dynamo Grove/LWS, RBG
- Convergence trends in the ecosystem
- When PD disaggregation truly provides value
- AIConfigurator for configuration optimization
- Recommendations for new and existing deployments

## 2025-12-01: AWS 10K Node EKS Ultra Scale Clusters

- [AWS 10K Node Clusters (English)](../archive-blog/2025-12-01/2025-12-01-aws-10k-node-clusters.md)
- [AWS 万节点集群 (Chinese)](../archive-blog/2025-12-01/2025-12-01-aws-10k-node-clusters_zh.md)

A follow-up to Google's 130K node cluster, covering AWS EKS ultra-scale
optimizations:

- Community improvements: Kubernetes v1.33 read/list cache, Karpenter
- AWS-specific: QLDB journal for etcd, BoltDB on tmpfs
- Image acceleration: SOCI Snapshotter for lazy loading
- AI workloads: LWS + vLLM, CoreDNS autoscaling
- Performance SLOs: 1s for gets/writes, 30s for lists, 500 pods/second

## 2025-11-28: Agent Sandbox — Secure AI Agents on Kubernetes

- [Agent Sandbox (English)](../archive-blog/2025-11-28/2025-11-28-agent-sandbox.md)
- [Agent Sandbox (Chinese)](../archive-blog/2025-11-28/2025-11-28-agent-sandbox_zh.md)

A comprehensive guide to Agent Sandbox, a Kubernetes SIG Apps project for
secure AI agent execution, covering:

- Project introduction and Sandbox CRD
- gVisor (GKE) integration status
- Kata Containers integration status
- SandboxWarmPool for sub-second startup latency
- Use cases for AI agents, development environments, and notebooks
- Industry trends and future directions

## 2025-11-26: JobSet In-Place Restart — 92% Faster Recovery

- [JobSet In-Place Restart (English)](../archive-blog/2025-11-26/2025-11-26-jobset-in-place-restart.md)
- [JobSet In-Place Restart (Chinese)](../archive-blog/2025-11-26/2025-11-26-jobset-in-place-restart_zh.md)

A blog post about JobSet leveraging Kubernetes In-Place Container Restart
(Co-Evolving theme), covering:

- Co-Evolving concept: Kubernetes features empowering the ecosystem
- In-Place Container Restart capability (KEP-5307 in 1.34, KEP-5532 in 1.35)
- Real-world results: Restart time from 2m10s to 10s (92% faster) on 5000 nodes
- Benefits for distributed training, job dependencies, and resource efficiency
- Integration considerations and future roadmap

## 2025-11-26: cgroup v2 Migration Guide

- [cgroup v2 Migration Guide (English)](../archive-blog/2025-11-26/2025-11-26-cgroup-v2.md)
- [cgroup v2 Migration Guide (Chinese)](../archive-blog/2025-11-26/2025-11-26-cgroup-v2_zh.md)

A comprehensive guide to cgroup v2 migration for Kubernetes users, covering:

- Kubernetes 1.31 maintenance mode and 1.35 deprecation announcement
- cgroup v1 vs v2 differences and technical improvements
- Historical timeline and kernel/controller evolution
- cgroup v2 hierarchy and controller details (CPU, memory, IO, PSI)
- Migration guidance with runc (1.3.2+) and crun (1.23+) recommendations
- kubeadm upgrade warnings for cgroup v1 environments

## 2025-11-25: Topology-Aware Scheduling

- [Topology-Aware Scheduling (English)](../archive-blog/2025-11-25/2025-11-25-topology-aware-scheduling.md)
- [Topology-Aware Scheduling (Chinese)](../archive-blog/2025-11-25/2025-11-25-topology-aware-scheduling_zh.md)

A comprehensive guide to topology-aware scheduling for AI workloads, covering:

- Background on current topology scheduling (Device Plugin, Kueue, Volcano)
- DRA topology management with GPU + NIC coordination
- DRAConsumableCapacity feature in Kubernetes 1.34
- Migration challenges from Device Plugin to DRA
- KubeCon NA 2025 insights and resources

## 2025-11-25: Gang Scheduling

- [Gang Scheduling Blog (English)](../archive-blog/2025-11-25/2025-11-25-gang-scheduling.md)
- [Gang Scheduling Blog (Chinese)](../archive-blog/2025-11-25/2025-11-25-gang-scheduling_zh.md)
- [Upstream: Kubernetes v1.35 WAS Intro](https://kubernetes.io/blog/2025/12/29/kubernetes-v1-35-introducing-workload-aware-scheduling/)

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
2. Add your blog post as `YYYY-MM-DD-topic-name.md` (English)
3. Optionally add a translation with suffix, e.g.
   `YYYY-MM-DD-topic-name_zh.md`
4. Follow the metadata format used in existing posts
5. Ensure all markdown passes `markdownlint` validation
6. Update this README with a link to your post
