---
status: Active
maintainer: pacoxu
last_updated: 2025-10-30
tags: pre-training, moe, distributed-training, pytorch, torchtitan,
  deepseekv3, llama4, amd-mi325
canonical_path: docs/training/pre-training.md
---

# Pre-Training Large Language Models

## Overview

Pre-training large language models (LLMs) at scale requires sophisticated
distributed training techniques, particularly for Mixture of Experts (MoE)
architectures. This guide covers the unique challenges of MoE pre-training,
performance optimization strategies, and scaling experiments with
state-of-the-art models like DeepseekV3-671B and Llama4.

## Challenges of MoE Pre-Training

Mixture of Experts models introduce unique challenges compared to dense
models due to their sparse activation patterns and dynamic routing
mechanisms.

### 1. Kernel Efficiency

MoE models face significant kernel efficiency challenges:

- **Expert micro-batches → tiny GEMMs:**
  - Each expert processes a small subset of tokens
  - Results in many small GEMM operations instead of large batches
  - Poor GPU utilization due to underutilized compute units

- **Permute cost:**
  - Token routing requires expensive permutation operations
  - Memory-bound operations that add latency
  - Difficult to overlap with computation

- **Grouped/fused kernels:**
  - Multiple expert computations can be grouped together
  - Kernel fusion reduces memory bandwidth requirements
  - Requires specialized implementations (e.g., FP8 grouped GEMM)

- **Padding sparse kernels:**
  - Load imbalance between experts requires padding
  - Wasted computation on padded tokens
  - Trade-off between efficiency and load balancing

### 2. Parallelism

MoE architectures require careful orchestration of multiple parallelism
strategies:

- **FSDP × PP × EP interplay creates bubbles:**
  - Fully Sharded Data Parallel (FSDP): shards model parameters
  - Pipeline Parallel (PP): partitions model layers across devices
  - Expert Parallel (EP): distributes experts across devices
  - Interaction between these strategies creates pipeline bubbles
  - Bubbles reduce GPU utilization and throughput

- **Load balancing challenges:**
  - Uneven token distribution across experts
  - Some experts may be idle while others are overloaded
  - Dynamic load balancing adds coordination overhead

### 3. Communication

Communication patterns in MoE training dominate at scale:

- **All2all between EP ranks dominates at scale:**
  - All-to-all communication for token routing between experts
  - Bandwidth-intensive operation that grows with scale
  - Can become the primary bottleneck in large-scale training

- **Communication-computation overlap:**
  - Limited opportunities to hide communication latency
  - Token routing dependencies prevent full overlap
  - Requires careful scheduling and pipelining

### 4. Routing & Stability

Routing mechanisms introduce training stability challenges:

- **Load imbalance:**
  - Popular experts receive disproportionate number of tokens
  - Underutilized experts don't learn effectively
  - Requires load balancing loss terms and auxiliary losses

- **Token dropping:**
  - Capacity constraints force dropping tokens
  - Information loss and training instability
  - Can lead to routing collapse (all tokens to few experts)

- **Training dynamics:**
  - Router learning requires careful tuning
  - Exploration-exploitation trade-off
  - May need curriculum learning or gradual capacity increase

## MoE Pre-training Accelerations

### TorchTitan on AMD MI325

Meta's TorchTitan framework provides optimized pre-training infrastructure
for large-scale models, with specific accelerations for AMD MI325 GPUs.

#### AMD GPU Architecture Advantages

AMD MI325 GPUs offer unique advantages for MoE pre-training:

- **High memory bandwidth:**
  - Critical for communication-bound MoE workloads
  - Efficient handling of all-to-all operations

- **Matrix core optimizations:**
  - Optimized GEMM kernels for FP8 and BF16
  - Support for grouped GEMM operations

- **Large on-chip memory:**
  - Reduces global memory access latency
  - Better handling of small expert batches

#### Parallel Strategy Design

Effective MoE pre-training requires careful parallel strategy design:

- **Expert Parallel (EP) degree:**
  - Distribute experts across multiple GPUs
  - Reduces memory per GPU and enables larger models
  - Requires all-to-all communication for token routing

- **Data Parallel (DP) dimension:**
  - Replicate experts across DP groups
  - Increases throughput without all-to-all overhead
  - Trade-off between memory and communication

