---
status: Active
maintainer: pacoxu
last_updated: 2025-10-29
tags: kubernetes, dra, resource-allocation, device-management
canonical_path: docs/kubernetes/dra.md
---

# Dynamic Resource Allocation (DRA)

[DRA](https://github.com/kubernetes/dynamic-resource-allocation/) is Dynamic
Resource Allocation for Kubernetes, enabling flexible device allocation with
structured parameters and topology awareness.

## Overview

DRA provides a more flexible alternative to the traditional device plugin
framework, supporting:

- Complex device requirements (GPU + NIC + storage combinations)
- Topology-aware scheduling (NUMA, NVLink, InfiniBand)
- Structured parameters for fine-grained device configuration
- Multiple device types per pod

![dra](./diagrams/dra-user-flow.svg)

**See also:**
[Scheduling Optimization Guide](./scheduling-optimization.md#26-topology-aware-scheduling)
for DRA usage in production scenarios.

## KEPs and Roadmap

- DRA: structured parameters
  [#4381](https://github.com/kubernetes/enhancements/issues/4381). GA in
  v1.34.
- All KEPs about DRA:
  [GitHub Issues](https://github.com/kubernetes/enhancements/issues/?q=is%3Aissue%20%20DRA%20in%3Atitle)

**Performance Testing:**

See [DRA Performance Testing](./dra-performance-testing.md) for comprehensive
scale testing, performance benchmarks, and production best practices.

## DRA Driver Implementations

### NVIDIA DRA Driver for GPUs

<a href="https://github.com/NVIDIA/k8s-dra-driver-gpu">**NVIDIA DRA Driver for
GPUs**</a> is NVIDIA's reference implementation of DRA for GPU resource
management.

**Architecture:**

The driver includes two kubelet plugins:

- <a href="https://github.com/NVIDIA/k8s-dra-driver-gpu/tree/main/cmd/gpu-kubelet-plugin">**gpu-kubelet-plugin**</a>:
  Standard GPU resource allocation using DRA
- <a href="https://github.com/NVIDIA/k8s-dra-driver-gpu/tree/main/cmd/compute-domain-kubelet-plugin">**compute-domain-kubelet-plugin**</a>:
  Advanced plugin for compute domain management

**Key Features:**

- GB200 support with specialized compute domain management
  (<a href="https://docs.google.com/presentation/d/1Xupr8IZVAjs5bNFKJnYaK0LE7QWETnJjkz6KOfLu87E/edit?pli=1&slide=id.g373e0ebfa8e_1_233#slide=id.g373e0ebfa8e_1_233">architecture
  presentation</a>)
- Topology-aware GPU scheduling (NVLink, NVSwitch awareness)
- Fine-grained resource allocation beyond simple GPU counts
- Support for complex multi-GPU configurations

**Integration:**

- Will be integrated into <a href="./nvidia-gpu-operator.md">NVIDIA GPU
  Operator</a> in future releases
- Provides migration path from traditional device plugin to DRA

**See also:** [NVIDIA GPU Operator](./nvidia-gpu-operator.md) for comprehensive
coverage of NVIDIA GPU management in Kubernetes.

## Learning Resources

### Conference Talks

- **KubeCon NA 2024**: [Kubernetes WG Device Management - GPUs, TPUs, NICs
  and More With DRA](https://www.youtube.com/watch?v=Z_15EyXOnhU) - Kevin
  Klues & Patrick Ohly

### Additional Resources

- [Kubernetes docs](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/), [GKE docs](https://cloud.google.com/kubernetes-engine/docs/concepts/about-dynamic-resource-allocation), [Kubernetes blog](https://kubernetes.io/blog/2025/05/01/kubernetes-v1-33-dra-updates/)
- [YouTube search: DRA](https://www.youtube.com/@cncf/search?query=DRA)
- [Kubernetes WG Device
  Management](https://github.com/kubernetes/community/blob/master/wg-device-management/README.md)
