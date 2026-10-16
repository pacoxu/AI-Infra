---
status: Active
maintainer: pacoxu
last_updated: 2026-10-15
tags: inference, model-switching, aegaeon, vllm, sleep-mode, optimization, fma, dynamo
canonical_path: docs/inference/model-switching.md
---

# Model Switching and Dynamic Scheduling

This document covers advanced model switching techniques in LLM inference
systems, including token-level scheduling, dynamic model switching, and fast
model actuation. These techniques enable efficient multi-model serving, reduced
latency, and optimized resource utilization in production environments.

## Table of Contents

- [Overview](#overview)
- [Alibaba Aegaeon: Token-Level Scheduling](#alibaba-aegaeon-token-level-scheduling)
- [vLLM Sleep Mode: Fast Model Switching](#vllm-sleep-mode-fast-model-switching)
- [Comparison of Model Switching Approaches](#comparison-of-model-switching-approaches)
- [Production Use Cases](#production-use-cases)
- [Best Practices](#best-practices)
- [References](#references)

---

## Overview

Model switching is a critical operation in modern LLM inference systems that
enables:

- **Multi-model serving** on limited GPU resources
- **Dynamic resource allocation** based on request patterns
- **Cost optimization** through efficient GPU utilization
- **Reduced latency** for multi-tenant inference platforms

Traditional model switching requires:

- Restarting Python processes
- Re-initializing CUDA contexts
- Re-compiling GPU kernels
- Re-capturing CUDA graphs

This results in switching overhead of 30-100 seconds per model change, making
frequent model switching impractical.

**Modern approaches** optimize model switching through:

1. **Token-level scheduling** - Make switching decisions after each token
2. **Sleep mode** - Preserve process state while freeing GPU memory
3. **Component reuse** - Share compiled kernels and CUDA graphs
4. **KV cache synchronization** - Efficiently transfer cached data

These techniques reduce model switching overhead by **up to 97%**, enabling
real-time multi-model serving with sub-second switching latency.

---

## Alibaba Aegaeon: Token-Level Scheduling

[Aegaeon](https://mp.weixin.qq.com/s/uJyk0HALKFZysTAgghjgpw) is Alibaba's
distributed LLM serving system that pioneers **token-level scheduling**,
enabling dynamic model switching decisions after each generated token.

### Key Innovation: Token-Level Scheduling

Traditional inference systems make model selection decisions at the request
level. Aegaeon introduces **token-level granularity**, allowing the system
to:

- Evaluate model switching needs after each token generation
- Switch models mid-inference based on latency requirements
- Serve multiple models concurrently while meeting SLOs
- Optimize resource allocation in real-time

### Architecture and Components

Aegaeon is implemented as a distributed LLM serving system with:

- **5,700 lines** of Python and CUDA/C++ code
- **Control plane**: Built on asyncio for concurrent orchestration
- **Data plane**: Uses Ray for distributed data management
- **Execution backend**: Leverages vLLM for broad architecture support

![Aegaeon Implementation Architecture](https://github.com/user-attachments/assets/e3aea800-f62d-465a-b6f7-92753500f445)

*Figure 1: Aegaeon Implementation - Control plane uses asyncio for
concurrency, data plane uses Ray for distribution, and vLLM provides the
model execution backend with support for modern optimizations like
FlashAttention and PagedAttention.*

### Core Capabilities

#### 1. Accurate Execution Time Prediction

Aegaeon uses machine learning models to predict:

- Token generation latency for each model
- Resource requirements per request
- Optimal switching points during inference

#### 2. Token-Level Scheduling Algorithm

The scheduler determines model switching based on:

- **Current latency budget** remaining for the request
- **Predicted execution time** for candidate models
- **Resource availability** across the cluster
- **SLO requirements** for the request

#### 3. Model Switching Optimization

Aegaeon reduces switching overhead by **97%** through:

**Component Reuse:**

- Preserve compiled CUDA kernels across switches
- Reuse CUDA graphs between compatible models
- Share memory allocators and GPU contexts

**Fine-Grained GPU Memory Management:**

- Release only necessary memory during switches
- Maintain kernel compilation cache
- Preserve initialized CUDA contexts

**Optimized KV Cache Synchronization:**

- Efficient transfer of KV cache between models
- Minimal data copying during switches
- Selective cache preservation

### Performance Characteristics

- **Switching latency**: Sub-second (reduced from 30-100s)
- **Overhead reduction**: Up to 97% compared to traditional approaches
- **Concurrent models**: Multiple models on same GPU resources
- **SLO compliance**: Meets latency requirements through dynamic scheduling

### Use Cases

Aegaeon is particularly effective for:

- **Quality-latency trade-offs**: Switch to faster models when under
  latency pressure
- **Multi-tenant serving**: Serve different model sizes to different users
- **Cost optimization**: Use smaller models when quality requirements permit
- **Hybrid serving**: Combine large and small models for optimal cost/quality

---

## vLLM Sleep Mode: Fast Model Switching

[vLLM Sleep Mode](https://blog.vllm.ai/2025/10/26/sleep-mode.html)
(released October 2025) enables ultra-fast model switching by preserving
process state while freeing GPU memory.

### The Challenge

Multi-model serving traditionally faces a painful dilemma:

- **Simultaneous loading**: GPU memory explosion 💸
- **Frequent switching**: 30-100 second wait times 🐌

### Sleep Mode Solution

vLLM Sleep Mode provides two operational levels:

#### Level 1: CPU Memory Offloading

**Characteristics:**

- Model weights moved to CPU RAM
- CUDA context and compiled kernels preserved
- Wake-up time: **0.1-0.8 seconds**
- Suitable for memory-abundant environments

**Memory Requirements:**

- GPU memory: Released (models unloaded)
- CPU memory: Full model weights retained
- Process state: Fully preserved

#### Level 2: Complete Weight Discarding

**Characteristics:**

- Model weights completely discarded
- Only process state preserved
- Memory footprint: **MB-level only**
- Ideal for cost-sensitive deployments

**Memory Requirements:**

- GPU memory: Released
- CPU memory: Minimal (process state only)
- Reload required: Full model reload from storage

### Why Sleep Mode is Fast

Traditional model switching requires:

❌ Restarting Python process  
❌ Re-initializing CUDA contexts  
❌ Re-compiling GPU kernels  
❌ Re-capturing CUDA graphs

Sleep Mode preserves process state:

✅ Memory allocators retained  
✅ CUDA graphs preserved  
✅ JIT-compiled kernels cached  
✅ Complete process state maintained

### Performance Benchmarks

#### A100 Large Model Tests

**Qwen3-235B (TP=4):**

- Cold start: 97.7 seconds 😫
- Sleep wake-up: 5.4 seconds ⚡
- **Speedup: 18x faster**

**Qwen3-Coder-30B:**

- Cold start: 47.4 seconds 😫
- Sleep wake-up: 2.9 seconds ⚡
- **Speedup: 17x faster**

#### A4000 Small Model Tests

**Qwen3-0.6B + Phi-3-vision:**

- Wake-up time: 0.1-0.8 seconds
- Equivalent to a finger snap 🫰
- **Speedup: 58-203x faster**

#### Multi-Switch Scenarios

**5 model switches comparison:**

- Traditional: 357 seconds
- Sleep mode: 125 seconds
- **Time saved: 65% (232 seconds)**

### First Inference Optimization

Sleep mode also accelerates initial inference:

- **First token latency**: 61-88% faster
- Benefit from preserved CUDA graphs
- No kernel recompilation overhead

### Configuration and Usage

```python
# vLLM sleep mode configuration
from vllm import EngineArgs

engine_args = EngineArgs(
    model="Qwen/Qwen3-Coder-30B",
    sleep_mode="level1",  # or "level2"
    sleep_timeout=300,    # 5 minutes idle before sleep
    preserve_kv_cache=True
)
```

**Level Selection Guide:**

- **Level 1**: When you have sufficient CPU RAM and need fastest wake-up
- **Level 2**: When memory cost is critical and can tolerate slight delay

### Ideal Use Cases

✅ **Multi-model services** (customer service + translation + code assistant)  
✅ **Development/testing** (frequent model switching)  
✅ **Cost optimization** (small GPU instances)  
✅ **Cloud deployment** (pay-per-use billing)

---

## Comparison of Model Switching Approaches

| Feature | Traditional | Aegaeon | vLLM Sleep Mode | llm-d FMA | Dynamo Snapshot |
| --- | --- | --- | --- | --- | --- |
| **Switching / warm latency** | 30–100s | <1s | 0.1–5.4s | Hot wake ~seconds | Restore ~10s vs cold ~1min |
| **Granularity** | Request | Token-level | Engine process | Dual-pods + launcher | Whole-process CRIU |
| **Skips engine init** | No | Partial | Yes (wake) | Yes (hot/warm) | Yes (restore) |
| **K8s GPU accounting** | Normal Pod | Framework-specific | Normal Pod | Requester reserves GPUs | Normal worker + privileged agent |
| **Best for** | Rare swaps | Dynamic QoS | Multi-model on one GPU | Shared pool swap / scale-up | Dynamo replica scale-out |

Orchestration-level FMA and Snapshot details:
[Model Lifecycle — Fast Model Actuation](./model-lifecycle.md#fast-model-actuation)
and
[Dynamo Snapshot](./model-lifecycle.md#dynamo-snapshot-checkpoint--restore).

### When to Use Each Approach

**Use Traditional Switching when:**

- Running single model workloads
- Model changes are infrequent (hours/days apart)
- Memory is not constrained

**Use Aegaeon Token-Level Scheduling when:**

- Need quality-latency trade-offs during inference
- Serving diverse request patterns with varying SLOs
- Optimizing cost while maintaining quality thresholds
- Running production multi-model serving

**Use vLLM Sleep Mode when:**

- Supporting multiple models on same hardware
- Development and testing environments
- Cost-sensitive cloud deployments
- Models have predictable idle periods

**Use llm-d FMA when:**

- Need Kubernetes-accurate GPU reservation while swapping models on a shared
  pool (dual-pods)
- Combining sleep/wake with a persistent launcher for hot/warm actuation

**Use Dynamo Snapshot when:**

- Scaling Dynamo workers and must skip full cold start (download + GPU load +
  engine init)
- You can run the privileged snapshot agent and meet preview prerequisites

---

## Production Use Cases

### Multi-Tenant AI Platform

**Scenario**: SaaS platform serving different model sizes to users

**Solution**: Combine Aegaeon + Sleep Mode

- Use Aegaeon for real-time quality-latency optimization
- Use Sleep Mode to maximize GPU utilization
- Support 5-10x more models on same hardware
- Maintain SLOs while reducing costs

### Development Environment

**Scenario**: ML engineers testing multiple model variants

**Solution**: vLLM Sleep Mode Level 1

- Keep models in CPU memory for instant access
- Switch between models in 0.1-0.8 seconds
- No GPU memory waste from idle models
- Preserve KV cache for testing iterations

### Cost-Optimized Production

**Scenario**: Startup with limited GPU budget

**Solution**: vLLM Sleep Mode Level 2

- Minimal memory footprint per model
- Serve 10+ models on single GPU
- Accept 2-5 second wake-up latency
- Optimize for cost over absolute performance

### Hybrid Quality Serving

**Scenario**: Application with varying quality requirements

**Solution**: Aegaeon Token-Level Scheduling

- Start with large model for complex requests
- Switch to smaller model under latency pressure
- Maintain acceptable quality within SLOs
- Reduce serving costs by 30-50%

---

## Best Practices

### Architecture Design

1. **Choose the right granularity**
   - Token-level for dynamic optimization
   - Request-level for simpler implementations
   - Process-level for resource efficiency

2. **Plan memory hierarchy**
   - GPU memory: Hot models
   - CPU memory: Warm models (Sleep Mode Level 1)
   - Disk/Storage: Cold models (Sleep Mode Level 2)

3. **Implement intelligent routing**
   - Route requests to appropriate models
   - Consider model affinity for KV cache reuse
   - Balance load across available instances

### Performance Optimization

1. **Monitor switching metrics**
   - Track switching frequency
   - Measure wake-up latencies (P50, P95, P99)
   - Monitor GPU memory utilization

2. **Tune sleep timeouts**
   - Balance latency vs. resource utilization
   - Use different timeouts for different model tiers
   - Consider usage patterns in timeout selection

3. **Optimize KV cache handling**
   - Preserve cache for long conversations
   - Implement cache eviction policies
   - Consider cache compression for storage

### Reliability

1. **Handle failures gracefully**
   - Implement fallback for failed wake-ups
   - Monitor wake-up success rates
   - Plan for graceful degradation

2. **Maintain service quality**
   - Set appropriate SLO thresholds
   - Monitor quality metrics post-switching
   - Alert on excessive switching latency

3. **Test switching scenarios**
   - Validate switching under load
   - Test edge cases (rapid switching, concurrent wake-ups)
   - Verify KV cache correctness after switches

---

## References

### Aegaeon

- [Alibaba Aegaeon Article (Chinese)](https://mp.weixin.qq.com/s/uJyk0HALKFZysTAgghjgpw)

### vLLM Sleep Mode

- [vLLM Sleep Mode Blog Post](https://blog.vllm.ai/2025/10/26/sleep-mode.html)
- [vLLM Sleep Mode on Xiaohongshu (Chinese)](https://www.xiaohongshu.com/explore/6900caf20000000005001c46)
- [vLLM GitHub Repository](https://github.com/vllm-project/vllm)

### Related Documentation

- [Model Lifecycle Management](./model-lifecycle.md)
- [llm-d Fast Model Actuation](https://github.com/llm-d-incubation/llm-d-fast-model-actuation)
- [Dynamo Snapshot](./model-lifecycle.md#dynamo-snapshot-checkpoint--restore)
- [Caching in LLM Inference](./caching.md)
- [AIBrix Platform](./aibrix.md)
- [Serverless AI Inference](./serverless.md)

---

**Note**: Some content about Aegaeon is based on the referenced WeChat article.
vLLM Sleep Mode benchmarks are from the official vLLM blog post. Please verify
current project status and performance characteristics for your specific
hardware and workload before implementation.
