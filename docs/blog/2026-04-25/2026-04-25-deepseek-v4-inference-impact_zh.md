---
status: Active
maintainer: pacoxu
date: 2026-04-25
tags: deepseek, deepseek-v4, inference, moe, tilelang, ascend, cuda, ai-infrastructure
canonical_path: docs/blog/2026-04-25/2026-04-25-deepseek-v4-inference-impact_zh.md
source_urls:
  - https://api-docs.deepseek.com/zh-cn/news/news260424
  - https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro
  - https://github.com/deepseek-ai/FlashMLA
  - https://github.com/deepseek-ai/DeepEP
  - https://github.com/deepseek-ai/DeepGEMM
  - https://github.com/tile-ai/tilelang
  - https://github.com/tile-ai/tilelang/blob/main/examples/deepseek_mla/README.md
  - https://github.com/tile-ai/tilelang-ascend
---

# DeepSeek V4 对推理方向的影响：长上下文、Agent Runtime 与非 CUDA 内核生态

2026 年 4 月 24 日，DeepSeek 发布了 `DeepSeek-V4` 预览版并同步开源。官方给出的
关键信号非常明确：`DeepSeek-V4-Pro` 总参数 **1.6T**、激活参数 **49B**，
`DeepSeek-V4-Flash` 总参数 **284B**、激活参数 **13B**，两者都把
**1M context** 作为默认能力；同时，模型又明显针对 **Agent** 场景做了专项优化。

如果从推理基础设施角度看，这不是一次“模型分数提升”那么简单，而是在重新定义未来
推理栈最值钱的部分。

> 说明：你提到的 `tiekernel / tielang`，公开且容易核实的资料主要集中在
> `TileLang` 主仓和 `tilelang-ascend`。下文用这条线来展开；如果你指的是围绕
> TileLang 的其他衍生 kernel 项目，整体判断方向基本一致。

## 先说结论

- **长上下文正式变成默认推理场景**。优化重点会从“decode 内环再快一点”，转向
  “上下文压缩、注意力变体、KV cache 分层、prefill 组织方式”。
- **Agent runtime 会进入推理主战场**。评测和 API 形态都表明，单轮 token/s
  不再是唯一指标，工具调用、多步状态、会话粘性会越来越重要。
- **MoE 的真正瓶颈继续向通信与拓扑迁移**。激活参数仍然远小于总参数，说明
  expert dispatch/combine、all-to-all、RDMA/NVLink 组织方式会比单点 GEMM 更关键。
- **CUDA 的护城河还在，但“唯一入口”地位会被削弱**。像 `TileLang` 这样把新算子
  抽象到 DSL/编译器层的路线，会显著缩短新模型结构在非 CUDA 后端上的跟进时间。

## 1. DeepSeek V4 真正改变了什么

### 1.1 1M context 不再是“实验配置”，而是默认规格

根据官方模型卡，DeepSeek-V4 采用了混合注意力架构，把
`Compressed Sparse Attention (CSA)`、`Heavily Compressed Attention (HCA)`
与 `DeepSeek Sparse Attention (DSA)` 组合在一起。在 **1M-token context** 下，
`DeepSeek-V4-Pro` 相比 `DeepSeek-V3.2`，只需要 **27% 的单 token 推理 FLOPs**
和 **10% 的 KV cache**。

这条信息的意义很大：

- 推理优化的核心，已经不只是 dense attention 的常规 kernel；
- `prefill` 的成本结构会重新洗牌，因为 token 压缩与 sparse path 直接改变了
  长上下文阶段的算力与显存占用；
- `KV cache` 不再只是“怎么分页”这么简单，而会演进成
  “压缩后保留什么、在哪一层保留、在哪个介质保留”的系统问题。

换句话说，未来推理引擎的竞争力，会越来越取决于它能否快速吃下
**长上下文注意力新变体**。

### 1.2 DeepSeek V4 明确把 Agent 场景放进模型目标函数

DeepSeek 官方新闻页释放了几个很明确的信号：

- `DeepSeek-V4` 在 Agentic Coding 和其他 Agent 评测上显著增强；
- 模型针对 `Claude Code`、`OpenClaw`、`OpenCode`、`CodeBuddy` 等主流 Agent
  产品做了适配和优化；
- API 层面也同步暴露了 `reasoning_effort`，并建议复杂 Agent 场景使用 `max`。

这说明一个很现实的变化：**推理系统不再只是“响应一次请求”，而是在执行一个有状态、
多轮、多工具调用的任务**。

因此，平台层要开始更认真地看这些能力：

- 会话级路由与 cache locality；
- 工具调用前后 KV 与中间状态能否保留下来；
- 多轮任务的 wall-clock 完成时间，而不仅是单轮吞吐；
- 长任务对 autoscaling、抢占、故障恢复的影响。

