---
status: Active
maintainer: pacoxu
last_updated: 2025-12-15
tags: kubernetes, bytedance, kubebrain, kubeadmiral, godel, katalyst,
  large-scale, multi-cluster
---

# ByteDance's Solution for Ultra-Large-Scale Kubernetes Clusters

ByteDance addresses ultra-large-scale Kubernetes requirements through a
combination of KubeAdmiral for multi-cluster orchestration and KubeBrain
for single-cluster metadata storage, supporting stable operation of clusters
with over 20,000 nodes. The Gödel scheduler and Katalyst resource management
system further optimize large-scale cluster performance.

## Table of Contents

- [Single-Cluster Scaling: KubeBrain](#single-cluster-scaling-kubebrain)
- [Multi-Cluster Orchestration: KubeAdmiral](#multi-cluster-orchestration-kubeadmiral)
- [Scheduler Optimization: Gödel](#scheduler-optimization-gödel)
- [Resource Management: Katalyst](#resource-management-katalyst)
- [References](#references)

## Single-Cluster Scaling: KubeBrain

### Background

KubeBrain is ByteDance's metadata storage system designed to replace etcd in
Kubernetes clusters. Built on distributed KV storage engines, it supports
stable operation of ultra-large-scale Kubernetes clusters with over 20,000
nodes in production.

### Architecture Design

KubeBrain adopts a layered architecture with a Storage Engine Interface that
supports multiple distributed KV storage backends:

![KubeBrain Architecture](https://github.com/user-attachments/assets/188bac43-ae01-404c-b9dd-220f94149b20)

Core components include:

- **KubeBrain Core**: Provides Kubernetes API Server compatible interface
- **Storage Engine Interface**: Unified storage engine abstraction layer
- **ByteKV Adaptor**: ByteDance internal distributed KV storage adapter
- **TiKV Adaptor**: Open-source TiKV storage adapter
- **Extensible Support**: Can adapt to other distributed KV storage engines

### Open Source Status

KubeBrain is now open-sourced based on TiKV:

- **GitHub**: <https://github.com/kubewharf/kubebrain>
- **Compatibility**: Supports Kubernetes < 1.25
- **Performance Advantages**: Significantly higher read/write throughput
  than etcd

![KubeBrain Performance](https://github.com/user-attachments/assets/efc3b59b-e3da-4c3a-b623-cd59feb0a223)

Performance benchmark results show:

- **Insert Throughput**: KubeBrain achieves 16,000+ ops/s vs etcd ~14,000 ops/s
- **Read Throughput**: KubeBrain achieves 14,000+ ops/s vs etcd ~14,000 ops/s
- **Events Write**: KubeBrain achieves 16,000+ ops/s vs etcd ~8,000 ops/s
- **PIread (Point In time read)**: KubeBrain achieves 14,000+ ops/s vs
  etcd ~8,000 ops/s

### Future Plans

- More feature support: bookmark, graceful leader change, storage backend
  patch, etc.
- Performance optimization on TiKV
- Compatibility with latest Kubernetes versions

### KubeCon Presentation

**An Alternative Metadata System for Large Kubernetes Clusters**

- Speakers: Yingcai Xue & Yixiang Chen, ByteDance
- Conference: KubeCon + CloudNativeCon China 2025
- Video: <https://www.youtube.com/watch?v=MGOa8Nn8_S0&t=1473s>
- Schedule: <https://sched.co/1i7oo>

![KubeCon China 2025 KubeBrain Talk](https://github.com/user-attachments/assets/71750e44-1c80-432c-a877-d0c54d49ae8a)

## Multi-Cluster Orchestration: KubeAdmiral

### Background

As business scale expands, a single cluster often cannot meet all requirements.
ByteDance open-sourced KubeAdmiral, a next-generation multi-cluster
orchestration and scheduling engine based on Kubernetes.

![ByteDance Multi-Cluster Evolution](https://github.com/user-attachments/assets/9f1084b2-32c9-4b1e-a6e6-755d440afe9a)

### Evolution Journey

ByteDance's multi-cluster architecture has evolved through three generations:

#### First Generation Infrastructure (2015-2017)

- Core business services went cloud-native
- TCE platform construction completed
- Unified company-wide SRE system

#### Second Generation Infrastructure (2018-2019)

- Focus on cluster scale and resource efficiency
- 2019: KubeFed introduced as foundation for cluster federation

#### Third Generation Infrastructure (2021-2022+)

- Application diversification and fine-grained scheduling requirements
- 2021: Third-generation federation KubeAdmiral released

### KubeAdmiral Core Features

- **Multi-Cluster Application Management**: Unified management of applications
  across multiple Kubernetes clusters
- **Intelligent Scheduling**: Smart scheduling based on resource, topology,
  affinity and other policies
- **Failover**: Automatic detection of cluster failures and workload migration
- **Flexible Federation Policies**: Support for multiple resource distribution
  and scheduling strategies

### References

- **Official Blog**: [ByteDance Open Sources KubeAdmiral: Next-Generation
  Multi-Cluster Orchestration Engine](https://mp.weixin.qq.com/s/aS18urPF8UB4K2I_9ECbHg)
  (Chinese)
- **GitHub Repository**: <https://github.com/kubewharf/kubeadmiral>

## Scheduler Optimization: Gödel

### Background

In large-scale Kubernetes clusters, the default scheduler often becomes a
performance bottleneck. ByteDance developed the Gödel scheduler to optimize
scheduling performance in large clusters.

![Gödel Unified Scheduling](https://github.com/user-attachments/assets/bc2c4887-8984-490c-8295-8b82f0603caa)

### Unified Scheduling Architecture

Gödel adopts a unified scheduling architecture with the following layers:

#### Platform Tenant Layer

- PaaS Platform
- ML Platform
- BigData Platform
- Function as a Service
- Storage Services

#### Cloud-Native Application Layer

- Deployment
- SolarNG
- L*x
- Other cloud-native applications

#### Tenant Access Layer

- **vKubernetes**: Virtual Kubernetes clusters
- **Yarn on Gödel**: Big data workload access
- **KubeZoo**: Multi-tenancy management

#### Resource Pooling Layer

- **Global Quota**: Global quota management
- **Workload Dispatch**: Workload distribution
- **Resource Dispatch**: Resource scheduling

#### Single-Cluster Scheduling Layer

Multiple single clusters running in parallel with flat quota management support

### Key Optimizations

- **High Throughput**: Supports large-scale pod scheduling
- **Resource Pooling**: Unified management of multi-cluster resources
- **Multi-Tenancy Support**: Isolation of different types of workloads
- **Flexible Quota Management**: Coordination of global and cluster quotas

### References

- **Technical Blog**: [ByteDance Large-Scale K8s Cluster Management
  Practice](https://mp.weixin.qq.com/s/P3-CrOVSSaVAT5tH9m06EA) (Chinese)
- **KubeCon Talk**: <https://sched.co/1i7pp>

## Resource Management: Katalyst

### Background

Katalyst is ByteDance's open-source Kubernetes resource management system,
focused on improving resource utilization and application service quality in
large-scale clusters.

![Gödel and Katalyst Integration](https://github.com/user-attachments/assets/f8962f4d-4cb7-412c-99bc-08667a9b8dd6)

### Core Capabilities

- **QoS-Aware Scheduling**: Intelligent scheduling based on quality of service
- **Resource Overcommit**: Safe resource overcommit strategies
- **Dynamic Resource Adjustment**: Dynamic resource adjustment based on actual
  workload
- **Co-location Optimization**: Optimization for online services and offline
  task co-location

### Architecture Advantages

Katalyst works together with the Gödel scheduler to form a complete resource
management solution:

- **Scheduling Layer**: Gödel handles global workload scheduling
- **Node Layer**: Katalyst manages node-level resource management and QoS
  guarantees
- **Feedback Loop**: Real-time feedback of node resource status to the scheduler

![Gödel Federation Architecture](https://github.com/user-attachments/assets/f3f1f392-eef1-4932-8f73-8b0a5d5af335)

### References

- **GitHub Repository**: <https://github.com/kubewharf/katalyst-core>
- **KubeCon Talk**: <https://sched.co/1i7pp>

## References

### Single-Cluster Scaling: KubeBrain

- [KubeBrain Official Blog (WeChat)](https://mp.weixin.qq.com/s/osJfi_oOfhEmQJNVqKel3Q)
  (Chinese)
- [KubeBrain GitHub](https://github.com/kubewharf/kubebrain)
- [KubeCon China 2025 Presentation](https://www.youtube.com/watch?v=MGOa8Nn8_S0&t=1473s)
- [KubeCon China 2025 Schedule](https://sched.co/1i7oo)

### Multi-Cluster Orchestration: KubeAdmiral

- [KubeAdmiral Official Blog (WeChat)](https://mp.weixin.qq.com/s/aS18urPF8UB4K2I_9ECbHg)
  (Chinese)
- [KubeAdmiral GitHub](https://github.com/kubewharf/kubeadmiral)

### Scheduler Optimization: Gödel

- [ByteDance Large-Scale K8s Cluster Management
  Practice](https://mp.weixin.qq.com/s/P3-CrOVSSaVAT5tH9m06EA) (Chinese)
- [KubeCon Talk: Gödel and Katalyst](https://sched.co/1i7pp)

### Resource Management: Katalyst

- [Katalyst GitHub](https://github.com/kubewharf/katalyst-core)
- [KubeCon Talk: Gödel and Katalyst](https://sched.co/1i7pp)

### Related Documentation

- [Large-Scale Kubernetes Clusters](../kubernetes/large-scale-clusters.md)
- [Scheduling Optimization](../kubernetes/scheduling-optimization.md)

---

**Note**: This document is based on ByteDance's publicly released technical
blogs and KubeCon presentations. For specific implementation details, please
refer to official documentation and GitHub repositories.
