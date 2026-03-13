---
status: Active
maintainer: pacoxu
date: 2025-11-25
tags: kubernetes, scheduling, topology, dra, device-plugin, gpu, nic
canonical_path: docs/blog/2025-11-25/topology-aware-scheduling.md
---

# Smarter Scheduling for AI Workloads: Topology-Aware Scheduling

## Why Topology? Why Now?

At KubeCon NA 2025, one theme dominated conversations in the AI/ML space:
**topology**. Everyone is talking about topology-aware scheduling because it's
critical for optimizing AI workload performance.

![Why Topology? Why Now?](https://github.com/user-attachments/assets/ac793010-3bd2-49a1-a0d3-4d1ec14b5154)

*Source: [Lightning Talk: Mind the Topology - Roman Baron, NVIDIA](https://www.youtube.com/watch?v=o5i7pTWZjfo)*

Modern AI workloads, especially distributed training and high-performance
inference, are extremely sensitive to hardware topology. When GPUs, NICs, CPUs,
and memory are not properly aligned within the same NUMA node, PCIe root, or
network fabric, performance can degrade by 30-50% or more.

## Background: Current Topology Scheduling Support

### Device Plugin: The Traditional Approach

Kubernetes Device Plugins have been the standard mechanism for managing
hardware resources like GPUs. The Device Plugin API provides:

![Device Management with Device Plugin](https://github.com/user-attachments/assets/3e642849-5879-4112-912b-6149825decce)

*Source: [KubeCon NA 2025: Device Management](https://www.youtube.com/watch?v=j6zkGxrxm6o&t=1007s)*

**Key Components:**

- **GetDevicePluginOptions**: Plugin configuration
- **ListAndWatch**: Report available devices to kubelet
- **GetPreferredAllocation**: Suggest optimal device allocation (topology hint)
- **Allocate**: Perform device allocation for containers
- **PreStartContainer**: Pre-container-start hooks

**Device Plugin supports:**

- Basic GPU counting (e.g., `nvidia.com/gpu: 8`)
- MIG (Multi-Instance GPU) partitioning
- Time-slicing for GPU oversubscription

### Limitations of Device Plugin

However, Device Plugins have significant limitations for topology-aware
scheduling:

![Limitations of Device Plugin Management](https://github.com/user-attachments/assets/a35ef2f0-a48a-47d3-b541-6a38b731931a)

*Source: [KubeCon NA 2025: Device Management](https://www.youtube.com/watch?v=j6zkGxrxm6o&t=1007s)*

1. **Static isolation config**: MIG configurations must be pre-defined
2. **Static slicing config**: Time-slicing ratios are fixed at deployment
3. **Only even sharing expected**: Limited sharing granularity
4. **Requires secondary scheduler**: Complex topologies need additional
   schedulers like Volcano or Kueue

### Kueue: Topology-Aware Scheduling

[Kueue](https://github.com/kubernetes-sigs/kueue) provides topology-aware
scheduling through node labels. It uses hierarchical topology levels like:

```yaml
# Node labels for rack/block topology
cloud.google.com/gce-topology-block: "block-1"
cloud.google.com/gce-topology-subblock: "subblock-1"
cloud.google.com/gce-topology-host: "host-1"
kubernetes.io/hostname: "node-1"
```

Kueue supports:

- **TopologyAwareScheduling**: Place workload pods on nodes with matching
  topology
- **Cohort-based resource sharing**: Share resources within topology groups
- **Gang scheduling with topology**: Ensure all gang members are
  topology-aligned

Kueue Topology Configuration Example:

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata:
  name: gpu-topology
spec:
  nodeLabels:
    cloud.google.com/gce-topology-block: "block-1"
  nodeTaints:
  - effect: NoSchedule
    key: nvidia.com/gpu
    value: "present"
```

### Volcano: Gang Scheduling with Topology

[Volcano](https://github.com/volcano-sh/volcano) provides advanced scheduling
features including:

- **Gang scheduling**: All-or-nothing scheduling for distributed workloads
- **Topology plugin**: Consider GPU topology in scheduling decisions
- **Network-aware scheduling**: RDMA/InfiniBand fabric awareness

```yaml
apiVersion: scheduling.volcano.sh/v1beta1
kind: PodGroup
metadata:
  name: distributed-training
spec:
  minMember: 8
  minResources:
    nvidia.com/gpu: "8"
  queue: training-queue
  # Topology affinity for NVLink connectivity
  topologyPolicy: "best-effort"
```

---

## DRA: The Next Generation of Topology Management

[Dynamic Resource Allocation (DRA)](https://github.com/kubernetes/dynamic-resource-allocation/)
represents a fundamental shift in how Kubernetes handles device topology. DRA
provides structured parameters that enable rich topology expression and
constraint specification.

### How DRA Handles Topology-Aware Scheduling

DRA uses **attributes** and **constraints** with CEL (Common Expression
Language) to express topology requirements. The key mechanisms include:

1. **Device Attributes**: Each device publishes topology information
   - `pcieRoot`: PCIe hierarchy identifier
   - `numaNode`: NUMA node association
   - `nvlinkDomain`: NVLink fabric identifier
   - `rdmaDevice`: Associated RDMA NIC

2. **Constraints**: CEL expressions that enforce topology rules
   - Same PCIe root for GPU and NIC
   - Same NUMA node for CPU and memory
   - NVLink connectivity between GPUs

3. **SharedID**: Devices on the same topology domain get a shared identifier

### GPU + NIC Topology Coordination

The most powerful use case for DRA topology is coordinating GPU and NIC
allocation on the same PCIe root. This is critical for RDMA-based distributed
training where GPU-Direct is used.

ResourceClaimTemplate with PCIe Topology Constraint Example:

```yaml
apiVersion: resource.k8s.io/v1beta1
kind: ResourceClaimTemplate
metadata:
  name: gpu-nic-topology
spec:
  spec:
    devices:
      requests:
      - name: gpu
        deviceClassName: nvidia-gpu
        count: 1
      - name: rdma-nic
        deviceClassName: rdma-nic
        count: 1
      constraints:
      # GPU and NIC must be on the same PCIe root
      - requests: ["gpu", "rdma-nic"]
        matchAttribute: pcieRoot
```

**How this works:**

1. The DRA scheduler evaluates available GPUs and NICs
2. For each candidate GPU, it finds NICs on the same PCIe root
3. Only allocations satisfying the constraint are considered
4. The `matchAttribute: pcieRoot` ensures both devices share the same
   PCIe topology

### DRANET: Network Device DRA

[DRANET](https://github.com/google/dranet) is Google's DRA implementation for
network devices. It integrates with Kueue's topology-aware scheduling using
node labels:

```yaml
# DRANET uses these labels for topology awareness
cloud.google.com/gce-topology-block
cloud.google.com/gce-topology-subblock
cloud.google.com/gce-topology-host
kubernetes.io/hostname
```

DRANET + NVIDIA GPU DRA can coordinate:

- RDMA NICs allocated with GPUs on same PCIe fabric
- Multi-NIC configurations for distributed training
- Network isolation using SR-IOV VFs

### CPU Micro-Topology Support

The [dra-driver-cpu](https://github.com/kubernetes-sigs/dra-driver-cpu/pull/16)
project is adding CPU micro-topology support including:

- NUMA-aware CPU allocation
- CPU pinning with topology alignment
- Coordination with GPU NUMA placement

---

## DRAConsumableCapacity: New in Kubernetes 1.34

A major advancement in DRA is the **DRAConsumableCapacity** feature:

![DRAConsumableCapacity](https://github.com/user-attachments/assets/12dfcd48-4307-4239-a7ba-27e114445790)

*Source: [KubeCon NA 2025: Device Management](https://www.youtube.com/watch?v=j6zkGxrxm6o&t=1007s)*

**Key Capabilities:**

- **Alpha feature** introduced in Kubernetes 1.34
- Recommended to start using from Kubernetes 1.35 (still in Alpha)

**Core abilities:**

- **Allow multiple allocations** over multiple resource requests
- **Consumable capacity**: Guaranteed resource sharing

**Potential use cases:**

- Virtual GPU Memory Partitioning
- Virtual NIC (vNIC) Sharing
- Bandwidth-limited Network Allocation
- I/O Bandwidth Smart Storage Device Sharing
- Native Resource Request (CPU)

This enables much more flexible resource sharing while maintaining topology
awareness.

---

## Challenges: Device Plugin to DRA Migration

Many organizations have invested heavily in Device Plugin-based solutions.
Migrating to DRA presents several challenges:

### 1. Existing Device Plugin Investments

Organizations may have:

- Custom Device Plugins with topology logic
- Integration with monitoring and observability tools
- Operator workflows depending on Device Plugin APIs

### 2. Coexistence Problems

Running Device Plugin and DRA together can cause:

- **Resource conflicts**: Same device managed by both systems
- **Topology inconsistency**: Different topology views between systems
- **Scheduling confusion**: Scheduler doesn't have unified view

### 3. Feature Gaps

Some Device Plugin features don't have DRA equivalents yet:

- **Device health monitoring**: Device Plugin has built-in health checks
- **Hot-plug support**: Device Plugin supports dynamic device addition
- **Metrics integration**: Prometheus metrics from Device Plugins

### Solutions and Workarounds

**DRA Extension Capabilities:**

- DRA drivers can implement compatibility layers
- NVIDIA's DRA driver supports Device Plugin migration path
- NRI integration can bridge runtime-level gaps

**Recommended Migration Path:**

1. Deploy DRA driver alongside existing Device Plugin
2. Use node taints to partition workloads
3. Gradually migrate workloads to DRA-based resource claims
4. Phase out Device Plugin once all workloads migrated

---

## Related KubeCon Talks

Several excellent talks from KubeCon NA 2025 cover these topics:

### Lightning Talk: Mind the Topology

[Mind the Topology: Smarter Scheduling for AI Workloads on Kubernetes](https://www.youtube.com/watch?v=o5i7pTWZjfo)
by Roman Baron, NVIDIA

Key topics:

- Why topology matters for AI workloads
- NVIDIA KAI Scheduler for topology-aware scheduling
- [NVIDIA KAI-Scheduler](https://github.com/NVIDIA/KAI-Scheduler)

### Device Management Deep Dive

[Deep dive into DRA and Device Plugin](https://www.youtube.com/watch?v=j6zkGxrxm6o)

Key topics:

- Evolution from Device Plugin to DRA
- DRAConsumableCapacity feature
- Multi-device topology coordination

---

## Best Practices for Topology-Aware Scheduling

1. **Understand your topology requirements**
   - Profile workloads to identify topology sensitivity
   - Map hardware topology (PCIe, NUMA, NVLink, RDMA)

2. **Choose the right scheduling approach**
   - Simple GPU workloads: Device Plugin + Topology Manager
   - Complex multi-device: DRA with constraints
   - Distributed training: Kueue or Volcano + DRA

3. **Label nodes with topology information**
   - Use consistent labeling scheme
   - Include rack, block, and host-level topology

4. **Test topology impact**
   - Benchmark with and without topology alignment
   - Measure latency and throughput differences

5. **Plan for migration**
   - Start with new workloads on DRA
   - Create compatibility tests
   - Document topology requirements

---

## Conclusion

Topology-aware scheduling has evolved from a nice-to-have feature to a critical
requirement for AI workloads. The transition from Device Plugin to DRA
represents a fundamental shift in how Kubernetes manages hardware topology:

- **Device Plugin**: Simple, established, but limited topology support
- **DRA**: Rich topology expression, multi-device coordination, future of
  Kubernetes device management

As AI workloads continue to grow in complexity, the need for sophisticated
topology-aware scheduling will only increase. Whether you're using Kueue,
Volcano, or native Kubernetes scheduling, understanding topology and planning
for DRA adoption is essential for optimizing your AI infrastructure.

---

## Resources

### Projects

- [DRA - Dynamic Resource Allocation](https://github.com/kubernetes/dynamic-resource-allocation/)
- [NVIDIA DRA GPU Driver](https://github.com/NVIDIA/k8s-dra-driver-gpu)
- [NVIDIA KAI Scheduler](https://github.com/NVIDIA/KAI-Scheduler)
- [Kueue](https://github.com/kubernetes-sigs/kueue)
- [Volcano](https://github.com/volcano-sh/volcano)
- [DRANET](https://github.com/google/dranet)
- [dra-driver-cpu](https://github.com/kubernetes-sigs/dra-driver-cpu)

### Documentation

- [DRA Kubernetes Documentation](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)
- [GCE Topology Policies](https://cloud.google.com/compute/docs/instances/use-compact-placement-policies#verify-vm-location)
- [Kubernetes Topology Manager](https://kubernetes.io/docs/tasks/administer-cluster/topology-manager/)

### Videos

- [Mind the Topology - Roman Baron, NVIDIA](https://www.youtube.com/watch?v=o5i7pTWZjfo)
- [Device Management Deep Dive](https://www.youtube.com/watch?v=j6zkGxrxm6o)

---

**Author**: AI Infrastructure Learning Path
**Date**: November 25, 2025
**Tags**: #kubernetes #scheduling #topology #dra #device-plugin #gpu #nic
