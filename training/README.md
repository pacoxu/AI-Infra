# Training on Kubernetes

## Overview

Training large-scale AI models on Kubernetes introduces unique challenges,
particularly around fault tolerance, diagnostics, and maintaining high
effective training time ratios (ETTR). As training clusters scale up, the
frequency and impact of failures increase significantly, making robust
fault handling mechanisms essential.

### Key Challenges at Scale

The expansion of resource scale brings widespread failures that pose
significant challenges to training stability:

- **Fault Types:**
  - CUDA errors (GPU hardware/driver failures)
  - NaN values (numerical instability)
  - Task hangs (communication timeouts, deadlocks)
  - Node failures (hardware issues)

- **Failure Characteristics:**
  - **Fail-stop nature:** Traditional approaches stop training immediately
    when failures occur
  - **High diagnostic overhead:** Identifying root causes requires significant
    time and expertise
  - **Frequency scales with cluster size:** Larger clusters experience more
    frequent failures

### Key Metrics

- **ETTR (Effective Training Time Ratio):**
  The ratio of effective training time to total job runtime. This metric
  captures both fault frequency and recovery efficiency.
  - Formula: `ETTR = Effective Training Time / Total Runtime`
  - Higher ETTR indicates better training efficiency

- **MFU (Model FLOPs Utilization):**
  Measures how efficiently the model utilizes available compute resources
  compared to theoretical peak performance.
  - Reflects both hardware utilization and software optimization

## Industry Best Practices

### ByteDance Training Optimization Framework

