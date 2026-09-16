---
status: Active
maintainer: pacoxu
date: 2026-09-16
last_updated: 2026-09-16
tags: kubernetes, gke, google-cloud, agent-substrate, agent-sandbox, gvisor, microvm, ai-infrastructure
canonical_path: docs/blog/2026-09-16/2026-09-16-agent-substrate-available-on-gke_zh.md
source_urls:
  - https://cloud.google.com/blog/products/containers-kubernetes/agent-substrate-available-on-gke
  - https://docs.cloud.google.com/kubernetes-engine/ai-ml/about-agent-substrate
  - https://github.com/agent-substrate/substrate
  - https://github.com/agent-substrate/substrate/blob/main/docs/architecture.md
  - https://cloud.google.com/kubernetes-engine
  - https://docs.cloud.google.com/kubernetes-engine/docs/concepts/machine-learning/agent-sandbox
  - https://github.com/kubernetes-sigs/agent-sandbox
  - https://cloud.google.com/blog/products/containers-kubernetes/bringing-you-agent-sandbox-on-gke-and-agent-substrate
  - https://gvisor.dev
  - https://github.com/cloud-hypervisor/cloud-hypervisor
  - https://cloud.google.com/storage
  - https://cloud.google.com/kubernetes-engine/docs/concepts/about-custom-compute-classes
  - https://cloud.google.com/products/axion
  - https://cloud.google.com/filestore
  - https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/filestore-csi-driver
  - https://nousresearch.com
  - https://github.com/nousresearch/hermes-agent
  - https://openrouter.ai
  - https://antigravity.google
  - https://code.claude.com
  - https://openai.com/codex
  - https://openclaw.ai
---

# Agent Substrate 为 GKE 带来高密度、可扩展的可信基础设施

