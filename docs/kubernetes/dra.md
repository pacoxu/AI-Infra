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

**See also:**
[Scheduling Optimization Guide](./scheduling-optimization.md#26-topology-aware-scheduling)
for DRA usage in production scenarios.

## KEPs and Roadmap

- DRA: structured parameters
  [#4381](https://github.com/kubernetes/enhancements/issues/4381). GA in
  v1.34.
- All KEPs about DRA:
  [GitHub Issues](https://github.com/kubernetes/enhancements/issues/?q=is%3Aissue%20%20DRA%20in%3Atitle)

## Learning Resources

### Conference Talks

- **KubeCon NA 2024**: [Kubernetes WG Device Management - GPUs, TPUs, NICs
  and More With DRA](https://www.youtube.com/watch?v=Z_15EyXOnhU) - Kevin
  Klues & Patrick Ohly

### Additional Resources

- [YouTube search: DRA](https://www.youtube.com/@cncf/search?query=DRA)
- [Kubernetes WG Device
  Management](https://github.com/kubernetes/community/blob/master/wg-device-management/README.md)
