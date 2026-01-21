---
status: Active
maintainer: pacoxu
last_updated: 2026-01-21
tags: supernode, superpod, hypernode, kubernetes, ai-infrastructure, lws
canonical_path: docs/kubernetes/supernode.md
---

# SuperNode：AI 基础设施的超节点架构深入分析

<img
src="https://github.com/user-attachments/assets/10bcc914-81cf-49e8-bcde-86fdb87098ee"
alt="Huawei Scale-Up System Architecture" width="800"/>

## 概述

**SuperNode**（也称 *SuperPod* / *HyperNode*）指将多个加速器节点通过超高速
互连组成的"超大节点"，使其在带宽与延迟特性上接近"单一机器"的体验。它将多台
GPU/AI 服务器融合为一个高度协同的计算单元，拥有远超单机的算力与内存容量。

## 1. SuperNode 概念及能解决的问题

典型 SuperNode 实例包括：

- **NVIDIA DGX NVL72 / GB200** - NVIDIA 的旗舰级超节点方案
- **华为 CloudMatrix 384** - 支持 384 卡规模的超大规模系统
- **阿里云盘古 AI Infra 2.0（128 cards）** - 阿里云的 128 卡超节点方案
- **浪潮 ScaleX640** - 浪潮信息的超大规模 AI 计算平台

<img
src="https://github.com/user-attachments/assets/278593bf-0cd7-4822-bf89-851551d155be"
alt="NVIDIA Vera Rubin NVL72" width="800"/>

*NVIDIA Vera Rubin NVL72 Compute Tray - 模块化 AI 工厂计算引擎*

SuperNode 试图解决的问题主要包括：

### 1.1 模型规模与显存天花板

- 百亿 / 万亿参数模型已无法由单机承载
- SuperNode 提供"跨节点的一体化显存池"，允许模型切片后视为"单节点模型"
- 训练和推理不再被单机显存上限卡死

### 1.2 多节点通信瓶颈

- 传统集群在大规模并行时，通信延迟与带宽成为瓶颈
- SuperNode 通过 NVLink、NVSwitch、光互联、RDMA Fabric 构建"近内存级"通信
- 目标是：**跨节点通信 ≈ 单机 PCIe/NVLink 级别体验**

### 1.3 调度与一致性问题

- 多 Pod / 多节点并行启动困难
- Kubernetes
  <a href="https://github.com/kubernetes-sigs/lws">`LeaderWorkerSet (LWS)`</a>
  将一组 Pod 抽象为"一个逻辑工作单元"
- 支持真正的 *Gang Scheduling*：
  - 要么全部就绪
  - 要么整体失败
- 适配多节点推理与多维并行训练

相关链接：

