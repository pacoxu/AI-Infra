---
status: Active
maintainer: pacoxu
date: 2025-12-15
tags: ai-infrastructure, ray, vllm, pytorch, kubernetes, data-processing
canonical_path: docs/blog/2025-12-15/sql-to-inference_zh.md
---

# 从 SQL on CPUs 到 Inference on GPUs：AI 数据处理的演进

**基于 PyTorchCon 2025 演讲：《开源后训练技术栈：Kubernetes + Ray + PyTorch + vLLM》
— Robert Nishihara，Anyscale 联合创始人**

## 引言

AI 基础设施正在经历一场根本性的变革。正如 LAMP 技术栈（Linux、Apache、MySQL、PHP）
定义了互联网时代，一个新的技术栈正在兴起以驱动 AI 时代。在最近的 PyTorchCon 2025
上，Anyscale 的 Robert Nishihara 介绍了 **PARK 技术栈**（PyTorch + AI + Ray +
Kubernetes）的概念，它正在迅速成为大规模 AI 部署的默认平台。

本文探讨这一转型的两个关键方面：

1. **新工作负载**：AI 数据处理如何从 SQL on CPUs 转向 Inference on GPUs
2. **共同演进的技术栈**：vLLM + Ray 和 Ray + Kubernetes 如何共同演进

## 第一部分：新工作负载 — 从 SQL on CPUs 到 Inference on GPUs

### 数据处理的范式转变

传统数据处理以结构化的表格数据为中心，使用 SQL 查询在 CPU 集群上处理。AI 时代
引入了根本不同的工作负载：

| 维度 | 传统 (SQL) | AI 数据处理 |
| ---- | ---------- | ----------- |
| **数据类型** | 表格数据 | 多模态数据（图像、视频、音频、文本、传感器） |
| **处理方式** | 常规处理 | 推理 + 常规处理 |
| **计算资源** | CPUs | CPUs & GPUs |

**关键洞察**：数据处理性质的转变不仅仅是增加 GPU - 而是从根本上改变了数据的含义
和我们处理数据的方式。

### 为什么这种转变很重要

从 SQL on CPUs 到 Inference on GPUs 的转变不仅仅是硬件的变化：

1. **数据复杂性**：从结构化表格转向捕捉真实世界的丰富多模态数据，包括图像、视频、
   音频和传感器读数

2. **处理范式**：传统 SQL 查询正在被推理操作补充（有时被替代），这些操作从非结构化
   数据中提取意义

3. **资源需求**：GPU 加速不仅对训练至关重要，对生产数据处理管道也变得必不可少

4. **规模挑战**：管理分布式 GPU 工作负载需要超越传统数据库集群的新编排模式

### 实际影响

这种转变使以前不可能的新应用成为可能：

- **自主系统**：实时处理传感器数据、摄像头画面和激光雷达
- **内容理解**：大规模分析图像和视频用于推荐和审核
- **语音接口**：实时语音识别和自然语言理解
- **文档智能**：从非结构化文档中提取结构化信息

基础设施必须演进以高效支持这些工作负载。

## 第二部分：共同演进的技术栈 — vLLM + Ray & Ray + Kubernetes

### 理解 PARK 技术栈

在 Linux 基金会的 Open Source Summit Japan 上，Jim Zemlin 提出了
**PARK 技术栈**：

- **P**: PyTorch（主流的 AI 框架）
- **A**: AI（模型和算法）
- **R**: Ray（用于大规模 AI/ML 的分布式计算框架）
- **K**: Kubernetes（云原生编排）

就像 LAMP 定义了 Web 基础设施，PARK 正在定义 AI 基础设施的一代。

### vLLM 和 Ray 的共同演进

**为什么 Ray 无处不在**：几乎每个开源强化学习（RL）框架都将 Ray 作为编排器：

| 框架 | 训练引擎 | 服务引擎 | 编排器 |
| ---- | -------- | -------- | ------ |
| TRL (Hugging Face) | Hugging Face Trainer | Hugging Face, vLLM | **Ray** |
| Verl (ByteDance) | FSDP, DeepSpeed, Megatron | vLLM, SGLang | **Ray** |
| OpenRLHF | DeepSpeed | Hugging Face, vLLM | **Ray** |
| AReaL (Ant Group) | DeepSpeed, Megatron | vLLM, SGLang | **Ray** |
| Prime RL | FSDP | vLLM | **Ray** |
| ROLL (Alibaba) | DeepSpeed, Megatron | vLLM, SGLang | **Ray** |
| NeMo-RL (Nvidia) | FSDP, Megatron | vLLM | **Ray** |
| SkyRL (UC Berkeley) | FSDP, DeepSpeed | vLLM, SGLang, OpenAI | **Ray** |
| SLIME (Z.ai) | Megatron | SGLang | **Ray** |
| RAGEN | Verl backend | Hugging Face, vLLM, SGLang | **Ray** |

**关键模式**：Ray 提供编排层，连接训练引擎（FSDP、DeepSpeed、Megatron）与服务
引擎（vLLM、SGLang），使得像从人类反馈中学习（RLHF）这样的复杂后训练工作流
成为可能。

### 新工作负载：RL/后训练架构

后训练工作流引入了复杂的编排需求：

