---
status: Active
maintainer: pacoxu
last_updated: 2025-12-12
tags: blog, kubernetes, ai-infrastructure
---

# AI-Infra Blog Posts

This directory contains blog posts and articles about AI infrastructure,
Kubernetes scheduling, and related topics.

## 2025-12-12: KEP-4017 Pod Index Label — Co-Evolving in Kubernetes

- [Pod Index Label (English)](./2025-12-12/pod-index-label.md)
- [Pod Index Label (Chinese)](./2025-12-12/pod-index-label_zh.md)

A comprehensive guide to KEP-4017: Pod Index Label, exploring how Kubernetes
foundational features enable ecosystem innovation (co-evolving theme):

- What is KEP-4017 and why it matters
- Pod index as a label for StatefulSets and Indexed Jobs
- LeaderWorkerSet (LWS) use case: leader as pod-0, workers starting from pod-1
- Distributed training with parameter servers
- Prefill-decode disaggregation for LLM inference
- Multi-replica model serving and A/B testing
- Observability improvements: filtering logs and metrics by pod index
- Ray clusters, chaos engineering, and rolling deployment use cases
- Technical impact: minimal changes, maximum value
- GA in Kubernetes 1.32 (December 2024)

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
