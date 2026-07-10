---
status: Active
maintainer: pacoxu
last_updated: 2026-07-10
tags: kubernetes, gpu-sharing, hami, mig, mps, vgpu, dra, kubecon
canonical_path: docs/kubernetes/hami-gpu-sharing.md
source_urls: |-
  https://www.lfopensource.cn/kubecon-cloudnativecon-openinfra-summit-pytorch-conference-china/program/schedule/
  https://github.com/Project-HAMi/HAMi
  https://github.com/NVIDIA/k8s-device-plugin
  https://github.com/NVIDIA/k8s-dra-driver-gpu
  https://github.com/Project-HAMi/k8s-dra-driver
---

# HAMi / MIG / GPU Sharing: A Systematic Guide

KubeCon China 2026 signals — Dynamic MIG with HAMi, GPU virtualization,
fragmented GPU clusters, and dynamic GPU sharing — point to a maturing
platform concern: **GPU is no longer a binary on/off resource**. Platform teams
must decide how to partition, share, isolate, and schedule fractional GPU
capacity across training, inference, development, and multi-tenant Agent
workloads.

This guide maps five common mechanisms — **HAMi**, **MIG**, **CUDA MPS**,
**vGPU**, and **DRA** — onto four isolation dimensions, then provides
selection matrices and integration boundaries with queues, quotas, and
observability.

**Related docs:**

- [Dynamic Resource Allocation (DRA)](./dra.md) — Kubernetes-native device
  allocation and partitionable devices
- [NVIDIA GPU Operator](./nvidia-gpu-operator.md) — driver, MIG Manager,
  time-slicing, and DRA driver integration
