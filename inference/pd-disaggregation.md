# PD Disaggregation in LLM Inference

This document introduces the concept of Prefill–Decode (PD) disaggregation in
large language model (LLM) inference, its benefits, current implementation
status in common AI Infra projects, and the future roadmap for its adoption.

## Table of Contents

- [What is PD Disaggregation](#what-is-pd-disaggregation)
- [Workload Solutions](#workload-solutions)
  - [LWS (LeaderWorkSet)](#lws-leaderworkset)
  - [SGLang RBG](#sglang-rbg)
  - [AIBrix StormService](#aibrix-stormservice)
  - [Volcano Kthena](#volcano-kthena)
  - [llm-d](#llm-d)
- [Project Support Status](#project-support-status)
  - [NVIDIA Dynamo](#nvidia-dynamo)
  - [vLLM production stack](#vllm-production-stack)
  - [AIBrix](#aibrix)
  - [InftyAI/llmaz](#inftyaillmaz)
  - [KServe](#kserve)
- [References](#references)

---

## What is PD Disaggregation

In LLM inference, the process can be divided into two distinct phases:

- **Prefill**: processes the entire input prompt in parallel, builds KV cache.
- **Decode**: generates output tokens one by one using the KV cache.

In a monolithic setup, both prefill and decode run on the same GPU, which
causes resource contention (e.g., prefill latency impacting decode throughput).
**PD Disaggregation** addresses this by disaggregating prefill and decode
phases into separate GPU workers or nodes.

**Benefits:**

- Improved latency (TTFT and TPOT)
- Higher throughput per GPU
- Independent scaling and tuning of each phase
- Flexibility for scheduling and load balancing

---

## Workload Solutions

This section covers specific workload orchestration solutions that enable
efficient PD disaggregation architectures in Kubernetes environments.

### LWS (LeaderWorkSet)

[`LWS (LeaderWorkSet)`](https://github.com/kubernetes-sigs/lws) is a
Kubernetes SIG project that provides a workload API for managing groups of
Pods with leader-follower relationships. For P/D disaggregation, LWS can be
used with StatefulSet and Pod resources to orchestrate disaggregated
inference workloads.

**Key Features for P/D Disaggregation:**

- **Dual LWS Architecture**: Use two separate LWS instances - one for prefill
  workers and another for decode workers
- **Leader-Follower Coordination**: Enable coordination between prefill and
  decode phases through leader selection
- **StatefulSet Integration**: Work alongside StatefulSets for persistent
  storage and networking requirements
- **Pod Group Management**: Manage groups of Pods as cohesive units for
  scaling and lifecycle management

**Architecture Pattern:**

```text
Prefill LWS + StatefulSet  →  KV Cache  →  Decode LWS + StatefulSet
```

This approach enables independent scaling and resource management for each
phase while maintaining coordination through the LWS leader-follower pattern.

### SGLang RBG

[`SGLang RBG`](https://github.com/sgl-project/rbg) is a resource-aware batch
scheduler designed for efficient LLM inference workload management. The
project learned from and reused design patterns from the LWS project.

**Key Features:**

- **LWS-Inspired Design**: Incorporates proven patterns from the LWS project
  for workload orchestration
- **Resource-Aware Scheduling**: Optimizes batch scheduling based on
  available GPU resources and workload characteristics
- **P/D Disaggregation Support**: Enables efficient scheduling of disaggregated
  prefill and decode workloads
- **Batch Optimization**: Provides intelligent batching strategies for
  improved throughput

**Integration with P/D Disaggregation:**

SGLang RBG enhances P/D disaggregation by providing:

- Intelligent scheduling of prefill and decode batches
- Resource optimization across disaggregated components
- Coordination between prefill and decode phases

### AIBrix StormService

[`AIBrix StormService`](https://github.com/vllm-project/aibrix/blob/fd8ddd8062602313c5f7b3b7ecbda20e845da647/docs/source/designs/aibrix-stormservice.rst)
is a specialized component designed to manage and orchestrate the lifecycle
of inference containers in Prefill/Decode disaggregated architectures.

**Key Capabilities:**

- **P/D Lifecycle Management**: Specialized orchestration for disaggregated
  prefill and decode container lifecycles
- **Multi-Mode Support**: Manages various deployment modes including:
  - Prefill/Decode disaggregation
  - Tensor Parallelism (TP)
  - Pipeline Parallelism (PP)
  - Single GPU model deployments
- **Container Orchestration**: Provides fine-grained control over inference
  container deployment and scaling
- **Resource Coordination**: Ensures proper resource allocation and
  coordination between disaggregated components

**StormService Architecture:**

StormService acts as a specialized controller that:

1. Manages the deployment of prefill and decode containers
2. Coordinates resource allocation across disaggregated components
3. Handles lifecycle events (scaling, updates, failures)
4. Optimizes resource utilization across different parallelism modes

This enables enterprise-grade P/D disaggregation with robust lifecycle
management and multi-tenancy support.

### Volcano Kthena

[`Volcano Kthena`](https://github.com/volcano-sh/kthena) is a
Kubernetes-native LLM inference platform that provides comprehensive
infrastructure for deploying and managing Large Language Models in production
environments. As part of the Volcano ecosystem, Kthena brings enterprise-grade
capabilities to LLM inference workloads.

**Key Capabilities:**

- **Kubernetes-Native Architecture**: Deep integration with Kubernetes for
  seamless workload orchestration and resource management
- **Production-Ready Inference**: Enterprise-grade platform for deploying and
  managing LLM inference at scale
- **Volcano Integration**: Leverages Volcano's advanced scheduling
  capabilities for optimal resource allocation
- **Workload Orchestration**: Comprehensive lifecycle management for inference
  workloads including scaling and failure handling

**Integration with P/D Disaggregation:**

Kthena provides infrastructure support for P/D disaggregation through:

- Native Kubernetes workload management for disaggregated architectures
- Coordinated scheduling of prefill and decode components
- Resource optimization across disaggregated inference phases
- Integration with Volcano's batch scheduling for efficient workload placement

This makes Kthena well-suited for organizations building production LLM
inference platforms with P/D disaggregation requirements.

### llm-d

[`llm-d`](https://github.com/llm-d/llm-d) is a production-ready LLM inference
platform that implements Prefill-Decode disaggregation using a dual
LeaderWorkSet (LWS) architecture. As a reference implementation for P/D
disaggregation on Kubernetes, llm-d demonstrates best practices for
orchestrating disaggregated inference workloads.

**Key Architecture:**

- **Dual LWS Design**: Uses two separate LeaderWorkSet instances:
  - One LWS for prefill workers
  - One LWS for decode workers
- **KV Cache Transfer**: Implements efficient KV cache transfer between
  prefill and decode phases
- **LMCache Integration**: Supports LMCache for KV cache offloading and
  management
- **Routing Sidecar**: Includes
  [`llm-d routing sidecar`](https://github.com/llm-d/llm-d-routing-sidecar)
  for intelligent request routing and cache optimization

**P/D Disaggregation Implementation:**

llm-d's two-LWS architecture enables:

- Independent scaling of prefill and decode workloads
- Optimized resource allocation for each phase
- Reduced TTFT through dedicated prefill workers
- Improved decode throughput with isolated decode workers
- Efficient KV cache management across disaggregated components

**Architecture Pattern:**

```text
Client → Routing Sidecar → Prefill LWS → KV Cache (LMCache) → Decode LWS → Response
```

This architecture demonstrates a production-grade implementation of P/D
disaggregation that balances performance, scalability, and operational
simplicity.

---

## Project Support Status

### NVIDIA Dynamo

- [FEATURE]: Unifying Disagg Implementation in Dynamo [#1728](https://github.com/ai-dynamo/dynamo/issues/1728)

### vLLM production stack

- vLLM community is exploring deeper native integration in
  [production-stack PR #340](https://github.com/vllm-project/production-stack/pull/340).

### AIBrix

- WIP issue:
  [Add Prefill/Decode Disaggregation Support in Inference Gateway](https://github.com/vllm-project/aibrix/issues/1223)
  and [#958](https://github.com/vllm-project/aibrix/issues/958).

### InftyAI/llmaz

- Not supported yet.
- Milestone [v0.3.0](https://github.com/InftyAI/llmaz/issues/433) includes PD disaggregation.

### KServe

[`KServe`](https://github.com/kserve/kserve) is a CNCF Incubating project that
provides a Kubernetes-native platform for deploying and serving machine
learning models at scale. KServe is actively developing support for LLM
inference and P/D disaggregation through its LLMInferenceService CRD.

**Current Capabilities:**

- **LMCache Integration**: LMCache-based KV cache offloading for improved
  TTFT and throughput
- **Chunked Prefill**: Support for chunked prefill to optimize memory usage
  and reduce latency spikes
- **LLMInferenceService CRD**: Custom Resource Definition for unified LLM
  inference service management

**P/D Disaggregation Support:**

KServe is working on native P/D disaggregation support through:

- [WIP] Unified LLM Inference Service API and disaggregated p/d serving
  support [#4520](https://github.com/kserve/kserve/issues/4520)
- Integration with LMCache for efficient KV cache management across
  disaggregated components
- Standardized API for managing prefill and decode workloads

**Architecture Goals:**

The LLMInferenceService CRD aims to provide:

- Declarative configuration for P/D disaggregation
- Automatic orchestration of prefill and decode services
- Built-in KV cache management and transfer
- Integration with KServe's inference graph for complex serving patterns

KServe's approach focuses on providing a high-level abstraction that
simplifies P/D disaggregation deployment while maintaining flexibility for
advanced use cases.

### LMCache

LMCache is an LLM serving engine extension to reduce TTFT and increase
throughput, especially under long-context scenarios.

- LMCache is supported in the vLLM production stack, llm-d, and KServe.
- Stable support for non-prefix KV caches.

## References

- <https://github.com/kubernetes-sigs/lws>
- <https://github.com/llm-d/llm-d>
- <https://github.com/llm-d/llm-d-routing-sidecar>
- <https://github.com/sgl-project/rbg>
- <https://github.com/volcano-sh/kthena>
- <https://github.com/ai-dynamo/dynamo>
- <https://github.com/vllm-project/vllm>
- <https://github.com/vllm-project/production-stack>
- <https://github.com/vllm-project/aibrix>
- <https://github.com/kserve/kserve>
- <https://github.com/InftyAI/llmaz>
- <https://github.com/LMCache/lmcache>
- DistServe (OSDI'24): <https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf>

**Some were generated by ChatGPT. So please be careful before you use them.
This is a personal learning notes.**
