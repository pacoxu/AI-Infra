---
status: Active
maintainer: pacoxu
date: 2026-06-05
tags: kubernetes, workload-aware-scheduling, gang-scheduling, volcano, grove, scheduling
canonical_path: docs/blog/2026-06-05/2026-06-05-gang-scheduling-workload-aware-scheduling_zh.md
source_urls:
  - https://kubernetes.io/blog/2025/12/29/kubernetes-v1-35-introducing-workload-aware-scheduling/
  - https://kubernetes.io/blog/2026/05/13/kubernetes-v1-36-advancing-workload-aware-scheduling/
  - https://kubernetes.io/docs/concepts/workloads/pods/scheduling-group/
  - https://kubernetes.io/docs/concepts/workloads/podgroup-api/
  - https://kubernetes.io/docs/concepts/scheduling-eviction/workload-aware-preemption/
  - https://github.com/NVIDIA/grove
  - https://docs.nvidia.com/dynamo/dev/kubernetes-deployment/multinode/multinode-deployments
  - https://volcano.sh/en/docs/podgroup/
  - https://kthena.volcano.sh/
---

# 如何理解 Workload-Aware Scheduling 与 Gang Scheduling：Volcano、kube-scheduler 与 Grove 三条路线

如果你最近在看 AI 训练、批处理、分布式推理或者多节点 serving，很容易连续遇到这些词：

- `Gang Scheduling`
- `Workload-Aware Scheduling`
- `PodGroup`
- `Volcano`
- `Grove`

问题是，这些词经常被混在一起讲，结果就会出现一个常见误区：

> 大家都在谈 “一组 Pod 要一起调度”，但说的其实不是同一层问题。

文中状态信息核对时间为 **2026-06-05**。

## 先说结论

- `kube-scheduler` 的 `Workload-Aware Scheduling`，代表的是 **Kubernetes 原生调度器开始理解 group / workload 语义**。
- `Volcano` 代表的是 **已经成熟可用的集群级 gang / queue / fairness / topology 调度平台**。
- `Grove` 代表的不是一个通用批调度器，而是 **面向多角色推理系统的编排 API**；它通常与 `KAI Scheduler` 配合来落地 gang 和 topology-aware placement。
- 所以这三条路线不是简单的“谁替代谁”，而是分别站在 **原生调度器、统一调度平台、推理编排层** 三个不同层级回答同一个问题：
  **如何把一组相互依赖的 Pod 当成一个整体来放置和运行。**

## 1. 为什么这个问题会变得越来越重要

对单 Pod 服务来说，逐 Pod 调度问题不大；但对下面这些工作负载，逐 Pod 调度很快就会暴露问题：

- 分布式训练
- Spark / Ray / MPI 批处理
- 多节点大模型推理
- prefill / decode / router 分离的推理系统
- Agent pipeline 或多阶段推理链路

核心矛盾非常一致：

1. **部分 Pod 先被调度上去，但整体系统并不能工作**
2. **已经占住的资源无法产生价值**
3. **剩余 Pod 因拓扑、配额、队列或公平性原因迟迟起不来**
4. **调度器需要决定的，不再是“这个 Pod 放哪”而是“这一组 Pod 能不能一起放、放在哪里更合理”**

所以真正的问题不只是 `Gang Scheduling`，而是三个能力要一起看：

- **整体准入**：这组 Pod 现在应不应该进入活跃调度
- **整体放置**：这一组 Pod 能不能一起落到满足约束的节点上
- **整体运行**：如果是一套多角色系统，启动顺序、扩缩、拓扑和资源回收如何协同

也正因为如此，`Gang Scheduling` 经常只是入口，真正的主题其实是 **Workload-Aware Scheduling**。

## 2. `kube-scheduler` 路线：原生调度器开始理解 workload

如果你站在 Kubernetes upstream 的视角，这条主线很清楚：

- `v1.35` 开始把 `Workload-Aware Scheduling` 作为新方向公开推出
- `v1.36` 进一步从 “基于 Pod framework 做 gang” 往 “PodGroup scheduling cycle” 推进

