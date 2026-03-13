---
status: Active
maintainer: pacoxu
date: 2025-12-01
tags: inference, orchestration, kubernetes, lws, pd-disaggregation, vllm
canonical_path: docs/blog/2025-12-01/inference-orchestration.md
---

# Inference Orchestration: Current Solutions and Convergence Trends

Note: The content in this article is based on currently available public information
and is intended for technical reference only.
The effectiveness of each solution depends heavily on your specific workload,
infrastructure, and ecosystem integration. The architectural affiliations
and early design choices mentioned here do not determine their future direction.
In practice, community activity, openness, and long-term evolution are
often more important factors.
Please evaluate and choose based on your own scenario.

## Introduction

The landscape of open-source inference orchestration for Large Language Models
(LLMs) has evolved rapidly in 2025. Multiple projects have emerged to address
the challenges of deploying and scaling LLM inference workloads on Kubernetes,
each with its own approach to workload management, resource orchestration, and
performance optimization.

This blog post provides an overview of the current inference orchestration
solutions, examines the convergence trends in the ecosystem, and raises
important questions about when Prefill-Decode (PD) disaggregation truly
provides value.

## The Current Landscape

### Rapid Development, Gradual Convergence

The inference orchestration space is characterized by:

- **Many implementations**: Multiple projects solving similar problems
- **Different architectural choices**: Varying approaches to workload
  management
- **Shared goals**: All aim to optimize LLM inference at scale
- **Emerging patterns**: Common solutions beginning to emerge

Despite the diversity, we're seeing convergence around key patterns:
LeaderWorkerSet (LWS)-based architectures, intelligent routing, and
disaggregated serving models.

## Workload Orchestration Solutions

### 1. Dual LWS Architecture

