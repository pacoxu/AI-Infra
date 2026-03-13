---
status: Active
maintainer: pacoxu
date: 2026-03-13
tags: kubernetes, gke, google-cloud, scalability, bayer, case-study
canonical_path: docs/blog/2026-03-13/bayer-gke-15000-nodes_zh.md
source_urls:
  - https://cloud.google.com/blog/products/containers-kubernetes/google-kubernetes-engine-clusters-can-have-up-to-15000-nodes
---

# 【2020】拜耳作物科学以 15,000 节点的 GKE 集群为未来播种

<img width="683" height="332" alt="Bayer Crop Science GKE 15,000 nodes" src="https://github.com/user-attachments/assets/c368f845-08e9-4dbd-8d58-373a6b3f2f51" />

## 背景

2020 年 11 月 17 日，Google Cloud 发布了一篇案例文章，介绍拜耳作物科学
（Bayer Crop Science）如何借助 Google Kubernetes Engine（GKE）把集群规模
提升到 **15,000 个 worker 节点**。这篇文章的重点不只是"规模更大"，
而是解释了为什么客户会撞上 1,000 节点时代的天花板，以及 GKE 需要在哪些
网络与地址分配能力上做出变化，才能让大规模集群真正可用。

原文链接：
<https://cloud.google.com/blog/products/containers-kubernetes/google-kubernetes-engine-clusters-can-have-up-to-15000-nodes>

## 为什么拜耳需要这么大的集群？

拜耳作物科学长期处理农业相关的大规模数据分析与机器学习任务。随着业务扩大，
团队希望把更多工作负载集中到 Kubernetes 平台上统一运行，而不是维护大量
彼此割裂的小集群。

在当时，超大规模集群的价值很直接：

- **减少多集群运维复杂度**：不用再把工作负载人为拆散到多个小集群中；
- **统一调度资源池**：让批处理、数据处理和模型相关任务共用一套平台；
- **适应季节性波峰**：农业业务存在明显的周期性，高峰期需要快速扩容；
- **降低平台心智负担**：开发团队面向同一套 API、同一套安全与治理机制工作。

## 旧瓶颈：为什么 1,000 节点之后就很难继续放大？

文章指出，一个关键限制来自 **基于路由（route-based）的集群网络模型**。
这种模式下，Google Cloud VPC 往往需要为每个节点维护对应路由。节点数量一大，
路由规模、管理复杂度与相关配额就会迅速成为瓶颈。

这意味着：

- 节点数提升时，网络层而不是调度器往往先触顶；
- 集群扩容会受到 VPC 路由上限影响；
- 即使控制平面还能继续工作，底层 IP 与路由模型也可能先失去可操作性。

对拜耳这样的客户来说，如果继续沿用旧模式，就只能把平台拆成多个较小集群，
再在上层自行处理工作负载分发、容量规划与运维隔离，代价很高。

## GKE 是怎么把上限抬到 15,000 节点的？

### 1. 采用 VPC-native 集群

核心变化是使用 **VPC-native** 网络模型。它依赖 Google Cloud 的
**Alias IP**，把 Pod 和节点地址直接纳入 VPC 的 IP 管理体系，而不是继续依赖
大规模的逐节点路由维护。

这样做带来的收益包括：

- **不再为每个节点维护单独路由**，显著降低网络扩容压力；
- **IP 分配更直接**，更适合大规模 Pod 网络；
- **控制面和数据面扩容路径更清晰**，让集群规模不再被旧网络模型卡死。

### 2. 为区域型集群引入自定义子网模式

文章还提到，**Regional Clusters** 新增了 **custom subnets mode**。
这允许用户在每个可用区使用自定义大小的子网，而不是被固定划分方式限制。

这项能力的价值在于：

- 可以按各区容量需求更精细地规划地址空间；
- 避免某些区域 IP 紧张、某些区域 IP 浪费；
- 让超大规模区域型集群更容易落地，而不必为了地址规划牺牲架构设计。

<img width="905" height="547" alt="Regional clusters custom subnet mode" src="https://github.com/user-attachments/assets/c2f6d86a-1283-4be7-969c-6f53ed9cb13c" />

### 3. 让单一集群承载更大的统一资源池

通过上面两项改进，GKE 当时已经能够支持：

- **最多 15,000 个 worker 节点**
- **最多 50,000 个 Pods**

这使得客户可以在单一 GKE 集群内承载更大的工作负载池，而不需要优先从
"怎么拆集群"开始思考。

<img width="865" height="377" alt="GKE supports 15,000 worker nodes and 50,000 pods" src="https://github.com/user-attachments/assets/af9b448d-76b6-4ed5-ae28-c51f69b8a55d" />

## 这对拜耳意味着什么？

对于拜耳作物科学，这不只是一个炫耀规模的里程碑，而是平台能力的跃迁：

- **更少的集群分片**：平台团队可以把注意力放在容量、稳定性和交付效率上；
- **更大的统一调度域**：数据处理与 ML 工作负载更容易共享基础设施；
- **更好的弹性**：面对业务高峰时，不必先跨多个小集群腾挪容量；
- **更低的系统复杂度**：网络、地址和节点规模不再过早成为架构上限。

从案例角度看，GKE 的价值并不只是"托管 Kubernetes"，而是把云网络、IP 规划、
区域高可用和集群管理组合成一套可以真正跑到超大规模的产品能力。

## 这篇 2020 案例放到今天还有什么启发？

这是一篇 2020 年的文章，但它对今天的 AI 基础设施仍然有参考价值。

### 1. 大规模集群首先是网络设计问题

很多团队提到大规模 Kubernetes 时，直觉会先想到调度器、etcd 或控制平面。
但这篇文章提醒我们，**网络寻址与地址规划**往往才是第一个真实瓶颈。

### 2. IP 规划必须前置

如果节点、Pod、区域和未来扩容路径没有在一开始设计清楚，后续往往只能靠迁移、
拆集群或者重做网络架构来补救，成本远高于前期规划。

### 3. 托管平台的价值在规模上会被放大

当集群规模进入万节点量级后，客户真正购买的不只是控制平面托管，
而是云厂商在网络、配额、地址管理和产品集成上的整体工程能力。

<img width="1003" height="284" alt="Why this matters for large-scale clusters" src="https://github.com/user-attachments/assets/71e42d87-bde7-4649-ab82-fb7d0da67cc4" />

## 总结

拜耳作物科学的这篇案例，本质上展示了一个重要转折点：
**Kubernetes 的大规模能力，不只是把控制平面调得更强，而是要同时解决网络、
地址空间和区域部署模型的问题。**

对今天关注 AI 基础设施、训练平台和超大规模推理平台的工程师来说，这篇 2020 年的
案例依然值得重读。它让我们看到，很多"现代"大规模平台问题，其实早在五年前就已经
出现，只是当时的关键词不是 AI，而是如何让云上的 Kubernetes 真正跨过万节点门槛。

## 参考

- Google Cloud Blog:
  [Google Kubernetes Engine clusters can have up to 15,000 nodes](https://cloud.google.com/blog/products/containers-kubernetes/google-kubernetes-engine-clusters-can-have-up-to-15000-nodes)
