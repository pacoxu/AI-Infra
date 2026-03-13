---
status: Active
maintainer: pacoxu
last_updated: 2025-12-17
tags: kubernetes, dranet, dra, network-driver, ai-infrastructure, kubecon
---

# 社区驱动的 Kubernetes 网络驱动演进 & DRANET 介绍

本文基于 KubeCon NA 2025 主题演讲和论文《The Kubernetes Network Driver
Model: A Composable Architecture for High-Performance Networking》，
介绍 Kubernetes 社区如何通过 DRANET 项目重新定义网络驱动模型，
为 AI/ML 时代的高性能网络需求提供创新解决方案。

**注意：** 部分内容由 AI 辅助生成，使用前请仔细验证。

## 目录

- [DRANET 概述](#dranet-概述)
- [新兴生态系统](#新兴生态系统)
- [DRA：通用语言](#dra通用语言)
- [理念演进历程](#理念演进历程)
- [Kubernetes 网络驱动的挑战](#kubernetes-网络驱动的挑战)
- [DRANET 架构设计](#dranet-架构设计)
- [性能测试结果](#性能测试结果)
- [项目资源](#项目资源)
- [参考资料](#参考资料)

## DRANET 概述

<img src="https://github.com/user-attachments/assets/b445686d-a595-4c15-b632-cfcff5398695"
width="800" alt="DRANET 概述">

DRANET (Dynamic Resource Allocation Network) 是一个基于 Kubernetes DRA
(Dynamic Resource Allocation) 的网络驱动项目，旨在解决传统 Kubernetes
网络模型的局限性，为 AI/ML 时代提供高性能、拓扑感知的网络解决方案。

### 三大核心特性

1. **基于 DRA 的 Kubernetes 网络驱动**
   - 利用 DRA 框架实现灵活的网络资源分配
   - 提供声明式的网络资源申请和管理
   - 支持复杂的网络拓扑和资源组合

2. **拓扑感知的网络资源**
   - 感知 NUMA、PCIe、NVLink 等硬件拓扑
   - 自动协调 GPU + NIC 在相同 PCIe fabric 上的分配
   - 优化 RDMA、GPU-Direct 等高性能网络场景

3. **为 AI/ML 时代增强网络性能**
   - 支持高吞吐量、低延迟的网络需求
   - 优化分布式训练和推理的网络性能
   - 提供硬件加速和高效的资源利用

## 新兴生态系统

<img src="https://github.com/user-attachments/assets/fe7c3cf4-867e-4fac-96ed-9ce10db7a306"
width="800" alt="新兴生态系统">

随着 AI/ML 工作负载的快速增长，Kubernetes 网络驱动面临新的挑战和机遇。
三大生态系统正在推动网络技术的创新：

### AI/ML 生态系统

- **需求特点**：高性能驱动、最大吞吐量、低延迟、高效硬件利用
- **关键技术**：GPU-Direct RDMA、NVLink、InfiniBand
- **典型工作负载**：分布式训练、大规模推理、模型并行

### HPC (高性能计算) 生态系统

- **需求特点**：紧密的节点同步、超低延迟、高精度计算、大规模互联
- **关键技术**：MPI、RDMA、DPDK、SR-IOV、GPU-Direct
- **典型工作负载**：科学计算、仿真模拟、大规模并行任务

### Telco (电信) 生态系统

- **需求特点**：5G/6G 网络支持、多宿主、网络切片、QoS、硬件加速
- **关键技术**：MPI、RDMA、DPDK、SR-IOV
- **典型工作负载**：网络功能虚拟化 (NFV)、边缘计算、网络切片

这些生态系统推动了底层网络技术的融合：**MPI、RDMA、DPDK、SR-IOV、
GPU-DIRECT** 成为共同的技术基础。

## DRA：通用语言

<img src="https://github.com/user-attachments/assets/20ec3cbe-09c8-423f-be2b-96030a7ebffe"
width="800" alt="DRA 通用语言">

Dynamic Resource Allocation (DRA) 作为 Kubernetes
的资源分配框架，为网络驱动提供了统一的抽象层：

### DRA 核心概念

- **DRA Network**: 网络驱动基于 DRA 实现，支持灵活的网络资源分配
- **DRA CPU/GPU**: 统一的资源管理接口，协调计算和网络资源
- **Kubelet**: 通过 DRA 插件与底层硬件交互
- **节点级资源管理**: AI/ML Pods、Telco Pods 通过统一接口访问网络资源

### 拓扑感知调度

DRA 使 Kubernetes 能够感知硬件拓扑，实现智能的资源分配：

- **GPU + NIC 协调**: 确保 GPU 和网络接口在相同 PCIe 根上
- **NUMA 亲和性**: 优化内存访问延迟
- **NVLink 域**: 协调多 GPU 通信
- **RDMA 设备**: 高效的 GPU-Direct RDMA 通信

## 理念演进历程

<img src="https://github.com/user-attachments/assets/fe83b962-b23e-4626-a20a-29e8548b7ff5"
width="800" alt="理念演进历程">

Kubernetes 网络驱动的演进经历了多个重要里程碑：

- **2015**: CNI Spec — 定义容器网络接口标准
- **2017**: Device Plugin — 支持设备（如 GPU）的插件机制
- **2017**: Network Plumbing Working Group — 社区开始关注网络管道问题
- **2022**: Multi-Network Subproject — 多网络支持成为独立子项目
- **2023**: KNI KEP — Kubernetes Network Interface 增强提案
- **2024**: DRA — Dynamic Resource Allocation 框架成熟
- **2025**: Kubernetes Network Drivers — DRANET 引入基于 DRA 的网络驱动

这一演进过程体现了社区对网络性能和灵活性需求的不断响应。

## Kubernetes 网络驱动的挑战

<img src="https://github.com/user-attachments/assets/bcde9255-f11a-4c2a-92f6-6f39818d8a5f"
width="800" alt="Kubernetes 网络驱动的挑战">

### 问题：拓扑抽奖 (The Topology Lottery)

传统的 Kubernetes 网络模型存在严重的性能瓶颈：

- **拓扑盲目**: Kubernetes 网络调度不感知硬件拓扑
- **性能瓶颈**: 导致严重的性能下降和不可预测的结果
- **资源浪费**: 无法充分利用高性能网络硬件

### 解决方案：拓扑感知调度

DRANET 通过两个核心机制解决拓扑问题：

1. **DRA: 表达式化的拓扑感知资源申请**
   - 使用 CEL (Common Expression Language) 表达复杂的拓扑约束
   - 声明式描述 GPU、NIC、存储等资源的拓扑关系
   - 支持跨设备类型的协调分配

2. **NRI: 可组合的运行时钩子替代脆弱的插件链**
   - Node Resource Interface 提供标准化的运行时扩展接口
   - 避免传统插件链的脆弱性和维护复杂性
   - 支持灵活的网络配置和设备绑定

### 结果：可预测的最大性能

性能测试显示显著提升：

- **NCCL All Gather 带宽提升**: 最高提升 59.6%
- **NCCL All Reduce 带宽提升**: 最高提升 58.1%
- **消除性能方差**: 通过解决"拓扑抽奖"问题，实现稳定的性能表现

*性能数据来源：论文《The Kubernetes Network Driver Model: A Composable
Architecture for High-Performance Networking》，IEEE 50th Conference on
Local Computer Networks (LCN) 2025*

## DRANET 架构设计

根据论文描述，DRANET 采用可组合的架构设计，将网络配置分解为独立的模块：

### 核心架构组件

1. **ResourceClaim API**
   - 声明式的网络资源申请接口
   - 支持复杂的拓扑约束和设备组合
   - 与 Kubernetes 调度器深度集成

2. **DRA 网络驱动**
   - 实现 DRA 驱动接口的网络资源管理器
   - 处理资源分配、拓扑匹配、设备绑定
   - 支持多种网络技术：SR-IOV、DPDK、RDMA

3. **NRI 运行时钩子**
   - 在容器启动时动态配置网络
   - 支持设备注入、环境变量设置、命名空间配置
   - 替代传统的 CNI 插件链

4. **拓扑管理器**
   - 维护节点的硬件拓扑信息
   - 协调多种资源类型的分配决策
   - 优化跨设备的性能

### 可组合性优势

DRANET 的可组合架构带来多个优势：

- **模块化**: 各组件独立开发和维护
- **灵活性**: 支持多种网络技术栈的组合
- **可扩展性**: 易于添加新的网络功能和设备类型
- **稳定性**: 避免复杂插件链带来的维护问题

## 性能测试结果

论文中详细描述了 DRANET 在 NCCL (NVIDIA Collective Communications
Library) 基准测试中的性能表现：

### 测试环境

- **集群规模**: 多节点 Kubernetes 集群
- **GPU 配置**: NVIDIA A100 GPU with NVLink
- **网络配置**: RDMA over Converged Ethernet (RoCE)
- **基准测试**: NCCL All-Reduce、All-Gather 等集合通信操作

### All-Reduce 性能

在 All-Reduce 操作中，DRANET 通过拓扑感知调度实现了显著的性能提升：

- **未对齐场景**: 传统调度方式下，性能随数据大小增长缓慢
- **对齐场景**: DRANET 确保 GPU 和 NIC 在相同拓扑域，性能提升高达 **58.1%**
- **性能稳定性**: 消除了因拓扑不匹配导致的性能波动

### All-Gather 性能

All-Gather 操作同样受益于拓扑感知调度：

- **带宽提升**: 最高提升 **59.6%**
- **延迟降低**: 通过优化的 PCIe 和 NVLink 路径，减少通信延迟
- **规模化**: 在大规模集群中保持稳定的性能表现

### 性能提升的关键因素

1. **GPU-Direct RDMA**: GPU 直接通过 RDMA 通信，绕过 CPU
2. **PCIe 拓扑优化**: GPU 和 NIC 在相同 PCIe 根上，减少总线竞争
3. **NVLink 协调**: 多 GPU 通信通过 NVLink 高速互联
4. **NUMA 亲和性**: 减少跨 NUMA 节点的内存访问开销

这些性能提升对于大规模分布式训练和推理场景至关重要，
能够显著缩短模型训练时间和提高推理吞吐量。

## 项目资源

### GitHub 仓库

DRANET 项目已捐赠给 Kubernetes 社区：

- 原始仓库：<a href="https://github.com/google/dranet">google/dranet</a>
- 现仓库：<a href="https://github.com/kubernetes-sigs/dranet">kubernetes-sigs/dranet</a>

### 演示项目

KubeCon NA 2025 演示代码：

- Demo 仓库：<a href="https://github.com/LionelJouin/kubecon-na-2025-knd">LionelJouin/kubecon-na-2025-knd</a>

### KubeCon NA 2025 主题演讲

- **演讲标题**: The Community-Driven Evolution of the Kubernetes Network
  Driver
- **演讲者**: Lionel Jouin (Ericsson) & Antonio Ojea (Google)
- **视频**: <a href="https://www.youtube.com/watch?v=1iFYEWx2zC8">YouTube 链接</a>
- **会议页面**:
  <a href="https://sched.co/27FYh">KubeCon NA 2025 Schedule</a>
- **幻灯片**: <a
  href="https://github.com/user-attachments/files/24203102/Kubecon.NA.2025.-.Keynote_.The.Community-Driven.Evolution.of.the.Kubernetes.Network.Driver.pdf">PDF
  下载</a>

<img src="https://github.com/user-attachments/assets/102123d8-7eb3-470d-9075-e99c75e93f67"
width="800" alt="KubeCon NA 2025 演讲">

### 研究论文

- **论文标题**: The Kubernetes Network Driver Model: A Composable Architecture
  for High-Performance Networking
- **作者**: Antonio Ojea (Google) 等
- **会议**: IEEE 50th Conference on Local Computer Networks (LCN) 2025
- **arXiv**: <a href="https://arxiv.org/abs/2506.23628">arXiv:2506.23628</a>
- **PDF**: <a href="https://github.com/user-attachments/files/24203103/2506.23628v1.pdf">论文下载</a>

论文详细描述了 DRANET 的设计理念、架构实现和性能评估，
是理解该项目技术细节的重要参考资料。

<img src="https://github.com/user-attachments/assets/5253107d-41fe-4038-a7aa-fc2fdb783c0c"
width="600" alt="论文图表 1">

<img src="https://github.com/user-attachments/assets/df955da0-ae8d-4eb9-9fb9-351a83819f8b"
width="600" alt="论文图表 2">

<img src="https://github.com/user-attachments/assets/37dbfe72-58a7-4fd4-9559-60a5f619b813"
width="600" alt="论文图表 3">

<img src="https://github.com/user-attachments/assets/5570e25e-d731-42e9-89a7-9149c9ce02ef"
width="600" alt="论文图表 4">

### 官方网站

- **DRANET 官网**: <a href="https://dranet.dev">dranet.dev</a>

### Twitter/X 讨论

- pacoxu 的推文：<a href="https://x.com/xu_paco/status/1989215857046876310">Twitter 链接</a>

## 参考资料

### Kubernetes DRA 相关

- [Dynamic Resource Allocation 文档](../kubernetes/dra.md)
- [DRA 性能测试](../kubernetes/dra-performance-testing.md)
- [拓扑感知调度](../kubernetes/scheduling-optimization.md)

### CNCF 和 Kubernetes 社区

- <a href="https://github.com/kubernetes/enhancements/issues/4381">KEP-4381:
  DRA Structured Parameters</a>
- <a href="https://github.com/kubernetes/dynamic-resource-allocation">Kubernetes
  Dynamic Resource Allocation</a>
- <a href="https://github.com/kubernetes-sigs/dra-example-driver">DRA Example
  Driver</a>

### NRI (Node Resource Interface)

- <a href="https://github.com/containerd/nri">containerd/nri</a>
- [Node Resource Interface 文档](../kubernetes/nri.md)

### NCCL 和高性能网络

- <a href="https://github.com/NVIDIA/nccl">NVIDIA NCCL</a>
- <a href="https://developer.nvidia.com/gpudirect">NVIDIA GPU-Direct</a>
- <a href="https://www.nvidia.com/en-us/data-center/nvlink/">NVIDIA
  NVLink</a>

### 相关博客

- [Gang Scheduling](../blog/2025-11-25/gang-scheduling_zh.md)
- [Topology-Aware Scheduling](../blog/2025-11-25/topology-aware-scheduling_zh.md)
- [GKE 65K Nodes](../blog/2025-12-08/gke-65k-nodes_zh.md)

## 总结

DRANET 代表了 Kubernetes 网络驱动的重要演进，通过 DRA 和 NRI
的组合，为 AI/ML、HPC 和 Telco 工作负载提供了高性能、
拓扑感知的网络解决方案。该项目体现了 Kubernetes 社区的创新能力，
以及对不断变化的工作负载需求的快速响应。

随着 AI/ML 工作负载的持续增长，DRANET 将在支持大规模分布式训练、
高性能推理和边缘计算场景中发挥越来越重要的作用。社区驱动的开发模式确保了
DRANET 能够持续演进，满足未来的技术挑战。

---

**致谢**: 感谢 Lionel Jouin、Antonio Ojea 及所有 DRANET 项目贡献者。
感谢 Kubernetes 社区和 CNCF 对该项目的支持。
