---
status: Active
maintainer: pacoxu
last_updated: 2025-10-30
tags: inference, llm, model-architecture, moe, dense, llama, qwen, deepseek, flux
canonical_path: docs/inference/model-architectures.md
---

# LLM Model Architectures

This document provides an overview of major LLM model architectures,
covering both dense and Mixture-of-Experts (MoE) approaches. Understanding
these architectures is essential for selecting the right model for your
deployment and optimizing inference performance.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Dense Models](#dense-models)
  - [Llama 3](#llama-3)
- [Mixture-of-Experts (MoE) Models](#mixture-of-experts-moe-models)
  - [Llama 4](#llama-4)
  - [Qwen 3](#qwen-3)
  - [DeepSeek-V3](#deepseek-v3)
- [Diffusion Models](#diffusion-models)
  - [Flux](#flux)
- [Architecture Comparison](#architecture-comparison)
- [MoE Key Benefits](#moe-key-benefits)
- [References](#references)

---

## Architecture Overview

Modern LLM architectures can be broadly categorized into two main approaches:

**Dense Models:** Traditional transformer architectures where all parameters
are activated for every token. These models offer predictable performance
and simpler deployment but scale linearly with parameter count.

**Mixture-of-Experts (MoE) Models:** Advanced architectures that activate
only a subset of specialized "expert" networks for each token. MoE models
achieve superior parameter efficiency and can scale to much larger total
parameter counts while maintaining fast inference speeds.

---

## Dense Models

Dense models activate all parameters for every input token, providing
consistent and predictable behavior. They are well-understood, widely
supported by inference engines, and offer excellent quality for their
parameter count.

### Llama 3

[`Llama 3`](https://github.com/meta-llama/llama3) is Meta's
third-generation dense transformer architecture, representing state-of-the-art
performance for open-source dense models.

**Architecture Characteristics:**

- **Model Type:** Dense transformer (decoder-only)
- **Available Sizes:** 8B, 70B, and 405B parameters
- **Context Length:** Up to 128K tokens (extended context versions)
- **Training Data:** 15+ trillion tokens across diverse domains
- **Tokenizer:** Enhanced tokenizer with 128K vocabulary size
- **Architecture Features:**
  - Grouped Query Attention (GQA) for efficient inference
  - RoPE (Rotary Position Embeddings) for position encoding
  - SwiGLU activation function in feed-forward layers
  - Pre-normalization with RMSNorm

**Key Specifications (Llama 3.1):**

| Model | Parameters | Hidden Size | Layers | Attention Heads | KV Heads |
|-------|-----------|-------------|--------|-----------------|----------|
| Llama 3.1 8B | 8B | 4096 | 32 | 32 | 8 |
| Llama 3.1 70B | 70B | 8192 | 80 | 64 | 8 |
| Llama 3.1 405B | 405B | 16384 | 126 | 128 | 8 |

**Advantages:**

- **Quality:** Leading performance among open-source dense models
- **Efficiency:** GQA reduces KV cache size and improves throughput
- **Long Context:** Native support for extended context lengths
- **Ecosystem:** Extensive tooling and inference engine support

**Inference Considerations:**

- Straightforward deployment on single or multi-GPU setups
- Well-supported by all major inference engines (vLLM, SGLang, TensorRT-LLM)
- Memory requirements scale linearly with model size
- Optimal for applications requiring consistent latency

**Use Cases:**

- General-purpose chat and assistant applications
- High-quality content generation
- Code generation and analysis
- Long-document understanding and summarization

---

## Mixture-of-Experts (MoE) Models

MoE models revolutionize LLM architecture by introducing sparsely activated
expert networks. Instead of processing every token through all parameters,
MoE models route tokens to a small subset of specialized experts, dramatically
improving parameter efficiency and inference speed.

**Core MoE Principles:**

1. **Sparse Activation:** Only a fraction of the model's parameters are
   active for each token (typically 10-20% of experts)
2. **Expert Specialization:** Different experts learn to handle different
   types of inputs (languages, domains, task types)
3. **Dynamic Routing:** A gating network learns to select the most relevant
   experts for each input token
4. **Parameter Efficiency:** Achieve quality comparable to much larger dense
   models while using fewer active parameters per token

For comprehensive details on MoE architectures, see
[Large Scale Experts (MoE Models)](./large-scale-experts.md).

### Llama 4

**Note:** Llama 4 is anticipated but not yet released. All specifications
presented here are hypothetical and based on expected architectural trends
in MoE evolution from Llama 3. These details should be verified against
official documentation when the model is released.

Llama 4 is expected to represent Meta's evolution to Mixture-of-Experts
architecture, combining the architectural advances of Llama 3 with sparse
expert activation for improved efficiency and scale.

**Architecture Characteristics:**

- **Model Type:** MoE transformer (decoder-only)
- **Expert Configuration:** Multiple specialized expert networks
- **Routing Strategy:** Top-K expert selection per token
- **Total Parameters:** Significantly larger than Llama 3, but with
  comparable active parameters per token
- **Core Features:**
  - Inherits GQA from Llama 3 architecture
  - RoPE positional embeddings
  - SwiGLU activation in expert networks
  - Load-balanced routing for expert utilization

**MoE Design:**

```text
Input Token
    ↓
Shared Self-Attention Layer (Dense)
    ↓
Router Network
    ↓
Top-K Expert Selection
    ↓
[Expert 1] [Expert 2] ... [Expert N] (only top-K activated)
    ↓
Weighted Expert Output Aggregation
    ↓
Output
```

**Advantages over Dense Llama 3:**

- **Inference Speed:** 2-3x faster inference for similar quality levels
- **Memory Efficiency:** Lower active parameter count per token
- **Scalability:** Can scale to larger total parameter counts
- **Specialization:** Experts can specialize for different domains/languages

**Inference Considerations:**

- Requires expert-aware inference engines (vLLM, SGLang, TensorRT-LLM)
- All-to-all communication patterns for expert routing
- Expert parallelism needed for multi-GPU deployment
- Dynamic load balancing across experts

**Use Cases:**

- High-throughput serving applications
- Multi-domain and multilingual applications
- Cost-sensitive deployments requiring maximum efficiency
- Applications where inference speed is critical

### Qwen 3

[`Qwen 3`](https://github.com/QwenLM/Qwen) (Qwen2.5 series) from
Alibaba Cloud implements a flexible hybrid architecture supporting both
dense and MoE configurations, providing deployment flexibility for different
use cases.

**Architecture Characteristics:**

- **Model Type:** Hybrid - both dense and MoE variants available
- **Available Configurations:**
  - **Dense Models:** 0.5B, 1.5B, 3B, 7B, 14B, 32B, 72B parameters
  - **MoE Models:** Qwen2.5-MoE with multiple expert configurations
- **Context Length:** Up to 32K tokens (128K for some variants)
- **Multilingual:** Strong support for English and Chinese
- **Training:** Extensive training on code, math, and multilingual data

**MoE Configuration (Qwen2.5-MoE):**

| Model | Total Params | Active Params | Experts | Experts/Token |
|-------|-------------|---------------|---------|---------------|
| Qwen2.5-MoE-A2.7B | ~14B | 2.7B | 60 | 8 |
| Qwen2.5-MoE-A14B | ~65B | 14B | 64 | 8 |

**Unique Features:**

- **Hybrid Approach:** Both dense and MoE variants with consistent API
- **Fine-Grained Experts:** Large number of smaller experts for better
  specialization
- **Code Optimization:** Specialized experts for programming tasks
- **Multi-Expert Routing:** Routes each token to multiple (8) experts for
  better quality

**Architecture Highlights:**

- Grouped Query Attention (GQA) for efficient KV cache
- RoPE with extended context support
- Enhanced tokenizer with multilingual support
- Load-balanced expert routing with auxiliary loss

**Advantages:**

- **Flexibility:** Choose between dense and MoE based on deployment needs
- **Quality:** Leading performance on Chinese and code benchmarks
- **Efficiency:** MoE variants provide excellent quality-to-cost ratio
- **Deployment:** Smooth migration path between dense and MoE versions

**Inference Considerations:**

- Dense models: Standard deployment patterns
- MoE models: Require expert parallelism with 60+ experts
- Consider expert caching strategies for frequently used experts
- Load balancing is critical due to high expert count

**Use Cases:**

- **Dense variants:** Single-GPU deployments, latency-critical applications
- **MoE variants:** High-throughput serving, multilingual applications
- Hybrid deployments for different endpoints
- Code generation and analysis tasks

### DeepSeek-V3

[`DeepSeek-V3`](https://github.com/deepseek-ai/DeepSeek-V3)
represents the state-of-the-art in large-scale MoE architectures, pushing
the boundaries of efficient scaling with 256 experts and advanced routing
mechanisms.

**Architecture Characteristics:**

- **Model Type:** Large-scale MoE transformer (decoder-only)
- **Total Parameters:** 671B total, 37B active per token
- **Expert Configuration:** 256 experts with multi-token prediction
- **Context Length:** Up to 128K tokens
- **Training:** Multi-stage training with expert specialization
- **Routing Strategy:** Advanced load-balanced routing with auxiliary losses

**Advanced MoE Features:**

- **Multi-Token Prediction:** Experts can predict multiple future tokens
- **Hierarchical Expert Organization:** Experts grouped by specialization
- **Dynamic Expert Capacity:** Adaptive capacity allocation per expert
- **Fine-Grained Load Balancing:** Sophisticated routing algorithms to
  prevent expert collapse

**Architecture Specifications:**

```text
Total Parameters: 671B
Active Parameters per Token: 37B (~5.5% activation rate)
Number of Experts: 256
Experts Activated per Token: Variable (typically 6-8)
Expert Size: ~2.6B parameters each
Hidden Dimensions: 7168
Number of Layers: 61
Attention Heads: 128 (16 KV heads with GQA)
```

**Key Innovations:**

1. **Large-Scale Expert Parallelism:**
   - 256 experts enable unprecedented specialization
   - Hierarchical expert distribution across GPUs
   - Optimized all-to-all communication patterns

2. **Multi-Token Prediction:**
   - Experts can predict multiple future tokens simultaneously
   - Improves throughput for autoregressive generation
   - Reduces sequential dependency in decoding

3. **Expert Specialization:**
   - Domain-specific experts (math, code, reasoning)
   - Language-specific experts for multilingual support
   - Task-type experts (QA, generation, analysis)

4. **Load Balancing:**
   - Auxiliary loss functions to encourage balanced expert usage
   - Dynamic capacity allocation prevents expert overload
   - Monitoring and adjustment during inference

**Performance Characteristics:**

| Metric | DeepSeek-V3 | GPT-4 | Notes |
|--------|------------|-------|-------|
| Active Params | 37B | ~1.7T (est.) | ~46x fewer active params |
| Inference Speed | 3x faster | Baseline | At similar quality |
| Memory per Token | 65% lower | Baseline | Due to sparse activation |
| Training Efficiency | 4x faster | Dense equivalent | Per training FLOP |

**Advantages:**

- **Extreme Efficiency:** Massive total capacity with minimal active compute
- **Quality:** GPT-4 level performance at fraction of active parameter cost
- **Specialization:** 256 experts enable fine-grained domain expertise
- **Scalability:** Proven architecture for scaling beyond trillion parameters
- **Cost-Effective:** Dramatically lower serving costs than dense equivalents

**Inference Considerations:**

- Requires 32+ GPUs for efficient deployment
- Expert parallelism is mandatory (distribute 256 experts)
- High-bandwidth interconnect critical (NVLink, InfiniBand)
- Sophisticated load balancing and monitoring required
- Consider expert caching for frequently activated experts

**Deployment Patterns:**

```yaml
# Example: DeepSeek-V3 multi-node deployment
# Conceptual configuration
apiVersion: v1
kind: Service
metadata:
  name: deepseek-v3
spec:
  replicas: 8  # Data parallelism: 8 replicas
  template:
    spec:
      containers:
      - name: vllm
        args:
        # Each replica uses 32 GPUs for expert parallelism
        - --tensor-parallel-size=2  # Shared layers
        - --expert-parallel-size=16  # 256/16 = 16 experts per GPU
        resources:
          limits:
            nvidia.com/gpu: "32"
```

**Use Cases:**

- **Enterprise LLM Serving:** Organizations requiring GPT-4 quality at
  lower cost
- **Multi-Domain Applications:** Systems handling diverse query types
- **High-Throughput Inference:** Serving thousands of requests per second
- **Research Platforms:** Exploring large-scale MoE architectures
- **Multilingual Services:** Global applications requiring many languages

**Challenges:**

- Complex deployment requiring significant infrastructure
- Requires expert-aware orchestration and monitoring
- Load balancing and expert utilization optimization
- Higher setup complexity compared to dense models

---

## Diffusion Models

While transformer-based LLMs dominate text generation, diffusion models
have become the state-of-the-art for image generation and other modalities.

### Flux

[`Flux`](https://github.com/black-forest-labs/flux) is a
state-of-the-art text-to-image diffusion model developed by Black Forest
Labs, representing the latest advances in image generation quality and
efficiency.

**Architecture Characteristics:**

- **Model Type:** Latent diffusion transformer
- **Available Variants:**
  - **Flux.1 [pro]:** Highest quality, API-only
  - **Flux.1 [dev]:** Open weights, non-commercial license
  - **Flux.1 [schnell]:** Fast variant, Apache 2.0 license
- **Total Parameters:** 12B parameters
- **Architecture:** Flow-matching transformer with parallel attention paths

**Key Features:**

- **Hybrid Architecture:** Combines diffusion process with transformer layers
- **Flow Matching:** Advanced training technique for improved quality
- **Parallel Attention:** Separate text and image attention paths
- **Guidance Distillation:** Enables high-quality generation without CFG
  (Classifier-Free Guidance) in schnell variant

**Architecture Components:**

```text
Text Input
    ↓
Text Encoder (T5 or CLIP)
    ↓
[Transformer Blocks with Parallel Attention]
    ├─ Text Attention Path
    └─ Image Latent Attention Path
    ↓
Flow Matching Diffusion Process
    ↓
VAE Decoder
    ↓
Generated Image
```

**Specifications by Variant:**

| Variant | Steps | Speed | Quality | License |
|---------|-------|-------|---------|---------|
| Flux.1 [pro] | 50 | Slower | Highest | Proprietary (API) |
| Flux.1 [dev] | 50 | Medium | High | Non-commercial |
| Flux.1 [schnell] | 4 | Fast | Good | Apache 2.0 |

**Advantages:**

- **Quality:** State-of-the-art image generation quality
- **Prompt Adherence:** Exceptional understanding of complex prompts
- **Efficiency:** Schnell variant generates in 4 steps (vs 50+ for SD)
- **Open Weights:** Dev and schnell variants available for deployment
- **Flexibility:** Multiple variants for different speed/quality trade-offs

**Inference Considerations:**

- Requires substantial GPU memory (12B parameters + VAE)
- Batching multiple requests improves throughput
- Schnell variant suitable for real-time applications
- Can be combined with LoRA for fine-tuned styles
- Supports various aspect ratios and resolutions

**Deployment Patterns:**

```python
# Example: Flux inference with Diffusers library
from diffusers import FluxPipeline

pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell",
    torch_dtype=torch.bfloat16
)
pipe.to("cuda")

# Fast generation (4 steps)
image = pipe(
    prompt="A serene landscape with mountains",
    num_inference_steps=4,
    guidance_scale=0.0  # Guidance distilled, not needed
).images[0]
```

**Use Cases:**

- **Creative Tools:** AI art generation, design assistance
- **Marketing:** Product visualization, ad creative generation
- **Gaming:** Asset generation, concept art
- **E-commerce:** Product image generation and variation
- **Real-time Applications:** Live image generation (with schnell variant)

**Integration with LLM Infrastructure:**

Flux models can be deployed alongside LLM inference infrastructure:

- Shared GPU pools for multi-modal applications
- Combined text-to-image pipelines with LLM prompt enhancement
- Unified API gateway for text and image generation
- Resource scheduling considering both LLM and diffusion workloads

---

## Architecture Comparison

Understanding the trade-offs between different architectures helps in
selecting the right model for your use case.

### Dense vs. MoE Comparison

| Aspect | Dense (Llama 3) | MoE (DeepSeek-V3, Llama 4) |
|--------|----------------|---------------------------|
| **Active Parameters** | All parameters | 5-20% of total parameters |
| **Inference Speed** | Baseline | 2-3x faster (same quality) |
| **Memory per Token** | 100% | 35-40% |
| **Deployment Complexity** | Simple | Moderate to High |
| **Latency Predictability** | Consistent | Variable (routing overhead) |
| **Multi-Domain Quality** | Good | Excellent (specialization) |
| **Throughput Scaling** | Linear with GPUs | Superlinear (expert parallelism) |
| **Cost per Token** | Baseline | 40-60% lower |

### Model Selection Guide

#### Choose Dense Models When

- **Simple Deployment:** Single GPU or simple multi-GPU setup
- **Consistent Latency:** Predictable performance is critical
- **Small Scale:** Limited request volume
- **Single Domain:** Focused application domain
- **Debugging:** Easier to understand and troubleshoot

**Recommended:** Llama 3 (8B, 70B)

#### Choose MoE Models When

- **High Throughput:** Serving thousands of requests per second
- **Multi-Domain:** Handling diverse query types
- **Cost Efficiency:** Optimizing serving costs is priority
- **Scale:** Large deployments with multi-GPU clusters
- **Quality Priority:** Need maximum quality per active parameter

**Recommended:**

- **Moderate Scale:** Llama 4, Qwen2.5-MoE-A2.7B
- **Large Scale:** DeepSeek-V3, Qwen2.5-MoE-A14B

#### Choose Hybrid Approaches When

- **Flexible Deployment:** Different endpoints with different needs
- **Migration Path:** Gradual transition from dense to MoE
- **Mixed Workloads:** Combining latency-critical and batch workloads

**Recommended:** Qwen 3 (both dense and MoE variants available)

### Performance Comparison

Based on public benchmarks and production deployments:

| Model | Type | Active Params | Throughput (relative) | Latency (TTFT) |
|-------|------|--------------|---------------------|---------------|
| Llama 3 8B | Dense | 8B | 1.0x | 50ms |
| Llama 3 70B | Dense | 70B | 0.3x | 180ms |
| Llama 4 (est.) | MoE | ~10B | 2.5x | 45ms |
| Qwen2.5-MoE-A2.7B | MoE | 2.7B | 3.0x | 35ms |
| DeepSeek-V3 | MoE | 37B | 2.5x | 60ms |

*Note: Throughput and latency are approximate and depend heavily on
hardware, batch size, and workload characteristics.*

---

## MoE Key Benefits

Mixture-of-Experts architectures provide significant advantages over
traditional dense models, particularly for large-scale deployments. Here
are the key benefits demonstrated by models like DeepSeek-V3 and Llama 4:

### 1. Sparse Activation

**How It Works:**

MoE models activate only a subset of experts for each token, typically
5-20% of the total parameters. This sparse activation dramatically reduces
computational requirements while maintaining model capacity.

**Example (DeepSeek-V3):**

```text
Total Parameters: 671B
Active Parameters per Token: 37B
Activation Rate: 5.5%

Comparison with Dense Model:
- Dense 671B: 671B FLOPs per token
- DeepSeek-V3: 37B FLOPs per token
- Reduction: 94.5% fewer FLOPs
```

**Benefits:**

- **Lower Latency:** Fewer computations per token means faster generation
- **Higher Throughput:** Process more tokens per second with same hardware
- **Energy Efficiency:** Reduced compute translates to lower power consumption
- **Cost Savings:** 40-60% lower serving costs compared to dense equivalents

### 2. Handling Larger Parameter Counts

**The Challenge:**

Dense models scale linearly - doubling quality often requires 4-10x more
parameters, which directly increases memory, compute, and cost.

**MoE Solution:**

MoE architecture decouples total parameter count from active computation,
enabling models with hundreds of billions or even trillions of parameters
while keeping inference costs manageable.

**Real-World Example:**

| Model | Total Params | Active Params | Memory (FP16) | Inference Speed |
|-------|-------------|---------------|---------------|----------------|
| Dense GPT-4 (est.) | ~1.7T | ~1.7T | ~3.4TB | Baseline |
| DeepSeek-V3 | 671B | 37B | ~1.3TB | 3x faster |
| Quality | Comparable | Comparable | 62% less | - |

*Note: Memory figures represent model weights only. Actual inference
memory includes additional overhead for KV cache, activations, and runtime
buffers.*

**How MoE Achieves This:**

1. **Expert Specialization:** Different experts learn complementary skills
2. **Selective Activation:** Only relevant experts process each token
3. **Efficient Storage:** Experts can be distributed across multiple GPUs
4. **Dynamic Loading:** Load experts on-demand for memory efficiency

**Benefits:**

- **Massive Scale:** Models with 1T+ parameters become practical
- **Memory Efficiency:** Store experts across distributed memory
- **Flexible Deployment:** Scale by adding more GPUs with more experts
- **Future-Proof:** Architecture scales beyond current hardware limits

### 3. Improved Training Speed and Higher Accuracy

**Training Efficiency:**

MoE models achieve better quality per training FLOP compared to dense
models, enabling faster iteration and lower training costs.

**Training Speed Comparison:**

| Model Type | FLOPs to Target Quality | Training Time | Cost |
|------------|------------------------|---------------|------|
| Dense | 1.0x (baseline) | 100 days | $10M |
| MoE (similar total params) | 0.25x | 25 days | $2.5M |
| MoE (4x total params) | 0.4x | 40 days | $4M (better quality) |

**Why MoE Trains Faster:**

1. **Sparse Gradients:** Only activated experts receive gradient updates
2. **Parallel Learning:** Different experts learn different skills
   simultaneously
3. **Efficient Capacity:** More parameters without proportional compute cost
4. **Better Generalization:** Expert specialization improves overall quality

**Accuracy Improvements:**

MoE models achieve higher accuracy through specialization:

```text
Benchmark Performance (normalized to 100):

Dense 70B:
├─ Code: 75
├─ Math: 72
├─ Reasoning: 78
└─ Average: 75

MoE (DeepSeek-V3, 37B active):
├─ Code: 88 (Code-specialized experts)
├─ Math: 85 (Math-specialized experts)
├─ Reasoning: 90 (Reasoning-specialized experts)
└─ Average: 88 (17% improvement)
```

**Why MoE Has Higher Accuracy:**

- **Specialization:** Experts focus on specific domains/skills
- **Capacity:** More total parameters capture more knowledge
- **Efficiency:** Better parameter utilization per task
- **Diversity:** Different experts provide complementary capabilities

### Combined Impact

The combination of sparse activation, larger parameter counts, and improved
training creates a multiplicative effect:

**Example ROI (DeepSeek-V3 vs. Dense Equivalent):**

```text
To achieve similar quality as DeepSeek-V3 with dense model:

Dense Model Required:
- Parameters: ~200B (active)
- Training Cost: $15M
- Inference Cost per 1M tokens: $15
- Latency: 200ms TTFT

DeepSeek-V3 (MoE):
- Parameters: 37B (active), 671B (total)
- Training Cost: $6M (60% savings)
- Inference Cost per 1M tokens: $5 (67% savings)
- Latency: 60ms TTFT (70% faster)

Total 3-Year TCO Savings: ~$50M for serving-focused deployment
```

### When MoE Benefits Are Maximized

MoE advantages are most pronounced in these scenarios:

1. **High-Volume Serving:** Thousands of requests per second
2. **Multi-Domain Applications:** Diverse query types benefit from
   specialization
3. **Cost-Sensitive Deployments:** Optimizing $/token is priority
4. **Quality Requirements:** Need state-of-the-art performance
5. **Long-Term Deployments:** Initial complexity pays off over time

### Implementation Considerations

To realize these benefits, consider:

- **Inference Engine:** Use MoE-aware engines (vLLM, SGLang, TensorRT-LLM)
- **Hardware:** High-bandwidth interconnects for expert communication
- **Monitoring:** Track expert utilization and load balancing
- **Optimization:** Tune expert parallelism and caching strategies

For detailed implementation guidance, see:

- [Large Scale Experts (MoE Models)](./large-scale-experts.md)
- [Model Lifecycle Management](./model-lifecycle.md)

---

## References

### Official Model Documentation

- [Llama 3 Model Card](https://github.com/meta-llama/llama3)
- [Qwen 3 Documentation](https://github.com/QwenLM/Qwen)
- [DeepSeek-V3 Technical Report](https://github.com/deepseek-ai/DeepSeek-V3)
- [Flux Model Repository](https://github.com/black-forest-labs/flux)

### Research Papers

- [Llama 3.1 Model Card](https://github.com/meta-llama/llama-models)
- DeepSeek-V3 Technical Report (check DeepSeek-AI repository for updates)
- Qwen Technical Reports (check QwenLM repository for updates)
- [Flow Matching for Generative Modeling](
  https://arxiv.org/abs/2210.02747)

### Model Weights and Deployment

- [Hugging Face - Meta Llama Models](https://huggingface.co/meta-llama)
- [Hugging Face - Qwen Models](https://huggingface.co/Qwen)
- [Hugging Face - DeepSeek Models](https://huggingface.co/deepseek-ai)
- [Hugging Face - Flux Models](https://huggingface.co/black-forest-labs)

### Inference Engines and Tools

- [vLLM - High-throughput LLM Serving](https://github.com/vllm-project/vllm)
- [SGLang - Efficient LLM Serving](https://github.com/sgl-project/sglang)
- [TensorRT-LLM - NVIDIA Inference](
  https://github.com/NVIDIA/TensorRT-LLM)
- [Diffusers - Flux Integration](
  https://github.com/huggingface/diffusers)

### Related Documentation

- [Large Scale Experts (MoE Models)](./large-scale-experts.md) - Deep dive
  into MoE architectures
- [Inference Engine Comparison](./README.md) - Overview of LLM serving
  platforms
- [Model Lifecycle Management](./model-lifecycle.md) - Cold-start, sleep
  mode, and offloading strategies

---

**Note**: This documentation covers current model architectures as of
October 2025. The field of LLM architectures is rapidly evolving. Always
refer to official model documentation for the most up-to-date specifications
and deployment guidance.
