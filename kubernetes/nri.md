# Node Resource Interface (NRI)

[NRI](https://github.com/containerd/nri) is Node Resource Interface for
containerd, enabling fine-grained and pluggable container resource management
at the node level.

## Overview

NRI provides a plugin interface for containerd that allows external components
to:

- Modify container resource allocations at runtime
- Inject custom device configurations
- Implement advanced resource management policies
- Enable fine-grained GPU sharing and partitioning

NRI complements DRA by operating at the runtime layer, while DRA handles
cluster-level scheduling decisions.

**See also:**
[Scheduling Optimization Guide](./scheduling-optimization.md#26-topology-aware-scheduling)
for NRI integration with scheduling strategies.

## Learning Resources

### Conference Talks

- **KCD Shanghai 2024** (Chinese): [基于 NRI
  实现精细化且可插拔的容器资源管理](https://www.bilibili.com/video/BV1pp421Q7o5)
  - Cloud Native Infrastructure and OS Track
- **KubeCon NA 2024**: [Improving GPU Utilization and Accelerating Model
  Training with Scheduling Framework and
  NRI](https://www.youtube.com/watch?v=Gc5M1y4Er8g&t=3s) - He Cao

### Related Projects

- [containerd/nri](https://github.com/containerd/nri): Official NRI
  implementation
- [Project HAMi](https://github.com/Project-HAMi/HAMi): GPU sharing using NRI
  (CNCF Sandbox)
