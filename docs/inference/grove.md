---
status: Active
maintainer: pacoxu
last_updated: 2026-03-30
tags: inference, grove, kubernetes, gang-scheduling, disaggregated-inference, nvidia
canonical_path: docs/inference/grove.md
---

# Grove: One API for Any Inference Architecture

[`Grove`](https://github.com/ai-dynamo/grove) is a Kubernetes API that
provides a single declarative interface for orchestrating any AI inference
workload — from simple, single-pod deployments to complex multi-node,
disaggregated systems. Grove lets you scale a multinode inference deployment
from a single replica to data-center scale, supporting tens of thousands of
GPUs.

Grove allows you to describe your entire inference serving system in
Kubernetes — for example, prefill, decode, routing, or any other component —
as a single Custom Resource (CR). From that one spec, the platform coordinates
hierarchical gang scheduling, topology-aware placement, multi-level
autoscaling, and explicit startup ordering.

## Overview

Modern AI inference workloads require capabilities that Kubernetes does not
provide natively:

- **Scaling for Multi-Node/Multi-Pod Units** – Large models are sharded across
  multiple nodes. The fundamental scaling unit is no longer an individual pod,
  but an entire group of pods that together form one model instance.
- **Hierarchical Gang Scheduling** – Multi-node model instances require pods
  to be scheduled together; a partial subset leaves resources idle and can
  cause deadlock. Disaggregated inference has similar constraints: at least one
  prefill and one decode instance must be scheduled to form a functional
  pipeline.
- **Startup Ordering** – Even when components must be scheduled together, they
  often need to start in a specific order (e.g., MPI workloads require all
  workers to be ready before the leader launches).
- **Topology-Aware Placement** – Inference components communicate heavily;
  network-optimised placement (e.g., within NVLink domains) is crucial to
  minimise communication overhead and maximise performance.

## Key Concepts

Grove introduces four core abstractions:

| Concept | Description |
| --- | --- |
| **PodClique** | A group of pods representing a specific role (e.g., leader, worker, frontend). Each clique has independent configuration and supports custom scaling logic. |
| **PodCliqueScalingGroup** | A set of PodCliques that scale and are scheduled together as a gang. Ideal for tightly coupled roles like prefill leader and worker. |
| **PodCliqueSet** | The top-level Grove object that defines a group of components managed and co-located together. Supports autoscaling with topology-aware spread for availability. |
| **PodGang** | The scheduler API that defines a unit of gang-scheduling — a collection of pod groups where each group defines a minimum replica count guaranteed for scheduling. |

## Key Features

- **Hierarchical Gang Scheduling** – Ensures all required pods (across multiple
  roles and scaling groups) are scheduled atomically as a unit.
- **Topology-Aware Placement** – Places pods within NVLink domains or other
  network-topology boundaries to minimise inter-node communication latency.
- **Multi-Level Autoscaling** – Scales PodCliques independently while honouring
  gang constraints at the PodCliqueScalingGroup level.
- **Startup Ordering** – Guarantees a specified startup sequence across cliques
  (e.g., workers start before leader).
- **Rolling Updates** – Supports configurable rolling updates while respecting
  gang scheduling invariants.
- **Single-CRD Simplicity** – Entire inference systems (prefill + decode +
  router) are expressed as one `PodCliqueSet` CR — no scripts, multiple YAML
  files, or custom controllers required.

## Example Use Cases

- **Multi-Node Disaggregated Inference** for large models (e.g.,
  DeepSeek-R1, Llama-4-Maverick) across tens of thousands of GPUs.
- **Single-Node Disaggregated Inference** with ordered prefill and decode
  startup.
- **Agentic Pipelines** where a chain of specialised models must be placed and
  scaled together.
- **Standard Aggregated Inference** – single-node or single-GPU deployments
  with full lifecycle management.

## Relationship to NVIDIA Dynamo

Grove serves as the Kubernetes orchestration layer for
[NVIDIA Dynamo](https://github.com/ai-dynamo/dynamo), NVIDIA's distributed
inference framework. Dynamo supports two deployment modes:

- **Grove mode** – NVIDIA-native, using Grove CRDs for full gang-scheduling and
  topology awareness.
- **LWS mode** – Kubernetes-native, using
  [LeaderWorkerSet](https://github.com/kubernetes-sigs/lws) for a lighter-weight
  multi-node deployment.

Grove can also be used independently of Dynamo with any inference engine.

## Quick Start

```bash
# 1. Create a local kind cluster
cd operator && make kind-up

# 2. Deploy Grove
make deploy

# 3. Deploy your first workload
kubectl apply -f samples/simple/simple1.yaml

# 4. Inspect created resources
kubectl get pcs,pclq,pcsg,pg,pod -o wide
```

For the full walkthrough, see the
[Quickstart Guide](https://github.com/ai-dynamo/grove/blob/main/docs/quickstart.md)
and
[Installation Docs](https://github.com/ai-dynamo/grove/blob/main/docs/installation.md).

## Roadmap

### Completed (2025)

- Hierarchical Gang Scheduling ✅
- Multi-Level Horizontal Auto-Scaling ✅
- Startup Ordering ✅
- Rolling Updates ✅
- Topology-Aware Scheduling ✅

### Planned (2026)

- Resource-Optimised Rolling Updates
- Topology Spread Constraints
- Automatic Topology Detection

## Learning Topics

- Gang scheduling concepts and Kubernetes scheduler extension points
- CRD-based workload orchestration patterns
- Topology-aware placement for NVLink / RDMA networks
- Disaggregated inference architectures (prefill + decode)
- Multi-level autoscaling strategies for inference systems

## References

- [GitHub: ai-dynamo/grove](https://github.com/ai-dynamo/grove)
- [Core Concepts Overview](https://github.com/ai-dynamo/grove/blob/main/docs/user-guide/01_core-concepts/01_overview.md)
- [API Reference](https://github.com/ai-dynamo/grove/blob/main/docs/api-reference/operator-api.md)
- [NVIDIA Dynamo](https://github.com/ai-dynamo/dynamo)
- [Grove Mailing List](https://groups.google.com/g/grove-k8s)
- [NVIDIA Dynamo Discord](https://discord.gg/UxcbxEYqS4)
