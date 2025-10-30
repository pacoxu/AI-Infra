---
status: Active
maintainer: pacoxu
last_updated: 2025-10-30
tags: training, parallelism, distributed-training, pytorch, data-parallel,
  sharded-data-parallel, context-parallel
canonical_path: docs/training/parallelism.md
---

# Parallelism Strategies for Distributed Training

## Overview

Training large-scale AI models requires distributing computation across
multiple GPUs and nodes. Different parallelism strategies offer various
trade-offs between memory efficiency, computational overhead, and
implementation complexity. This guide covers three fundamental parallelism
techniques used in modern distributed training.

## Key Parallelism Strategies

### 1. Data Parallel (DP)

**Data Parallel** is the most straightforward parallelism strategy where the
model is replicated across all devices, and each device processes a different
subset of the training data.

#### How Data Parallel Works

- Each GPU maintains a full copy of the model
- Training data is split into batches and distributed across GPUs
- Forward and backward passes are computed independently on each GPU
- Gradients are synchronized (averaged) across all GPUs using AllReduce
- Model parameters are updated identically on all GPUs

#### Data Parallel Implementation in PyTorch

```python
import torch
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP

# Initialize distributed process group
torch.distributed.init_process_group(backend='nccl')

# Create model and move to GPU
model = MyModel().cuda()

# Wrap with DDP
model = DDP(model, device_ids=[local_rank])

# Training loop - DDP handles gradient synchronization
for data, target in dataloader:
    optimizer.zero_grad()
    output = model(data)
    loss = criterion(output, target)
    loss.backward()  # Gradients are automatically synchronized
    optimizer.step()
```

#### Data Parallel Characteristics

- **Memory:** Each GPU stores full model + optimizer states + gradients
- **Communication:** All-reduce operations for gradient synchronization
- **Scalability:** Limited by model size fitting in single GPU memory
- **Efficiency:** High throughput with minimal communication overhead

#### Best Use Cases for Data Parallel

- Models that fit in a single GPU's memory
- High throughput training with large batch sizes
- Simple distributed training setups

### 2. Sharded Data Parallel (SDP) / Fully Sharded Data Parallel (FSDP)

**Sharded Data Parallel** (also known as **Fully Sharded Data Parallel** or
**FSDP**) extends data parallelism by sharding model parameters, gradients,
and optimizer states across GPUs, significantly reducing memory usage per GPU.

#### How Sharded Data Parallel Works

- Model parameters are sharded (partitioned) across all GPUs
- During forward pass:
  - Each GPU gathers parameters it needs via all-gather
  - Computes forward pass
  - Discards parameters after use
- During backward pass:
  - Each GPU gathers parameters again for gradient computation
  - Computes gradients and reduces them across GPUs
  - Each GPU keeps only its shard of gradients
- Optimizer states are also sharded, reducing memory further

#### FSDP Implementation in PyTorch

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp import ShardingStrategy
from torch.distributed.fsdp.wrap import size_based_auto_wrap_policy

# Initialize distributed process group
torch.distributed.init_process_group(backend='nccl')

# Wrap policy for automatic layer-wise sharding
auto_wrap_policy = functools.partial(
    size_based_auto_wrap_policy,
    min_num_params=1e8  # Wrap layers with >100M parameters
)

# Create model with FSDP
model = FSDP(
    MyModel(),
    sharding_strategy=ShardingStrategy.FULL_SHARD,
    auto_wrap_policy=auto_wrap_policy,
    device_id=torch.cuda.current_device(),
)

# Training loop - FSDP handles all-gather and reduce-scatter
for data, target in dataloader:
    optimizer.zero_grad()
    output = model(data)
    loss = criterion(output, target)
    loss.backward()
    optimizer.step()
```

#### Sharding Strategies

- **FULL_SHARD:** Parameters, gradients, and optimizer states are sharded
  (maximum memory savings)
- **SHARD_GRAD_OP:** Only gradients and optimizer states are sharded
- **NO_SHARD:** Equivalent to standard DDP (no sharding)
- **HYBRID_SHARD:** Sharding within nodes, replication across nodes

#### Sharded Data Parallel Characteristics

- **Memory:** Significantly reduced - each GPU stores 1/N of parameters
  (N = number of GPUs)
- **Communication:** More frequent all-gather and reduce-scatter operations
- **Scalability:** Can train models much larger than single GPU memory
- **Efficiency:** Slightly higher communication overhead than DDP

#### Best Use Cases for Sharded Data Parallel

- Very large models that don't fit in single GPU memory
- Training with limited GPU memory per device
- Multi-node training scenarios

### 3. Context Parallel (CP)

**Context Parallel** is a parallelism strategy specifically designed for
transformer models with long sequence lengths. It partitions the sequence
dimension across GPUs, enabling training with context lengths that exceed
single GPU memory capacity.

#### How Context Parallel Works

- Input sequences are split along the sequence dimension across GPUs
- Attention mechanism is modified to handle cross-GPU communication
- For self-attention, each GPU:
  - Computes attention for its sequence partition
  - Communicates with other GPUs to exchange keys/values for full
    attention computation
- Layer outputs are gathered or kept sharded depending on next layer's needs

#### Key Concepts

**Sequence Parallelism for Transformers:**

```text
Sequence length: 32K tokens
4 GPUs with Context Parallel