**[llm-d](https://github.com/llm-d/llm-d)** implements a dual LeaderWorkerSet
architecture for Prefill-Decode disaggregation:

- **Two LWS instances**: Separate LWS for prefill and decode workers
- **KServe integration**: Deep integration with KServe for model serving
- **LMCache support**: Efficient KV cache management across workers
- **Routing sidecar**: Intelligent request routing and cache optimization

```text
Client → Routing Sidecar → Prefill LWS → KV Cache → Decode LWS → Response
```

**Why dual LWS?** This architecture enables independent scaling and resource
optimization for each phase while maintaining coordination through the
leader-worker pattern.

### 2. Serving Group: Volcano Kthena

**[Kthena](https://github.com/volcano-sh/kthena)** takes a different approach
with its **Serving Group** concept:

- **No dual LWS**: Kthena intentionally avoids the dual LWS pattern
- **Gang scheduling integration**: Leverages Volcano's gang scheduling
  capabilities
- **Reduced layering**: Eliminates the StatefulSet/Pod layer complexity
- **Direct integration**: Native integration with Volcano scheduler

**Why not LWS?** The Kthena team found that integrating with Volcano's gang
scheduling required a different architecture. The dual LWS, StatefulSet, and
Pod layering added complexity without clear benefits for their use case.

This design choice reflects a key insight: **the best orchestration solution
depends on your existing infrastructure and scheduling requirements**.

> **Update (v0.3.0):** Kthena now supports LeaderWorkerSet integration as of
> the v0.3.0 release, providing flexible options for both LWS-based and
> Serving Group architectures depending on workload requirements.

### 3. StormService: AIBrix

**[AIBrix StormService](https://github.com/vllm-project/aibrix)** provides
specialized container lifecycle management for P/D disaggregation:

- **P/D lifecycle management**: Fine-grained control over prefill and decode
  containers
- **Multi-mode support**: TP, PP, single GPU, and P/D disaggregation
- **StormService and RoleSet CRDs**: Custom resources for P/D orchestration
- **Enterprise features**: Multi-tenancy, routing, and observability

**Architecture:**

```text
AIBrix Control Plane
    ├── StormService Controller
    │   ├── RoleSet (Prefill)
    │   └── RoleSet (Decode)
    ├── Gateway & Routing
    └── Autoscaler
```

### 4. NVIDIA Dynamo: Two Modes

**[Dynamo](https://github.com/ai-dynamo/dynamo)** offers two distinct
deployment modes:

**Grove Mode:**

- High-performance inference
- NVIDIA-native deployment
- Optimized for pure NVIDIA infrastructure

**LWS Mode:**

- Kubernetes-native deployment using LeaderWorkerSet
- Multi-node disaggregated serving
- Integration with Kubernetes ecosystem

This dual-mode approach allows users to choose the right level of abstraction
for their infrastructure.

### 5. SGLang RBG: LWS-Inspired

**[RBG (Resource-Aware Batch Scheduler)](https://github.com/sgl-project/rbg)**
learned from and reused design patterns from LWS:

- **LWS-inspired**: Incorporates proven patterns from LeaderWorkerSet
- **Resource-aware scheduling**: Optimizes batch scheduling based on resources
- **Batch optimization**: Intelligent batching strategies for throughput
- **P/D support**: Enables disaggregated prefill and decode workloads

## Convergence Trends

### Common Patterns Emerging

Despite different implementations, several patterns are converging:

| Pattern | llm-d | Kthena | AIBrix | Dynamo | RBG |
| --- | --- | --- | --- | --- | --- |
| LWS-based | ✓ (dual) | ✓ (v0.3.0+) | ✗ | ✓ (option) | ✓ (inspired) |
| P/D disaggregation | ✓ | ✓ | ✓ | ✓ | ✓ |
| Intelligent routing | ✓ | ✓ | ✓ | ✓ | ✓ |
| KV cache management | LMCache | Native | Distributed | Native | Native |

### Why So Many Implementations?

The diversity reflects different optimization goals:

1. **Scheduling integration**: Kthena needs Volcano gang scheduling directly
2. **Enterprise features**: AIBrix focuses on multi-tenancy and observability
3. **Performance focus**: Dynamo optimizes for NVIDIA hardware
4. **Simplicity**: RBG provides a lightweight LWS-inspired approach
5. **Production-readiness**: llm-d demonstrates a complete reference
   implementation

## The PD Disaggregation Question

### Does PD Disaggregation Always Provide Value?

At [KubeCon China 2025](https://www.bilibili.com/video/BV1dkUYBkEUc/), Yu Wen
Yuan's keynote "Kubernetes Was Built for Service-Resource Orchestration. MaaS
Changes Everything" raised important questions about PD disaggregation:

> "PD-Disaggregate Role Scheduling • Not So Sure? (Our answer is Data Plane!)"

This challenges the assumption that PD disaggregation is always beneficial.

### When PD Disaggregation Helps

PD disaggregation provides clear benefits when:

- **Long prefill, short decode**: Input prompts are much longer than outputs
- **High concurrency**: Many simultaneous requests need serving
- **Heterogeneous hardware**: Different GPU types for different phases
- **SLA-driven scheduling**: Different latency requirements (TTFT vs TPOT)

### When PD Disaggregation May Not Help

Consider alternatives when:

- **Short contexts**: Both prefill and decode are fast
- **Low concurrency**: Few simultaneous requests
- **Homogeneous hardware**: Same GPUs for all workloads
- **Complexity costs**: Operational overhead outweighs benefits
- **KV cache transfer overhead**: Network latency exceeds computation savings

### The Data Plane Perspective

The "Data Plane" answer suggests that the value of PD disaggregation depends
on where bottlenecks actually exist. Before implementing complex orchestration:

1. **Profile your workload**: Understand where time is spent
2. **Measure KV cache transfer costs**: Network overhead matters
3. **Consider simpler alternatives**: TP/DP without disaggregation
4. **Evaluate operational complexity**: More components = more failure modes

## Configuration Optimization: AIConfigurator

Choosing the right P/D configuration is complex. NVIDIA's
**[AIConfigurator](https://github.com/ai-dynamo/aiconfigurator)** helps
optimize disaggregated deployment configurations:

### What AIConfigurator Does

- **Configuration space search**: Evaluates thousands of P/D combinations
- **SLA-constrained optimization**: Finds configurations meeting TTFT/TPOT
  targets
- **Hardware-specific tuning**: Supports H100, H200, B200 with collected data
- **xPyD planning**: Determines optimal prefill/decode worker ratios

### Example Usage

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

### Why AIConfigurator Matters

Traditional autoscaling (HPA/KPA) doesn't understand LLM-specific
characteristics. AIConfigurator provides:

- **Informed decisions**: Data-driven configuration choices
- **Predictive optimization**: Estimate performance before deployment
- **Resource efficiency**: Maximize GPU utilization with SLA guarantees

## Recommendations

### For New Deployments

1. **Start simple**: Begin with monolithic serving (no P/D disaggregation)
2. **Profile first**: Understand your workload characteristics
3. **Use AIConfigurator**: Let data guide configuration decisions
4. **Add complexity gradually**: Introduce P/D only when benefits are clear

### For Existing Infrastructure

| If you use... | Consider... |
| --- | --- |
| Volcano | Kthena (native integration) |
| KServe | llm-d (deep integration) |
| vLLM | AIBrix (vLLM ecosystem) |
| NVIDIA GPUs | Dynamo (NVIDIA optimization) |
| SGLang | RBG (LWS-inspired, lightweight) |

### Key Questions Before Adopting PD Disaggregation

1. **Is your prefill time >> decode time?** If not, disaggregation may not
   help.
2. **Can your network handle KV cache transfer?** Network overhead can
   eliminate gains.
3. **Do you need independent scaling?** If P and D scale together, keep them
   together.
4. **Is operational complexity acceptable?** More components = more failure
   modes.

## Conclusion

The inference orchestration landscape is diverse but converging. Key
takeaways:

- **Multiple solutions exist** because different infrastructure has different
  needs
- **LWS-based patterns are popular** but not universal (Kthena's Serving Group
  shows alternatives)
- **PD disaggregation is not always valuable** - profile your workload first
- **Tools like AIConfigurator help** navigate the complex configuration space
- **Start simple, add complexity when needed** based on actual measurements

The future will likely see further consolidation around proven patterns, but
the current diversity reflects healthy experimentation in a rapidly evolving
field.

---

## References

### Workload Orchestration Projects

- [llm-d](https://github.com/llm-d/llm-d) - Dual LWS architecture for P/D
- [Kthena](https://github.com/volcano-sh/kthena) - Volcano-based Serving Group
- [AIBrix](https://github.com/vllm-project/aibrix) - StormService for P/D
- [Dynamo](https://github.com/ai-dynamo/dynamo) - NVIDIA inference platform
- [RBG](https://github.com/sgl-project/rbg) - LWS-inspired batch scheduler

### Configuration Tools

- [AIConfigurator](https://github.com/ai-dynamo/aiconfigurator) - P/D
  configuration optimizer

### Related Documentation

- [PD Disaggregation Overview](../../inference/pd-disaggregation.md)
- [Inference Guide](../../inference/README.md)
- [LWS (LeaderWorkerSet)](https://github.com/kubernetes-sigs/lws)

### Presentations

- [KubeCon China 2025: Kubernetes Was Built for Service-Resource
  Orchestration. MaaS Changes Everything](https://www.bilibili.com/video/BV1dkUYBkEUc/)
- [PDF Slides](https://github.com/user-attachments/files/23845814/04-kubernetes-was-built-for-service-resource-orchestration.-maas-changes-everything-yu-wen-yuan-.pdf)

---

**Author**: AI Infrastructure Learning Path
**Date**: December 1, 2025
**Tags**: #inference #orchestration #kubernetes #lws #pd-disaggregation