### 2.1 `v1.35` 的关键意义：group identity 进入原生语义

Kubernetes 官方在 **2025-12-29** 发布的
`Kubernetes v1.35: Introducing Workload Aware Scheduling`
里，把这一阶段的重点定义为：

- `Workload API`
- `Gang Scheduling`
- `Opportunistic Batching`

这里最重要的不是某一个 feature gate，而是一个更根本的变化：

> `kube-scheduler` 不再只看到“独立 Pod”，而开始看到“属于某个 group / workload 的 Pod”。

这条线在官方文档里的具体体现包括：

- `Scheduling Group`
- `PodGroup`
- workload 级调度语义

换句话说，upstream 不是简单加了一个 “all-or-nothing” 规则，而是在原生调度器里给 group identity 找到了正式挂载点。

### 2.2 `v1.36` 的关键意义：从 Pod-based gang 走向 PodGroup scheduling cycle

Kubernetes 官方在 **2026-05-13** 发布的
`Kubernetes v1.36: Advancing Workload-Aware Scheduling`
里，又把这条路线往前推进了一步：

- `Workload` 和 `PodGroup` API 解耦
- `kube-scheduler` 增加 `PodGroup scheduling cycle`
- 引入 `placementGenerate` 和 `placementScore`
- 引入 `topology-aware scheduling`
- 引入 `workload-aware preemption`
- 为 PodGroup / workload 打开更强的资源语义挂载点

这一步的本质变化是：

> scheduler 开始把 “一组 Pod 的 placement” 当成一个显式问题，而不是把单个 Pod 的调度结果事后拼起来。

所以如果你把 `kube-scheduler` 这条线概括成一句话，最准确的说法是：

> `Workload-Aware Scheduling` 是 Kubernetes 原生调度器把调度对象从 `Pod` 慢慢升级到 `PodGroup / Workload` 的过程。

### 2.3 这条路线最适合解决什么问题

`kube-scheduler` 的优势在于：

- 更贴近 upstream 原生能力
- 不需要额外引入一个完全不同的主调度器心智模型
- 更容易和后续 Kubernetes 原生 API、preemption、resource claim、拓扑语义一起演进

但这条路线今天也有一个现实边界：

- 它正在快速演进，但仍偏 **原生能力建设阶段**
- 如果你今天要做非常成熟的 queue、quota、DRF、公平性、复杂回收策略，往往还会看外部调度平台

也就是说，`kube-scheduler WAS` 的最大价值是：

> 它定义了原生未来方向，但不自动等于“已经替代所有外部 gang 调度器”。

## 3. `Volcano` 路线：成熟的统一调度平台

如果你站在生产集群治理视角，`Volcano` 回答的问题明显更完整：

- Pod 要不要一起调度
- 资源应该进哪个 queue
- 多租户之间如何做 quota / fairness
- 不同 job 之间如何 preempt / reclaim
- 拓扑、HyperNode、设备资源如何一起纳入放置决策

### 3.1 `Volcano` 的核心不是只有 PodGroup

很多人第一次接触 Volcano，会把它简单理解成 “支持 gang scheduling 的调度器”。这太低估它了。

`Volcano` 真正的核心组合更像是：

- `PodGroup`
- queue / quota
- `DRF`
- reclaim / preemption
- topology-aware scheduling
- 面向批处理和 AI 集群的统一调度策略

也就是说，`PodGroup` 只是它的 workload 粒度入口，不是全部价值。

### 3.2 为什么 `Volcano` 现在仍然重要

在 `kube-scheduler WAS` 快速推进的同时，`Volcano` 仍然有很强现实价值，原因很简单：

1. **它解决的是完整平台问题，不只是单个 upstream feature**
2. **它已经是很多训练、批处理、AI 混部场景的现成路径**
3. **它在 queue、公平性、抢占、设备资源与拓扑上的工程能力，比“只谈 gang”要完整得多**

如果你今天面对的是下面这些问题，Volcano 往往更贴近生产答案：