### 1.3 V4 继续证明：MoE 仍然是高端推理的主线

`1.6T/49B` 和 `284B/13B` 这两个数字本身就说明，DeepSeek 仍然在沿着
**大总参 + 小激活** 的 MoE 路线走。

这意味着推理系统的关键矛盾继续是：

- expert 如何分布；
- token 如何 dispatch / combine；
- 跨节点通信如何不拖垮 decode 尾延迟；
- prefill 与 decode 在通信路径上的优化是不是要分开做。

这正是为什么 DeepSeek 官方会持续把 `DeepEP` 这种
**expert-parallel communication library** 作为关键基础设施公开出来。

## 2. 这会如何改写推理栈

### 2.1 推理引擎会从“dense decode 优化器”变成“长上下文 runtime”

过去几年，推理引擎的主要故事是：

- continuous batching
- paged KV cache
- speculative decoding
- quantization
- CUDA kernel fusion

这些当然还重要，但 `DeepSeek-V4` 往前推了一步：引擎必须更擅长处理
**压缩注意力、稀疏注意力、超长上下文和混合推理路径**。

我的判断是，下一阶段更有价值的能力会是：

- hybrid attention 的统一执行路径；
- `prefill/decode` 分离后的专门 kernel 与调度；
- 面向 128K/1M context 的 KV 层级管理；
- 针对 Agent 工作负载的 session stickiness 与 state reuse。

如果引擎还只是在 4K/8K prompt、单轮 chat、纯 dense decode 上追 token/s，
很可能会开始偏离主战场。

### 2.2 推理平台会更像“网络系统”而不是“单机 kernel 系统”

`DeepEP` README 里直接写得很清楚：它面向 `MoE` 和 `EP`，
提供高吞吐、低延迟的 all-to-all GPU kernels，用来做 MoE 的
dispatch / combine；同时又区分了两类场景：

- 面向 `prefill` 的高吞吐路径，支持 `NVLink -> RDMA` 这样的跨域转发；
- 面向 `decode` 的低延迟路径，提供 pure RDMA kernel 来压低尾延迟。

这其实已经把问题说透了：

- **prefill** 更像带宽问题；
- **decode** 更像尾延迟问题；
- **MoE 推理** 的关键，不再只是单卡 matmul，而是通信拓扑能否被有效利用。

所以，平台层接下来要更重视：

- 拓扑感知调度；
- 专门面向 EP 的通信库；
- P/D disaggregation；
- KV-aware routing；
- 多角色 Pod 的启动顺序与共享缓存。

### 2.3 基准测试会从 token/s 扩展到“任务完成度”

DeepSeek-V4 官方模型卡已经把评测维度扩展到了：

- `MRCR 1M`
- `CorpusQA 1M`
- `Terminal Bench 2.0`
- `SWE Verified`
- `MCPAtlas`
- `Toolathlon`

这对推理基础设施是个明确信号：未来更可信的 benchmark，不是单一吞吐数字，
而是下面这些组合指标：

- 128K / 1M prompt 下的 prefill 成本；
- KV cache 命中率与 cache 保活能力；
- all-to-all 的 P95 / P99 延迟；
- tool-use 任务的端到端完成时间；
- 多轮 Agent 会话中状态迁移的代价。

## 3. 为什么要把 TileLang / Ascend 放进同一张图里看

### 3.1 DeepSeek V4 的“新价值点”刚好都是 DSL 擅长承接的对象

DeepSeek V4 这次最重要的结构增量，集中在：

- 长上下文注意力压缩；
- sparse attention；
- MoE dispatch/combine；
- 大规模 expert 相关 kernel。

这些并不是只能用 CUDA C++ 手搓的对象。只要模型结构足够清晰、调度与布局模式能被
表达出来，它们就很适合进入 **kernel DSL + codegen** 的体系。

而 `TileLang` 这条路线正在证明这件事：

- 主仓已经支持 `AscendC / AscendNPU IR` 后端；
- 还增加了 `Apple Metal` 与 `CuTeDSL backend`；
- 在 `DeepSeek MLA` 示例中，官方给出的结果是：
  `TileLang` 在多数场景下性能可比 `FlashMLA`，并且代码量大约只有
  **80 行 Python**；
- 主仓新闻里还写明，AMD `MI300X` 上的高性能 `FlashMLA` 实现已经能做到与
  手写汇编级 kernel 对齐。

这意味着一件很重要的事：**前沿模型算子的扩散速度，正在从“按硬件厂商分别重写”，
转向“先在 DSL 层表达，再向不同后端落地”**。

### 3.2 tilelang-ascend 最近的节奏，正好说明非 CUDA 侧在补齐“DeepSeek 相关能力”

