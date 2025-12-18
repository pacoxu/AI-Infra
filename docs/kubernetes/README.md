---
status: Active
maintainer: pacoxu
last_updated: 2025-12-17
tags: kubernetes, ai-infrastructure, scheduling, resource-management
canonical_path: docs/kubernetes/README.md
---

# Kubernetes for AI Infrastructure

Comprehensive guides for running AI workloads on Kubernetes, covering
container lifecycle, scheduling optimization, resource management, and
workload isolation.

## Learning Path

### Getting Started

- **[Kubernetes Learning Plan](./learning-plan.md)**: Structured 3-phase
  approach covering Docker basics, core Kubernetes concepts, and cloud-native
  ecosystem tools

### Core Concepts

- **[Pod Lifecycle](./pod-lifecycle.md)**: Understanding pod creation,
  scheduling, startup, and termination flows with detailed diagrams
- **[Pod Startup Speed Optimization](./pod-startup-speed.md)**: Strategies
  for accelerating pod startup including image optimization, scheduling
  improvements, and GPU workload considerations

### Advanced Topics

#### Scheduling and Resource Management

- **[Scheduling Optimization](./scheduling-optimization.md)**: Comprehensive
  guide covering high-throughput scheduling, multi-scheduler patterns,
  gang scheduling, topology-aware scheduling, load balancing, and
  descheduling strategies
- **[Dynamic Resource Allocation (DRA)](./dra.md)**: Flexible device
  allocation with structured parameters and topology awareness
- **[NVIDIA GPU Operator](./nvidia-gpu-operator.md)**: Automated GPU driver
  installation, device plugin deployment, DRA driver integration, and GPU
  monitoring with DCGM
- **[GPU Fault Detection and Self-Healing](./gpu-fault-detection.md)**:
  Comprehensive guide to detecting, diagnosing, and automatically recovering
  from GPU failures with DCGM, Node Problem Detector, and progressive
  remediation strategies
- **[Node Resource Interface (NRI)](./nri.md)**: Fine-grained container
  resource management at the runtime level

#### Workload Isolation

- **[Isolation Guide](./isolation.md)**: Comprehensive coverage of workload
  isolation techniques including cgroups, security contexts, user namespaces,
  VM-based isolation (Kata Containers, gVisor), and checkpoint/restore for
  AI workloads

#### Scalability and Large-Scale Clusters

- **[Large-Scale Clusters](./large-scale-clusters.md)**: Technologies and
  architectural patterns for running massive Kubernetes clusters (130,000+
  nodes), including Consistent Reads from Cache (KEP-2340), Snapshottable
  API Server Cache (KEP-4988), DRANET, Spanner, and Lustre distributed
  file system

## Quick Reference

### For Scheduling Engineers

1. Start with [Scheduling Optimization](./scheduling-optimization.md) for
   production patterns
2. Review [DRA](./dra.md) and [NVIDIA GPU Operator](./nvidia-gpu-operator.md)
   for GPU resource management
3. Explore [NRI](./nri.md) for fine-grained container control
4. Understand [Pod Lifecycle](./pod-lifecycle.md) for debugging

### For Platform Engineers

1. Begin with [Kubernetes Learning Plan](./kubernetes.md) for foundational
   knowledge
2. Study [Pod Startup Speed](./pod-startup-speed.md) for performance
   optimization
3. Implement [Isolation techniques](./isolation.md) for security and
   multi-tenancy

### For AI/ML Engineers

1. Focus on [Scheduling Optimization](./scheduling-optimization.md) for
   GPU workloads
2. Review [NVIDIA GPU Operator](./nvidia-gpu-operator.md) for GPU setup and
   monitoring
3. Study [GPU Fault Detection](./gpu-fault-detection.md) for production
   reliability and automated recovery
4. Study [Isolation Guide](./isolation.md) for checkpoint/restore
5. Understand [DRA](./dra.md) for complex device requirements

## Related Topics

- **Training**: See [Training Guide](../training/README.md) for distributed
  training, fault tolerance, and ML pipelines
- **Inference**: See [Inference Guide](../inference/README.md) for LLM
  serving and optimization

## Contributing

Contributions to Kubernetes-related documentation are welcome! Please ensure:

- Technical accuracy with official Kubernetes documentation
- Practical examples and production scenarios
- Links to relevant KEPs and community proposals
- Conference talks and learning resources

---

**Note**: This is a learning repository. Some content may be generated or
summarized. Please verify with official documentation before using in
production.
