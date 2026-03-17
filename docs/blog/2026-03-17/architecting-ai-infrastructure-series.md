---
status: Active
maintainer: pacoxu
date: 2026-03-17
tags: gpu, placement, mig, topology, vgpu, consumption-models
canonical_path: docs/blog/2026-03-17/architecting-ai-infrastructure-series.md
source_urls:
  - https://frankdenneman.nl/posts/2026-02-09-why-gpu-placement-becomes-the-defining-problem/
  - https://frankdenneman.nl/posts/2026-02-11-gpu-consumption-models-as-the-first-architectural-choice-in-production-ai/
  - https://frankdenneman.nl/posts/2026-03-06-MIG-Mode/
  - https://frankdenneman.nl/posts/2026-03-16-why-multi-gpu-requires-topology-awareness/
---

# Architecting AI Infrastructure Series by Frank Denneman

Frank Denneman published a nine-part series on architecting AI infrastructure,
focusing on GPU placement, consumption models, partitioning strategies, and
multi-GPU topology. This post maps the series to existing content in this
repository and highlights the concepts most relevant to cloud-native and
Kubernetes-based AI infrastructure.

## Series Overview

| Part | Title | Scope |
| --- | --- | --- |
| 1 | [Why GPU Placement Becomes the Defining Problem][p1] | General |
| 2 | [GPU Consumption Models as the First Architectural Choice][p2] | General |
| 3 | [How vSphere DRS Makes GPU Placement Decisions][p3] | vSphere-specific |
| 4 | [How vSphere GPU Modes and Assignment Policies Determine Host Level Placement][p4] | vSphere-specific |
| 5 | [How Same-Size vGPU Mode and Right-Sizing Shape GPU Placement Efficiency][p5] | vSphere-specific |
| 6 | [Mixed Size vGPU Mode in Practice][p6] | vSphere-specific |
| 7 | [Same Size vs Mixed Size Placement at Cluster Scale][p7] | vSphere-specific |
| 8 | [MIG Partitioning, Placement Geometry, and Stranded Capacity][p8] | General |
| 9 | [Why Multi-GPU Requires Topology Awareness][p9] | General |

Parts 3–7 are specific to VMware vSphere infrastructure. Parts 1, 2, 8, and 9
address concepts that apply broadly to any production AI infrastructure,
including Kubernetes-based deployments.

[p1]: https://frankdenneman.nl/posts/2026-02-09-why-gpu-placement-becomes-the-defining-problem/
[p2]: https://frankdenneman.nl/posts/2026-02-11-gpu-consumption-models-as-the-first-architectural-choice-in-production-ai/
[p3]: https://frankdenneman.nl/posts/2026-02-13-how-vsphere-drs-makes-gpu-placement-decisions/
[p4]: https://frankdenneman.nl/posts/2026-02-17-how-vsphere-gpu-modes-and-assignment-policies-determine-host-level-placement/
[p5]: https://frankdenneman.nl/posts/2026-02-19-how-same-size-vgpu-mode-and-right-sizing-shape-gpu-placement-efficiency/
[p6]: https://frankdenneman.nl/posts/2026-02-24-mixed-size-vgpu-mode-in-practice/
[p7]: https://frankdenneman.nl/posts/2026-03-01-same-size-vs-mixed-size-placement/
[p8]: https://frankdenneman.nl/posts/2026-03-06-MIG-Mode/
[p9]: https://frankdenneman.nl/posts/2026-03-16-why-multi-gpu-requires-topology-awareness/

## Key Themes and Kubernetes Relevance

### Part 1 – GPU Placement as the Defining Problem

GPU placement is the central scheduling challenge in production AI
infrastructure. Unlike CPU workloads, GPU-accelerated jobs are sensitive to:

- **Topology distance**: GPUs separated by PCIe hops or multiple NUMA nodes
  communicate significantly slower than those connected via NVLink
- **Fragmentation**: Suboptimal placement leaves GPUs stranded (allocated but
  underutilised, or unallocatable due to topology constraints)
- **Co-location effects**: Shared GPUs must be placed without introducing noisy
  neighbour interference

In Kubernetes this maps directly to topology-aware scheduling via DRA or the
Device Plugin topology hint mechanism. See
[Topology-Aware Scheduling](../2025-11-25/topology-aware-scheduling.md) and
[Dynamic Resource Allocation (DRA)](../../kubernetes/dra.md).

### Part 2 – GPU Consumption Models

The series identifies three primary GPU consumption models used in production:

| Model | Mechanism | Isolation | Overhead | Best For |
| --- | --- | --- | --- | --- |
| **Dedicated / Passthrough** | Whole GPU assigned to one workload | Hard | None | Training, single-model inference |
| **Time-slicing** | GPU shared via software scheduler (CUDA MPS or driver time-sharing) | Soft | Low | Dev/test, bursty inference |
| **MIG (Multi-Instance GPU)** | Hardware partitioned into independent instances | Hard | None | Multi-tenant inference, predictable SLA |

In Kubernetes, these map to:

- **Dedicated**: Standard `nvidia.com/gpu: 1` device plugin request, or DRA
  `ResourceClaim` for a whole GPU