- 多团队共享 GPU 集群
- 训练与推理混部
- 作业级排队、公平性和 quota 借还
- gang + topology + heterogeneous resource 一起考虑
- 已经围绕 `VolcanoJob` / `PodGroup` 建好控制面与运维流程

### 3.3 `Volcano` 与推理工作负载的关系

如果你的场景是推理而不是训练，也不要把 Volcano 直接排除掉。

一条很典型的路线就是：

- 上层用 `LWS` 或类似 workload 抽象表达多角色关系
- 下层用 `Volcano` 承接 gang / queue / topology / preemption

另外，`Kthena` 这类 Volcano 生态项目也说明了一件事：

> `Volcano` 不只是“批处理调度器”，它也在往 inference cloud 的方向延展。

所以从主题上说，`Volcano` 在这张图里的位置最适合描述为：

> **成熟的统一调度平台路线**

而不是单纯一个 “外部 gang scheduling 插件”。

## 4. `Grove` 路线：面向多角色推理系统的 orchestration API

`Grove` 最容易被误解的地方是：很多人会把它直接当成 “NVIDIA 的 gang scheduler”。

这并不准确。

`Grove` 的官方定位更像：

> 一个用单个声明式接口表达完整 AI inference system 的 Kubernetes API。

它要表达的不是 “一个 Job 有几个 Pod”，而是一整套推理系统，比如：

- prefill
- decode
- routing
- leader / worker
- 多个可扩缩角色

### 4.1 `Grove` 解决的是“系统编排”问题

从官方公开能力看，`Grove` 强调的是：

- hierarchical gang scheduling
- topology-aware placement
- multi-level autoscaling
- explicit startup ordering

这说明它的价值点不是单一的 “all-or-nothing” 调度规则，而是：

> 把一个多角色、多节点、强拓扑耦合的推理系统，变成 Kubernetes 可声明、可扩缩、可整体协调的对象。

所以 `Grove` 在层级上更像：

- **工作负载编排 API**
- 而不是通用集群主调度器本身

### 4.2 `Grove` 通常要和 `KAI Scheduler` 一起看

NVIDIA 官方 Dynamo 文档现在给出的 multinode 路线非常清楚：

- `Grove + KAI Scheduler`
- 或者 `LWS + Volcano`

这句话信息量很大，因为它直接说明：

1. `Grove` 路线默认依赖更强的 AI-aware 调度能力
2. NVIDIA 自己也把 `Volcano` 视作社区侧 gang scheduling 承接路径
3. `Grove` 和 `Volcano` 不是同一层对象

更准确地说：

- `Grove` 负责表达系统关系与整体生命周期
- `KAI Scheduler` 负责把这些关系落到真实集群的调度决策上

所以如果把 `Grove` 单独拎出来和 `kube-scheduler` 或 `Volcano` 对打，其实比较维度已经错了。

### 4.3 `Grove` 最适合什么场景

如果你的目标是：

- multinode inference
- prefill / decode disaggregation
- NVIDIA 拓扑优化路径
- 需要 startup ordering、multi-level autoscaling、系统级编排

那 `Grove + KAI` 明显是更顺手的一条路线。

它回答的问题不是 “一个 batch job 怎么原子启动”，而是：

> 一套复杂推理系统怎么以拓扑敏感、角色敏感、扩缩敏感的方式整体运行起来。

## 5. 这三条路线不是“谁替代谁”，而是三个层级

如果把它们放在同一张表里，更容易看清楚差异：

| 路线 | 主要层级 | 核心对象 | 主要强项 | 更适合谁 |
| --- | --- | --- | --- | --- |
| `kube-scheduler` `WAS` | 原生调度器 | `SchedulingGroup` / `PodGroup` / `Workload` | 把 workload 语义带回 upstream，原生演进 `PodGroup scheduling cycle`、`workload-aware preemption`、`topology-aware scheduling` | 想紧贴 upstream、重视原生 API 演进的团队 |
| `Volcano` | 统一调度平台 | `PodGroup` + queue + quota | gang、fairness、DRF、reclaim、preemption、拓扑、异构资源 | 已经在做共享集群治理、训练/推理混部、作业排队与公平性的团队 |
| `Grove + KAI` | 推理编排 + AI-aware scheduling | `PodCliqueSet` / `PodGang` / 多角色 inference system | hierarchical gang、topology-aware placement、startup ordering、multi-level autoscaling | 面向多角色、多节点、强拓扑约束推理系统的团队 |