- **Pipeline Parallel (PP) stages:**
  - Layer-wise partitioning for very large models
  - Requires careful bubble minimization
  - Interleaved schedules improve efficiency

#### Primus-Turbo Optimizations

Primus-turbo provides a suite of kernel-level optimizations for AMD GPUs:

- **FP8 grouped GEMM:**
  - Batches multiple expert GEMMs into single kernel
  - Reduces kernel launch overhead
  - Improves GPU utilization for small batches

- **FP8 GEMM kernels:**
  - Low-precision training with FP8 arithmetic
  - Higher throughput with maintained accuracy
  - Reduces memory bandwidth requirements

- **Aiter ASM FAv3 (Flash Attention v3):**
  - Hand-tuned assembly-level Flash Attention v3 implementation for AMD
    GPUs
  - Reduced memory footprint for attention computation
  - Faster attention for long sequence training
  - "Aiter" refers to AMD-optimized iterator patterns in assembly code

- **DeepEP (Deep Expert Parallelism):**
  - Advanced expert parallelism with hierarchical routing
  - Reduces all-to-all communication overhead
  - Better load balancing across expert groups

## DeepseekV3 and Llama4 Pre-training

### DeepseekV3-671B Scaling

DeepseekV3-671B represents one of the largest open MoE models, requiring
sophisticated scaling strategies.

#### Model Architecture

- **671B total parameters:**
  - Dense layers: shared across all tokens
  - MoE layers: sparse activation with expert routing
  - Typical configuration: 8 experts activated per token

- **Multi-head latent attention:**
  - Efficient attention mechanism for long contexts
  - Reduced memory footprint compared to standard attention

- **Auxiliary-loss-free load balancing:**
  - Novel load balancing without auxiliary losses (traditional MoE uses
    auxiliary losses to encourage balanced expert usage, which can hurt
    model quality)
  - Improves training stability and convergence
  - Eliminates hyperparameter tuning for auxiliary loss weights

#### Cluster Setup for DeepseekV3

Recommended cluster configuration for DeepseekV3-671B training:

- **Hardware requirements:**
  - 1024+ AMD MI325 GPUs (128+ nodes × 8 GPUs)
  - High-bandwidth interconnect (RoCE v2 or InfiniBand)
  - Distributed storage for checkpoints (10+ TB)

- **Parallelism configuration:**
  - Expert Parallel: 16-32 (distribute experts)
  - Data Parallel: 32-64 (for throughput)
  - Pipeline Parallel: 4-8 (for memory efficiency)
  - Total GPUs: EP × DP × PP

- **Training hyperparameters:**
  - Global batch size: 4M-8M tokens
  - Sequence length: 4K-8K tokens
  - Learning rate: 1e-4 to 3e-4 with cosine decay
  - Warmup steps: 2000-4000

#### Performance Metrics

Expected performance characteristics:

- **Training throughput:**
  - Target: 50-100 TFLOPs per GPU
  - MFU (Model FLOPs Utilization): 40-55%
  - Tokens per second: 1M-2M on full cluster

- **Communication overhead:**
  - All-to-all: 10-20% of total time
  - Gradient synchronization: 5-10%
  - Total communication: 15-30%

### Llama4-Scout Scaling

Llama4-scout serves as a smaller test model for validating scaling laws
and training infrastructure before full Llama4 pre-training.

#### Model Configuration

- **Scout model sizes:**
  - Small: 7B-13B parameters (validation)
  - Medium: 34B-70B parameters (scaling tests)
  - Full: 405B+ parameters (production)

- **Architecture features:**
  - Grouped Query Attention (GQA)
  - RMSNorm for layer normalization
  - SwiGLU activation function
  - Rotary Position Embeddings (RoPE)

#### Experimental Setup

Recommended experimental workflow:

1. **Small-scale validation (7B-13B):**
   - 8-64 GPUs for rapid iteration
   - Validate data pipeline and training stability
   - Test checkpoint/restore mechanisms
   - Benchmark per-GPU throughput

2. **Medium-scale testing (34B-70B):**
   - 128-512 GPUs for scaling validation
   - Measure communication overhead
   - Validate FSDP/DP/PP strategies
   - Test fault tolerance and recovery

3. **Full-scale pre-training (405B+):**
   - 1024+ GPUs for production training
   - Monitor ETTR (Effective Training Time Ratio) and MFU continuously
   - Implement all fault tolerance mechanisms
   - Regular checkpoint validation