- **Time-slicing**: NVIDIA Device Plugin `timeSlicing.replicas` configuration
- **MIG**: NVIDIA Device Plugin MIG strategy (`single` or `mixed`) or DRA
  with MIG-aware resource classes

For details on configuring each model in Kubernetes, see
[NVIDIA GPU Operator](../../kubernetes/nvidia-gpu-operator.md) and
[GPU Partitioning Strategies](../../kubernetes/gpu-partitioning.md).

### Part 8 – MIG Partitioning, Placement Geometry, and Stranded Capacity

Multi-Instance GPU (MIG) partitions a physical GPU into isolated instances with
guaranteed compute, memory, and bandwidth. Key concepts covered in the series:

#### MIG Profile Types (NVIDIA H100 80 GB example)

| Profile | Compute Slices | Memory | Instances per GPU |
| --- | --- | --- | --- |
| `1g.10gb` | 1 | 10 GB | 7 |
| `2g.20gb` | 2 | 20 GB | 3 |
| `3g.40gb` | 3 | 40 GB | 2 |
| `4g.40gb` | 4 | 40 GB | 1 |
| `7g.80gb` | 7 | 80 GB | 1 (full GPU) |

#### Placement Geometry and Stranded Capacity

The H100 GPU is divided into 7 GPU instances (GI) and 8 compute instances (CI)
slots arranged in a fixed physical layout. Profiles must fit contiguous slices,
which means mixing profiles of different sizes can result in **stranded
capacity**: unallocatable slices that do not fit any remaining profile.

Example of stranded capacity:

```text
H100 (7 slices): [2g.20gb][2g.20gb][2g.20gb][ ? ]
```

After placing three `2g.20gb` instances (using 6 slices), the remaining 1
slice can only accommodate a `1g.10gb` profile. If no such workload exists,
the slice is stranded.

**Kubernetes implications:**

- The NVIDIA Device Plugin `mixed` MIG strategy allows different instance
  profiles on the same node but requires per-profile resource names
  (e.g. `nvidia.com/mig-2g.20gb`)
- The `single` strategy enforces uniform profiles across all GPUs on a node,
  avoiding stranded capacity at the cost of flexibility
- NVIDIA DRA driver provides topology-aware MIG allocation that considers
  placement geometry when binding `ResourceClaims`

See [NVIDIA GPU Operator – MIG Manager](../../kubernetes/nvidia-gpu-operator.md)
and [GPU Partitioning Strategies](../../kubernetes/gpu-partitioning.md) for
configuration examples.

### Part 9 – Why Multi-GPU Requires Topology Awareness

When a workload spans multiple GPUs, the communication bandwidth between them
determines training throughput. NVIDIA GPU interconnects form a hierarchy:

```text
NVLink (NVSwitch fabric)  >  PCIe within same socket  >  PCIe across sockets
      ~600 GB/s                    ~32–64 GB/s                ~16 GB/s
```

Placing a distributed training job across GPUs connected by fast NVLink/NVSwitch
versus slow PCIe can result in a **30–50% performance difference** for
all-reduce-heavy workloads.

In Kubernetes, topology awareness for multi-GPU workloads is achieved through:

- **NUMA topology manager** (`--topology-manager-policy=best-effort|restricted|single-numa-node`)
- **DRA topology constraints** in `ResourceClaim` with `allocationMode: ExactCount`
  and topology selector
- **NVIDIA DRA driver compute domains**: Groups of GPUs connected via NVSwitch
  that are scheduled as a unit (relevant for GB200 NVL systems)

For an in-depth treatment of Kubernetes topology scheduling, see
[Topology-Aware Scheduling](../2025-11-25/topology-aware-scheduling.md) and
[Dynamic Resource Allocation (DRA)](../../kubernetes/dra.md).

## Content Coverage Summary

The table below shows how topics from the series map to existing documentation
in this repository:

| Series Topic | Existing Coverage | Gap |
| --- | --- | --- |
| GPU placement as key challenge | [Scheduling Optimization][so], [Topology-Aware Scheduling][tas] | None |
| GPU consumption models | [NVIDIA GPU Operator][ngo] (brief) | [GPU Partitioning][gp] (new) |
| vSphere DRS placement | Out of scope (vSphere-specific) | — |
| vGPU same-size / mixed-size | Out of scope (vSphere-specific) | — |
| MIG profiles and geometry | [NVIDIA GPU Operator][ngo] (brief mention) | [GPU Partitioning][gp] (new) |
| Stranded capacity | Not previously covered | [GPU Partitioning][gp] (new) |
| Multi-GPU topology | [Topology-Aware Scheduling][tas], [DRA][dra] | None |
| NVLink / NVSwitch hierarchy | [DRA][dra], [NVIDIA GPU Operator][ngo] | None |

[so]: ../../kubernetes/scheduling-optimization.md
[tas]: ../2025-11-25/topology-aware-scheduling.md
[ngo]: ../../kubernetes/nvidia-gpu-operator.md
[dra]: ../../kubernetes/dra.md
[gp]: ../../kubernetes/gpu-partitioning.md