- [Kubernetes LeaderWorkerSet Issue
  #620](https://github.com/kubernetes-sigs/lws/issues/620)
- [Scaling your LLM inference workloads: multi-node deployment with
  TensorRT-LLM and Triton on Amazon
  EKS](https://aws.amazon.com/cn/blogs/hpc/scaling-your-llm-inference-workloads-multi-node-deployment-with-tensorrt-llm-and-triton-on-amazon-eks/)

### 1.4 推理侧的延迟与并发瓶颈

- 大模型推理需要：
  - 模型跨节点切片
  - KV Cache 跨 GPU 协作
- SuperNode 提供：
  - 足够低延迟的激活与 KV 交换
  - 大模型"实时可用"的硬件基础

配合 vLLM / SGLang：

| 框架    | 强项                             | 与 SuperNode 的协同点               |
| ------- | -------------------------------- | ----------------------------------- |
| vLLM    | 单轮高并发吞吐、PagedAttention   | 多 GPU 张量并行 + 高效 KV 管理      |
| SGLang  | 多轮对话、前缀复用、结构化生成   | RadixAttention 跨节点缓存复用       |

SuperNode + 先进 Runtime = **极限吞吐 + 可控延迟**

---

## 2. SuperNode 的局限与不可解场景

SuperNode 不是"银弹"，其边界主要体现在：

### 2.1 算法层不可并行

- 严格串行 / 强同步算法
- Amdahl 定律主导的任务
- GPU 数量增加 ≠ 性能线性增长

### 2.2 能效与成本

- 以规模换性能
- 例如 CloudMatrix 384：
  - 功耗 ≈ NVL72 的 4 倍
  - 能效反而更低
- 对能源敏感场景不友好

### 2.3 低负载与长尾场景

- 请求稀疏
- 模型规模小
- 长期无法满载

→ 超节点将导致"算力闲置 + 单位成本升高"

### 2.4 工程复杂度极高

- 网络拓扑
- 散热与供电
- 存储带宽
- 大规模调度稳定性

没有 HPC 级别工程能力，SuperNode 很可能：

- 部署失败
- 运行不稳定
- 反而劣于普通集群

---

## 3. 训练 vs 推理中的不同角色

### 3.1 在训练中

- 目标：**线性扩展 + 缩短 Time-to-Model**
- 关键价值：
  - 张量并行 / Pipeline 并行 / MoE 并行
  - 高频梯度同步
  - 显存统一编址

效果：

- 百亿 / 万亿参数模型成为"工程可行"
- 训练周期从"月级"降到"周级"

### 3.2 在推理中

- 目标：**让"超大模型"变成"在线可用服务"**
- 关键价值：
  - 跨节点模型切片
  - KV Cache 高速交换
  - 支撑实时响应

配合 vLLM / SGLang：

- vLLM：单模型高并发
- SGLang：多轮长上下文 + 结构化生成

SuperNode 让"405B 模型实时推理"成为可能。

---

## 4. SuperNode 是否更具性价比？

结论：

> 在**高负载、长期运行、大模型场景**下，SuperNode 具备更高 TCO 优势。

原因：

### 4.1 更高单位吞吐

- 同样算力，完成更多请求
- 等价于"减少 GPU 数量"

### 4.2 模块化硬件设计

- GPU Tray、Switch Tray、Power 模块解耦
- 局部升级，避免整柜报废
- 降低生命周期成本

### 4.3 集中化供电与散热

- 液冷 + 母线
- PUE 可达 1.04–1.07
- 长期电力成本显著下降

### 4.4 网络与存储摊薄

- Fabric 一次构建，支持百卡规模
- 避免传统多层交换机级联成本

前提：

> 必须"持续满载"，否则性价比优势消失。

---

## 5. 哪些场景让 SuperNode 更有生命力？

### 5.1 前沿大模型研发

- 万亿参数
- 多模态基础模型
- RL / Agent 模拟

### 5.2 云端大模型服务

- 高并发 API
- 实时交互
- 企业级 SLA

### 5.3 芯片受限环境

- 以规模弥补单卡性能
- 多品牌 / 国产芯片混合
- 降低对单一供应商依赖

### 5.4 AI + HPC 融合场景

- 科学模拟
- 自动驾驶仿真
- 生物计算

SuperNode 正在成为：

> "AI 时代的新型超级计算机形态"

---

## 6. 沐曦 SuperNode 与 Shanghai Cube

### 6.1 沐曦 SuperNode 体系

沐曦（MetaX）作为国产 GPU 与 AI 基础设施厂商，在 SuperNode
方向上给出了较为完整的产品族：

- **C500X 光互联 SuperNode**
  以光链路作为节点间互联方式，目标是降低跨节点通信延迟、提升带宽上限，使多机在
  语义上更接近"单一大节点"。

- **C550 3D Mesh SuperNode**
  基于三维网格拓扑（3D Mesh），将多台服务器组织为一个紧耦合计算体，可扩展至 8
  台节点、64 卡规模，强调"去中心化互联 + 均匀带宽"。

- **Shanghai Cube 系列超节点**
  面向更高密度的整机柜方案，单柜可达 128 卡级别，并可作为构建千卡级集群的基本
  单元。

沐曦 SuperNode 的核心思路是：

- 不假设 NVLink / NVSwitch 的专有生态
- 在国产 GPU + 通用 CPU + 自研互联基础上构建"等价的超节点体验"
- 通过 MXMACA 软件栈，在训练与推理侧补齐并行调度、通信优化与算子适配能力

其战略定位并非"单卡对标最强 GPU"，而是：

> 在单卡能力受限的前提下，通过系统级架构与规模化设计，构建"国产可控的超节点
> 算力单元"。

这与 CloudMatrix、ScaleX 的路线高度一致：
**以系统工程弥补单芯片代差。**

---

### 6.2 Shanghai Cube 超节点方案

**Shanghai Cube** 是一个更偏"产业级交付形态"的国产 SuperNode：

- 由上海产业链多方联合打造
- 沐曦提供 GPU 与互联基础
- 联合液冷、电源、机柜、交换与软件生态厂商
- 目标是形成"国产软硬件一体化超节点标准形态"

核心特征：

#### 高密度液冷整柜

- 单机柜支持至多 128 张 GPU
- 在体积、功耗密度、散热能力上对标国际 SuperPod

#### 模块化架构

- GPU Tray、交换模块、电源模块解耦
- 单节点 / 单模块可替换
- 支持"按需扩展 + 局部升级"

#### 国产全链路闭环

- GPU、互联、操作系统、驱动、运行时
- 面向"自主可控算力底座"设计
- 可服务政府、高校、科研机构、大型央国企

#### 面向大模型工作负载

- 已在高校与研究机构中验证
- 支持 DeepSeek、通用 LLM 的训练与推理
- 可作为"国产大模型工厂"的基础单元

Shanghai Cube 的本质不是"卖一台机器"，而是：

> 将 SuperNode 抽象为一个**可规模复制的国产算力积木**。

---

### 6.3 在 SuperNode 版图中的定位

在整个 SuperNode 技术谱系中：

| 路线                  | 代表                  | 核心特征                             |
| --------------------- | --------------------- | ------------------------------------ |
| NVIDIA                | DGX NVL72 / GB200     | 单卡极强 + 专有互联 + 生态垄断       |
| 国产系统级            | CloudMatrix / ScaleX  | 以规模补性能 + 自研互联              |
| 沐曦 / Shanghai Cube  | MetaX SuperNode       | 国产 GPU + 系统工程 + 模块化整柜     |

沐曦与 Shanghai Cube 的独特价值在于：

#### 降低"进入超节点时代"的门槛

- 不依赖 NVLink 生态
- 可在国产供应链内闭环实现

#### 为 vLLM / SGLang / 国产 Runtime 提供现实载体

- "显存横向可扩展"成为可假设前提
- KV Cache / 激活跨节点通信具备工程可行性
- Agentic / 多轮推理的系统级优化成为可能

#### 在受限环境下保持算力演进能力

- 不再完全依赖"单卡代际跃迁"
- 可以通过架构与规模持续提升系统上限

从 AI Infra 的角度看，沐曦 SuperNode 与 Shanghai Cube 的意义在于：

> 它们证明：
> SuperNode 并非 NVIDIA 专属形态，
> 而是一个可以被"本土化重构"的基础设施范式。

这为"国产 AI Infra Stack"提供了一个真实、可落地的"物理锚点"，
使得 vLLM、SGLang、Agentic Runtime、K8s LWS 等软件层的演进，
不再只是"概念上依赖超节点"，
而是有了一个可以长期共进化的硬件实体。

---

## 7. SuperNode 作为拓扑键（Topology Key）

在 Kubernetes 环境中，SuperNode 可以作为一个特殊的拓扑键来管理：

- 将 SuperNode 定义为一个调度域
- 通过标签（Label）标识同一 SuperNode 内的节点
- 支持 Pod 亲和性（Affinity）和反亲和性（Anti-affinity）调度
- 配合 LeaderWorkerSet 实现 Gang Scheduling

示例拓扑标签：

```yaml
topology.kubernetes.io/supernode: "nvl72-01"
topology.kubernetes.io/zone: "datacenter-a"
```

---

## 8. 总结

SuperNode 本质上是：

> 将"集群"重新抽象为"一个巨型节点"。

它的意义不只是硬件堆叠，而是：

- 重新定义"节点边界"
- 为 AI Runtime 提供新的假设前提
- 让 vLLM / SGLang / Agentic Runtime 可以假设：
  - 显存是"横向可扩展的"
  - 通信是"近乎免费的"
  - 多 Pod = 一个逻辑工作单元

它不是为"所有 AI 工作负载"而生，而是为：

- 模型足够大
- 请求足够多
- 延迟足够敏感
- 负载足够持续

在这些场景中，SuperNode 不只是"更快"，而是：

> **让原本"工程不可行"的事情，变成"架构可行"。**

---

## 参考资料

- [Kubernetes LeaderWorkerSet
  (LWS)](https://github.com/kubernetes-sigs/lws)
- [AWS: Scaling LLM inference workloads with TensorRT-LLM and
  Triton](https://aws.amazon.com/cn/blogs/hpc/scaling-your-llm-inference-workloads-multi-node-deployment-with-tensorrt-llm-and-triton-on-amazon-eks/)
- NVIDIA DGX NVL72 Technical Documentation
- Huawei CloudMatrix Architecture
- Alibaba Pangu AI Infra 2.0
- MetaX SuperNode Solutions

---

## RoadMap (Ongoing)

- [ ] SuperNode 在 Kubernetes 中的最佳实践
- [ ] 与 LeaderWorkerSet 的深度集成
- [ ] SuperNode 性能基准测试
- [ ] 多 SuperNode 集群调度策略
- [ ] 国产 SuperNode 生态发展追踪
