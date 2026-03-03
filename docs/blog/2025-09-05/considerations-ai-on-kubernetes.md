---
status: Active
maintainer: pacoxu
date: 2025-09-05
tags: kubernetes, ai, gpu, scheduling, storage, networking, observability, multi-tenancy
canonical_path: docs/blog/2025-09-05/considerations-ai-on-kubernetes.md
---

# Considerations When Doing AI on Kubernetes

> **Source**: This post is based on the CNCF blog article
> [Considerations when doing AI on Kubernetes](https://www.cncf.io/blog/2025/09/05/considerations-when-doing-ai-on-kubernetes/)
> (September 5, 2025).

Running AI workloads on Kubernetes has become increasingly common, but it comes
with unique challenges that differ significantly from traditional web or
microservice workloads. This post summarizes the key considerations when
deploying AI workloads on Kubernetes.

## 1. GPU and Accelerator Management

AI workloads are compute-intensive and typically require GPUs or other
accelerators (TPUs, NPUs). Kubernetes provides several mechanisms for managing
these resources.

### Device Plugins vs. Dynamic Resource Allocation (DRA)

The traditional approach uses **Device Plugins** to expose GPU resources as
extended resources (e.g., `nvidia.com/gpu`). However, this model has
limitations:

- Coarse-grained allocation (whole GPU only)
- Limited topology awareness
- No support for sharing or partitioning

**Dynamic Resource Allocation (DRA)**, introduced in Kubernetes 1.26 and
reaching beta in 1.32, addresses these limitations:

- Fine-grained resource allocation (MIG partitions, vGPU shares)
- Topology-aware scheduling (NVLink, PCIe, NUMA alignment)
- Structured parameters for complex resource requirements
- Support for multi-device claims

```yaml
# Example DRA ResourceClaim for GPU
apiVersion: resource.k8s.io/v1beta1
kind: ResourceClaim
metadata:
  name: gpu-claim
spec:
  devices:
    requests:
    - name: gpu
      deviceClassName: gpu.nvidia.com
      count: 1
```

See the [DRA documentation](../../kubernetes/dra.md) for more details.

### NVIDIA GPU Operator

The
[NVIDIA GPU Operator](https://github.com/NVIDIA/gpu-operator)
automates the management of GPU-related software components:

- GPU drivers
- Container toolkit (nvidia-container-toolkit)
- Device plugin
- DCGM exporter for monitoring
- MIG manager for GPU partitioning
- GPU Feature Discovery (GFD) for node labeling

See the [NVIDIA GPU Operator guide](../../kubernetes/nvidia-gpu-operator.md).

## 2. High-Performance Networking

Distributed training and multi-node inference require high-bandwidth, low-latency
networking. Key technologies:

### RDMA and InfiniBand

**Remote Direct Memory Access (RDMA)** enables direct memory-to-memory transfers
between nodes without CPU involvement, dramatically reducing latency:

- **InfiniBand**: Up to 400 Gb/s bandwidth, sub-microsecond latency
- **RoCEv2 (RDMA over Converged Ethernet)**: RDMA over standard Ethernet
- **SR-IOV**: Hardware virtualization for network interfaces

Kubernetes networking for AI workloads requires specialized CNI plugins that
support RDMA:

- **NVIDIA Network Operator**: Manages RDMA devices, SR-IOV, and MACVLAN
- **Multus CNI**: Attach multiple network interfaces to pods
- **whereabouts**: IP address management for secondary interfaces

### NVLink and NVSwitch

Within a single node, NVIDIA's NVLink and NVSwitch provide high-bandwidth GPU
interconnects (up to 900 GB/s for NVLink 4.0). Topology-aware scheduling
ensures pods are placed on nodes where GPUs with NVLink connections are
co-located.

## 3. Storage for AI Workloads

AI workloads have unique storage requirements for model weights, training data,
and checkpoints.

### Model Distribution

Large language models (LLMs) can be hundreds of gigabytes. Efficient
distribution strategies include:

- **OCI Image Volumes**: Package models as OCI artifacts for efficient
  distribution and caching (Kubernetes 1.33+ Beta)
- **ReadOnlyMany PVCs**: Share model weights across multiple inference pods
- **Object Storage (S3/GCS/OSS)**: Store and stream model weights on demand

```yaml
# Example: OCI Volume for model distribution
spec:
  volumes:
  - name: model-weights
    image:
      reference: registry.example.com/models/llama3:70b
      pullPolicy: IfNotPresent
  containers:
  - name: inference
    volumeMounts:
    - name: model-weights
      mountPath: /models
```

### Checkpointing

Training workloads need reliable checkpointing for fault tolerance:

- **CSI drivers** with NFS/parallel file systems (Lustre, GPFS) for
  high-bandwidth checkpoint writes
- **ReadWriteMany** storage for distributed checkpoint coordination
- **GPU Checkpoint/Restore**: CRIU-based checkpointing for full GPU state
  (experimental with NVIDIA cuda-checkpoint)

## 4. Scheduling for AI Workloads

AI workloads have specialized scheduling requirements that vanilla Kubernetes
scheduler doesn't fully address.

### Gang Scheduling

Distributed training requires all pods to start simultaneously (or fail
together). Gang scheduling solutions:

- **[Kueue](https://github.com/kubernetes-sigs/kueue)**: Kubernetes-native
  job queueing with gang scheduling support (CNCF Incubating)
- **[Volcano](https://github.com/volcano-sh/volcano)**: Production-grade batch
  scheduling for AI/HPC workloads (CNCF Graduated)
- **[Koordinator](https://github.com/koordinator-sh/koordinator)**: QoS-aware
  scheduling for colocation

### Topology-Aware Scheduling

For optimal performance, pods should be placed considering hardware topology:

- GPU-to-GPU NVLink connectivity
- PCIe topology (GPU to NIC affinity)
- NUMA node alignment
- Rack/switch-level placement for RDMA performance

The combination of **DRA + NRI** enables fine-grained topology-aware resource
allocation. See
[Topology-Aware Scheduling](../2025-11-25/topology-aware-scheduling.md).

### Workload Queuing and Fair Sharing

- **ResourceQuotas**: Limit resource consumption per namespace/team
- **Kueue ClusterQueues**: Fair-share scheduling across teams
- **Priority and Preemption**: Interrupt lower-priority workloads for urgent jobs

```yaml
# Example Kueue ClusterQueue
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: team-a-queue
spec:
  namespaceSelector:
    matchLabels:
      team: a
  resourceGroups:
  - coveredResources: [cpu, memory, nvidia.com/gpu]
    flavors:
    - name: gpu-flavor
      resources:
      - name: nvidia.com/gpu
        nominalQuota: 8
```

## 5. Observability for AI Workloads

AI workloads require specialized observability beyond standard CPU/memory metrics.

### GPU Metrics

**[DCGM Exporter](https://github.com/NVIDIA/dcgm-exporter)** exposes GPU metrics
to Prometheus:

| Metric | Description |
| --- | --- |
| `DCGM_FI_DEV_GPU_UTIL` | GPU utilization (%) |
| `DCGM_FI_DEV_MEM_COPY_UTIL` | Memory bandwidth utilization |
| `DCGM_FI_DEV_FB_USED` | GPU memory used (MB) |
| `DCGM_FI_DEV_POWER_USAGE` | Power consumption (W) |
| `DCGM_FI_DEV_XID_ERRORS` | GPU XID error count |
| `DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL` | NVLink bandwidth |

### Inference Metrics

For LLM inference, key Service Level Indicators (SLIs):

- **TTFT (Time to First Token)**: Latency for first generated token
- **TPOT (Time Per Output Token)**: Per-token generation latency
- **ITL (Inter-Token Latency)**: Variance in token generation timing
- **Throughput**: Tokens per second, requests per second

Tools: [OpenLIT](https://github.com/openlit/openlit),
[OpenLLMetry](https://github.com/traceloop/openllmetry),
[Langfuse](https://github.com/langfuse/langfuse)

### GPU Fault Detection

See the dedicated
[GPU Fault Detection guide](../../kubernetes/gpu-fault-detection.md) for
handling XID errors, card dropout, and automated remediation.

## 6. Multi-Tenancy and Isolation

Running AI workloads for multiple teams or customers requires strong isolation.

### Isolation Levels

| Level | Mechanism | Overhead |
| --- | --- | --- |
| Namespace | RBAC + NetworkPolicy | Minimal |
| Node Pool | Node selectors/taints | Medium |
| Virtual Cluster | vCluster/Kamaji | Medium-High |
| Dedicated Cluster | Separate K8s cluster | High |

### Security Considerations

- **RBAC**: Fine-grained access control for model serving APIs
- **NetworkPolicies**: Restrict inter-pod communication
- **PodSecurityAdmission**: Enforce pod security standards
- **Seccomp/AppArmor**: Syscall filtering for container workloads
- **Confidential Containers**: Hardware-based trusted execution environments
  (Intel TDX, AMD SEV) for sensitive model inference

See the [Multi-Tenancy Isolation guide](../2025-12-15/multi-tenancy-isolation.md).

## 7. Autoscaling for Inference

LLM inference workloads have bursty traffic patterns requiring intelligent
autoscaling.

### HPA with Custom Metrics

Standard CPU/memory HPA is insufficient for LLM inference. Use custom metrics:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-inference
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: External
    external:
      metric:
        name: vllm:num_requests_waiting
      target:
        type: AverageValue
        averageValue: "5"
```

### KEDA for Event-Driven Scaling

**[KEDA (Kubernetes Event-Driven Autoscaling)](https://keda.sh)** enables
scaling based on external metrics (Prometheus, queue depth, etc.):

- Scale from zero for cost efficiency
- Queue-depth-based scaling for batch inference
- Prometheus metrics for TTFT-based scaling

### Scale-to-Zero Challenges

LLM inference cold-start is slow (model loading takes minutes). Solutions:

- **Pre-warming**: Keep a minimum number of replicas ready
- **Sandbox Warm Pool**: Pre-initialized containers awaiting activation
- **Model caching**: Cache model weights on node-local storage
- **OCI image pre-pulling**: DaemonSet-based image pre-pull

## 8. Training Workloads on Kubernetes

### Distributed Training Frameworks

- **[Kubeflow Training Operator](https://github.com/kubeflow/training-operator)**:
  Kubernetes-native operators for PyTorchJob, TFJob, XGBoostJob
- **[Volcano](https://github.com/volcano-sh/volcano)**: Gang scheduling for
  distributed training
- **[JobSet](https://github.com/kubernetes-sigs/jobset)**: Hierarchical job
  management for multi-role training jobs

### Fault Tolerance

Distributed training at scale requires robust fault handling:

- **Checkpointing**: Regular saves of model state to distributed storage
- **Elastic Training**: Add/remove workers without restarting from scratch
  (PyTorch Elastic, Horovod)
- **In-Place Restart**: Recover failed workers without reallocating all resources
  (KEP-5307: In-Place Container Restart)

See the [Training Guide](../../training/README.md).

## 9. Cost Optimization

AI workloads are expensive. Key cost optimization strategies:

### GPU Utilization

- **Time-slicing**: Share GPU across multiple pods (NVIDIA vGPU, MPS)
- **MIG (Multi-Instance GPU)**: Hardware-level GPU partitioning
- **Mixed workloads**: Collocate inference and batch workloads on the same node

### Spot/Preemptible Instances

Use spot instances for fault-tolerant training workloads with checkpointing.
Cloud providers offer significant discounts (60-80%) for interruptible compute.

### Rightsizing

Profile actual GPU utilization to identify over-provisioned workloads. Use
**Katalyst** (ByteDance) or **Vertical Pod Autoscaler** for recommendations.

## 10. Kubernetes Ecosystem Resources

### CNCF Working Groups

- **[WG Batch](https://github.com/kubernetes/community/blob/master/wg-batch/README.md)**:
  Batch workloads and gang scheduling
- **[WG Serving](https://github.com/kubernetes/community/blob/master/wg-serving/README.md)**:
  Model serving on Kubernetes
- **[WG Device Management](https://github.com/kubernetes/community/blob/master/wg-device-management/README.md)**:
  DRA and advanced device management
- **[WG AI Integration](https://github.com/kubernetes/community/blob/master/wg-ai-integration/charter.md)**:
  AI/ML workload integration

### Key Projects

| Category | Projects |
| --- | --- |
| Scheduling | Kueue, Volcano, Koordinator |
| GPU Management | NVIDIA GPU Operator, DRA drivers |
| Networking | NVIDIA Network Operator, Multus CNI |
| Model Serving | vLLM, KServe, Triton, TGI |
| Training | Kubeflow Training Operator, JobSet |
| Observability | DCGM Exporter, OpenLIT, Langfuse |
| Gateway | Gateway API Inference Extension, Envoy AI Gateway |

## Conclusion

Running AI workloads on Kubernetes requires careful consideration across
multiple dimensions: hardware resource management, high-performance networking,
storage, scheduling, observability, multi-tenancy, autoscaling, and cost
optimization.

The cloud-native ecosystem has evolved significantly to address these
challenges, with a rich set of tools and frameworks specifically designed for
AI/ML workloads. The key is to start with your specific requirements and
incrementally adopt the tools and patterns that solve your problems.

---

## References

- [CNCF Blog: Considerations when doing AI on Kubernetes](https://www.cncf.io/blog/2025/09/05/considerations-when-doing-ai-on-kubernetes/)
- [Kubernetes DRA Documentation](../../kubernetes/dra.md)
- [NVIDIA GPU Operator Guide](../../kubernetes/nvidia-gpu-operator.md)
- [Scheduling Optimization](../../kubernetes/scheduling-optimization.md)
- [Inference Overview](../../inference/README.md)
- [Training on Kubernetes](../../training/README.md)
- [Observability Guide](../../observability/README.md)
- [Multi-Tenancy Isolation](../2025-12-15/multi-tenancy-isolation.md)
- [GPU Fault Detection](../../kubernetes/gpu-fault-detection.md)

---

**Author**: AI Infrastructure Learning Path (based on CNCF Blog)
**Date**: September 5, 2025
**Tags**: #kubernetes #ai #gpu #scheduling #storage #networking #observability