最关键的一点是：

> `Volcano` 与 `kube-scheduler WAS` 更接近“调度路径”的对比，
> `Grove` 则更接近“工作负载编排模型”的对比。

所以不要把三者当成完全同构的候选项。

## 6. 如果你要做选择，我建议这样看

### 6.1 想看原生未来方向，优先看 `kube-scheduler WAS`

如果你的问题是：

- Kubernetes 原生 gang scheduling 正在演进到哪一步
- `PodGroup` 和 workload 语义最终会不会回到 upstream
- 以后哪些能力不必依赖外部调度器

那重点应该放在：

- `v1.35` 的 `Workload-Aware Scheduling`
- `v1.36` 的 `PodGroup scheduling cycle`
- `workload-aware preemption`
- `topology-aware scheduling`

### 6.2 今天就要生产可用的队列、公平性和 gang，优先看 `Volcano`

如果你的问题是：

- 今天怎么在共享集群里稳定跑训练和批处理
- 怎么把 queue、quota、公平性、抢占和 gang 放到一套系统里
- 怎么把 workload-level 调度落成平台能力

那 `Volcano` 往往是更现实的答案。

### 6.3 做多角色推理系统，优先看 `Grove + KAI`

如果你的问题是：

- prefill / decode / router 这套系统如何作为整体运行
- 多节点推理如何结合拓扑和启动顺序
- 系统级 autoscaling 如何围绕一个 inference graph 工作

那 `Grove` 才是更靠近问题定义的一层。

如果你不走 `Grove`，NVIDIA 官方文档给出的社区替代路径也很明确：

- `LWS + Volcano`

这也再次说明，`Grove` 路线与 `Volcano` 路线之间不是简单替换关系，而是 **一条偏 NVIDIA inference orchestration、另一条偏社区统一调度平台**。

## 7. 一个更实用的记忆方式

如果只记一句话，我建议记成这样：

> `kube-scheduler WAS` 解决的是 **Kubernetes 原生调度器如何理解 workload**，
> `Volcano` 解决的是 **共享集群里 workload 怎么被完整地排队、放置和抢占**，
> `Grove` 解决的是 **复杂推理系统怎么作为一个整体被表达、启动、扩缩和协同**。

从这个角度看，`Gang Scheduling` 不是一个独立小 feature，而是三条路线共同指向的结果：

- upstream 正在把它原生化
- Volcano 已经把它平台化
- Grove 则把它系统化、推理化

## 参考资料

- [Kubernetes v1.35: Introducing Workload Aware Scheduling](https://kubernetes.io/blog/2025/12/29/kubernetes-v1-35-introducing-workload-aware-scheduling/)
- [Kubernetes v1.36: Advancing Workload-Aware Scheduling](https://kubernetes.io/blog/2026/05/13/kubernetes-v1-36-advancing-workload-aware-scheduling/)
- [Scheduling Group](https://kubernetes.io/docs/concepts/workloads/pods/scheduling-group/)
- [PodGroup API](https://kubernetes.io/docs/concepts/workloads/podgroup-api/)
- [Workload-Aware Preemption](https://kubernetes.io/docs/concepts/scheduling-eviction/workload-aware-preemption/)
- [Grove GitHub](https://github.com/NVIDIA/grove)
- [NVIDIA Dynamo Multinode Deployments](https://docs.nvidia.com/dynamo/dev/kubernetes-deployment/multinode/multinode-deployments)
- [Volcano PodGroup](https://volcano.sh/en/docs/podgroup/)
- [Kthena](https://kthena.volcano.sh/)
