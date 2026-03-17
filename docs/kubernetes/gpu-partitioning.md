---
status: Active
maintainer: pacoxu
last_updated: 2026-03-17
tags: kubernetes, gpu, mig, partitioning, time-slicing, vgpu, topology
canonical_path: docs/kubernetes/gpu-partitioning.md
---

# GPU Partitioning Strategies

Modern NVIDIA GPUs support three distinct consumption models for sharing GPU
resources across multiple workloads. Choosing the right model has significant
implications for isolation, performance, placement density, and operational
complexity.

## Why GPU Partitioning Matters

A single H100 80 GB GPU costs tens of thousands of dollars. Running one
workload at a time wastes significant capacity for:

- **Inference services**: Individual models often use only 20–40% of GPU
  compute and memory
- **Development workloads**: Interactive sessions, experiments, and CI jobs
  need much less than a full GPU
- **Multi-tenant platforms**: Different teams need predictable, isolated GPU
  slices with guaranteed SLAs

At the same time, partitioning the wrong way introduces stranded capacity,
noisy-neighbour effects, or topological performance penalties.

## Three GPU Consumption Models

### 1. Dedicated (Whole GPU)

A single workload receives exclusive access to one or more physical GPUs.

**Mechanism**: Standard Kubernetes device plugin assignment or DRA
`ResourceClaim` with a whole GPU.

**Characteristics:**

- **Isolation**: Hard — no sharing with other workloads
- **Performance**: Maximum — no overhead from sharing
- **Memory**: Full GPU VRAM available
- **Kubernetes resource name**: `nvidia.com/gpu: 1`

**Best for:**

- Distributed training (multi-GPU and multi-node)
- Large single-model inference (e.g. 70B+ parameter models)
- Workloads requiring maximum memory bandwidth

**Configuration:**

```yaml
resources:
  limits:
    nvidia.com/gpu: "1"
```

---

### 2. Time-Slicing (Logical Sharing)

Multiple workloads share a single GPU by taking turns via a software time
scheduler. NVIDIA supports two mechanisms:

- **CUDA Time-Slicing**: Kernel-level context switching between processes
- **CUDA MPS (Multi-Process Service)**: Concurrent execution via a shared CUDA
  context with partial isolation

**Mechanism**: NVIDIA Device Plugin `timeSlicing.replicas` configuration in
the GPU Operator ClusterPolicy.

**Characteristics:**

- **Isolation**: Soft — workloads share GPU memory and compute; no memory
  protection between processes
- **Performance**: Degrades with contention; GPC (GPU Processing Cluster)
  context switches add overhead
- **Memory**: VRAM is shared; no per-workload memory limit enforcement at
  hardware level
- **Kubernetes resource name**: `nvidia.com/gpu: 1` (oversubscribed)

**Best for:**

- Development and experimentation workloads
- Bursty, low-latency-tolerant inference
- Environments where cost matters more than strict isolation

**Configuration:**

```yaml
# GPU Operator ClusterPolicy snippet
devicePlugin:
  config:
    default: |
      version: v1
      sharing:
        timeSlicing:
          replicas: 4
```

After applying this configuration, Kubernetes will advertise 4 virtual GPU
resources per physical GPU.

**Caveats:**

- Memory errors in one process can affect co-tenants (no hardware protection)
- `nvidia-smi` reports full GPU memory, not per-workload allocation
- CUDA MPS provides better GPU utilisation but limited fault isolation

---

### 3. MIG (Multi-Instance GPU)

Multi-Instance GPU (MIG) partitions a physical GPU at the hardware level into
fully independent instances, each with its own compute engines, L2 cache,
memory slice, and memory bandwidth.

**Mechanism**: NVIDIA MIG hardware feature available on A100, A30, H100, and
H200 GPUs. Managed in Kubernetes via GPU Operator MIG Manager or NVIDIA DRA
driver.

**Characteristics:**