GPU 0: Tokens [0:8K]
GPU 1: Tokens [8K:16K]
GPU 2: Tokens [16K:24K]
GPU 3: Tokens [24K:32K]

Each GPU computes attention over its partition while exchanging
key-value information with other GPUs for complete attention scores.
```

#### Context Parallel Implementation in PyTorch (Simplified)

```python
import torch
import torch.distributed as dist

def context_parallel_attention(
    query, key, value, cp_group, cp_rank, cp_world_size
):
    """
    Context parallel self-attention.
    
    Args:
        query, key, value: [batch, seq_len_local, hidden_dim]
        cp_group: Context parallel process group
        cp_rank: Rank within context parallel group
        cp_world_size: Size of context parallel group
    """
    batch_size, seq_len_local, hidden_dim = query.shape
    
    # All-gather keys and values from all GPUs
    key_all = [torch.empty_like(key) for _ in range(cp_world_size)]
    value_all = [torch.empty_like(value) for _ in range(cp_world_size)]
    
    dist.all_gather(key_all, key, group=cp_group)
    dist.all_gather(value_all, value, group=cp_group)
    
    # Concatenate to get full sequence
    key_full = torch.cat(key_all, dim=1)  # [batch, seq_len, hidden_dim]
    value_full = torch.cat(value_all, dim=1)
    
    # Compute attention over full sequence for local queries
    attention_output = compute_attention(query, key_full, value_full)
    
    return attention_output