`tilelang-ascend` 最近几个月的更新节奏很有代表性：

- `2026-04-24`：发布 `DeepSeek V4 kernels`
- `2026-03-28`：发布高性能 `Flash Attention` 与 `Sparse Flash Attention`
- `2026-03-12`：新增 `ACLGraph` 集成示例
- `examples` 目录里还在持续补 `LightningIndexer`、`TopK Selector` 等复杂算子

这说明什么？

- 非 CUDA 后端已经不满足于只补 GEMM；
- 它们在主动补齐 **DeepSeek/Agent/长上下文** 这类新模型真正需要的结构性算子；
- 一旦这些能力能在 DSL 层复用，Ascend 对新模型的跟进速度会明显加快。

这也是我认为它会冲击 CUDA 生态的核心原因之一。

## 4. 这会不会真正冲击 CUDA 生态？

我的判断是：**会，但冲击的重点不是“CUDA 明天就不行了”，而是 CUDA 从
“唯一默认选项”变成“成熟度最高的一个选项”。**

### 4.1 为什么 CUDA 的优势短期内还很稳

因为 DeepSeek 官方今天公开出来的很多核心基础设施，仍然明显偏向 NVIDIA：

- `FlashMLA` 当前要求 `SM90 / SM100` 与 `CUDA 12.8+`；
- `DeepGEMM` 明确是面向 `NVIDIA GPUs` 的 `FP8 GEMM kernels`；
- `DeepEP` 的主路径依赖 `NVLink`、`RDMA`、`NVSHMEM`，并以 Ampere / Hopper
  为核心环境。

换句话说，真正高成熟度、可直接复用的前沿推理基础设施，今天依然主要长在 CUDA
生态里。

### 4.2 但 CUDA 的护城河已经开始从“专有语法”退到“工程成熟度”

同时也要看到另一面：

- `TileLang` 已经把很多原本高度 CUDA 化的优化模式抽象成更高层表达；
- `tilelang-ascend` 正在快速补 `DeepSeek V4 kernels`、`Sparse Flash Attention`
  这些更贴近新模型真实需求的能力；
- `DeepEP` 生态里也已经出现了面向异构 GPU / NIC 的延展项目。

这意味着未来的竞争点会变成：

- 谁能最快把新模型结构变成可运行 kernel；
- 谁能最快在不同硬件后端上做出“够好”的版本；
- 谁的编译器、DSL、runtime、集群调度能协同起来。

在这种格局下，CUDA 仍然可能是**最好**的实现，但不一定还是**唯一值得做**的实现。

## 5. 给 AI-Infra 团队的几个直接建议

1. 把 **长上下文 attention / KV 体系** 放到推理优化优先级最前面，而不是继续只盯
   decode token/s。
2. 把 **MoE 通信** 当成推理基础设施的一等公民来建设，包括 all-to-all、RDMA、
   拓扑感知、EP 低延迟路径。
3. 在引擎与平台抽象层预留 **多后端 kernel 接口**，不要把新算子能力硬编码成
   “只有 CUDA kernel 才能接”。
4. 基准测试里增加 **1M context + Agent task**，否则很容易把平台优化到一个
   已经过时的目标函数上。
5. 如果预算允许，建议维持一条 **CUDA 主线 + Ascend/AMD 备线** 的验证路径，
   因为真正的竞争已经从硬件采购，延伸到 kernel 迁移速度和 runtime 组织能力。

## 总结

`DeepSeek-V4` 对推理方向的最大影响，不是简单把模型做得更强，而是把推理栈的竞争重心
从“CUDA 上的通用 dense 优化”推向了 **长上下文压缩、Agent runtime、MoE 通信、
以及可移植 kernel DSL**。

从这个角度看，`TileLang + Ascend` 最近围绕 `DeepSeek V4` 的补齐动作确实值得警惕：
它们未必会立刻取代 CUDA，但已经足以削弱“前沿推理能力只能长在 CUDA 上”的旧共识。

## 参考

- DeepSeek API Docs:
  [DeepSeek-V4 预览版：迈入百万上下文普惠时代](https://api-docs.deepseek.com/zh-cn/news/news260424)
- Hugging Face:
  [DeepSeek-V4-Pro Model Card](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro)
- DeepSeek GitHub:
  [FlashMLA](https://github.com/deepseek-ai/FlashMLA),
  [DeepEP](https://github.com/deepseek-ai/DeepEP),
  [DeepGEMM](https://github.com/deepseek-ai/DeepGEMM)
- TileLang GitHub:
  [tilelang](https://github.com/tile-ai/tilelang),
  [DeepSeek MLA Example](https://github.com/tile-ai/tilelang/blob/main/examples/deepseek_mla/README.md),
  [tilelang-ascend](https://github.com/tile-ai/tilelang-ascend)
