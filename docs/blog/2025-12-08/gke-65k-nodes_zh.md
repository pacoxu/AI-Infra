---
status: Active
maintainer: pacoxu
date: 2025-12-08
tags: kubernetes, gke, scalability, ai-workloads, google-cloud
canonical_path: docs/blog/2025-12-08/gke-65k-nodes_zh.md
source_urls:
  - https://cloud.google.com/blog/products/containers-kubernetes/benchmarking-a-65000-node-gke-cluster-with-ai-workloads
  - https://cloud.google.com/blog/products/containers-kubernetes/gke-65k-nodes-and-counting
---

# GKE 支持高达 65,000 个节点：AI 工作负载的超大规模基准测试

<img src="https://github.com/user-attachments/assets/f596e3ff-f91a-4719-b065-1dd1d9d907d3" alt="Support for up to 65,000 nodes" width="800">

## 概述

Google Kubernetes Engine (GKE) 现已支持高达 65,000 个节点的超大规模集群，
这是 Kubernetes 生态系统中的一个重要里程碑。本文将介绍 GKE 如何在保持
性能和可靠性的同时实现这一规模，以及针对 AI 工作负载的基准测试结果。

**原文链接：**

第一篇：
<https://cloud.google.com/blog/products/containers-kubernetes/benchmarking-a-65000-node-gke-cluster-with-ai-workloads>

第二篇：
<https://cloud.google.com/blog/products/containers-kubernetes/gke-65k-nodes-and-counting>

## 背景：为什么需要 65,000 个节点？

随着人工智能和机器学习工作负载的快速发展，企业需要运行越来越大规模的训练和
推理任务。这些工作负载通常具有以下特点：

- **大规模并行训练**：需要数千甚至数万个 GPU 协同工作
- **分布式推理**：需要在多个节点上部署模型以支持高并发请求
- **动态资源需求**：工作负载需要快速扩缩容以应对业务需求变化
- **混合工作负载**：同时运行训练、推理和数据处理任务

GKE 的 65K 节点支持为这些场景提供了强大的基础设施能力。

## 架构优化

为了支持如此大规模的集群，GKE 团队对 Kubernetes 的多个核心组件进行了优化：

### 1. 调度器优化

<img src="https://github.com/user-attachments/assets/8344bbfa-0ed9-4553-89ab-8f05d4f732aa" alt="Scheduler architecture with 65K nodes and 65K pods" width="400">

上图展示了 kube-scheduler 如何管理 65K 节点和 65K Pods 的训练工作负载
（使用 StatefulSet）。数据平面与训练工作负载之间的协调是实现大规模集群
的关键。

### 2. 混合工作负载支持

<img src="https://github.com/user-attachments/assets/f49f0577-57bc-461a-85f2-1fd0e6d426df" alt="Mixed training and inference workloads" width="400">

GKE 支持在同一集群中运行训练和推理工作负载：

- **50K Pods** 用于训练工作负载（StatefulSet）
- **15K Pods** 用于推理工作负载（StatefulSet）
- **65K 节点**的数据平面提供统一的资源池

这种架构允许企业在单个集群中整合不同类型的 AI 工作负载，
提高资源利用率。

### 3. 工作负载隔离与抢占

<img src="https://github.com/user-attachments/assets/977c021b-2f2c-44a6-92da-667679959e23" alt="Workload isolation with preemption" width="600">

GKE 实现了智能的工作负载隔离机制：

- **数据平面**：65K 节点提供计算资源
- **训练工作负载**：50K Pods（可被抢占）使用 StatefulSet 管理
- **推理工作负载**：65K Pods 使用 StatefulSet 管理，优先级更高
- **抢占机制**：当推理工作负载需要资源时，训练 Pods 可以被抢占
  （图中标记为 X）

这种设计确保了高优先级的推理服务始终有足够的资源，同时充分利用空闲
资源进行训练任务。

### 4. 故障恢复能力

<img src="https://github.com/user-attachments/assets/f9becd75-f263-4684-a71b-04a1c91b8273" alt="Fault recovery for training workloads" width="400">

GKE 提供强大的故障恢复能力：

- **训练工作负载**：50K Pods 在发生故障后可以自动恢复
- **推理工作负载**：15K Pods 在缩容后可以自动调整
- **StatefulSet 保证**：有状态工作负载的持久化身份和存储

## 性能基准测试

<img src="https://github.com/user-attachments/assets/68363535-de37-40e0-bfde-357cc662b395" alt="Performance benchmarks" width="600">

GKE 团队对 65K 节点集群进行了全面的性能基准测试，重点关注以下指标：

### Pod 启动时间

<img src="https://github.com/user-attachments/assets/2e74c05e-f72a-4272-aaee-459ded17ed56" alt="Pod startup time metrics" width="600">

在大规模集群中，Pod 启动时间是关键性能指标。GKE 通过以下优化实现了
快速启动：

- **镜像预拉取**：在节点上预先拉取常用镜像
- **并行调度**：优化调度器以支持大规模并行 Pod 创建
- **资源预分配**：提前分配资源以减少启动延迟

### API 服务器性能

<img src="https://github.com/user-attachments/assets/8e8a3bce-abbb-4f2f-adca-943c764c31b5" alt="API server performance" width="600">

API 服务器是 Kubernetes 的核心组件，GKE 对其进行了以下优化：

- **水平扩展**：API 服务器可以水平扩展以处理更多请求
- **缓存优化**：改进缓存策略以减少 etcd 负载
- **限流和优先级**：为不同类型的请求设置优先级和限流策略

## 控制平面优化

<img src="https://github.com/user-attachments/assets/90a6ccf3-3a14-4f86-9811-ac2e36555dd9" alt="Control plane optimization" width="600">