> 原文：[Agent Substrate brings high-density, scalable, trusted infrastructure to GKE](https://cloud.google.com/blog/products/containers-kubernetes/agent-substrate-available-on-gke)
>
> 作者：[Alex Zakonov](https://www.linkedin.com/in/azakonov)（VP Engineering）、
> [Tim Hockin](https://cloud.google.com/blog/authors/tim-hockin)（Engineer）
>
> 日期：2026 年 9 月 16 日

今天，我们宣布 [Agent Substrate](https://docs.cloud.google.com/kubernetes-engine/ai-ml/about-agent-substrate)
已可在 [Google Kubernetes Engine（GKE）](https://cloud.google.com/kubernetes-engine)
上使用。Agent Substrate 是一个开源、默认安全（secure-by-default）的 Agent
执行运行时，目标是以比标准容器运行时高 **10 倍** 的密度运行数百万个沙箱。它面向
自主 Agent 时代设计：原生提供零信任内核隔离与网络隔离，恢复延迟低于 **500ms**，
挂起/恢复吞吐超过 **每秒 500 次**。

Agent Substrate 以开源方案提供，可运行在任意 Kubernetes 基础设施上，并对 GKE
做了优化。领先的 AI 团队已经在其上构建：[Nous Research](https://nousresearch.com)
（[Hermes Agent](https://github.com/nousresearch/hermes-agent) 背后的团队）正在
Agent Substrate 之上持续开发。按 [OpenRouter](https://openrouter.ai) 用量统计，
Hermes 目前在生产力、编码、CLI 和个人助手等类别中位列全球第一的 AI Agent。

## 从本地走到百万级 Agent 规模

开发者已经在本地运行 [Antigravity](https://antigravity.google/)、
[Claude Code](https://code.claude.com)、
[Codex](https://openai.com/codex)、
[OpenClaw](https://openclaw.ai/) 和 Hermes 等 harness。但这与同时运行数十万个
长期存活、会生成代码、调用工具并驱动自动化执行的并发 Agent，有本质区别——现有架构
往往很难同时满足这些挑战。

把 Agent 平台从本地原型扩到大规模运行，会从根本上改变基础设施约束，常见包括：

- **不透明的信任边界**：模型可以即时生成并执行任意代码。如果没有内核级隔离和动态
  网络控制，运行从未被人工审查过的不可信代码，就可能带来宿主机逃逸、凭证窃取和数据
  外泄风险。
- **工具访问摩擦**：Agent 需要完整的计算机环境，才能调用命令行工具、无头浏览器和
  文件系统工作区。这些能力必须既安全，又足够快、足够容易落地。
- **大规模突发**：Agent harness、基准测试和强化学习 rollout 可以在每分钟创建数千个
  沙箱。通用调度器很难扛住这种 churn；反复解压容器镜像也会造成严重的磁盘争用。
- **空闲算力浪费**：自主 Agent 绝大多数时间都在休眠，等待模型推理、工具响应或人类
  反馈。为闲置容器预留专用 CPU 和内存，会浪费宝贵资源。

## 专为 Agent 打造的 Substrate

平台团队碰到这些问题时，往往只能接受一种不可接受的权衡：要么牺牲控制和隔离，要么
承受虚拟机的高延迟和低效率。我们认为团队不该被迫二选一。

Agent Substrate 的做法是把 **Agent 执行** 与 **机器管理** 解耦。它构建在云原生
Kubernetes 基础设施之上，提供一层专为 agentic 工作负载设计的新执行层。

![Agent Substrate 把 Agent 执行与机器管理解耦](https://storage.googleapis.com/gweb-cloudblog-publish/images/1_2dtrRM6.max-1900x1900.jpg)

在此之上，执行层直接管理沙箱化 Agent 环境的生命周期：

- **默认安全**：使用硬件隔离的 [Cloud Hypervisor](https://github.com/cloud-hypervisor/cloud-hypervisor)
  microVM 或 [gVisor](https://gvisor.dev) 沙箱，再配合出口代理（egress proxy）。
  代理执行细粒度网络策略，并在 Agent 无法触及的位置注入凭证，从而防止凭证窃取。
- **亚秒级激活**：把已激活的 Agent 毫秒级调度到预热 Worker 上，按需启动，避免容器
  启动延迟。
- **高效率**：空闲 Actor 可在数百毫秒内被挂起并取消调度，释放计算资源。
- **开源且可移植**：可运行在任意计算环境中的任意 Kubernetes 集群上，并兼容任意
  Agent 框架或 harness，包括 Claude Code、OpenClaw 和 Hermes。

## 核心架构原则

我们用四条核心架构原则，指导 Agent Substrate 如何解决上述挑战。

### 1. 内核与网络默认安全

AI Agent 的核心能力之一，就是生成并运行不可信代码和终端命令。把这些代码跑在共享
服务器上，会在共享内核或网络层造成逃逸和意外数据泄漏的严重风险。

![Agent Substrate 在内核与网络层默认安全](https://storage.googleapis.com/gweb-cloudblog-publish/images/2_zC5wfpY.max-1900x1900.jpg)

Agent Substrate 在宿主机内核和网络层都采取默认安全立场。团队可以在两种隔离方式中
选择：硬件隔离的 Cloud Hypervisor microVM（提供完整 Linux 内核兼容性），或开销更低
的 gVisor 沙箱内核隔离。Agent Substrate 的集成网关管理所有出站和入站请求，从而提供
细粒度、可扩展的网络访问控制。

### 2. 面向低延迟激活的控制面与数据面

要为隔离、长生命周期的 Agent 工作负载优化密度，需要专用的控制面和数据面，才能把
延迟压到最低，并把挂起/恢复吞吐拉到最高。Agent Substrate 引入专用控制面，以尽量低
的延迟做数据感知调度；数据面则直接在预热 Worker 上每秒处理数百次挂起/恢复，减少
环境准备开销。快照会写入本地磁盘和
[Google Cloud Storage](https://cloud.google.com/storage)，以实现持久状态保存。不到
**500ms**，一个沙箱环境就能恢复到先前状态；一旦再次空闲，也可以立即重新挂起。

![Agent Substrate 控制面与数据面的挂起/恢复路径](https://storage.googleapis.com/gweb-cloudblog-publish/images/3_AQ7nEJ0.max-1900x1900.jpg)

### 3. 高密度与“只为活跃计算付费”的经济模型

Agent 大部分时间都在等待模型推理、工具响应或用户输入。为闲置容器预留物理 CPU 和
内存，会锁住昂贵且稀缺的容量，让大规模 Agent 集群难以持续。

Agent Substrate 可以在 Agent 暂停的瞬间释放资源。它把 guest hypervisor 的状态快照
到本地磁盘和 Cloud Storage，释放 RAM 和 CPU 去运行其他 Agent，同时保持状态完整。
当下一轮对话或工具调用到来时，Agent Substrate 能在毫秒级恢复这份快照会话。这种
零空闲模型可以在每台宿主机上打包超过 **1,000** 个休眠 Agent，计算密度比传统计算
高 **10 倍**。如果工作负载需要跨轮次共享文件系统，可选的 Filestore agent volume
controller 能提供持久 NFS 存储——下文会继续介绍。

### 4. 以 Kubernetes 为根基：规模与可靠性

如果在标准虚拟机上自建沙箱编排器，团队就必须自己维护大量运维工具：节点恢复、自动
扩缩、跨可用区调度和网络策略。但如果把每一次亚秒级工具调用都走标准 Kubernetes
Pod 生命周期，又会给每个请求增加数秒延迟。

Agent Substrate 把两条路合在一起。高频挂起/恢复通过专用数据面直接跑在本地 Worker
上；与此同时，Kubernetes 负责管理机器，处理节点自愈、集群自动扩缩和集群可靠性，
并驱动 Worker Pod 自身的生命周期。对于仍需要标准 Pod 语义的工作负载，现有原语如
[Agent Sandbox](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/machine-learning/agent-sandbox)
和内核隔离 Pod 可以继续并行使用。

## 针对 Google Cloud 基础设施优化

要建成百万级 Agent 平台，底层计算和存储必须匹配。GKE 上的 Agent Substrate 通过自定义
[ComputeClasses](https://cloud.google.com/kubernetes-engine/docs/concepts/about-custom-compute-classes)
动态管理不同规格和系列的机器池（包括 Spot 和按需池），从而最大化机器可得性和灵活性。
这包括对 [Google Axion](https://cloud.google.com/products/axion)（Google 自研
Arm 处理器）的原生支持：对沙箱工作负载，它可比竞品云产品提供最高 **30%** 更好的
性价比。对有状态工作区，GKE 上的 Agent Substrate 还可以可选集成
[Filestore](https://cloud.google.com/filestore) agent volumes。这是一项新能力，能在
毫秒级挂载和卸载 NFS，让 Agent 近乎瞬时启动/恢复；同时原生支持
Read-Write-Many（RWX）访问和 POSIX 兼容文件锁，以便多个 Agent 安全协作、避免写冲突。

## 在可扩展的基础上构建你的 Agent 平台

构建生产级 Agent 应用时，不应在强安全、低延迟和运维规模之间被迫取舍。

Nous Research 打造了 Hermes。按 OpenRouter 用量统计，它是全球第一的 AI Agent，并在
生产力、编码、个人助手和 CLI Agent 类别中同样排名第一。Nous Research 是 Agent
Substrate 的早期设计伙伴，评估运行时如何处理 Agent 工作负载引入的隔离与身份需求。

> “我们构建 Hermes Enterprise，是为了让客户能够部署到自己现有的基础设施中，同时处理
> 每个 Agent 的隔离和可扩展访问控制。Agent Substrate 在平台层同时解决了这两件事，
> 并且还能保住宝贵的计算资源。与 Agent Substrate 的合作经验让我们有信心：随着 Agent
> 工作负载增长，这套架构可以高效扩展。”
>
> —— Hervé Bizira，Nous Research 首席商务官（Chief Business Officer）

通过把 Kubernetes 的机器韧性、节点自愈和声明式管理，与面向内核隔离、只为活跃计算
付费、亚秒级执行的 Agent 原生数据面结合起来，Agent Substrate 给工程团队提供了一条
清晰的扩展路径。

Agent Substrate 开源，并向所有 GKE 客户开放用于非生产工作负载。生产环境的 GA 支持
目前通过白名单提供。要在 GKE 集群上部署，请参阅
[Agent Substrate on GKE 文档](https://docs.cloud.google.com/kubernetes-engine/ai-ml/about-agent-substrate)。
了解更多，请阅读 [About Agent Substrate](https://docs.cloud.google.com/kubernetes-engine/ai-ml/about-agent-substrate)，
或访问[开源仓库](https://github.com/agent-substrate/substrate)。

## 译者补充

- 原文结尾的 “Agent Substrate on GKE documentation” 与 “About Agent Substrate”
  都指向 Google Cloud 文档
  [About GKE Agent Substrate](https://docs.cloud.google.com/kubernetes-engine/ai-ml/about-agent-substrate)。
  该页说明：所有 Google Cloud 客户都可用于评估和非生产环境；生产支持走私有 GA
  白名单。文档要求使用 **GKE Standard**（不支持 Autopilot），集群版本为 **1.36**
  （创建时启用指定 beta API）或 **1.37+**，并依赖 Workload Identity Federation 与
  Cloud Storage 保存快照。
- GKE 优化安装脚本位于面向合格客户的 `substrate-gke` 仓库；公开可跟进的部署入口是
  开源仓库的
  [GKE Quickstart](https://github.com/agent-substrate/substrate#gke-quickstart-development)
  和[架构说明](https://github.com/agent-substrate/substrate/blob/main/docs/architecture.md)。
- Agent Substrate 建立在 [Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox)
  的安全运行时与快照能力之上，但把 Kubernetes 控制面移出热路径，用专用控制面/数据面
  处理大规模挂起/恢复。相关前序公告见
  [Bringing you Agent Sandbox on GKE and Agent Substrate](https://cloud.google.com/blog/products/containers-kubernetes/bringing-you-agent-sandbox-on-gke-and-agent-substrate)。
- Filestore agent volumes 是面向有状态 Agent 工作区的新能力。公开 GKE 文档目前更完整
  覆盖的是 [Filestore CSI](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/filestore-csi-driver)
  与 [Agent Sandbox 存储](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/agent-sandbox-storage)；
  毫秒级挂载/卸载的 agent volume controller 以本文宣布为准。
- 原文 “that’s fundamentally than running …” 缺词，译文按 “fundamentally different
  from” 理解。

## 参考

- Google Cloud 原文，宣布 Agent Substrate 在 GKE 上可用：https://cloud.google.com/blog/products/containers-kubernetes/agent-substrate-available-on-gke
- GKE 官方概念文档，说明 Actor/Worker 模型、快照恢复路径和当前限制：https://docs.cloud.google.com/kubernetes-engine/ai-ml/about-agent-substrate
- Agent Substrate 开源仓库，包含控制面、数据面和 GKE Quickstart：https://github.com/agent-substrate/substrate
- 项目架构说明，解释如何把 Kubernetes 控制面移出热路径：https://github.com/agent-substrate/substrate/blob/main/docs/architecture.md
- GKE 产品页，Agent Substrate 优化运行的托管 Kubernetes 平台：https://cloud.google.com/kubernetes-engine
- GKE Agent Sandbox 概念文档，介绍隔离、Warm Pool 和 Claim 模型：https://docs.cloud.google.com/kubernetes-engine/docs/concepts/machine-learning/agent-sandbox
- Kubernetes SIG 的 Agent Sandbox 开源项目，提供 Sandbox CRD 和安全执行环境：https://github.com/kubernetes-sigs/agent-sandbox
- 前序公告，介绍 Agent Sandbox 在 GKE 上 GA，以及 Agent Substrate 首次公开：https://cloud.google.com/blog/products/containers-kubernetes/bringing-you-agent-sandbox-on-gke-and-agent-substrate
- 用户态内核沙箱运行时，Agent Substrate 的低开销内核隔离选项之一：https://gvisor.dev
- 硬件隔离 microVM hypervisor，提供完整 Linux 内核兼容性：https://github.com/cloud-hypervisor/cloud-hypervisor
- 对象存储服务，用于持久保存 Agent 挂起快照：https://cloud.google.com/storage
- GKE 自定义 ComputeClass 文档，用于跨机型和 Spot/按需池动态管理机器：https://cloud.google.com/kubernetes-engine/docs/concepts/about-custom-compute-classes
- Google 自研 Arm 处理器，文档称对沙箱工作负载有更高性价比：https://cloud.google.com/products/axion
- 托管 NFS 文件存储，可与 Agent Substrate 的有状态工作区集成：https://cloud.google.com/filestore
- 在 GKE 上通过 CSI 动态挂载 Filestore 卷的操作文档：https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/filestore-csi-driver
- Hermes Agent 背后的研究团队，也是 Agent Substrate 的早期设计伙伴：https://nousresearch.com
- Hermes Agent 开源仓库，文中作为正在 Agent Substrate 上构建的领先 Agent：https://github.com/nousresearch/hermes-agent
- 模型路由与用量排行平台，原文用它说明 Hermes 的全球用量排名：https://openrouter.ai
- Google 的 Agent 开发平台/harness，文中列为常见本地 Agent 运行方式之一：https://antigravity.google
- Anthropic 的编码 Agent，可在本地 harness 中运行，也可对接 Agent Substrate：https://code.claude.com
- OpenAI 的编码 Agent/harness，同样属于文中提到的本地开发入口：https://openai.com/codex
- 开源个人/团队 Agent harness，可在本地运行，也是 Agent Substrate 兼容的框架之一：https://openclaw.ai