ByteDance has developed a comprehensive approach to training stability at
scale, documented in their technical article:
[ByteDance Training Optimization](https://mp.weixin.qq.com/s/-KDhk_R4nj3C-uPG11VoYQ)

Key components of their framework:

#### 1. Lightweight Real-time Monitoring

- Continuous health checks for GPUs, network, and training metrics
- Early detection of anomalies before they cause failures
- Low-overhead monitoring to minimize impact on training performance

#### 2. Stop-Diagnose Pattern

- Separate failure detection from diagnosis
- Preserve system state for post-mortem analysis
- Automated diagnostic tools to identify root causes

#### 3. Replay Capability

- Record training state and configurations
- Enable reproduction of failures for debugging
- Support for rolling back to stable checkpoints

#### 4. In-place Hot Updates

- Update training code without destroying the runtime environment
- Preserve GPU memory and loaded data
- Minimize recovery time for software fixes

#### 5. Fast Recovery with Warm Standby

- Maintain standby resources for quick failover
- Pre-warmed environments reduce cold-start overhead
- Strategic resource allocation balances cost and availability

#### 6. Reduced Remote Filesystem Dependencies

- Local caching of checkpoints and data
- Minimize network I/O during recovery
- Enable fast restarts without waiting for remote data loads

#### 7. MFU Optimization

- Continuous profiling and optimization
- Kernel fusion and memory optimization
- Pipeline parallelism tuning

## Projects and Tools

### Training Operators

- <a href="https://github.com/kubeflow/training-operator">
  `Training Operator`</a>: Kubernetes-native operators for distributed
  training (PyTorch, TensorFlow, XGBoost, etc.). Part of Kubeflow project.
- <a href="https://github.com/volcano-sh/volcano">`Volcano`</a>:
  CNCF Incubating project with gang scheduling and queue management for
  batch workloads.
- <a href="https://github.com/kubernetes-sigs/kueue">`Kueue`</a>:
  Kubernetes SIG project for job queueing and resource quotas.

### Fault Tolerance and Checkpointing

- <a href="https://github.com/pytorch/pytorch/blob/main/torch/distributed/checkpoint/README.md">
  `PyTorch Distributed Checkpoint`</a>: Native checkpointing in PyTorch
  for fault tolerance.
- <a href="https://github.com/NVIDIA/Megatron-LM">`Megatron-LM`</a>:
  NVIDIA's framework for training large language models with built-in
  fault tolerance.
- <a href="https://github.com/microsoft/DeepSpeed">`DeepSpeed`</a>:
  Microsoft's deep learning optimization library with checkpointing and
  fault tolerance features.

### Monitoring and Observability

- <a href="https://github.com/NVIDIA/dcgm-exporter">`DCGM Exporter`</a>:
  NVIDIA Data Center GPU Manager exporter for Prometheus.
- <a href="https://github.com/pytorch/kineto">`Kineto`</a>:
  PyTorch profiling library for GPU utilization analysis.
- <a href="https://github.com/kubernetes-sigs/metrics-server">
  `Metrics Server`</a>: Kubernetes SIG project for resource metrics.

### Storage and Caching

- <a href="https://github.com/fluid-cloudnative/fluid">`Fluid`</a>:
  CNCF project for dataset orchestration and caching in Kubernetes.
- <a href="https://github.com/ceph/ceph-csi">`Ceph CSI`</a>:
  Container Storage Interface driver for Ceph.
- <a href="https://github.com/juicedata/juicefs-csi-driver">
  `JuiceFS CSI`</a>: High-performance distributed file system for
  checkpoint storage.

## Learning Topics

### Foundation

- **Distributed Training Fundamentals:**
  - Data parallelism vs model parallelism
  - Pipeline parallelism and tensor parallelism
  - Gradient synchronization strategies (AllReduce, Ring-AllReduce)
  - Communication libraries: NCCL, Gloo, MPI

- **PyTorch Distributed:**
  - <a href="https://pytorch.org/tutorials/beginner/dist_overview.html">
    DistributedDataParallel (DDP)</a>
  - <a href="https://pytorch.org/docs/stable/fsdp.html">
    Fully Sharded Data Parallel (FSDP)</a>
  - <a href="https://pytorch.org/docs/stable/rpc.html">
    RPC framework</a>

### Kubernetes Integration

- **Gang Scheduling:**
  - All-or-nothing scheduling for distributed jobs
  - PodGroup and scheduling plugins
  - Integration with training operators

- **Resource Management:**
  - GPU sharing and time-slicing
  - RDMA network configuration
  - Dynamic Resource Allocation (DRA)

- **Storage:**
  - Persistent volumes for checkpoints
  - CSI drivers and volume snapshots
  - Data locality optimization

### Fault Tolerance

- **Checkpointing Strategies:**
  - Full vs incremental checkpoints
  - Checkpoint frequency optimization
  - Distributed checkpoint storage

- **Failure Detection:**
  - Health checks and liveness probes
  - Deadlock detection
  - GPU error monitoring

- **Recovery Mechanisms:**
  - Automatic restart policies
  - Checkpoint-based recovery
  - Elastic training (dynamic scaling)

### Performance Optimization

- **Profiling:**
  - PyTorch Profiler
  - NVIDIA Nsight Systems
  - Communication bottleneck analysis

- **Memory Optimization:**
  - Gradient checkpointing
  - Mixed precision training (FP16, BF16)
  - Activation recomputation

- **Communication Optimization:**
  - Gradient compression
  - Overlap computation and communication
  - Network topology awareness

## Case Studies and Research

### Academic Papers

- **Fault Tolerance:**
  - <a href="https://arxiv.org/abs/2509.16293">
    "Training Large-Scale AI Models with Fault Tolerance"</a>
    (arXiv:2509.16293v4)

- **Distributed Training:**
  - <a href="https://arxiv.org/abs/1910.02054">
    "PyTorch Distributed: Experiences on Accelerating Data Parallel
    Training"</a>

### Industry Blog Posts

- **ByteDance:**
  - <a href="https://mp.weixin.qq.com/s/-KDhk_R4nj3C-uPG11VoYQ">
    Large-Scale Training Optimization Practices</a> (Chinese)

- **Meta:**
  - <a href="https://engineering.fb.com/2021/09/13/ml-applications/llama/">
    Training Large Language Models at Scale</a>

- **Microsoft:**
  - <a href="https://www.microsoft.com/en-us/research/blog/deepspeed-extreme-scale-model-training-for-everyone/">
    DeepSpeed: Extreme-scale model training for everyone</a>

## RoadMap (Ongoing Proposals)

### Kubernetes Enhancements

- **Elastic Training KEP:**
  Dynamic scaling of training jobs based on resource availability
- **Checkpoint Optimization:**
  Native Kubernetes support for distributed checkpointing
- **GPU Health Monitoring:**
  Built-in GPU error detection and node quarantine

### Training Operator Enhancements

- <a href="https://github.com/kubeflow/training-operator/issues">
  Training Operator Issues</a>: Feature requests and enhancements
- **Automatic Failure Recovery:**
  Self-healing training jobs with intelligent retry logic
- **Cross-cluster Training:**
  Federated training across multiple Kubernetes clusters

## Getting Started

### Prerequisites

- Kubernetes cluster with GPU nodes
- Training operator installed
- Persistent storage configured (for checkpoints)
- Monitoring stack (Prometheus + Grafana)

### Quick Start Example

```yaml
# PyTorch distributed training job
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: pytorch-distributed-training
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:latest
            resources:
              limits:
                nvidia.com/gpu: 1
    Worker:
      replicas: 3
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:latest
            resources:
              limits:
                nvidia.com/gpu: 1
```

## Best Practices

### Checkpoint Management

- Save checkpoints frequently (e.g., every N steps or every M minutes)
- Store checkpoints on reliable persistent storage
- Use asynchronous checkpointing to minimize training interruption
- Implement checkpoint versioning and cleanup policies

### Monitoring and Alerting

- Monitor GPU utilization, temperature, and errors
- Track training metrics (loss, throughput, MFU)
- Set up alerts for anomalies and failures
- Maintain training logs for post-mortem analysis

### Resource Planning

- Provision 10-20% extra capacity for fault tolerance
- Consider spot/preemptible instances with appropriate checkpointing
- Plan for peak resource usage during checkpoint writing
- Use resource quotas to prevent resource exhaustion

### Testing

- Test failure scenarios in staging environments
- Validate checkpoint/restore procedures regularly
- Benchmark recovery time objectives (RTO)
- Verify training correctness after recovery

## Contributing

Contributions to training-related documentation and best practices are welcome!
Please share your experiences, tools, and optimization techniques by opening
issues or pull requests.

---

**Note:** Some content may be generated or summarized from referenced sources.
Please verify technical details with official documentation before using in
production environments.
