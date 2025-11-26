---
status: Active
maintainer: pacoxu
last_updated: 2025-11-26
tags: blog, kubernetes, ai-infrastructure
---

# AI-Infra Blog Posts

This directory contains blog posts and articles about AI infrastructure,
Kubernetes scheduling, and related topics.

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