```

#### Context Parallel Characteristics

- **Memory:** Reduces activation memory proportional to sequence partitioning
- **Communication:** All-gather for keys/values in attention layers
- **Scalability:** Enables training with very long context lengths
- **Efficiency:** Communication overhead increases with sequence length

#### Best Use Cases for Context Parallel

- Training transformers with very long context lengths (>8K tokens)
- Models where sequence length is the memory bottleneck
- Long-context LLMs (32K, 64K, 128K+ tokens)

## Combining Multiple Parallelism Strategies

Modern large-scale training often combines multiple parallelism strategies to
maximize efficiency and scale. Common combinations include:

### 3D Parallelism (DP + TP + PP)

```text
Data Parallel (DP): Replicate across data
Tensor Parallel (TP): Shard model layers
Pipeline Parallel (PP): Split model across pipeline stages
```

### 4D Parallelism (DP + TP + PP + CP)

```text
Add Context Parallel to 3D parallelism for long-context models:
- DP: 4-way (4 data replicas)
- TP: 8-way (model sharded across 8 GPUs)
- PP: 4-way (model split into 4 pipeline stages)
- CP: 2-way (sequence split across 2 GPUs)
Total: 256 GPUs (4 × 8 × 4 × 2)
```

### Example: PyTorch TorchTitan Configuration

```python
# Example configuration from torchtitan for LLaMA 3 training
parallelism_config = {
    "data_parallel": 4,           # 4-way data parallelism
    "tensor_parallel": 8,          # 8-way tensor parallelism
    "pipeline_parallel": 4,        # 4-way pipeline parallelism
    "context_parallel": 2,         # 2-way context parallelism
    "enable_fsdp": True,           # Use FSDP for data parallel
    "fsdp_sharding_strategy": "FULL_SHARD",
}
```

## Performance Considerations

### Memory Efficiency Comparison

For a model with M parameters trained on N GPUs:

| Strategy | Memory per GPU | Communication Volume |
|----------|----------------|---------------------|
| DP | M + Optimizer + Gradients | Gradients only |
| FSDP | M/N + Optimizer/N + Gradients/N | Parameters + Gradients |
| CP | Reduced by sequence sharding | K-V in attention |

### Communication Patterns

- **DP:** All-reduce (ring or tree topology) during backward pass
- **FSDP:** All-gather (forward) + reduce-scatter (backward)
- **CP:** All-gather in attention layers, reduce-scatter in outputs

### When to Use Each Strategy

| Use Case | Recommended Strategy |
|----------|---------------------|
| Model fits in single GPU | DP (DDP) |
| Model too large for single GPU | FSDP or Model Parallel |
| Long context lengths (>8K) | CP + FSDP |
| Multi-billion parameter models | FSDP + TP + PP |
| Maximum throughput | DP with large batch sizes |

## Tools and Frameworks

### PyTorch Native

- [`torch.nn.parallel.DistributedDataParallel`](https://pytorch.org/docs/stable/generated/torch.nn.parallel.DistributedDataParallel.html):
  Standard DDP implementation
- [`torch.distributed.fsdp`](https://pytorch.org/docs/stable/fsdp.html):
  Fully Sharded Data Parallel (FSDP)
- [`torch.distributed.tensor.parallel`](https://pytorch.org/docs/stable/distributed.tensor.parallel.html):
  Tensor Parallel APIs

### Reference Implementations

- [`PyTorch TorchTitan`](https://github.com/pytorch/torchtitan):
  PyTorch's reference implementation for training large models with all
  parallelism strategies. Provides production-ready examples of DP, FSDP,
  TP, PP, and CP.
- [`Megatron-LM`](https://github.com/NVIDIA/Megatron-LM):
  NVIDIA's framework with advanced parallelism techniques
- [`DeepSpeed`](https://github.com/microsoft/DeepSpeed):
  Microsoft's optimization library with ZeRO (similar to FSDP)

### Training Operators

- [`Kubeflow Training Operator`](https://github.com/kubeflow/training-operator):
  Kubernetes-native operator supporting distributed PyTorch training
- [`Volcano`](https://github.com/volcano-sh/volcano):
  Batch scheduling with gang scheduling for multi-GPU jobs

## Learning Resources

### Official Documentation

- [PyTorch Distributed Overview](https://pytorch.org/tutorials/beginner/dist_overview.html)
- [FSDP Tutorial](https://pytorch.org/tutorials/intermediate/FSDP_tutorial.html)
- [Distributed Training with PyTorch](https://pytorch.org/tutorials/beginner/ddp_series_intro.html)

### Research Papers

- **FSDP/ZeRO:**
  ["ZeRO: Memory Optimizations Toward Training Trillion Parameter
  Models"](https://arxiv.org/abs/1910.02054) (arXiv:1910.02054)
- **Megatron-LM:**
  ["Megatron-LM: Training Multi-Billion Parameter Language Models Using Model
  Parallelism"](https://arxiv.org/abs/1909.08053) (arXiv:1909.08053)
- **Sequence Parallelism:**
  ["Reducing Activation Recomputation in Large Transformer
  Models"](https://arxiv.org/abs/2205.05198) (arXiv:2205.05198)

### Example Projects

- [PyTorch TorchTitan Examples](https://github.com/pytorch/torchtitan/tree/main/docs):
  Production-ready examples with all parallelism strategies
- [PyTorch FSDP Examples](https://github.com/pytorch/examples/tree/main/distributed/FSDP):
  Simple FSDP usage examples
- [Megatron-LM Training Scripts](https://github.com/NVIDIA/Megatron-LM/tree/main/examples):
  Advanced parallelism configurations

## Best Practices

### Choosing Parallelism Configuration

1. **Start with Data Parallel (DDP):** If model fits in GPU memory
2. **Add FSDP:** When model memory exceeds single GPU capacity
3. **Consider Context Parallel:** For sequence lengths >8K tokens
4. **Use Tensor/Pipeline Parallel:** For very large models (>100B parameters)

### Optimization Tips

- **Gradient Accumulation:** Increase effective batch size without more memory
- **Mixed Precision (FP16/BF16):** Reduce memory and increase throughput
- **Activation Checkpointing:** Trade computation for memory savings
- **Communication Overlap:** Overlap communication with computation where
  possible

### Debugging Distributed Training

- Test with single GPU first, then scale to multi-GPU
- Use smaller model variants for faster iteration
- Monitor GPU memory usage and communication time
- Verify gradient synchronization correctness
- Check for hanging processes with NCCL_DEBUG=INFO

## Roadmap

### Upcoming Features

- **Automatic Parallelism Selection:** Framework-level optimization of
  parallelism strategy selection
- **Heterogeneous Training:** Mixed GPU types and memory configurations
- **Dynamic Parallelism:** Adaptive parallelism based on workload
  characteristics

### Community Contributions

Contributions to parallelism strategy documentation and examples are welcome!
Please share your experiences, benchmarks, and best practices by opening
issues or pull requests.

---

**Note:** This documentation is based on PyTorch 2.x and references the
[PyTorch TorchTitan](https://github.com/pytorch/torchtitan) project.
Some content describes advanced techniques that require careful tuning for
production use. Always validate configurations with your specific workload
and hardware.