```text
┌─────────────────────────────────────────────────────┐
│  RL / 后训练系统                                     │
│                                                      │
│  ┌──────────────────┐         ┌──────────────────┐ │
│  │  学习算法        │ ◄─────► │      Actor       │ │
│  │ (GRPO, PPO, ...) │         │                  │ │
│  │                  │         │  ┌──────────┐    │ │
│  │  Actor 更新      │         │  │ 工具     │    │ │
│  └──────────────────┘         │  │ (思考,   │    │ │
│          ▲                    │  │ 终端,    │    │ │
│          │ 多轮               │  │ 浏览器)  │    │ │
│          │ Rollouts +         │  └──────────┘    │ │
│          │ 奖励               │        │         │ │
│          │                    │        ▼         │ │
│  ┌───────┴───────┐           │  ┌──────────┐    │ │
│  │ VeRL 后端     │           │  │环境运行时│    │ │
│  └───────────────┘           │  │ (SkyRL)  │    │ │
│                              │  └────┬─────┘    │ │
│                              │       │          │ │
│                              │       ▼          │ │
│                              │  观察/奖励       │ │
│                              └──────────────────┘ │
│                                                    │
│                        动作 → API 网关             │
│                                      ▼             │
│                                 沙箱服务器         │
└────────────────────────────────────────────────────┘
```

**组件**：

- **学习算法**：GRPO、PPO 和其他 RL 算法
- **Actor**：使用工具（思考、终端、浏览器）做出决策
- **环境运行时**：执行动作并提供反馈
- **VeRL 后端**：协调多轮 rollouts 和奖励

这种架构需要 Ray 自然提供的复杂编排。

### Ray + Kubernetes：完美组合

Ray 和 Kubernetes 正在共同演进以支持 AI 工作负载：

**AI 基础设施软件栈需求**：

```text
┌──────────────────────────────────────────────────┐
│ AI 工作负载（后训练、多模态数据处理、            │
│              Agentic AI 等）                     │
├──────────────────────────────────────────────────┤
│                                                  │
│    AI 基础设施软件栈的挑战：                     │
│                                                  │
│    • 扩展计算和异构性                           │
│    • 资源管理和混合 CPU+GPU                     │
│    • 多种数据模态                               │
│    • Spot 实例管理                              │
│    • 调度和依赖管理                             │
│    • 硬件故障                                   │
│                                                  │
├──────────────────────────────────────────────────┤
│         计算基底：GPUs、CPUs                     │
└──────────────────────────────────────────────────┘
```

**Ray 和 Kubernetes 如何互补**：

1. **Kubernetes 提供**：
   - 容器编排和生命周期管理
   - 资源分配和节点管理
   - 服务发现和网络
   - 声明式基础设施

2. **Ray 提供**：
   - 分布式应用框架
   - 有状态计算的 Actor 模型
   - ML 工作流的原生 Python API
   - 应用级调度和数据共享

3. **两者共同实现**：
   - 从开发到生产的无缝扩展
   - 高效的混合 CPU+GPU 工作负载管理
   - 长时间运行的 AI 训练作业的容错能力
   - 与云原生可观测性的集成

### 实际采用

PARK 技术栈正在被全球组织采用：

- **研究实验室**：UC Berkeley 的 SkyRL 用于 RL 研究
- **科技公司**：字节跳动的 Verl、阿里巴巴的 ROLL、蚂蚁集团的 AReaL
- **AI 初创公司**：Z.ai 的 SLIME 用于高效后训练
- **云服务商**：AWS、GCP、Azure 均支持 Ray on Kubernetes

## 未来：PARK 成为新标准

就像 LAMP 成为 Web 基础设施的代名词，PARK 正在成为 AI 基础设施的标准：

- **PyTorch** 为模型开发提供基础
- **AI 算法**继续快速发展
- **Ray** 编排复杂的分布式工作流
- **Kubernetes** 大规模管理底层基础设施

### 为什么 PARK 重要

PARK 技术栈解决了 AI 基础设施的根本挑战：

1. **统一平台**：从研究到生产使用一致的工具
2. **云原生**：利用现代编排和可观测性
3. **开源**：社区驱动的开发，无供应商锁定
4. **生产就绪**：经过大型组织大规模实战检验

## 结论

从 SQL on CPUs 到 Inference on GPUs 的转变代表了我们处理数据方式的根本转变。
这种变化不仅仅是关于硬件 - 而是支持全新类别的应用，这些应用处理多模态数据并需要
实时推理。

PARK 技术栈（PyTorch + AI + Ray + Kubernetes）正在成为这个新时代的基础技术，
Ray 作为连接 AI 框架与云原生基础设施的关键编排层。vLLM + Ray 和 Ray + Kubernetes
的共同演进展示了生态系统如何围绕大规模 AI 部署的成熟模式收敛。

随着我们更深入地进入 AI 时代，理解和采用这些模式对于构建可扩展、高效的 AI 基础
设施至关重要。

---

## 参考资料

### PyTorchCon 2025 演讲

- **视频**：[开源后训练技术栈：Kubernetes + Ray + PyTorch + vLLM - Robert
  Nishihara, Anyscale](https://www.youtube.com/watch?v=JEM-tA3XDjc&list=PL_lsbAsL_o2BUUxo6coMBFwQE31U4Eb2q&index=37)

### 相关博客文章

- [推理编排解决方案](../2025-12-01/inference-orchestration_zh.md)
- [Kubernetes 上的训练指南](../../training/README.md)
- [PyTorch 生态系统概览](../../training/pytorch-ecosystem.md)

### 项目和框架

- [Ray](https://github.com/ray-project/ray) - 分布式计算框架
- [vLLM](https://github.com/vllm-project/vllm) - 高吞吐量 LLM 服务
- [PyTorch](https://pytorch.org/) - 机器学习框架
- [Kubernetes](https://kubernetes.io/) - 容器编排

---

**作者**：AI 基础设施学习路径  
**日期**：2025 年 12 月 15 日  
**标签**：#ai-infrastructure #ray #vllm #pytorch #kubernetes #data-processing
