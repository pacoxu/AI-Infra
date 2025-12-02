---
status: Active
maintainer: pacoxu
last_updated: 2025-12-02
tags: blog, kubernetes, ai-infrastructure
---

# AI-Infra Blog Posts

This directory contains blog posts and articles about AI infrastructure,
Kubernetes scheduling, and related topics.

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