- **Isolation**: Hard — hardware-enforced separation; one instance cannot
  access another's memory or compute
- **Performance**: Predictable and consistent; no sharing overhead
- **Memory**: Fixed per instance based on profile; guaranteed bandwidth
- **Kubernetes resource names**: Profile-specific (e.g.
  `nvidia.com/mig-2g.20gb`)

**Best for:**

- Multi-tenant inference platforms with strict SLA requirements
- Serving multiple small models on a single GPU (e.g. 7B–13B parameter models)
- Environments requiring guaranteed performance and strong isolation

---

## MIG Profiles and Placement Geometry

### Available Profiles (NVIDIA H100 80 GB SXM)

The H100 GPU is divided into **7 GPU instances (GI)** and **8 compute
instances (CI)** arranged in a fixed physical layout with 7 compute slices and
80 GB of memory.

| Profile | Compute Slices | Memory | Max Instances |
| --- | --- | --- | --- |
| `1g.10gb` | 1 | 10 GB | 7 |
| `2g.20gb` | 2 | 20 GB | 3 |
| `3g.40gb` | 3 | 40 GB | 2 |
| `4g.40gb` | 4 | 40 GB | 1 |
| `7g.80gb` | 7 | 80 GB | 1 (full GPU equivalent) |

> **Note**: Profile names reflect compute slices and memory per instance.
> The A100 40 GB and 80 GB variants have different profile tables. Always
> check the
> [NVIDIA MIG User Guide](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/)
> for the specific GPU model.

### Stranded Capacity

MIG profiles must occupy **contiguous** slices on the GPU. Mixing profiles of
different sizes can leave slices in configurations where no valid profile fits
the remaining space — these become **stranded**.

**Example: stranded capacity with mixed profiles**

```text
H100 7 slices:  [ 3g.40gb ][ 3g.40gb ][ ? ]
                    slice 1    slice 4   slice 7 (stranded)
```

After placing two `3g.40gb` instances (using 6 of 7 slices), the remaining 1
slice can only fit a `1g.10gb`. If the workload mix requires only `3g.40gb`,
that slice cannot be used.

**Minimising stranded capacity:**

1. **Use uniform profiles** (`single` MIG strategy in device plugin): All GPUs
   on a node use the same profile, eliminating mixed-placement fragmentation
2. **Plan profiles for your workload mix**: If you need `2g.20gb` and `1g.10gb`
   together (2+2+2+1 = 7 slices), there is no stranded capacity
3. **Use DRA with topology awareness**: The NVIDIA DRA driver can select MIG
   instances that minimise fragmentation based on `ResourceClaim` requirements

### Kubernetes MIG Strategies

NVIDIA Device Plugin supports two MIG strategies:

| Strategy | Behaviour | Resource Names |
| --- | --- | --- |
| `single` | All GPUs on the node use the same MIG profile | Single name, e.g. `nvidia.com/gpu` mapped to one MIG profile |
| `mixed` | GPUs can have different profiles; each profile has its own resource name | `nvidia.com/mig-1g.10gb`, `nvidia.com/mig-2g.20gb`, etc. |

**`single` strategy** (recommended for homogeneous workloads):

```yaml
# Device plugin config
mig:
  strategy: single
```

Pods request the MIG profile by using the standard `nvidia.com/gpu` resource
name (which is remapped to the configured profile).

**`mixed` strategy** (for heterogeneous inference platforms):

```yaml
mig:
  strategy: mixed
```

Pods specify the exact profile needed:

```yaml
resources:
  limits:
    nvidia.com/mig-2g.20gb: "1"
```

---

## Choosing the Right Model

| Criteria | Dedicated | Time-Slicing | MIG |
| --- | --- | --- | --- |
| Workload type | Training, large inference | Dev/test, bursty inference | Multi-tenant inference |
| Isolation requirement | Highest | None | High (hardware) |
| Predictable performance | Yes | No | Yes |
| Memory protection | Yes | No | Yes |
| GPU utilisation | Low (for small models) | High (with contention risk) | Medium-high |
| Operational complexity | Low | Low | Medium |
| Supported GPUs | All | All | A100, A30, H100, H200 |

