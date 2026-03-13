---
status: Active
maintainer: pacoxu
last_updated: 2025-12-15
tags: kubernetes, bytedance, kubebrain, kubeadmiral, godel, katalyst,
  large-scale, multi-cluster
---

# 字节跳动如何解决超大规模 Kubernetes 需求

字节跳动通过多集群编排系统 KubeAdmiral 和单集群元数据存储系统 KubeBrain
的组合方案，支撑了超过 20,000 节点的超大规模 Kubernetes 集群稳定运行，
并通过 Gödel 调度器和 Katalyst 资源管理系统进一步优化大规模集群的性能。

## 目录

- [单集群大规模方案：KubeBrain](#单集群大规模方案kubebrain)
- [多集群编排方案：KubeAdmiral](#多集群编排方案kubeadmiral)
- [调度器优化：Gödel](#调度器优化gödel)
- [资源管理：Katalyst](#资源管理katalyst)
- [参考资料](#参考资料)

## 单集群大规模方案：KubeBrain

### 背景

KubeBrain 是字节跳动针对 Kubernetes 元信息存储的使用需求，
基于分布式 KV 存储引擎设计并实现的取代 etcd 的元信息存储系统，
支撑线上超过 20,000 节点的超大规模 Kubernetes 集群的稳定运行。

### 架构设计

KubeBrain 采用分层架构，通过 Storage Engine Interface 支持多种分布式 KV
存储后端：

![KubeBrain Architecture](https://github.com/user-attachments/assets/188bac43-ae01-404c-b9dd-220f94149b20)

核心组件包括：

- **KubeBrain Core**: 提供 Kubernetes API Server 兼容接口
- **Storage Engine Interface**: 统一的存储引擎抽象层
- **ByteKV Adaptor**: 字节内部分布式 KV 存储适配器
- **TiKV Adaptor**: 开源 TiKV 存储适配器
- **扩展支持**: 可适配其他分布式 KV 存储引擎

### 开源状态

KubeBrain 现已基于 TiKV 开源：

- **GitHub**: <https://github.com/kubewharf/kubebrain>
- **兼容性**: 支持 Kubernetes < 1.25 版本
- **性能优势**: 读写吞吐量显著高于 etcd

![KubeBrain Performance](https://github.com/user-attachments/assets/efc3b59b-e3da-4c3a-b623-cd59feb0a223)

性能测试结果显示：

- **Insert 吞吐量**: KubeBrain 达到 16,000+ ops/s，etcd 约 14,000 ops/s
- **Read 吞吐量**: KubeBrain 达到 14,000+ ops/s，etcd 约 14,000 ops/s
- **Events 写入**: KubeBrain 达到 16,000+ ops/s，etcd 约 8,000 ops/s
- **PIread (Point In time read)**: KubeBrain 达到 14,000+ ops/s，
  etcd 约 8,000 ops/s

### 未来规划

- 更多特性支持：bookmark、graceful leader change、storage backend patch 等
- 基于 TiKV 的性能优化
- 兼容最新版本 Kubernetes

### KubeCon 演讲

**An Alternative Metadata System for Large Kubernetes Clusters**

- 演讲者：Yingcai Xue & Yixiang Chen, ByteDance
- 会议：KubeCon + CloudNativeCon China 2025
- 视频链接：<https://www.youtube.com/watch?v=MGOa8Nn8_S0&t=1473s>
- 会议主页：<https://sched.co/1i7oo>

![KubeCon China 2025 KubeBrain Talk](https://github.com/user-attachments/assets/71750e44-1c80-432c-a877-d0c54d49ae8a)

## 多集群编排方案：KubeAdmiral

### 背景

随着业务规模的扩大，单集群往往难以满足所有需求。
字节跳动开源了 KubeAdmiral，这是一个基于 Kubernetes
的新一代多集群编排调度引擎。

![ByteDance Multi-Cluster Evolution](https://github.com/user-attachments/assets/9f1084b2-32c9-4b1e-a6e6-755d440afe9a)

### 演进历程

字节跳动的多集群架构经历了三代演进：

#### 第一代基础架构（2015-2017）

- 核心业务服务云原生化
- TCE 平台建设完成
- 统一公司级 SRE 体系

#### 第二代基础架构（2018-2019）

- 关注集群规模与资源效率
- 2019 年以 KubeFed 为基础引入集群联邦

#### 第三代基础架构（2021-2022+）

- 应用多样化、调度需求精细化
- 2021 年第三代联邦 KubeAdmiral 发布

### KubeAdmiral 核心特性

- **多集群应用管理**: 统一管理跨多个 Kubernetes 集群的应用
- **智能调度**: 基于资源、拓扑、亲和性等策略的智能调度
- **故障转移**: 自动检测集群故障并进行工作负载迁移
- **灵活的联邦策略**: 支持多种资源分发和调度策略

### 参考资料

- **官方博客**: [字节跳动开源 KubeAdmiral：基于 Kubernetes
  的新一代多集群编排调度引擎](https://mp.weixin.qq.com/s/aS18urPF8UB4K2I_9ECbHg)
- **GitHub 仓库**: <https://github.com/kubewharf/kubeadmiral>

## 调度器优化：Gödel

### 背景

在大规模 Kubernetes 集群中，默认调度器往往成为性能瓶颈。
字节跳动开发了 Gödel 调度器来优化大集群的调度性能。

![Gödel Unified Scheduling](https://github.com/user-attachments/assets/bc2c4887-8984-490c-8295-8b82f0603caa)

### 统一调度架构

Gödel 采用统一调度架构，包含以下层次：

#### 平台租户层

- PaaS Platform
- ML Platform
- BigData Platform
- Function as a Service
- Storage Services

#### 云原生应用层

- Deployment
- SolarNG
- L*x
- 等云原生应用

#### 租户接入层

- **vKubernetes**: 虚拟 Kubernetes 集群
- **Yarn on Gödel**: 大数据工作负载接入
- **KubeZoo**: 多租户管理

#### 资源池化层

- **Global Quota**: 全局配额管理
- **Workload Dispatch**: 工作负载分发
- **Resource Dispatch**: 资源调度

#### 单集群调度层

多个单集群并行调度，支持扁平化配额管理（Flat Quota）

### 关键优化

- **高吞吐量**: 支持大规模 Pod 调度
- **资源池化**: 统一管理多集群资源
- **多租户支持**: 支持不同类型工作负载的隔离
- **灵活的配额管理**: 全局配额与集群配额的协调

### 参考资料

- **技术博客**: [字节跳动大规模 K8s
  集群管理实践](https://mp.weixin.qq.com/s/P3-CrOVSSaVAT5tH9m06EA)
- **KubeCon 主题**: <https://sched.co/1i7pp>

## 资源管理：Katalyst

### 背景

Katalyst 是字节跳动开源的 Kubernetes 资源管理系统，
专注于提升大规模集群的资源利用率和应用服务质量。

![Gödel and Katalyst Integration](https://github.com/user-attachments/assets/f8962f4d-4cb7-412c-99bc-08667a9b8dd6)

### 核心能力

- **QoS 感知调度**: 基于服务质量的智能调度
- **资源超售**: 安全的资源超售策略
- **动态资源调整**: 根据实际负载动态调整资源
- **混部优化**: 在线服务与离线任务的混合部署优化

### 架构优势

Katalyst 与 Gödel 调度器配合，形成完整的资源管理解决方案：

- **调度层**: Gödel 负责工作负载的全局调度
- **节点层**: Katalyst 负责节点级别的资源管理和 QoS 保障
- **反馈闭环**: 节点资源状态实时反馈给调度器

![Gödel Federation Architecture](https://github.com/user-attachments/assets/f3f1f392-eef1-4932-8f73-8b0a5d5af335)

### 参考资料

- **GitHub 仓库**: <https://github.com/kubewharf/katalyst-core>
- **KubeCon 演讲**: <https://sched.co/1i7pp>

## 参考资料

### 单集群大规模：KubeBrain

- [KubeBrain 官方博客（微信公众号）](https://mp.weixin.qq.com/s/osJfi_oOfhEmQJNVqKel3Q)
- [KubeBrain GitHub](https://github.com/kubewharf/kubebrain)
- [KubeCon China 2025 演讲视频](https://www.youtube.com/watch?v=MGOa8Nn8_S0&t=1473s)
- [KubeCon China 2025 会议主页](https://sched.co/1i7oo)

### 多集群编排：KubeAdmiral

- [KubeAdmiral 官方博客（微信公众号）](https://mp.weixin.qq.com/s/aS18urPF8UB4K2I_9ECbHg)
- [KubeAdmiral GitHub](https://github.com/kubewharf/kubeadmiral)

### 调度器优化：Gödel

- [字节跳动大规模 K8s
  集群管理实践](https://mp.weixin.qq.com/s/P3-CrOVSSaVAT5tH9m06EA)
- [KubeCon 演讲：Gödel and Katalyst](https://sched.co/1i7pp)

### 资源管理：Katalyst

- [Katalyst GitHub](https://github.com/kubewharf/katalyst-core)
- [KubeCon 演讲：Gödel and Katalyst](https://sched.co/1i7pp)

### 相关文档

- [Large-Scale Kubernetes Clusters](../../kubernetes/large-scale-clusters.md)
- [Scheduling Optimization](../../kubernetes/scheduling-optimization.md)

---

**说明**: 本文档基于字节跳动公开发布的技术博客和 KubeCon
演讲内容整理。具体实现细节请参考官方文档和 GitHub 仓库。
