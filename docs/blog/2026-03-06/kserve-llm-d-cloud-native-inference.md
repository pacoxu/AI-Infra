---
status: Active
maintainer: pacoxu
date: 2026-03-06
tags: inference, kserve, llm-d, pd-disaggregation, kubernetes, cloud-native
canonical_path: docs/blog/2026-03-06/kserve-llm-d-cloud-native-inference.md
---

# Best of Both Worlds: Cloud-Native AI Inference at Scale using KServe and llm-d

This blog post summarizes the KServe official blog post:
[Best of Both Worlds: Cloud-Native AI Inference at Scale using KServe and llm-d](https://kserve.github.io/website/blog/cloud-native-ai-inference-kserve-llm-d)

## Overview

The blog post explores how [KServe](https://github.com/kserve/kserve)
(CNCF Incubating) and [llm-d](https://github.com/llm-d/llm-d) (Red Hat / IBM)
combine to deliver cloud-native LLM inference at scale. Together they implement
Prefill-Decode (P/D) disaggregation using a dual
[LeaderWorkerSet (LWS)](https://github.com/kubernetes-sigs/lws) architecture.

## Key Themes

### KServe as the Model Serving Foundation

KServe provides the Kubernetes-native model serving platform:

- **InferenceService CRD**: Unified API for deploying ML models
- **LLMInferenceService CRD**: Dedicated API for LLM serving and P/D
  disaggregation
- **LMCache integration**: KV cache offloading to reduce TTFT and improve
  throughput
- **Canary deployments**: Safe rollouts with traffic splitting
- **Serverless serving**: Knative-based scale-to-zero for variable traffic

### llm-d as the Disaggregation Engine

[`llm-d`](https://github.com/llm-d/llm-d) (Large Language Model Distributed)
provides the reference implementation for disaggregated LLM inference:

- **Dual LWS architecture**: Separate LeaderWorkerSets for prefill and decode
  workers
- **KServe integration**: Builds on KServe's InferenceService abstraction
- **LMCache**: Efficient KV cache transfer between prefill and decode nodes
- **Routing sidecar**: Intelligent request routing with cache-awareness
- **Production-grade**: Reference implementation following cloud-native best
  practices

### Best of Both Worlds

The combination addresses key inference challenges:

| Challenge | Solution |
| --- | --- |
| GPU resource contention | Separate prefill and decode onto dedicated nodes |
| TTFT (Time to First Token) | Prefill workers optimized for prompt processing |
| TPOT (Time Per Output Token) | Decode workers optimized for token generation |
| KV cache efficiency | LMCache transfers KV cache between phases |
| Kubernetes-native ops | InferenceService CRD + LWS orchestration |

### Architecture

```text
Client Request
    ↓
KServe InferenceService / Gateway
    ↓
Routing Sidecar (cache-aware)
    ↙              ↘
Prefill LWS      Decode LWS
(KV build)  →→  (KV reuse via LMCache)
    ↓
Response
```

## P/D Disaggregation Benefits

When prompts are long relative to output length (RAG, document Q&A,
code generation), P/D disaggregation provides:

- **Lower TTFT**: Prefill workers are not blocked by ongoing decode operations
- **Higher throughput**: Decode workers can process more concurrent requests
- **Independent scaling**: Scale prefill and decode capacity separately based
  on workload
- **Cost efficiency**: Right-size GPU allocation per inference phase

## Relationship to Kubernetes Ecosystem

- **LWS**: Foundation for orchestrating multi-pod leader-worker topologies
- **Gateway API Inference Extension**: Kubernetes SIG inference-aware routing
- **Kueue**: Gang scheduling for coordinated workload admission
- **KEDA**: Custom metrics autoscaling for LLM workloads

## References

- [KServe + llm-d Blog Post](https://kserve.github.io/website/blog/cloud-native-ai-inference-kserve-llm-d)
- [KServe GitHub](https://github.com/kserve/kserve)
- [llm-d GitHub](https://github.com/llm-d/llm-d)
- [LMCache GitHub](https://github.com/LMCache/LMCache)
- [LeaderWorkerSet (LWS)](https://github.com/kubernetes-sigs/lws)
- [PD Disaggregation Overview](../../inference/pd-disaggregation.md)
- [Inference Orchestration Blog](../2025-12-01/inference-orchestration.md)

---

**Source**: KServe Official Blog  
**Tags**: #kserve #llm-d #pd-disaggregation #cloud-native #kubernetes #inference