GKE 的控制平面经过特别优化以支持超大规模集群：

### 核心组件扩展

- **kube-apiserver**：多副本部署，支持负载均衡
- **kube-scheduler**：优化调度算法，支持大规模并行调度
- **kube-controller-manager**：优化控制器循环，减少资源消耗
- **etcd**：使用高性能存储和优化的配置

### 监控和可观测性

<img src="https://github.com/user-attachments/assets/886bc061-8301-40b6-a71c-de7006fc9ede" alt="Monitoring and observability" width="600">

在超大规模集群中，监控和可观测性至关重要：

- **分层监控**：在不同层次收集和聚合指标
- **采样策略**：智能采样以减少监控开销
- **告警优化**：针对大规模集群优化告警规则

## 网络优化

<img src="https://github.com/user-attachments/assets/aa33ade7-6700-4a99-853a-a5e6319038cc" alt="Network optimization" width="600">

大规模集群对网络性能提出了更高要求：

- **VPC 原生网络**：利用 Google Cloud 的 VPC 网络提供高性能、低延迟连接
- **网络策略优化**：高效实现网络隔离和安全策略
- **负载均衡**：支持大规模服务的负载均衡需求

## 实际应用场景

GKE 的 65K 节点支持为以下场景提供了强大能力：

### 大规模 AI 训练

- **分布式训练**：支持在数千个 GPU 上并行训练大型语言模型
- **超参数调优**：并行运行大量实验以找到最佳模型配置
- **数据并行**：在多个节点上分布式处理大规模数据集

### 高并发推理服务

- **模型服务**：支持部署数千个模型副本以处理高并发请求
- **A/B 测试**：并行运行多个模型版本进行比较
- **多模型部署**：在同一集群中部署多种不同的模型

### 混合工作负载

- **资源共享**：训练和推理工作负载共享资源池
- **成本优化**：通过抢占式实例降低成本
- **弹性伸缩**：根据需求自动扩缩容

## 最佳实践

基于 GKE 65K 节点的实践经验，以下是一些最佳实践建议：

### 1. 工作负载设计

- **使用 StatefulSet**：对于有状态工作负载，使用 StatefulSet 确保持久化身份
- **设置资源限制**：明确定义 CPU 和内存限制，避免资源争用
- **优先级和抢占**：为不同工作负载设置合适的优先级

### 2. 调度优化

- **节点亲和性**：使用节点亲和性将 Pods 调度到合适的节点
- **Pod 亲和性/反亲和性**：控制 Pods 之间的分布
- **Taints 和 Tolerations**：隔离特殊工作负载

### 3. 监控和诊断

- **关键指标监控**：监控 API 服务器延迟、调度器性能等关键指标
- **日志聚合**：使用集中式日志聚合系统
- **分布式追踪**：实现端到端的请求追踪

### 4. 安全性

- **网络策略**：实施网络隔离策略
- **RBAC**：使用细粒度的访问控制
- **密钥管理**：安全存储和使用敏感信息

## Kubernetes 社区贡献

<img src="https://github.com/user-attachments/assets/981d3cf4-b87a-4fcc-abc2-7034fe9c34aa" alt="KubeCon keynote 1" width="600">

<img src="https://github.com/user-attachments/assets/5dc414c5-be54-4fb7-b0bb-131f424a645b" alt="KubeCon keynote 2" width="600">

在去年的 KubeCon 北美大会上，Google 在主题演讲中分享了"Kubernetes
第二个十年：平衡创新与稳定性"的话题。演讲者 Jago Macleod 讨论了
Kubernetes 如何在保持稳定性的同时继续创新，GKE 的 65K 节点支持正是
这一理念的体现。

**演讲链接：**

Kubernetes in the Second Decade: Balancing Innovation with Stability - Jago Macleod

GKE 团队将这些大规模优化的经验反馈给 Kubernetes 社区，帮助整个生态
系统提升可扩展性能力。许多优化已经合并到 Kubernetes 上游项目中，
使所有用户都能受益。

## 未来展望

GKE 的 65K 节点支持只是开始。随着 AI 工作负载的持续增长，我们预期：

- **更大规模**：支持超过 100K 节点的集群
- **更好的性能**：进一步优化调度和资源管理
- **更智能的调度**：基于 AI 的智能调度算法
- **更低的成本**：通过混合使用不同类型的实例降低成本

## 总结

GKE 的 65,000 节点支持代表了 Kubernetes 在大规模集群管理方面的重大进步。
通过对调度器、API 服务器、网络和控制平面的深度优化，GKE 能够为企业的
AI 工作负载提供可靠、高性能的基础设施。

无论您是在运行大规模的模型训练、高并发的推理服务，还是混合工作负载，
GKE 都能提供所需的规模和性能。随着 AI 技术的不断发展，Kubernetes 和 GKE
将继续演进，为下一代 AI 应用提供强大支持。

## 参考资源

**原文博客：**

第一篇：
<https://cloud.google.com/blog/products/containers-kubernetes/benchmarking-a-65000-node-gke-cluster-with-ai-workloads>

第二篇：
<https://cloud.google.com/blog/products/containers-kubernetes/gke-65k-nodes-and-counting>

**相关资源：**

- GKE 文档：<https://cloud.google.com/kubernetes-engine/docs>
- Kubernetes 大规模最佳实践：
  <https://kubernetes.io/docs/setup/best-practices/>
- Kubernetes 调度器优化：
  <https://kubernetes.io/docs/concepts/scheduling-eviction/>

---

**注意**：本文基于 Google Cloud 官方博客编译整理，部分技术细节可能随
版本更新而变化。建议查阅最新的官方文档获取准确信息。