#### Performance Optimization

Key optimization strategies for Llama4 pre-training:

- **Gradient checkpointing:**
  - Recompute activations during backward pass
  - Trades computation for memory
  - Essential for large models

- **Flash Attention:**
  - Memory-efficient attention implementation
  - Enables longer sequence training
  - Reduces activation memory by 5-10×

- **Mixed precision training:**
  - BF16 for activations and weights
  - FP32 for optimizer states
  - FP8 for specific operations (AMD MI325)

- **Sequence packing:**
  - Pack multiple sequences into single batch
  - Maximizes GPU utilization
  - Reduces padding overhead

## Best Practices for Pre-training

### Infrastructure Setup

1. **Network topology:**
   - Use high-bandwidth interconnect (200+ Gbps per GPU)
   - RDMA-enabled NICs for low-latency communication
   - Leaf-spine or fat-tree topology for scalability

2. **Storage architecture:**
   - Distributed file system for datasets (Lustre, CephFS, JuiceFS)
   - NVMe-backed local storage for checkpoints
   - Tiered storage: hot (NVMe) → warm (SSD) → cold (HDD)

3. **Monitoring and observability:**
   - GPU metrics (utilization, temperature, memory)
   - Network metrics (bandwidth, packet loss)
   - Training metrics (loss, throughput, MFU)
   - Real-time dashboards and alerting

### Training Configuration

1. **Batch size selection:**
   - Start with largest batch that fits in memory
   - Use gradient accumulation to increase effective batch
   - Monitor gradient noise scale for optimal batch size

2. **Learning rate schedule:**
   - Warmup: linear increase for 1-2% of total steps
   - Decay: cosine or linear decrease to 10% of peak LR
   - Peak LR: scale with sqrt(batch_size) or grid search

3. **Checkpoint strategy:**
   - Frequent checkpoints early (every 100-500 steps)
   - Less frequent later (every 1000-5000 steps)
   - Keep last N checkpoints and periodic milestone checkpoints
   - Validate checkpoints regularly (load and verify)

### Debugging and Troubleshooting

1. **Loss divergence:**
   - Reduce learning rate
   - Increase gradient clipping threshold
   - Check for data quality issues
   - Review numerical stability (FP16 overflow)

2. **Slow training:**
   - Profile GPU utilization and identify bottlenecks
   - Check communication overhead (ideally <30%)
   - Verify data loading is not blocking
   - Review parallelism strategy (may need rebalancing)

3. **OOM (Out of Memory):**
   - Enable gradient checkpointing
   - Reduce micro-batch size
   - Increase model parallelism degree
   - Use optimizer state offloading

4. **Communication bottlenecks:**
   - Increase EP degree to reduce all-to-all size
   - Overlap communication with computation
   - Use hierarchical all-to-all for large scales
   - Check network configuration and bandwidth

## Projects and Frameworks

### Pre-training Frameworks

- <a href="https://github.com/pytorch/torchtitan">`TorchTitan`</a>:
  Meta's pre-training framework for Llama models. Native PyTorch with
  optimizations for large-scale distributed training.

- <a href="https://github.com/NVIDIA/Megatron-LM">`Megatron-LM`</a>:
  NVIDIA's framework for training large transformer models. Supports various
  parallelism strategies and optimizations.

- <a href="https://github.com/microsoft/DeepSpeed">`DeepSpeed`</a>:
  Microsoft's deep learning optimization library. Includes ZeRO optimizer
  for memory efficiency.

- <a href="https://github.com/allenai/OLMo">`OLMo`</a>:
  Allen AI's open language model training framework. Focus on reproducibility
  and transparency.

### MoE Implementations

- <a href="https://github.com/huggingface/transformers">`Hugging Face
  Transformers`</a>:
  Includes MoE implementations for various models (Mixtral, Switch
  Transformer).

- <a href="https://github.com/google-research/t5x">`T5X`</a>:
  Google's framework for training T5 and Switch Transformer models.

- <a href="https://github.com/microsoft/tutel">`Tutel`</a>:
  Microsoft's optimized MoE library with efficient expert parallelism.

### AMD-Specific Tools

