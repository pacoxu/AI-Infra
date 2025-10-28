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
- [Scaling P/D Workloads](#scaling-pd-workloads)
  - [Challenges with Traditional Autoscaling](#challenges-with-traditional-autoscaling)
  - [Configuration Optimization with AIConfigurator](#configuration-optimization-with-aiconfigurator)
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
Prefill LWS + StatefulSet + Pods  →  KV Cache  →  Decode LWS + StatefulSet + Pods
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

[`Dynamo`](https://github.com/ai-dynamo/dynamo) is NVIDIA's high-performance
LLM inference engine that provides enterprise-grade serving capabilities with
comprehensive support for Prefill-Decode disaggregation.

**P/D Disaggregation Support:**

- **Supported**: Dynamo has implemented P/D disaggregation for enhanced
  performance and resource efficiency
- **Multi-Node Architecture**: In multi-node deployments, Dynamo utilizes
  LeaderWorkSet (LWS) for orchestrating disaggregated workloads
- **Design Documentation**:
  [Disaggregation Serving](https://github.com/ai-dynamo/dynamo/blob/main/docs/design_docs/disagg_serving.md)
  \- Detailed design for separating prefill and decode phases
- **Feature Comparison**:
  [Feature Support Comparison](https://github.com/ai-dynamo/dynamo/blob/6deeecb1d6a9f4eb1770b4272bfa85a4b6226e0a/deploy/helm/README.md#feature-support-comparison)
  \- Shows disaggregation capabilities alongside other features

**Key Implementations:**

- Support for disaggregated prefill and decode serving
  [#998](https://github.com/ai-dynamo/dynamo/pull/998)
- Enhanced disaggregation features
  [#1511](https://github.com/ai-dynamo/dynamo/pull/1511)
- Ongoing unification efforts
  [#1728](https://github.com/ai-dynamo/dynamo/issues/1728)

**Architecture:**

Dynamo's disaggregation implementation enables:

- Independent scaling of prefill and decode workloads
- Optimized resource utilization across GPU clusters
- Coordinated workload management using LWS in multi-node scenarios
- Enterprise-ready deployment with Kubernetes integration

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

---

## Scaling P/D Workloads

Scaling disaggregated Prefill/Decode workloads presents unique challenges that
differ from traditional monolithic inference deployments. This section explores
the limitations of standard autoscaling approaches and introduces tools for
optimizing P/D configurations.

### Challenges with Traditional Autoscaling

Traditional Kubernetes autoscaling mechanisms like Horizontal Pod Autoscaler
(HPA) and Knative Pod Autoscaler (KPA) face significant limitations when
applied to P/D disaggregated workloads:

**Key Challenges:**

- **Independent Phase Characteristics**: Prefill and decode phases have
  distinct resource utilization patterns and performance characteristics.
  Standard autoscalers cannot independently optimize each phase based on their
  unique metrics (TTFT for prefill, TPOT for decode).

- **Complex Configuration Space**: Disaggregated deployments require decisions
  about:
  - Number of prefill workers vs. decode workers
  - Parallelism strategy for each phase (tensor parallel, pipeline parallel)
  - Batch sizes optimized for each phase
  - GPU allocation across phases

- **Interdependent Scaling**: Prefill and decode components must scale
  coordinately to maintain optimal throughput and latency. Scaling one without
  considering the other can create bottlenecks or waste resources.

- **SLA Awareness**: Traditional autoscalers don't understand LLM-specific SLA
  targets like TTFT (Time to First Token) and TPOT (Time per Output Token),
  which are critical for user experience in disaggregated serving.

- **Resource Heterogeneity**: P/D workloads often benefit from heterogeneous
  GPU allocations (e.g., more GPUs for decode than prefill), which standard
  autoscalers don't optimize for.

**Why HPA/KPA Fall Short:**

- **Reactive Rather Than Predictive**: They react to current metrics rather
  than proactively optimizing for workload characteristics
- **No Configuration Optimization**: They scale replica counts but don't
  optimize the underlying configuration (parallelism, batch sizes, etc.)
- **Single-Metric Focus**: They typically scale based on CPU/GPU utilization or
  request rate, ignoring the complex interplay of TTFT, TPOT, and throughput

### Configuration Optimization with AIConfigurator

[`AIConfigurator`](https://github.com/ai-dynamo/aiconfigurator) by NVIDIA
addresses these challenges through offline optimization of disaggregated
deployment configurations. It helps determine optimal configurations before
deployment rather than relying on reactive autoscaling.

**How AIConfigurator Works:**

AIConfigurator searches the configuration space for disaggregated serving
deployments by:

1. **Modeling LLM Inference Performance**: Uses collected data for target
   hardware to estimate execution time for different configurations
2. **Configuration Space Search**: Evaluates thousands of combinations of:
   - Number of prefill and decode workers
   - Parallelism strategies (TP, PP, DP)
   - Batch sizes for each phase
   - GPU allocation patterns
3. **SLA-Constrained Optimization**: Finds configurations that maximize
   throughput while meeting TTFT and TPOT targets
4. **Pareto Frontier Analysis**: Identifies trade-offs between throughput,
   latency, and resource utilization

**Key Features:**

- **xPyD Configuration Planning**: Determines optimal replica configurations
  where each replica consists of x prefill workers and y decode workers
- **Hardware-Specific Optimization**: Supports various GPU types (H100, H200,
  B200, etc.) with collected performance data
- **Quantization Support**: Evaluates different quantization strategies (FP16,
  FP8, INT4, etc.) per component
- **Deployment File Generation**: Generates ready-to-use configuration files
  for Dynamo deployments

**Example Usage:**

```bash
# Find optimal configuration for Qwen3-32B on 32 H200 GPUs
# with SLA targets: TTFT ≤ 300ms, TPOT ≤ 10ms
aiconfigurator cli default \
  --model QWEN3_32B \
  --total_gpus 32 \
  --system h200_sxm \
  --isl 4000 \
  --osl 500 \
  --ttft 300 \
  --tpot 10
```

**Benefits for P/D Workloads:**

- **Informed Scaling Decisions**: Provides data-driven insights on how to scale
  prefill vs. decode components
- **Configuration Templates**: Generates optimal starting configurations that
  can be used as baselines for autoscaling policies
- **Performance Prediction**: Estimates throughput and latency before
  deployment, reducing trial-and-error
- **Resource Efficiency**: Identifies configurations that maximize GPU
  utilization while meeting SLA targets

**Integration with Autoscaling:**

While AIConfigurator is an offline tool, its outputs can inform autoscaling
strategies:

- Use AIConfigurator to establish baseline configurations for different load
  levels
- Configure autoscalers to transition between AIConfigurator-optimized
  configurations based on workload patterns
- Leverage AIConfigurator's insights to set appropriate scaling thresholds and
  replica ratios between prefill and decode workers

This approach combines the predictive optimization of AIConfigurator with the
reactive capabilities of Kubernetes autoscaling for more effective P/D workload
management.

---

## References

- <https://github.com/kubernetes-sigs/lws>
- <https://github.com/llm-d/llm-d>
- <https://github.com/llm-d/llm-d-routing-sidecar>
- <https://github.com/sgl-project/rbg>
- <https://github.com/volcano-sh/kthena>
- <https://github.com/ai-dynamo/dynamo>
- <https://github.com/ai-dynamo/aiconfigurator>
- <https://github.com/vllm-project/vllm>
- <https://github.com/vllm-project/production-stack>
- <https://github.com/vllm-project/aibrix>
- <https://github.com/kserve/kserve>
- <https://github.com/InftyAI/llmaz>
- <https://github.com/LMCache/lmcache>
- DistServe (OSDI'24): <https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf>

**Some were generated by ChatGPT. So please be careful before you use them.
These are personal learning notes.**
