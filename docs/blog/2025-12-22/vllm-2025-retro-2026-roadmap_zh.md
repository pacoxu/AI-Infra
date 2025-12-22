---
status: Active
maintainer: pacoxu
last_updated: 2025-12-22
tags: vllm, llm, inference, roadmap, ai-infrastructure
---

# vLLM 2025 年度回顾与 2026 年路线图

本文总结 vLLM 在 2025 年取得的成就，并展望 2026 年的发展方向。内容来源于
vLLM Office Hours #38 (December 18, 2024)，由 vLLM 项目维护者 Simon Mo (UC
Berkeley) 和 Michael Goin (Red Hat AI) 主讲。

**注意：** 部分内容由 AI 辅助生成，使用前请仔细验证。

## 目录

- [vLLM 项目概览](#vllm-项目概览)
- [2025 年增长亮点](#2025-年增长亮点)
- [API 演进：迈向 Agentic 与强化学习](#api-演进迈向-agentic-与强化学习)
- [模型生态：SOTA 模型支持](#模型生态sota-模型支持)
- [引擎重构：V1 核心架构升级](#引擎重构v1-核心架构升级)
- [硬件生态：多样性与前沿支持](#硬件生态多样性与前沿支持)
- [分布式能力：大规模服务与易用性](#分布式能力大规模服务与易用性)
- [2025 年度总结](#2025-年度总结)
- [2026 年发展重点](#2026-年发展重点)
- [参与方式](#参与方式)
- [参考资料](#参考资料)

## vLLM 项目概览

vLLM 是业界领先的高吞吐、高内存效率的 LLM 推理与服务引擎。

### 核心数据

- GitHub Stars：65K+
- 月度 PR 数量：800+
- 24/7 部署的 GPU：500K+
- 活跃成员：10K+
- Slack 社区：slack.vllm.ai

### 项目里程碑

- **2000+ 贡献者**，来自超过 **50 家主要公司**
- 支持 **100+ 模型架构**
- 灵活的设备并行能力：
  - Tensor Parallel（张量并行）
  - Expert Parallel（专家并行）
  - Data Parallel（数据并行）
  - Context Parallel（上下文并行）
  - Disaggregated Prefill/Decode（分离式预填充/解码）
  - Disaggregated Encoder（分离式编码器）

## 2025 年增长亮点

### 用户增长

- Q1/Q2：使用量增长 **80%**
- Q3：使用量增长 **30%**

**注意：** 这是一个小规模且有偏差的样本数据，未排除使用数据上报。

### 模型分布

在 vLLM 服务的模型中，**Qwen 系列占比非常高**，其次是 Llama、Mistral、
Gpt-OSS 和 DeepSeek 系列。

### 硬件分布

当前硬件支持以 NVIDIA GPU 为主，AMD 硬件占比仅为个位数，但社区正在积极拓展
对更多硬件平台的支持。

## API 演进：迈向 Agentic 与强化学习

vLLM 在 2025 年显著扩展了 API 能力，以支持 Agentic AI 和强化学习场景。

### 核心 API 层次

#### 1. LLM Class

Python 接口，用于离线批量推理。

#### 2. OpenAI 兼容服务器

基于 FastAPI 的在线服务器，兼容 OpenAI API 标准。

#### 3. 通用兼容服务器

- **多模态输入 API**：支持图像、音频等多种输入
- **Rerank、Pooling 和 Embedding API**：支持文本表示任务
- **Responses API**：结构化响应
- **SageMaker API**：AWS 集成
- **Anthropic API**：Claude 模型兼容
- **强化学习 API**：Tokens-in-tokens-out 接口
- **Omni Modality API**（进行中）：全模态支持

#### 4. 原生强化学习支持

vLLM 与多个强化学习框架深度集成：

- verl
- PRIME-RL
- SkyRL
- unsloth
- OPENRLHF
- Pipeline RL
- NVIDIA Cosmos
- TRL
- AReaL
- RLinf
- Nemo RL
- ROLL

## 模型生态：SOTA 模型支持

### 广泛的模型支持

vLLM 支持几乎所有流行的文本生成模型。

### Transformers 后端

- 支持 vLLM 本身未实现但可通过 Transformers 运行的模型
- 开发者可在 Transformers 中编写模型实现
- 利用 vLLM 的 KV 缓存管理和连续批处理能力
- 同时支持视觉和语言模型
- 性能与纯 vLLM 实现相当

### 准确性优先

vLLM 将模型推理准确性放在首位，确保生成结果与原始模型一致。

### 性能优先

在保证准确性的前提下，vLLM 持续优化推理性能。

### 顶尖视觉模型支持

vLLM 对视觉-语言多模态模型提供了业界领先的支持。

### 2025 年多模态趋势

- 更多模型内置多模态理解能力，且不影响文本任务性能
- 开源模型的多模态生成能力不断提升（如 Hunyuan Image 3.0、Qwen3-Omni、
  Qwen-Image-Edit 等）

## 引擎重构：V1 核心架构升级

### vLLM V1：核心架构大升级

**发布日期：** 2025 年 1 月 27 日

vLLM V1 是对核心架构的重大升级，解决了多种推理优化技术组合使用的难题。

### 核心挑战：如何整合和组合多种推理优化？

#### vLLM 中的推理优化技术

**调度相关优化：**

- Prefix Caching（前缀缓存）
- Speculative Decoding（推测解码）
- Chunked Prefills（分块预填充）
- Disaggregated Serving（分离式服务）
- Streaming Prefills（流式预填充）
- Jump-forward Decoding（跳跃式解码）

**其他优化：**

- Quantization（量化）
- Cascade Attention（级联注意力）
- Structured Outputs（结构化输出）
- CPU KV Cache Offloading（CPU KV 缓存卸载）
- Multi-LoRA Serving（多 LoRA 服务）

#### 问题：有效组合多种推理优化

理论上，大多数推理优化技术是正交的，可以组合使用以最大化性能。然而，在实践中
我们发现这非常困难。

**vLLM V0 的特性矩阵：** 部分特性无法很好地协同工作。

**vLLM V1：** 几乎所有特性之间的兼容性问题都得到了修复。

### V1 引擎亮点

vLLM V1 引入了多项关键改进：

#### Hybrid Allocator（混合分配器）

混合分配器是 V1 引擎的核心创新，能够灵活管理 KV 缓存内存，支持不同优化技术
的内存需求。

#### KV Connector（KV 连接器）

KV Connector 提供了灵活的 KV 缓存存储后端，支持：

**项目集成：**

- LMCache
- Mooncake
- llm-d

**存储后端：**

- CPU RAM
- Local Storage
- GDS Backend
- Redis
- InfiniStore
- Mooncake
- Valkey
- Weka

## 硬件生态：多样性与前沿支持

vLLM 积极扩展硬件生态，通过插件机制支持多种硬件平台。

### vLLM 硬件插件生态

- **vLLM TPU**（预览版）：Google TPU 支持
- **vllm-ascend**：华为昇腾 NPU 支持
- **vllm-spyre**：Spyre AI 加速器支持
- **vllm-neuron**：AWS Neuron 支持
- **vllm-gaudi**：Intel Gaudi AI 加速器支持
- **vllm-metax**：MetaX 硬件支持
- **vllm-openvino**：Intel OpenVINO 支持

## 分布式能力：大规模服务与易用性

vLLM 在 2025 年显著提升了大规模部署和分布式服务能力。

### 大规模服务案例

**DeepSeek 服务：** 在 H200 GPU 上实现 **2.2k tok/s** 的吞吐量，采用
Wide-EP（宽专家并行）架构。

参考博客：
blog.vllm.ai/2025/12/17/large-scale-serving.html

### vLLM Router

**vLLM Router** 是高性能且 Prefill/Decode 感知的负载均衡器，为大规模服务
提供智能流量分发。

参考博客：
blog.vllm.ai/2025/12/13/vllm-router-release.html

## 2025 年度总结

vLLM 在 2025 年取得了显著成就：

- **社区增长**：2000+ 贡献者，50+ 主要公司参与
- **技术突破**：V1 引擎发布，特性兼容性大幅提升
- **生态扩展**：支持 100+ 模型架构，多种硬件平台
- **API 丰富**：强化学习、多模态、多种标准 API 支持
- **性能优化**：大规模服务案例，高吞吐量部署

## 2026 年发展重点

vLLM 在 2026 年将聚焦以下三个核心方向：

### 1. 稳定性、准确性、性能

继续提升引擎稳定性，保证推理准确性，优化性能表现。

### 2. 前沿模型支持

- 支持最新的 SOTA 模型架构
- 深度集成强化学习框架

### 3. 硬件稳定性

提升各硬件平台的稳定性和性能，扩大硬件生态覆盖范围。

## 参与方式

欢迎社区成员参与 vLLM 项目：

- **GitHub**：github.com/vllm-project/vllm
- **Slack 社区**：slack.vllm.ai
- **活动与交流**：vllm.ai/events（包含 Office Hour 和全球 vLLM Meetup）

## 参考资料

- vLLM Office Hours #38 视频：
  youtube.com/watch?v=-5n9_IxkLxo&list=PLbMP1JcGBmSHxp4-lubU5WYmJ9YgAQcf3
  &index=1
- vLLM 官方网站：vllm.ai
- vLLM GitHub 仓库：github.com/vllm-project/vllm
- vLLM 博客：blog.vllm.ai

---

*本文由 AI-Infra 社区整理，欢迎反馈与贡献。*