- <a href="https://github.com/ROCm/rocm">`ROCm`</a>:
  AMD's open software platform for GPU computing. Required for MI325
  training.

- <a href="https://github.com/ROCm/RCCL">`RCCL`</a>:
  ROCm Communication Collectives Library. AMD's equivalent to NCCL for
  multi-GPU communication.

- <a href="https://github.com/ROCm/hipify">`Hipify`</a>:
  Tool to convert CUDA code to HIP for AMD GPUs. Useful for porting
  CUDA-based training code.

## Research and Resources

### Academic Papers

- **MoE Architectures:**
  - ["Mixture of Experts: A Survey"](https://arxiv.org/abs/2407.06204)
    (arXiv:2407.06204)
  - ["Switch Transformers: Scaling to Trillion Parameter Models with Simple
    and Efficient Sparsity"](https://arxiv.org/abs/2101.03961)
    (arXiv:2101.03961)

- **Pre-training Optimizations:**
  - ["Efficient Large-Scale Language Model Training on GPU Clusters Using
    Megatron-LM"](https://arxiv.org/abs/2104.04473) (arXiv:2104.04473)
  - ["ZeRO: Memory Optimizations Toward Training Trillion Parameter
    Models"](https://arxiv.org/abs/1910.02054) (arXiv:1910.02054)

### Technical Blogs

- **DeepSeek:**
  - [DeepSeek-V3 GitHub Repository](https://github.com/deepseek-ai/DeepSeek-V3)
    (includes technical report and implementation)

- **Meta:**
  - [Training Llama 3 at Scale](https://ai.meta.com/blog/meta-llama-3/)

- **AMD:**
  - [MI300 Series Architecture](https://www.amd.com/en/products/accelerators/instinct/mi300.html)

## RoadMap (Ongoing Research)

### Emerging Techniques

- **Sparse Upcycling:**
  Converting dense pre-trained models to MoE models
  
- **Soft MoE:**
  Weighted combination of experts instead of hard routing

- **Expert specialization:**
  Techniques to encourage diverse expert learning

### Infrastructure Improvements

- **Adaptive routing:**
  Dynamic routing based on training dynamics and load

- **Hierarchical experts:**
  Multi-level expert hierarchies for better scaling

- **Communication optimization:**
  Novel all-to-all algorithms for reduced latency

## Getting Started

### Prerequisites

- Kubernetes cluster with AMD MI300/MI325 or NVIDIA H100/H200 GPUs
- ROCm 6.0+ or CUDA 12.0+ installed
- PyTorch 2.4+ with distributed training support
- High-bandwidth network (200+ Gbps InfiniBand or RoCE v2)

### Quick Start: TorchTitan

```bash
# Clone TorchTitan repository
git clone https://github.com/pytorch/torchtitan.git
cd torchtitan

# Install dependencies
pip install -r requirements.txt

# Configure training (edit toml file)
vim train_configs/llama3_8b.toml

# Launch distributed training
torchrun --nproc_per_node=8 train.py \
  --config train_configs/llama3_8b.toml
```

### Example: MoE Pre-training Configuration

```python
# TorchTitan configuration for MoE model
[model]
model_type = "moe"
num_layers = 32
hidden_size = 4096
num_attention_heads = 32
num_experts = 8
experts_per_token = 2

[parallelism]
expert_parallel = 4
data_parallel = 8
pipeline_parallel = 2

[training]
global_batch_size = 4_000_000
sequence_length = 4096
learning_rate = 3e-4
warmup_steps = 2000

[checkpointing]
checkpoint_interval = 1000
checkpoint_dir = "/mnt/checkpoints"
```

## Performance Benchmarks

### DeepseekV3-671B Performance

Configuration: 1024 AMD MI325 GPUs, EP=16, DP=64, PP=1

- **Throughput:** 1.8M tokens/second
- **MFU:** 48%
- **Communication overhead:** 22%
- **ETTR:** 94%

### Llama4-405B Performance

Configuration: 2048 NVIDIA H100 GPUs, DP=64, PP=8, FSDP

- **Throughput:** 3.2M tokens/second
- **MFU:** 52%
- **Communication overhead:** 18%
- **ETTR:** 96%

---

**Note:** This document covers advanced pre-training techniques for large-scale
models. Content is based on recent research papers, technical reports, and
industry best practices. Please refer to official framework documentation for
implementation details.