- [Scheduling Optimization](./scheduling-optimization.md#28-gpu-sharing-as-a-resource-layer-neutral-view)
  — GPU sharing as a schedulable resource layer
- [Agent Sandbox (archive)](../archive-blog/2025-11-28/2025-11-28-agent-sandbox.md)
  — GPU passthrough with Kata for Agent runtimes
- [GPU Fault Detection](./gpu-fault-detection.md) — remediation at MIG slice
  granularity
- [DRA Driver Feature Matrix](./dra-driver-feature-matrix.md) — HAMi DRA
  driver public feature signals

## Four Isolation Dimensions

Before comparing products, separate **what is being isolated** from **how
scheduling sees it**:

| Dimension | What it controls | Typical mechanisms | Scheduler visibility |
| --- | --- | --- | --- |
| **Resource partition** | Fixed hardware or logical slices (memory, SM, bandwidth) | MIG, HAMi memory/core quotas, DRA partitionable devices | Slice appears as discrete allocatable unit |
| **Time sharing** | Multiple processes share one context over time | CUDA time-slicing, MPS, some vGPU profiles | Often invisible or coarse-grained to scheduler |
| **Device abstraction** | How kubelet/scheduler models GPU capacity | Device Plugin, HAMi extended resources, DRA ResourceClaim | Fractional (`0.3 GPU`) or claim-based |
| **Runtime isolation** | Process/VM boundary around untrusted code | Kata passthrough, gVisor (limited GPU), VM + vGPU | Orthogonal to sharing; combines with above |

A production design usually stacks layers: e.g. **MIG partition** (hardware) +
**Kueue quota** (fairness) + **DCGM** (monitoring) + **Kata** (Agent sandbox).

## What Each Mechanism Solves

### MIG (Multi-Instance GPU)

**Problem:** Multiple tenants need **predictable, hardware-enforced** GPU slices
on a single A100/H100 without full virtualization overhead.

**How it works:** NVIDIA hardware partitions one physical GPU into up to seven
independent GPU Instances (GIs) with isolated memory and compute. Configured
via GPU Operator MIG Manager or `nvidia.com/mig.config` node labels.

**Solves:** Stable multi-tenant inference, dev/test slices with hard memory
walls, fault containment at slice level.

**Does not solve:** Elastic re-partitioning without node disruption (static
profiles), cross-GPU gang scheduling, or sub-slice memory fractions below MIG
profile granularity.

### CUDA MPS (Multi-Process Service)

**Problem:** Many **small CUDA processes** on one GPU need higher throughput
than separate contexts allow, with acceptable soft isolation.

**How it works:** A single CUDA context multiplexes client processes; optional
MPS memory limits per client. Typically deployed as a node daemon, not a
Kubernetes scheduler primitive.

**Solves:** Batch inference micro-batching, legacy apps that cannot use MIG,
high process count on one card.

**Does not solve:** Hard multi-tenant security boundaries or scheduler-aware
fractional allocation.

### vGPU (Virtual GPU)

**Problem:** **VM-based** multi-tenancy or cloud desktop scenarios need GPU
with hypervisor-enforced quotas and live migration options.

**How it works:** NVIDIA vGPU Manager assigns virtual GPUs to VMs (KubeVirt,
VMware, Citrix, etc.). GPU Operator includes vGPU Manager for supported
platforms.

**Solves:** Strong tenant separation in virtualized environments, licensed
enterprise multi-tenancy, GPU for VMs without bare-metal passthrough.

**Does not solve:** Low-overhead container-native sharing; adds hypervisor and
licensing complexity.

### HAMi (Heterogeneous AI Computing Virtualization Middleware)

**Problem:** **Heterogeneous GPU pools** (NVIDIA, Ascend, Cambricon, etc.) need
**unified fractional sharing** visible to the Kubernetes scheduler, beyond
whole-GPU or static MIG profiles.

**How it works:** CNCF Sandbox project. Device Plugin + optional scheduler
extension + NRI hooks enforce memory/core limits per Pod. Also ships
[`k8s-dra-driver`](https://github.com/Project-HAMi/k8s-dra-driver) for DRA-native
partitioning with consumable capacity signals.

**Solves:** Multi-vendor GPU virtualization, scheduler-visible GPU fractions
(`nvidia.com/gpumem`, `nvidia.com/gpucores`), dynamic oversubscription with
policy, integration with Volcano/Kueue-style queues.

**Does not solve:** Replacing hardware MIG where hard isolation is mandatory;
adds control-plane and compatibility validation burden.

### DRA (Dynamic Resource Allocation)

**Problem:** Device Plugin's `nvidia.com/gpu: 1` model cannot express **topology,
partitioning, health, binding conditions, or prioritized fallbacks** in one API.

**How it works:** Kubernetes GA resource model (v1.34+). Drivers publish
ResourceSlices; workloads use ResourceClaimTemplates. v1.36 **Partitionable
Devices (Beta)** models MIG-like slices dynamically; **Consumable Capacity
(Beta)** tracks shared pool usage.

**Solves:** GPU + NIC topology, dynamic MIG/slice allocation, migration from
extended resources, device taints, health status in Pod feedback loop.

**Does not solve:** Actual GPU slicing by itself — requires NVIDIA or HAMi DRA
driver (or other vendor driver) underneath.

### Relationship at a Glance

```text
                    ┌─────────────────────────────────────────┐
                    │         Kubernetes control plane         │
                    │  Scheduler │ Kueue/Volcano │ Quota/RL  │
                    └────────────┬────────────────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
    │ Device      │      │ HAMi        │      │ DRA         │
    │ Plugin      │      │ (fractional │      │ (claims +   │
    │ (whole GPU, │      │  resources) │      │  topology)  │
    │  time-slice,│      └──────┬──────┘      └──────┬──────┘
    │  MIG advert)│             │                    │
    └──────┬──────┘             │                    │
           │                    ▼                    ▼
           │             ┌──────────────────────────────────┐
           └────────────▶│ Node: driver, MIG Manager, MPS,  │
                         │ vGPU Manager, NRI enforcement    │
                         └──────────────────────────────────┘
```

## GPU Sharing Technology Matrix

| Mechanism | Partition type | Isolation strength | Scheduler granularity | Dynamic repartition | Multi-vendor | Ops complexity | Best fit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Whole GPU (Device Plugin)** | None (exclusive) | Strong | 1 GPU | N/A | NVIDIA-first | Low | Training, large-model inference |
| **Time-slicing** | Time share | Weak | Replica count (`replicas: N`) | Yes (config change) | NVIDIA | Low–medium | Dev/test, tiny models |
| **MIG** | Hardware partition | Strong | MIG profile per GI | Limited (profile change, often disruptive) | NVIDIA A100/H100+ | Medium | Stable inference tenants |
| **Dynamic MIG + DRA** | Hardware + API-driven | Strong | Claim-based slice | Improving (DRA PD Beta) | NVIDIA (DRA driver) | Medium–high | Mixed-size workloads on same node |
| **CUDA MPS** | Time + soft memory cap | Medium (not security) | None (node-local) | Informal | NVIDIA | Medium | Batch inference, many small processes |
| **vGPU** | Hypervisor virtual GPU | Strong (VM boundary) | vGPU profile per VM | Profile-dependent | NVIDIA (licensed) | High | VM/KubeVirt multi-tenancy |
| **HAMi** | Software quota (mem/core) | Medium–strong (policy) | Fractional extended resources | Yes (policy-driven) | Yes (heterogeneous) | Medium–high | Shared dev pools, mixed tenants |
| **HAMi DRA driver** | DRA partitionable + capacity | Medium–strong | ResourceClaim | Yes | Yes | High | Greenfield DRA + sharing |

**Reading the matrix:**

- **Isolation strength** ≠ **utilization**. MPS and time-slicing maximize
  utilization at the cost of noisy-neighbor risk.
- **Dynamic repartition** is the KubeCon China 2026 theme: DRA Partitionable
  Devices and HAMi aim to reduce static MIG profile lock-in.
- Treat **HAMi** and **DRA** as complementary: HAMi implements sharing;
  DRA standardizes how Kubernetes schedules and observes it.

## Scenario → Recommended Strategy

| Scenario | Primary recommendation | Secondary / fallback | Avoid |
| --- | --- | --- | --- |
| **Large-scale distributed training** | Whole GPU exclusive; gang scheduling (Volcano/JobSet) | DRA for GPU+NIC topology | Time-slicing, MPS, fractional sharing |
| **Online LLM inference (low P99)** | Whole GPU or MIG profile matched to model size | HAMi only with strict memory caps + SLO monitoring | MPS, aggressive oversubscription |
| **Batch / offline inference** | MPS or HAMi fractional pool | MIG for tenant isolation | Whole-GPU-per-small-job |
| **Multi-tenant Agent sandbox** | Kata GPU passthrough (1 GPU per sandbox) OR MIG slice per tenant | HAMi + warm pool for bursty dev agents | MPS with untrusted code |
| **Developer notebooks / CI** | HAMi fractional pool or time-slicing | MIG small profiles | Exclusive H100 for every notebook |
| **VM-based tenants (KubeVirt)** | vGPU or GPU passthrough per VM | — | Container time-slicing across trust boundaries |
| **Heterogeneous GPU fleet** | HAMi unified abstraction | Per-vendor Device Plugins + taints | Assuming one NVIDIA-only plugin |
| **Fragmented GPU cluster (many idle slices)** | DRA prioritized list + Partitionable Devices; descheduler | HAMi oversubscription policies | Leaving MIG slices unschedulable due to profile mismatch |

### Agent Sandbox GPU Path

Agent workloads combine **runtime isolation** with **GPU access**:

| Approach | Isolation | GPU model | When to use |
| --- | --- | --- | --- |
| **Kata + GPU passthrough** | VM-level | Whole GPU or PCI passthrough | Untrusted Agent code, tool execution |
| **gVisor** | User-space kernel | Limited / no GPU | CPU-only agents |
| **MIG slice per Sandbox** | Hardware slice | Fixed GI | Many small agents, predictable memory |
| **HAMi fraction + SandboxWarmPool** | Policy + warm Pod pool | Fractional | High churn, sub-second sandbox attach |

See [Agent Sandbox](../archive-blog/2025-11-28/2025-11-28-agent-sandbox.md) and
[GPU cold start notes](./gpu-pod-cold-start.md) for warm-pool trade-offs.

## Dynamic MIG: Benefits, Risks, and Operations

**Dynamic MIG** (reconfiguring MIG profiles at runtime, often driven by DRA
claims or operators) targets **fragmented GPU clusters** where static
`all-1g.10gb`-style labels leave capacity stranded.

### Benefits

- Higher **bin-packing** of mixed small/large workloads on one physical GPU
- **Scheduler-aligned** slices via DRA Partitionable Devices instead of
  pre-carving every node at install time
- **Fault isolation** retained vs. pure time-sharing
- Better alignment with **Kueue admission**: admit when a matching slice exists

### Risks

- **Reconfiguration latency**: changing MIG geometry can evict or block workloads
  on that GPU
- **Profile compatibility**: not all slice combinations are valid on every SKU;
  [KEP-5963 Device Compatibility Groups](https://github.com/kubernetes/enhancements/issues/5963)
  addresses mutual-exclusion scheduling
- **Observability gap**: metrics must be MIG-aware (DCGM UUID per GI)
- **Cold start**: slice preparation adds to Pod startup; see
  [Pod Startup Speed](./pod-startup-speed.md)

### Operational Complexity

| Area | Static MIG | Dynamic MIG + DRA/HAMi |
| --- | --- | --- |
| Node labeling | One profile label per node | Profile or claim-driven, may change |
| Monitoring | Per-GI DCGM dashboards | Same + allocation event audit |
| Upgrades | Drain node, apply profile | Coordinate driver + DRA driver + GPU Operator versions |
| Rollback | Re-label to known profile | Keep Device Plugin path documented |
| Testing | Profile matrix per GPU SKU | Add claim templates + preemption scenarios |

**Pragmatic rollout:** pilot on a non-production pool; benchmark against
`static MIG + native scheduler` before enabling dynamic paths in production.
See [Scheduling Optimization — GPU Sharing guardrails](./scheduling-optimization.md#28-gpu-sharing-as-a-resource-layer-neutral-view).

## Integration: Queues, Quotas, Fairness, Preemption, Monitoring

GPU sharing only works if **admission control** and **observability** match the
sharing model.

### Queue and quota layer

| Component | Role with GPU sharing |
| --- | --- |
| **[Kueue](https://github.com/kubernetes-sigs/kueue)** | ClusterQueue/localQueue admission; ResourceFlavor for GPU/MIG tiers; cohort borrowing for idle fractional capacity |
| **[Volcano](https://github.com/volcano-sh/volcano)** | Gang scheduling for training; DRF fairness across teams; integrates with HAMi scheduler extender |
| **ResourceQuota / LimitRange** | Namespace caps on `nvidia.com/gpu` or HAMi fractional resources |
| **DRA AdminAccess (GA)** | Platform team-owned claims for reserved slices |

**Pattern:** Kueue admits by **logical GPU budget**; underlying layer (MIG/HAMi/
DRA) fulfills with physical slices. Mismatch between queue semantics and device
plugin advertising causes admitted-but-pending Pods.

### Fairness and preemption

- **Training:** preemptible low-priority batch jobs via Kueue preemption;
  never preempt online inference without tier policy
- **Fractional pools:** HAMi and DRA Consumable Capacity expose **remaining
  pool** — use for autoscaling and descheduling idle fractions
- **Noisy neighbor:** enforce memory limits (HAMi/NRI/MIG), cap MPS clients,
  alert on SM util skew across co-located Pods

### Monitoring checklist

| Signal | Tool | Sharing relevance |
| --- | --- | --- |
| Per-slice utilization | DCGM Exporter | MIG GI UUID, HAMi pod labels |
| Memory pressure | DCGM + HAMi metrics | Detect oversubscription |
| Allocation events | Kube events, DRA claim status | Debug pending claims |
| Queue depth | Kueue/Volcano metrics | Backpressure vs. GPU fragmentation |
| Pod startup latency | kube-state-metrics | Dynamic MIG / warm pool impact |

See [NVIDIA GPU Operator — DCGM](./nvidia-gpu-operator.md#4-dcgm-exporter)
and [Observability README](../observability/README.md).

## When NOT to Share GPUs

Exclusive whole-GPU or **node/VM isolation** is the right default when:

1. **NCCL/RDMA multi-GPU training** — topology and bandwidth require full
   devices and predictable NVLink/NVSwitch layout ([DRA topology](./dra.md#topology-management-with-dra))
2. **Strict latency SLO** (P99 inference) — sharing adds tail latency jitter;
   see [Inference GPU Sharing](../inference/README.md#gpu-sharing)
3. **Untrusted multi-tenant code without VM boundary** — do not rely on MPS or
   time-slicing alone; use Kata passthrough or separate nodes
4. **Regulatory / confidential workloads** — prefer confidential computing or
   dedicated nodes over fractional pools
5. **Large single-process memory footprint** — exceeds largest MIG profile;
   whole GPU is simpler than failed partial allocation
6. **Frequent checkpoint/restart at scale** — shared slices complicate
   [GPU fault remediation](./gpu-fault-detection.md) and blast radius
7. **Ops maturity gap** — if DCGM, queueing, and rollback paths are not ready,
   exclusive GPUs reduce incident surface

## Selection Flow (Quick)

```text
Need GPU?
  │
  ├─ Untrusted Agent / arbitrary code?
  │    └─ Yes → Kata passthrough or dedicated node (optional MIG per sandbox)
  │
  ├─ Multi-GPU training with RDMA?
  │    └─ Yes → Whole GPU + DRA topology claims
  │
  ├─ Latency-sensitive online inference?
  │    └─ Yes → Whole GPU or static MIG matched to model
  │
  ├─ Many small jobs / dev pool / heterogeneous cards?
  │    └─ Yes → Evaluate HAMi fractional pool (+ Kueue)
  │
  ├─ VM tenants?
  │    └─ Yes → vGPU or passthrough per VM
  │
  └─ Batch throughput on single GPU?
       └─ MPS or time-slicing (monitor noisy neighbors)
```

## Implementation Pointers

### MIG via GPU Operator

```yaml
# Static profile example — see GPU Operator docs for full matrix
kubectl label node <node> nvidia.com/mig.config=all-1g.10gb --overwrite
```

See [NVIDIA GPU Operator — MIG Manager](./nvidia-gpu-operator.md#additional-components).

### Time-slicing via Device Plugin

```yaml
sharing:
  timeSlicing:
    replicas: 4
```

### HAMi fractional resources (illustrative)

```yaml
resources:
  limits:
    nvidia.com/gpu: 1          # or vendor-specific HAMi resources
    nvidia.com/gpumem: 4000    # MB quota — verify against your HAMi version
    nvidia.com/gpucores: 30    # percentage of SM
```

### DRA partitionable claim (conceptual)

Workload uses `ResourceClaimTemplate` with `deviceClassName` from
[NVIDIA](https://github.com/NVIDIA/k8s-dra-driver-gpu) or
[HAMi](https://github.com/Project-HAMi/k8s-dra-driver) DRA driver; see
[DRA v1.36 snapshot](./dra.md#v136-feature-snapshot-for-ai-infra).

## Related Issues and Further Reading

- [#303 — Large-scale GPU scheduling](https://github.com/pacoxu/AI-Infra/issues/303)
- [#258 — GPU sandbox matrix (Kata, MIG, VM)](https://github.com/pacoxu/AI-Infra/issues/258)
- [KubeCon China 2026 schedule](https://www.lfopensource.cn/kubecon-cloudnativecon-openinfra-summit-pytorch-conference-china/program/schedule/)
- [Project-HAMi](https://github.com/Project-HAMi/HAMi)
- [MIG vs vGPU — cold start perspective](../blog/2026-04-06/2026-04-06-gpu-pod-cold-start-optimization_zh.md#mig-与-vgpu-不是一回事)

---

**Note:** This is a learning repository. Validate driver versions, HAMi resource
names, and MIG profiles against your hardware SKU and vendor documentation
before production rollout.
