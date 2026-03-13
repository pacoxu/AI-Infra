---
status: Active
maintainer: pacoxu
last_updated: 2025-10-29
tags: inference, model-lifecycle, cold-start, offloading, optimization
canonical_path: docs/inference/model-lifecycle.md
---

# Model Cold-Starting, Sleep Mode, and Lifecycle Management

This document covers model lifecycle management in LLM inference systems,
focusing on cold-start optimization, sleep mode, model offloading, and fast
model actuation. These techniques are critical for efficient resource
utilization, cost reduction, and maintaining low latency in production
inference systems.

## Table of Contents

- [Overview](#overview)
- [Model Cold-Start Optimization](#model-cold-start-optimization)
- [Sleep Mode and Wake-Up](#sleep-mode-and-wake-up)
- [Model Offloading](#model-offloading)
- [Fast Model Actuation](#fast-model-actuation)
- [KV Cache Persistence](#kv-cache-persistence)
- [Production Implementations](#production-implementations)
- [Best Practices](#best-practices)
- [References](#references)

---

## Overview

Model lifecycle management addresses the challenge of efficiently managing
LLM resources across their operational states:

- **Cold Start**: Loading and initializing models from storage
- **Active Serving**: Model actively processing inference requests
- **Sleep Mode**: Temporarily pausing inactive models to free resources
- **Wake-Up**: Quickly reactivating sleeping models when needed
- **Offloading**: Moving models between storage tiers (GPU, CPU, disk)
- **Shutdown**: Completely unloading models from memory

![LLM Model Lifecycle](https://github.com/user-attachments/assets/f45727ca-526e-4e78-8afc-b1b085a24fc1)

*Figure 1: LLM Model Lifecycle State Diagram - Models transition through
various states from cold start to shutdown, with sleep mode and offloading
as intermediate optimization states.*

**Key Challenges:**

- Model loading can take seconds to minutes depending on model size
- GPU memory is limited and expensive
- Multiple models compete for the same resources
- Users expect low latency even for infrequently accessed models
- Inefficient lifecycle management leads to resource waste

**Benefits of Optimized Lifecycle Management:**

- Reduced infrastructure costs through better resource utilization
- Support for more models on the same hardware (oversubscription)
- Lower latency through intelligent preloading and caching
- Improved user experience with faster model switching
- Energy efficiency through sleep mode for idle models

---

## Model Cold-Start Optimization

**For comprehensive GPU Pod cold start strategies including pre-warmed pools,
faster serialization formats, and lazy loading patterns, see
[GPU Pod Cold Start Optimization](../kubernetes/gpu-pod-cold-start.md).**

Model cold-start refers to the time required to load a model from storage,
initialize it, and prepare it for inference. This includes loading model
weights, initializing GPU memory, compiling kernels, and warming up caches.
This section focuses on model-level optimizations, while the GPU Pod Cold Start
guide covers container and orchestration-level strategies.

### Cold-Start Components

The total cold-start time consists of several phases:

1. **Model Weight Loading** (typically 5-30 seconds)
   - Read model weights from disk/object storage
   - Transfer weights to GPU memory
   - Dependent on model size and storage I/O speed

2. **Model Initialization** (typically 2-10 seconds)
   - Initialize model architecture
   - Allocate GPU memory buffers
   - Set up attention mechanisms and caches

3. **Kernel Compilation** (typically 1-5 seconds)
   - Compile CUDA kernels for the specific GPU
   - May use cached compiled kernels
   - First-time compilation can be expensive

4. **Cache Warm-Up** (typically 0-2 seconds)
   - Populate internal caches
   - Run initial inference passes
   - Optimize memory layouts

### Optimization Strategies

#### Storage Tier Optimization

Choose the appropriate storage tier based on access patterns:

![Model Storage Tiers for LLM Inference](https://github.com/user-attachments/assets/8d2df23c-4dff-4100-952b-f6c95eb2e3b3)

*Figure 2: Model Storage Tiers for LLM Inference - Hierarchical storage
architecture from GPU VRAM (fastest) to remote object storage (slowest),
with transfer mechanisms between tiers.*

- **VRAM (GPU Memory)**: Fastest, for hot models
  - Zero cold-start latency for loaded models
  - Limited capacity (16GB-80GB per GPU)

- **RAM (Host Memory)**: Fast, for warm models
  - Sub-second transfer to GPU via PCIe
  - Larger capacity (256GB-2TB per node)

- **SSD (Local Storage)**: Moderate speed, for cached models
  - 1-5 second load time depending on model size
  - High capacity (1TB-16TB per node)

- **Remote Storage**: Slowest, for cold models
  - 5-30+ second load time including network transfer
  - Unlimited capacity via object storage

#### Model Format Optimization

Use optimized model formats to reduce loading time:

- **Safetensors**: Faster and safer than pickle-based formats
- **Memory-mapped files**: Avoid copying entire model into memory
- **Pre-compiled kernels**: Cache compiled CUDA kernels
- **Quantized models**: Smaller size, faster loading, lower memory usage

#### Predictive Preloading

Anticipate model usage patterns and preload models:

- **Usage pattern analysis**: Track model access patterns
- **Time-based preloading**: Load models before expected usage periods
- **Request-triggered preloading**: Start loading when first requests arrive
- **Collaborative filtering**: Predict model usage based on user patterns

---

## Sleep Mode and Wake-Up

Sleep mode allows inference systems to temporarily pause inactive models,
freeing GPU resources while maintaining fast reactivation capabilities.

### vLLM Sleep Mode

[vLLM](https://github.com/vllm-project/vllm) introduced sleep mode in October
2025, enabling efficient resource management for multi-model serving. Sleep
mode enables **18-200x faster** model switching compared to traditional cold
starts.

**Key Features:**

- **Automatic sleep**: Models automatically enter sleep mode after inactivity
- **GPU memory release**: Frees GPU memory while preserving model state
- **Fast wake-up**: Quickly restore models from sleep state
- **KV cache preservation**: Optionally preserve KV cache during sleep
- **Configurable timeouts**: Customize sleep timeout per model

**Architecture:**

Sleep mode operates through a state machine:

1. **Active State**: Model actively processing requests
2. **Idle Detection**: Monitor for inactivity period (e.g., 5 minutes)
3. **Sleep Preparation**: Serialize model state and KV cache
4. **Sleep State**: Release GPU memory, keep CPU state
5. **Wake-Up Trigger**: Restore model when new request arrives
6. **Active State**: Resume inference processing

**Two Operating Levels:**

#### Level 1: CPU Memory Offloading

- Model weights moved to CPU RAM
- Wake-up time: 0.1-0.8 seconds
- Suitable for memory-abundant environments
- Fastest wake-up performance

#### Level 2: Complete Weight Discarding

- Model weights completely discarded
- Memory footprint: MB-level only
- Ideal for cost-sensitive deployments
- Requires full model reload on wake-up

**Why Sleep Mode is Fast:**

Traditional model switching requires:

- ❌ Restarting Python process
- ❌ Re-initializing CUDA contexts
- ❌ Re-compiling GPU kernels
- ❌ Re-capturing CUDA graphs

Sleep mode preserves process state:

- ✅ Memory allocators retained
- ✅ CUDA graphs preserved
- ✅ JIT-compiled kernels cached
- ✅ Complete process state maintained

**Performance Benchmarks:**

*A100 Large Model Tests:*

- **Qwen3-235B (TP=4)**
  - Cold start: 97.7 seconds
  - Sleep wake-up: 5.4 seconds
  - **18x faster**

- **Qwen3-Coder-30B**
  - Cold start: 47.4 seconds
  - Sleep wake-up: 2.9 seconds
  - **17x faster**

*A4000 Small Model Tests:*

- **Qwen3-0.6B + Phi-3-vision**
  - Wake-up time: 0.1-0.8 seconds
  - **58-203x faster** than cold start

*Multi-Switch Scenarios:*

- 5 model switches: 357s → 125s
- **Time saved: 65% (232 seconds)**

**First Inference Acceleration:**

- First token latency: **61-88% faster**
- Benefits from preserved CUDA graphs
- No kernel recompilation overhead

**Benefits:**

- Support 5-10x more models on the same GPU hardware
- Reduce GPU memory waste from idle models
- Near-instant wake-up compared to cold-start
- Preserve KV cache for returning users

**Configuration Example:**

```python
# vLLM sleep mode configuration
engine_config = {
    "sleep_mode_enabled": True,
    "sleep_mode_level": "level1",  # or "level2"
    "sleep_timeout_seconds": 300,  # 5 minutes
    "preserve_kv_cache": True,
    "max_sleeping_models": 10
}
```

**Use Cases:**

- ✅ Multi-model services (customer service + translation + code assistant)
- ✅ Development and testing (frequent model switching)
- ✅ Cost optimization (small GPU instances)
- ✅ Cloud deployment (pay-per-use billing)

**Level Selection Guide:**

- **Choose Level 1** when you have sufficient CPU RAM and need the fastest
  wake-up times (0.1-0.8s)
- **Choose Level 2** when memory cost is critical and you can tolerate
  slightly longer wake-up times

For comprehensive model switching documentation including Alibaba Aegaeon's
token-level scheduling, see [Model Switching](./model-switching.md).

For more details, see the
[vLLM Sleep Mode Blog Post](https://blog.vllm.ai/2025/10/26/sleep-mode.html)
and [Xiaohongshu Article (Chinese)](https://www.xiaohongshu.com/explore/6900caf20000000005001c46).

### Wake-Up Optimization

Fast wake-up is critical for maintaining low latency:

- **Partial state restoration**: Only restore essential model components
- **Progressive loading**: Start inference before full restoration
- **Memory pinning**: Keep model weights in host memory
- **State compression**: Compress sleeping state to reduce restoration time

---

## Model Offloading

Model offloading moves models between different storage tiers based on
access patterns and resource availability. This enables oversubscription of
GPU resources and cost-effective multi-model serving.

### Offloading Strategies

#### Full Model Offloading

Move entire model between storage tiers:

- **GPU to CPU Memory**: Fast transfer via PCIe (sub-second)
- **CPU Memory to SSD**: Moderate speed, useful for long-term storage
- **SSD to Remote Storage**: Slow but unlimited capacity

**Trade-offs:**

- Pros: Complete GPU memory release, simple state management
- Cons: Longer reactivation time, all-or-nothing approach

#### Layer-by-Layer Offloading

Offload model layers individually:

- Keep frequently accessed layers on GPU
- Move infrequently accessed layers to CPU or disk
- Dynamically adjust layer placement based on usage

**Trade-offs:**

- Pros: Fine-grained control, better GPU utilization
- Cons: Complex management, potential pipeline stalls

#### Adaptive Offloading

Automatically adjust offloading based on system state:

- Monitor GPU memory pressure
- Track model access patterns
- Optimize for latency vs. cost trade-offs
- Implement eviction policies (LRU, LFU, usage prediction)

### Hardware Acceleration for Offloading

Modern hardware features accelerate model offloading:

- **PCIe Gen 4/5**: 16-32 GB/s bidirectional for CPU-GPU transfers
- **NVLink**: 300-900 GB/s for multi-GPU systems
- **CXL (Compute Express Link)**: Memory-semantic access to remote memory
- **High-speed RDMA**: Fast transfers between nodes

---

## Fast Model Actuation

Fast model actuation refers to techniques that minimize the time to switch
between different models or model configurations in an inference system.

### llm-d Fast Model Actuation

The
[llm-d fast-model-actuation](https://github.com/llm-d-incubation/llm-d-fast-model-actuation)
project provides mechanisms for rapid model switching in Kubernetes
environments.

**Key Features:**

- **Preloaded model pool**: Maintain pool of ready-to-use models
- **Model routing**: Intelligent routing to available model instances
- **Resource management**: Efficient allocation of GPU resources
- **Kubernetes integration**: Native support for K8s scheduling

**Architecture Components:**

1. **Model Pool Manager**: Maintains pool of preloaded models
2. **Router**: Directs requests to appropriate model instances
3. **Resource Controller**: Manages GPU allocation and deallocation
4. **State Manager**: Tracks model states and transitions

**Actuation Strategies:**

- **Static Pool**: Pre-allocate models based on expected usage
- **Dynamic Pool**: Adjust pool size based on real-time demand
- **Hybrid Pool**: Combine static base with dynamic expansion

### Model Switching Techniques

#### In-Memory Switching

Keep multiple models in GPU memory and switch between them:

- **Multi-model batching**: Run different models in same batch
- **Time-sliced switching**: Alternate models on time intervals
- **Priority-based switching**: Switch based on request priority

**Trade-offs:**

- Pros: Zero switching latency, high throughput
- Cons: Limited by GPU memory capacity

#### LoRA Adapter Switching

Use Low-Rank Adaptation (LoRA) for fast model switching:

- Base model stays in memory
- Swap lightweight LoRA adapters (typically 10-100MB)
- Sub-second switching time
- Support hundreds of adapters per base model

**Benefits:**

- Minimal memory overhead per variant
- Fast switching between model variants
- Cost-effective multi-tenant serving

---

## KV Cache Persistence

Preserving KV cache across model lifecycle transitions is critical for
maintaining user experience and reducing recomputation costs.

### KV Cache Offloading

The [kvcached project](https://github.com/ovg-project/kvcached) provides
mechanisms for persisting KV cache during model transitions.

**Key Features:**

- **KV cache serialization**: Save KV cache to persistent storage
- **Fast restoration**: Quickly restore KV cache when model wakes up
- **Compression**: Reduce storage requirements for cached data
- **Distributed storage**: Share KV cache across multiple instances

**Architecture:**

1. **Cache Capture**: Serialize active KV cache before sleep
2. **Storage Backend**: Write to fast storage tier (SSD, object storage)
3. **Cache Index**: Maintain index of cached conversations
4. **Cache Restoration**: Reload relevant cache on wake-up

**Benefits:**

- Resume conversations without recomputing history
- Reduce user-perceived latency after model wake-up
- Support longer context windows with persistent cache
- Enable cross-instance KV cache sharing

### Integration with Sleep Mode

Combining KV cache persistence with sleep mode:

```python
# Conceptual sleep mode with KV cache persistence
async def sleep_model(model_id):
    # 1. Capture KV cache
    kv_cache = capture_kv_cache(model_id)
    
    # 2. Serialize and store
    cache_id = await store_kv_cache(kv_cache)
    
    # 3. Release GPU memory
    release_gpu_memory(model_id)
    
    # 4. Store wake-up metadata
    save_wake_metadata(model_id, cache_id)

async def wake_model(model_id):
    # 1. Load model to GPU
    await load_model_to_gpu(model_id)
    
    # 2. Restore KV cache
    metadata = load_wake_metadata(model_id)
    kv_cache = await restore_kv_cache(metadata.cache_id)
    
    # 3. Resume inference
    inject_kv_cache(model_id, kv_cache)
```

For more comprehensive information about KV cache management, see
[Caching in LLM Inference](./caching.md).

---

## Production Implementations

### AIBrix Multi-Model Management

[AIBrix](https://github.com/vllm-project/aibrix) provides production-ready
multi-model lifecycle management:

- **Dynamic model loading**: Load models on-demand
- **LoRA multiplexing**: Efficient switching between LoRA adapters
- **Resource optimization**: Intelligent GPU memory management
- **Gateway integration**: Request routing with model affinity

### KServe Model Server

[KServe](https://github.com/kserve/kserve) offers model lifecycle capabilities:

- **Scale-to-zero**: Automatically scale down to zero replicas
- **Fast scale-up**: Quick model loading on first request
- **Knative integration**: Serverless model serving
- **Multi-framework support**: Works with various inference engines

### Kubernetes-Native Solutions

Kubernetes-based platforms for model lifecycle management:

- **Kthena**: Volcano-based LLM inference platform with ModelServing revision
  control, rolling updates, and plugin framework (v0.3.0+)
- **Kubeflow**: Comprehensive ML platform with model serving

---

## Best Practices

### When to Use Each Technique

**Use Sleep Mode when:**

- Models have predictable idle periods (>5 minutes)
- Supporting multiple models per GPU
- Cost optimization is priority over absolute lowest latency
- Users can tolerate 1-3 second wake-up latency

**Use Model Offloading when:**

- GPU memory is severely constrained
- Supporting very large model catalogs
- Access patterns are highly variable
- Infrastructure costs are a primary concern

**Use Fast Model Actuation when:**

- Frequent model switching is required
- Sub-second switching latency is needed
- Using LoRA or adapter-based models
- Running in orchestrated environments like Kubernetes

**Use KV Cache Persistence when:**

- Users have long conversations
- Model undergoes sleep/wake cycles
- Context preservation is critical for user experience
- Serving costs are high due to recomputation

### Design Guidelines

#### Resource Planning

- Monitor actual vs. theoretical GPU memory usage
- Plan for 20-30% memory overhead beyond model weights
- Account for KV cache growth with context length
- Implement memory pressure detection and response

#### Latency Management

- Set appropriate timeout thresholds for sleep mode
- Implement predictive preloading for common patterns
- Use LoRA adapters for sub-second model switching
- Monitor P95/P99 latency for wake-up operations

#### Reliability

- Implement health checks for sleeping models
- Monitor wake-up success rates and failure modes
- Maintain backup replicas for critical models
- Plan for graceful degradation under resource pressure

#### Cost Optimization

- Balance GPU utilization vs. latency requirements
- Use sleep mode for dev/test environments
- Implement tiered service levels (premium vs. standard)
- Monitor cost per inference and optimize accordingly

### Monitoring and Observability

Key metrics to track:

- **Cold-start latency**: Time from request to first token
- **Wake-up latency**: Time from sleep to active state
- **Sleep transition time**: Time to enter sleep mode
- **GPU memory utilization**: Before and after lifecycle transitions
- **Model switching rate**: Frequency of model changes
- **KV cache hit rate**: Percentage of restored vs. recomputed cache

---

## References

- [vLLM Sleep Mode Blog Post](https://blog.vllm.ai/2025/10/26/sleep-mode.html)
- [kvcached Project](https://github.com/ovg-project/kvcached)
- [llm-d Fast Model Actuation](https://github.com/llm-d-incubation/llm-d-fast-model-actuation)
- [vLLM GitHub Repository](https://github.com/vllm-project/vllm)
- [AIBrix Introduction](./aibrix.md)
- [Caching in LLM Inference](./caching.md)
- [KServe Model Server](https://github.com/kserve/kserve)
- [Kubernetes Serving WG](https://github.com/kubernetes/community/blob/master/wg-serving/README.md)

**Some content was organized based on provided GitHub references and blog
posts. Please verify technical details and current project status before
implementation.**
