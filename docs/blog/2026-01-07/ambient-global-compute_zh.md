---
status: Active
maintainer: pacoxu
last_updated: 2026-01-07
tags: kubernetes, ai-infrastructure, kubecon, ambient-compute, gpu, kueue
---

# Ambient Global Compute：用 Kubernetes 编排非弹性云

本文基于 Google Jago Macleod 在 KubeCon 上的演讲《Ambient Global Compute:
Orchestrating the Non-Elastic Cloud With Kubernetes》，探讨在 AI
时代如何应对资源稀缺和碎片化，以及如何通过 Kubernetes
实现全球资源的高效调度和利用。

**视频链接：** https://www.youtube.com/watch?v=r-UBNuWkUG8

**注意：** 部分内容由 AI 辅助生成，使用前请仔细验证。

## 目录

- [基础设施摆动](#基础设施摆动)
- [云计算的黄金时代](#云计算的黄金时代)
- [新现实：资源约束时代](#新现实资源约束时代)
  - [硬件碎片化](#硬件碎片化)
  - [区域扩展](#区域扩展)
  - [GPU 急性短缺](#gpu-急性短缺)
  - [CapEx 的回归](#capex-的回归)
- [运营理念的反转](#运营理念的反转)
- [Ambient Compute 四大支柱](#ambient-compute-四大支柱)
  - [工作负载编排](#工作负载编排)
  - [Kueue 队列管理](#kueue-队列管理)
  - [优先级感知堆栈](#优先级感知堆栈)
  - [全球调度能力](#全球调度能力)
- [实践模式](#实践模式)
  - [模式 A：全球批处理计算机](#模式-a全球批处理计算机)
  - [模式 B：固定硬件上的弹性平台](#模式-b固定硬件上的弹性平台)
- [总结](#总结)
- [参考资料](#参考资料)

## 基础设施摆动

<img src="https://github.com/user-attachments/assets/c11d0ae2-8898-4ad0-ae0c-e63af75954ad"
width="800" alt="基础设施摆动">

云计算基础设施的演进经历了几个阶段的摆动：

- **2000-2008：物理机托管时代**
  - 物理约束限制
  - 利用率仅 15%
  - 资源浪费严重

- **2008-2015：虚拟化时代**
  - 抽象化物理约束
  - Bin-Packing（装箱）模式
  - 提升资源利用率

- **2015-2023：弹性云的黄金时代**
  - 无限的运营支出（OpEx）模式
  - 按需扩展，随用随付
  - 云计算的巅峰时期

- **今天：非弹性云时代**
  - 回归资本支出（CapEx）模式
  - 资源稀缺性驱动
  - 容量约束成为新常态

## 云计算的黄金时代

<img src="https://github.com/user-attachments/assets/6a54b3e9-39ef-4440-a912-c58a4f095cfa"
width="800" alt="黄金时代">

在云计算的"黄金时代"，容量被认为是无限的。当提交作业时，云服务商会立即提供新的虚拟机来并行处理。

### 黄金时代的三大特征

1. **水平扩展：** 作业可以同时运行（Jobs run simultaneously）
2. **零等待时间：** 资源按需即时出现（Resources appear 'instantly' on-demand）
3. **OpEx 模型：** 仅在作业运行时付费（Pay only while the job runs）

这种模式下，工作负载通过无限云 API 提交，系统会自动分配 VM1、VM2、VM3、VM4
等多个虚拟机来处理请求。

## 新现实：资源约束时代

<img src="https://github.com/user-attachments/assets/86adec8c-c84f-473e-b890-01ed4dcf719a"
width="800" alt="资源约束时代">

然而，AI 时代的到来彻底改变了这一切，我们正在经历三个重大挑战：

### 硬件碎片化

<img src="https://github.com/user-attachments/assets/f4894cb4-161a-4dfd-ac71-af2a0eb6971c"
width="800" alt="硬件碎片化">

**统一性的终结**

简单的 x86 虚拟机不再是统一的、无处不在的硬件选择。
现在我们必须管理一个由不兼容架构组成的多样化资源池：

- **x86 标准型**（30%）：传统的服务器架构
- **ARM 定制型**（30%）：性价比更优，但需要多架构容器构建
- **NVIDIA GPU**（20%）：AI 训练和推理的主力
- **Google TPU**（10%）：针对特定工作负载优化
- **专用硬件**（10%）：高内存、存储优化、TPU v4 vs v5e 等

*注：上述比例为示意性数据，用于说明硬件类型的多样性，并非实际市场统计数据。*

### 区域扩展

<img src="https://github.com/user-attachments/assets/6699a58b-74a3-4458-bb3b-09e53d687f70"
width="800" alt="区域扩展">

**统一性的终结（续）**

云计算正在逐渐区域化隔离，因此您所需的机器类型可能在您需要的区域中不可用。

**资源选项爆炸式增长：**

```text
# 机器类型 × # 区域 = 总选项数量
```

根据图表显示：

- **AWS**：约 850 种机器类型组合
- **GCP**：约 450 种机器类型组合

从 2010 年到 2025 年，总选项数量呈指数级增长，给资源调度带来了巨大挑战。

### GPU 急性短缺

<img src="https://github.com/user-attachments/assets/a5abe95d-bdf6-4bcd-895b-c64bb9c5ea97"
width="800" alt="GPU 急性短缺">

**驱动因素 #2：急性稀缺**

AI 热潮打破了供应链。您不能简单地申请一个 H100 GPU。

**容量不再是公共资源，而是私有资产。**

H100 等高端 GPU 的短缺使得容量规划从公共云的按需模式，
转变为需要提前预订和长期承诺的私有资产管理模式。

### CapEx 的回归

<img src="https://github.com/user-attachments/assets/cc2f30fc-34eb-4adf-97d2-9eea787126de"
width="800" alt="CapEx 回归">

**驱动因素 #3：CapEx 的回归**

为了应对资源短缺，企业开始：

- **预付费购买容量**：提前支付大量资本支出
- **预留实例和承诺使用折扣**：锁定长期容量
- **私有云和本地部署**：自建 AI 基础设施

这意味着从"按需付费"的 OpEx 模式回归到"先买后用"的 CapEx 模式。

## 运营理念的反转

<img src="https://github.com/user-attachments/assets/be88085c-171e-4007-9ecf-021c2da9bd7c"
width="800" alt="运营理念反转">

从弹性云到非弹性云，运营理念发生了根本性的反转：

### 过去：按需支付最少

**旧模式（OpEx）：**

- 为您当前需要的资源支付最少的费用
- 用完即释放，不保留空闲资源
- 关注成本优化，按使用量付费

### 现在：最大化已有资源的利用率

**新模式（CapEx）：**

- 最大化您已经支付的资源的利用率
- 资源已经购买，必须充分使用
- 关注利用率优化，避免浪费

**这种理念反转要求我们重新思考资源调度、工作负载编排和容量规划策略。**

## Ambient Compute 四大支柱

<img src="https://github.com/user-attachments/assets/f96bafd2-da22-418d-af85-53f55da8f0c2"
width="800" alt="Ambient Compute 四大支柱">

为了应对非弹性云的挑战，Google 提出了 Ambient Compute 的概念，
它建立在四大支柱之上：

1. **工作负载编排（Workload Orchestration）**
2. **队列管理（Queue Management）**
3. **优先级感知（Priority Awareness）**
4. **全球调度（Global Dispatch）**

### 工作负载编排

<img src="https://github.com/user-attachments/assets/56caf741-c95e-48a5-a3a2-39928c42d23a"
width="800" alt="工作负载编排">

<img src="https://github.com/user-attachments/assets/a452fc2f-8ce7-48b6-9e7c-28f2f220023f"
width="800" alt="工作负载编排详情">

<img src="https://github.com/user-attachments/assets/1fb9afbc-f845-45aa-9b4a-4a3b40fcd30b"
width="800" alt="工作负载编排架构">

**核心理念：** 将复杂的分布式训练任务抽象为统一的工作负载对象。

**主要项目：**

- **JobSet**：管理多个相关 Job 的集合
- **Workload API**：统一的工作负载抽象层
- **LWS（LeaderWorkerSet）**：管理主从模式的分布式训练
- **Training Operators**：特定框架的训练编排（PyTorch、TensorFlow 等）

**解决的问题：**

- 简化分布式训练的部署和管理
- 统一不同训练框架的接口
- 提供统一的生命周期管理

### Kueue 队列管理

<img src="https://github.com/user-attachments/assets/54fac8c5-d488-43ab-81f2-935baa556c3e"
width="800" alt="Kueue">

**Kueue 是 Kubernetes 的作业排队和资源管理系统。**

**核心功能：**

1. **队列管理**
   - 按团队、项目或优先级分组作业
   - 公平共享和资源配额管理
   - 防止资源抢占和饥饿

2. **资源编排**
   - 等待资源可用时挂起作业
   - 资源就绪后自动调度
   - 支持资源借用和回收

3. **批处理优化**
   - Gang Scheduling 支持
   - 作业依赖管理
   - 优先级和抢占策略

**典型使用场景：**

- AI 训练作业的批处理调度
- 多租户环境的资源隔离
- 资源配额和成本控制

### 优先级感知堆栈

<img src="https://github.com/user-attachments/assets/1793ec18-8b98-413c-9e4f-83f0f07eb37b"
width="800" alt="利用率与延迟冲突">

**利用率与延迟的冲突**

在资源约束的环境中，我们面临一个根本性的权衡：

- **高利用率**：让集群尽可能满载，避免浪费
- **低延迟**：保持资源余量，确保新作业能快速启动

传统的静态分配无法同时满足两者。

<img src="https://github.com/user-attachments/assets/d62c391b-616f-4d68-85bc-342724587a8c"
width="800" alt="优先级感知堆栈">

**解决方案：优先级感知的多层调度**

通过优先级机制，可以实现：

1. **高优先级作业**
   - 低延迟启动
   - 可以抢占低优先级作业
   - 保证服务质量（SLO）

2. **中优先级作业**
   - 正常的生产工作负载
   - 平衡延迟和利用率

3. **低优先级作业**
   - 填充空闲容量
   - 可被抢占但提升整体利用率
   - 批处理、测试、实验性工作负载

**实现方式：**

- Kubernetes Priority Classes
- Kueue 的多层队列
- 抢占策略和回填算法

### 全球调度能力

<img src="https://github.com/user-attachments/assets/3408c734-ab6f-4b30-9c67-5fd31c555701"
width="800" alt="全球搁浅容量">

**全球搁浅容量问题**

在多区域、多集群的环境中，容量可能分散在不同位置：

- 区域 A：GPU 闲置，但没有训练作业
- 区域 B：有大量训练作业，但 GPU 不足
- 区域 C：有部分可用容量，但不够完整的作业运行

这导致全局资源浪费，即使总容量足够，也无法高效调度。

<img src="https://github.com/user-attachments/assets/4c5ae96f-4551-4dd1-bae6-3374d4cca055"
width="800" alt="MultiKueue 全球调度">

**解决方案：MultiKueue 全球调度**

MultiKueue 实现跨集群的统一调度：

**核心能力：**

1. **全局资源视图**
   - 聚合多个集群的资源状态
   - 统一的作业队列
   - 跨区域的容量感知

2. **智能作业分发**
   - 根据资源可用性选择最优集群
   - 考虑延迟、成本、策略等因素
   - 动态调整分发策略

3. **故障转移和弹性**
   - 集群故障时自动重新调度
   - 跨区域的负载均衡
   - 避免单点故障

**使用场景：**

- 跨区域的训练作业调度
- 多云环境的资源统一管理
- 灾难恢复和高可用性

## 实践模式

基于 Ambient Compute 的四大支柱，演讲者提出了两种实践模式：

### 模式 A：全球批处理计算机

<img src="https://github.com/user-attachments/assets/36dce747-ab0c-4aa3-bfce-598ecb8db483"
width="800" alt="模式 A：全球批处理计算机">

**适用场景：**

- 大规模 AI 训练任务
- 非实时的批处理工作负载
- 可以容忍一定延迟的任务

**架构特点：**

- 使用 MultiKueue 实现全球统一调度
- 作业可以在任意有资源的区域执行
- 最大化全球资源利用率

**实现要点：**

1. **统一的作业提交接口**
   - 用户提交作业到中央队列
   - 系统自动选择最优执行位置

2. **数据就近原则**
   - 考虑数据传输成本
   - 优先选择数据所在区域
   - 必要时进行数据复制

3. **成本优化**
   - 优先使用预留容量
   - 利用区域间的价格差异
   - 避免跨区域的高额流量费用

### 模式 B：固定硬件上的弹性平台

<img src="https://github.com/user-attachments/assets/c71992a4-891d-4e6c-a17c-7b39dcb818b5"
width="800" alt="模式 B：固定硬件上的弹性平台">

<img src="https://github.com/user-attachments/assets/57227242-f585-4c11-b1d7-d2bd0ee090b0"
width="800" alt="模式 B 详细架构">

**适用场景：**

- 私有云或本地部署
- 已购买的固定容量
- 需要同时支持在线和离线工作负载

**架构特点：**

- 固定的硬件资源池
- 通过优先级实现弹性
- 在线服务和批处理混合部署

**实现要点：**

1. **分层资源管理**
   - **在线服务（高优先级）**：保证低延迟和 SLO
   - **批处理任务（低优先级）**：填充空闲资源
   - **中间层（中优先级）**：平衡两者

2. **智能抢占机制**
   - 低优先级任务使用空闲资源
   - 高优先级任务到来时自动抢占
   - checkpoint 和恢复机制减少浪费

3. **利用率最大化**
   - 通过低优先级任务填充碎片时间
   - 在线服务的波谷期运行批处理
   - 整体利用率可提升至 80%+ (vs 传统 40-60%，具体取决于工作负载特征)

**关键技术：**

- Kubernetes Priority and Preemption
- Kueue 的多队列管理
- Workload API 的统一抽象

## 总结

<img src="https://github.com/user-attachments/assets/63cf9481-2070-478c-802e-d99e15c7133b"
width="800" alt="总结">

**云计算并未回到原点（但确实需要一些新的模式）**

Kubernetes 现在成为了管理新现实的分布式操作系统，这个新现实包括：

- **碎片化（Fragmentation）**：多样化的硬件架构
- **稀缺性（Scarcity）**：资源供应紧张
- **强制预留容量（Mandatory Reserved Capacity）**：CapEx 模式回归

**Ambient Global Compute 的核心价值：**

1. **统一编排**：通过 Workload API 和 JobSet 简化复杂工作负载
2. **智能排队**：Kueue 提供公平、高效的资源分配
3. **优先级管理**：在固定容量上实现弹性
4. **全球视野**：MultiKueue 打破区域限制，统一全球资源

**如果您有其他有效的模式，欢迎分享！**

## 参考资料

- **KubeCon 演讲视频：** https://www.youtube.com/watch?v=r-UBNuWkUG8
- **Kueue 项目：** https://github.com/kubernetes-sigs/kueue
- **JobSet 项目：** https://github.com/kubernetes-sigs/jobset
- **Workload API KEP：** https://github.com/kubernetes/enhancements/tree/master/keps/sig-scheduling/4817-workload-api
- **MultiKueue 文档：** https://kueue.sigs.k8s.io/docs/concepts/multikueue/