**Decision guide:**

1. **Training jobs** or **large inference models** (≥ 40 GB): Use
   **dedicated whole GPUs**
2. **Small inference models** (≤ 20 GB) in a multi-tenant platform with SLA
   requirements: Use **MIG** with `2g.20gb` or `3g.40gb` profiles
3. **Dev/test environments** or workloads that tolerate variability: Use
   **time-slicing** for maximum density
4. **Mixed workloads on same node**: Use **MIG mixed strategy** or separate
   node pools

---

## Topology Considerations for Multi-GPU Workloads

When a workload spans multiple GPUs (training or pipeline parallelism),
placement topology determines communication bandwidth. NVIDIA GPU interconnects
form a hierarchy:

```text
NVLink (NVSwitch fabric)  >>  PCIe same socket  >>  PCIe cross-socket
      ~600 GB/s                   ~32–64 GB/s            ~16 GB/s
```

Placing a distributed training job on GPUs connected by PCIe instead of
NVLink can reduce all-reduce throughput by **50–75%**, directly impacting
training time.

### Kubernetes Topology Controls

- **NUMA Topology Manager**: Set `--topology-manager-policy` to
  `best-effort`, `restricted`, or `single-numa-node` to align GPU and CPU
  allocations within NUMA domains
- **DRA topology constraints**: Use `ResourceClaim` with topology selectors to
  co-schedule GPUs that share NVLink connectivity
- **NVIDIA DRA driver compute domains**: GB200 NVL72 systems expose NVSwitch
  fabrics as compute domains; the DRA driver schedules workloads within a
  domain when requested

For a detailed treatment of topology-aware scheduling, see
[Topology-Aware Scheduling](../blog/2025-11-25/topology-aware-scheduling.md)
and [Dynamic Resource Allocation (DRA)](./dra.md).

---

## Kubernetes Implementation References

| Feature | Component | Reference |
| --- | --- | --- |
| Whole-GPU allocation | Device Plugin / DRA | [NVIDIA GPU Operator](./nvidia-gpu-operator.md) |
| Time-slicing | Device Plugin config | [NVIDIA GPU Operator](./nvidia-gpu-operator.md) |
| MIG Manager | GPU Operator | [NVIDIA GPU Operator](./nvidia-gpu-operator.md) |
| MIG with DRA | NVIDIA DRA driver | [DRA](./dra.md) |
| Topology-aware scheduling | DRA / Device Plugin topology hints | [Topology-Aware Scheduling][tas] |
| GPU fault detection | DCGM + Node Problem Detector | [GPU Fault Detection](./gpu-fault-detection.md) |

[tas]: ../blog/2025-11-25/topology-aware-scheduling.md

## RoadMap

- Dynamic MIG reconfiguration without node drain (in progress upstream)
- Fractional GPU support in DRA (sub-MIG granularity)
- Unified partitioning API across GPU vendors (AMD ROCm, Intel Gaudi)
- MIG-aware autoscaling in Kueue and Cluster Autoscaler

## Further Reading

- [Frank Denneman: Architecting AI Infrastructure Series](../blog/2026-03-17/architecting-ai-infrastructure-series.md)
- <a href="https://docs.nvidia.com/datacenter/tesla/mig-user-guide/">NVIDIA
  MIG User Guide</a>
- <a href="https://github.com/NVIDIA/gpu-operator">NVIDIA GPU Operator</a>
- <a href="https://github.com/NVIDIA/k8s-dra-driver-gpu">NVIDIA DRA Driver
  for GPUs</a>
- <a href="https://docs.nvidia.com/deploy/mig-user-guide/index.html#partitioning">
  MIG Partitioning Reference</a>
